"""Runner for the Python BotHack port."""
import argparse
import faulthandler
import logging
import time
import os
import random
import sys
import threading
import time

from .bothack import new_bh, run, start, stop, unpause, _load_config
from .action import typekw
from .delegator import Handler
from .handlers import deregister_handler, register_handler
from .util import ESC, PRIORITY_TOP, PRIORITY_BOTTOM

CTRL_R = chr(18)          # (r) "redraw" = (w (ctrl \r))


def _quit(bh):
    """(defn- q [] (w (str esc esc esc esc "#quit\nyq")) (System/exit 0))

    The `System/exit` matters, and not only for tidiness: `quit-when-stuck` is a
    `choose-action` handler, so if it *returns* the delegator keeps walking its
    handler list, finds no answer, and raises "No handler responded to prompt of
    choose_action".  The original never returns, so that never happens.  Seen for
    real on the deepest game so far - Dlvl 28, 6.9M points - which ended on that
    exception instead of a clean quit.

    From a background thread (quit-when-idle) raising SystemExit would only end
    that thread, so there it just stops the reader loop, which is what the JVM's
    exit accomplishes for the whole process.
    """
    bh.delegator.write(ESC * 4 + "#quit\nyq")
    bh._stop = True
    if threading.current_thread() is threading.main_thread():
        raise SystemExit(0)


_LAST_ACTION = [0.0]

#: quit-when-idle timings, in seconds (see _quit_when_idle)
IDLE_PERIOD = 3 * 60 - 50
IDLE_GRACE = 50


def _quit_when_idle(bh):
    """(quit-when-idle) - a background thread that unsticks, then gives up.

    ```clojure
    (future (while true
              (Thread/sleep (- (* 3 60 1000) 50000))
              (when-not (:inhibited @(:delegator a))
                (if-not @chosen
                  (do (log/warn "attempting to unstuck")
                      (w "#") (unpause a) (Thread/sleep 50000)
                      (when-not @chosen (log/error "3+ min idle - quitting") (q)))
                  (reset! chosen false)))))
    ```

    This is the only thing in the framework that recovers from a *scraper*
    deadlock, as opposed to an action-level one: `quit-when-looping` and
    `quit-when-stuck` are `choose-action` handlers, and a bot waiting on a
    prompt it cannot classify never reaches `choose-action` at all.

    Found missing by playing real games: the bot wielded a pick-axe, applied it,
    and NetHack asked "In what direction do you want to dig? [ulnj>]".  Both
    implementations throw on a direction prompt reaching `choice-fn` (the
    original's own comment there says "should recover itself"), and *this* is
    what recovers it - by writing `#`, which NetHack answers, breaking the
    deadlock.  Without it the game sat until the reader's idle timeout with the
    bot alive at Dlvl 9.

    Like the other two, it is registered only when `:no-exit` is false.
    """
    chosen = [True]
    # (- (* 3 60 1000) 50000) ms, then (Thread/sleep 50000).  Module-level so a
    # test can shorten them: a recovery path nobody has ever seen fire is the
    # one that fails unattended.
    period = IDLE_PERIOD
    stop_wait = IDLE_GRACE

    def loop():
        while not bh._stop:
            time.sleep(period)
            if bh._stop:
                return
            if bh.delegator.inhibited:
                continue
            if chosen[0]:
                chosen[0] = False
                continue
            logging.warning("attempting to unstuck")
            try:
                # (do (log/warn "attempting to unstuck") (w "#") (unpause a) ...)
                #
                # `(unpause a)` takes an argument, so it is
                # `bothack.bothack/unpause` - which resets the scraper, clears
                # inhibition and writes ESC ESC ESC ESC - and it is called
                # UNCONDITIONALLY.  It is not the private REPL helper
                #   (defn- u "unpause" [] (r) (if (:inhibited ...) (unpause a)))
                # which takes none, adds a ctrl-R, and is never called from
                # here.  An earlier version of this port conflated the two: it
                # added the ctrl-R and made the unpause conditional on
                # inhibition, so in the ordinary (un-inhibited) case the four
                # ESCs were never sent.  Those ESCs are the whole recovery -
                # they cancel whatever prompt NetHack is holding.  Seventeen
                # real games were lost to this, the deepest at Dlvl 18: the
                # scraper sat in `lastmsg+action` waiting for a redraw, NetHack
                # sat waiting for input, and neither moved until this handler
                # gave up 50 s later.
                bh.delegator.write("#")
                unpause(bh)
            except Exception:                             # noqa: BLE001
                logging.exception("unstuck write failed")
            time.sleep(stop_wait)
            if not chosen[0] and not bh._stop:
                logging.error("3+ min idle - quitting")
                _quit(bh)
                return

    t = threading.Thread(target=loop, name="quit-when-idle", daemon=True)
    t.start()
    h = Handler()

    def action_chosen(_a):
        chosen[0] = True
    h.action_chosen = action_chosen
    return h


def init_ui(bh, verbose=False):
    config = bh.config
    if not config.get('no-exit'):
        register_handler(bh, PRIORITY_TOP - 1, _quit_when_idle(bh))
        actions_this_turn = [0]
        h_loop = Handler()

        def choose_action_loop(game):
            last = (game.get('last-state') or {}).get('turn')
            if game.get('turn') == last:
                actions_this_turn[0] += 1
            else:
                actions_this_turn[0] = 0
            if actions_this_turn[0] > 1000:
                logging.error("stuck: too many actions within one game turn "
                              "- quitting")
                _quit(bh)
            return None
        h_loop.choose_action = choose_action_loop
        register_handler(bh, PRIORITY_TOP - 1, h_loop)

        h_stuck = Handler()

        def choose_action_stuck(_game):
            logging.error("No action chosen - quitting")
            _quit(bh)
            return None
        h_stuck.choose_action = choose_action_stuck
        register_handler(bh, PRIORITY_BOTTOM + 1, h_stuck)

    h = Handler()

    def choose_action(game):
        if (game.get('turn') or 0) > 100 and config.get('quit-resumed'):
            logging.error("Resumed game with :quit-resumed - quitting")
            _quit(bh)
        deregister_handler(bh, h)
        return None
    h.choose_action = choose_action
    register_handler(bh, PRIORITY_TOP - 1, h)

    log = logging.getLogger('bothack.ui')

    def ended():
        log.info("Game ended")

    def started():
        log.info("Game started")

    def message(text):
        log.info("Topline message: %s", text)

    counter = [0]
    _LAST_ACTION[0] = time.time()

    def action_chosen(action):
        now = time.time()
        if _LAST_ACTION[0] and now - _LAST_ACTION[0] > 2.0:
            log.warning("slow decision: %.1fs before %s %s",
                        now - _LAST_ACTION[0], typekw(action),
                        (action.get('reason') or [])[:3])
        _LAST_ACTION[0] = now
        if typekw(action) == 'pray':
            log.warning("praying")
        counter[0] += 1
        if counter[0] % 100 == 0:
            log.info("handlers registered: %d", len(bh.delegator.handlers))
        log.info("Performing action: %s %s", typekw(action),
                 action.get('reason'))

    def botl(status):
        log.debug("new botl status: %s", status)

    def dlvl_changed(old, new):
        log.info("dlvl changed from %s to %s", old, new)

    ui = Handler(ended=ended, started=started, message=message,
                 action_chosen=action_chosen, botl=botl,
                 dlvl_changed=dlvl_changed)
    register_handler(bh, PRIORITY_TOP - 1, ui)
    if verbose:
        register_handler(bh, PRIORITY_TOP - 1,
                         Handler(redraw=lambda f: print(f)))
    return bh


def main(argv=None):
    ap = argparse.ArgumentParser(description="Python BotHack")
    ap.add_argument('config', nargs='?', default="config/shell-config.edn")
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--lcg', action='store_true',
                    help="use the comparison harness's LCG instead of "
                         "Python's RNG, so the port and the original "
                         "take the same random decisions")
    ap.add_argument('--max-seconds', type=float, default=None)
    ap.add_argument('--log', default='INFO')
    ap.add_argument('--logfile', default=None)
    ap.add_argument('--ttyrec', default=None)
    ap.add_argument('--verbose-frames', action='store_true')
    ap.add_argument('--watchdog', type=float, default=None,
                    help="dump a traceback if a single step takes longer than "
                         "this many seconds (debugging aid)")
    ap.add_argument('--idle-timeout', type=float, default=None,
                    help="give up if the game sends nothing for this many "
                         "seconds.  Off by default and absent from the "
                         "original: it ends the run while the bot may only be "
                         "thinking, and it raced quit-when-idle, which needs up "
                         "to 310 s to react.  Use it for comparison runs, where "
                         ":no-exit has disabled the recovery handlers.")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log.upper()),
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        filename=args.logfile)

    if args.watchdog:
        faulthandler.enable()
    config = _load_config(args.config)
    if args.ttyrec:
        config['ttyrec'] = True
        config['ttyrec-path'] = args.ttyrec
    if args.lcg:
        from .util import LCG
        rng = LCG(args.seed if args.seed is not None else 12345)
    else:
        rng = random.Random(args.seed) if args.seed is not None else \
            random.Random()
    bh = new_bh(config=config, rng=rng)
    init_ui(bh, args.verbose_frames)
    if args.watchdog:
        import threading

        def _watch():
            while True:
                time.sleep(5)
                idle = time.time() - _LAST_ACTION[0]
                if idle > args.watchdog:
                    sys.stderr.write("\n=== no action for %.0fs, stack:\n"
                                     % idle)
                    faulthandler.dump_traceback()
                    # The stack says *where* it is waiting; these say *why* -
                    # which scraper state it settled in and what the frames
                    # looked like on the way there.
                    from .scraper import recent_transitions
                    sys.stderr.write("--- last scraper transitions:\n")
                    for line in recent_transitions():
                        sys.stderr.write("    %s\n" % line)
                    sys.stderr.flush()
                    _LAST_ACTION[0] = time.time()
        threading.Thread(target=_watch, daemon=True).start()
    try:
        start(bh)
        run(bh, max_seconds=args.max_seconds,
            idle_timeout=args.idle_timeout)
    finally:
        stop(bh)
    game = bh.game.deref()
    logging.info("final state: dlvl=%s turn=%s score=%s hp=%s",
                 game.get('dlvl'), game.get('turn'), game.get('score'),
                 (game.get('player') or {}).get('hp'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
