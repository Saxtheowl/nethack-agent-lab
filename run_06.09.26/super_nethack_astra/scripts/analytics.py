#!/usr/bin/env python3
"""Game analytics for the Strategy tab.

Replays each game's frames.jsonl (incrementally, cached in
runs/games/<id>/analytics.json), extracts every NEW message line from the
message window, and turns them into typed events: kills, damage taken,
pickups, prayers, hunger, traps, thefts, Elbereth, level/XL milestones...
"""
import json
import re
from collections import Counter

import frames

MSG_ROWS = range(1, 8)
VERSION = 6

RULES = [
    ('kill', re.compile(r'You (?:kill|destroy) (?:the |an? )?(?:poor )?(.+?)!')),
    ('pet_kill', re.compile(r'(?:The )?(.+?) is (?:killed|destroyed)!')),
    ('xl', re.compile(r'Welcome to experience level (\d+)')),
    ('pickup', re.compile(r'^([a-zA-Z]) - (.+?)\.?$')),  # handled specially below
    ('pray', re.compile(r'You begin praying to (\w+)')),
    ('pray_result', re.compile(r'You feel that \w+ is (well-pleased|pleased|satisfied|displeased)|You feel a hopeful feeling|You feel that .* is displeased')),
    ('hungry', re.compile(r'You are beginning to feel hungry')),
    ('weak', re.compile(r'(?:You are beginning to feel weak|needs food, badly)')),
    ('faint', re.compile(r'You faint from lack of food')),
    ('eat', re.compile(r'(?:You finish eating|This) (?:the )?(.+?)(?: corpse)? (?:tastes|is delicious|really hits)')),
    ('trap', re.compile(r'(trap door opens|level teleport trap|teleportation trap|fall into a pit|bear trap closes|squeaky board|magic trap|gush of water|cloud of gas|arrow shoots out|dart shoots out|rock falls on your head|land mine|tower of flame|polymorph trap|caught in a web|anti-magic field|rust trap|flash of light)', re.I)),
    ('theft', re.compile(r'(stole|snatches|steals|purse feels lighter|seduces you)', re.I)),
    ('elbereth', re.compile(r'write in the dust here\? Elbereth')),
    ('flee', re.compile(r'turns to flee')),
    ('hit_by', re.compile(r'^(?:The |An? )?(.+?) (?:hits|bites|stings|butts|kicks|claws|touches you|thrusts|swings)!')),
    ('shop', re.compile(r"Welcome(?: again)? to (?:\w+)'s (.+?)!")),
    ('altar', re.compile(r'There is an altar to (\w+) \((\w+)\) here')),
    ('excalibur', re.compile(r'From the murky depths, a hand reaches up')),
    ('intrinsic', re.compile(r'(You feel a strange mental acuity|You feel (?:healthy|full of hot air|wide awake|very firm|especially healthy|quick|sensitive|a momentary chill|cool|in touch with the cosmos)|You speed up)')),
    ('wish', re.compile(r'For what do you wish\?')),
    ('death', re.compile(r'You die\.\.\.|is fatal|You die from')),
    ('lifesave', re.compile(r'But wait\.\.\.|medallion begins to glow')),
    ('stair', re.compile(r'You (climb up|descend) the stairs')),
    ('fall', re.compile(r'You fall through')),
    ('shop_buy', re.compile(r'You bought (.+?) for (\d+) gold')),
    ('found_hidden', re.compile(r'You find a hidden (door|passage)')),
    ('stoning', re.compile(r'You are slowing down|Your limbs are stiffening')),
    ('sick', re.compile(r'You feel deathly sick')),
]
SKIP_PICKUP = re.compile(r'for sale|gold piece|^\$')
import os
MONSTERS = set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'monster_names.json'))))
MONSTERS |= {'dog', 'cat', 'kitten', 'little dog', 'large dog', 'housecat', 'large cat'}
ITEM_PAT = re.compile(r'(?:^|  )([a-zA-Z]) - (.+?)(?:\.(?=  |$)|$)')
MONSTERISH = re.compile(r'^[a-z][a-z \-]+$')


def norm_item(s):
    s = re.sub(r'[+-]\d+ ', '', s)
    s = re.sub(r'\b(an?|the|\d+|uncursed|blessed|cursed|pair of|partly eaten)\b ?', '', s)
    s = re.sub(r'\([^)]*\)', '', s)
    return re.sub(r'\s+', ' ', s).strip(' .')


def analyze(gid):
    path = frames.GAMES / gid / 'frames.jsonl'
    cache_path = frames.GAMES / gid / 'analytics.json'
    try:
        cache = json.loads(cache_path.read_text())
        if cache.get('version') != VERSION:
            raise ValueError
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        cache = {'version': VERSION, 'pos': 0, 'index': 0, 'rows': {}, 'prev': [], 'events': [],
                 'status': None, 'series': [], 'levels': {}, 'maxdepth': 0}
    if not path.exists():
        return cache
    size = path.stat().st_size
    if size < cache['pos']:
        cache = {'version': VERSION, 'pos': 0, 'index': 0, 'rows': {}, 'prev': [], 'events': [],
                 'status': None, 'series': [], 'levels': {}, 'maxdepth': 0}
    rows = cache['rows']
    with open(path, 'rb') as f:
        f.seek(cache['pos'])
        for raw in f:
            if not raw.endswith(b'\n'):
                break
            cache['pos'] += len(raw)
            fr = json.loads(raw)
            i, t = fr['i'], fr['t']
            cache['index'] = i
            touched = False
            for y, segs in fr['r'].items():
                if int(y) in MSG_ROWS:
                    rows[y] = ''.join(s[0] for s in segs)[1:80].strip(' │')
                    touched = True
            st = fr.get('s')
            if st:
                turn, dlvl, hp, hpmax, xl, ac = st
                prev = cache['status']
                if not prev or prev[1] != dlvl:
                    depth = int(dlvl) if str(dlvl).isdigit() else 60
                    new_max = depth > cache['maxdepth']
                    cache['maxdepth'] = max(cache['maxdepth'], depth)
                    cache['events'].append({'t': t, 'f': i, 'turn': turn, 'type': 'level', 'v': str(dlvl), 'new': new_max})
                if prev and hp <= hpmax / 4 < prev[2]:
                    cache['events'].append({'t': t, 'f': i, 'turn': turn, 'type': 'lowhp', 'v': f'{hp}/{hpmax}'})
                lv = cache['levels'].setdefault(str(dlvl), [turn, turn])
                lv[1] = turn
                cache['status'] = st
                if not cache['series'] or turn - cache['series'][-1][0] >= 50:
                    cache['series'].append([turn, dlvl, hp, hpmax, xl, ac, round(t)])
            if not touched:
                continue
            cur = [rows.get(str(y), '') for y in MSG_ROWS]
            cur = [l for l in cur if l]
            prev = cache['prev']
            # new lines = what follows the longest overlap of prev's tail with cur's head
            k = 0
            for n in range(min(len(prev), len(cur)), 0, -1):
                if prev[-n:] == cur[:n]:
                    k = n
                    break
            new = cur[k:] if k or not prev else [l for l in cur if l not in prev]
            cache['prev'] = cur
            turn = cache['status'][0] if cache['status'] else 0
            recent = cache.setdefault('recent', [])
            for line in new:
                # curses menus/windows overlay the message rows: cut at the box border
                line = re.split(r'\s*[│└┌┐┘├]', line)[0].strip()
                if not line or any(l == line and abs(tn - turn) <= 5 for tn, l in recent):
                    continue
                recent.append([turn, line])
                del recent[:-30]
                if '│' not in line and ' - ' in line and 'What do you want' not in line:
                    for m in ITEM_PAT.finditer(line):
                        it = norm_item(m.group(2))
                        if it and not SKIP_PICKUP.search(m.group(2)) and len(it) < 50:
                            cache['events'].append({'t': t, 'f': i, 'turn': turn, 'type': 'pickup', 'v': it, 'msg': line[:120]})
                for kind, rx in RULES:
                    if kind == 'pickup':
                        continue
                    for m in rx.finditer(line):
                        v = m.group(1) if m.groups() and m.group(1) else m.group(0)
                        if kind == 'pickup':
                            if SKIP_PICKUP.search(line) or 'What do you want' in line:
                                continue
                            v = norm_item(m.group(2))
                        if kind in ('hit_by', 'pet_kill', 'kill'):
                            v = re.sub(r'^(tame|peaceful|poor|invisible|the|an?) ', '', v.strip().lower())
                            if v not in MONSTERS:
                                continue
                        if kind == 'pet_kill' and ('You' in line[:m.start() + 1]):
                            continue
                        cache['events'].append({'t': t, 'f': i, 'turn': turn, 'type': kind, 'v': v[:80], 'msg': line[:120]})
                        if kind not in ('pickup', 'kill', 'hit_by'):
                            break
    cache_path.write_text(json.dumps(cache, ensure_ascii=False))
    return cache


def summarize(gid):
    c = analyze(gid)
    ev = c['events']
    count = lambda k: Counter(e['v'].lower() for e in ev if e['type'] == k)
    first = {}
    for e in ev:
        if e['type'] == 'xl' and int(e['v']) in (3, 5, 8, 10, 12, 14) and f"XL{e['v']}" not in first:
            first[f"XL{e['v']}"] = e['turn']
        if e['type'] == 'level' and e.get('new') and e['v'].isdigit() and int(e['v']) in (3, 5, 7, 10, 15, 20, 25) and f"Dlvl{e['v']}" not in first:
            first[f"Dlvl{e['v']}"] = e['turn']
        if e['type'] in ('excalibur', 'wish') and e['type'] not in first:
            first[e['type']] = e['turn']
    return {
        'id': gid, 'events': len(ev), 'maxdepth': c['maxdepth'],
        'kills': count('kill'), 'pet_kills': count('pet_kill'), 'hit_by': count('hit_by'),
        'pickups': count('pickup'), 'traps': count('trap'), 'thefts': count('theft'),
        'eaten': count('eat'), 'shops': count('shop'), 'altars': count('altar'), 'intrinsics': count('intrinsic'),
        'bought': count('shop_buy'),
        'n': {k: sum(1 for e in ev if e['type'] == k) for k in
              ('kill', 'pet_kill', 'pickup', 'pray', 'hungry', 'weak', 'faint', 'trap', 'theft', 'elbereth',
               'flee', 'lowhp', 'stair', 'fall', 'found_hidden', 'excalibur', 'wish', 'lifesave', 'eat', 'shop_buy', 'hit_by')},
        'prayers': [{'turn': e['turn'], 'f': e['f']} for e in ev if e['type'] == 'pray'],
        'pray_results': [e['v'] for e in ev if e['type'] == 'pray_result'],
        'milestones': first,
        'levels': c['levels'], 'series': c['series'],
        'key_events': [e for e in ev if e['type'] in ('xl', 'pray', 'trap', 'theft', 'excalibur', 'wish', 'lifesave',
                                                     'intrinsic', 'lowhp', 'death', 'faint', 'altar', 'shop', 'fall')
                       or (e['type'] == 'level' and e.get('new'))][-400:],
    }


if __name__ == '__main__':
    import sys
    s = summarize(sys.argv[1])
    print(json.dumps({k: v for k, v in s.items() if k not in ('series', 'key_events')}, ensure_ascii=False, indent=1)[:3000])
