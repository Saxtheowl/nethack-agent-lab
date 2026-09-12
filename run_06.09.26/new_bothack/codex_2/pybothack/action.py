"""Port of bothack.action - actions are maps carrying a trigger (the keys to
write) and an optional handler factory, exactly like the Clojure records."""


def action(type_, trigger_, handler_=None, **fields):
    a = {'type': type_, 'trigger': trigger_, 'handler': handler_,
         'handlers': [], 'reason': None}
    a.update(fields)
    return a


def typekw(a):
    return a.get('type') if a else None


def trigger(a):
    t = a['trigger']
    return t(a) if callable(t) else t


def handler(a, bh):
    h = a.get('handler')
    return h(a, bh) if h else None
