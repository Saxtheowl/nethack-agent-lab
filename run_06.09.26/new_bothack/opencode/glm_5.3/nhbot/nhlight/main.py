"""Game driver: autonomous play loop and inline supervision.

The read loop doubles as the supervisor: while no new data arrives the
same owner thread distinguishes a pending prompt, a pending transaction
result, a slow decision and genuine silence - the watchdog can never
fight the strategy for the terminal.  Recovery is staged and
evidence-first: classify the settled frame, probe with the marker
trick, escalate only when the probe fails.
"""

import json
import os
import time

from . import brain as br
from . import session as sm
from . import world as wl
from .dialogue import DefaultPolicy, Dialogue, classify_frame


class Game:
    def __init__(self, run_dir, username, seed=None, max_seconds=None):
        self.run_dir = run_dir
        self.username = username
        self.seed = seed
        self.max_seconds = max_seconds
        self.session = sm.Session(run_dir, username, seed=seed)
        self.dialogue = Dialogue(self.session)
        self.world = wl.World()
        self.brain = br.Brain(self.world, self.dialogue)
        self.actions = 0
        self.recoveries = []       # (t, what, ok)
        self.journal = []          # (t, kind, detail)
        self.t0 = time.monotonic()

    # ---- main ----------------------------------------------------------
    def run(self):
        try:
            self.session.start()
            self._welcome()
            self._loop()
        except sm.SessionDead:
            pass
        finally:
            self._dump()
            self.session.close()
        return self._verdict()

    def _dump(self):
        """Evidence-first accounting: journal tail + the final screen."""
        try:
            with open(os.path.join(self.run_dir, "journal.txt"), "w") as fh:
                for rec in self.journal:
                    fh.write("%s %s %s\n" % rec)
            lines, cells, cx, cy = self.session.terminal.snapshot()
            with open(os.path.join(self.run_dir, "final_screen.txt"), "w") as fh:
                fh.write("cursor=(%d,%d)\n" % (cx, cy))
                for i, l in enumerate(lines):
                    fh.write("%2d|%s|\n" % (i, l))
        except Exception:
            pass

    def _budget_left(self):
        return not (self.max_seconds
                    and time.monotonic() - self.t0 > self.max_seconds)

    def _welcome(self):
        """From launch to the first settled frame with a valid status."""
        for _ in range(40):
            if not self._budget_left():
                raise Stuck("budget exhausted before first frame")
            self.dialogue.settle(quiet=0.3, cap=3.0)
            kind, _ = classify_frame(self.session)
            self.journal.append((round(time.monotonic() - self.t0, 2), kind, ""))
            if kind == "more":
                self.dialogue.write(" ")
                continue
            lines, cells, cx, cy = self.session.terminal.snapshot()
            st = wl.Status.parse(lines)
            if st.valid():
                return
            if kind in ("extcmd", "marker", "stale-game"):
                self.dialogue.write("\x1b")
                continue
            if kind in ("menu", "choice", "waiting"):
                self.dialogue.write("\x1b")
                continue
        raise Stuck("welcome never settled")

    def _loop(self):
        while self._budget_left():
            try:
                self.dialogue.settle()
            except sm.SessionDead:
                return
            kind, detail = classify_frame(self.session)
            self.journal.append(
                (round(time.monotonic() - self.t0, 2), kind, str(detail)[:60]))
            if kind == "more":
                self.dialogue.write(" ")
                continue
            if kind == "marker":
                self.dialogue.write("\x1b")
                continue
            if kind == "extcmd":
                self.dialogue.write("\x1b\x1b")
                continue
            if kind == "stale-game":
                self.dialogue.write("y\n")
                continue
            if kind == "waiting":
                ok = self.dialogue.probe()
                self.recoveries.append(
                    (round(time.monotonic() - self.t0, 2), "waiting-frame", ok))
                continue
            if kind == "yesno":
                # death disclosure prompts and stray confirmations: answer
                # "yes" only to quit-confirmations, "no" everywhere else
                self.dialogue.write("y" if "Really quit" in detail else "n")
                continue
            if kind in ("menu", "choice", "direction"):
                self.dialogue.write("\x1b")   # stray prompt: cancel, never guess
                continue
            lines, cells, cx, cy = self.session.terminal.snapshot()
            st = wl.Status.parse(lines)
            if not st.valid():
                # possibly mid-redraw or a death disclosure: resync
                self.dialogue.pump(DefaultPolicy(), max_steps=25)
                continue
            self.world.observe(lines, cx, cy)
            self.brain.lines = lines
            act = self.brain.choose()
            if act is None:
                ok = self.dialogue.probe()
                self.recoveries.append(
                    (round(time.monotonic() - self.t0, 2), "no-action", ok))
                continue
            try:
                self._exec(act)
            except sm.SessionDead:
                return

    def _exec(self, action):
        if action.keys:
            self.dialogue.write(action.keys)
        if action.kind == "tx":
            self.dialogue.pump(action.policy or DefaultPolicy())
        else:
            self.dialogue.pump(DefaultPolicy())
        self.actions += 1
        if action.kind == "move":
            top = self.session.terminal.snapshot()[0][0].rstrip()
            if "It's a wall" in top:
                from .dialogue import REVERSE
                delta = REVERSE.get(action.keys)
                if delta:
                    lvl = self.world.level()
                    x = self.world.px + delta[0]
                    y = self.world.py + delta[1]
                    if 0 <= x < lvl.W and 0 <= y < lvl.H:
                        lvl.seen[y][x] = True
                        lvl.walkable[y][x] = False
                        lvl.kind[y][x] = "|"
        if action.on_done:
            try:
                action.on_done()
            except Exception:
                pass

    # ---- verdict -------------------------------------------------------
    def _verdict(self, fallback=None):
        entry = self._xlog_entry()
        if entry:
            death = entry.get("death", "")
            if death == "ascended":
                status = "ascension"
            elif death:
                status = "death:" + death
            else:
                status = "ended"
            return {"status": status, "xlog": entry}
        if fallback:
            return {"status": fallback}
        return {"status": "unknown-no-xlog"}

    def _xlog_entry(self):
        path = os.path.join(sm.NH_VAR, "xlogfile")
        if not os.path.exists(path):
            return None
        best = None
        with open(path, "rb") as fh:
            data = fh.read().decode("utf-8", "replace")
        for raw in data.splitlines():
            fields = {}
            for chunk in raw.split(":"):
                if "=" in chunk:
                    k, v = chunk.split("=", 1)
                    fields[k] = v
            if fields.get("name") == self.username:
                best = fields
        return best


# ---- CLI -------------------------------------------------------------
def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(prog="nhlight",
                                description="autonomous NetHack 3.4.3-NAO bot")
    sub = p.add_subparsers(dest="cmd", required=True)
    play = sub.add_parser("play", help="play one game")
    play.add_argument("--seed", type=int, default=None)
    play.add_argument("--max-seconds", type=int, default=1800)
    play.add_argument("--run-dir", default=None)
    camp = sub.add_parser("campaign", help="play several games")
    camp.add_argument("--games", type=int, default=5)
    camp.add_argument("--max-seconds", type=int, default=1800)
    camp.add_argument("--outdir", default="runs")
    sub.add_parser("summary", help="summarize finished runs")
    args = p.parse_args(argv)

    if args.cmd == "play":
        return _play(args.run_dir, args.seed, args.max_seconds)
    if args.cmd == "campaign":
        results = []
        for i in range(args.games):
            print("=== game %d/%d ===" % (i + 1, args.games), flush=True)
            results.append(_play(None, None, args.max_seconds))
        path = os.path.join(args.outdir, "campaign.json")
        with open(path, "w") as fh:
            json.dump(results, fh, indent=2)
        return results
    if args.cmd == "summary":
        from .report import summarize
        print(json.dumps(summarize(), indent=2))
        return None
    return None


def _play(run_dir=None, seed=None, max_seconds=1800):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    name = "nlig%06x" % (int(time.time() * 1000) % (1 << 24))
    if run_dir is None:
        run_dir = os.path.join("runs", "%s-%s" % (stamp, name))
    os.makedirs(run_dir, exist_ok=True)
    game = Game(run_dir, name, seed=seed, max_seconds=max_seconds)
    verdict = game.run()
    result = {
        "run_id": "%s-%s" % (stamp, name),
        "username": name,
        "seed": seed,
        "run_dir": run_dir,
        "actions": game.actions,
        "recoveries": game.recoveries,
        "verdict": verdict,
    }
    with open(os.path.join(run_dir, "result.json"), "w") as fh:
        json.dump(result, fh, indent=2)
    print(json.dumps(result["verdict"], indent=2))
    return result


if __name__ == "__main__":
    main()
