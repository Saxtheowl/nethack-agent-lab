"""First policy helpers translated from bots/mainbot.clj (GPL-2.0).

This is NOT the complete action-selection policy. No autonomous play entry
point is provided until the priority chain and its dependencies are ported.
"""
from fractions import Fraction
import re
from .catalog import items_by_name, data
from .itemid import common_properties, initial_ids
from .player import inventory, edible, tin, identity, item_type


def low_hp(player):
    return player["hp"] < 10 or Fraction(player["hp"], player["maxhp"]) <= Fraction(9, 20)


def safe_hp(player):
    return Fraction(player["hp"], player["maxhp"]) >= Fraction(9, 10) or player["hp"] > 175


def real_amulet(item):
    return item.get("name") == "Amulet of Yendor" and item.get("specific") == "REAL"


def bribe_demon(prompt):
    match = re.search(r"demands ([0-9][0-9]*) zorkmids for safe passage", prompt)
    return int(match[1]) if match else None


def hits_hard(monster):
    return (monster.get("type") or {}).get("name") in {"winged gargoyle", "Olog-hai", "salamander"}


def mobile(game, monster):
    monster_type = monster.get("type") or {}
    return (" mimic" not in monster_type.get("name", "") and "sessile" not in monster_type.get("tags", ())
            and (bool(monster.get("awake")) or game["turn"] - monster["first-known"] < 6))


def nutrition_weight_ratio(item):
    identity = common_properties(initial_ids(item)) or {}
    if identity.get("kind") != "food":
        return 0
    return Fraction(identity.get("nutrition") or 0, identity["weight"])


def choose_food(game):
    candidates = [(slot, food) for slot, food in inventory(game, True)
                  if edible(game["player"], food) and (identity(game, food) or {}).get("name") != "lizard corpse" and not tin(food)]
    # Clojure min-key selects the LAST minimum on a tie.
    if candidates:
        return min(reversed(candidates), key=lambda entry: nutrition_weight_ratio(entry[1]))
    return next(((slot, food) for slot, food in inventory(game, True)
                 if food["name"] == "lizard corpse" or (identity(game, food) or {}).get("name") == "lizard corpse"), None)


def utility(item, game=None):
    known = items_by_name().get(item.get("specific")) or items_by_name().get(item["name"], {})
    value = 50 if known.get("artifact") else 0
    if item.get("erosion") is not None and "key" not in item["name"]:
        value -= item["erosion"]
    if item.get("enchantment") is not None:
        value += item["enchantment"]
    if item_type(item) == "wand" and item.get("charges") is None:
        value += 3
    if item.get("charges") is not None:
        value += item["charges"]
    if item.get("proof"):
        value += 3
    if item.get("buc") == "blessed":
        value += 2
    # Upstream calls (uncursed? (:buc item)) instead of (uncursed? item),
    # so its purported uncursed bonus is never applied.
    if item.get("buc") == "cursed" and not item.get("in-use"):
        value -= 1
    if game is not None:
        name = (identity(game, item) or {}).get("name")
        for category in data()["desired-items"]:
            if name in category:
                value += 15 * (len(category) - category.index(name))
                break
    return value
