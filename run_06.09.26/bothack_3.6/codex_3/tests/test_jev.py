import json
import sys
from pathlib import Path
from unittest import mock
import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent / "claude"
sys.path[:0] = [str(ROOT), str(BASE)]

from jev_common import DecisionJournal, OpenRouterDecider
from jev_policy_support import strip_strategic_handlers


class FakeResponse:
    headers = {"x-request-id": "req-test"}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps({
            "model": "typesafe/jev-1.13",
            "answers": {"next_action": {"type": "choice", "choice": "b",
                "confidence": .75, "probabilities": {"a": .2, "b": .8}}},
            "usage": {"input_tokens": 100, "output_tokens": 4},
        }).encode()


def test_openrouter_decision_shape():
    client = OpenRouterDecider(api_key="test", retries=0)
    with mock.patch("urllib.request.urlopen", return_value=FakeResponse()) as call:
        answer = client.choose({"turn": 1}, {"a": "wait", "b": "move"},
                               "choose")
    sent = json.loads(call.call_args.args[0].data)
    assert sent["questions"]["next_action"]["type"] == "choice"
    assert sent["questions"]["next_action"]["criteria"]["b"] == "move"
    assert answer.choice == "b"
    assert answer.probabilities["b"] == .8
    assert answer.cost_usd == pytest.approx(100 * .042 / 1_000_000)


def test_journal_links_outcome(tmp_path):
    journal = DecisionJournal(str(tmp_path), "TEST")
    decider = OpenRouterDecider(offline=True)
    choices = {"move": {"description": "move", "action": {"type": "move"}}}
    before = {"turn": 1, "level": "1", "branch": "main",
              "position": {"x": 1, "y": 1},
              "player": {"hp": 10, "xplvl": 1}, "messages": []}
    after = {**before, "turn": 2, "position": {"x": 2, "y": 1}}
    journal.decide(decider, before, choices, "choose", True)
    journal.observe(after)
    journal.close()
    rows = [json.loads(x) for x in (tmp_path / "jev_decisions.jsonl").read_text().splitlines()]
    assert [r["event"] for r in rows] == ["decision", "outcome", "summary"]
    assert rows[1]["turn_delta"] == 1


def test_strategy_loader_is_disabled():
    from pybothack.bh36 import new_bh36
    bh = new_bh36({"bot": "mainbot"})
    before = sum(hasattr(h, "choose_action")
                 for _priority, _seq, h in bh.delegator.handlers)
    strip_strategic_handlers(bh)
    bh.delegator.started()
    bh.delegator.drain()
    after = sum(hasattr(h, "choose_action")
                for _priority, _seq, h in bh.delegator.handlers)
    assert before == after  # plumbing stayed; mainbot added no strategy
