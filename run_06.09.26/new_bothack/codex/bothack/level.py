"""Level representation from level.clj, GPL-2.0, translated 2026-09-07."""
import json
from functools import lru_cache
from pathlib import Path
from . import position as p
from .tile import initial_tile, DOORS


def pos(value):
    return value if isinstance(value, p.Position) else p.Position(value['x'], value['y'])


def new_level(dlvl, branch_id):
    return {'dlvl': dlvl, 'branch-id': branch_id, 'tags': set(), 'blueprint': None,
            'tiles': [[initial_tile(x, y) for x in range(80)] for y in range(1, 22)], 'monsters': {}}


def at(level, position):
    position = pos(position)
    if not p.valid_position(position):
        raise ValueError(position)
    return None if level is None else level['tiles'][position.y - 1][position.x]


def tile_seq(level):
    return (tile for row in (level or {}).get('tiles', ()) for tile in row)


def neighbors(level, position, include_origin=False, straight=False):
    position = pos(position)
    positions = p.straight_neighbors(position) if straight else p.neighbors(position)
    if include_origin:
        positions = (position, *positions)
    return tuple(at(level, q) for q in positions)


def column(level, x):
    return tuple(at(level, p.Position(x, y)) for y in range(1, 22))


def shop_inside(level, tile):
    return all(t.get('feature') not in DOORS for t in neighbors(level, tile, include_origin=True))


def diggable_floor(level):
    return (level['branch-id'] not in {'quest', 'wiztower', 'vlad', 'astral', 'earth', 'fire', 'air', 'water', 'sokoban'}
            and not (level.get('blueprint') or {}).get('undiggable-floor')
            and not {'undiggable-floor', 'end', 'sanctum'}.intersection(level['tags']))


@lru_cache(maxsize=1)
def world_data():
    return json.loads((Path(__file__).parent / 'data/world.json').read_text())
