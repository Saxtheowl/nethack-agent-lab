#!/usr/bin/env python3
"""Aggregate result.json files from a run_matrix output directory."""
import argparse
import json
from pathlib import Path
import statistics


def mean(values):
    values = [v for v in values if isinstance(v, (int, float))]
    return round(statistics.mean(values), 2) if values else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.path)
    groups = {}
    for path in root.glob("*/seed-*/result.json"):
        mode = path.parent.parent.name
        groups.setdefault(mode, []).append(json.loads(path.read_text()))
    report = {}
    for mode, games in sorted(groups.items()):
        report[mode] = {
            "games": len(games),
            "goal_reached": sum(g.get("outcome") == "goal_reached"
                                for g in games),
            "outcomes": {name: sum(g.get("outcome") == name for g in games)
                         for name in sorted(set(g.get("outcome") for g in games))},
            "mean_max_depth": mean([g.get("max_depth") for g in games]),
            "mean_turns": mean([g.get("turns") for g in games]),
            "mean_elapsed_s": mean([g.get("elapsed_s") for g in games]),
            "jev_calls": sum((g.get("jev") or {}).get("calls", 0) for g in games),
            "jev_cost_usd": round(sum((g.get("jev") or {}).get("cost_usd", 0)
                                      for g in games), 8),
            "mean_jev_latency_ms": mean([
                (g.get("jev") or {}).get("mean_latency_ms") for g in games]),
        }
    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    print("mode         games goal depth  turns  seconds calls cost_usd latency_ms outcomes")
    for mode, row in report.items():
        print("%-12s %5d %4d %5s %6s %8s %5d %8.5f %10s %s" % (
            mode, row["games"], row["goal_reached"], row["mean_max_depth"],
            row["mean_turns"], row["mean_elapsed_s"], row["jev_calls"],
            row["jev_cost_usd"], row["mean_jev_latency_ms"], row["outcomes"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

