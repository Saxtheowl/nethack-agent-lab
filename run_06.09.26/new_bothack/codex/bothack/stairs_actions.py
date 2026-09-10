"""Stair transitions from actions.clj, including original follower ambiguity.

GPL-2.0, 2026-09-09. Updates are deferred until the new player position is known.
"""
import re
from . import dungeon as d
from .actions import Responses
from .state import assoc_in, update_in, truth


def mark_branch_entrance(game, tile, old_game, origin_feature):
    if d.branch_key(game) == 'ludios' or game['dlvl'] == 'Home 1':
        return d.update_at(game, tile, lambda t: t | {'branch-id': 'main'})
    # Original mapcat over monster-at flattens monster records into map entries.
    # :friendly and follower? on those entries both return nil, even with a pet.
    # Consequently the intended surrounding-tile marking branch is never taken.
    return d.update_at(game, tile, lambda t: t | {'branch-id': d.branch_key(old_game)})


def handler(context):
    old_game = context.game
    old_branch = d.branch_key(old_game)
    old_dlvl = old_game['dlvl']
    old_stairs = d.at_player(old_game)
    entered_vlad = False

    def position_known(game):
        if (old_dlvl != game['dlvl'] and old_stairs.get('feature') in {'stairs-up', 'stairs-down'}
                and not truth(old_stairs.get('branch-id'))):
            tile = d.at_player(game)
            game = assoc_in(game, ['dungeon', 'levels', old_branch, old_dlvl, 'tiles',
                                   old_stairs['y'] - 1, old_stairs['x'], 'branch-id'], game['branch-id'])
            return mark_branch_entrance(game, tile, old_game, old_stairs['feature'])
        return game

    context.update_on_known_position(position_known)

    def message(text):
        nonlocal entered_vlad
        if re.search("You can't go down here", text):
            return context.mutate(d.update_at_player, lambda tile: tile | {'feature': None})
        if re.search('heat and smoke are gone.', text):
            entered_vlad = True
            return True
        if re.search('A mysterious force prevents you from descending', text):
            leader = d.curlvl(old_game)['blueprint']['leader']
            return context.mutate(d.update_around, leader, lambda tile: tile | {'walked': None})

    def dlvl_changed(previous_label, new_label):
        game = context.game
        if entered_vlad:
            branch = 'vlad'
        elif old_branch in d.SUBBRANCHES and d.branch_entry(game, old_branch) == new_label:
            branch = 'main'
        else:
            branch = old_stairs.get('branch-id', d.initial_branch_id(game, new_label))
        game = update_in(game, ['dungeon', 'levels', old_branch, previous_label, 'tags'],
                         lambda tags: set(tags or ()) | {branch})
        game = game | {'branch-id': branch}
        match = re.search(r'unknown-([0-9]+)', branch)
        if match:
            game = game | {'last-branch-no': max(game.get('last-branch-no') or 0, int(match[1]))}
        context.game = game
        return game if match else None

    return Responses(message=message, dlvl_changed=dlvl_changed)
