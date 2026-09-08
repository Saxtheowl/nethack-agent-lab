from bothack.benchmark import parse_xlog, legitimate_ascension


def test_historical_colon_and_modern_tab_records():
    for separator in (":", "\t"):
        record = parse_xlog(separator.join(["version=3.4.3", "name=Ref343d", "death=killed by a soldier ant", "flags=0x0", "turns=2986"]) + "\n")
        assert record["name"] == "Ref343d"
        assert record["death"] == "killed by a soldier ant"
        assert record["turns"] == "2986"
        assert not legitimate_ascension(record)


def test_wizard_and_exploration_victories_are_not_evidence():
    record = {"version": "3.4.3", "death": "ascended", "flags": "0x0"}
    assert legitimate_ascension(record)
    assert not legitimate_ascension(record | {"flags": "0x1"})
    assert not legitimate_ascension(record | {"flags": "0x2"})
    assert not legitimate_ascension(record | {"version": "3.6.7"})
    assert not legitimate_ascension({"version": "3.4.3", "death": "ascended"})
