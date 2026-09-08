"""Faithful rewrite of bothack.level (BotHack by krajj7).

A Level is a dict: dlvl, branch-id, tags (set), blueprint, tiles (21x80),
monsters ({'x:y' or pos-key -> Monster}).
Positions used as map keys are encoded as "x:y".
"""

from . import util
from . import tile as T
from . import montype as mt


def pos_key(pos):
    if isinstance(pos, str):
        return pos
    return "%d:%d" % (pos["x"], pos["y"])


def parse_key(k):
    if isinstance(k, dict):
        return k
    x, y = k.split(":")
    return {"x": int(x), "y": int(y)}


def initial_tiles():
    tiles = [[T.initial_tile(x, y + 1) for x in range(80)] for y in range(21)]
    return tiles


def new_level(dlvl, branch_id):
    return {"dlvl": dlvl, "branch-id": branch_id, "tags": set(),
            "blueprint": None, "tiles": initial_tiles(), "monsters": {}}


def diggable_floor(level):
    bid = level.get("branch-id")
    if bid in ("quest", "wiztower", "vlad", "astral", "earth", "fire", "air",
               "water", "sokoban"):
        return False
    if (level.get("blueprint") or {}).get("undiggable-floor"):
        return False
    tags = set(level.get("tags") or set())
    if tags & {"undiggable-floor", "end", "sanctum"}:
        return False
    return True


def tile_seq(level):
    return [t for row in level["tiles"] for t in row]


def at(level, x, y):
    return level["tiles"][y - 1][x]


def neighbors(level, pos):
    from . import position as p
    return [at(level, nb) for nb in p.neighbors(pos)]


def including_origin(nbr_fn, pos):
    return nbr_fn(pos) + [pos]


def shop_inside(level, tile):
    from . import position as p
    nbrs = including_origin(lambda t: neighbors(level, t), tile)
    return not any(T.door(x) for x in nbrs)


def blueprints():
    from ._data import data
    return data()["blueprints"]


def level_blueprint(level):
    """Return the blueprint matching this level (by branch/tag/role/dlvl), or
    None.  Mirrors bothack.level level-blueprint lookup."""
    if level.get("blueprint") is not None:
        return level["blueprint"]
    return None