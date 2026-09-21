"""NetHack state serialization and candidate helpers shared by policies."""
from __future__ import annotations

from collections import OrderedDict

from jev_common import action_summary, json_safe


def install_prompt_shims():
    """Small protocol-only translations needed when strategy is removed."""
    import re
    import pybothack.nhbridge as nhbridge
    if getattr(nhbridge, "_jev_prompt_shims", False):
        return
    original = nhbridge._choice_call

    def choice_call(text):
        if re.search(r"Beware, there will be no return!\s+Still climb\?",
                     text or ""):
            return "still_climb", ()
        return original(text)

    nhbridge._choice_call = choice_call
    nhbridge._jev_prompt_shims = True
    original_yn = nhbridge.Bridge._yn

    def bridge_yn(self, req):
        if re.search(r"Beware, there will be no return!\s+Still climb\?",
                     req.query or ""):
            self.engine.yn("y")
            self._record_answer(req, "y")
            return
        return original_yn(self, req)

    nhbridge.Bridge._yn = bridge_yn


def install_protocol_prompt_handlers(bh):
    """Answer protocol safety prompts without making a strategic choice."""
    from pybothack.delegator import Handler
    from pybothack.handlers import register_handler
    from pybothack.util import PRIORITY_TOP
    register_handler(bh, PRIORITY_TOP - 2,
                     Handler(still_climb=lambda _prompt: True))


def strip_strategic_handlers(bh):
    """Prevent deferred mainbot strategy loading while keeping plumbing.

    At factory time mainbot has not been loaded yet.  Existing
    ``choose_action`` handlers are one-shot inventory/discovery refreshes and
    must remain; deleting them makes the experimental policy blind.
    """
    plumbing_ids = {id(handler) for _p, _s, handler in bh.delegator.handlers}
    disabled = 0
    for _priority, _seq, handler in list(bh.delegator.handlers):
        # bh36 defers mainbot.init() until the ``started`` event.  Neutralize
        # that loader before it can add the original strategy after this
        # function has removed the selectors already present.
        if hasattr(handler, "started"):
            original_started = handler.started

            def start_with_prompt_plumbing(original_started=original_started):
                # mainbot contributes useful generic prompt/menu responders as
                # well as strategy handlers. Load it, then remove only the
                # newly-added action selectors.
                # Policy handlers installed after this function was called
                # are protected too (they are already in the list now).
                keep_ids = {id(handler0) for _p0, _s0, handler0
                            in bh.delegator.handlers}
                original_started()

                def remove_strategy_handlers():
                    for _p2, _s2, handler2 in list(bh.delegator.handlers):
                        if (id(handler2) not in plumbing_ids
                                and id(handler2) not in keep_ids
                                and not hasattr(handler2, "still_climb")
                                and hasattr(handler2, "choose_action")):
                            bh.delegator.deregister(handler2)

                # mainbot registers through the delegator while it is busy;
                # schedule cleanup after those queued registrations execute.
                bh.delegator._send(remove_strategy_handlers)

            handler.started = start_with_prompt_plumbing
            disabled += 1
    return disabled


def game_state(game, radius=6):
    from pybothack.dungeon import branch_key, curlvl, curlvl_tags, monster_at
    from pybothack.itemid import item_name
    from pybothack.position import at, position

    player = game.get("player") or {}
    pos = position(player)
    level = curlvl(game)
    rows = []
    features = []
    monsters = []
    floor_items = []
    for y in range(max(1, pos.y - radius), min(21, pos.y + radius) + 1):
        cells = []
        for x in range(max(0, pos.x - radius), min(79, pos.x + radius) + 1):
            tile = at(level, x, y)
            mon = monster_at(level, tile)
            glyph = str(tile.get("glyph") or " ")[:1]
            feature = tile.get("feature")
            token = glyph
            if feature:
                token += "{" + str(feature)[:12] + "}"
            if tile.get("items"):
                labels = [i.get("label", "item") for i in
                          list(tile.get("items"))[:5]]
                floor_items.append({"dx": x - pos.x, "dy": y - pos.y,
                                    "items": labels})
                token += "[item]"
            if mon:
                m = {k: json_safe(mon.get(k)) for k in
                     ("glyph", "type", "peaceful", "friendly")
                     if mon.get(k) is not None}
                monsters.append({"dx": x - pos.x, "dy": y - pos.y, **m})
                token += "<monster>"
            if feature:
                features.append({"dx": x - pos.x, "dy": y - pos.y,
                                 "feature": feature})
            cells.append(token)
        rows.append(cells)
    inv = []
    for slot, item in (player.get("inventory") or {}).items():
        try:
            name = item_name(game, item)
        except Exception:
            name = item.get("label")
        inv.append({"slot": str(slot), "name": name,
                    "label": item.get("label"), "quantity": item.get("quantity"),
                    "buc": item.get("buc"), "worn": bool(item.get("worn")),
                    "wielded": bool(item.get("wielded"))})
    return {
        "turn": game.get("turn"), "level": str(game.get("dlvl")),
        "branch": str(branch_key(game)), "level_tags": list(curlvl_tags(game)),
        "position": {"x": pos.x, "y": pos.y},
        "player": {k: json_safe(player.get(k)) for k in
                   ("hp", "maxhp", "xplvl", "ac", "pw", "maxpw", "hunger",
                    "state", "alignment", "trapped")},
        "inventory": inv,
        "map_origin": {"x": pos.x, "y": pos.y, "radius": radius},
        "local_map": rows, "visible_features": features,
        "visible_monsters": monsters, "visible_items": floor_items,
        "last_action": action_summary(game.get("last-action")),
        "messages": [str(game.get("last-topline") or "")][-1:],
    }


def candidate(description, action, intent=None):
    return {"description": description, "action": action,
            "intent": intent or description}


def unique_candidates(entries):
    result = OrderedDict()
    seen = set()
    for key, value in entries:
        if value is None or value.get("action") is None:
            continue
        action = value["action"]
        sig = (action.get("type"), str(action.get("dir")),
               str(action.get("slot")), str(action.get("pos")))
        if sig in seen:
            continue
        seen.add(sig)
        result[key] = value
    return result
