"""Interface reliability: key translation and glyph rendering of the bridge.
The hello table is captured from the real engine once (tests/data)."""
import collections
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pybothack.nhbridge import (Bridge, GlyphRenderer, simulate_getpos,  # noqa
                                str_string, bothack_status)
from pybothack.position import to_position  # noqa: E402
from pybothack.util import ESC  # noqa: E402

HELLO = os.path.join(ROOT, 'tests', 'data', 'hello.json')


def hello():
    with open(HELLO) as f:
        return json.load(f)


class GetPos(unittest.TestCase):
    def test_bothack_position_keys(self):
        # BotHack screen coordinates (x, y) = NetHack (x+1, y-1)
        for bx, by in ((0, 1), (10, 6), (78, 21), (39, 12)):
            keys = to_position({'x': bx, 'y': by}) + "."
            x, y, n, esc = simulate_getpos(list(keys), 40, 10)
            self.assertEqual((x, y), (bx + 1, by - 1))
            self.assertEqual(n, len(keys))
            self.assertFalse(esc)

    def test_escape(self):
        x, y, n, esc = simulate_getpos(['h', ESC, 'l'], 10, 10)
        self.assertTrue(esc)
        self.assertEqual(n, 2)


class Status(unittest.TestCase):
    def test_strength(self):
        self.assertEqual(str_string(16), "16")
        self.assertEqual(str_string(18), "18")
        self.assertEqual(str_string(19), "18/01")
        self.assertEqual(str_string(68), "18/50")
        self.assertEqual(str_string(118), "18/**")
        self.assertEqual(str_string(119), "19")
        self.assertEqual(str_string(125), "25")

    def test_bothack_status(self):
        st = {'hp': 10, 'hpmax': 20, 'pw': 1, 'pwmax': 2, 'ac': -3, 'xl': 4,
              'exp': 50, 'gold': 7, 'turn': 99, 'hunger': 2, 'enc': 1,
              'cond': 0x20 | 0x100, 'str': 68, 'dex': 10, 'con': 10,
              'int': 10, 'wis': 10, 'cha': 10, 'align': 1, 'poly': 0,
              'lvl': 'Dlvl:3 ', 'title': 'Stripling'}
        s = bothack_status(st, 'Bot')
        self.assertEqual(s['dlvl'], 'Dlvl:3')
        self.assertEqual(s['hunger'], 'hungry')
        self.assertEqual(s['encumbrance'], 'burdened')
        self.assertEqual(s['state'], {'blind', 'conf'})
        self.assertEqual(s['stats']['str*'], '18/50')
        self.assertEqual(s['alignment'], 'lawful')
        self.assertEqual(s['xp-label'], 'Exp')


@unittest.skipUnless(os.path.exists(HELLO), "no captured hello table")
class Render(unittest.TestCase):
    def setUp(self):
        self.h = hello()
        self.r = GlyphRenderer(self.h)
        self.cmap = self.h['off']['cmap']

    def test_features(self):
        c = self.cmap
        r = self.r.render
        self.assertEqual(r(c + 15, ord('+'), 3, 0), (']', 'brown'))  # door
        self.assertEqual(r(c + 13, ord('-'), 3, 0), ('-', 'brown'))  # open
        self.assertEqual(r(c + 30, ord('#'), 7, 0), ('{', None))     # sink
        self.assertEqual(r(c + 31, ord('{'), 12, 0), ('{', 'blue'))
        self.assertEqual(r(c + 18, ord('#'), 2, 0), ('}', 'green'))  # tree
        self.assertEqual(r(c + 59, ord('"'), 7, 0)[0], '^')          # web
        self.assertEqual(r(c + 20, ord('.'), 0, 0), (' ', None))     # dark
        self.assertEqual(r(c + 28, ord('|'), 15, 0), ('\\', None))   # grave

    def test_objects(self):
        off = self.h['off']['obj']
        names = [o[0] for o in self.h['objs']]
        boulder = names.index('boulder')
        self.assertEqual(self.r.render(off + boulder, ord('0'), 7, 0),
                         ('8', None))
        # a masked (unidentified) object keeps the engine char and color
        self.assertEqual(self.r.render(-1, ord('!'), 1, 0), ('!', 'red'))

    def test_monsters(self):
        names = [m[0] for m in self.h['mons']]
        ghost = names.index('ghost')
        self.assertEqual(self.r.render(ghost, ord(' '), 7, 0)[0], 'X')
        jackal = names.index('jackal')
        self.assertEqual(self.r.render(jackal, ord('d'), 3, 0),
                         ('d', 'brown'))
        pet = self.h['off']['pet'] + jackal
        self.assertEqual(self.r.render(pet, ord('d'), 3, 8),
                         ('d', 'inverse-brown'))


class FakeEngine(object):
    def __init__(self):
        self.sent = []

    def __getattr__(self, name):
        def f(*a):
            self.sent.append((name,) + a)
        return f


class FakeReq(object):
    def __init__(self, kind, items=None, cx=None, cy=None):
        self.kind = kind
        self.items = items
        self.cx, self.cy = cx, cy
        self.query = self.prompt = self.goal = None


class Consume(unittest.TestCase):
    def bridge(self, keys):
        b = Bridge.__new__(Bridge)
        b.queue = collections.deque(keys)
        b.engine = FakeEngine()
        b.rec = None
        b.counters = collections.Counter()
        return b

    def test_menu_letters_to_ids(self):
        items = [[0, 0, '', '', 0, 0, 'Weapons'],
                 [1, 1, 'a', '', 0, 0, 'a long sword'],
                 [2, 1, 'b', '', 0, 0, 'a dagger']]
        b = self.bridge("b\n")
        self.assertTrue(b._consume(FakeReq('menu', items)))
        self.assertEqual(b.engine.sent, [('menu', [2])])

    def test_extended_command(self):
        b = self.bridge("pray\nx")
        self.assertTrue(b._consume(FakeReq('ext')))
        self.assertEqual(b.engine.sent, [('ext', 'pray')])
        self.assertEqual(list(b.queue), ['x'])

    def test_line_with_escape(self):
        b = self.bridge("Elb" + ESC)
        b._consume(FakeReq('line'))
        self.assertEqual(b.engine.sent, [('escape',)])


if __name__ == '__main__':
    unittest.main()


class FarlookRewrite(unittest.TestCase):
    def bridge(self, ch):
        b = Bridge.__new__(Bridge)
        b.counters = collections.Counter()
        lines = [" " * 80 for _ in range(24)]
        row = list(lines[6])
        row[9] = ch
        lines[6] = "".join(row)

        class F(object):
            pass
        b.frame = F()
        b.frame.lines = lines
        b.farlook_pos = (10, 5)     # NetHack coords -> frame line 6, col 9
        return b

    def test_web(self):
        from pybothack.actions import FARLOOK_TRAP_RE
        import re
        out = self.bridge('^')._farlook_symbol(
            '"        an amulet or a web (web)')
        self.assertEqual(re.search(FARLOOK_TRAP_RE, out).group(1), 'web')

    def test_strange_object(self):
        from pybothack.actions import FARLOOK_MONSTER_RE
        from pybothack.util import re_any_group
        out = self.bridge('m')._farlook_symbol(
            ']        a mimic or a strange object (strange object)')
        self.assertTrue(out.startswith('m '))
        self.assertEqual(re_any_group(FARLOOK_MONSTER_RE, out), 'mimic')
