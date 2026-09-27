#!/usr/bin/env python3
"""Persistent local NetHack 3.6.7 terminal and a read-only viewer; stdlib only.

Adapted from kenforthewin/nethack_astra (MIT): the game runs on this machine
under ttyrec inside tmux instead of over SSH to Hardfought.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
import uuid
import audit
import guard
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from terminal import text_runs

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.runtime'
SOCKET = '/tmp/nhstream-' + hashlib.sha256(str(ROOT).encode()).hexdigest()[:12] + '.sock'
# Several games can run side by side: NH_SLOT=1|2|3 selects the tmux session,
# the NetHack player name (hence its save file) and the per-slot runtime files.
SLOT = os.environ.get('NH_SLOT', '1')
SESSION = 'nethack' if SLOT == '1' else f'nethack{SLOT}'
TARGET = f'{SESSION}:0.0'
NETHACK = ROOT / 'engine/install/games/lib/nethackdir/nethack'
SAVEDIR = ROOT / 'engine/install/games/lib/nethackdir/save'
PLAYER = 'Claude' if SLOT == '1' else f'Claude{SLOT}'
SLOTFILE = RUNTIME / f'slot-{SLOT}.json'
# wish_abuser: the game found by scripts/wish_scum.py stays on miniforum-worker
# (its save file never moves, PURE rule); the local tmux session only attaches
# to the worker's tmux over ssh. The slot file then holds
# "remote": {"host", "sock", "session", "player"}.
try:
    _info = json.loads(SLOTFILE.read_text())
except (FileNotFoundError, json.JSONDecodeError):
    _info = {}
REMOTE = _info.get('remote')
# A slot can live in another tmux server/session (wish games on the worker:
# "tmux_sock": "/tmp/wishscum.sock", "tmux_session": "wishK").
SOCKET = _info.get('tmux_sock', SOCKET)
SESSION = _info.get('tmux_session', SESSION)
TARGET = f'{SESSION}:0.0'
TTYREC = shutil.which('ttyrec') or str(Path.home() / 'bin/ttyrec')


def slot_tmux(slot):
    """(tmux socket, session) of a slot's game on this machine."""
    try:
        info = json.loads((RUNTIME / f'slot-{slot}.json').read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        info = {}
    default = 'nethack' if slot == '1' else f'nethack{slot}'
    base = '/tmp/nhstream-' + hashlib.sha256(str(ROOT).encode()).hexdigest()[:12] + '.sock'
    return info.get('tmux_sock', base), info.get('tmux_session', default)


def slot_where(slot):
    """'worker' when the slot's game and tools live on miniforum-worker."""
    try:
        return (RUNTIME / f'where-{slot}').read_text().strip() or 'local'
    except FileNotFoundError:
        return 'local'


HOST = os.environ.get('NH_HOST', 'local')  # 'worker' for processes started on the worker
if REMOTE:
    PLAYER = REMOTE['player']


def remote_sh(command, timeout=20):
    return subprocess.run(['ssh', '-o', 'BatchMode=yes', REMOTE['host'], command], text=True,
                          capture_output=True, timeout=timeout)


def remote_saved(remote, player):
    r = subprocess.run(['ssh', '-o', 'BatchMode=yes', remote['host'],
                        f'ls {SAVEDIR}/ 2>/dev/null | grep -c -- "{player}"'], text=True, capture_output=True, timeout=20)
    return r.stdout.strip() not in ('', '0')
COLS, ROWS = 144, 36


def tmux(*args, check=True):
    return subprocess.run(['tmux', '-S', SOCKET, *args], text=True,
                          capture_output=True, check=check)


def alive():
    return tmux('has-session', '-t', SESSION, check=False).returncode == 0


def screen(ansi=False):
    if not alive():
        return 'No NetHack terminal running.'
    captured = tmux('capture-pane', '-p', '-e', '-t', TARGET).stdout
    return captured if ansi else ''.join(run['text'] for run in text_runs(captured))


def start():
    if alive():
        if tmux('display-message', '-p', '-t', TARGET, '#{pane_dead}').stdout.strip() != '1':
            print('Session already exists. Use screen or attach.')
            return
    # Every session is recorded by ttyrec (one file per start), like Hardfought.
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d.%H:%M:%S')
    record = ROOT / 'runs' / (f'{stamp}.ttyrec' if SLOT == '1' else f'{stamp}.slot{SLOT}.ttyrec')
    # A game id survives save/restore: a new id only when no save file exists.
    try:
        info = json.loads(SLOTFILE.read_text())
    except FileNotFoundError:
        info = {}
    if REMOTE:
        saved = remote_saved(REMOTE, PLAYER)
    else:
        saved = any(SAVEDIR.glob(f'*{PLAYER}.gz')) or any(SAVEDIR.glob(f'*{PLAYER}'))
    if REMOTE:  # the game id was set when the wish game was handed over
        saved = True
    if not saved or not info.get('game_id'):
        info = {'game_id': f'{PLAYER}-{stamp}', 'player': PLAYER, 'slot': SLOT, 'started': stamp}
        (RUNTIME / f'explore-{SLOT}.json').unlink(missing_ok=True)  # new game: no stale dead ends
    info.setdefault('ttyrecs', []).append(record.name)
    SLOTFILE.write_text(json.dumps(info))
    record.parent.mkdir(exist_ok=True)
    command = ['env', f'NETHACKOPTIONS=@{ROOT / "config/nethackrc"}', 'TERM=screen-256color',
               TTYREC, '-e', f'{NETHACK} -u {PLAYER}', str(record)]
    if REMOTE:
        sock, sess = REMOTE['sock'], REMOTE['session']
        game = (f'env NETHACKOPTIONS=@{ROOT / "config/nethackrc"} TERM=screen-256color {NETHACK} -u {PLAYER}')
        # (re)start the game on the worker if its tmux session is gone (after a save)
        remote_sh(f"tmux -S {sock} has-session -t {sess} 2>/dev/null || "
                  f"tmux -S {sock} -f {ROOT / 'config/tmux.conf'} new-session -d -s {sess} -x {COLS} -y {ROWS} '{game}'; "
                  f"tmux -S {sock} set-option -t {sess} remain-on-exit off")
        command = ['env', 'TERM=screen-256color', TTYREC, '-e',
                   f"ssh -t -o BatchMode=yes {REMOTE['host']} tmux -S {sock} attach -t {sess}", str(record)]
    if alive():
        tmux('respawn-pane', '-t', TARGET, *command)
    else:
        subprocess.run(['tmux', '-S', SOCKET, '-f', str(ROOT / 'config/tmux.conf'),
                        'new-session', '-d', '-s', SESSION, '-x', str(COLS), '-y', str(ROWS),
                        *command], check=True)
    tmux('resize-window', '-t', f'{SESSION}:0', '-x', str(COLS), '-y', str(ROWS))
    audit.record('session_started', {'ttyrec': record.name, 'game_id': info['game_id']})
    time.sleep(1)
    print(screen())


HPGUARD = RUNTIME / f'hpguard-{SLOT}.json'


class HPAlarm(SystemExit):
    pass


def hp_guard(text, value, named):
    """Harness-level HP alarm (user rule 2026-09-27, after 3 deaths in agents'
    own loops): once HP has fallen by a fifth of max below the last
    acknowledged level AND is under 60% of max, every key is refused (except
    Escape) until the agent re-reads the screen and runs `session.py ack-hp`.
    A loop that ignores errors can then no longer pass turns."""
    m = re.search(r'HP:(\d+)\((\d+)\)', text)
    if not m:
        return
    hp, mx = int(m[1]), int(m[2])
    try:
        st = json.loads(HPGUARD.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        st = {}
    base = st.get('base', hp)
    if st.get('max') != mx:  # new game / new max: reset the baseline
        base = max(hp, base) if st.get('max') else hp
    if hp > base:
        base = hp
    # a counted rest/search (n20s...) passes many turns in ONE command: nothing
    # can stop it in between, so it is refused when already hurt
    # (number_pad: counts need the n prefix; bare digits are moves, e.g. farlook cursor keys)
    if not named and re.match(r'^n\d+[s.]$', value or '') and hp < mx * 0.7:
        raise HPAlarm(f'Counted rest {value!r} refused at HP {hp}({mx}) (< 70%): a monster can hit you for '
                      'the whole count. Rest one turn at a time (s) with an HP check, or get safe first.')
    # Stoning / sliming: only curing actions may go through (eat a lizard or an
    # acidic corpse, pray, quaff, answer prompts). Slot 8 died exploring while Stone.
    lines = text.splitlines()
    status = ' '.join(lines[33:36]) if len(lines) > 35 else text[-400:]
    if re.search(r'\b(Stone|Slime)\b', status) and not named and (
            re.match(r'^(?:n?\d|[_FmMsGg]|[hjklyubnHJKLYUBN]$|\d)', value or '') and value not in ('y', 'n')):
        raise HPAlarm(f'Refused {value!r}: you are turning to STONE/SLIME. Cure it NOW: eat a lizard corpse '
                      '(e + letter), or an acidic corpse, or #pray, before anything else.')
    # several blind steps at low HP walked slot 2 into an Elvenking and a xorn
    if not named and re.fullmatch(r'[1-46-9]{3,}', value or '') and hp < mx * 0.5:
        raise HPAlarm(f'Refused {value!r}: {len(value)} steps in one go at HP {hp}({mx}) (< 50%). '
                      'Move one step at a time and re-read the screen after each.')
    tripped = st.get("tripped", False) or (hp <= base - mx / 5 and hp < mx * 0.6)
    HPGUARD.write_text(json.dumps({'base': base, 'max': mx, 'hp': hp, 'tripped': tripped}))
    if tripped and not (named and value == 'Escape'):
        raise HPAlarm(f'HP ALARM: HP {hp}({mx}) fell from {base}. Key {value!r} refused. '
                      'Stop every loop, read the screen, decide (pray if HP < 1/7 max, flee, heal), '
                      'then run: <slot>/session ack-hp   (then send your keys one by one).')


def ack_hp():
    text = screen()
    m = re.search(r'HP:(\d+)\((\d+)\)', text)
    if m:
        HPGUARD.write_text(json.dumps({'base': int(m[1]), 'max': int(m[2]), 'hp': int(m[1]), 'tripped': False}))
        print(f'HP alarm acknowledged at HP {m[1]}({m[2]}): keys allowed again.')


def send(value, named=False, sensitive=False, publish=True):
    if not alive() or tmux('display-message', '-p', '-t', TARGET, '#{pane_dead}').stdout.strip() == '1':
        raise RuntimeError('No live NetHack pane; inspect screen and restart.')
    audit.require_healthy()
    visible = (not (RUNTIME / 'broadcast.hidden').exists()) and not sensitive
    current = screen()
    hp_guard(current, value, named)
    # "Really attack the <peaceful>?" : a loop answering y killed a shopkeeper
    # (slot 3) and a priestess (slot 7). Only a deliberate --really may say yes.
    if not named and value in ('y', 'Y') and 'Really attack' in current and not os.environ.get('NH_REALLY'):
        cy = tmux('display-message', '-p', '-t', TARGET, '#{cursor_y}').stdout.strip()
        if cy.isdigit() and int(cy) < 9:
            raise HPAlarm('Refused: "Really attack?" is on screen (peaceful: shopkeeper, priest, watchman...). '
                          'Answer n (or Escape). To really attack, resend with: keys --really y')
    before = current if visible else '[hidden for privacy]'
    command_id = uuid.uuid4().hex
    turn = re.search(r'\bT:(\d+)', before)
    data = {'command_id': command_id, 'input': value if not sensitive else None,
            'named': named, 'sensitive': sensitive, 'screen_before': before,
            'game_turn': int(turn[1]) if turn else None, 'source': 'session.py'}
    audit.record('input_requested', data)  # durable intent BEFORE input reaches SSH
    try:
        # tmux parses a standalone semicolon as a command separator even when
        # passed as one argv element. Send its byte explicitly, not as syntax.
        if value == ';' and not named:
            tmux('send-keys', '-t', TARGET, '-H', '--', '3b')
        else:
            tmux('send-keys', '-t', TARGET, *([] if named else ['-l']), '--', value)
    except Exception:
        audit.record('input_failed', {'command_id': command_id})
        raise
    audit.record('input_queued', {'command_id': command_id})
    if visible and turn and publish:
        label = ('move ' + guard.NAMES[value]) if value in guard.NAMES else {
            '<': 'go upstairs', '>': 'go downstairs', 's': 'search', 'i': 'inspect inventory',
            'S': 'save game', ',': 'pick up', '.': 'wait'}.get(value, 'game input')
        audit.publish('command', value, label=label, named=named, game_turn=int(turn[1]), command_id=command_id)


def snapshot():
    hidden = not (not (RUNTIME / 'broadcast.hidden').exists())
    note = RUNTIME / f'commentary-{SLOT}.txt'
    runs = text_runs('Preparing the expedition.\nThe game will appear here shortly.' if hidden else screen(ansi=True))
    activity = audit.public_state()
    if hidden:
        activity['feed'] = []
    return {'screen': ''.join(run['text'] for run in runs), 'runs': runs, 'cols': COLS, 'rows': ROWS,
            'commentary': note.read_text() if note.exists() else 'Setting up camp at the dungeon entrance.',
            'visible': not hidden, 'updated': datetime.now(timezone.utc).isoformat(), **activity}


def print_screen(compact=False):
    current = screen()
    if (RUNTIME / 'audit-active.json').exists():
        audit.record('agent_observation', {'screen': current if (not (RUNTIME / 'broadcast.hidden').exists())
                     else '[hidden for privacy]', 'compact_display': compact})
    if compact:
        cursor = tmux('display-message', '-p', '-t', TARGET, '#{cursor_x},#{cursor_y}').stdout.strip()
        print(f'Terminal cursor (x,y; usually hero when no menu): {cursor}')
        print('\n'.join(f'{row:02d} {line[:82]}' for row, line in enumerate(current.splitlines())
                        if line[:82].strip(' │─┌┐└┘')))
        features = [f'{char}@{col},{row}'
                    for row, line in enumerate(current.splitlines()) if 10 <= row <= 30
                    for col, char in enumerate(line[:81])
                    if char not in ' │─┌┐└┘·.▒}']
        print('Map features (x,y): ' + ' '.join(features))
        pets = guard.observe(sys.modules[__name__])[2]
        print('PETS (hilite, never attack): ' + (' '.join(f'{x},{y}' for x, y in sorted(pets)) or 'none visible'))
        lines = current.splitlines()
        for row, line in enumerate(lines):
            if not 10 <= row <= 30:
                continue
            for col, char in enumerate(line[:81]):
                if char != '@':
                    continue
                neighbors = []
                for key, dx, dy in [('7', -1, -1), ('8', 0, -1), ('9', 1, -1),
                                    ('4', -1, 0), ('6', 1, 0),
                                    ('1', -1, 1), ('2', 0, 1), ('3', 1, 1)]:
                    y, x = row + dy, col + dx
                    if 0 <= y < len(lines) and 0 <= x < len(lines[y]):
                        cell = lines[y][x]
                        neighbors.append(f'{key}:{cell if cell != " " else "blank"}({x},{y})')
                print(f'Neighbors of @({col},{row}): ' + ' '.join(neighbors))
    else:
        print(current, end='')


def pickup_guard(value, current):
    """Tariru-style safety: never auto-select every item in a menu, never pick
    up a gray stone (possible loadstone) — kick it first."""
    menu = re.search(r'(Pick up what\?|Take out what|What would you like to drop|'
                     r'Put in what|Drop what type|Take out what type|What would you like)', current)
    if menu and 'A' in value and re.search(r'A\) Auto-select every item', current):
        return 'Refused: never use "A - Auto-select every item"; select items one by one.'
    if menu:
        for letter in value:
            m = re.search(r'\b' + re.escape(letter) + r'\) [^│\n]*gr[ae]y stone', current)
            if letter.isalpha() and m:
                return 'Refused: gray stone in selection (possible loadstone); kick it first.'
    lines = [l for l in current.splitlines()[1:8] if l.strip(' │')]
    if value == ',' and lines and re.search(r'You see here [^.]*gr[ae]y stone', lines[-1]):
        return 'Refused: gray stone here (possible loadstone); kick it first ("Thump!" = loadstone).'
    return None


def stash_gold(bag, expected_gold):
    """One inventory action, with checked menu transitions and no blind macro."""
    initial = guard.state(*guard.observe(sys.modules[__name__]))
    if initial is None or expected_gold <= 0:
        raise RuntimeError('Stash requires a recognized map and positive expected gold.')
    gold = re.search(r'(?:\$|\*):(\d+)', initial['status'])
    if (not gold or int(gold[1]) != expected_gold
            or any(word in initial['status'] for word in guard.DANGERS)
            or initial['hp'] * 3 < initial['max_hp'] * 2):
        raise RuntimeError('Stash gold count, health, or condition preflight failed.')
    reason = f'Stash {expected_gold} loose gold in the holding bag; verify each menu before continuing.'
    audit.record('public_decision', {'text': reason})
    audit.publish('decision', reason, source='checked inventory action')

    def transition(keys, expected, final=False):
        send(keys)
        observed = guard.settled(sys.modules[__name__])
        audit.record('stash_gold_step', {'input': keys, 'observation': None if observed is None else {
            'screen': observed[0], 'cursor': observed[1], 'pets': sorted(observed[2])}})
        if observed is None:
            raise RuntimeError('Stash stopped: terminal did not settle. Inspect screen.')
        current, cursor, _ = observed
        rows = current.splitlines()
        # Only the actual game panel, never the permanent inventory sidebar.
        panel = '\n'.join(row[:81] for row in rows)
        status = rows[34][:81] if len(rows) > 34 else ''
        if expected not in panel:
            raise RuntimeError('Stash stopped: unexpected menu or confirmation. Inspect screen.')
        if final:
            after = guard.state(*observed)
            if (after is None or after['position'] != initial['position']
                    or after['level'] != initial['level']
                    or not re.search(r'(?:\$|\*):0\b', status)):
                raise RuntimeError('Stash stopped: final map or zero-gold state unverified.')
        elif status != initial['status'] or not (0 <= cursor[1] <= 10):
            raise RuntimeError('Stash stopped: game advanced or unexpected cursor. Inspect screen.')
        return panel

    panel = transition('a' + bag, 'Do what with your bag called HOLDING?')
    if 's) stash one item into the bag' not in panel:
        raise RuntimeError('Stash stopped: stash menu option missing.')
    panel = transition('s', 'What do you want to stash? [$')
    transition('$', f'You put {expected_gold} gold pieces into the bag called HOLDING.', final=True)
    print_screen(True)


def wrest_wish(letter, x, y, limit):
    """Retry a manually verified empty wishing wand; stop on any changed situation."""
    initial_hp = None
    previous_turn = None
    unchanged = 0
    for attempt in range(min(max(limit, 0), 20) + 1):
        current = screen()
        lines = current.splitlines()
        hp = re.search(r'HP:(\d+)\(', current)
        turn = re.search(r'T:(\d+)', current)
        cursor = tmux('display-message', '-p', '-t', TARGET,
                      '#{cursor_x},#{cursor_y}').stdout.strip()
        messages = [line[:82].strip(' │') for line in lines[1:8] if line[:82].strip(' │')]
        if (not hp or not turn or cursor != f'{x},{y}' or len(lines) < 35
                or lines[y][x:x+1] != '@' or not messages
                or not messages[-1].endswith('Nothing happens.')):
            print('Stopped: prompt, message, or position changed.')
            break
        hp, turn = int(hp[1]), int(turn[1])
        initial_hp = hp if initial_hp is None else initial_hp
        unchanged = unchanged + 1 if turn == previous_turn else 0
        if hp < initial_hp or unchanged >= 3 or any(
                word in lines[34] for word in ('Hungry', 'Weak', 'Faint', 'Blind', 'Conf', 'Stun')):
            print('Stopped: damage, condition, or no turn advancement.')
            break
        nearby = ''.join(lines[row][max(0, x-4):x+5]
                         for row in range(max(10, y-4), min(31, y+5)))
        if any(char.isalpha() or char in '&12345' for char in nearby) or nearby.count('@') != 1:
            print('Stopped: nearby monster or warning.')
            break
        if attempt == min(max(limit, 0), 20):
            print(f'Stopped after {attempt} attempts.')
            break
        previous_turn = turn
        send('z' + letter)
        time.sleep(1)
    print_screen(True)


def wait_pets(x, y, limit):
    """Bounded search turns at a manually verified safe rendezvous; never move."""
    previous_turn = None
    initial_hp = None
    initially_blind = 'Blind' in screen().splitlines()[-2]
    for attempt in range(min(max(limit, 0), 25) + 1):
        current = screen()
        lines = current.splitlines()
        hp = re.search(r'HP:(\d+)\(', current)
        turn = re.search(r'T:(\d+)', current)
        if not hp or not turn or y >= len(lines) or lines[y][x:x+1] != '@':
            print('Stopped: position/status not recognized.')
            break
        hp, turn = int(hp[1]), int(turn[1])
        initial_hp = hp if initial_hp is None else initial_hp
        if hp < initial_hp or turn == previous_turn or any(word in lines[34] for word in ('Weak', 'Faint', 'Conf', 'Stun')) or ('Blind' in lines[34] and not initially_blind):
            print('Stopped: damage, condition, or no turn advancement.')
            break
        nearby = ''.join(lines[row][max(0, x-1):x+2] for row in range(max(10, y-1), min(31, y+2)))
        if 'f' in nearby and 'u' in nearby:
            print(f'Both expected pet glyphs adjacent after {attempt} waiting turns; inspect before stairs.')
            break
        if any(char.isalpha() and char not in 'fu' for char in nearby):
            print('Stopped: another adjacent monster glyph.')
            break
        if attempt == min(max(limit, 0), 25):
            print('Stopped: waiting turn limit.')
            break
        previous_turn = turn
        send('s')
        time.sleep(1)
    print_screen(True)


def travel(x, y, confirm=True):
    """Travel (_) to screen cell x,y: cursor to self (@), then 8-steps (HJKL
    family) and single digit steps, then '.'. Stops on whatever the game shows."""
    observed = guard.observe(sys.modules[__name__])
    here = guard.state(*observed)
    if here is None:
        raise RuntimeError('Travel needs a recognized map prompt.')
    hx, hy = here['position']
    dx, dy = x - hx, y - hy
    keys = ''
    while dx or dy:
        sx = (dx > 0) - (dx < 0)
        sy = (dy > 0) - (dy < 0)
        big = {(-1, 0): 'H', (1, 0): 'L', (0, -1): 'K', (0, 1): 'J',
               (-1, -1): 'Y', (1, -1): 'U', (-1, 1): 'B', (1, 1): 'N'}[(sx, sy)]
        small = {(-1, 0): '4', (1, 0): '6', (0, -1): '8', (0, 1): '2',
                 (-1, -1): '7', (1, -1): '9', (-1, 1): '1', (1, 1): '3'}[(sx, sy)]
        if (sx == 0 or abs(dx) >= 8) and (sy == 0 or abs(dy) >= 8):
            keys += big
            dx -= 8 * sx
            dy -= 8 * sy
        else:
            keys += small
            dx -= sx
            dy -= sy
    audit.record('travel', {'from': [hx, hy], 'to': [x, y], 'cursor_keys': keys})
    send('_', publish=False)
    time.sleep(.3)
    send('@' + keys + '.', publish=False)
    turn = re.search(r'T:(\d+)', screen())
    audit.publish('command', f'travel → {x},{y}', label='déplacement', game_turn=int(turn[1]) if turn else None)
    time.sleep(1.5)
    # a travel prompt left open (unreachable target...) would swallow the next
    # key: close it (Escape is harmless on the map)
    if 'Where do you want to travel to' in screen() and tmux(
            'display-message', '-p', '-t', TARGET, '#{cursor_y}').stdout.strip() not in ('', '0'):
        send('Escape', named=True, publish=False)
        time.sleep(.3)
    print_screen(True)


class Viewer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            body = (ROOT / 'web/index.html').read_bytes()
            mime = 'text/html; charset=utf-8'
        elif self.path == '/state':
            body = json.dumps(snapshot()).encode()
            mime = 'application/json'
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('start', 'screen', 'attach', 'hide', 'show', 'viewer', 'ack-hp'):
        item = sub.add_parser(name)
        if name == 'screen':
            item.add_argument('--compact', action='store_true')
    keys = sub.add_parser('keys', help='Literal keystrokes, or tmux names with --named')
    keys.add_argument('value')
    keys.add_argument('--named', action='store_true')
    keys.add_argument('--compact', action='store_true')
    keys.add_argument('--why', help='Brief public rationale, recorded before these inputs')
    keys.add_argument('--raw', action='store_true', help='Explicit bypass for menu input, recorded in the audit')
    keys.add_argument('--really', action='store_true', help='Allow answering y to "Really attack?"')
    keys.add_argument('--settle', type=float, default=1,
                      help='Seconds to allow terminal animations to finish (0–10)')
    trav = sub.add_parser('travel', help='Travel command to screen cell x y')
    trav.add_argument('x', type=int)
    trav.add_argument('y', type=int)
    stash = sub.add_parser('stash-gold', help='One checked bag action; stop on unexpected menus or gold count')
    stash.add_argument('--bag', required=True, choices=list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    stash.add_argument('--expected-gold', required=True, type=int)
    pets = sub.add_parser('wait-pets', help='At a verified safe tile, search up to 25 turns for adjacent f and u')
    pets.add_argument('x', type=int)
    pets.add_argument('y', type=int)
    pets.add_argument('--limit', type=int, default=20)
    wrest = sub.add_parser('wrest-wish', help='Guarded retries of a verified empty wishing wand')
    wrest.add_argument('letter', choices=list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    wrest.add_argument('x', type=int)
    wrest.add_argument('y', type=int)
    wrest.add_argument('--limit', type=int, default=20)
    note = sub.add_parser('note', help='Set public stream commentary')
    note.add_argument('text')
    serve = sub.add_parser('serve')
    serve.add_argument('--port', type=int, default=8766)
    serve.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args()
    RUNTIME.mkdir(mode=0o700, exist_ok=True)
    if args.command == 'start':
        start()
    elif args.command == 'screen':
        print_screen(args.compact)
    elif args.command == 'attach':
        os.execvp('tmux', ['tmux', '-S', SOCKET, 'attach-session', '-r', '-t', SESSION])
    elif args.command == 'ack-hp':
        ack_hp()
    elif args.command == 'keys':
        if getattr(args, 'really', False):
            os.environ['NH_REALLY'] = '1'
        # tmux key names (Enter, Escape, C-m...) are not menu letters
        reason = None if args.named else pickup_guard(args.value, screen())
        if reason:
            audit.record('input_preflight_rejected', {'input': args.value, 'reason': reason})
            raise RuntimeError(reason)
        if not args.named and not args.raw and len(args.value) > 1:
            observed = guard.observe(sys.modules[__name__])
            reason = guard.command_preflight(guard.state(*observed), args.value)
            if reason:
                audit.record('input_preflight_rejected', {
                    'input': args.value, 'reason': reason, 'cursor': observed[1],
                    'screen': observed[0] if (not (RUNTIME / 'broadcast.hidden').exists()) else '[hidden for privacy]',
                })
                raise RuntimeError(reason)
        if args.why:
            audit.record('public_decision', {'text': args.why})
            audit.publish('decision', args.why, source='before command')
        if not args.named and not args.raw and re.fullmatch(r'[12346789]{2,}', args.value):
            guard.walk(sys.modules[__name__], args.value)
        else:
            if not args.raw and re.fullmatch(r'(F[12346789]){2,}', args.value):
                raise RuntimeError('Repeated combat input must be inspected between attacks.')
            if args.raw:
                audit.record('raw_input_override', {'reason': args.why, 'input': args.value})
            send(args.value, args.named)
            time.sleep(min(10, max(0, args.settle)))
            print_screen(args.compact)
    elif args.command == 'travel':
        travel(args.x, args.y)
    elif args.command == 'stash-gold':
        stash_gold(args.bag, args.expected_gold)
    elif args.command == 'wait-pets':
        wait_pets(args.x, args.y, args.limit)
    elif args.command == 'wrest-wish':
        wrest_wish(args.letter, args.x, args.y, args.limit)
    elif args.command == 'note':
        audit.record('public_decision', {'text': args.text})
        audit.publish('decision', args.text, source='stream note')
        (RUNTIME / f'commentary-{SLOT}.txt').write_text(audit.clean(args.text, public=True) + '\n')
    elif args.command == 'hide':
        (RUNTIME / 'broadcast.hidden').touch()
    elif args.command == 'show':
        (RUNTIME / 'broadcast.hidden').unlink(missing_ok=True)
    elif args.command == 'serve':
        print(f'Broadcast view listening on {args.host}:{args.port}', flush=True)
        ThreadingHTTPServer((args.host, args.port), Viewer).serve_forever()
    elif args.command == 'viewer':
        if tmux('has-session', '-t', 'viewer', check=False).returncode == 0:
            if tmux('display-message', '-p', '-t', 'viewer:0.0', '#{pane_dead}').stdout.strip() == '1':
                tmux('respawn-pane', '-t', 'viewer:0.0', sys.executable, str(Path(__file__).resolve()), 'serve')
        else:
            tmux('new-session', '-d', '-s', 'viewer', sys.executable, str(Path(__file__).resolve()), 'serve')
        print('Viewer: http://127.0.0.1:8766/')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
