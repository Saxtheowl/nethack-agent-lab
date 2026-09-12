#!/usr/bin/env python3
"""Summarise a batch of real games played by the port.

The question is not "how many keystrokes matched" - that is the replay gate.
It is how far the bot actually gets when nothing is pinned and nobody helps:
depth, turns, score, how it died, and whether any game **ascended**.

Outcomes are read from NetHack's own xlogfile where possible, matched by the
per-slot player name and a time window, because that record is written by the
game rather than by the bot.  The bot's log supplies the rest.

    tools/ascend_summary.py OUT [--xlog PATH]
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINAL = re.compile(r'final state: dlvl=(\S+) turn=(\d+) score=(\d+) hp=(-?\d+)')


def xlog_rows(path):
    rows = []
    if not os.path.exists(path):
        return rows
    for line in open(path, errors='replace'):
        f = dict(kv.split('=', 1) for kv in line.strip().split(':')
                 if '=' in kv)
        if f:
            rows.append(f)
    return rows


def pick(rows, name, lo, hi):
    """The player's xlogfile entry whose endtime falls in this game's window."""
    best = None
    for f in rows:
        if f.get('name') != name:
            continue
        try:
            end = int(f.get('endtime', -1))
        except ValueError:
            continue
        if lo - 5 <= end <= hi + 5:
            best = f
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--xlog',
                    default=os.path.join(ROOT, 'upstream', 'nh343', 'var',
                                         'xlogfile'))
    a = ap.parse_args()
    rows = xlog_rows(a.xlog)
    games = []
    for d in sorted(os.listdir(a.out)):
        gd = os.path.join(a.out, d)
        if not (d.startswith('game') and os.path.isdir(gd)):
            continue
        rec = {'game': d}
        log = os.path.join(gd, 'run.log')
        if os.path.exists(log):
            tail = ""
            with open(log, errors='replace') as fh:
                for line in fh:
                    if 'final state:' in line:
                        tail = line
            m = FINAL.search(tail)
            if m:
                rec.update(dlvl=m.group(1), turns=int(m.group(2)),
                           score=int(m.group(3)), hp=int(m.group(4)))
            rec['actions'] = sum(1 for line in open(log, errors='replace')
                                 if 'Performing action' in line)
        try:
            rec['wall_seconds'] = int(open(os.path.join(gd, 'wall_seconds'))
                                      .read().strip())
        except (IOError, ValueError):
            rec['wall_seconds'] = None
        try:
            name = open(os.path.join(gd, 'player')).read().strip()
        except IOError:
            name = None
        if name and rec['wall_seconds']:
            mt = int(os.path.getmtime(os.path.join(gd, 'run.log')))
            entry = pick(rows, name, mt - rec['wall_seconds'], mt)
            if entry:
                rec['xlog'] = {k: entry.get(k) for k in
                               ('death', 'turns', 'points', 'maxlvl', 'hp',
                                'role', 'race')}
                rec['ascended'] = entry.get('death') == 'ascended'
        games.append(rec)

    with open(os.path.join(a.out, 'summary.json'), 'w') as fh:
        fh.write(json.dumps(games, indent=1, sort_keys=True) + '\n')

    hdr = '%-8s %-8s %-8s %-8s %-7s %-7s %s' % (
        'game', 'dlvl', 'turns', 'score', 'hp', 'wall_s', 'death (xlogfile)')
    print(hdr)
    print('-' * len(hdr))
    asc = 0
    for g in games:
        x = g.get('xlog') or {}
        if g.get('ascended'):
            asc += 1
        print('%-8s %-8s %-8s %-8s %-7s %-7s %s'
              % (g['game'], g.get('dlvl', '?'), g.get('turns', '?'),
                 g.get('score', '?'), g.get('hp', '?'),
                 g.get('wall_seconds', '?'), x.get('death', '-')))
    done = [g for g in games if g.get('turns')]
    if done:
        turns = sorted(g['turns'] for g in done)
        scores = sorted(g.get('score', 0) for g in done)
        mid = len(turns) // 2
        print()
        print('games with an outcome: %d/%d' % (len(done), len(games)))
        print('median turns %d, max %d' % (turns[mid], turns[-1]))
        print('median score %d, max %d' % (scores[mid], scores[-1]))
    print('ASCENSIONS: %d' % asc)


if __name__ == '__main__':
    main()
