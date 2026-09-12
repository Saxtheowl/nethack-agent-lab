"""Port of bothack.tile."""
from .clj import clj_assert
from .clj import assoc, dissoc, update, conj_vec, conj_set
from .item import container
from .position import neighbors
from .util import not_any_fn, re_seq

TRAPS = {'trap', 'antimagic', 'arrowtrap', 'beartrap', 'darttrap', 'firetrap',
         'hole', 'magictrap', 'rocktrap', 'mine', 'levelport', 'pit',
         'polytrap', 'portal', 'bouldertrap', 'rusttrap', 'sleeptrap',
         'spikepit', 'squeaky', 'teletrap', 'trapdoor', 'web', 'statuetrap'}

TRAP_NAMES = {
    "magic portal": 'portal', "level teleporter": 'levelport',
    "teleportation trap": 'teletrap', "bear trap": 'beartrap',
    "falling rock trap": 'rocktrap', "rolling boulder trap": 'bouldertrap',
    "rust trap": 'rusttrap', "magic trap": 'magictrap',
    "anti-magic field": 'antimagic', "polymorph trap": 'polytrap',
    "fire trap": 'firetrap', "arrow trap": 'arrowtrap',
    "statue trap": 'statuetrap', "land mine": 'mine',
    "dart trap": 'darttrap', "sleeping gas trap": 'sleeptrap',
    "spider web": 'web', "web": 'web', "squeaky board": 'squeaky',
    "hole": 'hole', "trap door": 'trapdoor', "pit": 'pit',
    "spiked pit": 'spikepit',
}

_ITEM_GLYPHS = set('")[!?/=+*(`80$%,')


def digit(tile):
    return tile['glyph'].isdigit()


def monster_glyph(glyph):
    return ((glyph.isalnum() and glyph != '8' and glyph != '0')
            or glyph in "&@';:~")


def monster(tile_or_glyph, color=None):
    if color is None and isinstance(tile_or_glyph, (dict, )):
        return monster(tile_or_glyph['glyph'], tile_or_glyph.get('color'))
    if isinstance(tile_or_glyph, dict):
        return monster(tile_or_glyph['glyph'], color)
    glyph = tile_or_glyph
    return bool((glyph != '~' and monster_glyph(glyph)
                 and (color is not None or glyph != ':'))
                or (glyph == '~' and color == 'brown'))


def item(tile_or_glyph, color=None):
    if isinstance(tile_or_glyph, dict):
        return item(tile_or_glyph['glyph'], tile_or_glyph.get('color'))
    glyph = tile_or_glyph
    return bool(glyph in _ITEM_GLYPHS
                or (color is not None and glyph == '_')
                or (color is None and (glyph == ':' or glyph == ']')))


def dug(tile):
    return tile.get('dug')


def unknown(tile):
    return tile.get('feature') is None


def boulder(tile):
    return tile['glyph'] == '8' and tile.get('color') is None


def door(tile):
    return tile.get('feature') in ('door-open', 'door-closed', 'door-locked',
                                   'door-secret')


def drawbridge(tile):
    return tile.get('feature') in ('drawbridge-lowered', 'drawbridge-raised')


def stairs(tile):
    return tile.get('feature') in ('stairs-up', 'stairs-down')


def opposite_stairs(feature):
    clj_assert(feature in ('stairs-up', 'stairs-down'),
               '#{:stairs-up :stairs-down} feature')
    return 'stairs-down' if feature == 'stairs-up' else 'stairs-up'


def has_feature(tile, feature):
    return tile.get('feature') == feature


_FEATURES = list(TRAPS) + [
    'rock', 'floor', 'wall', 'stairs-up', 'stairs-down', 'corridor', 'altar',
    'pool', 'door-open', 'door-closed', 'door-locked', 'door-secret', 'sink',
    'grave', 'throne', 'bars', 'drawbridge-raised', 'drawbridge-lowered',
    'lava', 'ice', 'portal', 'tree', 'trapdoor', 'hole', 'firetrap', 'cloud',
    'polytrap']

_g = globals()
for _f in _FEATURES:
    _name = _f.replace('-', '_') + '_p'
    if _name not in _g:
        _g[_name] = (lambda feature: lambda t: t.get('feature') == feature)(_f)


def fountain_p(tile):
    """Dangerously overused minetown fountains not considered fountains."""
    return (has_feature(tile, 'fountain')
            and 'trickle' not in (tile.get('tags') or ()))


def trap(tile):
    """Clouds on the plane of air are considered a trap."""
    return tile.get('feature') in TRAPS or cloud_p(tile)


def unknown_trap(tile):
    return tile.get('feature') == 'trap'


def blank(tile):
    return tile['glyph'] == ' '


_WALKABLE_FEATURES = {'ice', 'floor', 'altar', 'door-open', 'sink', 'fountain',
                      'corridor', 'throne', 'grave', 'stairs-up',
                      'stairs-down', 'drawbridge-lowered', 'cloud'}


def walkable(tile):
    """Considers unexplored tiles, traps and ice walkable."""
    return (not boulder(tile)
            and (unknown(tile) or trap(tile)
                 or tile.get('feature') in _WALKABLE_FEATURES))


def diagonal_walkable(game, tile):
    return not door_open_p(tile)


def transparent(tile):
    """For unexplored tiles just a guess."""
    return (not boulder(tile)
            and tile.get('feature') not in ('rock', 'wall', 'tree',
                                            'door-closed', 'cloud')
            and bool(tile.get('feature') or tile.get('monster')
                     or tile.get('items')))


def diggable(tile):
    return bool(boulder(tile)
                or (tile.get('feature') in ('rock', 'wall', 'door-closed',
                                            'door-locked', 'door-secret')
                    and 0 < tile['x'] < 79 and 0 < tile['y'] < 21
                    and not tile.get('undiggable')))


def searched(level, tile):
    """How many times the tile has been searched (min over neighbours)."""
    return min(t['searched'] for t in neighbors(level, tile))


def walkable_by(tile, glyph):
    feature = tile.get('feature')
    if glyph not in "I12345EXP" and door(tile):
        newf = 'door-open'
    elif (glyph not in "I12345EX"
          and feature in ('rock', 'wall', 'tree', 'drawbridge-raised')):
        newf = None            # could be just-found door or corridor
    else:
        newf = feature
    return assoc(tile, 'feature', newf,
                 'dug', tile.get('dug') or (diggable(tile) and glyph in "Uphr"))


def _door_or_wall(current, new_color):
    if new_color == 'brown':
        return 'door-open'
    if current == 'door-secret':
        return 'door-secret'
    return 'wall'


def _infer_feature(current, new_glyph, new_color):
    g = new_glyph
    if g == ' ':
        return current
    if g == '.':
        if current in TRAPS:
            return current
        if new_color == 'cyan':
            return 'ice'
        if new_color == 'brown':
            return 'drawbridge-lowered'
        return 'floor'
    if g == '<':
        return 'stairs-up'
    if g == '>':
        return 'stairs-down'
    if g == '\\':
        return 'throne' if new_color == 'yellow' else 'grave'
    if g == '{':
        return 'sink' if new_color is None else 'fountain'
    if g == '}':
        return {'green': 'tree', 'red': 'lava', 'cyan': 'bars',
                'blue': 'pool', 'brown': 'drawbridge-raised'}.get(new_color,
                                                                  current)
    if g == '#':
        if current in TRAPS:
            return current
        if current == 'cloud':
            return 'cloud'
        return 'corridor'
    if g == '_':
        return 'altar' if new_color is None else current
    if g == '~':
        return 'pool'
    if g == '^':
        return current if current in TRAPS else 'trap'
    if g == ']':
        return 'door-closed'
    if g == '|' or g == '-':
        return _door_or_wall(current, new_color)
    return None


def _mark_seen_features(tile):
    if tile.get('feature') in ('wall', 'door-closed', 'pool', 'lava'):
        return assoc(tile, 'seen', True)
    return tile


def _update_feature_with_item(tile):
    if (not tile.get('items')
            and tile.get('feature') in ('rock', 'wall', 'door-closed',
                                        'door-locked', 'drawbridge-raised',
                                        'door-secret', 'pool')):
        return assoc(tile, 'feature', None)
    return tile


def reset_item(tile):
    return assoc(tile, 'item-color', None, 'item-glyph', None, 'items', [],
                 'new-items', False)


def _mark_item(tile, new_glyph, new_color):
    if new_glyph == '8':
        if monster(tile):
            return assoc(tile, 'new-items', True)
        return tile
    if (new_glyph == tile.get('item-glyph')
            and (not tile.get('item-color') or new_color == tile['item-color'])):
        return assoc(tile, 'item-color', new_color)
    return assoc(tile, 'new-items', True, 'item-glyph', new_glyph,
                 'item-color', new_color)


def _update_items(tile, new_glyph, new_color):
    if item(new_glyph, new_color):
        return _mark_item(_update_feature_with_item(tile), new_glyph, new_color)
    if monster(new_glyph, new_color) or new_glyph == ' ':
        return tile
    return reset_item(tile)


def _update_feature(tile, new_glyph, new_color):
    if monster(new_glyph, new_color):
        return walkable_by(tile, new_glyph)
    if item(new_glyph, new_color):
        return tile
    return assoc(tile, 'feature',
                 _infer_feature(tile.get('feature'), new_glyph, new_color))


def _mark_dug_tile(new_tile, old_tile):
    if (new_tile['searched'] == 0
            and old_tile.get('feature') in ('wall', 'rock')
            and new_tile.get('feature') in ('corridor', 'floor')):
        return assoc(new_tile, 'dug', True)
    return new_tile


def parse_tile(tile, new_glyph, new_color):
    if new_color != tile.get('color') or new_glyph != tile['glyph']:
        t = _update_items(tile, new_glyph, new_color)
        t = _update_feature(t, new_glyph, new_color)
        t = _mark_dug_tile(t, tile)
        t = assoc(t, 'glyph', new_glyph, 'color', new_color, 'thump', None)
        return _mark_seen_features(t)
    return tile


SHOP_TYPES = {
    "general store": 'general', "used armor dealership": 'armor',
    "second-hand bookstore": 'book', "liquor emporium": 'potion',
    "antique weapons outlet": 'weapon', "delicatessen": 'food',
    "jewelers": 'gem', "quality apparel and accessories": 'wand',
    "hardware store": 'tool', "rare books": 'book', "lighting store": 'light',
}

SHOPS = set(SHOP_TYPES.values()) | {'shop'}


def shop(tile):
    return tile.get('room') in SHOPS


def temple(tile):
    """Only true near the altar."""
    return tile.get('room') == 'temple'


def mark_death(tile, mon, turn):
    return assoc(tile, 'deaths', conj_vec(tile.get('deaths'), (turn, mon)),
                 'new-items', True)


def lootable_items(tile):
    return [i for c in (tile.get('items') or ())
            if not c.get('cost')
            for i in (c.get('items') or ())]


def e_p(tile):
    """Is Elbereth inscribed on the tile?"""
    return bool(tile.get('engraving') and "Elbereth" in tile['engraving'])


def perma_e(tile):
    return e_p(tile) and tile.get('engraving-type') == 'permanent'


def engravable(tile):
    return (walkable(tile)
            and not (pool_p(tile) or lava_p(tile) or fountain_p(tile)
                     or altar_p(tile) or grave_p(tile))
            and (not tile.get('engraving-type')
                 or tile.get('engraving-type') == 'dust'))


def visited_stairs(tile):
    return stairs(tile) and tile.get('branch-id')


def unexplored(tile):
    return not boulder(tile) and unknown(tile)


def blocked(tile):
    """Stubborn peacefuls."""
    return (tile.get('blocked') or 0) > 12


def initial_tile(x, y):
    return {'x': x, 'y': y, 'glyph': ' ', 'color': None, 'feature': None,
            'seen': False, 'dug': False, 'searched': 0, 'items': [],
            'deaths': [], 'new-items': False, 'tags': frozenset(),
            'item-glyph': None, 'item-color': None, 'first-walked': None,
            'walked': None, 'engraving': None, 'engraving-type': None,
            'room': None}
