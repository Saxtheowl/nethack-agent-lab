"""Tile memory translated from tile.clj, GPL-2.0, 2026-09-06."""
TRAPS = frozenset("trap antimagic arrowtrap beartrap darttrap firetrap hole magictrap rocktrap mine levelport pit polytrap portal bouldertrap rusttrap sleeptrap spikepit squeaky teletrap trapdoor web statuetrap".split())
DOORS = frozenset("door-open door-closed door-locked door-secret".split())
WALKABLE = frozenset("ice floor altar door-open sink fountain corridor throne grave stairs-up stairs-down drawbridge-lowered cloud".split())
FIELDS = "x y glyph color item-glyph item-color feature seen first-walked walked dug searched items new-items engraving engraving-type deaths tags room".split()


def initial_tile(x, y):
    return dict.fromkeys(FIELDS) | dict(x=x, y=y, glyph=" ", seen=False, dug=False, searched=0,
                                       items=[], deaths=[], tags=set(), **{"new-items": False})


def monster_glyph(glyph):
    return (glyph.isalnum() and glyph not in "80") or glyph in "&@';:~"


def monster(glyph, color):
    return (glyph != "~" and monster_glyph(glyph) and (color is not None or glyph != ":")) or (glyph == "~" and color == "brown")


def item(glyph, color):
    return glyph in '\")[!?/=+*(`80$%,' or (color is not None and glyph == "_") or (color is None and glyph in ":]")


def boulder(tile):
    return tile.get("glyph") == "8" and tile.get("color") is None


def trap(tile):
    return tile.get("feature") in TRAPS or tile.get("feature") == "cloud"


def walkable(tile):
    return not boulder(tile) and (tile.get("feature") is None or trap(tile) or tile.get("feature") in WALKABLE)


def transparent(tile):
    return (not boulder(tile) and tile.get("feature") not in {"rock", "wall", "tree", "door-closed", "cloud"}
            and bool(tile.get("feature") or tile.get("monster") or tile.get("items")))


def diggable(tile):
    if boulder(tile):
        return True
    if tile.get("feature") not in {"rock", "wall", "door-closed", "door-locked", "door-secret"}:
        return None
    return 0 < tile["x"] < 79 and 0 < tile["y"] < 21 and not tile.get("undiggable")


def fountain(tile):
    return tile.get("feature") == "fountain" and "trickle" not in (tile.get("tags") or ())


def engravable(tile):
    return (walkable(tile) and tile.get("feature") not in {"pool", "lava", "altar", "grave"}
            and not fountain(tile) and tile.get("engraving-type") in (None, "dust"))


def walkable_by(tile, glyph):
    feature = tile.get("feature")
    if glyph not in "I12345EXP" and feature in DOORS:
        new_feature = "door-open"
    elif glyph not in "I12345EX" and feature in {"rock", "wall", "tree", "drawbridge-raised"}:
        new_feature = None
    else:
        new_feature = feature
    dug = tile.get("dug")
    if dug is None or dug is False:
        dug = diggable(tile)
        if dug is not None and dug is not False:
            dug = glyph if glyph in "Uphr" else None
    return tile | {"feature": new_feature, "dug": dug}


def infer_feature(current, glyph, color):
    if glyph == " ": return current
    if glyph == ".": return current if current in TRAPS else {"cyan": "ice", "brown": "drawbridge-lowered"}.get(color, "floor")
    if glyph == "<": return "stairs-up"
    if glyph == ">": return "stairs-down"
    if glyph == "\\": return "throne" if color == "yellow" else "grave"
    if glyph == "{": return "sink" if color is None else "fountain"
    if glyph == "}": return {"green": "tree", "red": "lava", "cyan": "bars", "blue": "pool", "brown": "drawbridge-raised"}.get(color, current)
    if glyph == "#": return current if current in TRAPS or current == "cloud" else "corridor"
    if glyph == "_": return "altar" if color is None else current
    if glyph == "~": return "pool"
    if glyph == "^": return current if current in TRAPS else "trap"
    if glyph == "]": return "door-closed"
    if glyph in "|-": return "door-open" if color == "brown" else "door-secret" if current == "door-secret" else "wall"
    raise ValueError(f"Unknown terrain glyph {glyph!r}")


def reset_item(tile):
    return tile | {"item-color": None, "item-glyph": None, "items": [], "new-items": False}


def parse_tile(tile, glyph, color):
    if tile.get("glyph") == glyph and tile.get("color") == color:
        return tile
    result = dict(tile)
    if item(glyph, color):
        if not result.get("items") and result.get("feature") in {"rock", "wall", "door-closed", "door-locked", "drawbridge-raised", "door-secret", "pool"}:
            result["feature"] = None
        if glyph == "8":
            if monster(result["glyph"], result.get("color")):
                result["new-items"] = True
        elif glyph == result.get("item-glyph") and (result.get("item-color") is None or result["item-color"] == color):
            result["item-color"] = color
        else:
            result.update({"new-items": True, "item-glyph": glyph, "item-color": color})
    elif not monster(glyph, color) and glyph != " ":
        result = reset_item(result)
    if monster(glyph, color):
        result = walkable_by(result, glyph)
    elif not item(glyph, color):
        result["feature"] = infer_feature(result.get("feature"), glyph, color)
    if result["searched"] == 0 and tile.get("feature") in {"wall", "rock"} and result.get("feature") in {"corridor", "floor"}:
        result["dug"] = True
    result.update(glyph=glyph, color=color, thump=None)
    if result.get("feature") in {"wall", "door-closed", "pool", "lava"}:
        result["seen"] = True
    return result


def lootable_items(tile):
    return [item for container in tile["items"] if container.get("cost") is None for item in container.get("items", [])]


def has_elbereth(tile):
    return "Elbereth" in (tile.get("engraving") or "")


def permanent_elbereth(tile):
    return has_elbereth(tile) and tile.get("engraving-type") == "permanent"
