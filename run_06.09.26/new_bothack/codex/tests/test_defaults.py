"""Compare all present and absent fallback handlers to the original object."""
import pytest
from bothack.defaults import DefaultResponses, PRIORITY_BOTTOM
from bothack.delegator import Delegator
from bothack.protocols import KINDS, dispatch


@pytest.mark.oracle
@pytest.mark.parametrize('name', KINDS)
def test_original_fallback(oracle, name):
    method = getattr(DefaultResponses(), name.replace('-', '_'), None)
    result = {'handled': method is not None}
    if method:
        response = method()
        result['response'] = sorted(response) if isinstance(response, set) else response
    assert result == oracle.call('default-response', name)


def test_user_handler_precedes_fallback():
    writes = []
    class Decision:
        def really_attack(self, target):
            return True
    delegator = Delegator(writes.append).register(DefaultResponses(), PRIORITY_BOTTOM)
    decision = Decision()
    delegator.register(decision)
    dispatch(delegator, ('really-attack', 'a dwarf'))
    delegator.deregister(decision)
    dispatch(delegator, ('really-attack', 'a dwarf'))
    dispatch(delegator, ('eat-what', 'Which food?'))
    assert writes == ['y', 'n', '\x1b']
