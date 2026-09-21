"""JEV_PRIMITIVES: Jev selects goals; BotHack executes them reliably."""
from jev_common import DecisionError
from collections import OrderedDict

from jev_policy_support import (game_state, install_prompt_shims,
                                install_protocol_prompt_handlers,
                                strip_strategic_handlers)


INSTRUCTIONS = (
    "Choose the best high-level intention for this NetHack turn. BotHack will "
    "execute the selected intention, including pathfinding and menus. The "
    "experimental objective is stated below; prioritize it while staying alive."
)

INTENT_DESCRIPTIONS = OrderedDict([
    ("survive_illness", "Cure an urgent harmful condition using BotHack's inventory and prayer logic."),
    ("survive_hunger", "Handle dangerous hunger with safe food or prayer."),
    ("recover_impairment", "Cure blindness, confusion, stun or hallucination."),
    ("fight", "Fight or tactically approach a nearby hostile monster."),
    ("recover_hp", "Move to safety or rest to recover hit points."),
    ("collect_items", "Pathfind to and collect an item BotHack considers useful."),
    ("equip", "Equip better armor, amulet or weapon from inventory."),
    ("use_inventory", "Use a beneficial inventory item identified by BotHack."),
    ("eat", "Find and eat useful or necessary food."),
    ("interact_feature", "Use a useful dungeon feature such as an altar, fountain or throne."),
    ("reach_minetown", "Use BotHack navigation and dungeon memory to reach Minetown, entering and descending through the Gnomish Mines as needed."),
    ("reach_oracle", "Use BotHack navigation and dungeon memory to reach the Oracle level in the main dungeon."),
    ("seek_mines", "Use BotHack navigation and dungeon memory to enter the Gnomish Mines."),
    ("explore", "Explore the current area using BotHack mapping and pathfinding."),
    ("go_deeper", "Find a safe route downward, including stairs, holes or digging."),
    ("go_up", "Climb the staircase here to the previous level."),
    ("descend_here", "Descend the staircase under the hero."),
    ("search", "Search locally for hidden doors or traps."),
    ("wait", "Wait one turn."),
])


def primitive_candidates(game, objective=None, allow_escape=False):
    from pybothack.actions import Ascend, Descend, Search, Wait
    from pybothack.bots import mainbot
    from pybothack.dungeon import at_player, branch_key, curlvl
    from pybothack.pathing import explore, go_down, seek, seek_branch
    from pybothack.tile import stairs_down_p, stairs_up_p

    entries = OrderedDict()

    def reach_minetown():
        if branch_key(game) != "mines":
            return seek_branch(game, "mines")
        # Once inside the Mines, avoid the generic cross-level seeker: while
        # Minetown is still unknown it may pick the entrance stairs and bounce
        # back to the main branch.  Descend locally, falling back to mapping
        # the current Mines level when no downward route is available yet.
        if stairs_down_p(at_player(game)):
            return Descend()
        return (seek(game, stairs_down_p, {"go-down"})
                or go_down(game, curlvl(game)) or explore(game))

    def add(key, description, fn):
        # Candidate enumeration must not consume BotHack's RNG or tactical
        # bookkeeping.  Preview under a snapshot, restore it, and only invoke
        # the selected factory for real below.
        rng = game.get("rng")
        rng_state = rng.getstate() if hasattr(rng, "getstate") else None
        horn_uses = list(getattr(mainbot, "_UNIHORN_USES", ()))
        horn_blocked = list(getattr(mainbot, "_UNIHORN_BLOCKED", ()))
        try:
            action = fn()
        except Exception:
            action = None
        finally:
            if rng_state is not None:
                rng.setstate(rng_state)
            if hasattr(mainbot, "_UNIHORN_USES"):
                mainbot._UNIHORN_USES[:] = horn_uses
            if hasattr(mainbot, "_UNIHORN_BLOCKED"):
                mainbot._UNIHORN_BLOCKED[:] = horn_blocked
        if action is not None:
            entries[key] = {"description": description, "factory": fn,
                            "intent": key}

    add("survive_illness", INTENT_DESCRIPTIONS["survive_illness"],
        lambda: mainbot.handle_illness(game))
    add("survive_hunger", INTENT_DESCRIPTIONS["survive_hunger"],
        lambda: mainbot.handle_starvation(game))
    add("recover_impairment", INTENT_DESCRIPTIONS["recover_impairment"],
        lambda: mainbot.handle_impairment(game))
    add("fight", INTENT_DESCRIPTIONS["fight"],
        lambda: mainbot.fight(game))
    add("recover_hp", INTENT_DESCRIPTIONS["recover_hp"],
        lambda: mainbot.recover(game, True))
    add("collect_items", INTENT_DESCRIPTIONS["collect_items"],
        lambda: mainbot.consider_items(game))
    add("equip", INTENT_DESCRIPTIONS["equip"],
        lambda: mainbot.reequip(game) or mainbot.reequip_weapon(game))
    add("use_inventory", INTENT_DESCRIPTIONS["use_inventory"],
        lambda: mainbot.use_items(game))
    add("eat", INTENT_DESCRIPTIONS["eat"], lambda: mainbot.feed(game))
    add("interact_feature", INTENT_DESCRIPTIONS["interact_feature"],
        lambda: mainbot.use_features(game))
    if objective == "minetown":
        add("reach_minetown", INTENT_DESCRIPTIONS["reach_minetown"],
            reach_minetown)
    if objective == "oracle":
        add("reach_oracle", INTENT_DESCRIPTIONS["reach_oracle"],
            lambda: explore(game, "main", "oracle"))
    add("seek_mines", INTENT_DESCRIPTIONS["seek_mines"],
        lambda: seek_branch(game, "mines"))
    add("explore", INTENT_DESCRIPTIONS["explore"],
        lambda: explore(game))
    add("go_deeper", INTENT_DESCRIPTIONS["go_deeper"],
        lambda: go_down(game, curlvl(game)))
    if stairs_up_p(at_player(game)) and allow_escape:
        add("go_up", INTENT_DESCRIPTIONS["go_up"], Ascend)
    if at_player(game).get("feature") == "stairs-down":
        add("descend_here", INTENT_DESCRIPTIONS["descend_here"], Descend)
    add("search", INTENT_DESCRIPTIONS["search"], Search)
    add("wait", INTENT_DESCRIPTIONS["wait"], Wait)
    return entries


def install(bh, decider, journal, args):
    from pybothack.delegator import Handler
    from pybothack.handlers import register_handler
    from pybothack.util import PRIORITY_BOTTOM

    install_prompt_shims()
    strip_strategic_handlers(bh)
    install_protocol_prompt_handlers(bh)

    monitor = {"last": None, "last_position": None, "repeated": 0,
               "best_depth": 0,
               "depth_progress_call": 0, "seen_branches": set(),
               "active": None,
               "active_steps": 0, "active_level": None}

    def choose_action(game):
        state = game_state(game)
        state["objective"] = args.goal or "ascend"
        choices = primitive_candidates(
            game, objective=args.goal,
            allow_escape=(args.goal in ("ascend", "escape", "full")))

        # A primitive is a high-level intention, not a single keypress.  Let
        # BotHack keep executing it for a bounded burst and consult Jev again
        # when the level changes, it becomes unavailable, or its lease ends.
        active = monitor["active"]
        if (active in choices and args.jev_intent_steps > 1 and
                monitor["active_steps"] < args.jev_intent_steps and
                monitor["active_level"] == state.get("level")):
            try:
                action = choices[active]["factory"]()
            except Exception as exc:
                journal.error(state, exc, None)
                action = None
            if action is not None:
                monitor["active_steps"] += 1
                journal.continuation(state, active, monitor["active_steps"])
                return action
            monitor["active"] = None

        try:
            key = journal.decide(
                decider, state, choices,
                INSTRUCTIONS + " Current experiment objective: %s." %
                (args.goal or "full ascension"), True)
        except DecisionError as exc:
            if args.jev_on_error == "stop":
                raise SystemExit(str(exc))
            key = "search" if "search" in choices else next(iter(choices))
            journal.error(state, exc, key)

        monitor["active"] = key
        monitor["active_steps"] = 1
        monitor["active_level"] = state.get("level")

        position = state.get("position")
        if key == monitor["last"] and position == monitor["last_position"]:
            monitor["repeated"] += 1
        else:
            monitor["last"] = key
            monitor["last_position"] = position
            monitor["repeated"] = 1

        try:
            depth = int(str(state.get("level", "")).split(":")[-1])
        except ValueError:
            depth = 0
        branch = state.get("branch")
        if branch not in monitor["seen_branches"]:
            monitor["seen_branches"].add(branch)
            monitor["depth_progress_call"] = journal.calls
        if depth > monitor["best_depth"]:
            monitor["best_depth"] = depth
            monitor["depth_progress_call"] = journal.calls

        if (args.jev_repeat_limit and
                monitor["repeated"] >= args.jev_repeat_limit):
            journal.request_stop(
                "Jev repeated intention %r without moving %d times" %
                (key, monitor["repeated"]))
        elif (args.jev_depth_patience and journal.calls -
              monitor["depth_progress_call"] >= args.jev_depth_patience):
            journal.request_stop(
                "no new dungeon depth or branch in %d Jev decisions "
                "(best Dlvl:%d, branches:%s)" %
                (args.jev_depth_patience, monitor["best_depth"],
                 sorted(str(x) for x in monitor["seen_branches"])))
        try:
            action = choices[key]["factory"]()
        except Exception as exc:
            journal.error(state, exc, "search")
            action = None
        # State should be unchanged since candidate enumeration.  If a
        # primitive nevertheless becomes unavailable, use a neutral search
        # and record the policy failure rather than invoking BotHack strategy.
        if action is None:
            journal.error(state, RuntimeError("selected intention unavailable: "
                                              + key), "search")
            action = choices["search"]["factory"]()
        return action

    register_handler(bh, PRIORITY_BOTTOM - 10,
                     Handler(choose_action=choose_action))
