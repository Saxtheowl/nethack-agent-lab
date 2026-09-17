"""NetHack 3.6.7 rules that BotHack (written for 3.4.3) relied on.

Every function cites the 3.6.7 source it reproduces.  The strategy code calls
these instead of its 3.4.3 assumptions.
"""
import re

from .dungeon import at_planes, branch_key, in_gehennom
from .monster import ignores_e, typename

# --------------------------------------------------------------- Elbereth
#
# monmove.c onscary():
#   sengr_at("Elbereth", x, y, TRUE)                 exact text only
#   && hero on the square (or displaced image)
#   && !(isshk || isgd || blind || peaceful || S_HUMAN || minotaur
#        || Inhell || In_endgame)
#   (+ Rodney, lawful minions, Angels, Riders, shopkeepers/priests at home)
# mon.c setmangry(): attacking a monster that respects it (or a peaceful)
# while standing on Elbereth: "You feel like a hypocrite.", alignment -5,
# engraving erased.
# engrave.c: appending to an engraving makes "ElberethElbereth", which is
# not an exact match -> useless.

ELBERETH_RE = re.compile(r"^\s*elbereth\s*$", re.I)


def strict_elbereth_text(text):
    """engrave.c sengr_at(..., strict=TRUE): the whole engraving must read
    Elbereth (fuzzymatch ignoring case)."""
    return bool(text) and bool(ELBERETH_RE.match(text))


def elbereth_effective_here(game):
    """False where 3.6.7 ignores Elbereth entirely: Gehennom (Valley and
    below, including Rodney's tower levels) and the endgame planes."""
    if at_planes(game) or in_gehennom(game):
        return False
    if branch_key(game) in ('wiztower',):
        return False
    return True


def respects_elbereth(monster):
    """Would this monster be scared by a valid Elbereth under the hero?"""
    if monster is None:
        return False
    if ignores_e(monster):       # BotHack data: @ humans, minotaurs, shk...
        return False
    if monster.get('peaceful'):
        return False
    if monster.get('glyph') == '@':
        return False
    name = typename(monster) or ''
    if name in ('minotaur', 'shopkeeper', 'guard', 'watchman',
                'watch captain', 'Angel', 'Wizard of Yendor'):
        return False
    return True


# ----------------------------------------------------------------- prayer

def xlev_to_rank(xl):
    """role.c xlev_to_rank(): 1..30 -> 0..8"""
    if xl <= 2:
        return 0
    if xl <= 30:
        return (xl + 2) // 4
    return 8


def critically_low_hp(player):
    """pray.c critically_low_hp(FALSE), 3.6.7 thresholds (3.4.3 was
    hp < 1/7 max or <= 5)."""
    hp = player.get('hp')
    maxhp = player.get('maxhp')
    xl = player.get('xplvl') or 1
    if hp is None or maxhp is None:
        return False
    hplim = 15 * xl
    if maxhp > hplim:
        maxhp = hplim
    rank = xlev_to_rank(xl)
    if rank <= 1:
        divisor = 5
    elif rank <= 3:
        divisor = 6
    elif rank <= 5:
        divisor = 7
    elif rank <= 7:
        divisor = 8
    else:
        divisor = 9
    return hp <= 5 or hp * divisor <= maxhp


HYPOCRITE_PRAYER_BLOCK = 1000   # turns without prayer after a -5 alignment


def prayer_blocked(game):
    """After "You feel like a hypocrite." the alignment may be negative;
    pray.c then treats every prayer as 'too naughty' (smiting instead of
    fixing).  Do not pray for a while."""
    t = game.get('hypocrite-turn')
    return t is not None and (game.get('turn') or 0) - t < \
        HYPOCRITE_PRAYER_BLOCK


# ---------------------------------------------------------------- farming
#
# fixes36.0 "cloned creatures (of any type) don't deathdrop items",
# exper.c experience(): diminishing XP for revived/cloned monsters,
# mon.c: puddings leave globs.  BotHack's pudding farm produced most of the
# score and items of its 3.4.3 ascensions; in 3.6.7 it produces neither, and
# farm-done? (score > 6M/15M) would never become true.
#
# Replacement: no farming at all.  farm-done? keeps its only non-score arm
# (Rodney's tower known), so the progression that was gated on it behaves as
# the original did *before* its farm was complete, which is the path that
# does not depend on farm output.

FARMING_ENABLED = False


# ------------------------------------------------------------- profiles
#
# "full" (default) is BotHack's own progression: Mines to Minetown, Sokoban,
# quest portal, Mines end, every main level explored in order.
# "fast" is a declared strategy change for assisted runs and deep scenarios:
# no Mines/Sokoban detour (3.6.7 tower.des guarantees 8-16 candles in Vlad's
# Tower, next to the Candelabrum) and no going back up to finish exploring
# shallower main levels.  The profile is recorded in every game manifest.

import os as _os

def fast_profile():
    return _os.environ.get('BOTHACK_PROFILE', 'full') == 'fast'


def assisted_tactics():
    """BOTHACK_TACTICS=assisted: with the invincibility assist, retreating
    (fleeing upstairs, praying/Elbereth for HP, resting to heal) only wastes
    time and causes up/down loops.  Declared in the manifest; the survival
    tactics stay available with BOTHACK_TACTICS=normal."""
    return _os.environ.get('BOTHACK_TACTICS', 'normal') == 'assisted'


def skipped_steps():
    """BOTHACK_SKIP=quest-portal,quest,... : full-explore steps to skip, for
    scenarios that test one stage in isolation (recorded in the manifest).
    Steps: minetown, sokoban, quest-portal, mines-end, dlvl20, quest,
    excalibur, vlad, wiztower."""
    v = _os.environ.get('BOTHACK_SKIP', '')
    return frozenset(s.strip() for s in v.split(',') if s.strip())



def farm_done36(game):
    from .pathing import visited
    return bool(visited(game, 'wiztower'))
