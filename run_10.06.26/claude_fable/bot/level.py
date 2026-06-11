"""Level memory, glyph classification and pathfinding."""
from collections import deque

W, H = 80, 21  # map dimensions (tty rows 1..21)

DIRS = {
    (0, -1): "k", (0, 1): "j", (-1, 0): "h", (1, 0): "l",
    (-1, -1): "y", (1, -1): "u", (-1, 1): "b", (1, 1): "n",
}

MONSTER_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ@&;:'~")
# note: '`' is ROCK class in 3.7 (boulder = pushable; statue = walkable);
# we keep it walkable and let stuck-boulder messages ban dead edges
ITEM_CHARS = set("$\"'()[]%?/=!*`")
WALL_CHARS = set("|-")
# passive/dangerous-to-melee monsters: (char, fg) ; fg None = any color
MELEE_BLACKLIST = {
    ("e", None),     # floating eye (paralysis) / spheres (explode): never melee
    ("F", None),     # fungi/lichen: stick/passive
    ("j", None),     # jellies: passive damage
    ("b", None),     # blobs (acid)
    ("P", None),     # puddings: weapon corrosion
}


def melee_ok(char, fg):
    for c, f in MELEE_BLACKLIST:
        if char == c and (f is None or fg == f):
            return False
    return True


class Tile:
    __slots__ = ("char", "fg", "bold", "seen", "searched", "trap", "peaceful_until",
                 "door_locked", "kick_count", "wait_count", "phantom", "hard_ban",
                 "denied_until", "statue")

    def __init__(self):
        self.char = " "
        self.fg = "default"
        self.bold = False
        self.seen = False
        self.searched = 0
        self.trap = False
        self.peaceful_until = 0   # turn until which a peaceful blocks this tile
        self.door_locked = False
        self.kick_count = 0
        self.wait_count = 0       # times we waited for a blocker here
        self.phantom = 0          # no-op interactions with this tile
        self.hard_ban = False     # never path here in any mode (shop doors...)
        self.denied_until = 0     # "Really attack the peaceful X?" answered no
        self.statue = False       # 3.7 statues display as monster glyphs


class Level:
    def __init__(self, key):
        self.key = key            # (branch, dlvl)
        self.tiles = [[Tile() for _ in range(W)] for _ in range(H)]
        self.stairs_down = set()  # {(x,y)}
        self.stairs_up = set()
        self.tried_down = set()   # down stairs already known to lead to main branch
        self.tried_up = set()     # up stairs that lead somewhere useless (sokoban)
        self.doors_seen = set()
        self.visited = set()      # tiles the hero has stood on
        self.blocked_edges = {}   # {(from,to): [count, turn_of_last_fail]}
        self.total_searched = 0   # search turns spent on this level
        self.total_probed = 0     # probe steps spent on this level
        self.shop_doors = set()   # locked doors skipped because a shop is near
        self.desperate = False    # last-resort mode: kick suspected shop doors
        self.no_progress = 0

    def tile(self, x, y):
        return self.tiles[y][x]

    def ban_edge(self, a, b, turn, amount=1):
        c, _ = self.blocked_edges.get((a, b), (0, 0))
        self.blocked_edges[(a, b)] = (c + amount, turn)

    def edge_blocked(self, a, b, turn):
        c, t = self.blocked_edges.get((a, b), (0, 0))
        if c < 3:
            return False
        if turn - t > 400:  # transient causes (monsters) move on: retry old bans
            del self.blocked_edges[(a, b)]
            return False
        return True

    def update_from_snap(self, snap, hero):
        """Merge the visible screen into level memory."""
        hx, hy = hero
        # overlay guard: never ingest a screen with popup/menu artifacts
        joined = "\n".join(snap.lines)
        if "--More--" in joined or "(end)" in joined or "(1 of " in joined:
            return
        for y in range(H):
            for x in range(W):
                ch, fg, bold = snap.map_char(x, y)
                if ch == " ":
                    continue
                t = self.tiles[y][x]
                # a monster-ban expires once the monster glyph leaves the tile
                # (door bans on '+' must persist)
                if (t.peaceful_until and t.char in MONSTER_CHARS
                        and ch not in MONSTER_CHARS and ch != "+"):
                    t.peaceful_until = 0
                    t.wait_count = 0
                t.char, t.fg, t.bold = ch, fg, bold
                t.seen = True
                if ch == ">":
                    self.stairs_down.add((x, y))
                elif ch == "<":
                    self.stairs_up.add((x, y))
                elif ch == "^":
                    t.trap = True
                if self._is_door(ch, fg, x, y):
                    self.doors_seen.add((x, y))

    def _is_door(self, ch, fg, x, y):
        if fg not in ("brown", "yellow"):
            return False
        if ch == "+":
            return True
        return False

    # ---------- terrain queries ----------

    def is_monster(self, x, y, hero):
        t = self.tiles[y][x]
        if (x, y) == hero:
            return False
        if t.char in MONSTER_CHARS:
            # white/gray '@' could be hero only at hero pos; others are monsters
            return True
        return False

    def walkable(self, x, y, hero, turn=0, ignore_monsters=False):
        t = self.tiles[y][x]
        ch = t.char
        if (x, y) == hero:
            return True
        if t.phantom >= 2 or t.hard_ban:
            return False  # corrupted memory cell / forbidden door: wall
        if t.statue:
            return True   # statue: walkable floor despite the monster glyph
        if not t.seen:
            return False
        if t.trap and not ignore_monsters:  # fallback pathing may cross known traps
            return False
        if t.peaceful_until > turn and not ignore_monsters:
            return False
        if not ignore_monsters and ch in MONSTER_CHARS:
            return False
        if ch in ".<>_{":
            return True
        if ch == "#" and t.fg != "green":  # corridor (green # = tree)
            return True
        if ch == "+" and t.fg in ("brown", "yellow"):
            return True   # closed door: path through it, brain opens it
        if ch in "|-" and t.fg in ("brown", "yellow"):
            return True   # open door
        if ch in ITEM_CHARS:
            return True   # item lying on floor
        if ch in MONSTER_CHARS and ignore_monsters:
            return True
        return False

    def is_doorish(self, x, y):
        t = self.tiles[y][x]
        if t.char == "+" and t.fg in ("brown", "yellow"):
            return True
        if t.char in "|-" and t.fg in ("brown", "yellow"):
            return True
        # doorway heuristic: floor tile embedded in a wall line
        if t.char == ".":
            lr = (self.tiles[y][x - 1].char in WALL_CHARS and self.tiles[y][x + 1].char in WALL_CHARS) if 0 < x < W - 1 else False
            ud = (self.tiles[y - 1][x].char in WALL_CHARS and self.tiles[y + 1][x].char in WALL_CHARS) if 0 < y < H - 1 else False
            return lr or ud
        return False

    def neighbors(self, x, y, hero, turn=0, ignore_monsters=False):
        out = []
        for (dx, dy), key in DIRS.items():
            nx, ny = x + dx, y + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            if not self.walkable(nx, ny, hero, turn, ignore_monsters):
                continue
            diag = dx != 0 and dy != 0
            if diag and (self.is_doorish(nx, ny) or self.is_doorish(x, y)):
                continue
            if self.edge_blocked((x, y), (nx, ny), turn):
                continue
            out.append((nx, ny))
        return out

    # ---------- search ----------

    def bfs(self, start, goal_pred, hero, turn=0, ignore_monsters=False):
        """BFS from start; returns path (list of coords, excluding start) to nearest
        tile satisfying goal_pred, or None."""
        prev = {start: None}
        q = deque([start])
        while q:
            cur = q.popleft()
            if cur != start and goal_pred(*cur):
                path = []
                while cur != start:
                    path.append(cur)
                    cur = prev[cur]
                path.reverse()
                return path
            for nxt in self.neighbors(*cur, hero, turn, ignore_monsters):
                if nxt not in prev:
                    prev[nxt] = cur
                    q.append(nxt)
        return None

    def frontier_path(self, hero, turn=0, ignore_monsters=False):
        """Path to the nearest seen, walkable tile adjacent to unseen space."""
        def is_frontier(x, y):
            t = self.tiles[y][x]
            if not t.seen or (x, y) in self.visited:
                return False
            if not self.walkable(x, y, hero, turn, ignore_monsters):
                return False
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and not self.tiles[ny][nx].seen:
                        return True
            return False
        return self.bfs(hero, is_frontier, hero, turn, ignore_monsters)

    def probe_targets(self, hero, turn=0):
        """Walkable tiles adjacent to unseen space with an unbanned edge into it.
        Used to poke into dark-room pockets the visited-frontier rule skips."""
        out = {}
        for y in range(H):
            for x in range(W):
                ch = self.tiles[y][x].char
                if ch == "#":
                    # corridor: only probe from dead-end tips
                    nbs = sum(1 for (dx, dy) in DIRS
                              if 0 <= x + dx < W and 0 <= y + dy < H
                              and self.walkable(x + dx, y + dy, hero, turn,
                                                ignore_monsters=True))
                    if nbs > 1:
                        continue
                elif ch != ".":
                    continue  # rooms: probe from floor (dark-room pockets)
                if not self.walkable(x, y, hero, turn):
                    continue
                for (dx, dy) in DIRS:
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < W and 0 <= ny < H):
                        continue
                    if self.tiles[ny][nx].seen:
                        continue
                    if dx != 0 and dy != 0:
                        continue  # probe orthogonally only (doorway-safe)
                    if self.edge_blocked((x, y), (nx, ny), turn):
                        continue
                    out.setdefault((x, y), (dx, dy))
                    break
        return out

    def explore_unknown_path(self, hero, turn=0):
        """BFS where unseen tiles are traversable; returns a path whose final
        steps walk INTO the unknown. Edge bans (with expiry) prune real rock."""
        prev = {hero: None}
        q = deque([hero])
        goal = None
        while q:
            cur = q.popleft()
            x, y = cur
            if not self.tiles[y][x].seen and cur != hero:
                goal = cur
                break
            for (dx, dy) in DIRS:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < W and 0 <= ny < H):
                    continue
                if (nx, ny) in prev:
                    continue
                t = self.tiles[ny][nx]
                if t.seen:
                    if not self.walkable(nx, ny, hero, turn):
                        continue
                    diag = dx != 0 and dy != 0
                    if diag and (self.is_doorish(nx, ny) or self.is_doorish(x, y)):
                        continue
                else:
                    # unknown tile: only orthogonal probing, and respect bans
                    if dx != 0 and dy != 0:
                        continue
                if self.edge_blocked((x, y), (nx, ny), turn):
                    continue
                prev[(nx, ny)] = cur
                q.append((nx, ny))
        if goal is None:
            return None
        path = []
        cur = goal
        while cur != hero:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path

    def path_to(self, hero, targets, turn=0, adjacent=False, ignore_monsters=False):
        """Path to nearest of `targets` (set of coords). adjacent=True stops next to it."""
        tset = set(targets)
        if adjacent:
            def pred(x, y):
                return any((x + dx, y + dy) in tset
                           for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0))
        else:
            def pred(x, y):
                return (x, y) in tset
        return self.bfs(hero, pred, hero, turn, ignore_monsters)

    def search_spots(self, hero, turn=0):
        """Tiles worth searching: along a wall (or dead end) with unseen space beyond."""
        spots = []
        for y in range(H):
            for x in range(W):
                t = self.tiles[y][x]
                if not t.seen or not self.walkable(x, y, hero, turn) or t.searched >= 30:
                    continue
                if t.char == "#":
                    # corridor dead-end: hidden door/passage candidate even if
                    # the far side is already-mapped territory
                    nbs = sum(1 for (dx, dy) in DIRS
                              if 0 <= x + dx < W and 0 <= y + dy < H
                              and self.walkable(x + dx, y + dy, hero, turn,
                                                ignore_monsters=True))
                    if nbs <= 1:
                        spots.append((x, y))
                        continue
                for (dx, dy) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                    nx, ny = x + dx, y + dy
                    fx, fy = x + 2 * dx, y + 2 * dy
                    if not (0 <= nx < W and 0 <= ny < H):
                        continue
                    nch = self.tiles[ny][nx].char
                    if nch not in WALL_CHARS and nch != " ":
                        continue
                    # beyond the wall must be unseen (or off our explored area)
                    if 0 <= fx < W and 0 <= fy < H and self.tiles[fy][fx].seen:
                        continue
                    spots.append((x, y))
                    break
        return spots
