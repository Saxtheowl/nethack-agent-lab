"""The supervisor's recoveries must actually fire (a safeguard never seen
firing is not a safeguard)."""
import collections
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nhbot.supervisor import Supervisor  # noqa: E402
from pybothack.nhbridge import BridgeAbort  # noqa: E402


class Rec(object):
    gamedir = '/tmp'
    reached = {}
    last_action_desc = None
    nact = 0
    max_depth = 1
    counters = collections.Counter()

    def __init__(self):
        self.notes = []

    def request(self, eng, req):
        pass

    def note(self, what, detail):
        self.notes.append((what, detail))


class Eng(object):
    def __init__(self):
        self.status = {'turn': 1, 'lvl': 'Dlvl:2', 'depth': 2, 'xl': 3,
                       'dnum': 0, 'dlevel': 2}
        self.u = (10, 10)
        self.assist_events = []
        self.proc = None


class Req(object):
    def __init__(self, kind='cmd', query=None):
        self.kind = kind
        self.query = query
        self.prompt = None
        self.goal = None

    def messages(self):
        return []


class Bridge(object):
    def __init__(self):
        self.last_action = None
        self.forgotten = []
        self.force_escape = 0
        self.force_command = None

    def forget_target(self, x, y):
        self.forgotten.append((x, y))
        return "forgot"

    def recover_action_loop(self, a):
        return "blocked"

    def request_exploration_reset(self):
        pass


def sup(**limits):
    s = Supervisor(Rec(), Eng(), limits=limits)
    s.stop()
    return s


class Fixation(unittest.TestCase):
    def test_alternating_targets_are_forgotten(self):
        s = sup(storm_window=10 ** 9)
        b = Bridge()
        turn = 1
        for i in range(400):
            turn += 1
            s.engine.status['turn'] = turn
            s.engine.u = (10 + i % 2, 10)       # moving: no action loop
            tx = 70 if i % 2 else 72
            b.last_action = {'type': 'move', 'dir': 'S',
                             'reason': ["new or desired item at "
                                        "#Position{:x %d, :y 6}" % tx]}
            s.on_request(b, Req())
        self.assertIn((70, 6), b.forgotten)
        self.assertIn((72, 6), b.forgotten)

    def test_same_turn_target_loop(self):
        s = sup(storm_window=10 ** 9, action_loop=10 ** 9,
                no_turn_requests=10 ** 9)
        b = Bridge()
        for i in range(200):
            b.last_action = {'type': 'eat' if i % 2 else 'look',
                             'reason': ["want to eat corpse at {'x': 58, "
                                        "'y': 17, 'glyph': '%'}"]}
            s.on_request(b, Req())
        self.assertIn((58, 17), b.forgotten)


class Loops(unittest.TestCase):
    def test_prompt_loop_escapes_then_aborts(self):
        s = sup()
        b = Bridge()
        with self.assertRaises(BridgeAbort):
            for i in range(100):
                s.on_request(b, Req('yn', 'Dip it into the fountain?'))
        self.assertTrue(any('prompt-loop' in d for w, d in s.rec.notes))

    def test_request_storm(self):
        s = sup(storm_window=300, no_turn_requests=10 ** 9,
                action_loop=10 ** 9)
        b = Bridge()
        with self.assertRaises(BridgeAbort) as cm:
            for i in range(1000):
                s.on_request(b, Req())
        self.assertIn('request storm', cm.exception.reason)


if __name__ == '__main__':
    unittest.main()
