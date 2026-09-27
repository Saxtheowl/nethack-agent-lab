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
                if slot not in ('1', '2', '3'):
                    return self.send({'error': 'bad slot'}, code=400)
                return self.send(live(slot))
            if url.path == '/api/games':
                return self.send({'games': games(), 'slots': {s: slot_game(s) for s in '123'},
                                  'now': time.time()})
            if url.path == '/api/frames':
                lines, total = frame_lines(gid, int(q.get('from', 0)), min(int(q.get('limit', 4000)), 20000))
                body = '{"total":%d,"frames":[%s]}' % (total, ','.join(l.strip() for l in lines))
                return self.send(body)
            if url.path == '/api/log':
                p = frames.GAMES / gid / 'log.jsonl'
                rows = [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []
                return self.send({'log': rows})
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
