# Handoff: making the Python port byte-identical to BotHack

Read this before touching anything.  It is written for another agent joining
the work, and it is deliberately explicit about what is *proven*, what is
*hypothesis*, and what has already been ruled out — so you don't spend hours
re-deriving what a measurement already settled.

## 1. What this repository is

A from-scratch Python rewrite of [BotHack](https://github.com/krajj7/BotHack)
(Clojure, commit `70226b3`), the first NetHack bot to ascend.  Framework *and*
the ascending `mainbot` strategy are reimplemented; no Clojure or Java runs at
run time and no decision is delegated to the original.  Target game: NetHack
3.4.3 + the nethack.alt.org patchset, built by `tools/build_nethack343_nao.sh`
into `upstream/nh343`.

The original is checked out in the scratchpad and is **never modified**.  The
comparison harness adds its own namespaces to Leiningen's source path and
rebinds vars with `alter-var-root`; that is the only way it touches BotHack.

## 2. The goal

Not "plays well".  The goal is **behavioural identity**: given the same NetHack
game, the port must send the same keystrokes as the original, byte for byte,
from the first to the last.  That is a binary, checkable property, unlike any
statistic over played games.

## 3. Where it stands

| | |
| --- | --- |
| differential unit cases vs the live original | **1821/1821 identical** |
| recordings of the original | 9 (1 381 – 8 559 actions) |
| of those, with an **attested** end of game (`You die...`) | **5** (40001-40003, 40008, 40009) |
| with an unattested end (cut off, or PTY error) | 4 (40004-40007) |
| recordings reproduced **end to end** | **0 / 9** |
| earliest divergence | 3.7 % of the stream (seed 40005) |
| latest divergence | 93.4 % (seed 40009) |

Five real fidelity bugs were found and fixed in the session that produced this
document: `seek-fountain` (the port never dipped for Excalibur), monster-map
iteration order, a `nil`-glyph `TypeError` the delegator was silently
swallowing, menu-letter order, and inventory order.

## 4. The method, and why it is shaped like this

### 4.1 Three levels of comparison

1. **Differential unit tests** (`tests/test_differential.py` + the Clojure
   oracle in `tools/cljcmp/oracle.clj`).  Cheap, exact, ~1800 cases.  Runs the
   real original as a subprocess answering questions on stdin.
2. **Replay** — a recorded game of the original is fed to the port, and the
   port's keystrokes are compared with the ones the original actually sent.
3. **Live byte-identical play** (`tools/live_compare.sh`) — both bots play the
   same seeded game.  Strongest, slowest.

### 4.2 Everything that is *not* the port had to be pinned

This took most of the effort and is the reason the comparison means anything:

* **NetHack's RNG** (`tools/det_rng.c`).  The NAO patchset seeds from `time()`
  + `/dev/urandom` **and re-seeds every 10–710 `rn2()` calls**
  (`src/rnd.c`, `check_reseed`), so no game was reproducible at all.  The shim
  is `LD_PRELOAD`ed around the unmodified binary and lets only the first
  `srandom()` through, with `$NETHACK_FIXED_SEED`.  Not wizard mode: rules,
  binary and bot are untouched.
* **The original's handler tie-break** (`tools/cljcmp/handlers_det.clj`).
  BotHack keeps handlers in a `clojure.data.priority-map` and equal priorities
  fall back to `reify` **identity hashes** — so the original does not even
  agree with itself between JVM runs (its first two actions are
  `Discoveries, Inventory` in one run and `Inventory, Discoveries` in the
  next).  The harness makes the priority `[priority, registration-counter]`.
* **Frame boundaries** (`tools/pty_tap.py`).  Both scrapers react to *frames*,
  and a frame is whatever one `read()` returned.  The tap now detects that
  NetHack is blocked in `read()` (`/proc/<pid>/syscall`) and closes the output
  group there, emitting fixed 256-byte pieces.  Faster *and* more
  deterministic than the timing heuristic it replaced (31 interactions/s
  against 3.5).
* **The bots' own RNG** — a shared LCG (`--lcg` for the port,
  `cljcmp.runner` for the original).

### 4.3 The loop that makes iteration affordable

Running both bots live costs twice what it needs to and must be redone after
every fix.  The game is deterministic, so:

```
tools/record_orig.sh SEED OUT NAME SECS   # expensive, once per seed
tools/replay_port.sh OUT                  # cheap (46 MB, no JVM), after every fix
tools/classify_divergence.py A.tap B.keys # says *which command* first differed
tools/fidelity_batch.sh OUT N PAR SECS    # all of the above, N seeds, PAR at a time
```

Parallel recordings use **different NetHack user names** so their lock/level
files in `var/` don't collide.

### 4.4 What actually finds bugs

Every fidelity bug found so far is the same species: **a Clojure semantic that
Python does not share**.  The list, because it is the most useful thing in this
document:

* `(into {} …)` builds through a **transient** array map → *appends*, promotes
  to a hash map at the **9th** entry.  A chain of persistent `(assoc m k v)`
  **prepends** and stays an array map until the **10th**.  Same insertion
  sequence, opposite iteration order.  Both appear in BotHack, sometimes on the
  same map.  `clj.CljMap` models both, with sticky promotion.
* Hash order for a promoted map = the HAMT order of the keys: 5-bit chunks of
  the hash, least significant first.  Position hashes are dumped from the
  original; `Character` hashes are the code point; `String` hashes are
  `Murmur3.hashInt(String.hashCode())` — and the port tells Characters from
  Strings by length, which is correct only because no set the bot builds mixes
  them.
* `PersistentHashSet` iteration order decides which menu letters are sent, and
  Python's `set` order depends on the per-process string hash seed — the same
  code sent `,ab` in one run and `,ba` in the next.
* `min-key` / `max-key` keep the **last** extreme on ties.  `choose-food` is
  `(min-by nw-ratio …)`, and two food stacks with equal nutrition/weight are a
  perfect tie, so the eaten item is decided purely by inventory order.
* `(if-let [{:keys [step]} (navigate …)] then else)` binds on the **Path**, so
  `step` may be nil while the `then` branch is taken; the `else` must not run.
* `(#{\I \1 …} (:glyph m))` on a nil glyph returns nil in Clojure; the Python
  `in "I12345"` raises, and the delegator swallows the exception so the whole
  decision is silently skipped.

### 4.5 The most important methodological lesson

**Trust the live trace over the code, and over the test suite.**

The differential suite passed **1821/1821 while the port built the inventory
map the wrong way**, because the oracle case and the port both built it with
`into` — the test scenario did not reproduce the real code path.  What found
the bug was tracing the *original* during a real game
(`tools/cljcmp/dbg_inv.clj`, enabled by an environment variable, BotHack
unmodified) and reading its actual iteration order.

Three hypotheses in a row were refuted this way on a single divergence class.
Static reading of the two sources is the slowest way to be wrong.

## 4.6 The reference had to be made deterministic first

BotHack does not agree with itself: recorded twice on the same seed with
handlers pinned and both RNGs fixed, its own keystrokes diverge (byte 5 271,
16 126 and 45 441 on seeds 40005/40001/40004).  Two causes, both measured and
both neutralised — the `future` behind `:explore-cache`
(`tools/cljcmp/det_cache.clj`) and frame coalescing by the JVM's terminal
reader thread (`PTY_TAP_PIECE_DELAY=0.05`).  With both, all three seeds
reproduce exactly.  See `docs/TESTS.md` §2c-bis.

**Consequence: every divergence number measured before this was measured
against a moving target**, including the nine-recording table below.  It has to
be redone against the deterministic protocol.  The five bugs fixed so far are
unaffected — they were each demonstrated by other means (differential cases,
live inventory traces, map-order measurements).

## 5. The three open classes

Nine recordings, nine divergences, grouped by symptom.  **Only five of the
nine reach an attested end of game**; 40004-40006 stop mid-activity at the same
timestamp (a campaign limit) and 40007 ends on a PTY I/O error.  A recording
that was cut off can only ever prove "identical over what was captured", never
"identical game".  **The grouping is a working
hypothesis, not a proven common cause** — only seed 40005 has been traced to a
root.

| class | seeds | first differing command |
| --- | --- | --- |
| `search` vs move | 40001, 40006, 40009 | one searches, the other moves |
| different direction | 40002, 40003, 40005 | `move NE` vs `move E` |
| `look here` vs action | 40004, 40007, 40008 | `:` vs `throw` / `move` |

### The "different direction" class — narrowed, not closed

On seed 40005 the performed action differs by **exactly one reason**: the
port's chain carries `arbitrary direction` (so it came from `arbitrary-move`),
the original's does not, though both start with `fidgeting to make peacefuls
move` / `peaceful blocker`.

Ruled out **by measurement**, in order — do not re-investigate these:

* **the RNG**: 538 draws compared, identical values *and* identical kinds
  (13 `rand-nth`, 193 `rand-int 10`, 187 `rand-int 200` on each side);
* **`arbitrary-move` itself**: at the deciding draw (7th `rand-nth`, value
  7092) both see the same position, the same 8 neighbours in the same order,
  and both return `E`;
* **the `:blocked` counter**: nil on both sides, because the blocker is a
  shopkeeper inside a shop and both implementations skip the increment there
  (verified by tracing `about_to_choose`);
* **`fidget` itself**: tracing every return of the original's `fidget` shows
  **777/777** of its moves carry `arbitrary direction`, so the performed action
  did not come from `fidget`.

What is left: both chains contain `using cached exploration step`.  The action
inherited the fidget reasons **through the exploration cache**.  In the
original that cache is a **`future`**:

```clojure
(swap! (:game bh) assoc :explore-cache (future (curlvl-exploration game)))  ; about-to-choose
@(:explore-cache game)                                                     ; explore, blocking
(future-cancel f)                                                          ; action-chosen
```

The port computes `_curlvl_exploration(game)` eagerly and synchronously at the
same point.  Both capture the same pre-action state, so the *value* ought to
match — but `curlvl-exploration` runs `navigate`, whose cost function calls
`fidget`, which **draws from the RNG**, and in the original that happens on
another thread and can be cancelled mid-computation.

## 6. Pitfalls that have already cost hours

* `pkill -f <pattern>` / `pgrep -f` match **your own shell's command line**.
  Three runs died with exit 144 this way.  Kill by process name (`pkill -x
  java`, `pkill -x nethack.343-nao`) or use `[p]attern`.
* **Never edit a shell script while bash is executing it** — bash reads it
  incrementally and resumes mid-token.  Two long runs lost.
* `kill` on the `lein` wrapper leaves the **JVM alive**.  A handful of
  leftovers exhausts this 11 GB machine and the OOM killer takes down the run.
  `live_compare.sh` reaps them; cap the JVM (`-Xmx768m`).
* A **stray NetHack process** deletes the *running* game's level files on exit
  (`Cannot open file "1000claudebot.0"`), ending a game mid-stream, because
  every run plays as the same user.
* `difflib.SequenceMatcher` is quadratic in memory; a full game is ~120 KB per
  side.  `replay_compare.py` caps it (`REPLAY_DIFFLIB_LIMIT`).
* The original **stalls without DEBUG logging** (its scraper is timing
  sensitive) and hangs forever with `:no-exit true` unless killed by the
  harness.

## 7. Map of the tooling

| path | what |
| --- | --- |
| `pybothack/` | the port; `clj.py` holds the Clojure-semantics emulation (`CljMap`, `clj_vals`/`clj_keys`/`clj_items`, `into_map`) |
| `tools/cljcmp/oracle.clj` | answers differential questions from inside the original |
| `tools/cljcmp/runner.clj` | runs the original with the shared LCG + pinned handlers |
| `tools/cljcmp/handlers_det.clj` | pins the handler tie-break |
| `tools/cljcmp/dbg_inv.clj` | opt-in live tracing of the original (inventory order, `arbitrary-move`, `fidget`) — the tool that actually finds bugs |
| `tools/det_rng.c` | fixes NetHack's RNG seed via `LD_PRELOAD` |
| `tools/pty_tap.py` | records both directions with deterministic framing |
| `tools/record_orig.sh`, `replay_port.sh`, `fidelity_batch.sh` | the record-once / replay-often loop |
| `tools/classify_divergence.py` | turns a byte offset into "which command differed" |
| `docs/PORT.md`, `TESTS.md`, `RESULTS.md`, `LIMITATIONS.md` | design, test method, measurements, honest list of what is broken |

## 8. What "100 %" would mean

Three rungs, and we are below the first:

1. **one full game reproduced end to end** — never achieved;
2. **all nine local games** — what the current loop can prove;
3. **N games on random seeds** — the only strong sense of "100 %", and where
   renting a big machine pays: once the frequent bugs are gone, only scale
   surfaces the rare ones.

Each fix so far has *moved* the wall rather than removed it (seed 40004 went
from 5.1 % to 20.2 % of the stream and still diverges).  Nobody knows how many
bugs lie behind the first one.
