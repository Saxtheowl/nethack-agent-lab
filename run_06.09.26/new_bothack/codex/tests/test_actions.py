"""Compare action bytes and handler effects with the pinned original."""
from copy import deepcopy
from pathlib import Path
import re
from types import SimpleNamespace
import pytest
from bothack.actions import Action, SPECS, action, with_handler, search, enhance_all


def spec(a):
    return [SPECS[a.kind][0], [spec(v) if isinstance(v, Action) else v for v in a.args]]


def plain(value):
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


@pytest.mark.oracle
def test_record_coverage(oracle):
    source = Path(__file__).resolve().parents[1] / 'upstream/BotHack/src/bothack/actions.clj'
    actual = dict(re.findall(r'\(defaction (\w+) \[([^\]]*)\]', source.read_text()))
    assert {name: fields for name, fields, _ in SPECS.values()} == actual


@pytest.mark.oracle
@pytest.mark.parametrize('kind', SPECS)
def test_triggers(oracle, kind):
    values = {'dir': 'NW', 'cnt': 8, 'pos': {'x': 40, 'y': 10}, 'slot': 'a',
              'name': 'STASH', 'qty': 3, 'label-or-list': ['a dagger'],
              'slot-or-label': 'a', 'action': action('search'), 'n': 10,
              'item-slot': 'a', 'potion-slot': 'b', 'what': 'Elbereth',
              'append?': False, 'shk': {'x': 39, 'y': 10}}
    a = action(kind, *(values[field] for field in SPECS[kind][1].split()))
    assert a.trigger() == oracle.call('action-trigger', spec(a))


@pytest.mark.oracle
def test_all_directions_and_farming_counts(oracle):
    for direction in ('NW', 'N', 'NE', 'W', 'E', 'SW', 'S', 'SE', '.', '<', '>'):
        for kind in ('move', 'attack', 'kick', 'open', 'close', 'chat'):
            a = action(kind, direction)
            assert a.trigger() == oracle.call('action-trigger', spec(a))
        for count in (-1, 0, 1, 30):
            a = action('farmattack', direction, count)
            assert a.trigger() == oracle.call('action-trigger', spec(a))


@pytest.mark.oracle
def test_repeated_and_cursor_boundaries(oracle):
    for a in [search(0), search(-1), search(20), action('repeated', search(3), 2),
              *(action('farlook', {'x': x, 'y': y}) for x in (0, 79) for y in (1, 21))]:
        assert a.trigger() == oracle.call('action-trigger', spec(a))


@pytest.mark.oracle
@pytest.mark.parametrize('a,steps', [
    (action('wait'), []), (action('farmattack', 'E', 10), []),
    (action('pray'), []), (action('repeated', action('pray'), 3), []),
    (action('pay', {'x': 4, 'y': 7}), [('pay-whom', [])]),
    (action('enhance'), [('current-skills', [{}])]),
    (action('wipe'), [('message', ["You've got the glop off."])]),
    (action('wipe'), [('message', ['Your face is already clean.'])]),
    (action('wipe'), [('message', ['You are still blind.'])]),
    (action('wield', 'a'), [('wield-what', ['What do you want to wield?'])]),
    (action('quiver', 'b'), [('ready-what', ['What do you want to ready?'])]),
    (action('name', 'c', 'STASH'), [('name-menu', [{}]), ('name-what', ['Which?']), ('what-name', ['Name?'])]),
])
def test_handler_effects(oracle, a, steps):
    initial = {'turn': 123, 'player': {'state': ['ext-blind', 'conf'], 'can-enhance': True}}
    calls = []
    context = SimpleNamespace(game=deepcopy(initial),
                              update_inventory=lambda: calls.append(['update-inventory']),
                              possible_autoid=lambda slot: calls.append(['possible-autoid', slot]))
    handler = a.handler(context)
    results = [getattr(handler, name.replace('-', '_'))(*values) for name, values in steps]
    expected = oracle.call('action-handler', spec(a), initial, steps)
    # Initial Clojure state is a set; normalize the same field on both sides.
    context.game['player']['state'] = set(context.game['player']['state'])
    assert plain(dict(results=results, game=context.game, calls=calls,
                      **{'handler-map': isinstance(handler, dict)})) == expected


def test_unsupported_handler_is_explicit():
    with pytest.raises(NotImplementedError, match='loot'):
        action('loot').handler(SimpleNamespace(game={}))


def test_attachment_order_and_enhance():
    first, second = object(), object()
    a = with_handler(second, with_handler(first, action('wait'), 10), -1)
    assert a.handlers == ((-1, second), (10, first))
    enhanced = enhance_all()
    assert enhanced.trigger() == '#enhance\n'
    assert enhanced.handlers[0][1].enhance_what({}) == 'a'


@pytest.mark.oracle
@pytest.mark.parametrize('steps', [
    [('message', ['Not carrying anything.'])],
    [('message', ['Not carrying anything except gold.'])],
    [('inventory-list', [{'a': 'a sack', 'c': 'a cursed dagger', 'd': 'a food ration'}])],
    [('inventory-list', [{'a': 'a blessed sack'}])],
    [('inventory-list', [{'b': 'a thoroughly rusty thoroughly corroded long sword named ' + 'X' * 30}])],
    [('inventory-list', [{'b': 'a long sword'}])],
])
def test_inventory_memory(oracle, steps):
    initial = {'turn': 10, 'player': {'state': [], 'inventory': {
        'a': {'name': 'sack', 'buc': 'uncursed', 'items': [{'name': 'food ration'}], 'locked': False},
        'b': {'name': 'long sword', 'in-use': '(weapon in hand)', 'worn': None},
        'c': {'name': 'dagger', 'buc': 'blessed'}, '$': {'name': 'gold piece', 'qty': 100}}}}
    context = SimpleNamespace(game=deepcopy(initial))
    a = action('inventory')
    handler = a.handler(context)
    results = [getattr(handler, name.replace('-', '_'))(*values) for name, values in steps]
    expected = oracle.call('action-handler', spec(a), initial, steps)
    assert plain(dict(results=results, game=context.game, calls=[], **{'handler-map': False})) == expected


@pytest.mark.parametrize('kind,method,args,field,expected', [
    ('wipe', 'message', ['Your face is already clean.'], 'state', {'conf'}),
    ('inventory', 'message', ['Not carrying anything.'], 'inventory', {}),
    ('enhance', 'current_skills', [{}], 'can-enhance', None),
])
def test_handlers_read_current_game(kind, method, args, field, expected):
    old = {'player': {}}
    context = SimpleNamespace(game=old)
    handler = action(kind).handler(context)
    context.game = {'player': {'state': {'conf', 'ext-blind'}, 'inventory': {'a': {}}, 'can-enhance': True}}
    getattr(handler, method)(*args)
    assert context.game['player'][field] == expected
    assert old == {'player': {}}
