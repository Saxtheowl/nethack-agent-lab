#!/usr/bin/env python3
"""Replays a recorded NetHack session (tools/pty_tap.py log) to a bot.

The recording interleaves both directions, so the replay is *causal*: output
chunks are emitted in order, and whenever the recording shows the original bot
having written N bytes, the replay waits for the bot under test to write N
bytes before continuing.  Both bots therefore see the same bytes in the same
chunks at the same points of the interaction, whatever their speed.
"""
import os
import select
import struct
import sys
import termios
import time
import tty

CHUNK_DELAY = float(os.environ.get('REPLAY_DELAY', '0.002'))
WAIT_TIMEOUT = float(os.environ.get('REPLAY_WAIT', '5.0'))


def read_tap(path):
    data = open(path, 'rb').read()
    recs = []
    i = 0
    while i + 5 <= len(data):
        d = data[i:i + 1]
        n = struct.unpack('<I', data[i + 1:i + 5])[0]
        chunk = data[i + 5:i + 5 + n]
        if len(chunk) != n:
            break
        recs.append((d.decode(), chunk))
        i += 5 + n
    return recs


def main():
    recs = read_tap(os.environ['REPLAY_TAP'])
    keylog = open(os.environ.get('REPLAY_KEYS', 'replay_keys.bin'), 'wb',
                  buffering=0)
    status = open(os.environ.get('REPLAY_STATUS', '/dev/null'), 'w')
    stdin, stdout = sys.stdin.fileno(), sys.stdout.fileno()
    saved = None
    try:
        saved = termios.tcgetattr(stdin)
        tty.setraw(stdin)
    except Exception:
        pass
    pending = bytearray()
    timeouts = 0
    try:
        for idx, (d, data) in enumerate(recs):
            if d == 'O':
                os.write(stdout, data)
                time.sleep(CHUNK_DELAY)
                while select.select([stdin], [], [], 0)[0]:
                    got = os.read(stdin, 4096)
                    if not got:
                        break
                    pending += got
                    keylog.write(got)
            else:
                need = len(data)
                end = time.time() + WAIT_TIMEOUT
                while len(pending) < need and time.time() < end:
                    if select.select([stdin], [], [], 0.05)[0]:
                        got = os.read(stdin, 4096)
                        if not got:
                            break
                        pending += got
                        keylog.write(got)
                if len(pending) < need:
                    timeouts += 1
                    status.write("timeout at record %d waiting for %d bytes "
                                 "(have %d)\n" % (idx, need, len(pending)))
                    del pending[:]
                else:
                    del pending[:need]
        end = time.time() + 2.0
        while time.time() < end:
            if select.select([stdin], [], [], 0.1)[0]:
                got = os.read(stdin, 4096)
                if got:
                    keylog.write(got)
    finally:
        status.write("replay finished, %d desyncs\n" % timeouts)
        status.close()
        if saved is not None:
            try:
                termios.tcsetattr(stdin, termios.TCSADRAIN, saved)
            except Exception:
                pass
        keylog.close()


main()
