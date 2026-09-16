"""Dialogue layer: the single owner of everything written to the game.

A frame is acted on only when the screen is *settled* (PTY silence).
Prompts, menus and confirmations are answered as explicit transactions
through policy callables; every state transition is journalled.

Freshness probe (provenance: the `##'` marker trick from BotHack): typing
`#`, `#`, `'` at any quiet moment is a no-op that leaves NetHack waiting
for Enter with the topline exactly `# #'`.  That signature proves the
game is alive, the screen is complete and no other prompt is pending;
a following ESC resynchronises to a known-clean state.
"""

import re
import time

from . import term

SETTLE_QUIET = 0.09      # PTY silence (s) that counts as settled
SETTLE_MAX = 2.0         # hard cap on a settle wait
PROMPT_QUIET = 0.25      # quiet time before answering a prompt

DIR_KEYS = {(-1, 0): "h", (1, 0): "l", (0, -1): "k", (0, 1): "j",
            (-1, -1): "y", (1, -1): "u", (-1, 1): "b", (1, 1): "n"}
REVERSE = {v: k for k, v in DIR_KEYS.items()}

MORE = "--More--"
MARKER = "##'"
MARKER_TOPLINE = "# #'"


class Ended(Exception):
    pass


def classify_frame(session):
    """Classify the current frame. Returns (kind, detail).

    kind: idle | marker | more | menu | extcmd | direction | yesno |
          choice | waiting
    """
    lines, cells, cx, cy = session.terminal.snapshot()
    row0 = lines[0].rstrip()
    prompt = lines[0][:cx] if cy == 0 else row0
    prompt = prompt.rstrip()
    if "already a game in progress" in prompt:
        return "stale-game", prompt
    for i in range(22):                       # --More-- can wrap anywhere
        if lines[i].rstrip().endswith(MORE):
            return "more", lines[i].rstrip()
    for i in range(1, term.ROWS):
        t = lines[i].rstrip()
        if t.endswith("(end)") or re.search(r"\(\d+ of \d+\)\s*$", t):
            return "menu", (i, t)
    if prompt == "# ":
        return "extcmd", prompt
    if cy == 0 and row0 == MARKER_TOPLINE and cx >= 4:
        return "marker", prompt
    if prompt.startswith("In what direction"):
        return "direction", prompt
    if "[yn" in prompt:
        return "yesno", prompt
    if prompt.startswith(("What do you want", "What type of", "Pick an object",
                          "Talk to whom", "Call ", "Name ", "For what",
                          "Where do you want", "What do you look")):
        return "choice", prompt
    if prompt.startswith(("Do you want", "Really", "Die?", "Dump core")):
        return "yesno", prompt
    if prompt.endswith("?") or prompt.startswith("#"):
        return "choice", prompt
    if cy == 0 and prompt:
        if row0.startswith("#"):
            return "extcmd", prompt
        return "waiting", prompt
    return "idle", prompt


class DefaultPolicy:
    """Standalone prompt policy for out-of-transaction surprises."""

    def __init__(self, direction=None):
        self.direction = direction

    def __call__(self, kind, detail):
        if kind == "more":
            return " "
        if kind == "extcmd":
            return "\x1b\x1b"
        if kind == "marker":
            return "\x1b"
        if kind == "direction":
            return DIR_KEYS.get(self.direction, "y")
        if kind == "yesno":
            if "Really attack" in detail:
                return "y"
            return "n"
        if kind in ("menu", "choice"):
            return "\x1b"       # take / answer nothing by default
        return None


class Dialogue:
    """Single owner of terminal writes; journalled prompt transactions."""

    def __init__(self, session):
        self.session = session
        self.messages = []        # rolling topline log
        self.transitions = []     # bounded ring of (time, kind, detail)

    # ---- low level ---------------------------------------------------
    def write(self, data):
        self.session.write(data.encode("latin-1") if isinstance(data, str) else data)

    def settle(self, quiet=SETTLE_QUIET, cap=SETTLE_MAX):
        """Read until the screen looks stable; returns the latest lines."""
        last = time.monotonic()
        start = last
        while True:
            now = time.monotonic()
            if now - last >= quiet or now - start >= cap:
                break
            got = self.session.read(min(0.03, max(0.0, cap - (now - start))))
            if got:
                last = time.monotonic()
        return self.session.terminal.text()

    def _note(self, kind, detail):
        self.transitions.append((time.monotonic(), kind, str(detail)[:70]))
        if len(self.transitions) > 200:
            del self.transitions[:100]

    def log_message(self, lines):
        msg = lines[0].rstrip()
        if msg:
            self.messages.append(msg)
            if len(self.messages) > 400:
                del self.messages[:200]

    def classify(self):
        kind, detail = classify_frame(self.session)
        self._note(kind, detail)
        return kind, detail

    # ---- transaction loop ---------------------------------------------
    def pump(self, policy, max_steps=80):
        """Answer prompts per policy(kind, detail) until settled idle.

        Returns (kind, detail, lines); kind 'timeout' when budget exceeded.
        """
        for _ in range(max_steps):
            lines = self.settle(quiet=PROMPT_QUIET, cap=SETTLE_MAX)
            self.log_message(lines)
            kind, detail = classify_frame(self.session)
            self._note(kind, detail)
            if kind == "idle":
                return kind, detail, lines
            if kind == "marker":
                self.write("\x1b")      # cancel our own marker prompt
                continue
            resp = policy(kind, detail) if policy is not None else None
            if resp:
                self.write(resp)
        return "timeout", "", []

    # ---- freshness probe ------------------------------------------------
    def probe(self):
        """Resynchronise; True when a fresh complete frame was confirmed."""
        for _ in (1, 2):
            try:
                self.write(MARKER)
                self.settle(quiet=0.35, cap=1.5)
                kind, _ = classify_frame(self.session)
                if kind == "marker":
                    self.write("\x1b")   # cancel: a clean redraw follows
                    self.settle()
                    self._note("resync", "probe-ok")
                    return True
            except Exception:
                return False
            self.write("\x1b" * 4)
        return False
