#!/usr/bin/env python3
"""Local web server: live view (tab "Live") and dashboard with replay (tab
"Dashboard"). stdlib only; binds to 127.0.0.1 by default.

  python3 scripts/dashboard.py [--port 8766] [--host 127.0.0.1]

API
  /api/live?slot=N          current screen runs, status and feed of a slot
  /api/games                all games (meta.json), newest first
  /api/frames?game=ID&from=N[&limit=M]   frame deltas (see frames.py)
  /api/log?game=ID          decisions / commands with timestamps
  /api/journal?game=ID      the run journal (markdown text)
"""
import argparse
import json
import re
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import frames
from terminal import text_runs

ROOT = frames.ROOT
WEB = ROOT / 'web'
RUNTIME = ROOT / '.runtime'
import hashlib
SOCKET = '/tmp/nhstream-' + hashlib.sha256(str(ROOT).encode()).hexdigest()[:12] + '.sock'
SAFE_ID = re.compile(r'^[A-Za-z0-9_.:\-]+$')

_offsets = {}
_lock = threading.Lock()


def frame_lines(gid, start, limit):
    """Line-offset index per game, extended incrementally (files only grow)."""
    path = frames.GAMES / gid / 'frames.jsonl'
    if not path.exists():
        return [], 0
    with _lock:
        idx = _offsets.setdefault(gid, {'pos': 0, 'offs': []})
        size = path.stat().st_size
        if size < idx['pos']:  # file was rewritten
            idx.update(pos=0, offs=[])
        if size > idx['pos']:
            with open(path, 'rb') as f:
                f.seek(idx['pos'])
                pos = idx['pos']
                for line in f:
                    if not line.endswith(b'\n'):
                        break  # partial write, pick it up next time
                    idx['offs'].append(pos)
                    pos += len(line)
                idx['pos'] = pos
        offs = list(idx['offs'])
    total = len(offs)
    if start >= total:
        return [], total
    out = []
    with open(path, 'rb') as f:
        f.seek(offs[start])
        for _ in range(min(limit, total - start)):
            out.append(f.readline().decode())
    return out, total


_status_cache = {}


def statuses(gid):
    """[(frame_index, t, status)] for frames carrying a status line (cached)."""
    path = frames.GAMES / gid / 'frames.jsonl'
    if not path.exists():
        return []
    c = _status_cache.setdefault(gid, {'pos': 0, 'n': 0, 'rows': []})
    size = path.stat().st_size
    if size < c['pos']:
        c.update(pos=0, n=0, rows=[])
    with open(path, 'rb') as f:
        f.seek(c['pos'])
        for line in f:
            if not line.endswith(b'\n'):
                break
            c['pos'] += len(line)
            m = re.search(rb'"t":([0-9.]+).*"s":(\[[^\]]*\]|null)', line)
            if m and m[2] != b'null':
                c['rows'].append((c['n'], float(m[1]), json.loads(m[2])))
            c['n'] += 1
    return c['rows']


def chronicle(gid):
    p = frames.GAMES / gid / 'chronicle.jsonl'
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def frame_at(rows, t):
    best = 0
    for i, ft, _ in rows:
        if ft <= t:
            best = i
        else:
            break
    return best


def highlights(gid, window=1000, count=3):
    """Most important moments of the last `window` game turns."""
    rows = statuses(gid)
    meta = frames.load_meta(gid)
    evs = []
    maxdepth, prev = 0, None
    for i, t, s in rows:
        turn, dlvl, hp, hpmax, xl, ac = s
        depth = int(dlvl) if str(dlvl).isdigit() else 60
        if prev:
            if dlvl != prev[1]:
                if depth > maxdepth:
                    evs.append((35, i, t, turn, 'progress', f'Nouveau record : Dlvl {dlvl}', ''))
                else:
                    evs.append((8, i, t, turn, 'progress', f'Dlvl {dlvl}', ''))
            if xl > prev[4]:
                evs.append((20 + xl, i, t, turn, 'progress', f'XL {xl}', ''))
            if hp <= hpmax / 3 < prev[2]:
                evs.append((45, i, t, turn, 'danger', f'Danger : HP {hp}({hpmax})', ''))
            elif prev[2] - hp >= max(5, hpmax / 4):
                evs.append((25, i, t, turn, 'danger', f'Gros coup encaissé : HP −{prev[2] - hp}', ''))
        maxdepth = max(maxdepth, depth)
        prev = s
    for c in chronicle(gid):
        evs.append(({3: 90, 2: 60, 1: 30}.get(c.get('importance'), 30) + (10 if c.get('kind') == 'death' else 0),
                    frame_at(rows, c['t']), c['t'], c.get('turn'), c.get('kind', 'event'),
                    c['title'], c.get('text', '')))
    last_turn = rows[-1][2][0] if rows else 0
    recent = [e for e in evs if e[3] is None or e[3] >= last_turn - window]
    recent.sort(key=lambda e: (-e[0], -(e[3] or 0)))
    out, seen = [], set()
    for score, i, t, turn, kind, title, text in recent:
        if title in seen:
            continue
        seen.add(title)
        out.append({'score': score, 'frame': i, 't': t, 'turn': turn, 'kind': kind, 'title': title, 'text': text})
        if len(out) == count:
            break
    out.sort(key=lambda e: e['turn'] or 0)
    return {'game': gid, 'window': window, 'last_turn': last_turn, 'highlights': out}


def slot_game(slot):
    try:
        return json.loads((RUNTIME / f'slot-{slot}.json').read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def live(slot):
    session = 'nethack' if slot == '1' else f'nethack{slot}'
    r = subprocess.run(['tmux', '-S', SOCKET, 'capture-pane', '-p', '-e', '-t', f'{session}:0.0'],
                       text=True, capture_output=True)
    info = slot_game(slot) or {}
    meta = frames.load_meta(info['game_id']) if info.get('game_id') else {}
    try:
        feed = json.loads((RUNTIME / f'public-feed-{slot}.json').read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        feed = []
    note = RUNTIME / f'commentary-{slot}.txt'
    return {'slot': slot, 'alive': r.returncode == 0 and bool(r.stdout.strip()),
            'rows': frames.segment_rows(text_runs(r.stdout)) if r.returncode == 0 else [],
            'meta': meta, 'feed': feed[-40:],
            'commentary': note.read_text().strip() if note.exists() else ''}


def games():
    out = []
    if frames.GAMES.exists():
        for d in frames.GAMES.iterdir():
            if (d / 'meta.json').exists():
                m = frames.load_meta(d.name)
                m.setdefault('id', d.name)
                out.append(m)
    out.sort(key=lambda m: m.get('started', ''), reverse=True)
    return out


class Handler(BaseHTTPRequestHandler):
    def send(self, body, mime='application/json', code=200):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        gid = q.get('game', '')
        if gid and not SAFE_ID.match(gid):
            return self.send({'error': 'bad game id'}, code=400)
        try:
            if url.path in ('/', '/index.html'):
                return self.send((WEB / 'app.html').read_bytes(), 'text/html; charset=utf-8')
            if url.path == '/classic':
                return self.send((WEB / 'index.html').read_bytes(), 'text/html; charset=utf-8')
            if url.path == '/api/live':
                slot = q.get('slot', '1')
                if slot not in ('1', '2', '3', '4', '5'):
                    return self.send({'error': 'bad slot'}, code=400)
                return self.send(live(slot))
            if url.path == '/api/games':
                return self.send({'games': games(), 'slots': {s: slot_game(s) for s in '12345'},
                                  'now': time.time()})
            if url.path == '/api/frames':
                lines, total = frame_lines(gid, int(q.get('from', 0)), min(int(q.get('limit', 4000)), 20000))
                body = '{"total":%d,"frames":[%s]}' % (total, ','.join(l.strip() for l in lines))
                return self.send(body)
            if url.path == '/api/log':
                p = frames.GAMES / gid / 'log.jsonl'
                rows = [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []
                return self.send({'log': rows})
            if url.path == '/api/highlights':
                return self.send(highlights(gid, int(q.get('window', 1000)), int(q.get('count', 3))))
            if url.path == '/api/chronicle':
                ids = [gid] if gid else [g['id'] for g in games()]
                out = []
                for g in ids:
                    rows = statuses(g)
                    for c in chronicle(g):
                        out.append({**c, 'game': g, 'frame': frame_at(rows, c['t'])})
                out.sort(key=lambda c: c['t'], reverse=True)
                return self.send({'chronicle': out})
            if url.path == '/api/journal':
                m = frames.load_meta(gid)
                j = m.get('journal')
                text = (ROOT / j).read_text() if j and (ROOT / j).exists() else ''
                return self.send({'journal': j, 'text': text})
            if url.path == '/state':  # compatibility with the classic page
                return self.send(live('1'))
        except Exception as e:  # keep the server alive; report the error
            return self.send({'error': str(e)}, code=500)
        self.send_error(404)

    def log_message(self, *_):
        pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int, default=8766)
    p.add_argument('--host', default='127.0.0.1')
    a = p.parse_args()
    print(f'Dashboard on http://{a.host}:{a.port}/', flush=True)
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
