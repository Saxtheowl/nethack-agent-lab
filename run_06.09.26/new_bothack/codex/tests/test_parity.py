"""Differential tests: expected results come from the actual original code."""
from dataclasses import asdict
import random
import pytest
from bothack import position as p
from bothack.frame import Frame
from bothack.item import parse_label
from bothack.scraper import parse_botls, effective_strength
from bothack.sokoban import moves_for
from bothack.catalog import data

pytestmark = pytest.mark.oracle


def plain(value):
    if isinstance(value, p.Position):
        return asdict(value)
    if isinstance(value, tuple):
        return [plain(v) for v in value]
    return value


@pytest.mark.parametrize("method,function", [
    ("neighbors", p.neighbors), ("straight-neighbors", p.straight_neighbors),
    ("diagonal-neighbors", p.diagonal_neighbors), ("to-position", p.to_position),
    ("valid-position?", p.valid_position)])
def test_positions_unary(oracle, method, function):
    # Entire 80×21 playing field, including all boundaries.
    for y in range(1, 22):
        for x in range(80):
            pos = p.Position(x, y)
            assert plain(function(pos)) == oracle.call("position", method, asdict(pos))


@pytest.mark.parametrize("method,function", [
    ("distance", p.distance), ("distance-manhattan", p.distance_manhattan),
    ("towards", p.towards), ("adjacent?", p.adjacent),
    ("rectangle", p.rectangle), ("rectangle-boundary", p.rectangle_boundary)])
def test_positions_binary(oracle, method, function):
    rng = random.Random(343)
    for _ in range(100):
        a, b = (p.Position(rng.randrange(80), rng.randrange(1, 22)) for _ in range(2))
        assert plain(function(a, b)) == oracle.call("position", method, asdict(a), asdict(b))


LABELS = [
    "a - a blessed +1 long sword (weapon in hand)",
    "b - 3 uncursed food rations", "2 potions of holy water", "a potion of unholy water",
    "a thoroughly rusty very corroded -2 dagger", "a wand of wishing (1:3)",
    "a wand of digging (0:-1)", "a bag called bag1 named STASH", "the Amulet of Yendor",
    "a Candelabrum of Invocation (7 candles, lit)", "a Candelabrum of Invocation (no candles attached)",
    "Lord Surtur's partly eaten corpse", "a blessed diluted potion of healing (unpaid, 100 zorkmids)",
    "a partly used wax candle (lit)", "a pair of uncursed +2 leather gloves (being worn)",
    "a poisoned dart (in quiver)", "a ninja-to", "2 gunyoki", "a ruby potion, price 100 zorkmids each",
    "a greased rustproof +0 long sword (alternate weapon; not wielded)",
]


@pytest.mark.parametrize("label", LABELS)
def test_labels(oracle, label):
    assert parse_label(label) == oracle.call("label", label)


def test_generated_labels(oracle):
    # Every item identity, plus every explicit plural, parsed by both implementations.
    for item in data()["items"]:
        for label in ["an uncursed " + item["name"], *( ["3 " + item["plural"]] if item.get("plural") else [])]:
            assert parse_label(label) == oracle.call("label", label)


@pytest.mark.parametrize("strength", ["3", "18", "19", "25", "18/00", "18/01", "18/49", "18/50", "18/99", "18/**"])
def test_strength(oracle, strength):
    assert effective_strength(strength) == oracle.call("strength", strength)


@pytest.mark.parametrize("level", ["Dlvl:1", "Dlvl:45", "Home 3", "Fort Ludios", "End Game", "Astral Plane"])
def test_status(oracle, level):
    first = "Bot the Woman-at-arms St:18/50 Dx:12 Co:18 In:8 Wi:10 Ch:7 Lawful S:12345"
    for flags in ("", "Hungry", "Weak Burdened", "Satiated Blind Stun Conf FoodPois Hallu", "Fainting Overloaded", "Ill Strained"):
        for xp in ("Exp:14", "Xp:14/150000", "HD:10"):
            lines = [first, f"{level} $:123 HP:40(100) Pw:10(20) AC:-15 {xp} T:15000 {flags}"]
            assert parse_botls(lines) == oracle.call("status", lines)


def test_frames(oracle):
    for y in (0, 1, 2, 10, 21):
        for x in (0, 1, 40, 79):
            lines = ["You read: a message".ljust(80)] + [" " * 80] * 23
            if x >= 8:
                lines[y] = (" " * (x - 8) + "--More--").ljust(80)
            frame = Frame.text(lines, p.Position(x, y))
            result = {"topline": frame.topline, "topline-plus": frame.topline_plus,
                      "cursor-line": frame.cursor_line, "before-cursor": frame.before_cursor,
                      "topline-cursor": frame.topline_cursor, "engulfed": frame.looks_engulfed}
            assert result == oracle.call("frame", asdict(frame))


def test_all_sokoban_segments(oracle):
    for layout in data()["sokoban"].values():
        for stage in layout.values():
            for src, dest in zip(stage[::2], stage[1::2]):
                assert plain(moves_for(src, dest)) == oracle.call("moves", src, dest)


def test_data_export(oracle):
    assert data() == oracle.call("data")
