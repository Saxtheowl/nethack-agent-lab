"""Interactive play daemon: keeps a NetHack session alive between my turns.

Control files (in the run dir):
  input   — append raw keys here; the daemon sends them to the game
  screen.txt — always the latest rendered screen (with cursor marker)
  status.txt — one-line liveness info
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bot"))
from term import TtySession
from playground import make_playground, nethack_argv_env

RUN = sys.argv[1] if len(sys.argv) > 1 else "/tmp/nh-play"
os.makedirs(RUN, exist_ok=True)
inp = os.path.join(RUN, "input")
scr = os.path.join(RUN, "screen.txt")
stat = os.path.join(RUN, "status.txt")
open(inp, "w").close()

pg = make_playground(os.path.join(RUN, "playground"))
argv, env = nethack_argv_env(pg)
sess = TtySession(argv, env, record=os.path.join(RUN, "game.ttyrec"))

pos = 0
last_write = 0.0
while True:
    sess.settle(quiet=0.05, total=0.5)
    # consume new input
    try:
        with open(inp, "rb") as f:
            f.seek(pos)
            data = f.read()
            pos = f.tell()
    except OSError:
        data = b""
    if data:
        sess.send(data)
        sess.settle(quiet=0.08, total=2.0)
    now = time.time()
    if now - last_write > 0.3:
        last_write = now
        cx, cy = sess.cursor()
        lines = sess.lines()
        out = []
        for y, line in enumerate(lines):
            if y == cy and 0 <= cx < len(line):
                line = line[:cx] + "█" + line[cx + 1:]
            out.append(f"{y:2d}|{line.rstrip()}")
        with open(scr + ".tmp", "w") as f:
            f.write("\n".join(out) + "\n")
        os.replace(scr + ".tmp", scr)
        with open(stat, "w") as f:
            f.write(f"alive={sess.alive()} t={time.strftime('%H:%M:%S')} cursor=({cx},{cy})\n")
    if not sess.alive():
        with open(stat, "w") as f:
            f.write("DEAD\n")
        break
