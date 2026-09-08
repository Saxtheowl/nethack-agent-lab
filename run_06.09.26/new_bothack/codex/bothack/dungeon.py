"""Persistent dungeon state from dungeon.clj (GPL-2.0), 2026-09-07.

Positions remain hashable Position objects; maps and tile rows are copied on
updates so the previous game state retains the original observations.
"""
import re
from functools import cmp_to_key
from . import position as p, tile as t
from .level import pos, at, neighbors, new_level, tile_seq, world_data
from .state import assoc_in, update_in, get_in, dissoc, truth

BRANCHES = frozenset('main mines sokoban quest ludios vlad wiztower earth fire air water astral'.split())
SUBBRANCHES = BRANCHES - {'main'}
UPWARDS = frozenset({'sokoban', 'vlad', 'wiztower'})
PORTAL_BRANCHES = frozenset({'quest', 'wiztower', 'ludios'})
PLANES = frozenset({'earth', 'air', 'fire', 'water', 'astral'})


def new_dungeon():
    return {'levels': {}, 'id->branch': {b: b for b in BRANCHES}}


def dlvl_number(label):
    match = re.search(r'\d+', label)
    return int(match[0]) if match else None


def dlvl(game_or_level):
    value = dlvl_number(game_or_level['dlvl'])
    return -1 if value is None else value


def dlvl_compare(d1, d2, branch='main'):
    if branch in UPWARDS:
        d1, d2 = d2, d1
    if ':' in d1 and ':' in d2:
        a, b = dlvl_number(d1), dlvl_number(d2)
        return (a > b) - (a < b)
    for a, b in zip(d1, d2):
        if a != b:
            return ord(a) - ord(b)
    return len(d1) - len(d2)


def change_dlvl(function, label):
    number = dlvl_number(label)
    return label if number is None else re.sub(r'\d+', str(function(number)), label)


def prev_dlvl(label, branch='main'):
    return change_dlvl(lambda n: n + (1 if branch in UPWARDS else -1), label)


def next_dlvl(label, branch='main'):
    return change_dlvl(lambda n: n + (-1 if branch in UPWARDS else 1), label)


def branch_key(game, level_or_branch=None):
    branch = game['branch-id'] if level_or_branch is None else level_or_branch
    if isinstance(branch, dict):
        branch = branch['branch-id']
    return game['dungeon']['id->branch'].get(branch, branch)


def get_branch(game, branch=None):
    result = game['dungeon']['levels'].get(branch_key(game, branch))
    if result is None:
        return None
    key = cmp_to_key(lambda a, b: dlvl_compare(a, b, branch_key(game, branch)))
    return dict(sorted(result.items(), key=lambda pair: key(pair[0])))


def get_level(game, branch, dlvl_or_tag):
    levels = get_branch(game, branch)
    if levels is None:
        return None
    if ':' in dlvl_or_tag or dlvl_or_tag.startswith(('Home ', 'End Game', 'Astral Plane', 'Fort Ludios')):
        return levels.get(dlvl_or_tag)
    return next((level for level in levels.values() if dlvl_or_tag in level['tags']), None)


def get_dlvl(game, branch, dlvl_or_tag):
    return (get_level(game, branch, dlvl_or_tag) or {}).get('dlvl')


def curlvl(game):
    return get_in(game, ['dungeon', 'levels', branch_key(game), game['dlvl']])


def ensure_branch(game, branch):
    path = ['dungeon', 'levels', branch]
    return game if get_in(game, path) is not None else assoc_in(game, path, {})


def add_level(game, level):
    return assoc_in(ensure_branch(game, level['branch-id']),
                    ['dungeon', 'levels', level['branch-id'], level['dlvl']], level)


def ensure_curlvl(game):
    return game if curlvl(game) is not None else add_level(game, new_level(game['dlvl'], branch_key(game)))


def update_curlvl(game, function, *args):
    return update_in(game, ['dungeon', 'levels', branch_key(game), game['dlvl']], function, *args)


def add_curlvl_tag(game, *tags):
    return update_curlvl(game, lambda level: level | {'tags': set(level.get('tags') or ()) | set(tags)})


def curlvl_tags(game):
    return (curlvl(game) or {}).get('tags')


def curlvl_monsters(game):
    return tuple((curlvl(game) or {}).get('monsters', {}).values())


def monster_at(game_or_level, position):
    if position is None:
        return None
    level = game_or_level if 'monsters' in game_or_level else curlvl(game_or_level)
    return level['monsters'].get(pos(position))


def remove_monster(game, position):
    return update_curlvl(game, lambda level: level | {'monsters': dissoc(level['monsters'], pos(position))})


def reset_monster(game_or_level, monster):
    if 'dungeon' in game_or_level:
        return update_curlvl(game_or_level, reset_monster, monster)
    return assoc_in(game_or_level, ['monsters', pos(monster)], monster)


def update_monster(game, position, function, *args):
    return (update_curlvl(game, lambda level: update_in(level, ['monsters', pos(position)], function, *args))
            if monster_at(game, position) is not None else game)


def update_at(game_or_level, position, function, *args):
    if 'dungeon' in game_or_level:
        return update_curlvl(game_or_level, update_at, position, function, *args)
    q = pos(position)
    if not p.valid_position(q):
        raise ValueError(q)
    return update_in(game_or_level, ['tiles', q.y - 1, q.x], function, *args)


def at_player(game):
    return at(curlvl(game), game['player'])


def update_at_player(game, function, *args):
    return update_at(game, game['player'], function, *args)


def update_from_player(game, direction, function, *args):
    return update_at(game, p.in_direction(pos(game['player']), direction), function, *args)


def update_around(game, position, function, *args):
    for q in p.neighbors(pos(position)):
        game = update_at(game, q, function, *args)
    return game


def update_item_at_player(game, index, function, *args):
    return update_at_player(game, lambda tile: update_in(tile, ['items', index], function, *args))


def map_tiles(function, *grids):
    return [[function(*tiles) for tiles in zip(*rows)] for rows in zip(*grids)]


def lit(player, level, position):
    tile = at(level, position)
    return (p.adjacent(pos(position), pos(player)) or tile['glyph'] == '.'
            or (tile['glyph'] == '#' and tile['color'] == 'white'))


def branch_entry(game, branch):
    return 'Dlvl:1' if branch in PLANES else get_dlvl(game, 'main', branch_key(game, branch))


def next_plane(game):
    for branch, result in [('fire', 'water'), ('air', 'fire'), ('earth', 'air')]:
        if get_branch(game, branch) is not None:
            return result
    raise ValueError('No matching clause in next-plane')


def initial_branch_id(game, label):
    branch = branch_key(game)
    if label == 'End Game':
        return 'earth'
    if branch in SUBBRANCHES:
        return branch
    if not 3 <= dlvl_number(label) <= 9:
        return 'main'
    return 'unknown-' + str((game.get('last-branch-no') or 0) + 1)


def dlvl_range(branch, start='Dlvl:1', howmany=60):
    return [change_dlvl(lambda n: n + i, start) for i in range(howmany)]


def dlvl_from_entrance(game, branch, depth):
    levels = get_branch(game, branch)
    return change_dlvl(lambda n: n + depth - 1, next(iter(levels))) if levels else None


def dlvl_from_tag(game, branch, tag, depth):
    label = get_dlvl(game, branch, tag)
    return None if label is None else change_dlvl(lambda n: n + depth - 1, label)


def at_planes(game):
    return branch_key(game) in PLANES


def in_gehennom(game):
    castle = get_dlvl(game, 'main', 'castle')
    return branch_key(game) in {'wiztower', 'main'} and castle is not None and dlvl_compare(game['dlvl'], castle) > 0


def below_castle(game):
    castle = get_dlvl(game, 'main', 'castle')
    player = game['player']
    return (castle is not None and (dlvl_compare(game['dlvl'], castle) > 0
            or (game['dlvl'] == castle and (player['x'] > 69 or (player['x'] > 64 and 8 < player['y'] < 16)
                                           or (player['x'] >= 60 and player['y'] == 12)))))


def below_medusa(game):
    medusa = get_dlvl(game, 'main', 'medusa')
    return medusa is not None and (dlvl_compare(game['dlvl'], medusa) > 0
                                  or (game['dlvl'] == medusa and game['player']['x'] > 22))


def merge_tile(new, old):
    result = dict(new)
    if truth(old.get('branch-id')):
        result['branch-id'] = old['branch-id']
    result['tags'] = set(new.get('tags') or ()) | set(old.get('tags') or ())
    for field in ('first-walked', 'walked'):
        values = [v for v in (new.get(field), old.get(field)) if v is not None]
        result[field] = max(values) if values else None
    for field in ('seen', 'feature'):
        result[field] = new.get(field) if truth(new.get(field)) else old.get(field)
    result['searched'] = new['searched'] + old['searched']
    return result


def merge_levels(old, new):
    return new | {'blueprint': old.get('blueprint') if truth(old.get('blueprint')) else new.get('blueprint'),
                  'tags': set(new['tags']) | set(old['tags']),
                  'tiles': map_tiles(merge_tile, new['tiles'], old['tiles'])}


def merge_branch_id(game, branch_id, branch):
    entrance = branch_entry(game, branch_id)
    old_levels = game['dungeon']['levels'].get(branch_id, {})
    result = ensure_branch(assoc_in(game, ['dungeon', 'id->branch', branch_id], branch), branch)
    for label, level in old_levels.items():
        previous = get_in(result, ['dungeon', 'levels', branch, label])
        result = assoc_in(result, ['dungeon', 'levels', branch, label],
                          merge_levels(previous, level) if previous is not None else level)
    result = update_in(result, ['dungeon', 'levels', 'main', entrance, 'tags'],
                       lambda tags: (set(tags or ()) - {branch_id}) | {branch})
    return update_in(result, ['dungeon', 'levels'], dissoc, branch_id)


MAIN_FEATURES = frozenset({'door-closed', 'door-open', 'door-locked', 'door-secret', 'altar', 'sink', 'fountain', 'throne'})


def has_features(level):
    return any(tile.get('feature') in MAIN_FEATURES for tile in tile_seq(level))


def frame_lines(game):
    frame = game['frame']
    return frame.lines if hasattr(frame, 'lines') else frame['lines']


def recognize_soko(game):
    for y, line, tag in world_data()['soko-recog']:
        if frame_lines(game)[y].startswith(line):
            return tag
    raise RuntimeError('unrecognized sokoban level!')


def infer_branch(game):
    if branch_key(game) in BRANCHES:
        return game
    level = curlvl(game)
    if 5 <= dlvl(game) <= 9 and any(frame_lines(game)[y].startswith(line) for y, line, _ in world_data()['soko-recog'][:2]):
        branch = 'sokoban'
    elif has_features(level):
        branch = 'main'
    elif any(tile.get('feature') == other.get('feature') == 'wall' and tile['glyph'] == other['glyph']
             for row in level['tiles'][::2] for tile in row for other in neighbors(level, tile)
             if p.towards(pos(tile), pos(other)) in p.DIAGONAL):
        branch = 'mines'
    else:
        return game
    return merge_branch_id(game, level['branch-id'], branch)


def in_maze_corridor(level, position):
    return sum(tile.get('feature') == 'wall' for tile in neighbors(level, position)) > 5


def match_level(game, level, blueprint):
    return (('role' not in blueprint or blueprint['role'] == game['player'].get('role'))
            and ('branch' not in blueprint or blueprint['branch'] == branch_key(game, level))
            and ('dlvl' not in blueprint or blueprint['dlvl'] == level['dlvl'])
            and ('tag' not in blueprint or blueprint['tag'] in level['tags']))


def apply_blueprint(level, blueprint):
    from .monster import known_monster
    for q in blueprint.get('undiggable-tiles', ()):
        level = update_at(level, q, lambda tile: tile | {'undiggable': True})
    cutoff = [p.Position(x, y) for x in blueprint.get('cutoff-cols', ()) for y in range(1, 22)]
    cutoff += [p.Position(x, y) for x in range(80) for y in blueprint.get('cutoff-rows', ())]
    for q in cutoff:
        level = update_at(level, q, lambda tile: tile | {'feature': 'rock', 'undiggable': True, 'seen': True})
    for q, feature in blueprint.get('features', ()):
        old = at(level, q).get('feature')
        if feature == 'door-secret':
            feature = feature if old in (None, 'wall') else old
        elif feature != 'cloud' and old is not None:
            feature = old
        level = update_at(level, q, lambda tile: tile | {'feature': feature, 'seen': True})
    for q, monster_type in blueprint.get('monsters', ()):
        level = reset_monster(level, known_monster(q['x'], q['y'], monster_type))
    return level


def level_blueprint(game):
    level = curlvl(game)
    if truth(level.get('blueprint')):
        return game
    for blueprint in world_data()['blueprints']:
        if match_level(game, level, blueprint):
            updated = apply_blueprint(level | {'blueprint': blueprint}, blueprint)
            return assoc_in(game, ['dungeon', 'levels', branch_key(game, updated), updated['dlvl']], updated)
    return game


def diggable_walls(game, level):
    return (not {'rogue', 'sanctum', 'medusa', 'bigroom'}.intersection(level['tags'])
            and ('orcus' in level['tags'] or not (level.get('blueprint') or {}).get('undiggable'))
            and branch_key(game, level) not in {'vlad', 'astral', 'sokoban', 'quest'})


def apply_default_blueprint(game):
    if (in_gehennom(game) and 'votd' not in curlvl_tags(game)
            and any(tile.get('feature') == 'wall' for tile in neighbors(curlvl(game), game['player']))):
        return update_curlvl(game, apply_blueprint, world_data()['geh-maze'])
    return game


def narrow(game, level, start, end):
    start, end = pos(start), pos(end)
    if not p.adjacent(start, end) or p.towards(start, end) not in p.DIAGONAL:
        return None
    shared = set(p.straight_neighbors(start)) & set(p.straight_neighbors(end))
    return all(at(level, q).get('feature') in {'rock', 'wall'}
               or (branch_key(game) == 'sokoban' and t.boulder(at(level, q))) for q in shared)


def edge_passable_walking(game, level, start, end):
    return (p.towards(pos(start), pos(end)) in p.STRAIGHT
            or (start.get('feature') != 'door-open' and end.get('feature') != 'door-open'
                and ((branch_key(game, level) != 'sokoban' and not game['player'].get('thick'))
                     or not narrow(game, level, start, end))))


def passable_walking(game, level, start, end):
    return t.walkable(end) and edge_passable_walking(game, level, start, end)


def real_boulder(level, position):
    monster_type = (monster_at(level, position) or {}).get('type') or {}
    return t.boulder(at(level, position)) and ' mimic' not in (monster_type.get('name') or '')


def room_type(message):
    if message.endswith(', welcome to Delphi!"'):
        return 'oracle'
    if 'Invisible customers are not welcome' in message:
        return 'shop'
    match = re.search(r'Welcome(?: again)? to(?: (?:[A-Z]\S+|a))+ ([a-z -]+)!', message)
    return world_data()['shop-types'].get(match[1]) if match else None


def _shopkeeper_look(game, tile):
    return pos(game['player']) != pos(tile) and tile['glyph'] == '@' and tile['color'] == 'white'


def _boundary(tile):
    return tile.get('feature') in t.DOORS | {'wall'} or truth(tile.get('dug'))


def _missing_wall(level, tile):
    if _boundary(tile):
        return False
    adjacent = neighbors(level, tile)
    vertical = [n for n in adjacent if n['x'] == tile['x']]
    horizontal = [n for n in adjacent if n['y'] == tile['y']]
    return ((sum(map(_boundary, adjacent)) < 3 and any(map(_boundary, vertical)) and any(map(_boundary, horizontal)))
            or all(map(_boundary, vertical)) or all(map(_boundary, horizontal)))


def floodfill_room(game, position, kind):
    level = curlvl(game)
    origin = at(level, position)
    start = pos(origin)
    opened = {pos(q) for q in neighbors(level, origin, include_origin=True)} if _shopkeeper_look(game, origin) else {start}
    closed = set()
    minx = maxx = start.x
    miny = maxy = start.y
    while opened:
        q = opened.pop()
        tile = at(level, q)
        closed.add(q)
        minx, maxx, miny, maxy = min(minx, q.x), max(maxx, q.x), min(miny, q.y), max(maxy, q.y)
        if tile.get('feature') not in t.DOORS | {'wall'} and not _missing_wall(level, tile):
            opened.update(pos(n) for n in neighbors(level, q)
                          if n['glyph'] != ' ' and not truth(n.get('dug')) and n.get('feature') != 'corridor' and pos(n) not in closed)
    for q in p.rectangle(p.Position(minx, miny), p.Position(maxx, maxy)):
        game = update_at(game, q, lambda tile: tile | {'room': kind})
    if kind in set(world_data()['shop-types'].values()) | {'shop'}:
        for q in p.rectangle_boundary(p.Position(minx, miny), p.Position(maxx, maxy)):
            if at(level, q).get('feature') is None:
                game = update_at(game, q, lambda tile: tile | {'feature': 'wall'})
    return game


def reflood_room(game, position):
    tile = at(curlvl(game), position)
    return floodfill_room(game, position, tile['room']) if truth(tile.get('room')) and not truth(tile.get('walked')) else game


def mark_room(game, kind):
    result = add_curlvl_tag(game, kind)
    if kind in set(world_data()['shop-types'].values()) | {'shop'}:
        keepers = [m for m in curlvl_monsters(result) if _shopkeeper_look(result, m)]
        # Original min-key keeps the last minimum on ties.
        if keepers:
            keeper = min(reversed(keepers), key=lambda m: p.distance(pos(result['player']), pos(m)))
            result = floodfill_room(result, keeper, kind)
    if p.adjacent(pos(game['last-position']), pos(game['player'])):
        result = update_at(result, game['last-position'], lambda tile: tile | {'room': None})
    return result


def infer_tags(game):
    level, branch = curlvl(game), branch_key(game)
    depth, tags = dlvl(level), curlvl_tags(game)
    tiles = tuple(tile_seq(level))
    result = game
    def cell(x, y):
        return at(level, p.Position(x, y))
    def feature(x, y):
        return cell(x, y).get('feature')
    def water_or_monster(x, y):
        return feature(x, y) == 'pool' or monster_at(level, p.Position(x, y)) is not None
    def tag(*values):
        nonlocal result
        result = add_curlvl_tag(result, *values)
    last = game.get('last-state') or {}
    same_level = last.get('dlvl') == game['dlvl']
    previous_monsters = curlvl_monsters(last) if same_level else ()
    def previously_seen(name):
        return any((m.get('type') or {}).get('name') == name for m in previous_monsters)
    if branch == 'main' and 21 <= depth <= 28:
        if not {'medusa-1', 'medusa-2'}.intersection(tags):
            if any(feature(3, y) == 'floor' for y in range(2, 21)) and all(water_or_monster(2, y) for y in range(2, 21)):
                tag('medusa', 'medusa-1')
            if (not any(feature(3, y) == 'floor' for y in range(2, 21))
                    and all(feature(7, y) == 'pool' for y in (15, 16, 17))
                    and feature(8, 15) == feature(8, 17) == 'wall'):
                tag('medusa', 'medusa-2')
        if 'medusa' not in tags and same_level and (previously_seen('Medusa') or all(water_or_monster(2, y) for y in range(3, 15))):
            tag('medusa')
    if (branch == 'main' and 25 <= depth <= 29 and 'castle' not in tags
            and (feature(14, 12) in {'drawbridge-lowered', 'drawbridge-raised'}
                 or any(all(feature(x, y) == 'pool' for x in range(8, 16)) and feature(7, y) == 'wall' for y in (20, 4)))):
        tag('castle')
    if branch == 'sokoban' and not any(name.startswith('soko-') for name in tags if isinstance(name, str)):
        soko = recognize_soko(game)
        tag(soko)
        if soko in {'soko-4a', 'soko-4b'}:
            tag('end')
    if branch == 'main' and 10 <= depth <= 12 and 'bigroom' not in tags:
        for row in (8, 16):
            count = 0
            for x in range(3, 78):
                if feature(x, row) == 'corridor':
                    break
                count += feature(x, row) == 'floor' or monster_at(level, p.Position(x, row)) is not None
            if count > 45:
                tag('bigroom')
                break
    if branch == 'main' and 5 <= depth <= 9 and same_level and previously_seen('Oracle'):
        tag('oracle')
    if branch == 'main' and 36 <= depth <= 47 and 'wiztower-level' not in tags:
        inner = [at(level, q) for q in world_data()['wiztower-inner-boundary']]
        boundary = [at(level, q) for q in world_data()['wiztower-boundary']]
        if (any(q.get('undiggable') for q in inner)
                or (not any(q.get('feature') == 'floor' for q in inner)
                    and sum(q.get('feature') == 'wall' or truth(q.get('dug')) for q in boundary) > 20
                    and sum(q.get('feature') == 'floor' and not truth(q.get('dug')) for q in boundary) < 5)):
            tag('wiztower-level')
    features = has_features(level)
    if 5 <= depth <= 9 and branch == 'mines' and 'minetown' not in tags and features:
        tag('minetown')
    if 5 <= depth <= 9 and feature(3, 2) == 'stairs-up' and 'minetown' in tags and 'minetown-grotto' not in tags:
        tag('minetown-grotto')
    if (27 <= depth <= 36 and 'asmodeus' not in tags
            and ((any(q.get('undiggable') for q in tiles) and feature(27, 13) == 'stairs-down')
                 or all(cell(66, y)['glyph'] == '-' for y in (10, 9))
                 or all(cell(66, y)['glyph'] == '-' for y in (14, 15)) or feature(66, 12) in t.DOORS)):
        tag('asmodeus')
    if 29 <= depth <= 36 and 'juiblex' not in tags and sum(q.get('feature') == 'pool' for q in tiles) > 24:
        tag('juiblex')
    if 31 <= depth <= 38 and 'baalzebub' not in tags:
        walls = ((30, 10), (35, 10), (30, 11), (35, 11), (30, 13), (35, 13), (30, 14), (35, 14))
        if ((all(feature(x, y) != 'wall' for x in (31, 32, 33, 34) for y in (11, 13))
             and all(feature(x, y) == 'wall' and not truth(cell(x, y).get('dug')) for x, y in walls))
                or (feature(72, 12) == 'stairs-down' and feature(70, 12) in t.DOORS)):
            tag('baalzebub')
    if (branch == 'main' and 40 <= depth <= 51 and 'fake-wiztower' not in tags
            and any(at(level, q).get('feature') == 'pool' for q in world_data()['fake-wiztower-water'])):
        tag('fake-wiztower')
    end_level = get_level(game, 'main', 'end')
    if branch == 'main' and depth >= 40 and 'sanctum' not in tags and end_level and dlvl(end_level) + 1 == depth:
        tag('sanctum')
    if branch in {'wiztower', 'vlad'} and not {'bottom', 'middle', 'end'}.intersection(tags):
        tag({0: 'bottom', 1: 'middle', 2: 'end'}.get(dlvl_number(next(iter(get_branch(game, branch)))) - depth))
    if 10 <= depth <= 13 and branch == 'mines':
        if (not {'minesend-1', 'minesend-2', 'minesend-3'}.intersection(tags) and feature(38, 8) == 'stairs-up'
                and ((all(feature(x, 7) == 'floor' for x in range(35, 42))
                      and all(feature(x, 6) == 'wall' for x in range(35, 42)))
                     or sum(bool(q.get('undiggable')) for q in tiles) > 2)):
            tag('minesend-1')
        if 'end' not in tags and features:
            tag('end')
    return result
