"""World model: observation, memory and hypothesis.

- observation: a settled screen (one settled frame is not one turn)
- memory:     explored maps per dungeon level
- hypothesis: monster positions, valid only as of the last screen
Snapshots never share mutable state with later updates.
"""

import re

ROW_MESSAGE = 0
ROW_STATUS1 = 22
ROW_STATUS2 = 23
MAP_H = 21          # rows 1..21
W = 80

# ---- status line parsing (target format: showscore + time enabled) ----
BOTL1_RE = re.compile(
    r"^(?P<name>.+?)\s+the\s+(?P<title>.+?)\s+St:(?P<st>-?\d+(/\d+)?)\s+"
    r"Dx:(?P<dx>\d+)\s+Co:(?P<co>\d+)\s+In:(?P<in>\d+)\s+Wi:(?P<wi>\d+)\s+"
    r"Ch:(?P<ch>-?\d+)\s+(?P<align>Lawful|Neutral|Chaotic)"
    r"(?:\s+S:(?P<score>-?\d+))?"
)
BOTL2_RE = re.compile(
    r"(Dlvl:\d+|Home \d+|Fort Ludios|End Game|Astral Plane)"
    r"\s+\$:(?P<gold>\d+)\s+HP:(?P<hp>\d+)\((?P<maxhp>\d+)\)\s+"
    r"Pw:(?P<pw>\d+)\((?P<maxpw>\d+)\)\s+AC:(?P<ac>-?\d+)\s+"
    r"(?:Exp|Xp|HD):(?P<xpl>\d+)(?:/(?P<xpln>\d+))?\s+T:(?P<turn>\d+)"
)
FLAGS = {
    "Bl": "blind", "Stu": "stunned", "Con": "confused", "Foo": "ill",
    "Il": "ill", "Ha": "hallucinating", "Lev": "levitating", "Rde": "riding",
    "Fly": "flying", "Trl": "travelling", "Unk": "unknown", "Ve": "petrifying",
    "Sn": "sliming", "Elt": "elbereth",
}
FOOD_STATES = {"Hun": "hungry", "Wea": "weak", "Fai": "fainting"}


class Status:
    def __init__(self):
        self.name = ""
        self.title = ""
        self.alignment = ""
        self.score = 0
        self.dlvl = None
        self.level_desc = ""
        self.gold = 0
        self.hp = 0
        self.maxhp = 0
        self.pw = 0
        self.maxpw = 0
        self.ac = 0
        self.turn = 0
        self.hunger = None
        self.flags = set()
        self.raw1 = ""
        self.raw2 = ""

    @classmethod
    def parse(cls, lines):
        s = cls()
        s.raw1 = lines[ROW_STATUS1].rstrip()
        s.raw2 = lines[ROW_STATUS2].rstrip()
        m1 = BOTL1_RE.search(s.raw1)
        if m1:
            s.name = m1.group("name")
            s.title = m1.group("title")
            s.alignment = m1.group("align")
            s.score = int(m1.group("score") or 0)
        m2 = BOTL2_RE.search(s.raw2)
        if m2:
            s.level_desc = m2.group(1)
            if s.level_desc.startswith("Dlvl:"):
                s.dlvl = int(s.level_desc[5:])
            s.gold = int(m2.group("gold"))
            s.hp = int(m2.group("hp"))
            s.maxhp = int(m2.group("maxhp"))
            s.pw = int(m2.group("pw"))
            s.maxpw = int(m2.group("maxpw"))
            s.ac = int(m2.group("ac"))
            s.turn = int(m2.group("turn"))
        for token in s.raw2.split():
            if token in FLAGS:
                s.flags.add(FLAGS[token])
            elif token in FOOD_STATES:
                s.hunger = FOOD_STATES[token]
        return s

    def valid(self):
        return self.maxhp > 0 and "HP:" in self.raw2 and "T:" in self.raw2


def classify_glyph(ch):
    """-> (walkable, kind) for a remembered map glyph."""
    if ch == ".":
        return True, "."
    if ch == "<":
        return True, "<"
    if ch == ">":
        return True, ">"
    if ch == "]":
        return False, "]"
    if ch == "^":
        return True, "^"
    if ch in "{_":
        return True, ch
    if ch in "|-":
        return False, "|"
    if ch == "\\":
        return False, "\\"
    if ch == "}":
        return False, "}"
    if ch == "I":
        return False, "|"
    return True, "."          # objects, monsters, misc: remembered as floor


class Monster:
    __slots__ = ("glyph", "pos")

    def __init__(self, glyph, pos):
        self.glyph = glyph
        self.pos = pos


class Level:
    """Memory of one dungeon level: 80 cols x 21 rows."""

    W, H = W, MAP_H

    def __init__(self, key, desc):
        self.key = key
        self.desc = desc
        self.seen = [[False] * self.W for _ in range(self.H)]
        self.walkable = [[False] * self.W for _ in range(self.H)]
        self.kind = [["?"] * self.W for _ in range(self.H)]
        self.stairs_down = None
        self.stairs_up = None

    def observe(self, lines, px, py):
        """Merge one settled screen; returns observed monsters (hypothesis)."""
        monsters = []
        for row in range(1, 22):
            y = row - 1
            for x in range(self.W):
                ch = lines[row][x]
                if ch == " ":
                    continue
                if y == py and x == px:
                    continue                     # the hero glyph itself
                walk, kind = classify_glyph(ch)
                self.seen[y][x] = True
                self.walkable[y][x] = walk
                self.kind[y][x] = kind
                if ch == ">":
                    self.stairs_down = (x, y)
                elif ch == "<":
                    self.stairs_up = (x, y)
                if ch.isalpha() or ch in "&'~m":
                    monsters.append(Monster(ch, (x, y)))
        self.seen[py][px] = True                     # the hero stands here
        self.walkable[py][px] = True
        if self.kind[py][px] == "?":
            self.kind[py][px] = "."
        return monsters

    def adjacent(self, x, y):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.W and 0 <= ny < self.H:
                    yield nx, ny

    def bfs(self, start, blocked):
        """BFS over walkable memory -> (dist, prev); blocked set excluded.

        Diagonal steps additionally require both orthogonal corner cells to
        be walkable (the NetHack diagonal-movement rule) - an unseen corner
        counts as passable (optimistic) so exploration can proceed.
        """
        dist = {start: 0}
        prev = {}
        frontier = [start]
        blocked = set(blocked)
        while frontier:
            nxt = []
            for (x, y) in frontier:
                for nx, ny in self.adjacent(x, y):
                    if (nx, ny) in dist or (nx, ny) in blocked:
                        continue
                    if not self.walkable[ny][nx]:
                        continue
                    if nx != x and ny != y:
                        if not self.passable_corner(x, y, nx, ny):
                            continue
                    dist[(nx, ny)] = dist[(x, y)] + 1
                    prev[(nx, ny)] = (x, y)
                    nxt.append((nx, ny))
            frontier = nxt
        return dist, prev

    def passable_corner(self, x, y, nx, ny):
        dx = 1 if nx > x else -1
        dy = 1 if ny > y else -1
        for cx, cy in ((x + dx, y), (x, y + dy)):
            if self.seen[cy][cx] and not self.walkable[cy][cx]:
                return False
        return True

    def explore_targets(self, start, blocked):
        """Reachable walkable cells adjacent to unseen ground.
        Returns sorted list of (dist, cell, frontier_cell)."""
        dist, _ = self.bfs(start, blocked)
        targets = []
        for (x, y), d in dist.items():
            if not self.walkable[y][x]:
                continue
            for nx, ny in self.adjacent(x, y):
                if not self.seen[ny][nx]:
                    targets.append((d, (x, y), (nx, ny)))
                    break
        targets.sort(key=lambda t: (t[0], t[1]))
        return targets

    def door_targets(self, start, blocked):
        """Reachable cells adjacent to a closed door ']'."""
        dist, _ = self.bfs(start, blocked)
        targets = []
        for (x, y), d in dist.items():
            if not self.walkable[y][x]:
                continue
            for nx, ny in self.adjacent(x, y):
                if self.kind[ny][nx] == "]":
                    targets.append((d, (x, y), (nx, ny)))
                    break
        targets.sort(key=lambda t: (t[0], t[1]))
        return targets


class World:
    def __init__(self):
        self.levels = {}
        self.dlvl = None
        self.status = Status()
        self.monsters = []           # hypothesis, refreshed each frame
        self.px = None
        self.py = None

    def level(self):
        key = self.status.level_desc or "Dlvl:1"
        if key not in self.levels:
            self.levels[key] = Level(key, self.status.level_desc)
        return self.levels[key]

    def observe(self, lines, cx, cy):
        st = Status.parse(lines)
        if st.valid():
            self.status = st
            self.dlvl = st.dlvl
        self.px, self.py = cx, cy
        lvl = self.level()
        self.monsters = lvl.observe(lines, cx, cy)
        return self.monsters

    def hostile_adjacent(self):
        out = []
        for m in self.monsters:
            x, y = m.pos
            if abs(x - self.px) <= 1 and abs(y - self.py) <= 1:
                if m.glyph == "@":
                    continue        # '@' other than us: peaceful humans
                out.append(m)
        return out
