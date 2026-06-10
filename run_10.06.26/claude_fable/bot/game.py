"""Interaction layer: send commands, auto-handle --More--, collect messages, menus."""
import re
import time

CTRL_R = "\x12"  # redraw

from screen import snapshot

ESC = "\x1b"
CTRL_O = "\x0f"  # overview
CTRL_D = "\x04"  # kick


class GameOver(Exception):
    pass


class Game:
    def __init__(self, sess, log=None):
        self.sess = sess
        self.messages = []       # full message history
        self.turn_messages = []  # messages since last command
        self.flags = set()       # sticky state derived from messages
        self.log = log or (lambda *a: None)

    # ---------- low level ----------

    def snap(self):
        return snapshot(self.sess)

    def _collect_message(self, snap):
        msg = snap.message.replace("--More--", "").strip()
        if msg:
            if not self.messages or self.messages[-1] != msg:
                self.log(f"[msg] {msg}")
            self.messages.append(msg)
            self.turn_messages.append(msg)
            if len(self.messages) > 500:
                del self.messages[:250]
            if "cannot escape from" in msg or "is stuck to you" in msg:
                self.flags.add("stuck")
            if "lichen touches you" in msg:
                self.flags.add("kill_lichen")
            if re.search(r"The \S*were\S* (hits|bites|misses|just misses|summons)", msg):
                self.flags.add("hostile_human")
            if "more confident in your" in msg:
                self.flags.add("can_enhance")
            if re.search(r"You (kill|destroy) the \S*were", msg):
                self.flags.discard("hostile_human")
            if "pull free" in msg or "You kill" in msg or "You destroy" in msg:
                self.flags.discard("stuck")
                if "lichen" in msg and ("You kill" in msg or "You destroy" in msg):
                    self.flags.discard("kill_lichen")

    def pump(self, max_mores=200):
        """Settle output; press space through --More-- prompts, collecting messages.
        Stops at: normal play (no prompt), a [yn] question, a menu, or game over."""
        for _ in range(max_mores):
            self.sess.settle(quiet=0.03, total=2.0)
            if not self.sess.alive():
                raise GameOver()
            snap = self.snap()
            if snap.more:
                self._collect_message(snap)
                self.sess.send(" ")
                continue
            if snap.status is None and not self.in_menu(snap) and not snap.ynq:
                # screen not fully drawn yet (or an odd overlay): wait it out
                for _ in range(40):
                    self.sess.settle(quiet=0.05, total=1.0)
                    snap = self.snap()
                    if snap.status is not None or self.in_menu(snap) or snap.more or snap.ynq:
                        break
                    time.sleep(0.05)
                if snap.more:
                    self._collect_message(snap)
                    self.sess.send(" ")
                    continue
            self._collect_message(snap)
            return snap
        return self.snap()

    def cmd(self, keys, expect_menu=False):
        """Send keys, then pump. Returns the settled snapshot."""
        self.turn_messages = []
        self.sess.send(keys)
        return self.pump()

    # ---------- prompts ----------

    def answer(self, text):
        """Answer a pending prompt (single char or string + maybe newline)."""
        self.sess.send(text)
        return self.pump()

    def maybe_dismiss_prompt(self, snap):
        """If an unexpected question/menu is on screen, escape it."""
        msg = snap.lines[0]
        if (snap.ynq or self.in_menu(snap)
                or "What do you want" in msg
                or "In what direction" in msg
                or "don't have that object" in msg
                # open getlin text prompt (e.g. "Call a scroll labeled X:")
                or (snap.cursor[1] == 0 and re.search(r":\s*$", msg.rstrip()))):
            self.sess.send(ESC)
            return self.pump()
        return snap

    # ---------- menus / text windows ----------

    def in_menu(self, snap):
        """Detect a menu or text window overlay: '(end)' or '(x of y)' marker."""
        for line in snap.lines:
            s = line.rstrip()
            if s.endswith("(end)") or re.search(r"\(\d+ of \d+\)\s*$", s):
                return True
        return False

    def read_fullscreen(self):
        """Capture all pages of a menu/text window, dismissing it. Returns list of lines."""
        out = []
        # wait until the menu marker shows up AND the screen is stable
        snap = None
        prev_lines = None
        stable = 0
        for _ in range(40):
            self.sess.settle(quiet=0.05, total=1.0)
            snap = self.snap()
            if (self.in_menu(snap) or snap.more) and snap.lines == prev_lines:
                stable += 1
                if stable >= 2:
                    break
            else:
                stable = 0
            prev_lines = snap.lines
            time.sleep(0.04)
        for _ in range(25):
            pageful = [l.rstrip() for l in snap.lines]
            out.extend(pageful)
            joined = "\n".join(pageful)
            last = re.search(r"\((\d+) of (\d+)\)", joined)
            if last and last.group(1) != last.group(2):
                self.sess.send(">")  # next page
                self.sess.settle(quiet=0.05, total=1.5)
                snap = self.snap()
                continue
            break
        # dismiss with ESC until the overlay is gone
        for _ in range(10):
            snap = self.snap()
            if not self.in_menu(snap) and not snap.more:
                break
            self.sess.send(ESC if self.in_menu(snap) else " ")
            self.sess.settle(quiet=0.05, total=1.5)
        return out

    def overview(self):
        """Run ^O and return its raw text lines."""
        self.turn_messages = []
        self.sess.send(CTRL_O)
        self.sess.settle(quiet=0.08, total=2.0)
        snap = self.snap()
        if self.in_menu(snap) or snap.more:
            return self.read_fullscreen()
        # single line answer (rare)
        txt = [snap.message]
        return txt

    def inventory(self):
        """Read inventory as {letter: description}."""
        self.turn_messages = []
        self.sess.send("i")
        lines = self.read_fullscreen()
        inv = {}
        for line in lines:
            m = re.match(r"\s*([a-zA-Z])\s+-\s+(.*\S)\s*$", line)
            if m:
                inv[m.group(1)] = m.group(2)
        # make sure no leftover overlay
        snap = self.snap()
        if self.in_menu(snap):
            self.sess.send(ESC)
            self.pump()
        return inv
