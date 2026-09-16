"""PTY ownership, bounded reads, evidence capture, and run isolation."""
import fcntl, hashlib, json, os, pty, selectors, signal, struct, termios, time
from pathlib import Path
from .dialogue import classify, Prompt, Transaction
from .terminal import Terminal
from .world import World
from .strategy import Strategy


class Session:
    def __init__(self, game: str, run_dir: Path, seconds: float = 300, user: str = "bothack_new"):
        self.game, self.run_dir, self.deadline, self.user = game, run_dir, time.monotonic() + seconds, user
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.raw = self.run_dir / "terminal.bin"
        self.decisions = self.run_dir / "decisions.jsonl"
        self.term, self.world, self.strategy = Terminal(), World(), Strategy()
        self.recent_output = ""
        self.last_io = time.monotonic(); self.last_progress = self.last_io
        self.recoveries = 0; self.process = None; self.pid = None; self.returncode = None; self.master = None
        self.pending_prompt = None
        self.pending_keys = None

    def run(self) -> dict:
        # Valkyrie/dwarf gives the new strategy a credible early-game combat
        # baseline; the role choice is recorded in the run environment.
        options = "role:valkyrie,race:dwarf,!bones,!legacy,showscore,time,color,msg_wall_hits,autopickup,pickup_types:$%!,pettype:none,runmode:walk"
        env = os.environ.copy(); env.update({"TERM":"xterm", "NETHACKOPTIONS":options, "HOME":str(self.run_dir / "home"), "USER":self.user})
        (self.run_dir / "home").mkdir(exist_ok=True)
        self.pid, self.master = pty.fork()
        if self.pid == 0:
            os.execve(self.game, [self.game, "-u", self.user], env)
        fcntl.ioctl(self.master, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        os.set_blocking(self.master, False)
        sel = selectors.DefaultSelector(); sel.register(self.master, selectors.EVENT_READ)
        try:
            with self.raw.open("wb") as raw, self.decisions.open("w", encoding="utf-8") as log:
                while time.monotonic() < self.deadline and self._poll() is None:
                    events = sel.select(timeout=0.25)
                    if events:
                        try: data = os.read(self.master, 4096)
                        except OSError: break
                        if not data: break
                        raw.write(data); raw.flush(); self.term.feed(data); self.last_io = time.monotonic(); self.last_progress = self.last_io
                        # A stale message must not become a permanent command
                        # trigger.  The terminal screen is retained by
                        # Terminal; this field is only the current I/O batch.
                        self.recent_output = data.decode("latin1")[-1024:]
                        self.world = self.world.observe(self.term.snapshot().rows, self.recent_output)
                        prompt = classify("\n".join(self.world.screen) + "\n" + self.world.last_message); self._act(prompt, log)
                    elif time.monotonic() - self.last_io > 5:
                        self._recover(log, "no terminal data")
        finally:
            if self._poll() is None:
                try: os.kill(self.pid, signal.SIGTERM)
                except ProcessLookupError: pass
                end = time.monotonic() + 2
                while self._poll() is None and time.monotonic() < end: time.sleep(0.02)
                if self._poll() is None:
                    try: os.kill(self.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                    self._poll()
        return self.manifest()

    def _poll(self):
        if self.pid is None or self.returncode is not None:
            return self.returncode
        waited, status = os.waitpid(self.pid, os.WNOHANG)
        if waited:
            self.returncode = os.waitstatus_to_exitcode(status)
        return self.returncode

    def _act(self, prompt, log):
        if prompt == Prompt.END: return
        if self.pending_prompt is not None:
            if prompt != self.pending_prompt:
                self.pending_prompt = None
                self.pending_keys = None
            elif self.pending_keys in (b"e", b"a", b"?", b"\033", b"y", b"\n") or self.pending_keys.startswith(b"#pray"):
                # Menus and startup prompts may redraw repeatedly while the
                # game is waiting for the same response.  Re-sending a
                # response here consumes inventory or advances stale state.
                return
        decision = self.strategy.decide(self.world, prompt)
        if not decision.keys: return
        tx = Transaction(decision.reason, set(decision.expected), self.term.revision); tx.observe(prompt)
        os.write(self.master, decision.keys)
        if decision.reason.startswith("search for food"):
            self.world = self.world.food_search_started()
        self.pending_prompt = prompt
        self.pending_keys = decision.keys
        log.write(json.dumps({"at":time.time(),"prompt":prompt.value,"keys":decision.keys.hex(),"reason":decision.reason,"revision":self.term.revision})+"\n"); log.flush()

    def _recover(self, log, reason):
        self.recoveries += 1; self.world = self.world.invalidate(reason)
        # A silent PTY can still be sitting behind a pager or a stale map
        # cursor.  Space advances a pager, Ctrl-L requests a redraw, and the
        # escapes then cancel any nested command prompt.
        os.write(self.master, b" \014\033\033\033\033")
        self.pending_prompt = None
        self.pending_keys = None
        log.write(json.dumps({"at":time.time(),"recovery":reason,"count":self.recoveries})+"\n"); log.flush(); self.last_io = time.monotonic()

    def manifest(self) -> dict:
        digest = hashlib.sha256(self.raw.read_bytes()).hexdigest() if self.raw.exists() else None
        screen = self.term.snapshot().text().lower()
        raw_text = self.raw.read_bytes().lower() if self.raw.exists() else b""
        victory = b"ascended" in raw_text or b"you escaped" in raw_text
        death = b"you die" in raw_text or b"killed by" in raw_text or b"starved" in raw_text
        starvation_block = b"you don't have anything to eat" in raw_text and not death
        status = "ascension_candidate" if victory else ("death" if death else ("technical_stall" if starvation_block else "active_or_unproven"))
        return {"run_id":self.run_dir.name,"game":os.path.abspath(self.game),"game_sha256":hashlib.sha256(Path(self.game).read_bytes()).hexdigest(),"terminal_sha256":digest,"exit_code":self.returncode,"recoveries":self.recoveries,"victory_message_observed":victory,"death_message_observed":death,"status":status,"last_observed_turn":self.world.turn,"last_observed_hp":self.world.hp,"last_observed_level":self.world.level}
