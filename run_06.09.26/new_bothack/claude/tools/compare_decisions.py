#!/usr/bin/env python3
"""Align the original's decisions with the port's and name the first that differs.

A keystroke byte offset says *where* two runs part company; it does not say
*which decision* went wrong.  The original logs every chosen action together
with its `with-reason` stack at DEBUG level, and the port records the same pair
(tools/replay_compare.py --actions-out), so the two decision streams can be
aligned directly.  The first differing pair names the function to look at -
"searching walls" vs "fidgeting to make peacefuls move" is a lead; byte 35830
is not.

    tools/compare_decisions.py ORIG_BOTHACK.LOG PORT_ACTIONS.TSV [-n 6]

Action *indices* are comparable here (unlike keystroke offsets) only because
both sides count one entry per chosen action; `Repeated` writes one trigger, so
it is one action on both sides.
"""
import argparse
import re
import sys

ACTION_RE = re.compile(r'Performing action: #bothack\.actions\.(\w+)')
# Clojure's record printing for the action follows the type name; the reasons
# come on the next lines as a printed vector.
REASONS_RE = re.compile(r'^\s*\[(.*)\]\s*$')


def orig_decisions(path):
    """(type, reasons) per action, in order, from the original's DEBUG log."""
    out = []
    pending = None
    for line in open(path, errors='replace'):
        m = ACTION_RE.search(line)
        if m:
            if pending is not None:
                out.append(pending)
            pending = [_snake(m.group(1)), []]
            continue
        if pending is None:
            continue
        if line.strip() == 'reasons:':
            pending.append('await')
            continue
        if pending[-1] == 'await':
            pending.pop()
            m2 = REASONS_RE.match(line)
            if m2:
                pending[1] = [s.strip().strip('"')
                              for s in re.findall(r'"((?:[^"\\]|\\.)*)"',
                                                  m2.group(1))]
    if pending is not None:
        out.append(pending)
    return [(t, r) for t, r, *_ in out]


def _snake(name):
    """bothack.actions.FarLook -> farlook, as (typekw action) prints it."""
    return re.sub(r'(?<!^)(?=[A-Z])', '', name).lower()


def port_decisions(path):
    out = []
    for line in open(path, errors='replace'):
        t, _, reasons = line.rstrip('\n').partition('\t')
        out.append((t, [s.strip() for s in reasons.split(' | ') if s.strip()]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('orig_log')
    ap.add_argument('port_actions')
    ap.add_argument('-n', '--context', type=int, default=6)
    a = ap.parse_args()

    o = orig_decisions(a.orig_log)
    p = port_decisions(a.port_actions)
    print('original decisions: %d' % len(o))
    print('port decisions    : %d' % len(p))

    n = min(len(o), len(p))
    i = 0
    while i < n and o[i][0] == p[i][0]:
        i += 1
    if i == n:
        print('the shorter decision stream is a prefix of the longer '
              '(%d actions agree)' % n)
        return 0
    print('\nfirst differing decision: index %d (%.1f%% in)'
          % (i, 100.0 * i / n))
    lo = max(0, i - a.context)
    for j in range(lo, min(n, i + a.context + 1)):
        mark = '>>' if j == i else '  '
        print('%s %5d  orig %-12s %s' % (mark, j, o[j][0],
                                         ' | '.join(o[j][1])[:110]))
        print('%s %5s  port %-12s %s' % (mark, '', p[j][0],
                                         ' | '.join(p[j][1])[:110]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
