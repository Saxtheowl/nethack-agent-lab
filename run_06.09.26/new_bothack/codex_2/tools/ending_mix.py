#!/usr/bin/env python3
"""How real games END, from each bot's own log - the half the xlogfile misses.

NetHack writes an xlogfile line only when the *game* ends (death, quit,
escape).  When the bot abandons a game instead - its own quit-when-idle
firing, a crash, the harness killing it - NetHack records nothing, so
tools/compare_realgames.py cannot see it.  This reads the bot logs.
"""
import re, sys, glob, collections

# ordered: first match wins, most specific first
RULES = [
    ('ascension',            rb'You ascend|death=ascended'),
    ('mort (NetHack)',       rb'You die\b|possessions identified'),
    ('quit: idle',           rb'min idle - quitting'),
    ('quit: stuck',          rb'too many actions within one game turn'),
    ('quit: no action',      rb'No action chosen - quitting'),
    ('crash: delegator',     rb'delegator caught error'),
    ('crash: autre',         rb'Traceback \(most recent call last\)'),
]

# NOT an ending: `unknown itemtype for item` is a faithful port of the
# original's own log/error at itemid.clj:188, which returns nil and lets play
# continue.  An earlier version of this file matched it and mis-reported four
# interrupted games as crashes.

def classify(path):
    try:
        d = open(path, 'rb').read()
    except OSError:
        return None
    tail = d[-400_000:]
    for label, pat in RULES:
        if re.search(pat, tail):
            return label
    # still running, or killed by the harness with no marker
    return 'interrompu / en cours'

def main(patterns):
    c = collections.Counter()
    logs = []
    for pat in patterns:
        logs += glob.glob(pat)
    for lg in logs:
        k = classify(lg)
        if k: c[k] += 1
    tot = sum(c.values())
    if not tot:
        print('aucun log trouvé'); return
    print(f"{tot} parties\n")
    order = [r[0] for r in RULES] + ['interrompu / en cours']
    for k in order:
        if c[k]:
            print(f"  {c[k]:4d}  {100*c[k]/tot:5.1f}%  {k}")
    ended = tot - c['interrompu / en cours']
    if ended:
        died = c['mort (NetHack)'] + c['ascension']
        print(f"\nparmi les {ended} parties réellement terminées : "
              f"{100*died/ended:.0f}% se terminent dans NetHack, "
              f"{100*(ended-died)/ended:.0f}% par abandon du bot")

if __name__ == '__main__':
    main(sys.argv[1:] or ['artifacts/pool_*/game*/run.log',
                          'artifacts/ascend_run*/game*/run.log',
                          'artifacts/ascension/*/game*/run.log'])
