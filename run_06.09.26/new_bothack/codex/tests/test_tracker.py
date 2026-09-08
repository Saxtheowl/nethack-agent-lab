from types import SimpleNamespace
import pytest
from bothack import tracker, dungeon as d, level as l, monster as m

pytestmark = pytest.mark.oracle


def make_monster(input):
    if input.get('name'):
        result = m.known_monster(input['x'], input['y'], m.by_name(input['name'])) | {'remembered': False}
    else:
        result = m.new_monster(input['x'], input['y'], input.get('turn', 10), input['glyph'], input.get('color'))
    return result | {k: v for k, v in input.items() if k not in {'name', 'glyph', 'color'}}


@pytest.mark.parametrize('old,new', [
    ([{'name': 'giant rat', 'x': 42, 'y': 10, 'peaceful': True}], [{'name': 'giant rat', 'x': 43, 'y': 10}]),
    ([{'name': 'giant rat', 'x': 42, 'y': 10}], [{'name': 'giant rat', 'x': 41, 'y': 10}]),
    ([{'name': 'giant rat', 'x': 42, 'y': 10, 'cancelled': False}], [{'name': 'giant rat', 'x': 42, 'y': 10, 'peaceful': 'update'}]),
    ([{'name': 'giant rat', 'x': 42, 'y': 10}], []),
    ([{'name': 'giant rat', 'x': 42, 'y': 10}], [{'glyph': '1', 'x': 42, 'y': 10, 'color': 'red'}]),
    ([{'name': 'giant rat', 'x': 42, 'y': 10}, {'name': 'giant rat', 'x': 44, 'y': 10}],
     [{'name': 'giant rat', 'x': 43, 'y': 10}]),
])
@pytest.mark.parametrize('state,intrinsics', [([], []), (['blind'], []), (['blind'], ['telepathy']), (['hallu'], [])])
def test_tracking(oracle, old, new, state, intrinsics):
    player = dict(x=40, y=10, hp=20, state=state, intrinsics=intrinsics)
    level = l.new_level('Dlvl:1', 'main')
    level['tiles'] = [[tile | {'feature': 'floor', 'glyph': '.'} for tile in row] for row in level['tiles']]
    game = d.add_level(dict(dungeon=d.new_dungeon(), dlvl='Dlvl:1', player=player,
                            fov=[[True] * 80 for _ in range(22)], **{'branch-id': 'main'}), level)
    def populate(inputs):
        result = game
        for input in inputs:
            result = d.reset_monster(result, make_monster(input))
        return result
    actual = sorted(d.curlvl_monsters(tracker.track_monsters(populate(new), populate(old))), key=lambda m: (m['x'], m['y']))
    assert actual == oracle.call('track', player, old, new)


@pytest.mark.parametrize('age', [0, 29, 30, 500, 501])
@pytest.mark.parametrize('other', [None, 'giant rat', 'human zombie', 'wraith'])
def test_death_freshness(oracle, age, other):
    deaths = [[99, 'human'], [100 - age, other]]
    tile = {'deaths': [(turn, {'type': m.by_name(name) if name else None}) for turn, name in deaths]}
    assert tracker.only_fresh_deaths(tile, m.by_name('human'), 100) == oracle.call('fresh-deaths', 'human', 100, deaths)
