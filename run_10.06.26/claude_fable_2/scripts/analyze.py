#!/usr/bin/env python3
"""Analyse rapide d'un run : causes, trails, écrans des échecs."""

import json
import sys
from collections import Counter
from pathlib import Path

run = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/iter-009")
mode = sys.argv[2] if len(sys.argv) > 2 else "summary"

rows = [json.loads(l) for l in (run / "results.jsonl").open()]
rows.sort(key=lambda r: r["episode"])
succ = sum(r["success"] for r in rows)
print(f"{run.name}: {succ}/{len(rows)} = {succ/len(rows):.1%}")
print("causes:", dict(Counter(r["failure_cause"] for r in rows if not r["success"])))
succ_steps = sorted(r["steps"] for r in rows if r["success"])
print("steps succès:", succ_steps)

if mode in ("fail", "full"):
    for r in rows:
        if r["success"]:
            continue
        p = r.get("policy", {})
        tr = p.get("trail", [])
        labs = Counter(t[1] for t in tr)
        print(
            f"\n== ep {r['episode']} {r['failure_cause']} steps={r['steps']} "
            f"turn={p.get('turn')} hp={p.get('hp')}/{p.get('hpmax')} xl={p.get('xp_level')}"
        )
        print("   trail:", dict(labs.most_common(8)))
        print("   msgs:", p.get("recent_messages", [])[-4:])
        if mode == "full":
            print("   levels:", json.dumps(p.get("levels", {})))
            print(p.get("screen", ""))
