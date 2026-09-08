"""Prompt routing is compared to the actual scraper.clj, not a copied oracle."""
import pytest
from bothack.scraper import choice_call, menu_fn, multi_menu, merge_menu, prompt_fn, location_fn

pytestmark = pytest.mark.oracle

CHOICES = [
    'What do you want to charge? [a-z or ?*]',
    '"Shall I remove your cloak?" [yn] (n)',
    '"Take off your shirt?" [yn] (n)',
    'Please let me run my fingers through your hair? [yn]',
    'Would you wear it for me? [yn]', 'Force the gods to be pleased? [yn]',
    'Really attack the peaceful dwarf? [yn] (n)', 'Are you sure you want to enter? [yn]',
    *[f'What do you want to {verb}? [a-z or ?*]' for verb in (
        'wield', 'wear', 'put on', 'take off', 'remove', 'ready', 'drop',
        'use or apply', 'name', 'call', 'read', 'drink', 'zap', 'eat',
        'sacrifice', 'dip', 'dip the potion into', 'throw', 'write with', 'rub')],
    'Create what kind of monster? [a-z]', 'Die? [yn]', 'Dry up fountain? [yn]',
    'Dump core? [yn]', 'Advance skills without practice? [yn]',
    'Do you want to keep the save file? [yn]',
    'There is a chest here; force its lock? [yn]', 'Unlock it? [yn]',
    'There is a box; pick its lock? [yn]', 'Lock it? [yn]',
    'Drink from the fountain? [yn]', 'Which ring-finger, Right or Left? [rl]',
    '"Cad!  You did 400 zorkmids worth of damage!"  Pay? [yn]',
    'There is a newt corpse here; eat it? [yn]',
    'There are 2 food rations here; eat one? [yn]',
    'There is a goblin corpse here; sacrifice it? [yn]',
    'There are 3 goblin corpses here; sacrifice one? [yn]',
    'Do you wish to teleport? [yn]', 'Attach the candles to the candelabrum? [yn]',
    'Beware, there will be no return! Still climb? [yn]',
    'You have a little trouble lifting a chest. Continue? [yn]',
    'You have much trouble lifting a chest. Continue? [yn]',
    'You have extreme difficulty lifting a chest. Continue? [yn]',
    'There is a large box here, loot it? [yn]', 'Stop eating? [yn]',
    'Do you want to take something out of the bag? [yn]',
    'Do you wish to put something in? [yn]', 'Dip the sword into the fountain? [yn]',
    'Do you want to add to the current engraving? [yn]',
    'Izchak offers 1 gold piece for your dagger. Sell it? [yn]',
    'Izchak offers 100 gold pieces for your daggers.  Sell them? [yn]',
]


@pytest.mark.parametrize('message', CHOICES)
def test_choice(oracle, message):
    assert list(choice_call(message)) == oracle.call('scraper-call', 'choice', message)


@pytest.mark.parametrize('head', [
    'What do you wish to do?', 'Pick up what?', 'Put in what?', 'Take out what?',
    'Loot which containers?', 'Pick a skill to advance:', 'Current skills:',
    'What would you like to identify first?', 'Contents of the bag:', 'Your possessions:',
])
def test_menu(oracle, head):
    assert dict(fn=menu_fn(head), multi=multi_menu(head), merge=merge_menu(head)) == oracle.call('scraper-call', 'menu', head)


@pytest.mark.parametrize('message', [
    'What do you want to name this dagger?', 'Call a ruby potion:',
    'How much will you offer?', 'To what level do you want to teleport?',
    *[f'What do you want to {verb} on the floor here?' for verb in ('write', 'engrave', 'burn', 'scribble', 'scrawl', 'melt')],
    'What do you want to add to the engraving on the floor here?',
    'For what do you wish?', 'What monster do you want to genocide?',
    'What class of monsters do you wish to genocide?', '"Hello stranger, who are you?"',
])
def test_text_prompt(oracle, message):
    assert prompt_fn(message) == oracle.call('scraper-call', 'prompt', message)


@pytest.mark.parametrize('message', [
    'Where do you want to travel to?', 'To what location do you want to teleport?',
    'Pay whom?', '(For instructions type a ?)',
])
def test_location(oracle, message):
    assert location_fn(message) == oracle.call('scraper-call', 'location', message)


@pytest.mark.parametrize('kind,function,message', [
    ('choice', choice_call, 'In what direction?'),
    ('choice', choice_call, 'Really do an unknown thing? [yn]'),
    ('choice', choice_call, 'Lock it?'),  # Upstream requires a trailing space.
    ('menu', menu_fn, 'Unknown menu'), ('prompt', prompt_fn, 'Unknown prompt'),
    ('location', location_fn, 'Unknown location'),
])
def test_rejected_prompt(oracle, kind, function, message):
    with pytest.raises((NotImplementedError, RuntimeError)):
        function(message)
    with pytest.raises(RuntimeError):
        oracle.call('scraper-call', kind, message)
