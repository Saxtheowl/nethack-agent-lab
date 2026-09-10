#!/usr/bin/env python3
"""Find port code that reads like `condp-all` where the original wrote `condp`.

`condp` short-circuits: the first matching clause wins and the rest never run.
`condp-all` is BotHack's own macro and runs *every* matching clause - and it is
used in exactly **one** place, the topline message handler in `game.clj`.  So a
run of sibling `if re_seq(...)` statements in the port, none of which returns, is
either that one place or a mistranslated `condp`.

The failure is quiet: several clauses fire where the original fired one, so the
game state picks up an extra update that only shows much later.

    tools/audit_port_condp.py [pybothack dir]
"""
import ast
import os
import sys

MATCHERS = {'re_seq', 're_first_group', 're_first_groups', 're_any_group',
            'startswith', 'contains'}


def _is_match_test(node):
    """Does this `if` test look like a condp clause predicate?"""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            fn = sub.func
            name = (fn.id if isinstance(fn, ast.Name)
                    else fn.attr if isinstance(fn, ast.Attribute) else None)
            if name in MATCHERS:
                return True
    return False


def _falls_through(stmt):
    """True when the branch does not end the clause chain."""
    last = stmt.body[-1]
    return not isinstance(last, (ast.Return, ast.Raise, ast.Continue,
                                 ast.Break))


def audit(path):
    tree = ast.parse(open(path).read(), path)
    hits = []
    for node in ast.walk(tree):
        body = getattr(node, 'body', None)
        if not isinstance(body, list):
            continue
        run = []
        for stmt in body:
            if isinstance(stmt, ast.If) and _is_match_test(stmt.test) \
                    and not stmt.orelse:
                run.append(stmt)
            else:
                if len(run) >= 3 and all(_falls_through(s) for s in run):
                    hits.append((run[0].lineno, len(run)))
                run = []
        if len(run) >= 3 and all(_falls_through(s) for s in run):
            hits.append((run[0].lineno, len(run)))
    return hits


def self_test():
    """An audit that reports nothing is worthless until it has been shown to
    find the thing it looks for."""
    import tempfile
    bad = """
def handler(text):
    if re_seq('a', text):
        x = 1
    if re_seq('b', text):
        x = 2
    if re_seq('c', text):
        x = 3
"""
    good = """
def handler(text):
    if re_seq('a', text):
        return 1
    if re_seq('b', text):
        return 2
    if re_seq('c', text):
        return 3
"""
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for name, src, want in (('bad.py', bad, 1), ('good.py', good, 0)):
            path = os.path.join(tmp, name)
            open(path, 'w').write(src)
            got = len(audit(path))
            status = 'ok  ' if got == want else 'FAIL'
            if got != want:
                ok = False
            print('  %s %-8s %d hit(s), expected %d' % (status, name, got,
                                                        want))
    return 0 if ok else 1


def main():
    if '--self-test' in sys.argv:
        return self_test()
    root = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') \
        else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'pybothack')
    total = 0
    for dirpath, _d, files in os.walk(root):
        if '__pycache__' in dirpath:
            continue
        for fn in sorted(files):
            if not fn.endswith('.py'):
                continue
            path = os.path.join(dirpath, fn)
            for line, n in audit(path):
                print('  %s:%d  %d sibling match-tests, none of which returns'
                      % (os.path.relpath(path, os.path.dirname(root)), line, n))
                total += 1
    print('\n%d run(s) that behave like condp-all.  The original has exactly one '
          'condp-all\n(game.clj:344, the topline message handler); anything else '
          'here is a condp\nthat lost its short-circuit.' % total)


if __name__ == '__main__':
    sys.exit(main() or 0)
