#!/usr/bin/env python3
"""A small Clojure reader, enough to audit BotHack's source structurally.

Grepping finds text; the bugs that hurt are *structural* - a side-effecting call
sitting where an `or` reads its value, a `(str ...)` whose result lands in a set.
Those need the form tree, not lines.  This reads just enough Clojure for that:
lists, vectors, maps, sets, strings, character literals, comments and the
reader macros BotHack actually uses.  It is not a full reader and does not try
to be: unknown dispatch forms become plain symbols.

Each node is either a Sym/Str/Char/Num leaf carrying its source line, or a Form
with a `kind` ('list', 'vector', 'map', 'set') and children.
"""
import re


class Node(object):
    __slots__ = ('line',)


class Leaf(Node):
    __slots__ = ('text',)

    def __init__(self, text, line):
        self.text = text
        self.line = line

    def __repr__(self):
        return self.text


class Sym(Leaf):
    __slots__ = ()


class Str(Leaf):
    __slots__ = ()


class Char(Leaf):
    __slots__ = ()


class Num(Leaf):
    __slots__ = ()


class Kw(Leaf):
    __slots__ = ()


class Form(Node):
    __slots__ = ('kind', 'children')

    def __init__(self, kind, children, line):
        self.kind = kind
        self.children = children
        self.line = line

    def __repr__(self):
        inner = ' '.join(map(repr, self.children))
        wrap = {'list': '(%s)', 'vector': '[%s]', 'map': '{%s}',
                'set': '#{%s}', 'root': '%s'}
        return wrap.get(self.kind, '%s') % inner

    @property
    def head(self):
        """The symbol in head position, as text, or None."""
        if self.kind == 'list' and self.children and \
                isinstance(self.children[0], Sym):
            return self.children[0].text
        return None


_TOKEN = re.compile(r"""
    (?P<ws>[\s,]+)
  | (?P<comment>;[^\n]*)
  | (?P<char>\\(?:newline|space|tab|backspace|formfeed|return
                 |u[0-9a-fA-F]{4}|o[0-7]{1,3}|.))
  | (?P<string>"(?:[^"\\]|\\.)*")
  | (?P<setopen>\#\{)
  | (?P<dispatch>\#[\^'=_?<]?)
  | (?P<open>[\(\[\{])
  | (?P<close>[\)\]\}])
  | (?P<deref>@)
  | (?P<quote>['`~^])
  | (?P<atom>[^\s,;"'`~@^\(\)\[\]\{\}\\]+)
""", re.X)

_CLOSERS = {'(': ')', '[': ']', '{': '}'}
_KINDS = {'(': 'list', '[': 'vector', '{': 'map'}


def _emit(stack, node, pending_deref):
    """Append `node`, wrapping it in (deref ...) for each pending `@`."""
    while pending_deref and pending_deref[-1] == len(stack):
        pending_deref.pop()
        node = Form('list', [Sym('deref', node.line), node], node.line)
    stack[-1][1].append(node)


def read_forms(text):
    """Top-level forms of a Clojure source string.

    `@x` is expanded to `(deref x)` rather than skipped.  It has to be: the
    whole point of the atom audit is telling `@game` (the value) from `game`
    (the atom), and a reader that drops the `@` reports every deref as a bug.
    Other reader macros (quote, syntax-quote, metadata) stay transparent -
    nothing here depends on them.
    """
    pos, line = 0, 1
    stack = [('root', [], 1)]
    pending_deref = []
    n = len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if m is None:                       # unreadable char: skip it
            if text[pos] == '\n':
                line += 1
            pos += 1
            continue
        tok = m.group(0)
        kind = m.lastgroup
        line_here = line
        line += tok.count('\n')
        pos = m.end()
        if kind in ('ws', 'comment', 'quote', 'dispatch'):
            continue                        # metadata and quoting: transparent
        if kind == 'deref':
            pending_deref.append(len(stack))
            continue
        if kind == 'setopen':
            stack.append(('set', [], line_here))
        elif kind == 'open':
            stack.append((_KINDS[tok], [], line_here))
        elif kind == 'close':
            if len(stack) == 1:
                continue                    # unbalanced: ignore
            k, children, ln = stack.pop()
            _emit(stack, Form(k, children, ln), pending_deref)
        elif kind == 'string':
            _emit(stack, Str(tok[1:-1], line_here), pending_deref)
        elif kind == 'char':
            _emit(stack, Char(tok[1:], line_here), pending_deref)
        else:
            t = tok
            if t.startswith(':'):
                _emit(stack, Kw(t, line_here), pending_deref)
            elif re.match(r'^[-+]?[.0-9]', t):
                _emit(stack, Num(t, line_here), pending_deref)
            else:
                _emit(stack, Sym(t, line_here), pending_deref)
    while len(stack) > 1:                   # tolerate truncation
        k, children, ln = stack.pop()
        stack[-1][1].append(Form(k, children, ln))
    return stack[0][1]


def walk(node):
    """Every node, parents before children."""
    yield node
    if isinstance(node, Form):
        for c in node.children:
            for x in walk(c):
                yield x


def enclosing_defn(forms, target_line):
    """Name of the top-level definition containing a line."""
    best = None
    for f in forms:
        if not isinstance(f, Form) or f.line > target_line:
            continue
        if (f.head or '').startswith('def') and len(f.children) > 1:
            best = f
    if best is None:
        return '?'
    name = best.children[1]
    return getattr(name, 'text', '?')
