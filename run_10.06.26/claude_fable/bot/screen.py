"""Screen snapshot + status line parsing for NetHack 3.7 tty (statuslines:2)."""
import re
from dataclasses import dataclass, field

MAP_TOP = 1
MAP_BOTTOM = 21  # inclusive; rows 1..21 are the map
STATUS1 = 22
STATUS2 = 23

STATUS2_RE = re.compile(
    r"(?:Dlvl:|Home[: ]?|Fort[: ]?|End[: ]?)(?P<dlvl>\d+)\s+\$:(?P<gold>\d+)\s+HP:(?P<hp>-?\d+)\((?P<hpmax>\d+)\)\s+"
    r"Pw:(?P<pw>\d+)\((?P<pwmax>\d+)\)\s+AC:(?P<ac>-?\d+)\s+"
    r"(?:Xp:(?P<xp>\d+)(?:/(?P<exp>\d+))?|HD:\d+)\s+T:(?P<turn>\d+)\s*(?P<flags>.*)"
)


@dataclass
class Status:
    dlvl: int = 0
    gold: int = 0
    hp: int = 0
    hpmax: int = 0
    pw: int = 0
    pwmax: int = 0
    ac: int = 0
    xp: int = 0
    turn: int = 0
    flags: list = field(default_factory=list)

    @property
    def hungry(self):
        return "Hungry" in self.flags

    @property
    def weak(self):
        return "Weak" in self.flags or any(f.startswith("Faint") for f in self.flags)

    @property
    def satiated(self):
        return "Satiated" in self.flags

    @property
    def confused(self):
        return "Conf" in self.flags

    @property
    def stunned(self):
        return "Stun" in self.flags

    @property
    def blind(self):
        return "Blind" in self.flags


@dataclass
class Snap:
    lines: list          # 24 strings
    cells: list          # 24 x 80 of (char, fg, bold)
    cursor: tuple        # (x, y)
    status: Status

    @property
    def message(self):
        return self.lines[0].rstrip()

    def map_char(self, x, y):
        """x in 0..79, y in 0..20 (map coords); returns (char, fg, bold)."""
        return self.cells[y + MAP_TOP][x]

    @property
    def more(self):
        return any("--More--" in line for line in self.lines)

    @property
    def ynq(self):
        """Returns the bracketed choices string if the message line has a [yn..] style prompt."""
        m = re.search(r"\[([a-zA-Z$#*?]+(?: or \*)?[^\]]*)\]", self.lines[0])
        if m and ("y" in m.group(1) or "n" in m.group(1)):
            return m.group(1)
        return None


def parse_status(lines):
    st = Status()
    m = STATUS2_RE.search(lines[STATUS2])
    if not m:
        return None
    st.dlvl = int(m.group("dlvl"))
    st.gold = int(m.group("gold"))
    st.hp = int(m.group("hp"))
    st.hpmax = int(m.group("hpmax"))
    st.pw = int(m.group("pw"))
    st.pwmax = int(m.group("pwmax"))
    st.ac = int(m.group("ac"))
    st.xp = int(m.group("xp") or 0)
    st.turn = int(m.group("turn"))
    st.flags = m.group("flags").split()
    return st


def snapshot(sess):
    lines = sess.lines()
    cells = []
    for y in range(sess.rows):
        row = []
        buf = sess.screen.buffer[y]
        for x in range(sess.cols):
            c = buf[x]
            row.append((c.data, c.fg, c.bold))
        cells.append(row)
    status = parse_status(lines)
    return Snap(lines=lines, cells=cells, cursor=sess.cursor(), status=status)
