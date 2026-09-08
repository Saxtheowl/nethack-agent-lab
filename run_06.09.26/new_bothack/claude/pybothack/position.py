"""Port of bothack.position."""
from .util import VI_DIRECTIONS


class Pos(object):
    """A position; supports both attribute and ['x']/['y'] access so that it is
    interchangeable with tile/monster maps in the ported code."""
    __slots__ = ('x', 'y')

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getitem__(self, k):
        if k == 'x':
            return self.x
        if k == 'y':
            return self.y
        raise KeyError(k)

    def get(self, k, default=None):
        if k == 'x':
            return self.x
        if k == 'y':
            return self.y
        return default

    def __eq__(self, o):
        if isinstance(o, Pos):
            return self.x == o.x and self.y == o.y
        if isinstance(o, dict):
            return self.x == o.get('x') and self.y == o.get('y')
        return NotImplemented

    def __ne__(self, o):
        r = self.__eq__(o)
        return r if r is NotImplemented else not r

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return "#Position{:x %s, :y %s}" % (self.x, self.y)


def position(of, y=None):
    if y is not None:
        return Pos(of, y)
    if isinstance(of, Pos):
        return of
    return Pos(of['x'], of['y'])


def position_map(of):
    return {'x': of['x'], 'y': of['y']}


def valid_position(x, y=None):
    if y is None:
        x, y = x['x'], x['y']
    return 0 <= x <= 79 and 1 <= y <= 21


def at(level, x, y=None):
    """Tile of the level at given terminal position."""
    if y is None:
        x, y = x['x'], x['y']
    return level['tiles'][y - 1][x]


DIRECTIONS = ['NW', 'N', 'NE', 'W', 'E', 'SW', 'S', 'SE']
OPPOSITE = {'NW': 'SE', 'N': 'S', 'NE': 'SW', 'W': 'E',
            'E': 'W', 'SW': 'NE', 'S': 'N', 'SE': 'NW'}
DELTAS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
DIRMAP = dict(zip(DIRECTIONS, DELTAS))
DIRMAP.update(dict(zip(DELTAS, DIRECTIONS)))

STRAIGHT = {'N', 'W', 'S', 'E'}
DIAGONAL = {'NW', 'SW', 'NE', 'SE'}


def straight(d):
    return d in STRAIGHT


def diagonal(d):
    return d in DIAGONAL


def adjacent(p1, p2):
    return abs(p1['x'] - p2['x']) <= 1 and abs(p1['y'] - p2['y']) <= 1


def _cmp(a, b):
    return (a > b) - (a < b)


def towards(frm, to):
    return DIRMAP.get((_cmp(to['x'], frm['x']), _cmp(to['y'], frm['y'])))


def diagonal_p(frm, to):
    return towards(frm, to) in DIAGONAL


def straight_p(frm, to):
    return towards(frm, to) in STRAIGHT


def _build_neighbors():
    tbl = {}
    for x in range(80):
        for y in range(1, 22):
            res = []
            for dx, dy in DELTAS:
                nx, ny = x + dx, y + dy
                if 0 <= nx <= 79 and 1 <= ny <= 21:
                    res.append(Pos(nx, ny))
            tbl[(x, y)] = res
    return tbl


_NEIGHBORS = _build_neighbors()      # the map is a fixed 80x21 grid


def neighbors(level_or_pos, tile=None):
    if tile is not None:
        tiles = level_or_pos['tiles']
        return [tiles[p.y - 1][p.x] for p in _NEIGHBORS[(tile['x'],
                                                         tile['y'])]]
    pos = level_or_pos
    return _NEIGHBORS[(pos['x'], pos['y'])]


def including_origin(nbr_fn, level_or_pos, pos=None):
    if pos is None:
        return list(nbr_fn(level_or_pos)) + [position(level_or_pos)]
    return list(nbr_fn(level_or_pos, pos)) + [at(level_or_pos, pos)]


def straight_neighbors(level_or_tile, tile=None):
    if tile is None:
        t = level_or_tile
        return [n for n in neighbors(t) if straight_p(t, n)]
    return [n for n in neighbors(level_or_tile, tile) if straight_p(tile, n)]


def diagonal_neighbors(level_or_tile, tile=None):
    if tile is None:
        t = level_or_tile
        return [n for n in neighbors(t) if diagonal_p(t, n)]
    return [n for n in neighbors(level_or_tile, tile) if diagonal_p(tile, n)]


def in_direction(level_or_from, frm_or_dir, dir_=None):
    if dir_ is None:
        frm, d = level_or_from, frm_or_dir
        assert valid_position(frm) and d is not None
        dx, dy = DIRMAP[d]
        res = Pos(frm['x'] + dx, frm['y'] + dy)
        return res if valid_position(res) else None
    level, frm, d = level_or_from, frm_or_dir, dir_
    p = in_direction(frm, d)
    return at(level, p) if p is not None else None


def distance(frm, to):
    return max(abs(frm['x'] - to['x']), abs(frm['y'] - to['y']))


def distance_manhattan(frm, to):
    return abs(frm['x'] - to['x']) + abs(frm['y'] - to['y'])


def rectangle(nw, se):
    return [Pos(x, y)
            for x in range(nw['x'], se['x'] + 1)
            for y in range(nw['y'], se['y'] + 1)]


def rectangle_boundary(nw, se):
    return [Pos(x, y)
            for x in range(nw['x'], se['x'] + 1)
            for y in range(nw['y'], se['y'] + 1)
            if x == nw['x'] or x == se['x'] or y == nw['y'] or y == se['y']]


def in_line(frm, to):
    return frm['x'] == to['x'] or frm['y'] == to['y']


def to_position(pos):
    """Keys to move the cursor from the corner to the given position."""
    return ('H' * 10 + 'K' * 4) + ('j' * (pos['y'] - 1)) + ('l' * pos['x'])


# --------------------------------------------------------------- hash order
# clojure.data.priority-map keeps equal-priority items in a PersistentHashSet
# and peeks its first element, so the original's choice among equally good
# paths follows Clojure's hash order.  A PersistentHashSet iterates its keys
# in ascending order of the hash's 5-bit chunks, least significant first;
# the hashes themselves are dumped from the original (see tools/cljdump).
def _build_hamt_keys():
    import json
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, '_leveldata.json')) as f:
        data = json.load(f)
    hashes = data['__map__'] if '__map__' in data else None
    if hashes is None:
        hashes = data['position-hashes']
    else:
        hashes = dict(hashes)['position-hashes']
    keys = {}
    i = 0
    for y in range(1, 22):
        for x in range(80):
            h = hashes[i] & 0xffffffff
            keys[(x, y)] = tuple((h >> (5 * b)) & 31 for b in range(7))
            i += 1
    return keys


HAMT_KEYS = _build_hamt_keys()   # {(x, y): 5-bit chunk tuple}


def hamt_chunks(h):
    """Clojure's HAMT ordering key for a hash: 5-bit chunks, LSB first."""
    h &= 0xffffffff
    return tuple((h >> (5 * b)) & 31 for b in range(7))


def hamt_key(pos):
    """Sort key reproducing Clojure's PersistentHashSet iteration order."""
    return HAMT_KEYS[(pos.x, pos.y) if isinstance(pos, Pos)
                     else (pos['x'], pos['y'])]
