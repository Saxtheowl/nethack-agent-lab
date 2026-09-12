"""Port of bothack.sokoban.  The solutions table is the original's, extracted
verbatim."""
import logging

from ._load import LEVELDATA
from .action import typekw
from .clj import clj_assert
from .clj import assoc, dissoc, get_in, update
from .delegator import Handler
from .position import Pos, adjacent, at, in_direction, position, towards
from .util import find_first, firstv, less_than, more_than, re_seq, secondv

log = logging.getLogger('bothack.sokoban')

# soko-tag => no. boulders => [[srcx srcy] [destx desty] ...]
solutions = LEVELDATA['soko-solutions']
initial_boulders = LEVELDATA['soko-initial-boulders']
soko_items = LEVELDATA['soko-items']

BSWITCH = Pos(30, 15)   # handles the one layout where paths have to cross


def _moves_for(src, dest):
    clj_assert(src[0] == dest[0] or src[1] == dest[1],
               'src and dest share a row or a column')
    idx = 0 if src[0] != dest[0] else 1
    step = 1 if dest[idx] > src[idx] else -1
    res = []
    cur = list(src)
    while cur != list(dest):
        res.append(Pos(cur[0], cur[1]))
        cur[idx] += step
    res.append(Pos(dest[0], dest[1]))
    return res


def _walked_in_order(lst, *tiles):
    vals = [lst if lst is not None else 0]
    defaults = [-1, -2]
    for i, t in enumerate(tiles):
        v = t.get('pushed*')
        vals.append(v if v is not None else defaults[i])
    return all(vals[i] <= vals[i + 1] for i in range(len(vals) - 1))


def _boulder_count(level):
    from .dungeon import real_boulder
    from .level import tile_seq
    return len([t for t in tile_seq(level) if real_boulder(level, t)])


def _mimic_count(game):
    from .dungeon import curlvl_monsters
    from .monster import mimic
    return len([m for m in curlvl_monsters(game) if mimic(m)])


def soko_move(game):
    from .actions import Move, Search, with_reason
    from .dungeon import (branch_key, curlvl, curlvl_tags, monster_at,
                          real_boulder)
    from .level import tile_seq
    from .pathing import navigate
    from .tile import hole_p, pit_p
    if branch_key(game) != 'sokoban':
        return None
    level = curlvl(game)
    if not any(hole_p(t) or pit_p(t) for t in tile_seq(level)):
        return None
    tag = find_first(lambda t: t in solutions, curlvl_tags(game))
    if tag is None:
        return None
    s = solutions[tag]
    player = game['player']
    last_fill = game.get('last-fill')
    boulders = _boulder_count(level)
    if 'soko-4a' in curlvl_tags(game) and real_boulder(level, BSWITCH):
        x = 100 + boulders
    else:
        x = boulders
    steps = s.get(x)
    if steps is None:
        log.debug("soko no more moves")
        return None
    pairs = [(steps[i], steps[i + 1]) for i in range(0, len(steps) - 1, 2)]
    remaining = None
    for i, (src, dest) in enumerate(pairs):
        sp, dp = Pos(src[0], src[1]), Pos(dest[0], dest[1])
        beyond = in_direction(level, dp, towards(sp, dp))
        if beyond is not None and real_boulder(level, beyond):
            continue
        if _walked_in_order(last_fill, at(level, sp), at(level, dp)):
            continue
        remaining = (src, dest)
        break
    if remaining is None:
        log.debug("soko no more moves")
        return None
    src, dest = remaining
    moves = [at(level, p) for p in _moves_for(src, dest)]
    msrc = mdest = None
    for a, b in zip(moves, moves[1:]):
        from .tile import boulder
        if not boulder(b) and _walked_in_order(last_fill, a, b):
            continue
        msrc, mdest = a, b
        break
    if msrc is None:
        log.debug("soko no more moves")
        return None
    log.debug("soko moves >>> %s", [position(m) for m in moves])
    if position(msrc) == position(player):
        monster = monster_at(game, in_direction(mdest, towards(msrc, mdest)))
        if monster is not None:
            if ((monster['glyph'] == 'I' or not monster.get('remembered'))
                    and typekw(game.get('last-action*')) == 'move'):
                return with_reason("solving soko", tag,
                                   with_reason("soko blocked by monster",
                                               Search()))
        return with_reason("solving soko", tag,
                           with_reason("push", Move(towards(msrc, mdest))))
    p = navigate(game, msrc)
    return with_reason("solving soko", tag,
                       with_reason("boulder start", p['step'] if p else None))


def soko_done(game):
    return game.get('soko-done')


def do_soko(game):
    from .actions import Attack, kick, with_reason
    from .dungeon import branch_key, curlvl_tags, monster_at
    from .monster import mimic
    from .pathing import (explore, navigate, search_level, seek_branch,
                          seek_level)
    from .position import towards, position_map
    from .tile import hole_p
    if soko_done(game):
        return None
    res = seek_branch(game, 'sokoban')
    if res is None:
        p = navigate(game, lambda t: mimic(monster_at(game, t)), {'adjacent'})
        if p:
            res = with_reason("kill mimic", p['step'] or Attack(p['step']))
    if res is None:
        p = navigate(game, lambda t: (hole_p(t) and t.get('new-items')
                                      and not t.get('thump')),
                     {'max-steps': 3, 'adjacent': True})
        if p:
            res = with_reason("free items from hole",
                              p['step'] or kick(game, towards(game['player'],
                                                              p['target'])))
    if res is None:
        res = soko_move(game)
    if res is None:
        res = explore(game)
    if res is None and 'end' in curlvl_tags(game):
        items = None
        for t in curlvl_tags(game):
            if t in soko_items:
                items = soko_items[t]
        if items:
            p = navigate(game, lambda t: (Pos(t['x'], t['y']) in items
                                          and not t.get('walked')))
            if p:
                res = p['step']
    if res is None:
        res = seek_level(game, 'sokoban', 'end')
    if res is None:
        res = search_level(game, 1)
    return with_reason("sokoban", res) if res else None


def soko_handler(bh):
    from .dungeon import (at_curlvl, branch_key, curlvl, curlvl_tags,
                          real_boulder, update_at, update_at_player)
    from .handlers import deregister_handler
    from .itemid import add_discovery, item_type
    from .itemtype import name_to_item
    from .level import tile_seq
    from .monster import mimic
    from .player import dizzy, hallu
    from .position import in_direction
    from .tile import boulder, hole_p, item as tile_item, perma_e, pit_p
    from .actions import BOULDER_PLUG_RE

    h = Handler()

    def about_to_choose(game):
        if branch_key(game) != 'sokoban':
            return
        player = game['player']
        last_state = game.get('last-state')
        last_action = game.get('last-action*')
        turnstar = game['turn*']
        if (last_state
                and not hallu(player) and not hallu(last_state['player'])
                and last_state['dlvl'] == game['dlvl']
                and _mimic_count(game) == _mimic_count(last_state)
                and any(hole_p(t) or pit_p(t) for t in tile_seq(curlvl(game)))
                and _boulder_count(curlvl(last_state))
                < _boulder_count(curlvl(game))):
            log.warning("giving up on soko")
            bh.game.swap(assoc, 'soko-done', True)
        level = curlvl(game)
        if last_state and 'soko-4a' in level['tags'] \
                and typekw(last_action) == 'move':
            a = real_boulder(curlvl(last_state), BSWITCH)
            b = real_boulder(level, BSWITCH)
            if (a and not b) or (b and not a):
                bh.game.swap(lambda g: assoc(g, 'last-fill', g['turn*'] + 1))
        if 'end' in curlvl_tags(game) and typekw(last_action) in ('autotravel',
                                                                  'move'):
            items = None
            for t in curlvl_tags(game):
                if t in soko_items:
                    items = soko_items[t]
            if items and last_state:
                if any(perma_e(at_curlvl(last_state, p)) for p in items):
                    bh.game.swap(assoc, 'soko-done', True)
                    log.warning("soko done!")
                    deregister_handler(bh, h)
        if typekw(last_action) == 'move' and last_action.get('dir'):
            dir_ = last_action['dir']
            old_tile = at_curlvl(last_state, player)
            old_player = last_state['player']
            target = in_direction(curlvl(game), player, dir_)
            if (not dizzy(old_player) and boulder(old_tile)
                    and (boulder(target) or player.get('engulfed')
                         or (hallu(player) and tile_item(target)))
                    and not boulder(at_curlvl(last_state,
                                              in_direction(old_tile, dir_)))):
                bh.game.swap(update_at_player,
                             lambda t: assoc(t, 'pushed*', turnstar))
                bh.game.swap(update_at, old_player,
                             lambda t: assoc(t, 'pushed*', turnstar))
                bh.game.swap(update_at, player,
                             lambda t: dissoc(t, 'pushed'))
                bh.game.swap(update_at, in_direction(player, dir_),
                             lambda t: assoc(t, 'pushed', True))

    def action_chosen(act):
        game = bh.game.deref()
        if ('soko-4a' in curlvl_tags(game) and typekw(act) == 'call'
                and Pos(game['player']['x'], game['player']['y'])
                in soko_items['soko-4a']):
            bh.game.swap(add_discovery, act['name'], "bag of holding")

    def found_items(found):
        game = bh.game.deref()
        if branch_key(game) != 'sokoban':
            return
        tile = at_curlvl(game, game['player'])
        if tile is None or game['turn'] != tile.get('first-walked'):
            return
        items = None
        for t in curlvl_tags(game):
            if t in soko_items:
                items = soko_items[t]
        if not items:
            return
        id_ = items.get(Pos(game['player']['x'], game['player']['y']))
        if not id_:
            return
        matching = set(i['name'] for i in (tile.get('items') or ())
                       if item_type(name_to_item[id_]) == item_type(i))
        if matching and less_than(2, matching):
            bh.game.swap(add_discovery, list(matching)[0], id_)

    def message(msg):
        game = bh.game.deref()
        if branch_key(game) == 'sokoban' and re_seq(BOULDER_PLUG_RE, msg):
            bh.game.swap(lambda g: assoc(g, 'last-fill', g['turn*'] + 1))

    h.about_to_choose = about_to_choose
    h.action_chosen = action_chosen
    h.found_items = found_items
    h.message = message
    return h
