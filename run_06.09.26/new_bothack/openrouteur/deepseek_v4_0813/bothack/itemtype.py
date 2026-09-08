"""Faithful rewrite of bothack.itemtype (BotHack by krajj7).

Item types are plain dicts loaded from _data.json.  The JSON keys are strings
('name', 'glyph', 'price', 'weight', 'kind', ...)."""

from ._data import data

# item kinds (bothack.itemtype/item-kinds keys), in original order
ITEM_KINDS = ["spellbook", "amulet", "weapon", "wand", "gem", "armor", "food",
              "other", "tool", "statue", "scroll", "ring", "potion"]

blind_plurals = {"stones": "stone", "gems": "gem", "potions": "potion",
                 "wands": "wand", "spellbooks": "spellbook", "scrolls": "scroll"}

jap_eng = {
    "wakizashi": "short sword", "ninja-to": "broadsword", "nunchaku": "flail",
    "naginata": "glaive", "osaku": "lock pick", "koto": "wooden harp",
    "shito": "knife", "tanko": "plate mail", "kabuto": "helmet",
    "yugake": "leather gloves", "gunyoki": "food ration",
    "potion of sake": "potion of booze", "potions of sake": "potions of booze",
}


def _kind_of(item):
    return item.get("kind")


def _ensure_loaded():
    data()


def _items_list():
    return data()["items"]


def kw_to_itemtype(kind):
    """Return list of item records for a kind (bothack.kw->itemtype over a
    var holding the list)."""
    items = {}
    for it in _items_list():
        items.setdefault(it["kind"], []).append(it)
    return items.get(kind, [])


def _build_name_index():
    d = data()
    name_to_item = {}
    for it in d["items"]:
        name = it.get("name")
        if name is not None:
            name_to_item[name] = it
        fullname = it.get("fullname")
        if fullname:
            name_to_item[fullname] = it
    return name_to_item


def name_to_item(name):
    return _build_name_index().get(name)


def all_items():
    return _items_list()


def plural_to_singular():
    return data()["plural->singular"]


def item_kinds_map():
    result = {}
    for it in _items_list():
        result.setdefault(it["kind"], []).append(it)
    return result