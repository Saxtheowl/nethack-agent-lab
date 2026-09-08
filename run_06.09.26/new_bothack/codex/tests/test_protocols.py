"""Check response bytes and notifications against the real delegator."""
import pytest
from bothack.delegator import Delegator
from bothack.protocols import dispatch, KINDS


VALUES = {'choice': ['a', '', False], 'yesno': [False, True, 0, [], ''],
          'text': ['Excalibur', 'already\n', '', '\n', 42],
          'direction': ['NW', 'N', 'E', '.', '<', ''],
          'location': [{'x': 40, 'y': 10}, {'x': 0, 'y': 1}, ''],
          'menu': [['a', 'b'], [], 'a', '', ['2a', 'b']]}


@pytest.mark.oracle
@pytest.mark.parametrize('name,kind', [(n, k) for n, k in KINDS.items() if k in VALUES])
def test_encoding(oracle, name, kind):
    for value in VALUES[kind]:
        calls = []
        class Handler:
            def response_chosen(self, method, result):
                calls.append(['response', result])
        handler = Handler()
        setattr(handler, name.replace('-', '_'), lambda *args: value)
        delegator = Delegator(lambda text: calls.append(['write', text])).register(handler)
        dispatch(delegator, (name,))
        assert calls == oracle.call('delegator-response', name, value, False)
        calls.clear()
        delegator.inhibited = True
        dispatch(delegator, (name,))
        assert calls == oracle.call('delegator-response', name, value, True) == []


def test_queued_callbacks_can_reset_scraper():
    from bothack.scraper import Scraper
    calls = []
    scraper = Scraper(False)
    class Handler:
        def apply_what(self, text):
            return 'a'
    delegator = Delegator(calls.append).register(scraper, -10).register(Handler())
    dispatch(delegator, ('apply-what', 'What do you want to use or apply?'))
    assert scraper.state == 'no_mark'
    assert calls == ['a']


def test_action_notification_precedes_trigger():
    from bothack.scraper import Scraper
    scraper = Scraper(False)
    writes = []
    class Action:
        kind = 'autotravel'
        def trigger(self):
            assert scraper.state == 'no_mark'
            return '_'
    class Handler:
        def choose_action(self, game):
            return Action()
    delegator = Delegator(writes.append).register(scraper).register(Handler())
    dispatch(delegator, ('choose-action', {}))
    assert writes == ['_']
