#!/usr/bin/env python3
"""Summarise the NetHack xlogfile: one table per bot (by player name)."""
import sys
from collections import defaultdict


def parse(path):
    games = []
    with open(path, errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = {}
            for kv in line.split(':'):
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    d[k] = v
            games.append(d)
    return games


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'upstream/nh343/var/xlogfile'
    by_bot = defaultdict(list)
    for g in parse(path):
        by_bot[g.get('name', '?')].append(g)
    for name, gs in sorted(by_bot.items()):
        pts = [int(g['points']) for g in gs]
        turns = [int(g['turns']) for g in gs]
        maxlvl = [int(g['maxlvl']) for g in gs]
        asc = [g for g in gs if 'ascended' in g.get('death', '')]
        print("=== %s: %d games" % (name, len(gs)))
        print("    points  median %6d  max %8d" % (sorted(pts)[len(pts)//2],
                                                   max(pts)))
        print("    turns   median %6d  max %8d" % (sorted(turns)[len(turns)//2],
                                                   max(turns)))
        print("    maxlvl  median %6d  max %8d" %
              (sorted(maxlvl)[len(maxlvl)//2], max(maxlvl)))
        print("    ascensions: %d" % len(asc))
        deaths = defaultdict(int)
        for g in gs:
            deaths[g.get('death', '?')[:60]] += 1
        for d, c in sorted(deaths.items(), key=lambda kv: -kv[1])[:8]:
            print("      %3d  %s" % (c, d))


if __name__ == '__main__':
    main()
