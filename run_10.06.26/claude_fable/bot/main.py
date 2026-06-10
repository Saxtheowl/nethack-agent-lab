"""Run one Valkyrie->Minetown game. Writes meta.json into the output dir."""
import argparse
import json
import os
import signal
import sys
import time
import traceback


class Terminated(Exception):
    pass


def _on_term(signum, frame):
    raise Terminated()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from term import TtySession
from playground import make_playground, nethack_argv_env
from game import Game, GameOver, ESC
from brain import Brain, Abort

MAX_TICKS = 25000
MAX_TURNS = 40000
WALL_TIMEOUT = 40 * 60  # seconds


def parse_xlogfile(playground):
    path = os.path.join(playground, "xlogfile")
    try:
        with open(path) as f:
            lines = [l for l in f if l.strip()]
        if not lines:
            return {}
        fields = {}
        for kv in lines[-1].strip().split("\t"):
            if "=" in kv:
                k, v = kv.split("=", 1)
                fields[k] = v
        return fields
    except OSError:
        return {}


def run_one(outdir, game_id="g0", verbose=False):
    os.makedirs(outdir, exist_ok=True)
    playground = os.path.join(outdir, "playground")
    make_playground(playground)
    argv, env = nethack_argv_env(playground, user=f"Bot")

    logpath = os.path.join(outdir, "bot.log")
    logf = open(logpath, "w")

    def log(*a):
        line = " ".join(str(x) for x in a)
        logf.write(line + "\n")
        logf.flush()
        if verbose:
            print(line)

    meta = {
        "id": game_id,
        "result": "unknown",
        "branch": None,
        "dlvl": None,
        "turn": None,
        "ticks": 0,
        "death": None,
        "started": time.time(),
    }

    signal.signal(signal.SIGTERM, _on_term)
    sess = TtySession(argv, env, record=os.path.join(outdir, "game.ttyrec"))
    g = Game(sess, log=log)
    brain = Brain(g, log=log)
    t0 = time.time()
    try:
        brain.start()
        while True:
            if brain.success:
                meta["result"] = "minetown"
                break
            if brain.ticks >= MAX_TICKS:
                meta["result"] = "max_ticks"
                break
            if brain.turn >= MAX_TURNS:
                meta["result"] = "max_turns"
                break
            if time.time() - t0 > WALL_TIMEOUT:
                meta["result"] = "wall_timeout"
                break
            brain.tick()
    except GameOver:
        meta["result"] = "died"
    except Terminated:
        meta["result"] = "terminated"
    except Abort as e:
        meta["result"] = f"abort:{e}"
    except Exception:
        meta["result"] = "crash"
        log(traceback.format_exc())
    finally:
        meta["branch"] = brain.branch
        meta["dlvl"] = brain.dlvl
        meta["turn"] = brain.turn
        meta["ticks"] = brain.ticks
        meta["pray_count"] = brain.pray_count
        # dump final screen + brain state for debugging
        try:
            with open(os.path.join(outdir, "final_screen.txt"), "w") as f:
                for line in sess.lines():
                    f.write(line + "\n")
        except Exception:
            pass
        try:
            brain.dump_state(os.path.join(outdir, "state.json"))
        except Exception:
            pass
        sess.close()
        xlog = parse_xlogfile(playground)
        if xlog:
            meta["death"] = xlog.get("death")
            meta["xlog_dlvl"] = xlog.get("deathlev")
            meta["xlog_maxlvl"] = xlog.get("maxlvl")
            meta["xlog_turns"] = xlog.get("turns")
            meta["xlog_dnum"] = xlog.get("deathdnum")
        meta["wall_seconds"] = round(time.time() - t0, 1)
        with open(os.path.join(outdir, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2)
        logf.close()
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--id", default="g0")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    meta = run_one(args.outdir, args.id, args.verbose)
    print(json.dumps(meta, indent=2))
    sys.exit(0 if meta["result"] == "minetown" else 1)
