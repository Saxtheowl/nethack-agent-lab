import pytest
from bothack.delegator import Delegator, UnhandledPrompt


def test_priority_false_and_inhibition():
    events, writes = [], []
    class Handler:
        def __init__(self, value): self.value = value
        def yes_no(self): return self.value
        def event(self): events.append(self.value)
    d = Delegator(writes.append)
    d.register(Handler(True), 10)
    d.register(Handler(False), -10)
    assert d.prompt("yes_no") is False
    d.respond("yes_no", transform=lambda value: "y" if value else "n")
    assert writes == ["n"]
    d.inhibited = True
    d.respond("yes_no")
    d.event("event")
    assert events == [False, True]
    assert writes == ["n"]


def test_mutation_during_event_uses_snapshot_and_empty_response_escapes():
    writes = []
    d = Delegator(writes.append)
    class Once:
        def event(self): d.deregister(self)
        def choose(self): return ""
    h = Once()
    d.register(h)
    d.respond("choose")
    assert writes == ["\x1b"]
    d.event("event")
    with pytest.raises(UnhandledPrompt):
        d.prompt("choose")


def test_empty_collection_is_a_response_and_exception_falls_through():
    class Broken:
        def choose(self): raise ValueError("upstream catches handler errors")
    class Empty:
        def choose(self): return []
    d = Delegator(lambda _: None).register(Broken(), -1).register(Empty())
    assert d.prompt("choose") == []
