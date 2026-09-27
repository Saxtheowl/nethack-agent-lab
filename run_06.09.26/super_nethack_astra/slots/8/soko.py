#!/usr/bin/env python3
"""slots/8/soko.py: Sokoban solver for the board displayed in slot 8.

Reads the current screen (NH_SLOT=8), treats box-drawing chars as walls,
'0' boulders, '^' holes, '<' '>' and items as floor. Player moves are
orthogonal only (safe in Sokoban). Best-first search on pushes; prints the
push list as "X Y dir" lines (boulder position before the push, dir in
l/r/u/d) plus the full keystroke plan (digits 2468).

Usage: python3 slots/8/soko.py [--goal X,Y] [--max N]
"""
import argparse, heapq, os, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
os.environ.setdefault('NH_SLOT', '8')
import session

WALLS = set('│─┌┐└┘├┤┬┴┼|-')
DIRS = {'l': (-1, 0, '4'), 'r': (1, 0, '6'), 'u': (0, -1, '8'), 'd': (0, 1, '2')}


def parse(rows, hero):
    floor, boulders, holes = set(), set(), set()
    stairs = None
    for y in range(11, 32):
        row = rows[y] if y < len(rows) else ''
        for x in range(1, 80):
            c = row[x] if x < len(row) else ' '
            if c == ' ' or c in WALLS:
                continue
            p = (x, y)
            if c == '0':
                boulders.add(p); floor.add(p)
            elif c == '^':
                holes.add(p); floor.add(p)
            else:
                floor.add(p)
                if c == '<':
                    stairs = p
    floor.add(hero)
    return floor, boulders, holes, stairs


def reach(start, floor, boulders, holes):
    seen = {start: None}
    q = collections.deque([start])
    while q:
        c = q.popleft()
        for d in DIRS.values():
            n = (c[0] + d[0], c[1] + d[1])
            if n in seen or n not in floor or n in boulders or n in holes:
                continue
            seen[n] = c
            q.append(n)
    return seen


def path(seen, goal):
    out = []
    while seen[goal] is not None:
        prev = seen[goal]
        for k, d in DIRS.items():
            if (prev[0] + d[0], prev[1] + d[1]) == goal:
                out.append(d[2])
        goal = prev
    return ''.join(reversed(out))


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


def solve(hero, floor, boulders, holes, goal, maxn):
    live = live_cells(floor, holes)
    start = (frozenset(boulders), frozenset(holes))
    def key(b, h, p):
        r = reach(p, floor, b, h)
        return (b, h, min(r)), r
    k0, r0 = key(start[0], start[1], hero)
    def done(b, h, r):
        return goal in r
    # f = holes remaining that block the goal path estimate: just len(h)
    cnt = 0
    heap = [(len(start[1]), 0, cnt, start[0], start[1], hero, [])]
    seen = {k0}
    while heap:
        f, g, _, b, h, p, plan = heapq.heappop(heap)
        r = reach(p, floor, b, h)
        if done(b, h, r):
            return plan
        if g > maxn:
            continue
        for bx in b:
            for dn, d in DIRS.items():
                behind = (bx[0] - d[0], bx[1] - d[1])
                tgt = (bx[0] + d[0], bx[1] + d[1])
                if behind not in r or tgt not in floor or tgt in b:
                    continue
                nb, nh = set(b), set(h)
                nb.discard(bx)
                if tgt in h:
                    nh.discard(tgt)
                else:
                    if tgt not in live:
                        continue
                    nb.add(tgt)
                nb, nh = frozenset(nb), frozenset(nh)
                k, _ = key(nb, nh, bx)
                if k in seen:
                    continue
                seen.add(k)
                cnt += 1
                heapq.heappush(heap, (len(nh) * 3 + (g + 1) * 0.2, g + 1, cnt, nb, nh, bx,
                                      plan + [(bx, dn, behind)]))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--goal')
    ap.add_argument('--max', type=int, default=200)
    a = ap.parse_args()
    rows = session.screen().splitlines()
    out = session.tmux('display-message', '-p', '-t', session.TARGET, '#{cursor_x},#{cursor_y}').stdout
    hero = tuple(map(int, out.strip().split(',')))
    floor, boulders, holes, stairs = parse(rows, hero)
    goal = tuple(map(int, a.goal.split(','))) if a.goal else stairs
    print(f'hero {hero} goal {goal} boulders {len(boulders)} holes {len(holes)}')
    plan = solve(hero, floor, boulders, holes, goal, a.max)
    if plan is None:
        print('NO SOLUTION'); return
    b, h, p = set(boulders), set(holes), hero
    keys = []
    for bx, dn, behind in plan:
        r = reach(p, floor, b, h)
        walk = path(r, behind)
        d = DIRS[dn]
        tgt = (bx[0] + d[0], bx[1] + d[1])
        b.discard(bx)
        if tgt in h: h.discard(tgt)
        else: b.add(tgt)
        p = bx
        keys.append((bx, dn, walk))
        print(f'{bx[0]} {bx[1]} {dn}   walk:{walk} push:{d[2]}')
    print(len(plan), 'pushes')


if __name__ == '__main__':
    main()
