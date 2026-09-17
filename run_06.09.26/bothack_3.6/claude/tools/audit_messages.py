"""Audit: which message regexes of BotHack matched a 3.4.3 message whose
format string no longer exists verbatim in 3.6.7?

Heuristic, meant to produce a review list (docs/AUDIT_MESSAGES.md).
"""
import ast
import difflib
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC343 = os.path.join(ROOT, '..', '..', 'new_bothack', 'claude', 'upstream',
                      'nh343-nao-build', 'src')
SRC367 = os.path.join(ROOT, 'vendor', 'NetHack-NetHack-3.6.7_Released', 'src')

PREFIX = {'You': 'You ', 'Your': 'Your ', 'You_feel': 'You feel ',
          'You_hear': 'You hear ', 'You_see': 'You see ',
          'You_cant': "You can't ", 'There': 'There ', 'pline_The': 'The ',
          'You_are': 'You are '}

CALL_RE = re.compile(r'\b(You_feel|You_hear|You_see|You_cant|You_are|'
                     r'pline_The|Your|You|There|pline|verbalize|Norep|'
                     r'Sprintf|Strcpy|Strcat|yn_function|getlin|'
                     r'custompline|raw_printf|impossible)\s*\(([^;]*?)\)\s*;',
                     re.S)
LIT_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def c_strings(srcdir):
    out = {}
    for path in glob.glob(os.path.join(srcdir, '*.c')):
        txt = open(path, errors='replace').read()
        for m in CALL_RE.finditer(txt):
            fn, args = m.group(1), m.group(2)
            lits = LIT_RE.findall(args)
            if not lits:
                continue
            # adjacent literals concatenate
            s = "".join(lits) if fn not in ('Sprintf',) else lits[0]
            if len(s) < 6 or not re.search('[a-z]', s):
                continue
            out.setdefault(PREFIX.get(fn, '') + s, os.path.basename(path))
    return out


def sample(fmt):
    s = fmt.replace('\\"', '"').replace('\\n', ' ')
    s = re.sub(r'%l?[du]', '5', s)
    s = re.sub(r'%-?\d*s', 'the thing', s)
    s = re.sub(r'%c', 'x', s)
    return s


def bot_regexes():
    out = []
    files = glob.glob(os.path.join(ROOT, 'pybothack', '*.py')) + \
        glob.glob(os.path.join(ROOT, 'pybothack', 'bots', '*.py'))
    for path in files:
        if path.endswith(('nhbridge.py', 'compat36.py')):
            continue
        tree = ast.parse(open(path).read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fname = ''
                if isinstance(node.func, ast.Name):
                    fname = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    fname = node.func.attr
                if fname in ('re_seq', 're_first_group', 're_first_groups',
                             'search', 'match', 'compile', 'startswith',
                             'endswith', 'fullmatch'):
                    for a in node.args[:1]:
                        if isinstance(a, ast.Constant) and \
                                isinstance(a.value, str):
                            out.append((a.value, os.path.basename(path),
                                        node.lineno, fname))
            if (isinstance(node, ast.Tuple) and len(node.elts) == 2
                    and isinstance(node.elts[0], ast.Constant)
                    and isinstance(node.elts[0].value, str)
                    and path.endswith('scraper.py')):
                out.append((node.elts[0].value, os.path.basename(path),
                            node.lineno, 'prompt-table'))
            if isinstance(node, ast.Assign) and \
                    isinstance(node.value, ast.Constant) and \
                    isinstance(node.value.value, str):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id.endswith('_RE'):
                        out.append((node.value.value,
                                    os.path.basename(path), node.lineno,
                                    'const'))
    return out


def main():
    s343 = c_strings(SRC343)
    s367 = c_strings(SRC367)
    set367 = set(s367)
    samples343 = [(fmt, sample(fmt), f) for fmt, f in s343.items()]
    keys367 = list(s367)
    report = []
    for rx, pyfile, line, kind in bot_regexes():
        try:
            if kind in ('startswith', 'endswith'):
                pat = re.compile(re.escape(rx))
            else:
                pat = re.compile(rx)
        except re.error:
            continue
        hits = []
        for fmt, smp, cfile in samples343:
            if pat.search(smp):
                hits.append((fmt, cfile))
        if not hits or len(hits) > 12:
            continue
        missing = [(fmt, cfile) for fmt, cfile in hits if fmt not in set367]
        if not missing:
            continue
        found_new = any(pat.search(sample(k)) for k in keys367)
        for fmt, cfile in missing:
            words = sorted(set(re.findall(r'[a-z]{4,}', fmt)), key=len)[-3:]
            cands = [k for k in keys367 if all(w in k for w in words[-2:])] \
                or [k for k in keys367 if words and words[-1] in k]
            close = difflib.get_close_matches(fmt, cands[:400], n=1,
                                              cutoff=0.5)
            report.append((pyfile, line, rx, fmt, cfile,
                           close[0] if close else None, found_new))
    seen = set()
    print("# BotHack message regexes vs 3.6.7 (automatic audit)\n")
    print("Columns: bot regex (file:line) | 3.4.3 message format it matched |"
          " closest 3.6.7 format | does the regex still match some 3.6.7 "
          "string?\n")
    for pyfile, line, rx, fmt, cfile, close, still in report:
        key = (rx, fmt)
        if key in seen:
            continue
        seen.add(key)
        print("- `%s:%d` `%s`\n  - 3.4.3 (%s): `%s`\n  - 3.6.7 closest: `%s`"
              "\n  - regex still matches something in 3.6.7: %s"
              % (pyfile, line, rx, cfile, fmt, close, still))


if __name__ == '__main__':
    main()
