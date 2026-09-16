"""Game session: owns the NetHack process and its resources.

Isolation contract:
- every run gets a unique USER name (netgames key on the user name);
- every run gets its own HOME under the run directory;
- on start, the run removes only *its own* leftover files in the shared
  game var (those matching its own username) - never another run's;
- the game build itself lives under this project (tools/build_nethack343_nao.sh)
  so var/xlogfile never collide with neighbouring workspaces.
"""

import os
import pty
import re
import select
import signal
import struct
import subprocess
import time

from . import term

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NH_BINARY = os.path.join(PROJECT_ROOT, "upstream", "nh343", "nethack.343-nao")
NH_NETHACKRC = os.path.join(PROJECT_ROOT, "upstream", "bothack.nethackrc")
NH_VAR = os.path.join(PROJECT_ROOT, "upstream", "nh343", "var")
NH_DETRNG = os.path.join(PROJECT_ROOT, "upstream", "det_rng.so")
USER_PREFIX = "nlight"


def find_binary():
    return NH_BINARY if os.path.exists(NH_BINARY) else None


class SessionDead(Exception):
    pass


class Session:
    def __init__(self, run_dir, username, seed=None, ttyrec=None):
        self.run_dir = run_dir
        self.username = username
        self.seed = seed
        self.dead = False
        self.exitcode = None
        self.home = os.path.join(run_dir, "home")
        os.makedirs(self.home, exist_ok=True)
        self.ttyrec_path = ttyrec or os.path.join(run_dir, "game.ttyrec")
        self._ttyrec = None
        self._pid = None
        self._fd = None
        self._buf = b""
        self.terminal = term.Screen()

    # -- resource hygiene -------------------------------------------
    def cleanup_own_files(self):
        """Delete leftover game files for THIS run's username only."""
        pat = re.compile(re.escape(self.username) + r"\.(\d+|save|\d+\.lev|0)")
        removed = 0
        var = NH_VAR
        if not os.path.isdir(var):
            return removed
        for fn in os.listdir(var):
            if pat.match(fn):
                p = os.path.join(var, fn)
                try:
                    os.remove(p)
                    removed += 1
                except OSError:
                    pass
        save = os.path.join(var, "save")
        if os.path.isdir(save):
            for fn in os.listdir(save):
                if fn.startswith(self.username + "."):
                    try:
                        os.remove(os.path.join(save, fn))
                        removed += 1
                    except OSError:
                        pass
        # a stale lock held by our own name (already-checked file ownership)
        lock = os.path.join(var, "sessionlock")
        if os.path.exists(lock):
            try:
                owner = ""
                with open(lock, "rb") as fh:
                    owner = fh.read(40)
                # only remove if it clearly references our name
                if self.username.encode() in owner:
                    os.remove(lock)
                    removed += 1
            except OSError:
                pass
        return removed

    # -- process ------------------------------------------------------
    def start(self):
        self.cleanup_own_files()
        env = dict(os.environ)
        env["TERM"] = "xterm"
        env["HOME"] = self.home
        env["USER"] = self.username
        env["NETHACKOPTIONS"] = "@" + NH_NETHACKRC
        if self.seed is not None and os.path.exists(NH_DETRNG):
            env["NETHACK_FIXED_SEED"] = str(self.seed)
            env["LD_PRELOAD"] = NH_DETRNG
        self._ttyrec = open(self.ttyrec_path, "ab")
        self._pid, self._fd = pty.fork()
        if self._pid == 0:  # child
            try:
                os.execve(NH_BINARY, ["nethack", "-u", self.username], env)
            except Exception:
                os._exit(127)
        import fcntl
        import termios
        fcntl.ioctl(self._fd, termios.TIOCSWINSZ,
                    struct.pack("HHHH", term.ROWS, term.COLS, 0, 0))
        os.set_blocking(self._fd, False)
        return self

    def _ttyrec_frame(self, data):
        sec = int(time.time())
        usec = int((time.time() % 1) * 1e6)
        self._ttyrec.write(struct.pack("<III", sec, usec, len(data)))
        self._ttyrec.write(data)

    def read(self, timeout):
        """Read available PTY output for up to `timeout` seconds.

        Returns True if any bytes were read.  Raises SessionDead when the
        process is gone.
        """
        if self.dead:
            raise SessionDead()
        try:
            r, _, _ = select.select([self._fd], [], [], timeout)
        except OSError:
            self.dead = True
            raise SessionDead()
        if not r:
            if self._poll_exit():
                raise SessionDead()
            return False
        try:
            data = os.read(self._fd, 65536)
        except OSError:
            self.dead = True
            raise SessionDead()
        if not data:
            self.dead = True
            raise SessionDead()
        self._ttyrec_frame(data)
        self.terminal.feed(data)
        return True

    def write(self, data):
        if self.dead:
            raise SessionDead()
        try:
            os.write(self._fd, data)
        except OSError:
            self.dead = True
            raise SessionDead()

    def _poll_exit(self):
        if self._pid is None:
            return False
        try:
            pid, status = os.waitpid(self._pid, os.WNOHANG)
        except ChildProcessError:
            self.dead = True
            return True
        if pid == self._pid:
            self.exitcode = os.waitstatus_to_exitcode(status)
            self.dead = True
            self.close()
            return True
        return False

    def close(self):
        if self._ttyrec:
            try:
                self._ttyrec.close()
            except OSError:
                pass
            self._ttyrec = None
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
        if self._pid is not None and not self.dead:
            try:
                os.kill(self._pid, signal.SIGKILL)
            except OSError:
                pass
            try:
                os.waitpid(self._pid, 0)
            except ChildProcessError:
                pass

    def kill(self):
        self.close()
