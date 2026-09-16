"""New deterministic survival strategy; every decision has a reason."""
from dataclasses import dataclass
import random
import re
from .dialogue import Prompt
from .world import World


@dataclass(frozen=True)
class Decision:
    keys: bytes
    reason: str
    expected: frozenset[Prompt]


class Strategy:
    def __init__(self):
        # Long deterministic sweeps cover rooms instead of returning to the
        # same eight cells after every short cycle.
        self.move_rng = random.Random(0xB07A5C)
        self.actions = 0
        self.food_search_cooldown = 0
        self.last_prayer_action = -10000
        self.last_direction = None
        self.peaceful_cooldown = 0
        self.last_game_turn = None
        self.same_turn_actions = 0
        self.food_keys = set()
        self.inventory_probe = False

    def next_move(self) -> bytes:
        return self.move_rng.choice((b"h", b"j", b"k", b"l", b"y", b"u", b"b", b"n"))

    def decide(self, world: World, prompt: Prompt) -> Decision:
        self.actions += 1
        if world.game_turn is not None and world.game_turn == self.last_game_turn:
            self.same_turn_actions += 1
        else:
            self.same_turn_actions = 0
            self.last_game_turn = world.game_turn
        self.food_search_cooldown = max(0, self.food_search_cooldown - 1)
        self.peaceful_cooldown = max(0, self.peaceful_cooldown - 1)
        if prompt == Prompt.END: return Decision(b"", "terminal end", frozenset({Prompt.END}))
        if prompt == Prompt.START:
            text = ("\n".join(world.screen) + "\n" + world.last_message).lower()
            if "are you sure you want to pray" in text:
                return Decision(b"n", "decline repeated prayer confirmation", frozenset({Prompt.START, Prompt.GAME}))
            if "really attack" in text:
                self.peaceful_cooldown = 20
                return Decision(b"n", "decline attack on peaceful creature", frozenset({Prompt.START, Prompt.GAME}))
            if "beware, there will be no return" in text:
                return Decision(b"n", "decline irreversible upward travel during descent", frozenset({Prompt.START, Prompt.GAME}))
            if "already a game" in text or "destroy old game" in text:
                return Decision(b"y", "resolve stale run owned by this unique user", frozenset({Prompt.START, Prompt.GAME}))
            if "shall i pick" in text or "pick your" in text:
                return Decision(b"y", "accept configured role and race", frozenset({Prompt.START, Prompt.GAME}))
            return Decision(b"\n", "acknowledge startup prompt", frozenset({Prompt.START, Prompt.GAME}))
        if prompt == Prompt.MENU:
            text = ("\n".join(world.screen) + "\n" + world.last_message).lower()
            if "--more--" in text:
                return Decision(b" ", "advance pager before interpreting next prompt", frozenset({Prompt.MENU, Prompt.GAME}))
            if "what do you want to eat" in text:
                match = re.search(r"what do you want to eat\?\s*\[([a-z])", text)
                if match:
                    offered = match.group(1)
                    safe = sorted(self.food_keys & set(re.findall(r"[a-z]", match.group(1))))
                    return Decision((safe[0] if safe else offered).encode(), "eat identified non-corpse food", frozenset({Prompt.MENU, Prompt.GAME}))
                return Decision(b"q", "cancel food prompt without a known edible item", frozenset({Prompt.MENU, Prompt.GAME}))
            if self.inventory_probe:
                self.inventory_probe = False
                safe_names = ("ration", "lembas", "carrot", "apple", "orange", "pear", "melon", "banana")
                for line in world.screen:
                    match = re.match(r"\s*([a-z])\s+-\s+(.+)", line, re.I)
                    if match and any(name in match.group(2).lower() for name in safe_names):
                        self.food_keys.add(match.group(1).lower())
                return Decision(b"\033", "close inventory after recording safe food", frozenset({Prompt.MENU, Prompt.GAME}))
            return Decision(b"\033", "cancel unknown menu safely", frozenset({Prompt.GAME, Prompt.MENU}))
        if prompt == Prompt.DIRECTION: return Decision(b".", "cancel unknown direction", frozenset({Prompt.GAME, Prompt.DIRECTION}))
        if self.peaceful_cooldown:
            decision = Decision(self.next_move(), "leave peaceful creature's square", frozenset({Prompt.GAME, Prompt.UNKNOWN}))
            self.last_direction = decision.keys
            return decision
        text = ("\n".join(world.screen) + "\n" + world.last_message).lower()
        if "fainted" in text:
            if self.actions - self.last_prayer_action >= 500:
                self.last_prayer_action = self.actions
                return Decision(b"#pray\n", "recover from fainting before sending movement", frozenset({Prompt.GAME, Prompt.START, Prompt.MENU, Prompt.UNKNOWN}))
            if self.actions % 5:
                return Decision(b".", "advance one turn while fainted", frozenset({Prompt.GAME, Prompt.UNKNOWN}))
        if self.same_turn_actions >= 3 and "it's a wall" in text:
            choices = [b"h", b"j", b"k", b"l"]
            if self.last_direction in choices:
                choices.remove(self.last_direction)
            decision = Decision(choices[self.actions % len(choices)], "break repeated wall state", frozenset({Prompt.GAME, Prompt.UNKNOWN}))
            self.last_direction = decision.keys
            return decision
        if self.actions - self.last_prayer_action >= 500 and any(word in text for word in ("blind", "fainting", "fainted")) and world.hp is not None and world.hp <= 8:
            self.last_prayer_action = self.actions
            return Decision(b"#pray\n", "emergency prayer while incapacitated and critically wounded", frozenset({Prompt.GAME, Prompt.MENU, Prompt.UNKNOWN}))
        if world.hp is not None and world.hp <= 8 and ("bites!" in text or "hits!" in text):
            retreat = {b"h":b"k", b"l":b"k", b"j":b"h", b"k":b"h",
                       b"y":b"l", b"n":b"h", b"u":b"h", b"b":b"l"}.get(self.last_direction)
            if retreat:
                self.last_direction = retreat
                return Decision(retreat, "retreat from recent critical damage", frozenset({Prompt.GAME, Prompt.MENU}))
        # A staircase is a feature, not a monster or an item.  Probe the
        # descent command occasionally because NetHack can redraw a stair
        # under a moving player before the map model sees the glyph.
        if self.actions % 97 == 0:
            return Decision(b">", "probe for a visible downward staircase", frozenset({Prompt.GAME, Prompt.MENU}))
        combat = world.adjacent_monster_key()
        if combat is not None:
            return Decision(combat, "attack visible adjacent monster", frozenset({Prompt.GAME, Prompt.MENU}))
        if world.food_unavailable:
            if self.actions - self.last_prayer_action >= 500 and any(word in text for word in ("hungry", "fainting", "fainted")):
                self.last_prayer_action = self.actions
                return Decision(b"#pray\n", "pray immediately after food supply is exhausted", frozenset({Prompt.GAME, Prompt.MENU, Prompt.UNKNOWN}))
            if self.food_search_cooldown == 0:
                self.food_search_cooldown = 80
                return Decision(b"s", "search for food after empty inventory", frozenset({Prompt.GAME, Prompt.MENU}))
            return Decision(self.next_move(), "continue toward food after failed search", frozenset({Prompt.GAME, Prompt.UNKNOWN}))
        if any(word in text for word in ("hungry", "fainting", "fainted", "starved")) and "what do you want to eat" not in text:
            if not self.inventory_probe:
                self.inventory_probe = True
                return Decision(b"i", "inspect inventory before eating", frozenset({Prompt.GAME, Prompt.MENU}))
            return Decision(b"e", "eat before risking another movement", frozenset({Prompt.GAME, Prompt.MENU}))
        stairs = world.stair_key()
        action = world.stair_action()
        if action is not None:
            return Decision(action, "use memorized staircase", frozenset({Prompt.GAME, Prompt.MENU}))
        if stairs is not None:
            return Decision(stairs, "navigate toward visible staircase", frozenset({Prompt.GAME, Prompt.MENU}))
        if world.uncertain: return Decision(b"\014", "request fresh observation", frozenset({Prompt.GAME, Prompt.UNKNOWN}))
        decision = Decision(self.next_move(), "deterministic local exploration", frozenset({Prompt.GAME, Prompt.UNKNOWN}))
        self.last_direction = decision.keys
        return decision
