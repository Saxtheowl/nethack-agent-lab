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
  /api/strategy             cross-run statistics (analytics.py)
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

import analytics
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


def journal_sections(path):
    """DEATH / ABANDONNÉE headline + text, and Lessons bullets, from a journal."""
    out = {'end': None, 'end_text': '', 'lessons': []}
    try:
        text = (ROOT / path).read_text()
    except (OSError, TypeError):
        return out
    for block in re.split(r'^## ', text, flags=re.M)[1:]:
        title, _, body = block.partition('\n')
        if re.match(r'(DEATH|ABANDONN)', title, re.I) and not out['end']:
            out['end'] = title.strip()
            out['end_text'] = ' '.join(l.strip() for l in body.splitlines() if l.strip() and not l.startswith('- '))[:1200]
            out['lessons'] += [l[2:].strip() for l in body.splitlines() if l.startswith('- ')]
        elif re.match(r'(Lessons|Leçons)', title, re.I):
            cur = None
            for l in body.splitlines():
                if l.startswith('- '):
                    cur = l[2:].strip(); out['lessons'].append(cur)
                elif l.startswith('  ') and out['lessons'] and cur is not None:
                    out['lessons'][-1] += ' ' + l.strip()
    return out


def history():
    runs = []
    for m in games():
        gid = m['id']
        rows = statuses(gid)
        maxdepth = max([int(s[1]) for _, _, s in rows if str(s[1]).isdigit()] or [m.get('maxdepth') or m.get('maxlvl') or 0])
        maxxl = max([s[4] for _, _, s in rows] or [m.get('xl') or 0])
        lastturn = rows[-1][2][0] if rows else m.get('turn') or 0
        chron = chronicle(gid)
        for c in chron:
            c['frame'] = frame_at(rows, c['t'])
        j = journal_sections(m.get('journal'))
        runs.append({**{k: m.get(k) for k in ('id', 'player', 'slot', 'run', 'style', 'status', 'death',
                                            'points', 'started', 'cause_summary', 'journal')},
                     'turns': m.get('turns') or lastturn, 'maxdepth': maxdepth, 'maxxl': maxxl,
                     'items': [c['title'] for c in chron if c.get('kind') == 'item'],
                     'chronicle': chron, 'end': j['end'], 'end_text': j['end_text'], 'lessons': j['lessons']})
    def agg(rs):
        done = [r for r in rs if r['status'] in ('dead', 'ascended')]
        return {'games': len(rs), 'live': sum(r['status'] == 'live' for r in rs),
                'dead': sum(r['status'] == 'dead' for r in rs), 'quit': sum(r['status'] == 'quit' for r in rs),
                'ascended': sum(r['status'] == 'ascended' for r in rs),
                'best_depth': max([r['maxdepth'] for r in rs] or [0]), 'best_xl': max([r['maxxl'] for r in rs] or [0]),
                'turns': sum(r['turns'] or 0 for r in rs),
                'avg_turns_at_death': round(sum(r['turns'] or 0 for r in done) / len(done)) if done else 0}
    causes = {}
    for r in runs:
        if r['status'] == 'dead' and r['death']:
            k = re.sub(r'^killed by (an?|the) ', '', r['death'])
            causes[k] = causes.get(k, 0) + 1
    return {'runs': runs, 'total': agg(runs),
            'styles': {st: agg([r for r in runs if (r['style'] or 'avant-style') == st])
                       for st in sorted({r['style'] or 'avant-style' for r in runs})},
            'causes': sorted(causes.items(), key=lambda kv: -kv[1])}


_strategy_cache = {'t': 0, 'data': None}
EV_FR = {'xl': 'niveau XL', 'pray': 'prayer', 'trap': 'trap', 'theft': 'vol', 'excalibur': 'Excalibur',
         'wish': 'wish', 'lifesave': 'lifesaved', 'intrinsic': 'intrinsèque', 'lowhp': 'HP bas',
         'death': 'mort', 'faint': 'Fainted', 'altar': 'altar', 'shop': 'shop', 'fall': 'chute', 'level': 'Dlvl'}


def agent_activity(gid):
    p = frames.GAMES / gid / 'log.jsonl'
    out = {'commands': 0, 'travel': 0, 'decisions': 0, 'first': None, 'last': None, 'notes': []}
    if not p.exists():
        return out
    for l in p.read_text().splitlines():
        try:
            r = json.loads(l)
        except json.JSONDecodeError:
            continue
        k = r.get('kind')
        out['commands'] += k == 'command'
        out['travel'] += k == 'travel'
        if k == 'decision':
            out['decisions'] += 1
            out['notes'].append({'t': r['t'], 'text': r.get('text', '')[:300]})
        out['first'] = out['first'] or r['t']
        out['last'] = r['t']
    out['notes'] = out['notes'][-60:]
    return out


def strategy():
    """Cross-run statistics for the Stratégie sub-tabs (cached 60 s)."""
    if _strategy_cache['data'] and time.time() - _strategy_cache['t'] < 60:
        return _strategy_cache['data']
    from collections import Counter
    hist = history()
    tot = {k: Counter() for k in ('kills', 'pet_kills', 'hit_by', 'pickups', 'traps', 'thefts', 'eaten', 'intrinsics', 'shops')}
    kill_games = Counter()
    depth = {}  # dlvl -> {turns, visits, lowhp, deaths, hits}
    games_out, events, lessons = [], [], []
    for r in hist['runs']:
        gid = r['id']
        try:
            s = analytics.summarize(gid)
        except Exception:
            continue
        for k in tot:
            tot[k].update(s[k])
        for k in s['kills']:
            kill_games[k] += 1
        for d, (a, b) in s['levels'].items():
            e = depth.setdefault(d, {'turns': 0, 'visits': 0, 'lowhp': 0, 'deaths': 0, 'hit': 0})
            e['turns'] += max(0, b - a)
            e['visits'] += 1
        cur = None
        for e in analytics.analyze(gid)['events']:
            if e['type'] == 'level':
                cur = e['v']
            elif e['type'] in ('lowhp', 'hit_by') and cur:
                depth.setdefault(cur, {'turns': 0, 'visits': 0, 'lowhp': 0, 'deaths': 0, 'hit': 0})[
                    'lowhp' if e['type'] == 'lowhp' else 'hit'] += 1
        if r['status'] == 'dead' and s['series']:
            d = str(s['series'][-1][1])
            depth.setdefault(d, {'turns': 0, 'visits': 0, 'lowhp': 0, 'deaths': 0, 'hit': 0})['deaths'] += 1
        for e in s['key_events']:
            if e['type'] == 'level' and not (e['v'].isdigit() and int(e['v']) >= 3):
                continue
            events.append({'game': gid, 'slot': r['slot'], 'style': r['style'], 'turn': e['turn'], 't': e['t'],
                           'frame': e['f'], 'type': e['type'], 'label': EV_FR.get(e['type'], e['type']),
                           'v': e['v'], 'msg': e.get('msg', '')})
        act = agent_activity(gid)
        hours = ((act['last'] or 0) - (act['first'] or 0)) / 3600
        for l in r['lessons']:
            lessons.append({'game': gid, 'slot': r['slot'], 'style': r['style'], 'status': r['status'], 'text': l})
        ser = s['series']
        step = max(1, len(ser) // 150)
        games_out.append({
            **{k: r[k] for k in ('id', 'slot', 'run', 'style', 'status', 'death', 'turns', 'maxdepth', 'maxxl', 'started')},
            'n': s['n'], 'milestones': s['milestones'], 'prayers': len(s['prayers']), 'pray_results': s['pray_results'],
            'kills': dict(s['kills']), 'hit_by': dict(s['hit_by']), 'pet_kills': dict(s['pet_kills']),
            'pickups': dict(s['pickups']), 'eaten': dict(s['eaten']), 'intrinsics': list(s['intrinsics']), 'traps': dict(s['traps']),
            'chron_items': r['items'], 'lessons_n': len(r['lessons']), 'chronicle_n': len(r['chronicle']),
            'cause_summary': r.get('cause_summary'), 'player': r.get('player'),
            'thefts': sum(s['thefts'].values()), 'shops': list(s['shops']), 'altars': list(s['altars']),
            'levels': s['levels'], 'series': ser[::step] + ser[-1:],
            'agent': {**{k: act[k] for k in ('commands', 'travel', 'decisions')}, 'hours': round(hours, 2),
                      'turns_per_hour': round((r['turns'] or 0) / hours) if hours > 0.05 else None,
                      'keys_per_turn': round(act['commands'] / r['turns'], 2) if r['turns'] else None,
                      'notes': act['notes']},
        })
    events.sort(key=lambda e: e['t'], reverse=True)
    data = {
        'generated': time.time(), 'total': hist['total'], 'styles': hist['styles'], 'causes': hist['causes'],
        'games': games_out,
        'top': {k: v.most_common(40) for k, v in tot.items()},
        'kill_games': kill_games.most_common(40),
        'depth': sorted(({'dlvl': d, **v} for d, v in depth.items()), key=lambda x: int(x['dlvl']) if x['dlvl'].isdigit() else 99),
        'events': events[:3000], 'lessons': lessons,
    }
    _strategy_cache.update(t=time.time(), data=data)
    return data


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
                if slot not in [str(n) for n in range(1, 9)]:
                    return self.send({'error': 'bad slot'}, code=400)
                return self.send(live(slot))
            if url.path == '/api/games':
                return self.send({'games': games(), 'slots': {s: slot_game(s) for s in '12345678'},
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
            if url.path == '/api/history':
                return self.send(history())
            if url.path == '/api/strategy':
                return self.send(strategy())
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
