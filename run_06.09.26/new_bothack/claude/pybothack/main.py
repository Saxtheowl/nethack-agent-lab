"""Runner for the Python BotHack port."""
import argparse
import faulthandler
import logging
import time
import os
import random
import sys
import time

from .bothack import new_bh, run, start, stop, _load_config
from .action import typekw
from .delegator import Handler
from .handlers import deregister_handler, register_handler
from .util import ESC, PRIORITY_TOP, PRIORITY_BOTTOM


def _quit(bh):
    bh.delegator.write(ESC * 4 + "#quit\nyq")
    bh._stop = True


_LAST_ACTION = [0.0]


def init_ui(bh, verbose=False):
    config = bh.config
    if not config.get('no-exit'):
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
                    sys.stderr.flush()
                    _LAST_ACTION[0] = time.time()
        threading.Thread(target=_watch, daemon=True).start()
    try:
        start(bh)
        run(bh, max_seconds=args.max_seconds)
    finally:
        stop(bh)
    game = bh.game.deref()
    logging.info("final state: dlvl=%s turn=%s score=%s hp=%s",
                 game.get('dlvl'), game.get('turn'), game.get('score'),
                 (game.get('player') or {}).get('hp'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
