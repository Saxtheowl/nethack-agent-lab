#!/usr/bin/env python3
"""Which of BotHack's sets have their *iteration order* observed?

A Clojure set iterates in the HAMT order of its elements' `hasheq`.  Python's
set order is unrelated (and not even stable across processes for strings), so
every set whose order reaches a decision has to be reproduced deliberately -
`clj.clj_set_order` - and every set that is only ever a membership test can stay
a plain Python set.  Telling those apart by hand does not scale; this does it
structurally.

The bug this exists for: `(->> (hostile-threats game) (remove ...) set)` bound to
`threats`, then `(find-first #(and (= 2 (distance player %)) ...) threats)`.  With
one fleeing and one standing monster both at distance 2, the order picks which
one `fight` baits, and therefore whether the bot searches or steps.

Reports every `let`/`loop` binding whose value is a set, together with the
order-sensitive calls that consume it in the same top-level form.

    tools/audit_set_order_uses.py <src dir>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.cljread import Form, Sym, read_forms, walk               # noqa: E402

#: functions whose result depends on the order the collection is walked in
ORDER_SENSITIVE = {
    'first', 'ffirst', 'find-first', 'some', 'seq', 'rest', 'next',
    'string/join', 'clojure.string/join', 'random-nth', 'rand-nth',
    'min-key', 'max-key', 'reduce', 'into', 'sort-by', 'take', 'peek',
    'apply',
}
#: heads that yield a set
SET_PRODUCING = {'set', 'hash-set', 'disj', 'conj', 'union', 'difference',
                 'intersection', 'clojure.set/union',
                 'clojure.set/difference', 'clojure.set/intersection'}


#: forms whose value is the value of their own tail position(s)
TRANSPARENT = {'if', 'if-not', 'when', 'when-not', 'do', 'dosync', 'let',
               'binding', 'when-let', 'if-let', 'when-some', 'if-some'}


def _yields_set(node, depth=0):
    """Could this expression evaluate to a set?

    Looks through `if`/`when`/`let` tails: `navigate` binds its goal collection
    with `(let [goal-set (if (set? x) (->> x ... set) (->> ... set))] ...)`, and a
    check that only understands a bare `(-> ... set)` misses it - which made this
    audit report nothing for the most load-bearing function in the project.
    """
    if depth > 6:
        return False
    if isinstance(node, Form) and node.kind == 'set':
        return True
    if not isinstance(node, Form) or node.kind != 'list':
        return False
    head = node.head
    if head in SET_PRODUCING:
        return True
    if head in ('->>', '->') and node.children:
        last = node.children[-1]
        if isinstance(last, Sym) and last.text in SET_PRODUCING:
            return True
        return _yields_set(last, depth + 1)
    if head in TRANSPARENT:
        body = node.children[1:]
        if head in ('if', 'if-not'):
            return any(_yields_set(c, depth + 1) for c in body[1:])
        if head in ('let', 'binding', 'when-let', 'if-let', 'when-some',
                    'if-some'):
            return bool(body) and any(_yields_set(c, depth + 1)
                                      for c in body[1:])
        return bool(body) and _yields_set(body[-1], depth + 1)
    return False


def _bindings(form):
    """[(symbol, init)] for a let/loop-style binding vector."""
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
        setvars = {}
        for node in walk(top):
            if isinstance(node, Form) and node.kind == 'list' and \
                    node.head in ('let', 'loop', 'when-let', 'if-let',
                                  'when-some', 'if-some'):
                for sym, init in _bindings(node):
                    if _yields_set(init):
                        setvars[sym] = init.line
        if not setvars:
            continue
        for node in walk(top):
            if not (isinstance(node, Form) and node.kind == 'list'):
                continue
            if node.head not in ORDER_SENSITIVE:
                continue
            for arg in node.children[1:]:
                if isinstance(arg, Sym) and arg.text in setvars:
                    hits.append((node.line, name, arg.text, node.head,
                                 setvars[arg.text], repr(node)[:120]))
    return hits


def clj_sources(root):
    """Every .clj under `root`, recursively.

    `bots/mainbot.clj` lives in a subdirectory and is the densest decision code
    in the project; a flat listdir silently skips it, which makes any "no hits"
    conclusion worthless.
    """
    out = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in sorted(files):
            if fn.endswith('.clj'):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def main():
    root = sys.argv[1]
    total = 0
    for path in clj_sources(root):
        fn = os.path.relpath(path, root)
        hits = audit(path)
        if not hits:
            continue
        print('== %s' % fn)
        for line, where, var, fnname, bound, text in hits:
            print('  %s:%d  in %s: `%s` (a set bound at line %d) is walked by '
                  '`%s`' % (fn, line, where, var, bound, fnname))
            print('      %s' % text)
            total += 1
    print('\n%d order-sensitive use(s) of a set' % total)


if __name__ == '__main__':
    main()
