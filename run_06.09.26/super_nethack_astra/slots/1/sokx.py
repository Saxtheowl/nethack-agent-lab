#!/usr/bin/env python3
"""slots/1/sokx.py "X,Y:pushes" ... : execute Sokoban push groups one key at a time.
Walks (BFS over the current screen, avoiding boulders/holes/monsters, orthogonal+diagonal
except squeezing between boulders is not attempted) to the square behind the boulder, then pushes.
After every key: verifies hero position, boulder moved, no HP loss, no monster adjacent, no prompt.
Run with: slots/1/w python3 sokx.py ... (NH_SLOT=1)."""
import re, subprocess, sys, collections, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
D = {'l': (-1, 0), 'r': (1, 0), 'u': (0, -1), 'd': (0, 1)}
KEY = {(0, -1): '8', (1, 0): '6', (0, 1): '2', (-1, 0): '4', (1, -1): '9', (1, 1): '3', (-1, 1): '1', (-1, -1): '7'}

def run(args):
    return subprocess.run(['python3', 'scripts/session.py'] + args, cwd=ROOT, capture_output=True, text=True).stdout

def parse(out):
    rows = {}
    for l in out.split('\n'):
        m = re.match(r'^(\d\d) │(.*)', l)
        if m:
            rows[int(m[1])] = m[2]
    cells = {}
    for y, r in rows.items():
        for i, c in enumerate(r):
            cells[(i + 1, y)] = c
    m = re.search(r'Neighbors of @\((\d+),(\d+)\)', out)
    hero = (int(m[1]), int(m[2])) if m else None
    hp = re.search(r'HP:(\d+)\((\d+)\)', out)
    return cells, hero, (int(hp[1]), int(hp[2])) if hp else None

def screen():
    return parse(run(['screen', '--compact']))

def walkable(c):
    return c in '·.<>%)[?!/=*"($_{' or c == "`"

def bfs(cells, start, goal):
    prev = {start: None}; q = collections.deque([start])
    while q:
        c = q.popleft()
        if c == goal:
            break
        for d in KEY:
            n = (c[0] + d[0], c[1] + d[1])
            if n in prev or not walkable(cells.get(n, ' ')):
                continue
            if d[0] and d[1]:
                # Sokoban: no squeezing diagonally between two boulders/walls is fine to avoid entirely
                a = cells.get((c[0] + d[0], c[1]), ' '); b = cells.get((c[0], c[1] + d[1]), ' ')
                if not walkable(a) and not walkable(b):
                    continue
            prev[n] = c; q.append(n)
    if goal not in prev:
        return None
    path = []; c = goal
    while prev[c] is not None:
        p = prev[c]; path.append(KEY[(c[0] - p[0], c[1] - p[1])]); c = p
    return path[::-1]

def adjacent_monster(cells, hero):
    for d in KEY:
        c = cells.get((hero[0] + d[0], hero[1] + d[1]), ' ')
        if re.match(r"[A-Za-z&;:@']", c):
            return c
    return None

def send(k, why):
    out = run(['keys', '--compact', '--raw', '--why', why, k])
    return out, parse(out)

def main():
    cells, hero, hp = screen()
    for g in sys.argv[1:]:
        xy, pushes = g.split(':'); bx, by = map(int, xy.split(','))
        for p in pushes:
            dx, dy = D[p]
            if cells.get((bx, by)) != '0':
                print(f'NO BOULDER at {bx},{by} (see {cells.get((bx, by))!r})'); return 1
            behind = (bx - dx, by - dy)
            path = bfs(cells, hero, behind)
            if path is None:
                print(f'NO PATH from {hero} to {behind}'); return 1
            for k in path + [KEY[(dx, dy)]]:
                out, (cells2, hero2, hp2) = send(k, f'sokoban {g}')
                msg = '\n'.join(l for l in out.split('\n') if re.match(r'^0[5-7] ', l))
                if hero2 is None or hp2 is None:
                    print('LOST HERO / prompt'); print(msg); return 1
                if hp2[0] < hp[0]:
                    print(f'HP LOSS {hp[0]}->{hp2[0]}'); print(msg); return 1
                if re.search(r'--More--|\[yn|Perhaps that|in vain|You hear a monster|Really', out):
                    print('EVENT'); print(msg); return 1
                m = adjacent_monster(cells2, hero2)
                if m:
                    print(f'MONSTER adjacent: {m}'); print(msg); return 1
                if hero2 == hero:
                    print(f'DID NOT MOVE with {k} at {hero}'); print(msg); return 1
                cells, hero, hp = cells2, hero2, hp2
            if hero != (bx, by):
                print(f'push failed: hero {hero} want {(bx, by)}'); return 1
            bx, by = bx + dx, by + dy
        print(f'ok {g} -> hero {hero}')
    return 0

sys.exit(main())
