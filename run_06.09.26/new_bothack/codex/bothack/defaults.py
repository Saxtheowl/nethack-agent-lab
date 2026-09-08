"""Fallback prompt responses from bothack.clj/prompt-escape (GPL-2.0).

Translated 2026-09-07. Register at PRIORITY_BOTTOM, after the bot's decisions.
This is the original fallback policy, not an autonomous playing strategy.
"""
from copy import deepcopy

PRIORITY_TOP = -(2 ** 31) - 1
PRIORITY_BOTTOM = 2 ** 31

RESPONSES = {
    'enter_gehennom': True, 'still_climb': True, 'which_finger': 'l',
    'pay_damage': True, 'lift_burden': True, 'force_god': True,
    'seduced_puton': False, 'seduced_remove': False, 'stop_eating': True,
    'enhance_without_practice': False, 'dump_core': 'q', 'do_teleport': True,
    'really_attack': False, 'create_what_monster': '\x1b', 'identify_what': {','},
    'make_wish': 'nothing', 'genocide_class': 'none', 'genocide_monster': 'none',
    'charge_what': '', 'who_are_you': '', 'sell_it': '', 'eat_what': '',
    'offer_how_much': '', 'lock_it': '', 'unlock_it': '', 'force_lock': '',
    'apply_what': '', 'teleport_where': '', 'leveltele': '', 'dry_fountain': '',
    'die': '', 'keep_save': 'y', 'what_name': '',
}


class DefaultResponses:
    def __getattr__(self, name):
        if name not in RESPONSES:
            raise AttributeError(name)
        return lambda *args: deepcopy(RESPONSES[name])
