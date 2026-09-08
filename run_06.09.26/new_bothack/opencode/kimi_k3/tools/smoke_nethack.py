#!/usr/bin/env python3
"""Smoke test: start NAO NetHack 3.4.3 in a PTY, capture output, quit."""
import os
import pty
import select
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NH = os.path.join(ROOT, ".local/nethack/nethack")
RC = os.path.join(ROOT, "upstream/BotHack/bothack.nethackrc")

pid, fd = pty.fork()
if pid == 0:
    os.environ.update({"TERM": "xterm", "LINES": "24", "COLUMNS": "80",
                       "HOME": os.path.join(ROOT, ".local/home"),
                       "NETHACKOPTIONS": RC})
    os.execv(NH, ["nethack", "-u", "SmokeK3"])

buf = b""
deadline = time.time() + 25
while time.time() < deadline:
    r, _, _ = select.select([fd], [], [], 1.0)
    if r:
        try:
            chunk = os.read(fd, 65536)
        except OSError:
            break
        if not chunk:
            break
        buf += chunk
    if b"There is already a game in progress" in buf:
        os.write(fd, b"y")
        buf = b""
        continue
    if b"Shall I pick a character" in buf or b"welcome to NetHack" in buf:
        break

ok = (b"Shall I pick a character" in buf) or (b"welcome to NetHack" in buf)
if not ok:
    print("SMOKE FAILED; tail of output:")
    print(repr(buf[-600:]))
    try:
        os.kill(pid, 15)
    except ProcessLookupError:
        pass
    sys.exit(1)

# cleanup: escape + quit (answer y to "Really quit?")
try:
    os.write(fd, b"\x1b\x1b#quit\ny")
    time.sleep(1.0)
    os.write(fd, b" \n")
    time.sleep(0.5)
except OSError:
    pass
try:
    os.kill(pid, 15)
except ProcessLookupError:
    pass
print("SMOKE OK")
print("bytes captured:", len(buf))
sys.exit(0)
