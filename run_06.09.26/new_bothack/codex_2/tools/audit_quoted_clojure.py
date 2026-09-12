#!/usr/bin/env python3
"""Do the Clojure snippets quoted in the port's comments still exist upstream?

The port documents itself by quoting the Clojure it implements.  Those quotes
are load-bearing: they are what a reader checks the port against, and what I
check it against when hunting a divergence.  A quote that no longer matches the
source - a paraphrase, a stale copy, a function renamed upstream - turns the
comment into a confident lie, and a confident lie is worse than no comment.

Quotes routinely elide with `...`.  That is fine and is not drift, so each
fragment is split on `...` and every remaining segment long enough to be
distinctive is required to appear in the source.  Elision hides drift only
inside the elided part, which is the price of readable comments.

What this cannot catch, and what motivated it: the `quit-when-idle` defect,
where the comment quoted

    (defn- u "unpause" [] (r) (if (:inhibited ...) (unpause a)))

perfectly - and then implemented `u` where the original calls `unpause`.  The
quote was right; the attribution was wrong.  No textual check finds that.  This
finds the cheaper, commoner failure of the quote itself drifting.

Usage:  BOTHACK_SRC=<checkout> python3 tools/audit_quoted_clojure.py
"""
import io
import os
import re
import sys
import tokenize

HEADS = (r'defn-?|def|defmacro|defrecord|defprotocol|reify|let|if-let|'
         r'when-let|if-some|when-some|loop|fn|future|doseq|when|when-not|'
         r'if-not|swap!|reset!|ref-set|dosync|send|register-handler|'
         r'log/\w+|condp|case|cond|update-in|assoc-in|some->|some->>|->>|->|'
         r'with-reason|at-player|curlvl|navigate|seek')

#: Forms that explain a *core Clojure* function rather than quoting BotHack.
#: They use metasyntactic argument names, which BotHack's own code never does.
META_ARGS = re.compile(r'\b(m k v|m path f|coll|xs|f & args|k v)\b')
FORM = re.compile(r'\((?:%s)\b.{10,240}' % HEADS, re.S)

#: a segment shorter than this matches too much to be evidence of anything
MIN_SEGMENT = 24


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def load_source(src):
    body = []
    for root, _dirs, files in os.walk(os.path.join(src, 'src')):
        for f in files:
            if f.endswith('.clj'):
                with open(os.path.join(root, f), encoding='utf-8',
                          errors='replace') as fh:
                    body.append(fh.read())
    return norm('\n'.join(body))


def prose_of(path):
    """Every comment and string literal in a Python file, with line numbers."""
    out = []
    with open(path, 'rb') as fh:
        try:
            for tok in tokenize.tokenize(fh.readline):
                if tok.type in (tokenize.COMMENT, tokenize.STRING):
                    out.append((tok.start[0], tok.string))
        except (tokenize.TokenError, IndentationError, SyntaxError):
            pass
    return out


def main():
    src = os.environ.get('BOTHACK_SRC')
    if not src or not os.path.isdir(src):
        print("set BOTHACK_SRC to the BotHack checkout")
        return 2
    hay = load_source(src)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    checked = missing = elided = 0
    for dirpath, _d, files in os.walk(os.path.join(root, 'pybothack')):
        for f in sorted(files):
            if not f.endswith('.py'):
                continue
            path = os.path.join(dirpath, f)
            rel = os.path.relpath(path, root)
            for lineno, text in prose_of(path):
                # strip Python comment markers so the Clojure reads cleanly
                body = re.sub(r'^\s*#\s?', '', text, flags=re.M)
                for m in FORM.finditer(body):
                    frag = m.group(0)
                    segs = [norm(s) for s in frag.split('...')]
                    if len(segs) > 1:
                        elided += 1
                    for seg in segs:
                        # trailing junk from the regex window: trim to the last
                        # closing paren so a half-token is not "missing"
                        seg = seg[:seg.rfind(')') + 1] if ')' in seg else seg
                        if len(seg) < MIN_SEGMENT:
                            continue
                        if META_ARGS.search(seg):
                            continue
                        checked += 1
                        if seg not in hay:
                            missing += 1
                            print("%s:%d  quoted Clojure not found upstream:"
                                  % (rel, lineno))
                            print("    %s" % seg[:120])
    print("\n%d segments checked (%d fragments contained an elision), "
          "%d not found in the BotHack source" % (checked, elided, missing))
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
