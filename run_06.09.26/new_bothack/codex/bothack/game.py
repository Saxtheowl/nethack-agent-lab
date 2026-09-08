"""World observations translated from game.clj, GPL-2.0, 2026-09-07."""
from . import dungeon as d, level as l, position as p, tile as t, monster as m
from .player import new_player, update_player
from .itemid import Identification
from .catalog import data
from .state import update_in, truth
from .fov import update_fov, visible
from .tracker import track_monsters

FIELDS = 'frame player dungeon branch-id dlvl discoveries used-names tried fov genocided wishes turn turn* score'.split()


def new_game():
    return dict.fromkeys(FIELDS) | {'player': new_player(), 'dungeon': d.new_dungeon(),
            'branch-id': 'main', 'used-names': set(), 'tried': set(), 'turn*': 0,
            'wishes': 0, 'genocided': set(), 'discoveries': Identification()}


def update_by_botl(game, status):
    result = game | {'dlvl': status.get('dlvl'), 'player': update_player(game['player'], status)}
    return result | {key: value for key, value in status.items() if key in result}


def action_kind(action):
    return getattr(action, 'kind', None) if not isinstance(action, dict) else action.get('kind')


def action_field(action, field, default=None):
    if action is None:
        return default
    if isinstance(action, dict):
        return action.get(field, default)
    from .actions import SPECS
    fields = SPECS[action.kind][1].split()
    return action.args[fields.index(field)] if field in fields else action.extra.get(field, getattr(action, field, default))


def prayer_interval(game):
    last = game.get('last-prayer')
    return game['turn'] - (-900 if last is None else last)


def prayer_timeout(game):
    names = {item['name'] for item in game['player']['inventory'].values()}
    return 4000 if d.at_planes(game) or 'sanctum' in d.curlvl_tags(game) or {'Amulet of Yendor', 'Book of the Dead'}.intersection(names) else 1300


def can_pray(game):
    tile = d.at_player(game)
    return (not d.in_gehennom(game)
            and not (tile.get('feature') == 'altar' and tile.get('alignment') != game['player']['alignment'])
            and prayer_timeout(game) < prayer_interval(game))


def rogue_ghost(game, level, tile):
    if ('rogue' not in level['tags'] or 'blind' in (game['player'].get('state') or ())
            or d.frame_lines(game)[tile['y']][tile['x']] != ' '
            or not p.adjacent(l.pos(game['player']), l.pos(tile))):
        return False
    adjacent = l.neighbors(level, tile)
    return ((truth(tile.get('feature')) and tile.get('feature') != 'rock') or truth(tile.get('item-glyph'))
            or (sum(q.get('feature') in {None, 'rock', 'corridor'} | t.DOORS for q in adjacent) < 2
                and sum(q.get('feature') in t.DOORS for q in adjacent) < 2))


def soko_mimic(game, level, tile):
    tag = next((tag for tag in ('soko-4a', 'soko-4b') if tag in level['tags']), None)
    if tag is None or d.frame_lines(game)[tile['y']][tile['x']] != '8' or truth(tile.get('pushed')):
        return False
    action = game.get('last-action*')
    player = l.pos(game['player'])
    if (action_kind(action) == 'move' and t.boulder(l.at(d.curlvl(game['last-state']), player))
            and p.in_direction(player, action_field(action, 'dir')) == l.pos(tile)
            and p.adjacent(player, l.pos(tile))):
        return False
    initial = data()['initial-boulders'][tag]
    return not any(l.pos(q) == l.pos(tile) for q in initial)


def gather_monsters(game, frame):
    level = d.curlvl(game)
    rogue, soko = 'rogue' in level['tags'], d.branch_key(game) == 'sokoban'
    monsters = {}
    for tile in l.tile_seq(level):
        x, y = tile['x'], tile['y']
        glyph, color = frame.lines[y][x], frame.colors[y][x]
        if l.pos(tile) == l.pos(game['player']):
            continue
        if ((rogue and rogue_ghost(game, level, tile)) or (soko and soko_mimic(game, level, tile)) or t.monster(glyph, color)):
            monster = m.new_monster(x, y, game['turn'], glyph, color)
            name = (monster.get('type') or {}).get('name')
            if name == 'gremlin' and game.get('gremlins-peaceful') is not None:
                monster['peaceful'] = game['gremlins-peaceful']
            elif soko and glyph == '8':
                monster.update(peaceful=False, type=m.by_name('giant mimic'))
            monsters[l.pos(tile)] = monster
    return monsters


def parse_map(game, frame):
    monsters = gather_monsters(game, frame)
    result = d.update_curlvl(game, lambda level: level | {'monsters': monsters})
    result = d.remove_monster(result, game['player'])
    return d.update_curlvl(result, lambda level: level | {
        'tiles': d.map_tiles(t.parse_tile, level['tiles'], frame.lines[1:22], frame.colors[1:22])})


def update_visible_tile(game, level, tile):
    branch = d.branch_key(game)
    adjacent = l.neighbors(level, tile)
    dug = tile.get('dug')
    if (branch == 'mines' and not {'end', 'minetown'}.intersection(level['tags'])
            and (tile.get('feature') == 'corridor'
                 or (any(truth(q.get('dug')) or q.get('feature') == 'corridor' for q in adjacent)
                     and (t.boulder(tile) or (tile['glyph'] == '*' and tile.get('color') is None))))):
        dug = True
    feature = tile.get('feature')
    if branch in {'water', 'air'} and feature != 'rock' and tile['glyph'] == ' ':
        feature = 'floor'
    elif tile['glyph'] == ' ' and feature is None and not rogue_ghost(game, level, tile):
        feature = 'rock'
    seen = tile.get('seen') if truth(tile.get('seen')) else None if t.boulder(tile) else True
    return tile | {'seen': seen, 'dug': dug, 'feature': feature}


def update_explored(game):
    level = d.curlvl(game)
    return d.update_curlvl(game, lambda current: current | {'tiles': d.map_tiles(
        lambda tile: update_visible_tile(game, level, tile) if visible(game, tile, level) else tile, current['tiles'])})


def update_dungeon(game, frame):
    result = d.level_blueprint(d.infer_tags(d.infer_branch(parse_map(game, frame))))
    result = d.reflood_room(result, frame.cursor)
    def walked(tile):
        tile = dict(tile)
        tile.pop('blocked', None)
        tile['first-walked'] = tile.get('first-walked') if truth(tile.get('first-walked')) else game['turn']
        tile['walked'] = game['turn']
        return tile
    return d.update_at(result, frame.cursor, walked)


def update_map(game, frame):
    if frame.looks_engulfed:
        return update_in(game, ['player'], lambda player: player | {'engulfed': True})
    result = update_in(game, ['player'], lambda player: player | {'engulfed': False})
    result = update_fov(update_dungeon(result, frame), frame.cursor)
    result = track_monsters(result, game)
    result = d.remove_monster(result, game['player'])
    return update_explored(result)
