#!/usr/bin/env python3
"""Smoke-test the local NetHack 3.4.3-NAO build over a pty.

Drives the initial menus (character/name) and a handful of movement commands,
capturing the terminal output as evidence that the target game launches and is
playable with BotHack's nethackrc.  This is NOT an ascension run.
"""

import os
import sys
import time
import pty
import select

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_all(fd, timeout):
    out = b""
    end = time.time() + timeout
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.2)
        if r:
            try:
                d = os.read(fd, 65536)
            except OSError:
                break
            if not d:
                break
            out += d
    return out


def main():
    binpath = os.path.join(ROOT, "upstream", "nh343", "nethack.343-nao")
    home = os.path.join(ROOT, "artifacts", "home")
    os.makedirs(home, exist_ok=True)
    env = dict(os.environ)
    env["NETHACKOPTIONS"] = "@" + os.path.join(ROOT, "upstream", "bothack.nethackrc")
    env["TERM"] = "xterm"
    env["HOME"] = home
    name = "smoketest%d" % int(time.time())
    pid, fd = pty.fork()
    if pid == 0:
        os.execve(binpath, [binpath, "-u", name], env)

    # initial: skip intro, answer 'y' to "Shall I pick...", confirm choices,
    # give a name, then move around a little.
    seq = b"\n"            # intro
    seq += b"y\n"          # Shall I pick a character...? yes
    seq += b"y\n"          # accept random role (Valkyrie per nethackrc)
    seq += b"y\n"          # random alignment etc
    seq += name.encode() + b"\n"
    time.sleep(0.3)
    os.write(fd, seq)
    time.sleep(0.5)
    # a few movements / search / inventory
    os.write(fd, b"....jklhll.ssi>")
    time.sleep(0.5)
    text = read_all(fd, 2.0).decode("utf-8", "replace")
    os.write(fd, b"\x1b")  # ESC
    time.sleep(0.2)
    try:
        os.kill(pid, 9)
    except OSError:
        pass
    print(text)
    return text


if __name__ == "__main__":
    main()