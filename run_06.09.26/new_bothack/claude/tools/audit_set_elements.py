#!/usr/bin/env python3
"""Report what produces the elements of every set BotHack builds.

Set iteration order is the HAMT order of the elements' `hasheq`, and `hasheq`
differs by *type*: a Character hashes to its code point, a String to
`Murmur3.hashInt(String.hashCode())`.  The port keeps both as Python `str`, so
each construction site has to declare which it is (`clj.CljStr`).

The bug this exists for: `put-in-what` answers with
`(set (map #(str (val %) (key %)) amt-map))`, and with a nil amount `(str nil \\x)`
is the one-character *String* "x".  The port keyed on length, decided
"one character means Character", and sent the six letters in the wrong order.

So: every `(set ...)`, `(into #{} ...)` and `#{...}` in the source, with the head
of whatever computes its elements.  `str`, `subs`, `format`, `name` and `apply
str` produce Strings; a `\\c` literal is a Character; anything else has to be
read.

    tools/audit_set_elements.py <src dir>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.cljread import (Char, Form, Str, Sym, read_forms,      # noqa: E402
                           walk, enclosing_defn)

STRING_PRODUCING = {'str', 'subs', 'format', 'name', 'clojure.string/join',
                    'string/join', 'str/join', 'pr-str', 'print-str'}


def element_sources(node):
    """Heads of the calls that compute this collection's elements."""
    out = []
    for sub in walk(node):
        if isinstance(sub, Form) and sub.kind == 'list' and sub.head:
            if sub.head in STRING_PRODUCING:
                out.append(('String', sub.head, sub.line))
        elif isinstance(sub, Char):
            out.append(('Character', '\\' + sub.text, sub.line))
        elif isinstance(sub, Str):
            out.append(('String', '"%s"' % sub.text[:12], sub.line))
    return out


def audit(path):
    forms = read_forms(open(path).read())
    root = Form('root', forms, 0)
    hits = []
    for node in walk(root):
        is_set_call = (isinstance(node, Form) and node.kind == 'list'
                       and node.head in ('set', 'hash-set'))
        is_into_set = (isinstance(node, Form) and node.kind == 'list'
                       and node.head == 'into' and len(node.children) > 1
                       and isinstance(node.children[1], Form)
                       and node.children[1].kind == 'set')
        is_literal = isinstance(node, Form) and node.kind == 'set'
        if not (is_set_call or is_into_set or is_literal):
            continue
        srcs = element_sources(node)
        kinds = sorted({k for k, _, _ in srcs})
        if not kinds:
            kinds = ['?']
        hits.append((node.line, enclosing_defn(forms, node.line),
                     '+'.join(kinds), sorted({t for _, t, _ in srcs})[:4],
                     repr(node)[:110]))
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
    interesting = 0
    for path in clj_sources(root):
        fn = os.path.relpath(path, root)
        hits = audit(path)
        rows = [h for h in hits if 'String' in h[2]]
        if not rows:
            continue
        print('== %s' % fn)
        for line, where, kinds, tokens, text in rows:
            print('  %s:%d  in %s  elements: %s %s'
                  % (fn, line, where, kinds, tokens))
            print('      %s' % text)
            interesting += 1
    print('\n%d set(s) hold Clojure Strings.  Only the ones whose *order* is '
          'observed need clj.CljStr;\ncross-check with '
          'tools/audit_set_order_uses.py - the rest are membership tests.'
          % interesting)


if __name__ == '__main__':
    main()
