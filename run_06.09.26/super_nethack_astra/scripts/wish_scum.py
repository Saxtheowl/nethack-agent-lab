#!/usr/bin/env python3
"""wish_abuser start-scum loop (runs ON miniforum-worker, never save-scum).

Each worker thread chains new games (lawful female dwarven Valkyrie, same
options as the local slots) and looks at the FIRST ROOM only:
  - a fountain '{'  -> travel to it and quaff until it dries up; a water demon
    grants a wish ~19% of the time on Dlvl 1 (fountain.c dowaterdemon:
    rnd(100) > 80 + level_difficulty()), i.e. ~0.6% per quaff (fate 23/30);
  - a "lamp" '('    -> oil lamp (prob 45) or magic lamp (prob 15): hand over.
Nothing interesting / hostile demon / snakes / nymph / fountain dried up ->
#quit and start again. The loop NEVER answers the wish prompt and never uses
a lamp: as soon as one is found the game is left running in its tmux session
(socket /tmp/wishscum.sock, session wishK) and an LLM agent takes over through
`ssh -t miniforum-worker tmux -S /tmp/wishscum.sock attach -t wishK`.

  python3 scripts/wish_scum.py [--workers 3] [--max 2000] [--want 1]

Writes runs/wish_scum/attempts.jsonl (one line per game) and
runs/wish_scum/status.json (counters, found games) for the dashboard.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from terminal import text_runs  # noqa: E402

NETHACK = ROOT / 'engine/install/games/lib/nethackdir/nethack'
SAVEDIR = ROOT / 'engine/install/games/lib/nethackdir/save'
OUT = Path(os.environ.get('WISH_OUT', ROOT / 'runs/wish_scum'))
SOCK = '/tmp/wishscum.sock'
COLS, ROWS = 144, 36
MAP_ROWS = range(10, 31)
OBJ_CHARS = set(')[%?!/="*($')
lock = threading.Lock()
status = {'started': time.time(), 'attempts': 0, 'fountains': 0, 'quaffs': 0, 'lamps': 0,
          'demons_hostile': 0, 'deaths': 0, 'outcomes': {}, 'found': [], 'running': True, 'workers': {}}


def tmux(*args, check=False):
    return subprocess.run(['tmux', '-S', SOCK, *args], text=True, capture_output=True, check=check)


def screen(s):
    out = tmux('capture-pane', '-p', '-e', '-t', f'{s}:0.0').stdout
    return ''.join(r['text'] for r in text_runs(out)).split('\n')


def dead(s):
    r = tmux('display-message', '-p', '-t', f'{s}:0.0', '#{pane_dead}')
    return r.returncode != 0 or r.stdout.strip() == '1'


def keys(s, *ks, literal=True, pause=0.25):
    for k in ks:
        if literal:
            # a lone ';' is tmux's command separator: escape it
            tmux('send-keys', '-t', f'{s}:0.0', '-l', '\\;' if k == ';' else k)
        else:
            tmux('send-keys', '-t', f'{s}:0.0', k)
        time.sleep(pause)


def msgs(lines):
    return [l[1:81].strip() for l in lines[1:9] if l[1:81].strip()]


def settle(s, log, limit=25):
    """Dismiss --More-- / menus; collect every message seen. Returns lines."""
    lines = screen(s)
    for _ in range(limit):
        text = '\n'.join(lines)
        log.extend(m for m in msgs(lines) if m not in log[-12:])
        if 'For what do you wish?' in text:
            return lines
        if '--More--' in text or '(end)' in text or re.search(r'\(\d+ of \d+\)', text):
            keys(s, 'Enter', literal=False)
            lines = screen(s)
            continue
        return lines
    return lines


def write_status():
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / 'status.json.tmp'
    tmp.write_text(json.dumps(status, ensure_ascii=False))
    tmp.replace(OUT / 'status.json')


def record(entry):
    with lock:
        status['attempts'] += 1
        status['outcomes'][entry['outcome']] = status['outcomes'].get(entry['outcome'], 0) + 1
        for k in ('fountains', 'quaffs', 'lamps'):
            status[k] += entry.get(k, 0)
        status['demons_hostile'] += entry['outcome'] == 'hostile water demon'
        status['deaths'] += entry['outcome'].startswith('died')
        with open(OUT / 'attempts.jsonl', 'a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        write_status()


def end_game(s):
    """#quit (or finish a death) until the pane is gone."""
    if not dead(s):
        keys(s, 'Escape', 'Escape', literal=False)
        keys(s, '#quit')
        keys(s, 'Enter', literal=False)
        keys(s, 'y')
    for _ in range(40):
        if dead(s):
            break
        text = '\n'.join(screen(s))
        if 'Really quit' in text:
            keys(s, 'y')
        elif '[ynq]' in text or 'identified' in text:
            keys(s, 'q')
        else:
            keys(s, 'Enter', literal=False)
    tmux('kill-session', '-t', s)


def status_line(lines):
    for l in lines:
        m = re.search(r'Dlvl:(\d+).*HP:(\d+)\((\d+)\).*T:(\d+)', l)
        if m:
            return tuple(map(int, m.groups()))
    return None


def attempt(k, player):
    s = f'wish{k}'
    if tmux('has-session', '-t', s).returncode == 0:
        end_game(s)  # leftover game (driver restarted): quit it properly, never a hangup save
    cmd = f'env NETHACKOPTIONS=@{ROOT / "config/nethackrc"} TERM=screen-256color {NETHACK} -u {player}'
    tmux('-f', str(ROOT / 'config/tmux.conf'), 'new-session', '-d', '-s', s, '-x', str(COLS), '-y', str(ROWS), cmd, check=True)
    log, entry = [], {'t': round(time.time()), 'worker': k, 'player': player, 'fountains': 0, 'quaffs': 0, 'lamps': 0}
    lines = None
    for _ in range(40):
        time.sleep(0.25)
        lines = screen(s)
        text = '\n'.join(lines)
        if 'Destroy old game' in text or 'already a game in progress' in text:
            keys(s, 'y')
        elif '--More--' in text:
            keys(s, 'Enter', literal=False)
        elif status_line(lines):
            break
    if not lines or not status_line(lines):
        entry['outcome'] = 'start failed'
        end_game(s)
        return entry
    maprows = [lines[y][1:81] for y in MAP_ROWS]
    has_fountain = any('{' in r for r in maprows)
    has_tool = any('(' in r for r in maprows)
    # 1. lamps in the first room: farlook every object (nearest first)
    if has_tool:
        nobj = min(10, sum(sum(c in OBJ_CHARS for c in r) for r in maprows))
        for n in range(1, nobj + 1):
            before = set(msgs(screen(s)))
            keys(s, ';', *(['o'] * n), '.', pause=0.12)
            lines = settle(s, log)
            new = [m for m in msgs(lines) if m not in before]
            entry.setdefault('looked', []).extend(new[:1])
            # farlook ends with the object's name in parentheses: "(... ) (a lamp)"
            names = [re.findall(r'\(([^()]*)\)\s*$', m) for m in new]
            if any(n and re.search(r'\blamps?\b', n[-1]) for n in names):
                entry.update(lamps=1, outcome='lamp found', messages=new[-3:])
                return entry
    # 2. fountain: travel onto it, then quaff until something happens
    if has_fountain:
        entry['fountains'] = 1
        on = False
        for _ in range(6):
            keys(s, '_', pause=0.3)
            keys(s, '{', '.', pause=0.3)
            settle(s, log)
            keys(s, ':')
            lines = settle(s, log)
            if any('fountain here' in m for m in msgs(lines)):
                on = True
                break
            keys(s, 'Escape', literal=False)
        if not on:
            entry['outcome'] = 'fountain unreachable'
            end_game(s)
            return entry
        for q in range(40):
            before = set(msgs(screen(s)))
            keys(s, 'q', pause=0.3)
            text = '\n'.join(screen(s))
            if 'Drink from the fountain' not in text:
                keys(s, 'Escape', literal=False)
                entry['outcome'] = 'fountain gone'
                break
            keys(s, 'y', pause=0.4)
            entry['quaffs'] += 1
            seen = []
            lines = settle(s, seen)
            new = [m for m in seen if m not in before]
            log.extend(new)
            text = '\n'.join(lines)
            if 'For what do you wish?' in text or any('grants you a wish' in m for m in new):
                entry.update(outcome='WISH', messages=new[-4:])
                return entry
            if any('You die' in m for m in new) or dead(s):
                entry['outcome'] = 'died (quaff)'
                break
            if any('unleash' in m or 'presence of evil' in m for m in new):
                entry['outcome'] = 'hostile water demon'
                break
            if any('stream of snakes' in m for m in new):
                entry['outcome'] = 'water moccasins'
                break
            if any('water nymph' in m for m in new):
                entry['outcome'] = 'water nymph'
                break
            if any('dries up' in m for m in new):
                entry['outcome'] = 'fountain dried up'
                break
        else:
            entry['outcome'] = 'quaff limit'
        entry['messages'] = log[-4:]
        end_game(s)
        return entry
    entry['outcome'] = 'nothing (no fountain, no lamp)' if not has_tool else 'no lamp'
    end_game(s)
    return entry


def worker(k, max_attempts, want):
    player = f'Wish{k}'
    with lock:
        kept = any(f['session'] == f'wish{k}' for f in status['found'])
    if kept and tmux('has-session', '-t', f'wish{k}').returncode == 0:
        with lock:
            status['workers'][str(k)] = f'found game kept in wish{k}: not scumming'
            write_status()
        return
    while True:
        with lock:
            if not status['running'] or status['attempts'] >= max_attempts or len(status['found']) >= want:
                status['workers'][str(k)] = 'stopped'
                write_status()
                return
            status['workers'][str(k)] = 'scumming'
        if any(SAVEDIR.glob(f'*{player}*')):
            with lock:
                status['workers'][str(k)] = f'save file for {player} exists: stopped'
                write_status()
            return
        try:
            e = attempt(k, player)
        except Exception as ex:  # keep the loop alive, log the error
            e = {'t': round(time.time()), 'worker': k, 'player': player, 'outcome': f'error: {ex}'[:120]}
            tmux('kill-session', '-t', f'wish{k}')
        record(e)
        if e['outcome'] in ('WISH', 'lamp found'):
            with lock:
                status['found'].append({'t': e['t'], 'worker': k, 'player': player, 'session': f'wish{k}',
                                        'kind': e['outcome'], 'attempt': status['attempts'], 'messages': e.get('messages', [])})
                status['workers'][str(k)] = f'FOUND {e["outcome"]}: game kept in tmux session wish{k}'
                if len(status['found']) >= want:
                    status['running'] = False  # enough games found: stop the others
                write_status()
            return


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--workers', type=int, default=3)
    p.add_argument('--max', type=int, default=2000)
    p.add_argument('--want', type=int, default=1, help='number of found games to keep (one per wish_abuser slot)')
    a = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    try:  # continue the counters of an earlier run
        old = json.loads((OUT / 'status.json').read_text())
        for k in ('attempts', 'fountains', 'quaffs', 'lamps', 'demons_hostile', 'deaths', 'outcomes', 'found'):
            status[k] = old.get(k, status[k])
        status['started'] = old.get('started', status['started'])
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    status['running'] = True
    status['want'] = a.want
    write_status()
    ts = [threading.Thread(target=worker, args=(k, a.max, a.want)) for k in range(1, a.workers + 1)]
    for t in ts:
        t.start()
        time.sleep(0.5)
    for t in ts:
        t.join()
    status['running'] = False
    status['ended'] = time.time()
    write_status()


if __name__ == '__main__':
    main()
