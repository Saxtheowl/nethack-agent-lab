"""NetHack 3.6.7 interaction differences, translated into the questions the
BotHack handlers (written for 3.4.3) already know how to answer.

Every translation is explicit and named, so its use can be counted in the
game logs.  A translation returns the engine answer to send, or None when it
does not apply.
"""
import logging
import re

log = logging.getLogger('bothack.compat36')


def ask(delegator, name, *args):
    """Ask the handlers a prompt question and return their raw answer
    (None if nobody answers)."""
    try:
        return delegator._invoke_prompt(name, *args)
    except RuntimeError:
        return None


def _items_by_acc(req):
    return {it[2]: it for it in (req.items or []) if it[1] and it[2]}


def menu_container(bridge, req):
    """3.6: '#loot' / apply on a container opens "Do what with <box>?"
    (3.4.3 asked "Do you want to take something out of ...? [ynq]" and then
    "Do you wish to put something in? [ynq]")."""
    head = req.prompt or ''
    if not re.search(r"Do what with |is empty\.  Do what with it\?", head):
        return None
    d = bridge.bh.delegator
    m = re.match(r"^(.*? is empty\.)  Do what with it\?", head)
    if m:
        # 3.4.3 printed this as a message; the container handlers use it to
        # learn that the container holds nothing
        d.message(m.group(1))
        d.drain()
    accs = _items_by_acc(req)
    want_out = 'o' in accs and bool(
        ask(d, 'take_something_out',
            "Do you want to take something out of %s? [ynq]" % head))
    want_in = 'i' in accs and bool(
        ask(d, 'put_something_in', "Do you wish to put something in? [ynq]"))
    if want_out and want_in and 'b' in accs:
        pick = 'b'
    elif want_out:
        pick = 'o'
    elif want_in:
        pick = 'i'
    else:
        pick = 'q' if 'q' in accs else None
    return ('menu', [accs[pick][0]] if pick else [], 'container:%s' % pick)


def menu_name(bridge, req):
    """3.6 do_name.c docallcmd(): "What do you want to name?" with
    m/i/o/f/d/a.  The NAO 3.4.3 menu BotHack answers used b (individual
    item) and c (object type)."""
    if not re.search(r"^What do you want to name\?", req.prompt or ''):
        return None
    d = bridge.bh.delegator
    ans = ask(d, 'name_menu', {'b': 'an individual item',
                               'c': 'all items of a certain type'})
    pick = {'b': 'i', 'c': 'o'}.get(ans)
    accs = _items_by_acc(req)
    if pick not in accs:
        return ('escape', None, 'name:none')
    return ('menu', [accs[pick][0]], 'name:%s' % pick)


MENU_TRANSLATIONS = [menu_container, menu_name]
def yn_continue_eating(bridge, req):
    """eat.c 3.6.7 asks "Continue eating?"; 3.4.3 asked "Stop eating?" -
    the meaning of y/n is inverted."""
    if not re.match(r"^Continue eating\?", req.query or ''):
        return None
    stop = ask(bridge.bh.delegator, 'stop_eating', "Stop eating? [yn] (n)")
    if stop is None or stop == "":
        stop = True          # BotHack's default answer: stop
    return ('yn', 'n' if stop else 'y', 'continue-eating:%s'
            % ('stop' if stop else 'continue'))


YN_TRANSLATIONS = [yn_continue_eating]
LINE_TRANSLATIONS = []


# ------------------------------------------------------------- messages
# (pattern, replacement) applied to every message before the handlers see
# it; the replacement is the 3.4.3 wording the BotHack regexes expect.
MESSAGE_REWRITES = [
    # trap.c: in Sokoban every pit entry says "Air currents pull you down
    # into a pit!"; BotHack learns that it is at the bottom of the pit (and
    # can reach the items there) from "You fall into a pit!"
    (re.compile(r"^Air currents pull you down into an? (?:spiked )?pit!$"),
     "You fall into a pit!"),
    # hack.c test_move() with mention_walls: 3.6 distinguishes "solid stone"
    # and trees; BotHack only knows "It's a wall." (NAO msg_wall_hits)
    (re.compile(r"^It's (?:solid stone|a tree)\.$"), "It's a wall."),
    # pickup.c 3.6: bags say "You open the bag..." (3.4.3 "carefully open")
    (re.compile(r"^You open (.*\.\.\.)$"), r"You carefully open \1"),
    # do.c heal_legs: "Your legs feel better." (3.4.3 "somewhat better")
    (re.compile(r"^Your (\w+) (feels?) better\.$"),
     r"Your \1 \2 somewhat better."),
    # read.c: "You feel as if you need some help."
    (re.compile(r"^You feel as if you need some help\.$"),
     "You feel like you need some help."),
    # eat.c: "What a pity--you just ruined ..."
    (re.compile(r"^What a pity--you just ruined (.*)$"),
     r"What a pity - you just ruined \1"),
    # pickup.c: "Hmmm, %s turns out to be locked." / "%s is locked." /
    # "%s locked." (3.4.3: "Hmmm, it seems to be locked.")
    (re.compile(r"^It is locked\.$"), "Hmmm, it seems to be locked."),
    (re.compile(r"^(?:Hmmm, .* turns out to be locked|"
                r"(?!This door)(?:The|Your|Its?) .*(?:box|chest|coffer|"
                r"safe|trunk|sack|bag) (?:is|are) locked)\.$"),
     "Hmmm, it seems to be locked."),
]


def rewrite_message(bridge, text):
    for pat, repl in MESSAGE_REWRITES:
        if pat.search(text):
            new = pat.sub(repl, text)
            bridge.counters['msg-rewrite:' + pat.pattern[:30]] += 1
            return new
    return text


# ---------------------------------------------------------- object names
_LABEL_REWRITES = [
    # 3.6 prefixes absent in 3.4.3 (container state knowledge)
    (re.compile(r"\b(?:empty|broken|locked|unlocked) (?=(?:(?:un)?cursed |"
                r"blessed |greased )*[\w'-]*\s*(?:large box|chest|ice box|"
                r"sack|bag|box|oilskin sack|bag of \w+))"), ""),
    (re.compile(r"^(an?) empty "), r"\1 "),
    (re.compile(r" containing \d+ items?"), ""),
    # globs carry a size: "small glob of gray ooze", "very large glob of ..."
    (re.compile(r"\b(?:small|medium|large|very large) (globs? of )"),
     r"\1"),
    (re.compile(r" \((?:at the ready|in quiver pouch)\)"), " (in quiver)"),
    (re.compile(r" \(tethered weapon in hand\)"), " (weapon in hand)"),
    # objnam.c: armor whose multi-turn (un)wearing was interrupted
    (re.compile(r" \(being (?:donned|doffed)\)"), " (being worn)"),
    (re.compile(r" \(for sale, (\d+) zorkmids?\)"), r", price \1 zorkmids"),
    (re.compile(r" \(contents, (\d+) zorkmids?\)"), r" (\1 zorkmids)"),
    (re.compile(r" \(no charge\)"), ", no charge"),
]


_STACK_PRICE_RE = re.compile(r"^(\d+) (.*) \(for sale, (\d+) zorkmids?\)$")


def normalize_label(label):
    """3.6.7 object name -> the 3.4.3 wording ITEM_RE was written for."""
    # objnam.c doname_with_price(): a stack on a shop floor shows the price
    # of the whole stack; BotHack's price identification wants one unit
    m = _STACK_PRICE_RE.match(label)
    if m and int(m.group(1)) > 1:
        qty, total = int(m.group(1)), int(m.group(3))
        label = "%d %s, price %d zorkmids each" % (qty, m.group(2),
                                                   total // qty)
    for pat, repl in _LABEL_REWRITES:
        label = pat.sub(repl, label)
    # "an uncursed" after removing "empty" from "an empty uncursed ..."
    label = re.sub(r"^a (?=[aeiouAEIOU])", "an ", label)
    label = re.sub(r"^an (?=[^aeiouAEIOU])", "a ", label)
    return label
