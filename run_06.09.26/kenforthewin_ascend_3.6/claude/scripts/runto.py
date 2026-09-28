#!/usr/bin/env python3
"""Send up to N raw movement keys along a BFS path over the remembered map
toward x,y (avoiding monster glyphs, traps, boulders). For escapes where
travel (_) refuses to run because a monster is in view. Stops on HP loss."""
import collections, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import guard, session, explore

x, y, n = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 8
KEYS = {(0, -1): '8', (1, 0): '6', (0, 1): '2', (-1, 0): '4', (1, -1): '9', (1, 1): '3', (-1, 1): '1', (-1, -1): '7'}
for _ in range(n):
    st = guard.state(*guard.observe(session))
    if st is None:
        print('stop: prompt'); break
    rows, start = st['rows'], st['position']
    if start == (x, y):
        print('arrived'); break
    prev = {start: None}; q = collections.deque([start])
    while q:
        c = q.popleft()
        if c == (x, y): break
        for d in KEYS:
            nx, ny = c[0] + d[0], c[1] + d[1]
            t = explore.tile(rows, nx, ny)
            if (nx, ny) in prev or not explore.walkable(rows, nx, ny) or t in '0^' or (t.isalpha() and (nx, ny) != (x, y)):
                continue
            if d[0] and d[1] and (explore.is_door(rows, *c) or explore.is_door(rows, nx, ny)):
                continue
            prev[(nx, ny)] = c; q.append((nx, ny))
    if (x, y) not in prev:
        print('stop: no path'); break
    c = (x, y)
    while prev[c] != start:
        c = prev[c]
    session.send('m' + KEYS[(c[0] - start[0], c[1] - start[1])])  # m: never attack
    obs = guard.settled(session)
    st2 = guard.state(*obs) if obs else None
    if st2 is None:
        print('stop: prompt after step'); break
    if st2['hp'] < st['hp']:
        print('stop: HP loss'); break
session.print_screen(True)
