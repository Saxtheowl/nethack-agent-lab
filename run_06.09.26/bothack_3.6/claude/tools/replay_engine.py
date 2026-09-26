#!/usr/bin/env python3
"""Feed the answers of a recorded protocol trace back to a fresh engine,
without the bot: the engine alone reaches the recorded state in minutes
(an engine crash, a strange turn...).  The engine must see the same game:
same seed, same rungame options (scenario, assists) and the same clock.

    python3 tools/replay_engine.py runs/replays/replay-planes504/protocol.trace.gz \\
        <scratch-dir> [--until-turn N] [--fixed-time EPOCH] -- --seed 504 --scenario planes

--fixed-time: games recorded before the fixed clock of seeded games
(engine getnow(), NH_FIXED_TIME) ran on the real clock: pass the epoch of
the original start (same day, day or night alike) to replay them.
Stops at the end of the trace, at --until-turn, or when the engine dies
(its engine.stderr then holds the backtrace).
"""
import argparse
import gzip
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nhbot import rungame  # noqa: E402
from nhbot.engine import Engine  # noqa: E402


def answers(path):
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt', errors='replace') as f:
        try:
            for line in f:
                if line.startswith('> '):
                    yield line[2:].rstrip('\n')
        except (EOFError, OSError):
            return


def main():
    argv = sys.argv[1:]
    extra = []
    if '--' in argv:
        i = argv.index('--')
        argv, extra = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('trace')
    ap.add_argument('out')
    ap.add_argument('--until-turn', type=int, default=None)
    ap.add_argument('--fixed-time', default=None)
    ap.add_argument('--binary', default=None,
                    help="engine binary or wrapper (e.g. a gdb script)")
    a = ap.parse_args(argv)
    args = rungame.build_parser().parse_args(['--out', a.out] + extra)
    if args.scenario:
        args.wizard = True
    if args.no_assist:
        args.invincible = False
        args.nostarve = False
        args.kit = 'none'
    assists = rungame.assists_env(args)
    if a.fixed_time:
        assists['NH_FIXED_TIME'] = a.fixed_time
    os.makedirs(a.out, exist_ok=True)
    eng = Engine(a.out, seed=args.seed, wizard=args.wizard, assists=assists,
                 name=args.name,
                 **({'binary': os.path.abspath(a.binary)} if a.binary else {}),
                 trace=gzip.open(os.path.join(a.out, 'protocol.trace.gz'),
                                 'wt', compresslevel=1))
    eng.start()
    n = 0
    turn = 0
    for ans in answers(a.trace):
        req = eng.next_request()
        if req is None:
            break
        turn = (eng.status or {}).get('turn') or turn
        if a.until_turn and turn >= a.until_turn:
            break
        eng._send(ans)
        n += 1
        if n % 5000 == 0:
            print("answers %d  turn %s" % (n, turn), flush=True)
    else:
        while eng.next_request() is not None:
            break
    rc = eng.proc.poll()
    print("replayed %d answers, turn %s, engine rc=%s, verdict=%s"
          % (n, turn, rc, (eng.verdict or {}).get('how_s')))
    with open(os.path.join(a.out, 'engine.stderr')) as f:
        err = f.read()
    if err.strip():
        print(err)
    if rc is None:
        eng.stop()
    eng.trace.close()


if __name__ == '__main__':
    main()
