"""Run one BotHack game on the patched NetHack 3.6.7 and keep the evidence.

    python3 -m nhbot.rungame --out runs/manual/g1 --seed 42
    python3 -m nhbot.rungame --out runs/manual/g2 --seed 42 --goal minetown
    python3 -m nhbot.rungame --out runs/manual/g3 --no-assist

Files written in --out:
    manifest.json     what was run (engine/bot hashes, seed, assists, limits)
    result.json       outcome category, reason, engine verdict, progression
    progress.jsonl    milestones (depth, branches, special levels, assists)
    last_steps.jsonl  ring buffer: observations/answers/actions before the end
    bot.log           bot warnings and errors
    assist.jsonl      every assist intervention (written by the engine)
    nhdir/xlogfile    NetHack's own record; nhdir/dumplog.txt at game end
    engine.stderr     engine diagnostics
"""
import argparse
import hashlib
import json
import logging
import os
import platform
import random
import socket
import subprocess
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nhbot.engine import (BINARY, Engine, EngineEOF, cleanup_level_files,  # noqa
                          read_xlogfile)
from nhbot.recorder import Recorder  # noqa: E402
from nhbot.supervisor import DEFAULT_LIMITS, Supervisor  # noqa: E402

DEFAULT_KIT = os.path.join(ROOT, 'config', 'kit-default.txt')

OUTCOMES = ('ascended', 'died', 'quit', 'escaped', 'goal_reached', 'stuck',
            'limit', 'crash_bot', 'crash_engine', 'unknown')


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def tree_hash(paths, exts=('.py', '.c', '.h')):
    h = hashlib.sha256()
    for base in paths:
        for dirpath, dirnames, filenames in sorted(os.walk(base)):
            dirnames.sort()
            if '__pycache__' in dirpath:
                continue
            for fn in sorted(filenames):
                if fn.endswith(exts):
                    p = os.path.join(dirpath, fn)
                    h.update(p[len(base):].encode())
                    with open(p, 'rb') as f:
                        h.update(f.read())
    return h.hexdigest()[:16]


_CODE_HASH = None


def code_hashes():
    global _CODE_HASH
    if _CODE_HASH is None:
        patch = os.path.join(ROOT, 'engine', 'nethack-3.6.7-bot.patch')
        _CODE_HASH = {
            'engine_binary_sha256': sha256_file(BINARY),
            'engine_patch_sha256': (sha256_file(patch)
                                    if os.path.exists(patch) else None),
            'bot_code_hash': tree_hash([os.path.join(ROOT, 'pybothack'),
                                        os.path.join(ROOT, 'nhbot')]),
        }
        try:
            _CODE_HASH['git_head'] = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            _CODE_HASH['git_head'] = None
    return _CODE_HASH


def assists_env(args):
    env = {}
    if args.invincible:
        env['NH_ASSIST_INVINCIBLE'] = 1
    if args.nostarve:
        env['NH_ASSIST_NOSTARVE'] = 1
    if args.kit and args.kit != 'none':
        env['NH_ASSIST_KIT'] = os.path.abspath(args.kit)
    return env


def graceful_quit(eng, max_requests=40):
    """Ask the game to quit so that NetHack writes its own records."""
    req = eng.req
    n = 0
    while req is not None and n < max_requests:
        n += 1
        try:
            if req.kind == 'cmd':
                eng.key('#')
            elif req.kind == 'ext':
                eng.ext('quit')
            elif req.kind == 'yn':
                q = (req.query or '').lower()
                # only confirm quitting; "Dump core?" (wizard mode) must be
                # refused or the engine aborts without writing its records
                eng.yn('y' if ('quit' in q or 'die?' in q) else 'n')
            elif req.kind in ('cmdcont', 'key'):
                eng.key(27)
            else:
                eng.escape()
            req = eng.next_request()
        except EngineEOF:
            return True
    return req is None


def classify(abort, verdict, xlog, rc, crash, watchdog):
    """Returns (outcome, reason)."""
    if crash is not None:
        return 'crash_bot', crash
    if watchdog:
        return 'stuck', watchdog
    if abort is not None:
        cat, reason = abort
        if cat == 'goal':
            return 'goal_reached', reason
        return cat, reason
    if verdict is not None:
        how = verdict.get('how_s')
        if how == 'ascended':
            xl_ok = any(r.get('death') == 'ascended' for r in xlog)
            if xl_ok:
                return 'ascended', 'engine verdict and xlogfile agree'
            return 'unknown', 'engine says ascended but xlogfile disagrees'
        if how in ('died', 'choked', 'poisoned', 'starved', 'drowned',
                   'burned', 'dissolved', 'crushed', 'stoned', 'slimed',
                   'genocided'):
            return 'died', "%s: %s" % (how, verdict.get('killer'))
        if how == 'quit':
            return 'quit', 'the bot quit the game'
        if how == 'escaped':
            return 'escaped', verdict.get('killer')
        if how in ('panicked', 'tricked'):
            return 'crash_engine', "%s: %s" % (how, verdict.get('killer'))
        return 'unknown', 'verdict %r' % how
    return 'crash_engine', 'engine exited without a verdict (rc=%s)' % rc


def run_game(args):
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    import faulthandler
    import signal
    _stackf = open(os.path.join(out, 'stacks.txt'), 'a')
    faulthandler.register(signal.SIGUSR1, file=_stackf, all_threads=True)
    seed = args.seed if args.seed is not None else random.randrange(1, 2**31)
    bot_seed = args.bot_seed if args.bot_seed is not None else seed

    logf = os.path.join(out, 'bot.log')
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
    handler = logging.FileHandler(logf, mode='w')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'))
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, args.log.upper()))

    limits = dict(DEFAULT_LIMITS)
    for k in DEFAULT_LIMITS:
        v = getattr(args, k, None)
        if v is not None:
            limits[k] = v
    assists = assists_env(args)
    kit_lines = None
    if 'NH_ASSIST_KIT' in assists:
        with open(assists['NH_ASSIST_KIT']) as f:
            kit_lines = [l.rstrip('\n') for l in f
                         if l.strip() and not l.startswith('#')]
    manifest = {
        'game_id': args.game_id or os.path.basename(out),
        'series': args.series,
        'started': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'host': socket.gethostname(),
        'python': platform.python_version(),
        'engine': {'nethack': '3.6.7', 'windowport': 'bot', 'proto': 1},
        'code': code_hashes(),
        'engine_seed': seed,
        'bot_seed': bot_seed,
        'character': 'val-dwa-fem-law',
        'assists': {'invincible': bool(args.invincible),
                    'nostarve': bool(args.nostarve),
                    'kit': kit_lines},
        'wizard': bool(args.wizard),
        'scenario': args.scenario,
        'goal': args.goal,
        'bot_profile': args.profile,
        'bot_tactics': args.tactics,
        'bot_skip': os.environ.get('BOTHACK_SKIP', ''),
        'limits': limits,
        'counted_as_full_game': not args.wizard and not args.scenario,
    }
    with open(os.path.join(out, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=1)

    from pybothack.bh36 import new_bh36
    from pybothack.delegator import Handler
    from pybothack.handlers import register_handler
    from pybothack.nhbridge import Bridge, BridgeAbort
    from pybothack.util import PRIORITY_TOP

    rec = Recorder(out, ring=args.ring, full_trace=args.trace)
    # kill -USR2 <pid>: write the ring buffer now (live debugging)
    signal.signal(signal.SIGUSR2, lambda *_a: rec.dump_ring(
        os.path.join(out, 'last_steps.live.jsonl')))
    eng = Engine(out, seed=seed, wizard=args.wizard, assists=assists,
                 name=args.name,
                 trace=(open(os.path.join(out, 'protocol.trace'), 'w')
                        if args.protocol_trace else None))
    t0 = time.time()
    eng.start()
    bh = new_bh36({'bot': 'mainbot'}, rng=random.Random(bot_seed))
    bridge = Bridge(bh, eng, rec, nickname=args.name.capitalize())
    register_handler(bh, PRIORITY_TOP - 1,
                     Handler(action_chosen=bridge.on_action))
    sup = Supervisor(rec, eng, limits=limits, goal=args.goal)

    def _terminated(signum, _frame):
        # an operator/harness stop is a resource limit, not a bot crash;
        # also flagged for the supervisor in case a BotHack handler catches
        # the exception (it did: the game went on after SIGTERM)
        sup.terminated = 'terminated by signal %d' % signum
        raise BridgeAbort('limit', sup.terminated)
    signal.signal(signal.SIGTERM, _terminated)

    abort = None
    crash = None
    try:
        if args.scenario:
            from nhbot import scenarios
            scen = scenarios.setup(args.scenario, eng, rec)
            if scen.get('goal') and not args.goal:
                sup.goal = scen['goal']
        bridge.run(sup)
    except BridgeAbort as e:
        abort = (e.category, e.reason)
        rec.note('abort', "%s: %s" % (e.category, e.reason))
    except EngineEOF:
        pass
    except Exception:
        crash = traceback.format_exc()
        rec.note('crash', crash[-2000:])
        logging.getLogger('nhbot').error("bot crash:\n%s", crash)
    finally:
        sup.stop()

    if eng.req is not None and eng.returncode is None:
        try:
            graceful_quit(eng)
        except Exception:
            pass
    eng.stop()
    elapsed = time.time() - t0
    xlog = read_xlogfile(out)
    outcome, reason = classify(abort, eng.verdict, xlog, eng.returncode,
                               crash, sup.watchdog_fired)
    st = eng.status
    screen = bridge.frame.lines if bridge.frame is not None else None
    result = {
        'game_id': manifest['game_id'],
        'outcome': outcome,
        'reason': reason,
        'assisted': any(manifest['assists'].values()),
        'engine_verdict': eng.verdict,
        'xlogfile': xlog[-1] if xlog else None,
        'engine_rc': eng.returncode,
        'engine_seed': seed,
        'turns': st.get('turn'),
        'depth': st.get('depth'),
        'max_depth': rec.max_depth,
        'xl': st.get('xl'),
        'lvl': (st.get('lvl') or '').strip(),
        'dname': st.get('dname'),
        'stages': rec.reached,
        'last_stage': (max(rec.reached, key=lambda s: rec.reached[s])
                       if rec.reached else None),
        'assist_counts': _assist_counts(eng.assist_events),
        'counters': dict(bridge.counters),
        'notes': dict(rec.counters),
        'protoerrs': len(eng.protoerrs),
        'requests': eng.nreq,
        'actions': rec.nact,
        'action_hist': dict(rec.action_hist.most_common(25)),
        'elapsed_s': round(elapsed, 1),
        'turns_per_s': round((st.get('turn') or 0) / elapsed, 2)
        if elapsed else None,
        'last_action': rec.last_action_desc,
        'final_screen': screen,
    }
    if outcome == 'ascended':
        rec.stage('ascended')
        result['stages'] = dict(rec.reached)
        result['last_stage'] = 'ascended'
    rec.milestone('end', outcome=outcome, reason=reason)
    rec.dump_ring()
    rec.close()
    with open(os.path.join(out, 'result.json'), 'w') as f:
        json.dump(result, f, indent=1)
    if not args.keep_levels:
        cleanup_level_files(out)
    return result


def _assist_counts(events):
    c = {}
    for e in events:
        c[e.get('kind')] = c.get(e.get('kind'), 0) + 1
    return c


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--out', required=True)
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--bot-seed', type=int, default=None)
    ap.add_argument('--game-id', default=None)
    ap.add_argument('--series', default=None)
    ap.add_argument('--name', default='bot')
    ap.add_argument('--no-invincible', dest='invincible',
                    action='store_false')
    ap.add_argument('--no-nostarve', dest='nostarve', action='store_false')
    ap.add_argument('--kit', default=DEFAULT_KIT,
                    help="kit file, or 'none'")
    ap.add_argument('--no-assist', action='store_true',
                    help="disable every assist (invincible, nostarve, kit)")
    ap.add_argument('--profile', default='full', choices=('full', 'fast'),
                    help="BotHack progression: full (original) or fast "
                         "(no Mines/Sokoban detours, no backtracking)")
    ap.add_argument('--tactics', default=None,
                    choices=('assisted', 'normal'),
                    help="assisted: no retreat/rest (default when "
                         "invincible); normal: BotHack survival tactics")
    ap.add_argument('--goal', default=None,
                    help="stop successfully at this stage (e.g. minetown)")
    ap.add_argument('--wizard', action='store_true',
                    help="wizard mode (scenarios only; never counted)")
    ap.add_argument('--scenario', default=None)
    for k, v in DEFAULT_LIMITS.items():
        ap.add_argument('--' + k.replace('_', '-'), dest=k,
                        type=type(v), default=None)
    ap.add_argument('--ring', type=int, default=800)
    ap.add_argument('--trace', action='store_true',
                    help="write every observation/answer to trace.jsonl")
    ap.add_argument('--protocol-trace', action='store_true')
    ap.add_argument('--keep-levels', action='store_true')
    ap.add_argument('--log', default='WARNING')
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.scenario:
        args.wizard = True
        from nhbot import scenarios
        scen = scenarios.load(args.scenario)
        if args.max_turns is None and scen.get('max_turns'):
            args.max_turns = scen['max_turns']
        if scen.get('profile') and args.profile == 'full':
            args.profile = scen['profile']
        if scen.get('skip'):
            os.environ['BOTHACK_SKIP'] = ",".join(scen['skip'])
    if args.no_assist:
        args.invincible = False
        args.nostarve = False
        args.kit = 'none'
    os.environ['BOTHACK_PROFILE'] = args.profile
    if args.tactics is None:
        args.tactics = 'assisted' if args.invincible else 'normal'
    os.environ['BOTHACK_TACTICS'] = args.tactics
    res = run_game(args)
    summary = {k: res[k] for k in ('outcome', 'reason', 'turns', 'lvl',
                                   'max_depth', 'xl', 'last_stage',
                                   'assist_counts', 'elapsed_s',
                                   'turns_per_s')}
    print(json.dumps(summary))
    return 0


if __name__ == '__main__':
    sys.exit(main())
