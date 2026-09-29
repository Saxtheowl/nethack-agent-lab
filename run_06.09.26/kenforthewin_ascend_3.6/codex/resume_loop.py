#!/usr/bin/env python3
"""Sequential Codex continuation; no NetHack decisions or keystrokes here."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time

BASE = Path(__file__).resolve().parent
STATE = BASE / '.resume-loop'
HARNESS = BASE.parent / 'claude'
GAME = 'Codex-2026-09-28.10:47:13'
THREAD_FILE = STATE / 'thread-id'
STOP = STATE / 'STOP'
DONE = STATE / 'DONE'
child = None
stopping = False


def status(phase, **extra):
    value = dict(phase=phase, time=time.time(), pid=os.getpid(), **extra)
    tmp = STATE / 'status.tmp'
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(STATE / 'status.json')
    print(json.dumps(value), flush=True)


def quota():
    """Read official account limits without any model inference or reset redemption."""
    proc = subprocess.Popen(['codex', 'app-server', '--stdio'], cwd=BASE,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL)
    buffer = b''
    def request(number, method, params):
        nonlocal buffer
        proc.stdin.write((json.dumps(dict(id=number, method=method, params=params))+'\n').encode())
        proc.stdin.flush()
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            if not select.select([proc.stdout], [], [], 1)[0]:
                continue
            data = os.read(proc.stdout.fileno(), 65536)
            if not data:
                raise RuntimeError('quota server exited')
            buffer += data
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get('id') == number:
                    if 'error' in event:
                        raise RuntimeError(str(event['error']))
                    return event['result']
        raise TimeoutError(method)
    try:
        request(1, 'initialize', {'clientInfo': {'name': 'nethack_slot4_resume', 'version': '1.0'}})
        proc.stdin.write(b'{"method":"initialized"}\n')
        proc.stdin.flush()
        return request(2, 'account/rateLimits/read', {})
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def availability(result):
    limits = result.get('rateLimitsByLimitId', {}).get('codex') or result.get('rateLimits')
    if not limits:
        raise RuntimeError('No Codex limits returned; refusing blind retries')
    windows = [limits.get(name) or {} for name in ('primary', 'secondary')]
    exhausted = [w for w in windows if w.get('usedPercent', 0) >= 100]
    blocked = (result.get('ordinaryUsageAllowed') is False or bool(exhausted)
               or bool(limits.get('spendControlReached')) or bool(limits.get('rateLimitReachedType')))
    resets = [w['resetsAt'] for w in exhausted if w.get('resetsAt', 0) > time.time()]
    # Poll read-only at most every five minutes, or soon after the last required reset.
    delay = max(30, min(300, max(resets) - time.time() + 10)) if resets else 300
    return not blocked, delay, {name: limits.get(name) for name in ('primary', 'secondary')}


def wait(seconds):
    deadline = time.monotonic() + seconds
    while not stopping and not STOP.exists() and time.monotonic() < deadline:
        time.sleep(min(1, max(0, deadline - time.monotonic())))


def finish_signal(signum, frame):
    global stopping
    stopping = True
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)


def run():
    global child
    STATE.mkdir(exist_ok=True)
    lock = (STATE / 'lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Slot 4 continuation already running')
    signal.signal(signal.SIGTERM, finish_signal)
    signal.signal(signal.SIGINT, finish_signal)
    status('handoff_wait')
    wait(30)
    failures = 0
    while not stopping and not STOP.exists() and not DONE.exists():
        try:
            slot = json.loads((HARNESS / '.runtime/slot-4.json').read_text())
            if slot.get('game_id') != GAME or slot.get('player') != 'Codex':
                status('stopped_wrong_game')
                return
            allowed, delay, windows = availability(quota())
        except Exception as exc:
            failures += 1
            status('check_error', error=str(exc), consecutive=failures)
            if failures >= 3:
                return
            wait(300)
            continue
        if not allowed:
            status('waiting_quota', retry_seconds=delay, windows=windows)
            wait(delay)
            continue
        prompt = (BASE / 'resume_prompt.txt').read_text()
        stamp = str(time.time_ns())
        logpath = STATE / (stamp + '.jsonl')
        thread = THREAD_FILE.read_text().strip() if THREAD_FILE.exists() else None
        cmd = ['codex', 'exec', '-C', str(BASE), '-s', 'danger-full-access',
               '-c', 'approval_policy="never"']
        if thread:
            cmd += ['resume', '--skip-git-repo-check', '--json', thread, '-']
        else:
            cmd += ['--skip-git-repo-check', '--json', '-']
        env = dict(os.environ, NETHACK_RESUME_LOOP='1')
        status('playing', thread=thread, log=str(logpath))
        with logpath.open('w') as log, (STATE / (stamp+'.stderr')).open('w') as err:
            child = subprocess.Popen(cmd, cwd=BASE, stdin=subprocess.PIPE,
                                     stdout=log, stderr=err, env=env, start_new_session=True)
            child.stdin.write(prompt.encode())
            child.stdin.close()
            while child.poll() is None:
                if stopping or STOP.exists():
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
                    break
                time.sleep(1)
            code = child.returncode
            child = None
        # Persist the exact dedicated session even if it hit quota mid-turn.
        with logpath.open() as events:
            for line in events:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get('type') == 'thread.started' and event.get('thread_id'):
                    THREAD_FILE.write_text(event['thread_id'] + '\n')
                    break
        if stopping or STOP.exists() or DONE.exists():
            break
        if code == 0:
            failures = 0
            status('between_turns')
            wait(10)
        else:
            # Check quota before retrying; non-quota failures stop after three attempts.
            try:
                allowed, delay, windows = availability(quota())
            except Exception:
                allowed, delay = True, 300
            if allowed:
                failures += 1
                status('run_error', exit_code=code, consecutive=failures)
                if failures >= 3:
                    return
            else:
                failures = 0
                status('waiting_quota', retry_seconds=delay)
            wait(max(300, delay))
    status('finished' if DONE.exists() else 'stopped')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        allowed, delay, windows = availability(quota())
        print(json.dumps(dict(allowed=allowed, retry_seconds=delay, windows=windows)))
    else:
        run()
