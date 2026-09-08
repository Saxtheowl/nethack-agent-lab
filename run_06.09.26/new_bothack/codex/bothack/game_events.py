"""Game event handlers from game.clj (GPL-2.0), 2026-09-07."""
from dataclasses import asdict
import re
from . import game as g, dungeon as d, monster as m, position as p, tile as t
from .level import pos, neighbors, tile_seq, at
from .state import assoc_in, update_in, truth
from .tracker import filter_visible_uniques

LEVEL_MESSAGES = (
    (r'You enter what seems to be an older, more primitive world\.', 'rogue'),
    (r'The odor of burnt flesh and decay pervades the air\.', 'votd'),
    (r'Look for a \.\.\.ic transporter\.', 'quest'), (r'So be it\.', 'gehennom'),
    (r"Through clouds of sulphurous gasses, you see a rock palisade|Once again, you stand in sight of Lord Surtur's lair", 'end'),
    (r"You feel your mentor's presence; perhaps .*is nearby.|You sense the presence of |In your mind, you hear the taunts of Ashikaga Takauji", 'end'),
)
PLAYER_MESSAGES = (
    (r'can no longer hold you!|You get released!|(?:releases you!|grip relaxes\.)|You kill', 'grabbed', False),
    (r'(?:grabs|swings itself around) you!', 'grabbed', True),
    (r'You are slowing down|Your limbs are stiffening', 'stoning', True),
    (r'You feel (?:more )?limber|What a pity - you just ruined a future piece', 'stoning', False),
    (r'You feel you could be more dangerous|You feel more confident', 'can-enhance', True),
    (r'You feel weaker', 'stat-drained', True), (r'makes you feel better', 'stat-drained', True),
    (r'You feel feverish', 'lycantrophy', True), (r'You feel purified', 'lycantrophy', False),
    (r'Your .* feels? somewhat better', 'leg-hurt', False), (r"It's a wall\.", 'trapped', False),
    (r'Your.* is trapped|bear trap prevents you', 'trapped', True),
)
INTRINSIC_MESSAGES = (
    (r'You feel a strange mental acuity|You feel in touch with the cosmos|thee the gift of Telepathy', 'telepathy', True),
    (r'Your senses fail|You murderer!', 'telepathy', False),
    (r'You feel in control of yourself|You feel centered in your personal space', 'telecontrol', True),
    (r"You feel a momentary chill|You be chillin|You feel cool|You are uninjured|You don't feel hot|The fire doesn't feel hot|You feel rather warm|You feel mildly (?:warm|hot)|enveloped in flames\. But you resist the effects|It seems quite tasty", 'fire', True),
    (r'You feel warmer', 'fire', False),
    (r"You feel full of hot air|You feel warm|duck some of the blast|You don't feel cold|The frost doesn't seem cold|You feel a (?:little|mild) chill|You're covered in frost. But you resist the effects|You feel mildly chilly", 'cold', True),
    (r'You feel cooler', 'cold', False), (r'You feel wide awake|You feel awake!', 'sleep', True),
    (r'You feel tired!', 'sleep', False),
    (r'You feel grounded|Your health currently feels amplified|You feel insulated|You feel a mild tingle', 'shock', True),
    (r'You feel conductive', 'shock', False), (r'You feel(?: especially)? healthy|You feel hardy', 'poison', True),
    (r'You feel a little sick', 'poison', False), (r'You feel very jumpy|You feel diffuse', 'teleport', True),
    (r'You feel very firm|You feel totally together', 'disintegration', True),
    (r'You feel sensitive', 'warning', True), (r'You feel less sensitive', 'warning', False),
    (r'You feel stealthy|I grant thee the gift of Stealth', 'stealth', True),
    (r'You feel clumsy', 'stealth', False), (r'You feel less attractive', 'aggravate', False),
    (r'You feel less jumpy', 'teleport', False), (r'You feel hidden', 'invisibility', True),
    (r'You feel paranoid', 'invisibility', False),
    (r'You see an image of someone stalking you|You feel transparent|You feel very self-conscious|Your vision becomes clear', 'see-invis', True),
    (r'You feel perceptive!', 'search', True), (r'You thought you saw something|You tawt you taw a puttie tat', 'see-invis', False),
    (r'You feel quick!|grant thee the gift of Speed|You speed up|Your quickness feels more natural', 'speed', True),
    (r'You feel slower|You feel slow!|You slow down|Your quickness feels less natural', 'speed', False),
)
INVENTORY_MESSAGE = r"You now wield|gloves vanish|boots disintegrate|shield crumbles away| falls apart|turns to dust|crumbles to dust|boils? and explode|freeze and shatter|breaks? apart and explode|catch(?:es)? fire and burn|Your.* goes out|Your.* has gone out|Your.* is consumed!|Your.* has burnt away| stole |You feel a malignant aura surround you|Your.* (?:rust|corrode[^d]|rot|smoulder)| snatches |Take off your|let me run my fingers|cloud of smoke.* emerges|A curse upon thee|murmurs in your ear|suddenly explodes!|someone is helping you|feel as if you need some help|can't force anything without a "


def level_message(text):
    return next((tag for regex, tag in LEVEL_MESSAGES if re.search(regex, text)), None)


def recheck_peaceful(game, selector):
    for monster in d.curlvl_monsters(game):
        if selector(monster) and monster['glyph'] not in 'I12345' and monster.get('peaceful') is True:
            game = d.update_monster(game, monster, lambda m: m | {'peaceful': 'update'})
    return game


def unmark_temple(game):
    return d.update_curlvl(game, lambda level: level | {'tiles': d.map_tiles(
        lambda tile: tile | {'room': None} if tile.get('room') == 'temple' else tile, level['tiles'])})


def mark_temple(game):
    tile = d.at_player(game)
    if (tile.get('alignment') and tile.get('feature') == 'altar'
            and any('priest' in (m.get('type') or {}).get('name', '') and truth(m.get('peaceful')) for m in d.curlvl_monsters(game))):
        for q in neighbors(d.curlvl(game), game['player'], include_origin=True):
            game = d.update_at(game, q, lambda t: t | {'room': 'temple', 'alignment': tile['alignment']})
        return d.add_curlvl_tag(game, 'temple')
    return game


def update_portal_range(game, temperature):
    distance = {'hot': 3, 'very warm': 8, 'warm': 12}[temperature]
    player = pos(game['player'])
    return d.update_curlvl(game, lambda level: level | {'tiles': d.map_tiles(
        lambda tile: tile | {'walked': 1} if p.distance(player, pos(tile)) > distance else tile, level['tiles'])})


class RaceRoleHandler:
    def __init__(self, context):
        self.context = context

    def message(self, text):
        match = re.search(r'welcome to NetHack!  You are a.* (\w+ \w+)\.|.* (\w+ \w+), welcome back to NetHack!', text)
        if match:
            race, role = next(v for v in match.groups() if v is not None).split(' ')
            race = {'dwarven': 'dwarf', 'elven': 'elf', 'gnomish': 'gnome'}.get(race, race.lower())
            role = role.lower()
            intrinsics = ({'cold', 'stealth'} if role == 'valkyrie' else set()) | ({'poison'} if race == 'orc' else set())
            self.context.mutate(update_in, ['player'], lambda player: player | {'role': role, 'race': race, 'intrinsics': intrinsics})
            self.context.deregister(self)


class GameEvents:
    def __init__(self, context):
        self.context = context
        self.portal = self.levelport = None

    def about_to_choose(self, game):
        c = self.context
        c.mutate(update_in, ['turn*'], lambda turn: turn + 1)
        self.portal = self.levelport = None
        c.mutate(filter_visible_uniques)
        feature = d.at_player(c.game).get('feature')
        if feature == 'sink':
            c.mutate(d.add_curlvl_tag, 'sink')
        if feature == 'altar':
            c.mutate(d.add_curlvl_tag, 'altar')
            c.mutate(mark_temple)

    def dlvl_changed(self, old, new):
        c = self.context
        c.mutate(lambda game: game | {'gremlins-peaceful': None})
        if old == 'Dlvl:1' and new == 'End Game':
            c.mutate(lambda game: game | {'branch-id': 'earth'})
        if self.levelport and d.branch_key(c.game) == 'mines' and d.dlvl_compare(d.branch_entry(c.game, 'mines'), new) >= 0:
            c.mutate(lambda game: game | {'branch-id': 'main'})
        if self.portal:
            previous = c.game['last-state']
            if new == 'Astral Plane':
                branch = 'astral'
            elif d.branch_key(c.game, d.curlvl(previous)) in d.SUBBRANCHES:
                branch = 'main'
            elif new.startswith('Home'):
                branch = 'quest'
            elif new == 'Fort Ludios':
                branch = 'ludios'
            elif d.dlvl_number(new) > 35:
                branch = 'wiztower'
            else:
                branch = c.game['branch-id']
            c.mutate(lambda game: game | {'branch-id': branch})
            c.mutate(update_in, ['dungeon', 'levels', d.branch_key(previous), old, 'tags'],
                     lambda tags: set(tags or ()) | {d.branch_key(c.game)})

    def redraw(self, frame):
        self.context.mutate(lambda game: game | {'frame': frame})

    def botl(self, status):
        c = self.context
        old, new = c.game.get('dlvl'), status.get('dlvl')
        c.mutate(g.update_by_botl, status)
        if old != new:
            c.delegator.event('dlvl_changed', old, new)
            c.update_on_known_position(d.apply_default_blueprint)
            if old and old.startswith('Home') and new.startswith('Dlvl'):
                c.mutate(lambda game: game | {'branch-id': 'main'})
            else:
                c.mutate(d.ensure_curlvl)

    def know_position(self, frame):
        self.context.mutate(update_in, ['player'], lambda player: player | asdict(frame.cursor))

    def full_frame(self, frame):
        self.context.mutate(g.update_map, frame)

    def response_chosen(self, method, response):
        c = self.context
        if method in {'genocide_class', 'genocide_monster'}:
            c.mutate(update_in, ['genocided'], lambda values: set(values) | {response})
        if method == 'make_wish' and response != 'nothing':
            c.mutate(lambda game: game | {'last-prayer': game['turn'], 'wishes': game['wishes'] + 1})

    def message_lines(self, lines):
        c = self.context
        if not lines:
            raise ValueError('Original message-lines requires a first line')
        moved = c.game.get('last-position') is None or pos(c.game['last-position']) != pos(c.game['player'])
        if re.search(r'Things that (?:are|you feel) here:|You (?:see|feel)', lines[0]) and moved:
            c.mutate(d.update_at_player, lambda tile: tile | {'new-items': True})
        elif level := level_message(lines[0]):
            c.mutate(d.add_curlvl_tag, level)

    def message(self, text):
        c = self.context
        c.mutate(lambda game: game | {'last-topline': text})
        if level := level_message(text):
            c.update_on_known_position(d.add_curlvl_tag, level)
            return
        if room := d.room_type(text):
            c.update_before_action(d.mark_room, room)
            return
        if re.search(r'You have an eerie feeling|A shiver runs down your|You feel like you are being watched', text):
            c.mutate(unmark_temple)
        for pattern, field, value in PLAYER_MESSAGES[:2]:
            if re.search(pattern, text):
                c.mutate(assoc_in, ['player', field], value)
        if 'Nothing happens' in text and c.game['player'].get('stat-drained') and g.action_kind(c.game.get('last-action*')) == 'apply':
            c.mutate(assoc_in, ['player', 'stat-drained'], False)
        if g.action_kind(c.game.get('last-action*')) in {'move', 'autotravel'}:
            if re.search(r'You read: "(.*)"\.', text):
                c.update_tile()
            if re.search(r'You (?:see|feel) here ([^.]+).', text):
                c.update_tile()
        if match := re.search(r'The ([^!]+) turns to flee!', text):
            for monster in d.curlvl_monsters(c.game):
                if p.adjacent(pos(c.game['player']), pos(monster)) and (monster.get('type') or {}).get('name') == match[1]:
                    c.mutate(d.update_monster, monster, lambda m: m | {'fleeing': True})
        if 'You step onto a level teleport trap!' in text:
            self.levelport = True
        if match := re.search(r'The (.*) (?:hits|misses|just misses|kicks|casts a spell)[!.]', text):
            monster_type = m.by_name(match[1])
            if monster_type:
                c.mutate(recheck_peaceful, lambda monster: monster['glyph'] == monster_type['glyph']
                         and monster.get('color') == monster_type.get('color') and p.adjacent(pos(c.game['player']), pos(monster)))
        if "You've been warned" in text:
            c.mutate(recheck_peaceful, lambda monster: 'guard' in (monster.get('type') or {}).get('tags', ()))
        if ' appears before you.' in text:
            c.mutate(recheck_peaceful, lambda monster: all(tag in {'demon', 'prince'} for tag in (monster.get('type') or {}).get('tags', ())))
        if re.search(r"The venom blinds you|You can't see through all the sticky goop", text):
            c.mutate(update_in, ['player', 'state'], lambda values: set(values or ()) | {'ext-blind'})
        if "Infidel, you have entered Moloch's Sanctum!" in text:
            c.mutate(recheck_peaceful, lambda monster: (monster.get('type') or {}).get('name') == 'high priest')
        if match := re.search(r'The Amulet of Yendor.* feels (hot|very warm|warm)', text):
            c.update_on_known_position(update_portal_range, match[1])
        for pattern, field, value in PLAYER_MESSAGES[2:]:
            if re.search(pattern, text):
                c.mutate(assoc_in, ['player', field], value)
        if 'You sink into the lava' in text:
            c.update_at_player_when_known(lambda tile: tile | {'feature': 'lava'})
        if re.search(r'You turn into a| slips from your', text):
            c.update_inventory()
            c.update_tile()
        if re.search(r"You are almost hit|The altar glows |power of .*increase|can't go .*here", text):
            c.update_tile()
        if ' activated a magic portal!' in text:
            self.portal = True
            if d.at_planes(c.game):
                c.mutate(lambda game: d.ensure_curlvl(game | {'branch-id': d.next_plane(game)}))
            else:
                c.update_at_player_when_known(lambda tile: tile | {'feature': 'portal'})
        if 'The walls around you begin to bend and crumble!' in text:
            c.mutate(d.update_at_player, lambda tile: tile | {'feature': 'stairs-down'})
        if re.search(INVENTORY_MESSAGE, text):
            c.update_inventory()
        if re.search(r' reads a scroll | drinks a .*potion|Your brain is eaten!', text):
            c.update_discoveries()
        if 'shop appears to be deserted' in text and d.dlvl(c.game) > 33:
            c.mutate(d.add_curlvl_tag, 'orcus')
        if re.search(r'You hear the rumble of distant thunder|You hear the studio audience applaud!', text):
            c.mutate(assoc_in, ['player', 'protection'], 0)
            c.mutate(lambda game: game | {'last-prayer': game['turn']})
        if re.search(r'You feel guilty about losing your pet|Thou art arrogant, mortal|You feel that.* is displeased\.', text):
            c.mutate(lambda game: game | {'last-prayer': game['turn'], 'god-angry': True})
            c.mutate(assoc_in, ['player', 'protection'], 0)
        for pattern, intrinsic, add in INTRINSIC_MESSAGES:
            if pattern.startswith('You see an image') and 'This tastes like slime mold juice' in text:
                item = c.game['player']['inventory'].get(g.action_field(c.game.get('last-action'), 'slot'))
                if item and item.get('buc') == 'blessed' and c.game['discoveries'].item_id(item).get('name') == 'potion of see invisible':
                    c.mutate(update_in, ['player', 'intrinsics'], lambda values: set(values or ()) | {'see-invis'})
            if re.search(pattern, text):
                c.mutate(update_in, ['player', 'intrinsics'], lambda values: (set(values or ()) | {intrinsic}) if add else (set(values or ()) - {intrinsic}))
