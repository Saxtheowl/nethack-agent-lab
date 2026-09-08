#!/usr/bin/env python3
"""Compare the action sequences of the original and the port on the same
replayed game, and print the first differences with the port's reasoning."""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CLJ_ACTION_RE = re.compile(r'Performing action: #bothack\.actions\.(\w+)\{')

CLJ_TO_PY = {
    'Discoveries': 'discoveries', 'Inventory': 'inventory', 'Look': 'look',
    'FarLook': 'farlook', 'Search': 'search', 'Move': 'move',
    'PickUp': 'pickup', 'Attack': 'attack', 'Wield': 'wield',
    'Wear': 'wear', 'PutOn': 'puton', 'Remove': 'remove',
    'TakeOff': 'takeoff', 'DropSingle': 'dropsingle', 'Eat': 'eat',
    'Quaff': 'quaff', 'Read': 'read', 'Engrave': 'engrave', 'Apply': 'apply',
    'Kick': 'kick', 'Open': 'open', 'Close': 'close', 'Ascend': 'ascend',
    'Descend': 'descend', 'Pray': 'pray', 'Autotravel': 'autotravel',
    'Repeated': 'repeated', 'ZapWand': 'zapwand', 'Wait': 'wait',
    'Sit': 'sit', 'Loot': 'loot', 'Dip': 'dip', 'Name': 'name',
    'Call': 'call', 'Throw': 'throw', 'Enhance': 'enhance', 'Pay': 'pay',
    'Chat': 'chat', 'Offer': 'offer', 'Rub': 'rub', 'Wipe': 'wipe',
    'Quiver': 'quiver', 'ForceLock': 'forcelock', 'FarmAttack': 'farmattack',
}


def clj_actions(path):
    out = []
    with open(path, errors='replace') as f:
        for line in f:
            m = CLJ_ACTION_RE.search(line)
            if m:
                out.append(CLJ_TO_PY.get(m.group(1), m.group(1).lower()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('orig_log')
    ap.add_argument('port_actions')
    ap.add_argument('--max-diffs', type=int, default=10)
    a = ap.parse_args()
    orig = clj_actions(a.orig_log)
    port = []
    with open(a.port_actions) as f:
        for line in f:
            t, _, reason = line.rstrip("\n").partition("\t")
            port.append((t, reason))
    import difflib
    pseq = [t for t, _ in port]
    sm = difflib.SequenceMatcher(None, orig, pseq, autojunk=False)
    matched = sum(b.size for b in sm.get_matching_blocks())
    n = min(len(orig), len(port))
    diffs = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        diffs += 1
        if diffs <= a.max_diffs:
            print("%s original[%d:%d]=%s  port[%d:%d]=%s"
                  % (tag, i1, i2, orig[i1:i2][:6], j1, j2, pseq[j1:j2][:6]))
            if j1 < len(port):
                print("     port reason: %s" % port[j1][1][:200])
    print("\naligned action agreement: %d/%d (%.1f%%) - original %d actions, "
          "port %d, %d divergent regions"
          % (matched, max(len(orig), len(pseq)),
             100.0 * matched / max(1, max(len(orig), len(pseq))),
             len(orig), len(pseq), diffs))
    # longest common prefix
    lcp = 0
    while lcp < n and orig[lcp] == port[lcp][0]:
        lcp += 1
    print("identical action prefix: %d actions" % lcp)


if __name__ == '__main__':
    main()
