#!/usr/bin/env python3
"""slots/8/soko2.py: incremental Sokoban planner for slot 8.

Finds the SHORTEST push sequence (BFS over pushes, player moves orthogonal)
that ends with one more hole filled, from the current screen. Prints the
pushes grouped per boulder as `sk` commands ("X Y dirs").

Usage: python3 slots/8/soko2.py [--depth N] [--hidden X,Y ...] [--avoid X,Y ...]
"""
import argparse, collections, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts'))
os.environ.setdefault('NH_SLOT', '8')
import session

WALLS = set('│─┌┐└┘├┤┬┴┼')
DIRS = {'l': (-1, 0), 'r': (1, 0), 'u': (0, -1), 'd': (0, 1)}


def reach(start, floor, blocked):
    seen = {start}
    q = collections.deque([start])
    while q:
        c = q.popleft()
        for d in DIRS.values():
            n = (c[0] + d[0], c[1] + d[1])
            if n not in seen and n in floor and n not in blocked:
                seen.add(n); q.append(n)
    return seen


def live_cells(floor, holes):
    live = set(holes)
    q = collections.deque(holes)
    while q:
        t = q.popleft()
        for d in DIRS.values():
            s = (t[0] - d[0], t[1] - d[1])
            pl = (t[0] - 2 * d[0], t[1] - 2 * d[1])
            if s in floor and pl in floor and s not in live:
                live.add(s); q.append(s)
    return live


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--depth', type=int, default=14)
    ap.add_argument('--hidden', action='append', default=[])
    ap.add_argument('--maxstates', type=int, default=400000)
    ap.add_argument('--only', help='xmin,ymin,xmax,ymax: only push boulders inside this box')
    a = ap.parse_args()
    rows = session.screen().splitlines()
    out = session.tmux('display-message', '-p', '-t', session.TARGET, '#{cursor_x},#{cursor_y}').stdout
    hero = tuple(map(int, out.strip().split(',')))
    floor, boulders, holes = set(), set(), set()
    for y in range(11, 32):
        row = rows[y] if y < len(rows) else ''
        for x in range(1, 80):
            c = row[x] if x < len(row) else ' '
            if c == ' ' or c in WALLS:
                continue
            floor.add((x, y))
            if c == '0': boulders.add((x, y))
            if c == '^': holes.add((x, y))
    for h in a.hidden:
        holes.add(tuple(map(int, h.split(','))))
    floor.add(hero)
    live = live_cells(floor, holes)
    box = tuple(map(int, a.only.split(','))) if a.only else None
    start = frozenset(boulders)
    def norm(b, p):
        r = reach(p, floor, b | holes)
        return min(r), r
    k0, _ = norm(start, hero)
    seen = {(start, k0)}
    q = collections.deque([(start, hero, [])])
    n = 0
    while q:
        b, p, plan = q.popleft()
        if len(plan) >= a.depth:
            continue
        r = reach(p, floor, b | holes)
        for bx in b:
            if box and not (box[0] <= bx[0] <= box[2] and box[1] <= bx[1] <= box[3]):
                continue
            for dn, d in DIRS.items():
                behind = (bx[0] - d[0], bx[1] - d[1])
                tgt = (bx[0] + d[0], bx[1] + d[1])
                if behind not in r or tgt not in floor or tgt in b:
                    continue
                np_ = plan + [(bx, dn)]
                if tgt in holes:
                    # success: print grouped plan
                    groups = []
                    pos = {}
                    for (s, dd) in np_:
                        key = pos.pop(s, s)
                        t = (s[0] + DIRS[dd][0], s[1] + DIRS[dd][1])
                        if groups and groups[-1][2] == s:
                            groups[-1][1] += dd; groups[-1][2] = t
                        else:
                            groups.append([s, dd, t])
                    for s, dirs, _ in groups:
                        print(f'{s[0]} {s[1]} {dirs}')
                    print(f'# pushes={len(np_)} states={n}')
                    return
                if tgt not in live:
                    continue
                nb = frozenset((b - {bx}) | {tgt})
                k, _ = norm(nb, bx)
                if (nb, k) in seen:
                    continue
                seen.add((nb, k))
                n += 1
                if n > a.maxstates:
                    print('# too many states'); return
                q.append((nb, bx, np_))
    print('# no solution within depth')


if __name__ == '__main__':
    main()
