"""Faithful rewrite of bothack.position (BotHack by krajj7).

A Position is represented as a plain dict {'x': int, 'y': int}.  Keywords are
plain strings.  Coordinates: 0 <= x <= 79, 1 <= y <= 21 (terminal map layout).
"""

# bothack.position/directions and deltas (order matters: matches original)
_directions = ["NW", "N", "NE", "W", "E", "SW", "S", "SE"]
_opposite_map = {"NW": "SE", "N": "S", "NE": "SW", "W": "E",
                 "E": "W", "SW": "NE", "S": "N", "SE": "NW"}
_deltas = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

Straight = {"N", "W", "S", "E"}
Diagonal = {"NW", "SW", "NE", "SE"}


def position(x=None, y=None):
    """(position x y) or (position {:x .. :y ..})."""
    if y is None and isinstance(x, dict):
        return {"x": x["x"], "y": x["y"]}
    return {"x": x, "y": y}


def valid_position(x_or_pos, y=None):
    if y is None and isinstance(x_or_pos, dict):
        x = x_or_pos["x"]
        y = x_or_pos["y"]
    else:
        x = x_or_pos
    return 0 <= x <= 79 and 1 <= y <= 21


def at(level, x_or_pos, y=None):
    """Tile of the level at the given terminal position."""
    if y is None and isinstance(x_or_pos, dict):
        x = x_or_pos["x"]
        y = x_or_pos["y"]
    else:
        x = x_or_pos
    return level["tiles"][y - 1][x]


def adjacent(a, b):
    return abs(a["x"] - b["x"]) <= 1 and abs(a["y"] - b["y"]) <= 1


def _compare(x, y):
    return (x > y) - (x < y)


def towards(from_pos, to):
    d = (_compare(to["x"], from_pos["x"]), _compare(to["y"], from_pos["y"]))
    return dict(zip(_deltas, _directions)).get(d)


def dirmap_key(direction):
    """Map a direction keyword to its [dx dy] delta."""
    idx = _directions.index(direction)
    return _deltas[idx]


def diagonal(from_pos, to):
    return towards(from_pos, to) in Diagonal


def straight(from_pos, to):
    return towards(from_pos, to) in Straight


def neighbors(pos_or_level, pos=None):
    """(neighbors pos) => list of valid Positions, in delta order."""
    if pos is None and not isinstance(pos_or_level, dict):
        # (neighbors level tile) 3-arity not used in port; handled elsewhere
        pass
    p = pos_or_level
    result = []
    for dx, dy in _deltas:
        nb = {"x": p["x"] + dx, "y": p["y"] + dy}
        if valid_position(nb):
            result.append(nb)
    return result


def straight_neighbors(tile):
    return [p for p in neighbors(tile) if straight(tile, p)]


def diagonal_neighbors(tile):
    return [p for p in neighbors(tile) if diagonal(tile, p)]


def in_direction(from_pos, direction):
    if from_pos is None or direction is None:
        return None
    dx, dy = dirmap_key(direction)
    res = {"x": from_pos["x"] + dx, "y": from_pos["y"] + dy}
    if valid_position(res):
        return res
    return None


def distance(a, b):
    return max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"]))


def distance_manhattan(a, b):
    return abs(a["x"] - b["x"]) + abs(a["y"] - b["y"])


def rectangle(nw, se):
    return [{"x": x, "y": y}
            for x in range(nw["x"], se["x"] + 1)
            for y in range(nw["y"], se["y"] + 1)]


def rectangle_boundary(nw, se):
    return [{"x": x, "y": y}
            for x in range(nw["x"], se["x"] + 1)
            for y in range(nw["y"], se["y"] + 1)
            if x == nw["x"] or x == se["x"] or y == nw["y"] or y == se["y"]]


def to_position(pos):
    """Sequence of keys to move the cursor from the corner to pos."""
    return "H" * 10 + "K" * 4 + "j" * (pos["y"] - 1) + "l" * pos["x"]