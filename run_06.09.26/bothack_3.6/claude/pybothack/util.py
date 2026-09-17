"""Port of bothack.util."""
import os
import re

VI_DIRECTIONS = {
    '>': '>', '<': '<', '.': '.',
    'NW': 'y', 'N': 'k', 'NE': 'u',
    'W': 'h', 'E': 'l',
    'SW': 'b', 'S': 'j', 'SE': 'n',
}

PRIORITY_DEFAULT = 0
# bots should not go beyond these (mirrors (dec Integer/MIN_VALUE) etc.)
PRIORITY_TOP = -2147483649
PRIORITY_BOTTOM = 2147483648


def ctrl(ch):
    """CTRL+<ch>"""
    return chr(ord(ch) - 96)


ESC = chr(27)
BACKSPACE = chr(8)


def config_get(config, key, *default):
    if default:
        return config.get(key, default[0])
    v = config.get(key)
    if v is None:
        raise RuntimeError("Configuration missing key: %s" % key)
    return v


def firstv(v):
    v = list(v) if not isinstance(v, (list, tuple, str)) else v
    return v[0] if len(v) else None


def secondv(v):
    v = list(v) if not isinstance(v, (list, tuple, str)) else v
    return v[1] if len(v) > 1 else None


def re_first_groups(pattern, text):
    """Capturing groups of the first match, or the whole match if no groups."""
    if text is None:
        return None
    m = re.search(pattern, text)
    if not m:
        return None
    if m.re.groups:
        return list(m.groups())
    return m.group(0)


def re_first_group(pattern, text):
    """First capturing group of the first match (whole match if no groups)."""
    g = re_first_groups(pattern, text)
    if g is None:
        return None
    if isinstance(g, list):
        return g[0] if g else None
    return g


def re_any_group(pattern, text):
    """First non-nil capturing group of the first match."""
    g = re_first_groups(pattern, text)
    if isinstance(g, list):
        for x in g:
            if x is not None:
                return x
    return None


def re_seq(pattern, text):
    """Truthy iff the regex matches somewhere (Clojure re-seq used as a test)."""
    if text is None:
        return None
    return re.search(pattern, text)


def max_by(f, coll):
    """(apply max-key f coll): (if (> (k x) (k y)) x y) - on ties the LATER
    element wins."""
    coll = list(coll)
    if not coll:
        return None
    best, bv = coll[0], f(coll[0])
    for x in coll[1:]:
        v = f(x)
        if not bv > v:
            best, bv = x, v
    return best


def min_by(f, coll):
    """(apply min-key f coll): (if (< (k x) (k y)) x y) - on ties the LATER
    element wins."""
    coll = list(coll)
    if not coll:
        return None
    best, bv = coll[0], f(coll[0])
    for x in coll[1:]:
        v = f(x)
        if not bv < v:
            best, bv = x, v
    return best


def first_min_by(f, coll):
    """(apply min-key f (reverse coll)) - first minimum wins."""
    coll = list(coll)
    if not coll:
        return None
    return min_by(f, list(reversed(coll)))


def find_first(pred, s):
    for x in s:
        if pred(x):
            return x
    return None


def keep_first(f, s):
    for x in s:
        r = f(x)
        if r is not None and r is not False:
            return r
    return None


def parse_int(x):
    if x is None:
        return None
    return int(x)


def random_nth(coll, rng):
    coll = list(coll)
    if not coll:
        return None
    return coll[rng.randrange(len(coll))]


def more_than(n, coll):
    """Does coll have more than n elements? (returns the leftover seq/None)"""
    it = iter(coll)
    for _ in range(n):
        if next(it, _SENTINEL) is _SENTINEL:
            return None
    rest = list(it)
    return rest if rest else None


_SENTINEL = object()


def less_than(n, coll):
    """Does coll have less than n elements?"""
    cnt = 0
    for _ in coll:
        cnt += 1
        if cnt >= n:
            return False
    return cnt != n


def str_kw(s):
    return s.lower() if s else None


def select_some(m, ks):
    return {k: m[k] for k in ks if m.get(k) is not None}


def indexed(coll):
    return list(enumerate(coll))


def last_word(s):
    return re_first_group(r'([^ ]+$)', s)


def removev(pred, coll):
    return [x for x in (coll or []) if not pred(x)]


def effective_str(s):
    if len(s) <= 2:
        return parse_int(s)
    if s.endswith("**"):
        return 21
    if int(s[3:]) > 49:
        return 19
    return 20


def max_star(x, y):
    if x is not None and y is not None:
        return max(x, y)
    return x if x is not None else y


def not_any_fn(*fns):
    def f(x):
        return not any(fn(x) for fn in fns)
    return f


def some_fn(*fns):
    def f(x):
        for fn in fns:
            r = fn(x)
            if r:
                return r
        return None
    return f


def every_pred(*fns):
    def f(x):
        for fn in fns:
            if not fn(x):
                return False
        return True
    return f


class LCG(object):
    """A tiny deterministic RNG shared with the Clojure original by the
    comparison harness (tools/cljcmp), so that both bots take identical
    random decisions during a comparison run."""

    def __init__(self, seed=12345):
        self.state = seed & 0x7fffffff

    #: set to a list by the comparison harness to record every draw
    trace = None

    #: draws taken so far, so a trace line carries the index of its own draw
    count = 0

    def _next(self):
        self.state = (1103515245 * self.state + 12345) % 2147483648
        v = self.state >> 16
        LCG.count += 1
        if LCG.trace is not None:
            import traceback
            fr = traceback.extract_stack(limit=3)[0]
            LCG.trace.append((LCG.count, v,
                              "%s:%d" % (os.path.basename(fr.filename),
                                         fr.lineno)))
        return v

    def randrange(self, n):
        return self._next() % n

    def random(self):
        return self._next() / 32768.0


# ---------------------------------------------------------------- clj hashes
_M = 0xffffffff


def _i32(v):
    v &= _M
    return v - 0x100000000 if v & 0x80000000 else v


def java_string_hash(s):
    """java.lang.String.hashCode."""
    h = 0
    for ch in s:
        h = (31 * h + ord(ch)) & _M
    return _i32(h)


def _rotl(x, n):
    x &= _M
    return ((x << n) | (x >> (32 - n))) & _M


def murmur3_hash_int(x):
    """clojure.lang.Murmur3.hashInt (seed 0), as used by Util.hasheq for
    Strings in Clojure 1.6: (Murmur3/hashInt (.hashCode s))."""
    x &= _M
    if x == 0:
        return 0
    k1 = (x * 0xcc9e2d51) & _M
    k1 = _rotl(k1, 15)
    k1 = (k1 * 0x1b873593) & _M
    h1 = 0 ^ k1
    h1 = _rotl(h1, 13)
    h1 = (h1 * 5 + 0xe6546b64) & _M
    # fmix(h1, 4)
    h1 ^= 4
    h1 ^= h1 >> 16
    h1 = (h1 * 0x85ebca6b) & _M
    h1 ^= h1 >> 13
    h1 = (h1 * 0xc2b2ae35) & _M
    h1 ^= h1 >> 16
    return _i32(h1)


def _mix_k1(k1):
    k1 = (k1 * 0xcc9e2d51) & _M
    k1 = _rotl(k1, 15)
    return (k1 * 0x1b873593) & _M


def _mix_h1(h1, k1):
    h1 = (h1 & _M) ^ (k1 & _M)
    h1 = _rotl(h1, 13)
    return (h1 * 5 + 0xe6546b64) & _M


def _fmix(h1, length):
    h1 = (h1 & _M) ^ (length & _M)
    h1 ^= h1 >> 16
    h1 = (h1 * 0x85ebca6b) & _M
    h1 ^= h1 >> 13
    h1 = (h1 * 0xc2b2ae35) & _M
    h1 ^= h1 >> 16
    return h1 & _M


def murmur3_mix_coll_hash(hash_, count):
    """clojure.lang.Murmur3.mixCollHash - the tail of every collection hash."""
    return _i32(_fmix(_mix_h1(0, _mix_k1(hash_ & _M)), count))


def murmur3_hash_long(x):
    """clojure.lang.Murmur3.hashLong, which is Util.hasheq for Long/Integer."""
    if x == 0:
        return 0
    x &= (1 << 64) - 1
    h1 = _mix_h1(0, _mix_k1(x & _M))
    h1 = _mix_h1(h1, _mix_k1((x >> 32) & _M))
    return _i32(_fmix(h1, 8))


def murmur3_hash_unencoded_chars(s):
    """clojure.lang.Murmur3.hashUnencodedChars - the basis of Symbol.hasheq."""
    h1 = 0
    n = len(s)
    for i in range(1, n, 2):
        h1 = _mix_h1(h1, _mix_k1(ord(s[i - 1]) | (ord(s[i]) << 16)))
    if n & 1:
        h1 = (h1 & _M) ^ _mix_k1(ord(s[n - 1]))
    return _i32(_fmix(h1, 2 * n))


def java_hash_combine(seed, h):
    """clojure.lang.Util.hashCombine.

    `seed >> 2` is Java's *arithmetic* shift on a signed int.  Masking to 32
    bits before shifting (the obvious Python transcription) makes it logical
    and silently produces the right answer for every non-negative seed - which
    is why `:white` and `:remembered` agreed with the JVM while `:x`, `:y` and
    `:known` did not.
    """
    seed = _i32(seed)
    return _i32((seed & _M) ^ (((h & _M) + 0x9e3779b9
                                + ((seed << 6) & _M)
                                + ((seed >> 2) & _M)) & _M))


def clj_symbol_hasheq(name, ns=None):
    """clojure.lang.Symbol.hasheq."""
    return java_hash_combine(murmur3_hash_unencoded_chars(name),
                             0 if ns is None else clj_symbol_hasheq(ns))


def clj_keyword_hasheq(name):
    """clojure.lang.Keyword.hasheq = Symbol.hasheq + 0x9e3779b9."""
    return _i32(clj_symbol_hasheq(name) + 0x9e3779b9)


def clj_hash_ordered(items, hasheq=None):
    """Murmur3.hashOrdered - vectors, lists and map entries."""
    hasheq = hasheq or clj_hasheq
    h, n = 1, 0
    for x in items:
        h = (31 * h + (hasheq(x) & _M)) & _M
        n += 1
    return murmur3_mix_coll_hash(h, n)


def clj_hash_unordered(items, hasheq=None):
    """Murmur3.hashUnordered - sets and maps."""
    hasheq = hasheq or clj_hasheq
    h, n = 0, 0
    for x in items:
        h = (h + (hasheq(x) & _M)) & _M
        n += 1
    return murmur3_mix_coll_hash(h, n)


def clj_record_hasheq(type_hash, entries, val_hasheq):
    """`(bit-xor type-hash (APersistentMap/mapHasheq record))`, the hasheq
    `defrecord` generates.  `entries` are (key, value) pairs whose keys are
    keywords; `val_hasheq(key, value)` supplies the value's hasheq, because the
    port stores Clojure keywords and Clojure strings both as Python `str` and
    only a per-field table can tell them apart."""
    def entry_hasheq(kv):
        k, v = kv
        h = (31 * 1 + (clj_keyword_hasheq(k) & _M)) & _M
        h = (31 * h + (val_hasheq(k, v) & _M)) & _M
        return murmur3_mix_coll_hash(h, 2)
    return _i32((type_hash & _M)
                ^ (clj_hash_unordered(entries, entry_hasheq) & _M))


def clj_hasheq(o):
    """clojure.lang.Util.hasheq for the values the bot puts in menu sets.

    A Character hashes to its code point, a String to
    `Murmur3.hashInt(String.hashCode())`.  The port stores both as Python
    `str`, so a one-character value is ambiguous: `pick-up-what` answers with
    inventory slots, which are Characters, while `put-in-what` answers with
    `(str amt slot)`, which is a String even when it is one character long.
    `clj.CljStr` marks the latter at the site that builds it; anything else
    that is one character long is a Character.
    """
    from .clj import CljStr
    if isinstance(o, CljStr):
        return murmur3_hash_int(java_string_hash(str(o)))
    s = o if isinstance(o, str) else str(o)
    if len(s) == 1:
        return ord(s)
    return murmur3_hash_int(java_string_hash(s))
