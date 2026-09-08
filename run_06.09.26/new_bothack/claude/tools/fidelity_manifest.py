#!/usr/bin/env python3
"""Aggregate a fidelity batch into one manifest, and print the table.

Two verdicts per seed, kept separate on purpose:

  recording  GAME / TRUNCATED / INVALID_TRACE - what the *original* produced.
             A TRUNCATED capture is a prefix of a game; no amount of fidelity
             can make it PASS_COMPLETE.
  replay     the port's verdict against that capture (tools/verdict.py).

so the headline number is `PASS_COMPLETE / recordings that are GAMEs`, and the
truncated recordings are listed rather than silently diluting either side.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import verdict as V                                 # noqa: E402


def git_head(root):
    try:
        return subprocess.check_output(
            ['git', '-C', root, 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL).decode().strip()
    except (subprocess.CalledProcessError, OSError):
        return None


def load(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (IOError, ValueError):
        return None


def main():
    out = sys.argv[1]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    seeds = sorted(d for d in os.listdir(out)
                   if d.startswith('seed') and os.path.isdir(
                       os.path.join(out, d)))
    rows = []
    for name in seeds:
        d = os.path.join(out, name)
        rec = load(os.path.join(d, 'recording.json')) or {}
        rep = load(os.path.join(d, 'replay', 'verdict.json')) or {}
        rows.append({
            'seed': name[4:],
            'recording': rec.get('status', 'MISSING'),
            'orig_keystrokes': rec.get('keystrokes'),
            'end_marker': rec.get('end_marker'),
            'xlog_turns': (rec.get('xlog') or {}).get('turns'),
            'xlog_points': (rec.get('xlog') or {}).get('points'),
            'replay': rep.get('status', 'MISSING'),
            'port_keystrokes': rep.get('got_bytes', rep.get('port_bytes')),
            'first_divergence': rep.get('first_divergence'),
            'similarity': rep.get('similarity'),
        })

    games = [r for r in rows if r['recording'] == 'GAME']
    passes = [r for r in games if r['replay'] in V.SUCCESS]
    manifest = {
        'dir': out,
        'port_commit': git_head(root),
        'seeds': len(rows),
        'recordings_that_are_games': len(games),
        'pass_complete': sum(1 for r in rows
                             if r['replay'] == V.PASS_COMPLETE),
        'passes': len(passes),
        'by_replay_status': {s: sum(1 for r in rows if r['replay'] == s)
                             for s in sorted({r['replay'] for r in rows})},
        'by_recording_status': {s: sum(1 for r in rows
                                       if r['recording'] == s)
                                for s in sorted({r['recording']
                                                 for r in rows})},
        'rows': rows,
    }
    with open(os.path.join(out, 'manifest.json'), 'w') as fh:
        fh.write(json.dumps(manifest, indent=1, sort_keys=True) + '\n')

    hdr = ('%-7s %-11s %-10s %-15s %-10s %-8s %s'
           % ('seed', 'recording', 'orig_keys', 'replay', 'port_keys',
              'sim', 'first divergence'))
    print(hdr)
    print('-' * len(hdr))
    for r in rows:
        print('%-7s %-11s %-10s %-15s %-10s %-8s %s'
              % (r['seed'], r['recording'],
                 r['orig_keystrokes'] if r['orig_keystrokes'] is not None
                 else '-',
                 r['replay'],
                 r['port_keystrokes'] if r['port_keystrokes'] is not None
                 else '-',
                 ('%.2f%%' % r['similarity']) if isinstance(
                     r['similarity'], float) else '-',
                 r['first_divergence'] if r['first_divergence'] is not None
                 else '-'))
    print()
    print('recordings that are whole games: %d/%d'
          % (len(games), len(rows)))
    print('PASS_COMPLETE: %d/%d of those'
          % (manifest['pass_complete'], len(games)))
    for s, n in sorted(manifest['by_replay_status'].items()):
        print('  %-15s %d' % (s, n))
    print('manifest: %s' % os.path.join(out, 'manifest.json'))


if __name__ == '__main__':
    main()
