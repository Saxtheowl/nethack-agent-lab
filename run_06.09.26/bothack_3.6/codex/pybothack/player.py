"""Port of bothack.player - representation of the bot avatar."""
import logging

from .clj import (assoc, assoc_in, clj_items, dissoc, get_in, update_in,
                  conj_set, disj)
from .item import (amulet_p, armor_p, blessed, boh, can_take, container,
                   corpse, cursed, food_p, gloves, gold, noncursed, pick,
                   ring_p, safe_buc, shield, tin, two_handed, wand_p,
                   weapon_p, charged, item_weight)
from .itemid import (item_id, item_name, item_subtype, item_type, appearance_of,
                     know_id)
from .itemtype import name_to_item
from .montype import name_to_monster
from .util import (find_first, less_than, parse_int, re_seq, some_fn,
                   every_pred, find_first as _ff)

log = logging.getLogger('bothack.player')


def hungry(player):
    return player.get('hunger') if player.get('hunger') in (
        'hungry', 'weak', 'fainting') else None


def weak(player):
    return player.get('hunger') if player.get('hunger') in (
        'weak', 'fainting') else None


def fainting(player):
    return player.get('hunger') == 'fainting'


def satiated(player):
    return player.get('hunger') == 'satiated'


def _selfpoly_monster(title):
    if title:
        return name_to_monster(title)
    return name_to_monster("guardian naga hatchling")


def update_player(player, status):
    res = dict(player)
    for k in player.keys():
        if k in status:
            res[k] = status[k]
    if not status.get('blind'):
        res['state'] = disj(res.get('state') or set(), 'ext-blind')
    if status.get('xp-label') == "HD":
        res['polymorphed'] = _selfpoly_monster(status.get('title'))
    if status.get('xp-label') == "Exp":
        res['polymorphed'] = None
    if status.get('gold') == 0:
        res['inventory'] = dissoc(res.get('inventory') or {}, '$')
    if (status.get('gold') or 0) > 0:
        from .item import label_to_item
        res['inventory'] = assoc(res.get('inventory') or {}, '$',
                                 assoc(label_to_item("uncursed gold piece"),
                                       'qty', status['gold']))
    return res


def blind(player):
    return 'blind' in (player.get('state') or ())


def impaired(player):
    return any(s in (player.get('state') or ())
               for s in ('conf', 'stun', 'hallu', 'blind'))


def hallu(player):
    return 'hallu' in (player.get('state') or ())


def dizzy(player):
    return any(s in (player.get('state') or ()) for s in ('conf', 'stun'))


def confused(player):
    return 'conf' in (player.get('state') or ())


def thick(player):
    """True if the player can't pass through narrow diagonals."""
    return not player.get('thick')


def has_hands(player):
    poly = player.get('polymorphed')
    if poly:
        tags = poly.get('tags') or ()
        if 'nohands' in tags or 'nolimbs' in tags or 'were' in tags:
            return False
    wielded = _ff(lambda kv: kv[1].get('wielded'),
                  (player.get('inventory') or {}).items())
    if wielded:
        item = wielded[1]
        if cursed(item):
            if two_handed(item):
                return False
            if _ff(lambda kv: (shield(kv[1]) and cursed(kv[1])
                               and kv[1].get('worn')),
                   (player.get('inventory') or {}).items()):
                return False
    return True


def light_radius(game):
    return 1


def bagged_items(game_or_player):
    player = game_or_player.get('player') or game_or_player
    res = []
    for slot, bag in (player.get('inventory') or {}).items():
        if container(bag):
            for i in (bag.get('items') or ()):
                res.append((slot, i))
    return res


def inventory(game_or_player, bagged=False):
    # `(concat (:inventory player) …)` walks the map in Clojure's order, which
    # is what makes `have` deterministic about *which* matching item it picks.
    player = game_or_player.get('player') or game_or_player
    res = list(clj_items(player.get('inventory') or {}))
    if bagged:
        res += bagged_items(player)
    return res


SLOTS = ['helmet', 'cloak', 'suit', 'shirt', 'shield', 'gloves', 'boots',
         'accessory', 'amulet']

BLOCKER_SLOTS = {'suit': ['cloak'], 'shirt': ['cloak', 'suit']}
for _s in SLOTS:
    BLOCKER_SLOTS[_s] = BLOCKER_SLOTS.get(_s, []) + [_s]


def _base_selector(game, sel):
    if isinstance(sel, (set, frozenset)):
        return lambda i: (item_name(game, i) in sel) or (i.get('name') in sel)
    if callable(sel):
        return sel
    return lambda i: i.get('name') == sel or item_name(game, i) == sel


def inventory_slot(game, slot):
    if isinstance(slot, str) and len(slot) == 1 and slot not in SLOTS:
        return get_in(game, ['player', 'inventory', slot])
    return have(game, lambda i: i.get('worn') and item_subtype(i) == slot)


def wielding(game_or_player):
    player = game_or_player.get('player') or game_or_player
    return _ff(lambda kv: kv[1].get('wielded'), inventory(player))


def wielded_item(game):
    w = wielding(game)
    return w[1] if w else None


def free_finger(player):
    return less_than(2, [i for i in (player.get('inventory') or {}).values()
                         if ring_p(i) and i.get('worn')])


def blockers(game, item):
    """[slot item] pairs that need to be removed before item can be used."""
    subtype = item_subtype(item)
    if subtype and subtype != 'weapon':
        res = []
        for btype in BLOCKER_SLOTS.get(subtype, ()):
            b = have(game, lambda i, bt=btype: (item_subtype(i) == bt
                                                and i.get('worn')))
            if b:
                res.append(b)
        if subtype == 'gloves' and cursed(wielded_item(game) or {}):
            res.append(wielding(game))
        if (subtype == 'shield' and wielding(game)
                and two_handed(wielded_item(game))):
            res.append(wielding(game))
        return res or None
    if weapon_p(item) or pick(item):
        res = []
        weapon = wielding(game)
        if weapon:
            if weapon_p(weapon[1]) or item_subtype(weapon[1]) == 'weapon':
                res.append(weapon)
        if two_handed(item):
            sh = have(game, shield, {'worn'})
            if sh:
                res.append(sh)
        return res or None
    if ring_p(item):
        res = list(have_all(game, gloves, {'worn', 'cursed'}))
        if not (free_finger(game['player']) or item.get('in-use')):
            res += list(have_all(game, ring_p, {'worn'}))
        return res or None
    if amulet_p(item):
        return list(have_all(game, amulet_p, {'worn'})) or None
    return None


def cursed_blockers(game, slot):
    i = inventory_slot(game, slot)
    if not i:
        return None
    b = blockers(game, i)
    if not b:
        return None
    res = [x[1] for x in b if cursed(x[1])]
    return res or None


def _have_selector(game, sel, opts):
    preds = [_base_selector(game, sel)]
    if opts.get('nonempty'):
        preds.append(lambda i: i.get('specific') != "empty")
    if opts.get('safe-buc'):
        preds.append(safe_buc)
    if opts.get('unsafe-buc'):
        preds.append(lambda i: not safe_buc(i))
    if opts.get('safe-buc') is False:
        preds.append(lambda i: not safe_buc(i))
    if opts.get('noncursed'):
        preds.append(noncursed)
    if opts.get('buc'):
        preds.append(lambda i: i.get('buc') == opts['buc'])
    if opts.get('nonblessed'):
        preds.append(lambda i: not blessed(i))
    if opts.get('blessed'):
        preds.append(blessed)
    if opts.get('cursed'):
        preds.append(cursed)
    if opts.get('wished'):
        preds.append(lambda i: i.get('specific') == "wish")
    if opts.get('know-buc'):
        preds.append(lambda i: i.get('buc') is not None)
    if opts.get('know-buc') is False:
        preds.append(lambda i: i.get('buc') is None)
    if opts.get('in-use') is False:
        preds.append(lambda i: not i.get('in-use'))
    if opts.get('worn'):
        preds.append(lambda i: i.get('worn'))
    if opts.get('in-use'):
        preds.append(lambda i: i.get('in-use'))
    return lambda i: all(p(i) for p in preds)


def _normalize_opts(opts):
    if opts is None:
        return {}
    if isinstance(opts, (set, frozenset)):
        return {k: True for k in opts}
    return opts


def have_all(game, sel, opts=None):
    opts = _normalize_opts(opts)
    player = game['player']
    selector = _have_selector(game, sel, opts)
    res = []
    for slot, item in inventory(game):
        if not selector(item):
            continue
        if (opts.get('can-use')
                and ((((armor_p(item) or pick(item) or wand_p(item)
                        or weapon_p(item)) and not has_hands(player))
                      or (wand_p(item) and not charged(item))
                      or cursed_blockers(game, slot))
                     and not item.get('in-use'))):
            continue
        if ((opts.get('can-use') is False or opts.get('no-can-use'))
                and (item.get('in-use')
                     or (charged(item) if wand_p(item)
                         else not cursed_blockers(game, slot)))):
            continue
        if ((opts.get('can-remove') is False or opts.get('no-can-remove'))
                and (not item.get('in-use')
                     or not cursed_blockers(game, slot))):
            continue
        if (opts.get('can-remove') and item.get('in-use')
                and cursed_blockers(game, slot)):
            continue
        res.append((slot, item))
    if opts.get('bagged'):
        for slot, bagitem in inventory(game):
            if container(bagitem):
                for match in (bagitem.get('items') or ()):
                    if selector(match):
                        res.append((slot, match))
    return res


def have_sum(game, sel, opts=None):
    return sum(i.get('qty', 0) for _, i in have_all(game, sel, opts))


def have(game, sel, opts=None):
    if isinstance(sel, dict) and not callable(sel):
        return have(game, lambda i: True, sel)
    r = have_all(game, sel, opts)
    return r[0] if r else None


def have_usable(game, smth):
    return have(game, smth, {'can-use'})


def have_unihorn(game):
    return have(game, "unicorn horn", {'noncursed'})


def have_pick(game):
    return have_usable(game, lambda i: (
        item_name(game, i) in ("pick-axe", "dwarvish mattock")
        and (not cursed(i) or i.get('in-use'))))


def have_key(game):
    return have(game, {"skeleton key", "lock pick", "credit card"})


def have_levi_on(game):
    return have(game, {"boots of levitation", "ring of levitation"}, {'worn'})


def have_levi(game):
    return have(game, lambda i: item_name(game, i) in (
        "boots of levitation", "ring of levitation"),
        {'noncursed', 'can-use'})


def reflection(game):
    return have(game, {"amulet of reflection", "shield of reflection",
                       "silver dragon scale mail"}, {'worn'})


def free_action(game):
    return have(game, "ring of free action", {'worn'})


def unihorn_recoverable(game):
    player = game['player']
    if player.get('stat-drained'):
        return True
    if any(s in (player.get('state') or ())
           for s in ('conf', 'stun', 'hallu', 'ill')):
        return True
    return bool('blind' in (player.get('state') or ())
                and 'ext-blind' not in (player.get('state') or ())
                and not have(game, lambda i: (
                    item_name(game, i) in ("towel", "blindfold")
                    and i.get('worn'))))


def can_remove(game, slot):
    item = inventory_slot(game, slot)
    return bool(not item.get('in-use')
                or (not cursed_blockers(game, slot) and noncursed(item)))


def initial_intrinsics(race_or_role):
    if race_or_role == 'valkyrie':
        return {'cold', 'stealth'}
    if race_or_role == 'orc':
        return {'poison'}
    return set()


def add_intrinsic(game, intrinsic):
    log.debug("adding intrinsic: %s", intrinsic)
    return update_in(game, ['player', 'intrinsics'],
                     lambda s: conj_set(s, intrinsic))


def remove_intrinsic(game, intrinsic):
    log.debug("removing intrinsic: %s", intrinsic)
    return update_in(game, ['player', 'intrinsics'],
                     lambda s: disj(s, intrinsic))


def have_intrinsic(game_or_player, resist):
    player = game_or_player.get('player') or game_or_player
    return resist in (player.get('intrinsics') or ())


def fast(player):
    return have_intrinsic(player, 'speed')


def count_candles(game):
    from .item import CANDELABRUM, candle
    total = 0
    c = have(game, CANDELABRUM)
    if c:
        total += c[1].get('candles') or 0
    for _, candles in have_all(game, candle):
        total += candles['qty']
    return total


def have_candles(game):
    return count_candles(game) >= 7


TABOO_CORPSES = {"chickatrice", "cockatrice", "green slime", "stalker",
                 "quantum mechanic", "elf", "human", "dwarf", "giant",
                 "violet fungus", "yellow mold", "chameleon", "Medusa",
                 "doppelganger", "Pestilence", "Death", "Famine"}


def safe_corpse_type(player, corpse_item, corpse_type):
    monster = corpse_type.get('monster')
    if not (tin(corpse_item) or have_intrinsic(player, 'poison')
            or not corpse_type.get('poisonous')):
        return False
    tags = (monster or {}).get('tags') or ()
    if player.get('race') in tags:
        return False
    name = (monster or {}).get('name')
    if (name in TABOO_CORPSES
            or any(t in tags for t in ('were', 'teleport', 'domestic'))
            or re_seq(r'bat$', name or '')):
        return False
    return True


def edible(player, food):
    if cursed(food) or not can_take(food):
        return False
    if tin(food):
        return True
    itemtype = name_to_item.get(food.get('name'))
    if not itemtype:
        return False
    from .itemtype import typekw as _typekw
    return bool(_typekw(itemtype) == 'food'
                and (player.get('race') == 'orc'
                     or food['name'] != "tripe ration")
                and (not itemtype.get('monster')
                     or safe_corpse_type(player, food, itemtype)))


def want_to_eat(player, corpse_item):
    if not edible(player, corpse_item):
        return False
    corpse_type = name_to_item.get(corpse_item['name'])
    monster = (corpse_type or {}).get('monster') or {}
    strength = get_in(player, ['stats', 'str*'])
    if monster.get('name') in ("newt", "wraith"):
        return True
    # (and (or (not= "18/**" strength) (some-> (parse-int strength) (< 18)))
    #      (:str (:tags monster)))
    # NB the or is evaluated first, so with a displayed strength of 18/**
    # the original throws here (parse-int of "18/**"); reproduced as-is.
    if strength != "18/**":
        cond = True
    else:
        cond = parse_int(strength) < 18
    if cond and 'str' in (monster.get('tags') or ()):
        return True
    return any(not have_intrinsic(player, r)
               for r in (monster.get('resistances-conferred') or ()))


def update_slot(game, slot, f, *args):
    return update_in(game, ['player', 'inventory', slot], f, *args)


def nutrition_sum(game):
    total = 0
    for _, item in have_all(game, food_p, {'bagged', 'noncursed'}):
        n = (item_id(game, item) or {}).get('nutrition')
        total += (n or 0) * item['qty']
    return total


def nw_ratio_avg(game):
    food = have_all(game, food_p, {'bagged', 'noncursed'})
    if not food:
        return None
    w = sum((item_id(game, i) or {}).get('weight') or 0 for _, i in food)
    if not w:
        return None
    return nutrition_sum(game) / w


def overloaded(player):
    return player.get('encumbrance') == 'overloaded'


def overtaxed(player):
    return player.get('encumbrance') in ('overtaxed', 'overloaded')


def strained(player):
    return player.get('encumbrance') in ('strained', 'overtaxed', 'overloaded')


def stressed(player):
    return player.get('encumbrance') in ('stressed', 'strained', 'overtaxed',
                                         'overloaded')


def burdened(player):
    return player.get('encumbrance') is not None


def can_engrave(game):
    from .dungeon import branch_key
    player = game['player']
    return not (not has_hands(player) or impaired(player)
                or overtaxed(player)
                or branch_key(game) in ('air', 'water')
                or have_levi_on(game))


def weight_mod(game, item):
    if item.get('items') and boh(game, item):
        buc = item.get('buc')
        if buc == 'blessed':
            return lambda w: w * 0.25 + 1
        if buc == 'cursed':
            return lambda w: w * 2
        return lambda w: w * 0.5 + 1
    return lambda w: w


def weight_sum(game):
    total = 0
    for _, item in inventory(game):
        q = weight_mod(game, item)
        for i in list(item.get('items') or ()) + [item]:
            w = item_weight(i)
            if w is None:
                continue
            total += i['qty'] * (w if i is item else q(w))
    return total


def capacity(player):
    stats = player['stats']
    return min(1000, 50 + 25 * (stats['con'] + stats['str']))


def weight_to_burden(game):
    return capacity(game['player']) - weight_sum(game)


def available_gold(game):
    return get_in(game, ['player', 'inventory', '$', 'qty'], 0)


def gold_sum(game):
    return have_sum(game, gold, {'bagged'})


def inventory_label(game, label):
    return _ff(lambda kv: (kv[1]['label'].startswith(label)
                           or kv[1].get('name') == label), inventory(game))


def slot_appearance(game, slot):
    return appearance_of(inventory_slot(game, slot))


def have_mr(game):
    return have(game, {"gray dragon scale mail", "cloak of magic resistance",
                       "Magicbane", "gray dragon scales"}, {'in-use'})


def can_eat(player):
    return not overtaxed(player)


OPPOSITE_ALIGNMENT = {'lawful': 'chaotic', 'chaotic': 'lawful',
                      'neutral': 'neutral'}


def new_player():
    return {'protection': 0, 'inventory': {}, 'nickname': None, 'title': None,
            'role': None, 'race': None, 'hp': None, 'maxhp': None, 'pw': None,
            'maxpw': None, 'ac': None, 'xplvl': None, 'x': None, 'y': None,
            'hunger': None, 'encumbrance': None, 'intrinsics': frozenset(),
            'engulfed': False, 'trapped': False, 'leg-hurt': False,
            'state': frozenset(), 'stat-drained': False, 'polymorphed': None,
            'lycantrophy': False, 'stoning': False, 'stats': None,
            'alignment': None, 'can-enhance': None}
