#!/usr/bin/env python3
"""Find every place BotHack passes the game *atom* where a function wants the
game *value*.

`(:keys [game])` on a `bh` map binds the atom.  Inside such a scope `@game`
is the value and a bare `game` is the atom; Clojure does not complain when the
atom reaches a function that expects a map - `(:player atom)` and
`(get-in atom …)` just return nil.  So each of these sites is an upstream bug
with an observable, silent behaviour, and a port that "helpfully" derefs is
*not* faithful.  Reported so each one can be reproduced deliberately.
"""
import os
import re
import sys

# forms that legitimately take the atom
ATOM_OK = re.compile(r"""\(\s*(?:swap!|reset!|compare-and-set!|deref|atom|
                              update-inventory|with-reason)\s""", re.X)
BIND = re.compile(r"\{:keys\s*\[[^\]]*\bgame\b[^\]]*\]")


def scan(path):
    src = open(path).read()
    lines = src.split('\n')
    hits = []
    # a binding of `game` from a :keys destructuring holds until the next
    # top-level form
    live = False
    for i, line in enumerate(lines, 1):
        if line.startswith('(') and not BIND.search(line):
            live = False
        if BIND.search(line):
            live = True
        if not live:
            continue
        # strip strings and comments before looking for `game`
        body = re.sub(r'"(?:[^"\\]|\\.)*"', '""', line)
        body = re.sub(r';.*$', '', body)
        for m in re.finditer(r'(?<![@:\w-])game(?![\w?*!-])', body):
            pre = body[:m.start()]
            # the binding form itself, and (:game bh)
            if re.search(r':keys\s*\[[^\]]*$', pre):
                continue
            # first argument of a form that takes the atom
            call = re.search(r'\(\s*([\w.!?*<>=/+-]+)\s*$', pre)
            if call and ATOM_OK.match('(' + call.group(1) + ' '):
                continue
            # `(fn [game] …)` / `let [game …]` rebinding to a value
            if re.search(r'(?:fn|let|loop|for|doseq)\s*\[[^\]]*$', pre):
                continue
            hits.append((i, line.strip(), call.group(1) if call else '?'))
    return hits


def main():
    root = sys.argv[1]
    total = 0
    for fn in sorted(os.listdir(root)):
        if not fn.endswith('.clj'):
            continue
        hits = scan(os.path.join(root, fn))
        if not hits:
            continue
        print('== %s' % fn)
        for ln, text, callee in hits:
            print('  %s:%d  callee=%s' % (fn, ln, callee))
            print('      %s' % text)
            total += 1
    print('\n%d site(s)' % total)


if __name__ == '__main__':
    main()
