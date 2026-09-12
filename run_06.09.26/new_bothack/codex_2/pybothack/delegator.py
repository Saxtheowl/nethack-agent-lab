"""Port of bothack.delegator.

The delegator delegates event invocations to all registered handlers which
implement the given event, or to the first handler that implements a prompt.
For prompts it writes the response back to the terminal.  Handlers are invoked
in order of their priority (ties: registration order).
"""
import logging

from .position import to_position
from .util import VI_DIRECTIONS, ESC, PRIORITY_DEFAULT

log = logging.getLogger('bothack.delegator')

# ---------------------------------------------------------------- event names

EVENTS = [
    'online', 'offline', 'redraw', 'full_frame', 'know_position',
    'started', 'ended', 'message', 'botl', 'dlvl_changed',
    'about_to_choose', 'action_chosen', 'response_chosen',
    'inventory_list', 'message_lines', 'found_items',
]

# prompt name -> response transform kind
PROMPTS = {
    # location prompts
    'teleport_where': 'location', 'travel_where': 'location',
    'pay_whom': 'location',
    # single-letter choice prompts
    'choose_character': 'choice', 'apply_what': 'choice',
    'wield_what': 'choice', 'wear_what': 'choice', 'take_off_what': 'choice',
    'put_on_what': 'choice', 'remove_what': 'choice', 'drop_single': 'choice',
    'ready_what': 'choice', 'dump_core': 'choice', 'read_what': 'choice',
    'drink_what': 'choice', 'zap_what': 'choice', 'which_finger': 'choice',
    'eat_what': 'choice', 'sacrifice_what': 'choice', 'dip_what': 'choice',
    'dip_into_what': 'choice', 'throw_what': 'choice',
    'write_with_what': 'choice', 'name_what': 'choice',
    'charge_what': 'choice', 'rub_what': 'choice',
    # direction
    'what_direction': 'direction',
    # yes/no
    'really_attack': 'yesno', 'seduced_puton': 'yesno',
    'seduced_remove': 'yesno', 'enter_gehennom': 'yesno', 'force_god': 'yesno',
    'die': 'yesno', 'keep_save': 'yesno', 'dry_fountain': 'yesno',
    'lock_it': 'yesno', 'unlock_it': 'yesno', 'force_lock': 'yesno',
    'pay_damage': 'yesno', 'eat_it': 'yesno', 'sacrifice_it': 'yesno',
    'attach_candelabrum_candles': 'yesno', 'still_climb': 'yesno',
    'lift_burden': 'yesno', 'loot_it': 'yesno', 'put_something_in': 'yesno',
    'take_something_out': 'yesno', 'stop_eating': 'yesno',
    'drink_here': 'yesno', 'dip_here': 'yesno', 'append_engraving': 'yesno',
    'sell_it': 'yesno', 'enhance_without_practice': 'yesno',
    'do_teleport': 'yesno',
    # free text prompts (newline terminated)
    'what_name': 'text', 'offer_how_much': 'text', 'leveltele': 'text',
    'write_what': 'text', 'make_wish': 'text', 'genocide_class': 'text',
    'genocide_monster': 'text', 'who_are_you': 'text',
    'create_what_monster': 'text',
    # menus
    'pick_up_what': 'menu', 'name_menu': 'menu', 'take_out_what': 'menu',
    'put_in_what': 'menu', 'loot_what': 'menu', 'enhance_what': 'menu',
    'current_skills': 'menu', 'identify_what': 'menu',
    # actions
    'choose_action': 'action',
}


class Handler(object):
    """Equivalent of Clojure's (reify ...) - an object carrying only the
    event/prompt methods it implements."""

    def __init__(self, **methods):
        for name, fn in methods.items():
            setattr(self, name, fn)

    def __repr__(self):
        return "<Handler %s>" % ",".join(
            sorted(k for k in self.__dict__ if not k.startswith('_')))


def _enter_position(p):
    return to_position(p) + "."


def _newline_terminate(s):
    t = str(s)
    return t if t.endswith("\n") else t + "\n"


def _yesno(b):
    return "y" if b else "n"


def _direction(d):
    return VI_DIRECTIONS.get(d, d)


def _respond_menu(options):
    # `(string/join options)` walks the collection in *its* order.  A Clojure
    # set of menu letters is a PersistentHashSet, which iterates in the hash
    # order of its elements (Character.hashCode is the character's code
    # point); Python's set order depends on the per-process string hash seed,
    # so it has to be imposed explicitly.  Sequences keep their own order.
    if isinstance(options, (set, frozenset)):
        from .position import hamt_chunks
        from .util import clj_hasheq
        return "".join(str(o) for o in
                       sorted(options,
                              key=lambda o: hamt_chunks(clj_hasheq(o))))
    if isinstance(options, (list, tuple)):
        return "".join(str(o) for o in options)
    return str(options)


_TRANSFORM = {
    'choice': lambda r: str(r),
    'yesno': _yesno,
    'location': _enter_position,
    'direction': _direction,
    'text': _newline_terminate,
    'menu': _respond_menu,
}


class Delegator(object):
    """The Clojure original is an *agent*: every call from a handler is a
    `send`, i.e. it is queued and only processed once the current dispatch
    finishes.  That ordering is load-bearing (e.g. the scraper resets its
    state machine in action-chosen, which must happen after the redraw that
    triggered it has stored its next state), so it is reproduced here."""

    def __init__(self, writer=None):
        self.writer = writer
        self.handlers = []          # list of [priority, seq, handler]
        self.inhibited = False
        self._seq = 0
        self._queue = []
        self._busy = False

    # ------------------------------------------------------- agent semantics
    def _send(self, thunk):
        self._queue.append(thunk)
        if self._busy:
            return self
        self.drain()
        return self

    def drain(self):
        if self._busy:
            return self
        self._busy = True
        try:
            while self._queue:
                thunk = self._queue.pop(0)
                try:
                    thunk()
                except Exception:
                    log.exception("delegator caught error")
        finally:
            self._busy = False
        return self

    # -------------------------------------------------------------- plumbing
    def set_writer(self, writer):
        self.writer = writer

    def set_inhibition(self, state):
        self.inhibited = state

    def write(self, cmd):
        if not self.inhibited:
            log.debug("writing to terminal: %r", cmd)
            self.writer(cmd)
        return self

    def send_write(self, cmd):
        return self._send(lambda: self.write(cmd))

    def send_register(self, *args):
        return self._send(lambda: self.register(*args))

    def send_deregister(self, handler):
        return self._send(lambda: self.deregister(handler))

    def send_switch(self, old, new):
        return self._send(lambda: self.switch(old, new))

    def register(self, priority_or_handler, handler=None):
        if handler is None:
            priority, handler = PRIORITY_DEFAULT, priority_or_handler
        else:
            priority = priority_or_handler
        self._seq += 1
        self.handlers.append([priority, self._seq, handler])
        self.handlers.sort(key=lambda e: (e[0], e[1]))
        return self

    def deregister(self, handler):
        self.handlers = [e for e in self.handlers if e[2] is not handler]
        return self

    def switch(self, old, new):
        # `(-> delegator (deregister handler-old) (register priority
        # handler-new))` - the replacement is registered afresh, so it goes
        # *last* within its priority, it does not inherit the old handler's
        # place.  Only observable once ties are ordered at all.
        for e in self.handlers:
            if e[2] is old:
                priority = e[0]
                self.deregister(old)
                self.register(priority, new)
                return self
        raise ValueError("Handler to switch not present")

    def _handler_list(self):
        return [e[2] for e in self.handlers]

    # -------------------------------------------------------------- dispatch
    def _invoke_event(self, name, *args):
        for h in self._handler_list():
            fn = getattr(h, name, None)
            if fn is not None:
                try:
                    fn(*args)
                except Exception:
                    log.exception("Delegator caught handler exception in %s",
                                  name)

    def _invoke_prompt(self, name, *args):
        for h in self._handler_list():
            fn = getattr(h, name, None)
            if fn is None:
                continue
            try:
                res = fn(*args)
            except Exception:
                log.exception("Delegator caught handler exception in %s", name)
                continue
            if res is not None:
                return res
        raise RuntimeError("No handler responded to prompt of " + name)

    def _respond_escapable(self, kind, name, *args):
        if self.inhibited:
            return
        res = self._invoke_prompt(name, *args)
        log.debug("prompt response: %r", res)
        if isinstance(res, str) and res == "":
            log.info("Escaping prompt")
            self.write(ESC)
        else:
            self.response_chosen_direct(name, res)
            self.write(_TRANSFORM[kind](res))

    def _respond_action(self, name, *args):
        if self.inhibited:
            return
        from .action import trigger as _trigger
        action = self._invoke_prompt(name, *args)
        self.action_chosen_direct(action)
        self.write(_trigger(action))


def _make_event(name):
    def method(self, *args):
        return self._send(lambda: self._invoke_event(name, *args))

    def direct(self, *args):
        self._invoke_event(name, *args)
        return self
    method.__name__ = name
    direct.__name__ = name + '_direct'
    return method, direct


def _make_prompt(name, kind):
    if kind == 'action':
        def method(self, *args):
            return self._send(lambda: self._respond_action(name, *args))
    else:
        def method(self, *args):
            return self._send(
                lambda: self._respond_escapable(kind, name, *args))
    method.__name__ = name
    return method


for _e in EVENTS:
    _m, _d = _make_event(_e)
    setattr(Delegator, _e, _m)
    setattr(Delegator, _e + '_direct', _d)
for _p, _k in PROMPTS.items():
    setattr(Delegator, _p, _make_prompt(_p, _k))
