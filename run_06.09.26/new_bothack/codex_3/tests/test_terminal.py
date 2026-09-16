from bothack_new.terminal import Terminal
def test_fragmented_ansi_screen_and_snapshot_isolation():
    t=Terminal(10,3); payload=b"\033[2J\033[2;3Habc"
    for byte in payload: t.feed(bytes([byte]))
    first=t.snapshot(); t.feed(b"Z"); second=t.snapshot()
    assert first.rows[1][2:5] == "abc" and first.rows != second.rows
def test_cursor_movement():
    t=Terminal(5,2); t.feed(b"ab\033[1;1HZ")
    assert t.snapshot().rows[0].startswith("Zb")
