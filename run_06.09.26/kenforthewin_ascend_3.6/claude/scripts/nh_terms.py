#!/usr/bin/env python3
"""Put original NetHack terms back into French texts (user rule: game
elements keep their English names). Usage: nh_terms.py FILE.jsonl ...
(rewrites title/text fields) — also importable: fix(text)."""
import json
import re
import sys

RULES = [
    (r"niveau d['’]expérience (\d+)", r'XL \1'), (r"\bniveaux? (\d+)", r'Dlvl \1'),
    (r'\bau tour (\d+)', r'à T\1'), (r'\btour (\d+)', r'T\1'),
    (r'\b(\d+) PV\b', r'HP \1'), (r'\bPV\b', 'HP'), (r'\bCA\b', 'AC'),
    (r"amulettes? d['’]étranglement", 'amulet of strangulation'),
    (r"amulettes? de télépathie", 'amulet of ESP'), (r'[Aa]mulettes?', 'amulet'),
    (r'[Pp]archemins? de feu', 'scroll of fire'), (r'[Pp]archemins?', 'scroll'),
    (r'[Bb]aguettes?', 'wand'), (r'[Aa]nneaux?', 'ring'), (r'\b[Bb]agues?\b', 'ring'),
    (r'grands? coffres?', 'large box'), (r'\bcoffres?\b', 'chest'),
    (r'\b[Ff]ontaines?\b', 'fountain'), (r'\b[Aa]utels?\b', 'altar'), (r'\b[Pp]ièges?\b', 'trap'),
    (r'\b[Bb]outiques?\b', 'shop'), (r'\b[Pp]rière\b', 'prayer'), (r'\b[Cc]haton\b', 'kitten'),
    (r'\b[Éé]pée longue\b', 'long sword'), (r'\b[Dd]agues?\b', 'dagger'), (r'\b[Cc]asque\b', 'helmet'),
    (r'\b[Bb]andeau\b', 'blindfold'), (r'\b[Cc]lé\b', 'key'), (r'\b[Oo]eil flottant\b', 'floating eye'),
    (r'\bœil flottant\b', 'floating eye'), (r'vague psychique', 'psychic blast'),
]


def fix(text):
    for pat, rep in RULES:
        text = re.sub(pat, rep, text)
    return text


if __name__ == '__main__':
    for path in sys.argv[1:]:
        rows = [json.loads(l) for l in open(path) if l.strip()]
        for r in rows:
            for k in ('title', 'text'):
                if isinstance(r.get(k), str):
                    r[k] = fix(r[k])
        with open(path, 'w') as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)
