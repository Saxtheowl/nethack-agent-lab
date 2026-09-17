"""Progress supervision: limits, goals, loop/stall detection with recovery.

Each detector first tries a recovery that changes what the bot does, and
only aborts the game (classified "stuck") if the problem persists.  Every
recovery and abort is written to the recorder.
"""
import faulthandler
import os
import signal
import threading
import time

from pybothack.nhbridge import BridgeAbort

DEFAULT_LIMITS = {
    'max_turns': 200000,        # game turns
    'max_seconds': 12 * 3600,   # wall clock
    'max_requests': 3000000,    # engine input requests
    'prompt_loop': 40,          # identical consecutive non-command prompts
    'no_turn_requests': 600,    # requests without the game turn advancing
    'action_loop': 8,           # same action from the same state: recover
    'action_loop_abort': 40,    # ... and give up
    'stall_turns': 6000,        # turns without any novelty
    'fixation_recover': 400,    # same goal target for this many turns
    'fixation_abort': 1200,
    'death_loop': 150,          # assisted lifesaves ...
    'death_loop_turns': 300,    # ... within this many turns = death loop
    'storm_window': 3000,       # requests per check window ...
    'storm_min_turns': 30,      # ... that must advance at least this many turns
    'decision_warn': 60.0,      # seconds inside one request: dump stacks
    'decision_kill': 600.0,     # seconds inside one request: abort
}


class Supervisor(object):
    def __init__(self, recorder, engine, limits=None, goal=None):
        self.rec = recorder
        self.engine = engine
        self.limits = dict(DEFAULT_LIMITS)
        self.limits.update(limits or {})
        self.goal = goal
        self.t0 = time.time()
        self.nreq = 0
        # prompt loop
        self.last_prompt = None
        self.same_prompt = 0
        # turn progress
        self.last_turn = None
        self.req_since_turn = 0
        self.turn_recoveries = 0
        # novelty
        self.visited = set()
        self.last_novel_turn = 0
        self.stall_recoveries = 0
        self.max_depth = 0
        self.last_xl = 0
        # decision watchdog
        self._in_request_since = None
        self.watchdog_fired = None
        self._stop = False
        self._thread = threading.Thread(target=self._watch, daemon=True,
                                        name='decision-watchdog')
        self._thread.start()

    # ---------------------------------------------------------- watchdog
    def _watch(self):
        warned = False
        path = os.path.join(self.rec.gamedir, 'stacks.txt')
        while not self._stop:
            time.sleep(1.0)
            since = self._in_request_since
            if since is None:
                warned = False
                continue
            dt = time.time() - since
            if dt > self.limits['decision_warn'] and not warned:
                warned = True
                with open(path, 'a') as f:
                    f.write("=== decision running for %.0fs\n" % dt)
                    faulthandler.dump_traceback(file=f, all_threads=True)
                self.rec.note('slow-decision', round(dt))
            if dt > self.limits['decision_kill']:
                with open(path, 'a') as f:
                    f.write("=== decision killed after %.0fs\n" % dt)
                    faulthandler.dump_traceback(file=f, all_threads=True)
                self.watchdog_fired = "decision took more than %ds" % dt
                self.rec.note('decision-timeout', round(dt))
                try:
                    os.killpg(self.engine.proc.pid, signal.SIGKILL)
                except Exception:
                    pass
                return

    def begin(self):
        self._in_request_since = time.time()

    def end(self):
        self._in_request_since = None

    def stop(self):
        self._stop = True

    # --------------------------------------------------------- per request
    def on_request(self, bridge, req):
        self.end()
        self.rec.request(self.engine, req)
        self.nreq += 1
        st = self.engine.status
        lim = self.limits
        turn = st.get('turn') or 0

        # stop requested by a signal (the handler's own exception can be
        # swallowed by BotHack's delegator, which catches Exception)
        if getattr(self, 'terminated', None):
            raise BridgeAbort('limit', self.terminated)
        # goal reached?
        if self.goal and self.goal in self.rec.reached:
            raise BridgeAbort('goal', self.goal)
        # hard limits
        if turn >= lim['max_turns']:
            raise BridgeAbort('limit', 'max_turns %d' % lim['max_turns'])
        if time.time() - self.t0 >= lim['max_seconds']:
            raise BridgeAbort('limit', 'max_seconds %d' % lim['max_seconds'])
        if self.nreq >= lim['max_requests']:
            raise BridgeAbort('limit', 'max_requests %d' % lim['max_requests'])

        now = time.time()
        if now - getattr(self, '_live_t', 0) > 15:
            self._live_t = now
            self._write_live(st, turn)
        self._storm(turn)
        self._death_loop(turn)
        self._prompt_loop(bridge, req)
        self._action_loop(bridge, req, turn)
        self._fixation(bridge, req, turn)
        self._turn_progress(bridge, req, turn)
        self._novelty(bridge, req, turn, st)
        self.begin()

    def _death_loop(self, turn):
        """Invincibility can turn a lethal situation (lava, water, a gaze)
        into an endless series of undone deaths.  Heavy fighting also
        produces many lifesaves, so only abort when they pile up while the
        game makes no progress (no new stage, depth, experience level or
        newly occupied square: a slow advance through the Astral Plane crowd
        is progress, an undone death in the same few squares is not)."""
        ev = self.engine.assist_events
        n = len(ev)
        if n == getattr(self, '_assist_seen', 0):
            return
        self._assist_seen = n
        saves = [e.get('turn') or 0 for e in ev if e.get('kind') == 'lifesave']
        k = self.limits['death_loop']
        if len(saves) < k:
            return
        window_start = saves[-k]
        if saves[-1] - window_start > self.limits['death_loop_turns']:
            return
        progress_turns = [t for t in self.rec.reached.values()]
        progress_turns.append(getattr(self, 'last_depth_turn', 0))
        progress_turns.append(getattr(self, 'last_xl_turn', 0))
        progress_turns.append(getattr(self, 'last_novel_turn', 0))
        if max(progress_turns or [0]) >= window_start:
            return
        last = [e for e in ev if e.get('kind') == 'lifesave'][-1]
        raise BridgeAbort('stuck', 'death loop: %d assisted lifesaves in %d '
                          'turns without progress (last: %s)'
                          % (k, saves[-1] - window_start, last.get('killer')))

    def _storm(self, turn):
        """Many requests for almost no game time, whatever the recoveries
        did in between (a forced search advances the turn and would reset the
        per-turn detector)."""
        w = self.limits['storm_window']
        if self.nreq % w == 1:
            self._storm_turn = turn
        elif self.nreq % w == 0:
            start = getattr(self, '_storm_turn', turn)
            if turn - start < self.limits['storm_min_turns']:
                raise BridgeAbort('stuck', 'request storm: %d requests for %d '
                                  'turns (turn %d, last action %s)'
                                  % (w, turn - start, turn,
                                     self.rec.last_action_desc))

    def _write_live(self, st, turn):
        live = {'t': round(time.time() - self.t0), 'turn': turn,
                'lvl': (st.get('lvl') or '').strip(), 'dname': st.get('dname'),
                'hp': st.get('hp'), 'hpmax': st.get('hpmax'),
                'xl': st.get('xl'), 'requests': self.nreq,
                'actions': self.rec.nact, 'u': list(self.engine.u),
                'max_depth': self.rec.max_depth,
                'stages': self.rec.reached,
                'last_action': self.rec.last_action_desc,
                'notes': dict(self.rec.counters)}
        tmp = os.path.join(self.rec.gamedir, 'live.json.tmp')
        with open(tmp, 'w') as f:
            import json
            json.dump(live, f)
        os.replace(tmp, os.path.join(self.rec.gamedir, 'live.json'))

    def _prompt_loop(self, bridge, req):
        if req.kind in ('cmd', 'cmdcont'):
            self.same_prompt = 0
            self.last_prompt = None
            return
        key = (req.kind, req.query, req.prompt, req.goal,
               tuple(req.messages()))
        if key == self.last_prompt:
            self.same_prompt += 1
        else:
            self.same_prompt = 0
            self.last_prompt = key
        n = self.same_prompt
        if n == self.limits['prompt_loop'] // 2:
            self.rec.note('recovery', 'prompt-loop: escaping %r'
                          % (req.query or req.prompt or req.goal))
            bridge.force_escape = 3
        elif n >= self.limits['prompt_loop']:
            raise BridgeAbort('stuck', 'prompt loop: %r'
                              % (req.query or req.prompt or req.goal))

    def _action_loop(self, bridge, req, turn):
        if req.kind != 'cmd':
            return
        a = bridge.last_action
        if a is None:
            return
        sig = (a.get('type'), str(a.get('dir')), str(a.get('slot')),
               str(a.get('pos')),
               self.engine.u, turn, (self.engine.status.get('lvl') or ''))
        if sig == getattr(self, '_last_sig', None):
            self._sig_count += 1
        else:
            self._last_sig = sig
            self._sig_count = 0
            self._sig_recovered = False
        n = self._sig_count
        if n >= self.limits['action_loop'] and not self._sig_recovered:
            self._sig_recovered = True
            detail = bridge.recover_action_loop(a)
            self.rec.note('recovery', 'action-loop x%d %s: %s'
                          % (n, a.get('type'), detail))
        elif n >= self.limits['action_loop_abort']:
            raise BridgeAbort('stuck', 'action loop: %s repeated %d times at '
                              'turn %d (%s)' % (a.get('type'), n, turn,
                                                self.rec.last_action_desc))

    def _fixation(self, bridge, req, turn):
        """Goal targets the bot keeps choosing without ever getting them
        (unreachable/unaffordable items, a corpse it cannot reach, a tile it
        cannot explore) - one target or several alternating ones.  Every
        position quoted in an action's reasons is tracked; a target chosen
        continuously for `fixation_recover` turns, or 150 times without a
        pause, is forgotten; if it keeps coming back the game is aborted."""
        import re
        if req.kind != 'cmd' or bridge.last_action is None:
            return
        a = bridge.last_action
        if a is getattr(self, '_fix_last_action', None):
            return
        self._fix_last_action = a
        text = " ".join(str(w) for w in (a.get('reason') or [])[:1])
        m = (re.search(r"'x': (\d+), 'y': (\d+)", text)
             or re.search(r":x (\d+), :y (\d+)", text))
        if not m:
            return
        lvl = self.engine.status.get('lvl')
        key = (int(m.group(1)), int(m.group(2)), lvl)
        targets = getattr(self, '_fix_targets', None)
        if targets is None:
            targets = self._fix_targets = {}
        ent = targets.get(key)
        if ent is None or turn - ent['last'] > 50:
            ent = targets[key] = {'first': turn, 'last': turn, 'count': 0,
                                  'recovered': ent['recovered'] if ent
                                  else 0}
        ent['last'] = turn
        if (text.startswith(("hitting", "targetting"))
                and any(re.match(r"You (?:hit|miss|smite|kill|destroy)\b", msg)
                        for msg in req.messages())):
            # a real fight (the monster is there and is being hit/missed)
            # is not a fixation, however long it lasts (silver dragon on
            # the Plane of Earth, scen/planes-01)
            ent['first'] = turn
            ent['count'] = 0
            return
        ent['count'] += 1
        span = turn - ent['first']
        if len(targets) > 200:
            for k in [k for k, e in targets.items() if turn - e['last'] > 50]:
                del targets[k]
        if ((span >= self.limits['fixation_recover'] or ent['count'] >= 150)
                and ent['recovered'] < 3):
            ent['recovered'] += 1
            ent['first'] = turn
            ent['count'] = 0
            detail = bridge.forget_target(key[0], key[1])
            self.rec.note('recovery', 'fixation #%d on %r (%s): %s'
                          % (ent['recovered'], key, text[:60], detail))
        elif ent['recovered'] >= 3 and (span >= self.limits['fixation_recover']
                                        or ent['count'] >= 150):
            raise BridgeAbort('stuck', 'fixation: target %r keeps coming '
                              'back after 3 recoveries (%s)'
                              % (key, text[:80]))

    def _turn_progress(self, bridge, req, turn):
        if turn != self.last_turn:
            self.last_turn = turn
            self.req_since_turn = 0
            self.turn_recoveries = 0
            return
        self.req_since_turn += 1
        n = self.req_since_turn
        limit = self.limits['no_turn_requests']
        if n and n in (limit // 3, 2 * limit // 3):
            self.turn_recoveries += 1
            self.rec.note('recovery', 'no-turn-progress: forcing a search '
                          '(%d requests at turn %d)' % (n, turn))
            bridge.force_command = 's'
        elif n >= limit:
            raise BridgeAbort('stuck', 'no turn progress for %d requests at '
                              'turn %d (last action %s)'
                              % (n, turn, self.rec.last_action_desc))

    def _novelty(self, bridge, req, turn, st):
        depth = st.get('depth') or 0
        xl = st.get('xl') or 0
        key = (st.get('dnum'), st.get('dlevel'), self.engine.u)
        novel = False
        if key not in self.visited:
            self.visited.add(key)
            novel = True
        if depth > self.max_depth:
            self.max_depth = depth
            self.last_depth_turn = turn
            novel = True
        if xl > self.last_xl:
            self.last_xl = xl
            self.last_xl_turn = turn
            novel = True
        if novel:
            self.last_novel_turn = turn
            self.stall_recoveries = 0
            return
        stall = turn - self.last_novel_turn
        limit = self.limits['stall_turns']
        if stall >= limit // 2 and self.stall_recoveries == 0:
            self.stall_recoveries = 1
            self.rec.note('recovery', 'stall: %d turns without novelty, '
                          'resetting exploration state' % stall)
            bridge.request_exploration_reset()
        elif stall >= limit:
            raise BridgeAbort('stuck', 'no novelty for %d turns on %s '
                              '(last action %s)'
                              % (stall, (st.get('lvl') or '').strip(),
                                 self.rec.last_action_desc))
