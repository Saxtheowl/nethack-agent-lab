"""Valkyrie -> Minetown strategy."""
import re
import time

from game import Game, GameOver, ESC, CTRL_D
from level import Level, DIRS, MONSTER_CHARS, melee_ok, W, H

SAFE_NAMES = (
    r"newt|gecko|jackal|fox|coyote|sewer rat|giant rat|gnome lord|gnome|hobbit|"
    r"hill orc|Mordor orc|Uruk-hai|orc|rock piercer|giant ant|lichen|red mold|woodchuck|"
    r"rothe|floating eye|dingo|wolf|warg|jaguar|panther|housecat|kitten|pony|horse"
)
SAFE_CORPSES = re.compile(r"\b(" + SAFE_NAMES + r")\b.*corpse")
SAFE_KILL = re.compile(r"You (?:kill|destroy) the (" + SAFE_NAMES + r")\b")
FOOD_HERE = re.compile(
    r"You see here (a|an|some|\d+) (food rations?|cram rations?|lembas wafers?|apples?|oranges?|"
    r"pears?|melons?|bananas?|carrots?|slime molds?|candy bars?|fortune cookies?|pancakes?|"
    r"tin of|lichen corpse)"
)

# mindless monsters can't read Elbereth; most are also slow -> walk away
MINDLESS = set("PZFbjy")

BRANCH_DOOM = "Doom"
BRANCH_MINES = "Mines"
BRANCH_SOKOBAN = "Sokoban"
BRANCH_OTHER = "Other"


class Abort(Exception):
    pass


def expand_letter_ranges(s):
    """'d-gI' -> ['d','e','f','g','I']"""
    out = []
    i = 0
    while i < len(s):
        if i + 2 < len(s) and s[i + 1] == "-" and s[i + 2].isalpha():
            out.extend(chr(c) for c in range(ord(s[i]), ord(s[i + 2]) + 1))
            i += 3
        elif s[i].isalpha():
            out.append(s[i])
            i += 1
        else:
            i += 1
    return out


class Brain:
    def __init__(self, game: Game, log=print):
        self.g = game
        self.log = log
        self.levels = {}
        self.branch = BRANCH_DOOM
        self.dlvl = 1
        self.level = self._level(self.branch, 1)
        self.hero = None
        self.turn = 0
        self.last_pray_turn = -2000
        self.last_elbereth_turn = -2000
        self.elbereth_waits = 0
        self.pray_count = 0
        self.food_letters = []
        self.dagger_letter = None
        self.weapon_letter = None
        self.long_sword_letter = None
        self.spear_letter = None
        self.excalibur = False
        self.fountain_dips = 0
        self.rewield_letter = None  # weapon we threw and must pick up + wield
        self.mines_hunt = False
        self.mines_up_hunt = False
        self.success = False
        self.state = "explore"
        self.ticks = 0
        self.last_progress_tick = 0
        self.last_positions = []
        self.pending_corpse_eat = False
        self.pending_eat = None   # ((x,y), turn) of a safe corpse to go eat
        self.kill_sites = {}      # (x,y) -> turn of our last kill there
        self.corpse_sites = {}    # (x,y) -> turn we saw a corpse there
        self.shop_level = False   # heard shop sounds on current level
        self.last_stair_used = None
        self.arrived_via = None
        self.search_budget = 0
        self.no_eat_until = -1
        self.level_arrival_turn = 0
        self.last_perturb_tick = -1000
        self.nav_target = None    # sticky exploration target (kind, pos, tick)
        self.under_attack_until = -1
        self.hostile_human_until = -1
        self.minetown_key = None

    # ---------- helpers ----------

    def _level(self, branch, dlvl):
        key = (branch, dlvl)
        if key not in self.levels:
            self.levels[key] = Level(key)
        return self.levels[key]

    def sync(self, snap=None):
        snap = snap or self.g.pump()
        snap = self.g.maybe_dismiss_prompt(snap)
        if snap.status is None:
            # status line not parseable (overlay?) -> try escape
            self.g.sess.send(ESC)
            snap = self.g.pump()
            if snap.status is None:
                raise Abort("status unparseable")
        st = snap.status
        self.turn = st.turn
        if st.dlvl != self.dlvl:
            self.on_new_level(st.dlvl)
            snap = self.g.pump()
        # the cursor sits on the hero during normal play; it must be in the map area
        from game import CTRL_R
        for _ in range(3):
            cx, cy = snap.cursor
            if 1 <= cy <= 21 and 0 <= cx < W:
                self.hero = (cx, cy - 1)
                break
            self.g.sess.send(CTRL_R)
            snap = self.g.pump()
        else:
            if self.hero is None:
                raise Abort("cannot locate hero on screen")
            self.log(f"[sync] cursor off-map (cursor={snap.cursor}); keeping hero={self.hero}")
        if self.arrived_via == "down":
            self.level.stairs_up.add(self.hero)   # we are standing on the up stairs
            self.arrived_via = None
        elif self.arrived_via == "up":
            self.level.stairs_down.add(self.hero)
            self.arrived_via = None
        self.level.visited.add(self.hero)
        self.level.update_from_snap(snap, self.hero)
        return snap

    def on_new_level(self, new_dlvl):
        prev_level, prev_stair = self.level, self.last_stair_used
        self._prev_dlvl = self.dlvl
        branch = self.parse_branch()
        if branch == BRANCH_OTHER:
            branch = self.parse_branch()  # overview read may have raced: retry
        if branch == BRANCH_OTHER and new_dlvl <= 10:
            # almost certainly a misparse this early: keep the previous branch
            self.log(f"[lvl] overview parse gave Other at dlvl {new_dlvl}; keeping {self.branch}")
            branch = self.branch
        self.dlvl = new_dlvl
        self.branch = branch
        self.level = self._level(branch, new_dlvl)
        if branch != BRANCH_MINES:
            self.mines_up_hunt = False
        if branch == BRANCH_SOKOBAN and prev_stair and prev_stair[0] == "up":
            prev_level.tried_up.add(prev_stair[1])
        self.arrived_via = prev_stair[0] if prev_stair else None
        if (prev_stair is None and branch == BRANCH_MINES
                and new_dlvl > getattr(self, "_prev_dlvl", 1) + 1):
            # fell through a hole: the town may be on the skipped levels
            self.log(f"[lvl] fell into Mines:{new_dlvl}: will climb back to look for the town")
            self.mines_up_hunt = True
        self.last_stair_used = None
        self.shop_level = False
        self.kill_sites = {}
        self.corpse_sites = {}
        self.level_arrival_turn = self.turn
        self.nav_target = None
        self.log(f"[lvl] arrived branch={branch} dlvl={new_dlvl} T={self.turn}")

    def parse_branch(self):
        lines = self.g.overview()
        branch = BRANCH_DOOM
        cur = None
        for raw in lines:
            line = raw.strip()
            if "Dungeons of Doom" in line:
                cur = BRANCH_DOOM
            elif "Gnomish Mines" in line:
                cur = BRANCH_MINES
            elif "Sokoban" in line:
                cur = BRANCH_SOKOBAN
            elif re.search(r"^\S.*:", line) and "Level" not in line:
                cur = BRANCH_OTHER
            if "you are here" in line.lower() and cur:
                branch = cur
        return branch

    # ---------- prompts ----------

    def handle_prompt(self, snap):
        """Answer an unexpected [yn]-ish prompt conservatively. Returns new snap."""
        msg = snap.lines[0]
        if "Really attack" in msg and "peaceful" in msg:
            snap2 = self.g.answer("n")
            return snap2
        if "eat it?" in msg or "; eat" in msg:
            return self.g.answer("n")
        if "Really quit" in msg:
            return self.g.answer("n")
        if "Shall I remove" in msg or "force its lock" in msg:
            return self.g.answer("n")
        if "What do you want" in msg or "don't have that object" in msg:
            return self.g.answer(ESC)
        if snap.ynq:
            # default: refuse / escape
            if "q" in (snap.ynq or ""):
                return self.g.answer("q")
            return self.g.answer(ESC)
        return snap

    # ---------- actions ----------

    def step_dir(self, dxdy):
        key = DIRS[dxdy]
        before_pos, before_turn = self.hero, self.turn
        snap = self.g.cmd(key)
        # peaceful-attack confirmation?
        if snap.ynq and "Really attack" in snap.lines[0]:
            snap = self.g.answer("n")
            tx, ty = self.hero[0] + dxdy[0], self.hero[1] + dxdy[1]
            t = self.level.tile(tx, ty)
            t.peaceful_until = self.turn + 150
            t.denied_until = self.turn + 150
            if t.char == "@":
                self.hostile_human_until = -1  # that @ is peaceful: stand down
            return snap
        # hazard confirmations (traps, vapor clouds...)
        if snap.ynq and ("Really step" in snap.lines[0] or "vapor cloud" in snap.lines[0]
                         or "into that" in snap.lines[0]):
            msg = snap.lines[0]
            tx, ty = self.hero[0] + dxdy[0], self.hero[1] + dxdy[1]
            benign = re.search(r"falling rock|dart trap|arrow trap|squeaky board|"
                               r"rust trap", msg)
            if benign:
                return self.g.answer("y")
            t = self.level.tile(tx, ty) if (0 <= tx < W and 0 <= ty < H) else None
            if t is not None and "cloud" in msg:
                t.wait_count += 1
                if t.wait_count > 3:
                    return self.g.answer("y")  # persistent cloud on the only path
            snap = self.g.answer("n")
            if t is not None:
                if "trap" in msg:
                    t.trap = True   # permanent avoid (fallback pathing may cross)
                else:
                    t.peaceful_until = self.turn + 50  # cloud: dissipates
            return snap
        for m in self.g.turn_messages:
            if "statue" in m:
                tx2, ty2 = before_pos[0] + dxdy[0], before_pos[1] + dxdy[1]
                if 0 <= tx2 < W and 0 <= ty2 < H:
                    self.level.tile(tx2, ty2).statue = True
        # silent failure: no movement, no time, no meaningful message
        meaningful = [m for m in self.g.turn_messages
                      if not re.match(r"You hear|You smell|You feel the", m)]
        if (snap.status and snap.status.turn == before_turn
                and snap.cursor == (before_pos[0], before_pos[1] + 1)
                and not meaningful):
            tx, ty = before_pos[0] + dxdy[0], before_pos[1] + dxdy[1]
            if 0 <= tx < W and 0 <= ty < H:
                t = self.level.tile(tx, ty)
                if t.char in MONSTER_CHARS:
                    # phantom monster glyph (overlay junk in memory)
                    t.phantom += 1
                    if t.phantom == 2:
                        from game import CTRL_R
                        self.log(f"[phantom] ghost '{t.char}' at {(tx, ty)}: redraw + permanent ignore")
                        self.g.sess.send(CTRL_R)
                        self.g.pump()
                else:
                    # impassable edge (e.g. diagonal through a doorway, !cmdassist
                    # suppresses the explanation): ban it for the pathfinder
                    self.level.ban_edge(before_pos, (tx, ty), self.turn)
        return snap

    def move_along(self, path):
        """Take one step toward path[0]."""
        nx, ny = path[0]
        dx, dy = nx - self.hero[0], ny - self.hero[1]
        t = self.level.tile(nx, ny)
        if t.char in MONSTER_CHARS and t.peaceful_until > self.turn:
            self.wait_or_force((nx, ny), t)
            return self.g.pump()
        if t.char == "+" and t.fg in ("brown", "yellow"):
            return self.open_door((nx, ny), (dx, dy))
        before_pos, before_turn = self.hero, self.turn
        snap = self.step_dir((dx, dy))
        for m in self.g.turn_messages:
            if "door is locked" in m:
                self.level.tile(nx, ny).door_locked = True
            if "You kill" in m or "You destroy" in m:
                self.kill_sites[(nx, ny)] = self.turn
            if re.search(r"You see here .* corpse", m):
                self.corpse_sites[(nx, ny)] = self.turn
            if "statue" in m:
                self.level.tile(nx, ny).statue = True
            if "Closed for inventory" in m:
                # shop door warning: never touch the doors around here
                for ddx in (-1, 0, 1):
                    for ddy in (-1, 0, 1):
                        x2, y2 = nx + ddx, ny + ddy
                        if 0 <= x2 < W and 0 <= y2 < H:
                            t2 = self.level.tile(x2, y2)
                            if t2.char == "+":
                                t2.hard_ban = True
            if "cursing shoplifters" in m or "You hear the chime of a cash register" in m:
                self.shop_level = True
            if "is in the way" in m:
                self.level.tile(nx, ny).peaceful_until = self.turn + 100
            if "you can't see" in m or "something there" in m:
                # invisible monster: avoid the tile a while
                self.level.tile(nx, ny).peaceful_until = self.turn + 100
            if ("but in vain" in m or "You cannot pass" in m or "won't budge" in m
                    or "diagonal" in m or "solid stone" in m or "bump into a wall" in m
                    or "carrying too much" in m or "cannot move it" in m
                    or "behind the boulder" in m or "stuck here" in m):
                self.level.ban_edge(before_pos, (nx, ny), self.turn, amount=3)
        # silent failure: no movement, no time passed, no meaningful message -> ban edge
        meaningful = [m for m in self.g.turn_messages
                      if not re.match(r"You hear|You smell|You feel the", m)]
        if (snap.status and snap.status.turn == before_turn
                and snap.cursor == (before_pos[0], before_pos[1] + 1)
                and not meaningful):
            self.level.ban_edge(before_pos, (nx, ny), self.turn)
        return snap

    def open_door(self, pos, dxdy):
        t = self.level.tile(*pos)
        if t.door_locked:
            if self.shop_level and not self.level.desperate:
                # could be a closed shop: kicking it means death by shopkeeper.
                # hard-ban it; the desperation phase will unban if we get stuck.
                self.log(f"[door] locked door at {pos} on a shop level: hard ban (for now)")
                t.hard_ban = True
                self.level.shop_doors.add(pos)
                return self.g.cmd("ms")
            # kick it
            snap = self.g.cmd(CTRL_D)
            if "direction" in snap.lines[0].lower() or "In what direction" in snap.lines[0]:
                snap = self.g.answer(DIRS[dxdy])
            t.kick_count += 1
            for m in self.g.turn_messages:
                if "crashes open" in m or "The door opens" in m:
                    t.door_locked = False
            if t.kick_count > 25:
                # give up on this door
                t.hard_ban = True
            return snap
        # autoopen: walk into it
        snap = self.step_dir(dxdy)
        for m in self.g.turn_messages:
            if "door is locked" in m:
                t.door_locked = True
        return snap

    def pray(self):
        self.log(f"[pray] T={self.turn} hp low or weak (count={self.pray_count})")
        snap = self.g.cmd("#pray\n")
        if snap.ynq:
            snap = self.g.answer("y")
        self.last_pray_turn = self.turn
        self.pray_count += 1
        msgs = " ".join(self.g.turn_messages)
        if re.search(r"displeased|angry|angers|thunder|wrath|disgusted|arrogant|"
                     r"feel guilty|black cloud|relearn", msgs):
            self.log("[pray] god is upset: no more prayers this game")
            self.pray_count = 99
        return snap

    def engrave_elbereth(self):
        self.log(f"[elbereth] engraving at {self.hero} T={self.turn}")
        snap = self.g.cmd("E")
        for _ in range(6):
            msg = snap.lines[0]
            if "What do you want to write with" in msg or "write with" in msg:
                snap = self.g.answer("-")
            elif "add to the current engraving" in msg:
                snap = self.g.answer("n")
            elif "write in the dust" in msg or "What do you want to write" in msg:
                snap = self.g.answer("Elbereth\n")
                break
            elif snap.ynq:
                snap = self.g.answer(ESC)
                break
            else:
                break
        return self.g.pump()

    def excalibur_step(self):
        """Walk to a fountain and #dip the long sword (lawful XL5+ -> Excalibur)."""
        lv = self.level
        fountains = [(x, y) for y in range(H) for x in range(W)
                     if lv.tiles[y][x].char == "{"]
        if not fountains:
            return False
        if self.hero in fountains:
            self.fountain_dips += 1
            self.log(f"[excalibur] dip #{self.fountain_dips} T={self.turn}")
            snap = self.g.cmd("#dip\n")
            if "What do you want to dip" in snap.lines[0]:
                snap = self.g.answer(self.long_sword_letter)
            if snap.ynq and ("into the fountain" in snap.lines[0]
                             or "Dip" in snap.lines[0]):
                snap = self.g.answer("y")
            msgs = " ".join(self.g.turn_messages)
            if "hand reaches up" in msgs or "Excalibur" in msgs:
                self.log("[excalibur] OBTAINED! wielding it")
                self.excalibur = True
                snap = self.g.cmd("w")
                if "What do you want to wield" in snap.lines[0]:
                    self.g.answer(self.long_sword_letter)
                    self.weapon_letter = self.long_sword_letter
            if "dries up" in msgs or "dry" in msgs:
                lv.tiles[self.hero[1]][self.hero[0]].char = "."
            return True
        path = lv.path_to(self.hero, set(fountains), self.turn)
        if path:
            self.move_along(path)
            return True
        return False

    def enhance_skills(self):
        """#enhance any advancable weapon skill (free to-hit/damage)."""
        for _ in range(3):
            self.g.turn_messages = []
            self.g.sess.send("#enhance\n")
            lines = self.g.read_fullscreen()
            letter = None
            for line in lines:
                m = re.match(r"\s*([a-z]) - +\S", line)
                if m:
                    letter = m.group(1)
                    break
            if not letter:
                break
            self.log(f"[enhance] advancing skill '{letter}'")
            self.g.sess.send(letter)
            self.g.pump()
        self.g.maybe_dismiss_prompt(self.g.pump())

    def eat_from_inventory(self):
        if self.turn < self.no_eat_until:
            return False
        snap = self.g.cmd("e")
        if re.search(r"don't have anything( else)? to eat", " ".join(self.g.turn_messages)):
            self.no_eat_until = self.turn + 150
            return False
        msg = snap.lines[0]
        if "eat it?" in msg or "; eat" in msg:
            if "lichen corpse" in msg:  # lichen never rots: always safe
                self.g.answer("y")
                return True
            snap = self.g.answer("n")
            msg = snap.lines[0]
        if "What do you want to eat" not in msg:
            self.g.maybe_dismiss_prompt(self.g.pump())
            return False
        # the prompt lists the valid comestible letters: trust it
        m = re.search(r"\[([a-zA-Z-]+)", msg)
        valid = expand_letter_ranges(m.group(1)) if m else []
        if not valid:
            self.g.answer(ESC)
            return False
        letter = self.food_letters[0] if (self.food_letters
                                          and self.food_letters[0] in valid) else valid[0]
        snap = self.g.answer(letter)
        msgs = " ".join(self.g.turn_messages)
        if "cannot eat that" in msgs or "don't have that object" in msgs:
            if letter in self.food_letters:
                self.food_letters.remove(letter)
            self.g.maybe_dismiss_prompt(self.g.pump())
            return False
        return True

    def _own_fresh_corpse(self, pos):
        """Corpse seen at pos AND we killed something there recently."""
        seen = self.corpse_sites.get(pos)
        killed = self.kill_sites.get(pos)
        return (seen is not None and killed is not None
                and self.turn - killed <= 25 and self.turn - seen <= 25)

    def fresh_kill_site(self):
        """Nearest corpse from our own recent kill."""
        best = None
        for pos in list(self.corpse_sites):
            if self.turn - self.corpse_sites[pos] > 25:
                del self.corpse_sites[pos]
                continue
            if not self._own_fresh_corpse(pos):
                continue
            d = max(abs(pos[0] - self.hero[0]), abs(pos[1] - self.hero[1]))
            if d <= 6 and (best is None or d < best[0]):
                best = (d, pos)
        return best[1] if best else None

    def try_eat_corpse_here(self):
        """If we're standing on our own fresh kill's corpse, eat it."""
        if not self._own_fresh_corpse(self.hero):
            return False
        self.corpse_sites.pop(self.hero, None)  # one attempt only
        self.kill_sites.pop(self.hero, None)
        return self.eat_floor_corpse()

    def eat_floor_corpse(self):
        """'e' on the current tile, accepting only safe corpses."""
        snap = self.g.cmd("e")
        msg = snap.lines[0]
        if ("eat it?" in msg or "; eat" in msg) and snap.ynq:
            if SAFE_CORPSES.search(msg) and "dwarf" not in msg:
                self.g.answer("y")
                return True
            snap = self.g.answer("n")
            msg = snap.lines[0]
        if "What do you want to eat" in msg:
            self.g.answer(ESC)
        return False

    def pickup_food(self):
        msgs = " ".join(self.g.turn_messages)
        want_dagger = self.dagger_letter is None and re.search(
            r"You see here an? (\+\d+ )?(blessed |uncursed |cursed )?dagger", msgs)
        want_weapon = self.rewield_letter and re.search(
            r"You see here an? .*(spear|long sword)", msgs)
        if want_weapon:
            snap = self.g.cmd(",")
            if self.g.in_menu(snap):
                self.g.sess.send(ESC)
                self.g.pump()
            for m in self.g.turn_messages:
                m2 = re.match(r"([a-zA-Z]) - .*(spear|long sword)", m)
                if m2:
                    self.log(f"[wield] recovering thrown weapon '{m2.group(1)}'")
                    self.weapon_letter = m2.group(1)
                    self.rewield_letter = None
                    snap = self.g.cmd("w")
                    if "What do you want to wield" in snap.lines[0]:
                        self.g.answer(m2.group(1))
                    return
        if FOOD_HERE.search(msgs) or want_dagger:
            snap = self.g.cmd(",")
            if self.g.in_menu(snap):
                self.g.sess.send(ESC)
                self.g.pump()
                return
            for m in self.g.turn_messages:
                m2 = re.match(r"([a-zA-Z]) - (.*)", m)
                if not m2:
                    continue
                if re.search(r"ration|wafer|apple|orange|pear|melon|banana|carrot|"
                             r"slime mold|candy|cookie|pancake", m2.group(2)):
                    self.food_letters.append(m2.group(1))
                if "dagger" in m2.group(2) and self.dagger_letter is None:
                    self.dagger_letter = m2.group(1)

    # ---------- combat ----------

    def adjacent_monsters(self, snap):
        out = []
        hx, hy = self.hero
        # if something just hit us, stale tile marks must not hide the attacker
        attacked = self.turn <= self.under_attack_until
        for (dx, dy) in DIRS:
            x, y = hx + dx, hy + dy
            if not (0 <= x < W and 0 <= y < H):
                continue
            t = self.level.tile(x, y)
            if t.char == "@" and self.turn > self.hostile_human_until:
                continue  # shopkeeper/priest/watchman: never initiate
            if t.phantom >= 2 or t.statue:
                continue  # corrupted memory cell / statue glyph
            if t.char not in MONSTER_CHARS:
                continue
            if t.peaceful_until > self.turn:
                if not attacked or t.denied_until > self.turn:
                    continue
            out.append(((dx, dy), t.char, t.fg))
        return out

    def fight(self, adj):
        # attack the first melee-safe adjacent monster
        for (dxdy, ch, fg) in adj:
            if melee_ok(ch, fg):
                if self.ticks % 10 == 0:
                    self.log(f"[fight] {ch} ({fg}) dir={dxdy} at T={self.turn}")
                tx = self.hero[0] + dxdy[0]
                ty = self.hero[1] + dxdy[1]
                snap = self.step_dir(dxdy)
                for m in self.g.turn_messages:
                    if "You kill" in m or "You destroy" in m:
                        self.kill_sites[(tx, ty)] = self.turn
                        if SAFE_KILL.search(m):
                            self.pending_eat = ((tx, ty), self.turn, self.ticks)
                return True
        return False

    # ---------- goal logic ----------

    def town_features(self):
        if self.branch != BRANCH_MINES:
            return []
        lv = self.level
        feats = [(x, y) for y in range(H) for x in range(W)
                 if lv.tiles[y][x].char in "{_"]
        feats.extend(lv.doors_seen)
        return feats

    def town_detected(self):
        if self.branch != BRANCH_MINES:
            return False
        lv = self.level
        feats = self.town_features()
        fountains = sum(1 for x, y in feats if lv.tiles[y][x].char == "{")
        altars = sum(1 for x, y in feats if lv.tiles[y][x].char == "_")
        if len(lv.doors_seen) >= 2 or fountains >= 1 or altars >= 1:
            return True
        return False

    def stairs_to_try(self):
        """Down stairs on this level not yet known to be wrong."""
        return [s for s in self.level.stairs_down if s not in self.level.tried_down]

    # ---------- main tick ----------

    def tick(self):
        self.ticks += 1
        snap = self.sync()
        if self.ticks % 100 == 0:
            st = snap.status
            self.log(f"[tick {self.ticks}] T={st.turn} {self.branch}:{self.dlvl} "
                     f"pos={self.hero} hp={st.hp}/{st.hpmax} xp={st.xp} state={self.state}")
        if self.ticks % 400 == 0:
            self.dump_map()
        # --- anti-stuck watchdog ---
        self.last_positions.append((self.hero, self.turn))
        if len(self.last_positions) > 300:
            self.last_positions.pop(0)
        if len(self.last_positions) >= 30 and len(set(self.last_positions[-30:])) == 1:
            self.log(f"[watchdog] no progress for 30 ticks at {self.hero} T={self.turn}, recovering")
            try:
                lv = self.level
                fpath = lv.frontier_path(self.hero, self.turn)
                fpath2 = lv.frontier_path(self.hero, self.turn, ignore_monsters=True)
                probes = lv.probe_targets(self.hero, self.turn)
                goal = self.pick_goal()
                self.log(f"[diag] frontier={fpath[:3] if fpath else None} "
                         f"frontier_ign={fpath2[:3] if fpath2 else None} "
                         f"probes={len(probes)} goal={goal} "
                         f"down={lv.stairs_down} up={lv.stairs_up} "
                         f"bans={len(lv.blocked_edges)} adj={self.adjacent_monsters(self.g.pump())}")
            except Exception as e:
                self.log(f"[diag] failed: {e}")
            self.recover()
            return
        if (len(self.last_positions) >= 250
                and len({p for p, _ in self.last_positions[-250:]}) == 1):
            raise Abort("position frozen 250 ticks")
        if (self.ticks - self.last_perturb_tick > 150
                and len(self.last_positions) >= 120
                and len({p for p, _ in self.last_positions[-120:]}) <= 3):
            self.log(f"[watchdog] oscillation around {self.hero}: random perturbation")
            self.last_perturb_tick = self.ticks
            import random
            for _ in range(6):
                opts = [d for d in DIRS
                        if 0 <= self.hero[0] + d[0] < W and 0 <= self.hero[1] + d[1] < H
                        and self.level.walkable(self.hero[0] + d[0], self.hero[1] + d[1],
                                                self.hero, self.turn)]
                if not opts:
                    break
                self.step_dir(random.choice(opts))
                self.sync()
            self.last_positions.clear()
            return
        if snap.ynq:
            snap = self.handle_prompt(snap)
            snap = self.sync(snap)
        st = snap.status
        for m in self.g.turn_messages:
            if re.search(r"The \w[\w ]* (bites|hits|kicks|butts|stings)!", m):
                self.under_attack_until = self.turn + 3
            if re.search(r"The \S*were\S* (hits|bites|misses|just misses|summons)", m):
                self.hostile_human_until = self.turn + 25

        # --- umbrella safety: too long on one level means we're looping ---
        cap = 5000 if not self.level.stairs_down else 3000
        if self.turn - self.level_arrival_turn > cap:
            raise Abort(f"level timeout on {self.branch}:{self.dlvl}")

        # --- success check: must actually WALK INTO the town ---
        if self.town_detected():
            feats = self.town_features()
            dist = min(max(abs(self.hero[0] - x), abs(self.hero[1] - y))
                       for x, y in feats)
            if dist <= 3:
                self.log(f"[GOAL] Minetown ENTERED! branch={self.branch} dlvl={self.dlvl} "
                         f"T={self.turn} dist={dist}")
                self.success = True
                return
            # walk toward the town
            path = self.level.path_to(self.hero, set(feats), self.turn, adjacent=True)
            if path:
                self.move_along(path)
                return
            path = self.level.path_to(self.hero, set(feats), self.turn,
                                      adjacent=True, ignore_monsters=True)
            if path:
                nx, ny = path[0]
                t = self.level.tile(nx, ny)
                if t.char in MONSTER_CHARS or t.peaceful_until > self.turn:
                    if t.peaceful_until > self.turn:
                        self.wait_or_force((nx, ny), t)
                    else:
                        self.handle_blocker((nx, ny), t)
                    return
                self.move_along(path)
                return
            # no path yet: keep exploring (fall through)

        # --- emergencies ---
        hp_frac = st.hp / max(1, st.hpmax)
        adj = self.adjacent_monsters(snap)
        pray_ok = (self.turn - self.last_pray_turn) > 550 and self.pray_count < 10
        # prayer only helps when the god agrees we're in trouble: hp <= max/7
        if (hp_frac <= 1 / 7 or st.hp < 6) and pray_ok:
            self.pray()
            return
        # Elbereth early: it scares most of the early-game threats
        if adj and (hp_frac < 0.35 or (hp_frac < 0.45 and len(adj) >= 2)):
            readers = [a for a in adj if a[1] not in MINDLESS]
            if not readers:
                # mindless attackers ignore Elbereth; they're slow: step away
                if self.flee_step(adj):
                    return
                if self.fight(adj):
                    return
            if self.turn - self.last_elbereth_turn > 40:
                self.last_elbereth_turn = self.turn
                self.elbereth_waits = 0
                self.engrave_elbereth()
                return
            if self.turn - self.last_elbereth_turn <= 12 and self.elbereth_waits < 4:
                # attacking from the square would wipe the engraving: hold still
                self.elbereth_waits += 1
                self.g.cmd("ms")
                return
            # they ignore Elbereth (or it's gone): fight for our life
            if self.fight(adj):
                return
        # --- hunger: eat before it's too late ---
        fainting = any(f.startswith("Faint") for f in st.flags)
        if st.hungry or st.weak or fainting:
            if self.try_eat_corpse_here():
                return
            if (st.weak or fainting) and self.eat_from_inventory():
                return
            if (fainting and self.pray_count < 10
                    and self.turn - self.last_pray_turn > 400):
                self.pray()  # certain death otherwise
                return
            if st.weak:
                # Weak = major trouble: safe past ~450-500 turns (wiki: rnz(350)<201)
                if (self.turn - self.last_pray_turn) > 500 and self.pray_count < 12:
                    self.pray()
                    return
        if st.confused or st.stunned or st.blind:
            if not (adj and self.fight(adj)):
                self.g.cmd("ms")  # always consume time while impaired
            return

        # --- stuck to a lichen/clinger: kill it first ---
        if "stuck" in self.g.flags:
            hx, hy = self.hero
            for (dx, dy) in DIRS:
                x, y = hx + dx, hy + dy
                if not (0 <= x < W and 0 <= y < H):
                    continue
                t = self.level.tile(x, y)
                if t.char in MONSTER_CHARS and t.char not in ("e", "@") \
                        and not melee_ok(t.char, t.fg):
                    self.log(f"[stuck] killing the clinger {t.char} at {(x, y)}")
                    self.step_dir((dx, dy))
                    return
            self.g.flags.discard("stuck")  # nothing passive adjacent: stale flag

        # --- a lichen keeps touching us: kill it despite the blacklist ---
        if "kill_lichen" in self.g.flags:
            done = False
            for (dxdy, ch, fg) in adj:
                if ch == "F":
                    self.log(f"[fight] killing harassing lichen dir={dxdy}")
                    self.step_dir(dxdy)
                    done = True
                    break
            if done:
                return
            self.g.flags.discard("kill_lichen")

        # --- swarmed in the open: pull back into a chokepoint first ---
        if len(adj) >= 2 and hp_frac < 0.85:
            if self.funnel_step(adj):
                return

        # --- combat ---
        if adj and self.fight(adj):
            return

        # --- free combat upgrade: advance weapon skills when offered ---
        if "can_enhance" in self.g.flags and not adj:
            self.g.flags.discard("can_enhance")
            self.enhance_skills()
            return

        # --- low hp, no threat: rest until mostly healed ---
        if hp_frac < 0.7 and not adj:
            self.g.cmd("m20s")
            return

        # --- go eat the corpse of our last safe kill (bank nutrition) ---
        if self.pending_eat and not st.satiated and not adj:
            pos, t0, tick0 = self.pending_eat
            if self.turn - t0 > 20 or self.ticks - tick0 > 25:
                self.pending_eat = None
            elif self.hero == pos:
                self.pending_eat = None
                if self.eat_floor_corpse():
                    return
            else:
                path = self.level.path_to(self.hero, {pos}, self.turn)
                if path and len(path) <= 3:
                    self.move_along(path)
                    return
                self.pending_eat = None  # unreachable: drop it

        # --- food opportunism: bank nutrition from fresh safe corpses ---
        self.pickup_food()
        if not st.satiated:
            site = self.fresh_kill_site()
            if site:
                if site == self.hero:
                    if self.try_eat_corpse_here():
                        return
                else:
                    path = self.level.path_to(self.hero, {site}, self.turn)
                    if path and len(path) <= 4:
                        self.move_along(path)
                        return

        # --- Excalibur: dip the long sword at XL5+ on a fountain ---
        if (not self.excalibur and self.long_sword_letter and st.xp >= 5
                and self.fountain_dips < 15 and not adj):
            if self.excalibur_step():
                return

        # --- navigation ---
        if self.navigate():
            return

        # --- stuck: search for hidden passages ---
        self.search_step()

    def navigate(self):
        hero, turn = self.hero, self.turn
        lv = self.level

        # sticky target: commit to the current exploration goal to avoid
        # nearest-target flapping (the classic two-goal oscillation)
        if self.nav_target:
            kind, pos, since = self.nav_target
            if self.hero == pos or self.ticks - since > 80:
                self.nav_target = None
            elif not lv.walkable(pos[0], pos[1], hero, turn):
                self.nav_target = None
            elif kind in ("frontier", "probe") and pos in lv.visited:
                self.nav_target = None
            else:
                path = lv.path_to(hero, {pos}, turn)
                if path:
                    self.move_along(path)
                    return True
                self.nav_target = None

        # 0. too deep in Doom: bail out immediately, don't explore dangerous levels
        if self.branch == BRANCH_DOOM and self.dlvl >= 5:
            self.mines_hunt = True
            if hero in lv.stairs_up:
                self.log(f"[nav] too deep (Doom:{self.dlvl}): climbing right away")
                self.last_stair_used = ("up", hero)
                self.g.cmd("<")
                return True
            if lv.stairs_up:
                path = lv.path_to(hero, set(lv.stairs_up), turn)
                if path:
                    self.move_along(path)
                    return True
            # up stairs unknown: fall through to exploration to find them

        # 1. explore the level fully first (needed to spot mines stairs / the town)
        path = lv.frontier_path(hero, turn)
        if path:
            self.nav_target = ("frontier", path[-1], self.ticks)
            self.move_along(path)
            return True

        # 1b. frontier blocked by a monster (often a passive F/j/b in a corridor)
        path = lv.frontier_path(hero, turn, ignore_monsters=True)
        if path:
            nx, ny = path[0]
            t = lv.tile(nx, ny)
            if t.char in MONSTER_CHARS or t.peaceful_until > turn:
                if t.peaceful_until > turn:
                    return self.wait_or_force((nx, ny), t)
                return self.handle_blocker((nx, ny), t)
            self.move_along(path)
            return True

        # In Doom with a known way down (and no mines hunt), don't be a
        # completionist: descending fast saves food, time and fights.
        lazy = (self.branch == BRANCH_DOOM and not self.mines_hunt
                and (lv.stairs_down - lv.tried_down))

        # 1c. unified unknown-explorer: walk INTO the unknown (BFS where unseen
        # tiles are traversable); edge bans with expiry prune solid rock.
        if not lazy:
            path = lv.explore_unknown_path(hero, turn)
            if path:
                self.nav_target = ("probe", path[-1], self.ticks)
                nx, ny = path[0]
                t = lv.tile(nx, ny)
                if t.char in MONSTER_CHARS or t.peaceful_until > turn:
                    if t.peaceful_until > turn:
                        return self.wait_or_force((nx, ny), t)
                    return self.handle_blocker((nx, ny), t)
                self.move_along(path)
                return True

        # 2. fully explored: pick a stairs goal according to branch strategy
        goal = self.pick_goal()
        if goal is None:
            return False
        kind, target = goal
        if hero == target:
            if kind == "down":
                snap = self.g.pump()
                if (snap.status and snap.status.hp < 0.75 * max(1, snap.status.hpmax)
                        and not self.adjacent_monsters(snap)):
                    self.g.cmd("m20s")  # heal up before descending
                    return True
                self.log(f"[nav] descending at {hero} ({self.branch}:{self.dlvl})")
                lv.tried_down.add(hero)
                self.last_stair_used = ("down", hero)
                self.g.cmd(">")
            else:
                self.log(f"[nav] climbing at {hero} ({self.branch}:{self.dlvl})")
                self.last_stair_used = ("up", hero)
                self.g.cmd("<")
            return True
        path = lv.path_to(hero, {target}, turn)
        if path:
            self.move_along(path)
            return True
        # path blocked (peaceful/monster?) - try ignoring monsters
        path = lv.path_to(hero, {target}, turn, ignore_monsters=True)
        if path:
            nx, ny = path[0]
            t = lv.tile(nx, ny)
            if t.char in MONSTER_CHARS or t.peaceful_until > turn:
                if t.peaceful_until > turn:
                    return self.wait_or_force((nx, ny), t)
                return self.handle_blocker((nx, ny), t)
            self.move_along(path)
            return True
        return False

    def _openness(self, x, y):
        return sum(1 for (dx, dy) in DIRS
                   if 0 <= x + dx < W and 0 <= y + dy < H
                   and self.level.walkable(x + dx, y + dy, self.hero, self.turn,
                                           ignore_monsters=True))

    def funnel_step(self, adj):
        """Step into a chokepoint (corridor/doorway) so fewer enemies can hit us."""
        hx, hy = self.hero
        cur_open = self._openness(hx, hy)
        if cur_open <= 3:
            return False  # already in a chokepoint: stand and fight
        threats = [(hx + d[0][0], hy + d[0][1]) for d in adj]
        best = None
        for (dx, dy) in DIRS:
            nx, ny = hx + dx, hy + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            if not self.level.walkable(nx, ny, self.hero, self.turn):
                continue
            # don't step INTO contact with even more monsters
            n_adj = sum(1 for tx, ty in threats
                        if max(abs(nx - tx), abs(ny - ty)) <= 1)
            if n_adj >= len(adj):
                continue
            op = self._openness(nx, ny)
            if op <= cur_open - 2 and (best is None or op < best[0]):
                best = (op, (dx, dy))
        if best:
            self.log(f"[funnel] retreating into chokepoint dir={best[1]} (open {cur_open}->{best[0]})")
            self.step_dir(best[1])
            return True
        return False

    def flee_step(self, adj):
        """Step to a walkable neighbor that increases distance from attackers."""
        hx, hy = self.hero
        threats = [(hx + d[0][0], hy + d[0][1]) for d in adj]
        best = None
        for (dx, dy) in DIRS:
            nx, ny = hx + dx, hy + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            if not self.level.walkable(nx, ny, self.hero, self.turn):
                continue
            score = min(max(abs(nx - tx), abs(ny - ty)) for tx, ty in threats)
            if score >= 2 and (best is None or score > best[0]):
                best = (score, (dx, dy))
        if best:
            self.step_dir(best[1])
            return True
        return False

    def wait_or_force(self, pos, t):
        """A peaceful monster blocks us. Wait a while; if it never moves
        (sleeping), either rule the tile out or force-attack non-humans."""
        t.wait_count += 1
        if t.char == "e":
            return self.handle_blocker(pos, t)  # floating eye: never force-attack
        if t.wait_count <= 12:
            self.g.cmd("ms")
            return True
        if t.char == "@":
            # never anger shopkeepers/priests/watchmen: treat as a wall
            t.peaceful_until = self.turn + 10**9
            return True
        dx, dy = pos[0] - self.hero[0], pos[1] - self.hero[1]
        if t.char not in MONSTER_CHARS:
            # marked non-monster tile (vapor cloud, invisible long gone):
            # just try to walk in; the hazard prompt handler decides
            if abs(dx) <= 1 and abs(dy) <= 1 and (dx or dy):
                self.step_dir((dx, dy))
                return True
            self.g.cmd("ms")
            return True
        if abs(dx) <= 1 and abs(dy) <= 1 and (dx or dy):
            self.log(f"[force] attacking sleeping peaceful blocker {t.char} at {pos}")
            snap = self.g.cmd("F" + DIRS[(dx, dy)])
            if snap.ynq and "Really attack" in snap.lines[0]:
                self.g.answer("y")
            t.peaceful_until = 0
            return True
        self.g.cmd("ms")
        return True

    def handle_blocker(self, pos, tile):
        """A monster blocks the only way forward."""
        dx, dy = pos[0] - self.hero[0], pos[1] - self.hero[1]
        ch, fg = tile.char, tile.fg
        if ch == "@":
            # humans (shopkeeper/priest/watch): wait, then treat as wall
            tile.peaceful_until = self.turn + 100
            return self.wait_or_force(pos, tile)
        if ch == "e":
            # floating eye / sphere: throw something, never melee
            letter = None
            if self.dagger_letter:
                letter = self.dagger_letter
                self.dagger_letter = None  # single use until re-confirmed
            elif self.weapon_letter and not self.rewield_letter:
                letter = self.weapon_letter  # throw the spear, recover it after
                self.rewield_letter = letter
                self.weapon_letter = None
            if letter:
                self.log(f"[blocker] throwing '{letter}' at {ch} at {pos}")
                snap = self.g.cmd("t")
                if "What do you want to throw" in snap.lines[0]:
                    snap = self.g.answer(letter)
                if "don't have that object" in snap.lines[0]:
                    snap = self.g.answer(ESC)
                    return True
                if "direction" in snap.lines[0].lower():
                    self.g.answer(DIRS[(dx, dy)])
                return True
            # nothing left to throw: avoid
            self.log(f"[blocker] nothing to throw at {ch} at {pos}: avoiding 300 turns")
            tile.peaceful_until = self.turn + 300
            self.g.cmd("m10s")
            return True
        # passive monsters (molds, jellies): melee them if we're healthy
        snap = self.g.pump()
        hp = snap.status.hp if snap.status else 0
        hpmax = max(1, snap.status.hpmax if snap.status else 1)
        tile.wait_count += 1
        if hp > 0.55 * hpmax or (tile.wait_count > 6 and hp > 0.35 * hpmax):
            self.log(f"[blocker] melee passive {ch} ({fg}) at {pos} T={self.turn}")
            self.step_dir((dx, dy))
            return True
        self.g.cmd("m20s")  # rest until healthy enough
        return True

    def pick_goal(self):
        """Returns ('down'|'up', (x,y)) or None (-> search for hidden passages)."""
        lv = self.level

        def any_down():
            return next(iter(lv.stairs_down)) if lv.stairs_down else None

        def any_up():
            fresh = lv.stairs_up - lv.tried_up
            pool = fresh or lv.stairs_up
            return next(iter(pool)) if pool else None

        if self.branch == BRANCH_MINES:
            if self.mines_up_hunt:
                t = any_up()
                if t:
                    return ("up", t)
                self.mines_up_hunt = False  # no more ups: resume descending
            t = any_down()
            return ("down", t) if t else None
        if self.branch == BRANCH_SOKOBAN:
            t = any_down()  # leave sokoban the way we came up
            return ("down", t) if t else None
        # Dungeons of Doom
        if self.dlvl == 1:
            t = any_down()
            return ("down", t) if t else None
        if self.dlvl >= 5:
            # too deep: the mines entrance is on dlvl 2-4, climb back up
            self.mines_hunt = True
            t = any_up()
            return ("up", t) if t else None
        # dlvl 2-4
        untried = self.stairs_to_try()
        if untried:
            return ("down", untried[0])
        if self.untried_stairs_above():
            # a known untried staircase awaits on a shallower level: go get it
            self.mines_hunt = True
        if self.mines_hunt:
            if self.dlvl > 2:
                t = any_up()
                return ("up", t) if t else None
            return None  # dlvl 2 exhausted: search for hidden stairs
        # not hunting yet: keep going down the main branch
        t = any_down()
        if t:
            return ("down", t)
        # no way down here: the missing stairs are in zones we lazily skipped
        # on upper levels — climb back and explore them properly
        if self.dlvl > 2:
            self.mines_hunt = True
            t = any_up()
            if t:
                return ("up", t)
        return None

    def untried_stairs_above(self):
        for (br, dl), L in self.levels.items():
            if br == BRANCH_DOOM and dl < self.dlvl and (L.stairs_down - L.tried_down):
                return True
        return False

    def search_step(self):
        lv = self.level
        if lv.total_searched % 100 == 0:
            try:
                f = lv.frontier_path(self.hero, self.turn)
                fi = lv.frontier_path(self.hero, self.turn, ignore_monsters=True)
                goal = self.pick_goal()
                gp = gpi = None
                if goal and goal[1]:
                    gp = lv.path_to(self.hero, {goal[1]}, self.turn)
                    gpi = lv.path_to(self.hero, {goal[1]}, self.turn, ignore_monsters=True)
                self.log(f"[why-search] f={bool(f)} fi={(fi or [None])[0]} goal={goal} "
                         f"gp={bool(gp)} gpi={(gpi or [None])[0]} probes={len(lv.probe_targets(self.hero, self.turn))}")
            except Exception as e:
                self.log(f"[why-search] diag failed: {e}")
        if self.branch == BRANCH_MINES:
            # mines caverns have no hidden doors: blocked routes mean monsters
            # or boulders; wait for the crowd to disperse instead of searching
            if lv.total_searched > 400:
                raise Abort(f"search exhausted on {self.branch}:{self.dlvl}")
            lv.total_searched += 10
            self.g.cmd("m10s")
            return
        budget = 700 if lv.stairs_down else 1600
        if lv.total_searched > budget:
            if lv.shop_doors and not lv.desperate:
                # nothing else worked: kick the suspected shop doors after all
                self.log("[door] desperation: will kick the deferred doors")
                lv.desperate = True
                for pos in lv.shop_doors:
                    dt = lv.tile(*pos)
                    dt.peaceful_until = 0
                    dt.hard_ban = False
                lv.total_searched = 0
                return
            raise Abort(f"search exhausted on {self.branch}:{self.dlvl}")
        spots = lv.search_spots(self.hero, self.turn)
        if spots:
            if self.hero in spots:
                lv.tile(*self.hero).searched += 10
                lv.total_searched += 10
                self.g.cmd("m10s")
                return
            path = lv.path_to(self.hero, set(spots), self.turn)
            if path:
                self.move_along(path)
                return
        # nothing to search: search in place as last resort
        lv.tile(*self.hero).searched += 10
        lv.total_searched += 10
        self.g.cmd("m10s")

    def dump_map(self):
        lv = self.level
        self.log(f"[map] {self.branch}:{self.dlvl} hero={self.hero} "
                 f"stairs_down={lv.stairs_down} stairs_up={lv.stairs_up} doors={len(lv.doors_seen)}")
        for y in range(H):
            row = "".join(lv.tiles[y][x].char for x in range(W))
            if row.strip():
                self.log(f"[map] {y:2d}|{row.rstrip()}")

    def dump_state(self, path):
        import json
        data = {}
        for key, lv in self.levels.items():
            data[f"{key[0]}:{key[1]}"] = {
                "chars": ["".join(lv.tiles[y][x].char for x in range(W)) for y in range(H)],
                "fgs": [",".join(str(lv.tiles[y][x].fg) for x in range(W)) for y in range(H)],
                "visited": sorted(list(lv.visited)),
                "blocked_edges": [[list(a), list(b), list(c)] for (a, b), c in lv.blocked_edges.items()],
                "stairs_down": sorted(lv.stairs_down),
                "stairs_up": sorted(lv.stairs_up),
                "tried_down": sorted(lv.tried_down),
                "peaceful": [[x, y, lv.tiles[y][x].peaceful_until]
                             for y in range(H) for x in range(W)
                             if lv.tiles[y][x].peaceful_until > 0],
                "denied": [[x, y, lv.tiles[y][x].denied_until]
                           for y in range(H) for x in range(W)
                           if lv.tiles[y][x].denied_until > 0],
                "hard_bans": [[x, y] for y in range(H) for x in range(W)
                              if lv.tiles[y][x].hard_ban],
                "searched": [[x, y, lv.tiles[y][x].searched]
                             for y in range(H) for x in range(W)
                             if lv.tiles[y][x].searched > 0],
            }
        data["hero"] = list(self.hero) if self.hero else None
        data["branch"] = self.branch
        data["dlvl"] = self.dlvl
        data["turn"] = self.turn
        with open(path, "w") as f:
            json.dump(data, f)

    def recover(self):
        """Try to unwedge the UI: close overlays, redraw, take a step."""
        from game import CTRL_R
        self.g.sess.send(ESC)
        self.g.sess.settle(quiet=0.05, total=1.0)
        self.g.sess.send(" ")
        self.g.sess.settle(quiet=0.05, total=1.0)
        self.g.sess.send(ESC)
        self.g.sess.settle(quiet=0.05, total=1.0)
        self.g.sess.send(CTRL_R)
        self.g.pump()
        # nudge: search once (consumes a turn if UI is live)
        self.g.cmd("ms")

    # ---------- bootstrap ----------

    def start(self):
        snap = self.g.pump()
        inv = {}
        for _ in range(3):
            inv = self.g.inventory()
            if len(inv) >= 3:
                break
        for letter, desc in inv.items():
            if re.search(r"\b(food rations?|cram rations?|lembas wafers?|apples?|"
                         r"oranges?|pears?|melons?|bananas?|carrots?|slime molds?|"
                         r"candy bars?|fortune cookies?|pancakes?|tripe rations?)\b", desc):
                self.food_letters.append(letter)
            if "dagger" in desc and self.dagger_letter is None:
                self.dagger_letter = letter
            if "long sword" in desc and self.long_sword_letter is None:
                self.long_sword_letter = letter
            if "spear" in desc:
                self.spear_letter = letter
            if "(weapon in" in desc:
                self.weapon_letter = letter
            if "dragon scale mail" in desc and "(being worn)" not in desc:
                self.log(f"[wear] putting on the dragon scale mail '{letter}'")
                snap = self.g.cmd("W")
                if "What do you want to wear" in snap.lines[0]:
                    self.g.answer(letter)
                self.g.pump()
        if self.long_sword_letter:
            self.log(f"[start] wielding the long sword '{self.long_sword_letter}'")
            snap = self.g.cmd("w")
            if "What do you want to wield" in snap.lines[0]:
                self.g.answer(self.long_sword_letter)
            if self.spear_letter:
                self.weapon_letter = self.spear_letter  # throwable backup
        self.log(f"[start] inventory={inv} food={self.food_letters}")
        self.sync()
