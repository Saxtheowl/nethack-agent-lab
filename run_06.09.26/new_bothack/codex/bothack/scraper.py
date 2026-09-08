"""Pure screen readers translated from scraper.clj (GPL-2.0, 2026-09-06).

The state machine returns queued delegator calls, to be delivered after a
redraw is processed. The complete game/delegator integration is separate.
"""
import re
from .catalog import data
from .frame import inverse


def effective_strength(s):
    # Upstream maps 18/00..49 to 20 and 18/50..99 to 19. Preserve, don't fix.
    if len(s) <= 2:
        return int(s)
    if s.endswith("**"):
        return 21
    return 19 if int(s[3:]) > 49 else 20


def parse_botls(lines):
    first, second = lines
    result = {}
    if match := re.search(data()["regex"]["botl1"], first, flags=re.ASCII):
        s = match.groups()
        result.update(nickname=s[0], title=s[1], stats=dict(zip(
            ("str", "str*", "dex", "con", "int", "wis", "cha"),
            (effective_strength(s[2]), s[2], *(int(v) for v in s[3:8])))),
            alignment=s[8].lower(), score=int(s[9]) if s[9] else None)
    if match := re.search(data()["regex"]["botl2"], second):
        s = match.groups()
        result.update(dict(zip(("dlvl", "xp-label", "gold", "hp", "maxhp", "pw", "maxpw", "ac", "xplvl", "xp", "turn"),
                               (s[0], s[7], *(int(v) if v is not None else None for v in (*s[1:7], *s[8:11]))))))
    result["state"] = sorted({state for substring, state in ((" Bl", "blind"), (" Stu", "stun"), (" Con", "conf"), (" Foo", "ill"), (" Il", "ill"), (" Ha", "hallu")) if substring in second})
    result["encumbrance"] = next((value for prefix, value in ((" Overl", "overloaded"), (" Overt", "overtaxed"), (" Stra", "strained"), (" Stre", "stressed"), (" Bur", "burdened")) if prefix in second), None)
    result["hunger"] = next((value for prefix, value in ((" Sat", "satiated"), (" Hun", "hungry"), (" Wea", "weak"), (" Fai", "fainting")) if prefix in second), None)
    return result


def status_drawn(frame):
    return (frame.cursor.y < 22 and bool(re.search(r" T:[0-9]+ ", frame.lines[23]))
            and (frame.lines[22][78] != " " or frame.lines[22][79] != " " or bool(re.search(r" S:[0-9]+", frame.lines[22]))))


def menu_page(frame):
    if re.search(r"\(end\) $", frame.before_cursor):
        return 1, 1
    if match := re.search(r"\(([0-9]+) of ([0-9]+)\)$", frame.before_cursor):
        return int(match[1]), int(match[2])
    return None


def menu_options(frame):
    start = len(re.search(r"^ *", frame.lines[0])[0])
    result = {}
    for line, colors in zip(frame.lines[:frame.cursor.y], frame.colors):
        if not inverse(colors[start]):
            if match := re.search(r"^(.)  ?[-+#] (.*?)\s*$", line[start:]):
                result[match[1]] = match[2]
    return result


# Ordered just like the condp forms in scraper.clj. Names denote delegator
# prompts; recognition does not itself answer them or send terminal input.
MENU_RULES = (
    (r"What do you wish to do\?", "name-menu"),
    (r"Pick up what\?", "pick-up-what"),
    (r"Put in what\?", "put-in-what"),
    (r"Take out what\?", "take-out-what"),
    (r"Loot which containers\?", "loot-what"),
    (r"Pick a skill to advance", "enhance-what"),
    (r"Current skills", "current-skills"),
    (r"What would you like to identify ", "identify-what"),
    (r"Contents of ", "inventory-list"),
    (r"possessions:", "inventory-list"),
)
PROMPT_RULES = (
    (r"^What do you want to name ", "what-name"),
    (r"^Call .*:", "what-name"),
    (r"^How much will you offer\?", "offer-how-much"),
    (r"^To what level do you want to teleport\?", "leveltele"),
    (r"^What do you want to (?:write|engrave|burn|scribble|scrawl|melt) (?:in|into|on) the (.*?) here\?", "write-what"),
    (r"^What do you want to add to the (?:writing|engraving|grafitti|scrawl|text) (?:in|on|melted into) the (.*?) here\?", "write-what"),
    (r"^For what do you wish\?", "make-wish"),
    (r"^What monster do you want to genocide\?", "genocide-monster"),
    (r"^What class of monsters do you wish to genocide\?", "genocide-class"),
    (r'^"Hello stranger, who are you\?"', "who-are-you"),
)
CHOICE_RULES = (
    (r"^What do you want to charge", "charge-what"),
    (r'^"Shall I remove|^"Take off your |let me run my fingers', "seduced-remove"),
    (r"Would you wear it for me", "seduced-puton"),
    (r"^Force the gods to be pleased\?", "force-god"),
    (r"^Really attack (.*)\?", "really-attack"),
    (r"^Are you sure you want to enter\?", "enter-gehennom"),
    (r"^What do you want to wield", "wield-what"),
    (r"^What do you want to wear", "wear-what"),
    (r"^What do you want to put on", "put-on-what"),
    (r"^What do you want to take off", "take-off-what"),
    (r"^What do you want to remove", "remove-what"),
    (r"^What do you want to ready", "ready-what"),
    (r"^What do you want to drop", "drop-single"),
    (r"^Create what kind of monster\?", "create-what-monster"),
    (r"^Die\?", "die"),
    (r"^Dry up fountain\?", "dry-fountain"),
    (r"^Dump core\?", "dump-core"),
    (r"^Advance skills without practice\?", "enhance-without-practice"),
    (r"^Do you want to keep the save file\?", "keep-save"),
    (r"^What do you want to use or apply", "apply-what"),
    (r"^What do you want to (?:name|call)\?", "name-what"),
    (r"There is .*force its lock\?", "force-lock"),
    (r"[Uu]nlock it\? |pick its lock\?", "unlock-it"),
    (r"[Ll]ock it\? ", "lock-it"),
    (r"^What do you want to read\?", "read-what"),
    (r"^What do you want to drink\?", "drink-what"),
    (r"^Drink from .*\?", "drink-here"),
    (r"^What do you want to zap\?", "zap-what"),
    (r"^Which .*, [Rr]ight or [Ll]eft\?", "which-finger"),
    (r'^"Cad!  You did [0-9]+ zorkmids worth of damage!"  Pay\?', "pay-damage"),
    (r"^There (?:is|are) ([^;]+) here; eat (?:it|one)\?", "eat-it"),
    (r"^There (?:is|are) ([^;]+) here; sacrifice (?:it|one)\?", "sacrifice-it"),
    (r"^What do you want to eat\?", "eat-what"),
    (r"^Do you wish to teleport", "do-teleport"),
    (r"^What do you want to sacrifice\?", "sacrifice-what"),
    (r"^Attach the .*to .*\?", "attach-candelabrum-candles"),
    (r"^Beware, there will be no return! Still climb\?", "still-climb"),
    (r"^You have a little trouble lifting ([^.]+)\. Continue\?", "lift-burden:light"),
    (r"^You have much trouble lifting ([^.]+)\. Continue\?", "lift-burden:heavy"),
    (r"^You have extreme difficulty lifting ([^.]+)\. Continue\?", "lift-burden:extreme"),
    (r"There is ([^,]+) here, loot it\?", "loot-it"),
    (r"Stop eating\?", "stop-eating"),
    (r"Do you want to take something out.*", "take-something-out"),
    (r"Do you wish to put something in\?", "put-something-in"),
    (r"What do you want to dip\?", "dip-what"),
    (r"What do you want to dip.* into\?", "dip-into-what"),
    (r"^Dip the .* into the .*\?", "dip-here"),
    (r"What do you want to throw\?", "throw-what"),
    (r"What do you want to write with", "write-with-what"),
    (r"What do you want to rub\?", "rub-what"),
    (r"Do you want to add to the current engraving", "append-engraving"),
    (r" offers ([0-9]+) gold pieces? for your ([^.]+)\.  ?Sell (?:it|them)\?", "sell-it"),
)


def _match_rule(rules, message):
    for pattern, name in rules:
        if match := re.search(pattern, message):
            return name, match
    raise NotImplementedError(f"Unknown prompt: {message}")


def menu_fn(head):
    return _match_rule(MENU_RULES, head)[0]


def prompt_fn(message):
    return _match_rule(PROMPT_RULES, message)[0]


def location_fn(message):
    for prefix, name in (("Where do you want to travel to?", "travel-where"),
                         ("To what location", "teleport-where"),
                         ("Pay whom", "pay-whom"),
                         ("(For instructions type a ?)", "teleport-where")):
        if message.startswith(prefix):
            return name
    raise NotImplementedError(f"Unknown location message: {message}")


def choice_call(message):
    if message.startswith("In what direction"):
        raise RuntimeError(f"Unexpected direction prompt: {message}")
    name, match = _match_rule(CHOICE_RULES, message)
    if name.startswith("lift-burden:"):
        return ("lift-burden", name.split(":")[1], match[1])
    if name == "sell-it":
        return name, int(match[1]), match[2]
    return (name, *match.groups()) if match.groups() else (name, message)


def multi_menu(head):
    return not re.search(r"What do you wish to do\?|Pick a skill", head)


def merge_menu(head):
    return bool(re.search(r"What would you like to identify", head))


def choice_prompt(frame):
    if (not status_drawn(frame) or frame.cursor.y > 1
            or frame.topline.startswith(("What monster ", "What class of monsters "))):
        return None
    # Original less-than? compares the length of the trimmed line with x.
    if frame.cursor.x > 0 and len(frame.cursor_line.rstrip(" ")) >= frame.cursor.x:
        return None
    if match := re.search(r'.*\?"?  ?\[[^\]]+\]( \(.\))?$', frame.topline_plus):
        return match[0]
    return None


def more_prompt(frame):
    if frame.before_cursor.endswith("--More--"):
        return frame.topline_plus.replace("--More--", "")
    return None


def more_list(frame):
    y = frame.cursor.y
    if ((frame.before_cursor.endswith("--More--") and y > 1
         and not frame.topline.startswith("You read:"))
            or (y > 0 and frame.before_cursor == " --More--")):
        start = max(frame.cursor.x - 9, 0)
        return [line[start:].strip() for line in frame.lines[:y]]
    return None


def location_prompt(frame):
    if match := re.search(r"^Unknown direction: ''' \(use hjkl or \.\)|.*\(For instructions type a \?\)$", frame.topline):
        return location_fn(match[0])
    return None


def text_prompt(frame):
    if frame.cursor.y <= 1 and frame.before_cursor.endswith("##'"):
        end = frame.cursor.x - 4
        if end < 0:
            raise IndexError("Negative original substring endpoint")
        return frame.topline_plus[:end].strip()
    return None


class Scraper:
    """Translation of new-scraper's closure and redraw/action reset handlers.

    feed() returns ordered (delegator-function-name, *arguments) tuples. Never
    execute those callbacks inside feed(): an action can reset the scraper.
    """

    def __init__(self, no_mark_prompt=None):
        self.player = self.head = self.items = self.menu_nextpage = None
        self.prev = no_mark_prompt.strip() if isinstance(no_mark_prompt, str) else None
        self.state = "farm" if no_mark_prompt is False else "no_mark" if no_mark_prompt is not None else "initial"
        self.calls = []

    def action_chosen(self, kind):
        kind = getattr(kind, "kind", kind)
        self.__init__("" if kind in ("autotravel", "pay") else False if kind == "farmattack" else None)

    def zap_what(self, prompt):
        self.__init__(prompt)

    throw_what = apply_what = zap_what

    def feed(self, frame):
        previous = self.__dict__.copy()
        try:
            self.calls = []
            result = getattr(self, "_" + self.state)(frame)
            if isinstance(result, str):
                self.state = result
            return self.calls
        except Exception:
            # Original refs and send calls belong to a dosync transaction.
            # An unsupported prompt must not leave a half-updated scraper.
            self.__dict__.clear()
            self.__dict__.update(previous)
            raise

    def _emit(self, name, *args):
        self.calls.append((name, *args))

    def _botl(self, f):
        self._emit("botl", parse_botls(f.botls))

    def _flush(self):
        if self.items is not None:
            self._emit("message-lines", self.items)
            self.items = None

    def _game_start(self, f):
        if f.lines[1].startswith("NetHack, Copyright") and f.before_cursor.endswith("] "):
            if f.cursor_line.startswith("There is already a game in progress under your name."):
                self._emit("write", "y\n")
            elif f.cursor_line.startswith("Shall I pick a character"):
                self._emit("choose-character")
            return True

    def _game_end(self, f):
        if re.search(r"^Do you want your possessions identified\?|^Really quit\?|^Do you want to see what you had when you died\?", f.topline):
            self._emit("write", "y")
            return True
        if (more_prompt(f) is not None and not re.search(r" level \d+|welcome .* NetHack", f.topline)
                and re.search(r"^(Fare thee well|Sayonara|Aloha|Farvel|Goodbye|Be seeing you) ", f.topline)):
            self._emit("write", " ")
            self._emit("ended")
            return True

    def _choice(self, f):
        if (text := choice_prompt(f)) is not None:
            self.menu_nextpage = None
            self._botl(f)
            self._emit(*choice_call(text))
            self.prev = f.topline_plus
            return "initial"

    def _more(self, f):
        if (items := more_list(f)) is not None:
            self.menu_nextpage = None
            self.items = ([] if self.items is None else self.items) + items
            if self.items and (len(self.items) < 2 or not self.items[1]) and not self.items[0].endswith(":"):
                self._emit("message", self.items[0])
                if len(self.items) < 2:
                    raise IndexError("Original more-list subvec requires two lines")
                self.items = self.items[2:]
            self._emit("write", " ")
            return "initial"
        if (text := more_prompt(f)) is not None:
            self.menu_nextpage = None
            if text.startswith("You don't have that object."):
                result = "choice"
            elif text.startswith("To what position do you want to be teleported?"):
                result = "location"
            else:
                self._emit("message", text)
                result = "no_mark" if text.startswith("You wrest one last ") else "initial"
            self._emit("write", " ")
            return result

    def _menu_response_start(self, f):
        if (page := menu_page(f)) and page[0] == 1:
            self.menu_nextpage = 1
            return self._menu_response(f)

    def _menu_response(self, f):
        if re.search(r"^Unknown command ' |^You are now \w+ skilled", f.topline):
            self.items = None
            return self._initial(f) or "initial"
        if (page := menu_page(f)) and self.menu_nextpage == page[0]:
            self._emit(menu_fn(self.head), self.items if merge_menu(self.head) else menu_options(f))
            if multi_menu(self.head):
                self._emit("write", " ")
            self.menu_nextpage += 1
            if page[0] == page[1]:
                self.items = None
                return "initial"
        return "menu_response"

    def _menu(self, f):
        if (page := menu_page(f)) and self.menu_nextpage is None:
            if self.items is None:
                self.head = None if any(inverse(c) for c in f.colors[0]) else f.topline
                self.items = {}
            self.items = {**self.items, **menu_options(f)}
            if page[0] != page[1]:
                self._emit("write", " ")
                return True
            if self.head is not None:
                if page[1] == 1:
                    return self._menu_response_start(f)
                self._emit("write", "<" * (page[1] - 1))
                return "menu_response_start"
            self._emit("inventory-list", self.items)
            self.items = None
            self._emit("write", " ")
            return "initial"

    def _direction(self, f):
        if f.cursor.y == 0 and re.search(r"^In what direction.*\?", f.topline):
            self._botl(f)
            self._emit("what-direction", f.topline)
            return "initial"

    def _prompt(self, f):
        if (msg := text_prompt(f)) is not None:
            self._botl(f)
            self._emit("write", "\b" * 3)
            self._emit(prompt_fn(msg), msg)
            return "initial"

    def _location(self, f):
        if (event := location_prompt(f)) is not None:
            self._botl(f)
            if "travel to?" not in f.topline:
                self._emit("know-position", f)
            self._flush()
            self._emit("write", "-")
            self._emit(event)
            return "initial"

    def _initial(self, f):
        if self.prev == f.topline_plus and "; eat " not in self.prev:
            return True
        self.prev = None
        for handler in (self._game_start, self._game_end, self._more, self._menu, self._choice):
            if result := handler(f):
                return result
        if status_drawn(f):
            self._emit("write", "##'")
            return "marked"

    @staticmethod
    def _undrawn(f, text):
        length = min(len(f.topline), len(text))
        return f.topline[:length] == text[:length]

    def _no_mark(self, f):
        if self.prev == f.topline and (not re.search(r"What do you want to (?:zap|use or apply)\?", self.prev) or f.cursor.y == 0):
            return True
        self.prev = None
        return (self._direction(f) or self._undrawn(f, "In what direction") or self._location(f)
                or self._undrawn(f, "Pay whom") or self._undrawn(f, "Where do you want") or self._initial(f))

    def _marked(self, f):
        for handler in (self._game_end, self._more, self._menu, self._choice, self._prompt):
            if result := handler(f):
                return result
        if f.cursor.y == 0 and f.before_cursor.endswith("# '"):
            self._emit("write", "\x1b\x1b")
            return "initial"
        return self._farm(f)

    def _lastmsg_clear(self, f):
        if not f.topline:
            self._emit("write", "\x10\x10")
            return "lastmsg_get"

    def _lastmsg_get(self, f):
        if f.topline == "# #" and f.cursor.y < 22:
            self.player = f.cursor
            self._emit("write", "\x10")
            return "lastmsg_action"

    def _lastmsg_action(self, f):
        if more_prompt(f) is not None and f.extra_topline_cursor:
            self._emit("write", "\n##\n\n")
            return "lastmsg_clear"
        if f.topline == "# #":
            self.player = f.cursor
            return True
        if f.cursor == self.player:
            if not f.topline.startswith("#"):
                self._emit("message", f.topline)
            self._botl(f)
            self._emit("know-position", f)
            self._flush()
            self._emit("full-frame", f)
            return "sink"

    def _farm(self, f):
        if f.cursor.y == 0 and f.before_cursor.endswith("# #'"):
            self._emit("write", "\b\n\n")
            return "lastmsg_clear"

    def _sink(self, f):
        return None
