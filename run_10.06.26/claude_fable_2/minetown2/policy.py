"""Politique symbolique Valkyrie pour le début de NetHack 3.6.7.

Architecture héritée du run gpt_5.6 (politique 86% locale), avec quatre
améliorations principales :

- recherches de portes cachées par rafales comptées (``16s``) au lieu d'un
  ``s`` par step : ~10x moins de steps consommés, contre les step_timeout ;
- gravure d'Elbereth en situation critique (acculé ou PV bas), puis repos
  protégé sur la gravure ;
- interdiction absolue de mêlée contre les floating eyes (paralysie fatale)
  et repos avant chaque descente d'escalier ;
- anti-blocage : détection des attentes prolongées derrière un monstre
  pacifique et déblocage par pas de côté ou creusage.
"""

from __future__ import annotations

import re
from collections import Counter, deque
from dataclasses import dataclass
from heapq import heappop, heappush

import numpy as np
from nle import nethack

from .state import (
    BASE_PASSABLE,
    CARDINALS,
    CLOSED_DOOR_H,
    CLOSED_DOOR_V,
    CORRIDOR,
    DARKROOM,
    DIRECTIONS,
    DOORWAY,
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

DOOR_TILES = (DOORWAY, OPEN_DOOR_V, OPEN_DOOR_H)

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

# Cadavres toujours sans danger pour une Valkyrie naine (pas de poison, pas
# de cannibalisme — donc pas de nain).
SAFE_CORPSES = frozenset(
    {
        "lichen",
        "newt",
        "gecko",
        "jackal",
        "fox",
        "coyote",
        "sewer rat",
        "giant rat",
        "grid bug",
        "cave spider",
        "iguana",
        "gnome",
        "gnome lord",
        "hobbit",
        "rock piercer",
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
        # Toucher un (chick|cock)atrice pétrifie : à traiter à distance.
        "chickatrice",
        "cockatrice",
    }
)

# Animaux pacifiques qu'on accepte d'attaquer s'ils bloquent durablement le
# seul passage (pénalité d'alignement mineure, pas un meurtre).
FORCE_ATTACK_ANIMALS = frozenset(
    {
        "kitten",
        "housecat",
        "large cat",
        "little dog",
        "dog",
        "large dog",
        "pony",
        "horse",
        "warhorse",
        "hobbit",
    }
)

# Monstres qui ne respectent pas Elbereth (humains, elfes, minotaure,
# personnel des villes).  En leur présence adjacente, graver ne protège pas.
ELBERETH_IGNORER_PATTERN = re.compile(
    r"(elf|human|minotaur|shopkeeper|priest|watchman|watch captain|guard|"
    r"soldier|sergeant|lieutenant|captain|nurse|Kop)",
    re.I,
)

# Hostiles plus rapides qu'une Valkyrie (vitesse 12) : fuir est perdant, il
# faut combattre ou graver Elbereth.
FAST_HOSTILES = frozenset(
    {
        "kitten",
        "housecat",
        "large cat",
        "little dog",
        "dog",
        "large dog",
        "jackal",
        "coyote",
        "fox",
        "wolf",
        "bat",
        "giant bat",
        "pony",
        "horse",
        "warhorse",
        "leprechaun",
        # Fourmis : vitesse 18, fuir est perdant ; on les combat.
        "giant ant",
        "soldier ant",
        "fire ant",
        "killer bee",
    }
)

ATTACKING_PLAYER = re.compile(
    r"(?:The|A|An) ([A-Za-z][A-Za-z -]*?) "
    r"(?:hits|misses|bites|kicks|stings|claws|butts|touches|engulfs)(?:!|\.)"
)


def decode(raw: np.ndarray) -> str:
    return bytes(raw).split(b"\0", 1)[0].decode("utf-8", "replace")


@dataclass
class DescentContext:
    source_key: LevelKey
    source_point: Point
    return_if_main: bool


class MinetownPolicy:
    """Politique à état n'utilisant que l'observation publique du Challenge."""

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
        self.pending: deque[tuple[int, str]] = deque()
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
        self.trail: deque[tuple] = deque(maxlen=400)
        # Elbereth.
        self.elbereth_pos: Point | None = None
        self.elbereth_key: LevelKey | None = None
        self.elbereth_step = -10_000
        self.last_engrave_attempt = -10_000
        # Anti-blocage.
        self.blocked_streak = 0
        self.last_evade_step = -10_000
        self.more_streak = 0
        # Repos avant descente.
        self.descent_rest: Counter[LevelKey] = Counter()
        # Hostiles visibles de la frame courante (pour le repos sûr).
        self.visible_hostiles: dict[Point, str] = {}
        # Attaque forcée d'un animal pacifique bloquant.
        self.force_attack_step = -10_000
        # Suivi des attaques subies et de l'efficacité d'Elbereth.
        self.last_attacked_step = -10_000
        self.elbereth_futile_until = -10_000
        # Lancer cassé (ex. polymorphé sans mains) : ne pas boucler.
        self.throw_pending: int | None = None
        self.throw_broken_until = -10_000
        # Cadavres sûrs connus : (niveau, position) -> (tour, nom).
        self.corpses: dict[tuple[LevelKey, Point], tuple[int, str]] = {}
        # Récupération de projectiles au sol (contre les passifs bloquants).
        self.pickup_attempts: Counter[LevelKey] = Counter()
        self.fetch_hold = -1
        self.current_blocked: set[Point] = set()
        self.shopkeeper_levels: set[LevelKey] = set()

    @staticmethod
    def _index(raw: int) -> int:
        try:
            return RAW_TO_INDEX[int(raw)]
        except KeyError as exc:
            raise RuntimeError(f"Raw key {raw!r} is not in NLE's action space") from exc

    def _emit(self, raw: int, label: str) -> int:
        self.last_raw_action = int(raw)
        self.action_counts[label] += 1
        hp = None
        if self.latest_obs is not None:
            hp = int(self.latest_obs["blstats"][nethack.NLE_BL_HP])
        self.trail.append(
            (self.steps, label, hp, self.current_key, self.position)
        )
        return self._index(int(raw))

    def _queue_keys(self, keys: str, label: str) -> int:
        """Émet la première touche et met les suivantes en file."""

        for char in keys[1:]:
            self.pending.append((ord(char), label))
        return self._emit(ord(keys[0]), label)

    def _burst_search(self, level: LevelState, turns: int, label: str) -> int:
        """Recherche multi-tours ``<n>s`` : n tours de jeu pour ~3 steps."""

        assert self.position is not None
        level.searches[self.position] = min(
            32767, int(level.searches[self.position]) + turns
        )
        level.search_total += turns
        return self._queue_keys(f"{turns}s", label)

    def _rest_search(self, turns: int, label: str) -> int:
        """Repos par recherche comptée, sans consommer le budget de fouille."""

        return self._queue_keys(f"{turns}s", label)

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
            self.last_attacked_step = self.steps
            if (
                self.elbereth_pos == self.position
                and self.elbereth_key == self.current_key
                and self.steps - self.elbereth_step < 60
            ):
                # Attaqué debout sur la gravure : elle ne protège pas ici.
                self.elbereth_futile_until = self.steps + 200

        old_key, old_point = self.current_key, self.position
        self.previous_key, self.previous_position = old_key, old_point
        self.current_key, self.position = key, point
        self.last_message = message
        level = self.levels.setdefault(key, LevelState(key, obs["glyphs"].shape))
        level.update(obs, point)
        if any(
            phrase in lowered_message
            for phrase in (
                "succeed in cutting away",
                "make an opening in",
                "finish chopping",
            )
        ):
            level.dig_successes += 1
            level.unknown_attempts = 0
            level.exhausted = False

        if "staircase down" in lowered_message:
            level.stairs_down.add(point)
        if "staircase up" in lowered_message:
            level.stairs_up.add(point)
        # Escaliers fantômes (ex. case d'arrivée d'une chute de trappe
        # supposée être un escalier) : le jeu nous corrige, on écoute.
        if "can't go up" in lowered_message:
            level.stairs_up.discard(point)
        if "can't go down" in lowered_message:
            level.stairs_down.discard(point)

        if old_key is not None and old_point is not None and key != old_key:
            self.pending.clear()
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
            move_key, start, target, was_unknown, combat = self.last_move
            if key == move_key and point == start and not combat:
                # Échec détecté par la position : les bumps silencieux dans la
                # roche (aucun message) laissaient sinon le candidat éligible
                # pour toujours, d'où des allers-retours massifs.
                benign = any(
                    phrase in lowered_message
                    for phrase in (
                        "bear trap",
                        "stuck in a web",
                        "in a pit",
                        "really attack",
                        "wait!",
                        "you hit",
                        "you miss",
                        "you kill",
                        "you destroy",
                    )
                )
                if not benign:
                    self.levels[move_key].failed_edges.add((start, target))
                    if was_unknown:
                        self.levels[move_key].unknown_attempts += 1
            self.last_move = None

        # Détection des kills pour manger les cadavres sûrs.
        kill_match = re.search(r"You (?:kill|destroy) the ([a-z][a-z ]*)!", message)
        if kill_match and self.last_move is not None and self.last_move[4]:
            name = kill_match.group(1).strip()
            if name in SAFE_CORPSES:
                turn = int(bl[nethack.NLE_BL_TIME])
                self.corpses[(key, self.last_move[2])] = (turn, name)
        if "you see here a lichen corpse" in lowered_message:
            # Les cadavres de lichen ne pourrissent jamais.
            self.corpses[(key, point)] = (10**9, "lichen")

        # Lancer sans effet (ex. sans mains) : désactiver le lancer un moment.
        if self.throw_pending is not None and self.steps > self.throw_pending:
            if not np.any(obs["misc"]):
                self.throw_broken_until = self.steps + 500
            self.throw_pending = None

        # Une intention de commande est terminée dès le retour au mode normal.
        if not np.any(obs["misc"]) and self.intent is not None:
            if (
                self.intent.get("kind") == "engrave"
                and int(self.intent.get("stage", 0)) >= 2
            ):
                self.elbereth_pos = self.position
                self.elbereth_key = self.current_key
                self.elbereth_step = self.steps
            self.intent = None

        return level

    def _prompt(self, obs: dict[str, np.ndarray]) -> int | None:
        misc = obs["misc"]
        if misc[2]:
            self.more_streak += 1
            if self.more_streak > 30:
                # Fenêtre coincée sur --More-- : la fermer autrement.
                return self._emit(int(nethack.Command.ESC), "more_breaker")
            return self._emit(int(nethack.MiscAction.MORE), "more")
        self.more_streak = 0

        message = self.last_message.lower()
        if misc[1]:
            if self.intent and self.intent.get("kind") == "engrave":
                text = self.intent.setdefault("text", "Elbereth")
                index = int(self.intent.get("text_i", 0))
                if index < len(text):
                    self.intent["text_i"] = index + 1
                    self.intent["stage"] = 2
                    return self._emit(ord(text[index]), "engrave_text")
                self.intent["stage"] = 3
                return self._emit(ord("\r"), "engrave_confirm")
            self.intent = None
            return self._emit(int(nethack.Command.ESC), "escape_getlin")

        if not misc[0]:
            return None

        if "really attack" in message:
            if self.steps - self.force_attack_step <= 3:
                # Déblocage assumé d'un animal pacifique qui campe le passage.
                self.intent = None
                return self._emit(ord("y"), "force_attack_yes")
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
            if kind == "engrave":
                if "add to the current engraving" in message:
                    return self._emit(ord("y"), "engrave_append")
                if "engrave with" in message or "write with" in message:
                    self.intent["stage"] = 1
                    return self._emit(ord("-"), "engrave_fingers")
                return self._emit(ord("y"), "engrave_yes")
            if kind == "pickup":
                if "pick it up" in message or "pick up" in message:
                    self.intent = None
                    return self._emit(ord("y"), "pickup_confirm")
                self.intent = None
                return self._emit(int(nethack.Command.ESC), "pickup_abort")
            if kind == "eat_floor":
                if "eat it?" in message or "eat one?" in message:
                    self.intent = None
                    if self.current_key is not None and self.position is not None:
                        self.corpses.pop((self.current_key, self.position), None)
                    return self._emit(ord("y"), "eat_floor_confirm")
                self.intent = None
                if self.current_key is not None and self.position is not None:
                    self.corpses.pop((self.current_key, self.position), None)
                return self._emit(int(nethack.Command.ESC), "eat_floor_abort")
            if kind == "eat":
                if "eat it?" in message or "eat one?" in message:
                    return self._emit(ord("n"), "decline_floor_food")
                letter = self.intent.get("letter")
                self.intent = None
                return self._emit(ord(letter), "select_food")
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
                    self.throw_pending = None
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

        # Réponses conservatrices aux questions non sollicitées.
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

    def _creatures(
        self, obs: dict[str, np.ndarray]
    ) -> tuple[dict[Point, str], set[Point]]:
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

    def _is_hostile(self, name: str) -> bool:
        return not (
            name in PEACEFUL_DWARF_NAMES and name not in self.hostile_names
        ) and name not in self.forced_peaceful_names

    _COMBAT_MOVE_LABELS = frozenset(
        {"melee", "melee_passive_last_resort", "melee_forced"}
    )

    def _move(self, level: LevelState, target: Point, label: str) -> int:
        assert self.position is not None and self.current_key is not None
        delta = (target[0] - self.position[0], target[1] - self.position[1])
        raw = int(DIRECTION_ACTION[delta])
        was_unknown = int(level.terrain[target]) in (-1, STONE)
        self.last_move = (
            self.current_key,
            self.position,
            target,
            was_unknown,
            label in self._COMBAT_MOVE_LABELS,
        )
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

    def _flee_candidates(
        self,
        level: LevelState,
        hostiles: list[tuple[Point, str]],
        blocked: set[Point],
    ) -> list[tuple[int, int, Point]]:
        assert self.position is not None
        passable = level.passable_mask(blocked=blocked, avoid_traps=True)
        candidates: list[tuple[int, int, Point]] = []
        here_terrain = int(level.terrain[self.position])
        for delta in DIRECTIONS:
            point = add(self.position, delta)
            if not inside(point, level.shape) or not passable[point]:
                continue
            if delta[0] and delta[1]:
                side1 = (self.position[0] + delta[0], self.position[1])
                side2 = (self.position[0], self.position[1] + delta[1])
                if not passable[side1] and not passable[side2]:
                    continue
                if here_terrain in DOOR_TILES or int(level.terrain[point]) in DOOR_TILES:
                    continue
            separation = min(
                max(abs(point[0] - enemy[0][0]), abs(point[1] - enemy[0][1]))
                for enemy in hostiles
            )
            candidates.append((separation, -int(level.visits[point]), point))
        return candidates

    def _engrave_elbereth(self, label: str) -> int:
        self.last_engrave_attempt = self.steps
        self.intent = {"kind": "engrave", "stage": 0, "text": "Elbereth", "text_i": 0}
        return self._emit(int(nethack.Command.ENGRAVE), label)

    def _elbereth_applicable(self, hostiles: list[tuple[Point, str]]) -> bool:
        """Vrai si au moins un hostile adjacent respecte Elbereth."""

        if self.incapacitated:
            return False
        if self.steps < self.elbereth_futile_until:
            return False
        if self.steps - self.last_engrave_attempt < 6:
            return False
        if any(name in FAST_HOSTILES for _, name in hostiles):
            # Les animaux rapides multi-attaques usent la gravure en un ou
            # deux coups : graver ne fait que perdre des tours, on se bat.
            return False
        respecters = [
            name for _, name in hostiles if not ELBERETH_IGNORER_PATTERN.search(name)
        ]
        return bool(respecters)

    def _on_fresh_elbereth(self) -> bool:
        return (
            self.elbereth_pos == self.position
            and self.elbereth_key == self.current_key
            and self.steps - self.elbereth_step < 60
        )

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
            if point in pets or not self._is_hostile(name):
                continue
            if (
                max(
                    abs(point[0] - self.position[0]),
                    abs(point[1] - self.position[1]),
                )
                <= 1
            ):
                if name in PASSIVE_DANGER_NAMES:
                    passive_dangers.append((point, name))
                else:
                    hostiles.append((point, name))
        if not hostiles and not passive_dangers:
            return None

        hp = int(obs["blstats"][nethack.NLE_BL_HP])
        hpmax = max(1, int(obs["blstats"][nethack.NLE_BL_HPMAX]))
        blocked = set(creatures) | pets

        if hostiles:
            low_hp = hp * 100 < hpmax * 60
            critical = hp * 100 < hpmax * 40 or (
                hp * 100 < hpmax * 55 and len(hostiles) >= 2
            )
            under_fire = self.steps - self.last_attacked_step <= 2
            # Repos protégé sur une gravure fraîche — mais si on se fait
            # quand même taper dessus, la gravure ne marche pas : on riposte.
            if self._on_fresh_elbereth() and not under_fire and hp < hpmax:
                if self.steps - self.elbereth_step > 14 and self._elbereth_applicable(
                    hostiles
                ):
                    return self._engrave_elbereth("reengrave_elbereth")
                return self._emit(int(nethack.Command.SEARCH), "rest_on_elbereth")
            if low_hp:
                # Fuir un monstre plus rapide (chats, chiens, chacals...) ne
                # fait qu'offrir des attaques gratuites : Elbereth ou combat.
                fast_present = any(name in FAST_HOSTILES for _, name in hostiles)
                if critical and self._elbereth_applicable(hostiles):
                    return self._engrave_elbereth("engrave_elbereth")
                if not fast_present:
                    candidates = self._flee_candidates(level, hostiles, blocked)
                    safe_candidates = [row for row in candidates if row[0] > 1]
                    if safe_candidates:
                        point = max(safe_candidates)[2]
                        return self._move(level, point, "flee_low_hp")
                if self._elbereth_applicable(hostiles):
                    return self._engrave_elbereth("engrave_elbereth_cornered")

        if not hostiles and passive_dangers:
            gas_spores = [entry for entry in passive_dangers if entry[1] == "gas spore"]
            if gas_spores:
                if self.action_counts["avoid_gas_spore"] >= 24 and hp >= 28:
                    target, name = gas_spores[0]
                    self.failure_hint = f"combat:{name}"
                    return self._move(level, target, "melee_passive_last_resort")
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
            if projectile is not None and self.steps >= self.throw_broken_until:
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
                self.throw_pending = self.steps
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
            # Plus de projectile ni de wand : tenter d'aller ramasser un objet
            # au sol (souvent notre propre dague lancée).
            fetch = self._fetch_projectile(level, blocked)
            if fetch is not None:
                return fetch
            # Jamais de mêlée contre un floating eye tant qu'il reste une
            # alternative : la paralysie de 1d70 tours est presque toujours
            # fatale.  Les autres passifs deviennent attaquables à PV hauts,
            # d'autant plus vite qu'on est coincé depuis longtemps.
            other_hostiles = [
                other_name
                for other_point, other_name in creatures.items()
                if other_point not in pets
                and self._is_hostile(other_name)
                and other_name not in PASSIVE_DANGER_NAMES
            ]
            if (
                name not in ("floating eye", "gas spore", "chickatrice", "cockatrice")
                and hp * 4 >= hpmax * 3
                and (not other_hostiles or self.blocked_streak >= 60)
            ):
                self.failure_hint = f"combat:{name}"
                return self._move(level, target, "melee_passive_last_resort")
            if (
                name == "floating eye"
                and (
                    (self.blocked_streak >= 150 and not other_hostiles)
                    or self.blocked_streak >= 250
                )
                and hp * 100 >= hpmax * 85
            ):
                # Ultime recours : pari sur la paralysie, seul un blocage
                # total sans autre hostile visible le justifie.
                self.failure_hint = f"combat:{name}"
                return self._move(level, target, "melee_passive_last_resort")
            # Un passif sessile est plus sûr comme mur temporaire que comme
            # cible.  La navigation cherchera un autre chemin.
            return None

        def difficulty(entry: tuple[Point, str]) -> int:
            point, _ = entry
            glyph = int(obs["glyphs"][point])
            try:
                return int(
                    nethack.permonst(int(nethack.glyph_to_mon(glyph))).difficulty
                )
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
            self.intent = {"kind": "wield", "letter": sword}
            return self._emit(int(nethack.Command.WIELD), "wield_for_combat")
        return self._move(level, target, "melee")

    def _fetch_projectile(
        self, level: LevelState, blocked: set[Point]
    ) -> int | None:
        """Va ramasser un objet au sol quand on n'a plus rien à lancer."""

        assert self.position is not None and self.current_key is not None
        if self.latest_obs is None:
            return None
        if self.current_key in self.shopkeeper_levels:
            # Ramasser un article de boutique puis sortir = vol = shopkeeper
            # meurtrier.  On ne ramasse jamais rien sur un niveau à boutique.
            return None
        if self.pickup_attempts[self.current_key] >= 6:
            return None
        inventory = self._inventory(self.latest_obs)
        if any(
            projectile in description
            for projectile in ("dagger", "rock", "dart", "arrow")
            for description in inventory.values()
        ):
            return None
        candidates = level.objects - level.boulders - blocked
        candidates.discard(self.position)
        if self.position in level.objects:
            candidates.add(self.position)
        if not candidates:
            return None
        path = level.path(self.position, candidates, blocked)
        if path is None:
            return None
        if len(path) > 1:
            # Mode collant : sans persistance, ce but de navigation entrait en
            # ping-pong avec l'inspection d'objets de la couche objectif.
            self.fetch_hold = self.steps + 60
            return self._move(level, path[1], "fetch_projectile")
        self.fetch_hold = -1
        self.pickup_attempts[self.current_key] += 1
        level.objects.discard(self.position)
        self.intent = {"kind": "pickup"}
        return self._emit(int(nethack.Command.PICKUP), "pickup_projectile")

    def _hostile_nearby(self, radius: int = 6) -> bool:
        assert self.position is not None
        for point, name in self.visible_hostiles.items():
            if name in PASSIVE_DANGER_NAMES:
                continue
            if (
                max(
                    abs(point[0] - self.position[0]),
                    abs(point[1] - self.position[1]),
                )
                <= radius
            ):
                return True
        return False

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
            # Pas de ration : manger un cadavre sûr (frais ou lichen).
            action = self._eat_corpse(obs, turn, self.current_blocked)
            if action is not None:
                return action

        if hunger >= 3 and turn >= 350 and turn - self.last_prayer_turn >= 700:
            self.last_prayer_turn = turn
            self.intent = {"kind": "pray"}
            return self._emit(int(nethack.Command.PRAY), "pray_for_hunger")
        if hunger >= 4 and turn - self.last_prayer_turn >= 300:
            # Évanouissements : prier même si le délai est incertain.
            self.last_prayer_turn = turn
            self.intent = {"kind": "pray"}
            return self._emit(int(nethack.Command.PRAY), "pray_fainting")

        # Repos : uniquement sans hostile visible proche, par rafales de
        # recherche comptée (le jeu interrompt la rafale si un monstre surgit).
        if hp * 100 < hpmax * 70 and not self._hostile_nearby(6) and hunger < 3:
            return self._rest_search(15, "rest")
        return None

    def _eat_corpse(
        self, obs: dict[str, np.ndarray], turn: int, blocked: set[Point]
    ) -> int | None:
        assert self.position is not None and self.current_key is not None
        fresh: dict[Point, str] = {}
        for (key, point), (killed_turn, name) in list(self.corpses.items()):
            if key != self.current_key:
                continue
            if name != "lichen" and turn - killed_turn > 40:
                del self.corpses[(key, point)]
                continue
            if point in blocked:
                # Une créature (souvent pacifique) occupe le cadavre : marcher
                # dessus déclenchait une boucle « Really attack? ».
                continue
            fresh[point] = name
        if not fresh:
            return None
        if self.position in fresh:
            # Une seule tentative par cadavre : purger l'enregistrement dès
            # l'émission (s'il a disparu, EAT ne produit aucun prompt et on
            # bouclerait sinon indéfiniment).
            self.corpses.pop((self.current_key, self.position), None)
            self.intent = {"kind": "eat_floor", "name": fresh[self.position]}
            return self._emit(int(nethack.Command.EAT), "eat_corpse")
        level = self.levels[self.current_key]
        path = level.path(self.position, set(fresh), blocked)
        if path is not None and len(path) > 1:
            return self._move(level, path[1], "go_to_corpse")
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
            # La lycanthropie est un « trouble majeur » : la prière la soigne.
            # Non traitée, elle finit par tuer (forme de rat surchargée,
            # incapable de combattre, entourée de rats invoqués).
            turn = int(obs["blstats"][nethack.NLE_BL_TIME])
            if turn - self.last_prayer_turn >= 500:
                self.last_prayer_turn = turn
                self.intent = {"kind": "pray"}
                return self._emit(int(nethack.Command.PRAY), "pray_lycanthropy")
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
        ) or (
            hp * 5 <= hpmax
            and turn >= 100
            and turn - self.last_prayer_turn >= 600
        ):
            self.last_prayer_turn = turn
            self.intent = {"kind": "pray"}
            return self._emit(int(nethack.Command.PRAY), "pray_emergency")
        return None

    def _try_excalibur(
        self, obs: dict[str, np.ndarray], level: LevelState
    ) -> int | None:
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
                    nxt in level.boulders
                    and (point, nxt) not in level.failed_edges
                    and (point, nxt) not in level.probe_attempts
                ):
                    # Un boulder bouche souvent l'unique couloir : le pousser
                    # est prioritaire sur les sondes d'inconnu.
                    candidates.append((d - 6, point, nxt, "boulder"))
                elif (
                    value in (-1, STONE)
                    and (point, nxt) not in level.failed_edges
                    and (point, nxt) not in level.probe_attempts
                    and level.unknown_attempts < unknown_budget
                ):
                    continuation = 0
                    opposite = (point[0] - delta[0], point[1] - delta[1])
                    if inside(opposite, level.shape) and int(
                        level.terrain[opposite]
                    ) in (
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
            kick = failures > 0
            if kick and level.key in self.shopkeeper_levels:
                # Défoncer une porte de boutique rend le shopkeeper meurtrier.
                level.door_failures[target] = 6
                return self._emit(int(nethack.MiscDirection.WAIT), "skip_shop_door")
            raw = int(nethack.Command.KICK if kick else nethack.Command.OPEN)
            level.door_failures[target] = failures + 1
            self.intent = {"kind": "direction", "raw": int(DIRECTION_ACTION[delta])}
            return self._emit(raw, "kick_door" if kick else "open_door")
        level.probe_attempts.add((self.position, target))
        if kind == "boulder":
            return self._move(level, target, "push_boulder")
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
        # Masse d'inconnu derrière chaque mur : les passages cachés mènent aux
        # zones jamais vues OU vues mais injoignables (pièce aperçue de loin
        # sans couloir connu) ; on fouille en priorité les murs qui les bordent.
        unknown = (
            (level.terrain == -1)
            | (np.isin(level.terrain, tuple(BASE_PASSABLE)) & (dist < 0))
        ).astype(np.int32)
        integral = unknown.cumsum(0).cumsum(1)

        def unknown_mass(center: Point, radius: int = 5) -> int:
            y0 = max(0, center[0] - radius)
            x0 = max(0, center[1] - radius)
            y1 = min(level.shape[0] - 1, center[0] + radius)
            x1 = min(level.shape[1] - 1, center[1] + radius)
            total = int(integral[y1, x1])
            if y0 > 0:
                total -= int(integral[y0 - 1, x1])
            if x0 > 0:
                total -= int(integral[y1, x0 - 1])
            if y0 > 0 and x0 > 0:
                total += int(integral[y0 - 1, x0 - 1])
            return total

        candidates: list[tuple[float, Point]] = []
        for y, x in map(tuple, np.argwhere(dist >= 0)):
            point = (int(y), int(x))
            wallish = 0
            known_degree = 0
            best_mass = 0
            for delta in CARDINALS:
                nxt = add(point, delta)
                if not inside(nxt, level.shape):
                    continue
                value = int(level.terrain[nxt])
                is_wall = value in (-1, STONE) or WALL_MIN <= value <= WALL_MAX
                wallish += is_wall
                known_degree += value in (ROOM, DARKROOM, CORRIDOR)
                if is_wall:
                    beyond = (point[0] + delta[0] * 4, point[1] + delta[1] * 4)
                    beyond = (
                        min(max(beyond[0], 0), level.shape[0] - 1),
                        min(max(beyond[1], 0), level.shape[1] - 1),
                    )
                    best_mass = max(best_mass, unknown_mass(beyond))
            terrain = int(level.terrain[point])
            local_limit = (
                per_tile
                if terrain == CORRIDOR and known_degree <= 1
                else max(8, per_tile // 3)
            )
            if level.searches[point] >= local_limit:
                continue
            if wallish:
                priority = (
                    int(dist[point])
                    + int(level.searches[point]) * 0.5
                    + known_degree * 2
                    - wallish * 2
                    - best_mass * 0.4
                    - (80 if terrain == CORRIDOR and known_degree <= 1 else 0)
                )
                candidates.append((priority, point))
        if not candidates:
            return None
        current_candidate = next(
            (point for _, point in candidates if point == self.position), None
        )
        target = (
            current_candidate if current_candidate is not None else min(candidates)[1]
        )
        if target != self.position:
            action = self._path_step(level, {target}, blocked, "search_path")
            return None if action == -1 else action
        # Rafale comptée : ~16 tours de recherche pour 3 steps d'agent.
        remaining = max(1, min(16, budget - level.search_total))
        return self._burst_search(level, remaining, "search_hidden")

    def _inspect_objects(
        self,
        level: LevelState,
        blocked: set[Point],
    ) -> int | None:
        """`:` révèle un escalier caché sous un glyphe d'objet."""

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
        """Balaye le terrain cartographié des Mines jusqu'au signal exact."""

        assert self.position is not None
        dist, _ = level.distances(self.position, blocked=blocked, avoid_traps=True)
        if self.patrol_actions[level.key] < 500:
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
            if candidates:
                target = max(candidates, key=lambda point: int(dist[point]))
                self.patrol_targets[level.key] = target
                action = self._path_step(
                    level, {target}, blocked, "patrol_mapped_mines"
                )
                if action is not None and action != -1:
                    self.patrol_actions[level.key] += 1
                return None if action == -1 else action

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
        """Creuse un mur prometteur après échec de l'exploration ordinaire."""

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
        do_search: bool = True,
        unknown_cap: int = 320,
    ) -> int | None:
        mapped = level.key in self.mapped_levels
        unknown_budget = unknown_cap if not mapped else 0
        action = self._door_or_frontier(level, blocked, unknown_budget=unknown_budget)
        if action is not None:
            level.exhausted = False
            return action

        if mapped or not do_search:
            level.exhausted = True
            return None
        search_budget = (900 if thorough else 420) + level.escalation * 400
        per_tile = 32 + level.escalation * 16
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
            # Descendre blessé multiplie les morts à l'arrivée : un nouveau
            # niveau peut placer des hostiles adjacents immédiatement.
            assert self.latest_obs is not None
            bl = self.latest_obs["blstats"]
            hp = int(bl[nethack.NLE_BL_HP])
            hpmax = max(1, int(bl[nethack.NLE_BL_HPMAX]))
            hunger = int(bl[nethack.NLE_BL_HUNGER])
            if (
                hp * 100 < hpmax * 60
                and hunger < 3
                and not self._hostile_nearby(6)
                and self.descent_rest[self.current_key] < 40
            ):
                self.descent_rest[self.current_key] += 1
                return self._rest_search(15, "rest_before_descent")
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
        """Creuse une route déterministe vers un escalier cartographié."""

        assert self.position is not None and self.latest_obs is not None
        inventory = self._inventory(self.latest_obs)
        pickaxe = next(
            (letter for letter, desc in inventory.items() if "pick-axe" in desc),
            None,
        )
        if pickaxe is None:
            return None
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
        if (
            value in (CLOSED_DOOR_V, CLOSED_DOOR_H)
            and level.door_failures.get(nxt, 0) == 0
        ):
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
            level.stairs_up.add(self.position)
            return self._go_stair(level, self.position, blocked, down=False)

        if dnum != 0:
            self.mines_dnum = dnum
            if dlevel <= 4 and level.stairs_down:
                # Ne re-descendre que vers une destination encore utile,
                # sinon ping-pong infini 4<->5 quand le bas est épuisé.
                viable = [
                    p
                    for p in level.stairs_down
                    if not (
                        (dest := level.down_outcomes.get(p)) in self.levels
                        and self.levels[dest].exhausted
                        and not self.levels[dest].stairs_down
                    )
                ]
                if viable:
                    point = min(
                        viable,
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

        # ---- Donjon principal ----
        # Phase 1 (descente rapide) : descendre tout escalier non testé dès
        # qu'il est vu ; l'arrivée nous dit si c'était la branche des Mines.
        # Phase 2 (retour, branch_backtracking) : après dépassement au niveau
        # 5, remonter et fouiller sérieusement les niveaux 2-4.
        def nearest(points: set[Point]) -> Point:
            return min(
                points,
                key=lambda p: abs(p[0] - self.position[0])
                + abs(p[1] - self.position[1]),
            )

        attempted_here = {
            point for key, point in self.attempted_down if key == self.current_key
        }
        known_main = {
            point
            for point, dest in level.down_outcomes.items()
            if dest[0] == 0
        }
        untested = level.stairs_down - attempted_here - known_main

        if dlevel >= 5:
            self.branch_backtracking = True
            if not level.stairs_up and int(level.visits.sum()) < 20:
                level.stairs_up.add(self.position)
            if level.stairs_up:
                action = self._go_stair(
                    level, nearest(level.stairs_up), blocked, down=False
                )
                if action is not None:
                    return action
            return self._explore(level, blocked, thorough=False)

        if dlevel == 1:
            # Le niveau 1 ne peut pas contenir la branche : descendre.
            if level.stairs_down:
                action = self._go_stair(
                    level, nearest(level.stairs_down), blocked, down=True
                )
                if action is not None:
                    return action
            action = self._inspect_objects(level, blocked)
            if action is not None:
                return action
            action = self._explore(level, blocked, thorough=False)
            if action is not None:
                return action
            if not level.stairs_down and level.escalation < 3:
                level.escalation += 1
                level.exhausted = False
                return self._explore(level, blocked, thorough=True)
            return None

        # dlevel 2..4
        if not self.branch_backtracking:
            if untested:
                action = self._go_stair(level, nearest(untested), blocked, down=True)
                if action is not None:
                    return action
            # Frontière limitée dès qu'un escalier est connu : descendre vite,
            # la fouille sérieuse n'arrive qu'en phase retour.
            action = self._explore(
                level,
                blocked,
                thorough=False,
                do_search=not level.stairs_down,
                unknown_cap=120 if level.stairs_down else 320,
            )
            if action is not None:
                return action
            if not level.stairs_down:
                action = self._inspect_objects(level, blocked)
                if action is not None:
                    return action
                if level.escalation < 2:
                    level.escalation += 1
                    level.exhausted = False
                    return self._explore(level, blocked, thorough=True)
            if level.stairs_down:
                action = self._go_stair(
                    level, nearest(level.stairs_down), blocked, down=True
                )
                if action is not None:
                    return action
            return None

        # Phase retour : chasse à la branche cachée sur ce niveau.
        action = self._inspect_objects(level, blocked)
        if action is not None:
            return action
        action = self._explore(level, blocked, thorough=True)
        if action is not None:
            return action
        if untested:
            action = self._go_stair(level, nearest(untested), blocked, down=True)
            if action is not None:
                return action
        if dlevel > 2 and level.stairs_up:
            action = self._go_stair(
                level, nearest(level.stairs_up), blocked, down=False
            )
            if action is not None:
                return action
        if dlevel == 2:
            # Balayage 2-4 terminé sans branche : réarmer avec plus de budget
            # et redescendre par l'escalier principal connu.
            for candidate in self.levels.values():
                if candidate.key[0] == 0 and 2 <= candidate.key[1] <= 4:
                    candidate.escalation = min(candidate.escalation + 1, 6)
                    candidate.exhausted = False
            if known_main:
                action = self._go_stair(
                    level, nearest(known_main), blocked, down=True
                )
                if action is not None:
                    return action
        return None

    def _unstick(self, level: LevelState, blocked: set[Point]) -> int | None:
        """Après une longue attente derrière un pacifique, bouger ailleurs."""

        assert self.position is not None
        if self.blocked_streak < 30:
            return None
        # Un pacifique campe le passage : à 60 steps on attaque les animaux,
        # à 150 n'importe quel pacifique sauf le personnel de ville (coût
        # d'alignement mineur, très inférieur à un step_timeout garanti).
        if self.blocked_streak >= 60 and self.latest_obs is not None:
            creatures, pets = self._creatures(self.latest_obs)
            for delta in DIRECTIONS:
                point = add(self.position, delta)
                if point not in blocked or point in pets:
                    continue
                name = creatures.get(point, "")
                if not name or name in PASSIVE_DANGER_NAMES:
                    continue
                town_staff = name in (
                    "shopkeeper",
                    "watchman",
                    "watch captain",
                    "guard",
                    "aligned priest",
                    "high priest",
                )
                if town_staff:
                    continue
                if name not in FORCE_ATTACK_ANIMALS and self.blocked_streak < 150:
                    continue
                if delta[0] and delta[1]:
                    here = int(level.terrain[self.position])
                    there = int(level.terrain[point])
                    if here in DOOR_TILES or there in DOOR_TILES:
                        continue
                self.force_attack_step = self.steps
                self.failure_hint = f"combat:{name}"
                return self._move(level, point, "melee_forced")
        # Oublier la cible de patrouille : elle est peut-être injoignable
        # uniquement à cause du pacifique immobile.
        self.patrol_targets.pop(level.key, None)
        if self.blocked_streak % 4 == 3:
            passable = level.passable_mask(blocked=blocked, avoid_traps=True)
            candidates = [
                point
                for point in neighbors(self.position, diagonals=False)
                if inside(point, level.shape) and passable[point]
            ]
            if candidates:
                point = min(candidates, key=lambda p: int(level.visits[p]))
                return self._move(level, point, "unstick_sidestep")
        if self.blocked_streak >= 80 and self.latest_obs is not None:
            action = self._dig_escape(self.latest_obs, level, blocked)
            if action is not None:
                return action
        if self.blocked_streak >= 120 and self.steps - self.last_evade_step > 400:
            # Changer de niveau par n'importe quel escalier accessible : les
            # monstres se redistribuent et le blocage local disparaît souvent.
            stairs = set(level.stairs_down)
            if self.current_key != (0, 1):
                # L'escalier montant du niveau 1 sort du donjon (refusé), il
                # provoquait une boucle ascend/decline infinie.
                stairs |= level.stairs_up
            for point in sorted(
                stairs,
                key=lambda p: abs(p[0] - self.position[0])
                + abs(p[1] - self.position[1]),
            ):
                action = self._go_stair(
                    level, point, blocked, down=point in level.stairs_down
                )
                if action is not None:
                    self.last_evade_step = self.steps
                    self.action_counts["evade_level"] += 1
                    return action
        if self.blocked_streak >= 200:
            # Désespoir : retenter les sondes (des passages ont pu s'ouvrir,
            # les failed_edges restent car ce sont de vrais murs).
            level.probe_attempts.clear()
            level.unknown_attempts = 0
            level.exhausted = False
            self.blocked_streak = 0
            self.action_counts["desperation_reset"] += 1
        return None

    def act(self, obs: dict[str, np.ndarray]) -> int:
        level = self._observe(obs)
        prompt_action = self._prompt(obs)
        if prompt_action is not None:
            return prompt_action

        if self.pending:
            raw, label = self.pending.popleft()
            return self._emit(raw, label)

        if self.incapacitated:
            return self._emit(int(nethack.MiscDirection.WAIT), "wait_incapacitated")

        self.normal_turns += 1
        creatures, pets = self._creatures(obs)
        if any(name == "shopkeeper" for name in creatures.values()):
            self.shopkeeper_levels.add(self.current_key)
        self.visible_hostiles = {
            point: name
            for point, name in creatures.items()
            if point not in pets and self._is_hostile(name)
        }
        blocked = {
            point
            for point, name in creatures.items()
            if (
                name in PASSIVE_DANGER_NAMES
                or name in self.forced_peaceful_names
                or (name in PEACEFUL_DWARF_NAMES and name not in self.hostile_names)
            )
        } - pets
        # Boutiques : rester à distance des shopkeepers (vol involontaire,
        # portes, colères = morts assurées à bas niveau).
        for point, name in creatures.items():
            if name == "shopkeeper":
                for dy in range(-4, 5):
                    for dx in range(-4, 5):
                        tile = (point[0] + dy, point[1] + dx)
                        if inside(tile, level.shape):
                            blocked.add(tile)
        blocked.discard(self.position)
        self.current_blocked = blocked

        action = self._emergency(obs)
        if action is not None:
            self.blocked_streak = 0
            return action

        action = self._adjacent_combat(obs, level, creatures, pets)
        if action is not None:
            self.blocked_streak = 0
            return action

        action = self._survival(obs, level)
        if action is not None:
            self.blocked_streak = 0
            return action

        if self.fetch_hold > self.steps:
            action = self._fetch_projectile(level, blocked)
            if action is not None:
                return action
            self.fetch_hold = -1

        action = self._map_level(obs)
        if action is not None:
            self.blocked_streak = 0
            return action

        action = self._try_excalibur(obs, level)
        if action is not None:
            self.blocked_streak = 0
            return action

        action = self._objective(obs, level, blocked)
        if action is not None:
            # Les actions de pur déplacement ne prouvent aucun progrès : sans
            # cette distinction, une oscillation sur place remettait le
            # compteur à zéro et l'évasion de niveau ne partait jamais.
            label = self.trail[-1][1] if self.trail else ""
            if label not in (
                "explore_path",
                "search_path",
                "go_to_stair",
                "inspect_object_path",
                "patrol_mapped_mines",
                "fetch_projectile",
                "go_to_corpse",
                "tunnel_path",
            ):
                self.blocked_streak = 0
            return action

        # Des pacifiques occupent parfois le seul couloir.  Attendre est plus
        # sûr qu'attaquer, mais après une longue attente on se débloque par
        # pas de côté (le pacifique avance) ou creusage.
        self.blocked_streak += 1
        action = self._unstick(level, blocked)
        if action is not None:
            return action
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
            "blocked_streak": self.blocked_streak,
            "attempted_down": [
                [
                    [int(key[0]), int(key[1])],
                    [int(point[0]), int(point[1])],
                ]
                for key, point in sorted(self.attempted_down)
            ],
            "actions": dict(self.action_counts),
            "trail": [
                [step, label, hp, list(key) if key else None, list(pos) if pos else None]
                for step, label, hp, key, pos in self.trail
            ],
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
