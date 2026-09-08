"""Port of bothack.monster."""
from .frame import inverse, non_inverse
from .montype import (appearance_to_monster, has_drowning_attack,
                      passive_type, corrosive_type, name_to_monster)


def hostile(m):
    return not m.get('peaceful') and not m.get('friendly')


def _default_peaceful(monster_type):
    if not monster_type:
        return None
    tags = monster_type.get('tags') or ()
    if 'hostile' in tags:
        return False
    return True if 'peaceful' in tags else None


def typename(m):
    t = m.get('type') if m else None
    return t.get('name') if t else None


def shopkeeper(m):
    return typename(m) == "shopkeeper"


def high_priest(m):
    return typename(m) == "high priest"


def demon_lord(m):
    # (every? #{:demon :prince} tags) - vacuously true for an unknown type
    tags = (m.get('type') or {}).get('tags') or ()
    return all(t in ('demon', 'prince') for t in tags)


def oracle(m):
    return typename(m) == "Oracle"


def medusa(m):
    return typename(m) == "Medusa"


def pudding(m):
    return typename(m) in ("black pudding", "brown pudding")


def unique(m):
    return ((m.get('type') or {}).get('gen-flags') or set()) and 'unique' in (
        (m.get('type') or {}).get('gen-flags') or set())


def priest(m):
    n = typename(m)
    return n is not None and "priest" in n


def unicorn(m):
    n = typename(m)
    return n is not None and " unicorn" in n


def mimic(m):
    n = typename(m)
    return n is not None and " mimic" in n


def werecreature(m):
    return 'were' in ((m.get('type') or {}).get('tags') or ())


def drowner(m):
    return has_drowning_attack(m.get('type'))


def flies(m):
    return 'fly' in ((m.get('type') or {}).get('tags') or ())


def covetous(m):
    tags = (m.get('type') or {}).get('tags') or ()
    return any(t in tags for t in ('covetous', 'wants-arti', 'wants-amulet',
                                   'wants-book'))


def steals(m):
    if covetous(m):
        return True
    for a in ((m.get('type') or {}).get('attacks') or ()):
        if a.get('damage-type') in ('steal-amulet', 'steal-items'):
            return True
    return False


def ignores_e(m):
    return 'elbereth' in ((m.get('type') or {}).get('resistances') or ())


def sees_invisible(m):
    return 'see-invis' in ((m.get('type') or {}).get('tags') or ())


def follower(m):
    return 'follows' in ((m.get('type') or {}).get('tags') or ())


def amphibious(m):
    return 'amphibious' in ((m.get('type') or {}).get('tags') or ())


def _tagpred(tag):
    def p(m):
        return tag in ((m.get('type') or {}).get('tags') or ())
    p.__name__ = tag + '_p'
    return p


mindless = _tagpred('mindless')
undead = _tagpred('undead')
sessile = _tagpred('sessile')
guard = _tagpred('guard')
human = _tagpred('human')
nasty = _tagpred('nasty')
rider = _tagpred('rider')
strong = _tagpred('strong')
infravisible = _tagpred('infravisible')


def spellcaster(m):
    return any(a.get('type') == 'magic' for a in (m.get('attacks') or ()))


def passive(m):
    # (passive-type? (:type m)) - vacuously true when the type is unknown
    return passive_type(m.get('type') or {})


def corrosive(m):
    t = m.get('type')
    return corrosive_type(t) if t else False


def slow(m):
    t = m.get('type')
    return bool(t and t.get('speed') is not None and t['speed'] < 7)


def leprechaun(m):
    return typename(m) == "leprechaun"


def titan(m):
    return typename(m) == "titan"


def rodney(m):
    return typename(m) == "Wizard of Yendor"


def known_monster(x, y, mtype):
    """Create a known monster on a known location (eg. Medusa on Medusa's)."""
    return {'x': x, 'y': y, 'glyph': mtype['glyph'], 'color': mtype['color'],
            'known': 0, 'first-known': 0, 'type': mtype, 'awake': False,
            'friendly': False, 'peaceful': _default_peaceful(mtype),
            'remembered': True}


def new_monster(x, y, known, glyph, color):
    mtype = appearance_to_monster.get(glyph, {}).get(color)
    return {'x': x, 'y': y, 'known': known, 'first-known': known,
            'glyph': glyph, 'color': non_inverse(color), 'type': mtype,
            'friendly': bool(inverse(color)),
            'peaceful': _default_peaceful(mtype), 'remembered': False}


def unknown_monster(x, y, turn):
    return new_monster(x, y, turn, 'I', None)


# ---------------------------------------------------------------- Clojure hash
#
# `hostile-threats` ends in `set`, so the bot holds its monsters in a
# PersistentHashSet and every `find-first`/`some`/`filter` over it walks the
# HAMT order of the elements' `hasheq`.  That order decides, among other
# things, which monster the "baiting monsters" branch of `fight` picks when two
# are at distance 2 - one fleeing, one not - and therefore whether the bot
# searches or steps.  Reproducing it needs `hasheq` for the Monster record.
#
# Verified against the JVM: tools/cljcmp/dump_hash.clj prints the same values
# and tests/test_clj_hash.py checks the port against that dump.

import json as _json
import os as _os

from .util import (clj_hasheq, clj_record_hasheq, murmur3_hash_long,
                   clj_keyword_hasheq, murmur3_hash_int, java_string_hash)

_HASHDATA = _json.load(open(_os.path.join(_os.path.dirname(__file__),
                                          '_hashdata.json')))
MONSTER_TYPE_HASH = _HASHDATA['record_type_hash']['bothack.monster.Monster']
_TYPE_HASH = _HASHDATA['monster_type_hash']

# Which Clojure type each Monster field holds.  The port stores Clojure
# keywords and Clojure strings both as Python `str`, so the value alone cannot
# say which hashing rule applies; this table can.  `defrecord` puts unlisted
# keys in __extmap, and they hash exactly like the declared ones.
_FIELD_KIND = {
    'x': 'long', 'y': 'long', 'known': 'long', 'first-known': 'long',
    'glyph': 'char', 'color': 'kw', 'type': 'type',
    'awake': 'bool', 'friendly': 'bool', 'peaceful': 'bool',
    'remembered': 'bool', 'fleeing': 'bool', 'just-moved': 'bool',
    'cancelled': 'bool',
}


def monster_type_hasheq(t):
    """hasheq of a MonsterType record - looked up in the dumped table.

    The 376 types are constants, so their hashes are data like the rest of
    montype; computing them would mean hashing nested attack records, tag sets
    and resistance maps for no gain.  `by-description` can also put a plain
    role *string* in :type (an upstream quirk the port keeps), which hashes as
    a String.
    """
    if t is None:
        return 0
    if isinstance(t, str):
        return murmur3_hash_int(java_string_hash(t))
    key = '%s\t%s\t%s' % (t.get('name'), t.get('glyph'), t.get('color'))
    try:
        return _TYPE_HASH[key]
    except KeyError:
        raise KeyError("no dumped hasheq for monster type %r; re-run "
                       "tools/cljcmp/dump_hash.clj" % (key,))


def _field_hasheq(k, v):
    if v is None:
        return 0
    kind = _FIELD_KIND.get(k)
    if kind == 'long':
        return murmur3_hash_long(int(v))
    if kind == 'char':
        return ord(v) if len(v) == 1 else murmur3_hash_int(java_string_hash(v))
    if kind == 'kw':
        return clj_keyword_hasheq(v)
    if kind == 'bool':
        return 1231 if v else 1237
    if kind == 'type':
        return monster_type_hasheq(v)
    if isinstance(v, bool):
        return 1231 if v else 1237
    if isinstance(v, int):
        return murmur3_hash_long(v)
    if isinstance(v, str):
        return clj_hasheq(v)
    raise KeyError("Monster field %r holds %r, whose Clojure type is not in "
                   "monster._FIELD_KIND" % (k, v))


def monster_hasheq(m):
    """`hasheq` of a bothack.monster.Monster record."""
    return clj_record_hasheq(MONSTER_TYPE_HASH, m.items(), _field_hasheq)
