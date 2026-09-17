"""The interface to NetHack.  Replaces bothack.jta (JTA telnet/SSH/shell):
a local pty for :shell, a socket for :telnet, paramiko-free raw SSH is not
supported (use :shell or :telnet).

The reader reproduces JTA's behaviour of reading at most 256 bytes per read
and emitting exactly one redraw per non-empty chunk.
"""
import errno
import os
import pty
import select
import signal
import socket
import struct
import time


class Ttyrec(object):
    """Ttyrec writer (same format as bothack.ttyrec)."""

    def __init__(self, path):
        self.f = open(path, 'wb')

    def write(self, data):
        ts = time.time()
        sec = int(ts)
        usec = int((ts - sec) * 1000000)
        self.f.write(struct.pack('<III', sec, usec, len(data)))
        self.f.write(data)
        self.f.flush()

    def close(self):
        try:
            self.f.close()
        except Exception:
            pass


class ShellInterface(object):
    """Runs NetHack in a local pty."""

    def __init__(self, command, env=None, cols=80, rows=24):
        self.command = command
        self.env = env
        self.cols = cols
        self.rows = rows
        self.pid = None
        self.fd = None

    def start(self):
        pid, fd = pty.fork()
        if pid == 0:
            try:
                if isinstance(self.command, str):
                    args = ['/bin/sh', '-c', self.command]
                    os.execve('/bin/sh', args, self.env or os.environ)
                else:
                    os.execve(self.command[0], self.command,
                              self.env or os.environ)
            finally:
                os._exit(127)
        self.pid = pid
        self.fd = fd
        try:
            import fcntl
            import termios
            fcntl.ioctl(fd, termios.TIOCSWINSZ,
                        struct.pack('HHHH', self.rows, self.cols, 0, 0))
        except Exception:
            pass
        return self

    def read(self, n=256):
        try:
            return os.read(self.fd, n)
        except OSError as e:
            if e.errno in (errno.EIO, errno.EBADF):
                return b''
            raise

    def write(self, data):
        if isinstance(data, str):
            data = data.encode('latin-1')
        os.write(self.fd, data)

    def wait_readable(self, timeout):
        r, _, _ = select.select([self.fd], [], [], timeout)
        return bool(r)

    def alive(self):
        if self.pid is None:
            return False
        try:
            pid, _ = os.waitpid(self.pid, os.WNOHANG)
            return pid == 0
        except OSError:
            return False

    def stop(self):
        if self.pid:
            try:
                os.kill(self.pid, signal.SIGTERM)
            except OSError:
                pass
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None


class TelnetInterface(object):
    """Minimal telnet client (enough for dgamelaunch servers)."""

    IAC, DONT, DO, WONT, WILL, SB, SE = 255, 254, 253, 252, 251, 250, 240
    TTYPE, NAWS, SGA, ECHO, BINARY = 24, 31, 3, 1, 0

    def __init__(self, host, port=23, cols=80, rows=24):
        self.host = host
        self.port = port
        self.cols = cols
        self.rows = rows
        self.sock = None
        self._buf = b''

    def start(self):
        self.sock = socket.create_connection((self.host, self.port))
        self.sock.setblocking(False)
        return self

    def _negotiate(self, data):
        """Handle telnet negotiation, return the payload bytes."""
        out = bytearray()
        i = 0
        while i < len(data):
            b = data[i]
            if b != self.IAC:
                out.append(b)
                i += 1
                continue
            if i + 1 >= len(data):
                break
            cmd = data[i + 1]
            if cmd in (self.DO, self.DONT, self.WILL, self.WONT):
                if i + 2 >= len(data):
                    break
                opt = data[i + 2]
                self._respond(cmd, opt)
                i += 3
            elif cmd == self.SB:
                j = data.find(bytes([self.IAC, self.SE]), i)
                if j < 0:
                    break
                sub = data[i + 2:j]
                if sub and sub[0] == self.TTYPE:
                    self.sock.sendall(bytes([self.IAC, self.SB, self.TTYPE, 0])
                                      + b'xterm'
                                      + bytes([self.IAC, self.SE]))
                i = j + 2
            elif cmd == self.IAC:
                out.append(self.IAC)
                i += 2
            else:
                i += 2
        return bytes(out)

    def _respond(self, cmd, opt):
        if cmd == self.DO:
            if opt in (self.TTYPE, self.NAWS, self.SGA, self.BINARY):
                self.sock.sendall(bytes([self.IAC, self.WILL, opt]))
                if opt == self.NAWS:
                    self.sock.sendall(bytes([self.IAC, self.SB, self.NAWS])
                                      + struct.pack('>HH', self.cols, self.rows)
                                      + bytes([self.IAC, self.SE]))
            else:
                self.sock.sendall(bytes([self.IAC, self.WONT, opt]))
        elif cmd == self.WILL:
            if opt in (self.ECHO, self.SGA, self.BINARY):
                self.sock.sendall(bytes([self.IAC, self.DO, opt]))
            else:
                self.sock.sendall(bytes([self.IAC, self.DONT, opt]))

    def read(self, n=256):
        try:
            data = self.sock.recv(n)
        except (BlockingIOError, socket.error):
            return b''
        if not data:
            return b''
        return self._negotiate(data)

    def write(self, data):
        if isinstance(data, str):
            data = data.encode('latin-1')
        self.sock.sendall(data.replace(b'\xff', b'\xff\xff'))

    def wait_readable(self, timeout):
        r, _, _ = select.select([self.sock], [], [], timeout)
        return bool(r)

    def alive(self):
        return self.sock is not None

    def stop(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
