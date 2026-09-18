"""Port of bothack.itemid.

The original expresses item identification as a core.logic program.  The
relations it uses are all ground facts and the goals are deterministic
soft-cut (conda/condu) chains, so they translate directly into the explicit
filters below - including the original's "any observed price/property fact may
match" semantics of the conda in pricec/propc.
"""
import logging
import re

from . import itemtype as it
from .clj import clj_assert
from .clj import assoc, dissoc, update
from .itemtype import (items, name_to_item, exclusive_appearances, jap_to_eng,
                       blank_itemtype)
from .util import find_first, re_first_group

log = logging.getLogger('bothack.itemid')

OBSERVABLE_PROPS = {'engrave', 'target', 'hardness', 'autoid', 'food'}


# ----------------------------------------------------------- generated names
def _build_item_names():
    """{lamp => [lamp1 lamp2], bag => [bag1 ... bag4], ...}"""
    counts = {}
    for i in items:
        for a in (i.get('appearances') or []):
            if (a in exclusive_appearances or a == "Amulet of Yendor"
                    or a == "egg" or a == "tin"):
                continue
            counts.setdefault(a, []).append(a + str(len(counts[a]) + 1)
                                            if a in counts else a + "1")
    return {a: v for a, v in counts.items() if len(v) != 1}


item_names = _build_item_names()
names = set()
for _v in item_names.values():
    names.update(_v)


# --------------------------------------------------------------- price table
def _round36(tmp, multiplier, divisor):
    """shk.c 3.6.7: tmp *= multiplier; if (divisor > 1)
    tmp = (((tmp * 10) / divisor) + 5) / 10"""
    tmp *= multiplier
    if divisor > 1:
        tmp = ((tmp * 10) // divisor + 5) // 10
    return tmp


# charisma group -> (multiplier, divisor), shk.c get_cost() 3.6.7
_CHA_FACTORS36 = {5: (2, 1), 7: (3, 2), 10: (4, 3), 15: (1, 1),
                  17: (3, 4), 18: (2, 3), 25: (1, 2)}


def _cost_data():
    """(base price, charisma group, observed price) triples that are
    possible.  3.6.7 accumulates one multiplier/divisor and rounds once
    (3.4.3, which the original table modelled, applied integer divisions
    one after another, so prices could differ by one zorkmid and every
    candidate identity got excluded)."""
    res = set()
    for cost in range(501):
        base = cost if cost else 5          # get_cost: if (!tmp) tmp = 5
        for cha, (cm, cd) in _CHA_FACTORS36.items():
            for um, ud in ((1, 1), (4, 3)):         # unidentified surcharge
                for sm, sd in ((1, 1), (4, 3)):     # dunce cap / tourist
                    v = max(_round36(base, cm * um * sm, cd * ud * sd), 1)
                    res.add((cost, cha, v))
                    # angry shopkeeper surcharge, added after the rounding
                    # (a potion of 50 sold 90: 67 + 23, full-w01 g005)
                    res.add((cost, cha, v + (v + 2) // 3))
        # selling: set_cost() - half (a third for dunce/tourist), and an
        # unidentified item may get 3/4 of that
        if cost >= 1:
            for sd in (2, 3):
                for um, ud in ((1, 1), (3, 4)):
                    v = _round36(cost, um, sd * ud)
                    res.add((cost, 0, max(v, 1)))
    return res


BASE_CHA_COST = _cost_data()


def cha_group(cha):
    if cha < 3:
        return 0            # sell price
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


# ------------------------------------------------------ appearance -> id set
def _build_appearance_names():
    res = {}
    for i in items:
        if i.get('artifact') and i.get('base'):
            continue
        for a in (i.get('appearances') or []):
            res.setdefault(a, []).append(i['name'])
            for n in item_names.get(a, ()):
                res.setdefault(n, []).append(i['name'])
    return res


# The candidate order matters (item-type/subtype/weight take the first
# candidate) and core.logic enumerates a pldb index in hash order, so the
# order is taken verbatim from the original instead of being guessed.
from ._load import DATA as _DATA                                  # noqa: E402

_ORDER = _DATA['appearance-names']


def _ordered(a, ids):
    order = _ORDER.get(a) or []
    idx = {n: i for i, n in enumerate(order)}
    return sorted(ids, key=lambda n: idx.get(n, len(order)))


APPEARANCE_NAMES = {a: _ordered(a, ids)
                    for a, ids in _build_appearance_names().items()}
# 3.6.7 appearances added in itemtype._patch_appearances_36(): their
# candidate order is the one of the equivalent 3.4.3 appearance
for _a in set(APPEARANCE_NAMES) - set(_ORDER):
    import re as _re
    _base = None
    if _a.startswith("scroll labeled "):
        _suffix = _re.search(r"([0-9]*)$", _a).group(1)
        _base = "scroll labeled FOOBIE BLETCH" + _suffix
    elif _a.startswith("leathery spellbook"):
        _base = "leather spellbook" + _a[len("leathery spellbook"):]
    if _base is not None and _base in _ORDER:
        _ORDER[_a] = list(_ORDER[_base])
    elif _base is not None:
        _ORDER[_a] = list(APPEARANCE_NAMES[_a])
    APPEARANCE_NAMES[_a] = _ordered(_a, APPEARANCE_NAMES[_a])
for _a in set(_ORDER) - set(APPEARANCE_NAMES):
    if _a.startswith("leather spellbook"):
        del _ORDER[_a]
assert set(APPEARANCE_NAMES) == set(_ORDER), "appearance set mismatch"

BLIND_APPEARANCES = {
    "stone": blank_itemtype('gem', '*'),
    "gem": blank_itemtype('gem', '*'),
    "potion": blank_itemtype('potion', '!'),
    "wand": blank_itemtype('wand', '/'),
    "spellbook": blank_itemtype('spellbook', '+'),
    "scroll": blank_itemtype('scroll', '?'),
}


def knowable_appearance(appearance):
    """Does it make sense to know anything about this appearance?"""
    clj_assert(isinstance(appearance, str), 'string? appearance')
    return not (appearance in BLIND_APPEARANCES
                or (appearance not in names
                    and appearance not in exclusive_appearances))


def appearance_of(item):
    if item.get('name') in item_names and item.get('generic'):
        return item['generic']
    spec = name_to_item.get(item.get('specific'))
    if spec:
        return spec['name']
    # `(:name item)` is nil-safe in Clojure, and this is called on things that
    # are not items - `should-try?` hands it an item-*id* record, which has no
    # :name once several candidates remain
    return item.get('name')


# ------------------------------------------------------------- discoveries db
def new_discoveries():
    return {'discovery': {},        # appearance -> id
            'by_id': {},            # id -> appearance
            'prop': {},             # (appearance, prop) -> set of values
            'cost': {}}             # appearance -> set of (cha, cost)


def _prop_ok(disc, appearance, id_, prop):
    vals = disc['prop'].get((appearance, prop))
    if not vals:
        return True
    itemval = name_to_item[id_].get(prop)
    expected = False if itemval is None else itemval
    return any(_clj_eq(expected, v) for v in vals)


def _price_ok(disc, appearance, id_):
    facts = disc['cost'].get(appearance)
    if not facts:
        return True
    itm = name_to_item[id_]
    price = itm.get('price')
    if price is None:
        return False
    enchants = [0, 1, 2, 3, 4] if it.typekw(itm) == 'armor' else [0]
    for cha, cost in facts:
        for e in enchants:
            if (e * 10 + price, cha_group(cha), cost) in BASE_CHA_COST:
                return True
    return False


def _possible(disc, appearance, id_):
    if id_ not in APPEARANCE_NAMES.get(appearance, ()):
        return False
    if not knowable_appearance(appearance):
        return True
    a_of_id = disc['by_id'].get(id_)
    if a_of_id is not None:
        return a_of_id == appearance
    d = disc['discovery'].get(appearance)
    if d is not None:
        return d == id_
    return (_price_ok(disc, appearance, id_)
            and all(_prop_ok(disc, appearance, id_, p)
                    for p in sorted(OBSERVABLE_PROPS)))


def _possible_ids_raw(disc, appearance, n=None):
    res = []
    for id_ in APPEARANCE_NAMES.get(appearance, ()):
        if _possible(disc, appearance, id_):
            res.append(id_)
            if n and len(res) >= n:
                break
    return res


def _clj_eq(a, b):
    """Clojure equality: true and 1 are NOT equal (Python's == says they are)."""
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    return a == b


_MERGED_KEEP = []


def _merge_records(recs):
    recs = list(recs)
    if not recs:
        return None
    r = dict(recs[0])
    for s in recs[1:]:
        for k in list(s.keys()) + list(r.keys()):
            if k in r and k in s:
                if not _clj_eq(r[k], s[k]):
                    r[k] = None
            else:
                r.pop(k, None)
    # a merged record keeps its record type in Clojure - keep the kind (and a
    # strong reference so that id(r) stays valid for the ITEM_KIND table)
    it.ITEM_KIND[id(r)] = it.typekw(recs[0])
    _MERGED_KEEP.append(r)
    return r


_RELAXED_LOGGED = set()


def _relaxed_ids(disc, appearance, n=None):
    """Port safety net: the observed facts (shop prices, engrave messages,
    ...) excluded every identity of an appearance - one of the 3.6 fact
    models is wrong for this case.  An unknown item type makes BotHack
    forget the item's glyph and walk back to it forever (big-w01: 20 of 49
    games), so drop the price facts, then the property facts, and log the
    facts once so that the model can be fixed."""
    cands = APPEARANCE_NAMES.get(appearance, ())

    def fixed_ok(id_):
        a_of_id = disc['by_id'].get(id_)
        if a_of_id is not None:
            return a_of_id == appearance
        d = disc['discovery'].get(appearance)
        return d is None or d == id_
    no_price = [i for i in cands if fixed_ok(i) and knowable_appearance(appearance)
                and all(_prop_ok(disc, appearance, i, p)
                        for p in sorted(OBSERVABLE_PROPS))]
    ids = no_price or [i for i in cands if fixed_ok(i)] or list(cands)
    if n:
        ids = ids[:n]
    if appearance not in _RELAXED_LOGGED:
        _RELAXED_LOGGED.add(appearance)
        log.warning("identity facts exclude every candidate of %r: cost=%s "
                    "props=%s -> relaxed to %d candidates (%s)", appearance,
                    sorted(disc['cost'].get(appearance) or ()),
                    {k[1]: sorted(map(str, v)) for k, v in disc['prop'].items()
                     if k[0] == appearance},
                    len(ids), 'without prices' if no_price else
                    'without prices and properties')
    return ids


def _possibilities(game, appearance, n=None):
    unseen = BLIND_APPEARANCES.get(appearance)
    if unseen is not None:
        return [unseen]
    known = name_to_item.get(appearance)
    if known is not None:
        return [known]
    disc = game['discoveries']
    cache = game.get('_poss_cache')
    key = (appearance, n)
    if cache is not None and key in cache:
        return cache[key]
    ids = _possible_ids_raw(disc, appearance, n)
    if not ids and APPEARANCE_NAMES.get(appearance):
        ids = _relaxed_ids(disc, appearance, n)
    res = [name_to_item[i] for i in ids] if ids else None
    if res is None:
        log.error("unknown itemtype for item %s", appearance)
    if cache is not None:
        cache[key] = res
    return res


def _reset_possibilities(game):
    return assoc(game, '_poss_cache', {}, '_merge_cache', {})


def _eliminated(disc, appearance):
    """Group elimination: an appearance whose only remaining possibility is
    some id gets discovered (mirrors eliminatedo/add-eliminated)."""
    for id_ in APPEARANCE_NAMES.get(appearance, ()):
        for a in sorted(APPEARANCE_NAMES.keys()):
            if id_ not in APPEARANCE_NAMES[a]:
                continue
            if not (a in names or a in exclusive_appearances):
                continue
            if disc['discovery'].get(a) == id_:
                continue
            if not _possible(disc, a, id_):
                continue
            others = [x for x in APPEARANCE_NAMES[a]
                      if x != id_ and _possible(disc, a, x)]
            if not others:
                return a, id_
    return None


def _add_fact(game, kind, appearance, *args):
    disc = game['discoveries']
    new = dict(disc)
    if kind == 'discovery':
        (id_,) = args
        if disc['discovery'].get(appearance) == id_:
            return game
        new['discovery'] = assoc(disc['discovery'], appearance, id_)
        new['by_id'] = assoc(disc['by_id'], id_, appearance)
    elif kind == 'prop':
        prop, val = args
        cur = disc['prop'].get((appearance, prop), frozenset())
        if val in cur:
            return game
        new['prop'] = assoc(disc['prop'], (appearance, prop),
                            frozenset(cur | {val}))
    elif kind == 'cost':
        cha, cost = args
        cur = disc['cost'].get(appearance, frozenset())
        if (cha, cost) in cur:
            return game
        new['cost'] = assoc(disc['cost'], appearance,
                            frozenset(cur | {(cha, cost)}))
    res = _reset_possibilities(assoc(game, 'discoveries', new))
    return add_eliminated(res, appearance)


def add_eliminated(game, appearance):
    log.debug("group elimination for %s", appearance)
    hit = _eliminated(game['discoveries'], appearance)
    if hit:
        return add_discovery(game, hit[0], hit[1])
    return game


def add_discovery(game, appearance, id_):
    clj_assert(isinstance(appearance, str), 'string? appearance')
    if appearance == id_ or not knowable_appearance(appearance):
        return game
    id_ = jap_to_eng.get(id_, id_)
    log.debug("adding discovery: > %s < is > %s <", appearance, id_)
    return _add_fact(game, 'discovery', appearance, id_)


def add_discoveries(game, discoveries):
    for appearance, id_ in discoveries:
        game = add_discovery(game, appearance, id_)
    return game


def add_prop_discovery(game, appearance, prop, propval):
    clj_assert(prop in OBSERVABLE_PROPS, 'observable-props prop')
    if knowable_appearance(appearance):
        log.debug("for appearance %s adding observed property %s = %s",
                  appearance, prop, propval)
        return _add_fact(game, 'prop', appearance, prop, propval)
    return game


def add_observed_cost(game, appearance, cost, sell=False, cha=None):
    if cha is None:
        cha = game['player']['stats']['cha']
    clj_assert(isinstance(appearance, str), 'string? appearance')
    if knowable_appearance(appearance):
        log.debug("for appearance %s adding observed cost %s", appearance, cost)
        return _add_fact(game, 'cost', appearance,
                         0 if sell else cha_group(cha), cost)
    return game


# ------------------------------------------------------------- query helpers
def possible_ids(game, item, n=None):
    return _possibilities(game, appearance_of(item), n)


_INITIAL_GAME = {'discoveries': new_discoveries(), '_poss_cache': {},
                 '_merge_cache': {}}


def initial_ids(item, n=None):
    return _possibilities(_INITIAL_GAME, appearance_of(item), n)


_ID_CACHE = {'key': None, 'by_label': {}}


def item_id(game_or_item, item=None):
    single = item is None
    if single:
        item, game = game_or_item, _INITIAL_GAME
    else:
        game = game_or_item
    # one cache per discoveries version ('_poss_cache' is replaced whenever
    # the discoveries change); 9.3M calls in a 4000 turn profile
    label = (item.get('label') if (item is not None and isinstance(item, dict)
                                   and game is not _INITIAL_GAME) else None)
    if label is not None:
        ck = id(game.get('_poss_cache'))
        c = _ID_CACHE
        if c['key'] != ck:
            c['key'], c['by_label'] = ck, {}
        if label in c['by_label']:
            return c['by_label'][label]
    poss = possible_ids(game, item)
    if not poss:
        return None
    cache = game.get('_merge_cache')
    if cache is not None:
        key = tuple(p['name'] for p in poss)
        if key in cache:
            r = cache[key]
        else:
            r = cache[key] = _merge_records(poss)
    else:
        r = _merge_records(poss)
    if label is not None:
        _ID_CACHE['by_label'][label] = r
    return r


def item_type(item):
    if item:
        p = initial_ids(item, 1)
        return it.typekw(p[0]) if p else None
    return None


def item_subtype(item):
    if item:
        p = initial_ids(item, 1)
        return p[0].get('subtype') if p else None
    return None


def item_weight(item):
    if item:
        p = initial_ids(item, 1)
        return p[0].get('weight') if p else None
    return None


def item_name(game, item):
    if item:
        i = item_id(game, item)
        return i.get('name') if i else None
    return None


def know_id(game, item):
    return item_name(game, item) is not None


def possible_names(game, item):
    if item:
        p = possible_ids(game, item)
        return [i['name'] for i in (p or ())]
    return None


def ambiguous_appearance(item):
    return not item.get('generic') and item['name'] in item_names


def know_price(game, item):
    i = item_id(game, item)
    if i and i.get('price') is not None:
        return True
    return bool(game['discoveries']['cost'].get(appearance_of(item)))


def know_appearance(game, id_):
    clj_assert(isinstance(id_, str), 'string? id')
    cnt = 0
    disc = game['discoveries']
    for a in APPEARANCE_NAMES:
        if disc['discovery'].get(a) == id_ or _possible(disc, a, id_):
            cnt += 1
            if cnt > 1:
                return False
    return cnt == 1


def could_be(game, id_, item):
    clj_assert(isinstance(id_, str), 'string? id')
    return any(i['name'] == id_ for i in (possible_ids(game, item) or ()))


def name_for(game, item):
    return find_first(lambda n: n not in game['used_names'],
                      item_names.get(item['name'], ()))


def name_variants(name):
    return item_names.get(re.sub(r'(.*)[0-9]+', r'\1', name))


def _facts_for_name(disc, name):
    new = dict(disc)
    if name in disc['discovery']:
        d = dict(disc['discovery'])
        id_ = d.pop(name)
        new['discovery'] = d
        new['by_id'] = dissoc(disc['by_id'], id_)
    new['prop'] = {k: v for k, v in disc['prop'].items() if k[0] != name}
    new['cost'] = {k: v for k, v in disc['cost'].items() if k != name}
    return new


def forget_name(game, name):
    log.warning("forgot name %s", name)
    if name in game['used_names']:
        return game
    return assoc(game, 'discoveries', _facts_for_name(game['discoveries'],
                                                      name))


def forget_names(game, names_):
    names_ = list(names_)
    if not names_:
        return game
    for n in names_:
        game = assoc(game, 'used_names',
                     set(game['used_names']) - {n})
    for n in names_:
        game = forget_name(game, n)
    for n in names_:
        for variant in (name_variants(n) or ()):
            game = forget_name(game, variant)
    for n in names_:
        game = add_eliminated(game, n)
    return _reset_possibilities(game)
