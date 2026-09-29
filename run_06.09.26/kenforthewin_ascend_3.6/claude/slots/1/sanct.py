#!/usr/bin/env python3
"""Sanctum map (gehennom.des) with rulers + BFS. Usage: sanct.py [ox oy] [sx sy tx ty]
ox,oy = screen offset (screen = map + (ox,oy)). S = secret door (walkable once found), + = door."""
import sys
from collections import deque
M = """\
----------------------------------------------------------------------------
|             --------------                                               |
|             |............|             -------                           |
|       -------............-----         |.....|                           |
|       |......................|        --.....|            ---------      |
|    ----......................---------|......----         |.......|      |
|    |........---------..........|......+.........|     ------+---..|      |
|  ---........|.......|..........--S----|.........|     |........|..|      |
|  |..........|.......|.............|   |.........-------..----------      |
|  |..........|.......|..........----   |..........|....|..|......|        |
|  |..........|.......|..........|      --.......----+---S---S--..|        |
|  |..........---------..........|       |.......|.............|..|        |
|  ---...........................|       -----+-------S---------S---       |
|    |...........................|          |...| |......|    |....|--     |
|    ----.....................----          |...---....---  ---......|     |
|       |.....................|             |..........|    |.....----     |
|       -------...........-----             --...-------    |.....|        |
|             |...........|                  |...|          |.....|        |
|             -------------                  -----          -------        |
----------------------------------------------------------------------------""".split('\n')
FIRE = set()
for x in range(13, 24):
    FIRE.add((x, 5)); FIRE.add((x, 12))
for y in range(6, 12):
    FIRE.add((13, y)); FIRE.add((23, y))
args = [int(a) for a in sys.argv[1:]]
ox, oy = (args[0], args[1]) if len(args) >= 2 else (0, 0)
print('    ' + ''.join(str((x + ox) // 10 % 10) for x in range(76)))
print('    ' + ''.join(str((x + ox) % 10) for x in range(76)))
for y, row in enumerate(M):
    r = ''.join('F' if (x, y) in FIRE else c for x, c in enumerate(row))
    print('%3d %s' % (y + oy, r))
if len(args) >= 6:
    sx, sy, tx, ty = [a for a in args[2:6]]
    sx -= ox; sy -= oy; tx -= ox; ty -= oy
    ok = lambda x, y: 0 <= y < len(M) and 0 <= x < len(M[y]) and M[y][x] in '.+S'
    prev = {(sx, sy): None}
    q = deque([(sx, sy)])
    while q:
        c = q.popleft()
        if c == (tx, ty):
            break
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (c[0] + dx, c[1] + dy)
                if n in prev or not ok(*n):
                    continue
                # no diagonal moves into/out of doors
                if dx and dy and (M[n[1]][n[0]] in '+S' or M[c[1]][c[0]] in '+S'):
                    continue
                prev[n] = c
                q.append(n)
    p = []
    c = (tx, ty)
    while c in prev and c is not None:
        p.append(c); c = prev[c]
    p.reverse()
    print('path', ' '.join('%d,%d%s' % (x + ox, y + oy, 'F' if (x, y) in FIRE else '') for x, y in p))
