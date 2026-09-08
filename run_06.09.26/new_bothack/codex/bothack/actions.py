"""Action triggers and first handlers translated from actions.clj (GPL-2.0).

2026-09-07. All original record triggers are represented. Unsupported handlers
raise explicitly: a correct keystroke alone is not a complete action port.
The context supplies a game dict and the original deferred-update operations.
"""
from dataclasses import dataclass, replace, field
from copy import deepcopy
import re
from .position import Position, VI_DIRECTIONS, to_position
from .item import label_to_item

# Original record name, constructor fields, and fixed trigger (when applicable).
SPECS = {
    'attack': ('Attack', 'dir', None), 'farmattack': ('FarmAttack', 'dir cnt', None),
    'move': ('Move', 'dir', None), 'pray': ('Pray', '', '#pray\n'),
    'search': ('Search', '', 's'), 'wait': ('Wait', '', '.'),
    'ascend': ('Ascend', '', '<'), 'descend': ('Descend', '', '>'),
    'kick': ('Kick', 'dir', None), 'close': ('Close', 'dir', None),
    'look': ('Look', '', ':'), 'farlook': ('FarLook', 'pos', None),
    'open': ('Open', 'dir', None), 'inventory': ('Inventory', '', 'i'),
    'discoveries': ('Discoveries', '', '\\'), 'name': ('Name', 'slot name', '#name\n'),
    'call': ('Call', 'slot name', '#call\n'), 'apply': ('Apply', 'slot', 'a'),
    'forcelock': ('ForceLock', '', '#force\n'), 'wield': ('Wield', 'slot', 'w'),
    'wear': ('Wear', 'slot', 'W'), 'puton': ('PutOn', 'slot', 'P'),
    'remove': ('Remove', 'slot', 'R'), 'takeoff': ('TakeOff', 'slot', 'T'),
    'dropsingle': ('DropSingle', 'slot qty', 'd'), 'quiver': ('Quiver', 'slot', 'Q'),
    'pickup': ('PickUp', 'label-or-list', ','), 'autotravel': ('Autotravel', 'pos', '_'),
    'enhance': ('Enhance', '', '#enhance\n'), 'read': ('Read', 'slot', 'r'),
    'sit': ('Sit', '', '#sit\n'), 'eat': ('Eat', 'slot-or-label', 'e'),
    'quaff': ('Quaff', 'slot', 'q'), 'repeated': ('Repeated', 'action n', None),
    'offer': ('Offer', 'slot-or-label', '#offer\n'), 'loot': ('Loot', '', '#loot\n'),
    'dip': ('Dip', 'item-slot potion-slot', '#dip\n'), 'throw': ('Throw', 'slot dir', 't'),
    'engrave': ('Engrave', 'slot what append?', 'E'), 'wipe': ('Wipe', '', '#wipe\n'),
    'zapwand': ('ZapWand', 'slot', 'z'), 'rub': ('Rub', 'slot', '#rub\n'),
    'chat': ('Chat', 'dir', None), 'pay': ('Pay', 'shk', 'p'),
}


class Responses:
    def __init__(self, **methods):
        self.__dict__.update(methods)


@dataclass(frozen=True)
class Action:
    kind: str
    args: tuple = ()
    handlers: tuple = ()
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.kind not in SPECS:
            raise ValueError(f'Unknown action: {self.kind}')
        if len(self.args) != len(SPECS[self.kind][1].split()):
            raise TypeError(f'{self.kind} expects {SPECS[self.kind][1]}')

    def trigger(self):
        fixed = SPECS[self.kind][2]
        if fixed is not None:
            return fixed
        if self.kind == 'repeated':
            return str(self.args[1]) + self.args[0].trigger()
        if self.kind == 'farlook':
            pos = self.args[0]
            return ';' + to_position(Position(**pos) if isinstance(pos, dict) else pos) + '.'
        try:
            direction = VI_DIRECTIONS[self.args[0]]
        except (KeyError, TypeError) as error:
            raise ValueError(f'Invalid direction: {self.args[0]}') from error
        if self.kind == 'farmattack':
            return ('\x1b\x1bF' + direction) * max(0, self.args[1]) + '\x1b' * 30 + "##'"
        return {'attack': 'F', 'move': '', 'kick': '\x04', 'close': 'c',
                'open': 'o', 'chat': '#chat\n'}[self.kind] + direction

    def with_fields(self, **values):
        return replace(self, extra=self.extra | values)

    def handler(self, context):
        if self.kind in {'search', 'sit', 'open', 'close', 'kick', 'attack', 'move'}:
            from .movement_actions import handler
            return handler(self, context)
        if self.kind == 'repeated':
            return self.args[0].handler(context)
        if self.kind in ('wait', 'farmattack'):
            return None
        game = context.game
        if self.kind == 'pray':
            game['last-prayer'] = game.get('turn')
            # Upstream returns the updated game map from swap!, not nil.
            return deepcopy(game)
        if self.kind == 'pay':
            return Responses(pay_whom=lambda: self.args[0])
        if self.kind == 'wipe':
            def message(text):
                game = context.game
                if re.search(r"Your .* is already clean|You've got the glop off", text):
                    player = game.setdefault('player', {})
                    if player.get('state') is not None:
                        player['state'] = set(player['state']) - {'ext-blind'}
                    else:
                        player['state'] = None
                    return deepcopy(game)
            return Responses(message=message)
        if self.kind == 'inventory':
            def message(text):
                game = context.game
                player = game.setdefault('player', {})
                if text == 'Not carrying anything.':
                    player['inventory'] = {}
                elif text == 'Not carrying anything except gold.':
                    player['inventory'] = {k: v for k, v in (player.get('inventory') or {}).items() if k == '$'}
                else:
                    return None
                return deepcopy(game)

            def inventory_list(options):
                game = context.game
                player = game.setdefault('player', {})
                inventory = {slot: label_to_item(label) for slot, label in options.items()}
                for slot, old in (player.get('inventory') or {}).items():
                    if slot in inventory:
                        new = inventory[slot]
                        keys = ['items', 'locked']
                        if new.get('buc') is None:
                            keys.append('buc')
                        if len(new['label']) > 72 and old.get('in-use') is not None and old.get('in-use') is not False:
                            keys.extend(('in-use', 'worn'))
                        new.update({key: deepcopy(old[key]) for key in keys if key in old})
                player['inventory'] = inventory
                return deepcopy(game)
            return Responses(message=message, inventory_list=inventory_list)
        if self.kind == 'enhance':
            def current_skills(options):
                game = context.game
                game.setdefault('player', {})['can-enhance'] = None
                return set()
            return Responses(current_skills=current_skills)
        if self.kind in ('wield', 'quiver', 'name'):
            context.update_inventory()
            slot = self.args[0]
            if self.kind == 'wield':
                context.possible_autoid(slot)
                return Responses(wield_what=lambda prompt: slot)
            if self.kind == 'quiver':
                return Responses(ready_what=lambda prompt: slot)
            return Responses(name_menu=lambda options: 'b', name_what=lambda prompt: slot,
                             what_name=lambda prompt: self.args[1])
        raise NotImplementedError(f'Action handler not yet ported: {self.kind}')


def action(kind, *args):
    return Action(kind, args)


def with_handler(handler, selected, priority=0):
    # conj on the original initially-nil field builds a list in reverse order.
    return replace(selected, handlers=((priority, handler), *selected.handlers))


def search(n=1):
    return action('repeated', action('search'), n)


def enhance_all():
    return with_handler(Responses(enhance_what=lambda options: 'a'), action('enhance'))
