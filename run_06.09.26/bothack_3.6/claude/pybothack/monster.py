"""Port of bothack.monster."""
from .frame import inverse, non_inverse
from .montype import (appearance_to_monster, has_drowning_attack,
                      passive_type, corrosive_type, name_to_monster)


def type_map(m):
    """`(:type m)` as a map, or {} - Clojure's keyword lookup is nil-safe.

    A monster's `:type` is not always a MonsterType.  `by-description` returns a
    plain String for every player rank, because `rank->monster` is
    `(comp by-rank-map string/lower-case)` and `by-rank-map` maps a rank to a
    *role name*.  The original stores that String as `:type` and every later
    `(:tags (:type m))` quietly yields nil.

    In Python `"caveman" or {}` is `"caveman"`, so the idiom this replaces -
    `type_map(m).get('tags')` - raises AttributeError instead.  It had
    never fired only because a TypeError in the farlook handler aborted before
    the String was ever stored; fixing that one unmasked fourteen of these.
    """
    t = m.get('type') if m else None
    return t if isinstance(t, dict) else {}


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
    return type_map(m).get('name')


def shopkeeper(m):
    return typename(m) == "shopkeeper"


def high_priest(m):
    return typename(m) == "high priest"


def demon_lord(m):
    # (every? #{:demon :prince} tags) - vacuously true for an unknown type
    tags = type_map(m).get('tags') or ()
    return all(t in ('demon', 'prince') for t in tags)


def oracle(m):
    return typename(m) == "Oracle"


def medusa(m):
    return typename(m) == "Medusa"


def pudding(m):
    return typename(m) in ("black pudding", "brown pudding")


def unique(m):
    return (type_map(m).get('gen-flags') or set()) and 'unique' in (
        type_map(m).get('gen-flags') or set())


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
    return 'were' in (type_map(m).get('tags') or ())


def drowner(m):
    return has_drowning_attack(type_map(m))


def flies(m):
    return 'fly' in (type_map(m).get('tags') or ())


def covetous(m):
    tags = type_map(m).get('tags') or ()
    return any(t in tags for t in ('covetous', 'wants-arti', 'wants-amulet',
                                   'wants-book'))


def steals(m):
    if covetous(m):
        return True
    for a in (type_map(m).get('attacks') or ()):
        if a.get('damage-type') in ('steal-amulet', 'steal-items'):
            return True
    return False


def ignores_e(m):
    return 'elbereth' in (type_map(m).get('resistances') or ())


def sees_invisible(m):
    return 'see-invis' in (type_map(m).get('tags') or ())


def follower(m):
    return 'follows' in (type_map(m).get('tags') or ())


def amphibious(m):
    return 'amphibious' in (type_map(m).get('tags') or ())


def _tagpred(tag):
    def p(m):
        return tag in (type_map(m).get('tags') or ())
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
    return passive_type(type_map(m))


def corrosive(m):
    # (corrosive-type? (:type m)) - a String :type yields nil for (:attacks _),
    # so the original is vacuously false rather than an error.
    t = type_map(m)
    return corrosive_type(t) if t else False


def slow(m):
    t = type_map(m)
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
    # (map->Monster {...}) fills every *declared* record field the literal
    # omits with nil, so :awake is present-and-nil rather than absent.  It has
    # to be here too: `hasheq` counts map entries, so a missing key changes the
    # monster's hash and with it the order `hostile-threats`' set iterates -
    # which is what picks the monster `fight` baits.  See monster_hasheq.
    mtype = appearance_to_monster.get(glyph, {}).get(color)
    return {'x': x, 'y': y, 'known': known, 'first-known': known,
            'glyph': glyph, 'color': non_inverse(color), 'type': mtype,
            'awake': None,
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
    h = _TYPE_HASH.get(key)
    if h is None:
        # port: monster types added for 3.6.7 (Keystone Kops, Twoflower,
        # guide) have no dumped Clojure hash; a deterministic stand-in keeps
        # hash-ordered collections stable.  Raising here crashed the fight
        # handler against any Kop (planes scenarios, 2026-09-22).
        h = _TYPE_HASH[key] = murmur3_hash_int(java_string_hash(key))
    return h


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


# The record's declared fields, which `map->Monster` always materialises (nil
# when the literal omits them).  A dict missing one of these is not a faithful
# Monster: it has fewer map entries than the record, so it hashes differently
# and lands elsewhere in a set's iteration order.  Checked rather than assumed,
# because the symptom is a silently different monster choice hundreds of turns
# later.
MONSTER_BASE_FIELDS = ('x', 'y', 'known', 'glyph', 'color', 'type', 'awake',
                       'friendly', 'peaceful', 'remembered')


def monster_hasheq(m):
    """`hasheq` of a bothack.monster.Monster record."""
    missing = [k for k in MONSTER_BASE_FIELDS if k not in m]
    if missing:
        raise KeyError("monster %r is missing declared record field(s) %s; "
                       "map->Monster would have them as nil and the hash "
                       "counts them" % (m, missing))
    return clj_record_hasheq(MONSTER_TYPE_HASH, m.items(), _field_hasheq)
