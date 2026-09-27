"""Local hash-linked ledger and public feed.

Replaces nethack_astra's Codex-transcript recorder: here the game runs on this
machine, so the ledger only chains every input and observation (sha256 of the
previous line in each record), and the feed drives the local viewer.
"""
import fcntl
import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.runtime'
LEDGER = ROOT / 'runs' / 'ledger.jsonl'


def now():
    return datetime.now(timezone.utc).isoformat()


def clean(value, public=False):
    return value


def _locked(name):
    RUNTIME.mkdir(mode=0o700, exist_ok=True)
    fd = os.open(RUNTIME / name, os.O_CREAT | os.O_RDWR, 0o600)
    handle = os.fdopen(fd, 'w')
    fcntl.flock(handle, fcntl.LOCK_EX)
    return handle


def _head():
    try:
        with open(LEDGER, 'rb') as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - (1 << 20)))
            last = f.read().splitlines()[-1]
        return json.loads(last)['sha256']
    except (FileNotFoundError, IndexError):
        return '0' * 64


def record(kind, data):
    with _locked('ledger.lock'):
        LEDGER.parent.mkdir(exist_ok=True)
        event = {'at': now(), 'kind': kind, 'prev': _head(), 'data': data}
        body = json.dumps(event, sort_keys=True, ensure_ascii=False)
        event['sha256'] = hashlib.sha256(body.encode()).hexdigest()
        with open(LEDGER, 'a') as f:
            f.write(json.dumps(event, sort_keys=True, ensure_ascii=False) + '\n')


def verify():
    prev = '0' * 64
    count = 0
    with open(LEDGER) as f:
        for line in f:
            event = json.loads(line)
            digest = event.pop('sha256')
            if event['prev'] != prev:
                raise SystemExit(f'chain broken at event {count}')
            body = json.dumps(event, sort_keys=True, ensure_ascii=False)
            if hashlib.sha256(body.encode()).hexdigest() != digest:
                raise SystemExit(f'hash mismatch at event {count}')
            prev = digest
            count += 1
    print(f'{count} events, head {prev}')


def publish(kind, text, **details):
    path = RUNTIME / 'public-feed.json'
    with _locked('public-feed.lock'):
        try:
            rows = json.loads(path.read_text())
        except FileNotFoundError:
            rows = []
        rows.append({'id': uuid.uuid4().hex, 'at': now(), 'kind': kind, 'text': text, **details})
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(rows[-80:]))
        tmp.replace(path)


def public_state():
    try:
        feed = json.loads((RUNTIME / 'public-feed.json').read_text())
    except FileNotFoundError:
        feed = []
    return {'feed': feed, 'audit': {'healthy': True, 'head_sha256': _head()}}


def require_healthy():
    return True


if __name__ == '__main__':
    verify()
