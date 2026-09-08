"""Movement, searching and attack handlers from actions.clj (GPL-2.0)."""
import re
from .actions import Responses
from . import dungeon as d, position as p, tile as t
from .level import pos, at, neighbors
from .state import assoc_in, update_in, truth, get_in
from .player import dizzy
from .game import action_kind, action_field
from .game_events import recheck_peaceful

NO_MONSTER = r'You .*(?:thin air|empty water|empty space)'
BOULDER_PLUG = r'The boulder triggers and plugs|You no longer feel the boulder|The boulder fills a pit|The boulder falls into and plugs a hole|You hear the boulder fall'


def mark_trap_here(context):
    return context.update_at_player_when_known(lambda tile: tile | {'feature': tile.get('feature') if tile.get('feature') in t.TRAPS else 'trap'})


def move_message(context, message):
    if re.search(r'.*: "Closed for inventory"', message):
        def mark_shop(game):
            level = d.curlvl(game)
            door = next(q for q in neighbors(level, game['player']) if q.get('feature') in t.DOORS)
            result = d.add_curlvl_tag(game, 'shop-closed')
            for q in neighbors(level, door, include_origin=True, straight=True):
                if pos(q) != pos(game['player']):
                    result = d.update_at(result, q, lambda tile: tile | {'room': 'shop'})
            return result
        return context.update_before_action(mark_shop)
    if re.search(r'You crawl to the edge of the pit\.|You disentangle yourself\.', message):
        return context.mutate(assoc_in, ['player', 'trapped'], False)
    if re.search(r'You fall into \w+ pit!|bear trap closes on your|You stumble into \w+ spider web!|You are stuck to the web\.|You are still in a pit|notice a loose board|You are caught in a bear trap', message):
        context.mutate(assoc_in, ['player', 'trapped'], True)
        return mark_trap_here(context)
    if re.search(r'trap door opens|trap door in the .*and a rock falls on you|trigger a rolling boulder|\(little dart|arrow\) shoots out at you|gush of water hits|tower of flame erupts|cloud of gas', message):
        return mark_trap_here(context)
    if 'You feel a strange vibration' in message:
        context.mutate(d.add_curlvl_tag, 'end')
        return context.update_at_player_when_known(lambda tile: tile | {'vibrating': True})
    if re.search(r"Wait!  That's a .*mimic!", message):
        def clear_mimics(game):
            for q in neighbors(d.curlvl(game), game['player']):
                if q['glyph'] == 'm':
                    game = d.update_at(game, q, lambda tile: tile | {'feature': None})
            return game
        return context.update_before_action(clear_mimics)


def update_trapped(context, old_position):
    def update(game):
        if pos(game['player']) == old_position or t.trap(d.at_player(context.game)):
            return game
        result = assoc_in(game, ['player', 'trapped'], False)
        if truth(get_in(context.game, ['last-state', 'player', 'grabbed'])):
            result = assoc_in(result, ['player', 'grabbed'], False)
        return result
    return context.update_on_known_position(update)


def update_narrow(game, target):
    result = assoc_in(game, ['player', 'thick'], True)
    if d.branch_key(game) != 'sokoban':
        for q in set(p.straight_neighbors(pos(game['player']))) & set(p.straight_neighbors(pos(target))):
            result = d.update_at(result, q, lambda tile: tile | {'feature': 'rock'})
    return result


def door_message(context, direction, text):
    responses = [('The door opens.', 'door-open'), ('You cannot lock an open door.', 'door-open'),
                 ('This door is locked.', 'door-locked'), ('This door is already open.', 'door-open'),
                 ('This doorway has no door.', None), ('You see no door there.', None),
                 ('You succeed in picking the lock.', 'door-closed'), ('You succeed in unlocking the door.', 'door-closed'),
                 ('You succeed in locking the door.', 'door-locked'), ("You can't lock a door with a credit card.", 'door-closed')]
    for pattern, feature in responses:
        if pattern in text:
            return context.mutate(d.update_from_player, direction, lambda tile: tile | {'feature': feature})


def handler(selected, context):
    kind = selected.kind
    if kind == 'search':
        start = context.game['turn']
        def searched(game):
            turns = 1 + game['turn'] - start
            result = game
            for q in neighbors(d.curlvl(game), game['player'], include_origin=True):
                result = d.update_at(result, q, lambda tile: tile | {'searched': tile['searched'] + turns})
            return result
        context.update_on_known_position(searched)
        return None
    if kind == 'sit':
        def message(text):
            if 'not very comfortable...' in text:
                return context.mutate(d.update_at_player, lambda tile: tile | {'feature': None})
            if re.search(r'Having fun sitting on the (floor|air)\?', text):
                return context.mutate(d.update_at_player, lambda tile: tile | {'feature': 'floor'})
            return move_message(context, text)
        return Responses(message=message)
    direction = selected.args[0]
    if kind == 'open':
        return Responses(message=lambda text: door_message(context, direction, text))
    if kind == 'close':
        def message(text):
            features = {'This door is already closed.': 'door-closed', 'This doorway has no door.': None, 'You see no door there.': None}
            if text in features:
                return context.mutate(d.update_from_player, direction, lambda tile: tile | {'feature': features[text]})
        return Responses(message=message)
    if kind == 'kick':
        def message(text):
            if re.search(NO_MONSTER, text):
                return context.mutate(d.update_from_player, direction, t.reset_item)
            if re.search(r'Your .* is in no shape for kicking.', text):
                return context.mutate(assoc_in, ['player', 'leg-hurt'], True)
            if re.search(r"You can't move your leg!|There's not enough room to kick down here", text):
                return context.mutate(assoc_in, ['player', 'trapped'], True)
            for pattern, tag in [('A black ooze gushes up from the drain!', 'pudding'), ('The dish washer returns!', 'foocubus'),
                                  ('You see a ring shining in its midst', 'ring')]:
                if pattern in text:
                    return context.mutate(d.update_from_player, direction, lambda tile: tile | {'tags': set(tile['tags']) | {tag}})
            if 'Thump!' in text:
                return context.mutate(d.update_from_player, direction, lambda tile: tile | {'thump': True})
        return Responses(message=message)
    player = context.game['player']
    old_position = pos(player)
    target = p.in_direction(old_position, direction)
    if kind == 'attack':
        if dizzy(player):
            context.mutate(recheck_peaceful, lambda monster: p.adjacent(pos(player), pos(monster)))
            return None
        if target is not None:
            context.mutate(recheck_peaceful, lambda monster: pos(monster) == target)
            context.mutate(d.update_monster, target, lambda monster: monster | {'awake': True})
            def message(text):
                if re.search(NO_MONSTER, text):
                    context.mutate(d.update_at, target, lambda tile: tile | ({'feature': 'rock'} if tile['glyph'] == ' ' else {'pushed': True}))
                    return context.mutate(d.remove_monster, target)
            return Responses(message=message)
        return None
    if kind == 'move':
        old_game = context.game
        level = d.curlvl(old_game)
        got_message = False
        update_trapped(context, old_position)
        target_tile = at(level, target)
        if (not truth(player.get('trapped')) and direction in p.DIAGONAL
                and (t.item(target_tile['glyph'], target_tile.get('color')) or 'blind' in (player.get('state') or ()))):
            def uncertain_diagonal(game):
                if pos(game['player']) == old_position and not d.monster_at(game, target) and not got_message:
                    last = old_game.get('last-action')
                    if action_kind(last) == 'move' and action_field(last, 'dir') == direction:
                        return d.update_at(game, target, lambda tile: tile | {'feature': 'door-open'})
                return game
            context.update_on_known_position(uncertain_diagonal)
        def message(text):
            nonlocal got_message
            got_message = True
            result = move_message(context, text)
            if truth(result):
                return result
            if dizzy(player):
                return None
            if 'That door is closed' in text:
                return context.mutate(d.update_at, target, lambda tile: tile | {'feature': 'door-closed'})
            if re.search(NO_MONSTER, text):
                return context.mutate(d.remove_monster, target)
            if 'You are carrying too much to get through' in text:
                return context.mutate(update_narrow, target)
            if 'You try to move the boulder, but in vain.' in text:
                beyond = p.in_direction(target, direction)
                tile = at(level, beyond)
                feature = 'door-open' if direction in p.DIAGONAL and t.item(tile['glyph'], tile.get('color')) else 'rock'
                return context.mutate(d.update_at, beyond, lambda tile: tile | {'feature': feature})
            if re.search(BOULDER_PLUG, text):
                return context.mutate(d.update_at, p.in_direction(target, direction), lambda tile: tile | {'feature': 'floor'})
            if "It's a wall." in text:
                return context.mutate(d.update_at, target, lambda tile: tile | {'feature': 'rock' if tile['glyph'] == ' ' else 'wall'})
        def really_attack(text):
            context.update_before_action(d.update_monster, target, lambda monster: monster | {'peaceful': 'update'})
            return None
        return Responses(message=message, really_attack=really_attack)
    raise NotImplementedError(kind)
