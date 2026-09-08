"""Capture a small offline reference corpus from the actual Clojure oracle."""
from dataclasses import asdict
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.oracle import Oracle


def main():
    cases = []
    def add(op, *args):
        cases.append({"op": op, "args": list(args)})
    values = {'dir': 'NW', 'cnt': 3, 'pos': {'x': 40, 'y': 10}, 'slot': 'a',
              'name': 'STASH', 'qty': 2, 'label-or-list': ['a dagger'],
              'slot-or-label': 'a', 'action': ['Search', []], 'n': 10,
              'item-slot': 'a', 'potion-slot': 'b', 'what': 'Elbereth',
              'append?': False, 'shk': {'x': 39, 'y': 10}}
    source = (ROOT / 'upstream/BotHack/src/bothack/actions.clj').read_text()
    for name, fields in re.findall(r'\(defaction (\w+) \[([^\]]*)\]', source):
        add('action-trigger', [name, [values[field] for field in fields.split()]])
    for label in ("a blessed +1 long sword (weapon in hand)", "3 uncursed food rations",
                  "2 potions of holy water", "a potion of unholy water", "a wand of wishing (1:3)",
                  "a Candelabrum of Invocation (7 candles, lit)", "Lord Surtur's partly eaten corpse",
                  "a greased rustproof +0 long sword", "a bag called bag1 named STASH", "2 gunyoki"):
        add("label", label)
    for strength in ("3", "18", "18/00", "18/49", "18/50", "18/99", "18/**", "25"):
        add("strength", strength)
    for message in ('What do you want to charge? [a-z]', 'Really attack the peaceful dwarf? [yn]',
                    'There is a newt corpse here; eat it? [yn]',
                    'You have much trouble lifting a chest. Continue? [yn]',
                    'Izchak offers 100 gold pieces for your daggers.  Sell them? [yn]'):
        add('scraper-call', 'choice', message)
    for head in ('Pick up what?', 'What would you like to identify first?', 'Pick a skill to advance:'):
        add('scraper-call', 'menu', head)
    for message in ('For what do you wish?', 'What do you want to engrave on the floor here?'):
        add('scraper-call', 'prompt', message)
    add('scraper-call', 'location', 'Where do you want to travel to?')
    for base in (1, 7, 20, 60, 175, 500):
        for cha in (0, 5, 7, 10, 15, 17, 18, 25):
            add("prices", base, cha)
    for a, b in (([40, 9], [42, 9]), ([43, 16], [39, 16]), ([42, 7], [42, 15]), ([34, 17], [34, 13])):
        add("moves", a, b)
    for level in ("Dlvl:1", "Home 3", "Astral Plane"):
        add("status", ["Bot the Fighter St:18/50 Dx:12 Co:18 In:8 Wi:10 Ch:7 Lawful S:12345",
                       f"{level} $:123 HP:40(100) Pw:10(20) AC:-15 Exp:14 T:15000 Weak Burdened"])
    with Oracle() as oracle:
        for case in cases:
            case["expected"] = oracle.call(case["op"], *case["args"])
    target = ROOT / "tests/fixtures/original-core.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({"revision": "70226b3c8ed12d29c64068aec0acc0ca71d57adf", "cases": cases}, indent=2) + "\n")
    print(f"Captured {len(cases)} cases from Clojure")


if __name__ == "__main__":
    main()
