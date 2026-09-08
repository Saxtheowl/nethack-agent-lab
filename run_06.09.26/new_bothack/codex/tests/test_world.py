"""World model and original blueprint parity."""
from dataclasses import asdict, is_dataclass
import random
import pytest
from bothack import dungeon as d
from bothack import level as l
from bothack.state import assoc_in


def plain(value):
    if is_dataclass(value):
        return plain(asdict(value))
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    return value


def patched(label, branch, tags=(), patches=()):
    level = l.new_level(label, branch) | {'tags': set(tags)}
    for x, y, values in patches:
        level = d.update_at(level, {'x': x, 'y': y}, lambda tile: tile | values)
    return level


def summary(level):
    fields = {'x', 'y', 'glyph', 'feature', 'undiggable', 'seen', 'walked', 'searched', 'room', 'tags'}
    return plain({'tiles': [[{k: v for k, v in tile.items() if k in fields} for tile in row] for row in level['tiles']],
                  'monsters': list(level['monsters'].items()), 'tags': level['tags']})


@pytest.mark.oracle
def test_initial_world(oracle):
    assert plain(d.new_dungeon()) == oracle.call('dungeon-basic', 'new', None, None, None)
    assert plain(l.new_level('Dlvl:5', 'main')) == oracle.call('new-level', 'Dlvl:5', 'main')
    assert l.world_data() == oracle.call('world-data')


@pytest.mark.oracle
def test_level_order_and_navigation(oracle):
    for branch in d.BRANCHES:
        for a in ('Dlvl:1', 'Dlvl:9', 'Dlvl:10', 'Home 1', 'Home 10', 'End Game', 'Astral Plane'):
            assert d.next_dlvl(a, branch) == oracle.call('dungeon-basic', 'next', branch, a, None)
            assert d.prev_dlvl(a, branch) == oracle.call('dungeon-basic', 'prev', branch, a, None)
            for b in ('Dlvl:2', 'Home 3', 'End Game'):
                assert d.dlvl_compare(a, b, branch) == oracle.call('dungeon-basic', 'compare', branch, a, b)


@pytest.mark.oracle
@pytest.mark.parametrize('index', range(33))
def test_blueprints(oracle, index):
    blueprint = l.world_data()['blueprints'][index]
    patches = [[38, 12, {'feature': 'floor'}], [32, 14, {'feature': 'door-open'}],
               [0, 1, {'feature': 'floor'}], [39, 7, {'feature': 'stairs-up'}]]
    original = patched(blueprint.get('dlvl', 'Dlvl:5'), blueprint['branch'], patches=patches)
    result = d.apply_blueprint(original, blueprint)
    assert summary(result) == oracle.call('blueprint', index, patches)
    assert l.at(original, {'x': 0, 'y': 1})['feature'] == 'floor'


@pytest.mark.oracle
@pytest.mark.parametrize('label,branch,tags,patches', [
    ('Dlvl:26', 'main', [], [[14, 12, {'feature': 'drawbridge-lowered'}]]),
    ('Dlvl:7', 'mines', [], [[20, 10, {'feature': 'fountain'}]]),
    ('Dlvl:7', 'mines', ['minetown'], [[3, 2, {'feature': 'stairs-up'}]]),
    ('Dlvl:32', 'main', [], [[66, 12, {'feature': 'door-closed'}]]),
    ('Dlvl:34', 'main', [], [[x, 10, {'feature': 'pool'}] for x in range(30)]),
    ('Dlvl:11', 'mines', [], [[38, 8, {'feature': 'stairs-up'}], *[[x, 7, {'feature': 'floor'}] for x in range(35, 42)],
                            *[[x, 6, {'feature': 'wall'}] for x in range(35, 42)]]),
    ('Dlvl:11', 'mines', [], [[38, 8, {'feature': 'stairs-up'}], *[[x, 7, {'undiggable': True}] for x in range(35, 38)]]),
    ('Dlvl:11', 'main', [], [[x, 8, {'feature': 'floor'}] for x in range(3, 60)]),
    ('Dlvl:43', 'main', [], [[35, 9, {'feature': 'pool'}]]),
])
def test_infer_tags(oracle, label, branch, tags, patches):
    game = {'dungeon': d.new_dungeon(), 'dlvl': label, 'branch-id': branch, 'player': {'role': 'valkyrie'}}
    game = d.add_level(game, patched(label, branch, tags, patches))
    assert sorted(d.curlvl_tags(d.infer_tags(game))) == oracle.call('world-infer', label, branch, tags, patches, 'tags')


def test_previous_state_survives_updates():
    game = d.ensure_curlvl({'dungeon': d.new_dungeon(), 'dlvl': 'Dlvl:1', 'branch-id': 'main'})
    changed = d.update_at(game, {'x': 40, 'y': 10}, lambda tile: tile | {'feature': 'floor'})
    assert l.at(d.curlvl(game), {'x': 40, 'y': 10})['feature'] is None
    assert l.at(d.curlvl(changed), {'x': 40, 'y': 10})['feature'] == 'floor'
    assert d.curlvl(changed)['tiles'][0] is d.curlvl(game)['tiles'][0]
