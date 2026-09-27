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


def slot_style(s):
    try:
        return json.loads((ROOT / f'.runtime/slot-{s}.json').read_text()).get('style')
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def choose(slot, styles):
    current = styles.get(slot) or ('tariru' if slot == '1' else 'astra')
    count = {st: 0 for st in ORDER}
    for s, st in styles.items():
        if st in count:
            count[st] += 1
    allowed = ['tariru', 'tariru_v2'] if slot == '1' else ORDER
    if slot == '1' and current not in allowed:
        current = 'tariru'
    if count.get(current, 0) <= TARGET and current in allowed:
        # keep it, unless a style is still missing entirely and ours is at target... keep sticky
        return current
    lacking = [st for st in ORDER if st in allowed and st != current and count[st] < TARGET]
    if not lacking:
        return current
    return max(lacking, key=lambda st: (TARGET - count[st], -ORDER.index(st)))


def main():
    slot = sys.argv[1]
    dry = '--dry-run' in sys.argv
    styles = {str(s): slot_style(s) for s in range(1, 9)}
    style = choose(slot, styles)
    if not dry:
        plan = json.loads(PLAN.read_text()) if PLAN.exists() else {'history': []}
        plan['rule'] = f'{TARGET} parties par style (tariru, tariru_v2, astra, wish_abuser), remplacement progressif aux morts'
        plan['queue'] = []
        if style != styles.get(slot):
            plan['history'].append({'slot': slot, 'style': style, 'from': styles.get(slot), 't': time.time()})
        PLAN.write_text(json.dumps(plan, indent=1))
    print(style)


if __name__ == '__main__':
    main()
