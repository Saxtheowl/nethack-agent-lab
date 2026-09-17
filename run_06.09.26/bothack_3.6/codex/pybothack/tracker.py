"""Port of bothack.tracker - pairing monsters frame-to-frame and tracking
their deaths and corpses."""
import logging

from .clj import (assoc, CljMap, clj_items, clj_keys, clj_vals,
                  dissoc, get_in, update_in)
from .delegator import Handler
from .dungeon import (at_curlvl, curlvl, curlvl_monsters, monster_at,
                      remove_monster, reset_monster, update_at, update_monster)
from .fov import visible
from .handlers import update_before_action
from .item import corpse, single
from .itemtype import name_to_item
from .monster import (mindless, type_map, rodney, typename, undead, unique,
                      unknown_monster)
from .player import blind, hallu, have_intrinsic
from .position import distance, distance_manhattan, in_direction, position
from .tile import (altar_p, boulder, fountain_p, item as tile_item,
                   mark_death, monster as tile_monster, pool_p, stairs)
from .util import find_first, re_first_group, select_some

log = logging.getLogger('bothack.tracker')


def _transfer_pair(game, pair):
    old_monster, mon = pair
    player = game['player']
    cur = monster_at(game, mon)
    m = dict(cur or old_monster)
    m.update(select_some(old_monster, ['type', 'cancelled', 'awake',
                                       'first-known']))
    if mon.get('peaceful') != 'update':
        m['peaceful'] = old_monster.get('peaceful')
    if position(old_monster) != position(mon):
        m['awake'] = True
        m['just-moved'] = True
    d_old = distance_manhattan(player, old_monster)
    d_new = distance_manhattan(player, mon)
    if d_old < d_new:
        m['fleeing'] = True
    elif d_old == d_new:
        m['fleeing'] = old_monster.get('fleeing')
    else:
        m['fleeing'] = False
    if not cur or cur['glyph'] == 'I':
        m['remembered'] = True
    return reset_monster(game, m)


def filter_visible_uniques(game):
    """If a unique monster was remembered and now is visible, remove all
    remembered instances."""
    monsters = curlvl_monsters(game)
    res = game
    for m in monsters:
        if not (unique(m) and not m.get('remembered')):
            continue
        for n in monsters:
            if (typename(m) == typename(n) and not rodney(n)
                    and n.get('remembered')):
                res = remove_monster(res, position(n))
    return res


def _transfer_unpaired(game, unpaired):
    player = game['player']
    tile = at_curlvl(game, unpaired)
    if (not tile_monster(tile)
            and not (blind(player) and have_intrinsic(player, 'telepathy')
                     and not mindless(unpaired))
            and (not visible(game, unpaired)
                 or (unpaired['glyph'] in ('1', '2', '3', '4', '5')
                     and (stairs(tile) or boulder(tile) or fountain_p(tile)
                          or altar_p(tile) or tile.get('new-items'))))):
        return reset_monster(game, assoc(unpaired, 'remembered', True))
    return game


def track_monsters(new_game, old_game):
    """Transfer monster properties greedily from the old snapshot to the new,
    even if the monsters moved slightly."""
    if (old_game.get('dlvl') != new_game['dlvl']
            or hallu(new_game['player'])):
        return new_game
    # The maps stay *persistent* here: `(:monsters level)` is built by `into`
    # and iterates in scan order, while a plain dict copy would fall back to
    # the persistent-assoc rule and reverse it - which decides which old
    # record a new monster is paired with when two are equidistant.
    pairs = CljMap()
    old_monsters = curlvl(old_game)['monsters']
    if (blind(new_game['player'])
            and not have_intrinsic(new_game['player'], 'telepathy')):
        new_monsters = dissoc(old_monsters, position(new_game['player']))
    else:
        new_monsters = curlvl(new_game)['monsters']
    dist = 0
    while dist < 4 and old_monsters:
        if new_monsters:
            p = clj_keys(new_monsters)[0]
            m = new_monsters[p]
            new_monsters = dissoc(new_monsters, p)
            cands = [(cp, n) for cp, n in clj_items(old_monsters)
                     if ((m['glyph'] in ('5', '4', '3', '2', '1') and distance(m, n) == 0)
                         or (m['glyph'] == n['glyph']
                             and m.get('color') == n.get('color')
                             and m.get('friendly') == n.get('friendly')
                             and distance(m, n) == dist))]
            if cands:
                if len(cands) > 1:
                    continue          # ignore ambiguous cases
                cp, cm = cands[0]
                pairs = assoc(pairs, p, (cm, m))
                old_monsters = dissoc(old_monsters, cp)
        else:
            # (apply dissoc (:monsters (curlvl new-game)) (keys pairs))
            new_monsters = dissoc(curlvl(new_game)['monsters'], *clj_keys(pairs))
            dist += 1
    res = new_game
    for m in clj_vals(dissoc(old_monsters, position(new_game['player']))):
        res = _transfer_unpaired(res, m)
    for pair in clj_vals(pairs):
        res = _transfer_pair(res, pair)
    return res


def _mark_kill(game, old_game):
    from .player import dizzy
    if dizzy(old_game['player']) or hallu(old_game['player']):
        return game
    dir_ = (game.get('last-action*') or {}).get('dir')
    if not dir_:
        return game
    level = curlvl(game)
    tile = in_direction(level, old_game['player'], dir_)
    if tile is None:
        return game
    old_monster = (monster_at(curlvl(old_game), tile)
                   or unknown_monster(tile['x'], tile['y'], game['turn']))
    if (tile_item(tile) or tile_monster(tile) or pool_p(tile)
            or blind(game['player'])):
        res = update_at(game, tile, lambda t: dissoc(t, 'blocked'))
        res = update_at(res, tile,
                        lambda t: mark_death(t, old_monster, game['turn']))
        return remove_monster(res, tile)
    return game


def death_tracker(bh):
    def message(msg):
        old_game = bh.game.deref().get('last-state')
        if not old_game:
            return
        if hallu(old_game['player']):
            return
        if re_first_group(r'You (kill|destroy) [^.!]*[.!]', msg):
            update_before_action(bh, _mark_kill, old_game)
    return Handler(message=message)


def _only_fresh_deaths(tile, corpse_type, turn):
    deaths = tile.get('deaths') or []
    relevant = [d for d in deaths
                if not (turn - d[0] > 500 and type_map(d[1]).get(
                    'name') and d[1].get('type') != corpse_type)]
    unsafe = []
    safe = []
    for death_turn, mon in relevant:
        montype = mon.get('type')
        if (turn - death_turn >= 30 or not montype
                or (undead(mon) and montype.get('name') != "wraith"
                    and (corpse_type.get('name') or "")
                    in (montype.get('name') or ""))):
            unsafe.append((death_turn, mon))
        if turn - death_turn < 30 and montype == corpse_type:
            safe.append((death_turn, mon))
    return not unsafe and bool(safe)


def fresh_corpse(game, pos, item):
    if not (corpse(item) and single(item)):
        return False
    it = name_to_item.get(item['name'])
    corpse_type = it.get('monster') if it else None
    if not corpse_type:
        return False
    if corpse_type.get('permanent'):
        return True
    return _only_fresh_deaths(at_curlvl(game, pos), corpse_type, game['turn'])
