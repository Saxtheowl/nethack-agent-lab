"""Delegator protocols and terminal response encoding from delegator.clj.

GPL-2.0, translated 2026-09-06. Handler methods use Python underscores; queued
calls retain original hyphenated names. No gameplay decisions live here.
"""
from .position import Position, VI_DIRECTIONS, to_position

GROUPS = {
    'event': '''online offline redraw full-frame know-position started ended message
        botl dlvl-changed about-to-choose action-chosen response-chosen inventory-list
        message-lines found-items''',
    'location': 'teleport-where travel-where pay-whom',
    'direction': 'what-direction',
    'choice': '''choose-character apply-what wield-what wear-what take-off-what
        put-on-what remove-what drop-single ready-what dump-core name-what which-finger
        read-what drink-what zap-what eat-what sacrifice-what dip-what dip-into-what
        throw-what write-with-what rub-what charge-what''',
    'yesno': '''really-attack seduced-puton seduced-remove enter-gehennom force-god
        die keep-save dry-fountain lock-it unlock-it force-lock pay-damage drink-here
        eat-it sacrifice-it attach-candelabrum-candles still-climb dip-here lift-burden
        loot-it put-something-in take-something-out stop-eating append-engraving sell-it
        enhance-without-practice do-teleport''',
    'text': '''what-name offer-how-much leveltele write-what create-what-monster
        make-wish genocide-class genocide-monster who-are-you''',
    'menu': '''pick-up-what name-menu take-out-what put-in-what loot-what enhance-what
        current-skills identify-what''',
    'action': 'choose-action',
}
KINDS = {name: kind for kind, names in GROUPS.items() for name in names.split()}


def _str(value):
    if value is None:
        return ''
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    return str(value)


def encode_response(kind, value):
    if kind == 'yesno':
        # Clojure considers 0, empty strings and empty collections true.
        return 'n' if value is None or value is False else 'y'
    if kind == 'direction':
        return VI_DIRECTIONS.get(value, value)
    if kind == 'location':
        return to_position(Position(**value) if isinstance(value, dict) else value) + '.'
    if kind == 'menu':
        return ''.join(map(_str, value)) if isinstance(value, (list, tuple, set, frozenset)) else _str(value)
    text = _str(value)
    if kind == 'text' and not text.endswith('\n'):
        text += '\n'
    return text


def dispatch(delegator, call):
    """Deliver one scraper call after feed() has finished, in queue order."""
    name, *args = call
    if name == 'write':
        delegator.write(*args)
        return
    kind = KINDS[name]
    method = name.replace('-', '_')
    if kind == 'event':
        delegator.event(method, *args)
    elif kind == 'action':
        if not delegator.inhibited:
            action = delegator.prompt(method, *args)
            delegator.event('action_chosen', action)
            delegator.write(action.trigger())
    else:
        delegator.respond(method, *args, transform=lambda value: encode_response(kind, value))
