"""Initial identities and shop-price relation from itemid.clj (GPL-2.0).

Translated 2026-09-06. Discovery queries use finite relations rather than a
general logic-programming runtime, including forgetting and reusing names.
"""
from collections import defaultdict
from functools import lru_cache
import re
from .catalog import data, items_by_name


def charisma_group(cha):
    for threshold, group in ((3, 0), (6, 5), (8, 7), (11, 10), (16, 15), (18, 17), (19, 18)):
        if cha < threshold:
            return group
    return 25


def possible_prices(base, charisma):
    """All original prices, including unknown-item and sucker adjustments.

    Original cost-data deliberately only contains base prices 0..500.
    charisma < 3 selects the selling-price relation.
    """
    if not 0 <= base <= 500:
        return frozenset()
    group = charisma_group(charisma)
    result = set()
    id_prices = (base // 2,) if group == 0 else (base, base + base // 3)
    for price in id_prices:
        adjusted = (price, price - price // 4) if group == 0 else (price, price + price // 3)
        for price in adjusted:
            result.add({0: lambda p: p, 5: lambda p: 2 * p, 7: lambda p: p + p // 2,
                        10: lambda p: p + p // 3, 15: lambda p: p, 17: lambda p: p - p // 4,
                        18: lambda p: p - p // 3, 25: lambda p: p // 2}[group](price))
    return frozenset(result)


@lru_cache(maxsize=1)
def ambiguous_names():
    counts = defaultdict(int)
    exclusive = set(data()["exclusive"])
    for item in data()["items"]:
        for appearance in item.get("appearances") or ():
            if appearance not in exclusive and appearance not in {"Amulet of Yendor", "egg", "tin"}:
                counts[appearance] += 1
    return {name: tuple(name + str(n) for n in range(1, size + 1)) for name, size in counts.items() if size != 1}


def appearance_of(item):
    if item.get("name") in ambiguous_names() and item.get("generic") is not None:
        return item["generic"]
    if specific := items_by_name().get(item.get("specific")):
        return specific["name"]
    return item["name"]


@lru_cache(maxsize=1)
def appearances():
    result = defaultdict(list)
    variants = ambiguous_names()
    for item in data()["items"]:
        if item.get("artifact") and item.get("base"):
            continue
        for appearance in item.get("appearances") or ():
            for name in (appearance, *variants.get(appearance, ())):
                if item not in result[name]:
                    result[name].append(item)
    return dict(result)


def initial_ids(item):
    appearance = appearance_of(item)
    if appearance in data()["blind-identities"]:
        return (data()["blind-identities"][appearance],)
    if known := items_by_name().get(appearance):
        return (known,)
    return tuple(appearances().get(appearance, ()))


def common_properties(identities):
    identities = tuple(identities)
    if not identities:
        return None
    result = dict(identities[0])
    for other in identities[1:]:
        for key in list(result):
            if key not in other:
                del result[key]
            elif result[key] != other[key]:
                result[key] = None
    return result


class Identification:
    """Finite discovery, price and observable-property relations.

    Multiple observations of the same property are alternatives in the
    original core.logic query. Distinct property kinds are conjunctive.
    """
    OBSERVABLE = frozenset({"engrave", "target", "hardness", "autoid", "food"})
    BLIND = frozenset({"stone", "gem", "potion", "wand", "spellbook", "scroll"})

    def __init__(self):
        self.discoveries = []
        self.costs = defaultdict(list)
        self.properties = defaultdict(lambda: defaultdict(list))
        self.named = {name for variants in ambiguous_names().values() for name in variants}
        self.exclusive = set(data()["exclusive"])
        self.used_names = set()

    def knowable(self, appearance):
        return appearance not in self.BLIND and (appearance in self.named or appearance in self.exclusive)

    def _possible(self, appearance):
        candidates = initial_ids({"name": appearance})
        if appearance in items_by_name() or not self.knowable(appearance):
            return candidates
        result = []
        for item in candidates:
            name = item["name"]
            identities = [a for a, i in self.discoveries if i == name]
            known = [i for a, i in self.discoveries if a == appearance]
            if identities:
                allowed = appearance in identities
            elif known:
                allowed = name in known
            else:
                observations = self.costs[appearance]
                allowed = not observations or any(
                    cost in possible_prices(item["price"] + enchantment * 10, cha)
                    for cha, cost in observations
                    for enchantment in (range(5) if item["kind"] == "armor" else (0,)))
                if allowed:
                    for prop, values in self.properties[appearance].items():
                        expected = item.get(prop)
                        if expected is None:
                            expected = False
                        if not any(type(value) is type(expected) and value == expected for value in values):
                            allowed = False
                            break
            if allowed:
                result.append(item)
        return tuple(result)

    def possible_ids(self, item):
        return self._possible(appearance_of(item))

    def possible_names(self, appearance):
        return tuple(item.get("name") for item in self._possible(appearance))

    def item_id(self, item):
        return common_properties(self.possible_ids(item))

    def _eliminate(self, changed):
        # The original recursively commits newly singleton appearances sharing
        # the changed appearance's identity group.
        pending = [changed]
        while pending:
            appearance = pending.pop()
            affected = {i["name"] for i in appearances().get(appearance, ())}
            for candidate, items in appearances().items():
                if not self.knowable(candidate) or not any(i["name"] in affected for i in items):
                    continue
                possible = self._possible(candidate)
                if len(possible) == 1:
                    fact = (candidate, possible[0]["name"])
                    if fact not in self.discoveries:
                        self.discoveries.append(fact)
                        pending.append(candidate)

    def discover(self, appearance, identity):
        if appearance != identity and self.knowable(appearance):
            identity = data()["japanese"].get(identity, identity)
            fact = (appearance, identity)
            if fact not in self.discoveries:
                self.discoveries.append(fact)
                self._eliminate(appearance)
        return self

    def observe_cost(self, appearance, charisma, cost, sell=False):
        if self.knowable(appearance):
            fact = (0 if sell else charisma_group(charisma), cost)
            if fact not in self.costs[appearance]:
                self.costs[appearance].append(fact)
                self._eliminate(appearance)
        return self

    def observe_property(self, appearance, prop, value):
        if prop not in self.OBSERVABLE:
            raise ValueError(f"Not an observable property: {prop}")
        if self.knowable(appearance) and value not in self.properties[appearance][prop]:
            self.properties[appearance][prop].append(value)
            self._eliminate(appearance)
        return self

    def name_for(self, item):
        return next((name for name in ambiguous_names().get(item["name"], ()) if name not in self.used_names), None)

    def forget_names(self, names):
        if not names:
            return self
        self.used_names.difference_update(names)
        for name in names:
            base = re.sub(r"(.*)[0-9]+", r"\1", name)
            for variant in ambiguous_names().get(base, ()):
                if variant not in self.used_names:
                    self.discoveries = [(a, identity) for a, identity in self.discoveries if a != variant]
                    self.costs.pop(variant, None)
                    self.properties.pop(variant, None)
        for name in names:
            self._eliminate(name)
        return self
