"""Bridge between the BotHack decision code and the NetHack 3.6.7 "bot"
window port (nhbot.engine).

The original framework talks to a terminal: a scraper watches redraws, decides
when NetHack waits for input and what kind of input, and turns that into
delegator events; handlers answer by *typing keys*.  Here the engine tells us
exactly what it waits for (command, yes/no, text, extended command, menu,
position), so the scraper disappears:

* keys written by the delegator go into a queue (the "virtual keyboard");
* every engine request first delivers the new events (messages, text
  windows, map/status) to the delegator, then either consumes queued keys
  in a way appropriate for its kind, or - when nothing is queued - asks the
  handlers exactly like the scraper did (choose-action, choice prompts,
  menus, text prompts, locations);
* anything no handler understands gets a logged, conservative default.

Map cells are rendered from glyphs into the character/color conventions of
bothack.nethackrc (closed doors ']', boulders '8', traps '^', ...), so the
world model (tile.py, dungeon.py) is unchanged.
"""
import collections
import logging
import re
import time

from . import compat36
from .frame import COLORMAP, Frame
from .position import Pos
from .scraper import (_CHOICE_FNS, _MENU_FNS, _PROMPT_FNS, _choice_call,
                      _prompt_fn)
from .util import ESC, str_kw

log = logging.getLogger('bothack.nhbridge')

# NetHack color index -> BotHack color keyword.  3.4.3 tty: gray and
# NO_COLOR emit no escape (None); black is drawn as blue.
NH_COLORS = {0: 'blue', 1: 'red', 2: 'green', 3: 'brown', 4: 'blue',
             5: 'magenta', 6: 'cyan', 7: None, 8: None, 9: 'orange',
             10: 'bright-green', 11: 'yellow', 12: 'bright-blue',
             13: 'bright-magenta', 14: 'bright-cyan', 15: 'white'}

INVERSE = {None: 'inverse', 'red': 'inverse-red', 'green': 'inverse-green',
           'brown': 'inverse-brown', 'blue': 'inverse-blue',
           'magenta': 'inverse-magenta', 'cyan': 'inverse-cyan',
           'gray': 'inverse-gray', 'orange': 'inverse-orange',
           'bright-green': 'inverse-bright-green', 'yellow': 'inverse-yellow',
           'bright-blue': 'inverse-bright-blue',
           'bright-magenta': 'inverse-bright-magenta',
           'bright-cyan': 'inverse-bright-cyan', 'white': 'inverse-white'}

MG_PET = 0x08


class GlyphRenderer(object):
    """glyph -> (char, color keyword) following bothack.nethackrc."""

    def __init__(self, hello):
        off = hello['off']
        self.off = off
        self.mons = hello['mons']
        self.objs = hello.get('objs') or []
        self.cmap = hello['cmap']
        self.cmap_index = {c[1]: i for i, c in enumerate(self.cmap)}
        self.obj_index = {}
        for i, o in enumerate(self.objs):
            self.obj_index.setdefault(o[0], i)
        self.boulder = self.obj_index.get('boulder')
        self.statue = self.obj_index.get('statue')
        self.strange = 0          # "strange object" is objects[0]
        self._cmap_chars = self._build_cmap()
        self._cache = {}

    def _build_cmap(self):
        """3.6.7 cmap index (rm.h enum) -> (char, color) as BotHack expects
        from a 3.4.3 tty with bothack.nethackrc."""
        out = {}
        for i, (sym, expl, color) in enumerate(self.cmap):
            col = NH_COLORS.get(color)
            if i == 0 or i == 20 or i == 39:    # stone, dark room, air
                r = (' ', None)
            elif 1 <= i <= 11:                  # walls
                r = (sym, None)
            elif i == 12:                       # doorway (no door)
                r = ('.', None)
            elif i in (13, 14):                 # open door
                r = (sym, 'brown')
            elif i in (15, 16):                 # closed door
                r = (']', 'brown')
            elif i == 17:
                r = ('}', 'cyan')               # iron bars
            elif i == 18:
                r = ('}', 'green')              # tree
            elif i == 19:
                r = ('.', None)                 # room floor
            elif i in (21, 22):
                r = ('#', None)                 # corridors
            elif i in (23, 25):
                r = ('<', None)
            elif i in (24, 26):
                r = ('>', None)
            elif i == 27:
                r = ('_', None)                 # altar
            elif i == 28:
                r = ('\\', None)               # grave
            elif i == 29:
                r = ('\\', 'yellow')           # throne
            elif i == 30:
                r = ('{', None)                 # sink
            elif i == 31:
                r = ('{', 'blue')               # fountain
            elif i in (32, 41):
                r = ('}', 'blue')               # pool / water
            elif i == 33:
                r = ('.', 'cyan')               # ice
            elif i == 34:
                r = ('}', 'red')                # lava
            elif i in (35, 36):
                r = ('.', 'brown')              # lowered drawbridge
            elif i in (37, 38):
                r = ('}', 'brown')              # raised drawbridge
            elif i == 40:
                r = ('#', None)                 # cloud
            elif 42 <= i <= 63:
                r = ('^', col)                  # traps (web included)
            elif i == 64:
                r = ('.', None)                 # vibrating square: 3.4.3
                                                # showed floor (found by msg)
            else:
                r = (sym, col)                  # beams, effects, swallow
            out[i] = r
        return out

    def render(self, glyph, ch, color, special):
        """Returns (char, color keyword)."""
        key = (glyph, ch, color, special)
        r = self._cache.get(key)
        if r is not None:
            return r
        r = self._render(glyph, ch, color, special)
        self._cache[key] = r
        return r

    def _render(self, glyph, ch, color, special):
        off = self.off
        col = NH_COLORS.get(color)
        c = chr(ch) if 0 < ch < 256 else ' '
        if glyph == -2:
            return (' ', None)
        if glyph == -1:
            # masked object (unidentified type): engine char and color
            return self._object_char(c, col, None)
        if glyph < off['pet']:                        # monster
            return self._monster(glyph - off['mon'], col, special)
        if glyph < off['invis']:                      # pet
            ch_, col_ = self._monster(glyph - off['pet'], col, special)
            return (ch_, INVERSE.get(col_, 'inverse'))
        if glyph < off['detect']:                     # remembered invisible
            return ('I', None)
        if glyph < off['body']:                       # detected monster
            return self._monster(glyph - off['detect'], col, special)
        if glyph < off['ridden']:                     # corpse ("body")
            return ('%', col)
        if glyph < off['obj']:                        # ridden monster
            return self._monster(glyph - off['ridden'], col, special)
        if glyph < off['cmap']:                       # object
            return self._object_char(c, col, glyph - off['obj'])
        if glyph < off['explode']:                    # map feature
            return self._cmap_chars.get(glyph - off['cmap'], (c, col))
        if glyph < off['warning']:                    # explosions, zaps
            return (c, col)
        if glyph < off['statue']:                     # warning 0-5
            return (c, col)
        if glyph < off['max']:                        # statue (3.6)
            return ('`', None)
        return (c, col)

    def _monster(self, idx, col, special):
        if 0 <= idx < len(self.mons):
            name, sym, mcolor = self.mons[idx]
            if sym == ' ':                 # ghost/shade class -> 'X'
                sym = 'X'
            return (sym, NH_COLORS.get(mcolor))
        return ('?', col)

    def _object_char(self, c, col, otyp):
        if otyp is not None:
            if otyp == self.boulder:
                return ('8', None)
            if otyp == self.statue:
                return ('`', None)
            if otyp == self.strange:
                return ('m', None)
        if c == ']' and otyp is None:
            # a masked ']' is still an armor piece
            return ('[', col)
        return (c, col)

    def monster_index(self, glyph):
        """Monster type index for monster-like glyphs, else None."""
        off = self.off
        for base, end in (('mon', 'pet'), ('pet', 'invis'),
                          ('detect', 'body'), ('ridden', 'obj')):
            if off[base] <= glyph < off[end]:
                return glyph - off[base]
        return None


# ------------------------------------------------------------------ status

HUNGER = {0: 'satiated', 1: None, 2: 'hungry', 3: 'weak', 4: 'fainting',
          5: 'fainting', 6: 'fainting'}
ENCUMBRANCE = {0: None, 1: 'burdened', 2: 'stressed', 3: 'strained',
               4: 'overtaxed', 5: 'overloaded'}
ALIGN = {-1: 'chaotic', 0: 'neutral', 1: 'lawful'}
ALIGN_TXT = {-1: 'Chaotic', 0: 'Neutral', 1: 'Lawful'}


def str_string(v):
    if v > 18:
        if v <= 118:
            return "18/**" if v == 118 else "18/%02d" % (v - 18)
        return "%d" % (v - 100)
    return "%d" % v


def dlvl_string(st):
    lvl = (st.get('lvl') or '').strip()
    return lvl


def bothack_status(st, nickname):
    """The dict parse_botls would have produced."""
    from .util import effective_str
    s = str_string(st.get('str', 10))
    state = set()
    cond = st.get('cond', 0)
    if cond & 0x20:
        state.add('blind')
    if cond & 0x80:
        state.add('stun')
    if cond & 0x100:
        state.add('conf')
    if cond & (0x08 | 0x10):
        state.add('ill')
    if cond & 0x200:
        state.add('hallu')
    return {
        'nickname': nickname,
        'title': st.get('title'),
        'stats': {'str': effective_str(s), 'str*': s,
                  'dex': st.get('dex'), 'con': st.get('con'),
                  'int': st.get('int'), 'wis': st.get('wis'),
                  'cha': st.get('cha')},
        'alignment': ALIGN.get(st.get('align')),
        'score': None,
        'dlvl': dlvl_string(st),
        'gold': st.get('gold'),
        'hp': st.get('hp'), 'maxhp': st.get('hpmax'),
        'pw': st.get('pw'), 'maxpw': st.get('pwmax'),
        'ac': st.get('ac'),
        'xp-label': 'HD' if st.get('poly') else 'Exp',
        'xplvl': st.get('xl'),
        'xp': st.get('exp'),
        'turn': st.get('turn'),
        'state': state,
        'encumbrance': ENCUMBRANCE.get(st.get('enc')),
        'hunger': HUNGER.get(st.get('hunger')),
    }


def botl_lines(st, nickname):
    l1 = "%s the %s  St:%s Dx:%s Co:%s In:%s Wi:%s Ch:%s  %s" % (
        nickname, st.get('title'), str_string(st.get('str', 10)),
        st.get('dex'), st.get('con'), st.get('int'), st.get('wis'),
        st.get('cha'), ALIGN_TXT.get(st.get('align'), ''))
    extra = []
    h = HUNGER.get(st.get('hunger'))
    if h:
        extra.append({'satiated': 'Satiated', 'hungry': 'Hungry',
                      'weak': 'Weak', 'fainting': 'Fainting'}[h])
    cond = st.get('cond', 0)
    for bit, txt in ((0x100, 'Conf'), (0x08, 'FoodPois'), (0x10, 'Ill'),
                     (0x20, 'Blind'), (0x80, 'Stun'), (0x200, 'Hallu')):
        if cond & bit:
            extra.append(txt)
    e = ENCUMBRANCE.get(st.get('enc'))
    if e:
        extra.append(e.capitalize())
    l2 = "%s $:%s HP:%s(%s) Pw:%s(%s) AC:%s %s:%s/%s T:%s %s" % (
        dlvl_string(st), st.get('gold'), st.get('hp'), st.get('hpmax'),
        st.get('pw'), st.get('pwmax'), st.get('ac'),
        'HD' if st.get('poly') else 'Exp', st.get('xl'), st.get('exp'),
        st.get('turn'), " ".join(extra))
    return l1[:80].ljust(80), l2[:80].ljust(80)


# ------------------------------------------------------------ key parsing

_MOVE = {'h': (-1, 0), 'j': (0, 1), 'k': (0, -1), 'l': (1, 0),
         'y': (-1, -1), 'u': (1, -1), 'b': (-1, 1), 'n': (1, 1)}


def simulate_getpos(keys, cx, cy):
    """Apply getpos cursor keys; returns (x, y, consumed, escaped)."""
    x, y = cx, cy
    i = 0
    while i < len(keys):
        k = keys[i]
        i += 1
        if k == ESC:
            return x, y, i, True
        if k in '.,;:':
            return x, y, i, False
        if k.lower() in _MOVE:
            dx, dy = _MOVE[k.lower()]
            n = 8 if k.isupper() else 1
            x = min(max(x + dx * n, 1), 79)
            y = min(max(y + dy * n, 0), 20)
        # other getpos keys (@ < > _ m ...) are not used by the bot
    return x, y, i, False


# ------------------------------------------------------------------ bridge

class BridgeAbort(Exception):
    """Raised to end a game from inside the bridge (stuck / limits)."""

    def __init__(self, category, reason):
        Exception.__init__(self, "%s: %s" % (category, reason))
        self.category = category
        self.reason = reason


LOCATION_GOALS = [
    (r"travel to\?", 'travel_where'),
    (r"teleported\?|To what position", 'teleport_where'),
    (r"Pay whom", 'pay_whom'),
]


class Bridge(object):
    def __init__(self, bh, engine, recorder=None, nickname='Bot'):
        self.bh = bh
        self.engine = engine
        self.rec = recorder
        self.nickname = nickname
        self.queue = collections.deque()
        self.renderer = None
        self.counters = collections.Counter()
        self.last_action = None
        self.action_serial = 0
        self.queue_serial = 0       # action serial that filled the queue
        self._same_prompt = 0
        self._last_prompt_key = None
        self.lines = [" " * 80 for _ in range(24)]
        self.colors = [[None] * 80 for _ in range(24)]
        self.frame = None
        self.last_turn = None
        self.requests_since_turn = 0
        self.farlook_pos = None     # NetHack (x, y) of the last getpos pick
        self.force_escape = 0       # supervisor recovery: escape N prompts
        self.force_command = None   # supervisor recovery: next command key
        bh.delegator.set_writer(self.write)

    # --------------------------------------------------------- key queue
    def write(self, keys):
        if not keys:
            return
        if not self.queue:
            self.queue_serial = self.action_serial
        self.queue.extend(keys)

    def _pop(self):
        return self.queue.popleft() if self.queue else None

    # --------------------------------------------------------- rendering
    def _update_frame(self, req):
        eng = self.engine
        if self.renderer is None:
            self.renderer = GlyphRenderer(eng.hello)
        render = self.renderer.render
        lines = self.lines
        colors = self.colors
        for y in range(21):
            gr, cr, colr, sr = (eng.map_glyph[y], eng.map_ch[y],
                                eng.map_color[y], eng.map_special[y])
            row = []
            crow = colors[y + 1]
            for x in range(1, 80):
                ch, col = render(gr[x], cr[x], colr[x], sr[x])
                row.append(ch)
                crow[x - 1] = col
            lines[y + 1] = "".join(row) + " "
        # the hero: always '@' at the cursor (BotHack reads position from it)
        ux, uy = eng.u
        top = ""
        msgs = req.messages()
        if msgs:
            top = msgs[-1]
        lines[0] = top[:80].ljust(80)
        l1, l2 = botl_lines(eng.status, self.nickname)
        lines[22], lines[23] = l1, l2
        cursor = Pos(ux - 1, uy + 1) if ux else Pos(0, 0)
        self.frame = Frame(list(lines), [list(c) for c in colors], cursor)
        return self.frame

    # ---------------------------------------------------------- main loop
    def run(self, supervisor=None):
        eng = self.engine
        d = self.bh.delegator
        d.started()
        d.drain()
        # a scenario setup may already have read the first request
        req = eng.req if eng.req is not None else eng.next_request()
        while req is not None:
            if supervisor is not None:
                supervisor.on_request(self, req)
            self.handle(req)
            req = eng.next_request()
        d.ended()
        d.drain()

    def handle(self, req):
        d = self.bh.delegator
        self._deliver_events(req)
        kind = req.kind
        if self.force_command and kind == 'cmd':
            self.queue.clear()
            key, self.force_command = self.force_command, None
            self._note('forced-command', key)
            self.engine.key(key)
            self._record_answer(req, key)
            return
        if self.force_escape and kind not in ('cmd',):
            self.force_escape -= 1
            self.queue.clear()
            self._note('forced-escape', kind)
            self.engine.escape()
            self._record_answer(req, ESC)
            return
        if (kind == 'yn' and "You don't have that object." in req.messages()):
            # getobj() re-asks after a letter the hero does not carry; the
            # bot's inventory is stale and it would type the same letter
            # again (3000 requests, big-w01 g043).  Cancel, refresh.
            self.queue.clear()
            self.counters['stale_inventory_letter'] += 1
            self._note('stale-inventory', req.query or '')
            self.engine.escape()
            self._record_answer(req, ESC)
            from .actions import update_inventory
            update_inventory(self.bh)
            return
        if self.queue:
            if kind == 'cmd' and not self._leftover_allowed():
                dropped = "".join(self.queue)
                self.queue.clear()
                self.counters['leftover_keys_dropped'] += 1
                self._note('leftover', dropped)
            else:
                if self._consume(req):
                    return
        # nothing queued: ask the handlers
        self._track_prompt_loop(req)
        if kind == 'cmd':
            self._choose_action(req)
        elif kind == 'yn':
            if self._translated(req, compat36.YN_TRANSLATIONS):
                return
            self._yn(req)
        elif kind == 'line':
            if self._translated(req, compat36.LINE_TRANSLATIONS):
                return
            self._line(req)
        elif kind == 'menu':
            if self._translated(req, compat36.MENU_TRANSLATIONS):
                return
            self._menu(req)
        elif kind == 'pos':
            self._pos(req)
        else:  # cmdcont, key, ext with nothing queued
            self.counters['unexpected_' + kind] += 1
            self._note('unexpected', kind)
            self.engine.escape()
            return
        if getattr(self, '_answered', False):
            self._answered = False
            return
        if self.queue:
            if not self._consume(req):
                self._fallback(req, 'unconsumable')
        else:
            self._fallback(req, 'no-answer')

    def recover_action_loop(self, action):
        """Supervisor recovery for an action repeated from an identical
        state.  For a move, the target square is marked as blocked so that
        path finding stops choosing it; otherwise the next command is a
        search (it takes a turn and changes the state)."""
        from .clj import assoc
        from .dungeon import curlvl, update_at
        from .position import in_direction, position
        try:
            if action.get('type') == 'move' and action.get('dir'):
                g = self.bh.game.deref()
                target = in_direction(curlvl(g), position(g['player']),
                                      action['dir'])
                self.bh.game.swap(update_at, target,
                                  lambda t: assoc(t, 'blocked', 30,
                                                  'move-blocked', g.get('turn'),
                                                  'new-items', False,
                                                  'items', []))
                return "blocked %s and forgot its items" % (position(target),)
        except Exception as e:                    # noqa: BLE001
            self._note('recovery-error', repr(e))
        try:
            if action.get('type') == 'farlook' and action.get('pos'):
                from .dungeon import update_at, update_monster, monster_at
                pos = action['pos']
                g = self.bh.game.deref()

                def settle(t):
                    if t.get('feature') == 'altar' and not t.get('alignment'):
                        t = assoc(t, 'alignment', 'unknown')
                    if t.get('feature') == 'trap':
                        t = assoc(t, 'feature', 'squeaky')
                    return t
                self.bh.game.swap(update_at, pos, settle)
                if monster_at(g, pos) is not None:
                    self.bh.game.swap(update_monster, pos,
                                      lambda m: assoc(m, 'peaceful', False))
                return "farlook target %s marked examined" % (pos,)
        except Exception as e:                    # noqa: BLE001
            self._note('recovery-error', repr(e))
        self.force_command = 's'
        return "forced search"

    def forget_target(self, x, y):
        """Supervisor recovery for a goal target that stays unreachable:
        the tile (BotHack coordinates) stops being an item/exploration
        target and path finding avoids it."""
        from .clj import assoc
        from .dungeon import update_at
        from .position import Pos
        try:
            self.bh.game.swap(update_at, Pos(x, y),
                              lambda t: assoc(t, 'new-items', False,
                                              'blocked', 30,
                                              'items', []))
            return "forgot items/target at (%d,%d)" % (x, y)
        except Exception as e:                    # noqa: BLE001
            self._note('recovery-error', repr(e))
            return "error %r" % (e,)

    def request_exploration_reset(self):
        """Supervisor recovery for a stalled level: forget the exploration
        verdicts of the current level so the bot looks again."""
        from .clj import assoc
        from .dungeon import update_curlvl

        def forget(level):
            return assoc(level, 'explored', None)
        try:
            self.bh.game.swap(lambda g: assoc(update_curlvl(g, forget),
                                              'explore-cache', None,
                                              'autonav-stuck', None))
        except Exception as e:                    # noqa: BLE001
            self._note('recovery-error', str(e))

    def _leftover_allowed(self):
        a = self.last_action
        return a is not None and a.get('type') in ('farmattack',)

    # ----------------------------------------------------------- events
    def _deliver_events(self, req):
        d = self.bh.delegator
        eng = self.engine
        frame = self._update_frame(req)
        d.redraw(frame)
        for e in req.events:
            if not isinstance(e, list) or not e:
                continue
            k = e[0]
            if k == 'msg':
                text = compat36.rewrite_message(self, e[1])
                text = self._farlook_symbol(text)
                if self.rec is not None:
                    self.rec.message(e[1])
                if text.strip():
                    d.message(text)
            elif k == 'text':
                lines = [l for l in e[1]]
                while lines and not lines[-1].strip():
                    lines.pop()
                if lines:
                    d.message_lines(lines)
            elif k == 'menu_show':
                # a display-only menu (PICK_NONE): the scraper saw the same
                # screen and dispatched it by its title
                prompt, items = e[1] or '', e[2]
                opts = {}
                for sel, acc, text in items:
                    if sel and acc:
                        opts[acc] = text
                name = None
                for pat, n in _MENU_FNS:
                    if prompt and re.search(pat, prompt):
                        name = n
                        break
                if name and name != 'inventory_list':
                    try:
                        d._invoke_prompt(name, opts)
                    except RuntimeError:
                        pass
                    self.counters['menu_show:' + name] += 1
                elif opts:
                    d.inventory_list(opts)
                elif items:
                    lines = [t for _s, _a, t in items]
                    d.message_lines(([prompt] if prompt else []) + lines)
            elif k == 'assist':
                self._note('assist', e[1])
            elif k == 'protoerr':
                self.counters['protoerr'] += 1
                self._note('protoerr', e[1:])
        turn = eng.status.get('turn')
        if turn != self.last_turn:
            self.last_turn = turn
            self.requests_since_turn = 0
        else:
            self.requests_since_turn += 1
        d.drain()

    _FARLOOK_RE = re.compile(r"^(.)(\s{2,}\S.*)$")

    def _farlook_symbol(self, text):
        """A farlook result starts with the symbol NetHack 3.6 displays
        (default symset: ']' strange object, ' ' ghost...); BotHack parses it
        with its own remapped symbols, so use the symbol rendered for that
        map cell."""
        if self.farlook_pos is None:
            return text
        m = self._FARLOOK_RE.match(text)
        if not m:
            return text
        x, y = self.farlook_pos
        self.farlook_pos = None
        if not (0 < x < 80 and 0 <= y < 21) or self.frame is None:
            return text
        ch = self.frame.lines[y + 1][x - 1]
        rest = m.group(2)
        # 3.6 appends the looked-up name: "a mimic or a strange object
        # (strange object)"; BotHack's regex wants the 3.4.3 ending
        rest = re.sub(r"(a mimic or a strange object) \(strange object"
                      r"(?: in water| on lava)?\)$",
                      r"\1", rest)
        if ch == '^':
            # a symbol shared with another class ("an amulet or a web (web)")
            # is described by all its interpretations; BotHack's trap regex
            # wants "a trap (<name>)"
            from .tile import TRAP_NAMES
            t = re.match(r"^(\s+).*\(([^)]*)\)\s*$", rest)
            if t and t.group(2) in TRAP_NAMES and \
                    not re.match(r"^\s+a trap \(", rest):
                self.counters['farlook-trap'] += 1
                return "^" + t.group(1) + "a trap (%s)" % t.group(2)
        if ch != m.group(1) and ch != ' ':
            self.counters['farlook-symbol'] += 1
            return ch + rest
        return text

    # ------------------------------------------------------- consumption
    def _consume(self, req):
        """Answer `req` from the key queue.  Returns False if the queue
        cannot answer this kind of request (queue left untouched)."""
        eng = self.engine
        kind = req.kind
        q = self.queue
        if kind in ('cmd', 'cmdcont', 'key'):
            ch = q.popleft()
            eng.key(ch)
            self._record_answer(req, ch)
            return True
        if kind == 'yn':
            ch = q.popleft()
            if ch == ESC:
                eng.escape()
            else:
                eng.yn(ch)
            self._record_answer(req, ch)
            return True
        if kind in ('line', 'ext'):
            buf = []
            while q:
                ch = q.popleft()
                if ch == '\n' or ch == '\r':
                    break
                if ch == ESC:
                    eng.escape()
                    self._record_answer(req, ESC)
                    return True
                if ch == '\b':
                    if buf:
                        buf.pop()
                    continue
                buf.append(ch)
            text = "".join(buf)
            if kind == 'line':
                eng.line(text)
            else:
                eng.ext(text.strip())
            self._record_answer(req, text)
            return True
        if kind == 'menu':
            picks = []
            items = req.items or []
            used = set()
            while q:
                ch = q.popleft()
                if ch == ESC:
                    eng.escape()
                    self._record_answer(req, ESC)
                    return True
                if ch in '\n\r ':
                    break
                iid = getattr(self, '_menu_keys', {}).get(ch)
                if iid is not None:
                    if iid not in used:
                        picks.append(iid)
                        used.add(iid)
                    continue
                for it in items:
                    iid, selectable, acc = it[0], it[1], it[2]
                    if selectable and acc == ch and iid not in used:
                        picks.append(iid)
                        used.add(iid)
                        break
                else:
                    self.counters['menu_letter_unmatched'] += 1
            eng.menu(picks)
            self._record_answer(req, picks)
            return True
        if kind == 'pos':
            keys = list(q)
            x, y, n, escaped = simulate_getpos(keys, req.cx, req.cy)
            for _ in range(n):
                q.popleft()
            if escaped:
                eng.escape()
            else:
                eng.pos(x, y)
                self.farlook_pos = (x, y)
            self._record_answer(req, (x, y))
            return True
        return False

    # ----------------------------------------------------------- prompts
    def _choose_action(self, req):
        d = self.bh.delegator
        if not hasattr(self, '_vetoed'):
            self._vetoed = {}
            d.action_veto = self._veto
        self._check_refusal(req)
        game = self.bh.game
        d.botl(bothack_status(self.engine.status, self.nickname))
        d.know_position(self.frame)
        d.full_frame(self.frame)
        d.drain()

    def _yn(self, req):
        d = self.bh.delegator
        q = req.query or ''
        if q == "adjust?":
            # wizard mode only (quest.c chat_with_leader: "You are currently
            # N and require 20." adjust?): a prepared scenario character has
            # no alignment record; declining gets the hero expelled
            self._note('wizard-prompt', "adjust? -> y")
            self.counters['wizard_adjust'] += 1
            self.engine.yn('y')
            self._record_answer(req, 'y')
            self._answered = True
            return
        if re.match(r"^In what direction", q):
            d.botl(bothack_status(self.engine.status, self.nickname))
            self._safe_prompt(req, lambda: d.what_direction(q))
            return
        if req.choices is not None:
            vis = req.choices.split(ESC)[0]
            text = "%s [%s]" % (q, vis)
            if req.default and req.default != '\x00' and req.default != '':
                text += " (%s)" % req.default
        else:
            text = q
        d.botl(bothack_status(self.engine.status, self.nickname))
        try:
            name, args = _choice_call(text)
        except (NotImplementedError, RuntimeError) as e:
            self._unknown(req, 'yn', text)
            return
        self._safe_prompt(req, lambda: getattr(d, name)(*args))

    def _line(self, req):
        d = self.bh.delegator
        q = req.query or ''
        try:
            name = _prompt_fn(q)
        except NotImplementedError:
            self._unknown(req, 'line', q)
            return
        d.botl(bothack_status(self.engine.status, self.nickname))
        self._safe_prompt(req, lambda: getattr(d, name)(q))

    def _translated(self, req, table):
        for fn in table:
            r = fn(self, req)
            if r is not None:
                kind, value, label = r
                self.counters['compat:' + label] += 1
                self._note('compat', label)
                if kind == 'menu':
                    self.engine.menu(value)
                elif kind == 'yn':
                    self.engine.yn(value) if value != ESC else \
                        self.engine.escape()
                elif kind == 'line':
                    self.engine.line(value)
                elif kind == 'escape':
                    self.engine.escape()
                self._record_answer(req, value)
                return True
        return False

    def _menu(self, req):
        d = self.bh.delegator
        head = req.prompt or ''
        name = None
        for pat, n in _MENU_FNS:
            if re.search(pat, head):
                name = n
                break
        if name is None or name == 'inventory_list':
            self._unknown(req, 'menu', head)
            return
        opts = {}
        counts = collections.Counter(it[2] for it in req.items or []
                                     if it[1] and it[2])
        self._menu_keys = {}
        for it in req.items or []:
            iid, selectable, acc, gacc, attr, presel, text = it
            if selectable and acc:
                if counts[acc] > 1:
                    # a menu longer than 52 entries reuses letters (tty
                    # pages); a dict keyed by letter lost the first entries
                    # and the castle's pile was never picked from (seed
                    # 6006).  Duplicates get a private key -> item id.
                    key = chr(0xE000 + len(self._menu_keys))
                    self._menu_keys[key] = iid
                    opts[key] = text
                else:
                    opts[acc] = text
        self._safe_prompt(req, lambda: getattr(d, name)(opts))

    def _pos(self, req):
        d = self.bh.delegator
        context = " ".join(req.messages()[-2:]) + " " + (req.goal or '')
        name = None
        for pat, n in LOCATION_GOALS:
            if re.search(pat, context):
                name = n
                break
        if name is None:
            self._unknown(req, 'pos', context)
            return
        if name != 'travel_where':
            d.know_position(self.frame)
        self._safe_prompt(req, lambda: getattr(d, name)())

    def _safe_prompt(self, req, fn):
        try:
            fn()
            self.bh.delegator.drain()
            if req.kind == 'menu' and not self.queue:
                # the handler answered "nothing" (e.g. take_out_what just
                # learns the contents): select nothing, like the scraper's
                # confirming space did
                self.engine.menu([])
                self._record_answer(req, [])
                self.counters['menu_empty_answer'] += 1
                self._answered = True
        except RuntimeError as e:
            # "No handler responded to prompt of ..."
            self.counters['no_handler'] += 1
            self._note('no-handler', "%s: %s" % (req.kind, e))

    # ---------------------------------------------------------- fallbacks
    def _unknown(self, req, kind, text):
        self.counters['unknown_' + kind] += 1
        self._note('unknown-prompt', "%s: %s" % (kind, text))
        log.warning("unknown %s prompt: %r", kind, text)

    def _fallback(self, req, why):
        """Conservative default answer, always logged."""
        eng = self.engine
        self.counters['fallback'] += 1
        kind = req.kind
        if kind == 'yn':
            choices = req.choices or ''
            if 'n' in choices:
                eng.yn('n')
                ans = 'n'
            else:
                eng.escape()
                ans = ESC
        elif kind == 'cmd':
            # no action at all: a harmless no-time command keeps the game
            # moving; the supervisor counts these
            eng.key(ESC)
            ans = ESC
        else:
            eng.escape()
            ans = ESC
        self._note('fallback', "%s %s -> %r" % (why, req, ans))
        log.warning("fallback %s %s -> %r", why, req, ans)
        self._record_answer(req, ans)

    def _track_prompt_loop(self, req):
        key = (req.kind, req.query, req.prompt, req.goal)
        if req.kind != 'cmd' and key == self._last_prompt_key:
            self._same_prompt += 1
        else:
            self._same_prompt = 0
        self._last_prompt_key = key

    # ----------------------------------------------------------- logging
    def _note(self, what, detail):
        if self.rec is not None:
            self.rec.note(what, detail)

    def _record_answer(self, req, answer):
        if self.rec is not None:
            self.rec.answer(req, answer)

    # port: refusals that take no game time; BotHack's logic re-chooses the
    # same action forever (cursed ring/weapon, welded two-hander...)
    REFUSAL_RE = re.compile(
        r"^You can't\.\s+(?:It is|They are) cursed\.|^You have no free hand|"
        r"^You cannot free your weapon hand|welded to your hand|"
        r"^You cannot drop something you are wearing|"
        r"^You are already wearing|^You can't take that off|"
        r"^You can't move diagonally (?:out of|into) an intact doorway|"
        r"free hand, you cannot loot|^You can't reach over the edge|"
        r"^Never mind\.$")
    VETO_TURNS = 300

    def _action_key(self, a):
        # a refused move/attack depends on where the hero stands, a refused
        # item action does not
        pos = (tuple(self.engine.u) if (a.get('dir') or a.get('pos'))
               else None)
        return (a.get('type'), str(a.get('slot')), str(a.get('dir')),
                str(a.get('pos')), pos)

    def _check_refusal(self, req):
        a = self.last_action
        if a is None or req.kind != 'cmd':
            return
        turn = self.engine.status.get('turn') or 0
        if turn != getattr(self, '_last_action_turn', None):
            return
        if any(self.REFUSAL_RE.search(m) for m in req.messages()):
            key = self._action_key(a)
            if key not in self._vetoed:
                self._note('veto', "%s refused at turn %d, blocked for %d "
                           "turns" % (key, turn, self.VETO_TURNS))
                self.counters['action_veto'] += 1
            self._vetoed[key] = turn + self.VETO_TURNS

    def _veto(self, action):
        try:
            key = self._action_key(action)
        except Exception:                       # noqa: BLE001
            return False
        until = self._vetoed.get(key)
        return until is not None and (self.engine.status.get('turn') or 0) < until

    def on_action(self, action):
        self.action_serial += 1
        self._last_action_turn = self.engine.status.get('turn') or 0
        self.last_action = action
        if self.rec is not None:
            self.rec.action(action)
