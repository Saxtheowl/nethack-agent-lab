"""Faithful rewrite of bothack.item (BotHack by krajj7).

An Item is a dict produced by parse_label.  Keyword keys are plain strings.
"""

import re

from . import itemtype as it

_item_fields = ["slot", "qty", "buc", "grease", "poison", "erosion1",
                "erosion2", "proof", "used", "eaten", "diluted", "enchantment",
                "name", "generic", "specific", "recharges", "charges", "candles",
                "lit-candelabrum", "lit", "laid", "chained", "quivered", "offhand",
                "offhand-wielded", "wielded", "worn", "cost1", "cost2", "cost3"]

_item_re = (r"^(?:([\w\#\$])\s[+-]\s)?\s*([Aa]n?|[Tt]he|\d+)?\s*"
            r"(blessed|(?:un)?cursed|(?:un)?holy)?\s*(greased)?\s*(poisoned)?\s*"
            r"((?:(?:very|thoroughly) )?(?:burnt|rusty))?\s*"
            r"((?:(?:very|thoroughly) )?(?:rotted|corroded))?\s*"
            r"(fixed|(?:fire|rust|corrode)proof)?\s*(partly used)?\s*"
            r"(partly eaten)?\s*(diluted)?\s*([+-]\d+)?\s*"
            r"(?:(?:pair|set) of)?\s*\b(.*?)\s*(?:called (.*?))?\s*"
            r"(?:named (.*?))?\s*(?:\((\d+):(-?\d+)\))?\s*"
            r"(?:\((no|[1-7]) candles?(, lit| attached)\))?\s*(\(lit\))?\s*"
            r"(\(laid by you\))?\s*(\(chained to you\))?\s*(\(in quiver\))?\s*"
            r"(\(altern.*?\)?)?\s*(\(wielded i.*?\))?\s*"
            r"(\((?:weapo?n?|wield?e?d?).*?\)?)?\s*"
            r"(\((?:bei?n?g?|emb?e?d?d?e?d?|on?).*?\)?)?\s*"
            r"(?:\(unpaid, (\d+) zorkmids?\)|\((\d+) zorkmids?\)|, no charge(?:, .*)?|"
            r", (?:price )?(\d+) zorkmids( each)?(?:, .*)?)?\.?\s*$")


def _erosion(s):
    if s and any(w in s for w in ["burnt", "rusty", "rotted", "corroded"]):
        if "very" in s:
            return 2
        if "thoroughly" in s:
            return 3
        return 1
    return None


def parse_label(label):
    """bothack.item/parse-label."""
    norm = re.sub(r"(?:the )?(.*) partly eaten corpse$", r"partly eaten \1 corpse",
                  label)
    m = re.match(_item_re, norm)
    raw = dict(zip(_item_fields, m.groups() if m else [None] * len(_item_fields)))

    res = dict(raw)

    buc = res.get("buc")
    name = res.get("name") or ""
    m2 = re.match(r"^potions? of ((?:un)?holy) water$", name)
    if m2:
        res["name"] = "potion of water"
        res["buc"] = "blessed" if m2.group(1) == "holy" else "cursed"

    nm = re.match(r"([^(]*)( \(.*)?$", res["name"] or "")
    res["name"] = nm.group(1) if nm else res["name"]
    res["name"] = it.jap_eng.get(res["name"], res["name"])
    res["name"] = it.plural_to_singular().get(res["name"], res["name"])

    res["lit"] = res.get("lit") or (
        res.get("lit-candelabrum") and "lit" in res["lit-candelabrum"])

    in_use = res.get("wielded") or res.get("worn")
    res["in-use"] = in_use

    cost = None
    for c in ("cost1", "cost2", "cost3"):
        if res.get(c):
            cost = c
            break
    res["cost"] = cost

    qty = res.get("qty")
    if qty and re.search(r"[0-9]+", qty):
        res["qty"] = int(qty)
    else:
        res["qty"] = 1

    if raw.get("candles") is not None:
        res["candles"] = 0 if raw["candles"] == "no" else int(raw["candles"])

    for f in ("buc", "proof"):
        res[f] = res[f].lower() if res.get(f) else res[f]

    if not res.get("buc") and (raw.get("charges") or raw.get("enchantment")
                               or res.get("name") == "Amulet of Yendor"):
        res["buc"] = "uncursed"

    for f in ("cost", "enchantment", "charges", "recharges"):
        if res.get(f) is not None and res.get(f) != "":
            res[f] = int(res[f])

    e1 = _erosion(raw.get("erosion1"))
    e2 = _erosion(raw.get("erosion2"))
    res["erosion"] = max(e1 or 0, e2 or 0)

    for f in ("cost1", "cost2", "cost3", "lit-candelabrum", "erosion1",
              "erosion2", "slot"):
        res.pop(f, None)

    out = {"label": label}
    for k, v in res.items():
        if v is not None:
            out[k] = v
    return out


# buc predicates
def safe_buc(item):
    return item.get("buc") in ("uncursed", "blessed")


def cursed(item):
    return item.get("buc") == "cursed"


def uncursed(item):
    return item.get("buc") == "uncursed"


def noncursed(item):
    return item.get("buc") != "cursed"


def blessed(item):
    return item.get("buc") == "blessed"


def single(item):
    return item.get("qty") == 1


def corpse(item):
    return re.search(r" corpses?\b", item.get("name") or "") is not None


def corpse_monster(item):
    return it.name_to_item(item.get("name") or "")


def can_take(item):
    return not item.get("cost")


def candle(item):
    return "candle" in (item.get("name") or "")


def shield(item):
    return item.get("subtype") == "shield"


def gloves(item):
    return item.get("subtype") == "gloves"


def boots(item):
    return item.get("subtype") == "boots"


def container(item):
    return re.search(r"^bag\b|sack$|chest$|box$", item.get("name") or "") is not None


def bag(item):
    return re.search(r"^bag\b|sack$", item.get("name") or "") is not None


def know_contents(item):
    return (not container(item) or item.get("name") == "bag of tricks"
            or "items" in item)


def boh(item):
    return item.get("name") == "bag of holding"


def water(item):
    return item.get("name") == "potion of water"


def holy_water(item):
    return water(item) and item.get("buc") == "blessed"


def explorable_container(item):
    return (not know_contents(item) and not item.get("locked")
            and (noncursed(item) or not boh(item)))


candelabrum = "Candelabrum of Invocation"
bell = "Bell of Opening"
book = "Book of the Dead"


def dagger(item):
    return "dagger" in (item.get("name") or "")


def ammo(item):
    n = item.get("name") or ""
    return "arrow" in n or "bolt" in n


def dart(item):
    return "dart" in (item.get("name") or "")


def short_sword(item):
    return "short sword" in (item.get("name") or "")


def rocks(item):
    return item.get("name") == "rock"


def egg(item):
    return re.search(r"\begg\b", item.get("name") or "") is not None


def artifact(item):
    return bool(it.name_to_item(item.get("specific") or "") or
                it.name_to_item(item.get("name") or ""))


def nw_ratio(item):
    pass


def gold(item):
    return item.get("name") == "gold piece"


def key(item):
    return "key" in (item.get("name") or "")


def enchant(item):
    return item.get("enchantment") or 0


def charged(item):
    return (item.get("specific") != "empty"
            and not ((item.get("charges") or 1) == 0))


def recharged(item):
    return (item.get("specific") == "recharged"
            or not ((item.get("recharges") or 0) == 0))


def pick(item):
    return item.get("name") in ("pick-axe", "dwarvish mattock")


def two_handed(item):
    pass


def label_to_item(label):
    return parse_label(label)


def slot_item(s):
    """(slot-item "h - an octagonal amulet (being worn)") -> (char, Item)."""
    m = re.match(r"\s*(.)  ?[-+#] (.*)\s*$", s)
    if m:
        return m.group(1), label_to_item(m.group(2))
    return None