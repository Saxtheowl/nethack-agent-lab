"""PTY session driving a NetHack 3.7 process, with a pyte screen emulation."""
import fcntl
import os
import select
import signal
import struct
import subprocess
import termios
import time

import pyte


class TtySession:
    def __init__(self, argv, env=None, cwd=None, cols=80, rows=24, record=None):
        self.cols, self.rows = cols, rows
        self.record_f = open(record, "wb") if record else None
        master, slave = os.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        full_env = dict(os.environ)
        full_env.update(env or {})
        full_env.setdefault("TERM", "xterm")
        full_env["LINES"] = str(rows)
        full_env["COLUMNS"] = str(cols)

        def _preexec():
            os.setsid()
            fcntl.ioctl(0, termios.TIOCSCTTY, 0)

        self.proc = subprocess.Popen(
            argv,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env=full_env,
            cwd=cwd,
            preexec_fn=_preexec,
            close_fds=True,
        )
        os.close(slave)
        self.fd = master
        self.screen = pyte.Screen(cols, rows)
        self.stream = pyte.ByteStream(self.screen)

    def alive(self):
        return self.proc.poll() is None

    def send(self, data):
        if isinstance(data, str):
            data = data.encode("latin-1")
        os.write(self.fd, data)

    def _read_once(self, timeout):
        """Read whatever is available within timeout. Returns bytes read (0 if none)."""
        try:
            r, _, _ = select.select([self.fd], [], [], timeout)
        except (OSError, ValueError):
            return 0
        if not r:
            return 0
        try:
            data = os.read(self.fd, 65536)
        except OSError:
            return 0
        if not data:
            return 0
        if self.record_f:
            now = time.time()
            sec, usec = int(now), int((now % 1) * 1e6)
            self.record_f.write(struct.pack("<III", sec, usec, len(data)) + data)
        self.stream.feed(data)
        return len(data)

    def settle(self, quiet=0.05, total=3.0):
        """Read output until the stream is quiet for `quiet` seconds (or `total` elapsed)."""
        deadline = time.time() + total
        got_any = False
        while time.time() < deadline:
            n = self._read_once(quiet)
            if n:
                got_any = True
            else:
                break
        return got_any

    def lines(self):
        return [self.screen.display[i] for i in range(self.rows)]

    def char_at(self, x, y):
        """Return (char, fg, bold) at column x, row y."""
        c = self.screen.buffer[y][x]
        return c.data, c.fg, c.bold

    def cursor(self):
        return self.screen.cursor.x, self.screen.cursor.y

    def close(self):
        if self.alive():
            try:
                self.proc.send_signal(signal.SIGHUP)
                self.proc.wait(timeout=3)
            except Exception:
                self.proc.kill()
                try:
                    self.proc.wait(timeout=3)
                except Exception:
                    pass
        try:
            os.close(self.fd)
        except OSError:
            pass
        if self.record_f:
            try:
                self.record_f.close()
            except OSError:
                pass
