"""Bag contents as NetHack shows them ("Contents of the bag:" window).

Used by the inventory tool (which opens safe bags itself) and by the recorder,
which watches every screen: whenever an agent looks into a bag, the contents
it saw are kept in runs/games/<game>/bags.json (one entry per kind of bag),
so the dashboard can show them even for a bag the tool may not open (a bag
of unknown curse status could be a cursed bag of holding: opening one makes
items vanish).
"""
import json
import re
import time

import frames

PAGE = re.compile(r'\((?:Page )?(\d+) of (\d+)\)')


def window(lines):
    """(col, top row, title) of a "Contents of X:" window on screen, or None."""
    for i, line in enumerate(lines):
        c = line.find('Contents of ')
        if c > 0:
            return c, i, line[c:].split('│')[0].strip()
    return None


def items(lines, col, top):
    """Item lines of the window whose text starts at column `col` (each item
    is indented by two spaces; the title and the page marker are not)."""
    out = []
    for line in lines[top:]:
        if len(line) <= col or line[col - 1] == '└':
            break
        seg = line[col:].split('│')[0]
        if seg.startswith('  ') and seg.strip() and not PAGE.fullmatch(seg.strip()):
            out.append(seg.strip())
    return out


def page(lines, col, top):
    for line in lines[top:]:
        if len(line) <= col or line[col - 1] == '└':
            break
        m = PAGE.search(line[col:].split('│')[0])
        if m:
            return int(m[1]), int(m[2])
    return 1, 1


def kind(name):
    """'an uncursed bag of holding containing 3 items' and 'Contents of the bag
    of holding:' -> 'bag of holding' (so a look and an inventory line match)."""
    n = re.sub(r'^Contents of ', '', name.strip()).rstrip(':')
    n = re.sub(r'\s+(?:containing \d+ items?|\(.*\))$', '', n)
    n = re.sub(r"^(?:the|your|a|an|\d+|[A-Z][a-z]+'s)\s+", '', n)
    n = re.sub(r'^(?:(?:uncursed|blessed|cursed|greased|burnt|rotted|thoroughly|very|partly)\s+)+', '', n)
    n = re.sub(r'\s+(?:called|named)\s+.*$', '', n)
    return n.strip()


class Watcher:
    """Fed every recorded screen of one game; saves what a look showed once
    the window closes (all pages of it)."""

    def __init__(self, game_id):
        self.path = frames.GAMES / game_id / 'bags.json'
        self.cur = None

    def feed(self, lines, turn):
        w = window(lines)
        if w:
            col, top, title = w
            if not self.cur or self.cur['title'] != title:
                self.flush()
                self.cur = {'title': title, 'col': col, 'top': top, 'pages': {}, 'turn': turn}
        elif not (self.cur and len(lines) > self.cur['top'] and len(lines[self.cur['top'] - 1]) > self.cur['col']
                  and lines[self.cur['top'] - 1][self.cur['col'] - 1] == '┌'):
            self.flush()  # window gone (a later page has no title but keeps the frame)
            return
        col, top = self.cur['col'], self.cur['top']
        p, _ = page(lines, col, top)
        got = items(lines, col, top)
        if len(got) >= len(self.cur['pages'].get(p, [])):  # a half-drawn frame shows fewer lines
            self.cur['pages'][p] = got
        self.cur['n'] = page(lines, col, top)[1]

    def flush(self):
        cur, self.cur = self.cur, None
        if not cur or len(cur['pages']) < cur.get('n', 1):
            return  # nothing, or not every page was seen
        try:
            data = json.loads(self.path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        data[kind(cur['title'])] = {'title': cur['title'], 'turn': cur['turn'], 't': time.time(),
                                    'items': [x for p in sorted(cur['pages']) for x in cur['pages'][p]]}
        self.path.write_text(json.dumps(data, ensure_ascii=False))
