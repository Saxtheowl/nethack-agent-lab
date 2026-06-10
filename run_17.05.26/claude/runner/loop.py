#!/opt/venv/bin/python3
"""Run BotHack repeatedly until N winning games are recorded.

Supports running multiple games in parallel: each worker gets its own
NETHACKDIR (/nh343-wN) so the games don't fight over perm/save/record.

Layout under /data/games/:
  index.json                   — top-level summary, updated after each game
  winning/0001/                — first won game
    meta.json                  — seed, turn count, ascended:true, worker_id, ...
    game.ttyrec                — terminal recording
    bothack.log
  attempts/<id>_<seed>/        — every attempt (won or lost), kept for analysis

Usage:
  loop.py --target 10 --parallel 5 [--max-attempts 2000] [--seed-start ...]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path("/data/games")
WIN_DIR = ROOT / "winning"
ATTEMPT_DIR = ROOT / "attempts"
INDEX = ROOT / "index.json"

DETECT = "/opt/runner/detect_ascension.py"
RUN_ONE = "/opt/runner/run_one.sh"


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def log(msg: str) -> None:
    print(f"[{_now_iso()}] {msg}", flush=True)


# --- shared state (single index.json, written atomically under a lock) -----
class State:
    def __init__(self, target: int):
        self.lock = threading.Lock()
        self.target = target
        self.wins = 0
        self.attempts = 0
        self.games: list[dict] = []
        self._load()

    def _load(self) -> None:
        if INDEX.exists():
            try:
                d = json.loads(INDEX.read_text())
                self.target = d.get("target", self.target)
                self.wins = d.get("wins", 0)
                self.attempts = d.get("attempts", 0)
                self.games = d.get("games", [])
            except Exception:
                pass

    def save(self) -> None:
        INDEX.parent.mkdir(parents=True, exist_ok=True)
        tmp = INDEX.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump({
                "target": self.target,
                "wins": self.wins,
                "attempts": self.attempts,
                "games": self.games,
            }, f, indent=2)
        tmp.replace(INDEX)

    def claim_attempt(self) -> int:
        """Return a freshly-incremented attempt id."""
        with self.lock:
            self.attempts += 1
            return self.attempts

    def record_outcome(self, attempt: int, seed: int, worker: int, meta: dict) -> bool:
        """Append the game to the index. Returns True if this was an ascension.

        Lost games are deleted right after metrics are extracted — only
        ascensions are kept on disk under winning/. The summary line in
        index.json keeps the seed + final turn so attempts remain reproducible.
        """
        with self.lock:
            ascended = bool(meta.get("ascended"))
            game_dir = Path(meta["game_dir"]) if meta.get("game_dir") else None
            summary = {
                "attempt": attempt,
                "seed": seed,
                "worker": worker,
                "ascended": ascended,
                "final_turn": meta.get("final_turn"),
                "exit_code": meta.get("exit_code"),
                "started_at": meta.get("started_at"),
                "finished_at": meta.get("finished_at"),
            }
            if ascended:
                self.wins += 1
                slot = WIN_DIR / f"{self.wins:04d}_seed{seed}"
                if game_dir and game_dir.exists() and game_dir != slot:
                    try:
                        WIN_DIR.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(game_dir), str(slot))
                        summary["game_dir"] = str(slot)
                    except Exception as e:
                        log(f"   could not promote {game_dir} → {slot}: {e}")
                        summary["game_dir"] = str(game_dir)
                else:
                    summary["game_dir"] = str(game_dir) if game_dir else None
            else:
                # Lost — drop the ttyrec + logs unless this run beat the
                # previous "longest survivor" bar. We keep at most 3 such
                # diagnostic runs to help spot systematic problems without
                # eating disk on every failure.
                keep = False
                lost = sorted(
                    (g for g in self.games if not g["ascended"]
                     and g.get("game_dir")),
                    key=lambda g: -(g.get("final_turn") or 0))
                if (meta.get("final_turn") or 0) > 0:
                    if len(lost) < 3:
                        keep = True
                    else:
                        cutoff = lost[2].get("final_turn") or 0
                        if (meta.get("final_turn") or 0) > cutoff:
                            keep = True
                            # evict the previous shortest of the top 3
                            evict = lost[2]
                            ed = evict.get("game_dir")
                            if ed:
                                try: shutil.rmtree(ed)
                                except Exception: pass
                                evict["game_dir"] = None
                if keep:
                    summary["game_dir"] = str(game_dir) if game_dir else None
                else:
                    if game_dir and game_dir.exists():
                        try: shutil.rmtree(game_dir)
                        except Exception as e:
                            log(f"   could not delete {game_dir}: {e}")
                    summary["game_dir"] = None
            self.games.append(summary)
            self.save()
            return ascended

    def done(self) -> bool:
        with self.lock:
            return self.wins >= self.target


# --- single attempt --------------------------------------------------------
def run_attempt(attempt_id: int, seed: int, worker_id: int) -> dict:
    """Run one BotHack game with the given seed on worker `worker_id`."""
    game_dir = ATTEMPT_DIR / f"{attempt_id:05d}_seed{seed}"
    game_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["WORKER_ID"] = str(worker_id)

    log(f"w{worker_id} attempt {attempt_id:05d} seed={seed} → {game_dir.name}")
    rc = subprocess.call(
        [RUN_ONE, f"{attempt_id:05d}", str(seed), str(game_dir)],
        env=env,
    )
    subprocess.call([DETECT, str(game_dir)])

    meta_path = game_dir / "meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
        except Exception:
            meta = {"ascended": False, "exit_code": rc}
    else:
        meta = {"ascended": False, "exit_code": rc}
    meta["game_dir"] = str(game_dir)
    meta["worker_id"] = worker_id
    return meta


# --- main loop -------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--target", type=int, default=10)
    p.add_argument("--parallel", type=int, default=5,
                   help="number of games to run concurrently (1..8)")
    p.add_argument("--max-attempts", type=int, default=2000)
    p.add_argument("--seed-start", type=int, default=int(time.time()),
                   help="first seed (subsequent seeds increment by 1)")
    args = p.parse_args()

    if not 1 <= args.parallel <= 8:
        print("--parallel must be 1..8 (provisioned NETHACKDIRs)", file=sys.stderr)
        return 2

    ROOT.mkdir(parents=True, exist_ok=True)
    WIN_DIR.mkdir(parents=True, exist_ok=True)
    ATTEMPT_DIR.mkdir(parents=True, exist_ok=True)

    state = State(args.target)
    state.target = args.target
    state.save()

    next_seed = args.seed_start
    seed_lock = threading.Lock()
    def grab_seed() -> int:
        nonlocal next_seed
        with seed_lock:
            s = next_seed
            next_seed += 1
            return s

    submitted = 0  # total submitted so far (caps at --max-attempts)
    submit_lock = threading.Lock()

    def submit_one(executor, worker_id):
        nonlocal submitted
        with submit_lock:
            if submitted >= args.max_attempts:
                return None
            submitted += 1
        if state.done():
            return None
        aid = state.claim_attempt()
        seed = grab_seed()
        return executor.submit(run_attempt, aid, seed, worker_id), aid, seed, worker_id

    with cf.ThreadPoolExecutor(max_workers=args.parallel) as ex:
        in_flight: dict[cf.Future, tuple[int, int, int]] = {}

        # Seed initial batch — one game per worker slot.
        for w in range(1, args.parallel + 1):
            res = submit_one(ex, w)
            if res is None:
                break
            fut, aid, seed, worker = res
            in_flight[fut] = (aid, seed, worker)

        while in_flight and not state.done():
            done, _ = cf.wait(in_flight, return_when=cf.FIRST_COMPLETED)
            for fut in done:
                aid, seed, worker = in_flight.pop(fut)
                try:
                    meta = fut.result()
                except Exception as e:
                    log(f"w{worker} attempt {aid:05d} crashed: {e}")
                    meta = {"ascended": False, "exit_code": -1, "game_dir": ""}
                ascended = state.record_outcome(aid, seed, worker, meta)
                tag = "*** ASCENSION ***" if ascended else "no ascension"
                log(f"w{worker} attempt {aid:05d} done ({tag} turn={meta.get('final_turn')}) "
                    f"wins={state.wins}/{state.target} attempts={state.attempts}")

                if state.done():
                    break
                # Spawn a replacement for the worker slot that just finished.
                res = submit_one(ex, worker)
                if res is None:
                    continue
                new_fut, n_aid, n_seed, n_worker = res
                in_flight[new_fut] = (n_aid, n_seed, n_worker)

        # Drain remaining (don't cancel if state.done — let them finish gracefully)
        for fut in list(in_flight):
            aid, seed, worker = in_flight[fut]
            try:
                meta = fut.result()
                state.record_outcome(aid, seed, worker, meta)
            except Exception:
                pass

    if state.wins >= args.target:
        log(f"DONE: reached {state.wins} ascensions in {state.attempts} attempts.")
        return 0
    log(f"STOPPED: only {state.wins}/{args.target} ascensions after {state.attempts} attempts.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
