"""Persistent-update helpers mirroring the Clojure idioms BotHack is built on.

BotHack keeps the whole game state in immutable maps and relies on cheap
snapshots (``(:last-state game)``) to diff turn-to-turn.  Python has no
persistent maps, so we emulate Clojure's structural sharing with
copy-on-write: every ``assoc``/``update_in`` shallow-copies only the maps
along the updated path and shares everything else.  Nothing in the port may
mutate a map in place.
"""




class CljMap(dict):
    """A dict that remembers the order Clojure would iterate it in.

    Clojure has two ways of building a map and they disagree:

    * ``(into {} pairs)`` runs through a **transient** array map, whose
      ``assoc!`` *appends*, and which becomes a PersistentHashMap from the
      **9th** entry;
    * a chain of persistent ``(assoc m k v)`` *prepends* each new key, and
      stays an array map until the **10th** entry.

    Both are verified against the original (the ``maporder`` differential
    cases).  The bot uses both on the same map: ``gather-monsters`` rebuilds
    ``(:monsters level)`` with ``into`` every frame, and ``reset-monster``
    ``assoc``es into it in between - and that order decides which monster
    ``examine-monsters`` looks at and how ``track-monsters`` pairs snapshots.

    Promotion is sticky: once a Clojure map has become a hash map it stays
    one, even if entries are removed again.
    """

    __slots__ = ('_order', '_promoted')

    #: a persistent assoc chain promotes on the assoc that would make the 10th
    _ASSOC_LIMIT = 9
    #: a transient (into) promotes on the assoc! that would make the 9th
    _INTO_LIMIT = 8

    def __init__(self, *a, **kw):
        dict.__init__(self, *a, **kw)
        self._order = list(dict.keys(self))
        self._promoted = False

    # ---------------------------------------------------------- construction
    @classmethod
    def from_into(cls, pairs):
        """(into {} pairs) - transient, appends, promotes at the 9th entry."""
        r = cls()
        for k, v in pairs:
            if k not in r:
                r._order.append(k)
            dict.__setitem__(r, k, v)
            if not r._promoted and len(r) > cls._INTO_LIMIT:
                r._promoted = True
        return r

    @classmethod
    def from_assoc(cls, m):
        """A plain dict treated as if built by a persistent assoc chain."""
        r = cls()
        for k, v in m.items():
            r._assoc_(k, v)
        return r

    def _copy(self):
        r = CljMap()
        dict.update(r, self)
        r._order = list(self._order)
        r._promoted = self._promoted
        return r

    def _assoc_(self, k, v):
        if k not in self:
            self._order.insert(0, k)      # persistent assoc prepends
        dict.__setitem__(self, k, v)
        if not self._promoted and len(self) > self._ASSOC_LIMIT:
            self._promoted = True

    def _dissoc_(self, k):
        if k in self:
            dict.__delitem__(self, k)
            self._order.remove(k)

    # ------------------------------------------------------------- iteration
    def clj_order(self):
        if self._promoted:
            return sorted(self._order, key=clj_hash_chunks)
        return list(self._order)


_CHUNK_CACHE = {}


_POSMOD = []


def clj_hash_chunks(k):
    """Clojure's HAMT ordering key for any map key the port uses."""
    if not _POSMOD:
        from . import position as _pm
        _POSMOD.append(_pm)
    pm = _POSMOD[0]
    HAMT_KEYS, hamt_chunks, Pos = pm.HAMT_KEYS, pm.hamt_chunks, pm.Pos
    if isinstance(k, Pos):
        return HAMT_KEYS[(k.x, k.y)]
    if isinstance(k, dict) and 'x' in k and 'y' in k:
        return HAMT_KEYS[(k['x'], k['y'])]
    # pure function of the key: memoize (inventory letters, keywords ...);
    # the key's type is part of the cache key because a CljStr and a str of
    # the same text hash differently in Clojure
    try:
        ck = (type(k), k)
        r = _CHUNK_CACHE.get(ck)
    except TypeError:
        ck = r = None
    if r is None:
        from .util import clj_hasheq
        r = hamt_chunks(clj_hasheq(k))
        if ck is not None and len(_CHUNK_CACHE) < 100000:
            _CHUNK_CACHE[ck] = r
    return r


class CljAssertionError(BaseException):
    """A failed `{:pre ...}`, modelled with Java's Error/Exception split.

    Clojure's `assert` throws `java.lang.AssertionError`, which extends `Error`,
    and BotHack's delegator catches only `Exception`:

        (try (apply method handler args)
             (catch Exception e (log/error e "Delegator caught handler exception")))

    So a precondition failure is *not* swallowed - it escapes the handler, the
    event dispatch and the agent.  Python's `AssertionError` is an `Exception`
    subclass, so a plain `assert` in the port would be caught and the handler
    merely skipped: the two would fail in different places for the same cause.
    Deriving from `BaseException` reproduces the split, since `except Exception`
    does not catch it.

    It also survives `python -O`, which strips `assert` statements outright -
    a fragility the original does not have.
    """


def clj_assert(cond, msg):
    """`{:pre [cond]}` - raise the way Clojure's assert does (see
    CljAssertionError)."""
    if not cond:
        raise CljAssertionError(msg)


class CljStr(str):
    """A Clojure **String**, as opposed to a Character.

    The port keeps both as Python `str`, and `Util.hasheq` hashes them
    differently: a Character hashes to its code point, a String to
    `Murmur3.hashInt(String.hashCode())`.  For a menu answer that difference is
    observable behaviour, because `(string/join options)` walks a
    PersistentHashSet in the hash order of its elements.

    Length is not a usable discriminator: `put-in-what` and `take-out-what`
    build their answers with `(str amt slot)`, which yields a **one-character
    String** whenever the amount is nil.  Keying on length made the port send
    `AGgiox` where the original sent `xGigAo` (seed 40005, put-in of six items
    into a bag).  So the producing site says which it is, and this type carries
    that decision to `clj_hasheq`.
    """
    __slots__ = ()


def clj_set_order(items, hasheq):
    """Iterate `items` the way `(set items)` iterates in Clojure.

    A PersistentHashSet is a HAMT with no small-size special case, so its seq
    order is simply the elements' hashes read as 5-bit chunks, least
    significant first - the same key `CljMap` uses once a map has promoted.
    `hasheq` is passed in rather than inferred: a monster is a dict with `x`
    and `y`, so `clj_hash_chunks` would hash it as a position.

    Sorting is stable, so elements whose full hashes collide keep their
    insertion order, which is what a HAMT collision node does.
    """
    from .position import hamt_chunks
    return sorted(items, key=lambda x: hamt_chunks(hasheq(x)))


def into_map(pairs):
    """(into {} pairs) with Clojure's iteration order."""
    return CljMap.from_into(pairs)


def assoc(m, *kvs, **kw):
    """(assoc m k v ...) -> new dict"""
    if isinstance(m, CljMap):
        r = m._copy()
        for i in range(0, len(kvs), 2):
            r._assoc_(kvs[i], kvs[i + 1])
        for k, v in kw.items():
            r._assoc_(k, v)
        return r
    r = dict(m)
    for i in range(0, len(kvs), 2):
        r[kvs[i]] = kvs[i + 1]
    r.update(kw)
    return r


def dissoc(m, *ks):
    if isinstance(m, CljMap):
        r = m._copy()
        for k in ks:
            r._dissoc_(k)
        return r
    r = dict(m)
    for k in ks:
        r.pop(k, None)
    return r


def get_in(m, path, default=None):
    cur = m
    for k in path:
        if cur is None:
            return default
        try:
            cur = cur[k]
        except (KeyError, IndexError, TypeError):
            return default
    return default if cur is None else cur


def assoc_in(m, path, v):
    if not path:
        return v
    k = path[0]
    if isinstance(m, list):
        r = list(m)
        r[k] = assoc_in(m[k] if k < len(m) else None, path[1:], v)
        return r
    sub = (m or {}).get(k)
    return assoc(m or {}, k, assoc_in(sub, path[1:], v))


def update_in(m, path, f, *args):
    """(update-in m path f & args) - f gets the current value (may be None)."""
    if not path:
        return f(m, *args)
    k = path[0]
    if isinstance(m, list):
        r = list(m)
        r[k] = update_in(m[k], path[1:], f, *args)
        return r
    cur = (m or {}).get(k)
    return assoc(m or {}, k, update_in(cur, path[1:], f, *args))


def update(m, k, f, *args):
    """(update m k f & args)"""
    return assoc(m, k, f(m.get(k), *args))


def dissoc_in(m, path):
    """Clojure util/dissoc-in: prunes empty maps that result."""
    k, ks = path[0], path[1:]
    if ks:
        nextmap = m.get(k)
        if nextmap is None:
            return m
        newmap = dissoc_in(nextmap, ks)
        if newmap:
            return assoc(m, k, newmap)
        return dissoc(m, k)
    return dissoc(m, k)


def conj_set(s, *xs):
    r = set(s or ())
    r.update(xs)
    return r


def disj(s, *xs):
    r = set(s or ())
    r.difference_update(xs)
    return r


def conj_vec(v, *xs):
    r = list(v or ())
    r.extend(xs)
    return r


def merge(*ms):
    r = {}
    for m in ms:
        if m:
            r.update(m)
    return r


def select_keys(m, ks):
    return {k: m[k] for k in ks if k in m}


def fnil(f, default):
    return lambda x, *a: f(default if x is None else x, *a)


def clj_vals(m):
    """`(vals m)` with Clojure's iteration order.

    Clojure's `assoc` on a PersistentArrayMap *prepends* the new entry, so the
    map iterates in reverse insertion order; Python dicts iterate in insertion
    order.  PersistentArrayMap.assoc promotes to a PersistentHashMap when its
    backing array is already longer than 16, i.e. on the assoc that would make
    the tenth entry - so a 9-entry map is still an array map (verified against
    the original) and a 10-entry one iterates in hash order, which for the
    Position keys the port uses is `position.hamt_key`.
    """
    if isinstance(m, CljMap):
        return [m[k] for k in m.clj_order()]
    if len(m) <= 9:
        return list(m.values())[::-1]
    return [m[k] for k in sorted(m, key=clj_hash_chunks)]


def clj_keys(m):
    """`(keys m)` with Clojure's iteration order - see clj_vals."""
    if isinstance(m, CljMap):
        return m.clj_order()
    if len(m) <= 9:
        return list(m)[::-1]
    return sorted(m, key=clj_hash_chunks)


def clj_items(m):
    """`(seq m)` with Clojure's iteration order - see clj_vals."""
    return [(k, m[k]) for k in clj_keys(m)]


def kw(m, key, default=None):
    """`(:key m)` - Clojure keyword lookup, which is nil-safe on non-maps.

    `(:name montype)` returns nil when `montype` is a String, and BotHack relies
    on that: `rank->monster` is `(comp by-rank-map string/lower-case)` and
    `by-rank-map` maps a rank to a *role name string*, not a MonsterType - so
    `by-description` genuinely returns a String for "vagrant", "chieftain" and
    every other player rank.  The original then evaluates
    `(= "gremlin" (:name montype))` against that String and quietly gets false.

    Indexing it as a dict instead raised TypeError 3002 times across the logged
    games, and because the delegator catches handler exceptions the game carried
    on with the farlook silently discarded - the monster's :peaceful and :type
    were never recorded.
    """
    if isinstance(m, dict):
        return m.get(key, default)
    return default
