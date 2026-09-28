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
CLASS_ORDER = ['Coins', 'Amulets', 'Weapons', 'Armor', 'Comestibles', 'Scrolls', 'Spellbooks', 'Potions', 'Rings',
               'Wands', 'Tools', 'Gems/Stones', 'Boulders/Statues', 'Iron balls', 'Chains', 'Venoms', 'Other']
PAGE = re.compile(r'\((?:Page )?(\d+) of (\d+)\)')


def parse(text, items, order):
    """Read the `i` menu (left of the permanent panel) and the panel itself in
    two separate passes, so their class headers never mix. Menu text wins."""
    lines = text.splitlines()
    for which in ('menu', 'panel'):
        # a new menu page continues the class of the previous page
        cls = parse.last_menu_cls if which == 'menu' else None
        for line in lines:
            parts = line.split('││')
            if which == 'menu':
                part = parts[0]
            elif len(parts) > 1:
                part = parts[-1]
            else:
                continue
            c = CLASS.search('│' + part + '│')
            if c:
                cls = c[1]
            for m in ITEM.finditer(part):
                letter, name = m[1], m[2].strip()
                old = items.get(letter)
                if old is None or (which == 'menu' and old['src'] == 'panel') or (
                        old['src'] == which and len(name) > len(old['name'])):
                    items[letter] = {'letter': letter, 'name': name, 'class': cls, 'src': which}
                if letter not in order:
                    order.append(letter)
        if which == 'menu':
            parse.last_menu_cls = cls


parse.last_menu_cls = None


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
           'items': sorted(({k: v for k, v in items[x].items() if k != 'src'} for x in order if x in items),
                           key=lambda it: (CLASS_ORDER.index(it['class']) if it['class'] in CLASS_ORDER else 99))}
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
