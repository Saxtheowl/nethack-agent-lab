"""Port of bothack.actions."""
import logging
import re

from .action import action, handler as action_handler, trigger, typekw
from .clj import (assoc, assoc_in, CljMap, CljStr, clj_items, conj_set,
                  conj_vec,
                  dissoc, get_in, kw, merge, update, update_in)
from .delegator import Handler
from .dungeon import (add_curlvl_tag, at_curlvl, at_player, branch_key,
                      curlvl, curlvl_monsters, curlvl_tags, dlvl,
                      initial_branch_id, monster_at, remove_monster,
                      update_around, update_around_player, update_at,
                      update_at_player, update_curlvl, update_from_player,
                      update_item_at_player, update_monster, SUBBRANCHES,
                      branch_entry, dlvl_number, passable_walking)
from .handlers import (deregister_handler, register_handler,
                       update_at_player_when_known, update_before_action,
                       update_on_known_position)
from .item import (candle, container, dagger, label_to_item, pick, shield,
                   slot_item, two_handed, weapon_p, item_name as _iname)
from .itemid import (add_discovery, add_observed_cost, add_prop_discovery,
                     appearance_of, item_id, item_name, item_subtype,
                     item_type, know_id, names)
from .item import price_id
from .level import tile_seq
from .monster import follower
from .montype import by_description
from .player import (blind, can_remove, cursed_blockers, dizzy, has_hands,
                     hallu, impaired, inventory, inventory_slot,
                     slot_appearance, stressed, update_slot, wielded_item,
                     wielding, have, have_all)
from .position import (Pos, DIRMAP, adjacent, at, diagonal, diagonal_neighbors,
                       in_direction, including_origin, neighbors, position,
                       straight_neighbors, to_position, towards)
from .tile import (altar_p, blank, boulder, corridor_p, door, door_open_p,
                   e_p, floor_p, fountain_p, item as tile_item, lava_p,
                   monster_glyph,
                   monster as tile_monster, perma_e, pool_p, reset_item,
                   rock_p, shop, sink_p, stairs, stairs_down_p, stairs_up_p,
                   trap, TRAP_NAMES, TRAPS, unknown, unknown_trap, walkable,
                   wall_p, mark_death)
from .util import (ESC, PRIORITY_BOTTOM, PRIORITY_DEFAULT, PRIORITY_TOP, ctrl,
                   find_first, indexed, more_than, parse_int, re_any_group,
                   re_first_group, re_first_groups, re_seq, str_kw,
                   VI_DIRECTIONS, not_any_fn, some_fn, every_pred, min_by)

log = logging.getLogger('bothack.actions')

FEATURE_RE = (r"^(?:You see|There is|You escape)(?: an?| your)?(?: \w+)* "
              r"(falling rock trap|rolling boulder trap|rust trap|statue trap|"
              r"magic trap|anti-magic field|polymorph trap|fire trap|"
              r"arrow trap|dart trap|land mine|teleportation trap|"
              r"sleeping gas trap|magic portal|level teleporter|bear trap|"
              r"spiked pit|pit|ladder (?:up|down)|staircase (?:up|down)|"
              r"spider web|web|ice|opulent throne|pool of water|"
              r"lowered drawbridge|hole|trap door|fountain|sink|grave|"
              r"molten lava|doorway|squeaky board|open door|broken door)"
              r"(?: here| below you)?\.")

TRAP_DISARM_RE = (r"You tear through \w+ web!|You (?:burn|dissolve) \w+ spider"
                  r" web!|You hear a (?:loud|soft) click(?:!|\.)")


def feature_msg_update(tile, msg, rogue):
    align = re_first_group(
        # 3.6 invent.c dfeature_at: "a high altar" on the Astral Plane and
        # in the Sanctum; "(unaligned)" for Moloch
        r'There is an? (?:high )?altar to [^(]* \(([^)]*)\) here.', msg)
    if align:
        return assoc(tile, 'feature', 'altar', 'alignment', str_kw(align))
    if re_seq(TRAP_DISARM_RE, msg):
        return assoc(tile, 'feature', 'floor')
    txt = re_first_group(FEATURE_RE, msg)
    if txt:
        f = {"opulent throne": 'throne', "ice": 'ice',
             "doorway": ('door-open' if rogue else 'floor'),
             "open door": 'door-open', "broken door": 'floor',
             "ladder up": 'stairs-up', "ladder down": 'stairs-down',
             "staircase up": 'stairs-up', "staircase down": 'stairs-down',
             "lowered drawbridge": 'drawbridge-lowered',
             "fountain": 'fountain', "sink": 'sink', "grave": 'grave',
             "molten lava": 'lava', "pool of water": 'pool',
             }.get(txt, TRAP_NAMES.get(txt))
        return assoc(tile, 'feature', f)
    return None


def with_reason(*reason_and_action):
    """Attach reasoning to an action (debugging only)."""
    a = reason_and_action[-1]
    reason = " ".join(r if isinstance(r, str) else repr(r)
                      for r in reason_and_action[:-1])
    if callable(a):
        a = a()
    if a is None:
        return None
    return assoc(a, 'reason', conj_vec(a.get('reason'), reason))


# 3.6.7 hack.c domove(): "You harmlessly attack a boulder.", "You futilely
# explode at the wall.", "You attack nothing." (ca-w04 g004 hit a boulder
# forever)
NO_MONSTER_RE = (r"You .*(?:thin air|empty water|empty space)"
                 r"|^You (?:harmlessly |futilely )(?:attack|explode at) "
                 r"|^You (?:attack|explode at) (?:nothing|an air bubble)\.")


def recheck_peaceful_status(game, monster_selector):
    for m in curlvl_monsters(game):
        if not monster_selector(m):
            continue
        if m['glyph'] in ('I', '1', '2', '3', '4', '5'):
            continue
        if m.get('peaceful') is not True:
            continue
        game = update_monster(game, m, lambda mm: assoc(mm, 'peaceful',
                                                        'update'))
    return game


def direction_trigger(d):
    v = VI_DIRECTIONS.get(d)
    if v is None:
        raise ValueError("Invalid direction: %s" % (d,))
    return str(v)


# ------------------------------------------------------------------ actions
def Attack(dir_):
    def hnd(a, bh):
        game = bh.game
        if dizzy(game.deref()['player']):
            game.swap(recheck_peaceful_status,
                      lambda m: adjacent(game.deref()['player'], m))
        target = (None if dizzy(game.deref()['player'])
                  else in_direction(game.deref()['player'], dir_))
        if target is None:
            return None
        game.swap(recheck_peaceful_status,
                  lambda m: position(target) == position(m))
        game.swap(update_monster, target, lambda m: assoc(m, 'awake', True))

        def message(msg):
            if re_seq(NO_MONSTER_RE, msg):
                game.swap(update_at, target,
                          lambda t: (assoc(t, 'feature', 'rock') if blank(t)
                                     else assoc(t, 'pushed', True)))
                game.swap(remove_monster, target)
        return Handler(message=message)
    return action('attack', lambda a: 'F' + direction_trigger(dir_), hnd,
                  dir=dir_)


def FarmAttack(dir_, cnt):
    def trig(a):
        return ((ESC + ESC + 'F' + direction_trigger(dir_)) * cnt
                + ESC * 30 + "##'")
    return action('farmattack', trig, lambda a, bh: None, dir=dir_, cnt=cnt)


def mark_trap_here(bh):
    return update_at_player_when_known(
        bh, lambda t: update(t, 'feature',
                             lambda f: f if f in TRAPS else 'trap'))


def move_message_handler(bh, msg):
    game = bh.game
    if re_seq(r'.*: "Closed for inventory"', msg):
        def mark_shop(g):
            level = curlvl(g)
            d = find_first(door, neighbors(level, g['player']))
            if d is None:
                return g
            res = add_curlvl_tag(g, 'shop-closed')
            for t in including_origin(straight_neighbors, level, d):
                if position(g['player']) == position(t):
                    continue
                res = update_at(res, t, lambda tt: assoc(tt, 'room', 'shop'))
            return res
        return update_before_action(bh, mark_shop)
    if re_seq(r"You crawl to the edge of the pit\.|You disentangle yourself\.",
              msg):
        return game.swap(assoc_in, ['player', 'trapped'], False)
    if re_seq(r"You fall into \w+ pit!|bear trap closes on your|"
              r"You stumble into \w+ spider web!|You are stuck to the web\.|"
              r"You are still in a pit|notice a loose board|"
              r"You are caught in a bear trap", msg):
        game.swap(assoc_in, ['player', 'trapped'], True)
        return mark_trap_here(bh)
    if re_seq(r"trap door opens|trap door in the .*and a rock falls on you|"
              r"trigger a rolling boulder|\(little dart|arrow\) shoots out at "
              r"you|gush of water hits|tower of flame erupts|cloud of gas",
              msg):
        return mark_trap_here(bh)
    if re_seq(r"You feel a strange vibration", msg):
        game.swap(add_curlvl_tag, 'end')
        return update_at_player_when_known(
            bh, lambda t: assoc(t, 'vibrating', True))
    if re_seq(r"Wait!  That's a .*mimic!", msg):
        def unmimic(g):
            res = g
            for t in neighbors(curlvl(g), g['player']):
                if t['glyph'] == 'm':
                    res = update_at(res, t, lambda tt: assoc(tt, 'feature',
                                                             None))
            return res
        return update_before_action(bh, unmimic)
    return None


def update_trapped_status(bh, old_pos):
    game = bh.game

    def f(g):
        if position(g['player']) == old_pos or trap(at_player(game.deref())):
            return g
        res = assoc_in(g, ['player', 'trapped'], False)
        if get_in(game.deref(), ['last-state', 'player', 'grabbed']):
            res = assoc_in(res, ['player', 'grabbed'], False)
        return res
    return update_on_known_position(bh, f)


def update_narrow(game, target):
    res = assoc_in(game, ['player', 'thick'], True)
    if branch_key(game) == 'sokoban':
        return res
    common = (set(position(t) for t in straight_neighbors(game['player']))
              & set(position(t) for t in straight_neighbors(target)))
    for p in common:
        res = update_at(res, p, lambda t: assoc(t, 'feature', 'rock'))
    return res


BOULDER_PLUG_RE = (r"The boulder triggers and plugs|"
                   r"You no longer feel the boulder|The boulder fills a pit|"
                   r"The boulder falls into and plugs a hole|"
                   r"You hear the boulder fall")


def Move(dir_):
    def hnd(a, bh):
        game = bh.game
        got_message = [False]
        old_game = game.deref()
        old_player = old_game['player']
        old_pos = position(old_player)
        level = curlvl(old_game)
        target = in_direction(level, old_pos, dir_)
        update_trapped_status(bh, old_pos)
        if (not old_player.get('trapped') and diagonal(dir_)
                and (tile_item(target) or blind(old_player))):
            def f(g):
                if (position(g['player']) == old_pos
                        and not monster_at(g, target)
                        and not got_message[0]):
                    if (typekw(old_game.get('last-action')) == 'move'
                            and (old_game.get('last-action') or {}).get('dir')
                            == dir_):
                        return update_at(g, target,
                                         lambda t: assoc(t, 'feature',
                                                         'door-open'))
                    return g
                return g
            update_on_known_position(bh, f)

        def message(msg):
            got_message[0] = True
            if move_message_handler(bh, msg) is not None:
                return
            if dizzy(old_player):
                return
            if re_seq(r"That door is closed", msg):
                game.swap(update_at, target,
                          lambda t: assoc(t, 'feature', 'door-closed'))
            # 3.6.7 hack.c test_move(): these used to fail silently (and the
            # silence is what the diagonal inference above relies on)
            elif re_seq(r"You can't move diagonally out of an intact doorway",
                        msg):
                game.swap(update_at, old_pos,
                          lambda t: assoc(t, 'feature', 'door-open'))
            elif re_seq(r"You can't move diagonally into an intact doorway",
                        msg):
                game.swap(update_at, target,
                          lambda t: assoc(t, 'feature', 'door-open'))
            elif re_seq(NO_MONSTER_RE, msg):
                game.swap(remove_monster, target)
            elif re_seq(r"You are carrying too much to get through", msg):
                game.swap(update_narrow, target)
            elif re_seq(r"Perhaps that's why .* cannot move it\.|"
                        r"^You hear a monster behind the boulder\.|"
                        r"^There's .* on the other side\.", msg):
                # 3.6 hack.c moverock(): a monster behind the boulder, no
                # time passes (astral-altar s103: 40 identical moves)
                turn = game.deref().get('turn')
                game.swap(update_at, target,
                          lambda t: assoc(t, 'move-blocked', turn))
            elif re_seq(r"You try to move the boulder, but in vain\.", msg):
                bt = in_direction(level, target, dir_)
                if diagonal(dir_) and tile_item(bt):
                    game.swap(update_at, bt,
                              lambda t: assoc(t, 'feature', 'door-open'))
                else:
                    game.swap(update_at, bt,
                              lambda t: assoc(t, 'feature', 'rock'))
            elif re_seq(BOULDER_PLUG_RE, msg):
                game.swap(update_at,
                          in_direction(in_direction(old_pos, dir_), dir_),
                          lambda t: assoc(t, 'feature', 'floor'))
            elif re_seq(r"It's a wall\.", msg):
                game.swap(update_at, target,
                          lambda t: assoc(t, 'feature',
                                          'rock' if blank(t) else 'wall'))

        def really_attack(_what):
            update_before_action(bh, update_monster, target,
                                 lambda m: assoc(m, 'peaceful', 'update'))
            return None
        return Handler(message=message, really_attack=really_attack)
    return action('move', lambda a: direction_trigger(dir_), hnd, dir=dir_)


def adjust_prayer_timeout(game):
    return assoc(game, 'last-prayer', game['turn'])


def Pray():
    return action('pray', "#pray\n",
                  lambda a, bh: bh.game.swap(adjust_prayer_timeout) and None)


def _update_searched(game, start):
    turns = game['turn'] - start + 1
    res = game
    for p in including_origin(neighbors, game['player']):
        res = update_at(res, p,
                        lambda t: update(t, 'searched', lambda s: s + turns))
    return res


def Search():
    def hnd(a, bh):
        update_on_known_position(bh, _update_searched, bh.game.deref()['turn'])
        return None
    return action('search', "s", hnd)


def Wait():
    return action('wait', ".", lambda a, bh: None)


def _mark_branch_entrance(game, tile, old_game, origin_feature):
    if branch_key(game) == 'ludios' or game['dlvl'] == "Home 1":
        return update_at(game, tile, lambda t: assoc(t, 'branch-id', 'main'))
    followers = []
    for n in neighbors(old_game['player']):
        m = monster_at(curlvl(old_game), n)
        if m is not None:
            followers.append(m)
    if any(m.get('friendly') or follower(m) for m in followers):
        res = game
        for t in including_origin(neighbors, curlvl(game), tile):
            if t.get('feature') == origin_feature:
                continue
            res = update_at(res, t, lambda tt: assoc(tt, 'branch-id',
                                                     branch_key(old_game)))
        return res
    return update_at(game, tile,
                     lambda t: assoc(t, 'branch-id', branch_key(old_game)))


def stairs_handler(bh):
    game = bh.game
    old_game = game.deref()
    old_branch = branch_key(old_game)
    old_dlvl = old_game['dlvl']
    old_stairs = at_player(old_game)
    entered_vlad = [False]

    def on_known(new_game):
        log.debug("asc/desc from %s to %s new-branch is %s", old_dlvl,
                  new_game['dlvl'], new_game['branch-id'])
        if (old_dlvl != new_game['dlvl'] and stairs(old_stairs)
                and not old_stairs.get('branch-id')):
            new_stairs = at_player(new_game)
            res = assoc_in(new_game,
                           ['dungeon', 'levels', old_branch, old_dlvl, 'tiles',
                            old_stairs['y'] - 1, old_stairs['x'], 'branch-id'],
                           new_game['branch-id'])
            return _mark_branch_entrance(res, new_stairs, old_game,
                                         old_stairs.get('feature'))
        return new_game
    update_on_known_position(bh, on_known)

    def message(text):
        if re_seq(r"You can't go down here", text):
            game.swap(update_at_player, lambda t: assoc(t, 'feature', None))
        elif re_seq(r"heat and smoke are gone.", text):
            entered_vlad[0] = True
        elif re_seq(r"A mysterious force prevents you from descending", text):
            leader = get_in(curlvl(old_game), ['blueprint', 'leader'])
            if leader:
                game.swap(update_around, leader,
                          lambda t: assoc(t, 'walked', None))

    def dlvl_changed(old_d, new_d):
        def f(g):
            if entered_vlad[0]:
                new_branch = 'vlad'
            elif (old_branch in SUBBRANCHES
                  and branch_entry(g, old_branch) == new_d):
                new_branch = 'main'
            else:
                new_branch = old_stairs.get('branch-id') or initial_branch_id(
                    g, new_d)
            res = update_in(g, ['dungeon', 'levels', old_branch, old_d, 'tags'],
                            lambda tags: conj_set(tags, new_branch))
            return assoc(res, 'branch-id', new_branch)
        game.swap(f)
        log.debug("choosing branch-id %s for dlvl %s",
                  game.deref()['branch-id'], new_d)
        no = re_first_group(r'unknown-([0-9]+)', game.deref()['branch-id'])
        if no:
            game.swap(lambda g: assoc(
                g, 'last-branch-no',
                max(g.get('last-branch-no') or 0, int(no))))
    return Handler(message=message, dlvl_changed=dlvl_changed)


def Ascend():
    return action('ascend', "<", lambda a, bh: stairs_handler(bh))


def Descend():
    return action('descend', ">", lambda a, bh: stairs_handler(bh))


def Kick(dir_):
    def hnd(a, bh):
        game = bh.game

        def message(msg):
            if re_seq(NO_MONSTER_RE, msg):
                game.swap(update_from_player, dir_, reset_item)
            elif re_seq(r"Your .* is in no shape for kicking.", msg):
                game.swap(assoc_in, ['player', 'leg-hurt'], True)
            elif re_seq(r"You can't move your leg!|"
                        r"There's not enough room to kick down here", msg):
                game.swap(assoc_in, ['player', 'trapped'], True)
            elif re_seq(r"A black ooze gushes up from the drain!", msg):
                game.swap(update_from_player, dir_,
                          lambda t: update(t, 'tags',
                                           lambda s: conj_set(s, 'pudding')))
            elif re_seq(r"The dish washer returns!", msg):
                game.swap(update_from_player, dir_,
                          lambda t: update(t, 'tags',
                                           lambda s: conj_set(s, 'foocubus')))
            elif re_seq(r"You see a ring shining in its midst", msg):
                game.swap(update_from_player, dir_,
                          lambda t: update(t, 'tags',
                                           lambda s: conj_set(s, 'ring')))
            elif re_seq(r"Thump!", msg):
                game.swap(update_from_player, dir_,
                          lambda t: assoc(t, 'thump', True))
            elif re_seq(r"^Ouch!  That hurts!|^Dumb move!", msg):
                # kicking a wall/iron bars wounds the leg again: the bot
                # kicked, waited for the leg, kicked... for 6000 turns
                # (cyc-03 g001).  Stop kicking that square.
                turn = game.deref().get('turn')
                game.swap(update_from_player, dir_,
                          lambda t: assoc(t, 'no-kick', turn))
        return Handler(message=message)
    return action('kick', lambda a: ctrl('d') + direction_trigger(dir_), hnd,
                  dir=dir_)


def Close(dir_):
    def hnd(a, bh):
        game = bh.game

        def message(text):
            d = in_direction(game.deref()['player'], dir_)
            f = {"This door is already closed.": 'door-closed',
                 "This doorway has no door.": None,
                 "You see no door there.": None}
            if text in f:
                game.swap(update_at, d,
                          lambda t: assoc(t, 'feature', f[text]))
        return Handler(message=message)
    return action('close', lambda a: 'c' + direction_trigger(dir_), hnd,
                  dir=dir_)


def _rogue_item_glyph(glyph):
    return {'"': ',', '$': '*', '%': ':', '[': ']'}.get(glyph, glyph)


def _item_glyph(game, item):
    g = (item_id(game, item) or {}).get('glyph')
    if 'rogue' in curlvl_tags(game):
        return _rogue_item_glyph(g)
    return g


THINGS_RE = r"^Things that (?:are|you feel) here:|You (?:see|feel)"
THING_RE = r"You (?:see|feel) here ([^.]+)."
ETYPE_RE = (r"Something is (written|engraved) here (?:in|on) the (?:.*)\.|"
            r"Some text has been (burned|melted) into the|"
            r"There's some (graffiti) on the|"
            r"You see a message (scrawled) in blood here")
ETEXT_RE = r"You read: \"(.*)\"\."


def unparseable_item(item):
    return bool(more_than(72, item['label']))


def Look():
    def hnd(a, bh):
        game = bh.game
        has_item = [False]
        has_engraving = [False]
        has_feature = [False]
        game.swap(lambda g: (update_at_player(g, lambda t: assoc(
            t, 'seen', True, 'new-items', False))
            if not blind(g['player']) else g))

        def after_look(g):
            res = update_at_player(g, lambda t: assoc(t, 'examined', g['turn']))
            if blind(g['player']):
                if at_player(res).get('engraving-type') != 'permanent':
                    res = update_at_player(res, lambda t: assoc(
                        t, 'engraving', None, 'engraving-type', None))
            elif not has_engraving[0]:
                res = update_at_player(res, lambda t: assoc(
                    t, 'engraving', None, 'engraving-type', None))
            t = at_player(res)
            if not has_feature[0] and not (floor_p(t) or corridor_p(t)):
                res = update_at_player(res,
                                       lambda tt: assoc(tt, 'feature', 'floor'))
            if not has_item[0]:
                res = update_at_player(res, lambda tt: assoc(tt, 'items', []))
            return res
        update_on_known_position(bh, after_look)

        def full_frame(_frame):
            # (send delegator #(if-let [items ...] (found-items % items) %))
            def emit():
                items = at_player(game.deref()).get('items')
                if items:
                    bh.delegator._invoke_event('found_items', items)
            bh.delegator._send(emit)

        def message_lines(lines):
            # 3.6 look_here(): with objects the dungeon feature is the first
            # line of the window ("There is an altar to Moloch (unaligned)
            # here.", "", "Things that are here:", ...); it used to be
            # ignored, the square became 'floor' and the bot engraved on the
            # altar forever (ca-w04/ca-w05 g010)
            start = 0
            while (start < len(lines) - 1
                   and not re_seq(THINGS_RE, lines[start])):
                text = lines[start]

                def upd(t, text=text):
                    nt = feature_msg_update(
                        t, text, 'rogue' in curlvl_tags(game.deref()))
                    if nt:
                        has_feature[0] = True
                        return nt
                    return t
                if text.strip():
                    game.swap(update_at_player, upd)
                start += 1
            lines = lines[start:]
            if re_seq(THINGS_RE, lines[0]):
                items = [label_to_item(l) for l in lines[1:]]
                top_item = items[0] if items else None
                has_item[0] = True
                game.swap(lambda g: update_at_player(g, lambda t: assoc(
                    t, 'items', [i for i in items if not unparseable_item(i)],
                    'item-glyph', _item_glyph(g, top_item) if top_item else None,
                    'item-color', None)))

        def message(text):
            if text == "But you can't reach it!":
                has_feature[0] = True
                has_item[0] = True
                return
            lbl = re_first_group(THING_RE, text)
            if lbl:
                item = label_to_item(lbl)
                log.debug("Single item here: %s", item)
                has_item[0] = True
                game.swap(lambda g: update_at_player(g, lambda t: assoc(
                    t, 'items', [] if unparseable_item(item) else [item],
                    'item-glyph', _item_glyph(g, item), 'item-color', None)))
            etype = re_any_group(ETYPE_RE, text)
            if etype:
                has_engraving[0] = True
                game.swap(update_at_player, lambda t: assoc(
                    t, 'engraving-type',
                    {"written": 'dust', "scrawled": 'dust', "melted": 'semi',
                     "graffiti": 'semi', "engraved": 'semi',
                     "burned": 'permanent'}.get(etype)))
            etext = re_first_group(ETEXT_RE, text)
            if etext:
                game.swap(update_at_player,
                          lambda t: assoc(t, 'engraving', etext))

            def upd(t):
                nt = feature_msg_update(t, text,
                                        'rogue' in curlvl_tags(game.deref()))
                if nt:
                    has_feature[0] = True
                    return nt
                return t
            game.swap(update_at_player, upd)
        return Handler(full_frame=full_frame, message_lines=message_lines,
                       message=message)
    return action('look', ":", hnd)


FARLOOK_MONSTER_RE = (r"^(?:.     *)?[^(]*\(([^,)]*)(?:,[^)]*)?\)|"
                      r"a (mimic) or a strange object$")
FARLOOK_TRAP_RE = r"^\^ * a trap \(([^)]*)\)"


def FarLook(pos):
    pos = position(pos)

    def hnd(a, bh):
        game = bh.game

        def message(text):
            align = re_first_group(r'\(([^ ]*) altar\)$', text)
            if align and align != "aligned":
                # (or (when-let [align ...] (if (not= align "aligned") (swap! ...)))
                #     (when-let [trap ...] ...) ...)
                # The clause's value is the inner `if`'s, so an *aligned* altar
                # yields nil and the `or` carries on to the trap and monster
                # clauses.  Returning on `align` alone - which reads naturally -
                # would swallow the rest of the chain.
                game.swap(update_at, pos,
                          lambda t: assoc(t, 'alignment', str_kw(align)))
                return
            trapname = re_first_group(FARLOOK_TRAP_RE, text)
            if trapname:
                f = TRAP_NAMES.get(trapname)
                if f is None:
                    raise ValueError("unknown farlook trap: %s >>> %s"
                                     % (text, trapname))
                game.swap(update_at, pos, lambda t: assoc(t, 'feature', f))
                return
            if text and monster_glyph(text[0]):
                desc = re_any_group(FARLOOK_MONSTER_RE, text)
                if desc:
                    peaceful = "peaceful " in desc
                    montype = by_description(desc)
                    log.debug("monster description %s => %s", text, montype)
                    # (if (= "gremlin" (:name montype)) ...) - `montype` is a
                    # plain String for any player rank, because `rank->monster`
                    # maps ranks to role names.  Clojure's keyword lookup is
                    # nil-safe on a String; indexing is not.  See clj.kw.
                    if kw(montype, 'name') == "gremlin":
                        game.swap(assoc, 'gremlins-peaceful', peaceful)
                    game.swap(update_monster, pos,
                              lambda m: assoc(m, 'peaceful', peaceful,
                                              'type', montype))
                    return
            log.debug("non-monster farlook result: %s", text)
        return Handler(message=message)
    return action('farlook', lambda a: ';' + to_position(pos) + '.', hnd,
                  pos=pos)


def _handle_door_message(game, dir_, text):
    d = in_direction(game.deref()['player'], dir_)
    mapping = [("The door opens.", 'door-open'),
               ("You cannot lock an open door.", 'door-open'),
               ("This door is locked.", 'door-locked'),
               ("This door is already open.", 'door-open'),
               ("This doorway has no door.", None),
               ("You see no door there.", None),
               ("You succeed in picking the lock.", 'door-closed'),
               ("You succeed in unlocking the door.", 'door-closed'),
               ("You succeed in locking the door.", 'door-locked'),
               ("You can't lock a door with a credit card.", 'door-closed')]
    for sub, feature in mapping:
        if sub in text:
            game.swap(update_at, d, lambda t: assoc(t, 'feature', feature))
            return


def Open(dir_):
    def hnd(a, bh):
        return Handler(message=lambda text: _handle_door_message(bh.game, dir_,
                                                                 text))
    return action('open', lambda a: 'o' + direction_trigger(dir_), hnd,
                  dir=dir_)


def _transfer_item(inv, old_slot, old_item):
    if old_slot not in inv:
        return inv               # item gone
    cur = inv[old_slot]
    ks = ['items', 'locked']
    if cur.get('buc') is None:
        ks.append('buc')
    if unparseable_item(cur) and old_item.get('in-use'):
        ks += ['in-use', 'worn']
    upd = dict(cur)
    for k in ks:
        if k in old_item:
            upd[k] = old_item[k]
    return assoc(inv, old_slot, upd)


def Inventory():
    def hnd(a, bh):
        game = bh.game

        def message(text):
            if text == "Not carrying anything.":
                game.swap(assoc_in, ['player', 'inventory'], {})
            elif text == "Not carrying anything except gold.":
                game.swap(lambda g: assoc_in(
                    g, ['player', 'inventory'],
                    {k: v for k, v in get_in(g, ['player', 'inventory'],
                                             {}).items() if k == '$'}))

        def inventory_list(inv):
            # `(reduce transfer-item (into {} (for [[c i] inventory]
            #  (slot-item c i))) old-inventory)` - `into` keeps the parse
            # order and promotes to hash order at the 9th item, and the old
            # inventory is folded over it in *its* Clojure order.  `have`
            # returns the first match in that order, so this decides which
            # item the bot eats, wields or throws once it carries 9 things.
            # Measured against the original (tools/cljcmp/dbg_inv.clj): with
            # 9 slots it iterates ["$" "h" "d" "i" "g" "e" "c" "b" "a"] for a
            # screen listing a,b,c,e,g,i,d,h and gold - i.e. the *reverse* of
            # the screen, with gold in front.  That is the persistent-assoc
            # rule (prepend, hash order from the 10th entry), not `into`'s.
            new = CljMap()
            for c, i in inv.items():
                slot, item = slot_item(c, i)
                new._assoc_(slot, item)

            def f(old_inv):
                res = new
                for old_slot, old_item in clj_items(old_inv or {}):
                    res = _transfer_item(res, old_slot, old_item)
                return res
            game.swap(lambda g: update_in(g, ['player', 'inventory'], f))
        return Handler(message=message, inventory_list=inventory_list)
    return action('inventory', "i", hnd)


def examine_tile(game):
    player = game['player']
    if player.get('engulfed'):
        return None
    tile = at_player(game)
    if tile is None:
        return None
    if not (not blind(player) or (altar_p(tile) and not tile.get('alignment'))):
        return None
    if (tile.get('new-items') or unknown(tile) or unknown_trap(tile)
            or (e_p(tile) and not perma_e(tile)
                and tile.get('examined') != game['turn'])
            or (altar_p(tile) and not tile.get('alignment'))):
        return with_reason("examining tile", tile, Look())
    return None


def examine_features(game):
    if game['player'].get('engulfed'):
        return None

    def pred(t):
        return ((unknown_trap(t)
                 or (branch_key(game) != 'astral' and altar_p(t)
                     and not t.get('alignment')))
                and not blank(t) and not tile_item(t) and not tile_monster(t))
    t = find_first(pred, tile_seq(curlvl(game)))
    if t:
        return with_reason("examining ambiguous feature", FarLook(t))
    return None


def examine_monsters(game):
    player = game['player']
    if player.get('engulfed') or hallu(player):
        return None
    for m in curlvl_monsters(game):
        if m.get('remembered') or m.get('friendly'):
            continue
        if (m.get('type') and m.get('peaceful') is not None
                and m.get('peaceful') != 'update'):
            continue
        if m['glyph'] in ('I', '1', '2', '3', '4', '5'):
            continue
        return with_reason("examining monster", FarLook(m))
    return None


def _inventory_handler(bh):
    h = Handler()

    def choose_action(game):
        deregister_handler(bh, h)
        if typekw(game.get('last-action*')) != 'inventory':
            return with_reason("requested inventory update", Inventory())
        return None
    h.choose_action = choose_action
    return h


def update_inventory(bh):
    return register_handler(bh, PRIORITY_TOP - 1, _inventory_handler(bh))


def update_tile(bh):
    return update_at_player_when_known(bh,
                                       lambda t: assoc(t, 'new-items', True))


def _discovery_demangle(section, appearance):
    if section == "Gems":
        return (appearance + " stone" if appearance == "gray"
                else appearance + " gem")
    return {"Amulets": appearance + " amulet", "Wands": appearance + " wand",
            "Rings": appearance + " ring", "Potions": appearance + " potion",
            "Spellbooks": appearance + " spellbook",
            "Scrolls": "scroll labeled " + appearance}.get(section, appearance)


DISCOVERIES_RE = (r"(Artifacts|Unique Items|Spellbooks|Amulets|Weapons|Wands|"
                  r"Gems|Armor|Food|Tools|Scrolls|Rings|Potions)|"
                  r"(?:\* )?([^\(]*)(?: called [^(]+)? \(([^\)]*)\)$|"
                  r"^(?:[^(]+)$")


def Discoveries():
    def hnd(a, bh):
        game = bh.game
        known_names = set()

        def about_to_choose(_g):
            # (swap! game forget-names (difference (:used-names game)
            #                                      @known-names))
            # `game` is the atom, so `(:used-names game)` is nil and
            # `(difference nil @known-names)` is nil; `forget-names` returns
            # its game unchanged on an empty name set.  The original's
            # Discoveries handler therefore never forgets a name.  Reproduced
            # as the same no-op rather than repaired.
            from .itemid import forget_names
            game.swap(forget_names, set())

        def message_lines(lines_all):
            section = None
            discoveries = []
            for line in lines_all:
                l2 = re.sub(r'^(.*) called ([^(]+) \([^)]*\)', r'\1 (\2)', line)
                g = re_first_groups(DISCOVERIES_RE, l2)
                group, id_, appearance = (g[0], g[1], g[2]) if g else (None,
                                                                       None,
                                                                       None)
                called = re_first_group(r'called ([^(]+)(?: |$)', line)
                if called:
                    known_names.add(called)
                if group:
                    section = group
                    continue
                if section == "Unique Items":
                    continue
                if appearance:
                    discoveries.append(
                        (_discovery_demangle(section, appearance), id_))
            from .itemid import add_discoveries
            game.swap(add_discoveries, discoveries)
        return Handler(about_to_choose=about_to_choose,
                       message_lines=message_lines)
    return action('discoveries', "\\", hnd)


def _discoveries_handler(bh):
    h = Handler()

    def choose_action(game):
        deregister_handler(bh, h)
        if typekw(game.get('last-action*')) != 'discoveries':
            return with_reason("discoveries update", Discoveries())
        return None
    h.choose_action = choose_action
    return h


def update_discoveries(bh):
    return register_handler(bh, PRIORITY_TOP - 1, _discoveries_handler(bh))


def Name(slot, name):
    def hnd(a, bh):
        update_inventory(bh)
        return Handler(name_menu=lambda _o: 'b',
                       name_what=lambda _t: slot,
                       what_name=lambda _t: name)
    return action('name', "#name\n", hnd, slot=slot, name=name)


def Call(slot, name):
    def hnd(a, bh):
        update_inventory(bh)
        update_tile(bh)
        update_discoveries(bh)
        if name in names:
            bh.game.swap(lambda g: assoc(g, 'used_names',
                                         conj_set(g['used_names'], name)))
        return Handler(name_menu=lambda _o: 'c',
                       name_what=lambda _t: slot,
                       what_name=lambda _t: name)
    return action('call', "#call\n", hnd, slot=slot, name=name)


def name_item(bh, slot, name):
    h = Handler()

    def choose_action(game):
        deregister_handler(bh, h)
        item = inventory_slot(game, slot)
        if item:
            if name != item.get('specific'):
                return Name(slot, name)
            return None
        log.warning("naming nonexistent slot %s", slot)
        return None
    h.choose_action = choose_action
    return register_handler(bh, PRIORITY_TOP, h)


def identify_slot(game, slot, id_):
    return add_discovery(game, slot_appearance(game, slot), id_)


def Apply(slot):
    def hnd(a, bh):
        game = bh.game
        possible_autoid(bh, slot)

        def message(msg):
            if re_seq(r"has no oil|has run out of power", msg):
                game.swap(identify_slot, slot, "oil lamp")
                name_item(bh, slot, "empty")
            elif re_seq(r" lamp is now (on|off)|burns? brightly!|"
                        r"You light your |^You snuff ", msg):
                update_inventory(bh)
            elif re_seq(r" seems to be locked", msg):
                game.swap(update_slot, slot, lambda i: assoc(i, 'locked', True))
            elif re_seq(r" is empty\.", msg):
                game.swap(update_slot, slot, lambda i: assoc(i, 'items', []))

        def take_something_out(_p):
            game.swap(update_slot, slot, lambda i: assoc(i, 'items', []))
            return True

        def take_out_what(options):
            game.swap(update_slot, slot, lambda i: update(
                i, 'items',
                lambda its: conj_vec(its, *[label_to_item(v)
                                            for v in options.values()])))
            return set()          # update items but don't take anything out
        return Handler(
            attach_candelabrum_candles=lambda _p: update_inventory(bh) and True
            or True,
            message=message, apply_what=lambda _p: slot,
            take_something_out=take_something_out,
            take_out_what=take_out_what,
            put_something_in=lambda _p: False)
    return action('apply', "a", hnd, slot=slot)


def with_handler(*args):
    """(with-handler [priority] handler action)"""
    if len(args) == 2:
        priority, hnd, act = PRIORITY_DEFAULT, args[0], args[1]
    else:
        priority, hnd, act = args
    return assoc(act, 'handlers', conj_vec(act.get('handlers'),
                                           (priority, hnd)))


def ApplyAt(slot, dir_):
    def hfactory(bh):
        game = bh.game

        def message(msg):
            if re_seq(r"The ceiling collapses around you!", msg):
                game.swap(update_around_player,
                          lambda t: assoc(t, 'feature', 'rock'))
            elif re_seq(r"you can't dig while entangled", msg):
                game.swap(assoc_in, ['player', 'trapped'], True)
            elif re_seq(r"This wall (seems|is) too hard to dig into\.", msg):
                if 'orcus' not in curlvl(game.deref())['tags']:
                    game.swap(update_from_player, dir_,
                              lambda t: assoc(t, 'undiggable', True))
            elif re_seq(r"You make an opening", msg):
                game.swap(update_from_player, dir_,
                          lambda t: assoc(t, 'dug', True, 'feature', 'floor'))
            elif re_seq(r"You succeed in cutting away some rock", msg):
                game.swap(update_from_player, dir_,
                          lambda t: assoc(t, 'dug', True,
                                          'feature', 'corridor'))
            elif re_seq(r"^You swing your pick", msg):
                game.swap(update_from_player, dir_,
                          lambda t: assoc(t, 'feature', None))
            elif re_seq(r"here is too hard to", msg):
                game.swap(add_curlvl_tag, 'undiggable-floor')
            elif re_seq(r"You dig a pit", msg):
                game.swap(update_at_player, lambda t: assoc(t, 'feature',
                                                            'pit'))
            elif re_seq(r"You dig a hole through", msg):
                game.swap(update_at_player, lambda t: assoc(t, 'feature',
                                                            'hole'))
        return Handler(what_direction=lambda _p: dir_, message=message)
    return with_handler(PRIORITY_TOP, hfactory, Apply(slot))


def ForceLock():
    def hnd(a, bh):
        game = bh.game
        for idx, item in indexed(at_player(game.deref()).get('items') or ()):
            if item.get('locked'):
                game.swap(update_item_at_player, idx,
                          lambda i: assoc(i, 'locked', False))
        return Handler(force_lock=lambda _p: True)
    return action('forcelock', "#force\n", hnd)


def Unlock(slot, dir_):
    def hfactory(bh):
        game = bh.game
        if dir_ == '.':
            for idx, item in indexed(at_player(game.deref()).get('items') or ()):
                if item.get('locked'):
                    game.swap(update_item_at_player, idx,
                              lambda i: assoc(i, 'locked', False))

        def message(msg):
            if dir_ != '.':
                _handle_door_message(game, dir_, msg)

        def lock_it(_p):
            if dir_ in DIRMAP:
                game.swap(update_from_player, dir_,
                          lambda t: assoc(t, 'feature', 'door-closed'))
            return False

        def unlock_it(_p):
            if dir_ in DIRMAP:
                game.swap(update_from_player, dir_,
                          lambda t: assoc(t, 'feature', 'door-locked'))
            return True
        return Handler(message=message, lock_it=lock_it, unlock_it=unlock_it)
    return with_handler(PRIORITY_TOP, hfactory, ApplyAt(slot, dir_))


def possible_autoid(bh, slot, no_mark=False):
    """Check if the item at slot auto-identified on use."""
    item = inventory_slot(bh.game.deref(), slot)
    if not item:
        return
    if know_id(bh.game.deref(), item):
        return
    update_discoveries(bh)
    if no_mark:
        return
    h = Handler()

    def about_to_choose(game):
        if typekw(game.get('last-action*')) == 'discoveries':
            deregister_handler(bh, h)
            if not know_id(game, item):
                bh.game.swap(add_prop_discovery, appearance_of(item),
                             'autoid', False)
    h.about_to_choose = about_to_choose
    register_handler(bh, h)


def mark_tried(game, item):
    if not impaired(game['player']):
        return assoc(game, 'tried', conj_set(game['tried'],
                                             appearance_of(item)))
    return game


def tried(game, item):
    return appearance_of(item) in game['tried']


def _mark_use(bh, slot):
    bh.game.swap(lambda g: mark_tried(g, inventory_slot(g, slot)))


def Wield(slot):
    def hnd(a, bh):
        update_inventory(bh)
        possible_autoid(bh, slot)
        return Handler(wield_what=lambda _p: slot)
    return action('wield', "w", hnd, slot=slot)


def UnWield(*_):
    return Wield('-')


def Wear(slot):
    def hnd(a, bh):
        game = bh.game
        update_inventory(bh)
        possible_autoid(bh, slot)

        def message(msg):
            if re_seq(r"You don't have anything else to wear|"
                      r"already wearing that", msg):
                game.swap(update_in, ['player', 'inventory', slot],
                          lambda i: assoc(i, 'worn', True, 'in-use', True))

        def wear_what(_p):
            _mark_use(bh, slot)
            return slot
        return Handler(message=message, wear_what=wear_what)
    return action('wear', "W", hnd, slot=slot)


def PutOn(slot):
    def hnd(a, bh):
        update_inventory(bh)
        possible_autoid(bh, slot)

        def put_on_what(_p):
            _mark_use(bh, slot)
            return slot
        return Handler(put_on_what=put_on_what)
    return action('puton', "P", hnd, slot=slot)


def Remove(slot):
    def hnd(a, bh):
        update_inventory(bh)

        def remove_what(_p):
            _mark_use(bh, slot)
            return slot
        return Handler(remove_what=remove_what)
    return action('remove', "R", hnd, slot=slot)


def TakeOff(slot):
    def hnd(a, bh):
        game = bh.game
        update_inventory(bh)

        def message(msg):
            if re_seq(r"Not wearing any armor|not wearing that", msg):
                game.swap(update_in, ['player', 'inventory', slot],
                          lambda i: assoc(i, 'worn', False, 'in-use', False))

        def take_off_what(_p):
            _mark_use(bh, slot)
            return slot
        return Handler(message=message, take_off_what=take_off_what)
    return action('takeoff', "T", hnd, slot=slot)


_RING_MSGS = [
    (r"got lost in the sink, but there it is!", "ring of searching"),
    (r"The ring is regurgitated!", "ring of slow digestion"),
    (r"The sink quivers upward for a moment", "ring of levitation"),
    (r"You smell rotten fruit", "ring of poison resistance"),
    (r"Static electricity surrounds the sink", "ring of shock resistance"),
    (r"You hear loud noises coming from the drain", "ring of conflict"),
    (r"The water flow seems fixed", "ring of sustain ability"),
    (r"The water flow seems (stronger|weaker) now", "ring of gain strength"),
    (r"The water flow seems (greater|lesser) now",
     "ring of gain constitution"),
    (r"The water flow (hits|misses) the drain", "ring of increase accuracy"),
    (r"The water's force seems (greater|smaller) now",
     "ring of increase damage"),
    (r"Several flies buzz angrily around the sink",
     "ring of aggravate monster"),
    (r"Suddenly, .*from the sink!", "ring of hunger"),
    (r"The faucets flash brightly for a moment", "ring of adornment"),
    (r"The sink looks as good as new", "ring of regeneration"),
    (r"You don't see anything happen to the sink", "ring of invisibility"),
    (r"You see the ring slide right down the drain!", "ring of free action"),
    (r"You see some air in the sink", "ring of see invisible"),
    (r"The sink seems to blend into the floor for a moment", "ring of stealth"),
    (r"The hot water faucet flashes brightly", "ring of fire resistance"),
    (r"The cold water faucet flashes brightly", "ring of cold resistance"),
    (r"The sink looks nothing like",
     "ring of protection from shape changers"),
    (r"The sink glows (silver|black) for a moment", "ring of protection"),
    (r"The sink glows white for a moment", "ring of warning"),
    (r"The sink momentarily vanishes", "ring of teleportation"),
    (r"The sink looks like it is being beamed", "ring of teleport control"),
    (r"The sink momentarily looks like a fountain", "ring of polymorph"),
    (r"The sink momentarily looks like a regularly",
     "ring of polymorph control"),
]


def _ring_msg(msg):
    for pat, id_ in _RING_MSGS:
        if re_seq(pat, msg):
            return id_
    return None


UNDROPPABLE_LABELS = set()


def DropSingle(slot, qty):
    def hnd(a, bh):
        game = bh.game
        update_inventory(bh)
        update_tile(bh)
        game.swap(lambda g: assoc(g, 'player', dissoc(g['player'], 'thick')))

        def message(msg):
            id_ = _ring_msg(msg)
            if id_:
                game.swap(identify_slot, slot, id_)
            elif msg == "You cannot drop something you are wearing.":
                game.swap(update_in, ['player', 'inventory', slot],
                          lambda i: assoc(i, 'worn', True, 'in-use', True))
                # the inventory refresh gives the label back without a worn
                # marker we understand: remember the label (big-w01 g014,
                # g035 dropped the same worn item 40 times)
                item = inventory_slot(game.deref(), slot) or {}
                UNDROPPABLE_LABELS.add(item.get('label'))
                log.warning("cannot drop worn item %r (slot %s)",
                            item.get('label'), slot)

        def sell_it(bid, _what):
            item = inventory_slot(game.deref(), slot)
            if price_id(game.deref(), item):
                game.swap(add_observed_cost, appearance_of(item), bid, True)
            return None
        return Handler(message=message, sell_it=sell_it,
                       drop_single=lambda _p: (str(qty) if qty > 0 else "")
                       + slot)
    return action('dropsingle', "d", hnd, slot=slot, qty=qty)


def Quiver(slot):
    def hnd(a, bh):
        update_inventory(bh)
        return Handler(ready_what=lambda _p: slot)
    return action('quiver', "Q", hnd, slot=slot)


def Drop(slot_or_map, qty=None):
    if qty is not None:
        return DropSingle(slot_or_map, qty)
    if isinstance(slot_or_map, str):
        return DropSingle(slot_or_map, 1)
    raise NotImplementedError("multidrop not yet implemented")


def PickUp(label_or_list):
    def hnd(a, bh):
        update_inventory(bh)
        update_tile(bh)
        if isinstance(label_or_list, str):
            labels = [label_or_list]
        else:
            labels = list(label_or_list)
        remaining = list(labels)

        def pick_up_what(options):
            res = set()
            for slot, lbl in options.items():
                if lbl in remaining:
                    remaining.remove(lbl)
                    res.add(slot)
            if remaining:
                log.warning("pickup: wanted labels not in the menu: %r "
                            "(menu: %r)", remaining, list(options.values()))
            return res

        def message(msg):
            # 3.6 hack.c pickup checks: standing on a trap door/hole the hero
            # escaped, levitating, riding unskilled... - no time passes and
            # BotHack wanted the items again at once (full-w02 g010)
            if re_seq(r"^You cannot reach the (?:bottom of the abyss|floor|"
                      r"ground|ice)\.|^You cannot reach anything here\.|"
                      r"^You can't reach the bottom to pick things up\.",
                      msg):
                turn = bh.game.deref().get('turn')
                bh.game.swap(update_at_player,
                             lambda t: assoc(t, 'no-pickup', turn))
        return Handler(pick_up_what=pick_up_what, message=message)
    return action('pickup', ",", hnd, labels=label_or_list)


def Autotravel(pos):
    def hnd(a, bh):
        game = bh.game
        p = position(pos)
        path = set(position(x) for x in (a.get('path') or [])[1:-1])
        game.swap(lambda g: assoc(g, 'last-autonav', p,
                                  'autonav-stuck', False))

        def know_position(frame):
            cursor = frame.cursor
            if (path and p != cursor
                    and (any(boulder(t) for t in neighbors(curlvl(game.deref()),
                                                           cursor))
                         or not any(position(n) in path
                                    for n in neighbors(cursor)))):
                log.debug("autonav stuck")
                game.swap(assoc, 'autonav-stuck', True)
        return Handler(know_position=know_position,
                       message=lambda msg: move_message_handler(bh, msg),
                       travel_where=lambda: p)
    return action('autotravel', "_", hnd, pos=position(pos))


def Enhance():
    def hnd(a, bh):
        def current_skills(_options):
            bh.game.swap(assoc_in, ['player', 'can-enhance'], None)
            return set()
        return Handler(current_skills=current_skills)
    return action('enhance', "#enhance\n", hnd)


def enhance_all():
    return with_handler(Handler(enhance_what=lambda _o: 'a'), Enhance())


def Read(slot):
    def hnd(a, bh):
        game = bh.game
        update_inventory(bh)
        possible_autoid(bh, slot)

        def read_what(_p):
            _mark_use(bh, slot)
            return slot

        def message(msg):
            if re_seq(r"Your [a-z]* (glow|begin to glow|tingle|begin to "
                      r"tingle)|A faint (buzz|glow) surrounds your [a-z]*\.|"
                      r"You feel confused\.", msg):
                game.swap(identify_slot, slot, "scroll of confuse monster")
            elif re_seq(r"You feel like someone is helping you\.|"
                        r"You feel in touch with the Universal Oneness\.|"
                        r"You feel like you need some help\.|"
                        r"You feel the power of the Force against you", msg):
                game.swap(identify_slot, slot, "scroll of remove curse")
            elif re_seq(r"You hear maniacal laughter|You hear sad wailing",
                        msg):
                game.swap(identify_slot, slot, "scroll of scare monster")
        return Handler(read_what=read_what, message=message)
    return action('read', "r", hnd, slot=slot)


def Sit():
    def hnd(a, bh):
        game = bh.game

        def message(msg):
            if re_seq(r"not very comfortable\.\.\.", msg):
                game.swap(update_at_player, lambda t: assoc(t, 'feature', None))
            elif re_seq(r"Having fun sitting on the (floor|air)\?", msg):
                game.swap(update_at_player,
                          lambda t: assoc(t, 'feature', 'floor'))
            else:
                move_message_handler(bh, msg)
        return Handler(message=message)
    return action('sit', "#sit\n", hnd)


_PRICE_SUFFIX_RE = re.compile(
    r" \((?:no charge|unpaid, \d+ zorkmids?|for sale, \d+ zorkmids?"
    r"(?: each)?|\d+ zorkmids?)\)$")


def _no_price(label):
    return _PRICE_SUFFIX_RE.sub('', label or '')


def Eat(slot_or_label):
    def hnd(a, bh):
        def message(msg):
            if msg == "You don't have anything to eat.":
                update_inventory(bh)
                update_tile(bh)

        def eat_it(what):
            # 3.6 floorfood() asks with iflags.suppress_price: the question
            # has no "(no charge)" / "(for sale, N zorkmids)" (ca-w04 g011)
            if isinstance(slot_or_label, str) and len(slot_or_label) > 1 \
                    and _no_price(what) == _no_price(slot_or_label):
                update_tile(bh)
                return True
            return False

        def eat_what(_p):
            if isinstance(slot_or_label, str) and len(slot_or_label) > 1:
                update_tile(bh)
                return None
            update_inventory(bh)
            return slot_or_label
        return Handler(message=message, eat_it=eat_it, eat_what=eat_what)
    return action('eat', "e", hnd, slot=slot_or_label)


FOUNTAIN_RE = r"The flow reduces to a trickle|, stop using that fountain!"


def Quaff(slot):
    def hnd(a, bh):
        game = bh.game
        possible_autoid(bh, slot)

        def message(msg):
            if re_seq(FOUNTAIN_RE, msg):
                game.swap(update_at_player,
                          lambda t: update(t, 'tags',
                                           lambda s: conj_set(s, 'trickle')))

        def drink_here(_p):
            if slot == '.':
                update_tile(bh)
                return True
            return False

        def drink_what(_p):
            if slot != '.':
                _mark_use(bh, slot)
                update_inventory(bh)
                return slot
            return None
        return Handler(message=message, drink_here=drink_here,
                       drink_what=drink_what)
    return action('quaff', "q", hnd, slot=slot)


def use_action(item):
    t = item_type(item)
    if t in ('scroll', 'spellbook'):
        return Read
    if t == 'potion':
        return Quaff
    if t in ('ring', 'amulet'):
        return PutOn
    if t == 'armor':
        return Wear
    if t == 'weapon':
        return Wield
    if t == 'tool':
        return PutOn if item_subtype(item) == 'accessory' else Apply
    return None


def remove_action(item):
    if item.get('wielded'):
        return UnWield
    t = item_type(item)
    if t in ('ring', 'amulet', 'tool'):
        return Remove
    if t == 'weapon':
        return UnWield
    return TakeOff


def remove_blockers(game, slot):
    item = inventory_slot(game, slot)
    bs = None
    from .player import blockers as _blockers
    if item:
        bs = _blockers(game, item)
    if not bs:
        return None
    blocker_slot, blocker = bs[0]
    if (blocker and not any(b[1].get('buc') == 'cursed' for b in bs)
            and (not blocker.get('wielded') or shield(item))):
        return with_reason("removing blockers of", slot,
                           remove_action(blocker)(blocker_slot))
    return None


def make_use(game, slot):
    item = inventory_slot(game, slot)
    if (item.get('in-use') or cursed_blockers(game, slot)
            or not has_hands(game['player'])):
        return None
    res = None
    # port: only boots care about the hero being trapped; untrapping first
    # for a ring made the bot climb out of a pit, then go back in for the
    # gold forever (big-w01 g023)
    if (game['player'].get('trapped')
            and 'boots' in (item.get('name') or '')):
        res = untrap_move(game)
    if res is None:
        res = remove_blockers(game, slot)
    if res is None:
        f = use_action(item)
        res = f(slot) if f else None
    return with_reason("making use of", slot, res) if res else None


# port: turn of the last removal the bot decided itself (enchanting armor,
# swapping rings...); the assisted re-dress handler must not undo it
LAST_BOT_REMOVAL = [-1000]


def remove_use(game, slot):
    item = inventory_slot(game, slot)
    if not item.get('in-use'):
        return None
    LAST_BOT_REMOVAL[0] = game.get('turn') or 0
    res = None
    # port: only boots care about the hero being trapped; untrapping first
    # for a ring made the bot climb out of a pit, then go back in for the
    # gold forever (big-w01 g023)
    if (game['player'].get('trapped')
            and 'boots' in (item.get('name') or '')):
        res = untrap_move(game)
    if res is None:
        res = remove_blockers(game, slot)
    if res is None and can_remove(game, slot):
        res = remove_action(item)(slot)
    return with_reason("removing use of", slot, res) if res else None


def without_levitation(game, act):
    from .player import have_levi_on
    a = act() if callable(act) else act
    if a is None:
        return None
    if branch_key(game) != 'air':
        levi = have_levi_on(game)
        if levi:
            return with_reason("action", typekw(a), "forbids levitation",
                               remove_use(game, levi[0]))
    return a


def Repeated(act, n):
    return action('repeated', lambda a: str(n) + trigger(act),
                  lambda a, bh: action_handler(act, bh), inner=act, n=n)


def search(n=1):
    return Repeated(Search(), n)


def arbitrary_move(game, level, diagonal_only=False):
    player = game['player']
    nbrs = (diagonal_neighbors(level, player) if diagonal_only
            else neighbors(level, player))
    cands = [t for t in nbrs
             if not trap(t) and not monster_at(level, t)
             and (passable_walking(game, level, at(level, player), t)
                  or (not boulder(t) and unknown(t)))]
    if not cands:
        return None
    from .util import random_nth
    t = random_nth(cands, game['rng'])
    if t is None:
        return None
    return with_reason("arbitrary direction", Move(towards(player, t)))


def untrap_move(game, level=None):
    if level is None:
        level = curlvl(game)
    player = game['player']
    wall = find_first(lambda t: wall_p(t) or rock_p(t),
                      diagonal_neighbors(level, player))
    if wall:
        return with_reason("untrap move", Move(towards(player, wall)))
    a = arbitrary_move(game, level, True)
    if a is None:
        a = arbitrary_move(game, level)
    return with_reason("untrap move", a) if a else None


def kick(game, target_or_dir):
    player = game['player']
    dir_ = (target_or_dir if isinstance(target_or_dir, str)
            else towards(player, target_or_dir))
    if (in_direction(curlvl(game), player, dir_) or {}).get('thump') \
            or stressed(player):
        return None
    if player.get('leg-hurt'):
        return with_reason("kick", with_reason("wait out leg hurt", search(10)))
    if player.get('trapped'):
        return with_reason("kick", untrap_move(game))
    return with_reason("kick", without_levitation(game, Kick(dir_)))


def dig(slot_item_pair, dir_):
    slot, item = slot_item_pair
    if item.get('in-use'):
        return ApplyAt(slot, dir_)
    return Wield(slot)


def descend(game):
    return without_levitation(game, Descend)


def Offer(slot_or_label):
    def hnd(a, bh):
        game = bh.game

        def message(msg):
            if re_seq(r"You are not standing on an altar", msg):
                log.warning("#offer on non-altar")
            elif re_seq(r"You have a feeling of reconciliation\.|"
                        r"You glimpse a four-leaf clover at your feet|"
                        r"You think something brushed your foot|"
                        r"You see crabgrass at your feet", msg):
                game.swap(assoc_in, ['player', 'last-prayer'], -1000)

        def sacrifice_it(what):
            if isinstance(slot_or_label, str) and len(slot_or_label) > 1 \
                    and what == slot_or_label:
                update_tile(bh)
                return True
            return False

        def sacrifice_what(_p):
            if isinstance(slot_or_label, str) and len(slot_or_label) > 1:
                update_tile(bh)
                return None
            update_inventory(bh)
            return slot_or_label
        return Handler(message=message, sacrifice_it=sacrifice_it,
                       sacrifice_what=sacrifice_what)
    return action('offer', "#offer\n", hnd, slot=slot_or_label)


def _nth_container_index(game, n):
    containers = 0
    for idx, item in enumerate(at_player(game).get('items') or ()):
        if container(item):
            if containers == n:
                return idx
            containers += 1
    return None


def Loot():
    def hnd(a, bh):
        game = bh.game
        n = [-1]

        def take_something_out(_p):
            game.swap(lambda g: update_item_at_player(
                g, _nth_container_index(g, n[0]),
                lambda i: assoc(i, 'items', [])))
            return True

        def take_out_what(options):
            game.swap(lambda g: update_item_at_player(
                g, _nth_container_index(g, n[0]),
                lambda i: update(i, 'items',
                                 lambda its: conj_vec(
                                     its, *[label_to_item(v)
                                            for v in options.values()]))))
            return set()

        def message(msg):
            if msg.startswith("You carefully open"):
                n[0] += 1
            if re_seq(r"You don't find anything here to loot", msg):
                update_tile(bh)
            elif re_seq(r"It develops a huge set of teeth and bites you!", msg):
                game.swap(lambda g: update_item_at_player(
                    g, _nth_container_index(g, n[0]),
                    lambda i: assoc(i, 'name', "bag of tricks")))
            elif re_seq(r" seems to be locked\.", msg):
                n[0] += 1
                idx = n[0]
                game.swap(lambda g: update_item_at_player(
                    g, _nth_container_index(g, idx),
                    lambda i: assoc(i, 'locked', True)))
            elif re_seq(r" is empty\.", msg):
                game.swap(lambda g: update_item_at_player(
                    g, _nth_container_index(g, n[0]),
                    lambda i: assoc(i, 'items', [])))
        return Handler(loot_what=lambda _o: {','}, loot_it=lambda _p: True,
                       take_something_out=take_something_out,
                       take_out_what=take_out_what, message=message,
                       put_something_in=lambda _p: False)
    return action('loot', "#loot\n", hnd)


def _update_container(bh, slot):
    h = Handler()

    def choose_action(game):
        if not has_hands(game['player']):
            return None
        deregister_handler(bh, h)
        if slot == '.':
            return with_reason("updating content of container at", slot, Loot())
        if inventory_slot(game, slot):
            return with_reason("updating content of container at", slot,
                               Apply(slot))
        log.warning("container at %s disappeared - exploded BoH?", slot)
        return None
    h.choose_action = choose_action
    register_handler(bh, PRIORITY_TOP, h)


def put_in(bag_slot, slot_or_amt_map, amt=None):
    if amt is not None:
        amt_map = {slot_or_amt_map: amt}
    elif isinstance(slot_or_amt_map, dict):
        amt_map = slot_or_amt_map
    else:
        amt_map = {slot_or_amt_map: None}

    def hfactory(bh):
        update_inventory(bh)
        _update_container(bh, bag_slot)
        return Handler(
            take_something_out=lambda _p: False,
            put_something_in=lambda _p: True,
            # (set (map #(str (val %) (key %)) amt-map)) - `str` makes these
            # Clojure Strings, one character long when the amount is nil, and
            # they hash as Strings rather than as Characters
            put_in_what=lambda _o: set(
                CljStr(("" if v is None else str(v)) + k)
                for k, v in amt_map.items()))
    act = Loot() if bag_slot == '.' else Apply(bag_slot)
    return with_reason("putting", amt_map, "into bag at", bag_slot,
                       with_handler(PRIORITY_TOP - 1, hfactory, act))


def take_out(bag_slot, label_or_amt_map, amt=None):
    if amt is not None:
        amt_map = {label_or_amt_map: amt}
    elif isinstance(label_or_amt_map, dict):
        amt_map = label_or_amt_map
    else:
        amt_map = {label_or_amt_map: None}

    def hfactory(bh):
        update_inventory(bh)
        _update_container(bh, bag_slot)

        def take_out_what(options):
            res = set()
            for slot, label in options.items():
                if label in amt_map:
                    a = amt_map[label]
                    # (str amt slot): a Clojure String, see put-in-what above
                    res.add(CljStr(("" if a is None else str(a)) + slot))
            return res
        return Handler(take_something_out=lambda _p: True,
                       take_out_what=take_out_what,
                       put_something_in=lambda _p: False)
    act = Loot() if bag_slot == '.' else Apply(bag_slot)
    return with_reason("taking", amt_map, "out of container at", bag_slot,
                       with_handler(PRIORITY_TOP - 1, hfactory, act))


def unbag(game, maybe_bag_slot, item, qty=1):
    if item != inventory_slot(game, maybe_bag_slot):
        if more_than(51, inventory(game)):
            log.warning("tried unbagging with full inventory - doing nothing")
            return None
        return with_reason("preparing item -", item['name'],
                           take_out(maybe_bag_slot, item['label'], qty))
    return None


def Dip(item_slot, potion_slot):
    def hnd(a, bh):
        game = bh.game
        update_inventory(bh)

        def message(msg):
            from .item import holy_water
            if (msg == "Interesting..."
                    and holy_water(inventory_slot(game.deref(), potion_slot))):
                game.swap(assoc_in,
                          ['player', 'inventory', item_slot, 'buc'], 'blessed')

        def dip_here(_p):
            if potion_slot == '.':
                update_tile(bh)
                return True
            return False
        return Handler(message=message, dip_what=lambda _p: item_slot,
                       dip_into_what=lambda _p: (None if potion_slot == '.'
                                                 else potion_slot),
                       dip_here=dip_here)
    return action('dip', "#dip\n", hnd, slot=item_slot, potion=potion_slot)


def examine_handler(bh):
    def choose_action(game):
        return (examine_tile(game) or examine_monsters(game)
                or examine_features(game))
    return Handler(choose_action=choose_action)


def Throw(slot, dir_):
    def hnd(a, bh):
        game = bh.game
        update_inventory(bh)
        level = curlvl(game.deref())
        player = game.deref()['player']
        prev_tile = at(level, player)
        tile = in_direction(level, player, dir_)
        while tile is not None and not (pool_p(tile) or lava_p(tile)):
            if monster_at(level, tile) or not walkable(tile):
                break
            prev_tile = tile
            tile = in_direction(level, tile, dir_)
        to_update = prev_tile if (tile is None or pool_p(tile) or lava_p(tile)
                                  or monster_at(level, tile)
                                  or not walkable(tile)) else tile
        # (if (and to-update (not (visible? game level to-update))) ...)
        # `game` here is the *atom* the handler destructured out of `bh`, not
        # its value: the original passes it to `visible?` without derefing.
        # `visible?` then destructures {:keys [player]} out of an atom (nil)
        # and calls `(get-in game [:fov …])`, which Clojure answers with nil
        # for a non-collection - so the whole `and` is nil and the guard is
        # *always* true.  Throw marks the tile unconditionally.  Reproduced,
        # not repaired: deref'ing here makes the bot skip the mark whenever
        # the target is in sight, which changes where it goes looking for
        # items afterwards (measured on seed 40002, turn 1354, tile (5,18)).
        if to_update:
            game.swap(update_at, to_update,
                      lambda t: assoc(t, 'new-items', True))
        return Handler(throw_what=lambda _p: slot,
                       what_direction=lambda _p: dir_)
    return action('throw', "t", hnd, slot=slot, dir=dir_)


def _engrave_effect(msg):
    for pat, eff in [(r"The engraving .*vanishes!", 'vanish'),
                     (r"A few ice cubes drop", 'ice'),
                     (r"The.* is riddled by bullet holes", 'bullet'),
                     (r"The bugs on the.* stop moving!", 'stop'),
                     (r"The bugs on the.* slow down", 'slow'),
                     (r"The bugs on the.* speed up", 'speed'),
                     (r"The engraving now reads", 'change'),
                     (r"fights your attempt to write", 'fights')]:
        if re_seq(pat, msg):
            return eff
    return None


EMPTY_WAND_RE = (r"You write in the dust with .*wand of "
                 r"(?:lightning|fire|digging)")


def Engrave(slot, what, append=False):
    def hnd(a, bh):
        game = bh.game
        update_tile(bh)
        if slot != '-':
            possible_autoid(bh, slot, True)
            update_inventory(bh)
            _mark_use(bh, slot)

        def message(msg):
            if re_seq(EMPTY_WAND_RE, msg):
                name_item(bh, slot, "empty")
            eff = _engrave_effect(msg)
            if eff:
                game.swap(lambda g: add_prop_discovery(
                    g, slot_appearance(g, slot), 'engrave', eff))
        return Handler(message=message,
                       append_engraving=lambda _p: bool(append),
                       write_with_what=lambda _p: slot,
                       write_what=lambda _p: what)
    return action('engrave', "E", hnd, slot=slot, what=what, append=append)


def call_id_handler(bh):
    """Automatically disambiguate items like lamp, stone, harp by calling."""
    from .itemid import ambiguous_appearance, name_for

    def choose_action(game):
        if blind(game['player']):
            return None
        found = have(game, ambiguous_appearance)
        if not found:
            return None
        slot, item = found
        n = name_for(game, item)
        if n:
            return with_reason("call item to disambiguate", Call(slot, n))
        return None
    return Handler(choose_action=choose_action)


def wish_id_handler(bh):
    wish = [None]
    slot = [None]

    def response_chosen(method, res):
        if method == 'make_wish' and res != "nothing":
            update_inventory(bh)
            wish[0] = res

    def about_to_choose(_g):
        game = bh.game
        if wish[0] and typekw(game.deref().get('last-action*')) == 'inventory':
            item = label_to_item(wish[0])
            game.swap(identify_slot, slot[0], item['name'])
            game.swap(update_slot, slot[0],
                      lambda i: assoc(i, 'buc', item.get('buc')))
            from .item import potion_p, scroll_p
            if potion_p(item) or scroll_p(item):
                name_item(bh, slot[0], "wish")
            slot[0] = None
            wish[0] = None

    def message(msg):
        if wish[0] and slot[0] is None:
            s = re_first_group(r'^([a-zA-Z]) - ', msg)
            if s:
                slot[0] = s[0]
    return Handler(response_chosen=response_chosen,
                   about_to_choose=about_to_choose, message=message)


def mark_recharge_handler(bh):
    def response_chosen(method, res):
        if method == 'charge_what':
            name_item(bh, res[0] if isinstance(res, str) else res, "recharged")
    return Handler(response_chosen=response_chosen)


def Wipe():
    def hnd(a, bh):
        def message(msg):
            if re_seq(r"Your .* is already clean|You've got the glop off", msg):
                bh.game.swap(update_in, ['player', 'state'],
                             lambda s: set(s) - {'ext-blind'})
        return Handler(message=message)
    return action('wipe', "#wipe\n", hnd)


def ZapWand(slot):
    def hnd(a, bh):
        game = bh.game
        update_inventory(bh)
        target = [False]
        charged_ = [True]

        def about_to_choose(_g):
            if charged_[0]:
                possible_autoid(bh, slot)
                game.swap(lambda g: add_prop_discovery(
                    g, slot_appearance(g, slot), 'target', target[0]))

        def what_direction(_p):
            target[0] = True
            return None

        def message(msg):
            if re_seq(r"Nothing happens", msg):
                charged_[0] = False
                item = inventory_slot(game.deref(), slot)
                if (item.get('specific') != "recharged"
                        or item_name(game.deref(), item) != "wand of wishing"):
                    name_item(bh, slot, "empty")
        return Handler(zap_what=lambda _p: slot,
                       about_to_choose=about_to_choose,
                       what_direction=what_direction, message=message)
    return action('zapwand', "z", hnd, slot=slot)


def ZapWandAt(slot, dir_):
    return with_handler(PRIORITY_BOTTOM + 1,
                        Handler(what_direction=lambda _p: dir_),
                        ZapWand(slot))


def Rub(slot):
    def hnd(a, bh):
        game = bh.game
        possible_autoid(bh, slot)

        def message(msg):
            if re_seq(r"puff of smoke", msg):
                game.swap(identify_slot, slot, "magic lamp")
            elif re_seq(r"weapon is welded to your hand", msg):
                # 3.6 dorub(): no rubbing with a welded (cursed) weapon, no
                # time passes (big-w01 g025, g046: 40 identical #rub)
                game.swap(lambda g: assoc(g, 'welded-turn', g.get('turn')))
        return Handler(rub_what=lambda _p: slot, message=message)
    return action('rub', "#rub\n", hnd, slot=slot)


def Chat(dir_):
    def hnd(a, bh):
        game = bh.game
        from .monster import priest, shopkeeper
        game.swap(recheck_peaceful_status,
                  lambda m: priest(m) or shopkeeper(m))

        def message(msg):
            if "Thy devotion has been rewarded" in msg:
                game.swap(update_in, ['player', 'protection'],
                          lambda p: (p or 0) + 1)
        return Handler(message=message)
    return action('chat', lambda a: "#chat\n" + direction_trigger(dir_), hnd,
                  dir=dir_)


def Contribute(dir_, amt):
    return with_handler(Handler(offer_how_much=lambda _p: amt), Chat(dir_))


def Pay(shk):
    def hnd(a, bh):
        return Handler(pay_whom=lambda: position(shk))
    return action('pay', "p", hnd, shk=shk)


def wield(game, slot):
    item = inventory_slot(game, slot) if has_hands(game['player']) else None
    if not item:
        return None
    from .item import cursed as _cursed
    if item.get('in-use') or _cursed(wielded_item(game) or {}):
        return None
    if two_handed(item):
        sh = have(game, shield, {'worn'})
        if sh:
            return remove_use(game, sh[0])
    return Wield(slot)
