import pytest
from bothack.item import parse_label
from bothack.mainbot import low_hp, safe_hp, utility, choose_food


@pytest.mark.oracle
def test_hp_threshold_boundaries(oracle):
    for maxhp in (10, 20, 33, 100, 200, 501):
        for hp in sorted({1, 9, 10, int(maxhp * 0.45), int(maxhp * 0.45) + 1, int(maxhp * 0.9), int(maxhp * 0.9) + 1, maxhp}):
            player = {"hp": hp, "maxhp": maxhp}
            assert {"low": low_hp(player), "safe": safe_hp(player)} == oracle.call("hp", player)


@pytest.mark.oracle
@pytest.mark.parametrize("label", ["a +1 long sword", "a blessed +2 Excalibur", "an uncursed dagger", "a cursed -1 dagger", "a cursed -1 dagger (weapon in hand)", "a wand of digging", "a wand of digging (0:0)", "a wand of wishing (1:2)", "a very rusty skeleton key", "a rustproof +3 long sword"])
def test_equipment_utility(oracle, label):
    for with_game in (False, True):
        assert utility(parse_label(label), {} if with_game else None) == oracle.call("utility", label, with_game)


@pytest.mark.oracle
@pytest.mark.parametrize("entries", [
    [], [["a", "a food ration"], ["b", "an apple"]],
    [["a", "a food ration"], ["b", "a food ration"]],
    [["a", "a lizard corpse"], ["b", "a cursed food ration"]],
    [["a", "a cursed lizard corpse"]],
    [["a", "a tripe ration"], ["b", "a tin"]],
    [["a", "a bag of holding", ["an apple", "2 food rations"]], ["b", "a lizard corpse"]],
])
def test_choose_food(oracle, entries):
    p = {"race": "dwarf", "intrinsics": [], "stats": {"str*": "18"}}
    inventory = {}
    for slot, label, *contents in entries:
        inventory[slot] = parse_label(label)
        if contents:
            inventory[slot]["items"] = [parse_label(text) for text in contents[0]]
    result = choose_food({"player": p | {"inventory": inventory}})
    assert ([result[0], result[1]["label"]] if result else None) == oracle.call("choose-food", p, entries)
