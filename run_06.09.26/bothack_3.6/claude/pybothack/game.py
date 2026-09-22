"""Port of bothack.game - representation of the game world."""
import logging
import re

from .actions import (adjust_prayer_timeout, ETEXT_RE, THING_RE, THINGS_RE,
                      recheck_peaceful_status, update_discoveries,
                      update_inventory, update_tile)
from .action import typekw
from .clj import (assoc, assoc_in, conj_set, dissoc, get_in, into_map,
                  select_keys, update, update_in)
from .delegator import Handler
from .dungeon import (add_curlvl_tag, at_curlvl, at_player, branch_entry,
                      branch_key, curlvl, curlvl_monsters, curlvl_tags,
                      dlvl_compare, ensure_curlvl, in_gehennom, at_planes,
                      infer_branch, infer_tags, level_blueprint, map_tiles,
                      monster_at, new_dungeon, next_plane, reflood_room,
                      remove_monster, update_at, update_at_player,
                      update_curlvl, update_monster, PLANES, SUBBRANCHES,
                      apply_default_blueprint, dlvl_number, get_level, dlvl)
from .fov import update_fov, visible
from .frame import looks_engulfed
from .handlers import (update_at_player_when_known, update_before_action,
                       update_on_known_position)
from .item import price_id
from .itemid import (add_observed_cost, appearance_of, item_name, know_id,
                     new_discoveries)
from .level import tile_seq
from .monster import (demon_lord, guard, high_priest, medusa, new_monster,
                      typename)
from .montype import name_to_monster
from .player import (blind, hallu, have_intrinsic, inventory_slot, new_player,
                     update_player, add_intrinsic, remove_intrinsic)
from .position import (Pos, adjacent, at, in_direction, including_origin,
                       neighbors, position, rectangle)
from .sokoban import initial_boulders
from .tile import (altar_p, blank, boulder, corridor_p, door, item as tile_item,
                   monster as tile_monster, parse_tile, rock_p, shop, sink_p,
                   stairs_down_p, mark_death)
from .tracker import filter_visible_uniques, track_monsters
from .util import (find_first, less_than, more_than, re_first_group,
                   re_first_groups, re_seq, str_kw)

log = logging.getLogger('bothack.game')


def _update_game_status(game, status):
    res = dict(game)
    for k in game.keys():
        if k in status:
            res[k] = status[k]
    return res


def _update_by_botl(game, status):
    g = assoc(game, 'dlvl', status['dlvl'])
    g = assoc(g, 'player', update_player(g['player'], status))
    return _update_game_status(g, status)


def _rogue_ghost(game, level, tile):
    if 'rogue' not in level['tags'] or blind(game['player']):
        return False
    if get_in(game, ['frame', 'lines', tile['y'], tile['x']]) != ' ':
        return False
    if not adjacent(game['player'], tile):
        return False
    if tile.get('feature') and not rock_p(tile):
        return True
    if tile.get('item-glyph'):
        return True
    nbrs = neighbors(level, tile)
    return bool(less_than(2, [t for t in nbrs
                              if t.get('feature') is None or rock_p(t)
                              or corridor_p(t) or door(t)])
                and less_than(2, [t for t in nbrs if door(t)]))


def _update_visible_tile(game, level, tile):
    from .tile import boulder as _boulder
    dug = tile.get('dug')
    if (branch_key(game) == 'mines'
            and not any(t in level['tags'] for t in ('end', 'minetown'))
            and (corridor_p(tile)
                 or (any(t.get('dug') or corridor_p(t)
                         for t in neighbors(level, tile))
                     and (_boulder(tile)
                          or (tile['glyph'] == '*'
                              and tile.get('color') is None))))):
        dug = True
    if (branch_key(game) in ('water', 'air') and not rock_p(tile)
            and blank(tile)):
        feature = 'floor'
    elif (blank(tile) and tile.get('feature') is None
          and not _rogue_ghost(game, level, tile)):
        feature = 'rock'
    else:
        feature = tile.get('feature')
    return assoc(tile, 'seen', tile.get('seen') or (not _boulder(tile) or None),
                 'dug', dug, 'feature', feature)


def _update_explored(game):
    level = curlvl(game)

    def f(tile):
        if visible(game, level, tile):
            return _update_visible_tile(game, level, tile)
        return tile
    return update_curlvl(game, lambda l: assoc(l, 'tiles',
                                               map_tiles(f, l['tiles'])))


def _soko_mimic(game, level, tile):
    sokotag = None
    for t in ('soko-4a', 'soko-4b'):
        if t in level['tags']:
            sokotag = t
    if not sokotag:
        return False
    player = game['player']
    last_action = game.get('last-action*')
    return bool(
        get_in(game, ['frame', 'lines', tile['y'], tile['x']]) == '8'
        and not tile.get('pushed')
        and not (typekw(last_action) == 'move'
                 and boulder(at_curlvl(game['last-state'], player))
                 and position(in_direction(player, last_action.get('dir')))
                 == position(tile)
                 and adjacent(player, tile))
        and Pos(tile['x'], tile['y']) not in initial_boulders[sokotag])


def _gather_monsters(game, frame):
    # `(into {} (map monster-entry (tile-seq level) …))` - `into` builds
    # through a transient array map, which keeps the scan order and promotes
    # to a hash map from the 9th entry.  A plain dict plus `clj_vals` would
    # give the *reverse* (the persistent-assoc rule), which changes which
    # monster `examine-monsters` farlooks and how `track-monsters` pairs
    # snapshots.  See clj.CljMap and the `maporder` differential cases.
    level = curlvl(game)
    rogue = 'rogue' in level['tags']
    soko = branch_key(game) == 'sokoban'
    pairs = []
    glyph_lines = frame.lines[1:]
    color_lines = frame.colors[1:]
    for tile in tile_seq(level):
        y, x = tile['y'] - 1, tile['x']
        glyph = glyph_lines[y][x]
        color = color_lines[y][x]
        if position(tile) == position(game['player']):
            continue
        if not ((rogue and _rogue_ghost(game, level, tile))
                or (soko and _soko_mimic(game, level, tile))
                or tile_monster(glyph, color)):
            continue
        mon = new_monster(tile['x'], tile['y'], game['turn'], glyph, color)
        if typename(mon) == "gremlin" and game.get('gremlins-peaceful') \
                is not None:
            pairs.append((position(tile),
                          assoc(mon, 'peaceful', game['gremlins-peaceful'])))
        elif soko and glyph == '8':
            pairs.append((position(tile),
                          assoc(mon, 'peaceful', False, 'type',
                                name_to_monster("giant mimic"))))
        else:
            pairs.append((position(tile), mon))
    return into_map(pairs)


def _parse_map(game, frame):
    g = update_curlvl(game, lambda l: assoc(l, 'monsters',
                                            _gather_monsters(game, frame)))
    g = remove_monster(g, game['player'])
    glyph_rows = frame.lines[1:]
    color_rows = frame.colors[1:]
    return update_curlvl(g, lambda l: assoc(
        l, 'tiles', map_tiles(parse_tile, l['tiles'], glyph_rows, color_rows)))


def _update_dungeon(game, frame):
    cursor = frame.cursor
    turn = game['turn']
    g = _parse_map(game, frame)
    g = infer_branch(g)
    g = infer_tags(g)
    g = level_blueprint(g)
    g = reflood_room(g, cursor)
    g = update_at(g, cursor, lambda t: dissoc(t, 'blocked'))
    g = update_at(g, cursor, lambda t: update(t, 'first-walked',
                                              lambda f: f if f else turn))
    return update_at(g, cursor, lambda t: assoc(t, 'walked', turn))


def _update_map(game, frame):
    if looks_engulfed(frame):
        return assoc_in(game, ['player', 'engulfed'], True)
    g = assoc_in(game, ['player', 'engulfed'], False)
    g = _update_dungeon(g, frame)
    g = update_fov(g, frame.cursor)
    g = track_monsters(g, game)
    g = remove_monster(g, game['player'])
    return _update_explored(g)


def _level_msg(msg):
    for pat, tag in [
        (r"You enter what seems to be an older, more primitive world\.",
         'rogue'),
        (r"The odor of burnt flesh and decay pervades the air\.", 'votd'),
        (r"Look for a \.\.\.ic transporter\.", 'quest'),
        (r"So be it\.", 'gehennom'),
        (r"Through clouds of sulphurous gasses, you see a rock palisade|"
         r"Once again, you stand in sight of Lord Surtur's lair", 'end'),
        (r"You feel your mentor's presence; perhaps .*is nearby.|"
         r"You sense the presence of |"
         r"In your mind, you hear the taunts of Ashikaga Takauji", 'end'),
    ]:
        if re_seq(pat, msg):
            return tag
    return None


def prayer_timeout(game):
    from .player import have
    if (at_planes(game) or 'sanctum' in curlvl_tags(game)
            or have(game, {"Amulet of Yendor", "Book of the Dead"})):
        return 4000
    return 1300


def prayer_interval(game):
    return game['turn'] - (game.get('last-prayer')
                           if game.get('last-prayer') is not None else -900)


def can_pray(game):
    from .rules36 import prayer_blocked
    tile = at_player(game)
    if in_gehennom(game):
        return False
    if prayer_blocked(game):
        return False
    if altar_p(tile) and game['player']['alignment'] != tile.get('alignment'):
        return False
    return prayer_timeout(game) < prayer_interval(game)


WELCOME_RE = (r"welcome to NetHack!  You are a.* (\w+ \w+)\.|"
              r".* (\w+ \w+), welcome back to NetHack!")

RACES = {"dwarven": 'dwarf', "elven": 'elf', "gnomish": 'gnome'}


def set_race_role_handler(bh):
    h = Handler()

    def message(text):
        g = re_first_groups(WELCOME_RE, text)
        if not g:
            return
        s = find_first(lambda x: x is not None, g)
        if not s:
            return
        parts = s.split(" ")
        race, role = [RACES.get(p, str_kw(p)) for p in parts]
        log.debug("player role: %s - race: %s", role, race)
        from .player import initial_intrinsics
        bh.game.swap(lambda gm: update_in(
            gm, ['player'],
            lambda p: assoc(p, 'role', role, 'race', race, 'intrinsics',
                            frozenset(initial_intrinsics(role)
                                      | initial_intrinsics(race)))))
        from .handlers import deregister_handler
        deregister_handler(bh, h)
    h.message = message
    return h


def _move_action(game):
    return typekw(game.get('last-action*')) in ('move', 'autotravel')


def _moved(game):
    return (not game.get('last-position')
            or game['last-position'] != position(game['player']))


def _update_portal_range(game, temp):
    player = game['player']
    dist = {"hot": 3, "very warm": 8, "warm": 12}[temp]
    in_range = set(rectangle(Pos(player['x'] - dist, player['y'] - dist),
                             Pos(player['x'] + dist, player['y'] + dist)))
    return update_curlvl(game, lambda l: assoc(
        l, 'tiles',
        map_tiles(lambda t: (t if position(t) in in_range
                             else assoc(t, 'walked', 1)), l['tiles'])))


def _portal_handler(bh, level, new_dlvl):
    game = bh.game
    if new_dlvl == "Astral Plane":
        log.debug("entering astral")
        return game.swap(assoc, 'branch-id', 'astral')
    if branch_key(game.deref(), level) in SUBBRANCHES:
        log.debug("leaving subbranch via portal")
        return game.swap(assoc, 'branch-id', 'main')
    if new_dlvl[:4] == "Home":
        log.debug("entering quest portal")
        return game.swap(assoc, 'branch-id', 'quest')
    if new_dlvl == "Fort Ludios":
        log.debug("entering ludios")
        return game.swap(assoc, 'branch-id', 'ludios')
    n = dlvl_number(new_dlvl)
    if n is not None and n > 35:
        log.debug("entering wiztower portal")
        return game.swap(assoc, 'branch-id', 'wiztower')
    return None


def update_fleeing(game, desc):
    res = game
    for m in curlvl_monsters(game):
        if adjacent(game['player'], m) and desc == typename(m):
            res = update_monster(res, m, lambda mm: assoc(mm, 'fleeing', True))
    return res


def _mark_temple(game):
    player = game['player']
    level = curlvl(game)
    tile = at(level, player)
    align = tile.get('alignment')
    from .monster import priest
    if (align and altar_p(tile)
            and any(priest(m) and m.get('peaceful')
                    for m in level['monsters'].values())):
        res = game
        for t in including_origin(neighbors, level, player):
            res = update_at(res, t, lambda tt: assoc(tt, 'room', 'temple',
                                                     'alignment', align))
        return add_curlvl_tag(res, 'temple')
    return game


def itemid_handler(bh):
    def found_items(items):
        for item in items:
            if not item.get('cost'):
                continue
            if price_id(bh.game.deref(), item):
                # compat36.normalize_label already turns a 3.6 stack price
                # ("2 potions (for sale, 266 zorkmids)") into the unit price
                # ("price 133 zorkmids each"); dividing again produced
                # impossible prices that eliminated every identity
                per_unit = (item['cost'] if item.get('cost-each')
                            else item['cost'] // max(item['qty'], 1))
                bh.game.swap(add_observed_cost, appearance_of(item),
                             per_unit)
    return Handler(found_items=found_items)


def unmark_temple(game):
    return update_curlvl(game, lambda l: assoc(
        l, 'tiles', map_tiles(lambda t: (assoc(t, 'room', None)
                                         if t.get('room') == 'temple' else t),
                              l['tiles'])))


_INTRINSIC_MSGS = [
    (r"You feel a strange mental acuity|You feel in touch with the cosmos|"
     r"thee the gift of Telepathy", 'add', 'telepathy'),
    (r"Your senses fail|You murderer!", 'remove', 'telepathy'),
    (r"You feel in control of yourself|"
     r"You feel centered in your personal space", 'add', 'telecontrol'),
    (r"You feel a momentary chill|You be chillin|You feel cool|"
     r"You are uninjured|You don't feel hot|The fire doesn't feel hot|"
     r"You feel rather warm|You feel mildly (?:warm|hot)|"
     r"enveloped in flames\. But you resist the effects|"
     r"It seems quite tasty", 'add', 'fire'),
    (r"You feel warmer", 'remove', 'fire'),
    (r"You feel full of hot air|You feel warm|duck some of the blast|"
     r"You don't feel cold|The frost doesn't seem cold|"
     r"You feel a (?:little|mild) chill|"
     r"You're covered in frost. But you resist the effects|"
     r"You feel mildly chilly", 'add', 'cold'),
    (r"You feel cooler", 'remove', 'cold'),
    (r"You feel wide awake|You feel awake!", 'add', 'sleep'),
    (r"You feel tired!", 'remove', 'sleep'),
    (r"You feel grounded|Your health currently feels amplified|"
     r"You feel insulated|You feel a mild tingle", 'add', 'shock'),
    (r"You feel conductive", 'remove', 'shock'),
    (r"You feel(?: especially)? healthy|You feel hardy", 'add', 'poison'),
    (r"You feel a little sick", 'remove', 'poison'),
    (r"You feel very jumpy|You feel diffuse", 'add', 'teleport'),
    (r"You feel very firm|You feel totally together", 'add', 'disintegration'),
    (r"You feel sensitive", 'add', 'warning'),
    (r"You feel less sensitive", 'remove', 'warning'),
    (r"You feel stealthy|I grant thee the gift of Stealth", 'add', 'stealth'),
    (r"You feel clumsy", 'remove', 'stealth'),
    (r"You feel less attractive", 'remove', 'aggravate'),
    (r"You feel less jumpy", 'remove', 'teleport'),
    (r"You feel hidden", 'add', 'invisibility'),
    (r"You feel paranoid", 'remove', 'invisibility'),
    (r"You see an image of someone stalking you|You feel transparent|"
     r"You feel very self-conscious|Your vision becomes clear",
     'add', 'see-invis'),
    (r"You feel perceptive!", 'add', 'search'),
    (r"You thought you saw something|You tawt you taw a puttie tat",
     'remove', 'see-invis'),
    (r"You feel quick!|grant thee the gift of Speed|You speed up|"
     r"Your quickness feels more natural", 'add', 'speed'),
    (r"You feel slower|You feel slow!|You slow down|"
     r"Your quickness feels less natural", 'remove', 'speed'),
]


def game_handler(bh):
    game = bh.game
    portal = [None]
    levelport = [None]

    def about_to_choose(_g):
        game.swap(lambda gm: update(gm, 'turn*', lambda t: (t or 0) + 1))
        portal[0] = None
        levelport[0] = None
        game.swap(filter_visible_uniques)
        if sink_p(at_player(game.deref())):
            game.swap(add_curlvl_tag, 'sink')
        if altar_p(at_player(game.deref())):
            game.swap(add_curlvl_tag, 'altar')
            game.swap(_mark_temple)

    def dlvl_changed(old_dlvl, new_dlvl):
        game.swap(assoc, 'gremlins-peaceful', None)
        if old_dlvl == "Dlvl:1" and new_dlvl == "End Game":
            game.swap(assoc, 'branch-id', 'earth')
        # 3.6 port: the status line names only the Astral Plane; arriving
        # there by any other route than the water portal (level teleport in
        # a prepared scenario) must still set the branch
        if (new_dlvl == "Astral Plane"
                and branch_key(game.deref()) != 'astral'):
            game.swap(assoc, 'branch-id', 'astral')
        # the first "End Game" level is always the Plane of Earth; a hero
        # level-teleported there (scenario) was left in 'main' and the
        # planes logic never ran
        if new_dlvl == "End Game" and branch_key(game.deref()) not in (
                'earth', 'air', 'fire', 'water', 'astral'):
            game.swap(assoc, 'branch-id', 'earth')
        if (new_dlvl.startswith("Home ")
                and branch_key(game.deref()) != 'quest'):
            game.swap(assoc, 'branch-id', 'quest')
        if (levelport[0] and branch_key(game.deref()) == 'mines'
                and not dlvl_compare(branch_entry(game.deref(), 'mines'),
                                     new_dlvl) < 0):
            game.swap(assoc, 'branch-id', 'main')
        if portal[0]:
            last = game.deref().get('last-state')
            _portal_handler(bh, curlvl(last), new_dlvl)
            game.swap(lambda g: update_in(
                g, ['dungeon', 'levels', branch_key(last), old_dlvl, 'tags'],
                lambda tags: conj_set(tags, branch_key(g))))

    def redraw(frame):
        game.swap(assoc, 'frame', frame)

    def botl(status):
        old_dlvl = game.deref().get('dlvl')
        new_dlvl = status['dlvl']
        game.swap(_update_by_botl, status)
        if old_dlvl != new_dlvl:
            bh.delegator.dlvl_changed_direct(old_dlvl, new_dlvl)
            update_on_known_position(bh, apply_default_blueprint)
            if old_dlvl and old_dlvl[:4] == "Home" and new_dlvl[:4] == "Dlvl":
                game.swap(assoc, 'branch-id', 'main')  # kicked out of quest
            else:
                game.swap(ensure_curlvl)

    def know_position(frame):
        game.swap(lambda g: update_in(
            g, ['player'], lambda p: assoc(p, 'x', frame.cursor.x,
                                           'y', frame.cursor.y)))

    def full_frame(frame):
        game.swap(_update_map, frame)

    def response_chosen(method, res):
        if method in ('genocide_class', 'genocide_monster'):
            game.swap(lambda g: assoc(g, 'genocided',
                                      conj_set(g['genocided'], res)))
        if method == 'make_wish' and res != "nothing":
            game.swap(adjust_prayer_timeout)
            game.swap(lambda g: update(g, 'wishes', lambda w: w + 1))

    def message_lines(lines):
        if re_seq(THINGS_RE, lines[0]) and _moved(game.deref()):
            game.swap(update_at_player, lambda t: assoc(t, 'new-items', True))
            return
        level = _level_msg(lines[0])
        if level:
            game.swap(add_curlvl_tag, level)

    def message(text):
        from .dungeon import room_type, mark_room
        game.swap(assoc, 'last-topline', text)
        if re.match(r"You (?:can't|cannot) reach the (?:bottom of the "
                    r"(?:pit|abyss)|floor|ground)", text):
            # 3.6: at the edge of a known pit / over a hole - pickup, #loot,
            # engrave... fail without using a turn (big-w01 g027, g033)
            turn = game.deref().get('turn')
            update_at_player_when_known(
                bh, lambda t: assoc(t, 'no-pickup', turn))
        if text in ("You have no free hand to write with!",
                    "You can't reach the floor!",
                    "You can't even hold anything!"):
            # engrave.c refusals, no time passes (big-w01 g039)
            game.swap(lambda g: assoc(g, 'no-engrave-turn', g.get('turn')))
        if text.startswith("You make a motion towards the altar"):
            # engrave.c: the square under the hero is an altar (BotHack
            # would otherwise keep trying to engrave there)
            update_at_player_when_known(
                bh, lambda t: assoc(t, 'feature', 'altar'))
        if text.startswith("You feel like a hypocrite."):
            # 3.6.7 mon.c setmangry: alignment -5; see rules36.prayer_blocked
            game.swap(lambda g: assoc(g, 'hypocrite-turn', g.get('turn')))
            log.warning("hypocrite: attacked from Elbereth at turn %s",
                        game.deref().get('turn'))
        level = _level_msg(text)
        if level:
            update_on_known_position(bh, add_curlvl_tag, level)
            return
        room = room_type(text)
        if room:
            update_before_action(bh, mark_room, room)
            return
        # condp-all: every matching clause fires (no short-circuit)
        if re_seq(r"You have an eerie feeling|A shiver runs down your|"
                  r"You feel like you are being watched", text):
            game.swap(unmark_temple)
        if re_seq(r"can no longer hold you!|You get released!|"
                  r"(?:releases you!|grip relaxes\.)|You kill", text):
            game.swap(assoc_in, ['player', 'grabbed'], False)
        if re_seq(r"(?:grabs|swings itself around) you!", text):
            game.swap(assoc_in, ['player', 'grabbed'], True)
        if re_seq(r"Nothing happens", text):
            if (game.deref()['player'].get('stat-drained')
                    and typekw(game.deref().get('last-action*')) == 'apply'):
                game.swap(assoc_in, ['player', 'stat-drained'], False)
        if re_seq(ETEXT_RE, text) and _move_action(game.deref()):
            update_tile(bh)
        if re_seq(THING_RE, text) and _move_action(game.deref()):
            update_tile(bh)
        g = re_first_group(r"The ([^!]+) turns to flee!", text)
        if g:
            game.swap(update_fleeing, g)
        if re_seq(r"You step onto a level teleport trap!", text):
            levelport[0] = True
        g = re_first_group(r"The (.*) (?:hits|misses|just misses|kicks|"
                           r"casts a spell)[!.]", text)
        if g:
            mt = name_to_monster(g)
            if mt:
                glyph, color = mt['glyph'], mt['color']
                game.swap(recheck_peaceful_status,
                          lambda m: (m['glyph'] == glyph
                                     and m.get('color') == color
                                     and adjacent(game.deref()['player'], m)))
        if re_seq(r"You've been warned", text):
            game.swap(recheck_peaceful_status, guard)
        if re_seq(r" appears before you\.", text):
            game.swap(recheck_peaceful_status, demon_lord)
        if re_seq(r"The venom blinds you|"
                  r"You can't see through all the sticky goop", text):
            game.swap(update_in, ['player', 'state'],
                      lambda s: conj_set(s, 'ext-blind'))
        if re_seq(r"Infidel, you have entered Moloch's Sanctum!", text):
            game.swap(recheck_peaceful_status, high_priest)
        g = re_first_group(r"The Amulet of Yendor.* feels (hot|very warm|warm)",
                           text)
        if g:
            update_on_known_position(bh, _update_portal_range, g)
        if re_seq(r"You are slowing down|Your limbs are stiffening", text):
            game.swap(assoc_in, ['player', 'stoning'], True)
        if re_seq(r"You feel (?:more )?limber|"
                  r"What a pity - you just ruined a future piece", text):
            game.swap(assoc_in, ['player', 'stoning'], False)
        if re_seq(r"You don't feel very well|You are turning a little green|"
                  r"Your limbs are getting oozy|Your skin begins to peel away|"
                  r"You are turning into a green slime", text):
            log.warning("sliming")
        if re_seq(r"You feel you could be more dangerous|"
                  r"You feel more confident", text):
            game.swap(assoc_in, ['player', 'can-enhance'], True)
        if re_seq(r"You feel weaker", text):
            game.swap(assoc_in, ['player', 'stat-drained'], True)
        if re_seq(r"makes you feel better", text):
            game.swap(assoc_in, ['player', 'stat-drained'], True)
        if re_seq(r"You feel feverish", text):
            game.swap(assoc_in, ['player', 'lycantrophy'], True)
        if re_seq(r"You feel purified", text):
            game.swap(assoc_in, ['player', 'lycantrophy'], False)
        if re_seq(r"Your .* feels? somewhat better", text):
            game.swap(assoc_in, ['player', 'leg-hurt'], False)
        if re_seq(r"It's a wall\.", text):
            game.swap(assoc_in, ['player', 'trapped'], False)
        if re_seq(r"Your.* is trapped|bear trap prevents you", text):
            game.swap(assoc_in, ['player', 'trapped'], True)
        if re_seq(r"You sink into the lava", text):
            update_at_player_when_known(bh,
                                        lambda t: assoc(t, 'feature', 'lava'))
        if re_seq(r"You turn into a| slips from your", text):
            update_inventory(bh)
            update_tile(bh)
        if re_seq(r"You are almost hit|The altar glows |power of .*increase|"
                  r"can't go .*here", text):
            update_tile(bh)
        if re_seq(r" activated a magic portal!", text):
            portal[0] = True
            if at_planes(game.deref()):
                game.swap(lambda g: ensure_curlvl(
                    assoc(g, 'branch-id', next_plane(g))))
            else:
                update_at_player_when_known(
                    bh, lambda t: assoc(t, 'feature', 'portal'))
        if re_seq(r"The walls around you begin to bend and crumble!", text):
            game.swap(update_at_player,
                      lambda t: assoc(t, 'feature', 'stairs-down'))
        if re_seq(r"You now wield|gloves vanish|boots disintegrate|"
                  r"shield crumbles away| falls apart|turns to dust|"
                  r"crumbles to dust|boils? and explode|freeze and shatter|"
                  r"breaks? apart and explode|catch(?:es)? fire and burn|"
                  r"Your.* goes out|Your.* has gone out|Your.* is consumed!|"
                  r"Your.* has burnt away| stole |"
                  r"You feel a malignant aura surround you|"
                  r"Your.* (?:rust|corrode[^d]|rot|smoulder)| snatches |"
                  r"Take off your|let me run my fingers|"
                  r"cloud of smoke.* emerges|A curse upon thee|"
                  r"murmurs in your ear|suddenly explodes!|"
                  r"someone is helping you|feel as if you need some help|"
                  r"can't force anything without a ", text):
            update_inventory(bh)
        if re_seq(r" reads a scroll | drinks a .*potion|"
                  r"Your brain is eaten!", text):
            update_discoveries(bh)
        if re_seq(r"shop appears to be deserted", text):
            if dlvl(game.deref()) > 33:
                game.swap(add_curlvl_tag, 'orcus')
        if re_seq(r"You hear the rumble of distant thunder|"
                  r"You hear the studio audience applaud!", text):
            game.swap(assoc_in, ['player', 'protection'], 0)
            game.swap(adjust_prayer_timeout)
        if re_seq(r"You feel guilty about losing your pet|"
                  r"Thou art arrogant, mortal|"
                  r"You feel that.* is displeased\.", text):
            log.warning("god angered: %s", text)
            game.swap(adjust_prayer_timeout)
            game.swap(assoc_in, ['player', 'protection'], 0)
            game.swap(assoc, 'god-angry', True)
        if re_seq(r"This tastes like slime mold juice", text):
            slot = (game.deref().get('last-action') or {}).get('slot')
            if slot:
                item = inventory_slot(game.deref(), slot)
                if (item and item.get('buc') == 'blessed'
                        and item_name(game.deref(), item)
                        == "potion of see invisible"):
                    game.swap(add_intrinsic, 'see-invis')
        for pat, op, intrinsic in _INTRINSIC_MSGS:
            if re_seq(pat, text):
                game.swap(add_intrinsic if op == 'add' else remove_intrinsic,
                          intrinsic)

    return Handler(about_to_choose=about_to_choose, dlvl_changed=dlvl_changed,
                   redraw=redraw, botl=botl, know_position=know_position,
                   full_frame=full_frame, response_chosen=response_chosen,
                   message_lines=message_lines, message=message)


def new_game(rng=None):
    import random
    return {'frame': None, 'player': new_player(), 'dungeon': new_dungeon(),
            'branch-id': 'main', 'dlvl': None,
            'discoveries': new_discoveries(), 'used_names': frozenset(),
            'tried': frozenset(), 'fov': None, 'genocided': frozenset(),
            'wishes': 0, 'turn': None, 'turn*': 0, 'score': None,
            'last-state': None, 'last-action': None, 'last-action*': None,
            'last-position': None, 'last-path': None, 'last-topline': None,
            'last-prayer': None, 'last-branch-no': None,
            'gremlins-peaceful': None, 'god-angry': None,
            'explore-cache': None, 'soko-done': None, 'last-fill': None,
            'autonav-stuck': None, 'last-autonav': None,
            '_poss_cache': {}, '_merge_cache': {},
            'rng': rng if rng is not None else random.Random()}
