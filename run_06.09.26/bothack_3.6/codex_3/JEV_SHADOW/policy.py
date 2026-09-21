"""JEV_SHADOW: observe selected BotHack actions without changing them."""
from collections import deque
import time

from jev_common import DecisionError, action_summary
from jev_policy_support import game_state, install_prompt_shims, install_protocol_prompt_handlers
from JEV_PRIMITIVES.policy import INTENT_DESCRIPTIONS


INSTRUCTIONS = (
    "Choose the high-level intention that should be taken in this NetHack "
    "situation. Your answer is observational and will not be executed."
)


class ShadowObserver:
    IMPORTANT_ITEMS = ("levitation", "reflection", "dragon scale", "speed boot",
                       "unicorn horn", "bag of holding", "pick-axe", "excalibur",
                       "amulet of yendor", "bell of opening", "candelabrum",
                       "book of the dead", "candle")

    def __init__(self, bh, decider, journal, args):
        self.bh = bh
        self.decider = decider
        self.journal = journal
        self.args = args
        self.started = time.monotonic()
        self.positions = deque(maxlen=80)
        self.last_branch = None
        self.last_goal = None
        self.last_inventory = set()
        self.last_turn_sample = -1000
        self.last_action_sig = None
        self.same_action = 0
        self.near_turn_limit_seen = False
        self.near_time_limit_seen = False

    def action_chosen(self, action):
        game = self.bh.game.deref()
        trigger = self._triggers(game, action)
        if not trigger:
            return
        state = game_state(game)
        state["objective"] = self.args.goal or "ascend"
        # Do not invoke any primitive here.  Several BotHack functions use
        # its RNG or update tactical bookkeeping while constructing an
        # action; doing that in Shadow would subtly change future play.
        choices = {key: {"description": description, "action": None,
                         "intent": key}
                   for key, description in INTENT_DESCRIPTIONS.items()}
        # The comparison must always contain a faithful representation of X.
        choices["bothack_exact"] = {
            "description": "Execute exactly BotHack's selected action: %s" %
                           action_summary(action),
            "action": action,
            "intent": "bothack_exact",
        }
        try:
            self.journal.decide(
                                self.decider, state, choices,
                                INSTRUCTIONS + " Current experiment objective: %s." %
                                (self.args.goal or "full ascension"),
                                False, bothack_action=action_summary(action),
                                trigger=trigger, track_outcome=True)
        except DecisionError as exc:
            self.journal.error(state, exc, None)

    def _triggers(self, game, action):
        from pybothack.dungeon import branch_key
        from pybothack.position import position
        triggers = []
        turn = game.get("turn") or 0
        pos = position(game["player"])
        pkey = (pos.x, pos.y, str(game.get("dlvl")))
        self.positions.append(pkey)
        if len(self.positions) >= 40 and len(set(self.positions)) <= 5:
            triggers.append("stagnation")
        branch = str(branch_key(game))
        if self.last_branch is not None and branch != self.last_branch:
            triggers.append("branch_change")
        self.last_branch = branch
        reason = " ".join(str(x) for x in (action.get("reason") or ())).lower()
        goal = self._goal_class(reason, action.get("type"))
        if self.last_goal is not None and goal and goal != self.last_goal:
            triggers.append("goal_change")
        self.last_goal = goal
        inv = self._important_inventory(game)
        if self.last_inventory and inv != self.last_inventory:
            triggers.append("important_item_change")
        self.last_inventory = inv
        sig = (action.get("type"), str(action.get("dir")),
               str(action.get("slot")), str(action.get("pos")))
        if sig == self.last_action_sig:
            self.same_action += 1
        else:
            self.same_action = 0
            self.last_action_sig = sig
        if self.same_action == 5:
            triggers.append("loop_detected")
        max_turns = getattr(self.args, "max_turns", None)
        if (max_turns and not self.near_turn_limit_seen
                and turn >= max(0, max_turns - min(1000, max_turns // 10))):
            self.near_turn_limit_seen = True
            triggers.append("near_turn_limit")
        max_seconds = getattr(self.args, "max_seconds", None)
        if (max_seconds and not self.near_time_limit_seen
                and time.monotonic() - self.started >= max(0, max_seconds - 60)):
            self.near_time_limit_seen = True
            triggers.append("near_time_limit")
        if action.get("type") in ("ascend", "descend", "pray", "offer",
                                   "read", "quaff", "zap", "rub"):
            triggers.append("major_action")
        if turn - self.last_turn_sample >= 250:
            triggers.append("periodic")
            self.last_turn_sample = turn
        return sorted(set(triggers))

    def _important_inventory(self, game):
        found = set()
        for item in (game["player"].get("inventory") or {}).values():
            label = str(item.get("label") or "").lower()
            for name in self.IMPORTANT_ITEMS:
                if name in label:
                    found.add(name)
        return found

    @staticmethod
    def _goal_class(reason, action_type):
        groups = (
            ("survive", ("retreat", "recover", "starv", "ill", "pray")),
            ("fight", ("fight", "targetting", "hitting", "enemy")),
            ("items", ("item", "pickup", "container", "loot", "bag")),
            ("equipment", ("wear", "wield", "equip", "remove")),
            ("branch", ("branch", "mines", "sokoban", "quest", "gehennom")),
            ("explore", ("explor", "search", "progress", "stair", "down")),
        )
        for name, words in groups:
            if any(word in reason for word in words):
                return name
        return action_type or "unknown"


def install(bh, decider, journal, args):
    from pybothack.delegator import Handler
    from pybothack.handlers import register_handler
    from pybothack.util import PRIORITY_BOTTOM
    install_prompt_shims()
    install_protocol_prompt_handlers(bh)
    observer = ShadowObserver(bh, decider, journal, args)
    register_handler(bh, PRIORITY_BOTTOM,
                     Handler(action_chosen=observer.action_chosen))
