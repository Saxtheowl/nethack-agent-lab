#!/usr/bin/env python3
"""Find `if-let`/`when-let` forms that test the container but use a key of it.

    (if-let [{:keys [step]} (navigate game fountain?)]
      step
      (or ...))

The test is the **Path**, not `step`.  A Path exists whenever a route was found,
including when the player is already standing on the target - and then `step` is
nil while the *then* branch still runs, so the form yields nil and the `or` in the
else branch never gets a chance.  Translating it as "if there is a step" flips
the behaviour: that is how the port stopped dipping for Excalibur.

Every site is a question, not a verdict - most destructurings are used in a way
that makes the distinction invisible.  What matters is that the port's
translation of each one tests the same thing the original tests.

    tools/audit_iflet_destructuring.py <src dir>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.cljread import (Form, Kw, Sym, read_forms, walk)         # noqa: E402

BIND_HEADS = {'if-let', 'when-let', 'if-some', 'when-some'}


def _destructured_names(node):
    """The names a binding form introduces, if it is a map destructuring."""
    if not isinstance(node, Form) or node.kind != 'map':
        return []
    names = []
    kids = node.children
    for i in range(0, len(kids) - 1, 2):
        k, v = kids[i], kids[i + 1]
        if isinstance(k, Kw) and k.text == ':keys' and \
                isinstance(v, Form) and v.kind == 'vector':
            names.extend(x.text for x in v.children if isinstance(x, Sym))
        elif isinstance(k, Sym) and isinstance(v, Kw):
            names.append(k.text)
    return names


def audit(path):
    forms = read_forms(open(path).read())
    root = Form('root', forms, 0)
    hits = []
    for node in walk(root):
        if not (isinstance(node, Form) and node.kind == 'list'
                and node.head in BIND_HEADS):
            continue
        if len(node.children) < 3:
            continue
        vec = node.children[1]
        if not (isinstance(vec, Form) and vec.kind == 'vector'
                and len(vec.children) >= 2):
            continue
        names = _destructured_names(vec.children[0])
        if not names:
            continue
        init = vec.children[1]
        body = node.children[2:]
        # does the then-branch's value come from one of the destructured names?
        then = body[0]
        uses = [n for n in names
                if any(isinstance(x, Sym) and x.text == n for x in walk(then))]
        has_else = len(body) > 1
        hits.append((node.line, node.head, names, uses, has_else,
                     repr(init)[:70], repr(then)[:60]))
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
    total = risky = 0
    for path in clj_sources(root):
        fn = os.path.relpath(path, root)
        hits = audit(path)
        if not hits:
            continue
        printed = False
        for line, head, names, uses, has_else, init, then in hits:
            total += 1
            # the trap needs three things: a destructuring, a then-branch that
            # depends on a destructured name, and an else-branch that the
            # nil-name case would skip
            if not (uses and has_else):
                continue
            risky += 1
            if not printed:
                print('== %s' % fn)
                printed = True
            print('  %s:%d  `%s` tests %s but yields %s, and has an else branch'
                  % (fn, line, head, init, ', '.join(uses)))
            print('      then: %s' % then)
    print('\n%d destructuring %s form(s); %d test the container while yielding '
          'one of its keys *and* have an else branch' % (total, '/'.join(sorted(BIND_HEADS)), risky))


if __name__ == '__main__':
    main()
