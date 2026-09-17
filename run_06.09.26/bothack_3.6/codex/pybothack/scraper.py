"""Port of bothack.scraper.

The screen scraper handles redraw events, tries to determine when the frame is
completely drawn and sends off higher-level events.  This is BotHack's
synchronization mechanism with NetHack (the "##'" marker trick) and is
reproduced here step for step.
"""
import os
import collections
import time
import logging
import re

from .action import typekw
from .clj import into_map
from .frame import (before_cursor, before_cursor_p, botls, cursor_line,
                    extra_topline_cursor, inverse, nth_line, topline,
                    topline_plus, wrapped_cursor)
from .util import (BACKSPACE, ESC, ctrl, effective_str, firstv, less_than,
                   parse_int, re_first_group, re_first_groups, re_seq, secondv,
                   str_kw)

log = logging.getLogger('bothack.scraper')


def _status_drawn(frame):
    """Does the status line look fully drawn?"""
    last_line = nth_line(frame, 23)
    name_line = nth_line(frame, 22)
    return bool(frame.cursor.y < 22
                and re_seq(r' T:[0-9]+ ', last_line)
                and (name_line[78] != ' ' or name_line[79] != ' '
                     or re_seq(r' S:[0-9]+', name_line)))


def _menu_head(frame):
    if not any(inverse(c) for c in frame.colors[0]):
        return topline(frame)
    return None


def _menu_page(frame):
    bc = before_cursor(frame)
    if re_seq(r'\(end\) $', bc):
        return [1, 1]
    g = re_first_groups(r'\(([0-9]+) of ([0-9]+)\)$', bc)
    if g:
        return [int(g[0]), int(g[1])]
    return None


def _menu_curpage(frame):
    p = _menu_page(frame)
    return p[0] if p else None


def _menu_end(frame):
    p = _menu_page(frame)
    return p[0] == p[1] if p else None


def _menu(frame):
    return _menu_page(frame) is not None


def _menu_line(start, line, colors):
    if inverse(colors[start]):
        return None
    g = re_first_groups(r'^(.)  ?[-+#] (.*?)\s*$', line[start:])
    if g:
        return (g[0][0], g[1])
    return None


def _menu_options(frame):
    """(into {} (map menu-line ...)) - the options on the current page.

    `into` builds through a *transient* array map: it appends, keeping screen
    order, until the **ninth** entry promotes it to a hash map, after which
    `vals`/`keys` walk in the hash order of the slot Characters.  A full
    inventory page has well over nine entries, and the order is observable:
    `take-out-what` appends `(map label->item (vals options))` to the
    container's `:items`, and `pick-up-what` walks `options` while `disj`-ing
    labels off its wanted set, so with two identically labelled stacks the order
    picks which slot it takes.
    """
    m = re.match(r'^ *', nth_line(frame, 0))
    xstart = len(m.group(0)) if m else 0
    yend = frame.cursor.y
    pairs = []
    for line, colors in zip(frame.lines[:yend], frame.colors[:yend]):
        r = _menu_line(xstart, line, colors)
        if r:
            pairs.append((r[0], r[1]))
    return into_map(pairs)


_MENU_FNS = [
    (r"What do you wish to do\?|What do you want to name\?", 'name_menu'),
    (r"Pick up what\?", 'pick_up_what'),
    (r"Put in what\?", 'put_in_what'),
    (r"Take out what\?", 'take_out_what'),
    (r"Loot which containers\?", 'loot_what'),
    (r"Pick a skill to advance", 'enhance_what'),
    (r"Current skills", 'current_skills'),
    (r"What would you like to identify ", 'identify_what'),
    (r"Contents of ", 'inventory_list'),
    (r"possessions:", 'inventory_list'),
]


def _menu_fn(head):
    for pat, name in _MENU_FNS:
        if re_seq(pat, head):
            return name
    raise NotImplementedError("Unknown menu " + head)


def _multi_menu(head):
    return not re_seq(r"What do you wish to do\?|What do you want to name\?|Pick a skill", head)


def _merge_menu(head):
    return re_seq(r"What would you like to identify", head)


def _choice_prompt(frame):
    if not _status_drawn(frame):
        return None
    if topline(frame).startswith("What monster "):
        return None
    if topline(frame).startswith("What class of monsters "):
        return None
    if frame.cursor.y > 1:
        return None
    x = frame.cursor.x
    if x > 0:
        trimmed = re_first_group(r'^(.*[^ ]) *$', cursor_line(frame))
        if not less_than(x, trimmed or ""):
            return None
    m = re.search(r'.*\?"?  ?\[[^\]]+\]( \(.\))?$', topline_plus(frame))
    return m.group(0) if m else None


def _more_prompt_p(frame):
    return before_cursor_p(frame, "--More--")


def _more_items(frame):
    xstart = max(frame.cursor.x - 9, 0)
    yend = frame.cursor.y
    return [l[xstart:].strip() for l in frame.lines[:yend]]


def _more_list_prompt(frame):
    y = frame.cursor.y
    return bool((_more_prompt_p(frame) and y > 1
                 and not topline(frame).startswith("You read:"))
                or (y > 0 and before_cursor(frame) == " --More--"))


def _more_list(frame):
    if _more_list_prompt(frame):
        return _more_items(frame)
    return None


def _more_prompt(frame):
    if _more_prompt_p(frame):
        return re.sub(r'--More--', '', topline_plus(frame))
    return None


def _location_fn(msg):
    for pre, name in [("Where do you want to travel to?", 'travel_where'),
                      ("To what location", 'teleport_where'),
                      ("Pay whom", 'pay_whom'),
                      ("(For instructions type a ?)", 'teleport_where')]:
        if msg.startswith(pre):
            return name
    raise NotImplementedError("unknown location message" + msg)


LOCATION_RE = (r"^Unknown direction: ''' \(use hjkl or \.\)|"
               r".*\(For instructions type a \?\)$")


def _location_prompt(frame):
    if os.getenv('BH_EVENTS') and topline(frame).startswith('Where do you want to travel to?'):
        return 'travel_where'
    m = re.search(LOCATION_RE, topline(frame))
    if m:
        return _location_fn(m.group(0))
    return None


def _prompt(frame):
    if frame.cursor.y <= 1 and before_cursor_p(frame, "##'"):
        return topline_plus(frame)[:frame.cursor.x - 4].strip()
    return None


_PROMPT_FNS = [
    (r"^What do you want to name ", 'what_name'),
    (r"^Call .*:", 'what_name'),
    (r"^How much will you offer\?", 'offer_how_much'),
    (r"^To what level do you want to teleport\?", 'leveltele'),
    (r"^What do you want to (?:write|engrave|burn|scribble|scrawl|melt) "
     r"(?:in|into|on) the (.*?) here\?", 'write_what'),
    (r"^What do you want to add to the (?:writing|engraving|grafitti|scrawl|"
     r"text) (?:in|on|melted into) the (.*?) here\?", 'write_what'),
    (r"^For what do you wish\?", 'make_wish'),
    (r"^What monster do you want to genocide\?", 'genocide_monster'),
    (r"^What class of monsters do you wish to genocide\?", 'genocide_class'),
    (r"^\"Hello stranger, who are you\?\"", 'who_are_you'),
]


def _prompt_fn(msg):
    for pat, name in _PROMPT_FNS:
        if re_seq(pat, msg):
            return name
    raise NotImplementedError("unknown prompt msg " + msg)


_CHOICE_FNS = [
    (r"^Are you sure you want to pray\?", 'confirm_pray'),
    (r"^In what direction", '__direction_error__'),
    (r"^What do you want to charge", 'charge_what'),
    (r"^\"Shall I remove|^\"Take off your |let me run my fingers",
     'seduced_remove'),
    (r"Would you wear it for me", 'seduced_puton'),
    (r"^Force the gods to be pleased\?", 'force_god'),
    (r"^Really attack (.*)\?", ('really_attack', 1)),
    (r"^Are you sure you want to enter\?", 'enter_gehennom'),
    (r"^What do you want to wield", 'wield_what'),
    (r"^What do you want to wear", 'wear_what'),
    (r"^What do you want to put on", 'put_on_what'),
    (r"^What do you want to take off", 'take_off_what'),
    (r"^What do you want to remove", 'remove_what'),
    (r"^What do you want to ready", 'ready_what'),
    (r"^What do you want to drop", 'drop_single'),
    (r"^Create what kind of monster\?", 'create_what_monster'),
    (r"^Die\?", 'die'),
    (r"^Dry up fountain\?", 'dry_fountain'),
    (r"^Dump core\?", 'dump_core'),
    (r"^Advance skills without practice\?", 'enhance_without_practice'),
    (r"^Do you want to keep the save file\?", 'keep_save'),
    (r"^What do you want to use or apply", 'apply_what'),
    (r"^What do you want to (?:name|call)\?", 'name_what'),
    (r"There is .*force its lock\?", 'force_lock'),
    (r"[Uu]nlock it\? |pick its lock\?", 'unlock_it'),
    (r"[Ll]ock it\? ", 'lock_it'),
    (r"^What do you want to read\?", 'read_what'),
    (r"^What do you want to drink\?", 'drink_what'),
    (r"^Drink from .*\?", 'drink_here'),
    (r"^What do you want to zap\?", 'zap_what'),
    (r"^Which .*, [Rr]ight or [Ll]eft\?", 'which_finger'),
    (r"^\"Cad!  You did [0-9]+ zorkmids worth of damage!\"  Pay\?",
     'pay_damage'),
    (r"^There (?:is|are) ([^;]+) here; eat (?:it|one)\?", ('eat_it', 1)),
    (r"^There (?:is|are) ([^;]+) here; sacrifice (?:it|one)\?",
     ('sacrifice_it', 1)),
    (r"^What do you want to eat\?", 'eat_what'),
    (r"^Do you wish to teleport", 'do_teleport'),
    (r"^What do you want to sacrifice\?", 'sacrifice_what'),
    (r"^Attach the .*to .*\?", 'attach_candelabrum_candles'),
    (r"^Beware, there will be no return! Still climb\?", 'still_climb'),
    (r"^You have a little trouble lifting ([^.]+)\. Continue\?",
     ('lift_burden', 'light')),
    (r"^You have much trouble lifting ([^.]+)\. Continue\?",
     ('lift_burden', 'heavy')),
    (r"^You have extreme difficulty lifting ([^.]+)\. Continue\?",
     ('lift_burden', 'extreme')),
    (r"There is ([^,]+) here, loot it\?", ('loot_it', 1)),
    (r"Stop eating\?", 'stop_eating'),
    (r"Do you want to take something out.*", 'take_something_out'),
    (r"Do you wish to put something in\?", 'put_something_in'),
    (r"What do you want to dip\?", 'dip_what'),
    (r"What do you want to dip.* into\?", 'dip_into_what'),
    (r"^Dip the .* into the .*\?", 'dip_here'),
    (r"What do you want to throw\?", 'throw_what'),
    (r"What do you want to write with", 'write_with_what'),
    (r"What do you want to rub\?", 'rub_what'),
    (r"Do you want to add to the current engraving", 'append_engraving'),
    (r" offers ([0-9]+) gold pieces? for your ([^.]+)\.  ?Sell (?:it|them)\?",
     ('sell_it', 'sell')),
]


def _choice_call(msg):
    """Returns (method-name, args) for the choice prompt."""
    log.debug("choice: %s", msg)
    for pat, target in _CHOICE_FNS:
        g = re_first_groups(pat, msg)
        if g is None:
            continue
        if target == '__direction_error__':
            raise RuntimeError("Unexpected direction prompt: " + msg)
        if isinstance(target, tuple):
            name, kind = target
            if kind == 1:
                return (name, [g[0] if isinstance(g, list) else g])
            if kind == 'sell':
                return (name, [int(g[0]), g[1]])
            return (name, [kind, g[0] if isinstance(g, list) else g])
        return (target, [msg])
    raise NotImplementedError("unimplemented choice prompt: " + msg)


def _game_over(frame):
    return re_seq(r"^Do you want your possessions identified\?|"
                  r"^Really quit\?|"
                  r"^Do you want to see what you had when you died\?",
                  topline(frame))


def _goodbye(frame):
    return bool(_more_prompt_p(frame)
                and not re_seq(r" level \d+", topline(frame))
                and not re_seq(r"welcome .* NetHack", topline(frame))
                and re_seq(r"^(Fare thee well|Sayonara|Aloha|Farvel|Goodbye|"
                           r"Be seeing you) ", topline(frame)))


def _game_beginning(frame):
    return (nth_line(frame, 1).startswith("NetHack, Copyright")
            and before_cursor_p(frame, "] "))


BOTL1_RE = (r"^(\w+)?(?: the (.*[^ ]))? *St:(\d+(?:\/(?:\*\*|\d+))?) Dx:(\d+) "
            r"Co:(\d+) In:(\d+) Wi:(\d+) Ch:(\d+)\s*(\w+)\s*(?:S:(\d+))?.*$")

BOTL2_RE = (r"^(Dlvl:\d+|Home \d+|Fort Ludios|End Game|Astral Plane|Astral|Earth|Air|Fire|Water)\s+"
            r"(?:\$|\*):(\d+)\s+HP:(\d+)\((\d+)\)\s+Pw:(\d+)\((\d+)\)\s+"
            r"AC:([0-9-]+)\s+(Exp|Xp|HD):(\d+)(?:\/(\d+))?\s+T:(\d+)\s+(.*?)"
            r"\s*$")


def parse_botls(lines):
    botl1, botl2 = lines[0], lines[1]
    res = {}
    s = re_first_groups(BOTL1_RE, botl1)
    if s:
        res.update({
            'nickname': s[0],
            'title': s[1],
            'stats': {'str': effective_str(s[2]), 'str*': s[2],
                      'dex': parse_int(s[3]), 'con': parse_int(s[4]),
                      'int': parse_int(s[5]), 'wis': parse_int(s[6]),
                      'cha': parse_int(s[7])},
            'alignment': str_kw(s[8]),
            'score': parse_int(s[9]) if s[9] is not None else None,
        })
    else:
        log.error("failed to parse botl1 %r", botl1)
    s = re_first_groups(BOTL2_RE, botl2)
    if s:
        vals = [s[0], parse_int(s[1]), parse_int(s[2]), parse_int(s[3]),
                parse_int(s[4]), parse_int(s[5]), parse_int(s[6]), s[7],
                parse_int(s[8]), parse_int(s[9]) if s[9] is not None else None,
                parse_int(s[10])]
        res.update(dict(zip(['dlvl', 'gold', 'hp', 'maxhp', 'pw', 'maxpw',
                             'ac', 'xp-label', 'xplvl', 'xp', 'turn'], vals)))
    else:
        log.error("failed to parse botl2 %r", botl2)
    res['state'] = set(state for substr, state in
                       ((" Bl", 'blind'), (" Stu", 'stun'), (" Con", 'conf'),
                        (" Foo", 'ill'), (" Il", 'ill'), (" Ha", 'hallu'))
                       if substr in botl2)
    res['encumbrance'] = None
    for substr, enc in ((" Overl", 'overloaded'), (" Overt", 'overtaxed'),
                        (" Stra", 'strained'), (" Stre", 'stressed'),
                        (" Bur", 'burdened')):
        if substr in botl2:
            res['encumbrance'] = enc
            break
    res['hunger'] = None
    for substr, h in ((" Sat", 'satiated'), (" Hun", 'hungry'),
                      (" Wea", 'weak'), (" Fai", 'fainting')):
        if substr in botl2:
            res['hunger'] = h
            break
    # NB: the original's parse-botls emits no :blind key either, so
    # update-player always clears :ext-blind - reproduced faithfully.
    return res


def _emit_botl(delegator, frame):
    delegator.botl(parse_botls(botls(frame)))


def _undrawn(frame, what):
    """Can the topline possibly be this not-yet-drawn message?"""
    t = topline(frame)
    n = min(len(t), len(what))
    return t[:n] == what[:n]


def new_scraper(delegator, no_mark_prompt=None):
    st = {'player': None, 'head': None, 'items': None, 'menu_nextpage': None,
          'lastmsg_waits': 0,
          'lastmsg_since': None,
          'prev': (no_mark_prompt.strip()
                   if isinstance(no_mark_prompt, str) else None)}

    def flush_more_list():
        if st['items'] is not None:
            log.debug("Flushing --More-- list")
            delegator.message_lines(st['items'])
            st['items'] = None

    def handle_game_start(frame):
        if _game_beginning(frame):
            log.debug("Handling game start")
            cl = cursor_line(frame)
            if cl.startswith("There is already a game in progress under your "
                             "name."):
                delegator.send_write("y\n")     # destroy old game
            elif cl.startswith("Shall I pick a character"):
                delegator.choose_character()
            return True
        return None

    def handle_choice_prompt(frame):
        text = _choice_prompt(frame)
        if text:
            log.debug("Handling choice prompt")
            st['menu_nextpage'] = None
            _emit_botl(delegator, frame)
            name, args = _choice_call(text)
            getattr(delegator, name)(*args)
            st['prev'] = topline_plus(frame)
            return initial
        return None

    def handle_more(frame):
        item_list = _more_list(frame)
        if item_list is not None:
            log.debug("Handling --More-- list")
            st['menu_nextpage'] = None
            if st['items'] is None:
                st['items'] = []
            st['items'] = st['items'] + list(item_list)
            if (secondv(st['items']) in (None, "")
                    and not (firstv(st['items']) or "").endswith(":")):
                delegator.message(firstv(st['items']))
                st['items'] = st['items'][2:]
            delegator.send_write(" ")
            return initial
        text = _more_prompt(frame)
        if text is not None:
            log.debug("Handling --More-- prompt")
            st['menu_nextpage'] = None
            if re_seq(r"^You don't have that object\.", text):
                res = handle_choice_prompt
            elif re_seq(r"^To what position do you want to be teleported\?",
                        text):
                res = handle_location
            elif re_seq(r"^You wrest one last ", text):
                delegator.message(text)
                res = no_mark
            else:
                delegator.message(text)
                res = initial
            delegator.send_write(" ")
            return res
        return None

    def handle_menu_response_start(frame):
        if _menu(frame) and _menu_curpage(frame) == 1:
            log.debug("first page menu response")
            st['menu_nextpage'] = 1
            return handle_menu_response(frame)
        log.debug("menu response start - not yet rewound")
        return None

    def handle_menu_response(frame):
        if re_seq(r"^Unknown command ' |^You are now \w+ skilled",
                  topline(frame)):
            log.debug("enhance menu done")
            st['items'] = None
            return initial(frame) or initial
        if _menu(frame) and st['menu_nextpage'] == _menu_curpage(frame):
            log.debug("responding to menu page %s options %s",
                      st['menu_nextpage'], st['items'])
            options = (st['items'] if _merge_menu(st['head'])
                       else _menu_options(frame))
            getattr(delegator, _menu_fn(st['head']))(options)
            if _multi_menu(st['head']):
                delegator.send_write(" ")
            st['menu_nextpage'] += 1
            if _menu_end(frame):
                log.debug("last menu page response done")
                st['items'] = None
                return initial
        log.debug("menu reponse - continuing")
        return handle_menu_response

    def handle_menu(frame):
        if _menu(frame) and st['menu_nextpage'] is None:
            log.debug("Handling menu")
            head = _menu_head(frame) or ""
            if "Do what with " in head:
                # 3.6.2+ replaced sequential y/n bag prompts with this menu.
                take = delegator._invoke_prompt('take_something_out', head)
                put = delegator._invoke_prompt('put_something_in', head)
                options = _menu_options(frame)
                key = 'b' if take and put else 'o' if take else 'i' if put else 'q'
                delegator.send_write(key if key in options else 'q')
                st['prev'] = topline_plus(frame)
                return initial
            if st['items'] is None:
                st['head'] = _menu_head(frame)
                log.debug("Menu start")
                st['items'] = {}
            st['items'] = dict(st['items'], **_menu_options(frame))
            if not _menu_end(frame):
                delegator.send_write(" ")
                return None
            log.debug("Menu end")
            if st['head']:
                cur, end = _menu_page(frame)
                if end == 1:
                    return handle_menu_response_start(frame)
                delegator.send_write("<" * (end - 1))     # rewind menu
                return handle_menu_response_start
            delegator.inventory_list(st['items'])
            st['items'] = None
            delegator.send_write(" ")
            return initial
        return None

    def handle_direction(frame):
        if frame.cursor.y == 0 and re_seq(r"^In what direction.*\?",
                                          topline(frame)):
            log.debug("Handling direction")
            _emit_botl(delegator, frame)
            delegator.what_direction(topline(frame))
            return initial
        return None

    def handle_prompt(frame):
        msg = _prompt(frame)
        if msg is not None:
            log.debug("prompt: %s", msg)
            _emit_botl(delegator, frame)
            delegator.send_write(BACKSPACE * 3)
            getattr(delegator, _prompt_fn(msg))(msg)
            return initial
        return None

    def handle_game_end(frame):
        if _game_over(frame):
            delegator.send_write("y")
            return True
        if _goodbye(frame):
            delegator.send_write(" ")
            delegator.ended()
            return True
        return None

    def handle_location(frame):
        ev = _location_prompt(frame)
        if ev:
            log.debug("Handling location")
            _emit_botl(delegator, frame)
            if "travel to?" not in topline(frame):
                delegator.know_position(frame)
            flush_more_list()
            # nuke topline for the next redraw to stop repeated botl/map
            # updates while the prompt is active causing multiple prompts
            delegator.send_write("-")
            getattr(delegator, ev)()
            return initial
        return None

    def sink(frame):
        log.debug("sink discarding redraw")
        return None

    def initial(frame):
        log.debug("initial scraper, prev = %s", st['prev'])
        if (st['prev'] is not None and st['prev'] == topline_plus(frame)
                and "; eat " not in st['prev']):
            return True
        st['prev'] = None
        for f in (handle_game_start, handle_game_end, handle_more, handle_menu,
                  handle_direction, handle_choice_prompt):
            r = f(frame)
            if r:
                return r
        if os.getenv('BH_EVENTS'):
            r = handle_direction(frame) or handle_location(frame)
            if r:
                return r
            if frame.cursor.y <= 1:
                msg = topline_plus(frame).strip()
                for pat, name in _PROMPT_FNS:
                    if re_seq(pat, msg):
                        getattr(delegator, name)(msg)
                        st['prev'] = msg
                        return initial
            return None
        # if the status line is drawn, nothing above may react to "##"
        if _status_drawn(frame):
            delegator.send_write("##'")
            return marked
        log.debug("expecting further redraw")
        return None

    def no_mark(frame):
        """In contexts where ##' could be destructive (direction prompts) wait
        until something appears that provably isn't the start of a direction
        prompt, then send the marker."""
        log.debug("no-mark maybe direction/location prompt, prev = %s",
                  st['prev'])
        if (st['prev'] is not None and st['prev'] == topline(frame)
                and (not re_seq(r"What do you want to (?:zap|use or apply)\?",
                                st['prev'])
                     or frame.cursor.y == 0)):
            return True
        st['prev'] = None
        log.debug("no-mark - new topline: %s", topline(frame))
        r = handle_direction(frame)
        if r:
            return r
        if _undrawn(frame, "In what direction"):
            return True
        r = handle_location(frame)
        if r:
            return r
        if _undrawn(frame, "Pay whom"):
            return True
        if _undrawn(frame, "Where do you want"):
            return True
        log.debug("no-mark - not direction/location prompt")
        return initial(frame)

    def marked(frame):
        for f in (handle_game_end, handle_more, handle_menu,
                  handle_choice_prompt, handle_prompt):
            r = f(frame)
            if r:
                return r
        if frame.cursor.y == 0 and before_cursor_p(frame, "# '"):
            delegator.send_write(ESC + ESC)
            return initial
        if frame.cursor.y == 0 and before_cursor_p(frame, "# #'"):
            delegator.send_write(BACKSPACE + "\n\n")
            return lastmsg_clear
        log.debug("marked expecting further redraw")
        return None

    def lastmsg_clear(frame):
        if topline(frame) == "":
            delegator.send_write(ctrl('p') + ctrl('p'))
            return lastmsg_get
        return None

    #: How many redraws `lastmsg+action` may wait before forcing progress.
    #: A legitimate wait is one to three; this is far above that and only ever
    #: fires when `player` has been poisoned (see lastmsg_action).
    def lastmsg_get(frame):
        # (when (and (= "# #" (topline frame)) (< (-> frame :cursor :y) 22)) ...)
        #
        # DELIBERATE DEVIATION, and the only one in this file: the original's
        # guard is `y < 22`, which also admits y = 0.  `player` is meant to be
        # the hero's position on the map, and NetHack restores the cursor there
        # after writing a topline - but on rare part-drawn frames the topline is
        # written and the cursor has not moved yet, so it sits just after the
        # text at (3, 0).  Recording that traps `lastmsg+action` for good: it
        # waits for the cursor to come back to (3, 0) while every later frame
        # has it on the map, and the game hangs until quit-when-idle ends it.
        #
        # Measured: one game in five stalled this way, always the deepest ones -
        # Dlvl 15-18 with scores up to 179 008 - and it is not load-related (it
        # reproduces with two games on four cores).  Requiring the cursor to be
        # off the topline changes nothing else: the replay gate stays at
        # 1 145 222/1 145 222 identical keystrokes over fifteen captures, so this
        # branch never fires on any recorded game of the original.
        if topline(frame) == "# #" and 0 < frame.cursor.y < 22:
            st['player'] = frame.cursor
            # `lastmsg_waits` is deliberately NOT reset here.  It used to be,
            # and that made the bound below unreachable: the observed stall is
            # not the scraper sitting in `lastmsg+action`, it is the whole
            # protocol cycling - lastmsg_get -> lastmsg+action -> sink ->
            # marked -> lastmsg_clear -> lastmsg_get - so every lap cleared the
            # counter.  Measured: "lastmsg stuck" was logged **zero** times
            # across ~40 games containing 14 of these stalls.  A safeguard that
            # has never fired is not a safeguard.
            delegator.send_write(ctrl('p'))
            return lastmsg_action
        return None

    def lastmsg_action(frame):
        if _more_prompt_p(frame) and extra_topline_cursor(frame):
            delegator.send_write("\n##\n\n")
            return lastmsg_clear
        if topline(frame) == "# #":
            # (or ...
            #     (if (= "# #" (topline frame)) (ref-set player (:cursor frame)))
            #     (when (= (:cursor frame) @player) ... sink)
            #     ...)
            # That `if` is a *clause of the or*, and `ref-set` returns the
            # Position it just set - truthy - so the or short-circuits here.
            # `apply-scraper` keeps the current scraper for any non-function
            # return, so the original sets the player position and waits for the
            # next redraw instead of falling through to the sink branch.
            #
            # Falling through makes the bot choose its action one redraw earlier
            # than the original.  That is invisible while consecutive redraws
            # carry the same picture, and decisive when they do not: during a
            # hallucination episode NetHack re-randomises every monster glyph on
            # every redraw, so one redraw of slack becomes a different monster
            # map.  Measured on seed 40002 at keystroke 63137, where the
            # original had already consumed three "# #" frames.
            st['player'] = frame.cursor
            return None
        if frame.cursor == st['player']:
            # a normal pass completed: this is the only place the wait is
            # considered satisfied, so it is the only place the bound resets
            st['lastmsg_waits'] = 0
            st['lastmsg_since'] = None
            if not topline(frame).startswith("#"):
                delegator.message(topline(frame))
            _emit_botl(delegator, frame)
            delegator.know_position(frame)
            flush_more_list()
            delegator.full_frame(frame)
            return sink
        # The two conditions that could have moved this on, so a stall here
        # says which one failed rather than only that it happened.
        # DELIBERATE DEVIATION: the original waits here with no bound, and a
        # poisoned `player` makes that wait permanent.
        #
        # `player` is recorded in `lastmsg_get` and re-recorded by the "# #"
        # clause above, which exists to *correct* it from a later frame.  When a
        # "# #" frame carries a **stale** cursor the correction goes the wrong
        # way and no later frame can ever match.  Seen exactly:
        #     lastmsg_get     cursor=(59,20) topline=''      -> player=(59,20)
        #     lastmsg_action  cursor=(58,20) topline='# #'   -> player=(58,20)
        #     lastmsg_action  cursor=(59,20) topline='#'     -> stuck for good
        # The bot then sits until quit-when-idle ends the game, and it is the
        # long games that lose the most by it.
        #
        # Rather than guess which frame is authoritative, keep the original's
        # logic and bound the wait: a legitimate wait here is one to three
        # frames, so after many more than that, proceed as the matching branch
        # would.  Normal play never reaches the bound - the replay gate stays at
        # 1 182 022/1 182 022 identical keystrokes over fifteen recordings.
        st['lastmsg_waits'] += 1
        if st['lastmsg_since'] is None:
            st['lastmsg_since'] = time.time()
        waited = time.time() - st['lastmsg_since']
        if (st['lastmsg_waits'] > LASTMSG_WAIT_LIMIT
                or waited > LASTMSG_WAIT_SECONDS):
            log.warning("lastmsg stuck for %d redraws / %.0fs "
                        "(cursor=%r player=%r); proceeding",
                        st['lastmsg_waits'], waited, frame.cursor,
                        st['player'])
            st['lastmsg_waits'] = 0
            st['lastmsg_since'] = None
            if not topline(frame).startswith("#"):
                delegator.message(topline(frame))
            _emit_botl(delegator, frame)
            delegator.know_position(frame)
            flush_more_list()
            delegator.full_frame(frame)
            return sink
        log.debug("lastmsg expecting further redraw (cursor=%r player=%r "
                  "topline=%r)", frame.cursor, st['player'],
                  topline(frame)[:40])
        return None

    def farm(frame):
        if frame.cursor.y == 0 and before_cursor_p(frame, "# #'"):
            delegator.send_write(BACKSPACE + "\n\n")
            return lastmsg_clear
        log.debug("farm expecting further redraw")
        return None

    if no_mark_prompt is False:
        return farm
    if no_mark_prompt is not None:
        return no_mark
    return initial


#: The last few scraper transitions, for a post-mortem when the bot stops
#: acting.  A stall leaves no trace in the INFO log - its last line is an
#: ordinary action - and running everything at DEBUG costs about 1.2 GB for a
#: three-hour game.  This keeps only the context that matters, in memory, and
#: main.py's watchdog dumps it when no action has been chosen for a while.
RECENT = collections.deque(maxlen=60)

#: see lastmsg_action
LASTMSG_WAIT_LIMIT = 40

#: Wall-clock companion to LASTMSG_WAIT_LIMIT.  The redraw count alone cannot
#: see the failure that actually happens: the protocol cycles through
#: lastmsg_get on every lap, and a per-state counter is meaningless when the
#: state is re-entered.  A legitimate pass takes milliseconds, so twenty
#: seconds is three orders of magnitude of headroom - replays finish whole
#: games in less time than this, which is why the gate is unaffected.
LASTMSG_WAIT_SECONDS = 20.0


def recent_transitions():
    """The ring buffer as formatted lines, oldest first."""
    now = time.time()
    return ["%7.1fs ago  %-16s cursor=(%2d,%2d) topline=%r"
            % (now - r[4], r[0], r[1], r[2], r[3]) for r in RECENT]


def _apply_scraper(orig_scraper, delegator, frame):
    current = orig_scraper if orig_scraper else new_scraper(delegator)
    nxt = current(frame)
    nxt = nxt if callable(nxt) else current
    # Timestamped: a dump of RECENT is only useful if the reader can tell which
    # transitions happened *after* the event being investigated.  Without this,
    # a 60-entry deque read at the end of quit-when-idle's grace window cannot
    # distinguish "the scraper recovered and the bot still chose nothing" from
    # "the scraper never moved" - which is exactly the question the dump exists
    # to answer, and it went unanswered twice for want of a clock.
    RECENT.append((getattr(nxt, '__name__', str(nxt)),
                   frame.cursor.x, frame.cursor.y, topline(frame)[:46],
                   time.time()))
    return nxt


def scraper_handler(scraper_ref, delegator):
    """scraper_ref is an Atom holding the current scraper function."""
    from .delegator import Handler

    def set_no_mark(prompt):
        scraper_ref.reset(new_scraper(delegator, prompt))
        log.debug("no-mark scraper, prev = %s", prompt)
        return None

    def action_chosen(act):
        t = typekw(act)
        if t in ('autotravel', 'pay'):
            set_no_mark("")
        elif t == 'farmattack':
            set_no_mark(False)
        else:
            scraper_ref.reset(None)      # escape sink
        log.debug("reset scraper for %s", t)

    def redraw(frame):
        nxt = _apply_scraper(scraper_ref.deref(), delegator, frame)
        scraper_ref.reset(nxt)
        log.debug("next scraper: %s", getattr(nxt, '__name__', nxt))

    return Handler(zap_what=set_no_mark, throw_what=set_no_mark,
                   apply_what=set_no_mark, action_chosen=action_chosen,
                   redraw=redraw)
