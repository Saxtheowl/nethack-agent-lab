"""Differential tests: compare the Python port against the original Clojure
BotHack used as an oracle.  The oracle is only invoked when BOTHACK_ORACLE=1
and JDK8 + lein are present; otherwise these tests are skipped — but their
absence must not be read as validation."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from bothack import util  # noqa: E402
from bothack import position  # noqa: E402
from bothack import item as Bitem  # noqa: E402
from bothack import itemid  # noqa: E402
from bothack import montype  # noqa: E402
from bothack import tile as Btile  # noqa: E402
from tools import edn  # noqa: E402

HAS_ORACLE = os.environ.get("BOTHACK_ORACLE") == "1"

_positions = [
    {"x": 39, "y": 12}, {"x": 0, "y": 1}, {"x": 79, "y": 21},
    {"x": 40, "y": 12}, {"x": 38, "y": 11}, {"x": 5, "y": 6},
    {"x": 0, "y": 21}, {"x": 79, "y": 1},
]

_labels = [
    "a blessed +1 long sword (weapon in hand)",
    "an uncursed +0 dagger",
    "a cursed -2 orcish helm (being worn)",
    "3 uncursed food rations",
    "a potion",
    "2 blessed scrolls labeled ZELGO MER",
    "a wand",
    "a ring",
    "an uncursed amulet",
    "The Amulet of Yendor",
    "a partly eaten lembas wafer",
    "a tin of spinach",
    "a gray stone",
    "an uncursed spellbook of identify",
    "a +3 dagger (alternate weapon; not wielded)",
    "a lantern (lit)",
    "an uncursed potion of holy water",
    "a glass wand called wand1 (0:8)",
    "a crude dagger",
    "a pick-axe",
    "a dwarvish mattock",
    "a large box",
    "a dead giant ant corpse",
    "a black pudding corpse",
    "a tinning kit",
    "19 uncursed rocks",
]

_monster_names = ["giant ant", "killer bee", "Medusa", "shopkeeper", "ghost",
                  "black pudding", "wood golem", "Norn", "high priest",
                  "guardian naga hatchling"]

_glyphs = ["a", "b", "@", "'", ":", "~", "8", "0", ")", "]", "[", "/", "!",
           "?", "=", "+", "*", "(", "$", "%", "_", ",", " ", "&", ";"]
_colors = ["red", "brown", "nil", "cyan", "blue", "yellow"]


def _build_cases():
    cases = []
    for a in _positions:
        for b in _positions:
            cases.append(("position", ["distance", edn.dumps(a), edn.dumps(b)]))
            cases.append(("position", ["manhattan", edn.dumps(a), edn.dumps(b)]))
            cases.append(("position", ["towards", edn.dumps(a), edn.dumps(b)]))
            cases.append(("position", ["adjacent", edn.dumps(a), edn.dumps(b)]))
        for d in ["NW", "N", "NE", "W", "E", "SW", "S", "SE"]:
            cases.append(("position", ["in-direction", edn.dumps(a), d]))
        cases.append(("position", ["neighbors", edn.dumps(a)]))
    for s in ["3", "18", "18/00", "18/50", "18/**", "25", "18/99", "18/49",
              "7", "10", "18/01", "4"]:
        cases.append(("util", ["effective-str", s]))
    for lb in _labels:
        cases.append(("item", ["parse-label", lb]))
        cases.append(("item", ["item-type", lb]))
        cases.append(("item", ["item-subtype", lb]))
        cases.append(("item", ["item-weight", lb]))
        cases.append(("item", ["appearance-of", lb]))
        cases.append(("item", ["corpse", lb]))
        cases.append(("item", ["container", lb]))
    for nm in _monster_names:
        cases.append(("monster", ["typename", nm]))
    for g in _glyphs:
        for c in _colors:
            cases.append(("tile", ["monster", g, c]))
            cases.append(("tile", ["item", g, c]))
        cases.append(("tile", ["monster-glyph", g]))
    return cases


_CASES = None
_RESULTS = None


def _run():
    global _CASES, _RESULTS
    if _RESULTS is None:
        _CASES = _build_cases()
        from tools import oracle
        _RESULTS, proc = oracle.run(_CASES)
    return _CASES, _RESULTS


def _py_result(op, args):
    sub = args[0]
    if op == "position":
        if sub == "distance":
            return position.distance(edn.loads(args[1]), edn.loads(args[2]))
        if sub == "manhattan":
            return position.distance_manhattan(edn.loads(args[1]), edn.loads(args[2]))
        if sub == "towards":
            return position.towards(edn.loads(args[1]), edn.loads(args[2]))
        if sub == "adjacent":
            return position.adjacent(edn.loads(args[1]), edn.loads(args[2]))
        if sub == "in-direction":
            return position.in_direction(edn.loads(args[1]), args[2])
        if sub == "neighbors":
            return [{"x": p["x"], "y": p["y"]}
                    for p in position.neighbors(edn.loads(args[1]))]
    elif op == "util":
        if sub == "effective-str":
            return util.effective_str(args[1])
    elif op == "item":
        label = args[1]
        item = Bitem.parse_label(label)
        if sub == "parse-label":
            return item
        if sub == "item-type":
            return itemid.item_type(item)
        if sub == "item-subtype":
            return itemid.item_subtype(item)
        if sub == "item-weight":
            return itemid.item_weight(item)
        if sub == "appearance-of":
            return itemid.appearance_of(item)
        if sub == "corpse":
            return Bitem.corpse(item)
        if sub == "container":
            return Bitem.container(item)
    elif op == "monster":
        if sub == "typename":
            m = montype.name_to_monster(args[1])
            return m["name"] if m else None
    elif op == "tile":
        g = args[1]
        if sub == "monster-glyph":
            return Btile.monster_glyph(g)
        c = None if args[2] == "nil" else args[2]
        if sub == "monster":
            return Btile.monster_impl(g, c)
        if sub == "item":
            return Btile.item_impl(g, c)
    return None


def _norm(v):
    # normalize positions/records for comparison
    return v


@pytest.mark.skipif(not HAS_ORACLE, reason="BOTHACK_ORACLE not set")
def test_differential_against_oracle():
    cases, results = _run()
    assert len(results) == len(cases), "oracle returned %d of %d cases" % (
        len(results), len(cases))
    only_parse = set()
    mismatches = []
    for (op, args), res in zip(cases, results):
        if op == "item" and args[0] == "parse-label":
            py = _py_result(op, args)
            # compare only the common subset of keys present in the oracle map
            for k, v in res.items():
                if k not in ("label",):
                    if py.get(k) != v:
                        mismatches.append((args[1], k, py.get(k), v))
            continue
        if op == "item" and args[0] == "item-type" and args[1] == "a gray stone":
            pass  # item-type of gray stone is ambiguous in both; compared below
        py = _py_result(op, args)
        if py != res:
            mismatches.append((op, args, py, res))
    assert not mismatches, "mismatches:\n" + "\n".join(map(str, mismatches[:50]))


# --- non-oracle unit tests (always run) ------------------------------------

def test_position_basics():
    assert position.distance({"x": 0, "y": 1}, {"x": 79, "y": 21}) == 79
    assert position.towards({"x": 0, "y": 1}, {"x": 1, "y": 2}) == "SE"
    assert position.in_direction({"x": 39, "y": 12}, "N") == {"x": 39, "y": 11}
    assert position.in_direction({"x": 0, "y": 1}, "W") is None
    assert position.adjacent({"x": 1, "y": 1}, {"x": 1, "y": 1}) is True


def test_effective_str():
    assert util.effective_str("18") == 18
    assert util.effective_str("18/00") == 20
    assert util.effective_str("18/99") == 19
    assert util.effective_str("18/**") == 21


def test_item_data_count():
    from bothack import itemtype
    assert len(itemtype.all_items()) == 1722


def test_monster_data_count():
    assert len(montype.monster_types()) == 376


def test_parse_label_basic():
    it = Bitem.parse_label("a blessed +1 long sword (weapon in hand)")
    assert it["buc"] == "blessed"
    assert it["enchantment"] == 1
    assert it["name"] == "long sword"
    assert it["in-use"] == "(weapon in hand)"


def test_item_type():
    assert itemid.item_type(Bitem.parse_label("a long sword")) == "weapon"
    assert itemid.item_type(Bitem.parse_label("a potion")) == "potion"
    assert itemid.item_type(Bitem.parse_label("a food ration")) == "food"


def test_appearance_of():
    it = Bitem.parse_label("a scroll labeled ZELGO MER")
    assert itemid.appearance_of(it) == "scroll labeled ZELGO MER"
    it2 = Bitem.parse_label("a short sword named Excalibur")
    assert itemid.appearance_of(it2) == "Excalibur"