#!/usr/bin/env python3
"""Style of a slot's NEXT game, after a death.

  python3 scripts/next_style.py <slot> [--dry-run]

User plan 2026-09-27: reach TARGET games per style (2 x tariru, tariru_v2,
astra, wish_abuser over the 8 slots), replacing progressively at deaths:
- games in progress never change style;
- the dying slot keeps its style (sticky) unless that style has more than
  TARGET slots while another style has fewer: then it takes the style that
  lacks the most (queue order breaks ties: wish_abuser first);
- slot 1 always stays in the Tariru family (tariru or tariru_v2).
State and history: .runtime/style-plan.json.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / '.runtime/style-plan.json'
ORDER = ['wish_abuser', 'tariru_v2', 'tariru', 'astra']
TARGET = 2
# user decision 2026-09-27 ~19h: no more Tariru styles: 6 astra + 2 wish_abuser
TARGETS = {'astra': 8, 'wish_abuser': 0, 'tariru': 0, 'tariru_v2': 0}  # 27/09 ~22h45: all slots astra


def slot_style(s):
    try:
        return json.loads((ROOT / f'.runtime/slot-{s}.json').read_text()).get('style')
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def choose(slot, styles):
    current = styles.get(slot) or 'astra'
    count = {st: 0 for st in ORDER}
    for s, st in styles.items():
        if st in count:
            count[st] += 1
    if count.get(current, 0) <= TARGETS.get(current, 0):
        return current
    lacking = [st for st in ORDER if st != current and count[st] < TARGETS[st]]
    if not lacking:
        return 'astra' if TARGETS.get(current, 0) == 0 else current
    return max(lacking, key=lambda st: (TARGETS[st] - count[st], -ORDER.index(st)))


def main():
    slot = sys.argv[1]
    dry = '--dry-run' in sys.argv
    styles = {str(s): slot_style(s) for s in range(1, 9)}
    style = choose(slot, styles)
    if not dry:
        plan = json.loads(PLAN.read_text()) if PLAN.exists() else {'history': []}
        plan['rule'] = '8 astra : tous les emplacements en style Astra (décision utilisateur 27/09 22h45)'
        plan['queue'] = []
        if style != styles.get(slot):
            plan['history'].append({'slot': slot, 'style': style, 'from': styles.get(slot), 't': time.time()})
        PLAN.write_text(json.dumps(plan, indent=1))
    print(style)


if __name__ == '__main__':
    main()
