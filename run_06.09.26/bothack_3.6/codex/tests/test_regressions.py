import unittest
from localbot.protocol import Decoder, ProtocolError
from pybothack.item import label_to_item
from pybothack.tile import e_p
from pybothack.bots.mainbot import farming, init_farm, engrave_e

class Regressions(unittest.TestCase):
    def test_wire_arbitrary_chunk_boundaries(self):
        data=b'first\x1b]777;command\x07second\x1b]777;input\x07\x1b]777;ack\x07'
        expected=[(b'command',b'first'),(b'input',b'second'),(b'ack',b'')]
        for split in range(len(data)+1):
            d=Decoder()
            self.assertEqual(d.feed(data[:split])+d.feed(data[split:]),expected)
        d=Decoder();out=[]
        for byte in data:out+=d.feed(bytes([byte]))
        self.assertEqual(out,expected)
    def test_empty_bag_observed_seed_one(self):
        i=label_to_item('an empty blessed bag of holding')
        self.assertEqual((i['name'],i['buc'],i['items']),('bag of holding','blessed',[]))
    def test_quiver_variants(self):
        for text in ['in quiver','in quiver pouch','at the ready']:
            i=label_to_item(f'12 uncursed +0 darts ({text})')
            self.assertTrue(i.get('quivered'))
            self.assertEqual(i['name'],'dart')
    def test_no_old_elbereth_stacking(self):
        self.assertTrue(e_p({'engraving':'Elbereth'}))
        self.assertFalse(e_p({'engraving':'Elbereth Elbereth'}))
        self.assertFalse(e_p({'engraving':'Elbereth*'}))
        self.assertIsNone(engrave_e({}))
    def test_farming_disabled(self):
        self.assertFalse(farming({}))
        self.assertFalse(init_farm({}))
if __name__=='__main__': unittest.main()

class Rules367(unittest.TestCase):
    def test_prayer_threshold_high_level(self):
        from pybothack.rules367 import critically_low_hp
        self.assertFalse(critically_low_hp(40,284,25))
        self.assertTrue(critically_low_hp(35,284,25))
        self.assertFalse(critically_low_hp(6,1000,1))
        self.assertTrue(critically_low_hp(5,1000,1))
    def test_high_altar_real_message(self):
        from pybothack.actions import feature_msg_update
        t=feature_msg_update({},'There is a high altar to Tyr (lawful) here.',False)
        self.assertEqual(t['feature'],'altar')
        self.assertEqual(t['alignment'],'lawful')
    def test_partial_json_tail(self):
        import io
        from localbot.protocol import JSONTail
        stream=io.StringIO('{"event":')
        tail=JSONTail(stream)
        self.assertEqual(tail.poll(),[])
        stream.seek(0);stream.truncate();stream.write('"input"}\n');stream.seek(0)
        self.assertEqual(tail.poll(),[{'event':'input'}])

class Appearance367(unittest.TestCase):
    def test_new_scroll_appearance_keeps_unknown_identity(self):
        from pybothack.itemid import APPEARANCE_NAMES
        candidates=APPEARANCE_NAMES['scroll labeled HAPAX LEGOMENON']
        self.assertIn('scroll of identify',candidates)
        self.assertIn('scroll of genocide',candidates)
        self.assertGreater(len(candidates),1)
