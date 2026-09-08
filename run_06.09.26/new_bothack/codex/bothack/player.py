"""Player state, food safety and carrying calculations from player.clj.

GPL-2.0, translated 2026-09-06. Equipment blockers and the complete inventory
selection API are not yet integrated.
"""
import re
from .catalog import items_by_name
from .item import container, noncursed
from .itemid import initial_ids, common_properties

FIELDS = "nickname title role race hp maxhp pw maxpw ac xplvl x y inventory hunger encumbrance intrinsics engulfed trapped leg-hurt state stat-drained polymorphed lycantrophy stoning stats alignment protection can-enhance".split()
TABOO_CORPSES = frozenset({"chickatrice", "cockatrice", "green slime", "stalker", "quantum mechanic", "elf", "human", "dwarf", "giant", "violet fungus", "yellow mold", "chameleon", "Medusa", "doppelganger", "Pestilence", "Death", "Famine"})


def new_player():
    return dict.fromkeys(FIELDS) | {"protection": 0, "inventory": {}}


def update_player(player, status):
    from .item import label_to_item
    from .monster import by_name
    result = player | {k: v for k, v in status.items() if k in player}
    if not status.get('blind'):
        result['state'] = None if result.get('state') is None else set(result['state']) - {'ext-blind'}
    if status.get('xp-label') == 'HD':
        result['polymorphed'] = by_name(status.get('title') or 'guardian naga hatchling')
    if status.get('xp-label') == 'Exp':
        result['polymorphed'] = None
    inventory = dict(result.get('inventory') or {})
    if status['gold'] == 0:
        inventory.pop('$', None)
    if status['gold'] > 0:
        inventory['$'] = label_to_item('uncursed gold piece') | {'qty': status['gold']}
    return result | {'inventory': inventory}


def hungry(player):
    return player.get("hunger") in {"hungry", "weak", "fainting"}


def weak(player):
    return player.get("hunger") in {"weak", "fainting"}


def impaired(player):
    return bool({"conf", "stun", "hallu", "blind"}.intersection(player.get("state") or ()))


def dizzy(player):
    return bool({"conf", "stun"}.intersection(player.get("state") or ()))


def overtaxed(player):
    return player.get("encumbrance") in {"overtaxed", "overloaded"}


def capacity(player):
    return min(1000, 50 + 25 * (player["stats"]["con"] + player["stats"]["str"]))


def inventory(game_or_player, bagged=False):
    player = game_or_player.get("player", game_or_player)
    main = tuple(player["inventory"].items())
    return main + (tuple((slot, item) for slot, bag in main if container(bag) for item in bag.get("items") or ()) if bagged else ())


def item_type(item):
    ids = initial_ids(item)
    return ids[0].get("kind") if ids else None


def tin(item):
    return item_type(item) == "food" and bool(re.search(r"\btins?\b", item["name"]))


def safe_corpse_type(player, corpse, corpse_type):
    monster = corpse_type["monster"]
    tags = monster["tags"]
    return ((tin(corpse) or "poison" in player["intrinsics"] or not corpse_type.get("poisonous"))
            and player["race"] not in tags and monster["name"] not in TABOO_CORPSES
            and not {"were", "teleport", "domestic"}.intersection(tags)
            and not re.search(r"bat$", monster["name"]))


def edible(player, food):
    if not noncursed(food) or food.get("cost") is not None:
        return False
    if tin(food):
        return True
    identity = items_by_name().get(food["name"])
    return bool(identity and identity["kind"] == "food" and
                (player["race"] == "orc" or food["name"] != "tripe ration") and
                (not identity.get("monster") or safe_corpse_type(player, food, identity)))


def want_to_eat(player, corpse):
    if not edible(player, corpse):
        return False
    identity = items_by_name().get(corpse["name"], {})
    monster = identity.get("monster") or {}
    strength = player["stats"]["str*"]
    if monster.get("name") in {"newt", "wraith"}:
        return True
    # Keep upstream's short-circuit behavior, including its parse error for
    # "18/**" in this branch. Silently fixing it would hide a divergence.
    if (strength != "18/**" or int(strength) < 18) and "str" in monster.get("tags", ()):
        return True
    return bool(set(monster.get("resistances-conferred", ())) - set(player["intrinsics"]))


def identity(game, item):
    if db := game.get("identification", game.get("discoveries")):
        return db.item_id(item)
    return common_properties(initial_ids(item))


def nutrition_sum(game):
    return sum((identity(game, item).get("nutrition") or 0) * item["qty"]
               for _, item in inventory(game, True) if item_type(item) == "food" and noncursed(item))


def weight_sum(game):
    result = 0
    for _, item in inventory(game):
        contents = item.get("items")
        bag = contents is not None and (identity(game, item) or {}).get("name") == "bag of holding"
        for current in [*(contents or ()), item]:
            ids = initial_ids(current)
            weight = ids[0].get("weight") if ids else None
            if weight is not None:
                if current != item and bag:
                    weight = 2 * weight if item.get("buc") == "cursed" else 1 + weight * (0.25 if item.get("buc") == "blessed" else 0.5)
                result += current["qty"] * weight
    return result
