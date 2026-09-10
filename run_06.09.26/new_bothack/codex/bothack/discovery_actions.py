"""Discovery menu parsing from actions.clj (GPL-2.0), 2026-09-09."""
import re
from copy import deepcopy
from .actions import Responses

DISCOVERIES_RE = re.compile(
    r'(Artifacts|Unique Items|Spellbooks|Amulets|Weapons|Wands|Gems|Armor|Food|Tools|Scrolls|Rings|Potions)'
    r'|(?:\* )?([^\(]*)(?: called [^(]+)? \(([^\)]*)\)$|^(?:[^(]+)$')


def demangle(section, appearance):
    if section == 'Gems':
        return appearance + (' stone' if appearance == 'gray' else ' gem')
    suffixes = {'Amulets': 'amulet', 'Wands': 'wand', 'Rings': 'ring',
                'Potions': 'potion', 'Spellbooks': 'spellbook'}
    if section in suffixes:
        return appearance + ' ' + suffixes[section]
    if section == 'Scrolls':
        return 'scroll labeled ' + appearance
    return appearance


def parse_discoveries(lines):
    section = None
    discoveries = []
    for line in lines:
        text = re.sub(r'^(.*) called ([^(]+) \([^)]*\)', r'\1 (\2)', line)
        match = DISCOVERIES_RE.search(text)
        if match:
            group, identity, appearance = match.groups()
            if group:
                section = group
            elif section != 'Unique Items' and appearance is not None:
                discoveries.append((demangle(section, appearance), identity))
    return discoveries


def handler(context):
    def message_lines(lines):
        db = deepcopy(context.game['discoveries'])
        for appearance, identity in parse_discoveries(lines):
            db.discover(appearance, identity)
        context.game = context.game | {'discoveries': db}
        return context.game

    def about_to_choose(game):
        # (:used-names game) in the original addresses the atom, not its value.
        # Its difference is nil, so forget-names is a no-op.
        return context.game

    return Responses(message_lines=message_lines, about_to_choose=about_to_choose)
