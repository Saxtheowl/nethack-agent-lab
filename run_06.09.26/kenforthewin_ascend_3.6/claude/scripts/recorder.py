#!/usr/bin/env python3
"""Continuous screen recorder for every game slot (1-3).

Polls each slot's tmux pane a few times per second and appends a frame to
runs/games/<game_id>/frames.jsonl whenever the screen changes, so any game
can be replayed from the dashboard while it is still being played. Also keeps
meta.json up to date and records the outcome (from the xlogfile) when a game
ends. Run it in the background: python3 scripts/recorder.py
"""
import json
import subprocess
import time
from datetime import datetime, timezone

import bags
import frames
from session import SOCKET, RUNTIME, ROOT, HOST, slot_tmux, slot_where
from terminal import text_runs

SLOTS = tuple(str(n) for n in range(1, 9))
SAVEDIR = ROOT / 'engine/install/games/lib/nethackdir/save'


def tmux_slot(slot, *args):
    sock, sess = slot_tmux(slot)
    args = [a.replace('@S', sess) for a in args]
    return subprocess.run(['tmux', '-S', sock, *args], text=True, capture_output=True)


def slot_info(slot):
    try:
        return json.loads((RUNTIME / f'slot-{slot}.json').read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def pane_alive(slot):
    r = tmux_slot(slot, 'display-message', '-p', '-t', '@S:0.0', '#{pane_dead}')
    return r.returncode == 0 and r.stdout.strip() == '0'


def remote_xlog(remote):
    r = subprocess.run(['ssh', '-o', 'BatchMode=yes', remote['host'], f'tail -50 {frames.XLOG}'],
                       text=True, capture_output=True, timeout=20)
    return [dict(f.split('=', 1) for f in l.split('\t') if '=' in f) for l in r.stdout.splitlines()]


def finish(meta, player, remote=None):
    """Game pane closed: saved (to be resumed) or over (xlogfile has the verdict).
    A wish_abuser game lives on the worker: its save/xlogfile are read there."""
    if remote:
        from session import remote_saved
        try:
            saved = remote_saved(remote, player)
            entries = remote_xlog(remote)
        except subprocess.TimeoutExpired:
            meta['status'] = 'stopped'
            return
    else:
        saved = any(SAVEDIR.glob(f'*{player}.gz')) or any(SAVEDIR.glob(f'*{player}'))
        entries = frames.xlog_entries()
    if saved:
        meta['status'] = 'saved'
        return
    started = meta.get('started_epoch', 0)
    for entry in reversed(entries):
        if entry.get('name') == player and int(entry.get('endtime', 0)) >= started - 5:
            meta.update(status={'ascended': 'ascended', 'quit': 'quit'}.get(entry.get('death'), 'dead'),
                        death=entry.get('death'), points=int(entry.get('points', 0)),
                        turns=int(entry.get('turns', 0)), maxlvl=int(entry.get('maxlvl', 0)),
                        endtime=int(entry.get('endtime', 0)))
            return
    meta['status'] = 'stopped'


def main():
    writers, alive, metas, last_meta, watchers = {}, {}, {}, 0, {}
    while True:
        now = time.time()
        for slot in SLOTS:
            info = slot_info(slot)
            if not info or slot_where(slot) != HOST:  # each machine records its own slots
                continue
            gid = info['game_id']
            is_alive = pane_alive(slot)
            meta = metas.get(gid) or frames.load_meta(gid)
            metas[gid] = meta
            meta.update(id=gid, slot=slot, player=info['player'])
            meta.setdefault('started', info.get('started'))
            meta.setdefault('started_epoch', now)
            for key in ('journal', 'run', 'style', 'remote'):
                if info.get(key):
                    meta[key] = info[key]
            if is_alive:
                if gid not in writers:
                    writers[gid] = frames.Writer(gid)
                captured = tmux_slot(slot, 'capture-pane', '-p', '-e', '-t', '@S:0.0').stdout
                w = writers[gid]
                rows = frames.segment_rows(text_runs(captured))
                try:  # remember what the agent saw inside its bags (dashboard inventory)
                    watchers.setdefault(gid, bags.Watcher(gid)).feed(
                        [frames.row_text(r) for r in rows], meta.get('turn'))
                except Exception:
                    pass
                if w.add(rows, now):
                    meta['frames'] = w.index
                    meta['updated'] = now
                    if w.last_status:
                        t, dlvl, hp, hpmax, xl, ac = w.last_status
                        meta.update(turn=t, dlvl=dlvl, hp=hp, hpmax=hpmax, xl=xl, ac=ac)
                        if str(dlvl).isdigit():
                            meta['maxdepth'] = max(meta.get('maxdepth', 0), int(dlvl))
                meta['status'] = 'live'
            elif alive.get(slot) and meta.get('status') == 'live':
                finish(meta, info['player'], info.get('remote'))
                frames.save_meta(gid, meta)
            alive[slot] = is_alive
        if now - last_meta > 2:
            for gid, meta in metas.items():
                if meta.get('status') == 'live':
                    frames.save_meta(gid, meta)
            last_meta = now
        time.sleep(0.5)


if __name__ == '__main__':
    main()
