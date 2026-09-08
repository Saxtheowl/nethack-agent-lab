"""Run actual, captured reference results without requiring a JVM."""
from dataclasses import asdict
import json
from pathlib import Path
import pytest
from bothack.item import parse_label
from bothack.itemid import possible_prices
from bothack.scraper import effective_strength, parse_botls, choice_call, menu_fn, multi_menu, merge_menu, prompt_fn, location_fn
from bothack.sokoban import moves_for
from bothack.actions import action, SPECS

CORPUS = json.loads((Path(__file__).parent / "fixtures/original-core.json").read_text())


def scraper_call(kind, message):
    if kind == 'choice':
        return list(choice_call(message))
    if kind == 'menu':
        return dict(fn=menu_fn(message), multi=multi_menu(message), merge=merge_menu(message))
    return {'prompt': prompt_fn, 'location': location_fn}[kind](message)


def from_spec(spec):
    name, args = spec
    if name == 'Repeated':
        args = [from_spec(args[0]), args[1]]
    kind = next(k for k, s in SPECS.items() if s[0] == name)
    return action(kind, *args)


@pytest.mark.parametrize("case", CORPUS["cases"], ids=lambda c: c["op"] + repr(c["args"]))
def test_frozen_reference(case):
    functions = {"label": parse_label, "strength": effective_strength, "status": parse_botls,
                 "scraper-call": scraper_call,
                 "action-trigger": lambda spec: from_spec(spec).trigger(),
                 "prices": lambda *args: sorted(possible_prices(*args), key=lambda x: str(x)),
                 "moves": lambda *args: [asdict(p) for p in moves_for(*args)]}
    result = functions[case["op"]](*case["args"])
    if case["op"] == "prices":
        assert set(result) == set(case["expected"])
    else:
        assert result == case["expected"]
