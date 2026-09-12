#!/usr/bin/env python3
"""A pty tap: runs NetHack in a pty, relays it to stdin/stdout and records
both directions.

It writes the game's output in chunks of at most 256 bytes and yields the CPU
after every chunk, so that the bot's reader (JTA reads at most 256 bytes per
read, and so does the Python port) sees exactly the chunk boundaries recorded
here.  That makes the recording replayable byte-for-byte into either bot.

Record format (little endian): <dir:1><len:4><data> where dir is
b'O' (game -> bot) or b'I' (bot -> game).
"""
import os
import pty
import select
import struct
import sys
import termios
import time
import tty

CHUNK = 256


def _blocked_on_read(pid):
    """Is the child blocked in read(), i.e. has the game finished answering
    and gone back to waiting for the bot?

    This replaces waiting a fixed settle time: it is both ~100x faster and
    *more* deterministic, because the group boundary no longer depends on how
    the scheduler spaced NetHack's writes.  Returns None when /proc is not
    usable, so the caller can fall back to the timeout.
    """
    try:
        with open('/proc/%d/syscall' % pid) as f:
            parts = f.read().split()
    except (IOError, OSError):
        return None
    if not parts:
        return None
    if parts[0] in ('running', '-1'):
        return False
    try:
        return int(parts[0]) == 0          # __NR_read on x86_64
    except ValueError:
        return None


def main():
    logpath = os.environ.get('PTY_TAP_LOG', 'pty_tap.log')
    cmd = sys.argv[1:]
    if not cmd:
        sys.exit("usage: pty_tap.py <command> [args...]")
    settle = float(os.environ.get('PTY_TAP_SETTLE', '0') or 0)
    # How long to wait after handing the bot a 256-byte piece.  The bots read
    # at most 256 bytes per read and react to each read as one frame, so if a
    # second piece lands before the bot has read the first, the two get
    # coalesced and the bot sees a different frame than a slower bot would.
    piece_delay = float(os.environ.get('PTY_TAP_PIECE_DELAY', '0.002') or 0.002)
    # Detect "the game is waiting for input" directly instead of waiting out
    # the settle window; PTY_TAP_IDLE=0 falls back to pure timing.
    use_idle = os.environ.get('PTY_TAP_IDLE', '1') != '0'
    log = open(logpath, 'wb', buffering=0)
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(cmd[0], cmd)
        os._exit(127)
    try:
        import fcntl
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 80, 0, 0))
    except Exception:
        pass
    stdin = sys.stdin.fileno()
    stdout = sys.stdout.fileno()
    # The outer terminal (the bot's pty) still has its line discipline in
    # cooked mode with echo on - without this the bot's own keystrokes are
    # echoed back onto the screen.
    saved = None
    try:
        saved = termios.tcgetattr(stdin)
        tty.setraw(stdin)
    except Exception:
        pass
    try:
        while True:
            r, _, _ = select.select([fd, stdin], [], [], 1.0)
            if fd in r:
                try:
                    data = os.read(fd, CHUNK if not settle else 65536)
                except OSError:
                    break
                if not data:
                    break
                if settle:
                    # Deterministic framing: keep reading until the game has
                    # been quiet for `settle` seconds, then emit the whole
                    # response in fixed 256-byte pieces.  Without this the
                    # chunk boundaries depend on process scheduling, so two
                    # bots playing the same game do not see the same frames -
                    # and the bots react to *frames*.
                    deadline = time.time() + settle
                    while True:
                        # Stop as soon as the bot writes its next key: that
                        # closes the group at an *interaction* boundary, so the
                        # framing is a function of the exchange rather than of
                        # how fast either bot happens to run.
                        r2, _, _ = select.select([fd, stdin], [], [],
                                                 0.001 if use_idle else settle)
                        if stdin in r2:
                            break
                        if fd in r2:
                            try:
                                more = os.read(fd, 65536)
                            except OSError:
                                more = b''
                            if not more:
                                break
                            data += more
                            deadline = time.time() + settle
                            continue
                        if use_idle:
                            idle = _blocked_on_read(pid)
                            if idle:
                                break
                            if idle is None:
                                use_idle = False     # /proc unusable
                            if time.time() < deadline:
                                continue
                        break
                    for i in range(0, len(data), CHUNK):
                        piece = data[i:i + CHUNK]
                        log.write(b'O' + struct.pack('<I', len(piece)) + piece)
                        os.write(stdout, piece)
                        time.sleep(piece_delay)
                else:
                    log.write(b'O' + struct.pack('<I', len(data)) + data)
                    os.write(stdout, data)
                    time.sleep(0.002)  # let the reader consume this chunk
            if stdin in r:
                try:
                    data = os.read(stdin, CHUNK)
                except OSError:
                    break
                if not data:
                    break
                log.write(b'I' + struct.pack('<I', len(data)) + data)
                os.write(fd, data)
    finally:
        if saved is not None:
            try:
                termios.tcsetattr(stdin, termios.TCSADRAIN, saved)
            except Exception:
                pass
        log.close()
        try:
            os.close(fd)
        except OSError:
            pass
        os.waitpid(pid, 0)


main()
