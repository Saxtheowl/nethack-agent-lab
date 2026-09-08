import pytest
from bothack.itemid import Identification, ambiguous_names, appearances, initial_ids, possible_prices


@pytest.mark.oracle
def test_ambiguous_names(oracle):
    assert {k: list(v) for k, v in ambiguous_names().items()} == oracle.call("ambiguous-names")


@pytest.mark.oracle
def test_initial_id_names(oracle):
    for appearance in appearances():
        item = {"name": appearance}
        assert {i.get("name") for i in initial_ids(item)} == set(oracle.call("initial-ids", item))


@pytest.mark.oracle
def test_prices(oracle):
    for base in (0, 1, 2, 3, 7, 10, 20, 50, 60, 75, 100, 150, 175, 200, 250, 300, 500, 501):
        for cha in (0, 3, 5, 6, 7, 8, 10, 11, 15, 16, 17, 18, 19, 25):
            assert possible_prices(base, cha) == set(oracle.call("prices", base, cha))


@pytest.mark.oracle
@pytest.mark.parametrize("facts,names", [
    ([("discovery", "scroll labeled ZELGO MER", "scroll of identify")], ["scroll labeled ZELGO MER", "scroll labeled JUYED AWK YACC"]),
    ([("cost", "lamp1", 13, 10, False)], ["lamp", "lamp1", "lamp2"]),
    ([("cost", "oak wand", 15, 500, False)], ["oak wand", "glass wand"]),
    ([("property", "oak wand", "engrave", "vanish")], ["oak wand", "glass wand"]),
    ([("property", "oak wand", "engrave", "nothing"), ("property", "oak wand", "target", False)], ["oak wand", "glass wand"]),
    ([("cost", "ruby potion", 10, 100, False), ("cost", "ruby potion", 10, 200, False)], ["ruby potion", "pink potion"]),
    ([("discovery", "lamp1", "oil lamp")], ["lamp", "lamp1", "lamp2"]),
    ([("discovery", "lamp", "oil lamp")], ["lamp", "lamp1", "lamp2"]),
])
def test_discovery_relations(oracle, facts, names):
    db = Identification()
    for kind, appearance, *args in facts:
        {"discovery": db.discover, "cost": db.observe_cost, "property": db.observe_property}[kind](appearance, *args)
    expected = oracle.call("identified", names, facts)
    assert {name: set(db.possible_names(name)) for name in names} == {name: set(ids or ()) for name, ids in expected.items()}


@pytest.mark.oracle
def test_forgetting_names_keeps_still_used_variants(oracle):
    for used in ([], ["lamp1"], ["lamp2"], ["lamp1", "lamp2"]):
        facts = [("discovery", "lamp1", "oil lamp"), *(("used", name) for name in used), ("forget", ["lamp1"])]
        db = Identification().discover("lamp1", "oil lamp")
        db.used_names.update(used)
        db.forget_names(["lamp1"])
        expected = oracle.call("identified", ["lamp1", "lamp2"], facts)
        assert {name: set(db.possible_names(name)) for name in expected} == {name: set(ids or ()) for name, ids in expected.items()}


@pytest.mark.oracle
def test_consistent_observations_from_random_identities(oracle):
    import random
    rng = random.Random(343)
    for appearance, others in (("ruby potion", ["pink potion", "orange potion"]),
                               ("oak wand", ["glass wand", "marble wand"]),
                               ("scroll labeled ZELGO MER", ["scroll labeled JUYED AWK YACC"])):
        candidates = initial_ids({"name": appearance})
        for _ in range(8):
            identity = rng.choice(candidates)
            cha = rng.choice([3, 7, 13, 18, 25])
            price = rng.choice(sorted(possible_prices(identity["price"], cha)))
            facts = [("cost", appearance, cha, price, False)]
            db = Identification().observe_cost(appearance, cha, price)
            for prop in sorted(Identification.OBSERVABLE):
                value = identity.get(prop)
                if value is None:
                    value = False
                facts.append(("property", appearance, prop, value))
                db.observe_property(appearance, prop, value)
            expected = oracle.call("identified", [appearance, *others], facts)
            assert {name: set(db.possible_names(name)) for name in expected} == {name: set(ids or ()) for name, ids in expected.items()}
