"""Port of bothack.level.  The special level blueprints are the ones from the
original (extracted verbatim, see tools/cljdump)."""
from ._load import LEVELDATA
from .montype import name_to_monster
from .position import Pos, at, position, rectangle, rectangle_boundary
from .tile import initial_tile, door, wall_p
from .position import including_origin, neighbors


def _initial_tiles():
    return [[initial_tile(x, y + 1) for x in range(80)] for y in range(21)]


def diggable_floor(level):
    return not (level.get('branch-id') in
                ('quest', 'wiztower', 'vlad', 'astral', 'earth', 'fire', 'air',
                 'water', 'sokoban')
                or (level.get('blueprint') or {}).get('undiggable-floor')
                or any(t in (level.get('tags') or ())
                       for t in ('undiggable-floor', 'end', 'sanctum')))


def tile_seq(level):
    """All 80x21 tiles of the level, left to right, top to bottom."""
    if level is None:
        return []
    assert 'monsters' in level
    return [t for row in level['tiles'] for t in row]


def column(level, x):
    return [at(level, x, y) for y in range(1, 22)]


def shop_inside(level, tile):
    return not any(door(t) for t in including_origin(neighbors, level, tile))


ORACLE_POSITION = LEVELDATA['oracle-position']

wiztower_boundary = set(LEVELDATA['wiztower-boundary'])
wiztower_inner_boundary = set(LEVELDATA['wiztower-inner-boundary'])
wiztower_rect = list(LEVELDATA['wiztower-rect'])
geh_maze = LEVELDATA['geh-maze']


def _fix_blueprint(b):
    b = dict(b)
    if b.get('monsters'):
        b['monsters'] = {p: name_to_monster(n)
                         for p, n in b['monsters'].items()}
    return b


blueprints = [_fix_blueprint(b) for b in LEVELDATA['blueprints']]


def new_level(dlvl, branch_id):
    return {'dlvl': dlvl, 'branch-id': branch_id, 'tags': frozenset(),
            'blueprint': None, 'tiles': _initial_tiles(), 'monsters': {},
            'explored': None}
