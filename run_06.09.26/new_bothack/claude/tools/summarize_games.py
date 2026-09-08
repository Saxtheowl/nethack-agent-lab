#!/usr/bin/env python3
"""Summarise a batch of games of either bot from its logs + NetHack's xlogfile."""
import glob
import gzip
import os
import re
import sys


def _open(path):
    """Open a log, transparently handling the gzipped evidence in artifacts/."""
    if os.path.exists(path):
        return open(path, errors='replace')
    return gzip.open(path + '.gz', 'rt', errors='replace')


def _exists(path):
    return os.path.exists(path) or os.path.exists(path + '.gz')


def py_games(root):
    out = []
    for d in sorted(glob.glob(os.path.join(root, 'artifacts/games/py/game*'))):
        log = os.path.join(d, 'run.log')
        if not _exists(log):
            continue
        txt = _open(log).read()
        m = re.findall(r'final state: dlvl=(\S+) turn=(\S+) score=(\S+) '
                       r'hp=(\S+)', txt)
        acts = txt.count('Performing action')
        died = 'You die...' in txt
        maxdlvl = max([int(x) for x in re.findall(r'dlvl changed from \S+ to '
                                                  r'Dlvl:(\d+)', txt)] or [1])
        if m:
            dlvl, turn, score, hp = m[-1]

            def _i(v):
                try:
                    return int(v)
                except ValueError:
                    return 0
            out.append(dict(name=os.path.basename(d), dlvl=dlvl,
                            maxdlvl=maxdlvl, turn=_i(turn), score=_i(score),
                            actions=acts, died=died))
    return out


def orig_games(root):
    out = []
    for d in sorted(glob.glob(os.path.join(root,
                                           'artifacts/games/orig/game*'))):
        log = os.path.join(d, 'bothack.log')
        if not _exists(log):
            continue
        acts = 0
        turn = 0
        score = 0
        dlvl = 1
        maxdlvl = 1
        died = False
        with _open(log) as f:
            for line in f:
                if 'Performing action' in line:
                    acts += 1
                elif 'new botl status' in line:
                    mt = re.search(r':turn (\d+)', line)
                    ms = re.search(r':score (\d+)', line)
                    md = re.search(r':dlvl Dlvl:(\d+)', line)
                    if mt:
                        turn = max(turn, int(mt.group(1)))
                    if ms:
                        score = max(score, int(ms.group(1)))
                    if md:
                        dlvl = int(md.group(1))
                        maxdlvl = max(maxdlvl, dlvl)
                elif 'You die...' in line:
                    died = True
        out.append(dict(name=os.path.basename(d), dlvl="Dlvl:%d" % dlvl,
                        maxdlvl=maxdlvl, turn=turn, score=score, actions=acts,
                        died=died))
    return out


def show_md(title, games):
    print("**%s** (%d games)\n" % (title, len(games)))
    print("| game | max dlvl | turns | score | actions | died |")
    print("| --- | --- | --- | --- | --- | --- |")
    for g in games:
        print("| %s | %s | %d | %d | %d | %s |"
              % (g['name'], g['maxdlvl'], g['turn'], g['score'], g['actions'],
                 "yes" if g['died'] else "no"))
    if games:
        def med(k):
            v = sorted(g[k] for g in games)
            m = (v[(len(v) - 1) // 2] + v[len(v) // 2]) / 2.0
            return int(m) if m == int(m) else round(m, 1)
        print("| **median** | **%s** | **%s** | **%s** | **%s** | %d/%d |"
              % (med('maxdlvl'), med('turn'), med('score'), med('actions'),
                 sum(1 for g in games if g['died']), len(games)))
    print()


def show(title, games):
    print("=== %s (%d games)" % (title, len(games)))
    if not games:
        return
    print("    %-8s %-8s %7s %8s %8s %6s" % ("game", "maxdlvl", "turns",
                                             "score", "actions", "died"))
    for g in games:
        print("    %-8s %-8s %7d %8d %8d %6s"
              % (g['name'], g['maxdlvl'], g['turn'], g['score'], g['actions'],
                 g['died']))
    def med(k):
        v = sorted(g[k] for g in games)
        return v[len(v) // 2]
    print("    median: maxdlvl %s  turns %s  score %s  actions %s"
          % (med('maxdlvl'), med('turn'), med('score'), med('actions')))
    print("    deaths: %d/%d" % (sum(1 for g in games if g['died']),
                                 len(games)))


def main():
    args = [a for a in sys.argv[1:] if a != '--markdown']
    root = args[0] if args else '.'
    fn = show_md if '--markdown' in sys.argv else show
    fn("python port", py_games(root))
    fn("original BotHack", orig_games(root))


if __name__ == '__main__':
    main()
