"""Port of bothack.bothack - the framework instance and main loop."""
import ast
import logging
import os
import time

from .action import handler as action_handler, typekw
from .actions import (call_id_handler, examine_handler, mark_recharge_handler,
                      update_discoveries, update_inventory, wish_id_handler)
from .atom import Atom
from .clj import CljStr, assoc, dissoc
from .delegator import Delegator, Handler
from .game import game_handler, itemid_handler, new_game, set_race_role_handler
from .handlers import deregister_handler, register_handler, replace_handler
from .iface import ShellInterface, TelnetInterface, Ttyrec
from .pathing import reset_exploration
from .position import position
from .scraper import scraper_handler
from .sokoban import soko_handler
from .term import Terminal
from .tracker import death_tracker
from .util import (ESC, PRIORITY_BOTTOM, PRIORITY_TOP, config_get)

log = logging.getLogger('bothack')


class BotHack(object):
    def __init__(self, config, delegator, iface, terminal, scraper, game):
        self.config = config
        self.delegator = delegator
        self.iface = iface
        self.terminal = terminal
        self.scraper = scraper
        self.game = game
        self.ttyrec = None
        self._stop = False

    def register_handler(self, *args):
        return register_handler(self, *args)

    def deregister_handler(self, h):
        return deregister_handler(self, h)


def _load_config(fname):
    """Reads the EDN-ish config files of the original (a subset: keywords,
    strings, booleans)."""
    with open(fname) as f:
        txt = f.read()
    txt = txt.split(';')[0] if txt.strip().startswith(';') else txt
    res = {}
    for m in _config_entries(txt):
        res[m[0]] = m[1]
    return res


def _config_entries(txt):
    import re
    body = txt[txt.index('{') + 1:txt.rindex('}')]
    out = []
    for line in body.splitlines():
        line = line.split(';')[0].strip()
        if not line:
            continue
        m = re.match(r'^:([\w-]+)\s+(.*)$', line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val.startswith('"'):
            v = ast.literal_eval(val)
        elif val == 'true':
            v = True
        elif val == 'false':
            v = False
        elif val.startswith(':'):
            v = val[1:]
        else:
            try:
                v = int(val)
            except ValueError:
                v = val
        out.append((key, v))
    return out


def _start_bot(bh):
    bot = bh.config.get('bot')
    if not bot:
        raise RuntimeError("Missing :bot in configuration.")
    mod = __import__('pybothack.bots.' + bot.replace('-', '_'),
                     fromlist=['init'])
    return mod.init(bh)


def _start_menubot(bh):
    menubot = bh.config.get('menubot')
    if menubot:
        mod = __import__('pybothack.bots.' + menubot.replace('-', '_'),
                         fromlist=['init'])
        mod.init(bh)
        return True
    return False


def _actions_handler(bh):
    action_handlers = [set()]

    def action_chosen(action):
        for h in action_handlers[0]:
            deregister_handler(bh, h)
        action_handlers[0] = set()
        h = action_handler(action, bh)
        if h is not None:
            register_handler(bh, PRIORITY_TOP, h)
            action_handlers[0].add(h)
        for p, hh in (action.get('handlers') or ()):
            h2 = hh(bh) if callable(hh) else hh
            if h2 is not None:
                register_handler(bh, p, h2)
                action_handlers[0].add(h2)
        bh.game.swap(lambda g: assoc(
            g, 'last-position', position(g['player']),
            'last-action*', action,
            'last-state', dissoc(g, 'last-state')))
        if typekw(action) not in ('call', 'name', 'discoveries', 'inventory',
                                  'look', 'farlook'):
            bh.game.swap(lambda g: assoc(
                g, 'last-path', action.get('path', g.get('last-path')),
                'last-action', action))
    return Handler(action_chosen=action_chosen)


def pause(bh):
    bh.delegator.set_inhibition(True)
    log.info("pausing")
    return bh


def unpause(bh):
    log.info("unpaused")
    bh.scraper.reset(None)
    bh.delegator.set_inhibition(False)
    bh.delegator.write(ESC * 4)
    return bh


def _prompt_escape():
    """Default responses for unhandled prompts."""
    def warn_identify(_o):
        # `#{","}` - a Clojure String, not a Character (see clj.CljStr).  A
        # single-element set has no observable order, but marking it keeps the
        # rule "the producing site says which it is" true everywhere.
        log.warning("default handler identifying anything")
        return {CljStr(",")}

    def warn_wish(_p):
        log.warning("default handler wishing for nothing")
        return "nothing"

    def warn_geno_class(_p):
        log.warning("default handler genociding class none")
        return "none"

    def warn_geno(_p):
        log.warning("default handler genociding none")
        return "none"

    return Handler(
        enter_gehennom=lambda _p: True,
        still_climb=lambda _p: True,
        which_finger=lambda _p: 'l',
        pay_damage=lambda _p: True,
        lift_burden=lambda _b, _i: True,
        force_god=lambda _p: True,
        seduced_puton=lambda _p: False,
        seduced_remove=lambda _p: False,
        stop_eating=lambda _p: True,
        enhance_without_practice=lambda _p: False,
        dump_core=lambda _p: "q",
        do_teleport=lambda _p: True,
        really_attack=lambda _p: False,
        create_what_monster=lambda _p: ESC,
        identify_what=warn_identify,
        make_wish=warn_wish,
        genocide_class=warn_geno_class,
        genocide_monster=warn_geno,
        charge_what=lambda _p: "",
        who_are_you=lambda _p: "",
        sell_it=lambda _o, _w: "",
        eat_what=lambda _p: "",
        offer_how_much=lambda _p: "",
        lock_it=lambda _p: "",
        unlock_it=lambda _p: "",
        force_lock=lambda _p: "",
        apply_what=lambda _p: "",
        teleport_where=lambda: "",
        leveltele=lambda _p: "",
        dry_fountain=lambda _p: "",
        die=lambda _p: (log.warning("died"), "")[1],
        keep_save=lambda _p: "y",
        what_name=lambda _p: "")


def new_bh(fname="config/shell-config.edn", config=None, rng=None):
    config = config if config is not None else _load_config(fname)
    delegator = Delegator()
    iface_kind = config_get(config, 'interface')
    if iface_kind == 'shell':
        iface = ShellInterface(config_get(config, 'nh-command'),
                               env=config.get('env'))
    elif iface_kind == 'telnet':
        iface = TelnetInterface(config_get(config, 'host'),
                                config_get(config, 'port', 23))
    else:
        raise ValueError("Invalid :interface configuration")
    terminal = Terminal()
    scraper_ref = Atom(None)
    game = Atom(new_game(rng))
    bh = BotHack(config, delegator, iface, terminal, scraper_ref, game)
    delegator.set_writer(iface.write)
    scraper = scraper_handler(scraper_ref, delegator)

    # registration order as in the original's new-bh; which of the two
    # answers first is a priority-map tie there (hash order of reify objects)
    # and differs from run to run - see docs/TESTS.md
    update_inventory(bh)
    update_discoveries(bh)
    register_handler(bh, PRIORITY_TOP - 1, game_handler(bh))

    def full_frame(_frame):
        # (send delegator #(about-to-choose % @game)) - the original
        # dereferences the game when the queued send *runs*, so the action is
        # chosen from the state as updated by the about-to-choose handlers
        delegator._send(
            lambda: delegator._invoke_event('about_to_choose', game.deref()))
        delegator._send(
            lambda: delegator._respond_action('choose_action', game.deref()))
    register_handler(bh, PRIORITY_BOTTOM + 1, Handler(full_frame=full_frame))
    register_handler(bh, PRIORITY_TOP, set_race_role_handler(bh))
    register_handler(bh, PRIORITY_BOTTOM, _actions_handler(bh))
    register_handler(bh, PRIORITY_TOP, examine_handler(bh))
    register_handler(bh, PRIORITY_TOP, call_id_handler(bh))
    register_handler(bh, PRIORITY_TOP, mark_recharge_handler(bh))
    register_handler(bh, PRIORITY_BOTTOM, _prompt_escape())
    register_handler(bh, PRIORITY_TOP, soko_handler(bh))
    register_handler(bh, PRIORITY_TOP, wish_id_handler(bh))
    register_handler(bh, PRIORITY_TOP, itemid_handler(bh))
    register_handler(bh, PRIORITY_TOP, reset_exploration(bh))
    register_handler(bh, PRIORITY_TOP, death_tracker(bh))

    pause_h = Handler()

    def full_frame_pause(_f):
        if config.get('start-paused'):
            pause(bh)
        deregister_handler(bh, pause_h)
    pause_h.full_frame = full_frame_pause
    register_handler(bh, PRIORITY_BOTTOM, pause_h)

    def ended():
        deregister_handler(bh, scraper)
        bh._stop = True

    def started():
        register_handler(bh, PRIORITY_TOP - 1, scraper)
        _start_bot(bh)
    register_handler(bh, Handler(ended=ended, started=started))
    bh._scraper_handler = scraper
    return bh


def start(bh):
    log.info("BotHack instance started")
    if bh.config.get('ttyrec'):
        path = bh.config.get('ttyrec-path') or ("%d.ttyrec" % time.time())
        bh.ttyrec = Ttyrec(path)
    bh.iface.start()
    if not _start_menubot(bh):
        bh.delegator.started()
    bh.delegator.drain()
    bh.delegator.online()
    return bh


def stop(bh):
    bh.iface.stop()
    bh.scraper.reset(None)
    if bh.ttyrec:
        bh.ttyrec.close()
    log.info("BotHack instance stopped")
    return bh


def run(bh, max_seconds=None, idle_timeout=None):
    """The reader loop - JTA reads at most 256 bytes at a time and emits one
    redraw per non-empty chunk.

    `idle_timeout` has **no counterpart in the original**: JTA's reader simply
    blocks.  It was added as a harness safety net, and it defaults to off,
    because a timeout here ends the whole run while the bot may only be
    thinking - and it raced the framework's own recovery.  `quit-when-idle`
    notices an idle bot on a 130 s tick, so it can take up to 260 s to react and
    another 50 s before it gives up; a 180 s reader timeout always won that race
    and killed the game first.  Seven of sixteen real games died that way, the
    best of them at Dlvl 15 with 66 778 points.

    Pass one explicitly for a comparison run, where the harness owns the process
    lifetime and `:no-exit true` has disabled the recovery handlers.
    """
    start_time = time.time()
    last_data = time.time()
    while not bh._stop:
        if max_seconds and time.time() - start_time > max_seconds:
            log.warning("time limit reached")
            break
        if not bh.iface.wait_readable(1.0):
            if idle_timeout is not None and \
                    time.time() - last_data > idle_timeout:
                log.error("idle timeout")
                break
            continue
        data = bh.iface.read(256)
        if not data:
            break
        last_data = time.time()
        if bh.ttyrec:
            bh.ttyrec.write(data)
        bh.terminal.feed(data)
        bh.delegator.redraw(bh.terminal.frame())
    return bh
