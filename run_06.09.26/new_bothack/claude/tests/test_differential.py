"""Differential test: compare the Python port against the original Clojure
BotHack on identical inputs.

Usage:  python3 tests/test_differential.py [--oracle-out FILE]
The Clojure answers are produced by tools/cljcmp/oracle.clj (see
tools/run_oracle.sh) and cached in artifacts/oracle_answers.txt.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.canonical import jsn                                  # noqa: E402
from tests.differential_cases import (BOTLS, ITEM_LABELS,        # noqa: E402
                                      FOV_MAPS, MONSTER_DESCRIPTIONS,
                                      MONSTER_NAMES, ROOM_MESSAGES,
                                      COMBAT_CASES, EXCAL_CASES, FOOD_CASES,
                                      INVORDER_CASES, MAPORDER_CASES,
                                      MENU_CASES,
                                      INVENTORY_CASES,
                                      FARM_DONE_CASES,
                                      NAV_CASES, RANK_DESCRIPTIONS, STRENGTHS,
                                      TILE_CASES, TRAP_NAMES)
from pybothack import item as pyitem                             # noqa: E402
from pybothack import itemid as pyitemid                         # noqa: E402
from pybothack import montype as pymontype                       # noqa: E402
from pybothack import tile as pytile                             # noqa: E402
from pybothack import dungeon as pydungeon                       # noqa: E402
from pybothack import scraper as pyscraper                       # noqa: E402
from pybothack import util as pyutil                             # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def op_arg_split(arg, n):
    """Split on "|" into exactly n fields, padding with "" like Clojure's
    (string/split s #"\\|" n) which drops trailing empties."""
    parts = arg.split('|')
    return (parts + [""] * n)[:n]


def cases():
    out = []
    for lbl in ITEM_LABELS:
        out.append(("parse-label", lbl))
        out.append(("item-type", lbl))
        out.append(("appearance-of", lbl))
        out.append(("initial-ids", lbl))
        out.append(("item-id", lbl))
    for lbl in ITEM_LABELS:
        out.append(("item-preds", lbl))
    for d in MONSTER_DESCRIPTIONS:
        out.append(("by-description", d))
    for m in MONSTER_NAMES:
        out.append(("monster-preds", m))
    for d in RANK_DESCRIPTIONS:
        out.append(("monster-preds-desc", d))
    for c in FARM_DONE_CASES:
        out.append(("farm-done", c))
    for t in TILE_CASES:
        out.append(("infer-feature", t))
    for pos, rows in FOV_MAPS:
        out.append(("fov", pos + "|" + ";".join(rows)))
    for c in NAV_CASES:
        out.append(("nav", c))
    for c in INVENTORY_CASES:
        out.append(("inventory-logic", c))
    for c in COMBAT_CASES:
        out.append(("combat", c))
    for c in EXCAL_CASES:
        out.append(("excal", c))
    for c in MENU_CASES:
        out.append(("menuorder", c))
    for c in MAPORDER_CASES:
        out.append(("maporder", c))
    for c in INVORDER_CASES:
        out.append(("invorder", c))
    for c in FOOD_CASES:
        out.append(("food", c))
    for m in ROOM_MESSAGES:
        out.append(("room-type", m))
    for t in TRAP_NAMES:
        out.append(("trap-name", t))
    for s in STRENGTHS:
        out.append(("effective-str", s))
    for a in ("silver wand", "lamp", "lamp1", "gray stone", "food ration",
              "scroll labeled TEMOV", "boulder", "Amulet of Yendor"):
        out.append(("knowable", a))
    for b1, b2 in BOTLS:
        out.append(("parse-botls", b1 + "|" + b2))
    return out


_COLOURS = {'n': None, 'r': 'red', 'g': 'green', 'b': 'brown', 'B': 'blue',
            'm': 'magenta', 'c': 'cyan', 'G': 'gray', 'w': 'white',
            'y': 'yellow', 'o': 'orange', 'e': 'bright-green',
            'u': 'bright-blue', 'p': 'bright-magenta', 'C': 'bright-cyan',
            'd': 'bold'}


def _nav(arg):
    import random
    from pybothack.game import new_game
    from pybothack.level import new_level
    from pybothack.dungeon import add_level, map_tiles
    from pybothack.pathing import navigate, explorable_tile
    from pybothack.position import Pos
    from pybothack.tile import parse_tile, has_feature, door, walkable
    pos, optstr, goalspec, rows = arg.split("|", 3)
    px, py = [int(v) for v in pos.split(",")]
    grid = rows.split(";")
    glyphs = [[row[i] for i in range(0, 160, 2)] for row in grid]
    cols = [[_COLOURS[row[i]] for i in range(1, 160, 2)] for row in grid]
    level = new_level("Dlvl:1", 'main')
    level = dict(level, tiles=map_tiles(parse_tile, level['tiles'], glyphs,
                                        cols))
    game = new_game(random.Random(1))
    game = dict(game, dlvl="Dlvl:1", **{'branch-id': 'main'})
    game['turn'] = 100
    game['turn*'] = 100
    game['player'] = dict(game['player'], x=px, y=py, hp=20, maxhp=20, ac=6,
                          xplvl=1, intrinsics=frozenset(), inventory={},
                          stats={'str': 18, 'con': 18, 'cha': 8, 'dex': 10,
                                 'int': 10, 'wis': 10, 'str*': "18"})
    game = add_level(game, level)
    opts = {o: True for o in optstr.split(",") if o}
    lvl = level
    goals = {
        'explorable': lambda t: explorable_tile(lvl, t),
        'stairs-down': lambda t: has_feature(t, 'stairs-down'),
        'stairs-up': lambda t: has_feature(t, 'stairs-up'),
        'door': door,
        'items': lambda t: t.get('new-items'),
        'unwalked': lambda t: walkable(t) and not t.get('walked'),
    }
    if goalspec in goals:
        goal = goals[goalspec]
    else:
        gx, gy = [int(v) for v in goalspec.split(",")]
        goal = Pos(gx, gy)
    from pybothack.action import typekw as _tk
    p = navigate(game, goal, opts)
    if not p:
        return jsn({'found': False})
    step = p.get('step')
    return jsn({
        'found': True,
        'len': len(p['path']),
        'target': ([p['target']['x'], p['target']['y']]
                   if p.get('target') is not None else None),
        'step': _tk(step) if step else None,
        'dir': (step or {}).get('dir'),
        'first': ([p['path'][0]['x'], p['path'][0]['y']] if p['path']
                  else None),
    })


def _combat(arg):
    import random
    from pybothack.game import new_game
    from pybothack.level import new_level
    from pybothack.dungeon import add_level, map_tiles, reset_monster
    from pybothack.monster import new_monster
    from pybothack.action import typekw as _tk
    from pybothack.bots import mainbot as mb
    from pybothack import actions as pyactions
    from pybothack.tile import parse_tile
    pos, hpspec, mons, invspec, rows = arg.split("|", 4)
    px, py = [int(v) for v in pos.split(",")]
    hp, maxhp, ac = [int(v) for v in hpspec.split("/")]
    grid = rows.split(";")
    glyphs = [[row[i] for i in range(0, 160, 2)] for row in grid]
    cols = [[_COLOURS[row[i]] for i in range(1, 160, 2)] for row in grid]
    level = new_level("Dlvl:3", 'main')
    level = dict(level, tiles=map_tiles(parse_tile, level['tiles'], glyphs,
                                        cols))
    for spec in mons.split(";"):
        if not spec:
            continue
        x, y, nm = spec.split(",")
        t = pymontype.name_to_monster(nm)
        m = new_monster(int(x), int(y), 500, (t or {}).get('glyph'),
                        (t or {}).get('color'))
        m = dict(m, type=t, awake=True, **{'first-known': 495})
        level = reset_monster(level, m)
    game = new_game(random.Random(1))
    game = dict(game, dlvl="Dlvl:3", **{'branch-id': 'main'})
    game['turn'] = 500
    game['turn*'] = 500
    game['score'] = 1000
    game['wishes'] = 0
    game['player'] = dict(game['player'], x=px, y=py, hp=hp, maxhp=maxhp,
                          ac=ac, xplvl=5, protection=0, role='valkyrie',
                          race='dwarf', alignment='lawful',
                          intrinsics=frozenset({'cold', 'stealth'}),
                          state=frozenset(),
                          stats={'str': 18, 'con': 18, 'cha': 8, 'dex': 10,
                                 'int': 10, 'wis': 10, 'str*': "18"},
                          inventory={
                              e.split(":", 1)[0][0]:
                                  pyitem.label_to_item(e.split(":", 1)[1])
                              for e in invspec.split(";") if e})
    game = add_level(game, level)
    mb._desired_cache['value'] = None

    def _clean(r):
        return re.split(r'[\{#]', r, 1)[0].replace(':', '').strip()

    def act(a):
        if not a:
            return None
        out = {'type': _tk(a), 'dir': a.get('dir'),
               'reason': [_clean(r) for r in (a.get('reason') or ())]}
        if a.get('pos'):
            out['pos'] = [a['pos']['x'], a['pos']['y']]
        return out
    # hostile_threats now returns the monsters in Clojure set-seq order (it
    # models a PersistentHashSet, not a map); the oracle sorts them anyway
    threats = sorted([m['x'], m['y']] for m in mb.hostile_threats(game))
    return jsn({
        'threats': threats,
        'monster-order': [[m['x'], m['y']]
                          for m in pydungeon.curlvl_monsters(game)],
        'fight': act(mb.fight(game)),
        'retreat': act(mb.retreat(game)),
        'feed': act(mb.feed(game)),
        'progress': act(mb.progress(game)),
        'low-hp': bool(mb.low_hp(game['player'])),
        'exposed': bool(mb.exposed(game, level, game['player'])),
        'reequip': act(mb.reequip(game)),
        'reequip-weapon': act(mb.reequip_weapon(game)),
        'use-items': act(mb.use_items(game)),
        'itemid': act(mb.itemid(game)),
        'use-features': act(mb.use_features(game)),
        'consider-items': act(mb.consider_items(game)),
        'consider-items-here': act(mb.consider_items_here(game)),
        'examine-containers': act(mb.examine_containers(game)),
        'examine-containers-here': act(mb.examine_containers_here(game)),
        'handle-illness': act(mb.handle_illness(game)),
        'handle-starvation': act(mb.handle_starvation(game)),
        'handle-impairment': act(mb.handle_impairment(game)),
        'recover': act(mb.recover(game, True)),
        'rob-peacefuls': act(mb.rob_peacefuls(game)),
        'get-protection': act(mb.get_protection(game)),
        'bag-items': act(mb.bag_items(game)),
        'shop': act(mb.shop_action(game)),
        'fight-covetous': act(mb.fight_covetous(game)),
        'cursed-levi': act(mb.cursed_levi(game)),
        'drop-junk': act(mb.drop_junk(game)),
        'wear-armor': act(mb.wear_armor(game)),
        'wield-weapon': act(mb.wield_weapon(game)),
        'bless-gear': act(mb.bless_gear(game)),
        'use-light': act(mb.use_light(game, level)),
        'remove-rings': act(mb.remove_rings(game)),
        'enchant-gear': act(mb.enchant_gear(game)),
        'make-excal': act(mb.make_excal(game)),
        'handle-drowning': act(mb.handle_drowning(game)),
        'offer-amulet': act(mb.offer_amulet(game)),
        'wander': act(mb.wander(game)),
        'examine-tile': act(pyactions.examine_tile(game)),
        'examine-monsters': act(pyactions.examine_monsters(game)),
        'examine-features': act(pyactions.examine_features(game)),
    })


def _excal(arg):
    """make-excal / seek-fountain with a known Oracle level (the branch of
    seek-fountain that the combat scenarios cannot reach)."""
    import random
    from pybothack.game import new_game
    from pybothack.level import new_level, ORACLE_POSITION
    from pybothack.dungeon import add_level, map_tiles
    from pybothack.position import neighbors as pos_neighbors
    from pybothack.action import typekw as _tk
    from pybothack.bots import mainbot as mb
    from pybothack.clj import assoc_in
    from pybothack.tile import parse_tile
    pos, acs, invspec, omode, rows = arg.split("|", 4)
    px, py = [int(v) for v in pos.split(",")]
    ac = int(acs)
    grid = rows.split(";")
    glyphs = [[row[i] for i in range(0, 160, 2)] for row in grid]
    cols = [[_COLOURS[row[i]] for i in range(1, 160, 2)] for row in grid]
    level = new_level("Dlvl:5", 'main')
    level = dict(level, tiles=map_tiles(parse_tile, level['tiles'], glyphs,
                                        cols))
    oracle = None
    if omode != "none":
        oracle = dict(new_level("Dlvl:3", 'main'), tags=frozenset({'oracle'}))
        for p in pos_neighbors(ORACLE_POSITION):
            oracle = assoc_in(oracle, ['tiles', p['y'] - 1, p['x'], 'seen'],
                              True)
        if omode == "seen-fountain":
            oracle = assoc_in(oracle, ['tiles', ORACLE_POSITION['y'] - 1,
                                       ORACLE_POSITION['x'] + 1, 'feature'],
                              'fountain')
    game = new_game(random.Random(1))
    game = dict(game, dlvl="Dlvl:5", **{'branch-id': 'main'})
    game['turn'] = 500
    game['turn*'] = 500
    game['score'] = 1000
    game['wishes'] = 0
    game['player'] = dict(game['player'], x=px, y=py, hp=40, maxhp=40,
                          ac=ac, xplvl=5, protection=0, role='valkyrie',
                          race='dwarf', alignment='lawful',
                          intrinsics=frozenset({'cold', 'stealth'}),
                          state=frozenset(),
                          stats={'str': 18, 'con': 18, 'cha': 8, 'dex': 10,
                                 'int': 10, 'wis': 10, 'str*': "18"},
                          inventory={
                              e.split(":", 1)[0][0]:
                                  pyitem.label_to_item(e.split(":", 1)[1])
                              for e in invspec.split(";") if e})
    game = add_level(game, level)
    if oracle is not None:
        game = add_level(game, oracle)
    if omode == "seen-prev-fountain":
        # a fountain on a level *above* the Oracle: seek-fountain's last
        # resort, which must not be reached while we stand on a fountain
        prev = new_level("Dlvl:2", 'main')
        prev = assoc_in(prev, ['tiles', 5, 20, 'feature'], 'fountain')
        game = add_level(game, prev)
    mb._desired_cache['value'] = None

    def _clean(r):
        return re.split(r'[\{#]', r, 1)[0].replace(':', '').strip()

    def act(a):
        if not a:
            return None
        out = {'type': _tk(a), 'dir': a.get('dir'),
               'reason': [_clean(r) for r in (a.get('reason') or ())]}
        if a.get('pos'):
            out['pos'] = [a['pos']['x'], a['pos']['y']]
        return out
    return jsn({
        'make-excal': act(mb.make_excal(game)),
        'seek-fountain': act(mb._seek_fountain(game)),
    })


def _inventory_logic(arg):
    import random
    from pybothack.game import new_game
    from pybothack.level import new_level
    from pybothack.dungeon import add_level
    from pybothack.action import typekw as _tk
    from pybothack.bots import mainbot as mb
    from pybothack.player import nutrition_sum, weight_sum
    invspec, cands = arg.split("||", 1)
    inv = {}
    for e in invspec.split(";"):
        if not e:
            continue
        sl, lbl = e.split(":", 1)
        inv[sl[0]] = pyitem.label_to_item(lbl)
    game = new_game(random.Random(1))
    game = dict(game, dlvl="Dlvl:1", **{'branch-id': 'main'})
    game['turn'] = 100
    game['turn*'] = 100
    game['score'] = 1234
    game['wishes'] = 0
    game['player'] = dict(game['player'], x=40, y=10, hp=20, maxhp=20, ac=6,
                          xplvl=3, protection=0, role='valkyrie', race='dwarf',
                          alignment='lawful',
                          intrinsics=frozenset({'cold', 'stealth'}),
                          stats={'str': 18, 'con': 18, 'cha': 8, 'dex': 10,
                                 'int': 10, 'wis': 10, 'str*': "18"},
                          inventory=inv)
    game = add_level(game, new_level("Dlvl:1", 'main'))
    mb._desired_cache['value'] = None
    take = mb.take_selector(game)
    dj = mb.drop_junk(game)
    return jsn({
        'desired': sorted(mb.currently_desired(game)),
        'drop-junk': _tk(dj) if dj else None,
        'nutrition': nutrition_sum(game),
        'weight': weight_sum(game),
        'candidates': [
            {'label': c,
             'worthwhile': bool(mb.worthwhile(game, pyitem.label_to_item(c))),
             'should-try': bool(mb.should_try(game,
                                              pyitem.label_to_item(c))),
             'take': bool(take(pyitem.label_to_item(c))),
             'utility': mb.utility(game, pyitem.label_to_item(c))}
            for c in cands.split(";") if c],
    })


def _drop_kind(d):
    if isinstance(d, dict):
        return {k: v for k, v in d.items() if k != 'kind'}
    return d


def python_answer(op, arg):
    if op == "parse-label":
        return jsn(pyitem.parse_label(arg))
    if op == "item-type":
        return jsn(pyitemid.item_type(pyitem.label_to_item(arg)))
    if op == "appearance-of":
        return jsn(pyitemid.appearance_of(pyitem.label_to_item(arg)))
    if op == "initial-ids":
        ids = pyitemid.initial_ids(pyitem.label_to_item(arg))
        return jsn([i['name'] for i in (ids or ())])
    if op == "item-id":
        return jsn(_drop_kind(pyitemid.item_id(pyitem.label_to_item(arg))))
    if op == "item-preds":
        i = pyitem.label_to_item(arg)
        from pybothack.bots import mainbot as pymainbot
        return jsn({
            "charged": bool(pyitem.charged(i)),
            "recharged": bool(pyitem.recharged(i)),
            "safe-enchant": bool(pyitem.safe_enchant(i)),
            "two-handed": bool(pyitem.two_handed(i)),
            "artifact": bool(pyitem.artifact(i)),
            "price-id": bool(pyitem.price_id(i)),
            "container": bool(pyitem.container(i)),
            "know-contents": bool(pyitem.know_contents(i)),
            "boh": bool(pyitem.boh(i)),
            "tin": bool(pyitem.tin(i)),
            "corpse": bool(pyitem.corpse(i)),
            "can-take": bool(pyitem.can_take(i)),
            "candle": bool(pyitem.candle(i)),
            "dagger": bool(pyitem.dagger(i)),
            "ammo": bool(pyitem.ammo_p(i)),
            "dart": bool(pyitem.dart(i)),
            "rocks": bool(pyitem.rocks(i)),
            "egg": bool(pyitem.egg(i)),
            "gold": bool(pyitem.gold(i)),
            "key": bool(pyitem.key_p(i)),
            "shield": bool(pyitem.shield(i)),
            "gloves": bool(pyitem.gloves(i)),
            "boots": bool(pyitem.boots(i)),
            "wished": bool(pyitem.wished(i)),
            "explorable-container": bool(pyitem.explorable_container(i)),
            "single": bool(pyitem.single(i)),
            "safe-buc": bool(pyitem.safe_buc(i)),
            "noncursed": bool(pyitem.noncursed(i)),
            "subtype": pyitemid.item_subtype(i),
            "weight": pyitemid.item_weight(i),
            "nw-ratio": float(pyitem.nw_ratio(i)),
            "enchantment": pyitem.enchantment(i),
            "utility": pymainbot.utility(i),
        })
    if op == "farm-done":
        from pybothack.game import new_game
        from pybothack.clj import assoc, assoc_in
        from pybothack.bots.mainbot import farm_done
        from pybothack.level import new_level
        from pybothack.item import label_to_item
        sc, tn, wi, ac, geno, brs, invspec = (op_arg_split(arg, 7))
        inv = {}
        for e in [x for x in invspec.split(';') if x]:
            sl, lbl = e.split(':', 1)
            inv[sl[0]] = label_to_item(lbl)
        brset = set(x for x in brs.split(',') if x)
        game = new_game()
        game = assoc(game, 'dlvl', "Dlvl:5", 'branch-id', 'main',
                     'turn', int(tn), 'turn*', int(tn), 'score', int(sc),
                     'wishes', int(wi),
                     'genocided', frozenset(x for x in geno.split(',') if x))
        game = assoc_in(game, ['player', 'ac'], int(ac))
        game = assoc_in(game, ['player', 'inventory'], inv)
        if 'castle' in brset:
            lv = assoc(new_level("Dlvl:30", 'main'), 'tags', frozenset({'castle'}))
            game = assoc_in(game, ['dungeon', 'levels', 'main', "Dlvl:30"], lv)
        if 'wiztower' in brset:
            game = assoc_in(game, ['dungeon', 'levels', 'wiztower', "Dlvl:35"],
                            new_level("Dlvl:35", 'wiztower'))
        return jsn({"farm-done": bool(farm_done(game))})
    if op == "monster-preds-desc":
        # `by_description` returns a plain str for a player rank, and FarLook
        # stores it as the monster's :type.  Clojure's keyword lookup is
        # nil-safe on that; Python indexing is not.
        from pybothack import monster as pymonster
        t = pymontype.by_description(arg)
        tm = t if isinstance(t, dict) else {}
        m = {'type': t, 'glyph': tm.get('glyph'), 'color': tm.get('color')}
        return jsn({
            "type-is-string": isinstance(t, str),
            # (str nil) is "" in Clojure, not "None"
            "typename": pymonster.typename(m) or "",
            "passive": bool(pymonster.passive(m)),
            "corrosive": bool(pymonster.corrosive(m)),
            "flies": bool(pymonster.flies(m)),
            "slow": bool(pymonster.slow(m)),
            "mindless": bool(pymonster.mindless(m)),
            "demon-lord": bool(pymonster.demon_lord(m)),
            "drowner": bool(pymonster.drowner(m)),
            "werecreature": bool(pymonster.werecreature(m)),
            "sees-invisible": bool(pymonster.sees_invisible(m)),
            "follower": bool(pymonster.follower(m)),
            "amphibious": bool(pymonster.amphibious(m)),
            "unique": bool(pymonster.unique(m)),
            "ignores-e": bool(pymonster.ignores_e(m)),
            "shopkeeper": bool(pymonster.shopkeeper(m)),
        })
    if op == "monster-preds":
        from pybothack import monster as pymonster
        t = pymontype.name_to_monster(arg)
        m = {'type': t, 'glyph': (t or {}).get('glyph'),
             'color': (t or {}).get('color')}
        return jsn({
            "passive": bool(pymonster.passive(m)),
            "corrosive": bool(pymonster.corrosive(m)),
            "covetous": bool(pymonster.covetous(m)),
            "steals": bool(pymonster.steals(m)),
            "ignores-e": bool(pymonster.ignores_e(m)),
            "flies": bool(pymonster.flies(m)),
            "drowner": bool(pymonster.drowner(m)),
            "slow": bool(pymonster.slow(m)),
            "unique": bool(pymonster.unique(m)),
            "werecreature": bool(pymonster.werecreature(m)),
            "sees-invisible": bool(pymonster.sees_invisible(m)),
            "follower": bool(pymonster.follower(m)),
            "amphibious": bool(pymonster.amphibious(m)),
            "nasty": bool(pymonster.nasty(m)),
            "rider": bool(pymonster.rider(m)),
            "mindless": bool(pymonster.mindless(m)),
            "sessile": bool(pymonster.sessile(m)),
            "strong": bool(pymonster.strong(m)),
            "human": bool(pymonster.human(m)),
            "guard": bool(pymonster.guard(m)),
            "undead": bool(pymonster.undead(m)),
            "infravisible": bool(pymonster.infravisible(m)),
            "priest": bool(pymonster.priest(m)),
            "mimic": bool(pymonster.mimic(m)),
            "unicorn": bool(pymonster.unicorn(m)),
            "pudding": bool(pymonster.pudding(m)),
            "shopkeeper": bool(pymonster.shopkeeper(m)),
            "demon-lord": bool(pymonster.demon_lord(m)),
            "hostile": bool(pymonster.hostile(m)),
        })
    if op == "infer-feature":
        cur, g, c = arg.split(",", 2)
        t = pytile.initial_tile(5, 5)
        t = dict(t, feature=(None if cur == "nil" else cur))
        nt = pytile.parse_tile(t, g, None if c == "nil" else c)
        return jsn({
            'feature': nt.get('feature'), 'glyph': str(nt['glyph']),
            'color': nt.get('color'), 'new-items': bool(nt.get('new-items')),
            'item-glyph': ("" if nt.get('item-glyph') is None
                           else str(nt.get('item-glyph'))),
            'walkable': bool(pytile.walkable(nt)),
            'transparent': bool(pytile.transparent(nt)),
            'monster': bool(pytile.monster(nt)),
            'item': bool(pytile.item(nt)),
            'boulder': bool(pytile.boulder(nt)),
            'door': bool(pytile.door(nt)),
            'trap': bool(pytile.trap(nt)),
            'diggable': bool(pytile.diggable(nt)),
            'seen': bool(nt.get('seen')), 'dug': bool(nt.get('dug')),
        })
    if op == "fov":
        from pybothack.fov import NHFov
        pos, rows = arg.split("|", 1)
        px, py = [int(v) for v in pos.split(",")]
        grid = rows.split(";")

        def transparent(x, y):
            if 0 < y < 20 and 0 < x < 79:
                row = grid[y] if y < len(grid) else ""
                return (row[x] if x < len(row) else '#') == '.'
            return False
        fov = NHFov(transparent).calculate_fov(px, py)
        return jsn(["".join('1' if v else '0' for v in row) for row in fov])
    if op == "nav":
        return _nav(arg)
    if op == "inventory-logic":
        return _inventory_logic(arg)
    if op == "combat":
        return _combat(arg)
    if op == "excal":
        return _excal(arg)
    if op == "invorder":
        import random as _r
        from pybothack.clj import into_map
        from pybothack.game import new_game
        from pybothack.item import slot_item
        from pybothack.player import inventory as _inv
        from pybothack.bots import mainbot as mb
        inv = into_map([slot_item(e.split(":", 1)[0][0], e.split(":", 1)[1])
                        for e in arg.split(";") if e])
        game = new_game(_r.Random(1))
        game = dict(game, dlvl="Dlvl:3", **{'branch-id': 'main'})
        game['turn'] = 500
        game['player'] = dict(game['player'], hp=40, maxhp=40, xplvl=5,
                              role='valkyrie', race='dwarf',
                              alignment='lawful', intrinsics=frozenset(),
                              state=frozenset(),
                              stats={'str': 18, 'con': 18, 'cha': 8,
                                     'dex': 10, 'int': 10, 'wis': 10,
                                     'str*': "18"},
                              inventory=inv)
        cf = mb._choose_food(game)
        return jsn({'order': [k for k, _ in _inv(game)],
                    'choose-food': cf[0] if cf else None})
    if op == "maporder":
        from pybothack.clj import clj_keys, into_map, CljMap
        from pybothack.position import Pos
        how, spec = arg.split("|", 1)
        chars = how.endswith("-char")
        how = how[:-5] if chars else how

        def mk(k):
            if chars:
                return k[0]
            if ":" in k:
                x, y = k.split(":")
                return Pos(int(x), int(y))
            return k
        ks = [mk(k) for k in spec.split(",") if k]
        if how == "into":
            m = into_map([(k, 1) for k in ks])
        else:
            m = CljMap()
            for k in ks:
                m._assoc_(k, 1)
        return jsn([[k.x, k.y] if isinstance(k, Pos) else k
                    for k in clj_keys(m)])
    if op == "menuorder":
        from pybothack.delegator import _respond_menu
        items = ([x for x in arg.split(",") if x] if "," in arg
                 else list(arg))
        return jsn(_respond_menu(set(items)))
    if op == "food":
        from pybothack.player import edible, want_to_eat, safe_corpse_type
        from pybothack.itemtype import name_to_item
        race, intr, strength, labels = arg.split("|", 3)
        player = {'race': race,
                  'intrinsics': frozenset(x for x in intr.split(",") if x),
                  'stats': {'str*': strength}}
        res = []
        for l in labels.split(";"):
            if not l:
                continue
            i = pyitem.label_to_item(l)
            try:
                want = bool(want_to_eat(player, i))
            except Exception:                            # noqa: BLE001
                want = "ERR"
            t = name_to_item.get(i['name'])
            safe = bool(safe_corpse_type(player, i, t)) if (
                t and t.get('monster')) else False
            res.append({'label': l, 'edible': bool(edible(player, i)),
                        'want': want, 'safe-type': safe})
        return jsn(res)
    if op == "by-description":
        try:
            m = pymontype.by_description(arg)
        except ValueError as e:
            return "ERR " + str(e)
        # (:name x) is nil for non-maps - rank->monster returns a role string
        return jsn(m.get('name') if isinstance(m, dict) else None)
    if op == "room-type":
        return jsn(pydungeon.room_type(arg))
    if op == "trap-name":
        return jsn(pytile.TRAP_NAMES.get(arg))
    if op == "effective-str":
        return jsn(pyutil.effective_str(arg))
    if op == "knowable":
        return jsn(pyitemid.knowable_appearance(arg))
    if op == "parse-botls":
        a, b = arg.split("|", 1)
        return jsn(pyscraper.parse_botls([a, b]))
    raise ValueError(op)


def main():
    answers_path = os.path.join(ROOT, 'artifacts', 'oracle_answers.txt')
    cs = cases()
    if not os.path.exists(answers_path):
        sys.exit("no oracle answers at %s - run tools/run_oracle.sh first"
                 % answers_path)
    with open(answers_path) as f:
        answers = f.read().splitlines()
    if len(answers) != len(cs):
        sys.exit("oracle answered %d of %d cases - regenerate"
                 % (len(answers), len(cs)))
    bad = 0
    for (op, arg), expected in zip(cs, answers):
        try:
            got = python_answer(op, arg)
        except Exception as e:                        # noqa: BLE001
            got = "PYERR " + repr(e)
        if got.startswith("ERR") and expected.startswith("ERR"):
            # both raised - compare only the message, not the class/stack
            def _msg(x):
                x = x.split(" @ ")[0]
                for pre in ("ERR class java.lang.IllegalArgumentException ",
                            "ERR class java.lang.RuntimeException ",
                            "ERR class java.lang.NullPointerException ",
                            "ERR class java.lang.UnsupportedOperationException ",
                            "ERR "):
                    if x.startswith(pre):
                        return x[len(pre):]
                return x
            if _msg(got) == _msg(expected):
                continue
        if got != expected:
            bad += 1
            print("MISMATCH %-16s %s" % (op, arg))
            print("   clojure: %s" % expected)
            print("   python : %s" % got)
    print("%d/%d cases identical to the original (%d mismatches)"
          % (len(cs) - bad, len(cs), bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
