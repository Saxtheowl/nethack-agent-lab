"""Port of bothack.behaviors."""
from .actions import Apply, Dip, Read, descend, unbag, with_reason
from .dungeon import at_player, get_level
from .item import BELL, BOOK, CANDELABRUM, blessed, candle, holy_water
from .player import OPPOSITE_ALIGNMENT, have, inventory_slot
from .pathing import seek, seek_level
from .tile import altar_p, stairs_down_p


def _invocation_complete(game):
    return stairs_down_p(at_player(game))


def attach_candles(game):
    c = have(game, CANDELABRUM)
    assert c
    if c[1].get('candles') != 7:
        found = have(game, candle)
        if found:
            return with_reason("attaching candles to candelabrum",
                               Apply(found[0]))
    return None


def _handle_candelabrum(game):
    found = have(game, CANDELABRUM)
    if not found:
        return None
    slot, cand = found
    if ((cand.get('lit') and _invocation_complete(game))
            or (not cand.get('lit') and not _invocation_complete(game))):
        return with_reason("lighting or snuffing out candelabrum", Apply(slot))
    return None


def _ring_bell(game):
    if (_invocation_complete(game)
            or (game.get('last-topline') or "").endswith(
                " issues an unsettling shrill sound...")):
        return None
    found = have(game, BELL)
    if found:
        return with_reason("ringing the bell", Apply(found[0]))
    return None


def _read_book(game):
    if _invocation_complete(game):
        return None
    found = have(game, "Book of the Dead")
    if found:
        return with_reason("reading the book", Read(found[0]))
    return None


def bless(game, slot):
    """Take holy water out of a bag (if bagged) and dip item at slot into it"""
    item = inventory_slot(game, slot)
    if item and not blessed(item):
        found = have(game, holy_water, {'bagged'})
        if found:
            water_slot, water = found
            return with_reason("blessing", item,
                               unbag(game, water_slot, water)
                               or Dip(slot, water_slot))
    return None


def uncurse_invocation_artifacts(game):
    found = have(game, {BELL, CANDELABRUM, BOOK}, {'unsafe-buc'})
    if found:
        return with_reason("making sure invocation artifacts are not cursed",
                           bless(game, found[0]))
    return None


def invocation(game):
    if get_level(game, 'main', 'sanctum'):
        return None
    return (seek_level(game, 'main', 'end')
            or seek(game, lambda t: t.get('vibrating'))
            or attach_candles(game)
            or uncurse_invocation_artifacts(game)
            or _handle_candelabrum(game)
            or _ring_bell(game)
            or _read_book(game)
            or descend(game))


def seek_high_altar(game):
    player = game['player']
    if (player['alignment'] != 'neutral'
            and have(game, "helm of opposite alignment",
                     {'bagged', 'can-use'})):
        align = {player['alignment'],
                 OPPOSITE_ALIGNMENT[player['alignment']]}
    else:
        align = {player['alignment']}
    return with_reason("seeking high altar",
                       seek(game, lambda t: (altar_p(t)
                                             and (t.get('alignment') in align
                                                  or not t.get('walked')))))


def pray(game):
    from .game import can_pray
    from .actions import Pray
    if can_pray(game):
        return with_reason("pray", Pray())
    return None


def enhance(game):
    from .actions import enhance_all
    if game['player'].get('can-enhance'):
        return enhance_all()
    return None
