"""Translation of bothack/position.clj, GPL-2.0, 2026-09-06.

Preserves screen coordinates, traversal order and the original inclusive adjacency.
"""
from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Position:
    x: int
    y: int


DIRECTIONS = ("NW", "N", "NE", "W", "E", "SW", "S", "SE")
DELTAS = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
DIRMAP = dict(zip(DIRECTIONS, DELTAS))
OPPOSITE = dict(zip(DIRECTIONS, reversed(DIRECTIONS)))
VI_DIRECTIONS = dict(zip(DIRECTIONS, "ykuhlbjn")) | {">": ">", "<": "<", ".": "."}
STRAIGHT = frozenset(("N", "W", "S", "E"))
DIAGONAL = frozenset(("NW", "SW", "NE", "SE"))


def position(value, y=None):
    if y is not None:
        return Position(value, y)
    if isinstance(value, Position):
        return value
    if isinstance(value, dict):
        return Position(value["x"], value["y"])
    return Position(*value)


def valid_position(p):
    return 0 <= p.x <= 79 and 1 <= p.y <= 21


def distance(a, b):
    return max(abs(a.x - b.x), abs(a.y - b.y))


def distance_manhattan(a, b):
    return abs(a.x - b.x) + abs(a.y - b.y)


def adjacent(a, b):
    return distance(a, b) <= 1


def towards(a, b):
    delta = ((b.x > a.x) - (b.x < a.x), (b.y > a.y) - (b.y < a.y))
    return dict(zip(DELTAS, DIRECTIONS)).get(delta)


def in_direction(p, direction):
    if not valid_position(p):
        raise ValueError(p)
    dx, dy = DIRMAP[direction]
    result = Position(p.x + dx, p.y + dy)
    return result if valid_position(result) else None


def neighbors(p):
    return tuple(q for dx, dy in DELTAS if valid_position(q := Position(p.x + dx, p.y + dy)))


def straight_neighbors(p):
    return tuple(q for q in neighbors(p) if towards(p, q) in STRAIGHT)


def diagonal_neighbors(p):
    return tuple(q for q in neighbors(p) if towards(p, q) in DIAGONAL)


def rectangle(nw, se):
    return tuple(Position(x, y) for x in range(nw.x, se.x + 1) for y in range(nw.y, se.y + 1))


def rectangle_boundary(nw, se):
    return tuple(p for p in rectangle(nw, se) if p.x in (nw.x, se.x) or p.y in (nw.y, se.y))


def in_line(a, b):
    return a.x == b.x or a.y == b.y


def to_position(p):
    if not valid_position(p):
        raise ValueError(p)
    return "H" * 10 + "K" * 4 + "j" * (p.y - 1) + "l" * p.x
