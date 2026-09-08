"""Ordered event delivery and action lifecycle from bothack.clj/handlers.clj.

GPL-2.0, 2026-09-07. This runtime contains no substitute playing strategy.
Unported action handlers fail before keyboard dispatch instead of silently
pretending to maintain the world model.
"""
from collections import deque
from copy import deepcopy
from types import FunctionType
from .actions import action, Responses
from .defaults import PRIORITY_TOP, PRIORITY_BOTTOM
from .delegator import Delegator
from .protocols import dispatch
from .game import new_game, action_kind, action_field
from . import dungeon as d
from .level import pos
from .state import truth, assoc_in, update_in, dissoc
from .itemid import appearance_of


class Runtime:
    def __init__(self, writer, game=None):
        self.game = new_game() if game is None else game
        self.queue = deque()
        self.failure = None
        self.delegator = Delegator(self._write)
        self.writer = writer
        self.lifecycle = ActionLifecycle(self)
        self.delegator.register(self.lifecycle, PRIORITY_BOTTOM)

    def _write(self, command):
        if self.failure is not None:
            raise self.failure
        self.writer(command)

    def mutate(self, function, *args):
        self.game = function(self.game, *args)
        return self.game

    def send(self, name, *args):
        self.queue.append((name, *args))

    def later(self, function):
        self.queue.append(function)

    def register(self, handler, priority=0):
        self.later(lambda: self.delegator.register(handler, priority))
        return self

    def deregister(self, handler):
        self.later(lambda: self.delegator.deregister(handler))
        return self

    def drain(self):
        while self.queue:
            call = self.queue.popleft()
            if isinstance(call, FunctionType):
                call()
            else:
                dispatch(self.delegator, call)
            if self.failure is not None:
                raise self.failure

    def update_before_action(self, function, *args):
        context = self
        class Once:
            def about_to_choose(self, game):
                context.mutate(function, *args)
                context.deregister(self)
        return self.register(Once(), PRIORITY_TOP)

    def update_on_known_position(self, function, *args):
        context = self
        class Once:
            def about_to_choose(self, frame_or_game):
                context.mutate(function, *args)
                context.deregister(self)
            know_position = about_to_choose
        return self.register(Once(), PRIORITY_TOP)

    def update_at_player_when_known(self, function, *args):
        return self.update_on_known_position(d.update_at_player, function, *args)

    def update_tile(self):
        return self.update_at_player_when_known(lambda tile: tile | {'new-items': True})

    def _request_action(self, kind, reason):
        context = self
        class Once:
            def choose_action(self, game):
                context.deregister(self)
                if action_kind(game.get('last-action*')) != kind:
                    return action(kind).with_fields(reason=[reason])
        return self.register(Once(), PRIORITY_TOP - 1)

    def update_inventory(self):
        return self._request_action('inventory', 'requested inventory update')

    def update_discoveries(self):
        return self._request_action('discoveries', 'discoveries update')

    def change_identification(self, method, *args):
        db = deepcopy(self.game['discoveries'])
        getattr(db, method)(*args)
        self.game = self.game | {'discoveries': db}
        return self.game

    def possible_autoid(self, slot, no_mark=False):
        item = self.game['player']['inventory'].get(slot)
        if item is not None and len(self.game['discoveries'].possible_ids(item)) != 1:
            self.update_discoveries()
            if not no_mark:
                context = self
                class Observe:
                    def about_to_choose(self, game):
                        if action_kind(game.get('last-action*')) == 'discoveries':
                            context.deregister(self)
                            if len(game['discoveries'].possible_ids(item)) != 1:
                                context.change_identification('observe_property', appearance_of(item), 'autoid', False)
                return self.register(Observe())

    def mark_use(self, slot):
        if not {'conf', 'stun', 'hallu', 'blind'}.intersection(self.game['player'].get('state') or ()):
            item = self.game['player']['inventory'].get(slot)
            self.game = self.game | {'tried': set(self.game['tried']) | {appearance_of(item)}}
        return self.game

    def identify_slot(self, slot, identity):
        return self.change_identification('discover', appearance_of(self.game['player']['inventory'][slot]), identity)


class ActionLifecycle:
    def __init__(self, context):
        self.context = context
        self.handlers = []

    def action_chosen(self, selected):
        context = self.context
        try:
            for old in self.handlers:
                context.deregister(old)
            self.handlers = []
            handler = selected.handler(context)
            if truth(handler):
                context.register(handler, PRIORITY_TOP)
                self.handlers.append(handler)
            for priority, handler in selected.handlers:
                if isinstance(handler, FunctionType):
                    handler = handler(context)
                if truth(handler):
                    context.register(handler, priority)
                    self.handlers.append(handler)
            previous = deepcopy(dissoc(context.game, 'last-state'))
            updated = context.game | {'last-position': pos(context.game['player']),
                       'last-action*': selected, 'last-state': previous}
            if selected.kind not in {'call', 'name', 'discoveries', 'inventory', 'look', 'farlook'}:
                updated['last-path'] = action_field(selected, 'path', updated.get('last-path'))
                updated['last-action'] = selected
            context.game = updated
        except Exception as error:
            context.failure = error
            raise
