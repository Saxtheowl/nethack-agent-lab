"""Faithful rewrite of bothack.tile (BotHack by krajj7).

A Tile is a dict: x, y, glyph, color, item-glyph, item-color, feature, seen,
first-walked, walked, dug, searched, items, new-items, engraving, engraving-type,
deaths, tags, room, branch-id, alignment, pushed, thump, undiggable, ...
"""

from . import util

traps = {"trap", "antimagic", "arrowtrap", "beartrap", "darttrap", "firetrap",
         "hole", "magictrap", "rocktrap", "mine", "levelport", "pit", "polytrap",
         "portal", "bouldertrap", "rusttrap", "sleeptrap", "spikepit", "squeaky",
         "teletrap", "trapdoor", "web", "statuetrap"}

trap_names = {
    "magic portal": "portal", "level teleporter": "levelport",
    "teleportation trap": "teletrap", "bear trap": "beartrap",
    "falling rock trap": "rocktrap", "rolling boulder trap": "bouldertrap",
    "rust trap": "rusttrap", "magic trap": "magictrap",
    "anti-magic field": "antimagic", "polymorph trap": "polytrap",
    "fire trap": "firetrap", "arrow trap": "arrowtrap",
    "statue trap": "statuetrap", "land mine": "mine", "dart trap": "darttrap",
    "sleeping gas trap": "sleeptrap", "spider web": "web", "web": "web",
    "squeaky board": "squeaky", "hole": "hole", "trap door": "trapdoor",
    "pit": "pit", "spiked pit": "spikepit",
}


def digit(tile):
    return str(tile.get("glyph", "")).isdigit()


def monster_glyph(glyph):
    import re
    if glyph is None:
        return False
    return (glyph.isalnum() and glyph not in ("8", "0")) or glyph in "&@';:~"


def monster_tile(tile_or_glyph, color=True):
    if isinstance(tile_or_glyph, dict):
        glyph, color = tile_or_glyph.get("glyph"), tile_or_glyph.get("color")
        return monster_impl(glyph, color)
    return monster_impl(tile_or_glyph, color)


def monster_impl(glyph, color):
    if glyph and monster_glyph(glyph):
        if glyph == "~":
            return color == "brown"
        if color or glyph != ":":
            return glyph != "~"
        return False
    return False


def item_tile(tile):
    return item_impl(tile.get("glyph"), tile.get("color"))


def item_impl(glyph, color):
    if glyph in '")\[!?/=+*(\`80$%,':
        return True
    if glyph == "_":
        return color is not None
    if color is None:
        return glyph in (":", "]")
    return False


def dug(tile):
    return tile.get("dug")


def unknown(tile):
    return tile.get("feature") is None


def boulder(tile):
    return tile.get("glyph") == "8" and tile.get("color") is None


def door(tile):
    return tile.get("feature") in ("door-open", "door-closed", "door-locked",
                                   "door-secret")


def drawbridge(tile):
    return tile.get("feature") in ("drawbridge-lowered", "drawbridge-raised")


def stairs(tile):
    return tile.get("feature") in ("stairs-up", "stairs-down")


def opposite_stairs(feature):
    return "stairs-down" if feature == "stairs-up" else "stairs-up"


def has_feature(tile, feature):
    return feature == tile.get("feature")


def _pred(feature):
    def p(tile):
        return has_feature(tile, feature)
    p.__name__ = feature + "_pred"
    return p


_globals = globals()
for _f in traps | {"rock", "floor", "wall", "stairs-up", "stairs-down",
                   "corridor", "altar", "pool", "door-open", "door-closed",
                   "door-locked", "door-secret", "sink", "grave", "throne",
                   "bars", "drawbridge-raised", "drawbridge-lowered",
                   "lava", "ice", "portal", "tree", "trapdoor", "hole",
                   "firetrap", "cloud", "polytrap"}:
    _globals[_f.replace("-", "_")] = _pred(_f)


def fountain(tile):
    return tile.get("feature") == "fountain" and "trickle" not in (
        tile.get("tags") or set())


def trap(tile):
    return tile.get("feature") in traps or _globals["cloud"](tile)


def unknown_trap(tile):
    return tile.get("feature") == "trap"


def blank(tile):
    return tile.get("glyph") == " "


def walkable(tile):
    return (not boulder(tile)
            and (unknown(tile) or trap(tile)
                 or tile.get("feature") in
                 ("ice", "floor", "altar", "door-open", "sink", "fountain",
                  "corridor", "throne", "grave", "stairs-up", "stairs-down",
                  "drawbridge-lowered", "cloud")))


def diagonal_walkable(game, tile):
    return not _globals["door-open"](tile)


def transparent(tile):
    f = tile.get("feature")
    return (not boulder(tile)
            and f not in ("rock", "wall", "tree", "door-closed", "cloud")
            and (f is not None or tile.get("monster") or tile.get("items")))


def diggable(tile):
    return (boulder(tile)
            or (tile.get("feature") in ("rock", "wall", "door-closed",
                                        "door-locked", "door-secret")
                and 0 < tile.get("x", 0) < 79 and 0 < tile.get("y", 0) < 21
                and not tile.get("undiggable")))


def e(tile):
    eng = tile.get("engraving")
    return bool(eng and "Elbereth" in eng)


def perma_e(tile):
    return e(tile) and tile.get("engraving-type") == "permanent"


def engravable(tile):
    return (walkable(tile)
            and not (_globals["pool"](tile) or _globals["lava"](tile)
                     or _globals["fountain"](tile) or _globals["altar"](tile)
                     or _globals["grave"](tile))
            and (tile.get("engraving-type") is None
                 or tile.get("engraving-type") == "dust"))


def temple(tile):
    return tile.get("room") == "temple"


def visited_stairs(tile):
    return stairs(tile) and tile.get("branch-id") is not None


def unexplored(tile):
    return not boulder(tile) and unknown(tile)


def blocked(tile):
    return (tile.get("blocked") or 0) > 12


shop_types = {
    "general store": "general", "used armor dealership": "armor",
    "second-hand bookstore": "book", "liquor emporium": "potion",
    "antique weapons outlet": "weapon", "delicatessen": "food",
    "jewelers": "gem", "quality apparel and accessories": "wand",
    "hardware store": "tool", "rare books": "book", "lighting store": "light",
}

shops = {"shop"} | set(shop_types.values())


def shop(tile):
    return tile.get("room") in shops


def mark_death(tile, monster, turn):
    deaths = tile.get("deaths") or []
    return util.assoc(tile, "deaths", deaths + [[turn, monster]],
                      "new-items", True)


def lootable_items(tile):
    out = []
    for container in tile.get("items") or []:
        if not container.get("cost"):
            out.extend(container.get("items") or [])
    return out


def initial_tile(x, y):
    return {"x": x, "y": y, "glyph": " ", "seen": False, "dug": False,
            "searched": 0, "items": [], "deaths": [], "new-items": False,
            "tags": set()}


def parse_tile(tile, new_glyph, new_color):
    """bothack.tile/parse-tile (simplified faithful port)."""
    if new_color != tile.get("color") or new_glyph != tile.get("glyph"):
        t = dict(tile)
        t["glyph"] = new_glyph
        t["color"] = new_color
        t["thump"] = None
        return t
    return tile