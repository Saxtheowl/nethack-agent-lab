"""Persistent, conservative knowledge extracted from observed screens."""
from dataclasses import dataclass, replace
import re


@dataclass(frozen=True)
class World:
    screen: tuple[str, ...] = ()
    turn: int = 0
    game_turn: int | None = None
    level: int | None = None
    hp: int | None = None
    max_hp: int | None = None
    last_message: str = ""
    food_unavailable: bool = False
    known_stairs: tuple[tuple[int, int, str], ...] = ()
    uncertain: bool = True

    def observe(self, screen: tuple[str, ...], recent: str = "") -> "World":
        text = "\n".join(screen) + "\n" + recent
        hp, max_hp = self.hp, self.max_hp
        match = re.search(r"HP:(\d+)\((\d+)\)", text)
        if match:
            hp, max_hp = int(match.group(1)), int(match.group(2))
        level = self.level
        game_turn = self.game_turn
        turn_match = re.search(r"\bT:(\d+)", text)
        if turn_match: game_turn = int(turn_match.group(1))
        level_match = re.search(r"(?:Dlvl|dungeon level)[: ]+(\d+)", text, re.I)
        if level_match: level = int(level_match.group(1))
        stairs = {(x, y, glyph) for y, line in enumerate(screen) for x, glyph in enumerate(line) if glyph in "<>"}
        remembered = set(self.known_stairs) | stairs
        player = next(((x, y) for y in range(len(screen) - 1, -1, -1)
                       for x in range(len(screen[y]) - 1, -1, -1)
                       if screen[y][x] == "@"), None)
        return replace(self, screen=screen, turn=self.turn + 1, game_turn=game_turn, hp=hp, max_hp=max_hp, level=level,
                       food_unavailable=self.food_unavailable or "you don't have anything to eat" in text.lower(),
                       known_stairs=tuple(sorted(remembered)),
                       last_message=recent[-500:] or (screen[-2].strip() if len(screen) >= 2 else ""),
                       uncertain=False)

    def invalidate(self, reason: str) -> "World":
        return replace(self, uncertain=True, last_message=f"invalidated:{reason}")

    def food_search_started(self) -> "World":
        return replace(self, food_unavailable=False)

    @property
    def player_row(self) -> int | None:
        for y in range(len(self.screen) - 1, -1, -1):
            if "@" in self.screen[y]: return y
        return None

    def player_col(self) -> int | None:
        for row in reversed(self.screen):
            if "@" in row: return row.rindex("@")
        return None

    def adjacent_monster_key(self) -> bytes | None:
        """Return a movement/attack key only for a visible adjacent monster."""
        row, col = self.player_row, self.player_col()
        if row is None or col is None: return None
        directions = ((-1, -1, "y"), (0, -1, "k"), (1, -1, "u"),
                      (-1, 0, "h"), (1, 0, "l"), (-1, 1, "b"),
                      (0, 1, "j"), (1, 1, "n"))
        for dx, dy, key in directions:
            x, y = col + dx, row + dy
            if 0 <= y < len(self.screen) and 0 <= x < len(self.screen[y]):
                glyph = self.screen[y][x]
                # The run configuration disables pets, so alphabetic map
                # glyphs are hostile candidates rather than companions.
                # NetHack uses ':' for lizards/newts and ';' for eels; these
                # are monsters too even though they are not alphabetic.
                if (glyph.isalpha() or glyph in ":;&") and glyph not in "@":
                    return key.encode()
        return None

    def stair_key(self) -> bytes | None:
        row, col = self.player_row, self.player_col()
        if row is None or col is None: return None
        targets = []
        for y, line in enumerate(self.screen):
            for x, glyph in enumerate(line):
                if glyph == ">" and (x, y) != (col, row):
                    targets.append((abs(x-col) + abs(y-row), x, y))
        if not targets: return None
        _, target_x, target_y = min(targets)
        queue = [(col, row)]
        first = {(col, row): None}
        directions = ((-1,-1,b"y"),(0,-1,b"k"),(1,-1,b"u"),(-1,0,b"h"),(1,0,b"l"),(-1,1,b"b"),(0,1,b"j"),(1,1,b"n"))
        for x, y in queue:
            if (x, y) == (target_x, target_y): break
            for dx, dy, key in directions:
                nx, ny = x + dx, y + dy
                if (nx, ny) in first or not (0 <= ny < len(self.screen) and 0 <= nx < len(self.screen[ny])): continue
                tile = self.screen[ny][nx]
                if tile not in ".>#@%#+-|" and not tile.isalpha(): continue
                first[(nx, ny)] = (x, y, key); queue.append((nx, ny))
        if (target_x, target_y) not in first: return None
        cursor = (target_x, target_y)
        while first[cursor] and first[cursor][0:2] != (col, row):
            cursor = first[cursor][0:2]
        return first[cursor][2] if first[cursor] else None

    def stair_action(self) -> bytes | None:
        position = (self.player_col(), self.player_row)
        for x, y, glyph in self.known_stairs:
            if position == (x, y) and glyph == ">":
                return glyph.encode()
        return None
