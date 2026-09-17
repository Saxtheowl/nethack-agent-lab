"""Explain what happened in a game or a series.

    python3 -m nhbot.analyze runs/dev/g011            # one game
    python3 -m nhbot.analyze runs/dev/g011 --steps 120
    python3 -m nhbot.analyze runs/s001                # a series
"""
import argparse
import collections
import json
import os
import sys


def load_jsonl(path):
    out = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        pass
    return out


def fmt_step(r):
    if 'r' in r:
        extra = r.get('q') or r.get('p') or r.get('g') or ''
        line = "#%-6s %-7s T=%-6s %-12s u=%-9s hp=%s/%s %s" % (
            r['r'], r['k'], r.get('T'), r.get('lvl'), tuple(r.get('u') or ()),
            r.get('hp'), r.get('hpmax'), extra)
        if r.get('c') is not None:
            line += " [%s]" % r['c']
        if r.get('items'):
            line += "\n          items: " + " | ".join(r['items'])
        return line
    if 'm' in r:
        return "        msg: %s" % r['m']
    if 'a' in r:
        return "        ans: %r" % (r['a'],)
    if 'act' in r:
        return "    ACTION %s %s %s" % (r['act'], r.get('dir') or r.get('slot')
                                        or r.get('pos') or '',
                                        "; ".join(r.get('why') or []))
    if 'note' in r:
        return "    NOTE %s: %s" % (r['note'], str(r.get('d'))[:200])
    return "    %s" % r


def game_report(gdir, steps):
    rp = os.path.join(gdir, 'result.json')
    if not os.path.exists(rp):
        print("no result.json (game running or harness killed)")
        res = {}
    else:
        with open(rp) as f:
            res = json.load(f)
    man = {}
    if os.path.exists(os.path.join(gdir, 'manifest.json')):
        with open(os.path.join(gdir, 'manifest.json')) as f:
            man = json.load(f)
    print("=== %s" % gdir)
    print("seed=%s assists=%s goal=%s code=%s" % (
        man.get('engine_seed'),
        {k: (v if not isinstance(v, list) else len(v))
         for k, v in (man.get('assists') or {}).items()},
        man.get('goal'), (man.get('code') or {}).get('bot_code_hash')))
    for k in ('outcome', 'reason', 'turns', 'lvl', 'dname', 'max_depth', 'xl',
              'stages', 'assist_counts', 'counters', 'notes', 'requests',
              'actions', 'elapsed_s', 'turns_per_s', 'last_action'):
        if k in res:
            v = res[k]
            if k == 'reason' and isinstance(v, str):
                v = v.strip()[-1500:]
            print("%-14s %s" % (k, v))
    if res.get('action_hist'):
        print("%-14s %s" % ('actions', res['action_hist']))
    prog = load_jsonl(os.path.join(gdir, 'progress.jsonl'))
    print("--- milestones")
    for m in prog:
        if m.get('kind') in ('heartbeat',):
            continue
        if m.get('kind') == 'assist' and m.get('x_kind') == 'kit':
            continue
        print("  T=%-6s %s" % (m.get('turn'), {k: v for k, v in m.items()
                                                if k not in ('turn',)}))
    ring = load_jsonl(os.path.join(gdir, 'last_steps.jsonl'))
    print("--- last %d steps" % min(steps, len(ring)))
    for r in (ring[-steps:] if steps > 0 else []):
        print(fmt_step(r))
    if res.get('final_screen'):
        print("--- final screen")
        print("\n".join(res['final_screen']))


def series_report(sdir):
    s = os.path.join(sdir, 'summary.txt')
    if os.path.exists(s):
        print(open(s).read())
        return
    results = []
    for g in sorted(os.listdir(sdir)):
        rp = os.path.join(sdir, g, 'result.json')
        if os.path.exists(rp):
            with open(rp) as f:
                results.append(json.load(f))
    c = collections.Counter(r.get('outcome') for r in results)
    print("%d finished games: %s" % (len(results), dict(c)))
    for r in results:
        print("  %s %s T=%s %s" % (r.get('game_id'), r.get('outcome'),
                                   r.get('turns'),
                                   (r.get('reason') or '').strip()[-100:]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('path')
    ap.add_argument('--steps', type=int, default=60)
    args = ap.parse_args(argv)
    if os.path.exists(os.path.join(args.path, 'series.json')):
        series_report(args.path)
    else:
        game_report(args.path, args.steps)
    return 0


if __name__ == '__main__':
    sys.exit(main())
