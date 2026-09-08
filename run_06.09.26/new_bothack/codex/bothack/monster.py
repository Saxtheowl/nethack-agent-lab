"""Monster appearances, descriptions and traits from montype/monster.clj.

GPL-2.0, translated 2026-09-06. Retains upstream ambiguities and return shapes.
"""
from functools import lru_cache
import re
from .catalog import data
from .frame import inverse, non_inverse


@lru_cache(maxsize=1)
def by_name_map():
    return {m["name"].lower(): m for m in data()["monsters"]}


def by_name(name):
    return by_name_map().get(name.lower())


@lru_cache(maxsize=1)
def by_appearance():
    result = {}
    ambiguous = object()
    for m in data()["monsters"]:
        key = m["glyph"], m["color"]
        result[key] = ambiguous if key in result else m
    result = {k: v for k, v in result.items() if v is not ambiguous}
    result[" ", None] = result.get(("X", None))
    return result


def strip_modifier(desc):
    for prefix in ("invisible ", "saddled "):
        if desc.startswith(prefix):
            return desc[len(prefix):]
    return desc


def by_description(text):
    desc = text
    for prefix in ("a ", "an ", "the ", "your "):
        if desc.startswith(prefix):
            desc = desc[len(prefix):]
            break
    for prefix in ("tame ", "peaceful ", "guardian "):
        if desc.startswith(prefix):
            if prefix != "guardian " or " naga" not in desc:
                desc = desc[len(prefix):]
            break
    desc = strip_modifier(desc)
    ghost_or_called = bool(re.search("ghost|called", desc))
    if desc == "tail of a peaceful long worm": return by_name("long worm tail")
    if re.search(r"^(?:the )?high priest(?:ess)?$", desc): return by_name("high priest")
    if desc == "mimic": return by_name("large mimic")
    if not re.search("Minion of Huhetotl| Yendor", desc) and not ghost_or_called:
        if match := re.search(r"(.*) of (.*)", desc):
            subject = match[1]
            if re.search("poohbah|priest|priestess", subject):
                result = by_name("high priest" if "high " in subject else "aligned priest")
            else:
                result = by_name(subject[9:] if subject.startswith("guardian ") else subject)
            if result is None:
                raise ValueError(f"Failed to parse monster-of description: {text}")
            return result
    if not ghost_or_called and "Neferet the Green" not in desc and "Vlad the Impaler" not in desc:
        if match := re.search(r"(.*) the (.*)", desc):
            if result := by_name(strip_modifier(match[2])):
                return result
    if match := re.search(r"(.*) called (.*)", desc):
        if result := by_name(match[1]): return result
    if re.search(r"'?s? ghost", desc): return by_name("ghost")
    if "coyote - " in desc: return by_name("coyote")
    if desc in data()["shopkeepers"]: return by_name("shopkeeper")
    if result := by_name(desc): return result
    # Original rank->monster actually returns the role's name, not a record.
    if result := data()["rank-roles"].get(desc.lower()): return result
    raise ValueError(f"Failed to parse monster description: {text}")


def default_peaceful(monster_type):
    tags = (monster_type or {}).get("tags", ())
    return False if "hostile" in tags else "peaceful" if "peaceful" in tags else None


def new_monster(x, y, turn, glyph, color):
    mtype = by_appearance().get((glyph, color))
    return dict(x=x, y=y, known=turn, glyph=glyph, color=non_inverse(color), type=mtype,
                awake=None, friendly=inverse(color), peaceful=default_peaceful(mtype), remembered=False,
                **{"first-known": turn})


def known_monster(x, y, monster_type):
    return dict(x=x, y=y, known=0, glyph=monster_type["glyph"], color=monster_type["color"], type=monster_type,
                awake=False, friendly=False, peaceful=default_peaceful(monster_type), remembered=True,
                **{"first-known": 0})


def hostile(monster):
    monster = monster or {}
    return not monster.get("peaceful") and not monster.get("friendly")


def covetous(monster):
    return bool({"covetous", "wants-arti", "wants-amulet", "wants-book"}.intersection((monster.get("type") or {}).get("tags", ())))


def passive(monster_type):
    return all(a["type"] == "passive" for a in (monster_type or {}).get("attacks", ()))


def corrosive(monster_type):
    return any(a["type"] == "passive" and a["damage-type"] in {"corrode", "acid"} for a in (monster_type or {}).get("attacks", ()))


def drowning_attack(monster_type):
    return any(a["damage-type"] == "wrap" for a in (monster_type or {}).get("attacks", ()))
