#!/usr/bin/env python3
"""One flee step: choose the adjacent walkable free cell that maximises
distance from the given monster glyph position (Chebyshev), ties broken by
more open neighbours. Prints the result."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import guard, session, explore
mx, my = int(sys.argv[1]), int(sys.argv[2])
st = guard.state(*guard.observe(session))
rows, (x, y) = st['rows'], st['position']
KEYS = {(0, -1): '8', (1, 0): '6', (0, 1): '2', (-1, 0): '4', (1, -1): '9', (1, 1): '3', (-1, 1): '1', (-1, -1): '7'}
best = None
for (dx, dy), k in KEYS.items():
    nx, ny = x + dx, y + dy
    t = explore.tile(rows, nx, ny)
    if not explore.walkable(rows, nx, ny) or t.isalpha() or t in '0^@':
        continue
    d = max(abs(nx - mx), abs(ny - my))
    free = sum(1 for (ex, ey) in KEYS if explore.walkable(rows, nx + ex, ny + ey)
               and not explore.tile(rows, nx + ex, ny + ey).isalpha())
    score = (d, free)
    if best is None or score > best[0]:
        best = (score, k)
print('flee key', best)
if best:
    session.send(best[1])
