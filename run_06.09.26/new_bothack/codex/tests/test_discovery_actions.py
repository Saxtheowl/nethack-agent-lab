import pytest
from bothack.discovery_actions import parse_discoveries
from bothack.actions import action
from bothack.runtime import Runtime


@pytest.mark.oracle
@pytest.mark.parametrize('lines', [
    ['Discoveries', 'Potions', 'potion of healing (ruby)'],
    ['Scrolls', '* scroll of identify (ZELGO MER)'],
    ['Gems', 'flint (gray)', 'worthless piece of red glass (red)'],
    ['Amulets', 'amulet of ESP (circular)', 'Rings', 'ring of levitation (opal)'],
    ['Wands', 'wand of fire (glass)', 'Spellbooks', 'spellbook of force bolt (parchment)'],
    ['Unique Items', 'Amulet of Yendor (Amulet of Yendor)', 'Tools', 'magic whistle (whistle)'],
    ['Potions', 'potion of healing called RED (ruby)'],
    ['Armor', 'gauntlets of power (riding gloves)', 'Weapons', 'dagger'],
    [], ['Artifacts', 'Excalibur'],
])
def test_discovery_lines(oracle, lines):
    assert [list(pair) for pair in parse_discoveries(lines)] == oracle.call('discovery-lines', lines)


def test_discoveries_update_database_without_changing_previous_snapshot():
    context = Runtime(lambda _: None)
    previous = context.game
    previous['discoveries'].used_names.add('lamp1')
    handler = action('discoveries').handler(context)
    handler.message_lines(['Potions', 'potion of healing (ruby)'])
    assert ('ruby potion', 'potion of healing') in context.game['discoveries'].discoveries
    assert ('ruby potion', 'potion of healing') not in previous['discoveries'].discoveries
    handler.about_to_choose(context.game)
    assert 'lamp1' in context.game['discoveries'].used_names
