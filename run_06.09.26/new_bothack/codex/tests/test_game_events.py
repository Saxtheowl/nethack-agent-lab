import pytest
from bothack import dungeon as d, game as g
from bothack.game_events import GameEvents
from bothack.runtime import Runtime
from tests.test_world import plain, summary

MESSAGES = [
    'The giant eel grabs you!', 'The giant eel releases you!', 'You kill the giant rat!',
    'You are slowing down.', 'You feel more limber.', 'You feel weaker.',
    'You feel feverish.', 'You feel purified.', 'You feel more confident.',
    'Your leg feels somewhat better.', "It's a wall.", 'Your foot is trapped.',
    'The venom blinds you!', 'You sink into the lava.',
    'You hear the rumble of distant thunder.', 'You feel guilty about losing your pet.',
    'You feel a strange mental acuity.', 'You murderer!', 'You feel in control of yourself.',
    'You feel a momentary chill.', 'You feel warmer.', 'You feel warm.', 'You feel cooler.',
    'You feel wide awake.', 'You feel tired!', 'You feel grounded.', 'You feel conductive.',
    'You feel especially healthy.', 'You feel a little sick.', 'You feel very jumpy.',
    'You feel very firm.', 'You feel sensitive.', 'You feel less sensitive.',
    'You feel stealthy.', 'You feel clumsy.', 'You feel less attractive.', 'You feel less jumpy.',
    'You feel hidden.', 'You feel paranoid.', 'Your vision becomes clear.',
    'You feel perceptive!', 'You thought you saw something.', 'You feel quick!', 'You feel slower.',
    'You enter what seems to be an older, more primitive world.',
    'You are almost hit.', 'Your boots disintegrate!', 'The goblin reads a scroll of identify.',
    'The Amulet of Yendor feels very warm.', 'You activated a magic portal!',
    'The walls around you begin to bend and crumble!', 'You turn into a dragon.',
]


class EffectContext(Runtime):
    def __init__(self):
        game = g.new_game() | {'dlvl': 'Dlvl:1', 'turn': 100}
        game['player'] = game['player'] | {'x': 40, 'y': 10, 'hp': 20, 'state': set(), 'intrinsics': set()}
        super().__init__(lambda _: None, d.ensure_curlvl(game))
        self.calls, self.pending = [], []

    def update_inventory(self):
        self.calls.append('inventory')
        return self

    def update_tile(self):
        self.calls.append('tile')
        return self

    def update_discoveries(self):
        self.calls.append('discoveries')
        return self

    def update_on_known_position(self, function, *args):
        self.calls.append('position')
        self.pending.append((function, args))
        return self

    def update_before_action(self, function, *args):
        self.calls.append('before')
        self.pending.append((function, args))
        return self


@pytest.mark.oracle
@pytest.mark.parametrize('messages', [[m] for m in MESSAGES] + [MESSAGES[:14], MESSAGES[16:44]])
def test_message_effects(oracle, messages):
    context = EffectContext()
    events = GameEvents(context)
    for message in messages:
        events.message(message)
    for function, args in context.pending:
        context.mutate(function, *args)
    actual = dict(player=context.game['player'], level=summary(d.curlvl(context.game)),
                  prayer=context.game.get('last-prayer'), angry=context.game.get('god-angry'), calls=context.calls)
    assert plain(actual) == oracle.call('game-events', messages)
