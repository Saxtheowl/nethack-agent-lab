"""JEV_RAW: direct NetHack actions, no BotHack strategic selectors."""
from collections import OrderedDict

from jev_common import DecisionError
from jev_policy_support import (candidate, game_state, install_prompt_shims,
                                install_protocol_prompt_handlers,
                                strip_strategic_handlers)


INSTRUCTIONS = (
    "Choose the single best immediate NetHack action. The goal is to survive, "
    "explore, descend through the dungeon and reach Minetown. Use only facts "
    "in the current state; avoid repeating actions that made no progress."
)


def raw_candidates(game, allow_escape=False):
    from pybothack.actions import (Apply, Ascend, Descend, Eat, Kick, Move,
                                   Open, PickUp, Pray, PutOn, Quaff, Read,
                                   Remove, Search, TakeOff, Wait, Wear, Wield)
    from pybothack.dungeon import at_player, curlvl
    from pybothack.position import DIRECTIONS, in_direction

    choices = OrderedDict()
    for direction in DIRECTIONS:
        choices["move_" + direction.lower()] = candidate(
            "Move or melee one square %s." % direction, Move(direction))
    choices["search"] = candidate("Search adjacent squares for secret doors or traps.", Search())
    choices["wait"] = candidate("Wait one turn.", Wait())
    choices["pray"] = candidate("Pray to the hero's god; useful only in serious trouble.", Pray())
    here = at_player(game)
    feature = here.get("feature")
    # At the starting square the up staircase exits the dungeon.  It is not a
    # useful choice for the Minetown/depth objectives, and exposing it makes a
    # perfectly reasonable model choice terminate the experiment immediately.
    if feature == "stairs-up" and allow_escape:
        choices["ascend"] = candidate("Use the staircase or ladder up here.", Ascend())
    if feature == "stairs-down":
        choices["descend"] = candidate("Use the staircase or ladder down here.", Descend())
    items = list(here.get("items") or ())
    if items:
        labels = [i.get("label") for i in items if i.get("label")]
        if labels:
            choices["pickup_here"] = candidate(
                "Pick up the visible items on the current square: %s" % labels,
                PickUp(labels))
    level = curlvl(game)
    for direction in DIRECTIONS:
        tile = in_direction(level, game["player"], direction)
        if tile and tile.get("feature") in ("door-closed", "door-locked"):
            choices["open_" + direction.lower()] = candidate(
                "Open the adjacent door to the %s." % direction, Open(direction))
            choices["kick_" + direction.lower()] = candidate(
                "Kick the adjacent door to the %s." % direction, Kick(direction))
    inventory = game["player"].get("inventory") or {}
    for n, (slot, item) in enumerate(inventory.items()):
        if n >= 24:  # under Jev's option limit and bounded prompt size
            break
        sid = str(slot).encode("unicode_escape").decode().replace("\\", "_")
        label = item.get("label") or "unknown item"
        actions = (("eat", Eat), ("quaff", Quaff), ("read", Read),
                   ("apply", Apply), ("wield", Wield), ("wear", Wear),
                   ("puton", PutOn))
        for verb, fn in actions:
            choices["%s_%s" % (verb, sid)] = candidate(
                "%s inventory slot %s: %s" % (verb.capitalize(), slot, label),
                fn(slot))
        if item.get("worn"):
            fn = TakeOff if item.get("type") == "armor" else Remove
            choices["remove_" + sid] = candidate(
                "Remove worn item in slot %s: %s" % (slot, label), fn(slot))
    return choices


def install(bh, decider, journal, args):
    from pybothack.delegator import Handler
    from pybothack.handlers import register_handler
    from pybothack.util import PRIORITY_BOTTOM

    install_prompt_shims()
    strip_strategic_handlers(bh)
    install_protocol_prompt_handlers(bh)

    def choose_action(game):
        state = game_state(game)
        state["objective"] = args.goal or "ascend"
        choices = raw_candidates(
            game, allow_escape=(args.goal in ("ascend", "escape", "full")))
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
        return choices[key]["action"]

    register_handler(bh, PRIORITY_BOTTOM - 10,
                     Handler(choose_action=choose_action))
