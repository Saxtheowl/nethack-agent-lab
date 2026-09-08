"""Script selection from sokoban.clj (GPL-2.0, translated 2026-09-06).

Coordinates describe player pushes, not boulder destinations. Interruption
tracking and navigation belong to the game/action layers, not this selector.
"""
from .catalog import data
from .position import Position, in_direction, towards, position


def moves_for(src, dest):
    src, dest = position(src), position(dest)
    if src.x != dest.x and src.y != dest.y:
        raise ValueError("Sokoban scripted segments must be straight")
    direction = towards(src, dest)
    result = [src]
    while result[-1] != dest:
        nxt = in_direction(result[-1], direction)
        if nxt is None:
            raise ValueError("Segment outside the map")
        result.append(nxt)
    return tuple(result)


def walked_in_order(last_fill, src_pushed, dest_pushed):
    return (0 if last_fill is None else last_fill) <= (-1 if src_pushed is None else src_pushed) <= (-2 if dest_pushed is None else dest_pushed)


def next_push(tag, boulders, pushed_at, last_fill=None):
    """Return the next (player source, player destination), or None.

    boulders is the set of real (non-mimic) boulders; pushed_at maps positions
    to the upstream pushed* action counter, NOT the NetHack turn counter.
    """
    count = len(boulders)
    if tag == "soko-4a" and Position(30, 15) in boulders:
        count += 100
    script = data()["sokoban"].get(tag, {}).get(str(count), [])
    for start, finish in zip(script[::2], script[1::2]):
        src, dest = position(start), position(finish)
        if in_direction(dest, towards(src, dest)) in boulders:
            continue
        if walked_in_order(last_fill, pushed_at.get(src), pushed_at.get(dest)):
            continue
        moves = moves_for(src, dest)
        for a, b in zip(moves, moves[1:]):
            if b not in boulders and walked_in_order(last_fill, pushed_at.get(a), pushed_at.get(b)):
                continue
            return a, b
        return None
    return None
