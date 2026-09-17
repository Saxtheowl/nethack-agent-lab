"""Unit tests of the 3.6.7 -> 3.4.3 translations (messages, object names).
Expected values come from the 3.6.7 sources (pickup.c, do.c, objnam.c)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pybothack import compat36  # noqa: E402
from pybothack.item import label_to_item  # noqa: E402


class FakeBridge(object):
    def __init__(self):
        import collections
        self.counters = collections.Counter()


def rw(text):
    return compat36.rewrite_message(FakeBridge(), text)


class MessageRewrites(unittest.TestCase):
    def test_container_locked(self):
        self.assertEqual(rw("Hmmm, the large box turns out to be locked."),
                         "Hmmm, it seems to be locked.")
        self.assertEqual(rw("The chest is locked."),
                         "Hmmm, it seems to be locked.")

    def test_door_locked_untouched(self):
        # regression: the container rule used to rewrite door messages
        self.assertEqual(rw("This door is locked."), "This door is locked.")

    def test_bag_open(self):
        self.assertEqual(rw("You open the bag of holding..."),
                         "You carefully open the bag of holding...")

    def test_legs(self):
        self.assertEqual(rw("Your legs feel better."),
                         "Your legs feel somewhat better.")

    def test_unrelated(self):
        for m in ("You hit the jackal.", "The door opens.",
                  "You see here a dagger."):
            self.assertEqual(rw(m), m)


class Labels(unittest.TestCase):
    def check(self, label, **expect):
        it = label_to_item(label)
        for k, v in expect.items():
            self.assertEqual(it.get(k), v, "%s: %s" % (label, k))

    def test_container_suffix(self):
        self.check("an uncursed bag of holding containing 1 item",
                   name="bag of holding", buc="uncursed")

    def test_empty_locked(self):
        self.check("an empty uncursed unlocked large box", name="large box",
                   buc="uncursed")
        self.check("a locked chest", name="chest")

    def test_quiver_variants(self):
        self.check("3 +0 daggers (at the ready)", name="dagger", qty=3)
        self.check("12 +0 darts (in quiver pouch)", name="dart", qty=12)

    def test_prices(self):
        self.check("a scroll labeled FOO (for sale, 20 zorkmids)",
                   name="scroll labeled FOO", cost=20)

    def test_worn(self):
        self.check("a blessed greased +2 gray dragon scale mail (being worn)",
                   name="gray dragon scale mail", buc="blessed")


if __name__ == '__main__':
    unittest.main()


class Rules36(unittest.TestCase):
    def test_critically_low_hp(self):
        from pybothack.rules36 import critically_low_hp
        # XL 1-5 divisor 5
        self.assertTrue(critically_low_hp({'hp': 3, 'maxhp': 16, 'xplvl': 1}))
        self.assertFalse(critically_low_hp({'hp': 6, 'maxhp': 16,
                                            'xplvl': 1}))
        # 16*... hp*5 <= max: 7*5=35 <= 35
        self.assertTrue(critically_low_hp({'hp': 7, 'maxhp': 35, 'xplvl': 5}))
        # megadoc example: XL25, 284 max -> capped 375 unused, divisor 8:
        # critical at hp*8 <= 284 -> hp <= 35
        self.assertTrue(critically_low_hp({'hp': 35, 'maxhp': 284,
                                           'xplvl': 25}))
        self.assertFalse(critically_low_hp({'hp': 36, 'maxhp': 284,
                                            'xplvl': 25}))
        # maxhp capped at 15*XL: XL2 max 100 -> 30, divisor 5 -> hp <= 6
        self.assertTrue(critically_low_hp({'hp': 6, 'maxhp': 100,
                                           'xplvl': 2}))
        self.assertFalse(critically_low_hp({'hp': 7, 'maxhp': 100,
                                            'xplvl': 2}))

    def test_strict_elbereth(self):
        from pybothack.rules36 import strict_elbereth_text
        from pybothack.tile import e_p
        self.assertTrue(strict_elbereth_text("Elbereth"))
        self.assertTrue(strict_elbereth_text("elbereth"))
        self.assertFalse(strict_elbereth_text("ElberethElbereth"))
        self.assertFalse(strict_elbereth_text("Elbereth*"))
        self.assertFalse(strict_elbereth_text("Elbcreth"))
        self.assertTrue(e_p({'engraving': "Elbereth"}))
        self.assertFalse(e_p({'engraving': "xElbereth"}))

    def test_xlev_to_rank(self):
        from pybothack.rules36 import xlev_to_rank
        self.assertEqual([xlev_to_rank(x) for x in (1, 2, 3, 5, 6, 13, 14,
                                                     21, 22, 29, 30)],
                         [0, 0, 1, 1, 2, 3, 4, 5, 6, 7, 8])


class ShopPrices36(unittest.TestCase):
    def test_price_table(self):
        from pybothack.itemid import BASE_CHA_COST
        # scroll of identify base 20: CHA 11-15 -> 20, unID surcharge 27
        self.assertIn((20, 15, 20), BASE_CHA_COST)
        self.assertIn((20, 15, 27), BASE_CHA_COST)   # 20*4/3=26.67 -> 27
        # 3.4.3 gave 20 + 20/3 = 26: must not be accepted any more
        self.assertNotIn((20, 15, 26), BASE_CHA_COST)
        # CHA 8-10 (x4/3) with unID surcharge (x4/3): 20*16/9=35.6 -> 36
        self.assertIn((20, 10, 36), BASE_CHA_COST)
        # selling base 100: 50, or 3/4 -> 37.5 -> 38 (3.4.3: 37)
        self.assertIn((100, 0, 50), BASE_CHA_COST)
        self.assertIn((100, 0, 38), BASE_CHA_COST)


class RawLabel(unittest.TestCase):
    def test_label_kept_verbatim(self):
        # regression: normalised labels no longer matched pickup menu texts
        raw = "an uncursed bag of holding containing 1 item"
        self.assertEqual(label_to_item(raw)['label'], raw)
        raw = "a scroll labeled FOO (for sale, 20 zorkmids)"
        self.assertEqual(label_to_item(raw)['label'], raw)


class ContinueEating(unittest.TestCase):
    def test_inverted(self):
        import collections

        class D(object):
            def __init__(self, ans):
                self.ans = ans

            def _invoke_prompt(self, name, *args):
                assert name == 'stop_eating'
                return self.ans

        class BH(object):
            pass

        class B(object):
            def __init__(self, ans):
                self.bh = BH()
                self.bh.delegator = D(ans)
                self.counters = collections.Counter()

        class R(object):
            query = "Continue eating?"

        self.assertEqual(compat36.yn_continue_eating(B(True), R())[1], 'n')
        self.assertEqual(compat36.yn_continue_eating(B(False), R())[1], 'y')


class PromptClassification(unittest.TestCase):
    """Real 3.6.7 prompt texts seen in games -> BotHack prompt names."""
    CASES = [
        ("Dip a blessed +1 long sword (weapon in hand) into the fountain? "
         "[yn] (n)", 'dip_here'),
        ("Dip it into the fountain? [yn] (n)", 'dip_here'),
        ("There is an unlocked large box here, loot it? [ynq] (q)", 'loot_it'),
        ("There is a large box here; force its lock? [ynq] (q)", 'force_lock'),
        ("What do you want to eat? [d or ?*]", 'eat_what'),
        ("What do you want to use or apply? [ijk or ?*]", 'apply_what'),
        ("What do you want to drop? [a-l or ?*]", 'drop_single'),
        ("What do you want to throw? [$an or ?*]", 'throw_what'),
        ("What do you want to dip? [$a-kmpr-tvx-z or ?*]", 'dip_what'),
    ]

    def test_choice_prompts(self):
        from pybothack.scraper import _choice_call
        for text, name in self.CASES:
            self.assertEqual(_choice_call(text)[0], name, text)


class Appearances36(unittest.TestCase):
    def test_new_scroll_labels(self):
        from pybothack.itemid import APPEARANCE_NAMES
        ids = APPEARANCE_NAMES.get("scroll labeled ZLORFIK")
        self.assertTrue(ids and "scroll of identify" in ids)
        self.assertTrue(APPEARANCE_NAMES.get("scroll labeled GHOTI"))

    def test_leathery_spellbook(self):
        from pybothack.itemid import APPEARANCE_NAMES
        self.assertTrue(APPEARANCE_NAMES.get("leathery spellbook"))
        self.assertFalse(APPEARANCE_NAMES.get("leather spellbook"))


class WallMessages(unittest.TestCase):
    def test_solid_stone(self):
        self.assertEqual(rw("It's solid stone."), "It's a wall.")
        self.assertEqual(rw("It's a tree."), "It's a wall.")
        self.assertEqual(rw("It's a wall."), "It's a wall.")


class StackPrice(unittest.TestCase):
    def test_per_unit(self):
        it = label_to_item("2 uncursed potions of healing "
                           "(for sale, 40 zorkmids)")
        self.assertEqual(it.get('cost'), 20)
        self.assertEqual(it.get('qty'), 2)
        self.assertEqual(label_to_item("a scroll labeled FOO (for sale, "
                                       "20 zorkmids)").get('cost'), 20)


class Globs(unittest.TestCase):
    def test_glob_known_not_edible(self):
        from pybothack.itemtype import name_to_item, typekw
        from pybothack.player import edible
        it = label_to_item("a small glob of black pudding")
        self.assertEqual(it['name'], "glob of black pudding")
        self.assertEqual(typekw(name_to_item[it['name']]), 'other')
        self.assertFalse(edible({'race': 'dwarf'}, it))
        self.assertEqual(label_to_item("a very large glob of green slime")
                         ['name'], "glob of green slime")


class SokobanPit(unittest.TestCase):
    def test_air_currents(self):
        self.assertEqual(rw("Air currents pull you down into a pit!"),
                         "You fall into a pit!")
        self.assertEqual(rw("Air currents pull you down into a spiked pit!"),
                         "You fall into a pit!")


def test_high_altar_alignment_parsed():
    # ca scenario astral-altar: the bot left its own god's high altar
    from pybothack.actions import feature_msg_update
    t = feature_msg_update({'x': 1, 'y': 1},
                           "There is a high altar to Tyr (lawful) here.",
                           False)
    assert t['feature'] == 'altar' and t['alignment'] == 'lawful'
    t = feature_msg_update({'x': 1, 'y': 1},
                           "There is an altar to Anhur (chaotic) here.", False)
    assert t['alignment'] == 'chaotic'


def test_all_367_monsters_known():
    # ca-w05 g012: Kops were missing, farlook looped on a Kop Kaptain
    import json
    import os
    from pybothack import montype
    h = json.load(open(os.path.join(os.path.dirname(__file__), 'data',
                                    'hello.json')))
    assert [m[0] for m in h['mons']
            if m[0].lower() not in montype._by_name] == []


def test_stack_shop_price_is_unit_price():
    # ca series: "unknown itemtype for item sky blue potion" - the per-unit
    # price was divided by the quantity a second time
    from pybothack.item import label_to_item
    i = label_to_item('2 sky blue potions (for sale, 266 zorkmids)')
    assert i['cost'] == 133 and i.get('cost-each')
    i = label_to_item('a sky blue potion (for sale, 200 zorkmids)')
    assert i['cost'] == 200 and not i.get('cost-each')


def test_novel_known():
    from pybothack.item import label_to_item
    from pybothack import itemid
    import pybothack.game as G
    it = label_to_item('a paperback book named Guards! Guards! '
                       '(for sale, 27 zorkmids)')
    assert (itemid.item_id(G.new_game(), it) or {}).get('glyph') == '+'


def test_new_36_appearances_are_exclusive():
    # ca-w06 g008/g009: new labels were "shared", BotHack #called them
    from pybothack import itemid
    assert not any('KO BATE' in k or 'leathery' in k
                   for k in itemid.item_names)


def test_new_36_appearances_plural():
    from pybothack.item import label_to_item
    assert label_to_item('2 scrolls labeled PHOL ENDE WODAN')['name'] == \
        'scroll labeled PHOL ENDE WODAN'
    assert label_to_item('2 leathery spellbooks')['name'] == \
        'leathery spellbook'


def test_price_with_shopkeeper_surcharge():
    from pybothack import itemid
    assert (50, itemid.cha_group(12), 90) in itemid.BASE_CHA_COST


def test_being_donned_is_worn():
    # full-w02 g002: "You cannot drop something you are wearing." loop
    from pybothack.item import label_to_item
    assert label_to_item('a plumed helmet (being donned)').get('in-use')
    assert label_to_item('a plumed helmet (being doffed)').get('in-use')


def test_contradictory_facts_do_not_make_items_unknown():
    # big-w01: "unknown itemtype for item sky blue potion" loops
    from pybothack import itemid
    import pybothack.game as G
    from pybothack.clj import assoc_in
    from pybothack.item import label_to_item
    g = assoc_in(G.new_game(), ['player', 'stats'], {'cha': 12})
    g = itemid.add_observed_cost(g, 'sky blue potion', 7)   # impossible
    it = itemid.item_id(g, label_to_item('a sky blue potion'))
    assert (it or {}).get('glyph') == '!'
