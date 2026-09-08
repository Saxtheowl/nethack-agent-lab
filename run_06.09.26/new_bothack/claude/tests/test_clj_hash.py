#!/usr/bin/env python3
"""Check the port's Clojure hashing against values dumped from the JVM.

Every expected number here was printed by tools/cljcmp/dump_hash.clj running
inside the original project (Clojure 1.6 on a JDK 8), not derived by reading
the algorithm.  Clojure set iteration order is the HAMT order of the elements'
`hasheq`, and `hostile-threats` hands the bot a *set* of monsters, so a wrong
hash silently changes which monster `fight` picks.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pybothack.monster import monster_hasheq, monster_type_hasheq   # noqa
from pybothack.util import (clj_keyword_hasheq, clj_symbol_hasheq,  # noqa
                            murmur3_hash_long, murmur3_hash_int,
                            java_string_hash, clj_hash_ordered,
                            clj_hash_unordered, murmur3_mix_coll_hash,
                            murmur3_hash_unencoded_chars)

FAILED = []


def check(name, got, expected):
    if got == expected:
        print('  ok   %-34s %d' % (name, got))
    else:
        print('  FAIL %-34s got %d, JVM said %d' % (name, got, expected))
        FAILED.append(name)


def main():
    print('primitives (clojure.lang.Murmur3 / Util.hasheq)')
    for n, exp in ((1, 1392991556), (2, -971005196), (17, 2038905747),
                   (4396, 799854095), (-1, 1651860712), (0, 0),
                   (1000000, 1669527334)):
        check('hashLong(%d)' % n, murmur3_hash_long(n), exp)
    check('hasheq("abc")', murmur3_hash_int(java_string_hash('abc')),
          74834163)
    check('hasheq("little dog")',
          murmur3_hash_int(java_string_hash('little dog')), 1443607713)
    check('hashUnencodedChars("x")', murmur3_hash_unencoded_chars('x'),
          -427671604)
    check('hashUnencodedChars("white")',
          murmur3_hash_unencoded_chars('white'), 381272698)

    print('keywords and symbols (the arithmetic-shift trap in hashCombine)')
    for n, exp in (('x', 2099068185), ('y', -1757859776),
                   ('white', -483998618), ('known', 1655795903),
                   ('first-known', -868392170), ('fleeing', 1600491278),
                   ('remembered', 1425906249)):
        check('hasheq(:%s)' % n, clj_keyword_hasheq(n), exp)
    check("hasheq('bothack.monster.Monster)",
          clj_symbol_hasheq('bothack.monster.Monster'), -639613306)

    print('collections')
    check('hasheq([])', clj_hash_ordered([], lambda _: 0), -2017569654)
    check('hasheq([1 2])', clj_hash_ordered([1, 2], murmur3_hash_long),
          156247261)
    check('hasheq(#{})', clj_hash_unordered([], lambda _: 0), -15128758)
    check('mixCollHash(0, 0)', murmur3_mix_coll_hash(0, 0), -15128758)

    print('Monster records (hasheq = type-hash XOR mapHasheq)')
    samples = [
        (dict(y=1, awake=False, color='white', remembered=False, type=None,
              friendly=False, glyph='d', x=1, known=0, peaceful=None),
         -1485211035),
        (dict(y=18, awake=True, color='white', remembered=False, type=None,
              fleeing=False, friendly=False, glyph='d', x=23, known=4396,
              peaceful=None, **{'first-known': 4392}), 2068560490),
        (dict(y=19, awake=True, color='gray', remembered=False, type=None,
              fleeing=True, friendly=False, glyph='s', x=23, known=4396,
              peaceful=None, **{'first-known': 4392}), 399142901),
        (dict(y=1, awake=False, color='white', remembered=True, type=None,
              friendly=False, glyph='d', x=1, known=0, peaceful=True),
         130182025),
    ]
    for i, (m, exp) in enumerate(samples):
        check('monster sample %d' % i, monster_hasheq(m), exp)

    print('every monster type has a dumped hasheq')
    from pybothack import montype
    missing = []
    for t in montype.monster_types:
        try:
            monster_type_hasheq(t)
        except KeyError:
            missing.append(t['name'])
    if missing:
        print('  FAIL %d type(s) with no dumped hasheq: %s'
              % (len(missing), missing[:5]))
        FAILED.append('monster type coverage')
    else:
        print('  ok   all %d types' % len(montype.monster_types))

    print()
    if FAILED:
        print('%d check(s) failed: %s' % (len(FAILED), ', '.join(FAILED)))
        return 1
    print('all Clojure-hash checks match the JVM dump')
    return 0


if __name__ == '__main__':
    sys.exit(main())
