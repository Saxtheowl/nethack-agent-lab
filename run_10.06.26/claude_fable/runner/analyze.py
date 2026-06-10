"""Summarize failures of a batch: death causes, last positions, stuck patterns."""
import json
import os
import sys
from collections import Counter

def main(batchdir):
    rows = []
    for name in sorted(os.listdir(batchdir)):
        d = os.path.join(batchdir, name)
        mp = os.path.join(d, "meta.json")
        if not os.path.isdir(d) or not os.path.exists(mp):
            continue
        with open(mp) as f:
            meta = json.load(f)
        rows.append((name, meta, d))

    n_ok = sum(1 for _, m, _ in rows if m.get("result") == "minetown")
    print(f"games={len(rows)} minetown={n_ok} rate={100.0*n_ok/max(1,len(rows)):.1f}%\n")
    print(f"{'game':8} {'result':12} {'branch':7} {'dlvl':4} {'turn':6} {'ticks':6} death")
    for name, m, d in rows:
        print(f"{name:8} {str(m.get('result')):12} {str(m.get('branch')):7} "
              f"{str(m.get('dlvl')):4} {str(m.get('turn')):6} {str(m.get('ticks')):6} "
              f"{m.get('death')}")
    print("\n-- failures detail --")
    for name, m, d in rows:
        if m.get("result") == "minetown":
            continue
        print(f"\n### {name}: {m.get('result')} ({m.get('branch')}:{m.get('dlvl')} T={m.get('turn')}) {m.get('death')}")
        log = os.path.join(d, "bot.log")
        if os.path.exists(log):
            with open(log) as f:
                lines = f.readlines()
            for l in lines[-8:]:
                print("   ", l.rstrip())

if __name__ == "__main__":
    main(sys.argv[1])
