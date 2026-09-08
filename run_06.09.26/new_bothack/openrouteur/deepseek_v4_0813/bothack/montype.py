"""Faithful rewrite of bothack.montype (BotHack by krajj7).

Monster types are dicts loaded from _data.json.  Set-valued fields (gen-flags,
resistances, resistances-conferred, tags) are stored as sorted lists in the
JSON; membership is tested with `in`.
"""

from ._data import data


def monster_types():
    return data()["monster-types"]


def appearance_to_monster():
    """glyph -> color -> monster name (only unambiguous appearances)."""
    return data()["appearance->monster"]


_name_index = None


def name_to_monster(name):
    """Returns MonsterType dict or None (bothack.montype/name->monster)."""
    global _name_index
    if _name_index is None:
        idx = {}
        for m in data()["monster-types"]:
            n = m["name"]
            idx[n] = m
            idx[n.lower()] = m
        _name_index = idx
    if name is None:
        return None
    return _name_index.get(name.lower())


def _tags(m):
    return m.get("tags") or []


def _resistances(m):
    return m.get("resistances") or []


def passive_type(m):
    return all(a["type"] == "passive" for a in m["attacks"])


def corrosive_type(m):
    return any(a["type"] == "passive" and a["damage-type"] in ("corrode", "acid")
               for a in m["attacks"])


def has_drowning_attack(m):
    return any(a["damage-type"] == "wrap" for a in m["attacks"])


# IMonsterType accessor methods (computed the same way as the original)
def is_poisonous(m):
    return bool(m.get("poisonous") or "poisonous" in _tags(m))


def is_unique(m):
    return bool("unique" in (m.get("gen-flags") or []))


def has_hands(m):
    return not ("nohands" in _tags(m) or "nolimbs" in _tags(m))


def is_hostile(m):
    return bool("hostile" in _tags(m))


def is_covetous(m):
    return bool("covetous" in _tags(m))


def respects_elbereth(m):
    return "elbereth" not in _resistances(m)


def sees_invisible(m):
    return bool("see-invis" in _tags(m))


def is_follower(m):
    return bool("follows" in _tags(m))


def is_werecreature(m):
    return bool("were" in _tags(m))


def is_mimic(m):
    return " mimic" in m["name"]


def is_priest(m):
    return "priest" in m["name"]


def is_shopkeeper(m):
    return m["name"] == "shopkeeper"


def is_passive(m):
    return bool(passive_type(m))


def is_corrosive(m):
    return bool(corrosive_type(m))


def is_sessile(m):
    return bool("sessile" in _tags(m))


def has_drowning(m):
    return bool(has_drowning_attack(m))


def is_rider(m):
    return bool("rider" in _tags(m))


def is_undead(m):
    return bool("undead" in _tags(m))


def is_strong(m):
    return bool("strong" in _tags(m))


def is_nasty(m):
    return bool("nasty" in _tags(m))


def is_human(m):
    return bool("human" in _tags(m))


def is_guard(m):
    return bool("guard" in _tags(m))


def is_mindless(m):
    return bool("mindless" in _tags(m))


def infravisible(m):
    return bool("infravisible" in _tags(m))