"""Food and drink handlers from actions.clj (GPL-2.0), 2026-09-09."""
import re
from .state import assoc_in
from .actions import Responses, Slot
from . import dungeon as d


def handler(selected, context):
    target = selected.args[0]
    if selected.kind in ('eat', 'offer'):
        def message(text):
            if selected.kind == 'offer':
                if 'You are not standing on an altar' in text:
                    return None
                if re.search(r'You have a feeling of reconciliation\.|You glimpse a four-leaf clover at your feet|You think something brushed your foot|You see crabgrass at your feet', text):
                    # Original writes inside player, unlike Pray's game-level field.
                    return context.mutate(assoc_in, ['player', 'last-prayer'], -1000)
            elif text == "You don't have anything to eat.":
                context.update_inventory()
                return context.update_tile()

        def eat_it(what):
            if isinstance(target, str) and not isinstance(target, Slot) and what == target:
                return context.update_tile()
            return False

        def eat_what(prompt):
            if isinstance(target, Slot):
                context.update_inventory()
                return target
            if isinstance(target, str):
                context.update_tile()

        if selected.kind == 'offer':
            return Responses(message=message, sacrifice_it=eat_it, sacrifice_what=eat_what)
        return Responses(message=message, eat_it=eat_it, eat_what=eat_what)

    context.possible_autoid(target)

    def message(text):
        if re.search(r'The flow reduces to a trickle|, stop using that fountain!', text):
            return context.mutate(d.update_at_player,
                                  lambda tile: tile | {'tags': set(tile.get('tags') or ()) | {'trickle'}})

    def drink_here(prompt):
        return context.update_tile() if target == '.' else False

    def drink_what(prompt):
        if target != '.':
            context.mark_use(target)
            context.update_inventory()
            return target

    return Responses(message=message, drink_here=drink_here, drink_what=drink_what)
