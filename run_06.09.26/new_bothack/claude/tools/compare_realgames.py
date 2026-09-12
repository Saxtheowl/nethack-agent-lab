#!/usr/bin/env python3
"""Compare the two bots' REAL-GAME results from NetHack's own xlogfile.

The xlogfile is written by NetHack, not by either bot or by this harness, so it
is the one record neither implementation can flatter.  Games are attributed by
player name: the pools give the original and the port disjoint name prefixes.

Only games NetHack itself recorded appear here.  A game the bot abandons - its
own quit-when-idle firing, a crash, or the harness killing it - leaves no
xlogfile line, so this measures *how games end when they end in NetHack*, and
tools/ascend_summary.py measures the rest.
"""
import re, sys, collections

ORIG_PREFIXES = ('origbot', 'origp', 'origsmk')

#: NetHack writes its xlogfile to a path fixed at compile time, and a
#: neighbouring workspace on this machine (codex_2) shares that destination for
#: some of its runs.  Its games therefore land in *this* var/xlogfile and, since
#: anything not matching ORIG_PREFIXES used to count as "the port", were being
#: reported as ours.  Measured on 2026-09-11: 21 of 192 lines were not ours.
#: Excluded by player-name prefix, with a count printed so the exclusion is
#: visible rather than silent.
FOREIGN_PREFIXES = ('codex', 'seed1009', 'patch2')

def load(path):
    rows, foreign = [], 0
    for line in open(path):
        r = dict(kv.split('=', 1) for kv in line.strip().split(':') if '=' in kv)
        if 'name' in r and 'points' in r:
            if r['name'].startswith(FOREIGN_PREFIXES):
                foreign += 1
                continue
            rows.append(r)
    if foreign:
        print("note: %d games excluded as another workspace's (prefixes %s)\n"
              % (foreign, ", ".join(FOREIGN_PREFIXES)))
    return rows

def side(name):
    return 'original' if name.startswith(ORIG_PREFIXES) else 'port'

def pct(xs, p):
    if not xs: return 0
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * p))]

def summarise(rows):
    if not rows:
        return None
    lvl = [int(r['maxlvl']) for r in rows]
    pts = [int(r['points']) for r in rows]
    trn = [int(r['turns']) for r in rows]
    rt  = [int(r['realtime']) for r in rows]
    return {
        'n': len(rows),
        'ascended': sum(1 for r in rows if r['death'] == 'ascended'),
        'dlvl_med': pct(lvl, .5), 'dlvl_p90': pct(lvl, .9), 'dlvl_max': max(lvl),
        'score_med': pct(pts, .5), 'score_max': max(pts),
        'turns_med': pct(trn, .5), 'turns_max': max(trn),
        'mins_med': pct(rt, .5) // 60,
        'deep15': sum(1 for v in lvl if v >= 15),
        'mines': sum(1 for r in rows if r.get('deathdnum') == '2'),
    }

def main(path):
    rows = load(path)
    by = collections.defaultdict(list)
    for r in rows:
        by[side(r['name'])].append(r)
    o, p = summarise(by['original']), summarise(by['port'])

    rowdefs = [
        ('parties enregistrées', 'n', '{}'),
        ('ascensions',           'ascended', '{}'),
        ('Dlvl médian',          'dlvl_med', '{}'),
        ('Dlvl p90',             'dlvl_p90', '{}'),
        ('Dlvl max',             'dlvl_max', '{}'),
        ('parties Dlvl>=15',     'deep15', '{}'),
        ('morts dans les Mines', 'mines', '{}'),
        ('score médian',         'score_med', '{:,}'),
        ('score max',            'score_max', '{:,}'),
        ('tours médians',        'turns_med', '{:,}'),
        ('tours max',            'turns_max', '{:,}'),
        ('durée médiane (min)',  'mins_med', '{}'),
    ]
    w = max(len(r[0]) for r in rowdefs)
    print(f"{'':{w}}  {'original':>12}  {'portage':>12}")
    print(f"{'':{w}}  {'-'*12}  {'-'*12}")
    for label, key, fmt in rowdefs:
        ov = fmt.format(o[key]) if o else '-'
        pv = fmt.format(p[key]) if p else '-'
        print(f"{label:{w}}  {ov:>12}  {pv:>12}")

    print("\ncauses de mort partagées (original / portage):")
    def causes(rs):
        return collections.Counter(
            re.sub(r'^killed by an? ', '', r['death']) for r in rs)
    co, cp = causes(by['original']), causes(by['port'])
    keys = sorted(set(co) | set(cp), key=lambda k: -(co[k] + cp[k]))[:12]
    for k in keys:
        print(f"  {co[k]:3d} / {cp[k]:3d}  {k}")

    if o and o['n'] < 20:
        print(f"\nAVERTISSEMENT: seulement {o['n']} parties pour l'original - "
              "trop peu pour conclure quoi que ce soit.")

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1
         else 'upstream/nh343/var/xlogfile')
