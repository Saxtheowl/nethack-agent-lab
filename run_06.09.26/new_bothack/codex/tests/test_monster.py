import pytest
from bothack.catalog import data
from bothack.monster import by_description, new_monster


@pytest.mark.oracle
def test_monster_descriptions(oracle):
    for m in data()["monsters"]:
        for prefix in ("a ", "the peaceful ", "a tame invisible "):
            desc = prefix + m["name"]
            try:
                expected = oracle.call("monster-description", desc)
            except RuntimeError as error:
                assert "Failed to parse monster" in str(error)
                with pytest.raises(ValueError, match="Failed to parse monster"):
                    by_description(desc)
            else:
                assert by_description(desc) == expected
    for desc in ("the high priestess of Tyr", "a soldier called Bob", "Izchak", "Bob's ghost", "a coyote - Carnivorous Vulgaris", "tail of a peaceful long worm", "Fighter", "Vlad the Impaler", "Neferet the Green"):
        assert by_description(desc) == oracle.call("monster-description", desc)


@pytest.mark.oracle
def test_monster_appearance_and_pet_colors(oracle):
    for m in data()["monsters"]:
        args = (40, 12, 50, m["glyph"], m["color"])
        assert new_monster(*args) == oracle.call("new-monster", *args)
    for color in ("inverse", "inverse-white", "inverse-bold", "inverse-red"):
        args = (40, 12, 51, "d", color)
        assert new_monster(*args) == oracle.call("new-monster", *args)
