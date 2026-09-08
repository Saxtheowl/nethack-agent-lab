from dataclasses import asdict
import pytest
from bothack.runtime import Runtime
from bothack.actions import action, with_handler, Responses
from bothack.position import Position


def runtime(writes):
    context = Runtime(writes.append)
    context.game['player'].update(x=40, y=10)
    context.game['turn'] = 12
    return context


def test_temporary_action_handlers():
    writes = []
    context = runtime(writes)
    choices = iter([action('pay', {'x': 42, 'y': 10}), action('wait')])
    context.register(Responses(choose_action=lambda _: next(choices)))
    context.send('choose-action', context.game)
    context.drain()
    context.send('pay-whom')
    context.drain()
    assert writes[0] == 'p' and writes[1].endswith('.')
    assert context.game['last-action'].kind == 'pay'
    context.send('choose-action', context.game)
    context.drain()
    assert writes[-1] == '.'
    assert all(not hasattr(h, 'pay_whom') for h in context.delegator._ordered())


def test_previous_game_survives_inventory_handler_mutation():
    context = runtime([])
    choices = iter([action('inventory'), action('pray')])
    context.game['player']['inventory'] = {'a': {'name': 'dagger'}}
    context.register(Responses(choose_action=lambda _: next(choices)))
    context.send('choose-action', context.game)
    context.drain()
    previous = context.game['last-state']
    context.send('message', 'Not carrying anything.')
    context.drain()
    assert previous['player']['inventory'] == {'a': {'name': 'dagger'}}
    assert context.game['player']['inventory'] == {}


@pytest.mark.parametrize('event', ['know-position', 'about-to-choose'])
def test_deferred_update_unregisters_after_delivery(event):
    context = runtime([])
    context.update_on_known_position(lambda game: game | {'counter': game.get('counter', 0) + 1})
    context.drain()
    context.send(event, None)
    context.drain()
    context.send('about-to-choose', None)
    context.drain()
    assert context.game['counter'] == 1


def test_missing_handler_prevents_keypress():
    writes = []
    context = runtime(writes)
    context.register(Responses(choose_action=lambda _: action('loot')))
    context.send('choose-action', context.game)
    with pytest.raises(NotImplementedError):
        context.drain()
    assert writes == []
