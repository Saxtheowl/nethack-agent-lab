import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts')); os.chdir(ROOT); os.environ['NH_SLOT'] = '8'
import session, guard
from explore import tile, walkable, frontier, is_door
st = guard.state(*guard.observe(session))
x, y = st['position']
print('pos', st['position'], 'pets', st['pets'])
for dy in (-1, 0, 1):
    print(' '.join(f"{tile(st['rows'], x+dx, y+dy)!r}:{walkable(st['rows'], x+dx, y+dy)}" for dx in (-1, 0, 1)))
