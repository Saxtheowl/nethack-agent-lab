from dataclasses import asdict
from io import BytesIO
import random
import struct
import pytest
from bothack.tile import initial_tile, parse_tile
from bothack.pathing import base_cost, astar, dijkstra
from bothack.position import Position
from bothack.terminal import Terminal, read_ttyrec, write_ttyrec


def normalize(value):
    if isinstance(value, dict): return {k: normalize(v) for k, v in value.items()}
    if isinstance(value, set): return sorted(value)
    if isinstance(value, (list, tuple)): return [normalize(v) for v in value]
    return value


@pytest.mark.oracle
def test_tile_transition_sequences(oracle):
    rng = random.Random(343)
    glyphs = ' .<>\\{}#_~^]|-@rUPI8!/$%:?'
    colors = [None, "red", "green", "brown", "blue", "cyan", "yellow", "white"]
    for x, y in [(0, 1), (40, 12), (79, 21)]:
        tile = initial_tile(x, y)
        for _ in range(300):
            glyph, color = rng.choice(glyphs), rng.choice(colors)
            expected = oracle.call("tile", normalize(tile), glyph, color)
            tile = parse_tile(tile, glyph, color)
            assert normalize(tile) == expected


@pytest.mark.oracle
def test_base_costs(oracle):
    for feature in (None, "floor", "stairs-down", "wall", "cloud", "pool", "pit", "fountain"):
        for direction in ("N", "NE"):
            for opts in ({}, {"prefer-items": True}, {"prefer-items": True, "pick": True}):
                t = initial_tile(40, 12) | {"feature": feature}
                assert base_cost({}, direction, t, opts) == oracle.call("base-cost", {}, direction, normalize(t), opts)


@pytest.mark.oracle
def test_terminal_jta(oracle):
    oracle.call("terminal-reset")
    terminal = Terminal()
    for chunk in ["hello", "\r\nworld", "\x1b[2J\x1b[H", "\x1b[3;7H@", "\x1b[1;31mred",
                  "\x1b[0m\x1b[7mreverse", "\x1b[0m\x1b[22;1H" + "X" * 80, "Y", "\bZ", "\x1b[K",
                  "\x1b[2;3H\x1b[32mgreen\x1b[0m", "\x1b[3;1H\x1b[1;34;43;7mPET"]:
        assert normalize(asdict(terminal.feed(chunk))) == oracle.call("terminal-feed", chunk)


def test_ttyrec_roundtrip_and_truncation():
    stream = BytesIO()
    write_ttyrec(stream, b"\x1b[H@", timestamp=123.5)
    stream.seek(0)
    record, = list(read_ttyrec(stream))
    assert (record.seconds, record.microseconds, record.payload) == (123, 500000, b"\x1b[H@")
    for bad in (b"123", struct.pack("<III", 1, 0, 20) + b"x", struct.pack("<III", 1, 1_000_000, 0)):
        with pytest.raises(ValueError): list(read_ttyrec(BytesIO(bad)))


def test_astar_target_can_be_unwalkable_and_start_is_not_in_path():
    start, target = Position(3, 3), Position(5, 3)
    def move(a, b):
        return (1, "step") if b in {Position(4, 3)} else None
    assert astar(start, target, move) == (Position(4, 3), target)
    assert astar(start, start, move) == ()


@pytest.mark.oracle
def test_search_corridors_fractional_cost_and_limits(oracle):
    start, target = Position(3, 3), Position(8, 3)
    for costs in ([(x, 3, 1.7) for x in range(3, 9)], [(x, 3, 1) for x in range(3, 8)], []):
        weights = {Position(x, y): cost for x, y, cost in costs}
        def move(a, b):
            return (weights[b], "move") if b in weights else None
        for limit in (None, 0, 1, 4, 5, 6, 10):
            for algo in ("astar", "dijkstra"):
                result = astar(start, target, move, limit) if algo == "astar" else dijkstra(start, lambda p: p == target, move, limit)
                result = [asdict(p) for p in result] if result is not None else None
                assert result == oracle.call("path", algo, asdict(start), asdict(target), costs, limit)
