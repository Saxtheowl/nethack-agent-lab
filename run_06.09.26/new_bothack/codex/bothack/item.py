"""Translation of item.clj label parsing and predicates (GPL-2.0, 2026-09-06)."""
import re
from .catalog import data


def erosion(value):
    if value and any(word in value for word in ("burnt", "rusty", "rotted", "corroded")):
        return 2 if "very" in value else 3 if "thoroughly" in value else 1
    return 0


def parse_label(label):
    norm = re.sub(r"(?:the )?(.*) partly eaten corpse$", r"partly eaten \1 corpse", label)
    match = re.search(data()["regex"]["item"], norm, flags=re.ASCII)
    if not match:
        raise ValueError(f"Unparseable item label: {label!r}")
    raw = dict(zip(data()["item-fields"], match.groups()))
    result = dict(raw)
    if holy := re.search(r"^potions? of ((?:un)?holy) water$", result["name"]):
        result.update(name="potion of water", buc="blessed" if holy[1] == "holy" else "cursed")
    result["name"] = re.search(r"([^(]*)( \(.*)?$", result["name"])[1]
    result["name"] = data()["japanese"].get(result["name"], result["name"])
    result["name"] = data()["plural"].get(result["name"], result["name"])
    result["lit"] = result["lit"] or ("lit" in result["lit-candelabrum"] if result["lit-candelabrum"] is not None else None)
    result["in-use"] = result["wielded"] or result["worn"]
    result["cost"] = result["cost1"] or result["cost2"] or result["cost3"]
    result["qty"] = int(result["qty"]) if result["qty"] and re.search(r"[0-9]+", result["qty"]) else 1
    if raw["candles"] is not None:
        result["candles"] = 0 if raw["candles"] == "no" else int(raw["candles"])
    for key in ("buc", "proof"):
        if result[key] is not None:
            result[key] = result[key].lower()
    if result["buc"] is None and (raw["charges"] or raw["enchantment"] or result["name"] == "Amulet of Yendor"):
        result["buc"] = "uncursed"
    for key in ("cost", "enchantment", "charges", "recharges"):
        if result[key]:
            result[key] = int(result[key])
    result["erosion"] = max(erosion(result["erosion1"]), erosion(result["erosion2"]))
    for key in ("cost1", "cost2", "cost3", "lit-candelabrum", "erosion1", "erosion2", "slot"):
        result.pop(key)
    return {"label": label} | {key: value for key, value in result.items() if value is not None}


def safe_buc(item):
    return item.get("buc") in ("blessed", "uncursed")


def label_to_item(label):
    """Construct the original Item record, including its explicit nil fields."""
    fields = 'label name generic specific qty buc erosion proof enchantment charges recharges in-use cost'
    return dict.fromkeys(fields.split()) | parse_label(label)


def noncursed(item):
    return item.get("buc") != "cursed"


def corpse(item):
    return bool(re.search(r" corpses?\b", item["name"]))


def container(item):
    return bool(re.search(r"^bag\b|sack$|chest$|box$", item["name"]))


def bag(item):
    return bool(re.search(r"^bag\b|sack$", item["name"]))


def know_contents(item):
    return not container(item) or item["name"] == "bag of tricks" or item.get("items") is not None
