"""Faithful Python rewrite of bothack.util (BotHack by krajj7)."""

import re
import random

# vi-direction key map (bothack.util/vi-directions)
vi_directions = {
    ">": ">", "<": "<", ".": ".",
    "NW": "y", "N": "k", "NE": "u",
    "W": "h", "E": "l",
    "SW": "b", "S": "j", "SE": "n",
}

# priorities (bothack.util/priority-*)
priority_default = 0
priority_top = -2147483649  # (dec Integer/MIN_VALUE) = -2147483648 - 1
priority_bottom = 2147483648  # (inc Integer/MAX_VALUE) = 2147483647 + 1

ESC = "\x1b"
BACKSPACE = "\x08"


def ctrl(ch):
    return chr(ord(ch) - 96)


def firstv(v):
    return v[0] if len(v) > 0 else None


def secondv(v):
    return v[1] if len(v) > 1 else None


def re_first_groups(pattern, text):
    """Returns the list of capturing groups of the first match, or the whole
    match if no groups (bothack.util/re-first-groups)."""
    if text is None:
        return None
    m = re.search(pattern, text)
    if m is None:
        return None
    if m.groups():
        return list(m.groups())
    return m.group(0)


def re_first_group(pattern, text):
    """Returns the first capturing group of the first match, or the whole
    match if no groups (bothack.util/re-first-group)."""
    if text is None:
        return None
    m = re.search(pattern, text)
    if m is None:
        return None
    if m.groups():
        return m.group(1)
    return m.group(0)


def re_any_group(pattern, text):
    """Returns the first non-nil capturing group of the first match."""
    if text is None:
        return None
    m = re.search(pattern, text)
    if m is None:
        return None
    if m.groups():
        for g in m.groups():
            if g is not None:
                return g
        return None
    return m.group(0)


def max_by(f, coll):
    coll = list(coll)
    if not coll:
        return None
    # Clojure's (max-key f ...) keeps the LAST maximum on ties
    best = coll[0]
    best_v = f(best)
    for x in coll[1:]:
        v = f(x)
        if v >= best_v:
            best = x
            best_v = v
    return best


def min_by(f, coll):
    coll = list(coll)
    if not coll:
        return None
    # (min-key f ...) keeps the LAST minimum on ties
    best = coll[0]
    best_v = f(best)
    for x in coll[1:]:
        v = f(x)
        if v <= best_v:
            best = x
            best_v = v
    return best


def first_min_by(f, coll):
    coll = list(coll)
    if not coll:
        return None
    # (min-key f ...) applied over reversed coll keeps the FIRST minimum
    best = coll[-1]
    best_v = f(best)
    for x in coll[:-1]:
        v = f(x)
        if v <= best_v:
            best = x
            best_v = v
    return best


def find_first(p, s):
    for x in s:
        if p(x):
            return x
    return None


def parse_int(x):
    if x is None:
        return None
    return int(x)


def random_nth(coll):
    coll = list(coll)
    if not coll:
        return None
    return random.choice(coll)


def update(m, k, f, *args):
    new = dict(m)
    new[k] = f(m[k], *args) if k in m else f(None, *args)
    return new


def update_in(m, ks, f, *args):
    ks = list(ks)
    if not ks:
        return f(m, *args)
    k = ks[0]
    new = dict(m) if isinstance(m, dict) else m
    new[k] = update_in(m[k] if k in m else None, ks[1:], f, *args)
    return new


def assoc(m, *kvs):
    new = dict(m)
    for i in range(0, len(kvs), 2):
        new[kvs[i]] = kvs[i + 1]
    return new


def assoc_in(m, ks, v):
    return update_in(m, ks, lambda _: v)


def dissoc(m, *ks):
    new = dict(m)
    for k in ks:
        if k in new:
            del new[k]
    return new


def get_in(m, ks, default=None):
    cur = m
    for k in ks:
        if cur is None or (isinstance(cur, dict) and k not in cur) or \
           (isinstance(cur, (list, tuple, str)) and not (isinstance(k, int) and 0 <= k < len(cur))):
            return default
        cur = cur[k]
    return cur


def dissoc_in(m, ks):
    """bothack.util/dissoc-in: dissociate, pruning empty maps."""
    ks = list(ks)
    if not ks:
        return m
    k = ks[0]
    if not isinstance(m, dict) or k not in m:
        return m
    if len(ks) == 1:
        new = dict(m)
        del new[k]
        return new
    sub = dissoc_in(m[k], ks[1:])
    new = dict(m)
    if isinstance(sub, dict) and len(sub) == 0:
        del new[k]
    elif sub is None:
        return m
    else:
        new[k] = sub
    return new


def effective_str(s):
    """bothack.util/effective-str — surprising 18/xx conversion preserved."""
    if len(s) <= 2:
        return parse_int(s)
    if s.endswith("**"):
        return 21
    if 49 < parse_int(s[3:]):
        return 19
    return 20


def last_word(s):
    return re_first_group(r"([^ ]+$)", s)


def more_than(n, coll):
    it = iter(coll)
    for _ in range(n + 1):
        try:
            next(it)
        except StopIteration:
            return False
    return True


def less_than(n, coll):
    it = iter(coll)
    cnt = 0
    for _ in it:
        cnt += 1
        if cnt >= n:
            return False
    return cnt != n


def str_to_kw(s):
    if s is None:
        return None
    return s.lower()


def select_some(m, ks):
    return {k: m[k] for k in ks if m.get(k) is not None}


def indexed(coll):
    return list(enumerate(coll))