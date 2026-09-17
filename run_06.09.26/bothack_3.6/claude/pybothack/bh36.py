"""Framework instance for NetHack 3.6.7 through the "bot" window port.

Same handler registration as bothack.new_bh, minus everything that exists only
to talk to a terminal (interface, terminal emulator, scraper, idle watchdog).
"""
import logging

from .actions import (call_id_handler, examine_handler, mark_recharge_handler,
                      update_discoveries, update_inventory, wish_id_handler)
from .atom import Atom
from .bothack import BotHack, _actions_handler, _prompt_escape, _start_bot
from .delegator import Delegator, Handler
from .game import game_handler, itemid_handler, new_game, set_race_role_handler
from .handlers import register_handler
from .pathing import reset_exploration
from .sokoban import soko_handler
from .tracker import death_tracker
from .util import PRIORITY_BOTTOM, PRIORITY_TOP

log = logging.getLogger('bothack.bh36')


def new_bh36(config, rng=None):
    delegator = Delegator(writer=lambda keys: None)
    game = Atom(new_game(rng))
    bh = BotHack(config, delegator, None, None, Atom(None), game)

    update_inventory(bh)
    update_discoveries(bh)
    register_handler(bh, PRIORITY_TOP - 1, game_handler(bh))

    def full_frame(_frame):
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

    def ended():
        bh._stop = True

    def started():
        _start_bot(bh)
    register_handler(bh, Handler(ended=ended, started=started))
    return bh
