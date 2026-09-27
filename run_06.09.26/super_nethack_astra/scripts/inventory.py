#!/usr/bin/env python3
"""Full inventory (the right-hand perm_invent panel is cut after ~33 lines).

  NH_SLOT=N python3 scripts/inventory.py        (or slots/N/inv)

Opens `i` (a free action: no game turn passes), reads every page, closes the
menu, prints the whole list and saves it to runs/games/<game>/inventory.json
for the dashboard ("Inventaire complet").
"""
import json
import re
import time

import frames
import session

ITEM = re.compile(r'(?:^|[│ ])\s?([a-zA-Z$#])\) (.+?)\s*(?:│|$)')
CLASS = re.compile(r'[│ ](Coins|Amulets|Weapons|Armor|Comestibles|Scrolls|Spellbooks|Potions|Rings|Wands|Tools|'
                   r'Gems/Stones|Boulders/Statues|Iron balls|Chains|Venoms|Other)\s*│')
PAGE = re.compile(r'\((?:Page )?(\d+) of (\d+)\)')


def parse(text, items, order):
    cls = None
    for line in text.splitlines():
        # the `i` menu sits left of the permanent panel: read the menu part first
        for part in line.split('││'):
            c = CLASS.search('│' + part + '│')
            if c:
                cls = c[1]
            for m in ITEM.finditer(part):
                letter, name = m[1], m[2].strip()
                if len(name) > len(items.get(letter, {}).get('name', '')):
                    items[letter] = {'letter': letter, 'name': name, 'class': cls or items.get(letter, {}).get('class')}
                if letter not in order:
                    order.append(letter)


def main():
    before = session.screen()
    turn = re.search(r'\bT:(\d+)', before)
    session.send('i', publish=False)
    time.sleep(.8)
    items, order, seen = {}, [], set()
    for _ in range(12):
        text = session.screen()
        parse(text, items, order)
        page = PAGE.search(text)
        if not page or page[1] == page[2] or text in seen:
            break
        seen.add(text)
        session.send('>', publish=False)
        time.sleep(.6)
    session.send('Escape', named=True, publish=False)
    time.sleep(.4)
    if PAGE.search(session.screen()):
        session.send('Escape', named=True, publish=False)
    out = {'t': time.time(), 'turn': int(turn[1]) if turn else None,
           'items': [items[k] for k in order if k in items]}
    try:
        info = json.loads(session.SLOTFILE.read_text())
        (frames.GAMES / info['game_id'] / 'inventory.json').write_text(json.dumps(out, ensure_ascii=False))
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        pass
    cls = None
    for it in out['items']:
        if it['class'] != cls:
            cls = it['class']
            print(cls or '?')
        print(f"  {it['letter']}) {it['name']}")
    print(f"{len(out['items'])} items (T{out['turn']})")


if __name__ == '__main__':
    main()
