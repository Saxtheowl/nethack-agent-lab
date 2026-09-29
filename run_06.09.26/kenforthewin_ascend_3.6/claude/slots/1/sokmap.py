#!/usr/bin/env python3
"""sokmap.py X0 Y0 X1 Y1 OUT : dump the current screen region as a solver map
(# wall, . floor/door/stairs/items, 0 boulder, ^ hole, @ hero). Coordinates = screen (x,y)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
import session
x0, y0, x1, y1 = map(int, sys.argv[1:5])
lines = session.screen().splitlines()
walls = set('│─┌┐└┘├┤┬┴┼')
out = []
for y in range(y0, y1 + 1):
    row = lines[y] if y < len(lines) else ''
    s = ''
    for x in range(x0, x1 + 1):
        c = row[x] if x < len(row) else ' '
        if c in walls: s += '#'
        elif c in '0^@': s += c
        elif c == ' ': s += ' '
        else: s += '.'
    out.append(s.rstrip())
Path(sys.argv[5]).write_text('\n'.join(out) + '\n')
print('\n'.join(out))
