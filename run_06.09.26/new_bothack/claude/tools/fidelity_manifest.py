#!/usr/bin/env python3
"""Aggregate a fidelity batch into one manifest, and print the table.

Two verdicts per seed, kept separate on purpose:

  recording  GAME / TRUNCATED / INVALID_TRACE - what the *original* produced.
             A TRUNCATED capture is a prefix of a game; no amount of fidelity
             can make it PASS_COMPLETE.
  replay     the port's verdict against that capture (tools/verdict.py).

so the headline is `PASS_COMPLETE / recordings that are GAMEs`, and the truncated
recordings are listed rather than silently diluting either side.

The manifest also records everything needed to say *what* was verified, because
"100 %" only means something against a named corpus under named conditions: the
port commit, the pinned BotHack commit, checksums of the NetHack binary and the
RNG shim, tool versions, the PTY parameters, the two seeds, the caps, the initial
state of the shared `var/`, and a checksum of every capture.  A new port commit
invalidates the previous *replay* verdict for that commit until it is replayed;
it does not invalidate the capture.

    tools/fidelity_manifest.py OUT [--bothack-src DIR]
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import verdict as V                                 # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(*cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL,
                                       cwd=ROOT).decode().strip()
    except (subprocess.CalledProcessError, OSError):
        return None


def sha256(path, limit=None):
    """Checksum a file; `limit` caps how much is read for very large captures."""
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    read = 0
    with open(path, 'rb') as fh:
        while True:
            chunk = fh.read(1 << 20)
            if not chunk:
                break
            if limit is not None and read + len(chunk) > limit:
                h.update(chunk[:limit - read])
                break
            h.update(chunk)
            read += len(chunk)
    return h.hexdigest()


def load(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (IOError, ValueError):
        return None


def pty_params(nh_sh):
    """The PTY and RNG settings the launcher baked in - part of the contract."""
    out = {}
    if not os.path.exists(nh_sh):
        return out
    for line in open(nh_sh, errors='replace'):
        m = re.match(r'export (PTY_TAP_\w+|NETHACK_FIXED_SEED|LD_PRELOAD|USER)'
                     r'="?([^"\n]*)"?', line.strip())
        if m:
            out[m.group(1)] = m.group(2)
    return out


def environment(bothack_src):
    """Everything outside the corpus that a verdict depends on."""
    nh = os.path.join(ROOT, 'upstream', 'nh343', 'nethack.343-nao')
    env = {
        'recorded_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'port_commit': sh('git', 'rev-parse', 'HEAD'),
        'port_dirty': bool(sh('git', 'status', '--porcelain', '--',
                              'pybothack', 'tools', 'tests')),
        'python': sys.version.split()[0],
        'nethack_binary_sha256': sha256(nh),
        'det_rng_so_sha256': sha256(os.path.join(ROOT, 'artifacts',
                                                 'det_rng.so')),
        'nethackrc_sha256': sha256(os.path.join(ROOT, 'upstream',
                                                'bothack.nethackrc')),
    }
    for name in ('pybothack', 'tools'):
        digests = []
        for dirpath, _d, files in os.walk(os.path.join(ROOT, name)):
            if '__pycache__' in dirpath:
                continue
            for fn in sorted(files):
                if fn.endswith(('.py', '.json', '.clj', '.sh', '.c')):
                    digests.append(sha256(os.path.join(dirpath, fn)))
        env['%s_tree_sha256' % name] = hashlib.sha256(
            ''.join(d for d in digests if d).encode()).hexdigest()
    if bothack_src:
        env['bothack_commit'] = sh('git', '-C', bothack_src, 'rev-parse',
                                   'HEAD')
        env['bothack_dirty'] = bool(sh('git', '-C', bothack_src, 'status',
                                       '--porcelain'))
    jdk = os.environ.get('JDK8_HOME')
    if jdk:
        env['jdk'] = sh(os.path.join(jdk, 'bin', 'java'), '-version') or None
    return env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--bothack-src', default=os.environ.get('BOTHACK_SRC'))
    a = ap.parse_args()
    out = a.out

    seeds = sorted(d for d in os.listdir(out)
                   if d.startswith('seed') and os.path.isdir(
                       os.path.join(out, d)))
    rows = []
    for name in seeds:
        d = os.path.join(out, name)
        rec = load(os.path.join(d, 'recording.json')) or {}
        rep = (load(os.path.join(d, 'replay', 'verdict.json'))
               or load(os.path.join(d, 'verdict.json')) or {})
        params = pty_params(os.path.join(d, 'nh.sh'))
        rows.append({
            'seed': name[4:],
            'player': rec.get('player') or params.get('USER'),
            'nethack_seed': params.get('NETHACK_FIXED_SEED'),
            'bot_seed': os.environ.get('BOTHACK_SEED', '12345'),
            'pty': {k: v for k, v in params.items()
                    if k.startswith('PTY_TAP_')},
            'recording': rec.get('status', 'MISSING'),
            'orig_keystrokes': rec.get('keystrokes'),
            'orig_output': rec.get('output'),
            'chunks': rec.get('chunks'),
            'end_marker': rec.get('end_marker'),
            'xlog': rec.get('xlog'),
            'tap_sha256': sha256(os.path.join(d, 'tap.log')),
            'tap_bytes': (os.path.getsize(os.path.join(d, 'tap.log'))
                          if os.path.exists(os.path.join(d, 'tap.log'))
                          else None),
            'replay': rep.get('status', 'MISSING'),
            'port_keystrokes': rep.get('got_bytes'),
            # `common_prefix` is min(len(expected), len(got)) - the length the
            # two streams *overlap*, not the length they agree over.  On a
            # DIVERGENCE the agreement stops at `first_divergence`, and using
            # common_prefix there silently reports a diverging run as 100 %
            # identical.
            'identical_prefix': (rep.get('first_divergence')
                                 if rep.get('first_divergence') is not None
                                 else rep.get('common_prefix')),
            'first_divergence': rep.get('first_divergence'),
        })

    games = [r for r in rows if r['recording'] == 'GAME']
    tot_o = sum(r['orig_keystrokes'] or 0 for r in rows)
    tot_id = sum(r['identical_prefix'] or 0 for r in rows)
    manifest = {
        'campaign': os.path.basename(os.path.abspath(out)),
        'dir': os.path.abspath(out),
        'environment': environment(a.bothack_src),
        'var_initial': sha256(os.path.join(out, 'var_initial.txt')),
        'seeds': len(rows),
        'recordings_that_are_games': len(games),
        'pass_complete': sum(1 for r in rows
                             if r['replay'] == V.PASS_COMPLETE),
        'passes': sum(1 for r in rows if r['replay'] in V.SUCCESS),
        'original_keystrokes_total': tot_o,
        'identical_keystrokes_total': tot_id,
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

    hdr = ('%-7s %-11s %-10s %-15s %-10s %s'
           % ('seed', 'recording', 'orig_keys', 'replay', 'identical',
              'first divergence'))
    print(hdr)
    print('-' * len(hdr))
    for r in rows:
        print('%-7s %-11s %-10s %-15s %-10s %s'
              % (r['seed'], r['recording'],
                 r['orig_keystrokes'] if r['orig_keystrokes'] is not None
                 else '-',
                 r['replay'],
                 r['identical_prefix'] if r['identical_prefix'] is not None
                 else '-',
                 r['first_divergence'] if r['first_divergence'] is not None
                 else '-'))
    print()
    print('recordings that are whole games: %d/%d' % (len(games), len(rows)))
    print('PASS_COMPLETE: %d of those %d' % (manifest['pass_complete'],
                                             len(games)))
    if tot_o:
        print('original keystrokes %d, identical %d (%.2f%%)'
              % (tot_o, tot_id, 100.0 * tot_id / tot_o))
    for s, n in sorted(manifest['by_replay_status'].items()):
        print('  %-15s %d' % (s, n))
    env = manifest['environment']
    print('port %s%s, nethack %s, det_rng %s'
          % ((env.get('port_commit') or '?')[:12],
             ' (dirty)' if env.get('port_dirty') else '',
             (env.get('nethack_binary_sha256') or '?')[:12],
             (env.get('det_rng_so_sha256') or '?')[:12]))
    print('manifest: %s' % os.path.join(out, 'manifest.json'))


if __name__ == '__main__':
    main()
