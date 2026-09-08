"""Clojure atom/ref equivalent - a mutable box around an immutable value."""


class Atom(object):
    __slots__ = ('value',)

    def __init__(self, value=None):
        self.value = value

    def deref(self):
        return self.value

    def swap(self, f, *args):
        self.value = f(self.value, *args)
        return self.value

    def reset(self, v):
        self.value = v
        return v
