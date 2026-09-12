#!/usr/bin/env python3
"""Does quit-when-idle actually fire?

It is the only thing in the framework that recovers from a *scraper* deadlock:
`quit-when-looping` and `quit-when-stuck` are `choose-action` handlers, and a bot
waiting on a prompt it cannot classify never reaches `choose-action`.  A real
game hit exactly that (an unclassifiable "In what direction do you want to dig?")
and sat there until the reader's idle timeout.

So this drives the thread with the timings shortened and checks what the
original actually does, which is more than writing `#`:

    (w "#") (unpause a) (Thread/sleep 50000) (when-not @chosen ... (q))

`(unpause a)` is `bothack.bothack/unpause` - it takes an argument, unlike the
private REPL helper `u` - and it is called unconditionally.  It resets the
scraper, clears inhibition, and writes ESC ESC ESC ESC.  Those ESCs are the
recovery: they cancel whatever prompt NetHack is holding.

An earlier version of this test asserted the opposite - that a ctrl-R is sent
and that an un-inhibited bot is *not* unpaused - because the port had conflated
`unpause` with `u`.  The test passed and seventeen real games were still lost to
the deadlock, so the assertions below are written against the Clojure, not
against the port.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pybothack import main as M                                  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  ok   %s" % name)
    else:
        print("  FAIL %s %s" % (name, detail))
        FAILURES.append(name)


class FakeDelegator(object):
    def __init__(self):
        self.writes = []
        self.inhibited = False
        self.unpaused = False

    def write(self, s):
        self.writes.append(s)

    def set_inhibition(self, v):
        if v is False:
            self.unpaused = True
        self.inhibited = v


class FakeScraper(object):
    def __init__(self):
        self.resets = 0

    def reset(self, _frame):
        self.resets += 1


class FakeBh(object):
    def __init__(self):
        self.delegator = FakeDelegator()
        self._stop = False
        self.config = {}
        self.scraper = FakeScraper()


def run_case(name, keep_choosing, expect_unstuck, expect_quit):
    M.IDLE_PERIOD, M.IDLE_GRACE = 0.05, 0.05
    bh = FakeBh()
    h = M._quit_when_idle(bh)
    deadline = time.time() + 3.0
    while time.time() < deadline:
        if keep_choosing:
            h.action_chosen(None)
        if bh._stop:
            break
        time.sleep(0.01)
    unstuck = "#" in bh.delegator.writes
    redraw = M.CTRL_R in bh.delegator.writes
    escapes = any(w == "\x1b" * 4 for w in bh.delegator.writes)
    quit_sent = any("#quit" in w for w in bh.delegator.writes)
    bh._stop = True
    time.sleep(0.2)
    check("%s: unstuck write" % name, unstuck == expect_unstuck,
          "writes=%r" % (bh.delegator.writes[:4],))
    check("%s: no ctrl-R (that belongs to the REPL helper, not this)" % name,
          not redraw, "writes=%r" % (bh.delegator.writes[:4],))
    check("%s: four ESCs written" % name, escapes == expect_unstuck,
          "writes=%r" % (bh.delegator.writes[:4],))
    check("%s: unpauses even though never inhibited" % name,
          bh.delegator.unpaused == expect_unstuck,
          "unpaused=%r" % (bh.delegator.unpaused,))
    check("%s: scraper reset" % name,
          (bh.scraper.resets > 0) == expect_unstuck,
          "resets=%d" % bh.scraper.resets)
    check("%s: quit" % name, quit_sent == expect_quit,
          "writes=%r" % (bh.delegator.writes[:4],))


def main():
    print("quit-when-idle")
    run_case("idle bot", keep_choosing=False,
             expect_unstuck=True, expect_quit=True)
    run_case("busy bot", keep_choosing=True,
             expect_unstuck=False, expect_quit=False)
    print()
    if FAILURES:
        print("%d FAILED: %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("quit-when-idle fires when idle and stays out of the way when not")
    return 0


if __name__ == '__main__':
    sys.exit(main())
