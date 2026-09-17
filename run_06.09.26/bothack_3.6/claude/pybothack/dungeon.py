"""Port of bothack.dungeon."""
import logging
import re

from .clj import clj_assert
from .clj import (assoc, assoc_in, clj_vals, dissoc, get_in,
                  update_in, conj_set, merge)
from .level import (blueprints, diggable_floor, geh_maze, new_level, tile_seq,
                    wiztower_boundary, wiztower_inner_boundary, column,
                    ORACLE_POSITION)
from .monster import known_monster, medusa, mimic, oracle
from .position import (Pos, adjacent, at, diagonal_p, in_direction,
                       including_origin, neighbors, position, rectangle,
                       rectangle_boundary, straight, straight_neighbors,
                       towards)
from .tile import (altar_p, boulder, corridor_p, dug, door, door_open_p,
                   floor_p, fountain_p, monster as tile_monster, pool_p,
                   rock_p, shop, SHOPS, SHOP_TYPES, stairs_down_p,
                   stairs_up_p, unknown, walkable, wall_p, blank,
                   diagonal_walkable, TRAPS)
from .util import (find_first, less_than, more_than, parse_int, re_first_group,
                   re_seq)
from ._load import LEVELDATA

log = logging.getLogger('bothack.dungeon')

BRANCHES = {'main', 'mines', 'sokoban', 'quest', 'ludios', 'vlad', 'wiztower',
            'earth', 'fire', 'air', 'water', 'astral'}
SUBBRANCHES = {'mines', 'sokoban', 'ludios', 'vlad', 'quest', 'wiztower',
               'earth', 'air', 'fire', 'water', 'astral'}
UPWARDS_BRANCHES = {'sokoban', 'vlad', 'wiztower'}
PORTAL_BRANCHES = {'quest', 'wiztower', 'ludios'}
PLANES = {'earth', 'air', 'fire', 'water', 'astral'}

fake_wiztower_water = LEVELDATA['fake-wiztower-water']
fake_wiztower_portal = LEVELDATA['fake-wiztower-portal']
SOKO_RECOG = LEVELDATA['soko-recog']


def _next_branch_id(game):
    return "unknown-%d" % ((game.get('last-branch-no') or 0) + 1)


def upwards(branch):
    return branch in UPWARDS_BRANCHES


def dlvl_number(dlvl):
    m = re.search(r'\d+', dlvl)
    return int(m.group(0)) if m else None


def dlvl(game_or_level):
    n = dlvl_number(game_or_level['dlvl'])
    return n if n is not None else -1


def dlvl_compare(a, b, c=None):
    """(dlvl-compare [branch] d1 d2)"""
    if c is not None:
        branch, d1, d2 = a, b, c
        if upwards(branch):
            return dlvl_compare(d2, d1)
        return dlvl_compare(d1, d2)
    d1, d2 = a, b
    if ':' in d1 and ':' in d2:
        n1, n2 = dlvl_number(d1), dlvl_number(d2)
        return (n1 > n2) - (n1 < n2)
    return (d1 > d2) - (d1 < d2)


def _sorted_branch(levels, branch_id):
    """Return the dlvl keys of a branch map in dlvl-compare order."""
    import functools
    return sorted(levels.keys(),
                  key=functools.cmp_to_key(
                      lambda a, b: dlvl_compare(branch_id, a, b)))


def branch_keys(game, branch_id):
    b = get_in(game, ['dungeon', 'levels', branch_key(game, branch_id)]) or {}
    return _sorted_branch(b, branch_key(game, branch_id))


def ensure_branch(game, branch_id):
    log.debug("ensuring branch %s", branch_id)
    if get_in(game, ['dungeon', 'levels', branch_id]) is None:
        return assoc_in(game, ['dungeon', 'levels', branch_id], {})
    return game


def add_level(game, level):
    branch_id = level['branch-id']
    return assoc_in(ensure_branch(game, branch_id),
                    ['dungeon', 'levels', branch_id, level['dlvl']], level)


def change_dlvl(f, dlvl_):
    n = dlvl_number(dlvl_)
    if n is None:
        return dlvl_
    return re.sub(r'\d+', str(f(n)), dlvl_)


def prev_dlvl(branch_or_dlvl, dlvl_=None):
    if dlvl_ is None:
        return prev_dlvl('main', branch_or_dlvl)
    if upwards(branch_or_dlvl):
        return change_dlvl(lambda n: n + 1, dlvl_)
    return change_dlvl(lambda n: n - 1, dlvl_)


def next_dlvl(branch_or_dlvl, dlvl_=None):
    if dlvl_ is None:
        return next_dlvl('main', branch_or_dlvl)
    if upwards(branch_or_dlvl):
        return change_dlvl(lambda n: n - 1, dlvl_)
    return change_dlvl(lambda n: n + 1, dlvl_)


def branch_key(game, level_or_branch_id=None):
    if level_or_branch_id is None:
        branch_id = game['branch-id']
        clj_assert(branch_id, 'branch-id')
        return branch_key(game, branch_id)
    if isinstance(level_or_branch_id, str):
        branch_id = level_or_branch_id
    else:
        # tiles carry :branch-id only once known - (:branch-id tile) is nil
        branch_id = level_or_branch_id.get('branch-id')
    if branch_id is None:
        return None
    return get_in(game, ['dungeon', 'id->branch', branch_id], branch_id)


def curlvl(game):
    return get_in(game, ['dungeon', 'levels', branch_key(game), game['dlvl']])


def curlvl_monsters(game):
    return clj_vals(curlvl(game)['monsters'])


def update_curlvl(game, f, *args):
    return update_in(game, ['dungeon', 'levels', branch_key(game),
                            game['dlvl']], f, *args)


def add_curlvl_tag(game, *tags):
    log.debug("tagging curlvl with %s", tags)
    return update_curlvl(game, lambda l: assoc(
        l, 'tags', conj_set(l['tags'], *[t for t in tags if t is not None])))


def curlvl_tags(game):
    return curlvl(game)['tags']


def remove_monster(game, pos):
    return update_curlvl(game, lambda l: assoc(
        l, 'monsters', dissoc(l['monsters'], position(pos))))


def reset_monster(game_or_level, mon):
    if 'dungeon' in game_or_level:
        return update_curlvl(game_or_level, reset_monster, mon)
    lvl = game_or_level
    return assoc(lvl, 'monsters',
                 assoc(lvl['monsters'], position(mon), mon))


def update_monster(game, pos, f, *args):
    if position(pos) in curlvl(game)['monsters']:
        return update_curlvl(
            game, lambda l: update_in(l, ['monsters', position(pos)], f, *args))
    return game


def monster_at(game_or_level, x, y=None):
    pos = position(x, y) if y is not None else x
    if pos is None:
        return None
    if 'monsters' in game_or_level:
        return game_or_level['monsters'].get(position(pos))
    return monster_at(curlvl(game_or_level), pos)


def real_boulder(level, pos):
    return boulder(at(level, pos)) and not mimic(monster_at(level, pos))


def update_at(game_or_level, pos, f, *args):
    if 'dungeon' in game_or_level:
        return update_curlvl(game_or_level, update_at, pos, f, *args)
    return update_in(game_or_level, ['tiles', pos['y'] - 1, pos['x']], f, *args)


def update_at_player(game, f, *args):
    return update_at(game, game['player'], f, *args)


def update_from_player(game, dir_, f, *args):
    return update_at(game, in_direction(game['player'], dir_), f, *args)


def update_item_at_player(game, idx, f, *args):
    return update_at_player(
        game, lambda t: update_in(t, ['items', idx], f, *args))


def update_around(game, pos, f, *args):
    for n in neighbors(pos):
        game = update_at(game, n, f, *args)
    return game


def update_around_player(game, f, *args):
    return update_around(game, game['player'], f, *args)


def at_curlvl(game, x, y=None):
    pos = position(x, y) if y is not None else x
    return at(curlvl(game), pos)


def at_player(game):
    return at_curlvl(game, game['player'])


def get_branch(game, branch_id=None):
    if branch_id is None:
        branch_id = branch_key(game)
    return get_in(game, ['dungeon', 'levels', branch_key(game, branch_id)])


_TAG_RE = re.compile(r'^[a-z0-9-]+$')


def is_tag(s):
    """Clojure distinguishes tags (keywords) from dlvls (strings); here both
    are str, so we tell them apart by shape - every dlvl carries an upper-case
    letter ("Dlvl:3", "Home 1", "End Game", ...) and every tag is lowercase."""
    return bool(_TAG_RE.match(s))


def get_level(game, branch, dlvl_or_tag):
    levels = get_branch(game, branch)
    if not levels:
        return None
    if is_tag(dlvl_or_tag):
        for k in _sorted_branch(levels, branch_key(game, branch)):
            if dlvl_or_tag in levels[k]['tags']:
                return levels[k]
        return None
    return levels.get(dlvl_or_tag)


def get_dlvl(game, branch, dlvl_or_tag):
    l = get_level(game, branch, dlvl_or_tag)
    return l['dlvl'] if l else None


def lit(player, level, pos):
    """Pessimistic guess at lit-ness."""
    tile = at(level, pos)
    return (adjacent(pos, player)
            or tile['glyph'] == '.'
            or (tile['glyph'] == '#' and tile.get('color') == 'white'))


def map_tiles(f, *tile_colls):
    return [[f(*cells) for cells in zip(*rows)] for rows in zip(*tile_colls)]


_MAIN_FEATURES = {'door-closed', 'door-open', 'door-locked', 'door-secret',
                  'altar', 'sink', 'fountain', 'throne'}


def _has_features(level):
    return any(t.get('feature') in _MAIN_FEATURES for t in tile_seq(level))


def _same_glyph_diag_walls(level):
    """Diagonally adjacent walls with the same glyph => mines (thanks TAEB)."""
    for row in level['tiles'][::2]:
        for tile in row:
            for n in neighbors(level, tile):
                if straight(towards(tile, n)):
                    continue
                if (wall_p(tile) and wall_p(n)
                        and tile['glyph'] == n['glyph']):
                    return True
    return False


SOKO1_14 = "                                |..^^^^8888...|"
SOKO2_12 = "                                |..^^^<|.....|"


def _in_soko(game):
    return (5 <= dlvl(game) <= 9
            and (get_in(game, ['frame', 'lines', 14], '').startswith(SOKO1_14)
                 or get_in(game, ['frame', 'lines', 12],
                           '').startswith(SOKO2_12)))


def _recognize_branch(game, level):
    if _in_soko(game):
        return 'sokoban'
    if _has_features(level):
        return 'main'
    if _same_glyph_diag_walls(level):
        return 'mines'
    return None


def branch_entry(game, branch):
    """Dlvl of :main containing entrance to branch, if known."""
    if branch in PLANES:
        return "Dlvl:1"
    l = get_level(game, 'main', branch_key(game, branch))
    return l['dlvl'] if l else None


def _merge_tile(new_tile, old_tile):
    t = new_tile
    if old_tile.get('branch-id'):
        t = assoc(t, 'branch-id', old_tile['branch-id'])
    from .util import max_star
    return assoc(
        t,
        'tags', conj_set(t.get('tags'), *(old_tile.get('tags') or ())),
        'first-walked', max_star(t.get('first-walked'),
                                 old_tile.get('first-walked')),
        'walked', max_star(t.get('walked'), old_tile.get('walked')),
        'seen', t.get('seen') or old_tile.get('seen'),
        'feature', t.get('feature') or old_tile.get('feature'),
        'searched', t['searched'] + old_tile['searched'])


def _merge_levels(old_level, new_level_):
    log.debug("merging dlvl %s", old_level['dlvl'])
    l = assoc(new_level_, 'blueprint',
              old_level.get('blueprint') or new_level_.get('blueprint'))
    l = assoc(l, 'tags', conj_set(l['tags'], *old_level['tags']))
    return assoc(l, 'tiles', map_tiles(_merge_tile, l['tiles'],
                                       old_level['tiles']))


def merge_branch_id(game, branch_id, branch):
    log.debug("merging branch-id %s to branch %s", branch_id, branch)
    entry = branch_entry(game, branch_id)
    game = assoc_in(game, ['dungeon', 'id->branch', branch_id], branch)
    game = ensure_branch(game, branch)
    old = get_in(game, ['dungeon', 'levels', branch_id]) or {}
    target = dict(get_in(game, ['dungeon', 'levels', branch]) or {})
    for k, v in old.items():
        target[k] = _merge_levels(target[k], v) if k in target else v
    game = assoc_in(game, ['dungeon', 'levels', branch], target)
    if entry is not None and get_in(game, ['dungeon', 'levels', 'main', entry]):
        game = update_in(game, ['dungeon', 'levels', 'main', entry, 'tags'],
                         lambda tags: conj_set(
                             set(tags) - {branch_id}, branch))
    levels = dissoc(get_in(game, ['dungeon', 'levels']), branch_id)
    return assoc_in(game, ['dungeon', 'levels'], levels)


def infer_branch(game):
    if branch_key(game) in BRANCHES:
        return game            # branch already known
    level = curlvl(game)
    branch = _recognize_branch(game, level)
    if branch:
        return merge_branch_id(game, level['branch-id'], branch)
    return game


def in_maze_corridor(level, pos):
    return bool(more_than(5, [t for t in neighbors(level, pos) if wall_p(t)]))


def _recognize_soko(game):
    for y, line, tag in SOKO_RECOG:
        if get_in(game, ['frame', 'lines', y], '').startswith(line):
            return tag
    raise RuntimeError("unrecognized sokoban level!")


def infer_tags(game):
    level = curlvl(game)
    curdlvl = dlvl(level)
    tags = level['tags']
    branch = branch_key(game)
    has_features = _has_features(level)
    last = game.get('last-state')

    def L(x, y=None):
        return at(level, x, y)

    if (branch == 'main' and 21 <= curdlvl <= 28
            and 'medusa-1' not in tags and 'medusa-2' not in tags
            and any(floor_p(L(3, y)) for y in range(2, 21))
            and all(pool_p(L(2, y)) or monster_at(level, Pos(2, y))
                    for y in range(2, 21))):
        game = add_curlvl_tag(game, 'medusa', 'medusa-1')
        level = curlvl(game); tags = level['tags']
    if (branch == 'main' and 21 <= curdlvl <= 28
            and 'medusa-1' not in tags and 'medusa-2' not in tags
            and not any(floor_p(L(3, y)) for y in range(2, 21))
            and all(pool_p(L(7, y)) for y in (15, 16, 17))
            and wall_p(L(8, 15)) and wall_p(L(8, 17))):
        game = add_curlvl_tag(game, 'medusa', 'medusa-2')
        level = curlvl(game); tags = level['tags']
    if (branch == 'main' and 21 <= curdlvl <= 28 and 'medusa' not in tags
            and last and last['dlvl'] == game['dlvl']
            and (any(medusa(m) for m in curlvl_monsters(last))
                 or all(pool_p(L(2, y)) or monster_at(level, Pos(2, y))
                        for y in range(3, 15)))):
        game = add_curlvl_tag(game, 'medusa')
        level = curlvl(game); tags = level['tags']
    # 3.6.7 dat/medusa.des adds medusa-3 (ravens, trees) and medusa-4
    # (iron bars, yellow dragon); neither matches the two geometries above.
    # All four are mostly water; the Castle is a maze with a moat.  Uses only
    # what has been seen on the map.
    if (branch == 'main' and 21 <= curdlvl <= 28 and 'medusa' not in tags
            and 'castle' not in tags):
        seen = 0
        pools = 0
        trees = 0
        bars = 0
        for t in tile_seq(level):
            f = t.get('feature')
            if f is None or f == 'rock':
                continue
            seen += 1
            if f == 'pool':
                pools += 1
            elif f == 'tree':
                trees += 1
            elif f == 'bars':
                bars += 1
        if pools >= 120 and pools * 2 >= seen:
            variant = ('medusa-3' if trees > bars else
                       'medusa-4' if bars > trees else None)
            game = (add_curlvl_tag(game, 'medusa', variant) if variant
                    else add_curlvl_tag(game, 'medusa'))
            level = curlvl(game); tags = level['tags']
    if (branch == 'main' and 25 <= curdlvl <= 29 and 'castle' not in tags
            and (drawbridge_at(L(14, 12))
                 or (all(pool_p(L(x, 20)) for x in range(8, 16))
                     and wall_p(L(7, 20)))
                 or (all(pool_p(L(x, 4)) for x in range(8, 16))
                     and wall_p(L(7, 4))))):
        game = add_curlvl_tag(game, 'castle')
        level = curlvl(game); tags = level['tags']
    if (branch == 'sokoban'
            and not any(t in tags for t in ('soko-1a', 'soko-1b', 'soko-2a',
                                            'soko-2b', 'soko-3a', 'soko-3b',
                                            'soko-4a', 'soko-4b'))):
        tag = _recognize_soko(game)
        game = add_curlvl_tag(game, tag)
        if tag in ('soko-4a', 'soko-4b'):
            game = add_curlvl_tag(game, 'end')
        level = curlvl(game); tags = level['tags']
    if (branch == 'main' and 10 <= curdlvl <= 12 and 'bigroom' not in tags):
        for row in (8, 16):
            seq = []
            for x in range(3, 78):
                t = L(x, row)
                if corridor_p(t):
                    break
                seq.append(t)
            if more_than(45, [t for t in seq
                              if floor_p(t) or monster_at(level, t)]):
                game = add_curlvl_tag(game, 'bigroom')
                level = curlvl(game); tags = level['tags']
                break
    if (branch == 'main' and 5 <= curdlvl <= 9
            and last and last['dlvl'] == game['dlvl']
            and any(oracle(m) for m in curlvl_monsters(last))):
        game = add_curlvl_tag(game, 'oracle')
        level = curlvl(game); tags = level['tags']
    if (branch == 'main' and 36 <= curdlvl <= 47
            and 'wiztower-level' not in tags
            and (any(L(p).get('undiggable') for p in wiztower_inner_boundary)
                 or (not any(floor_p(L(p)) for p in wiztower_inner_boundary)
                     and more_than(20, [L(p) for p in wiztower_boundary
                                        if wall_p(L(p)) or L(p).get('dug')])
                     and less_than(5, [L(p) for p in wiztower_boundary
                                       if floor_p(L(p))
                                       and not L(p).get('dug')])))):
        game = add_curlvl_tag(game, 'wiztower-level')
        level = curlvl(game); tags = level['tags']
    if (5 <= curdlvl <= 9 and branch == 'mines' and 'minetown' not in tags
            and has_features):
        game = add_curlvl_tag(game, 'minetown')
        level = curlvl(game); tags = level['tags']
    if (5 <= curdlvl <= 9 and stairs_up_p(L(3, 2)) and 'minetown' in tags
            and 'minetown-grotto' not in tags):
        game = add_curlvl_tag(game, 'minetown-grotto')
        level = curlvl(game); tags = level['tags']
    if (27 <= curdlvl <= 36 and 'asmodeus' not in tags
            and ((any(t.get('undiggable') for t in tile_seq(level))
                  and stairs_down_p(L(27, 13)))
                 or all(L(x, y)['glyph'] == '-' for x, y in ((66, 10), (66, 9)))
                 or all(L(x, y)['glyph'] == '-'
                        for x, y in ((66, 14), (66, 15)))
                 or door(L(66, 12)))):
        game = add_curlvl_tag(game, 'asmodeus')
        level = curlvl(game); tags = level['tags']
    if (29 <= curdlvl <= 36 and 'juiblex' not in tags
            and more_than(24, [t for t in tile_seq(level) if pool_p(t)])):
        game = add_curlvl_tag(game, 'juiblex')
        level = curlvl(game); tags = level['tags']
    if (31 <= curdlvl <= 38 and 'baalzebub' not in tags
            and ((not any(wall_p(L(x, y))
                          for x, y in ((31, 11), (32, 11), (33, 11), (34, 11),
                                       (31, 13), (32, 13), (33, 13), (34, 13)))
                  and not any((not wall_p(L(x, y))) or dug(L(x, y))
                              for x, y in ((30, 10), (35, 10), (30, 11),
                                           (35, 11), (30, 13), (35, 13),
                                           (30, 14), (35, 14))))
                 or (stairs_down_p(L(72, 12)) and door(L(70, 12))))):
        game = add_curlvl_tag(game, 'baalzebub')
        level = curlvl(game); tags = level['tags']
    if (branch == 'main' and 40 <= curdlvl <= 51 and 'fake-wiztower' not in tags
            and any(pool_p(L(p)) for p in fake_wiztower_water)):
        game = add_curlvl_tag(game, 'fake-wiztower')
        level = curlvl(game); tags = level['tags']
    if (branch == 'main' and 40 <= curdlvl and 'sanctum' not in tags):
        end = get_level(game, 'main', 'end')
        if end is not None and dlvl(end) + 1 == curdlvl:
            game = add_curlvl_tag(game, 'sanctum')
            level = curlvl(game); tags = level['tags']
    if (branch in ('wiztower', 'vlad')
            and not any(t in tags for t in ('bottom', 'middle', 'end'))):
        keys = branch_keys(game, branch)
        if keys:
            delta = dlvl_number(keys[0]) - curdlvl
            game = add_curlvl_tag(game, {0: 'bottom', 1: 'middle',
                                         2: 'end'}.get(delta))
            level = curlvl(game); tags = level['tags']
    if (10 <= curdlvl <= 13 and branch == 'mines'
            and not any(t in tags for t in ('minesend-1', 'minesend-2',
                                            'minesend-3'))
            and stairs_up_p(L(38, 8))
            and ((all(floor_p(L(x, 7)) for x in range(35, 42))
                  and all(wall_p(L(x, 6)) for x in range(35, 42)))
                 or more_than(2, [t for t in tile_seq(level)
                                  if t.get('undiggable')]))):
        game = add_curlvl_tag(game, 'minesend-1')
        level = curlvl(game); tags = level['tags']
    if (10 <= curdlvl <= 13 and branch == 'mines' and 'end' not in tags
            and has_features):
        game = add_curlvl_tag(game, 'end')
    return game


def drawbridge_at(tile):
    from .tile import drawbridge
    return drawbridge(tile)


def next_plane(game):
    """Next unvisited elemental plane."""
    if get_branch(game, 'fire'):
        return 'water'
    if get_branch(game, 'air'):
        return 'fire'
    if get_branch(game, 'earth'):
        return 'air'
    return None


def initial_branch_id(game, dlvl_):
    if dlvl_ == "End Game":
        return 'earth'
    b = branch_key(game)
    if b in SUBBRANCHES:
        return b
    n = dlvl_number(dlvl_)
    if not (n is not None and 3 <= n <= 9):
        return 'main'
    return _next_branch_id(game)


def dlvl_range(branch, start="Dlvl:1", howmany=60):
    return [change_dlvl(lambda n, x=x: n + x, start) for x in range(howmany)]


def dlvl_from_entrance(game, branch, in_branch_depth):
    keys = branch_keys(game, branch)
    if not keys:
        return None
    return change_dlvl(lambda n: n + in_branch_depth - 1, keys[0])


def dlvl_from_tag(game, branch, tag, after_tag_depth):
    d = get_dlvl(game, branch, tag)
    if d is None:
        return None
    return change_dlvl(lambda n: n + after_tag_depth - 1, d)


def ensure_curlvl(game):
    if get_in(game, ['dungeon', 'levels', branch_key(game), game['dlvl']]) \
            is None:
        return add_level(game, new_level(game['dlvl'], branch_key(game)))
    return game


def _shopkeeper_look(game, tile_or_monster):
    return (position(game['player']) != position(tile_or_monster)
            and tile_or_monster['glyph'] == '@'
            and tile_or_monster.get('color') == 'white')


def _room_rectangle(game, nw, se, kind):
    log.debug("room rectangle: %s %s %s", nw, se, kind)
    if max(se['x'] - nw['x'], se['y'] - nw['y']) > 20:
        log.error("spilled room at %s %s", game['dlvl'], branch_key(game))
    res = game
    for p in rectangle(nw, se):
        res = update_at(res, p, lambda t: assoc(t, 'room', kind))
    if kind in SHOPS:
        for p in rectangle_boundary(nw, se):
            if unknown(at_curlvl(game, p)):
                res = update_at(res, p, lambda t: assoc(t, 'feature', 'wall'))
    return res


def _boundary(tile):
    return wall_p(tile) or door(tile) or tile.get('dug')


def _missing_wall(level, tile):
    if _boundary(tile):
        return False
    nbrs = neighbors(level, tile)
    vert = [n for n in nbrs if n['x'] == tile['x']]
    horiz = [n for n in nbrs if n['y'] == tile['y']]
    return bool((less_than(3, [n for n in nbrs if _boundary(n)])
                 and any(_boundary(n) for n in vert)
                 and any(_boundary(n) for n in horiz))
                or all(_boundary(n) for n in vert)
                or all(_boundary(n) for n in horiz))


def _floodfill_room(game, pos, kind):
    log.debug("room floodfill from: %s type: %s", pos, kind)
    level = curlvl(game)
    origin = at(level, pos)
    closed = set()
    nw = {'x': origin['x'], 'y': origin['y']}
    se = {'x': origin['x'], 'y': origin['y']}
    if _shopkeeper_look(game, origin):
        openset = list(including_origin(neighbors, level, origin))
    else:
        openset = [origin]
    openset = {position(t): t for t in openset}
    while openset:
        key = next(iter(openset))
        x = openset.pop(key)
        closed.add(position(x))
        nw = {'x': min(nw['x'], x['x']), 'y': min(nw['y'], x['y'])}
        se = {'x': max(se['x'], x['x']), 'y': max(se['y'], x['y'])}
        if not (door(x) or wall_p(x) or _missing_wall(level, x)):
            for n in neighbors(level, x):
                if (blank(n) or n.get('dug') or corridor_p(n)
                        or position(n) in closed):
                    continue
                openset.setdefault(position(n), n)
    return _room_rectangle(game, nw, se, kind)


def reflood_room(game, pos):
    tile = at_curlvl(game, pos)
    if tile.get('room') and not tile.get('walked'):
        log.debug("room reflood from: %s type: %s", pos, tile['room'])
        return _floodfill_room(game, pos, tile['room'])
    return game


def _closest_roomkeeper(game):
    from .util import min_by
    from .position import distance
    return min_by(lambda m: distance(game['player'], m),
                  [m for m in curlvl_monsters(game)
                   if _shopkeeper_look(game, m)])


ROOM_RE = r"Welcome(?: again)? to(?: (?:[A-Z]\S+|a))+ ([a-z -]+)!"


def room_type(msg):
    if msg.endswith(", welcome to Delphi!\""):
        return 'oracle'
    if re_seq(r'Invisible customers are not welcome', msg):
        return 'shop'
    return SHOP_TYPES.get(re_first_group(ROOM_RE, msg))


def mark_room(game, kind):
    log.debug("marking room as %s", kind)
    res = add_curlvl_tag(game, kind)
    if kind in SHOPS:
        rk = _closest_roomkeeper(res)
        if rk:
            res = _floodfill_room(res, rk, kind)
    if game.get('last-position') and adjacent(game['last-position'],
                                              game['player']):
        res = update_at(res, game['last-position'],
                        lambda t: assoc(t, 'room', None))
    return res


def _match_level(game, level, blueprint):
    return ((not blueprint.get('role')
             or game['player'].get('role') == blueprint['role'])
            and (not blueprint.get('branch')
                 or blueprint['branch'] == branch_key(game, level))
            and (not blueprint.get('dlvl')
                 or blueprint['dlvl'] == level['dlvl'])
            and (not blueprint.get('tag')
                 or blueprint['tag'] in level['tags']))


def apply_blueprint(level, blueprint):
    log.debug("applying blueprint %s",
              {k: blueprint.get(k) for k in ('branch', 'tag', 'dlvl')})
    res = level
    for p in (blueprint.get('undiggable-tiles') or ()):
        res = update_at(res, p, lambda t: assoc(t, 'undiggable', True))
    for x in (blueprint.get('cutoff-cols') or ()):
        for y in range(1, 22):
            res = update_at(res, Pos(x, y), lambda t: assoc(
                t, 'feature', 'rock', 'undiggable', True, 'seen', True))
    for y in (blueprint.get('cutoff-rows') or ()):
        for x in range(0, 80):
            res = update_at(res, Pos(x, y), lambda t: assoc(
                t, 'feature', 'rock', 'undiggable', True, 'seen', True))
    for pos, feature in (blueprint.get('features') or {}).items():
        cur = at(res, pos)
        if feature == 'door-secret':
            newf = ('door-secret' if (unknown(cur) or wall_p(cur))
                    else cur.get('feature'))
        elif feature == 'cloud':
            newf = feature
        else:
            newf = cur.get('feature') or feature
        res = update_at(res, pos, lambda t, nf=newf: assoc(t, 'seen', True,
                                                           'feature', nf))
    for pos, mon in (blueprint.get('monsters') or {}).items():
        res = reset_monster(res, known_monster(pos['x'], pos['y'], mon))
    return res


def _match_blueprint(game, level):
    bp = find_first(lambda b: _match_level(game, level, b), blueprints)
    if bp is None:
        return None
    log.debug("matched blueprint, level: %s; branch: %s; tags: %s",
              level['dlvl'], branch_key(game, level), level['tags'])
    return apply_blueprint(assoc(level, 'blueprint', bp), bp)


def level_blueprint(game):
    level = curlvl(game)
    if not level.get('blueprint'):
        new = _match_blueprint(game, level)
        if new:
            return assoc_in(game, ['dungeon', 'levels',
                                   branch_key(game, new), new['dlvl']], new)
    return game


def diggable_walls(game, level):
    return (not any(t in level['tags']
                    for t in ('rogue', 'sanctum', 'medusa', 'bigroom'))
            and ('orcus' in level['tags']
                 or not (level.get('blueprint') or {}).get('undiggable'))
            and branch_key(game, level) not in ('vlad', 'astral', 'sokoban',
                                                'quest'))


def below_castle(game):
    player = game['player']
    castle = get_dlvl(game, 'main', 'castle')
    if not castle:
        return False
    return bool(dlvl_compare(game['dlvl'], castle) > 0
                or (game['dlvl'] == castle
                    and (player['x'] > 69
                         or (player['x'] > 64 and 8 < player['y'] < 16)
                         or (player['x'] >= 60 and player['y'] == 12))))


def at_planes(game):
    return branch_key(game) in PLANES


def in_gehennom(game):
    if branch_key(game) not in ('wiztower', 'main'):
        return False
    castle = get_dlvl(game, 'main', 'castle')
    return bool(castle and dlvl_compare(game['dlvl'], castle) > 0)


def below_medusa(game):
    m = get_dlvl(game, 'main', 'medusa')
    if not m:
        return False
    return bool(dlvl_compare(game['dlvl'], m) > 0
                or (game['dlvl'] == m and game['player']['x'] > 22))


def apply_default_blueprint(game):
    if (in_gehennom(game) and 'votd' not in curlvl_tags(game)
            and any(wall_p(t) for t in neighbors(curlvl(game),
                                                 game['player']))):
        return update_curlvl(game, apply_blueprint, geh_maze)
    return game


def narrow(game, level_or_from, from_or_to, to=None):
    if to is None:
        level, frm, to_ = curlvl(game), level_or_from, from_or_to
    else:
        level, frm, to_ = level_or_from, from_or_to, to
    if adjacent(frm, to_) and diagonal_p(frm, to_):
        common = set(position(t) for t in straight_neighbors(level, frm)) & \
            set(position(t) for t in straight_neighbors(level, to_))
        return all(rock_p(at(level, p)) or wall_p(at(level, p))
                   or (branch_key(game) == 'sokoban' and boulder(at(level, p)))
                   for p in common)
    return None


def edge_passable_walking(game, level, from_tile, to_tile):
    return bool(straight(towards(from_tile, to_tile))
                or (diagonal_walkable(game, from_tile)
                    and diagonal_walkable(game, to_tile)
                    and ((branch_key(game, level) != 'sokoban'
                          and not game['player'].get('thick'))
                         or not narrow(game, level, from_tile, to_tile))))


def passable_walking(game, level, from_tile, to_tile):
    return (walkable(to_tile)
            and edge_passable_walking(game, level, from_tile, to_tile))


def new_dungeon():
    return {'levels': {}, 'id->branch': {b: b for b in BRANCHES}}
