#!/usr/bin/env python3
"""Run baseline and Jev variants under the same seeds and conditions."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
DEFAULT_BASE = ROOT.parent / "claude"
MODES = ("baseline", "raw", "primitives", "shadow")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", default="42001,42002,42003")
    ap.add_argument("--modes", default=",".join(MODES))
    ap.add_argument("--goal", default="minetown")
    ap.add_argument("--max-turns", type=int, default=30000)
    ap.add_argument("--max-seconds", type=int, default=7200)
    ap.add_argument("--bothack-base", default=os.environ.get(
        "BOTHACK_BASE", str(DEFAULT_BASE)))
    ap.add_argument("--no-assist", action="store_true")
    ap.add_argument("--jev-offline", action="store_true",
                    help="plumbing test only; never use as a Jev result")
    args = ap.parse_args(argv)
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    modes = [x.strip() for x in args.modes.split(",") if x.strip()]
    unknown = set(modes) - set(MODES)
    if unknown:
        ap.error("unknown modes: %s" % sorted(unknown))
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    plan = {"seeds": seeds, "modes": modes, "goal": args.goal,
            "max_turns": args.max_turns, "max_seconds": args.max_seconds,
            "assisted": not args.no_assist,
            "bothack_base": str(Path(args.bothack_base).resolve())}
    (out / "matrix.json").write_text(json.dumps(plan, indent=1) + "\n")
    scripts = {
        "raw": ROOT / "JEV_RAW" / "run.py",
        "primitives": ROOT / "JEV_PRIMITIVES" / "run.py",
        "shadow": ROOT / "JEV_SHADOW" / "run.py",
    }
    for seed in seeds:
        for mode in modes:
            game_out = out / mode / ("seed-%d" % seed)
            common = ["--out", str(game_out), "--seed", str(seed),
                      "--goal", args.goal, "--max-turns", str(args.max_turns),
                      "--max-seconds", str(args.max_seconds)]
            if args.no_assist:
                common.append("--no-assist")
            if mode == "baseline":
                cmd = [sys.executable, "-m", "nhbot.rungame", *common]
                cwd = args.bothack_base
            else:
                cmd = [sys.executable, str(scripts[mode]), *common,
                       "--bothack-base", args.bothack_base]
                if args.jev_offline:
                    cmd.append("--jev-offline")
                cwd = str(ROOT)
            print("RUN", mode, seed, flush=True)
            rc = subprocess.call(cmd, cwd=cwd)
            if rc:
                print("FAILED", mode, seed, "rc", rc, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

