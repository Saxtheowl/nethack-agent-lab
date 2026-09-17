"""Real 3.6.7 engine regressions; fixture victories are NOT full ascensions."""
import json
from pathlib import Path
import time
import unittest
from localbot.engine import Engine

ROOT=Path(__file__).resolve().parents[1]

class EngineTests(unittest.TestCase):
    def engine(self,name,**kw):
        return Engine(ROOT/'runs'/'fixtures'/f'{time.time_ns()}-{name}',**kw)
    def test_commands_direction_cancel_and_inventory(self):
        with self.engine('control') as e:
            self.assertTrue(e.command_ready()['command'])
            e.send('o');o=e.next()
            self.assertIn('In what direction',o['screen'][0])
            e.send('\x1b');self.assertTrue(e.command_ready()['command'])
            e.send('i');o=e.next()
            self.assertTrue(any('blessed' in s for s in o['screen']))
            e.send(' ');self.assertTrue(e.command_ready()['command'])
            e.send('#quit\ny')
            for _ in range(30):
                if e.result():break
                o=e.next()
                if o is None:break
                e.send(' ')
            self.assertEqual(e.result()['event'],'quit')
    def test_invincibility_enabled(self):
        with self.engine('death-protected',fixture='death') as e:
            self.assertTrue(e.command_ready()['command'])
            records=[json.loads(s) for s in e.events.read_text().splitlines()]
            self.assertTrue(any(x['event']=='prevent_death' for x in records))
            self.assertIsNone(e.result())
    def test_invincibility_disabled(self):
        with self.engine('death-unprotected',fixture='death',aids=False) as e:
            for _ in range(50):
                if e.result():break
                o=e.next()
                if o is None:break
                e.send(' ')
            self.assertEqual(e.result()['event'],'death')
    def test_hunger_protection(self):
        with self.engine('hunger',fixture='hunger') as e:
            e.command_ready();e.send('.');e.command_ready()
            records=[json.loads(s) for s in e.events.read_text().splitlines()]
            self.assertTrue(any(x['event']=='hunger' for x in records))
    def test_astral_offering_engine_result(self):
        with self.engine('astral-offer',fixture='astral-offer') as e:
            e.command_ready()
            e.send('#offer\n');o=e.next()
            # Object chosen from the real engine prompt, never a hard-coded slot.
            import re
            match=re.search(r'\[([^\]]+)\]',o['screen'][0])
            self.assertIsNotNone(match,o['screen'][0])
            slot=match[1].split()[0]
            self.assertEqual(len(slot),1,o['screen'][0])
            e.send(slot)
            for _ in range(100):
                if e.result():break
                o=e.next()
                if o is None:break
                e.send(' ')
            self.assertEqual(e.result()['event'],'ascended')
            self.assertFalse(e.manifest['full_from_start'])
if __name__=='__main__':unittest.main()
