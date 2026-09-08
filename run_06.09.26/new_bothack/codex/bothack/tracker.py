"""Monster memory and corpse freshness from tracker.clj, GPL-2.0, 2026-09-07."""
from . import dungeon as d, position as p, tile as t
from .level import pos, at
from .fov import visible
from .state import truth
from .catalog import items_by_name
from .item import corpse


def transfer_pair(game, old, new):
    current = d.monster_at(game, new)
    monster = dict(current if current is not None else old)
    monster.update({key: old[key] for key in ('type', 'cancelled', 'awake', 'first-known') if old.get(key) is not None})
    if monster.get('peaceful') != 'update':
        monster['peaceful'] = old.get('peaceful')
    if pos(old) != pos(monster):
        monster.update(awake=True, **{'just-moved': True})
    old_distance = p.distance_manhattan(pos(game['player']), pos(old))
    new_distance = p.distance_manhattan(pos(game['player']), pos(monster))
    monster['fleeing'] = old.get('fleeing') if old_distance == new_distance else old_distance < new_distance
    if current is None or current['glyph'] == 'I':
        monster['remembered'] = True
    return d.reset_monster(game, monster)


def filter_visible_uniques(game):
    monsters = d.curlvl_monsters(game)
    for monster in monsters:
        mtype = monster.get('type') or {}
        if 'unique' in mtype.get('gen-flags', ()) and not monster.get('remembered'):
            for other in monsters:
                if ((other.get('type') or {}).get('name') == mtype.get('name')
                        and mtype.get('name') != 'Wizard of Yendor' and other.get('remembered')):
                    game = d.remove_monster(game, other)
    return game


def transfer_unpaired(game, monster):
    tile = at(d.curlvl(game), monster)
    player = game['player']
    blind = 'blind' in (player.get('state') or ())
    telepathy = 'telepathy' in (player.get('intrinsics') or ())
    mindless = 'mindless' in (monster.get('type') or {}).get('tags', ())
    warning_obscured = (monster['glyph'] in '12345'
                        and (tile.get('feature') in {'stairs-up', 'stairs-down', 'altar'}
                             or t.boulder(tile) or t.fountain(tile) or truth(tile.get('new-items'))))
    if (not t.monster(tile['glyph'], tile.get('color')) and not (blind and telepathy and not mindless)
            and (not visible(game, monster) or warning_obscured)):
        return d.reset_monster(game, monster | {'remembered': True})
    return game


def track_monsters(new_game, old_game):
    player = new_game['player']
    state = player.get('state') or ()
    if old_game.get('dlvl') != new_game['dlvl'] or 'hallu' in state:
        return new_game
    old = dict(d.curlvl(old_game)['monsters'])
    actual = d.curlvl(new_game)['monsters']
    new = {q: m for q, m in old.items() if q != pos(player)} if 'blind' in state and 'telepathy' not in (player.get('intrinsics') or ()) else dict(actual)
    pairs = {}
    for distance in range(4):
        for q, monster in new.items():
            if not old:
                break
            candidates = [(oldq, candidate) for oldq, candidate in old.items()
                          if ((monster['glyph'] in '12345' and p.distance(pos(monster), pos(candidate)) == 0)
                              or (monster['glyph'] == candidate['glyph'] and monster.get('color') == candidate.get('color')
                                  and monster.get('friendly') == candidate.get('friendly')
                                  and distance == p.distance(pos(monster), pos(candidate))))]
            if len(candidates) == 1:
                oldq, candidate = candidates[0]
                pairs[q] = (candidate, monster)
                del old[oldq]
        if not old:
            break
        new = {q: m for q, m in actual.items() if q not in pairs}
    result = new_game
    for q, monster in old.items():
        if q != pos(player):
            result = transfer_unpaired(result, monster)
    for old_monster, new_monster in pairs.values():
        result = transfer_pair(result, old_monster, new_monster)
    return result


def only_fresh_deaths(tile, corpse_type, turn):
    safe = False
    for death_turn, monster in tile.get('deaths') or ():
        mtype = monster.get('type')
        age = turn - death_turn
        if age > 500 and mtype and mtype.get('name') and mtype != corpse_type:
            continue
        if age >= 30 or not mtype:
            return False
        if ('undead' in mtype.get('tags', ()) and mtype['name'] != 'wraith'
                and corpse_type['name'] in mtype['name']):
            return False
        safe = safe or mtype == corpse_type
    return safe


def fresh_corpse(game, position, item):
    corpse_type = (items_by_name().get(item['name']) or {}).get('monster') if corpse(item) and item.get('qty') == 1 else None
    return bool(corpse_type and (corpse_type.get('permanent')
                or only_fresh_deaths(at(d.curlvl(game), position), corpse_type, game['turn'])))
