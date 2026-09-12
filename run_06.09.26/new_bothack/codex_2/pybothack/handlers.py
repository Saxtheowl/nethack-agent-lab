"""Port of bothack.handlers."""
from .delegator import Handler
from .dungeon import update_at_player
from .util import PRIORITY_TOP


def register_handler(bh, *args):
    bh.delegator.send_register(*args)
    return bh


def deregister_handler(bh, handler):
    bh.delegator.send_deregister(handler)
    return bh


def replace_handler(bh, old, new):
    bh.delegator.send_switch(old, new)
    return bh


def update_before_action(bh, f, *args):
    """Before the next action is chosen, apply f to the game state."""
    h = Handler()

    def about_to_choose(_game):
        bh.game.swap(f, *args)
        deregister_handler(bh, h)
    h.about_to_choose = about_to_choose
    return register_handler(bh, PRIORITY_TOP, h)


def update_on_known_position(bh, f, *args):
    """When the player position on the map is known, apply f to the game."""
    h = Handler()

    def fire(_x):
        bh.game.swap(f, *args)
        deregister_handler(bh, h)
    h.about_to_choose = fire
    h.know_position = fire
    return register_handler(bh, PRIORITY_TOP, h)


def update_at_player_when_known(bh, update_fn, *args):
    return update_on_known_position(
        bh, lambda game: update_at_player(game, update_fn, *args))
