import pytest
from bothack import dungeon as d
from bothack.actions import action
from bothack.game import new_game
from bothack.runtime import Runtime
from tests.test_world import plain


@pytest.mark.oracle
@pytest.mark.parametrize('pet', [False, True])
@pytest.mark.parametrize('kind', ['ascend', 'descend'])
@pytest.mark.parametrize('branch,old,new,destination,messages', [
    ('main', 'Dlvl:1', 'Dlvl:2', None, []),
    ('main', 'Dlvl:3', 'Dlvl:4', None, []),
    ('main', 'Dlvl:8', 'Dlvl:7', 'sokoban', []),
    ('mines', 'Dlvl:5', 'Dlvl:6', None, []),
    ('main', 'Dlvl:27', 'Dlvl:26', None, ['The heat and smoke are gone.']),
    ('main', 'Dlvl:1', 'End Game', None, []),
    ('main', 'Dlvl:3', 'Dlvl:3', None, ["You can't go down here."]),
    ('main', 'Dlvl:12', 'Home 1', 'quest', []),
])
def test_stair_transition(oracle, kind, branch, old, new, destination, messages, pet):
    game = new_game() | {'branch-id': branch, 'dlvl': old}
    game['player'] = game['player'] | {'x': 40, 'y': 10}
    game = d.update_at_player(d.ensure_curlvl(game), lambda t: t | {'feature': 'stairs-down'})
    if destination:
        game = d.update_at_player(game, lambda t: t | {'branch-id': destination})
    if pet:
        game = d.reset_monster(game, {'x': 41, 'y': 10, 'friendly': True})
    context = Runtime(lambda _: None, game)
    pending = []
    context.update_on_known_position = lambda f, *args: pending.append((f, args))
    handler = action(kind).handler(context)
    for message in messages:
        handler.message(message)
    context.game = context.game | {'dlvl': new}
    handler.dlvl_changed(old, new)
    context.game = d.update_at_player(d.ensure_curlvl(context.game), lambda t: t | {'feature': 'stairs-up'})
    for function, args in pending:
        context.mutate(function, *args)
    game = context.game
    old_level = game['dungeon']['levels'][branch][old]
    actual = {'branch': game['branch-id'], 'last-branch-no': game.get('last-branch-no'),
              'old-tags': old_level['tags'], 'old-stairs': old_level['tiles'][9][40],
              'new-stairs': d.at_player(game),
              'neighbor': d.at(d.curlvl(game), {'x': 41, 'y': 10})}
    assert plain(actual) == oracle.call('stairs-transition', branch, old, new, destination, messages, pet)
