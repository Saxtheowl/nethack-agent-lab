"""Rule-based Valkyrie policy for the early NetHack game."""

from __future__ import annotations

import re
from collections import Counter, deque
from dataclasses import dataclass
from heapq import heappop, heappush

import numpy as np
from nle import nethack

from .state import (
    ALTAR,
    BASE_PASSABLE,
    CARDINALS,
    CLOSED_DOOR_H,
    CLOSED_DOOR_V,
    CORRIDOR,
    DARKROOM,
    DIRECTIONS,
    DOORWAY,
    FOUNTAIN,
    LevelKey,
    LevelState,
    Point,
    ROOM,
    OPEN_DOOR_H,
    OPEN_DOOR_V,
    STONE,
    WALL_MAX,
    WALL_MIN,
    add,
    inside,
    neighbors,
)


DIRECTION_ACTION = {
    (-1, 0): nethack.CompassDirection.N,
    (-1, 1): nethack.CompassDirection.NE,
    (0, 1): nethack.CompassDirection.E,
    (1, 1): nethack.CompassDirection.SE,
    (1, 0): nethack.CompassDirection.S,
    (1, -1): nethack.CompassDirection.SW,
    (0, -1): nethack.CompassDirection.W,
    (-1, -1): nethack.CompassDirection.NW,
}

RAW_TO_INDEX = {int(action): index for index, action in enumerate(nethack.ACTIONS)}

PEACEFUL_DWARF_NAMES = frozenset(
    {
        "gnome",
        "gnome lord",
        "gnomish wizard",
        "gnome king",
        "hobbit",
        "dwarf",
        "dwarf lord",
        "dwarf king",
        "watchman",
        "watch captain",
        "guard",
        "pony",
        "horse",
        "warhorse",
        "kitten",
        "housecat",
        "large cat",
        "little dog",
        "dog",
        "large dog",
        "shopkeeper",
        "aligned priest",
        "high priest",
    }
)

SAFE_CORPSES = frozenset(
    {
        "lichen",
        "newt",
        "gecko",
        "jackal",
        "fox",
        "sewer rat",
        "giant rat",
        "grid bug",
        "bat",
        "cave spider",
        "iguana",
        "floating eye",
    }
)

PASSIVE_DANGER_NAMES = frozenset(
    {
        "floating eye",
        "gas spore",
        "blue jelly",
        "brown mold",
        "yellow mold",
        "green mold",
        "red mold",
    }
)

WALL_FAILURE = re.compile(
    r"(solid (?:rock|stone)|wall|cannot move|can't move|boulder)", re.I
)
ATTACKING_PLAYER = re.compile(
    r"(?:The|A|An) ([A-Za-z][A-Za-z -]*?) "
    r"(?:hits|misses|bites|kicks|stings|claws|butts|touches|engulfs)(?:!|\.)"
)
PLAYER_COMBAT_RESULT = re.compile(
    r"\bYou (?:hit|miss|kill|destroy|attack|smite|bite|kick|stagger|begin bashing)\b",
    re.I,
)


def decode(raw: np.ndarray) -> str:
    return bytes(raw).split(b"\0", 1)[0].decode("utf-8", "replace")


@dataclass
class DescentContext:
    source_key: LevelKey
    source_point: Point
    return_if_main: bool


class MinetownPolicy:
    """Stateful policy using only the public Challenge observation dictionary."""

    def __init__(self) -> None:
        self.levels: dict[LevelKey, LevelState] = {}
        self.current_key: LevelKey | None = None
        self.previous_key: LevelKey | None = None
        self.position: Point | None = None
        self.previous_position: Point | None = None
        self.last_message = ""
        self.messages: deque[str] = deque(maxlen=80)
        self.last_raw_action: int | None = None
        self.last_move: tuple[LevelKey, Point, Point, bool] | None = None
        self.intent: dict | None = None
        self.descent: DescentContext | None = None
        self.ascent_source: tuple[LevelKey, Point] | None = None
        self.return_after_descent = False
        self.mines_dnum: int | None = None
        self.branch_backtracking = False
        self.attempted_down: set[tuple[LevelKey, Point]] = set()
        self.last_prayer_turn = -10_000
        self.excalibur_attempts: Counter[tuple[LevelKey, Point]] = Counter()
        self.excalibur_done = False
        self.hostile_names: set[str] = set()
        self.tried_wands: dict[tuple[LevelKey, Point], set[str]] = {}
        self.incapacitated = False
        self.mapped_levels: set[LevelKey] = set()
        self.forced_peaceful_names: set[str] = set()
        self.patrol_targets: dict[LevelKey, Point] = {}
        self.patrol_actions: Counter[LevelKey] = Counter()
        self.prebuff_healing_used = 0
        self.lycanthropy_suspected = False
        self.latest_obs: dict[str, np.ndarray] | None = None
        self.steps = 0
        self.normal_turns = 0
        self.action_counts: Counter[str] = Counter()
        self.failure_hint = "unknown"

    @staticmethod
    def _index(raw: int) -> int:
        try:
            return RAW_TO_INDEX[int(raw)]
        except KeyError as exc:
            raise RuntimeError(f"Raw key {raw!r} is not in NLE's action space") from exc

    def _emit(self, raw: int, label: str) -> int:
        self.last_raw_action = int(raw)
        self.action_counts[label] += 1
        return self._index(int(raw))

    def _observe(self, obs: dict[str, np.ndarray]) -> LevelState:
        self.latest_obs = obs
        self.steps += 1
        bl = obs["blstats"]
        key = (int(bl[nethack.NLE_BL_DNUM]), int(bl[nethack.NLE_BL_DLEVEL]))
        point = (int(bl[nethack.NLE_BL_Y]), int(bl[nethack.NLE_BL_X]))
        message = decode(obs["message"]).strip()
        if message and message != self.last_message:
            self.messages.append(message)
        lowered_message = message.lower()
        if "feel feverish" in lowered_message:
            self.lycanthropy_suspected = True
        if "feel purified" in lowered_message or "affinity to" in lowered_message:
            self.lycanthropy_suspected = False
        if any(
            phrase in lowered_message
            for phrase in ("frozen by", "paralyzed", "faint from lack of food")
        ):
            self.incapacitated = True
        if any(
            phrase in lowered_message
            for phrase in ("can move again", "regain consciousness")
        ):
            self.incapacitated = False
        for match in ATTACKING_PLAYER.finditer(message):
            name = match.group(1).strip().lower()
            if name.startswith("invisible "):
                name = name.removeprefix("invisible ")
            self.hostile_names.add(name)

        old_key, old_point = self.current_key, self.position
        self.previous_key, self.previous_position = old_key, old_point
        self.current_key, self.position = key, point
        self.last_message = message
        level = self.levels.setdefault(key, LevelState(key, obs["glyphs"].shape))
        level.update(obs, point)
        if any(
            phrase in message.lower()
            for phrase in (
                "succeed in cutting away",
                "make an opening in",
                "finish chopping",
            )
        ):
            level.dig_successes += 1
            level.unknown_attempts = 0
            level.exhausted = False

        if "staircase down" in message.lower():
            level.stairs_down.add(point)
        if "staircase up" in message.lower():
            level.stairs_up.add(point)

        if old_key is not None and old_point is not None and key != old_key:
            old_level = self.levels[old_key]
            pending_descent = (
                self.descent is not None and self.descent.source_key == old_key
            )
            pending_ascent = (
                self.ascent_source is not None and self.ascent_source[0] == old_key
            )
            if (
                self.last_raw_action == int(nethack.MiscDirection.DOWN)
                or pending_descent
            ):
                old_level.stairs_down.add(old_point)
                old_level.down_outcomes[old_point] = key
                level.stairs_up.add(point)
                level.up_outcomes[point] = old_key
                if key[0] != 0:
                    self.mines_dnum = key[0]
                    self.return_after_descent = False
                elif self.descent and self.descent.return_if_main:
                    self.return_after_descent = True
                if key[0] == 0 and key[1] >= 5 and self.mines_dnum is None:
                    self.branch_backtracking = True
                    for candidate in self.levels.values():
                        if candidate.key[0] == 0 and 2 <= candidate.key[1] <= 4:
                            candidate.escalation = max(candidate.escalation, 1)
                            candidate.exhausted = False
                self.descent = None
            elif (
                self.last_raw_action == int(nethack.MiscDirection.UP)
                or pending_ascent
            ):
                old_level.stairs_up.add(old_point)
                old_level.up_outcomes[old_point] = key
                level.stairs_down.add(point)
                level.down_outcomes[point] = old_key
                self.return_after_descent = False
                self.ascent_source = None

        if self.last_move is not None:
            move_key, start, target, was_unknown = self.last_move
            if key == move_key and point == start:
                immobilized = any(
                    phrase in message.lower()
                    for phrase in ("bear trap", "stuck in a web", "in a pit")
                )
                if (
                    WALL_FAILURE.search(message)
                    and not immobilized
                ):
                    self.levels[move_key].failed_edges.add((start, target))
                    if was_unknown:
                        self.levels[move_key].unknown_attempts += 1
            self.last_move = None

        # A command intent is complete once NetHack returns to ordinary mode.
        if not np.any(obs["misc"]) and self.intent is not None:
            self.intent = None

        return level

    def _prompt(self, obs: dict[str, np.ndarray]) -> int | None:
        misc = obs["misc"]
        if misc[2]:
            return self._emit(int(nethack.MiscAction.MORE), "more")

        message = self.last_message.lower()
        if misc[1]:
            # No current strategy uses free-form getlin input.
            self.intent = None
            return self._emit(int(nethack.Command.ESC), "escape_getlin")

        if not misc[0]:
            return None

        if "really attack" in message:
            match = re.search(r"really attack (?:the |a |an )?([^?]+?)\?", message)
            if match:
                name = match.group(1).strip().lower()
                self.forced_peaceful_names.add(name)
                self.hostile_names.discard(name)
            self.intent = None
            return self._emit(ord("n"), "decline_peaceful_attack")

        if self.intent:
            kind = self.intent.get("kind")
            if kind == "direction":
                raw = int(self.intent["raw"])
                self.intent = None
                return self._emit(raw, "direction_prompt")
            if kind == "eat":
                if "eat it?" in message or "eat one?" in message:
                    # Decline unknown floor food, then select the known ration.
                    return self._emit(ord("n"), "decline_floor_food")
                letter = self.intent.get("letter")
                self.intent = None
                return self._emit(ord(letter), "select_food")
            if kind == "eat_floor":
                self.intent = None
                return self._emit(ord("y"), "accept_safe_corpse")
            if kind == "pray":
                self.intent = None
                return self._emit(ord("y"), "confirm_prayer")
            if kind == "dip":
                stage = int(self.intent.get("stage", 0))
                if stage == 0:
                    self.intent["stage"] = 1
                    return self._emit(ord(self.intent["letter"]), "select_dip_item")
                self.intent = None
                return self._emit(ord("y"), "confirm_dip")
            if kind == "throw":
                stage = int(self.intent.get("stage", 0))
                if stage == 0:
                    self.intent["stage"] = 1
                    return self._emit(ord(self.intent["letter"]), "select_throw_item")
                raw = int(self.intent["raw"])
                self.intent = None
                return self._emit(raw, "throw_direction")
            if kind == "zap":
                stage = int(self.intent.get("stage", 0))
                if stage == 0:
                    self.intent["stage"] = 1
                    return self._emit(ord(self.intent["letter"]), "select_wand")
                raw = int(self.intent["raw"])
                self.intent = None
                return self._emit(raw, "zap_direction")
            if kind == "dig":
                stage = int(self.intent.get("stage", 0))
                if stage == 0:
                    self.intent["stage"] = 1
                    return self._emit(ord(self.intent["letter"]), "select_pickaxe")
                raw = int(self.intent["raw"])
                self.intent = None
                return self._emit(raw, "dig_direction")
            if kind == "quaff":
                letter = self.intent["letter"]
                self.intent = None
                return self._emit(ord(letter), "select_healing")
            if kind == "wield":
                letter = self.intent["letter"]
                self.intent = None
                return self._emit(ord(letter), "select_combat_weapon")
            if kind == "read_map":
                letter = self.intent["letter"]
                self.intent = None
                return self._emit(ord(letter), "select_magic_mapping")

        # Conservative defaults for unsolicited questions.
        if "attack" in message or "quit" in message:
            return self._emit(ord("n"), "decline_question")
        return self._emit(int(nethack.Command.ESC), "escape_question")

    def _inventory(self, obs: dict[str, np.ndarray]) -> dict[str, str]:
        inventory: dict[str, str] = {}
        for raw_letter, raw_description in zip(obs["inv_letters"], obs["inv_strs"]):
            if not np.any(raw_description):
                break
            inventory[chr(int(raw_letter))] = decode(raw_description)
        return inventory

    def _creatures(self, obs: dict[str, np.ndarray]) -> tuple[dict[Point, str], set[Point]]:
        glyphs = obs["glyphs"]
        creatures: dict[Point, str] = {}
        pets = set(map(tuple, np.argwhere(nethack.glyph_is_pet(glyphs))))
        for y, x in np.argwhere(nethack.glyph_is_monster(glyphs)):
            point = (int(y), int(x))
            if point == self.position:
                continue
            glyph = int(glyphs[point])
            try:
                name = nethack.permonst(int(nethack.glyph_to_mon(glyph))).mname
            except (IndexError, RuntimeError, TypeError):
                name = "unknown monster"
            creatures[point] = str(name)
        for y, x in np.argwhere(nethack.glyph_is_invisible(glyphs)):
            point = (int(y), int(x))
            if point != self.position:
                creatures.setdefault(point, "invisible monster")
        return creatures, pets

    def _move(self, level: LevelState, target: Point, label: str) -> int:
        assert self.position is not None and self.current_key is not None
        delta = (target[0] - self.position[0], target[1] - self.position[1])
        raw = int(DIRECTION_ACTION[delta])
        was_unknown = int(level.terrain[target]) in (-1, STONE)
        self.last_move = (self.current_key, self.position, target, was_unknown)
        return self._emit(raw, label)

    def _path_step(
        self,
        level: LevelState,
        targets: set[Point],
        blocked: set[Point],
        label: str,
    ) -> int | None:
        assert self.position is not None
        path = level.path(self.position, targets, blocked)
        if path is None:
            return None
        if len(path) == 1:
            return -1
        return self._move(level, path[1], label)

    def _adjacent_combat(
        self,
        obs: dict[str, np.ndarray],
        level: LevelState,
        creatures: dict[Point, str],
        pets: set[Point],
    ) -> int | None:
        assert self.position is not None
        hostiles: list[tuple[Point, str]] = []
        passive_dangers: list[tuple[Point, str]] = []
        for point, name in creatures.items():
            if point in pets or (
                name in PEACEFUL_DWARF_NAMES and name not in self.hostile_names
            ):
                continue
            if max(abs(point[0] - self.position[0]), abs(point[1] - self.position[1])) <= 1:
                if name in PASSIVE_DANGER_NAMES:
                    passive_dangers.append((point, name))
                else:
                    hostiles.append((point, name))
        if not hostiles and not passive_dangers:
            return None

        hp = int(obs["blstats"][nethack.NLE_BL_HP])
        hpmax = max(1, int(obs["blstats"][nethack.NLE_BL_HPMAX]))
        blocked = set(creatures) | pets
        if hostiles and hp * 100 < hpmax * 65:
            candidates = []
            passable = level.passable_mask(blocked=blocked, avoid_traps=True)
            for point in neighbors(self.position, diagonals=False):
                if not inside(point, level.shape) or not passable[point]:
                    continue
                separation = min(
                    max(abs(point[0] - enemy[0][0]), abs(point[1] - enemy[0][1]))
                    for enemy in hostiles
                )
                candidates.append((separation, -int(level.visits[point]), point))
            if candidates:
                point = max(candidates)[2]
                return self._move(level, point, "flee_low_hp")

        if not hostiles and passive_dangers:
            gas_spores = [entry for entry in passive_dangers if entry[1] == "gas spore"]
            if gas_spores:
                # Killing an adjacent gas spore with a thrown dagger still
                # catches us in the blast.  Step away (or wait if trapped)
                # until it is safe to engage from range.
                if self.action_counts["avoid_gas_spore"] >= 24 and hp >= 24:
                    target, name = gas_spores[0]
                    self.failure_hint = f"combat:{name}"
                    return self._move(level, target, "melee_passive_last_resort")
                blocked = set(creatures) | pets
                passable = level.passable_mask(blocked=blocked, avoid_traps=True)
                candidates = [
                    point
                    for point in neighbors(self.position)
                    if inside(point, level.shape) and passable[point]
                ]
                if candidates:
                    point = max(
                        candidates,
                        key=lambda candidate: min(
                            max(
                                abs(candidate[0] - enemy[0][0]),
                                abs(candidate[1] - enemy[0][1]),
                            )
                            for enemy in gas_spores
                        ),
                    )
                    return self._move(level, point, "avoid_gas_spore")
                if hp >= 24 and hp * 4 >= hpmax * 3:
                    target, name = gas_spores[0]
                    self.failure_hint = f"combat:{name}"
                    return self._move(level, target, "melee_passive_last_resort")
                return self._emit(int(nethack.MiscDirection.WAIT), "wait_gas_spore")
            inventory = self._inventory(obs)
            projectile = next(
                (
                    letter
                    for preferred in ("dagger", "rock", "dart", "arrow")
                    for letter, desc in inventory.items()
                    if preferred in desc and "Excalibur" not in desc
                ),
                None,
            )
            if projectile is not None:
                target, name = passive_dangers[0]
                delta = (
                    target[0] - self.position[0],
                    target[1] - self.position[1],
                )
                self.failure_hint = f"combat:{name}"
                self.intent = {
                    "kind": "throw",
                    "letter": projectile,
                    "raw": int(DIRECTION_ACTION[delta]),
                    "stage": 0,
                }
                return self._emit(int(nethack.Command.THROW), "throw_at_passive")
            target, name = passive_dangers[0]
            wand_key = (self.current_key, target)
            tried = self.tried_wands.setdefault(wand_key, set())
            wand = next(
                (
                    (letter, desc)
                    for letter, desc in inventory.items()
                    if "wand" in desc and desc not in tried
                ),
                None,
            )
            if wand is not None:
                letter, description = wand
                tried.add(description)
                delta = (
                    target[0] - self.position[0],
                    target[1] - self.position[1],
                )
                self.intent = {
                    "kind": "zap",
                    "letter": letter,
                    "raw": int(DIRECTION_ACTION[delta]),
                    "stage": 0,
                }
                return self._emit(int(nethack.Command.ZAP), "zap_at_passive")
            if (name != "gas spore" or hp >= 28) and hp * 4 >= hpmax * 3:
                # Last resort after ranged options are exhausted.  For a lone
                # floating eye this can paralyse us, but with no other visible
                # hostile and AC -5 it is preferable to permanent starvation.
                other_hostiles = [
                    other_name
                    for other_point, other_name in creatures.items()
                    if other_point not in pets
                    and other_name not in PEACEFUL_DWARF_NAMES
                    and other_name not in PASSIVE_DANGER_NAMES
                ]
                if not other_hostiles:
                    self.failure_hint = f"combat:{name}"
                    return self._move(level, target, "melee_passive_last_resort")
            # A sessile passive monster is safer as a temporary blocked tile
            # than as a melee target.  Navigation will seek another route.
            return None

        def difficulty(entry: tuple[Point, str]) -> int:
            point, _ = entry
            glyph = int(obs["glyphs"][point])
            try:
                return int(nethack.permonst(int(nethack.glyph_to_mon(glyph))).difficulty)
            except (IndexError, RuntimeError, TypeError):
                return 99

        target, name = min(hostiles, key=difficulty)
        self.failure_hint = f"combat:{name}"
        inventory = self._inventory(obs)
        sword = next(
            (
                letter
                for letter, description in inventory.items()
                if ("long sword" in description or "Excalibur" in description)
                and "weapon in hand" not in description
            ),
            None,
        )
        if sword is not None:
            # Applying the pick-axe makes it the current weapon.  Re-equip the
            # sword before a real fight instead of slowly bashing with a tool.
            self.intent = {"kind": "wield", "letter": sword}
            return self._emit(int(nethack.Command.WIELD), "wield_for_combat")
        return self._move(level, target, "melee")

    def _survival(self, obs: dict[str, np.ndarray], level: LevelState) -> int | None:
        bl = obs["blstats"]
        hunger = int(bl[nethack.NLE_BL_HUNGER])
        turn = int(bl[nethack.NLE_BL_TIME])
        inventory = self._inventory(obs)

        hp = int(bl[nethack.NLE_BL_HP])
        hpmax = max(1, int(bl[nethack.NLE_BL_HPMAX]))
        if self.prebuff_healing_used < 2 and hp == hpmax:
            extra_healing = next(
                (
                    letter
                    for letter, description in inventory.items()
                    if "blessed" in description
                    and "potion" in description
                    and "extra healing" in description
                ),
                None,
            )
            if extra_healing is not None:
                self.prebuff_healing_used += 1
                self.intent = {"kind": "quaff", "letter": extra_healing}
                return self._emit(int(nethack.Command.QUAFF), "prebuff_extra_healing")

        if hunger >= 2:
            for letter, description in inventory.items():
                if "food ration" in description:
                    self.intent = {"kind": "eat", "letter": letter}
                    return self._emit(int(nethack.Command.EAT), "eat_ration")

        if hunger >= 3 and turn >= 350 and turn - self.last_prayer_turn >= 450:
            self.last_prayer_turn = turn
            self.intent = {"kind": "pray"}
            return self._emit(int(nethack.Command.PRAY), "pray_for_hunger")

        if hp * 100 < hpmax * 65:
            return self._emit(int(nethack.MiscDirection.WAIT), "rest")
        return None

    def _emergency(self, obs: dict[str, np.ndarray]) -> int | None:
        if self.lycanthropy_suspected:
            holy_water = next(
                (
                    letter
                    for letter, description in self._inventory(obs).items()
                    if "potion" in description and "holy water" in description
                ),
                None,
            )
            if holy_water is not None:
                self.lycanthropy_suspected = False
                self.intent = {"kind": "quaff", "letter": holy_water}
                return self._emit(int(nethack.Command.QUAFF), "cure_lycanthropy")
        bl = obs["blstats"]
        hp = int(bl[nethack.NLE_BL_HP])
        hpmax = max(1, int(bl[nethack.NLE_BL_HPMAX]))
        if hp * 2 >= hpmax:
            return None
        inventory = self._inventory(obs)
        healing = next(
            (
                letter
                for letter, description in inventory.items()
                if "potion" in description
                and any(
                    name in description
                    for name in ("healing", "extra healing", "full healing")
                )
            ),
            None,
        )
        if healing is not None:
            self.intent = {"kind": "quaff", "letter": healing}
            return self._emit(int(nethack.Command.QUAFF), "quaff_healing")
        turn = int(bl[nethack.NLE_BL_TIME])
        if (
            hp * 2 <= hpmax
            and turn >= 300
            and turn - self.last_prayer_turn >= 500
        ):
            self.last_prayer_turn = turn
            self.intent = {"kind": "pray"}
            return self._emit(int(nethack.Command.PRAY), "pray_emergency")
        return None

    def _try_excalibur(self, obs: dict[str, np.ndarray], level: LevelState) -> int | None:
        assert self.position is not None and self.current_key is not None
        inventory = self._inventory(obs)
        if any("Excalibur" in description for description in inventory.values()):
            self.excalibur_done = True
            return None
        if self.excalibur_done or int(obs["blstats"][nethack.NLE_BL_XP]) < 5:
            return None
        if self.position not in level.fountains:
            return None
        key = (self.current_key, self.position)
        if self.excalibur_attempts[key] >= 8:
            return None
        hp = int(obs["blstats"][nethack.NLE_BL_HP])
        hpmax = max(1, int(obs["blstats"][nethack.NLE_BL_HPMAX]))
        if hp * 4 < hpmax * 3:
            return None
        for letter, description in inventory.items():
            if "long sword" in description and "Excalibur" not in description:
                self.excalibur_attempts[key] += 1
                self.intent = {"kind": "dip", "letter": letter, "stage": 0}
                return self._emit(int(nethack.Command.DIP), "dip_for_excalibur")
        return None

    def _map_level(self, obs: dict[str, np.ndarray]) -> int | None:
        assert self.current_key is not None
        if self.current_key in self.mapped_levels:
            return None
        inventory = self._inventory(obs)
        scroll = next(
            (
                letter
                for letter, description in inventory.items()
                if "magic mapping" in description
            ),
            None,
        )
        if scroll is None:
            return None
        self.mapped_levels.add(self.current_key)
        self.intent = {"kind": "read_map", "letter": scroll}
        return self._emit(int(nethack.Command.READ), "read_magic_mapping")

    def _door_or_frontier(
        self,
        level: LevelState,
        blocked: set[Point],
        *,
        unknown_budget: int,
    ) -> int | None:
        assert self.position is not None
        dist, _ = level.distances(self.position, blocked=blocked, avoid_traps=True)
        reachable = list(map(tuple, np.argwhere(dist >= 0)))

        candidates: list[tuple[float, Point, Point, str]] = []
        for point in reachable:
            d = int(dist[point])
            for delta in CARDINALS:
                nxt = add(point, delta)
                if not inside(nxt, level.shape):
                    continue
                value = int(level.terrain[nxt])
                if value in (CLOSED_DOOR_V, CLOSED_DOOR_H):
                    failures = level.door_failures.get(nxt, 0)
                    if failures < 6:
                        candidates.append((d + failures * 3 - 8, point, nxt, "door"))
                elif (
                    value in (-1, STONE)
                    and (
                        int(level.terrain[point]) in (
                            CORRIDOR,
                            DOORWAY,
                            OPEN_DOOR_V,
                            OPEN_DOOR_H,
                        )
                        or level.key[0] != 0
                    )
                    and (point, nxt) not in level.failed_edges
                    and level.unknown_attempts < unknown_budget
                ):
                    continuation = 0
                    opposite = (point[0] - delta[0], point[1] - delta[1])
                    if inside(opposite, level.shape) and int(level.terrain[opposite]) in (
                        ROOM,
                        DARKROOM,
                        CORRIDOR,
                    ):
                        continuation = -3
                    candidates.append(
                        (
                            d + int(level.visits[point]) * 0.2 + continuation,
                            point,
                            nxt,
                            "unknown",
                        )
                    )

        if not candidates:
            return None
        _, approach, target, kind = min(candidates, key=lambda row: row[0])
        if approach != self.position:
            action = self._path_step(level, {approach}, blocked, "explore_path")
            return None if action == -1 else action

        delta = (target[0] - self.position[0], target[1] - self.position[1])
        if kind == "door":
            failures = level.door_failures.get(target, 0)
            raw = int(nethack.Command.OPEN if failures == 0 else nethack.Command.KICK)
            level.door_failures[target] = failures + 1
            self.intent = {"kind": "direction", "raw": int(DIRECTION_ACTION[delta])}
            return self._emit(raw, "open_door" if failures == 0 else "kick_door")
        return self._move(level, target, "probe_unknown")

    def _search_hidden(
        self,
        level: LevelState,
        blocked: set[Point],
        *,
        budget: int,
        per_tile: int,
    ) -> int | None:
        assert self.position is not None
        if level.search_total >= budget:
            return None
        dist, _ = level.distances(self.position, blocked=blocked, avoid_traps=True)
        candidates: list[tuple[float, Point]] = []
        for y, x in map(tuple, np.argwhere(dist >= 0)):
            point = (int(y), int(x))
            wallish = 0
            known_degree = 0
            for nxt in neighbors(point, diagonals=False):
                if not inside(nxt, level.shape):
                    continue
                value = int(level.terrain[nxt])
                wallish += value in (-1, STONE) or WALL_MIN <= value <= WALL_MAX
                known_degree += value in (ROOM, DARKROOM, CORRIDOR)
            terrain = int(level.terrain[point])
            local_limit = (
                per_tile
                if terrain == CORRIDOR and known_degree <= 1
                else max(3, per_tile // 5)
            )
            if level.searches[point] >= local_limit:
                continue
            # Culs-de-sac remain highest priority, but ordinary room-edge
            # squares must stay eligible: many generated levels put their only
            # continuation behind an otherwise unremarkable wall segment.
            if wallish:
                priority = (
                    int(dist[point])
                    + int(level.searches[point]) * 7
                    + known_degree * 2
                    - wallish * 2
                    - (80 if terrain == CORRIDOR and known_degree <= 1 else 0)
                )
                candidates.append((priority, point))
        if not candidates:
            return None
        # Once we reach a promising wall, perform the whole local search burst
        # before selecting another room.  Re-selecting globally after every
        # single `s` caused costly cross-level oscillation.
        current_candidate = next(
            (point for _, point in candidates if point == self.position), None
        )
        target = current_candidate if current_candidate is not None else min(candidates)[1]
        if target != self.position:
            action = self._path_step(level, {target}, blocked, "search_path")
            return None if action == -1 else action
        level.searches[target] += 1
        level.search_total += 1
        return self._emit(int(nethack.Command.SEARCH), "search_hidden")

    def _inspect_objects(
        self,
        level: LevelState,
        blocked: set[Point],
    ) -> int | None:
        """Use `:` to reveal a staircase hidden beneath an object glyph."""

        assert self.position is not None
        candidates = level.objects - level.inspected_objects - level.boulders
        if not candidates:
            return None
        path = level.path(self.position, candidates, blocked)
        if path is None:
            return None
        target = path[-1]
        if len(path) > 1:
            return self._move(level, path[1], "inspect_object_path")
        level.inspected_objects.add(target)
        return self._emit(int(nethack.Command.LOOK), "inspect_under_object")

    def _patrol_unvisited(
        self,
        level: LevelState,
        blocked: set[Point],
    ) -> int | None:
        """Sweep mapped Mines terrain until the exact town evaluator fires."""

        assert self.position is not None
        dist, _ = level.distances(
            self.position, blocked=blocked, avoid_traps=True
        )
        if self.patrol_actions[level.key] < 200:
            target = self.patrol_targets.get(level.key)
            if target is not None and dist[target] >= 0 and level.visits[target] == 0:
                action = self._path_step(
                    level, {target}, blocked, "patrol_mapped_mines"
                )
                if action is not None and action != -1:
                    self.patrol_actions[level.key] += 1
                return None if action == -1 else action
            candidates = list(
                map(tuple, np.argwhere((dist >= 0) & (level.visits == 0)))
            )
            if not candidates:
                pass
            else:
                target = max(candidates, key=lambda point: int(dist[point]))
                self.patrol_targets[level.key] = target
                action = self._path_step(level, {target}, blocked, "patrol_mapped_mines")
                if action is not None and action != -1:
                    self.patrol_actions[level.key] += 1
                return None if action == -1 else action

        # Magic mapping can reveal a town component behind locked doors or
        # non-diggable walls.  If ordinary patrol cannot reach an unvisited
        # mapped floor, tunnel toward the nearest such component once instead
        # of cycling forever between Mines levels 3 and 4.
        inaccessible = [
            tuple(map(int, point))
            for point in np.argwhere(
                np.isin(level.terrain, tuple(BASE_PASSABLE))
                & (level.visits == 0)
                & (dist < 0)
            )
            if tuple(map(int, point)) not in blocked
            and tuple(map(int, point)) not in level.boulders
        ]
        if inaccessible:
            target = self.patrol_targets.get(level.key)
            if target not in inaccessible:
                target = min(
                    inaccessible,
                    key=lambda point: abs(point[0] - self.position[0])
                    + abs(point[1] - self.position[1]),
                )
                self.patrol_targets[level.key] = target
            action = self._tunnel_toward(level, target, blocked)
            if action is not None:
                self.action_counts["tunnel_to_mapped_mines"] += 1
                return action
        return None

    def _dig_escape(
        self,
        obs: dict[str, np.ndarray],
        level: LevelState,
        blocked: set[Point],
    ) -> int | None:
        """Dig one promising wall only after ordinary exploration failed."""

        assert self.position is not None
        inventory = self._inventory(obs)
        pickaxe = next(
            (letter for letter, desc in inventory.items() if "pick-axe" in desc),
            None,
        )
        if pickaxe is None:
            return None
        if level.dig_successes >= 24:
            return None
        dist, _ = level.distances(self.position, blocked=blocked, avoid_traps=True)
        candidates: list[tuple[float, Point, Point]] = []
        for point in map(tuple, np.argwhere(dist >= 0)):
            for delta in CARDINALS:
                wall = add(point, delta)
                if not inside(wall, level.shape):
                    continue
                value = int(level.terrain[wall])
                if not (value in (-1, STONE) or WALL_MIN <= value <= WALL_MAX):
                    continue
                attempts = level.dig_attempts.get((point, wall), 0)
                if attempts >= 2:
                    continue
                visible_wall_bonus = -80 if WALL_MIN <= value <= WALL_MAX else 0
                score = (
                    int(dist[point])
                    + attempts * 20
                    + int(level.visits[point]) * 0.1
                    + visible_wall_bonus
                )
                candidates.append((score, point, wall))
        if not candidates:
            return None
        _, approach, wall = min(candidates, key=lambda row: row[0])
        if approach != self.position:
            action = self._path_step(level, {approach}, blocked, "dig_path")
            return None if action == -1 else action
        delta = (wall[0] - approach[0], wall[1] - approach[1])
        level.dig_attempts[(approach, wall)] = (
            level.dig_attempts.get((approach, wall), 0) + 1
        )
        self.intent = {
            "kind": "dig",
            "letter": pickaxe,
            "raw": int(DIRECTION_ACTION[delta]),
            "stage": 0,
        }
        return self._emit(int(nethack.Command.APPLY), "dig_escape")

    def _explore(
        self,
        level: LevelState,
        blocked: set[Point],
        *,
        thorough: bool,
    ) -> int | None:
        mapped = level.key in self.mapped_levels
        # Probe darkness only from a known corridor endpoint.  This follows
        # unlit corridors without wasting turns bumping along every room wall.
        unknown_budget = 320 if not mapped else 0
        action = self._door_or_frontier(level, blocked, unknown_budget=unknown_budget)
        if action is not None:
            level.exhausted = False
            return action

        if mapped:
            level.exhausted = True
            return None
        search_budget = (700 if thorough else 260) + level.escalation * 350
        per_tile = 20 + level.escalation * 5
        action = self._search_hidden(
            level, blocked, budget=search_budget, per_tile=per_tile
        )
        if action is not None:
            level.exhausted = False
            return action
        level.exhausted = True
        return None

    def _go_stair(
        self,
        level: LevelState,
        point: Point,
        blocked: set[Point],
        *,
        down: bool,
        return_if_main: bool = False,
    ) -> int | None:
        assert self.position is not None and self.current_key is not None
        if point != self.position:
            action = self._path_step(level, {point}, blocked, "go_to_stair")
            if action is not None and action != -1:
                return action
            return self._tunnel_toward(level, point, blocked)
        if down:
            self.attempted_down.add((self.current_key, point))
            self.descent = DescentContext(self.current_key, point, return_if_main)
            return self._emit(int(nethack.MiscDirection.DOWN), "descend")
        self.ascent_source = (self.current_key, point)
        return self._emit(int(nethack.MiscDirection.UP), "ascend")

    def _tunnel_toward(
        self,
        level: LevelState,
        target: Point,
        blocked: set[Point],
    ) -> int | None:
        """Carve a deterministic Manhattan route to a mapped staircase."""

        assert self.position is not None and self.latest_obs is not None
        inventory = self._inventory(self.latest_obs)
        pickaxe = next(
            (letter for letter, desc in inventory.items() if "pick-axe" in desc),
            None,
        )
        if pickaxe is None:
            return None
        # Plan over both floor and diggable rock.  The earlier Manhattan
        # greedy stepper could bounce forever at a non-diggable wall: one step
        # away, one step back.  Positive-cost Dijkstra routes cannot contain
        # that cycle and automatically re-plan around exhausted dig edges.
        frontier: list[tuple[int, Point]] = [(0, self.position)]
        costs: dict[Point, int] = {self.position: 0}
        parent: dict[Point, Point] = {}
        while frontier:
            cost, point = heappop(frontier)
            if cost != costs.get(point):
                continue
            if point == target:
                break
            for delta in CARDINALS:
                nxt = add(point, delta)
                if (
                    not inside(nxt, level.shape)
                    or nxt in blocked
                    or nxt in level.boulders
                    or (point, nxt) in level.failed_edges
                ):
                    continue
                value = int(level.terrain[nxt])
                attempts = level.dig_attempts.get((point, nxt), 0)
                if value in BASE_PASSABLE:
                    # Walking a known spike pit can cause an instant poison
                    # death.  A short detour through ordinary rock is cheaper.
                    step_cost = 50 if nxt in level.traps else 1
                elif value in (CLOSED_DOOR_V, CLOSED_DOOR_H):
                    if attempts >= 3:
                        continue
                    step_cost = 3 if level.door_failures.get(nxt, 0) == 0 else 8
                elif value in (-1, STONE) or WALL_MIN <= value <= WALL_MAX:
                    if attempts >= 3:
                        continue
                    step_cost = 8 + attempts * 4
                else:
                    continue
                new_cost = cost + step_cost
                if new_cost >= costs.get(nxt, 1_000_000):
                    continue
                costs[nxt] = new_cost
                parent[nxt] = point
                heappush(frontier, (new_cost, nxt))

        if target not in costs:
            return None
        nxt = target
        while parent.get(nxt) != self.position:
            if nxt not in parent:
                return None
            nxt = parent[nxt]
        delta = (nxt[0] - self.position[0], nxt[1] - self.position[1])
        value = int(level.terrain[nxt])
        attempts = level.dig_attempts.get((self.position, nxt), 0)
        if value in (CLOSED_DOOR_V, CLOSED_DOOR_H) and level.door_failures.get(nxt, 0) == 0:
            level.door_failures[nxt] = 1
            self.intent = {
                "kind": "direction",
                "raw": int(DIRECTION_ACTION[delta]),
            }
            return self._emit(int(nethack.Command.OPEN), "open_tunnel_door")
        if (
            value in (-1, STONE, CLOSED_DOOR_V, CLOSED_DOOR_H)
            or WALL_MIN <= value <= WALL_MAX
        ):
            level.dig_attempts[(self.position, nxt)] = attempts + 1
            self.intent = {
                "kind": "dig",
                "letter": pickaxe,
                "raw": int(DIRECTION_ACTION[delta]),
                "stage": 0,
            }
            return self._emit(int(nethack.Command.APPLY), "dig_toward_stair")
        return self._move(level, nxt, "tunnel_path")

    def _objective(
        self,
        obs: dict[str, np.ndarray],
        level: LevelState,
        blocked: set[Point],
    ) -> int | None:
        assert self.position is not None and self.current_key is not None
        dnum, dlevel = self.current_key

        if self.return_after_descent:
            # A tested staircase stayed in the main dungeon; return immediately
            # and try the other known staircase, which is the Mines branch.
            level.stairs_up.add(self.position)
            return self._go_stair(level, self.position, blocked, down=False)

        if dnum != 0:
            self.mines_dnum = dnum
            # The evaluator succeeds on the arrival square itself.  Once a
            # Mines down stair is known, taking it immediately is both faster
            # and safer than sweeping the current non-town cavern.
            if dlevel <= 4 and level.stairs_down:
                point = min(
                    level.stairs_down,
                    key=lambda p: abs(p[0] - self.position[0])
                    + abs(p[1] - self.position[1]),
                )
                action = self._go_stair(level, point, blocked, down=True)
                if action is not None:
                    return action
            if dlevel >= 5:
                if dlevel <= 6:
                    action = self._patrol_unvisited(level, blocked)
                    if action is not None:
                        return action
                    action = self._explore(level, blocked, thorough=False)
                    if action is not None:
                        return action
                if level.stairs_up:
                    action = self._go_stair(
                        level, next(iter(level.stairs_up)), blocked, down=False
                    )
                    if action is not None:
                        return action
                return self._explore(level, blocked, thorough=False)
            if not level.stairs_down:
                action = self._inspect_objects(level, blocked)
                if action is not None:
                    return action
            # Minetown is around Mines levels 3-4.  Fully enter/explore all
            # candidate levels before allowing another descent; the evaluator
            # stops on the exact first town tile.
            if dlevel >= 2:
                action = self._patrol_unvisited(level, blocked)
                if action is not None:
                    return action
                action = self._explore(level, blocked, thorough=False)
                if action is not None:
                    return action
                if dlevel == 4:
                    if level.escalation < 2:
                        level.escalation += 1
                        level.exhausted = False
                        return self._explore(level, blocked, thorough=True)
                    if level.stairs_down:
                        point = min(
                            level.stairs_down,
                            key=lambda p: abs(p[0] - self.position[0])
                            + abs(p[1] - self.position[1]),
                        )
                        action = self._go_stair(level, point, blocked, down=True)
                        if action is not None:
                            return action
                    if level.stairs_up:
                        return self._go_stair(
                            level, next(iter(level.stairs_up)), blocked, down=False
                        )
            viable_down = [
                point
                for point in level.stairs_down
                if not (
                    (dest := level.down_outcomes.get(point)) in self.levels
                    and self.levels[dest].exhausted
                    and not self.levels[dest].stairs_down
                )
            ]
            if viable_down:
                point = min(
                    viable_down,
                    key=lambda p: abs(p[0] - self.position[0])
                    + abs(p[1] - self.position[1]),
                )
                action = self._go_stair(level, point, blocked, down=True)
                if action is not None:
                    return action
            action = self._explore(level, blocked, thorough=dlevel >= 3)
            if action is not None:
                return action
            if not level.stairs_down and level.escalation < 5:
                level.escalation += 1
                level.exhausted = False
                return self._explore(level, blocked, thorough=True)
            return None

        # Main dungeon level 1 cannot contain the branch.
        if dlevel == 1:
            if level.stairs_down:
                action = self._go_stair(
                    level, next(iter(level.stairs_down)), blocked, down=True
                )
                if action is not None:
                    return action
            action = self._inspect_objects(level, blocked)
            if action is not None:
                return action
            action = self._explore(level, blocked, thorough=False)
            if action is not None:
                return action
            if not level.stairs_down and level.escalation < 1:
                level.escalation += 1
                level.exhausted = False
                return self._explore(level, blocked, thorough=True)
            return None

        if 2 <= dlevel <= 4:
            if not level.stairs_down:
                action = self._inspect_objects(level, blocked)
                if action is not None:
                    return action
            action = self._explore(
                level, blocked, thorough=self.branch_backtracking
            )
            if action is not None:
                return action

            attempted_here = {
                point for key, point in self.attempted_down if key == self.current_key
            }
            untested = level.stairs_down - attempted_here
            if untested:
                point = min(untested)
                action = self._go_stair(
                    level,
                    point,
                    blocked,
                    down=True,
                    return_if_main=True,
                )
                if action is not None:
                    return action

            if not level.stairs_down and level.escalation < 1:
                level.escalation += 1
                level.exhausted = False
                return self._explore(level, blocked, thorough=True)

            if self.branch_backtracking:
                # This level has been re-searched after missing the branch.
                # Continue upward rather than looping down the known main stair.
                if level.stairs_up:
                    return self._go_stair(level, next(iter(level.stairs_up)), blocked, down=False)
            else:
                # The sole exhausted staircase is the normal continuation.
                known_main = [
                    point for point, dest in level.down_outcomes.items() if dest[0] == 0
                ]
                if known_main:
                    return self._go_stair(level, known_main[0], blocked, down=True)
            return None

        # Reaching main dungeon level 5 means the branch on levels 2-4 was
        # missed.  Turn around and repeat targeted secret-door searches.
        self.branch_backtracking = True
        if not level.stairs_up and int(level.visits.sum()) < 20:
            # On the first observation after descent this square is necessarily
            # the arrival staircase, even if a --More-- prompt hid the raw `>`.
            level.stairs_up.add(self.position)
        if level.stairs_up:
            point = min(
                level.stairs_up,
                key=lambda p: abs(p[0] - self.position[0])
                + abs(p[1] - self.position[1]),
            )
            return self._go_stair(level, point, blocked, down=False)
        return self._explore(level, blocked, thorough=False)

    def act(self, obs: dict[str, np.ndarray]) -> int:
        level = self._observe(obs)
        prompt_action = self._prompt(obs)
        if prompt_action is not None:
            return prompt_action

        if self.incapacitated:
            return self._emit(int(nethack.MiscDirection.WAIT), "wait_incapacitated")

        self.normal_turns += 1
        creatures, pets = self._creatures(obs)
        # Tame pets can normally be displaced by walking into them.  Treating
        # them as walls creates permanent one-tile corridor deadlocks.
        blocked = {
            point
            for point, name in creatures.items()
            if (
                name in PASSIVE_DANGER_NAMES
                or name in self.forced_peaceful_names
                or (name in PEACEFUL_DWARF_NAMES and name not in self.hostile_names)
            )
        } - pets
        blocked.discard(self.position)

        action = self._emergency(obs)
        if action is not None:
            return action

        action = self._adjacent_combat(obs, level, creatures, pets)
        if action is not None:
            return action

        action = self._survival(obs, level)
        if action is not None:
            return action

        action = self._map_level(obs)
        if action is not None:
            return action

        action = self._try_excalibur(obs, level)
        if action is not None:
            return action

        action = self._objective(obs, level, blocked)
        if action is not None:
            return action

        # Peaceful creatures sometimes occupy the only corridor.  Waiting is
        # safer than answering a "Really attack?" prompt and usually unblocks
        # the route within a handful of turns.
        return self._emit(int(nethack.MiscDirection.WAIT), "wait_blocked")

    def summary(self, obs: dict[str, np.ndarray] | None = None) -> dict:
        bl = obs["blstats"] if obs is not None else None
        screen = None
        if obs is not None:
            screen = "\n".join(
                bytes(row).decode("utf-8", "replace") for row in obs["chars"]
            )
        return {
            "steps": self.steps,
            "turn": int(bl[nethack.NLE_BL_TIME]) if bl is not None else None,
            "depth": int(bl[nethack.NLE_BL_DEPTH]) if bl is not None else None,
            "dungeon": int(bl[nethack.NLE_BL_DNUM]) if bl is not None else None,
            "dlevel": int(bl[nethack.NLE_BL_DLEVEL]) if bl is not None else None,
            "hp": int(bl[nethack.NLE_BL_HP]) if bl is not None else None,
            "hpmax": int(bl[nethack.NLE_BL_HPMAX]) if bl is not None else None,
            "xp_level": int(bl[nethack.NLE_BL_XP]) if bl is not None else None,
            "hunger": int(bl[nethack.NLE_BL_HUNGER]) if bl is not None else None,
            "mines_dnum": self.mines_dnum,
            "last_message": self.last_message,
            "recent_messages": list(self.messages)[-12:],
            "failure_hint": self.failure_hint,
            "excalibur": self.excalibur_done,
            "attempted_down": [
                [
                    [int(key[0]), int(key[1])],
                    [int(point[0]), int(point[1])],
                ]
                for key, point in sorted(self.attempted_down)
            ],
            "actions": dict(self.action_counts),
            "screen": screen,
            "levels": {
                f"{key[0]}:{key[1]}": {
                    "visits": int(level.visits.sum()),
                    "searches": level.search_total,
                    "unknown_attempts": level.unknown_attempts,
                    "objects_inspected": len(level.inspected_objects),
                    "dig_successes": level.dig_successes,
                    "up": len(level.stairs_up),
                    "down": len(level.stairs_down),
                    "exhausted": level.exhausted,
                }
                for key, level in self.levels.items()
            },
        }
