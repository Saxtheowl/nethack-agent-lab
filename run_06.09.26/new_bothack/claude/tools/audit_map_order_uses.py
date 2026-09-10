#!/usr/bin/env python3
"""Which of BotHack's maps have their *iteration order* observed?

A Clojure map of nine or fewer entries is a PersistentArrayMap whose `assoc`
**prepends**, so `vals`/`keys`/`seq` walk it in reverse insertion order; the
tenth entry promotes it to a PersistentHashMap, which walks in hash order.
`(into {} …)` builds through a *transient* array map, which appends instead and
promotes on the ninth.  Python dicts always walk in insertion order, so every map
whose order reaches a decision needs `clj.CljMap` and `clj_vals`/`clj_keys`.

Two bugs came from this: `(:monsters level)`, whose order picks the monster to
farlook and the pairing order in `track-monsters`, and the inventory map, whose
order breaks the tie between two food stacks of equal nutrition.

Reports every `let`/`loop` binding whose value is a map, together with the
order-sensitive calls that consume it in the same top-level form, plus direct
order-sensitive uses of the well-known map-valued keys.

    tools/audit_map_order_uses.py <src dir>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.cljread import (Form, Kw, Sym, read_forms, walk)        # noqa: E402

ORDER_SENSITIVE = {
    'first', 'ffirst', 'find-first', 'some', 'seq', 'rest', 'next', 'vals',
    'keys', 'reduce', 'reduce-kv', 'into', 'min-key', 'max-key', 'take',
    'random-nth', 'rand-nth', 'string/join', 'clojure.string/join',
}
#: order-sensitive *and* order-insensitive uses are worth telling apart: `count`,
#: `get`, `contains?` and `assoc` never observe order
MAP_PRODUCING = {'into', 'assoc', 'assoc-in', 'merge', 'zipmap', 'hash-map',
                 'update', 'update-in', 'dissoc', 'select-keys',
                 'group-by', 'frequencies'}
#: keys whose value is a map the bot iterates
#: keys whose value really is a *map*.  `:items` is a vector on a Tile and
#: `:used-names` a set, so listing them here only manufactures false positives.
MAP_KEYS = {':monsters', ':inventory', ':levels', ':discoveries'}
TRANSPARENT = {'if', 'if-not', 'when', 'when-not', 'do', 'dosync', 'let',
               'binding', 'when-let', 'if-let', 'when-some', 'if-some'}


def _yields_map(node, depth=0):
    if depth > 6:
        return False
    if isinstance(node, Form) and node.kind == 'map':
        return True
    if not isinstance(node, Form) or node.kind != 'list':
        return False
    head = node.head
    if head in MAP_PRODUCING:
        # (into {} …) / (into [] …): the target decides
        if head == 'into' and len(node.children) > 1:
            tgt = node.children[1]
            return isinstance(tgt, Form) and tgt.kind == 'map'
        return True
    if head in ('->>', '->') and node.children:
        last = node.children[-1]
        if isinstance(last, Sym) and last.text in MAP_PRODUCING:
            return True
        return _yields_map(last, depth + 1)
    if head in TRANSPARENT:
        body = node.children[1:]
        if head in ('if', 'if-not'):
            return any(_yields_map(c, depth + 1) for c in body[1:])
        if head in ('let', 'binding', 'when-let', 'if-let', 'when-some',
                    'if-some'):
            return bool(body) and any(_yields_map(c, depth + 1)
                                      for c in body[1:])
        return bool(body) and _yields_map(body[-1], depth + 1)
    return False


def _bindings(form):
    out = []
    if len(form.children) < 2:
        return out
    vec = form.children[1]
    if not isinstance(vec, Form) or vec.kind != 'vector':
        return out
    kids = vec.children
    for i in range(0, len(kids) - 1, 2):
        if isinstance(kids[i], Sym):
            out.append((kids[i].text, kids[i + 1]))
    return out


def audit(path):
    forms = read_forms(open(path).read())
    hits = []
    for top in forms:
        if not isinstance(top, Form):
            continue
        name = (top.children[1].text
                if len(top.children) > 1 and isinstance(top.children[1], Sym)
                else '?')
        mapvars = {}
        for node in walk(top):
            if isinstance(node, Form) and node.kind == 'list' and \
                    node.head in ('let', 'loop', 'when-let', 'if-let',
                                  'when-some', 'if-some'):
                for sym, init in _bindings(node):
                    if _yields_map(init):
                        mapvars[sym] = init.line
        for node in walk(top):
            if not (isinstance(node, Form) and node.kind == 'list'):
                continue
            if node.head not in ORDER_SENSITIVE:
                continue
            for arg in node.children[1:]:
                if isinstance(arg, Sym) and arg.text in mapvars:
                    hits.append((node.line, name, arg.text, node.head,
                                 'let-bound map', repr(node)[:120]))
                    break
                # (vals (:monsters level)) and friends
                if isinstance(arg, Form) and arg.kind == 'list' and \
                        arg.children and isinstance(arg.children[0], Kw) and \
                        arg.children[0].text in MAP_KEYS:
                    hits.append((node.line, name, arg.children[0].text,
                                 node.head, 'map-valued key', repr(node)[:120]))
                    break
    return hits


def clj_sources(root):
    found = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in sorted(files):
            if fn.endswith('.clj'):
                found.append(os.path.join(dirpath, fn))
    return sorted(found)


def main():
    root = sys.argv[1]
    total = 0
    for path in clj_sources(root):
        fn = os.path.relpath(path, root)
        hits = audit(path)
        if not hits:
            continue
        print('== %s' % fn)
        for line, where, var, fnname, why, text in hits:
            print('  %s:%d  in %s: `%s` (%s) is walked by `%s`'
                  % (fn, line, where, var, why, fnname))
            print('      %s' % text)
            total += 1
    print('\n%d order-sensitive use(s) of a map' % total)


if __name__ == '__main__':
    main()
