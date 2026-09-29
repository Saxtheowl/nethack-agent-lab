import os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts')); os.chdir(ROOT); os.environ['NH_SLOT'] = '8'
import session, guard
from explore import tile, walkable, frontier, is_door, DIRS
st = guard.state(*guard.observe(session))
rows = st['rows']; start = st['position']
seen = {start}; q = collections.deque([start])
while q:
    c = q.popleft()
    for dx, dy in DIRS:
        n = (c[0]+dx, c[1]+dy)
        if n in seen: continue
        ch = tile(rows, *n)
        if ch in '^}{0+': continue
        if not walkable(rows, *n): continue
        if dx and dy and (is_door(rows, *c) or is_door(rows, *n)): continue
        if dx and dy and not walkable(rows, c[0]+dx, c[1]) and not walkable(rows, c[0], c[1]+dy): continue
        seen.add(n); q.append(n)
out = []
for y in range(11, 30):
    out.append(''.join('*' if (x, y) in seen else tile(rows, x, y) for x in range(0, 80)))
print('\n'.join(out))
