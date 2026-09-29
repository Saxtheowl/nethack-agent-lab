#!/usr/bin/env python3
"""roomcells.py SCREENFILE X Y: flood-fill the room interior containing (X,Y) on a saved
`v` screen dump (rows 'NN │...'), print its floor cells as a serpentine waypoint list
"x,y x,y ...". Doorways/doors (squares in the wall line) and known traps '^' are excluded.
Interior = cells that are not walls/doors/blank/corridor."""
import sys

path, sx, sy = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
grid = {}
for line in open(path, encoding='utf-8'):
    if len(line) > 3 and line[:2].isdigit():
        y = int(line[:2])
        row = line[3:].rstrip('\n')
        for x, ch in enumerate(row):
            grid[(x, y)] = ch
WALLS = set('│─┌┐└┘├┤┬┴┼|-+')
STOP = WALLS | set(' ▒#')
seen, todo = set(), [(sx, sy)]
while todo:
    c = todo.pop()
    if c in seen:
        continue
    ch = grid.get(c, ' ')
    if ch in STOP:
        continue
    seen.add(c)
    x, y = c
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx or dy:
                todo.append((x + dx, y + dy))


def is_doorway(c):
    # a floor cell lying in a wall line: walls on both sides horizontally or vertically
    x, y = c
    h = grid.get((x - 1, y), ' ') in WALLS and grid.get((x + 1, y), ' ') in WALLS
    v = grid.get((x, y - 1), ' ') in WALLS and grid.get((x, y + 1), ' ') in WALLS
    return h or v


cells = sorted(c for c in seen if grid.get(c) != '^' and not is_doorway(c))
rows = sorted(set(y for _, y in cells))
out = []
for i, y in enumerate(rows):
    xs = sorted(x for x, yy in cells if yy == y)
    if i % 2:
        xs.reverse()
    out += [f"{x},{y}" for x in xs]
print(' '.join(out))
