#!/usr/bin/env python3
"""Style of a slot's NEXT game, after a death (user plan 2026-09-27).

  python3 scripts/next_style.py <slot> [--dry-run]

The first death after the plan was set switches that slot to tariru_v2, the
next death (another slot) to wish_abuser; after that a slot keeps its style
(styles are sticky per slot). State: .runtime/style-plan.json.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / '.runtime/style-plan.json'


def main():
    slot = sys.argv[1]
    dry = '--dry-run' in sys.argv
    plan = json.loads(PLAN.read_text())
    try:
        current = json.loads((ROOT / f'.runtime/slot-{slot}.json').read_text()).get('style')
    except FileNotFoundError:
        current = None
    assigned = {h['slot'] for h in plan['history']}
    # slot 1 always plays a Tariru style (user rule): it may take tariru_v2,
    # never wish_abuser
    if plan['queue'] and slot not in assigned and not (slot == '1' and plan['queue'][0] == 'wish_abuser'):
        style = plan['queue'][0]
        if not dry:
            plan['queue'].pop(0)
            plan['history'].append({'slot': slot, 'style': style, 'from': current, 't': time.time()})
            PLAN.write_text(json.dumps(plan, indent=1))
    else:
        style = current or ('tariru' if slot == '1' else 'astra')
    print(style)


if __name__ == '__main__':
    main()
