"""Prepared situations for testing hard stages (wizard mode only).

A scenario game is NEVER counted as a full game: rungame marks it
`counted_as_full_game: false` and the setup steps are logged.

Scenario files live in scenarios/<name>.json:

    {
      "description": "Medusa's island with the default kit, XL 14",
      "steps": [["xl", 14], ["wish", "blessed ring of levitation"],
                ["levelport", "medusa"], ["map"]],
      "goal": "castle",
      "max_turns": 6000
    }

Steps:
    ["xl", N]              #levelchange to experience level N
    ["wish", "text"]       ^W wish (repeatable)
    ["levelport", X]       ^V to a level number or a special level name
                           (lev_by_name: "oracle", "medusa", "castle",
                           "valley", "sanctum", "minetn", "soko1" ...)
    ["levelport_rel", N, d] ^V to (depth of special level N) + d, the depth
                           read from the wizard overview (#wizwhere)
    ["levelport_menu", T]  ^V "?" menu entry containing T (other dungeons,
                           e.g. "Val-strt", "earth", "astral")
    ["teleport", x, y]     ^T to map position (x, y) (engine coordinates)
    ["identify"]           ^I identify everything carried
    ["wear"|"wield"|"puton", "text"]  W/w/P the unworn item named like text
    ["map"]                ^F reveal the level map
    ["keys", "abc"]        raw command keys (escape hatch)
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCEN_DIR = os.path.join(ROOT, 'scenarios')


def load(name):
    path = name if name.endswith('.json') else os.path.join(SCEN_DIR,
                                                            name + '.json')
    with open(path) as f:
        return json.load(f)


class _Driver(object):
    def __init__(self, eng, rec):
        self.eng = eng
        self.rec = rec

    def _note(self, detail):
        if self.rec is not None:
            self.rec.note('scenario', detail)

    def until_cmd(self, answers, limit=60):
        """Answer requests from `answers` (dict kind -> list of values, used
        in order) until the game asks for a new command."""
        eng = self.eng
        req = eng.req or eng.next_request()
        n = 0
        while req is not None and req.kind != 'cmd' and n < limit:
            n += 1
            vals = answers.get(req.kind) or []
            self._note("%s %r -> %r" % (req.kind,
                                        req.query or req.prompt or '',
                                        vals[0] if vals else 'ESC'))
            if req.kind == 'line' and vals:
                eng.line(str(vals.pop(0)))
            elif req.kind == 'yn' and vals:
                eng.yn(vals.pop(0))
            elif req.kind == 'menu' and vals:
                pick = vals.pop(0)
                ids = [it[0] for it in (req.items or [])
                       if it[1] and pick in it[6]]
                eng.menu(ids[:1])
            elif req.kind == 'pos' and vals:
                x, y = vals.pop(0)
                eng.pos(int(x), int(y))
            elif req.kind == 'ext' and vals:
                eng.ext(vals.pop(0))
            elif req.kind == 'key' and vals:
                eng.key(vals.pop(0))
            elif req.kind in ('key', 'cmdcont'):
                eng.key(27)
            else:
                eng.escape()
            req = eng.next_request()
        for m in (req.messages() if req is not None else []):
            self._note("msg: %s" % m)
        return req

    def cmd(self, key):
        req = self.eng.req or self.eng.next_request()
        if req is None:
            raise RuntimeError("game over during scenario setup")
        if req.kind != 'cmd':
            req = self.until_cmd({})
        self.eng.key(key)
        return self.eng.next_request()


def setup(name, eng, rec):
    scen = load(name)
    drv = _Driver(eng, rec)
    req = eng.next_request()
    drv.until_cmd({})
    for step in scen.get('steps', []):
        kind = step[0]
        rec.note('scenario', 'step %r' % (step,))
        if kind == 'wish':
            drv.cmd(chr(23))
            drv.until_cmd({'line': [step[1]], 'yn': ['n']})
        elif kind == 'levelport':
            drv.cmd(chr(22))
            drv.until_cmd({'line': [step[1]], 'yn': ['y']})
        elif kind == 'xl':
            drv.cmd('#')
            drv.until_cmd({'ext': ['levelchange'], 'line': [step[1]]})
        elif kind == 'levelport_rel':
            # ["levelport_rel", "sanctum", -1]: depth read from the wizard
            # dungeon overview (#wizwhere), e.g. the vibrating square level
            drv.cmd('#')
            eng.ext('wizwhere')
            req2 = eng.next_request()
            depth = None
            import re as _re
            for e in (req2.events if req2 is not None else []):
                if e and e[0] in ('text', 'menu_show'):
                    lines = e[1] if e[0] == 'text' else \
                        [t[2] for t in e[2]]
                    for line in lines:
                        m = _re.search(r"\b%s: (\d+)" % _re.escape(step[1]),
                                       line)
                        if m:
                            depth = int(m.group(1))
            if depth is None:
                raise RuntimeError("level %r not in the overview" % step[1])
            rec.note('scenario', '%s is at depth %d' % (step[1], depth))
            drv.until_cmd({})
            drv.cmd(chr(22))
            drv.until_cmd({'line': [depth + int(step[2])], 'yn': ['y']})
        elif kind == 'levelport_menu':
            # ["levelport_menu", "Val-strt"]: wizard ^V "?" menu; reaches
            # other dungeons (quest, planes - the game then adds an Amulet of
            # Yendor as "endgame prerequisite")
            drv.cmd(chr(22))
            drv.until_cmd({'line': ['?'], 'menu': [step[1]], 'yn': ['y']})
        elif kind == 'teleport':
            # ["teleport", x, y]: wizard ^T (ignores no-teleport levels),
            # "Override?" (carrying the Amulet) and getpos answered
            drv.cmd(chr(20))
            drv.until_cmd({'yn': ['y', 'y', 'y'], 'pos': [(step[1], step[2])]})
        elif kind == 'identify':
            # wizard ^I, "_" = identify everything carried
            drv.cmd(chr(9))
            drv.until_cmd({'menu': ['permanently identify']})
        elif kind in ('wear', 'wield', 'puton'):
            # ["wear", "text"]: the inventory item whose name contains text
            letters = [it[0] for it in eng.inventory
                       if step[1] in it[1] and not it[4]]
            if not letters:
                raise RuntimeError("no unworn item %r to %s in %r"
                                   % (step[1], kind, eng.inventory))
            drv.cmd({'wear': 'W', 'wield': 'w', 'puton': 'P'}[kind])
            drv.until_cmd({'yn': [letters[0]], 'key': [letters[0]]})
        elif kind == 'map':
            drv.cmd(chr(6))
            drv.until_cmd({})
        elif kind == 'keys':
            for k in step[1]:
                drv.cmd(k)
                drv.until_cmd({})
        else:
            raise ValueError("unknown scenario step %r" % (step,))
    rec.note('scenario', 'setup done: %s' % scen.get('description'))
    return scen
