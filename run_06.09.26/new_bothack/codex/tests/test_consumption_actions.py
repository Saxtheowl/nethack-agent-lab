from copy import deepcopy
import pytest
from bothack.actions import Slot, action
from bothack.runtime import Runtime
from tests.test_actions import spec, plain


@pytest.mark.oracle
@pytest.mark.parametrize('target', [Slot('a'), 'a', 'a food ration', 'a newt corpse'])
@pytest.mark.parametrize('steps', [
    [('eat-it', ['a'])],
    [('eat-it', ['a food ration'])],
    [('eat-it', ['a newt corpse']), ('eat-what', ['Which?'])],
    [('message', ["You don't have anything to eat."])],
    [('message', ['You finish eating.']), ('eat-what', ['Which?'])],
])
def test_eating_source_and_updates(oracle, target, steps):
    compare(oracle, action('eat', target), steps)


@pytest.mark.oracle
@pytest.mark.parametrize('target', [Slot('a'), 'a', 'a newt corpse'])
@pytest.mark.parametrize('message', [
    'You have a feeling of reconciliation.',
    'You glimpse a four-leaf clover at your feet.',
    'You think something brushed your foot.',
    'You see crabgrass at your feet.',
    'You are not standing on an altar.', 'Nothing happens.',
])
def test_sacrifice_source_and_prayer(oracle, target, message):
    compare(oracle, action('offer', target), [('sacrifice-it', ['a newt corpse']),
                                           ('sacrifice-what', ['Which?']), ('message', [message])])


@pytest.mark.oracle
@pytest.mark.parametrize('target', [Slot('a'), Slot('.')])
@pytest.mark.parametrize('state', [[], ['hallu'], ['blind'], ['ext-blind']])
def test_drinking_source_and_updates(oracle, target, state):
    compare(oracle, action('quaff', target), [('drink-here', ['fountain']),
                                           ('drink-what', ['Which?'])], state)


def compare(oracle, selected, steps, state=()):
    initial = {'turn': 100, 'tried': [], 'player': {'state': list(state), 'inventory': {
        'a': {'name': 'ruby potion'}}}}
    context = Runtime(lambda _: None, deepcopy(initial))
    context.game['tried'] = set()
    calls = []
    context.update_inventory = lambda: calls.append(['update-inventory'])
    context.possible_autoid = lambda slot: calls.append(['possible-autoid', slot])
    def update_tile():
        calls.append(['update-tile'])
        return 'deferred-tile'
    context.update_tile = update_tile
    handler = selected.handler(context)
    results = [getattr(handler, name.replace('-', '_'))(*args) for name, args in steps]
    context.game['player']['state'] = set(state)
    assert plain(dict(results=results, game=context.game, calls=calls,
                      **{'handler-map': False})) == oracle.call('action-handler', spec(selected), initial, steps)


def test_slot_validation():
    for value in ('', 'ab', None, 1):
        with pytest.raises(ValueError):
            Slot(value)
    assert Slot('a') == 'a'
    assert deepcopy(Slot('a')).__class__ is Slot


@pytest.mark.oracle
@pytest.mark.parametrize('kind,method', [('wear', 'wear-what'), ('puton', 'put-on-what'),
                                       ('remove', 'remove-what'), ('takeoff', 'take-off-what')])
def test_typed_slots_in_equipment(oracle, kind, method):
    compare(oracle, action(kind, Slot('a')), [(method, ['Which?'])])


@pytest.mark.oracle
@pytest.mark.parametrize('messages', [
    ['The flow reduces to a trickle.'],
    ['Hey, stop using that fountain!'],
    ['The flow reduces to a trickle.', 'The flow reduces to a trickle.'],
    ['This water is refreshing.'],
])
def test_fountain_memory(oracle, messages):
    from tests.test_game_events import EffectContext
    from tests.test_world import plain, summary
    from bothack import dungeon as d
    context = EffectContext()
    context.possible_autoid = lambda slot: context.calls.append(['autoid', slot])
    selected = action('quaff', Slot('.'))
    handler = selected.handler(context)
    for message in messages:
        handler.message(message)
    actual = dict(player=context.game['player'], level=summary(d.curlvl(context.game)),
                  prayer=context.game.get('last-prayer'), angry=context.game.get('god-angry'), calls=context.calls)
    assert plain(actual) == oracle.call('game-events', messages, spec(selected))
