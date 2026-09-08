"""Faithful rewrite of bothack.monster (BotHack by krajj7).

A Monster is a dict: x, y, known, glyph, color, type (MonsterType dict or None),
awake, friendly, peaceful, remembered, plus optional first-known.
"""

from . import montype as mt
from .frame import non_inverse, inverse_color


def typename(m):
    t = m.get("type")
    return t["name"] if t else None


def hostile(m):
    return not m.get("peaceful") and not m.get("friendly")


def default_peaceful(monster_type):
    if monster_type is None:
        return None
    if "hostile" in (monster_type.get("tags") or []):
        return False
    return True if "peaceful" in (monster_type.get("tags") or []) else None


def shopkeeper(m):
    return typename(m) == "shopkeeper"


def high_priest(m):
    return typename(m) == "high priest"


def demon_lord(m):
    t = m.get("type")
    if not t:
        return False
    return {"demon", "prince"}.issubset(set(t.get("tags") or []))


def oracle(m):
    return typename(m) == "Oracle"


def medusa(m):
    return typename(m) == "Medusa"


def pudding(m):
    return typename(m) in ("black pudding", "brown pudding")


def unique(m):
    t = m.get("type")
    return bool(t and "unique" in (t.get("gen-flags") or []))


def priest(m):
    n = typename(m)
    return "priest" in n if n else False


def unicorn(m):
    n = typename(m)
    return " unicorn" in n if n else False


def mimic(m):
    n = typename(m)
    return " mimic" in n if n else False


def werecreature(m):
    t = m.get("type")
    return bool(t and "were" in (t.get("tags") or []))


def drowner(m):
    t = m.get("type")
    return mt.has_drowning(t) if t else False


def flies(m):
    t = m.get("type")
    return bool(t and "fly" in (t.get("tags") or []))


def covetous(m):
    t = m.get("type")
    if not t:
        return False
    tags = set(t.get("tags") or [])
    return bool(tags & {"covetous", "wants-arti", "wants-amulet", "wants-book"})


def steals(m):
    if covetous(m):
        return True
    t = m.get("type")
    if t:
        return any(a["damage-type"] in ("steal-amulet", "steal-items")
                   for a in t.get("attacks", []))
    return False


def ignores_e(m):
    t = m.get("type")
    return bool(t and "elbereth" in (t.get("resistances") or []))


def sees_invisible(m):
    return mt.sees_invisible(m)


def follower(m):
    t = m.get("type")
    return bool(t and "follows" in (t.get("tags") or []))


def amphibious(m):
    t = m.get("type")
    return bool(t and "amphibious" in (t.get("tags") or []))


def mindless(m):
    return mt.is_mindless(m)


def undead(m):
    return mt.is_undead(m)


def sessile(m):
    return mt.is_sessile(m)


def guard(m):
    return mt.is_guard(m)


def human(m):
    return mt.is_human(m)


def nasty(m):
    return mt.is_nasty(m)


def rider(m):
    return mt.is_rider(m)


def strong(m):
    return mt.is_strong(m)


def infravisible(m):
    return mt.infravisible(m)


def spellcaster(m):
    t = m.get("type")
    if not t:
        return False
    return any(a["type"] == "magic" for a in t.get("attacks", []))


def passive(m):
    t = m.get("type")
    return mt.is_passive(t) if t else False


def corrosive(m):
    t = m.get("type")
    return mt.is_corrosive(t) if t else False


def slow(m):
    t = m.get("type")
    return bool(t and t.get("speed", 0) < 7)


def leprechaun(m):
    return typename(m) == "leprechaun"


def titan(m):
    return typename(m) == "titan"


def rodney(m):
    return typename(m) == "Wizard of Yendor"


def known_monster(x, y, type):
    return {
        "x": x, "y": y,
        "glyph": type["glyph"], "color": type["color"],
        "known": 0, "first-known": 0,
        "type": type, "awake": False, "friendly": False,
        "peaceful": default_peaceful(type), "remembered": True,
    }


def new_monster(x, y, known, glyph, color):
    am = mt.appearance_to_monster()
    type = am.get(glyph, {}).get(None if color is None else color) if glyph in am else None
    type = am.get(glyph, {}).get(color, None) if type is None and glyph in am else type
    return {
        "x": x, "y": y, "known": known, "first-known": known,
        "glyph": glyph, "color": non_inverse(color),
        "type": type,
        "friendly": bool(inverse_color(color)),
        "peaceful": default_peaceful(type),
        "remembered": False,
    }


def unknown_monster(x, y, turn):
    return new_monster(x, y, turn, "I", None)