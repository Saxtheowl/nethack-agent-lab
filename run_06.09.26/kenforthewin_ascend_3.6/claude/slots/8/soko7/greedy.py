#!/usr/bin/env python3
"""Greedy subgoal Sokoban solver: repeatedly BFS (in push space) for the shortest push
sequence that fills one more hole; with backtracking over the first K alternatives if a
later stage fails. Map: # wall . floor 0 boulder @ player ^ hole. Orthogonal moves only.
Prints pushes 'x y dir' (map coords, boulder position before the push)."""
import sys
from collections import deque
lines = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip('\n')]
MAXN = int(sys.argv[2]) if len(sys.argv) > 2 else 400000
W = max(len(l) for l in lines); g = [l.ljust(W, '#') for l in lines]
walls, holes, B = set(), set(), set(); player = None
for y, l in enumerate(g):
    for x, c in enumerate(l):
        if c == '#' or c == ' ': walls.add((x, y))
        elif c == '^': holes.add((x, y))
        elif c == '0': B.add((x, y))
        elif c == '@': player = (x, y)
D = {'l': (-1, 0), 'r': (1, 0), 'u': (0, -1), 'd': (0, 1)}
floor = {(x, y) for y in range(len(g)) for x in range(W) if (x, y) not in walls}


# live squares: a boulder there can still be pushed to some hole (ignoring other boulders)
live = set(holes); dq = deque(holes)
while dq:
    n = dq.popleft()
    for dx, dy in D.values():
        c = (n[0] - dx, n[1] - dy); pl = (c[0] - dx, c[1] - dy)
        if c in floor and pl in floor and c not in live:
            live.add(c); dq.append(c)


def reach(p, bs, hs):
    seen = {p}; q = deque([p])
    while q:
        x, y = q.popleft()
        for dx, dy in D.values():
            n = (x + dx, y + dy)
            if n in seen or n not in floor or n in bs or n in hs: continue
            seen.add(n); q.append(n)
    return seen


def corner_dead(t, hs):
    # a boulder on a non-hole floor square in a wall corner can never move again
    if t in hs: return False
    wl = lambda c: c not in floor
    x, y = t
    return ((wl((x - 1, y)) or wl((x + 1, y))) and (wl((x, y - 1)) or wl((x, y + 1))))


def stage(bs, hs, p):
    """BFS for pushes until one hole is filled. Returns list of (path, newstate)."""
    start = (bs, hs)
    r = reach(p, bs, hs)
    key0 = (bs, min(r))
    prev = {key0: None}
    q = deque([(bs, hs, p, key0)])
    sols = []
    n = 0
    while q and n < MAXN:
        bs_, hs_, p_, key = q.popleft()
        r = reach(p_, bs_, hs_)
        for b in bs_:
            for dn, (dx, dy) in D.items():
                pp = (b[0] - dx, b[1] - dy); t = (b[0] + dx, b[1] + dy)
                if pp not in r or t not in floor or t in bs_: continue
                nb = set(bs_); nb.discard(b); nh = set(hs_)
                filled = t in nh
                if filled: nh.discard(t)
                else:
                    if t not in live: continue
                    nb.add(t)
                nb = frozenset(nb); nh = frozenset(nh)
                if len(nb) < len(nh): continue
                nk = (nb, min(reach(b, nb, nh)))
                if nk in prev: continue
                prev[nk] = (key, (b[0], b[1], dn))
                n += 1
                if filled:
                    path = []; k = nk
                    while prev[k] is not None:
                        k, push = prev[k]; path.append(push)
                    sols.append((path[::-1], (nb, nh, b)))
                    if len(sols) >= 2: return sols
                    continue
                q.append((nb, nh, b, nk))
    return sols


def solve(bs, hs, p, depth=0):
    if not hs: return []
    st = stage(bs, hs, p)
    print('depth', depth, 'holes left', len(hs), 'stage sols', [x[0] for x in st], flush=True)
    for path, (nb, nh, np_) in st:
        rest = solve(nb, nh, np_, depth + 1)
        if rest is not None: return path + rest
    return None


res = solve(frozenset(B), frozenset(holes), player)
if res is None:
    print('no solution'); sys.exit(1)
print(len(res), 'pushes')
for x, y, d in res: print(x, y, d)
