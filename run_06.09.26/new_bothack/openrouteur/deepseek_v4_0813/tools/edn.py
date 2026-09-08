"""Minimal EDN reader/writer for the value subset used by the oracle.

Handles: nil, true/false, integers, floats, strings, keywords (:kw as bare
Python str), chars (\\c), symbols, vectors, lists, sets (#{...}), maps
({... => ...} with symbol/keyword/string keys).
"""

import re


class _Reader:
    def __init__(self, s):
        self.s = s
        self.i = 0
        self.n = len(s)

    def _ws(self):
        while self.i < self.n and self.s[self.i] in " \t\r\n,":
            self.i += 1

    def peek(self):
        self._ws()
        if self.i < self.n:
            return self.s[self.i]
        return None

    def read(self):
        self._ws()
        if self.i >= self.n:
            return None
        c = self.s[self.i]
        if c == '{':
            return self._map()
        if c == '[':
            return self._seq(']')
        if c == '(':
            return self._seq(')')
        if c == '#':
            return self._dispatch()
        if c == '"':
            return self._str()
        if c == '\\':
            return self._char()
        return self._token()

    def _dispatch(self):
        self.i += 1
        c = self.s[self.i]
        if c == '{':
            return self._set()
        return self._token()

    def _seq(self, close):
        self.i += 1
        out = []
        while True:
            self._ws()
            if self.i >= self.n:
                break
            if self.s[self.i] == close:
                self.i += 1
                break
            out.append(self.read())
        return out

    def _set(self):
        return frozenset(self._seq('}'))

    def _map(self):
        self.i += 1
        out = {}
        while True:
            self._ws()
            if self.i >= self.n:
                break
            if self.s[self.i] == '}':
                self.i += 1
                break
            k = self.read()
            self._ws()
            v = self.read()
            out[k] = v
        return out

    def _str(self):
        self.i += 1
        buf = []
        while self.i < self.n:
            c = self.s[self.i]
            if c == '\\':
                nxt = self.s[self.i + 1]
                buf.append({'n': '\n', 't': '\t', 'r': '\r', '"': '"',
                            '\\': '\\'}.get(nxt, nxt))
                self.i += 2
                continue
            if c == '"':
                self.i += 1
                break
            buf.append(c)
            self.i += 1
        return ''.join(buf)

    def _char(self):
        self.i += 1
        c = self.s[self.i]
        if c in '\\':
            self.i += 1
            name = self.s[self.i]
            named = {'n': '\n', 't': '\t', 'r': '\r', 's': ' ',
                     'b': chr(8)}
            if name in named:
                self.i += 1
                return named[name]
            return name
        self.i += 1
        return c

    def _token(self):
        m = re.match(r'[^\s,{}\[\]()]+', self.s[self.i:])
        tok = m.group(0)
        self.i += len(tok)
        if tok == 'nil':
            return None
        if tok == 'true':
            return True
        if tok == 'false':
            return False
        if tok.startswith(':'):
            return tok[1:]
        if re.match(r'^[+-]?\d+$', tok):
            return int(tok)
        if re.match(r'^[+-]?\d*\.\d+([eE][+-]?\d+)?$', tok):
            return float(tok)
        if re.match(r'^[+-]?\d+[eE][+-]?\d+$', tok):
            return float(tok)
        return tok


def loads(s):
    r = _Reader(s)
    v = r.read()
    return v


def dumps(v):
    if v is None:
        return 'nil'
    if v is True:
        return 'true'
    if v is False:
        return 'false'
    if isinstance(v, str):
        if v == '' :
            return '""'
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, dict):
        return '{' + ', '.join(_dumps_key(k) + ' ' + dumps(x) for k, x in v.items()) + '}'
    if isinstance(v, (list, tuple)):
        return '[' + ' '.join(dumps(x) for x in v) + ']'
    if isinstance(v, (set, frozenset)):
        return '#{' + ' '.join(dumps(x) for x in sorted(v, key=str)) + '}'
    return str(v)


def _dumps_key(k):
    """Emit a map key as a Clojure keyword."""
    s = str(k)
    if re.match(r'^[A-Za-z0-9*+!_?\'<>=$%&.\\/-]+$', s):
        return ':' + s
    return dumps(k)