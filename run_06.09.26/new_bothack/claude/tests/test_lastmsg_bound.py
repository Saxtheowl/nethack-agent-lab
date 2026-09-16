#!/usr/bin/env python3
"""Does the lastmsg wait bound actually fire on the stall that happens?

The previous bound counted redraws *while in* `lastmsg+action` and was reset on
every pass through `lastmsg_get`.  The stall that actually occurs is the whole
protocol cycling - lastmsg_get -> lastmsg+action -> sink -> marked ->
lastmsg_clear -> lastmsg_get - so every lap cleared the counter and the bound
was unreachable.  Measured before this test existed: "lastmsg stuck" appeared
**zero** times in ~40 real games that contained 14 such stalls.

So this drives the exact recorded signature and asserts the bound fires.  A
safeguard nobody has watched fire is not a safeguard - that is the whole reason
this file exists.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pybothack import scraper as S                              # noqa: E402
from pybothack.frame import Frame as F                          # noqa: E402
from pybothack.position import Pos                               # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  ok   %s" % name)
    else:
        print("  FAIL %s %s" % (name, detail))
        FAILURES.append(name)


BOTL1 = ("Bot the Stripling        St:18 Dx:11 Co:19 In:8 Wi:11 Ch:9  "
         "Lawful S:1234  ")
BOTL2 = "Dlvl:5  $:198 HP:25(27) Pw:3(3) AC:6  Exp:2 T:679  "


def frame(top, x, y):
    """A real pybothack Frame with a drawn status line, so _status_drawn holds."""
    lines = [top.ljust(80)] + [" " * 80 for _ in range(21)]
    lines.append(BOTL1.ljust(80))
    lines.append(BOTL2.ljust(80))
    colors = [[None] * 80 for _ in range(24)]
    return F(lines, colors, Pos(x, y))


class FakeDelegator(object):
    def __init__(self):
        self.writes = []
        self.full_frames = 0
        self.messages = []

    def send_write(self, s):
        self.writes.append(s)

    def write(self, s):
        self.writes.append(s)

    def message(self, m):
        self.messages.append(m)

    def know_position(self, f):
        pass

    def full_frame(self, f):
        self.full_frames += 1

    def __getattr__(self, _n):
        return lambda *a, **k: None


def main():
    print("borne d'attente de lastmsg")

    # The recorded signature, from artifacts/pool_g (13 of 13 stalls):
    #     lastmsg_get     cursor=(59,20) topline=''      -> player=(59,20)
    #     lastmsg_action  cursor=(58,20) topline='# #'   -> player=(58,20)
    #     lastmsg_action  cursor=(59,20) topline='#'     -> waits for ever
    # Walked through the protocol's real route, not forced.
    S.LASTMSG_WAIT_SECONDS = 0.3          # keep the test quick
    d = FakeDelegator()
    st = S.new_scraper(d)

    def step(f, expect):
        nonlocal st
        r = st(f)
        if callable(r):
            st = r
        check("-> %s" % expect, getattr(st, '__name__', '') == expect,
              "etat=%r" % getattr(st, '__name__', st))

    step(frame("", 59, 20), 'marked')          # initial: status drawn -> ##'
    # `initial` writes "##'", so NetHack's topline reads "# #'" - the prompt's
    # own '#', then what was typed.  before-cursor? matches those four chars.
    step(frame("# #'", 4, 0), 'lastmsg_clear')
    step(frame("", 59, 20), 'lastmsg_get')     # lastmsg_clear: empty topline
    step(frame("# #", 59, 20), 'lastmsg_action')   # records player=(59,20)

    # a "# #" frame carrying a STALE cursor re-records player the wrong way
    r = st(frame("# #", 58, 20))
    check("le cadre '# #' obsolete empoisonne player", r is None)

    # now the stuck frame: topline '#', cursor != player
    stuck = frame("#", 59, 20)
    r = st(stuck)
    check("attend d'abord (pas de sortie immediate)", r is None,
          "retour=%r" % (getattr(r, '__name__', r),))

    # the bound must fire once the wall clock passes, even though the counter
    # is far below LASTMSG_WAIT_LIMIT and even if lastmsg_get ran in between
    time.sleep(0.35)
    before = d.full_frames
    r = st(stuck)
    check("la borne temporelle se declenche",
          getattr(r, '__name__', '') == 'sink' and d.full_frames == before + 1,
          "retour=%r full_frames=%d" % (getattr(r, '__name__', r), d.full_frames))

    print()
    if FAILURES:
        print("%d FAILED: %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("la borne d'attente de lastmsg se declenche sur la signature reelle")
    return 0


if __name__ == '__main__':
    sys.exit(main())
