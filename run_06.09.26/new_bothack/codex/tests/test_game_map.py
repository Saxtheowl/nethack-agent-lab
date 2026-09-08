from dataclasses import asdict
import pytest
from bothack import game as g, dungeon as d
from bothack.frame import Frame
from bothack.position import Position
from bothack.scraper import parse_botls
from tests.test_world import summary, plain


def room(monster_x=45, turn=1):
    rows = [''] * 24
    for y in range(5, 16):
        rows[y] = (' ' * 30 + ('-' * 25 if y in (5, 15) else '|' + '.' * 23 + '|')).ljust(80)
    rows[10] = rows[10][:40] + '@' + rows[10][41:]
    rows[10] = rows[10][:monster_x] + 'r' + rows[10][monster_x + 1:]
    rows[22] = 'Bot the Stripling St:18 Dx:12 Co:18 In:8 Wi:10 Ch:7 Lawful S:0'
    rows[23] = f'Dlvl:1 $:10 HP:16(16) Pw:2(2) AC:6 Xp:1/0 T:{turn} '
    colors = [[None] * 80 for _ in range(24)]
    colors[10][monster_x] = 'brown'
    return Frame(tuple(row.ljust(80) for row in rows), tuple(tuple(row) for row in colors), Position(40, 10))


@pytest.mark.oracle
def test_world_frames(oracle):
    frames = [room(45, 1), room(44, 2), room(43, 3), room(43, 4)]
    expected = oracle.call('game-maps', [asdict(frame) for frame in frames])
    game = g.new_game()
    for frame, reference in zip(frames, expected):
        game = g.update_by_botl(game | {'frame': frame}, parse_botls(frame.botls))
        game['player'] = game['player'] | asdict(frame.cursor)
        game = g.update_map(d.ensure_curlvl(game), frame)
        assert plain({'level': summary(d.curlvl(game)), 'player': game['player'], 'fov': game['fov']}) == reference
