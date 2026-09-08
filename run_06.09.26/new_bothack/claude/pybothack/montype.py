"""Port of bothack.montype - monster type data and lookups.

The monster table itself is the one from the original (extracted verbatim).
"""
import re

from ._load import DATA
from .util import re_first_groups, re_seq

RANGED = {'spit', 'breath', 'gaze'}       # ranged attack types

monster_types = DATA['monster-types']
shopkeepers = DATA['shopkeepers']
role_ranks = DATA['role-ranks']


def passive_type(monster):
    atks = monster.get('attacks') or []
    return all(a.get('type') == 'passive' for a in atks)


def corrosive_type(montype):
    """Corrodes weapon passively when hit?"""
    for a in (montype.get('attacks') or []):
        if a.get('type') == 'passive' and a.get('damage-type') in ('corrode',
                                                                   'acid'):
            return True
    return False


def has_drowning_attack(m):
    if not m:
        return False
    return any(a.get('damage-type') == 'wrap' for a in (m.get('attacks') or []))


# {glyph => {color => MonsterType}}, only unambiguous
def _build_appearance_map():
    m = {}
    for mon in monster_types:
        g = m.setdefault(mon['glyph'], {})
        g[mon['color']] = ':ambiguous' if mon['color'] in g else mon
    res = {}
    for glyph, colors in m.items():
        res[glyph] = {c: mon for c, mon in colors.items()
                      if mon != ':ambiguous'}
    res.setdefault(' ', {})
    res[' '][None] = res.get('X', {}).get(None)
    return res


appearance_to_monster = _build_appearance_map()

_by_name = {}
for _m in monster_types:
    _by_name[_m['name']] = _m
    _by_name[_m['name'].lower()] = _m


def name_to_monster(name):
    if name is None:
        return None
    return _by_name.get(name.lower())


_by_rank = {}
for _role, _ranks in role_ranks.items():
    for _r in _ranks:
        _by_rank[_r] = _role


def rank_to_monster(desc):
    if desc is None:
        return None
    return _by_rank.get(desc.lower())


def _strip_modifier(desc):
    for pre, n in (("saddled invisible ", 18), ("invisible ", 10),
                   ("saddled ", 8)):
        if desc.startswith(pre):
            return desc[n:]
    return desc


def _strip_disposition(desc):
    if desc.startswith("tame "):
        return desc[5:]
    if desc.startswith("peaceful "):
        return desc[9:]
    if desc.startswith("guardian "):
        return desc if " naga" in desc else desc[9:]
    return desc


def _strip_article(desc):
    for pre, n in (("a ", 2), ("an ", 3), ("the ", 4), ("your ", 5)):
        if desc.startswith(pre):
            return desc[n:]
    return desc


def by_description(text):
    """Return MonsterType by farlook description."""
    desc = _strip_modifier(_strip_disposition(_strip_article(text)))
    ghost_or_called = re_seq(r'ghost|called', desc)

    if desc == "tail of a peaceful long worm":
        return name_to_monster("long worm tail")
    if re_seq(r'^(?:the )?high priest(?:ess)?$', desc):
        return name_to_monster("high priest")
    if desc == "mimic":
        return name_to_monster("large mimic")   # could be any mimic really
    if not re_seq(r'Minion of Huhetotl| Yendor', desc) and not ghost_or_called:
        g = re_first_groups(r'(.*) of (.*)', desc)
        if g:
            d2 = g[0]
            if re_seq(r'poohbah|priest|priestess', d2):
                r = (name_to_monster("high priest") if "high " in d2
                     else name_to_monster("aligned priest"))
            elif d2.startswith("guardian "):
                r = name_to_monster(d2[9:])
            else:
                r = name_to_monster(d2)
            if r is None:
                raise ValueError("Failed to parse monster-of description: "
                                 + text)
            return r
    if (not ghost_or_called and "Neferet the Green" not in desc
            and "Vlad the Impaler" not in desc):
        g = re_first_groups(r'(.*) the (.*)', desc)
        if g:
            r = name_to_monster(_strip_modifier(g[1]))
            if r is not None:
                return r
    g = re_first_groups(r'(.*) called (.*)', desc)
    if g:
        r = name_to_monster(g[0])
        if r is not None:
            return r
    if re_seq(r"'?s? ghost", desc):
        r = name_to_monster("ghost")
        if r is not None:
            return r
    if "coyote - " in desc:
        r = name_to_monster("coyote")
        if r is not None:
            return r
    if desc in shopkeepers:
        r = name_to_monster("shopkeeper")
        if r is not None:
            return r
    r = name_to_monster(desc)
    if r is not None:
        return r
    r = rank_to_monster(desc)
    if r is not None:
        return r
    raise ValueError("Failed to parse monster description: " + text)
