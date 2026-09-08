"""Faithful rewrite of bothack.itemid (BotHack by krajj7).

The original is a core.logic program, but every relation is a set of ground
facts and every goal is a deterministic conda/condu chain, so it translates
directly to explicit filters.  Candidate item ids for each appearance are
enumerated in the exact core.logic order (see _data.json "appearance-candidates").
"""

from ._data import data as _load_data
from . import itemtype as it

# observable props understood by the original (bothack.itemid/observable-props)
OBSERVABLE_PROPS = {"engrave", "target", "hardness", "autoid", "food"}


def clj_eq(a, b):
    """Clojure = semantics: True == 1 is false in Clojure, true in Python."""
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    return a == b


def _d():
    return _load_data()


def _record(name):
    return it.name_to_item(name)


# ---------------------------------------------------------------------------
# appearance / names / candidates (extracted data)

def item_names(name=None):
    nm = _d()["item-names"]
    if name is None:
        return nm
    return nm.get(name)


def names_set():
    return set(_d()["names"])


def exclusive_appearances():
    return set(_d()["exclusive-appearances"])


def blind_appearances_map():
    return _d()["blind-appearances"]


# bothack.itemid/blind-appearances (lines 69-77): {generic-name: [kind, glyph]}.
# The generic "unseen item" has only a glyph and its kind, no name.
_BLIND = {
    "stone": ("gem", "*"), "gem": ("gem", "*"), "potion": ("potion", "!"),
    "wand": ("wand", "/"), "spellbook": ("spellbook", "+"),
    "scroll": ("scroll", "?"),
}


def _blind_item(generic_name):
    kind, glyph = _BLIND[generic_name]
    return {"kind": kind, "glyph": glyph, "name": None}


def appearance_candidates():
    return _d()["appearance-candidates"]


def appearance_of(item):
    """bothack.itemid/appearance-of."""
    name = item.get("name") or ""
    if item_names().get(name) and item.get("generic"):
        return item.get("generic")
    specific = item.get("specific")
    if specific:
        rec = it.name_to_item(specific)
        if rec is not None:
            return rec["name"]
    return name


def knowable_appearance(appearance):
    """bothack.itemid/knowable-appearance?."""
    if not isinstance(appearance, str):
        return False
    if appearance in blind_appearances_map():
        return False
    return appearance in names_set() or appearance in exclusive_appearances()


def initial_ids(item, n=False):
    """bothack.itemid/initial-ids: n or all possible ItemTypes ignoring
    discoveries (given an item's appearance)."""
    a = appearance_of(item)
    if a is None:
        return []
    if a in _BLIND:
        return [_blind_item(a)]
    known = _record(a)
    if known is not None:
        return [known]
    recs = [r for r in (_record(c) for c in appearance_candidates().get(a, []))
            if r is not None]
    if n:
        return recs[:n]
    return recs


def item_type(item):
    if item is None:
        return None
    recs = initial_ids(item, 1)
    return recs[0].get("kind") if recs else None


def item_subtype(item):
    if item is None:
        return None
    recs = initial_ids(item, 1)
    return recs[0].get("subtype") if recs else None


def item_weight(item):
    if item is None:
        return None
    recs = initial_ids(item, 1)
    return recs[0].get("weight") if recs else None


# ---------------------------------------------------------------------------
# discoveries

def new_discoveries():
    return {"discovery": [], "props": [], "costs": []}


def _facts(game):
    return game.get("discoveries") or new_discoveries()


def cha_group(cha):
    """bothack.itemid/cha-group."""
    if cha < 6:
        return 5
    if cha < 8:
        return 7
    if cha < 11:
        return 10
    if cha < 16:
        return 15
    if cha < 18:
        return 17
    if cha < 19:
        return 18
    return 25


def _direct_discoveries(game, appearance):
    return [f[1] for f in _facts(game)["discovery"] if f[0] == appearance]


def add_fact(game, rel, appearance, *args):
    key = {"discovery": "discovery",
           "appearance-prop-val": "props",
           "appearance-cha-cost": "costs"}[rel]
    facts = _facts(game)
    newlst = list(facts[key]) + [tuple([appearance] + list(args))]
    if newlst == facts[key]:
        return game
    newd = {"discovery": list(facts["discovery"]),
            "props": list(facts["props"]),
            "costs": list(facts["costs"])}
    newd[key] = newlst
    res = dict(game)
    res["discoveries"] = newd
    res = add_eliminated(res, appearance)
    return res


def add_eliminated(game, appearance):
    if not isinstance(appearance, str):
        return game
    if appearance in _BLIND or _record(appearance) is not None:
        return game
    room = _possible_names(game, appearance)
    if len(room) == 1 and room[0] not in _direct_discoveries(game, appearance):
        return add_discovery_impl(game, appearance, room[0])
    return game


def add_discovery_impl(game, appearance, id):
    if appearance == id or not knowable_appearance(appearance):
        return game
    id = it.jap_eng.get(id, id)
    return add_fact(game, "discovery", appearance, id)


def add_discovery(game, appearance, id):
    return add_discovery_impl(game, appearance, id)


def add_discoveries(game, discoveries):
    for appearance, id in discoveries:
        game = add_discovery(game, appearance, id)
    return game


def _item_prop(rec, prop):
    if prop == "engrave":
        return rec.get("name")
    if prop == "autoid":
        return bool(rec.get("auto-id", False))
    if prop == "target":
        return rec.get("zaptype")
    if prop == "hardness":
        return rec.get("hardness")
    if prop == "food":
        return rec.get("kind") == "food"
    return None


def _passes_prop(facts, rec):
    for f in facts["props"]:
        prop, propval = f[1], f[2]
        v = _item_prop(rec, prop)
        if v is None:
            if propval is not False:
                return False
        elif not clj_eq(v, propval):
            return False
    return True


def _passes_price(facts, rec, cha):
    if not facts["costs"]:
        return True
    price = rec.get("price")
    kind = rec.get("kind")
    ench = [0, 1, 2, 3, 4] if kind == "armor" else [0]
    for f in facts["costs"]:
        f_cha, f_cost = f[1], f[2]
        if f_cha != cha_group(cha):
            continue
        for e in ench:
            if price is not None and (price + 10 * e) == f_cost:
                return True
    return False


def _possible_names(game, appearance):
    a = appearance
    if a in _BLIND:
        return [a]
    if _record(a) is not None and a not in item_names() and \
            a not in exclusive_appearances():
        return [_record(a)["name"]]
    direct = _direct_discoveries(game, a)
    if direct:
        return direct
    facts = _facts(game)
    cha = ((game.get("player") or {}).get("stats") or {}).get("cha")
    out = []
    for name in appearance_candidates().get(a, []):
        rec = _record(name)
        if rec is None:
            continue
        if _passes_prop(facts, rec) and _passes_price(facts, rec, cha):
            out.append(name)
    return out


def possible_ids(game, item, n=False):
    a = appearance_of(item)
    if a is None:
        return []
    if a in _BLIND:
        return [_blind_item(a)]
    recs = [r for r in (_record(c) for c in _possible_names(game, a))
            if r is not None]
    if n:
        return recs[:n]
    return recs


def _merge_records(recs):
    recs = list(recs)
    if not recs:
        return None
    r = dict(recs[0])
    for s in recs[1:]:
        for k in list(dict(s).keys()) + list(r.keys()):
            if k in r and k in s:
                if not clj_eq(r[k], s[k]):
                    r[k] = None
            else:
                r.pop(k, None)
    return r


def item_id(game, item):
    if item is None:
        return None
    return _merge_records(possible_ids(game, item))


def item_name(game, item):
    if item is None:
        return None
    id_ = item_id(game, item)
    return id_.get("name") if id_ else None


def know_id(game, item):
    return item_name(game, item) is not None


def possible_names(game, item):
    if item is None:
        return None
    return [r.get("name") for r in possible_ids(game, item)]


def add_prop_discovery(game, appearance, prop, propval):
    if not knowable_appearance(appearance):
        return game
    return add_fact(game, "appearance-prop-val", appearance, prop, propval)


def add_observed_cost(game, appearance, cha_or_cost=None, cost=None, sell=False):
    """Overloaded: (game appearance cost) / (game appearance cost sell) /
    (game appearance cha cost sell)."""
    if cost is None:
        cha = ((game.get("player") or {}).get("stats") or {}).get("cha")
        cost = cha_or_cost
    else:
        cha = cha_or_cost
    if not knowable_appearance(appearance):
        return game
    g = 0 if sell else cha_group(cha)
    return add_fact(game, "appearance-cha-cost", appearance, g, cost)


def know_price(game, item):
    id_ = item_id(game, item)
    if id_ is not None and id_.get("price") is not None:
        return True
    a = appearance_of(item)
    return any(f[0] == a for f in _facts(game)["costs"])


def could_be(game, id, item):
    return any(r.get("name") == id for r in possible_ids(game, item))


def name_for(game, item):
    name = item.get("name")
    variants = item_names().get(name)
    if not variants:
        return None
    used = game.get("used-names") or set()
    for v in variants:
        if v not in used:
            return v
    return None


def name_variants(name):
    import re
    base = re.sub(r"(.*)[0-9]+", r"\1", name)
    return item_names().get(base)


def forget_names(game, names):
    # best-effort; the original retracts facts for used names
    return game


def add_intrinsic(player, intrinsic):  # convenience used elsewhere
    return player