"""Event/prompt priority semantics from delegator.clj (GPL-2.0, 2026-09-06)."""
import logging

log = logging.getLogger(__name__)


class UnhandledPrompt(RuntimeError):
    pass


class Delegator:
    def __init__(self, writer):
        self.writer = writer
        self.inhibited = False
        self.handlers = {}  # identity keys; upstream leaves equal-priority order unspecified

    def register(self, handler, priority=0):
        self.handlers[id(handler)] = (handler, priority)
        return self

    def deregister(self, handler):
        self.handlers.pop(id(handler), None)
        return self

    def switch(self, old, new):
        if id(old) not in self.handlers:
            raise ValueError("Handler to switch not present")
        priority = self.handlers[id(old)][1]
        self.deregister(old)
        return self.register(new, priority)

    def _ordered(self):
        return [h for h, _ in sorted(self.handlers.values(), key=lambda entry: entry[1])]

    @staticmethod
    def _invoke(handler, method, args):
        if function := getattr(handler, method, None):
            try:
                return function(*args)
            except Exception:
                log.exception("Delegator caught handler exception")
        return None

    def event(self, method, *args):
        for h in self._ordered():
            self._invoke(h, method, args)

    def prompt(self, method, *args):
        if self.inhibited:
            return None
        for h in self._ordered():
            result = self._invoke(h, method, args)
            if result is not None:  # False and empty collections ARE responses in Clojure.
                return result
        raise UnhandledPrompt(method)

    def write(self, command):
        if not self.inhibited:
            self.writer(command)

    def respond(self, method, *args, transform=str):
        if not self.inhibited:
            result = self.prompt(method, *args)
            if isinstance(result, str) and result == "":
                self.write("\x1b")
            else:
                self.event("response_chosen", method, result)
                self.write(transform(result))
