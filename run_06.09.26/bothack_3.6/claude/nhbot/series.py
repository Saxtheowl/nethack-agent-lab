"""Run a series of games locally, keep every result, summarize.

    python3 -m nhbot.series --name s001 --games 8 --jobs 2
    python3 -m nhbot.series --name mt01 --games 20 --jobs 3 --goal minetown \\
        --max-turns 30000
    python3 -m nhbot.series --name s002 --seeds 11,12,13 -- --no-assist

Every game is a separate `python3 -m nhbot.rungame` process (a bot crash or a
hung engine never takes the series down).  Arguments after `--` are passed to
rungame unchanged.

Early stop: when `--stop-on-repeat N` games (default 3) end with the same
failure signature (outcome + reason with numbers/names stripped), no new game
is started - fix the bug first instead of reproducing it.

Output: runs/<name>/series.json (manifest), runs/<name>/summary.json and
summary.txt, runs/<name>/gNNN/ per game.
"""
import argparse
import collections
import json
import os
import random
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from nhbot.recorder import STAGES  # noqa: E402

FAILURES = ('died', 'stuck', 'crash_bot', 'crash_engine', 'unknown', 'quit',
            'escaped')


def signature(res):
    reason = res.get('reason') or ''
    reason = reason.strip().splitlines()[-1] if reason.strip() else ''
    reason = re.sub(r"\d+", "N", reason)
    reason = re.sub(r"'[^']*'|\"[^\"]*\"", "S", reason)
    reason = re.sub(r"\{.*\}", "{..}", reason)
    return "%s | %s" % (res.get('outcome'), reason[:120])


def run_one(args, gid, seed, extra):
    out = os.path.join(args.outdir, gid)
    cmd = [sys.executable, '-m', 'nhbot.rungame', '--out', out,
           '--seed', str(seed), '--game-id', gid, '--series', args.name]
    if args.goal:
        cmd += ['--goal', args.goal]
    if args.max_turns:
        cmd += ['--max-turns', str(args.max_turns)]
    if args.max_seconds:
        cmd += ['--max-seconds', str(args.max_seconds)]
    cmd += extra
    os.makedirs(out, exist_ok=True)
    logf = open(os.path.join(out, 'runner.out'), 'w')
    p = subprocess.Popen(cmd, cwd=ROOT, stdout=logf, stderr=subprocess.STDOUT,
                         start_new_session=True)
    return p, logf, out, time.time()


def harness_result(out, gid, seed, outcome, reason):
    res = {'game_id': gid, 'engine_seed': seed, 'outcome': outcome,
           'reason': reason, 'stages': {}, 'harness_generated': True}
    with open(os.path.join(out, 'result.json'), 'w') as f:
        json.dump(res, f, indent=1)
    return res


def summarize(args, results, stopped_reason=None):
    outcomes = collections.Counter(r.get('outcome') for r in results)
    sigs = collections.Counter(signature(r) for r in results
                               if r.get('outcome') not in ('ascended',
                                                           'goal_reached'))
    funnel = collections.OrderedDict()
    for s in STAGES:
        n = sum(1 for r in results if s in (r.get('stages') or {}))
        if n:
            funnel[s] = n
    anomalies = collections.Counter()
    assists = collections.Counter()
    for r in results:
        for k, v in (r.get('counters') or {}).items():
            anomalies[k] += v
        for k, v in (r.get('notes') or {}).items():
            anomalies['note:' + k] += v
        for k, v in (r.get('assist_counts') or {}).items():
            assists[k] += v
    turns = [r.get('turns') or 0 for r in results]
    elapsed = [r.get('elapsed_s') or 0 for r in results]
    summary = {
        'series': args.name,
        'games': len(results),
        'outcomes': dict(outcomes),
        'stage_funnel': funnel,
        'failure_signatures': sigs.most_common(15),
        'anomaly_totals': dict(anomalies.most_common(40)),
        'assist_totals': dict(assists),
        'turns_total': sum(turns),
        'turns_max': max(turns) if turns else 0,
        'elapsed_total_s': round(sum(elapsed), 1),
        'stopped_early': stopped_reason,
        'games_detail': [
            {k: r.get(k) for k in ('game_id', 'engine_seed', 'outcome',
                                   'reason', 'turns', 'max_depth',
                                   'last_stage', 'elapsed_s', 'turns_per_s',
                                   'assist_counts')}
            for r in results],
    }
    for g in summary['games_detail']:
        if g.get('reason'):
            g['reason'] = g['reason'].strip().splitlines()[-1][:200]
    with open(os.path.join(args.outdir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=1)
    lines = ["series %s: %d games" % (args.name, len(results)),
             "outcomes: %s" % dict(outcomes),
             "stage funnel: %s" % ", ".join("%s=%d" % kv
                                            for kv in funnel.items()),
             "assists: %s" % dict(assists)]
    if stopped_reason:
        lines.append("STOPPED EARLY: %s" % stopped_reason)
    lines.append("failure signatures:")
    for s, n in sigs.most_common(15):
        lines.append("  %3d  %s" % (n, s))
    lines.append("top anomalies:")
    for k, v in anomalies.most_common(15):
        lines.append("  %6d  %s" % (v, k))
    lines.append("games:")
    for g in summary['games_detail']:
        lines.append("  %s seed=%s %-12s T=%-6s depth=%-3s stage=%-12s "
                     "%ss  %s" % (g['game_id'], g['engine_seed'],
                                  g['outcome'], g['turns'], g['max_depth'],
                                  g['last_stage'], g['elapsed_s'],
                                  (g.get('reason') or '')[:90]))
    txt = "\n".join(lines)
    with open(os.path.join(args.outdir, 'summary.txt'), 'w') as f:
        f.write(txt + "\n")
    return txt


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    extra = []
    if '--' in argv:
        i = argv.index('--')
        argv, extra = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--name', required=True)
    ap.add_argument('--games', type=int, default=4)
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--seeds', default=None,
                    help="comma separated engine seeds (default: random)")
    ap.add_argument('--seed-base', type=int, default=None,
                    help="seeds seed_base+1 .. seed_base+games")
    ap.add_argument('--goal', default=None)
    ap.add_argument('--max-turns', type=int, default=None)
    ap.add_argument('--max-seconds', type=int, default=None)
    ap.add_argument('--stop-on-repeat', type=int, default=3)
    ap.add_argument('--runs-dir', default=os.path.join(ROOT, 'runs'))
    args = ap.parse_args(argv)
    args.outdir = os.path.join(args.runs_dir, args.name)
    os.makedirs(args.outdir, exist_ok=True)

    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(',')]
    elif args.seed_base is not None:
        seeds = [args.seed_base + i + 1 for i in range(args.games)]
    else:
        rng = random.Random()
        seeds = [rng.randrange(1, 2**31) for _ in range(args.games)]
    with open(os.path.join(args.outdir, 'series.json'), 'w') as f:
        json.dump({'name': args.name, 'seeds': seeds, 'jobs': args.jobs,
                   'goal': args.goal, 'max_turns': args.max_turns,
                   'max_seconds': args.max_seconds, 'rungame_extra': extra,
                   'started': time.strftime('%Y-%m-%dT%H:%M:%S%z')},
                  f, indent=1)

    pending = list(enumerate(seeds))
    running = []
    results = []
    sig_count = collections.Counter()
    stopped = None
    hard_limit = (args.max_seconds or 12 * 3600) + 600
    while pending or running:
        while pending and len(running) < args.jobs and not stopped:
            i, seed = pending.pop(0)
            gid = "g%03d" % (i + 1)
            p, logf, out, t0 = run_one(args, gid, seed, extra)
            running.append((p, logf, out, t0, gid, seed))
            print("[%s] start %s seed=%d" % (time.strftime('%H:%M:%S'), gid,
                                              seed), flush=True)
        if stopped and not running:
            break
        time.sleep(1.0)
        for item in list(running):
            p, logf, out, t0, gid, seed = item
            rc = p.poll()
            if rc is None and time.time() - t0 > hard_limit:
                p.kill()
                p.wait()
                rc = 'killed'
            if rc is None:
                continue
            running.remove(item)
            logf.close()
            rpath = os.path.join(out, 'result.json')
            if os.path.exists(rpath):
                with open(rpath) as f:
                    res = json.load(f)
            elif rc == 'killed':
                res = harness_result(out, gid, seed, 'limit',
                                     'harness wall-clock kill')
            else:
                res = harness_result(out, gid, seed, 'crash_bot',
                                     'rungame exited rc=%s without result'
                                     % rc)
            results.append(res)
            sig = signature(res)
            print("[%s] end   %s %s T=%s depth=%s stage=%s (%s)"
                  % (time.strftime('%H:%M:%S'), gid, res.get('outcome'),
                     res.get('turns'), res.get('max_depth'),
                     res.get('last_stage'), sig), flush=True)
            if res.get('outcome') in FAILURES:
                sig_count[sig] += 1
                if (args.stop_on_repeat
                        and sig_count[sig] >= args.stop_on_repeat
                        and not stopped):
                    stopped = ("signature repeated %d times: %s"
                               % (sig_count[sig], sig))
                    print("[series] %s -- not starting new games" % stopped,
                          flush=True)
    results.sort(key=lambda r: r.get('game_id') or '')
    print(summarize(args, results, stopped))
    return 0


if __name__ == '__main__':
    sys.exit(main())
