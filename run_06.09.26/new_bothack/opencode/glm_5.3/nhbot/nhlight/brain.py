"""Autonomous play: explicit priorities, deterministic ties.

Every behaviour declares its precondition; the first satisfied one acts.
Transactions (menus, prompts) are returned as Action objects and are
executed by the Game driver through Dialogue.pump().
"""

import random
import re

from .dialogue import DIR_KEYS

MENU_ITEM_RE = re.compile(r"^\s*([a-zA-Z])\s+-\s+(.+?)\s*$")

FOOD_WORDS = (
    "food ration", "apple", "orange", "pear", "melon", "banana", "carrot",
    "clove of garlic", "tripe ration", "egg", "grape", "slime mold",
    "lump of royal jelly", "cream pie", "candy bar", "pancake", "burrito",
    "cram ration", "meatball", "meat stick", "huge chunk of meat",
    "k-ration", "c-ration", "lembas wafer", "mushroom",
)
ARMOR_BONUS = {
    "leather jacket": 1, "leather armor": 2, "studded leather armor": 3,
    "ring mail": 3, "scale mail": 4, "chain mail": 5, "orcish chain mail": 5,
    "banded mail": 6, "splint mail": 6, "bronze plate mail": 6,
    "plate mail": 7, "crystal plate mail": 8, "dwarvish mithril-coat": 8,
    "mithril-coat": 8,
}
ARMOR_EXTRA = ("helmet", "boots", "gloves", "cloak", "shield", "robe",
               "shirt")


def is_food(desc):
    d = desc.lower()
    return any(w in d for w in FOOD_WORDS) or "ration" in d or \
        d.endswith("corpse")


def is_armor(desc):
    d = " " + desc.lower() + " "
    return any((" " + w) in d for w in list(ARMOR_BONUS) + list(ARMOR_EXTRA))


def armor_bonus_of(desc):
    d = desc.lower()
    best = None
    for k, v in ARMOR_BONUS.items():
        if k in d and (best is None or v > best):
            best = v
    return best


def menu_options(lines):
    """Parse one menu page into [(letter, description)]."""
    out = []
    for y in range(1, 21):
        line = lines[y] if y < len(lines) else ""
        m = MENU_ITEM_RE.match(line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def _chain(first, second):
    """Two-stage policy: `first` handles the opening prompt, `second` menus."""
    def policy(kind, detail):
        resp = first(kind, detail)
        if resp is not None:
            return resp
        return second(kind, detail)
    return policy


class Action:
    def __init__(self, kind, keys="", reason="", policy=None, on_done=None):
        self.kind = kind          # move | attack | tx | open | pray | wait
        self.keys = keys
        self.reason = reason
        self.policy = policy      # callable(kind, detail) -> keys or None
        self.on_done = on_done    # zero-arg callback executed after success


class Brain:
    """choose() -> Action: first satisfied behaviour in priority order."""

    def __init__(self, world, dialogue, seed=12345):
        self.world = world
        self.dialogue = dialogue
        self.lines = None            # last settled screen, set by the driver
        self.rng = random.Random(seed)
        self.last_pray_turn = -100_000
        self.best_bonus = 0          # best armor bonus worn so far

    # -- observation helpers -------------------------------------------
    def glyph_at(self, x, y):
        if self.lines is None:
            return " "
        return self.lines[y + 1][x]

    def hostiles(self):
        return self.world.hostile_adjacent()

    def blocked_cells(self):
        """Never path through remembered traps or visible monsters."""
        lvl = self.world.level()
        blocked = set()
        for y in range(lvl.H):
            for x in range(lvl.W):
                if lvl.kind[y][x] == "^":
                    blocked.add((x, y))
        for m in self.world.monsters:
            blocked.add(m.pos)
        return blocked

    def _adjacent_key(self, cell):
        dx = max(-1, min(1, cell[0] - self.world.px))
        dy = max(-1, min(1, cell[1] - self.world.py))
        return DIR_KEYS.get((dx, dy), ".")

    def _path_first(self, target):
        """First single-step cell along the BFS path to `target`."""
        lvl = self.world.level()
        dist, prev = lvl.bfs((self.world.px, self.world.py),
                             self.blocked_cells())
        if target not in dist:
            return None
        cur = target
        while prev.get(cur) != (self.world.px, self.world.py):
            if cur not in prev:
                return None
            cur = prev[cur]
        if dist[cur] >= 1:
            return cur
        return None

    def _frontier(self, blocked):
        return self.world.level().explore_targets(
            (self.world.px, self.world.py), blocked)

    def _door_list(self, blocked):
        return self.world.level().door_targets(
            (self.world.px, self.world.py), blocked)

    def _flee_adjacent(self, hostiles):
        lvl = self.world.level()
        hx, hy = self.world.px, self.world.py
        best, best_score = None, None
        for nx, ny in lvl.adjacent(hx, hy):
            if not lvl.walkable[ny][nx]:
                continue
            if any((nx, ny) == m.pos for m in self.world.monsters):
                continue
            d = min(abs(nx - m.pos[0]) + abs(ny - m.pos[1])
                    for m in hostiles)
            trap = -3 if lvl.kind[ny][nx] == "^" else 0
            score = d + trap
            if best_score is None or score > best_score:
                best, best_score = (nx, ny), score
        return best

    def _fidget(self):
        lvl = self.world.level()
        hx, hy = self.world.px, self.world.py
        cands = [(x, y) for x, y in lvl.adjacent(hx, hy)
                 if lvl.walkable[y][x]
                 and lvl.kind[y][x] != "^"
                 and not any((x, y) == m.pos for m in self.world.monsters)]
        if not cands:
            return None
        return self.rng.choice(cands)

    def _on_stairs_down(self):
        return self.world.level().stairs_down == (self.world.px, self.world.py)

    # -- transactions -----------------------------------------------------
    def _menu_pick(self, want):
        """Menu policy: open the full menu, take the first wanted item."""
        d = self.dialogue

        def policy(kind, detail):
            if kind == "menu":
                lines, _, _, _ = d.session.terminal.snapshot()
                for letter, desc in menu_options(lines):
                    if want(desc):
                        return letter        # choose-one menus apply at once
                if re.search(r"\(\d+ of \d+\)", detail):
                    return " "               # advance to the next page
                return "\x1b"                # nothing wanted: leave the menu
            return None
        return policy

    def _eat_action(self):
        def open_menu(kind, detail):
            if kind == "choice" and "want to eat" in detail:
                return "?"
            return None
        return Action("tx", "e", "hungry",
                      policy=_chain(open_menu, self._menu_pick(is_food)))

    def _pickup_action(self):
        return Action("tx", ",", "objects-here",
                      policy=self._menu_pick(lambda d: is_food(d)
                                             or is_armor(d)))

    # -- priority chain ---------------------------------------------------
    def choose(self):
        st = self.world.status
        hostiles = self.hostiles()
        blocked = self.blocked_cells()
        lvl = self.world.level()

        # 1. survival: starving, or critical HP with hostiles adjacent
        if st.hunger in ("weak", "fainting"):
            return self._eat_action()
        if st.hp < max(1, st.maxhp // 3) and hostiles:
            step = self._flee_adjacent(hostiles)
            if step:
                return Action("move", self._adjacent_key(step),
                              "flee-critical")
            return self._attack_action(hostiles[0], "cornered")

        # 2. fight adjacent hostiles
        if hostiles:
            return self._attack_action(hostiles[0], "hostile-adjacent")

        # 3. pray when hurt and safe
        if (st.hp < max(2, st.maxhp // 2) and st.turn > 200
                and st.turn - self.last_pray_turn > 400):
            return Action("pray", "#pray\n", "low-hp-safe",
                          on_done=self._mark_pray)

        # 4. pickup underfoot objects
        if self.glyph_at(self.world.px, self.world.py) == "m":
            return self._pickup_action()

        # 5. explore / open doors
        targets = lvl.explore_targets((self.world.px, self.world.py), blocked)
        if targets:
            dist, cell, frontier = targets[0]
            if dist == 0:
                mv = self._fidget()
                if mv:
                    return Action("move", self._adjacent_key(mv), "explore")
                return Action("wait", ".", "explore-stuck")
            step = self._path_first(cell)
            if step:
                return Action("move", self._adjacent_key(step), "explore")
        doors = lvl.door_targets((self.world.px, self.world.py), blocked)
        if doors:
            dist, cell, door = doors[0]
            if dist == 0:
                return Action("open", "o" + self._adjacent_key(door),
                              "open-door")
            step = self._path_first(cell)
            if step:
                return Action("move", self._adjacent_key(step), "to-door")

        # 6. descend when the level is clear and we are healthy
        if (self._on_stairs_down() and st.hp * 2 >= st.maxhp
                and st.hunger not in ("weak", "fainting")):
            return Action("descend", ">", "level-clear")

        if lvl.stairs_down:
            step = self._path_first(lvl.stairs_down)
            if step:
                return Action("move", self._adjacent_key(step), "to-stairs")

        # 7. fidget / wait
        mv = self._fidget()
        if mv:
            return Action("move", self._adjacent_key(mv), "fidget")
        return Action("wait", ".", "idle")

    def _attack_action(self, monster, reason):
        dx = max(-1, min(1, monster.pos[0] - self.world.px))
        dy = max(-1, min(1, monster.pos[1] - self.world.py))
        return Action("attack", DIR_KEYS.get((dx, dy), "."), reason)

    def _mark_pray(self):
        self.last_pray_turn = self.world.status.turn
