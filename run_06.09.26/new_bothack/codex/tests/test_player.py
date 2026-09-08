import pytest
from bothack.catalog import data
from bothack.item import parse_label
from bothack.player import edible, want_to_eat, nutrition_sum, weight_sum, capacity


@pytest.mark.oracle
def test_food_safety_and_benefit(oracle):
    names = [i["name"] for i in data()["items"] if i["kind"] == "food"]
    for name in names:
        for race, intrinsics in (("dwarf", []), ("orc", ["poison"])):
            player = {"race": race, "intrinsics": intrinsics, "stats": {"str*": "18/50"}}
            label = "an uncursed " + name
            item = parse_label(label)
            expected = oracle.call("food", player, label)
            assert {"edible": edible(player, item), "want": want_to_eat(player, item)} == expected


@pytest.mark.oracle
def test_food_refusals_and_upstream_exception(oracle):
    player = {"race": "dwarf", "intrinsics": [], "stats": {"str*": "18/**"}}
    for label in ("a cursed food ration", "a food ration (unpaid, 45 zorkmids)", "a cockatrice corpse", "a newt corpse", "a food ration"):
        item = parse_label(label)
        try:
            want = want_to_eat(player, item)
        except ValueError:
            want = "number-format-error"
        assert {"edible": edible(player, item), "want": want} == oracle.call("food", player, label)


@pytest.mark.oracle
def test_bag_weight_nutrition_and_capacity(oracle):
    for buc in ("blessed", "uncursed", "cursed"):
        player = {"race": "dwarf", "intrinsics": [], "stats": {"str*": "18", "str": 18, "con": 18}}
        entries = [["a", f"a {buc} bag of holding", ["3 food rations", "a cursed apple", "an apple"]], ["b", "a +1 long sword"]]
        inv = {}
        for slot, label, *contents in entries:
            inv[slot] = parse_label(label)
            if contents:
                inv[slot]["items"] = [parse_label(text) for text in contents[0]]
        game = {"player": player | {"inventory": inv}}
        assert {"nutrition": nutrition_sum(game), "weight": weight_sum(game), "capacity": capacity(player)} == oracle.call("carried", player, entries)
