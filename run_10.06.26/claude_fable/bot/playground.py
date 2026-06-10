"""Per-game playground directories so parallel NetHack games don't fight over locks."""
import os
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NHDIR = os.path.join(BASE, "nh370", "games", "lib", "nethackdir")
NHBIN = os.path.join(NHDIR, "nethack")
RCFILE = os.path.join(BASE, "config", "nethackrc")

WRITABLE = {"perm", "record", "logfile", "xlogfile", "paniclog", "livelog"}


def make_playground(path):
    """Create a playground at `path` with symlinks to the read-only game data."""
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(os.path.join(path, "save"))
    for name in os.listdir(NHDIR):
        if name in ("save", "nethack", "recover"):
            continue
        src = os.path.join(NHDIR, name)
        dst = os.path.join(path, name)
        if name in WRITABLE:
            continue
        os.symlink(src, dst)
    for name in WRITABLE:
        with open(os.path.join(path, name), "w"):
            pass
    return path


def nethack_argv_env(playground, user="Bot"):
    argv = [NHBIN, "-d", playground, "-u", user]
    env = {
        "HACKDIR": playground,
        "NETHACKOPTIONS": "@" + RCFILE,
        "TERM": "xterm",
        "HOME": playground,
    }
    return argv, env
