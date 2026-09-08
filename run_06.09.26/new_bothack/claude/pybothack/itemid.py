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
def _cost_data():
    charges = [
        (5, lambda c: 2 * c),
        (7, lambda c: c + c // 2),
        (10, lambda c: c + c // 3),
        (15, lambda c: c),
        (17, lambda c: c - c // 4),
        (18, lambda c: c - c // 3),
        (25, lambda c: c // 2),
        (0, lambda c: c),                     # sell price
    ]
    res = set()
    for cost in range(501):
        for cha, charge in charges:
            id_charges = ([lambda c: c // 2] if cha == 0
                          else [lambda c: c, lambda c: c + c // 3])
            sucker_charges = ([lambda c: c, lambda c: c - c // 4] if cha == 0
                              else [lambda c: c, lambda c: c + c // 3])
            for idc in id_charges:
                for suc in sucker_charges:
                    res.add((cost, cha, charge(suc(idc(cost)))))
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
    assert isinstance(appearance, str)
    return not (appearance in BLIND_APPEARANCES
                or (appearance not in names
                    and appearance not in exclusive_appearances))


def appearance_of(item):
    if item.get('name') in item_names and item.get('generic'):
        return item['generic']
    spec = name_to_item.get(item.get('specific'))
    if spec:
        return spec['name']
    return item['name']


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
    assert isinstance(appearance, str)
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
    assert prop in OBSERVABLE_PROPS
    if knowable_appearance(appearance):
        log.debug("for appearance %s adding observed property %s = %s",
                  appearance, prop, propval)
        return _add_fact(game, 'prop', appearance, prop, propval)
    return game


def add_observed_cost(game, appearance, cost, sell=False, cha=None):
    if cha is None:
        cha = game['player']['stats']['cha']
    assert isinstance(appearance, str)
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


def item_id(game_or_item, item=None):
    if item is None:
        item, game = game_or_item, _INITIAL_GAME
    else:
        game = game_or_item
    poss = possible_ids(game, item)
    if not poss:
        return None
    cache = game.get('_merge_cache')
    if cache is not None:
        key = tuple(p['name'] for p in poss)
        if key in cache:
            return cache[key]
        r = _merge_records(poss)
        cache[key] = r
        return r
    return _merge_records(poss)


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
    assert isinstance(id_, str)
    cnt = 0
    disc = game['discoveries']
    for a in APPEARANCE_NAMES:
        if disc['discovery'].get(a) == id_ or _possible(disc, a, id_):
            cnt += 1
            if cnt > 1:
                return False
    return cnt == 1


def could_be(game, id_, item):
    assert isinstance(id_, str)
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
