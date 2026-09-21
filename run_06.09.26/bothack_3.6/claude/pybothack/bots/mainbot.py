"""Port of bothack.bots.mainbot - the example bot that ascended NetHack."""
import logging

from ..action import typekw
from ..actions import (Apply, Attack, Contribute, Drop, DropSingle, Eat,
                       Engrave, FarmAttack, ForceLock, Move, Name, Offer,
                       PickUp, PutOn, Quaff, Read, Remove, Repeated, Rub,
                       Search, Sit, TakeOff, Throw, Unlock, Wait, Wield, Wipe,
                       ZapWand, ZapWandAt, Loot, enhance_all, kick, make_use,
                       put_in, remove_use, search, take_out, unbag,
                       with_handler, with_reason, wield, Ascend, Descend,
                       descend, tried, without_levitation)
from ..behaviors import (bless, enhance, invocation, pray, seek_high_altar)
from ..clj import assoc, clj_set_order, clj_vals, get_in, into_map
from ..delegator import Handler
from ..dungeon import (at_curlvl, at_planes, at_player, below_medusa,
                       below_castle, branch_key, curlvl, curlvl_monsters,
                       curlvl_tags, dlvl, get_dlvl, get_level, in_gehennom,
                       monster_at, prev_dlvl, next_dlvl)
from ..fov import visible
from ..handlers import deregister_handler, register_handler
from ..item import (AMMO, BELL, BOOK, CANDELABRUM, DAGGERS, ammo_p, amulet_p,
                    can_take,
                    armor_p, artifact, bag, blessed, boots, candle, container,
                    corpse, cursed, dagger, dart, egg, enchantment, food_p,
                    gem_p, gold, holy_water, key_p, nw_ratio, pick, potion_p,
                    price_id, ring_p, rocks, safe, safe_buc, safe_enchant,
                    scroll_p, shield, shops_taking, short_sword, statue_p,
                    tin, tool_p, uncursed, wand_p, weapon_p,
                    explorable_container, know_contents, charged, recharged)
from ..itemid import (ambiguous_appearance, could_be, item_id, item_name,
                      know_appearance, know_id, possible_names)
from ..itemtype import item_kinds, name_to_item
from ..level import tile_seq
from ..monster import (covetous, drowner, flies, hostile, ignores_e,
                       leprechaun, mimic, nasty, passive, priest, pudding,
                       rider, sees_invisible, sessile, slow, spellcaster,
                       titan, typename, unicorn, unique, werecreature,
                       corrosive, steals, monster_hasheq)
from ..pathing import (Path, explore, explore_level, exploration_index,
                       explored, fidget, go_down, level_seq, nav_targets,
                       navigate, needs_levi, search_level, seek, seek_branch,
                       seek_feature, seek_level, seek_tile, unstuck, visit,
                       entering_shop, safely_walkable, likely_walkable,
                       autonavigable)
from ..player import (OPPOSITE_ALIGNMENT, available_gold, blind, burdened,
                      can_engrave, can_remove, confused, count_candles,
                      dizzy, edible, fainting, fast, free_action, free_finger,
                      hallu, has_hands, have, have_all, have_candles, have_key,
                      have_levi, have_levi_on, have_mr, have_pick, have_sum,
                      have_unihorn, have_intrinsic, hungry, impaired,
                      inventory, inventory_label, inventory_slot, item_subtype,
                      nutrition_sum, nw_ratio_avg, overloaded, overtaxed,
                      reflection, satiated, unihorn_recoverable, want_to_eat,
                      weak, wielded_item, wielding, stressed)
from ..position import (Pos, adjacent, at, diagonal, distance,
                        distance_manhattan, in_direction, in_line,
                        including_origin, neighbors, position, position_map,
                        towards, DIRECTIONS)
from ..sokoban import do_soko, soko_done
from .. import rules36
from ..tile import (altar_p, blocked, boulder, door, drawbridge, e_p,
                    lootable_items,
                    engravable, fountain_p, has_feature, item as tile_item,
                    monster as tile_monster, perma_e, pit_p, pool_p, shop,
                    sink_p, spikepit_p, stairs_up_p, stairs_down_p, temple,
                    throne_p, trap, walkable, portal_p, visited_stairs)
from ..tracker import fresh_corpse
from ..util import (ESC, find_first, first_min_by, keep_first, less_than,
                    max_by, min_by, more_than, parse_int, re_first_group,
                    removev, PRIORITY_BOTTOM)

log = logging.getLogger('bothack.mainbot')


def _hostile_dist_thresh(game):
    if at_planes(game):
        return 1
    if branch_key(game) == 'sokoban':
        return 500
    return 5


def hostile_threats(game):
    """(->> (curlvl-monsters game) (filter ...) set)

    Returns the monsters in the order the Clojure *set* iterates them, which is
    the HAMT order of their `hasheq` - not the order `curlvl-monsters` yields.
    Load-bearing: `fight` runs `find-first` over this collection to pick the
    monster it baits, and picking a fleeing one instead of a standing one makes
    it step where the original searches.
    """
    player = game['player']
    res = []
    for m in curlvl_monsters(game):
        if not hostile(m):
            continue
        if (adjacent(player, m) or covetous(m)
                or (not (blind(player) and m.get('remembered'))
                    and (5 + _hostile_dist_thresh(game)
                         > game['turn'] - m['known'])
                    and distance(player, m) < _hostile_dist_thresh(game)
                    and not blind(player) and not hallu(player))):
            res.append(m)
    return clj_set_order(res, monster_hasheq)


def _threat_map(game):
    # (into {} (for [m (hostile-threats game)] [(position m) m]))
    return into_map((position(m), m) for m in hostile_threats(game))


def _choose_food(game):
    def sel(i):
        return (edible(game['player'], i)
                and item_name(game, i) != "lizard corpse" and not tin(i))
    r = min_by(lambda kv: nw_ratio(kv[1]), have_all(game, sel, {'bagged'}))
    return r or have(game, "lizard corpse", {'bagged'})


def handle_starvation(game):
    player = game['player']
    if (weak(player)
            and (not _can_pray(game) or nutrition_sum(game) > 1200)
            and not overtaxed(player)
            and (not farming(game) or farm_spot_p(game, player))):
        found = _choose_food(game)
        if found:
            slot, food = found
            return with_reason("weak or worse, eating", food,
                               unbag(game, slot, food) or Eat(slot))
    if ((fainting(player) or (weak(player) and not farming(game)))
            and _can_pray(game)):
        from ..actions import Pray
        return with_reason("praying for food", Pray())
    return None


def _can_pray(game):
    from ..game import can_pray
    return can_pray(game)


_CURSED_LEVI = [None]


def cursed_levi(game):
    if (have(game, {"boots of levitation", "ring of levitation"},
             {'cursed', 'worn'})
            and not have(game, holy_water, {'bagged'})
            and not have(game, "scroll of remove curse",
                         {'bagged', 'noncursed'})):
        r = (pray(game)
             or (seek_level(game, 'main', 'castle')
                 if in_gehennom(game) else None))
        if r is None:
            # port: waiting for a prayer that never comes blocked the bot for
            # 6000 turns (big-w04 g001); wait a while, then play on and hope
            # to find holy water or a scroll of remove curse
            turn = game.get('turn') or 0
            if _CURSED_LEVI[0] is None or turn - _CURSED_LEVI[0] > 6000:
                _CURSED_LEVI[0] = turn
            if turn - _CURSED_LEVI[0] < 2000:
                r = search(10)
        return with_reason("cursed levitation", r)
    return None


def _choose_amulet(game):
    if not have(game, {"silver dragon scale mail", "shield of reflection"},
                {'worn'}):
        r = have(game, "amulet of reflection", {'can-use', 'bagged'})
        if r:
            return r
    return (have(game, "amulet of life saving", {'can-use', 'bagged'})
            or have(game, "amulet of ESP", {'can-use', 'bagged'}))


def wear_amulet(game):
    if typekw(game.get('last-action')) != 'remove':
        found = _choose_amulet(game)
        if found:
            slot, item = found
            return with_reason("wear amulet",
                               unbag(game, slot, item) or make_use(game, slot))
    return None


def replace_ls(game):
    if not have(game, amulet_p, {'worn'}) and have(game,
                                                   "amulet of life saving"):
        return wear_amulet(game)
    return None


def handle_illness(game):
    player = game['player']
    if overtaxed(player):
        return with_reason("overtaxed", search(10))
    r = replace_ls(game)
    if r:
        return r
    if player.get('stoning'):
        found = have(game, "lizard corpse", {'bagged'})
        if found:
            slot, item = found
            return with_reason("fix stoning",
                               unbag(game, slot, item) or Eat(slot))
        return with_reason("fix stoning", pray(game))
    if player.get('lycantrophy'):
        found = have(game, "sprig of wolfsbane", {'bagged'})
        if found:
            slot, item = found
            return with_reason("fix lycantrophy",
                               unbag(game, slot, item) or Eat(slot))
        return with_reason("fix lycantrophy", pray(game))
    if (unihorn_recoverable(game)
            and (any(s in player['state'] for s in ('conf', 'stun', 'ill'))
                 or (not have_intrinsic(player, 'telepathy')
                     and blind(player)))):
        found = _recovery_unihorn(game)
        if found:
            return with_reason("applying unihorn to recover", Apply(found[0]))
    if 'ill' in player['state']:
        found = have(game, "eucalyptus leaf", {'noncursed'})
        if found:
            return with_reason("fixing illness", Eat(found[0]))
        found = (have(game, "potion of healing",
                      {'buc': 'blessed', 'bagged': True})
                 or have(game, {"potion of extra healing",
                                "potion of full healing"},
                         {'noncursed', 'bagged'}))
        if found:
            slot, item = found
            return with_reason("fixing illness",
                               unbag(game, slot, item) or Quaff(slot))
        return with_reason("fixing illness", pray(game))
    return None


_UNIHORN_USES = []        # turns of recovery applications
_UNIHORN_BLOCKED = [-1]   # turn until which the horn is not trusted


def _recovery_unihorn(game):
    """have_unihorn() for curing impairments, distrusting a horn that does
    not work: after a "curse items" spell a horn believed blessed is cursed
    and *causes* confusion/stun/blindness; BotHack applied it forever
    (scen/valley-to-vlad-01).  6 applications within 30 turns while still
    impaired -> not used for recovery during 300 turns."""
    turn = game.get('turn') or 0
    if turn < _UNIHORN_BLOCKED[0]:
        return None
    found = have_unihorn(game)
    if not found:
        return None
    recent = [t for t in _UNIHORN_USES if turn - t <= 30]
    if len(recent) >= 6:
        _UNIHORN_BLOCKED[0] = turn + 300
        del _UNIHORN_USES[:]
        log.warning("unicorn horn applied %d times in 30 turns without "
                    "curing: not trusted until turn %d", len(recent),
                    turn + 300)
        return None
    _UNIHORN_USES[:] = recent + [turn]
    return found


def name_first_amulet(bh):
    h = Handler()

    def choose_action(game):
        found = have(game, "Amulet of Yendor")
        if found:
            deregister_handler(bh, h)
            return with_reason("naming the real amulet",
                               Name(found[0], "REAL"))
        return None
    h.choose_action = choose_action
    return h


def real_amulet(item):
    return (item.get('name') == "Amulet of Yendor"
            and item.get('specific') == "REAL")


def get_amulet(game):
    if not have(game, real_amulet, {'bagged'}):
        return with_reason("searching for the amulet",
                           explore(game) or search_level(game, 1)
                           or seek(game, stairs_up_p))
    return None


def have_throwable(game):
    return (have(game, lambda i: dagger(i) or short_sword(i), {'can-remove'})
            or have(game, lambda i: dart(i) or ammo_p(i), {'can-remove'})
            or have(game, rocks, {'can-remove'}))


def castle_plan_b(game):
    player = game['player']
    level = curlvl(game)
    # (or (not (have-levi game))
    #     (not-any? (:genocided game) #{";" "electric eel"})
    #     (not (reflection? game)))
    #
    # `(not-any? pred coll)` with the genocided *set* as the predicate is true
    # only when NEITHER ";" nor "electric eel" has been genocided.  This port
    # carried a fourth clause - `";" not in genocided` - with no counterpart
    # upstream: a leftover from a first attempt at `not-any?`, and implied by
    # the real one.  Inside an `or` an extra clause can only make the guard
    # fire more often, so castle-plan-b would engage when ";" was ungenocided
    # but the eel was genocided, where the original declines.
    if not ('castle' in level['tags'] and player['x'] < 13
            and not any(walkable(at(level, 13, y)) for y in (11, 12, 13))
            and (not have_levi(game)
                 or not any(g in game['genocided']
                            for g in (";", "electric eel"))
                 or not reflection(game))):
        return None
    res = None
    if not any(stairs_up_p(t) for t in tile_seq(level)):
        res = with_reason("find stairs", seek(game, stairs_up_p))
    if res is None and not (farm_done(game)
                            and have(game, "scroll of earth",
                                     {'noncursed', 'bagged'})):
        found = have(game, "wand of cold")
        if found:
            pool = find_first(pool_p, [at(level, 13, y) for y in (11, 12, 13)])
            if pool:
                p = navigate(game, lambda t: (distance(pool, t) == 2
                                              and in_line(pool, t)))
                if p:
                    res = with_reason("using wand of cold",
                                      p['step'] or ZapWandAt(
                                          found[0], towards(player, pool)))
    if res is None:
        found = have(game, "scroll of earth", {'noncursed', 'bagged'})
        if found:
            p = navigate(game, Pos(12, 13))
            if p:
                res = with_reason("using scroll of earth",
                                  p['step'] or unbag(game, found[0], found[1])
                                  or Read(found[0]))
    if res is None:
        p = navigate(game, lambda t: stairs_up_p(t) and not visited_stairs(t))
        if p:
            res = with_reason("visit Medusa", p['step'] or Ascend())
    if res is None and not drawbridge(at_curlvl(game, 14, 12)):
        p = navigate(game, Pos(13, 12), {'adjacent'})
        if p:
            res = with_reason("no way to cross moat",
                              p['step'] or Move(towards(player, p['target'])))
    return with_reason("castle plan B", res) if res else None


def _have_dsm(game, opts=None):
    return have(game, {"silver dragon scale mail", "gray dragon scale mail"},
                opts or {})


def full_explore(game):
    player = game['player']
    if get_level(game, 'main', 'sanctum'):
        return None
    fast = rules36.fast_profile()
    skip = rules36.skipped_steps()
    res = (None if (fast or 'minetown' in skip)
           else explore(game, 'mines', 'minetown'))
    if res is None and not (fast or 'sokoban' in skip):
        res = explore(game, 'main', 'sokoban')
    if (res is None and not (fast or 'sokoban' in skip)
            and have(game, "Excalibur") and have_throwable(game)):
        res = do_soko(game)
    if res is None and 'quest-portal' not in skip:
        res = explore(game, 'main', 'quest')
    if res is None and not (fast or 'mines-end' in skip):
        minetown = get_level(game, 'mines', 'minetown')
        k = have_key(game)
        if (not below_medusa(game)
                and ((k and key_p(k[1]))
                     or not minetown
                     or 'minetown-grotto' not in minetown['tags']
                     or at(minetown, 48, 5).get('seen'))
                and (player['ac'] > -7 or not have_pick(game)
                     or not have_key(game))):
            res = explore(game, 'mines')
    if res is None and not (farm_done(game) or below_medusa(game)
                            or 'dlvl20' in skip):
        res = explore(game, 'main', "Dlvl:20")
    if res is None:
        res = castle_plan_b(game)
    if res is None:
        if ((player['ac'] < -7 or not _have_dsm(game)
             or not any(g in game['genocided'] for g in (";", "electric eel")))
                and have(game, "wand of striking", {'bagged'})):
            res = explore_level(game, 'main', 'castle')
    if res is None and 'quest' not in skip:
        if (have_levi(game) and game['player']['xplvl'] >= 14
                and _have_dsm(game)):
            res = explore_level(game, 'quest', 'end') or quest_bell(game)
    if res is None and 'vlad' not in skip:
        res = explore_level(game, 'vlad', 'end') or vlad_candelabrum(game)
    if res is None:
        res = explore_level(game, 'main', 'end')
    if res is None and 'wiztower' not in skip:
        res = explore_level(game, 'wiztower', 'end')
    if res is None:
        res = invocation(game)
    return with_reason("full-explore", res) if res else None


def endgame(game):
    return get_level(game, 'main', 'sanctum')


def amulet_safekeeping(game):
    """3.6.7 steal.c stealamulet() and the "mysterious force" of do.c only
    look at the Amulet carried directly (u.uhave.amulet): in a bag it can be
    neither stolen by the Wizard of Yendor nor send the hero back down.  The
    Wizard stole it in big-w09 g007/g009 and the bot spent tens of thousands
    of turns recovering it.  It must be out on Dlvl 1 (the up stairs ask to
    leave the dungeon without it) and in the Planes (offering, portals)."""
    found = have(game, real_amulet, {'bagged'})
    if not found:
        return None
    slot, item = found
    bagged = item is not inventory_slot(game, slot) and \
        item != inventory_slot(game, slot)
    out_needed = (at_planes(game)
                  or (branch_key(game) == 'main'
                      and game.get('dlvl') == "Dlvl:1"))
    if out_needed:
        if bagged:
            return with_reason("taking the Amulet out for the endgame",
                               unbag(game, slot, item))
        return None
    if not bagged:
        b = have(game, lambda i: i.get('name') in ("bag of holding",
                                                   "oilskin sack", "sack"),
                 {'noncursed'})
        if b:
            return with_reason("bagging the Amulet against theft",
                               put_in(b[0], slot))
    return None


_ASTRAL_UNIHORN = [-10]


def assisted_astral_rush(game):
    """Assisted tactics (invincibility): on the Astral Plane with the Amulet,
    go for the altars before fighting anything that is not in the way
    (fight has a higher priority than progress and kept the bot busy with
    Angels and player monsters)."""
    if not rules36.assisted_tactics() or branch_key(game) != 'astral':
        return None
    if not have(game, real_amulet, {'bagged'}):
        return None
    player = game['player']
    if has_hands(player) and 'ext-blind' in player['state']:
        return with_reason("assisted astral: fixing external blindness",
                           Wipe())
    # not unihorn_recoverable(): a 3.6 unicorn horn no longer restores
    # drained attributes, 'stat-drained' would loop
    # at most every 3 turns: in the Astral crowd stun/confusion come back
    # every turn and the hero would only ever apply the horn
    if (unihorn_recoverable(game)
            and set(player.get('state') or ()) & {'conf', 'stun', 'hallu',
                                                  'ill', 'blind'}
            and (game.get('turn') or 0) - _ASTRAL_UNIHORN[0] >= 3):
        found = _recovery_unihorn(game)
        if found:
            _ASTRAL_UNIHORN[0] = game.get('turn') or 0
            return with_reason("assisted astral: applying unihorn",
                               Apply(found[0]))
    res = _astral_known_altars(game)
    if res is not None:
        return with_reason("assisted: rushing to the high altar", res)
    return with_reason("assisted: rushing to the high altar",
                       seek_high_altar(game))


# dat/endgame.des "astral": ALTAR (07,09) (37,05) (67,09), map placed at
# (3,1) (sp_lev.c CENTER for a 75x20 map) -> engine (10,10) (40,6) (70,10)
# -> BotHack screen coordinates (x-1, y+1)
ASTRAL_ALTARS = (Pos(9, 11), Pos(39, 7), Pos(69, 11))


def _astral_known_altars(game):
    """Head for the fixed altar squares of the Astral Plane that are not
    known to be cross-aligned: the temples are dark and the generic
    exploration wanders (and pushes boulders in vain) instead."""
    level = curlvl(game)
    align = game['player']['alignment']
    targets = []
    for p in ASTRAL_ALTARS:
        t = at(level, p)
        if t is None:
            continue
        if t.get('feature') not in (None, 'altar'):
            return None          # not the expected map: generic behaviour
        if t.get('alignment') in (None, align):
            targets.append(p)
    if not targets:
        return None
    path = navigate(game, set(targets))
    if path is None:
        return None
    return with_reason("astral altar squares %s" % (targets,),
                       path['step'])


def progress(game):
    if not (endgame(game) or at_planes(game)):
        res = full_explore(game)
    else:
        res = (get_amulet(game) or visit(game, 'astral')
               or seek_high_altar(game))
    return with_reason("progress", res) if res else None


desired_weapons = ["Excalibur", "long sword", "katana"]
desired_suit = ["gray dragon scale mail", "silver dragon scale mail",
                "dwarvish mithril-coat", "elven mithril-coat", "scale mail",
                "splint mail"]
desired_shirt = ["T-shirt", "Hawaiian shirt"]
desired_boots = ["speed boots", "high boots", "iron shoes"]
desired_shield = ["shield of reflection", "small shield"]
desired_cloak = ["cloak of magic resistance", "cloak of protection",
                 "oilskin cloak", "elven cloak", "cloak of displacement",
                 "cloak of invisibility", "dwarvish cloak"]
desired_helmet = ["helm of telepathy", "helm of brilliance",
                  "dwarvish iron helm", "orcish helm"]
desired_gloves = ["gauntlets of power", "gauntlets of dexterity",
                  "leather gloves"]
blind_tool = ["blindfold", "towel"]
farm_tool = ["skeleton key", "lock pick"]

always_desired = {"magic lamp", "wand of wishing", "scroll of genocide",
                  "potion of gain level", "potion of full healing",
                  "potion of extra healing", "tallow candle", "wax candle"}

limited_desired = {"wand of death": 5, "scroll of identify": 5,
                   "scroll of remove curse": 18, "scroll of enchant armor": 5,
                   "scroll of earth": 3, "scroll of charging": 5,
                   "scroll of enchant weapon": 4, "amulet of life saving": 8}

desired_bag = ["oilskin sack", "sack", "bag of holding"]

desired_items = [
    ["pick-axe"],       # currently-desired presumes this is the first category
    ["skeleton key", "lock pick", "credit card"],
    ["ring of levitation", "boots of levitation"],
    ["ring of conflict"],
    ["ring of regeneration"],
    ["ring of invisibility"],
    ["Orb of Fate"],
    blind_tool,
    ["oil lamp", "brass lantern"],
    ["unicorn horn"],
    [CANDELABRUM],
    [BELL],
    [BOOK],
    ["lizard corpse"],
    ["ring of slow digestion"],
    ["sprig of wolfsbane"],
    ["helm of opposite alignment"],
    desired_cloak,
    desired_suit,
    desired_shield,
    desired_shirt,
    desired_boots,
    desired_helmet,
    desired_gloves,
    ["scroll of teleportation"],
    ["amulet of reflection"],
    ["amulet of ESP"],
    ["wand of fire"],
    ["wand of cold"],
    ["wand of lightning"],
    ["wand of teleportation"],
    ["wand of striking"],
    desired_weapons,
    desired_bag,
]

desired_singular = set(n for cat in desired_items for n in cat)


def desired_food(game):
    ns = nutrition_sum(game)
    if ns > 2400:
        min_nw = nw_ratio_avg(game)
    elif ns > 3500:
        min_nw = 50
    else:
        min_nw = 24
    if min_nw is None:
        min_nw = 24
    return [f['name'] for f in item_kinds['food']
            if not egg(f) and not tin(f) and not corpse(f)
            and nw_ratio(f) > min_nw]


def desired_throwables(game):
    amt_daggers = have_sum(game, dagger, {'noncursed'})
    amt_ammo = have_sum(game, dart, {'noncursed'})
    amt_rocks = have_sum(game, rocks, {'noncursed'})
    if amt_daggers > 3:
        return []
    if amt_ammo > 6:
        return list(DAGGERS)
    if amt_rocks > 6 and less_than(35, inventory(game)):
        return list(DAGGERS) + ["dart"]
    if less_than(30, inventory(game)):
        return list(DAGGERS) + ["dart", "rock"]
    return []


def utility(game_or_item, item=None):
    if item is None:
        i = game_or_item
        res = 0
        if artifact(i):
            res += 50
        if i.get('erosion') and not key_p(i):
            res -= i['erosion']
        if i.get('enchantment'):
            res += i['enchantment']
        if wand_p(i) and not i.get('charges'):
            res += 3
        if i.get('charges'):
            res += i['charges']
        if i.get('proof'):
            res += 3
        if blessed(i):
            res += 2
        # (uncursed? (:buc item)) - applied to the keyword, not the item, so
        # this clause of the original never fires; reproduced as-is.
        if uncursed(i.get('buc')) if isinstance(i.get('buc'), dict) else False:
            res += 1
        if cursed(i) and not i.get('in-use'):
            res -= 1
        return res
    game = game_or_item
    res = utility(item)
    iname = item_name(game, item)
    cat = find_first(lambda c: iname in c, desired_items)
    if cat is not None:
        res += 15 * (len(cat) - cat.index(iname))
    return res


def want_protection(game):
    return (game['player']['protection'] < 3 and game['player']['xplvl'] < 15)


def want_gold(game):
    return (want_protection(game)
            and available_gold(game) < 400 * (game['player']['xplvl'] + 1))


def currently_desired(game):
    cs = list(desired_items)
    if entering_shop(game) or shop(at_player(game)):
        cs = cs[1:]          # don't pick that pickaxe back up
    res = set(always_desired)
    for item, amt in limited_desired.items():
        if amt > have_sum(game, item, {'bagged'}):
            res.add(item)
    for c in cs:
        found = max_by(lambda kv: utility(game, kv[1]),
                       have_all(game, set(c), {'bagged'}))
        if found:
            iname = item_name(game, found[1])
            res.add(iname)
            for n in c:
                if n == iname:
                    break
                res.add(n)
        else:
            res.update(c)
    res.update(desired_food(game))
    res.update(desired_throwables(game))
    sanctum = get_level(game, 'main', 'sanctum')
    if sanctum and not have(game, real_amulet, {'bagged'}) and at(sanctum, 20,
                                                      11).get('seen'):
        res.add("Amulet of Yendor")
    if not fast(game['player']):
        res.add("wand of speed monster")
    if get_level(game, 'main', 'votd') and farm_done(game):
        res.discard("scroll of earth")
    if not endgame(game):
        res.discard("helm of opposite alignment")
    else:
        for n in (CANDELABRUM, BELL, BOOK, "scroll of enchant armor",
                  "scroll of enchant weapon", "wand of teleportation",
                  "wand of fire", "wand of cold", "wand of striking",
                  "ring of invisibility", "amulet of ESP"):
            res.discard(n)
    if want_gold(game):
        res.add("gold piece")
    return res


def handle_impairment(game):
    player = game['player']
    res = None
    if has_hands(player) and 'ext-blind' in player['state']:
        res = with_reason("fixing external blindness", Wipe())
    if res is None and unihorn_recoverable(game):
        found = _recovery_unihorn(game)
        if found:
            res = with_reason("applying unihorn to recover", Apply(found[0]))
    if res is None:
        found = have(game, set(blind_tool), {'worn', 'noncursed'})
        if found:
            res = with_reason("unblinding self", Remove(found[0]))
    if res is None and (impaired(player) or player.get('polymorphed')):
        res = with_reason("waiting out impairment", Repeated(Wait(), 10))
    return with_reason("impairment", res) if res else None


_TAKE_CURSED = {"levitation boots", "speed boots", "water walking boots",
                "cloak of displacement", "cloak of invisibility",
                "cloak of magic resistance", "cloak of protection",
                "elven cloak", "gauntlets of dexterity", "gauntlets of power",
                "helm of brilliance", "helm of opposite alignment",
                "helm of telepathy", "shield of reflection", "long sword",
                "unicorn horn", "scroll of identify", "skeleton key"}


def take_cursed(game, item):
    return bool(item_name(game, item) in _TAKE_CURSED
                or (not could_be(game, "bag of holding", item)
                    and (ring_p(item) or amulet_p(item) or tool_p(item)
                         or artifact(item) or wand_p(item))))


def want_buy(game, item):
    return False        # TODO


def should_try(game, item):
    if item.get('cost') or know_id(game, item):
        return False
    if wand_p(item):
        # ((some-fn (every-pred (complement :engrave)
        #                       (complement (partial tried? game)))
        #           (comp nil? :target))
        #  (item-id game item))
        # Every predicate in that some-fn is applied to the **item-id record**,
        # not to the item - including `tried?`, which then asks
        # `((:tried game) (appearance-of id-record))`.  An id record that still
        # has several candidates has no :name, so `appearance-of` is nil and the
        # wand counts as never tried however many times its appearance was
        # engrave-tested.  The port used to pass `item` here, which made an
        # engrave-tested wand fail `should-try?` and become junk: on the
        # 2-hour seed 40002 recording the port dropped the glass wand the
        # original kept, then livelocked trying to drop it again.
        iid = item_id(game, item) or {}
        return bool((not iid.get('engrave') and not tried(game, iid))
                    or iid.get('target') is None)
    if (scroll_p(item) or potion_p(item) or ring_p(item) or amulet_p(item)
            or armor_p(item)):
        return not tried(game, item) and safe(game, item)
    return False


def worthwhile(game, item):
    iname = item_name(game, item)
    if real_amulet(item):
        return True
    desired = _desired(game)
    return bool(
        not (enchantment(item) < -1)
        and not tin(item)
        and (food_p(item) or dart(item) or dagger(item) or gold(item)
             or rocks(item) or pick(item)
             or iname in desired
             or iname in limited_desired
             or should_try(game, item)
             or any(n in desired for n in (possible_names(game, item) or ())))
        and iname != "bag of tricks"
        and not (fast(game['player']) and iname == "wand of speed monster")
        and (charged(item) or iname == BELL or iname == "wand of death"
             or iname == "wand of wishing"
             or ('castle' in curlvl_tags(game)
                 and iname == "wand of striking"))
        and ((item.get('buc') != 'cursed' and item.get('erosion', 0) < 2)
             or enchantment(item) > 2 or take_cursed(game, item))
        and (not item.get('cost') or want_buy(game, item)))


def have_spare(game, itemname):
    return (have(game, itemname, {'can-remove', 'bagged'})
            or have(game, itemname, {'can-remove': False}))


def take_selector(game):
    player = game['player']
    farm = farming(game) and sink_p(at_player(game))
    need_bag = not have(game, bag) and have(game, scroll_p)

    def sel(item):
        if real_amulet(item):
            return True
        if not can_take(item):
            return False
        if recently_dropped_junk(game, item):
            return False
        if not (worthwhile(game, item)
                or (farm and could_be(game, "scroll of scare monster", item))):
            return False
        if not (not farm_level(game)
                or 'pudding' not in ((farm_sink(game) or {}).get('tags') or ())
                or have(game, "scroll of identify", {'bagged'})
                or (bag(item) and need_bag)
                or food_p(item) or scroll_p(item)):
            return False
        if not (less_than(49, inventory(game))
                or (less_than(52, inventory(game))
                    and any(n in _pickup_set(game, need_bag)
                            for n in (possible_names(game, item) or ())))):
            return False
        iname = item_name(game, item)
        if not ((item['qty'] < 16 or not rocks(item))
                and (not candle(item) or item['qty'] == 7)
                and (not potion_p(item) or know_id(game, item))):
            return False
        # (or (should-try? ...) (and farm? ...) (if-let [want ...] ...))
        if should_try(game, item):
            wanted = True
        elif farm and could_be(game, "scroll of scare monster", item):
            wanted = True
        else:
            want = find_first(lambda n: n in _desired(game),
                              possible_names(game, item) or ())
            if want is None:
                return False           # nothing about it is desired
            spare = (have_spare(game, item['name'])
                     if want in desired_singular else None)
            wanted = (utility(item) > utility(spare[1])) if spare else True
        if not wanted:
            return False
        spare = (have_spare(game, iname) if iname in desired_singular else None)
        if spare:
            return utility(item) > utility(spare[1])
        return True
    return sel


def _pickup_set(game, need_bag):
    res = {"scroll of scare monster", "scroll of identify", CANDELABRUM, BELL,
           BOOK}
    if need_bag:
        res |= {"sack", "oilskin sack"}
    if not have(game, food_p):
        res.add("food ration")
    return res


def interesting_container(game, item):
    return (explorable_container(item)
            and (bag(item) or (branch_key(game) != 'vlad'
                               and not in_gehennom(game))))


def examine_containers(game):
    found = have(game, explorable_container)
    if found:
        return with_reason("learning contents of", found[1], Apply(found[0]))
    return None


def unlockable_chest(game, tile):
    # same conjunction as the original, cheapest (tile-local) test first
    return bool(any(i.get('locked') for i in (tile.get('items') or ()))
                and not shop(tile) and not in_gehennom(game)
                and branch_key(game) != 'vlad'
                and (have_key(game) or have(game, dagger, {'noncursed'})))


def examine_containers_here(game):
    tile = at_player(game)
    if _no_pickup(game, tile):
        return None
    if (any(interesting_container(game, i) for i in (tile.get('items') or ()))
            and not sink_p(tile)):
        return with_reason("learning contents of containers on ground",
                           without_levitation(game, Loot()))
    if unlockable_chest(game, tile):
        k = have_key(game)
        if k:
            return without_levitation(game, with_reason(
                "unlock chest", Unlock(k[0], '.')))
        d = (have(game, dagger, {'safe', 'can-use'})
             or have(game, dagger, {'noncursed', 'can-use'}))
        if d:
            return without_levitation(game, with_reason(
                "unlock chest", make_use(game, d[0]) or ForceLock()))
    return None


def _no_pickup(game, tile):
    """Port: pickup failed here without using a turn (see actions.PickUp)."""
    t = tile.get('no-pickup')
    return t is not None and 0 <= (game.get('turn') or 0) - t < 500


def consider_items_here(game):
    player = game['player']
    tile = at_player(game)
    if not tile.get('items') or _no_pickup(game, tile):
        return None
    to_take = take_selector(game)
    level = curlvl(game)
    if not shop(tile):
        to_get = [i['label'] for i in lootable_items(tile) if to_take(i)]
        if to_get:
            r = with_reason("looting desirable items",
                            without_levitation(
                                game, take_out('.',
                                               {l: None for l in to_get})))
            if r:
                return r
        else:
            log.debug("no desired lootable items")
    to_get = [i['label'] for i in (tile.get('items') or ()) if to_take(i)]
    if to_get:
        from ..actions import arbitrary_move
        if (pit_p(tile) or spikepit_p(tile)) and not player.get('trapped'):
            return with_reason("getting desirable items",
                               without_levitation(
                                   game, with_reason("getting into a pit",
                                                     arbitrary_move(game,
                                                                    level))))
        return with_reason("getting desirable items",
                           without_levitation(game,
                                              PickUp(list(dict.fromkeys(
                                                  to_get)))))
    log.debug("no desired items here")
    return None


_BH = [None]


def _bell_note(game, key, turn):
    """`game` here is a value, not the atom: record on the bot's atom."""
    bh = _BH[0]
    if bh is not None:
        bh.game.swap(assoc, key, turn)


def _set_bell_hopeless(game, turn):
    _bell_note(game, 'bell-hopeless', turn)


def quest_bell(game):
    """The Bell of Opening is carried by the quest nemesis."""
    return fetch_invocation_item(game, BELL, 'quest', 'the Bell of Opening')


def vlad_candelabrum(game):
    """The Candelabrum of Invocation is carried by Vlad the Impaler, at the
    top of his tower (big-w06: 8 of the 12 most advanced games were only
    missing the Candelabrum)."""
    return fetch_invocation_item(game, CANDELABRUM, 'vlad',
                                 'the Candelabrum of Invocation')


def fetch_invocation_item(game, item, branch, what):
    """Go back to the level where the item's owner lives, hunt it, walk the
    level if nothing is known there; bounded, because the bot must carry on
    when the item cannot be reached.  BotHack only explored those levels and
    left without the item, making the invocation impossible thousands of
    turns later (cyc-03 g002, big-w06)."""
    if have(game, item, {'bagged'}):
        return None
    goal = get_level(game, branch, 'end')
    if goal is None:
        return None
    turn = game.get('turn') or 0
    # give up for a while when the goal level has nothing left to offer,
    # else this alternates with "leaving the quest" on the stairs
    # (cyc-04 g002 went up and down 50 times)
    hkey, skey = 'fetch-hopeless-' + branch, 'fetch-start-' + branch
    hopeless = game.get(hkey)
    if hopeless is not None and turn - hopeless < 5000:
        return None
    started = game.get(skey)
    if started is None:
        _bell_note(game, skey, turn)
    elif turn - started > 3000:
        # the nemesis is not where we can reach it (big-w05 g022, g024
        # hunted for thousands of turns on a quest level)
        log.warning("gave up on %s after %d turns", what, turn - started)
        _bell_note(game, hkey, turn)
        _bell_note(game, skey, None)
        return None
    if branch_key(game) != branch or game['dlvl'] != goal['dlvl']:
        return with_reason("going back for " + what,
                           seek_level(game, branch, 'end'))
    targets = [position(m) for m in curlvl_monsters(game)
               if m.get('peaceful') is False and not m.get('friendly')]
    if targets:
        r = seek(game, set(targets))
        if r:
            return with_reason("hunting the owner of " + what, r)
    # monsters are forgotten when the level is left: walk the level again to
    # find the nemesis (big-w04: "monsters seen: []" on arrival)
    r = seek(game, lambda t: (walkable(t) and not t.get('walked')
                              and not trap(t)), {'no-explore'})
    if r:
        return with_reason("touring the level for " + what, r)
    # the owner is often behind a closed or locked door (Vlad's room)
    r = seek(game, lambda t: t.get('feature') in ('door-closed',
                                                  'door-locked'),
             {'no-explore'})
    if r:
        return with_reason("opening the way to " + what, r)
    r = search_level(game, 1)
    if r:
        return with_reason("looking for " + what, r)
    mons = [(m.get('type') or {}).get('name') or m.get('glyph')
            for m in curlvl_monsters(game)]
    lvl = curlvl(game)
    tiles = list(tile_seq(lvl))
    unwalked = sum(1 for t in tiles if walkable(t) and not t.get('walked'))
    doors = sum(1 for t in tiles
                if t.get('feature') in ('door-closed', 'door-locked'))
    unknown_t = sum(1 for t in tiles if t.get('feature') is None)
    log.warning("no way to get %s on %s here, giving up until turn %d "
                "(monsters=%s unwalked=%d closed-doors=%d unknown=%d)",
                what, game.get('dlvl'), turn + 5000, mons[:10], unwalked,
                doors, unknown_t)
    _bell_note(game, hkey, turn)
    return None


def unstick_handler(bh):
    """Last resort, registered after `progress`, for when no handler answers
    (BotHack's search-level raises "stuck :-(" once it has nothing left to
    search - typically it cannot find the stairs it wants):

    1. main dungeon above the Castle, where going down is the objective:
       go down (trapdoor/hole, or dig);
    2. otherwise forget this level's search counts (at most once every 300
       turns) and search again for hidden passages;
    3. if the level keeps being hopeless (3 times), leave it by digging down
       whatever the objective: coming back by the stairs lands in the part
       of the level connected to them (e.g. after falling into a closed
       area)."""
    from ..pathing import go_down, navigate
    from ..dungeon import below_castle, update_curlvl, map_tiles
    from ..level import diggable_floor
    from ..player import have_pick
    from ..actions import Repeated, Search, dig
    from ..tile import lava_p
    last_reset = {}
    firings = {}

    def dig_anywhere(game, level):
        r = go_down(game, level)
        if r:
            return r
        pick_ = have_pick(game) if diggable_floor(level) else None
        if not pick_:
            log.warning("unstick: cannot dig here (pick=%s diggable_floor=%s"
                        " tags=%s)", bool(have_pick(game)),
                        diggable_floor(level), sorted(level.get('tags') or ()))
            return None

        def pred(t):
            return (t.get('feature') in ('floor', 'corridor')
                    and not shop(t) and not altar_p(t)
                    and not any(pool_p(n) or lava_p(n)
                                for n in neighbors(level, t)))
        p = navigate(game, pred)
        if p:
            return p['step'] or without_levitation(game, dig(pick_, '>'))
        from ..pathing import have_levi, have_levi_on
        log.warning("unstick: no reachable dig spot (candidates=%d levi=%s"
                    " levi_on=%s)",
                    sum(1 for t in tile_seq(level) if pred(t)),
                    bool(have_levi(game)), bool(have_levi_on(game)))
        return None

    def choose_action(game):
        level = curlvl(game)
        key = (game.get('branch-id'), game.get('dlvl'))
        turn = game.get('turn') or 0
        fired = [t for t in firings.get(key, []) if turn - t < 3000]
        fired.append(turn)
        firings[key] = fired
        if shop(at_player(game)):
            return None
        if (branch_key(game) == 'main' and not below_castle(game)
                and 'castle' not in level['tags']):
            r = dig_anywhere(game, level)
            if r:
                log.warning("unstick: going down (no other action)")
                return with_reason("unstick: no action chosen, going down", r)
        if len(fired) >= 3 and branch_key(game) not in ('sokoban',):
            r = dig_anywhere(game, level)
            if r:
                log.warning("unstick: leaving hopeless level %s", key)
                return with_reason("unstick: level hopeless, leaving it", r)
            if branch_key(game) not in ('main',):
                # cannot dig here (quest, Vlad...): use the stairs instead of
                # searching for 6000 turns (big-w05 g022 on Home 5)
                from ..actions import Ascend
                from ..tile import stairs_up_p
                r = (Ascend() if stairs_up_p(at_player(game))
                     else seek(game, stairs_up_p, {'no-explore'}))
                if r:
                    log.warning("unstick: leaving %s by the stairs", key)
                    return with_reason("unstick: leaving the level", r)
        if key not in last_reset or turn - last_reset[key] >= 300:
            last_reset[key] = turn
            log.warning("unstick: resetting search counts on %s", key)
            bh.game.swap(lambda g: update_curlvl(
                g, lambda l: assoc(l, 'tiles', map_tiles(
                    lambda t: assoc(t, 'searched', 0), l['tiles']))))
        return with_reason("unstick: no action chosen, searching",
                           Repeated(Search(), 15))
    return Handler(choose_action=choose_action)


def sokoban_no_levi(game):
    """Sokoban levels pull a levitating hero down into the pits ("Air
    currents pull you down into a pit!"); path finding already ignores
    levitation there, but a ring put on earlier stayed on."""
    if branch_key(game) != 'sokoban':
        return None
    found = have_levi_on(game)
    if found and not needs_levi(at_player(game)):
        return with_reason("no levitation in Sokoban",
                           remove_use(game, found[0]))
    return None


def remove_levi(game, path=None):
    if (not needs_levi(at_player(game))
            and game['branch-id'] not in ('water', 'air')
            and not any(needs_levi(t) for t in (path or ()))):
        found = have_levi_on(game)
        if found:
            return with_reason("don't want levi", remove_use(game, found[0]))
    return None


def consider_items(game):
    if (have(game, real_amulet, {'bagged'})
            and have(game, set(desired_weapons)) and at_planes(game)):
        return None
    to_take = take_selector(game)
    sanctum = 'sanctum' in curlvl_tags(game)

    def pred(t):
        if _no_pickup(game, t):
            return False
        if t.get('new-items'):
            return True
        if ((any(interesting_container(game, i) for i in (t.get('items') or ()))
             or unlockable_chest(game, t))
                and not sanctum and not sink_p(t)):
            return True
        return any(to_take(i) for i in
                   list(t.get('items') or ()) + lootable_items(t))
    p = navigate(game, pred, {'no-fight', 'no-levitation'})
    if p:
        return with_reason("new or desired item at", p['target'],
                           p['step'] or remove_levi(game))
    log.debug("no desirable items anywhere")
    return None


def uncurse_weapon(game):
    w = wielding(game)
    if w and cursed(w[1]):
        found = have(game, "scroll of remove curse", {'noncursed', 'bagged'})
        if found:
            return with_reason("uncursing weapon", w[1]['label'],
                               unbag(game, found[0], found[1])
                               or Read(found[0]))
    return None


def wield_weapon(game):
    player = game['player']
    if not overloaded(player) and has_hands(player):
        excal = find_first(lambda i: item_name(game, i) == "Excalibur",
                           at_player(game).get('items') or ())
        if excal:
            return PickUp(excal['label'])
    found = keep_first(lambda n: have(game, n, {'can-use'}), desired_weapons)
    if found:
        slot, weapon = found
        if not (weapon.get('wielded')
                or typekw(game.get('last-action')) in ('rub', 'wield')):
            return (uncurse_weapon(game)
                    or with_reason("wielding better weapon -", weapon['label'],
                                   make_use(game, slot)))
    return None


def wear_armor(game):
    for category in (desired_shield, desired_boots, desired_shirt,
                     desired_suit, desired_cloak, desired_helmet,
                     desired_gloves):
        found = keep_first(lambda n: have(game, n, {'can-use'}), category)
        if not found:
            continue
        slot, armor = found
        if (armor and not armor.get('worn')
                and not (farming(game) and boots(armor))
                and (item_name(game, armor) != "cloak of invisibility"
                     or not shop(at_player(game)))
                and typekw(game.get('last-action')) != 'takeoff'):
            r = with_reason("wearing better armor", make_use(game, slot))
            if r:
                return r
    return None


def light(item):
    return (item.get('specific') != "empty" and not item.get('cost')
            and item_subtype(item) == 'light'
            and (item_id(item) or {}).get('material') == 'copper')


def wearable(item):
    return armor_p(item) or ring_p(item) or amulet_p(item)


def bless_gear(game):
    found = have(game, {"Orb of Fate", "unicorn horn", "luckstone",
                        "bag of holding"}, {'nonblessed', 'know-buc'})
    if found:
        r = bless(game, found[0])
        if r:
            return r
    found = have(game, "scroll of remove curse", {'noncursed', 'bagged'})
    if not found:
        return None
    slot, scroll = found
    if not at_planes(game):
        s = have(game, lambda i: (wearable(i) and know_id(game, i)
                                  and item_name(game, i)
                                  != "helm of opposite alignment"),
                 {'can-use': True, 'cursed': True, 'in-use': False})
        if s:
            return with_reason("put on to uncurse", s[1]['label'],
                               make_use(game, s[0]))
    it = have(game, lambda i: cursed(i) and i.get('in-use'))
    if it:
        r = unbag(game, slot, scroll)
        if r:
            return with_reason("uncursing", it[1]['label'], r)
        if not (cursed(wielded_item(game) or {}) or at_planes(game)):
            c = have(game, cursed, {'in-use': False})
            if c:
                r = with_reason("wield for extra uncurse", wield(game, c[0]))
                if r:
                    return with_reason("uncursing", it[1]['label'], r)
        return with_reason("uncursing", it[1]['label'], Read(slot))
    u = None
    if (have(game, BOOK) and 'end' in curlvl_tags(game)):
        u = have(game, {CANDELABRUM, BOOK, BELL}, {'cursed'})
    if u is None:
        u = have(game, {"unicorn horn", "pick-axe", "Orb of Fate"}, {'cursed'})
    if u:
        return with_reason("misc uncurse",
                           unbag(game, slot, scroll) or wield(game, u[0]))
    return None


def lit_mines(game, level):
    if branch_key(game) != 'mines':
        return False
    from ..tile import floor_p, blank
    floors = [t for t in tile_seq(level)
              if floor_p(t) and distance(t, game['player']) > 5]
    if not floors:
        return False
    return not any(blank(t) for t in floors)


def want_light(game, level):
    return not (explored(game) or 'minetown' in level['tags']
                or branch_key(game) in ('air', 'water')
                or lit_mines(game, level))


def use_light(game, level):
    found = have(game, lambda i: i.get('lit') and light(i))
    if found:
        if (not could_be(game, "magic lamp", found[1])
                and not want_light(game, level)):
            return with_reason("saving energy", Apply(found[0]))
    found = have(game, lambda i: (could_be(game, "magic lamp", i)
                                  and not (i.get('cost') or i.get('lit'))))
    if found:
        return with_reason("using magic lamp", Apply(found[0]))
    if want_light(game, level) and not have(game, lambda i: i.get('lit')):
        found = have(game, light)
        if found:
            return with_reason("using any light source", Apply(found[0]))
    return None


def remove_rings(game):
    player = game['player']
    if not (farming(game) or endgame(game)):
        found = have(game, {"ring of slow digestion"}, {'worn'})
        if found:
            return with_reason("don't need SD", remove_use(game, found[0]))
    found = have(game, {"ring of invisibility", "ring of conflict"}, {'worn'})
    if found:
        return with_reason("don't need ring", remove_use(game, found[0]))
    if player['hp'] == player['maxhp']:
        found = have(game, "ring of regeneration", {'worn'})
        if found:
            return with_reason("don't need regen", remove_use(game, found[0]))
    return None


# port: item names dropped as junk -> turn.  worthwhile() can change once
# the item is carried (3 spears wanted, then junk), and the bot picked up and
# dropped the same stack forever (full-w02 g001, g003).
_JUNK_DROPPED = {}
JUNK_MEMORY_TURNS = 2000


def recently_dropped_junk(game, item):
    t = _JUNK_DROPPED.get(item.get('name'))
    return t is not None and 0 <= (game.get('turn') or 0) - t < JUNK_MEMORY_TURNS


def drop_junk(game):
    from ..actions import UNDROPPABLE_LABELS
    found = have(game, lambda i: (not worthwhile(game, i)
                                  and i.get('label') not in UNDROPPABLE_LABELS),
                 {'can-remove', 'bagged'})
    if found:
        slot, item = found
        r = remove_use(game, slot) or unbag(game, slot, item)
        if r is None:
            r = Drop(slot, item['qty'])
            if r is not None and item.get('name'):
                _JUNK_DROPPED[item['name']] = game.get('turn') or 0
        return with_reason("dropping junk", r)
    for cat in desired_items:
        cat_items = have_all(game, set(cat), {'bagged'})

        def stuck(kv):
            return kv[1].get('in-use') and not can_remove(game, kv[0])
        if (more_than(2, cat_items)
                or (more_than(1, cat_items)
                    and not any(stuck(x) for x in cat_items))):
            cand = [x for x in cat_items if not stuck(x)]
            found = min_by(lambda kv: utility(game, kv[1]), cand)
            if found:
                slot, item = found
                return with_reason(
                    "dropping less useful duplicate",
                    remove_use(game, slot) or unbag(game, slot, item)
                    or (None if item.get('in-use') else Drop(slot)))
            return None
    found = None
    if more_than(35, inventory(game)):
        found = have(game, rocks)
    if not found and more_than(44, inventory(game)):
        found = have(game, dart)
    if found:
        return with_reason("dropping ammo - low on inventory slots",
                           Drop(found[0], found[1]['qty']))
    found = have(game, lambda i: rocks(i) and i['qty'] > 7)
    if found:
        return with_reason("dropping rock excess",
                           Drop(found[0], found[1]['qty'] - 7))
    if not want_protection(game) and available_gold(game) > 0:
        return with_reason("don't want gold", Drop('$', available_gold(game)))
    return None


def remove_unsafe(game):
    found = have(game, lambda i: not safe(game, i), {'can-remove'})
    if found:
        return with_reason("removing potentially unsafe item",
                           remove_use(game, found[0]))
    return None


def enchant_gear(game):
    if endgame(game):
        return None
    found = have(game, "scroll of enchant armor", {'bagged', 'noncursed'})
    if not found:
        return None
    slot, item = found
    if have(game, lambda i: safe_enchant(i) and armor_p(i)):
        slots = [s for s, _ in have_all(game, lambda i: (not safe_enchant(i)
                                                         and armor_p(i)
                                                         and i.get('worn')))]
        if slots:
            if all(can_remove(game, s) for s in slots):
                return with_reason("enchant armor", remove_use(game, slots[0]))
            return None
        return with_reason("enchant armor",
                           unbag(game, slot, item) or Read(slot))
    return None


def reequip(game):
    level = curlvl(game)
    tile_path = [at(level, p) for p in (game.get('last-path') or ())]
    step = tile_path[0] if tile_path else None
    branch = branch_key(game)
    farm = farming(game)
    res = (wear_amulet(game) or drop_junk(game) or enchant_gear(game)
           or bless_gear(game) or wear_armor(game) or remove_unsafe(game)
           or remove_rings(game))
    if res is None and (farm or endgame(game)) and free_finger(game['player']) \
            and typekw(game.get('last-action')) != 'remove':
        found = have(game, "ring of slow digestion")
        if found:
            res = make_use(game, found[0])
    if res is None and farm and not farm_done(game):
        found = have(game, "speed boots")
        if found:
            res = remove_use(game, found[0])
    if res is None and not fast(game['player']):
        found = have(game, "wand of speed monster", {'bagged'})
        if found:
            res = with_reason("zapping self with /oSpeed",
                              unbag(game, found[0], found[1])
                              or ZapWandAt(found[0], '.'))
    if (res is None and typekw(game.get('last-action')) != 'wield'
            and step and not step.get('dug')
            and all(walkable(t) for t in tile_path)):
        if branch in ('air', 'fire') and not any(portal_p(t)
                                                 for t in tile_seq(level)):
            found = have(game, real_amulet)
            if found and not found[1].get('in-use'):
                res = with_reason("using amulet to search for portal",
                                  wield(game, found[0]))
    if res is None:
        res = use_light(game, level)
    if res is None:
        res = remove_levi(game, tile_path)
    return res


def reequip_weapon(game):
    if (typekw(game.get('last-action')) != 'apply'
            and not amulet_p(wielded_item(game) or {'name': ''})
            and not at_player(game).get('dug')):
        return wield_weapon(game)
    return None


def _bait_wizard(game, level, monster):
    from ..tile import lava_p, unknown
    if (monster.get('color') == 'magenta' and monster['glyph'] == '@'
            and (not typename(monster) or typename(monster)
                 == "Wizard of Yendor")
            and branch_key(game) not in ('water', 'earth', 'astral')
            and (pool_p(at(level, monster)) or lava_p(at(level, monster))
                 or unknown(at(level, monster)))):
        p = navigate(game, lambda t: all(not (lava_p(n) or pool_p(n))
                                         for n in neighbors(level, t)),
                     {'explored', 'no-dig'})
        return with_reason("baiting possible wizard away from water/lava",
                           (p['step'] if p else None) or Wait())
    return None


def _bait_giant(game, level, monster):
    if (monster['glyph'] == 'H' and level['dlvl'] == "Home 3"
            and not have_pick(game) and monster['y'] == 12
            and 18 < monster['x'] < 25):
        p = navigate(game, {Pos(26, 12), Pos(16, 12)})
        return with_reason("baiting giant away from corridor",
                           (p['step'] if p else None) or Wait())
    return None


def ranged(game, monster):
    if _hypocrite_attack(game, monster):
        return None
    found = have_throwable(game)
    if found:
        return with_reason("ranged combat",
                           Throw(found[0], towards(game['player'], monster)))
    return None


def hit_floating_eye(game, monster):
    player = game['player']
    if adjacent(player, monster) and typename(monster) == "floating eye":
        res = wield_weapon(game)
        if res is None and (blind(player) or reflection(game)
                            or free_action(game)):
            res = Attack(towards(player, monster))
        if res is None:
            found = have(game, set(blind_tool), {'noncursed'})
            if found:
                res = PutOn(found[0])
        if res is None:
            res = ranged(game, monster)
        return with_reason("killing floating eye", res) if res else None
    return None


def corrodeproof_weapon(item):
    return weapon_p(item) and (artifact(item) or item.get('proof'))


def hit_corrosive(game, monster):
    if not corrosive(monster):
        return None
    found = have(game, corrodeproof_weapon, {'can-use', 'noncursed'})
    if found:
        res = make_use(game, found[0])
    else:
        w = wielding(game)
        res = None
        if w and not cursed(w[1]):
            res = Wield('-')
    if res is None:
        res = Move(towards(game['player'], monster))
    return with_reason("hitting corrosive monster", monster, res)


def mobile(game, monster):
    return bool(not mimic(monster) and not sessile(monster)
                and (monster.get('awake')
                     or game['turn'] - monster['first-known'] < 6))


def kite(game, monster):
    player = game['player']
    if (adjacent(player, monster)
            and typename(monster) in ("black pudding", "brown pudding",
                                      "dwarf", "mumak")
            and mobile(game, monster) and player['ac'] > -7
            and game['rng'].randrange(20) > 0
            and not monster.get('just-moved')):
        p = navigate(game, lambda t: distance(monster, t) == 2,
                     {'max-steps': 1, 'no-traps': True, 'no-fight': True,
                      'walking': True})
        return with_reason("kite", p['step'] if p else None)
    return None


def hit_surtur(game, monster):
    if typename(monster) == "Lord Surtur":
        found = have(game, "wand of cold", {'can-use'})
        if found:
            return ZapWandAt(found[0], towards(game['player'], monster))
    return None


def hit_wizard(game, monster):
    if typename(monster) in ("Wizard of Yendor", "Ashikaga Takauji", "Famine",
                             "Pestilence"):
        found = have(game, "wand of death", {'can-use'})
        if found:
            return ZapWandAt(found[0], towards(game['player'], monster))
    return None


def hit_leprechaun(game, monster):
    if leprechaun(monster):
        found = have(game, "gold piece")
        if found:
            return DropSingle('$', found[1]['qty'])
    return None


def _hypocrite_attack(game, monster):
    """mon.c setmangry: attacking (melee, throw, zap) a monster that respects
    Elbereth, or a peaceful, while standing on Elbereth."""
    return bool(e_p(at_player(game))
                and (rules36.respects_elbereth(monster)
                     or monster.get('peaceful')))


def hit(game, level, monster):
    player = game['player']
    if _hypocrite_attack(game, monster):
        return None
    res = _bait_wizard(game, level, monster)
    if res is None:
        res = _bait_giant(game, level, monster)
    if res is None and branch_key(game) == 'air' and not have_levi_on(game):
        found = have_levi(game)
        if found:
            res = with_reason("levitation for :air", make_use(game, found[0]))
    if res is None and adjacent(player, monster):
        res = (hit_wizard(game, monster) or hit_leprechaun(game, monster)
               or hit_surtur(game, monster) or hit_floating_eye(game, monster)
               or kite(game, monster) or hit_corrosive(game, monster)
               or wield_weapon(game))
        if res is None:
            if (not tile_monster(at(level, monster))
                    or monster['glyph'] in ('I', '1', '2', '3', '4', '5')):
                res = Attack(towards(player, monster))
            else:
                res = Move(towards(player, monster))
    return with_reason("hitting", monster, res) if res else None


def kill_engulfer(game):
    if game['player'].get('engulfed'):
        return with_reason("killing engulfer",
                           wield_weapon(game) or Move('E'))
    return None


def low_hp(player):
    return player['hp'] < 10 or (player['hp'] / player['maxhp']) <= 9 / 20


def can_ignore(game, monster):
    return bool(passive(monster) or not hostile(monster) or unicorn(monster)
                or (pool_p(at_curlvl(game, monster)) and not flies(monster)
                    and not any(pool_p(t) for t in neighbors(curlvl(game),
                                                             game['player'])))
                or typename(monster) in ("grid bug", "newt", "leprechaun")
                or (mimic(monster) and not adjacent(game['player'], monster)))


def pushover(game, monster):
    return bool(can_ignore(game, monster)
                or (game['player']['ac'] <= -14
                    and (monster['glyph'] in ('a', 'b', 's', 'S', 'B')
                         or monster.get('name') == "gremlin")))


def can_handle(game, monster):
    player = game['player']
    if drowner(monster) and pool_p(at_curlvl(game, monster)):
        return False
    tn = typename(monster)
    if tn == "floating eye":
        return bool(blind(player) or reflection(game) or free_action(game)
                    or have_throwable(game)
                    or have(game, set(blind_tool), {'noncursed'}))
    if tn == "blue jelly":
        return bool(have_intrinsic(player, 'cold') or player['hp'] > 60)
    if tn in ("spotted jelly", "ochre jelly"):
        return bool(have(game, corrodeproof_weapon) and player['hp'] > 60)
    return True


def _engrave_slot(game, perma):
    if perma:
        found = have(game, {"wand of fire", "wand of lightning"})
        if found:
            return found[0]
    return '-'


def engrave_e(game, perma=False, farm=False):
    player = game['player']
    tile = at_player(game)
    # 3.6.7: useless in Gehennom and the planes; the text must be exactly
    # "Elbereth" (engrave.c sengr_at strict), so never append; a permanent
    # engraving that is not Elbereth cannot be wiped with dust.
    if not rules36.elbereth_effective_here(game):
        return None
    if e_p(tile) and (not perma or perma_e(tile)):
        return None
    if (tile.get('engraving') and tile.get('engraving-type') == 'permanent'
            and not e_p(tile) and not perma):
        return None
    append = False
    if has_hands(player) and engravable(tile):
        res = remove_levi(game)
        if res is None and can_engrave(game):
            res = Engrave(_engrave_slot(game, perma),
                          "Elbereth" + ("*" if farm else ""), append)
        return with_reason("engrave E", res) if res else None
    return None


def pray_for_hp(game):
    player = game['player']
    # 3.6.7 pray.c critically_low_hp() (3.4.3: hp < 1/7 max)
    if _can_pray(game) and rules36.critically_low_hp(player):
        from ..actions import Pray
        return with_reason("praying for hp", Pray())
    return None


def exposed(game, level, pos):
    return bool(more_than(2, [t for t in neighbors(level, pos)
                              if walkable(t) or pool_p(t)]))


def safe_hp(player):
    return (player['hp'] / player['maxhp']) >= 9 / 10 or player['hp'] > 175


def recover(game, safe=False):
    player = game['player']
    if safe_hp(player):
        return None
    if free_finger(player):
        found = have(game, "ring of regeneration", {'noncursed'})
        if found:
            return with_reason("recover - regen", make_use(game, found[0]))
    if safe and not at_planes(game):
        p = navigate(game, lambda t: t.get('new-items'),
                     {'no-fight': True, 'no-autonav': True, 'no-traps': True,
                      'explored': True, 'no-levitation': True,
                      'max-steps': 10})
        if p:
            return with_reason("recovering - exploring nearby items",
                               p['step'] or remove_levi(game))
    if branch_key(game) == 'astral':
        return with_reason("rush astral", seek_high_altar(game))
    p = navigate(game, lambda t: not exposed(game, curlvl(game), t),
                 {'max-steps': 8, 'no-traps': True, 'explored': True,
                  'no-fight': True})
    if p and p['step']:
        return with_reason("moving to safer position", p['step'])
    return with_reason("recovering", Repeated(Wait(), 10))


def retreat(game):
    player = game['player']
    if not low_hp(player):
        return None
    level = curlvl(game)
    tile = at(level, player)
    threats = _threat_map(game)
    adjacent_m = [m for m in (monster_at(level, n) for n in neighbors(player))
                  if m is not None and hostile(m)]
    res = pray_for_hp(game)
    if res is None and not have(game, amulet_p, {'worn'}):
        res = wear_amulet(game)          # replace LS
    if res is None:
        res = kill_engulfer(game)
    if (res is None
            and rules36.elbereth_effective_here(game)
            and any(not m.get('fleeing') and not passive(m)
                    for m in adjacent_m)
            and all(rules36.respects_elbereth(m) for m in adjacent_m)
            and not perma_e(tile) and can_engrave(game)):
        if engravable(tile):
            res = with_reason("retreat engrave",
                              engrave_e(game, not any(ignores_e(m)
                                                      for m in
                                                      clj_vals(threats))))
        else:
            from ..dungeon import passable_walking
            t = find_first(lambda x: (engravable(x)
                                      and not monster_at(level, x)
                                      and passable_walking(game, level, tile, x)
                                      and less_than(len(adjacent_m),
                                                    [n for n in neighbors(x)
                                                     if position(n)
                                                     in threats])),
                           neighbors(level, tile))
            if t:
                res = with_reason("moving to neighbor tile to engrave",
                                  Move(towards(player, t)))
    if res is None and (not threats
                        or (perma_e(tile)
                            and rules36.elbereth_effective_here(game)
                            and not any(ignores_e(m)
                                        for m in clj_vals(threats)))):
        res = recover(game)
    if res is None:
        p = navigate(game, stairs_up_p, {'no-fight', 'explored', 'no-autonav',
                                         'walking'})
        if p:
            if stairs_up_p(at(level, player)):
                if threats and dlvl(game) != 1:
                    res = with_reason("retreating upstairs", Ascend())
                else:
                    res = with_reason("prepared to retreat upstairs", Search())
            else:
                step = p['step']
                if step and (
                        (p.get('target') is not None and step.get('path')
                         and position(p['target'])
                         == position(step['path'][0]))
                        or (step.get('dir') and not any(
                            position(n) in threats for n in neighbors(
                                in_direction(player, step['dir']))))):
                    res = step
    if res is None:
        from ..dungeon import passable_walking
        nbr = find_first(lambda x: (not exposed(game, level, x)
                                    and passable_walking(game, level, tile, x)
                                    and not monster_at(level, x)
                                    and not any(position(n) in threats
                                                for n in neighbors(x))),
                         neighbors(level, tile))
        if nbr:
            res = with_reason("running away", Move(towards(tile, nbr)))
    if res is None:
        log.debug("retreat failed")
    return with_reason("retreating", res) if res else None


def keep_away(game, m):
    player = game['player']
    if (pool_p(at_curlvl(game, m)) and (drowner(m) or not typename(m))
            and not have(game, "oilskin cloak", {'worn'})):
        return True
    montype = typename(m)
    if montype:
        if any(s in montype for s in ("nymph", "rust monster", "disenchanter",
                                      "mind flayer")):
            return True
        if montype == "homunculus" and not have_intrinsic(player, 'sleep'):
            return True
    return False


def targettable(game, max_dist=6, ray=False):
    level = curlvl(game)
    player = game['player']
    res = []
    for d in DIRECTIONS:
        tiles = []
        cur = player
        for _ in range(max_dist):
            cur = in_direction(level, cur, d)
            if cur is None:
                break
            tiles.append(cur)
        from ..tile import lava_p
        if not ray and any(pool_p(t) or lava_p(t) or sink_p(t) for t in tiles):
            continue
        if any(t.get('room') for t in tiles):
            continue
        monsters = []
        for t in tiles:
            if not (walkable(t) or boulder(t)):
                break
            m = monster_at(level, t)
            if m:
                monsters.append(m)
        if not all(hostile(m) for m in monsters):
            continue
        target = monsters[0] if monsters else None
        if target and not target.get('remembered'):
            res.append(target)
    return res


def use_rings(game, threats):
    player = game['player']
    if (free_finger(player) and 'minetown' not in curlvl(game)['tags']
            and not any(t.get('room') for t in neighbors(curlvl(game), player))
            and more_than(3, threats)):
        found = have(game, "ring of conflict", {'noncursed'})
        if found:
            return with_reason("conflict for combat", make_use(game, found[0]))
    if free_finger(player) and not endgame(game):
        if ((not any(sees_invisible(m) for m in threats)
             and more_than(1, threats))
                or any(not sees_invisible(m) and keep_away(game, m)
                       for m in threats)):
            found = have(game, "ring of invisibility", {'noncursed'})
            if found:
                return with_reason("invis for combat",
                                   make_use(game, found[0]))
    return None


def hits_hard(m):
    return typename(m) in ("winged gargoyle", "Olog-hai", "salamander")


def castle_fort(game, level):
    if ('castle' in level['tags']
            and not at(level, 35, 15).get('walked')
            and not at(level, 35, 14).get('walked')
            and not at(level, 40, 8).get('walked')
            and not at(level, 40, 16).get('walked')
            and position(at_player(game)) == position(Pos(35, 12))
            and game['rng'].randrange(16) > 0):
        return with_reason("stay in fort", Search())
    return None


def castle_move(game, level):
    if 'castle' in level['tags']:
        if (position(at_player(game)) == position(Pos(12, 13))
                and boulder(at(level, 11, 13)) and boulder(at(level, 11, 14))
                and not boulder(at(level, 10, 13))
                and not monster_at(level, Pos(10, 13))):
            return with_reason("make castle fort",
                               without_levitation(game, Move('W')))
    return None


def clear_farm(game):
    player = game['player']
    if at_player(game).get('engraving') == "Elbereth*" and farm_done(game):
        t = find_first(boulder, neighbors(curlvl(game), player))
        if t:
            p = navigate(game, t)
            return with_reason("clear farm", p['step'] if p else None)
    return None


def destroy_drawbridges(game, level):
    player = game['player']
    if branch_key(game) == 'quest':
        db = find_first(drawbridge, neighbors(level, player))
        if db:
            from ..tile import wall_p
            if (have_levi(game) and not drawbridge(at(level, player))
                    and not any(wall_p(t) for t in neighbors(level, player))):
                found = have(game, "wand of striking")
                if found:
                    return with_reason("destroy drawbridge",
                                       ZapWandAt(found[0],
                                                 towards(player, db)))
    return None


def fight(game):
    player = game['player']
    level = curlvl(game)
    nav_opts = {'adjacent': True, 'no-traps': True, 'no-autonav': True,
                'walking': True, 'max-steps': _hostile_dist_thresh(game)}
    res = kill_engulfer(game)
    if res is None:
        res = castle_move(game, level)
    if res is None:
        res = destroy_drawbridges(game, level)
    if res is not None:
        return res

    # (->> (hostile-threats game) (remove (partial can-ignore? game)) set)
    threats = clj_set_order([m for m in hostile_threats(game)
                             if not can_ignore(game, m)], monster_hasheq)
    adjacent_m = [m for m in (monster_at(level, n) for n in neighbors(player))
                  if m is not None and hostile(m) and not can_ignore(game, m)]

    # 3.6.7: the original engraved Elbereth here and then kept fighting from
    # the square; attacking from it now erases it and costs alignment
    # (mon.c setmangry), so this tactic is removed.
    if (exposed(game, level, player) and game['rng'].randrange(10) > 0
            and more_than(1, [m for m in adjacent_m if mobile(game, m)])):
        p = navigate(game, lambda t: (not exposed(game, level, t)
                                      and not any(monster_at(level, n)
                                                  for n in including_origin(
                                                      neighbors, t))),
                     {'max-steps': 2, 'no-traps': True, 'no-fight': True,
                      'explored': True})
        if p and p['step']:
            return with_reason("moving to non-exposed position", p['step'])
    if (not rules36.assisted_tactics()
            and exposed(game, level, player)
            and any(mobile(game, m) for m in adjacent_m)
            and (more_than(1, [m for m in threats if ignores_e(m)])
                 or more_than(2, [m for m in threats
                                  if mobile(game, m) and not pushover(game, m)
                                  and not slow(m)]))):
        p = navigate(game, stairs_up_p, {'max-steps': 40, 'no-autonav': True,
                                         'walking': True, 'explored': True})
        if p:
            path = p['path'] or []
            bad = False
            for t in path:
                for n in including_origin(neighbors, t):
                    m = monster_at(level, n)
                    if m and not pushover(game, m) and (game['turn']
                                                        - m['known'] > 20):
                        bad = True
            exposed_prefix = []
            for t in path:
                if not exposed(game, level, t):
                    break
                exposed_prefix.append(t)
            if (not bad and less_than(8, exposed_prefix)
                    and game['rng'].randrange(20) > 0):
                r = with_reason("moving towards the upstairs", p['step'])
                if r:
                    return r
    monster = (find_first(rider, adjacent_m)
               or find_first(lambda m: unique(m) or titan(m), adjacent_m)
               or find_first(priest, adjacent_m)
               or find_first(werecreature, adjacent_m)
               or find_first(ignores_e, adjacent_m)
               or find_first(lambda m: m['glyph'] in ('I', '5'), adjacent_m)
               or find_first(hits_hard, adjacent_m)
               or find_first(nasty, adjacent_m)
               or find_first(lambda m: m['glyph'] in ('4', '3', '2'), adjacent_m))
    if monster:
        r = hit(game, level, monster)
        if r:
            return r
    r = clear_farm(game)
    if r:
        return r
    m = min_by(lambda x: distance(player, x),
               [x for x in threats
                if keep_away(game, x) and not x.get('fleeing')
                and not x.get('remembered') and mobile(game, x)])
    if m and distance(player, m) < 3 and game['rng'].randrange(15) > 0:
        r = with_reason("trying to keep away from", m, engrave_e(game))
        if r:
            return r
    m = find_first(lambda x: keep_away(game, x) and not adjacent(player, x),
                   targettable(game))
    if m:
        r = with_reason("keep-away monster", m, ranged(game, m))
        if r:
            return r
    if threats:
        p = navigate(game, set(position(m) for m in threats), nav_opts)
        if p:
            monster = monster_at(level, p['target'])
            res = (use_rings(game, threats)
                   or (hit(game, level, monster) if monster else None)
                   or castle_fort(game, level))
            if res is None:
                step = p['step']
                if (more_than(2, [m for m in threats if mobile(game, m)])
                        and not exposed(game, level, player)
                        and step and step.get('dir')
                        and exposed(game, level,
                                    in_direction(player, step['dir']))):
                    if game['rng'].randrange(13) > 0:
                        res = with_reason("staying in more favourable position",
                                          Search())
                if res is None:
                    m2 = find_first(lambda x: (distance(player, x) == 2
                                               and not pushover(game, x)
                                               and mobile(game, x)), threats)
                    if m2 and (game['rng'].randrange(30 if slow(m2) else 10) > 0
                               and not passive(m2) and not m2.get('fleeing')
                               and not spellcaster(m2)):
                        res = with_reason("baiting monsters", Search())
                if res is None:
                    res = step
            if res is not None:
                return with_reason("targetting enemy", monster, res)
    if branch_key(game) != 'astral':
        leftovers = clj_set_order([m for m in hostile_threats(game)
                                   if can_ignore(game, m)
                                   and can_handle(game, m)], monster_hasheq)
        if leftovers:
            p = navigate(game, set(position(m) for m in leftovers),
                         dict(nav_opts, explored=True))
            if p:
                monster = monster_at(level, p['target'])
                res = (hit(game, level, monster) if monster else None) \
                    or p['step']
                if res:
                    return with_reason("targetting leftover enemy", monster,
                                       res)
    if branch_key(game) == 'sokoban' and typekw(game.get('last-action')) \
            == 'move':
        dir_ = (game.get('last-action') or {}).get('dir')
        if dir_ and boulder(in_direction(level, player, dir_)) \
                and position(player) == position(game.get('last-position')):
            m = monster_at(game, in_direction(in_direction(player, dir_),
                                              dir_))
            if m and m['first-known'] + 10 < game['turn']:
                r = with_reason("ranged attack soko blocker",
                                ranged(game, m))
                if r:
                    return r
    return castle_fort(game, level)


def fight_covetous(game):
    m = find_first(lambda x: covetous(x) and hostile(x) and mobile(game, x),
                   curlvl_monsters(game))
    if m:
        p = navigate(game, m)
        return with_reason("going to kill", typename(m),
                           p['step'] if p else None)
    return None


def _bribe_demon(prompt):
    return parse_int(re_first_group(
        r'demands ([0-9][0-9]*) zorkmids for safe passage', prompt))


def eat_all(game):
    return bool(hungry(game['player']) or nutrition_sum(game) < 1000
                or (have_intrinsic(game, 'fire')
                    and have_intrinsic(game, 'poison')))


def feed(game):
    player = game['player']
    if satiated(player) or overloaded(player):
        return None
    if branch_key(game) == 'astral':
        found = _choose_food(game)
        if found:
            slot, food = found
            return with_reason("eating against Famine", food,
                               unbag(game, slot, food) or Eat(slot))

    def beneficial(pos, item):
        return fresh_corpse(game, pos, item) and want_to_eat(player, item)

    def edible_here(pos, item):
        return fresh_corpse(game, pos, item) and edible(player, item)

    p = navigate(game, lambda t: any(beneficial(t, i)
                                     for i in (t.get('items') or ())))
    if p:
        r = p['step']
        if r is None:
            it = find_first(lambda i: beneficial(game['player'], i),
                            at_player(game).get('items') or ())
            if it:
                r = without_levitation(game, Eat(it['label']))
        if r:
            return with_reason("want to eat corpse at", p['target'], r)
    if eat_all(game):
        p = navigate(game, lambda t: any(edible_here(t, i)
                                         for i in (t.get('items') or ())))
        if p:
            r = p['step']
            if r is None:
                it = find_first(lambda i: edible_here(game['player'], i),
                                at_player(game).get('items') or ())
                if it:
                    r = without_levitation(game, Eat(it['label']))
            if r:
                return with_reason("going to eat corpse at", p['target'], r)
    return None


def offer_amulet(game):
    if game['branch-id'] != 'astral':
        return None
    tile = at_player(game)
    if not altar_p(tile):
        return None
    player = game['player']
    if player['alignment'] == OPPOSITE_ALIGNMENT.get(tile.get('alignment')):
        found = have(game, "helm of opposite alignment",
                     {'can-use', 'bagged'})
        if found:
            return unbag(game, found[0], found[1]) or make_use(game, found[0])
    if player['alignment'] == tile.get('alignment'):
        found = have(game, real_amulet, {'bagged'})
        if found:
            return (unbag(game, found[0], found[1]) or Offer(found[0]))
    return None


def detect_portal(bh):
    h = Handler()

    def choose_action(game):
        player = game['player']
        if branch_key(game) != 'water' or player.get('polymorphed'):
            return None
        found = have(game, "scroll of gold detection", {'safe-buc', 'bagged'})
        if not found:
            return None
        scroll, s = found
        r = unbag(game, scroll, s)
        if r:
            return with_reason("detecting portal", r)
        if confused(player):
            deregister_handler(bh, h)
            return with_reason("detecting portal", Read(scroll))
        if not any(distance(player, m) < 4 and hostile(m)
                   for m in curlvl_monsters(game)):
            p2 = have(game, {"potion of confusion", "potion of booze"},
                      {'nonblessed', 'bagged'})
            if p2:
                return with_reason("detecting portal",
                                   with_reason("confusing self",
                                               unbag(game, p2[0], p2[1])
                                               or Quaff(p2[0])))
        return None
    h.choose_action = choose_action
    return h


def _seek_fountain(game):
    from ..level import ORACLE_POSITION
    oracle = get_level(game, 'main', 'oracle')
    res = None
    if oracle is None or not any(t.get('seen')
                                 for t in neighbors(oracle, ORACLE_POSITION)):
        res = (seek_level(game, 'main', 'oracle')
               or seek(game, ORACLE_POSITION, {'adjacent'}))
    if res is None and oracle is not None and any(fountain_p(t)
                                                  for t in tile_seq(oracle)):
        res = seek_level(game, 'main', 'oracle')
    if res is None:
        # (if-let [{:keys [step]} (and (not (:minetown (curlvl-tags game)))
        #                              (navigate game fountain?))]
        #   step        <- binds on the Path, so this is nil when we are already
        #                  standing on the fountain, and the else branch is NOT
        #                  taken: seek-fountain returns nil and make-excal dips
        #   (or ...))
        p = (navigate(game, fountain_p)
             if 'minetown' not in curlvl_tags(game) else None)
        if p is not None:
            res = p['step']
        else:
            if oracle is not None:
                d = prev_dlvl(oracle['dlvl'])
                while d != "Dlvl:0":
                    lvl = get_level(game, 'main', d)
                    if lvl and any(fountain_p(t) for t in tile_seq(lvl)):
                        res = seek_level(game, 'main', d)
                        break
                    d = prev_dlvl(d)
            if res is None:
                res = seek_feature(game, 'fountain')
    return with_reason("seeking a fountain to make Excal", res) if res else None


def make_excal(game):
    player = game['player']
    if (player['xplvl'] >= 5
            and (player['ac'] <= 3 or get_level(game, 'mines', 'end'))):
        found = have(game, "long sword")
        if found:
            from ..actions import Dip
            res = _seek_fountain(game)
            if res is None and fountain_p(at_player(game)):
                res = without_levitation(game, Dip(found[0], '.'))
            return with_reason("getting Excal", res) if res else None
    return None


def excal_handler(bh):
    h = Handler()

    def choose_action(game):
        if have(game, "Excalibur"):
            deregister_handler(bh, h)
            log.warning("got excal")
            return None
        if 'excalibur' in rules36.skipped_steps():
            return None
        return make_excal(game)
    h.choose_action = choose_action
    return h


def rob(m):
    return typename(m) in ("dwarf", "dwarf lord", "dwarf king", "hobbit")


def rob_peacefuls(game):
    player = game['player']
    level = curlvl(game)

    def pred(t):
        m = monster_at(level, t)
        if not m:
            return False
        return (not unicorn(m) and not shop(t) and game['dlvl'] != "Home 1"
                and (blocked(t) or rob(m)))
    p = navigate(game, pred, {'adjacent'})
    if p:
        return with_reason("robbing a poor peaceful dorf",
                           p['step'] or Attack(towards(player, p['target'])))
    return None


def wander(game):
    from ..tile import corridor_p, floor_p
    res = explore(game) or search_level(game, 1)
    if res is None:
        cands = [t for t in tile_seq(curlvl(game))
                 if not boulder(t) and (floor_p(t) or corridor_p(t))
                 and t.get('walked')]
        t = min_by(lambda x: x['walked'], cands)
        if t:
            p = navigate(game, t)
            res = p['step'] if p else None
    return with_reason("wandering", res) if res else None


def _hunt_action(game, robbed_of):
    player = game['player']
    if not robbed_of:
        return None
    _, dlvl_, branch, _ = robbed_of[0]
    level = curlvl(game)
    stealers = [m for m in clj_vals(level['monsters']) if steals(m)]
    recent = max_by(lambda m: m['known'], stealers)
    res = seek_level(game, branch, dlvl_)
    if res is None and (not recent or game['turn'] - recent['known'] > 11) \
            and have_intrinsic(player, 'telepathy'):
        found = have(game, set(blind_tool), {'noncursed'})
        if found:
            res = make_use(game, found[0])
    if res is None and stealers:
        p = navigate(game, nav_targets(stealers))
        if p and p['step']:
            res = p['step']
    if res is None:
        res = wander(game)
    return with_reason("seeking monsters that stole my items:", robbed_of,
                       res) if res else None


def _found_item(found, entry):
    _, _, _, item = entry
    keys = ('specific', 'proof', 'name', 'enchantment')
    target = {k: item.get(k) for k in keys}
    return any({k: i.get(k) for k in keys} == target for i in found)


def _amulet_escape(game, entry):
    turn, dlvl_, branch, item = entry
    if (real_amulet(item) and dlvl_ == game['dlvl'] and branch == 'main'
            and branch_key(game) == 'main'):
        if dlvl_ == "Dlvl:1":
            log.warning("assuming amulet is downstairs")
            return (turn + 5000, get_dlvl(game, 'main', 'sanctum'), 'main',
                    item)
        log.warning("assuming amulet is upstairs")
        return (turn + 500, prev_dlvl(dlvl_), branch, item)
    return entry


def hunt(bh):
    robbed_of = []

    def choose_action(game):
        return _hunt_action(game, robbed_of)

    def about_to_choose(game):
        player = game['player']
        before = list(robbed_of)
        robbed_of[:] = [e for e in robbed_of if game['turn'] - e[0] <= 3000]
        if before != robbed_of:
            log.debug("forgetting about stolen items, now missing %s",
                      robbed_of)
        if (blind(player) and have_intrinsic(player, 'telepathy')
                and not any(steals(m) for m in curlvl_monsters(game))):
            robbed_of[:] = [_amulet_escape(game, e) for e in robbed_of]
            robbed_of[:] = [e for e in robbed_of
                            if not (e[1] == game['dlvl']
                                    and branch_key(game, e[2])
                                    == branch_key(game))]

    def found_items(items):
        before = list(robbed_of)
        robbed_of[:] = [e for e in robbed_of if not _found_item(items, e)]
        if before != robbed_of:
            log.debug("found stolen items, now missing %s", robbed_of)

    def message(msg):
        label = re_first_group(r' (?:stole|snatches) ([^.!]*)[.!]', msg)
        if label:
            log.debug("robbed of %s", label)
            game = bh.game.deref()
            found = inventory_label(game, label)
            if found:
                robbed_of.append((game['turn'], game['dlvl'],
                                  game['branch-id'], found[1]))
            else:
                log.warning("stolen item %s not in inventory?", label)
    return Handler(choose_action=choose_action, about_to_choose=about_to_choose,
                   found_items=found_items, message=message)


def wish(game):
    player = game['player']
    if (typekw(game.get('last-action')) in ('engrave', 'zapwand')
            and not have(game, "scroll of charging", {'blessed', 'bagged'})
            and not have(game, "scroll of charging", {'wished', 'bagged'})
            and (inventory_slot(game, (game.get('last-action')
                                       or {}).get('slot')) or {}).get(
                                           'specific') != "recharged"):
        return "2 blessed scrolls of charging"
    if below_medusa(game) and not have(game, "ring of levitation", {'bagged'}):
        return "blessed ring of levitation"
    if below_medusa(game) and not any(g in game['genocided']
                                      for g in (";", "electric eel")):
        return "2 blessed scrolls of genocide"
    if (not _have_dsm(game)
            and not have(game, "cloak of magic resistance")):
        return "blessed greased +3 gray dragon scale mail"
    if not _have_dsm(game):
        return "blessed greased +3 silver dragon scale mail"
    if (_have_dsm(game)
            and not have(game, {"amulet of reflection",
                                "silver dragon scale mail",
                                "shield of reflection"})):
        return "blessed greased fixed +3 shield of reflection"
    if (not have(game, "scroll of remove curse", {'bagged', 'safe'})
            and (_have_dsm(game, {'can-use': False})
                 or (have(game, "ring of levitation", {'bagged'})
                     and not have_levi(game) and below_medusa(game)))):
        return "2 blessed scrolls of remove curse"
    if not all(g in game['genocided'] for g in ("L", ";")):
        return "2 blessed scrolls of genocide"
    if not have_candles(game) and below_medusa(game):
        return "7 blessed wax candles"
    if not have(game, "speed boots"):
        return "blessed greased fixed +3 speed boots"
    if not all(g in game['genocided']
               for g in ("mind flayer", "master mind flayer")):
        return "2 uncursed scrolls of genocide"
    if (not have(game, "helm of telepathy")
            and 'see-invis' not in player['intrinsics']):
        return "blessed greased fixed +3 helm of telepathy"
    if not have(game, "wand of death", {'bagged'}):
        return "blessed wand of death"
    if not any(g in game['genocided'] for g in ("R", "disenchanter")):
        return "2 blessed scrolls of genocide"
    if not have(game, {"silver dragon scale mail", "shield of reflection"}):
        return "blessed greased fixed +3 shield of reflection"
    if player['ac'] > -21 and not endgame(game):
        return "3 blessed scrolls of enchant armor"
    if (not have(game, "amulet of life saving", {'bagged'})
            and not have(game, "amulet of reflection", {'in-use'})):
        return "blessed amulet of life saving"
    n = game['wishes'] % (3 if (player['ac'] >= -25 and not endgame(game))
                          else 2)
    return {0: "blessed amulet of life saving", 1: "blessed wand of death",
            2: "3 blessed scrolls of enchant armor"}[n]


def want_buc(game, item):
    return bool(item.get('buc') is None
                and not (food_p(item) or gem_p(item) or statue_p(item)
                         or wand_p(item) or ammo_p(item) or dagger(item))
                and (know_id(game, item)
                     or (item_id(game, item) or {}).get('safe')))


def wow_spot(game):
    return [at_curlvl(game, x, y) for y in (6, 18) for x in (12, 66)]


def kickable_sink(tile):
    return bool(sink_p(tile) and not blocked(tile) and not tile.get('items')
                and tile.get('walked')
                and 'ring' not in (tile.get('tags') or ()))


def sinkid_ring(game):
    found = have(game, lambda i: not know_id(game, i) and ring_p(i),
                 {'can-remove'})
    if found:
        slot, ring = found
        p = navigate(game, sink_p)
        if p:
            return with_reason("drop ring in sink",
                               p['step'] or remove_use(game, slot)
                               or Drop(slot))
    return None


def use_features(game):
    player = game['player']
    if 'castle' in curlvl_tags(game) and not any(perma_e(t)
                                                 for t in wow_spot(game)):
        wow = find_first(lambda t: not t.get('walked'), wow_spot(game))
        if wow:
            p = navigate(game, wow, {'no-traps', 'no-levitation'})
            r = with_reason("getting WoW", p['step'] if p else None)
            if r:
                return r
    r = sinkid_ring(game)
    if r:
        return r
    if have(game, "Excalibur", {'can-use'}) and not farm_level(game):
        p = navigate(game, kickable_sink, {'adjacent'})
        if p:
            res = p['step']
            if res is None and monster_at(game, p['target']):
                res = fidget(game, curlvl(game), p['target'])
            if res is None:
                res = kick(game, p['target'])
            r = with_reason("kick sink", res)
            if r:
                return r
    if altar_p(at_player(game)):
        found = have(game, {'can-remove': True, 'bagged': True,
                            'know-buc': False})
        if found:
            slot, item = found
            r = with_reason("dropping things on altar",
                            unbag(game, slot, item) or remove_use(game, slot)
                            or Drop(slot, item['qty']))
            if r:
                return r
    if branch_key(game) != 'astral' and have(game,
                                             lambda i: want_buc(game, i),
                                             {'can-remove', 'bagged'}):
        p = navigate(game, altar_p)
        r = with_reason("going to altar", p['step'] if p else None)
        if r:
            return r
    if not ('castle' in curlvl_tags(game)) or player['ac'] < -3:
        p = navigate(game, lambda t: throne_p(t) and not t.get('items'),
                     {'explored'})
        if p:
            r = (with_reason("going to throne", p['step']) if p['step']
                 else with_reason("sitting on throne", Sit()))
            if r:
                return r
    db = find_first(drawbridge, tile_seq(curlvl(game)))
    if db:
        found = have(game, "wand of striking")
        if found:
            p = navigate(game, lambda t: (distance(db, t) == 3
                                          and in_line(db, t)))
            if p:
                r = with_reason("destroy drawbridge",
                                p['step'] or ZapWandAt(found[0],
                                                       towards(player, db)))
                if r:
                    return r
    return None


def _medusa_spot(level):
    if 'medusa-1' in level['tags']:
        return at(level, 38, 11)
    if 'medusa-2' in level['tags']:
        return at(level, 70, 11)
    return None


def _medusa_action(game, medusa_level):
    player = game['player']
    found = have(game, set(blind_tool), {'noncursed'})
    if not found:
        return None
    slot, _ = found
    spot = _medusa_spot(medusa_level)
    if game['dlvl'] == medusa_level['dlvl'] and spot:
        if 2 < distance(player, Pos(38, 11)) < 25:
            r = go_down(game, medusa_level)
            if r:
                return with_reason("killing medusa", r)
        p = navigate(game, spot, {'adjacent'})
        if p and p['step']:
            return with_reason("killing medusa", p['step'])
        if adjacent(player, spot):
            return with_reason("killing medusa", Search())
        return None
    if (stairs_up_p(at_player(game))
            and prev_dlvl(game['dlvl']) == medusa_level['dlvl']):
        if not visited_stairs(at_player(game)):
            r = make_use(game, slot)
            if r:
                return with_reason("killing medusa", r)
        return with_reason("killing medusa", Ascend())
    return None


def kill_medusa(bh):
    h = Handler()

    def choose_action(game):
        if reflection(game) or game['player'].get('polymorphed'):
            return None
        medusa_level = get_level(game, 'main', 'medusa')
        if not medusa_level:
            return None
        spot = _medusa_spot(medusa_level)
        if spot and (spot.get('searched') or 0) > 0:
            deregister_handler(bh, h)
            return None
        return _medusa_action(game, medusa_level)
    h.choose_action = choose_action
    return h


def safe_zap(game, dir_):
    from ..tile import corridor_p, floor_p, door_open_p
    level = curlvl(game)
    cur = game['player']
    for _ in range(7):
        cur = in_direction(level, cur, dir_)
        if cur is None:
            return False
        if not (corridor_p(cur) or floor_p(cur) or pool_p(cur)
                or door_open_p(cur)):
            return False
        if game['branch-id'] == 'sokoban' and boulder(cur):
            return False
        if monster_at(level, cur):
            return False
    return True


def itemid(game):
    from ..actions import Engrave as _Engrave
    if can_engrave(game):
        found = have(game, lambda i: ((item_id(game, i) or {}).get('engrave')
                                      is None and not tried(game, i)
                                      and wand_p(i)), {'nonempty'})
        if found:
            slot, w = found
            p = navigate(game, lambda t: engravable(t) and not perma_e(t))
            if p and p['step']:
                return with_reason("engrave-id wand", w, p['step'])
            # port fix: no engravable square reachable - do not engrave where
            # we stand if it is an altar/fountain/... (endless "You make a
            # motion towards the altar" loop, ca-w04 g010)
            if engravable(at_player(game)):
                if not at_player(game).get('engraving'):
                    r = engrave_e(game)
                    if r:
                        return with_reason("engrave-id wand", w, r)
                r = with_reason("engrave-id wand", w,
                                _Engrave(slot, "Elbereth", True))
                if r:
                    return r
    found = have(game, lambda i: ((item_id(game, i) or {}).get('target') is None
                                  and wand_p(i)), {'nonempty'})
    if found:
        slot, wand = found
        d = find_first(lambda x: safe_zap(game, x), DIRECTIONS)
        if d:
            return with_reason("zap-id wand", wand, ZapWandAt(slot, d))
    found = have(game, lambda i: should_try(game, i) and not wand_p(i),
                 {'safe-buc', 'bagged'})
    if found:
        slot, item = found
        return with_reason("trying out safe item",
                           unbag(game, slot, item) or make_use(game, slot))
    tile = at_player(game)
    if tile.get('room'):
        from ..level import shop_inside
        if shop_inside(curlvl(game), game['player']):
            found = have(game, lambda i: (price_id(game, i) and not i.get(
                'cost') and tile['room'] in shops_taking(i)), {'bagged'})
            if found:
                slot, item = found
                r = with_reason("price id (sell)",
                                unbag(game, slot, item)
                                or remove_use(game, slot) or Drop(slot))
                if r:
                    return r
    shoptypes = set()
    for _, i in have_all(game, lambda x: price_id(game, x), {'bagged'}):
        shoptypes |= shops_taking(i)
    shoptype = find_first(lambda t: t in curlvl_tags(game), sorted(shoptypes))
    if shoptype:
        from ..level import shop_inside
        p = navigate(game, lambda t: (t.get('room') == shoptype
                                      and shop_inside(curlvl(game), t)))
        r = with_reason("visit shop", shoptype, "to price id items",
                        p['step'] if p else None)
        if r:
            return r
    return None


def want_name(item):
    return ambiguous_appearance(item) and not gem_p(item) and not candle(item)


def shop_action(game):
    def want(i):
        return i.get('cost') and (want_buy(game, i) or want_name(i))
    it = find_first(want, at_player(game).get('items') or ())
    if it:
        r = with_reason("want to call item", PickUp(it['label']))
        if r:
            return r
    p = navigate(game, lambda t: any(want(i) for i in (t.get('items') or ())))
    return with_reason("visit shop for items", p['step'] if p else None)


def baggable(item):
    return scroll_p(item) or potion_p(item)


def bag_items(game):
    if typekw(game.get('last-action')) != 'apply':
        found = have(game, bag)
        if found:
            baggables = [s for s, _ in have_all(game, baggable)]
            if baggables:
                return with_reason("bag items",
                                   put_in(found[0],
                                          {b: None for b in baggables}))
    return None


def id_priority(game, item):
    know = know_id(game, item)
    price = (item_id(game, item) or {}).get('price')
    res = 0
    if food_p(item) or rocks(item) or gold(item) or candle(item):
        res -= 10
    if not know:
        res += 2
    if item.get('buc') is None:
        res += 1
    if ((not know or (item.get('buc') is None and wearable(item)))
            and any(n in _desired(game)
                    for n in (possible_names(game, item) or ()))):
        res += 4
    if item_name(game, item) in (BOOK, CANDELABRUM) and item.get('buc') is None:
        res += 5
    if not know and price not in (100, 200) and scroll_p(item):
        res += 10
    if (not know and not have(game, {"silver dragon scale mail",
                                     "shield of reflection"})
            and could_be(game, "amulet of reflection", item)):
        res += 10
    if not know and could_be(game, "scroll of remove curse", item):
        res += 10
    if not know and could_be(game, "scroll of genocide", item):
        res += 8
    if not know and could_be(game, "speed boots", item):
        res += 8
    if (not know and price == 200
            and (could_be(game, "ring of levitation", item)
                 or could_be(game, "ring of regeneration", item))):
        res += 8
    if not know and wand_p(item) and price != 150:
        res += 5
    if not know and (ring_p(item) or amulet_p(item)):
        res += 5
    return res


def want_id(game, bagged=False):
    inv = [kv for kv in inventory(game, bagged)
           if not (kv[1].get('buc') is not None
                   and kv[1].get('enchantment') is not None)]
    inv.sort(key=lambda kv: id_priority(game, kv[1]))
    return list(reversed(inv))


def recharge(game, slot, wand):
    if charged(wand) or (item_name(game, wand) == "wand of wishing"
                         and recharged(wand)):
        return None
    found = (have(game, "scroll of charging", {'blessed', 'bagged'})
             or have(game, "scroll of charging", {'wished', 'bagged'})
             or have(game, "scroll of charging", {'bagged'}))
    if found:
        s, item = found
        return with_reason("recharge",
                           unbag(game, s, item)
                           or with_handler(
                               Handler(charge_what=lambda _p: slot),
                               Read(s)))
    return None


def use_items(game):
    player = game['player']
    if shop(at_player(game)):
        return None
    bagged = 'bagged' if less_than(52, inventory(game)) else None

    def opts(*extra):
        o = {}
        for e in extra:
            if e:
                o[e] = True
        return o

    found = have(game, "Excalibur", {'can-use'})
    if found:
        excal, i = found
        if safe_enchant(i):
            f2 = have(game, "scroll of enchant weapon",
                      opts(bagged, 'noncursed'))
            if f2:
                scroll, item = f2
                return with_reason("enchant excal",
                                   unbag(game, scroll, item)
                                   or make_use(game, excal) or Read(scroll))
    o = {'safe-buc': True} if (farming(game)
                               or 'sanctum' in curlvl_tags(game)) else opts(
                                   bagged)
    found = have(game, {"potion of gain level"}, o)
    if found:
        slot, item = found
        return with_reason("helpful potion",
                           unbag(game, slot, item) or Quaff(slot))
    welded = game.get('welded-turn')
    if less_than(50, inventory(game)) and not (
            welded is not None and 0 <= (game.get('turn') or 0) - welded < 1000):
        found = have(game, "magic lamp", opts('noncursed', bagged))
        if found:
            slot, item = found
            return with_reason("rubbing lamp",
                               unbag(game, slot, item) or bless(game, slot)
                               or Rub(slot))
    found = have(game, "scroll of genocide", opts(bagged, 'safe-buc'))
    if found:
        slot, geno = found
        return with_reason("geno", unbag(game, slot, geno)
                           or bless(game, slot) or Read(slot))
    if less_than(50, inventory(game)):
        found = have(game, "wand of wishing", opts(bagged))
        if found:
            slot, wow = found
            return with_reason("wish", unbag(game, slot, wow)
                               or recharge(game, slot, wow) or ZapWand(slot))
    found = have(game, "wand of death", {'can-use': False})
    if found:
        return with_reason("recharge WoD", recharge(game, found[0], found[1]))
    found = have(game, "scroll of identify", opts(bagged))
    if found:
        slot, item = found
        want = want_id(game, bagged)
        if want:
            top = want[0]
            if ((not container(item) or less_than(50, inventory(game)))
                    and (id_priority(game, top[1]) > 6
                         or (id_priority(game, top[1]) > 0
                             and (more_than(45, inventory(game))
                                  or have_sum(game, "scroll of identify",
                                              {'bagged'}) > 5
                                  or burdened(player))))):
                res = unbag(game, slot, item)
                if res is None and less_than(51, inventory(game)):
                    res = keep_first(
                        lambda kv: (unbag(game, kv[0], kv[1])
                                    if id_priority(game, kv[1]) > 0 else None),
                        want)
                if res is None:
                    res = Read(slot)
                return with_reason("identify", top, res)
    found = have(game, {"potion of extra healing", "potion of full healing"},
                 opts(bagged))
    if found and player['hp'] == player['maxhp']:
        slot, item = found
        return with_reason("improve maxhp",
                           unbag(game, slot, item) or Quaff(slot))
    return None


def choose_identify(game, options):
    want = want_id(game)
    return find_first(lambda k: k in options, [kv[0] for kv in want])


def respond_geno(bh):
    geno_classes = [";", "L", "R", "c", "n", "m", "N", "q", "T", "U"]
    geno_types = ["master mind flayer", "mind flayer", "electric eel",
                  "disenchanter", "minotaur", "giant eel", "green slime",
                  "golden naga", "gremlin"]
    throne_geno = ["minotaur", "disenchanter", "green slime", "golden naga",
                   "gremlin"]

    def nxt(lst):
        return lst.pop(0) if lst else None

    def genocide_class(_p):
        return nxt(geno_classes)

    def genocide_monster(_p):
        if typekw(bh.game.deref().get('last-action*')) == 'sit':
            return nxt(throne_geno)
        return nxt(geno_types)
    return Handler(genocide_class=genocide_class,
                   genocide_monster=genocide_monster)


def random_unihorn(game):
    if game['rng'].randrange(200) == 0:
        found = have_unihorn(game)
        if found:
            return with_reason("randomly use unihorn", Apply(found[0]))
    return None


def get_protection(game):
    player = game['player']
    if (want_protection(game)
            and available_gold(game) > 400 * player['xplvl']
            and (not below_medusa(game) or in_gehennom(game))):
        p = find_first(lambda m: (priest(m) and m.get('peaceful')
                                  and adjacent(player, m)),
                       curlvl_monsters(game))
        if p:
            return with_reason("get protection",
                               Contribute(towards(player, p),
                                          400 * player['xplvl']))
        tags = curlvl(game)['tags']
        if 'temple' in tags or 'votd' in tags:
            pr = find_first(lambda m: priest(m) and m.get('peaceful'),
                            curlvl_monsters(game))
            if pr:
                path = navigate(game, pr)
                if path and path['step']:
                    return with_reason("get protection", path['step'])
            path = navigate(game, lambda t: altar_p(t) and temple(t))
            if path and path['step']:
                return with_reason("get protection", path['step'])
        target = find_first(lambda l: ('temple' in l['tags']
                                       and ('votd' not in l['tags']
                                            or in_gehennom(game))),
                            level_seq(game))
        if target:
            return with_reason("get protection",
                               seek_level(game, target['branch-id'],
                                          target['dlvl']))
    return None


def handle_drowning(game):
    player = game['player']
    if not (player.get('grabbed')
            and any(pool_p(t) for t in neighbors(curlvl(game), player))):
        return None
    level = curlvl(game)
    drowners = []
    for t in neighbors(level, player):
        if not pool_p(t):
            continue
        m = monster_at(level, t)
        if m is None or not typename(m) or drowner(m):
            drowners.append(t)
    drowner_t = drowners[0] if drowners else None
    if drowner_t and game['rng'].randrange(60) > 0:
        res = pray(game)
        if res is None:
            found = have_levi_on(game)
            if found and ring_p(found[1]) and walkable(at_player(game)):
                res = remove_use(game, found[0])
        if res is None:
            res = engrave_e(game, True)
        if res is None and more_than(2, drowners):
            found = (have(game, "wand of teleportation")
                     or have(game, "wand of cold"))
            if found:
                res = ZapWandAt(found[0], towards(player, drowner_t))
        if res is None:
            res = engrave_e(game)
        return with_reason("grabbed - avoid drowning", res) if res else None
    return None


def _maybe_boulder(level, tile):
    m = monster_at(level, tile)
    return boulder(tile) or (m is not None and m['glyph'] in ('H', 'X', 'E'))


def farm_spot_p(game, tile=None):
    if tile is None:
        return at_player(game).get('engraving') == "Elbereth*"
    level = curlvl(game)
    if at(level, tile).get('engraving') == "Elbereth*":
        return True
    return bool(more_than(6, [t for t in neighbors(level, tile)
                              if _maybe_boulder(level, t)]))


def farm_sink(game):
    r = find_first(sink_p, including_origin(neighbors, curlvl(game),
                                            game['player']))
    return r or find_first(sink_p, tile_seq(curlvl(game)))


def farm_spot(game):
    return find_first(lambda t: t.get('engraving') == "Elbereth*",
                      including_origin(neighbors, curlvl(game),
                                       game['player']))


def farm_spot_star(game):
    return find_first(lambda t: farm_spot_p(game, t),
                      including_origin(neighbors, curlvl(game),
                                       game['player']))


def farming(game):
    player = game['player']
    if player.get('x') is None:
        return False
    if farm_spot(game) is not None:
        return True
    level = curlvl(game)
    return bool(any(sink_p(t) for t in including_origin(neighbors, level,
                                                        player))
                and more_than(3, [t for t in neighbors(level, player)
                                  if _maybe_boulder(level, t)]))


def farm_done(game):
    """3.6.7: pudding farming yields nothing (see rules36); the score arms of
    the original predicate can never be met, only 'wiztower known' remains."""
    return rules36.farm_done36(game)


def init_farm(game):
    return bool(not farm_done(game) and game['player']['xplvl'] >= 7
                and soko_done(game)
                and know_appearance(game, "scroll of identify")
                and have_pick(game) and have_unihorn(game)
                and have(game, set(farm_tool))
                and have(game, {"wand of lightning", "wand of fire"})
                and nutrition_sum(game) > 2001
                and have(game, "scroll of earth", {'bagged', 'noncursed'}))


def farm_rect(game, sink):
    from ..position import rectangle
    return [p for p in rectangle(Pos(sink['x'] - 4, sink['y'] - 4),
                                 Pos(sink['x'] + 4, sink['y'] + 4))
            if 2 < p['y'] < 21]


def farm_clear(tile):
    return not (tile.get('walked') or tile.get('undiggable') or shop(tile)
                or trap(tile) or pool_p(tile))


def farm_level(game):
    from ..pathing import at_level
    return at_level(game, get_level(game, 'main', 'sink'))


def farm_init(game):
    from ..pathing import at_level
    sink_level = get_level(game, 'main', 'sink')
    if not sink_level:
        return None
    if not at_level(game, sink_level):
        return with_reason("initiating farm",
                           seek_level(game, 'main', sink_level['dlvl']))
    sink = farm_sink(game)
    if not sink:
        return None
    rect = set(position(p) for p in farm_rect(game, sink))
    if any(farm_clear(at_curlvl(game, p)) for p in rect):
        p = navigate(game, lambda t: (position(t) in rect and farm_clear(t)))
        if p:
            return with_reason("initiating farm",
                               with_reason("digging out sink surroundings",
                                           p['step']))
    r = seek(game, lambda t: (distance_manhattan(t, sink) == 1
                              and engravable(t)))
    if r:
        return with_reason("initiating farm", r)
    found = have(game, "scroll of earth", {'bagged'})
    if found:
        slot, item = found
        return with_reason("initiating farm",
                           unbag(game, slot, item) or Read(slot))
    return None


def _farm_spot_opposite(game):
    return in_direction(curlvl(game), farm_sink(game),
                        towards(farm_spot_star(game), farm_sink(game)))


def farm_init_move(game):
    player = game['player']
    if not perma_e(at_player(game)):
        sink = farm_sink(game)
        if more_than(7, [t for t in neighbors(curlvl(game), player)
                         if boulder(t)]):
            return Move(towards(player, sink))
        if ('pudding' not in (sink.get('tags') or ())
                and not monster_at(game, sink)):
            return kick(game, towards(player, sink))
    return None


def _reap_turn(game, splits):
    turn = game['turn']
    return bool(farm_done(game)
                or (splits > 110
                    and (turn % 1000) // 100 % (4 if splits > 160 else 8) == 0
                    and turn % 100 < 60))


def _heal_turn(game, splits, kills):
    turn = game['turn']
    score = game.get('score') or 0
    return bool(not farm_done(game) and splits > 25
                and (turn % 1000) // 100 % 3 == 0
                and ((score < 2000000 and kills < 130) or turn % 100 < 40))


def farm_wield(game, splits):
    player = game['player']
    if ((hungry(player) and not have(game, food_p) and not _can_pray(game))
            or _reap_turn(game, splits)):
        found = have(game, "Excalibur")
    else:
        found = have_key(game)
    if found and not found[1].get('wielded'):
        return Wield(found[0])
    return None


def farm_spot_move(game, state):
    player = game['player']
    kills, splits = state['kills'], state['splits']
    if not unihorn_recoverable(game):
        m = None
        for n in neighbors(player):
            mm = monster_at(game, n)
            if mm and not pudding(mm) and not mm.get('friendly'):
                m = mm
                break
        if m:
            return with_reason("killing non-pudding",
                               wield_weapon(game) or hit(game, curlvl(game), m))
    res = (handle_impairment(game) or farm_init_move(game) or use_items(game)
           or reequip(game) or examine_containers(game)
           or examine_containers_here(game) or consider_items_here(game)
           or bag_items(game))
    if res is not None:
        return res
    sink = farm_sink(game)
    walked = sink.get('walked') or 0
    if (((game['turn'] - walked > (200 if have(game, food_p) else 75)
          and (hungry(player) or sink['glyph'] == '?'))
         or game['turn'] - walked > 1500)
            and not monster_at(game, sink)):
        p = navigate(game, sink)
        if p and p['step']:
            return p['step']
    res = farm_wield(game, splits)
    if res is not None:
        return res
    if _heal_turn(game, splits, kills):
        return with_reason("letting puddings heal", search(8))
    if splits > 160:
        if not (hungry(player) and not have(game, food_p)):
            return FarmAttack(towards(player, sink), 8)
        return Attack(towards(player, sink))
    if splits < 2:
        return Attack(towards(player, sink))
    if game['rng'].randrange(5 if splits > 50 else 16) == 0:
        return Attack(towards(player, sink))
    if splits >= 2 and not e_p(at_player(game)):
        return engrave_e(game, True, True)
    return with_reason("letting puddings heal", Search())


def farm_sink_move(game):
    player = game['player']
    spot = farm_spot(game)
    if spot:
        m = monster_at(game, spot)
        if m:
            return wield_weapon(game) or hit(game, curlvl(game), m)
    opp = _farm_spot_opposite(game)
    if opp and boulder(opp):
        return seek(game, opp)
    if (player['hp'] / player['maxhp'] < 2 / 3
            or (fainting(player) and have(game, food_p))):
        p = navigate(game, lambda t: farm_spot_p(game, t))
        if p and p['step']:
            return p['step']
    r = consider_items_here(game)
    if r:
        return r
    if know_appearance(game, "ring of hunger") or nutrition_sum(game) > 3000:
        r = sinkid_ring(game)
        if r:
            return r
    p = navigate(game, lambda t: farm_spot_p(game, t))
    return p['step'] if p else None


def farm_action(game, state):
    if farm_spot_p(game, at_player(game)):
        return farm_spot_move(game, state)
    return farm_sink_move(game)


def end_farm(game):
    player = game['player']
    return bool(farm_done(game)
                and not any(pudding(m) and not m.get('remembered')
                            and distance(m, player) < 5
                            for m in curlvl_monsters(game)))


def botched_farm(game, state):
    return bool(state.get('last_seen') and not farm_done(game)
                and game['turn'] - state['last_seen'] > 500)


def farm(bh):
    state = {'splits': 0, 'kills': 0, 'last_seen': None}
    h = Handler()

    def choose_action(game):
        if not farming(game):
            return None
        if any(pudding(m) and not m.get('remembered')
               for m in curlvl_monsters(game)):
            state['last_seen'] = game['turn']
        if end_farm(game) or botched_farm(game, state):
            if botched_farm(game, state):
                log.warning("farm messed up - abandoning")
            else:
                log.warning("done farming")
            deregister_handler(bh, h)
            return enhance_all()
        return farm_action(game, state)

    def message(msg):
        if farming(bh.game.deref()):
            if re_first_group(r'You kill.*(brown|black) pudding', msg):
                state['kills'] += 1
            elif re_first_group(r'divides as you', msg):
                state['splits'] += 1
    h.really_attack = lambda _w: farming(bh.game.deref())
    h.force_god = lambda _p: False
    h.choose_action = choose_action
    h.message = message
    return h


_desired_cache = {'value': None}


def _desired(game):
    return _desired_cache['value'] or currently_desired(game)


def init(bh):
    _BH[0] = bh
    _desired_cache['value'] = None
    game = bh.game

    def pause_condition(_g):
        return False
    register_handler(bh, PRIORITY_BOTTOM, Handler(
        full_frame=lambda _f: None))

    h_char = Handler()

    def choose_character():
        deregister_handler(bh, h_char)
        return "nvd"          # a dwarven valkyrie
    h_char.choose_character = choose_character
    register_handler(bh, h_char)

    register_handler(bh, Handler(
        identify_what=lambda options: choose_identify(game.deref(), options),
        offer_how_much=lambda _p: _bribe_demon(
            game.deref().get('last-topline') or "")))

    register_handler(bh, Handler(
        who_are_you=lambda _p: ("Croesus" if have(
            game.deref(), {"pick-axe", "scroll of teleportation",
                           "wand of teleportation"}, {'can-use'}) else None)))
    register_handler(bh, respond_geno(bh))
    register_handler(bh, Handler(make_wish=lambda _p: wish(game.deref())))

    def about_to_choose(g):
        if (typekw(g.get('last-action*')) == 'inventory'
                or _desired_cache['value'] is None
                or (g.get('last-state')
                    and shop(at_player(g['last-state'])))
                or shop(at_player(g))):
            _desired_cache['value'] = currently_desired(g)
    register_handler(bh, Handler(about_to_choose=about_to_choose))

    def reg(priority, fn):
        register_handler(bh, priority, Handler(choose_action=fn))

    reg(-99, offer_amulet)
    reg(-16, enhance)
    reg(-20, assisted_astral_rush)
    # NB: no "bag the Amulet against theft": 3.6.7 pickup.c refuses the
    # Amulet, Bell, Candelabrum and Book in containers ("cannot be confined
    # in such trappings"); tried in big-w10, it only wasted turns
    register_handler(bh, -15, name_first_amulet(bh))
    reg(-13, handle_drowning)
    reg(-11, handle_starvation)
    register_handler(bh, -10, detect_portal(bh))
    reg(-9, handle_illness)
    if rules36.FARMING_ENABLED:
        register_handler(bh, -8, farm(bh))
    if not rules36.assisted_tactics():
        reg(-7, retreat)
    else:
        # invincible hero: put armor/amulet back on before fighting on (an
        # incubus undressed the hero in the Valley and the bot fought naked
        # for 6000 turns, scen/valley-to-vlad-01)
        from ..actions import LAST_BOT_REMOVAL

        def _redress(g):
            # not right after the bot removed something itself (enchant
            # armor took the shield off, re-dress put it back: big-w01 g022)
            if (g.get('turn') or 0) - LAST_BOT_REMOVAL[0] < 100:
                return None
            return with_reason("assisted: re-dress before fighting",
                               wear_amulet(g) or wear_armor(g))
        reg(-7, _redress)
    reg(-6, fight)
    reg(-5, cursed_levi)
    reg(-5, sokoban_no_levi)
    register_handler(bh, -4, kill_medusa(bh))
    reg(-3, handle_impairment)
    reg(-2, fight_covetous)
    reg(-1, reequip)
    reg(0, reequip_weapon)
    reg(1, feed)
    reg(2, consider_items_here)
    if not rules36.assisted_tactics():
        reg(3, lambda g: recover(g, True))
    reg(4, examine_containers)
    reg(5, examine_containers_here)
    reg(6, consider_items)
    reg(7, use_items)
    reg(8, random_unihorn)
    register_handler(bh, 9, hunt(bh))
    reg(10, itemid)
    reg(11, use_features)
    reg(12, shop_action)
    reg(13, bag_items)
    reg(15, get_protection)
    register_handler(bh, 16, excal_handler(bh))
    reg(17, rob_peacefuls)

    h_farm = Handler()

    def farm_about_to_choose(g):
        if farming(g):
            log.warning("farm initiated")
            deregister_handler(bh, h_farm)

    def farm_choose(g):
        if init_farm(g):
            return farm_init(g)
        return None
    h_farm.about_to_choose = farm_about_to_choose
    h_farm.choose_action = farm_choose
    if rules36.FARMING_ENABLED:
        register_handler(bh, 18, h_farm)
    reg(19, progress)
    register_handler(bh, 25, unstick_handler(bh))
    return bh
