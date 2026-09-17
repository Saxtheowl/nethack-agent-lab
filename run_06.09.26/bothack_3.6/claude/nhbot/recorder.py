"""Per-game evidence: a ring buffer of the most recent observations, answers,
actions and anomalies, a milestone log that is always written, and counters.

Nothing here is read by the policy.
"""
import collections
import json
import os
import time

# special levels / branches worth a milestone line
BRANCH_MILESTONES = {
    "The Gnomish Mines": "mines", "Sokoban": "sokoban",
    "The Quest": "quest", "Fort Ludios": "ludios",
    "Gehennom": "gehennom", "Vlad's Tower": "vlad",
    "The Elemental Planes": "planes",
}

# ordered stages used for goals and for the progression funnel
STAGES = ["start", "dlvl2", "mines", "minetown", "oracle", "sokoban",
          "bigroom", "dlvl10", "medusa", "castle", "valley", "quest",
          "bell", "vlad", "candelabrum", "gehennom_deep", "wizard_tower",
          "book", "invoked", "sanctum", "amulet", "planes", "astral",
          "ascended"]


class Recorder(object):
    def __init__(self, gamedir, ring=800, full_trace=False):
        self.gamedir = gamedir
        self.ring = collections.deque(maxlen=ring)
        self.counters = collections.Counter()
        self.milestones = []
        self.reached = {}
        self.progress_f = open(os.path.join(gamedir, 'progress.jsonl'), 'w')
        self.trace_f = (open(os.path.join(gamedir, 'trace.jsonl'), 'w')
                        if full_trace else None)
        self.t0 = time.time()
        self.max_depth = 0
        self.seen_dnames = set()
        self.seen_special = set()
        self.last_xl = 0
        self.last_ach = {}
        self.last_heartbeat_turn = 0
        self.turn = 0
        self.depth = 0
        self.nreq = 0
        self.nact = 0
        self.last_action_desc = None
        self.action_hist = collections.Counter()

    # ---------------------------------------------------------- writers
    def _ring(self, rec):
        self.ring.append(rec)
        if self.trace_f is not None:
            self.trace_f.write(json.dumps(rec) + "\n")

    def milestone(self, kind_, **data):
        rec = dict(kind=kind_, turn=self.turn, depth=self.depth,
                   t=round(time.time() - self.t0, 1))
        for k, v in data.items():
            rec[k if k not in ('kind', 'turn', 'depth', 't') else 'x_' + k] = v
        self.milestones.append(rec)
        self.progress_f.write(json.dumps(rec) + "\n")
        self.progress_f.flush()

    def stage(self, name, **data):
        if name not in self.reached:
            self.reached[name] = self.turn
            self.milestone('stage', stage=name, **data)

    # ------------------------------------------------------------ hooks
    def request(self, eng, req):
        st = eng.status
        pv = eng.priv
        self.nreq += 1
        self.turn = st.get('turn') or self.turn
        self.depth = st.get('depth') or self.depth
        rec = {'r': req.seq, 'k': req.kind, 'T': self.turn,
               'lvl': (st.get('lvl') or '').strip(), 'u': list(eng.u),
               'hp': st.get('hp'), 'hpmax': st.get('hpmax')}
        if req.query:
            rec['q'] = req.query
        if req.prompt:
            rec['p'] = req.prompt
        if req.goal:
            rec['g'] = req.goal
        if req.kind == 'yn' and req.choices is not None:
            rec['c'] = req.choices
        if req.kind == 'menu' and req.items:
            rec['items'] = [("%s%s" % (it[2], '' if it[1] else '#'))
                            + " " + it[6][:60] for it in req.items[:60]]
        self._ring(rec)
        self._progress(eng, st, pv)
        self._watch_items(eng, req)

    # key items: gaining/losing one is a milestone with its context (a lost
    # ring of levitation left the bot on a Medusa island, ca-w06/g012)
    WATCHED_ITEMS = ("ring of levitation", "amulet of reflection",
                     "dragon scale mail", "speed boots", "unicorn horn",
                     "bag of holding", "pick-axe", "Excalibur",
                     "Amulet of Yendor", "Bell of Opening",
                     "Candelabrum of Invocation", "Book of the Dead",
                     "levitation boots", "water walking boots",
                     # unidentified names of the invocation items
                     "silver bell", "candelabrum", "papyrus spellbook",
                     "wax candle", "tallow candle")

    def _watch_items(self, eng, req=None):
        inv = getattr(eng, 'inventory', None)
        if inv is None or inv is getattr(self, '_last_inv_obj', None):
            return
        self._last_inv_obj = inv
        have = set()
        for it in inv:
            text = it[1] if len(it) > 1 else ''
            for w in self.WATCHED_ITEMS:
                if w in text:
                    have.add(w)
        prev = getattr(self, '_watched', None)
        self._watched = have
        if prev is None:
            return
        for w in sorted(have - prev):
            self.milestone('item_gained', item=w)
        for w in sorted(prev - have):
            # the messages of this request explain the change; they are
            # added to the ring only after request() returns
            msgs = ([r['m'] for r in self.ring if 'm' in r][-8:]
                    + (req.messages() if req is not None else []))[-16:]
            self.milestone('item_lost', item=w, messages=msgs,
                           last_action=self.last_action_desc)

    def message(self, text):
        self._ring({'m': text})

    def answer(self, req, ans):
        if isinstance(ans, str) and len(ans) == 1:
            ans = ans if 32 <= ord(ans) < 127 else "\\x%02x" % ord(ans)
        self._ring({'a': ans if isinstance(ans, (str, int, list))
                    else str(ans)})

    def action(self, a):
        self.nact += 1
        t = a.get('type')
        self.action_hist[t] += 1
        reason = a.get('reason')
        desc = {'act': t}
        if reason:
            desc['why'] = [str(x)[:100] for x in list(reason)[:10]]
        for k in ('dir', 'slot', 'pos'):
            if a.get(k) is not None:
                desc[k] = str(a.get(k))
        self.last_action_desc = desc
        self._ring(desc)

    def note(self, what, detail):
        self.counters[what] += 1
        self._ring({'note': what, 'd': detail if isinstance(
            detail, (str, int, float, list, dict)) else str(detail)})
        if what == 'assist':
            self.milestone('assist', **(detail if isinstance(detail, dict)
                                        else {'detail': str(detail)}))

    # -------------------------------------------------------- progression
    def _progress(self, eng, st, pv):
        depth = st.get('depth') or 0
        dname = st.get('dname') or ''
        special = pv.get('special') or ''
        turn = self.turn
        if depth > self.max_depth:
            self.max_depth = depth
            self.milestone('depth', value=depth, dname=dname)
            if depth >= 2:
                self.stage('dlvl2')
            if depth >= 10:
                self.stage('dlvl10')
        if dname and dname not in self.seen_dnames:
            self.seen_dnames.add(dname)
            self.milestone('branch', dname=dname, lvl=st.get('lvl'))
            b = BRANCH_MILESTONES.get(dname)
            if b == 'mines':
                self.stage('mines')
            elif b == 'sokoban':
                self.stage('sokoban')
            elif b == 'vlad':
                self.stage('vlad')
            elif b == 'quest':
                self.stage('quest')
            elif b == 'planes':
                self.stage('planes')
        if special and special not in self.seen_special:
            self.seen_special.add(special)
            self.milestone('special', name=special, lvl=st.get('lvl'))
            if special.startswith('minetn'):
                self.stage('minetown', variant=special)
            elif special == 'oracle':
                self.stage('oracle')
            elif special.startswith('bigrm'):
                self.stage('bigroom', variant=special)
            elif special.startswith('medusa'):
                self.stage('medusa', variant=special)
            elif special == 'castle':
                self.stage('castle')
            elif special == 'valley':
                self.stage('valley')
            elif special.startswith('wizard'):
                self.stage('wizard_tower')
            elif special == 'sanctum':
                self.stage('sanctum')
            elif special == 'astral':
                self.stage('astral')
        if (pv.get('evt') or {}).get('invoked'):
            self.stage('invoked')
        if pv.get('inhell') and depth >= 40:
            self.stage('gehennom_deep')
        xl = st.get('xl') or 0
        if xl > self.last_xl:
            if self.last_xl:
                self.milestone('xl', value=xl)
            self.last_xl = xl
        ach = pv.get('ach') or {}
        for k, v in ach.items():
            if v and not self.last_ach.get(k):
                self.milestone('achievement', name=k)
                if k in ('amulet', 'bell', 'book'):
                    self.stage(k)
                elif k == 'menorah':
                    self.stage('candelabrum')
        self.last_ach = dict(ach)
        if turn - self.last_heartbeat_turn >= 1000:
            self.last_heartbeat_turn = turn
            self.milestone('heartbeat', lvl=(st.get('lvl') or '').strip(),
                           dname=dname, hp=st.get('hp'), hpmax=st.get('hpmax'),
                           xl=xl, ac=st.get('ac'), requests=self.nreq,
                           actions=self.nact)

    # ------------------------------------------------------------ output
    def dump_ring(self, path=None):
        path = path or os.path.join(self.gamedir, 'last_steps.jsonl')
        with open(path, 'w') as f:
            for rec in self.ring:
                f.write(json.dumps(rec) + "\n")
        return path

    def close(self):
        self.progress_f.close()
        if self.trace_f is not None:
            self.trace_f.close()
