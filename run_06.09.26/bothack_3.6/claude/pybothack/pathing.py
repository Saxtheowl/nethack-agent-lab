"""Port of bothack.pathing."""
import heapq
import logging
import os

from .action import typekw
from .actions import (Autotravel, Close, Drop, Move, Open, Read, Remove, Search,
                      Sit, TakeOff, Unlock, ZapWandAt, descend, dig, kick,
                      search, untrap_move, with_reason, without_levitation,
                      Ascend, Descend)
from .clj import clj_assert
from .clj import assoc, get_in, update
from .delegator import Handler
from .dungeon import (at_curlvl, at_planes, below_castle, below_medusa,
                      branch_key, branch_entry, curlvl, curlvl_tags,
                      diggable_walls, dlvl, dlvl_compare, dlvl_from_entrance,
                      dlvl_from_tag, dlvl_range, edge_passable_walking,
                      fake_wiztower_portal, fake_wiztower_water, get_branch,
                      get_dlvl, get_level, in_gehennom, in_maze_corridor,
                      monster_at, narrow, next_dlvl, passable_walking,
                      prev_dlvl, real_boulder, PLANES, PORTAL_BRANCHES,
                      SUBBRANCHES, upwards, dlvl_number, change_dlvl,
                      diggable_floor, BRANCHES)
from .handlers import register_handler, deregister_handler
from .item import pick, key_p
from .itemid import item_name
from .level import tile_seq, wiztower_inner_boundary
from .monster import guard, rider, shopkeeper
from .player import (have, have_key, have_levi, have_levi_on, have_mr,
                     have_pick, has_hands, weak, inventory_slot)
from .position import (Pos, adjacent, at, diagonal, diagonal_neighbors,
                       hamt_key, _NEIGHBORS,
                       distance, in_direction, including_origin, neighbors,
                       position, straight, straight_neighbors, towards)
from .tile import (altar_p, blocked, boulder, cloud_p, corridor_p,
                   diggable, door, door_closed_p, door_locked_p, door_open_p,
                   door_secret_p, drawbridge_lowered_p, dug, engravable,
                   floor_p, fountain_p, grave_p, has_feature, hole_p, ice_p,
                   item as tile_item, lava_p, monster as tile_monster,
                   pit_p, pool_p, portal_p, rock_p, searched, shop, sink_p,
                   stairs, stairs_down_p, stairs_up_p, throne_p, trap,
                   trapdoor_p, unexplored, unknown, walkable, wall_p, blank)
from .util import (find_first, first_min_by, less_than, more_than, min_by,
                   not_any_fn, some_fn, every_pred)

log = logging.getLogger('bothack.pathing')

# Tie-breaking direction in the open set.  clojure.data.priority-map keeps
# equal-priority items in a hash set, so the original's choice among equally
# good paths follows Clojure's hash order; +1 = FIFO, -1 = LIFO here.
TIE = int(os.environ.get('BOTHACK_ASTAR_TIE', '1'))


def base_cost(level, dir_, tile, opts):
    clj_assert(level is not None and dir_ is not None and tile is not None,
               'some? level, some? dir, some? tile')
    cost = 1
    if opts.get('prefer-items') and not tile.get('new-items'):
        cost += 0.5
    if (opts.get('prefer-items') and opts.get('pick') and boulder(tile)
            and tile.get('new-items')):
        cost -= 5
    if trap(tile):
        cost += 15
    if (any(t in level['tags'] for t in ('castle', 'medusa'))
            and any(pool_p(t) for t in including_origin(neighbors, level,
                                                        tile))):
        cost += 5
    if diagonal(dir_):
        cost += 0.1
    if unknown(tile) and not tile.get('seen'):
        cost += 3
    if not stairs(tile):
        cost += 0.1
    if not engravable(tile):
        cost += 0.5
    if cloud_p(tile):
        cost += 10
    if tile.get('blocked'):
        cost += 10 * tile['blocked']
    if not (tile.get('dug') or tile.get('walked')):
        cost += 0.2
    if not tile.get('walked') and floor_p(tile):
        cost += 0.5
    return cost


class _PriorityMap(object):
    """clojure.data.priority-map semantics: one entry per node, ties broken by
    Clojure's hash order, and re-adding a node with an *equal* priority
    replaces the entry (merge-with (partial min-key first))."""

    __slots__ = ('entries', 'heap', 'ver')

    def __init__(self):
        self.entries = {}
        self.heap = []
        self.ver = 0

    def put(self, node, priority, payload):
        cur = self.entries.get(node)
        if cur is not None and priority > cur[0]:
            return
        self.ver += 1
        self.entries[node] = (priority, payload, self.ver)
        heapq.heappush(self.heap, (priority, hamt_key(node), self.ver, node))

    def pop(self):
        while self.heap:
            priority, _key, ver, node = heapq.heappop(self.heap)
            e = self.entries.get(node)
            if e is not None and e[2] == ver:
                del self.entries[node]
                return node, e[0], e[1]
        return None


def _a_star(frm, to, move_fn, max_steps=None):
    """Move-fn must always return non-negative cost values, the target tile may
    not be passable but will always be included in the path."""
    log.debug("a*")
    closed = {}
    openm = _PriorityMap()
    openm.put(position(frm), 0, (0, None))
    while True:
        top = openm.pop()
        if top is None:
            return None
        node, total, (dist, prev) = top
        path = list(closed.get(prev, [])) + [node]
        delta = distance(node, to)
        if delta == 0:
            return path[1:]
        if delta == 1 and not any(move_fn(n, to) for n in neighbors(to)):
            return path[1:] + [position(to)]
        if max_steps is not None and max_steps < delta + len(path):
            return None
        closed[node] = path
        for nbr in neighbors(node):
            if nbr in closed:
                continue
            res = move_fn(node, nbr)
            if res is None:
                continue
            cost, act = res
            if act is None:
                continue
            new_dist = int(dist + cost)
            openm.put(nbr, new_dist + distance(nbr, to), (new_dist, node))


def _dijkstra(frm, goal_p, move_fn, max_steps=None):
    log.debug("dijkstra")
    closed = {}
    openm = _PriorityMap()
    openm.put(position(frm), 0, None)
    while True:
        top = openm.pop()
        if top is None:
            return None
        node, dist, prev = top
        path = list(closed.get(prev, [])) + [node]
        if goal_p(node):
            return path[1:]
        if max_steps is not None and max_steps < len(path):
            return None
        closed[node] = path
        for nbr in neighbors(node):
            if nbr in closed:
                continue
            res = move_fn(node, nbr)
            if res is None:
                continue
            cost, act = res
            if act is None:
                continue
            openm.put(nbr, dist + cost, node)


def needs_levi(tile):
    return tile.get('feature') in ('pool', 'lava', 'ice', 'hole', 'trapdoor',
                                   'cloud')


def _drop_unpaid(game):
    found = have(game, lambda i: i.get('cost'))
    if found:
        slot, item = found
        return with_reason("drop unpaid items", Drop(slot, item['qty']))
    return None


def fidget(game, level=None, target=None):
    """Move around randomly or wait to make a peaceful move out of the way."""
    from .actions import arbitrary_move
    if level is None:
        level = curlvl(game)
    player = game['player']

    def hfactory(bh):
        if not target:
            return None

        def about_to_choose(new_game):
            if altar_p(at(level, target)):
                return
            m = monster_at(new_game, target)
            if m and m.get('peaceful'):
                log.debug("blocked by peaceful %s", target)
                if not (shopkeeper(m) and shop(at_curlvl(new_game,
                                                         new_game['player']))):
                    bh.game.swap(lambda g: _update_blocked(g, target))
        return Handler(about_to_choose=about_to_choose)

    act = None
    if typekw(game.get('last-action*')) != 'pay':
        shk = find_first(lambda n: shopkeeper(monster_at(level, n)),
                         neighbors(level, player))
        if shk:
            from .actions import Pay
            act = _drop_unpaid(game) or Pay(shk)
    if act is None:
        act = arbitrary_move(game, level)
    if act is None:
        act = Search()
    from .actions import with_handler
    from .util import PRIORITY_TOP
    return with_handler(PRIORITY_TOP, hfactory,
                        with_reason("fidgeting to make peacefuls move", act))


def _update_blocked(game, target):
    from .dungeon import update_at
    return update_at(game, target,
                     lambda t: assoc(t, 'blocked', (t.get('blocked') or 0) + 1))


def safe_from_guards(level):
    return not any(guard(m) for m in level['monsters'].values())


def dare_destroy(level, tile):
    return bool(boulder(tile)
                or (('minetown' not in level['tags']
                     or safe_from_guards(level))
                    and not shop(tile)))


def likely_walkable(level, tile):
    if not walkable(tile):
        return False
    m = monster_at(level, tile)
    if m is not None and m['glyph'] != ';':
        return True
    return bool(tile.get('feature') or tile_item(tile))


def safely_walkable(level, tile):
    if tile is None:
        return False
    return (likely_walkable(level, tile)
            and not (trap(tile) or ice_p(tile) or drawbridge_lowered_p(tile)))


def _blocked_door(level, pos):
    ws = [t for t in straight_neighbors(level, pos)
          if walkable(t) and not trap(t)]
    if not ws:
        return None
    tile = at(level, pos)
    w = ws[0]
    dir_ = towards(pos, w)
    from .position import OPPOSITE
    o = in_direction(level, pos, OPPOSITE[dir_])
    if o is None:
        return None
    common = (set(position(t) for t in diagonal_neighbors(level, pos))
              & set(position(t) for t in straight_neighbors(level, o)))
    if (not tile.get('items') and len(ws) == 1
            and any(likely_walkable(level, at(level, p)) for p in common)):
        return dir_
    return None


def _kickable_door(level, tile, opts):
    return bool(door(tile) and 'rogue' not in level['tags']
                and not opts.get('walking') and dare_destroy(level, tile)
                and not tile_item(tile))


def _kick_door(game, level, tile, dir_):
    if door_open_p(tile):
        act = None if monster_at(level, tile) else Close(dir_)
        return (8, with_reason("closing door to kick it", act) if act else None)
    return (30 if game['player'].get('leg-hurt') else 6, kick(game, dir_))


def can_unlock(game):
    return has_hands(game['player'])


def _enter_shop(game):
    found = have(game, {"pick-axe", "dwarvish mattock"}, {'can-remove'})
    if found:
        return (2, with_reason("dropping pick to enter shop", Drop(found[0])))
    found = have(game, "ring of invisibility", {'can-remove', 'worn'})
    if found:
        return (2, with_reason("removing invis to enter shop",
                               Remove(found[0])))
    found = have(game, "cloak of invisibility", {'can-remove', 'worn'})
    if found:
        return (2, with_reason("taking off invis to enter shop",
                               TakeOff(found[0])))
    return None


def pass_monster(game, level, to_tile, dir_, monster, opts):
    if (monster.get('peaceful')
            or (monster.get('friendly') and diagonal(dir_) and door(to_tile))):
        if not blocked(to_tile):
            return (4 if at_planes(game) else 50,
                    with_reason("peaceful blocker", monster,
                                fidget(game, level, to_tile)))
        return None
    if monster.get('friendly'):
        if not opts.get('walking'):
            return (8, with_reason("displace friendly", monster, Move(dir_)))
        return None
    if not opts.get('no-fight'):
        # port: the Riders revive - walking "through" one is an endless fight
        # (Astral Plane); take any detour shorter than ~40 squares
        return ((40 if rider(monster) else 2) if at_planes(game) else 12,
                with_reason("pathing through hostiles", monster, Move(dir_)))
    return None


MOVE_BLOCKED_TURNS = 30
# port: a presumed secret door (blueprint guess) that 60 searches did not
# reveal is not one; BotHack searched there for 20 000 turns on the levels
# below the Wizard's Tower (big-w01: 9 of 49 games)
SECRET_DOOR_SEARCH_LIMIT = 60


def _recently_move_blocked(game, tile):
    """Port addition: a move into this square failed without using a turn
    (boulder with an unseen monster behind it, supervisor action-loop
    recovery); avoid it for a while instead of retrying forever."""
    t = tile.get('move-blocked')
    return t is not None and 0 <= (game.get('turn') or 0) - t < MOVE_BLOCKED_TURNS


def move(game, level, frm, to, opts=None):
    """Returns [cost, Action] for a move, if it is possible."""
    if opts is None:
        opts = {}
    to_tile = at(level, to)
    from_tile = at(level, frm)
    dir_ = towards(from_tile, to_tile)
    monster = monster_at(level, to)
    need_levi = ((opts.get('levi') and game['branch-id'] in ('air', 'water')
                  and walkable(to_tile)) or needs_levi(to_tile))

    res = None
    if (passable_walking(game, level, from_tile, to_tile)
            and (not opts.get('explored') or to_tile.get('new-items')
                 or to_tile.get('feature'))
            and not (_kickable_door(level, to_tile, opts)
                     and _blocked_door(level, to_tile))):
        if monster:
            res = pass_monster(game, level, to_tile, dir_, monster, opts)
        else:
            res = None
            if shop(to_tile) and not shop(from_tile):
                res = _enter_shop(game)
            if res is None:
                if not ((opts.get('levi') and need_levi)
                        or ('castle' in level['tags']
                            and position(Pos(60, 12)) == position(to_tile))
                        or (to_tile.get('feature') == 'polytrap'
                            and not have_mr(game))
                        or (branch_key(game) == 'sokoban' and hole_p(to_tile))
                        or _recently_move_blocked(game, to_tile)
                        or (opts.get('no-traps') and trap(to_tile))):
                    res = (0, Move(dir_))
    if res is None and _kickable_door(level, from_tile, opts):
        odir = _blocked_door(level, from_tile)
        if odir:
            if monster_at(level, in_direction(from_tile, odir)):
                res = (3, with_reason(
                    "waiting for monster to move to kick door at my pos",
                    Search()))
            else:
                res = (1, with_reason("moving to kick blocked door at my pos",
                                      Move(odir)))
    if (res is None and edge_passable_walking(game, level, from_tile, to_tile)
            and need_levi and not boulder(to_tile)):
        levi = opts.get('levi')
        if levi:
            slot, item = levi
            if monster:
                cm = pass_monster(game, level, to_tile, dir_, monster, opts)
            else:
                cm = (1, Move(dir_))
            if cm:
                cost, mv = cm
                if item.get('worn'):
                    res = (cost, with_reason("assuming levitation", mv))
                else:
                    from .actions import make_use
                    res = (cost + 2, with_reason("need levi for next move",
                                                 make_use(game, slot)))
    if (res is None and door(to_tile) and not opts.get('walking')
            and not opts.get('no-kick')):
        if monster:
            res = pass_monster(game, level, to_tile, dir_, monster, opts)
        if (res is None and door_secret_p(to_tile)
                and (to_tile.get('searched') or 0) < SECRET_DOOR_SEARCH_LIMIT):
            res = (10, search(10))
        if res is None and (_kickable_door(level, to_tile, opts)
                            and walkable(from_tile)
                            and _blocked_door(level, to_tile)):
            c, a = _kick_door(game, level, to_tile, dir_)
            res = (c, with_reason("the door is blocked from one side", a))
        if res is None:
            if diagonal(dir_):
                if _kickable_door(level, to_tile, opts) and walkable(from_tile):
                    res = _kick_door(game, level, to_tile, dir_)
            else:
                if door_closed_p(to_tile):
                    res = (3, Open(dir_))
                else:
                    k = (have_key(game) if (door_locked_p(to_tile)
                                            and can_unlock(game)) else None)
                    if k:
                        slot, i = k
                        if (dare_destroy(level, to_tile) or key_p(i)
                                or 'minetown' not in level['tags']):
                            res = (4, Unlock(slot, dir_))
                    elif (_kickable_door(level, to_tile, opts)
                          and walkable(from_tile)):
                        res = _kick_door(game, level, to_tile, dir_)
    if (res is None and opts.get('pick') and diggable(to_tile)
            and (boulder(to_tile) or diggable_walls(game, level))
            and dare_destroy(level, to_tile)):
        if monster:
            res = pass_monster(game, level, to_tile, dir_, monster, opts)
        elif (not game['player'].get('thick')
              or not narrow(game, level, from_tile, to_tile)):
            res = (8, dig(opts['pick'], dir_))
        else:
            res = (16, dig(opts['pick'], dir_))
    if res is None:
        return None
    cost, act = res
    if act is None:
        return None
    return (cost + base_cost(level, dir_, to_tile, opts), act)


def Path(step, path, target):
    return {'step': step, 'path': path, 'target': target}


def autonavigable(game, level, opts, edge):
    frm, to = edge
    return bool(not shop(frm)
                and not (shop(to) or trap(to) or unknown(to))
                and edge_passable_walking(game, level, frm, to)
                and not ('castle' in level['tags'] and door(frm))
                and (safely_walkable(level, to)
                     or ((pool_p(to) or ice_p(to))
                         and (opts.get('levi') or (None, {}))[1].get('worn'))))


def _autonav_target(game, frm, level, path, opts):
    from .player import wielded_item
    if (opts.get('no-autonav') or shop(at(level, frm))
            or pick(wielded_item(game) or {'name': ''})
            or typekw(game.get('last-action')) == 'autotravel'):
        return None
    path_tiles = [at(level, p) for p in path]
    steps = list(zip([at(level, frm)] + path_tiles, path_tiles))
    autonavigable_tiles = []
    for s in steps:
        if not autonavigable(game, level, opts, s):
            break
        autonavigable_tiles.append(s[1])
    target = position(autonavigable_tiles[-1]) if autonavigable_tiles else None
    if (not (game.get('autonav-stuck') and game.get('last-autonav') == target)
            and more_than(3, autonavigable_tiles)
            and not any(monster_at(level, n) for n in neighbors(frm))):
        return target
    return None


def _path_step(game, level, frm, move_fn, path, opts):
    if not path:
        return None
    start = path[0]
    act = None
    if game['player'].get('trapped'):
        act = with_reason("untrapping self", untrap_move(game, level))
    if act is None and not opts.get('no-autonav') and not weak(game['player']):
        target = _autonav_target(game, frm, level, path, opts)
        if target:
            act = Autotravel(target)
    if act is None:
        r = move_fn(frm, start)
        act = r[1] if r else None
    if act is None:
        return None
    return assoc(act, 'path', path)


def _get_a_star_path(game, level, frm, to, move_fn, opts, max_steps):
    path = _a_star(frm, to, move_fn, max_steps)
    if path is None:
        return None
    if path:
        if opts.get('adjacent'):
            return Path(_path_step(game, level, frm, move_fn, path, opts),
                        path[:-1], to)
        if len(path) == 1 or move_fn(path[-2], to):
            step = _path_step(game, level, frm, move_fn, path, opts)
            if step:
                return Path(step, path, to)
        return None
    return Path(None, [], to)


def navigate(game, pos_or_goal_fn, opts=None):
    """Shortest Path to a position or matching tile (A* or Dijkstra)."""
    if opts is None:
        opts = {}
    if isinstance(opts, (set, frozenset)):
        opts = {k: True for k in opts}
    opts = dict(opts)
    log.debug("navigating %s %s", pos_or_goal_fn, opts)
    player = game['player']
    level = curlvl(game)
    branch = branch_key(game, level)
    max_steps = opts.get('max-steps')
    levi = None
    if (not opts.get('no-levitation') and not opts.get('walking')
            and branch != 'sokoban'):
        levi = have_levi_on(game) or have_levi(game)
    pick_ = None
    if (not opts.get('walking') and not opts.get('no-dig')
            and branch != 'sokoban'):
        pick_ = have_pick(game)
    if levi:
        opts['levi'] = levi
    if pick_:
        opts['pick'] = pick_

    def move_fn(a, b):
        return move(game, level, a, b, opts)

    if isinstance(pos_or_goal_fn, (Pos, dict)) and not callable(pos_or_goal_fn):
        return _get_a_star_path(game, level, player, pos_or_goal_fn, move_fn,
                                opts, max_steps)

    if isinstance(pos_or_goal_fn, (set, frozenset, list, tuple)):
        goal_set = set(position(p) for p in pos_or_goal_fn)

        def goal_fn(p):
            return position(p) in goal_set
        goal_seq = list(pos_or_goal_fn)
        is_set = True
    else:
        def goal_fn(p):
            return pos_or_goal_fn(at(level, p))
        goal_seq = None
        is_set = False

    if opts.get('adjacent'):
        if is_set:
            gs = set()
            for p in pos_or_goal_fn:
                gs.update(position(n) for n in neighbors(p))
        else:
            gs = set()
            for t in tile_seq(level):
                if goal_fn(t):
                    gs.update(position(n) for n in neighbors(t))
        if not gs:
            return None
        if len(gs) == 1:
            return _get_a_star_path(game, level, player, next(iter(gs)),
                                    move_fn, opts, max_steps)
        path = _dijkstra(player, lambda p: p in gs, move_fn, max_steps)
        if path is None:
            return None
        last = path[-1] if path else position(player)
        return Path(_path_step(game, level, player, move_fn, path, opts), path,
                    find_first(goal_fn, neighbors(last)))

    if is_set:
        seq = list(goal_seq)
    else:
        seq = [t for t in tile_seq(level) if goal_fn(t)]
    if not seq:
        return None
    if len(seq) > 1:
        path = _dijkstra(player, goal_fn, move_fn, max_steps)
        if path is None:
            return None
        return Path(_path_step(game, level, player, move_fn, path, opts), path,
                    path[-1] if path else position(player))
    return _get_a_star_path(game, level, player, seq[0], move_fn, opts,
                            max_steps)


def isolated(level, tile):
    return all(blank(t) and unknown(t) for t in neighbors(level, tile))


def _probably_dug(level, tile):
    return bool(dug(tile)
                or (boulder(tile)
                    and more_than(2, [t for t in straight_neighbors(level, tile)
                                      if boulder(t) or corridor_p(t)])))


def _explorable_tile(level, tile):
    if _probably_dug(level, tile):
        return False
    if unknown(tile) and not blank(tile):
        return not isolated(level, tile)
    if tile.get('new-items'):
        return not isolated(level, tile)
    if (not tile.get('walked')
            and (grave_p(tile) or throne_p(tile) or sink_p(tile)
                 or altar_p(tile) or fountain_p(tile))):
        return not isolated(level, tile)
    if ((walkable(tile) or door(tile) or needs_levi(tile))
            and any(lava_p(t) or pool_p(t) or boulder(t) or trap(t)
                    or safely_walkable(level, t)
                    for t in neighbors(level, tile))
            and any(not (t.get('seen') or boulder(t) or blocked(t))
                    for t in neighbors(level, tile))):
        return not isolated(level, tile)
    return False


_EXPLORABLE_MEMO = {}
_MEMO_CHECK = os.environ.get('BOTHACK_MEMO_CHECK') == '1'


def explorable_tile(level, tile):
    """Memoized `_explorable_tile`.  Its result depends only on the tile, its
    eight neighbours and the monsters standing on those neighbours; tiles are
    persistent (every update makes a new dict), so identity of those objects
    is a sound cache key.  The entry keeps references to the objects, so an
    id can never be reused while the entry exists."""
    xy = (tile['x'], tile['y'])
    npos = _NEIGHBORS[xy]
    tiles = level['tiles']
    nbrs = tuple(tiles[p.y - 1][p.x] for p in npos)
    mons = level.get('monsters') or {}
    mkey = tuple((m['glyph'] if m is not None else None)
                 for m in (mons.get(p) for p in npos)) if mons else ()
    ent = _EXPLORABLE_MEMO.get(xy)
    if (ent is not None and ent[0] is tile and ent[3] == mkey
            and all(a is b for a, b in zip(ent[1], nbrs))):
        if _MEMO_CHECK:
            real = _explorable_tile(level, tile)
            if real != ent[2]:
                log.error("explorable_tile memo mismatch at %s", xy)
            return real
        return ent[2]
    r = _explorable_tile(level, tile)
    _EXPLORABLE_MEMO[xy] = (tile, nbrs, r, mkey)
    return r


def dead_end_p(level, tile):
    if not likely_walkable(level, tile):
        return False
    if trap(tile) or tile.get('dug'):
        return False
    for d in diagonal_neighbors(level, tile):
        if (((d['glyph'] == '*' and d.get('color') is None)
             or (d.get('items') and all(i['name'] == "rock"
                                        for i in d['items']))
             or corridor_p(d) or boulder(d))
                and not any(likely_walkable(level, s)
                            for s in straight_neighbors(level, d))):
            return False
    if in_maze_corridor(level, tile):
        return False
    snbr = straight_neighbors(level, tile)
    return bool((any(walkable(t) for t in snbr)
                 or not any(walkable(t) for t in neighbors(level, tile)))
                and len([t for t in snbr
                         if not (rock_p(t) or wall_p(t))]) < 2)


def _has_dead_ends(game, level):
    return bool(not any(t in level['tags']
                        for t in ('bigroom', 'juiblex', 'sanctum'))
                and not in_gehennom(game)
                and (branch_key(game, level) not in SUBBRANCHES
                     or 'minetown' in level['tags']))


def _search_dead_end(game, num_search):
    level = curlvl(game)
    tile = at(level, game['player'])
    if (_has_dead_ends(game, level) and tile['searched'] < num_search
            and dead_end_p(level, tile)):
        return with_reason("searching dead end", search(10))
    return None


def _pushable_through(game, level, frm, to):
    return bool(((walkable(to) or pool_p(to) or lava_p(to))
                 or (not boulder(to) and unknown(to)))
                and (straight(towards(frm, to))
                     or (branch_key(game) != 'sokoban'
                         and not door_open_p(frm) and not door_open_p(to))))


def _pushable_from(game, level, pos):
    if branch_key(game) == 'earth':
        return None
    tile = at(level, pos)
    if tile is None:
        return None
    if needs_levi(tile) and not ice_p(tile):
        return None
    res = []
    for n in neighbors(level, pos):
        if not boulder(n):
            continue
        dir_ = towards(pos, n)
        dest = in_direction(level, n, dir_)
        if (dest is not None
                and (straight(dir_) or branch_key(game, level) != 'sokoban')
                and not monster_at(level, dest)
                and edge_passable_walking(game, level, tile, n)
                and _pushable_through(game, level, n, dest)):
            res.append(n)
    return res or None


def _blocking_boulder(level, tile):
    return bool(boulder(tile)
                and (explorable_tile(level, tile)
                     or not (corridor_p(tile) or floor_p(tile) or ice_p(tile))
                     or not all(likely_walkable(level, t)
                                for t in neighbors(level, tile))))


def _unblocked_boulder(game, level, tile):
    for n in neighbors(level, tile):
        if (safely_walkable(level, in_direction(level, tile,
                                                towards(n, tile)))
                and not monster_at(level, n)
                and _pushable_through(game, level, tile, n)):
            return True
    return False


def _push_boulders(game, level):
    player = game['player']
    if any(_blocking_boulder(level, t) and _unblocked_boulder(game, level, t)
           for t in tile_seq(level)):
        path = navigate(game, lambda t: _pushable_from(game, level, t))
        if path:
            if path['step']:
                return with_reason("going to push a boulder", path['step'])
            pf = _pushable_from(game, level, player)
            if pf:
                return with_reason("going to push a boulder",
                                   without_levitation(
                                       game, Move(towards(player, pf[0]))))
        return None
    log.debug("no boulders to push")
    return None


def _recheck_dead_ends(game, level, howmuch):
    if not _has_dead_ends(game, level):
        return None
    p = navigate(game, lambda t: (searched(level, t) < howmuch
                                  and dead_end_p(level, t)))
    if p:
        return with_reason("re-checking dead ends", p['step'] or search(10))
    return None


def _searchable_position(pos):
    return 2 < pos['y'] < 20 and 1 < pos['x'] < 78


def _wall_end(level, tile):
    if not wall_p(tile) or not (0 < tile['x'] < 80) or not (0 < tile['y'] < 22):
        return False
    return not ((wall_p(at(level, tile['x'] - 1, tile['y']))
                 and wall_p(at(level, tile['x'] + 1, tile['y'])))
                or (wall_p(at(level, tile['x'], tile['y'] - 1))
                    and wall_p(at(level, tile['x'], tile['y'] + 1))))


def _searchable_wall(level, howmuch, tile):
    if not (_searchable_position(tile) and wall_p(tile)
            and tile['searched'] < howmuch):
        return False
    if level['branch-id'] == 'wiztower':
        if position(tile) in wiztower_inner_boundary:
            return False
    elif 'sanctum' in level['tags']:
        from .tile import firetrap_p
        if len([t for t in straight_neighbors(level, tile)
                if firetrap_p(t)]) != 1:
            return False
    elif shop(tile):
        return False
    if _wall_end(level, tile):
        return False
    return bool(howmuch >= 45
                or [t for t in straight_neighbors(level, tile)
                    if not t.get('seen')])


def _search_walls(game, level, howmuch):
    p = navigate(game, lambda t: _searchable_wall(level, howmuch, t),
                 {'adjacent'})
    if p:
        return with_reason("searching walls", p['step'] or search(10))
    return None


def _search_corridors(game, level, howmuch):
    def pred(tile):
        return ((corridor_p(tile) or door(tile))
                and _searchable_position(tile)
                and searched(level, tile) < howmuch)
    p = navigate(game, pred)
    if p:
        return with_reason("searching corridors", p['step'] or search(10))
    return None


def _searchable_extremity(level, y, xs, howmuch):
    tile = find_first(lambda t: likely_walkable(level, t),
                      [at(level, x, y) for x in xs])
    if tile is None:
        return None
    if (floor_p(tile) and tile['searched'] < howmuch
            and at(level, tile['x'] - 1, tile['y'])['glyph'] != '-'
            and at(level, tile['x'] + 1, tile['y'])['glyph'] != '-'
            and not shop(tile)):
        return tile
    return None


def unexplored_columns(game, level):
    if (branch_key(game, level) in ('mines', 'main')
            and not in_gehennom(game) and 'castle' not in level['tags']):
        return [x for x in (17, 20, 40, 60, 63)
                if not any(at(level, x, y).get('feature')
                           for y in range(2, 19))]
    return []


def unexplored_column(game, level):
    cols = unexplored_columns(game, level)
    return cols[0] if cols else None


def _corridor_extremities(level, init_cols, howmuch):
    for x in init_cols:
        col = column(level, x) if False else [at(level, x, y)
                                              for y in range(1, 22)]
        if any(not (unknown(t) or corridor_p(t) or rock_p(t)) for t in col):
            return None
        corridors = [t for t in col if corridor_p(t)]
        if corridors:
            return [t for t in corridors if t['searched'] < howmuch]
    return None


def _unsearched_extremities(game, level, howmuch):
    col = unexplored_column(game, level)
    if col is None:
        return None
    res = set()
    for y in range(1, 21):
        t = _searchable_extremity(level, y, range(col, 80), howmuch)
        if t:
            res.add(position(t))
        t = _searchable_extremity(level, y, range(col, -1, -1), howmuch)
        if t:
            res.add(position(t))
    for tiles in (_corridor_extremities(level, range(col, -1, -1), howmuch),
                  _corridor_extremities(level, range(col, 80), howmuch)):
        for t in (tiles or ()):
            res.add(position(t))
    return res


def at_level(game, level):
    return (level is not None and game['dlvl'] == level['dlvl']
            and branch_key(game) == branch_key(game, level))


def _curlvl_exploration(game):
    step = explore_step(game)
    if step is not None:
        return step
    return sum(t['searched'] for t in tile_seq(curlvl(game))) + 1


class LazyExploration(object):
    """The original computes the exploration cache in a Clojure `future`
    started in about-to-choose.  Computing it synchronously on every decision
    cost 60% of the bot's time; this computes it from the same immutable game
    snapshot, but only when something reads it."""
    __slots__ = ('_game', '_value', '_done')

    def __init__(self, game):
        self._game = game
        self._value = None
        self._done = False

    def value(self):
        if not self._done:
            self._value = _curlvl_exploration(self._game)
            self._done = True
            self._game = None
        return self._value


def explore_cache(game):
    c = game.get('explore-cache')
    if isinstance(c, LazyExploration):
        return c.value()
    return c


def exploration_index(game, branch=None, tag_or_dlvl=None):
    if branch is None:
        n = explore_cache(game)
        if isinstance(n, (int, float)):
            return n
        return 0
    level = get_level(game, branch, tag_or_dlvl)
    if level is None:
        return 0
    if at_level(game, level):
        return exploration_index(game)
    return level.get('explored') or 0


def reset_exploration(bh):
    loc = [None]
    save = [False]

    def dlvl_changed(_o, _n):
        save[0] = True

    def action_chosen(act):
        if typekw(act) in ('call', 'name', 'discoveries', 'inventory', 'look',
                           'farlook'):
            return
        if bh.game.deref().get('explore-cache') is not None:
            if save[0]:
                from .clj import assoc_in as _ai
                bh.game.swap(lambda g: _ai(
                    g, ['dungeon', 'levels', branch_key(g, loc[0][0]),
                        loc[0][1], 'explored'], exploration_index(g)))
            bh.game.swap(assoc, 'explore-cache', None)

    def about_to_choose(game):
        loc[0] = [game['branch-id'], game['dlvl']]
        bh.game.swap(assoc, 'explore-cache', LazyExploration(game))
    return Handler(dlvl_changed=dlvl_changed, action_chosen=action_chosen,
                   about_to_choose=about_to_choose)


def _search_extremities(game, level, howmuch):
    if not _has_dead_ends(game, level):
        return None
    goals = _unsearched_extremities(game, level, howmuch)
    if goals:
        p = navigate(game, goals)
        if p:
            return with_reason("searching extremity", p.get('target') or "here",
                               p['step'] or search(10))
    return None


def go_down(game, level):
    p = navigate(game, lambda t: trapdoor_p(t) or hole_p(t),
                 {'max-steps': 15, 'walking': True})
    if p:
        return with_reason("going to a trapdoor/hole",
                           p['step'] or descend(game))
    pick_ = have_pick(game) if diggable_floor(level) else None
    if pick_:
        def pred1(t):
            return (t.get('feature') in ('pit', 'floor')
                    and not any(pool_p(n) for n in neighbors(level, t))
                    and any(wall_p(n) for n in diagonal_neighbors(level, t))
                    and more_than(1, [n for n in straight_neighbors(level, t)
                                      if wall_p(n)]))

        def pred2(t):
            return (t.get('feature') in ('pit', 'floor', 'corridor')
                    and not any(pool_p(n) for n in neighbors(level, t))
                    and more_than(2, [n for n in straight_neighbors(level, t)
                                      if safely_walkable(level, n)]))
        p = navigate(game, pred1) or navigate(game, pred2)
        if p:
            if p['step']:
                return with_reason("finding somewhere to dig down", p['step'])
            return with_reason("digging down",
                               without_levitation(game, dig(pick_, '>')))
        return None
    if (diggable_floor(curlvl(game))
            and at_curlvl(game, game['player']).get('feature') in ('floor',
                                                                   'corridor')):
        found = have(game, "wand of digging", {'bagged'})
        if found:
            from .actions import unbag
            slot, item = found
            return unbag(game, slot, item) or ZapWandAt(slot, '>')
    return None


def seek_portal(game):
    level = curlvl(game)
    p = navigate(game, portal_p)
    if p:
        r = p['step'] or with_reason("sitting on a portal",
                                     without_levitation(game, Sit()))
        if r:
            return with_reason("seeking portal", r)
    if branch_key(game) == 'air':
        p = navigate(game, lambda t: (not t.get('walked') and not cloud_p(t)
                                      and t['x'] > 44))
        if p and p['step']:
            return with_reason("seeking portal",
                               with_reason("seeking :air portal", p['step']))
    if branch_key(game) == 'water':
        def portal_spot(tile):
            return (game['turn'] - (tile.get('walked') or 0) > 250
                    and 3 < tile['y'] < 17
                    and ((40 < tile['x'] < 74) if game['turn'] % 100 > 49
                         else (5 < tile['x'] < 40)))
        p = navigate(game, lambda t: t['glyph'] != '}' and portal_spot(t))
        if p and p['step']:
            return with_reason("seeking portal", p['step'])
        p = navigate(game, portal_spot)
        if p and p['step']:
            return with_reason("seeking portal", p['step'])
    if dlvl(game) > 35:
        if not at(level, fake_wiztower_portal).get('walked'):
            p = navigate(game, fake_wiztower_portal)
            if p and p['step']:
                return with_reason("seeking fake wiztower portal", p['step'])
    else:
        p = navigate(game, lambda t: (likely_walkable(level, t)
                                      and not isolated(level, t)
                                      and not cloud_p(t)
                                      and not corridor_p(t)
                                      and not t.get('walked')
                                      and not door(t)))
        if p and p['step']:
            return with_reason("stepping everywhere to find portal", p['step'])
    return explore(game) or search_level(game)


def unstuck(game):
    from .actions import unbag
    found = have(game, "scroll of teleportation", {'bagged'})
    if found:
        slot, item = found
        return with_reason("unstuck", unbag(game, slot, item) or Read(slot))
    found = have(game, "wand of teleportation", {'bagged'})
    if found:
        slot, item = found
        return with_reason("unstuck",
                           unbag(game, slot, item) or ZapWandAt(slot, '.'))
    return with_reason("unstuck", go_down(game, curlvl(game)))


def search_level(game, max_iter=None):
    if max_iter is None:
        res = search_level(game, 3)
        if res:
            return res
        res = unstuck(game)
        if res:
            return res
        res = search_level(game, 6)
        if res:
            return res
        raise RuntimeError("stuck :-(")
    level = curlvl(game)
    mul = 1
    while True:
        log.debug("search iteration %s", mul)
        if mul == 1 and (branch_key(game) != 'sokoban'
                         or not any(hole_p(t) or pit_p(t)
                                    for t in tile_seq(curlvl(game)))):
            r = _push_boulders(game, level)
            if r:
                return with_reason("searching - max-iter =", max_iter, r)
        if branch_key(game) == 'water':
            r = seek_portal(game)
            if r:
                return with_reason("searching - max-iter =", max_iter, r)
        if dlvl(game) > 43 and 'sanctum' not in curlvl_tags(game):
            p = navigate(game, lambda t: (5 < t['x'] < 75 and 6 < t['y'] < 17
                                          and not t.get('walked')
                                          and not wall_p(t)))
            if p and p['step']:
                return with_reason("searching - max-iter =", max_iter,
                                   with_reason("no stairs, possibly :main :end",
                                               p['step']))
        for f in (lambda: _recheck_dead_ends(game, level, min(mul * 30, 50)),
                  lambda: _search_extremities(game, level, mul * 20),
                  lambda: (_search_corridors(game, level, mul * 5)
                           if mul > 1 else None),
                  lambda: _search_walls(game, level, mul * 15)):
            r = f()
            if r:
                return with_reason("searching - max-iter =", max_iter, r)
        if mul > max_iter - 1:
            return None
        mul += 1


def seek(game, smth, opts=None):
    if opts is None:
        opts = {}
    if isinstance(opts, (set, frozenset)):
        opts = {k: True for k in opts}
    p = navigate(game, smth, opts)
    if p is not None:
        # (if-let [{:keys [step]} (navigate ...)] ...) - a Path with a nil step
        # makes seek return nil, it does NOT fall through to exploring
        return with_reason("seek going directly", p['step'])
    res = None
    if not opts.get('no-explore'):
        res = explore(game)
    if res is None and opts.get('go-down'):
        res = with_reason("can't find downstairs", go_down(game, curlvl(game)))
    if res is None:
        res = search_level(game)
    return with_reason("seeking", res) if res else None


def _tile_member(tiles):
    """`(set tiles)` used as a predicate, which is what Clojure does here.

    The original writes `(seek game (set (straight-neighbors level leader)) ...)`
    and relies on a PersistentHashSet being callable: it tests membership.
    Translating `set` literally raises `TypeError: unhashable type: 'dict'`,
    because a tile is a dict in this port and dicts are not hashable, while
    Clojure maps are.  That crash killed a 4h22 game at Dlvl 29 and ten others -
    always the long ones, because this path is only reached on the quest level
    with a leader still to greet.

    Membership in Clojure is *structural* equality against the tiles as they
    were when the set was built, so the snapshot is taken here and compared with
    `==`, which is structural for dicts.  A tile that has since changed - the
    hero walked onto it, say - no longer matches, exactly as upstream.
    """
    snapshot = [dict(t) for t in tiles]
    return lambda t: any(t == s for s in snapshot)


def _switch_dlvl(game, new_dlvl):
    if game['dlvl'] == new_dlvl or new_dlvl is None:
        return None
    if game['dlvl'] == "Home 1":
        level = curlvl(game)
        leader = get_in(level, ['blueprint', 'leader'])
        if leader and not any(t.get('walked')
                              for t in straight_neighbors(level, leader)):
            return with_reason(
                "switching within branch to", new_dlvl,
                with_reason("trying to seek out quest leader at", leader,
                            "before descending",
                            seek(game, _tile_member(
                                     straight_neighbors(level, leader)),
                                 {'explored': True})))
    branch = branch_key(game)
    level = curlvl(game)
    if dlvl_compare(game['dlvl'], new_dlvl) > 0:
        stairs_f, act = 'stairs-up', Ascend()
    else:
        stairs_f = 'trapdoor' if 'castle' in level['tags'] else 'stairs-down'
        act = descend(game)
    step = None
    if (stairs_f == 'stairs-down'
            and ('medusa' in level['tags'] or below_medusa(game))
            and not below_castle(game)):
        step = with_reason("dive", go_down(game, level))
    if step is None:
        def pred(t):
            if not has_feature(t, stairs_f):
                return False
            b = branch_key(game, t)
            if b:
                return b == branch or b not in BRANCHES
            return True
        step = with_reason("looking for the", stairs_f,
                           seek(game, pred,
                                {'go-down': True}
                                if stairs_f == 'stairs-down' else {}))
    return with_reason("switching within branch to", new_dlvl, step or act)


def _escape_branch(game):
    levels = get_branch(game)
    branch = branch_key(game)
    d = game['dlvl']
    if upwards(branch):
        stairs_f, stair_action = 'stairs-down', descend(game)
    else:
        stairs_f, stair_action = 'stairs-up', Ascend()
    from .dungeon import branch_keys
    keys = branch_keys(game, branch)
    if ((keys and d == keys[0] and branch in PORTAL_BRANCHES)
            or branch in PLANES):
        r = seek_portal(game)
        if r:
            return with_reason("escaping subbranch", branch, r)
    r = with_reason("seeking stairs",
                    seek(game, lambda t: has_feature(t, stairs_f)))
    if r:
        return with_reason("escaping subbranch", branch, r)
    return with_reason("escaping subbranch", branch,
                       with_reason("using stairs", stair_action))


def _least_explored(game, branch, dlvls):
    curdlvl = curlvl(game)['dlvl'] if branch == branch_key(game) else None

    def key(d):
        res = exploration_index(game, branch, d)
        if d == curdlvl and res > 0:
            return max(1, res - 1000)
        return res
    return first_min_by(key, dlvls)


def _possibly_oracle(game, d):
    level = get_level(game, 'main', d)
    if level is None:
        return True
    return not any(corridor_p(at(level, x, y))
                   for y in (7, 8, 14, 15) for x in range(34, 45))


def _possibly_wiztower(game, d):
    level = get_level(game, 'main', d)
    if level is None:
        return True
    if any(t in level['tags'] for t in ('wiztower-level', 'orcus', 'asmodeus',
                                        'juiblex', 'baalzebub')):
        return None
    return less_than(5, [t for t in [at(level, p) for p in fake_wiztower_water]
                         if not (unknown(t) or pool_p(t))])


def visited(game, branch, dlvl_or_tag=None):
    if dlvl_or_tag is None:
        return get_branch(game, branch)
    return get_level(game, branch, dlvl_or_tag)


def _first_unvisited(game, dlvls):
    for d in dlvls:
        if not visited(game, 'main', d):
            return d
    return None


def _vlad_range(game):
    vlad = dlvl_from_tag(game, 'main', 'votd', 9)
    if vlad:
        return dlvl_range('main', vlad, 5)
    return dlvl_range('main', "Dlvl:34", 9)


def _double_stairs(game, stairs_p, d):
    level = get_level(game, 'main', d)
    if level is None:
        return False
    return bool(more_than(1, [t for t in tile_seq(level) if stairs_p(t)]))


def dlvl_candidate(game, branch, tag=None):
    if tag is None:
        e = branch_entry(game, branch)
        if e:
            return e
        if branch == 'wiztower':
            for level in (get_branch(game, 'main') or {}).values():
                if ('fake-wiztower' in level['tags']
                        and not at(level, fake_wiztower_portal).get('walked')):
                    return level['dlvl']
        elif branch == 'vlad':
            r = find_first(lambda d: _double_stairs(game, stairs_up_p, d),
                           _vlad_range(game))
            if r:
                return r
        elif branch == 'sokoban':
            r = find_first(lambda d: _double_stairs(game, stairs_up_p, d),
                           dlvl_range('main', "Dlvl:6", 5))
            if r:
                return r
            oracle = get_dlvl(game, 'main', 'oracle')
            if oracle:
                return next_dlvl('main', oracle)
            return dlvl_candidate(game, 'main', 'oracle')
        elif branch == 'quest':
            r = _first_unvisited(game, dlvl_range('main', "Dlvl:11", 8))
            if r:
                return r
        elif branch == 'mines':
            r = find_first(lambda d: _double_stairs(game, stairs_down_p, d),
                           dlvl_range('main', "Dlvl:2", 3))
            if r:
                return r
        if branch == 'wiztower':
            end = get_dlvl(game, 'main', 'end')
            gh = get_dlvl(game, 'main', 'gehennom')
            if end:
                rng = dlvl_range('main', change_dlvl(lambda n: n - 4, end), 4)
            elif gh:
                rng = dlvl_range('main', change_dlvl(lambda n: n + 15, gh), 8)
            else:
                rng = dlvl_range('main', "Dlvl:40", 12)
            cand = [d for d in rng if _possibly_wiztower(game, d)]
        elif branch == 'vlad':
            cand = _vlad_range(game)
        elif branch == 'mines':
            cand = dlvl_range('main', "Dlvl:2", 3)
        else:
            cand = dlvl_range('main')
        return _least_explored(game, 'main', cand)
    # with tag
    if tag in SUBBRANCHES:
        r = dlvl_candidate(game, tag)
        if r:
            return r
    r = get_dlvl(game, branch, tag)
    if r:
        return r
    if not get_branch(game, branch):
        r = dlvl_candidate(game, branch)
        if r:
            return r
    if tag in ('end', 'votd', 'gehennom', 'castle'):
        from .dungeon import branch_keys
        keys = branch_keys(game, branch)
        if keys:
            return next_dlvl(branch, keys[-1])
    if tag == 'rogue':
        r = _first_unvisited(game, dlvl_range('main', "Dlvl:15", 4))
        if r:
            return r
    elif tag == 'medusa':
        castle = get_dlvl(game, 'main', 'castle')
        rng = []
        for d in dlvl_range('main', "Dlvl:21", 8):
            if d == castle:
                break
            rng.append(d)
        r = _first_unvisited(game, rng) or _least_explored(game, 'main', rng)
        if r:
            return r
    if tag == 'oracle':
        cand = [d for d in dlvl_range('main', "Dlvl:5", 5)
                if _possibly_oracle(game, d)]
    elif tag == 'minetown':
        cand = dlvl_range('mines', dlvl_from_entrance(game, 'mines', 3), 2)
    else:
        cand = dlvl_range(branch)
    return _least_explored(game, branch, cand)


def _enter_branch(game, branch):
    if branch_key(game) != 'main':
        return explore(game) or search_level(game)
    branch = branch_key(game, branch)
    if upwards(branch) or branch in PLANES:
        stairs_f, stair_action = 'stairs-up', Ascend()
    else:
        stairs_f, stair_action = 'stairs-down', descend(game)
    new_dlvl = dlvl_candidate(game, branch)
    res = _switch_dlvl(game, new_dlvl)
    if res is None and branch in PORTAL_BRANCHES:
        res = seek_portal(game)
    if res is None:
        res = seek(game, lambda t: (has_feature(t, stairs_f)
                                    and branch_key(game, t) != 'main'))
    if res is None:
        res = stair_action
    return with_reason("trying to enter", branch, "from", new_dlvl, res)


def seek_branch(game, new_branch_id):
    new_branch = branch_key(game, new_branch_id)
    level = curlvl(game)
    branch = branch_key(game, level)
    if branch != new_branch:
        if branch in SUBBRANCHES:
            res = _escape_branch(game)
        else:
            res = _enter_branch(game, new_branch)
        return with_reason("seeking branch", new_branch_id, "(", new_branch,
                           ")", res) if res else None
    return None


def seek_level(game, new_branch_id, tag_or_dlvl):
    level = curlvl(game)
    branch = branch_key(game, level)
    new_branch = branch_key(game, new_branch_id)
    new_level = get_level(game, new_branch, tag_or_dlvl)
    from .dungeon import is_tag
    if branch == new_branch:
        if new_level:
            res = _switch_dlvl(game, new_level['dlvl'])
        elif is_tag(tag_or_dlvl):
            res = _switch_dlvl(game, dlvl_candidate(game, new_branch,
                                                    tag_or_dlvl))
            if res is None and tag_or_dlvl in SUBBRANCHES:
                res = seek_branch(game, tag_or_dlvl)
            if res is None:
                res = with_reason("exploring dlvl candidate", explore(game))
            if res is None:
                res = with_reason("searching dlvl candidate",
                                  search_level(game))
        else:
            res = _switch_dlvl(game, tag_or_dlvl)
    else:
        res = seek_branch(game, new_branch)
    return with_reason("seeking level", new_branch_id, tag_or_dlvl,
                       res) if res else None


def explored(game, branch=None, tag_or_dlvl=None):
    if branch is None:
        return exploration_index(game) > 0
    if tag_or_dlvl is None:
        tag_or_dlvl = 'end'
    return exploration_index(game, branch, tag_or_dlvl) > 0


def _shallower_unexplored(game, branch, tag_or_dlvl=None):
    if tag_or_dlvl is None:
        if branch_key(game, branch) == 'main':
            t = 'end'
        else:
            d = get_dlvl(game, 'main', branch)
            t = next_dlvl('main', d) if d else branch
        return _shallower_unexplored(game, 'main', t)
    branch = branch_key(game, branch)
    start = None
    if branch == 'main' and not have_levi(game):
        if below_castle(game):
            start = get_dlvl(game, 'main', 'castle')
        elif below_medusa(game):
            start = get_dlvl(game, 'main', 'medusa')
    if start is None:
        from .dungeon import branch_keys
        keys = branch_keys(game, branch)
        start = keys[0] if keys else None
    d = get_dlvl(game, branch, tag_or_dlvl)
    if d is None:
        if branch == branch_key(game):
            d = next_dlvl(branch, game['dlvl'])
        else:
            from .dungeon import branch_keys
            keys = branch_keys(game, branch)
            d = next_dlvl(keys[-1]) if keys else None
    if start and d and dlvl_compare(branch, start, d) < 0:
        cur = start
        while cur != d:
            if not explored(game, branch, cur):
                return cur
            cur = next_dlvl(branch, cur)
    return None


def explore_level(game, branch, tag_or_dlvl):
    if not explored(game, branch, tag_or_dlvl):
        return seek_level(game, branch, tag_or_dlvl) or explore(game)
    return None


def _center_explored(level):
    return any(at(level, 40, y).get('feature') for y in range(5, 15))


def _search_limit(game, level):
    if 'minetown' in level['tags'] and _center_explored(level):
        return 1
    if branch_key(game) == 'mines':
        return 10
    if more_than(1, unexplored_columns(game, level)):
        return 2
    return 1


def explore_step(game):
    player = game['player']
    level = curlvl(game)
    branch = branch_key(game, level)
    r = _search_dead_end(game, 20)
    if r:
        return r
    if 'sanctum' in level['tags'] and not at_curlvl(game, 20, 10).get('walked'):
        r = seek(game, Pos(20, 10), {'no-explore': True})
        if r:
            return with_reason("searching sanctum", r)
    path = navigate(game, lambda t: explorable_tile(level, t),
                    {'prefer-items'})
    if path and path['step']:
        return with_reason("exploring", at(level, path['target']),
                           path['step'])
    if (unexplored_column(game, level) is not None
            and not ('medusa' in level['tags'] and not have_levi(game))):
        r = search_level(game, _search_limit(game, level))
        if r:
            return with_reason("level not explored enough, searching", r)
    if branch != 'sokoban':
        bldrs = [t for t in tile_seq(level)
                 if boulder(t) and explorable_tile(level, t)]
        if bldrs:
            path = navigate(game, lambda t: (
                any(adjacent(t, b) for b in bldrs)
                and _pushable_from(game, level, t)))
            if path:
                if path['step']:
                    return with_reason("going to push an explorable boulder",
                                       path['step'])
                pf = _pushable_from(game, level, player)
                if pf:
                    return with_reason(
                        "going to push an explorable boulder",
                        without_levitation(game,
                                           Move(towards(player, pf[0]))))
    if (branch == 'wiztower' and 'end' in curlvl_tags(game)
            and unknown(at_curlvl(game, 40, 11))):
        r = seek(game, Pos(40, 11), {'no-explore': True})
        if r:
            return with_reason("searching wiztower top", r)
    log.debug("nothing to explore")
    return None


def explore(game, branch=None, tag_or_dlvl=None, exclusive=False):
    if branch is None:
        if not exploration_index(game) > 0:
            cache = explore_cache(game)
            if cache is not None and not isinstance(cache, (int, float)):
                return with_reason("using cached exploration step", cache)
            return with_reason("using cached exploration step",
                               explore_step(game))
        return None
    if tag_or_dlvl is None:
        tag_or_dlvl = 'end'
    res = None
    if branch_key(game, branch) != 'main':
        l = _shallower_unexplored(game, branch)
        if l:
            res = with_reason("first exploring main until branch entrance",
                              explore_level(game, 'main', l))
    from .rules36 import fast_profile
    if res is None and not (fast_profile()
                            and branch_key(game, branch) == 'main'):
        l = _shallower_unexplored(game, branch, tag_or_dlvl)
        if l:
            res = with_reason("first exploring previous levels of branch",
                              explore_level(game, branch, l))
    if res is None and not (exclusive or explored(game, branch, tag_or_dlvl)):
        res = with_reason("reaching exploration target",
                          explore_level(game, branch, tag_or_dlvl))
    if res is None:
        log.debug("all explored")
        return None
    return with_reason("exploring", branch, "until", tag_or_dlvl, res)


def visit(game, branch, tag_or_level=None):
    if tag_or_level is None:
        if not visited(game, branch):
            return seek_branch(game, branch)
        return None
    if not visited(game, branch, tag_or_level):
        return seek_level(game, branch, tag_or_level)
    return None


def nav_targets(coll):
    return set(position(x) for x in coll)


def branch_map(game):
    """{dlvl of entrance in :main => branch} for 'standard' branches"""
    res = {}
    for branch in ('mines', 'sokoban', 'quest', 'wiztower', 'vlad'):
        entry = branch_entry(game, branch)
        if entry:
            res[entry] = branch
    return res


def _neighbor_levels(game, level, bmap, opts):
    branch = branch_key(game, level)
    d = level['dlvl']
    res = []
    if not (not have_levi(game)
            and (('medusa' in level['tags'] and below_medusa(game))
                 or ('castle' in level['tags'] and below_castle(game)))):
        res.append(get_level(game, branch, prev_dlvl(branch, d)))
    from .dungeon import branch_keys
    if branch != 'main':
        keys = branch_keys(game, branch)
        if keys and d == keys[0]:
            res.append(get_level(game, 'main', branch_entry(game, branch)))
    if branch == 'main' and not opts.get('up'):
        b = bmap.get(d)
        if b:
            sub = get_branch(game, b)
            if sub:
                keys = branch_keys(game, b)
                res.append(sub[keys[0]])
    if not opts.get('up'):
        res.append(get_level(game, branch, next_dlvl(branch, d)))
    return [l for l in res if l]


def level_seq(game, opts=None):
    """Levels by unit distance from the current one."""
    if opts is None:
        opts = {}
    bmap = branch_map(game)

    def levid(l):
        return (l['dlvl'], l.get('branch-id'))
    start = _neighbor_levels(game, curlvl(game), bmap, opts)
    queue = list(start)
    closed = set(levid(l) for l in start) | {(game['dlvl'],
                                              game.get('branch-id'))}
    while queue:
        nbr = queue.pop(0)
        yield nbr
        for n in _neighbor_levels(game, nbr, bmap, opts):
            if levid(n) not in closed:
                closed.add(levid(n))
                queue.append(n)


def seek_tile(game, goal_p, opts=None):
    if opts is None:
        opts = {}
    log.debug("seek tile %s", goal_p)
    p = navigate(game, goal_p, opts)
    if p and p['step']:
        return with_reason("seeking tile", goal_p, p['step'])
    seq = level_seq(game, opts)
    if opts.get('max-delta'):
        seq = list(seq)[:opts['max-delta']]
    for level in seq:
        if any(goal_p(t) for t in tile_seq(level)):
            return with_reason("seeking tile", goal_p,
                               seek_level(game, level['branch-id'],
                                          level['dlvl']))
    return None


def seek_feature(game, feature):
    return with_reason("seeking feature", feature,
                       seek_tile(game, lambda t: has_feature(t, feature)))


def entering_shop(game):
    lp = game.get('last-path')
    if lp:
        return shop(at_curlvl(game, lp[0]))
    return None
