"""Persistent, observation-only dungeon state and path finding."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
from nle import nethack


Point = tuple[int, int]  # (y, x)
LevelKey = tuple[int, int]  # (dungeon number, dungeon level)

CARDINALS: tuple[Point, ...] = ((-1, 0), (0, 1), (1, 0), (0, -1))
DIAGONALS: tuple[Point, ...] = ((-1, 1), (1, 1), (1, -1), (-1, -1))
DIRECTIONS: tuple[Point, ...] = CARDINALS + DIAGONALS

# NetHack 3.6.7 ``enum screen_symbols`` from include/rm.h.
STONE = 0
WALL_MIN, WALL_MAX = 1, 11
DOORWAY, OPEN_DOOR_V, OPEN_DOOR_H = 12, 13, 14
CLOSED_DOOR_V, CLOSED_DOOR_H = 15, 16
ROOM, DARKROOM, CORRIDOR, LITCORRIDOR = 19, 20, 21, 22
UPSTAIR, DOWNSTAIR = 23, 24
ALTAR, FOUNTAIN = 27, 31
POOL, ICE, LAVA = 32, 33, 34
OPEN_DRAWBRIDGE_V, OPEN_DRAWBRIDGE_H = 35, 36
TRAP_MIN = 42

BASE_PASSABLE = frozenset(
    [DOORWAY, OPEN_DOOR_V, OPEN_DOOR_H]
    + list(range(ROOM, FOUNTAIN + 1))
    + [ICE, OPEN_DRAWBRIDGE_V, OPEN_DRAWBRIDGE_H]
)


def add(point: Point, delta: Point) -> Point:
    return point[0] + delta[0], point[1] + delta[1]


def inside(point: Point, shape: tuple[int, int]) -> bool:
    return 0 <= point[0] < shape[0] and 0 <= point[1] < shape[1]


def neighbors(point: Point, diagonals: bool = True) -> Iterable[Point]:
    for delta in DIRECTIONS if diagonals else CARDINALS:
        yield add(point, delta)


@dataclass
class LevelState:
    key: LevelKey
    shape: tuple[int, int]
    terrain: np.ndarray = field(init=False)
    visits: np.ndarray = field(init=False)
    searches: np.ndarray = field(init=False)
    stairs_up: set[Point] = field(default_factory=set)
    stairs_down: set[Point] = field(default_factory=set)
    fountains: set[Point] = field(default_factory=set)
    traps: set[Point] = field(default_factory=set)
    trap_types: dict[Point, int] = field(default_factory=dict)
    boulders: set[Point] = field(default_factory=set)
    objects: set[Point] = field(default_factory=set)
    inspected_objects: set[Point] = field(default_factory=set)
    failed_edges: set[tuple[Point, Point]] = field(default_factory=set)
    probe_attempts: set[tuple[Point, Point]] = field(default_factory=set)
    door_failures: dict[Point, int] = field(default_factory=dict)
    dig_attempts: dict[tuple[Point, Point], int] = field(default_factory=dict)
    dig_successes: int = 0
    down_outcomes: dict[Point, LevelKey] = field(default_factory=dict)
    up_outcomes: dict[Point, LevelKey] = field(default_factory=dict)
    unknown_attempts: int = 0
    search_total: int = 0
    escalation: int = 0
    exhausted: bool = False

    def __post_init__(self) -> None:
        self.terrain = np.full(self.shape, -1, dtype=np.int16)
        self.visits = np.zeros(self.shape, dtype=np.int16)
        self.searches = np.zeros(self.shape, dtype=np.int16)

    def update(self, obs: dict[str, np.ndarray], player: Point) -> None:
        glyphs = obs["glyphs"]
        cmap_mask = nethack.glyph_is_cmap(glyphs)
        if np.any(cmap_mask):
            self.terrain[cmap_mask] = nethack.glyph_to_cmap(glyphs[cmap_mask])

        # Objects and creatures obscure the underlying terrain.  If this is
        # their first observed frame, ROOM is a conservative passable memory;
        # subsequent frames retain the actual terrain revealed before/after.
        overlay = (
            nethack.glyph_is_monster(glyphs)
            | nethack.glyph_is_pet(glyphs)
            | nethack.glyph_is_object(glyphs)
            | nethack.glyph_is_trap(glyphs)
            | nethack.glyph_is_invisible(glyphs)
        )
        first_overlay = overlay & (self.terrain < 0)
        self.terrain[first_overlay] = ROOM
        self.terrain[player] = max(int(self.terrain[player]), ROOM)
        self.visits[player] = min(32767, int(self.visits[player]) + 1)

        cmap = np.full(self.shape, -1, dtype=np.int16)
        cmap[cmap_mask] = nethack.glyph_to_cmap(glyphs[cmap_mask])
        self.stairs_up.update(map(tuple, np.argwhere(cmap == UPSTAIR)))
        self.stairs_down.update(map(tuple, np.argwhere(cmap == DOWNSTAIR)))
        self.fountains.update(map(tuple, np.argwhere(cmap == FOUNTAIN)))
        for y, x in np.argwhere(nethack.glyph_is_trap(glyphs)):
            point = (int(y), int(x))
            self.traps.add(point)
            self.trap_types[point] = int(
                nethack.glyph_to_cmap(int(glyphs[point]))
            )

        boulders: set[Point] = set()
        object_points = set(map(tuple, np.argwhere(nethack.glyph_is_object(glyphs))))
        self.objects.update(object_points)
        for y, x in object_points:
            glyph = int(glyphs[y, x])
            try:
                obj = nethack.objclass(int(nethack.glyph_to_obj(glyph)))
                if nethack.OBJ_NAME(obj) == "boulder":
                    boulders.add((int(y), int(x)))
            except (IndexError, RuntimeError, TypeError):
                continue
        self.boulders = boulders

    def is_closed_door(self, point: Point) -> bool:
        return int(self.terrain[point]) in (CLOSED_DOOR_V, CLOSED_DOOR_H)

    def is_wallish(self, point: Point) -> bool:
        value = int(self.terrain[point])
        return value == STONE or WALL_MIN <= value <= WALL_MAX

    def passable_mask(
        self,
        blocked: set[Point] | None = None,
        avoid_traps: bool = True,
    ) -> np.ndarray:
        mask = np.isin(self.terrain, tuple(BASE_PASSABLE))
        if avoid_traps:
            for point in self.traps:
                mask[point] = False
        for point in self.boulders:
            mask[point] = False
        if blocked:
            for point in blocked:
                mask[point] = False
        return mask

    def distances(
        self,
        start: Point,
        blocked: set[Point] | None = None,
        avoid_traps: bool = True,
        allow: set[Point] | None = None,
    ) -> tuple[np.ndarray, dict[Point, Point]]:
        passable = self.passable_mask(blocked=blocked, avoid_traps=avoid_traps)
        if allow:
            for point in allow:
                passable[point] = True
        passable[start] = True
        dist = np.full(self.shape, -1, dtype=np.int32)
        parent: dict[Point, Point] = {}
        dist[start] = 0
        queue: deque[Point] = deque([start])
        while queue:
            cur = queue.popleft()
            for nxt in neighbors(cur):
                if not inside(nxt, self.shape) or not passable[nxt] or dist[nxt] >= 0:
                    continue
                if (cur, nxt) in self.failed_edges:
                    continue
                dy, dx = nxt[0] - cur[0], nxt[1] - cur[1]
                if dy and dx:
                    # Avoid squeezing diagonally through two solid corners.
                    side1, side2 = (cur[0] + dy, cur[1]), (cur[0], cur[1] + dx)
                    if not passable[side1] and not passable[side2]:
                        continue
                    # NetHack forbids diagonal movement into or out of an
                    # intact doorway even when the adjacent floor looks free.
                    if int(self.terrain[cur]) in (12, 13, 14) or int(
                        self.terrain[nxt]
                    ) in (12, 13, 14):
                        continue
                dist[nxt] = dist[cur] + 1
                parent[nxt] = cur
                queue.append(nxt)
        return dist, parent

    def path(
        self,
        start: Point,
        targets: Iterable[Point],
        blocked: set[Point] | None = None,
        allow_targets: bool = False,
    ) -> list[Point] | None:
        targets = set(targets)
        if not targets:
            return None
        dist, parent = self.distances(
            start,
            blocked,
            avoid_traps=True,
            allow=targets if allow_targets else None,
        )
        reachable = [point for point in targets if dist[point] >= 0]
        if not reachable:
            return None
        target = min(reachable, key=lambda point: (dist[point], self.visits[point]))
        path = [target]
        while path[-1] != start:
            path.append(parent[path[-1]])
        path.reverse()
        return path
