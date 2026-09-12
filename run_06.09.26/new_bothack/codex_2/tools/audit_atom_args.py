#!/usr/bin/env python3
"""Find every place BotHack passes the game *atom* where a function wants the map.

`{:keys [game]}` destructured out of a `bh` map binds the **atom**.  In that
scope `@game` is the value and a bare `game` is the atom - and Clojure does not
complain when the atom reaches a function that expects a map: `(:player atom)`
and `(get-in atom [...])` simply answer nil.  Each such site is an upstream bug
with silent, observable behaviour, and a port that "helpfully" derefs is *not*
faithful.

Two were found this way and are reproduced deliberately:

  * `Throw`'s `(not (visible? game level to-update))` - always true, so Throw
    always marks the tile;
  * `Discoveries`' `(difference (:used-names game) @known-names)` - always nil,
    so it never forgets a name.

Scoping is structural, not textual: a nested `(choose-action [_ game] ...)`
rebinds `game` to a *value*, and a line-based scan reports every use inside it
(that mistake turned 12 real sites into 114).  So this walks the form tree and
tracks what `game` currently means.

    tools/audit_atom_args.py <src dir>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.cljread import (Form, Kw, Sym, read_forms,              # noqa: E402
                           enclosing_defn)

#: forms that legitimately take the atom
ATOM_OK = {'swap!', 'reset!', 'compare-and-set!', 'deref', 'atom', 'add-watch',
           'remove-watch', 'set-validator!', 'partial', 'fn', 'update-inventory',
           'update-container', 'update-on-known-position',
           'update-before-action', 'update-at-player-when-known',
           # takes the atom on purpose: it does its own @game and swap!
           'handle-door-message'}
#: heads that introduce parameter vectors
FN_HEADS = {'fn', 'fn*', 'defn', 'defn-', 'defmacro', 'defmethod'}
BIND_HEADS = {'let', 'loop', 'when-let', 'if-let', 'when-some', 'if-some',
              'for', 'doseq', 'with-open', 'letfn', 'dotimes', 'binding'}
#: forms whose children are `(method [params] body...)` lists.  `defaction` is
#: BotHack's own macro and carries the `(handler [_ {:keys [game] :as bh}] ...)`
#: that holds both of the real bugs this audit exists for - omitting it made the
#: audit silently report nothing.
METHOD_HEADS = {'reify', 'defaction', 'deftype', 'defrecord', 'extend-type',
                'extend-protocol', 'proxy', 'specify!'}


def _binds_game(node):
    """Does this binding form bind `game`, and to the atom or to a value?

    Returns 'atom', 'value' or None.  `{:keys [... game ...]}` is the atom
    (it is destructured out of a bh map); a plain `game` symbol is a value.
    """
    if isinstance(node, Sym) and node.text == 'game':
        return 'value'
    if isinstance(node, Form) and node.kind == 'map':
        kids = node.children
        for i in range(0, len(kids) - 1, 2):
            k, v = kids[i], kids[i + 1]
            if isinstance(k, Kw) and k.text == ':keys' and \
                    isinstance(v, Form) and v.kind == 'vector':
                if any(isinstance(x, Sym) and x.text == 'game'
                       for x in v.children):
                    return 'atom'
            if isinstance(k, Sym) and k.text == 'game':
                return 'value'          # {game :game} style
            if isinstance(k, Kw) and k.text == ':as' and \
                    isinstance(v, Sym) and v.text == 'game':
                return 'value'          # :as game destructures the *value*
    return None


def _params_effect(vec):
    """What a parameter vector does to the meaning of `game`."""
    if not isinstance(vec, Form) or vec.kind != 'vector':
        return None
    effect = None
    for p in vec.children:
        e = _binds_game(p)
        if e:
            effect = e
    return effect


def walk_scoped(node, state, out, forms):
    """Depth-first walk carrying whether `game` currently means the atom."""
    if not isinstance(node, Form):
        return
    head = node.head if node.kind == 'list' else None

    # --- forms that rebind `game` -------------------------------------------
    if head in FN_HEADS:
        for child in node.children[1:]:
            e = _params_effect(child)
            if e:
                state = e
            # (fn name? [params] body) and multi-arity ([params] body) lists
            if isinstance(child, Form) and child.kind == 'list' and \
                    child.children and _params_effect(child.children[0]):
                inner = _params_effect(child.children[0])
                for sub in child.children[1:]:
                    walk_scoped(sub, inner, out, forms)
                continue
            walk_scoped(child, state, out, forms)
        return
    if head in METHOD_HEADS:
        for child in node.children[1:]:
            if isinstance(child, Form) and child.kind == 'list' and \
                    len(child.children) > 1:
                inner = _params_effect(child.children[1])
                sub_state = inner or state
                for sub in child.children[2:]:
                    walk_scoped(sub, sub_state, out, forms)
                continue
            walk_scoped(child, state, out, forms)
        return
    if head in BIND_HEADS and len(node.children) > 1 and \
            isinstance(node.children[1], Form) and \
            node.children[1].kind == 'vector':
        vec = node.children[1].children
        inner = state
        for i in range(0, len(vec) - 1, 2):
            walk_scoped(vec[i + 1], inner, out, forms)
            e = _binds_game(vec[i])
            if e:
                inner = e
        for sub in node.children[2:]:
            walk_scoped(sub, inner, out, forms)
        return

    # --- a call in atom scope ----------------------------------------------
    if node.kind == 'list' and state == 'atom' and head not in ATOM_OK:
        for arg in node.children[1:]:
            if isinstance(arg, Sym) and arg.text == 'game':
                out.append((node.line, head or '?',
                            enclosing_defn(forms, node.line),
                            repr(node)[:130]))
                break
    for child in node.children:
        walk_scoped(child, state, out, forms)


def scan(path):
    forms = read_forms(open(path).read())
    out = []
    for top in forms:
        walk_scoped(top, None, out, forms)
    return out


def clj_sources(root):
    """Every .clj under `root`, recursively - `bots/mainbot.clj` lives in a
    subdirectory and a flat listdir silently skips the densest file."""
    found = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in sorted(files):
            if fn.endswith('.clj'):
                found.append(os.path.join(dirpath, fn))
    return sorted(found)


def main():
    root = sys.argv[1]
    total = 0
    for path in clj_sources(root):
        fn = os.path.relpath(path, root)
        hits = scan(path)
        if not hits:
            continue
        print('== %s' % fn)
        for line, callee, where, text in hits:
            print('  %s:%d  in %s: the atom reaches `%s`' % (fn, line, where,
                                                             callee))
            print('      %s' % text)
            total += 1
    print('\n%d site(s) to read' % total)


if __name__ == '__main__':
    main()
