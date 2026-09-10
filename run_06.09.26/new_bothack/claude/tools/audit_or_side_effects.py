#!/usr/bin/env python3
"""Find `or` clauses whose value is a side effect, not a test.

The bug this exists for: in BotHack's scraper,

    (or (when (and (more-prompt? frame) ...) ... lastmsg-clear)
        (if (= "# #" (topline frame)) (ref-set player (:cursor frame)))
        (when (= (:cursor frame) @player) ... sink)
        (log/debug "lastmsg expecting further redraw"))

The middle clause looks like a statement but is a *clause of the or*, and
`ref-set` returns the value it set - truthy - so the `or` short-circuits and the
remaining clauses never run on that frame.  Reading it as a statement (which is
what a straightforward port does) makes the bot act one redraw earlier.  That
was invisible for 780 000 keystrokes and decisive inside a hallucination
episode, where every monster glyph is re-randomised per redraw.

This walks the form tree and reports every non-final `or`/`and` clause whose
value in tail position comes from a call that returns something truthy for its
side effect.  A report is a *question*, not a verdict: many are deliberate.

    tools/audit_or_side_effects.py <src dir>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.cljread import (Form, Sym, read_forms, walk,          # noqa: E402
                           enclosing_defn)

#: calls whose return value is truthy but whose point is the side effect
SIDE_EFFECT = {
    'ref-set', 'reset!', 'swap!', 'alter', 'commute', 'set!',
    'send', 'send-off', 'conj!', 'assoc!', 'disj!', 'dissoc!', 'pop!',
    'vreset!', 'deliver', 'doto',
}
#: forms whose value is the value of their own tail position(s)
TRANSPARENT = {'if', 'if-not', 'when', 'when-not', 'when-let', 'when-some',
               'do', 'dosync', 'let', 'binding', 'io!'}


def _tails(node):
    """The forms that can supply this form's value, following tail position.

    Getting this right is the whole point: `(when test (send ...) next-state)`
    yields `next-state`, so the `send` is a statement and must not be reported,
    while `(if test (ref-set ...))` yields the ref-set - and, when the test
    fails, nil.
    """
    if not isinstance(node, Form) or node.kind != 'list':
        return [node]
    head = node.head
    body = node.children[1:]
    if head in ('if', 'if-not'):
        # (if test then else?) - the branches, not the test
        return [t for c in body[1:] for t in _tails(c)]
    if head in ('when', 'when-not', 'do', 'dosync', 'io!'):
        return _tails(body[-1]) if body else []
    if head in ('when-let', 'when-some', 'let', 'binding', 'if-let'):
        # (let [bindings] & body) - only the last body form
        return _tails(body[-1]) if len(body) > 1 else []
    return [node]


def tail_calls(node):
    """Side-effecting calls that could supply this form's value."""
    return [t for t in _tails(node)
            if isinstance(t, Form) and t.kind == 'list'
            and t.head in SIDE_EFFECT]


def audit(path):
    forms = read_forms(open(path).read())
    root = Form('root', forms, 0)
    hits = []
    for node in walk(root):
        if not isinstance(node, Form) or node.head not in ('or', 'and'):
            continue
        clauses = node.children[1:]
        for i, clause in enumerate(clauses):
            if i == len(clauses) - 1:
                continue            # the last clause *is* the value
            for call in tail_calls(clause):
                hits.append((clause.line, node.head, call.head,
                             enclosing_defn(forms, clause.line),
                             repr(clause)[:150]))
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
        for line, op, call, where, text in hits:
            print('  %s:%d  in %s: a non-final `%s` clause returns from `%s`'
                  % (fn, line, where, op, call))
            print('      %s' % text)
            total += 1
    print('\n%d site(s) to read' % total)


if __name__ == '__main__':
    main()
