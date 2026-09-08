# How the port is checked against the original

Everything below runs the **real** original: BotHack 70226b3 (the current
master of krajj7/BotHack) compiled with Leiningen on a Temurin JDK 8, playing
the NetHack 3.4.3-NAO build in `upstream/nh343`.  No part of the original is
modified; the harness only adds files of its own (`tools/cljcmp/*.clj`) to the
Leiningen source path.

## 1. Differential unit tests (`tests/test_differential.py`)

`tools/cljcmp/oracle.clj` runs inside the original project and answers
questions on stdin; `tools/canonical.py` and the Clojure `jsn` function
produce the same canonical JSON so answers compare as strings.

```
BOTHACK_SRC=… JDK8_HOME=… LEIN_DIR=… ./tools/run_oracle.sh   # record answers
python3 tests/test_differential.py                            # compare
```

| what | cases |
| --- | --- |
| `parse-label` on 60 item labels (BUC, erosion, charges, candles, shop prices, japanese names, artifacts, corpses…) | 60 |
| `item-type` / `appearance-of` / `initial-ids` / `item-id` for the same labels | 240 |
| 33 item predicates + subtype/weight/nw-ratio/enchantment/utility per label | 60 |
| 30 monster predicates for 70 monster types | 70 |
| `by-description` on 28 farlook descriptions | 28 |
| `room-type`, trap names, `effective-str`, `knowable-appearance?` | 24 |
| `parse-botls` on 6 real status lines | 6 |
| `parse-tile` + 12 tile predicates for 23 features × 41 glyph/colour pairs | 943 |
| NetHack FOV (`NHFov`) on 6 full 80×21 maps | 6 |
| `navigate` (A*/Dijkstra, `move`, `base-cost`, autotravel choice) on 3 maps × 6 goal kinds × 7 option sets, plus 16 point-to-point cases | 142 |
| `currently-desired` / `worthwhile?` / `should-try?` / `take-selector` / `drop-junk` / `utility` / nutrition / weight for 6 inventories × 30 candidate items | 6 |
| `edible?` / `want-to-eat?` / `safe-corpse-type?` for 58 foods × 48 player states (race, intrinsics, strength) | 48 |
| **35 top-level decision functions of the bot** (`fight`, `retreat`, `feed`, `progress`, `reequip`, `use-items`, `itemid`, `use-features`, `consider-items`, `handle-illness`, `handle-starvation`, `handle-impairment`, `recover`, `rob-peacefuls`, `get-protection`, `bag-items`, `shop`, `drop-junk`, `wear-armor`, `wield-weapon`, `bless-gear`, `use-light`, `enchant-gear`, `make-excal`, `handle-drowning`, `wander`, …) on 51 scenarios: 3 maps (one with fountains), 7 monster layouts (including two with 9 and 12 monsters), 3 inventories, hp/AC variations — over 2000 individual decisions.  Each scenario also checks the farlook chain (`examine-tile` / `examine-monsters` / `examine-features`, with the position they target) and the order `(vals (:monsters level))` yields | 51 |
| `(keys m)` for 20 maps built two ways - `(into {} …)` and a persistent `assoc` chain - with Position keys at 2, 3, 9, 10 and 12 entries | 20 |
| `(string/join (set …))` for 25 menu-answer sets — 16 sets of letters (Characters) and 9 sets of count+slot strings, which Clojure hashes differently; this is the order the bot presses menu keys in | 25 |
| `make-excal` / `seek-fountain` with a **known Oracle level** (3 inventories × 4 dungeon shapes × 5 player positions) — the only way to reach `seek-fountain`'s "walk to a fountain on this level" branch | 60 |

**Result: 1821/1821 identical.**

Bugs the three comparisons found — each a real behavioural difference, now
fixed and covered by cases above (the section that actually caught it is named
where it was not this one):

* `charged?` — `(fnil zero? 1)` was mistranslated, so *every* item without a
  charge count counted as uncharged; the bot considered its own starting
  equipment junk and unwielded it on turn 1.
* `take-selector` — the `or` chain of the original was flattened, so the bot
  picked up everything, including rocks it had just dropped (an infinite
  pick-up/drop loop that starved it to death).
* `utility` — the original applies `uncursed?` to `(:buc item)` instead of the
  item, so the +1 never fires; the port now reproduces that.
* `passive?` / `demon-lord?` — `(every? …)` is vacuously true for an unknown
  monster type, which is what makes the bot ignore unidentified `I` marks.
* `min-key`/`max-key` tie-breaking (last one wins) — got the branch-candidate
  level wrong.
* `(= true 1)` is false in Clojure — item-type merging kept `stackable`.
* `nw-ratio`, `typekw` on merged item records, float formatting.
* **Menu answer order** (caught by §2).  The bot answers a menu with a *set* —
  of inventory letters for a pick-up, of `count + slot` strings like `"3a"`
  for taking things out of a bag — and `(string/join options)` sends them in
  the set's iteration order, i.e. hash order for a PersistentHashSet.  The
  port joined a Python `set`, whose order depends on the interpreter's
  per-process string hash seed: the same code sent `,ab` in one run and `,ba`
  in the next, and only one of those matches the original.
  `delegator._respond_menu` now sorts by Clojure's HAMT key over
  `util.clj_hasheq`, which is the code point for a Character and
  `Murmur3.hashInt(String.hashCode())` for a String — the distinction matters,
  and getting it wrong the first time (treating `"3a"` as a character) crashed
  the take-out handler and livelocked the bot on a container for a whole game
  (`artifacts/games/py_menucrash`).  Fixing that moved recording A's first
  keystroke divergence from byte 910 to byte 11 326.
* **`into` vs `assoc` map order.**  `(into {} pairs)` builds through a
  *transient* array map, which **appends** and promotes to a hash map from the
  **9th** entry; a chain of persistent `(assoc m k v)` **prepends** and stays
  an array map until the **10th**.  Same insertion sequence, opposite
  iteration order - and the bot uses both on the same map: `gather-monsters`
  rebuilds `(:monsters level)` with `into` every frame while `reset-monster`
  `assoc`es into it in between.  The port applied the prepend rule everywhere,
  so it iterated the monsters in reverse scan order; that decides which old
  record a moving monster is paired with when two are equidistant, hence which
  monster keeps its identification and which one gets farlooked.  `clj.CljMap`
  now models both regimes (with sticky promotion).  Fixing this moved the live
  seed-31337 comparison from 286 identical keystrokes to 37 810.
* **Monster map iteration order.**  `(vals (:monsters level))` decides which
  monster the bot farlooks, which one `hunt` chases and how `track-monsters`
  pairs the old and new snapshots.  Clojure's `assoc` on a PersistentArrayMap
  *prepends*, so such a map iterates in **reverse** insertion order, and it is
  promoted to a PersistentHashMap (hash order) only on the assoc that would
  make the tenth entry — both boundaries verified against the original, with
  9- and 12-monster scenarios.  The port iterated Python's insertion order and
  farlooked the wrong monster; `clj.clj_vals` / `clj_keys` / `clj_items` now
  reproduce both regimes.
* **`(#{\I \1 \2 \3 \4 \5} (:glyph m))` on a nil glyph.**  Clojure returns
  nil; the port wrote `m['glyph'] in "I12345"`, which raises `TypeError` for a
  monster whose type has no glyph (the exception was swallowed by the
  delegator, so the bot silently skipped the whole decision).  Eight such
  membership tests are now tuple tests, which also stops `in` from matching a
  multi-character substring.
* `seek-fountain` — `(if-let [{:keys [step]} (navigate game fountain?)] step
  (or …))` binds on the **Path**, so when the bot is already standing on the
  fountain `step` is nil, the `if-let` returns nil and `make-excal` goes on to
  `->Dip`.  The port tested `step` for truthiness instead, fell into the else
  branch and walked off to look for another fountain on an earlier level — so
  it never dipped for Excalibur at all.  This one was found by the real-game
  comparison (§3), not by the unit tests, because none of the 32 combat
  scenarios has a known Oracle level; the 60 `excal` cases were added to cover
  it.

## 2. Replayed-game comparison (`tools/replay_compare.py`)

1. `tools/pty_tap.py` records a real game of the **original** bot: every chunk
   NetHack writes and every keystroke the bot sends, in order.
2. `tools/replay_server.py` plays that recording back *causally* — it emits
   the recorded output chunks and, wherever the recording shows the original
   having written N bytes, waits for the bot under test to write N bytes.
   Both bots therefore see the same bytes in the same chunks at the same
   points of the interaction.
3. The original is re-run against the replay (`tools/run_orig_replay.sh`),
   which captures its keystrokes under replay conditions, and the port is run
   against the same recording (`tools/replay_compare.py`).  Both use the same
   deterministic RNG (`tools/cljcmp/runner.clj` and `util.LCG`).

The two keystroke streams are then compared byte for byte, and the action
sequences (`tools/compare_actions.py`) are aligned with `difflib`.

## 2b. The same game, played live by both bots (`tools/live_compare.sh`)

This is the strongest test in the repository, and the only binary one: both
bots play **the same NetHack game**, live, and their keystrokes are compared
byte for byte.  A replay can only ever show that the port reacts to recorded
screens the way the original did; here the port drives a real game and the
game answers it.

Getting there meant pinning every source of non-determinism that is *not* the
port.  In order of how much each one mattered:

1. **NetHack's RNG** (`tools/det_rng.c`).  The NAO patchset seeds from
   `time()` + `/dev/urandom` at start-up *and re-seeds every 10-710 `rn2()`
   calls* (`src/rnd.c`, `check_reseed`), so no NetHack game is reproducible,
   with or without a fixed start seed.  The shim is `LD_PRELOAD`ed around the
   unmodified binary: the first `srandom()` is let through with
   `$NETHACK_FIXED_SEED`, every later one is swallowed, so the game runs one
   normal uninterrupted RNG stream that is identical from run to run.  This is
   **not** wizard mode - the rules, the binary and the bot are untouched, only
   the source of entropy is.
2. **The original's handler tie-break** (`tools/cljcmp/handlers_det.clj`).
   BotHack keeps its handlers in a `clojure.data.priority-map` and its own
   docstring admits that equal priorities have no defined order; in practice
   the order comes from the *identity* hashes of `reify` objects, so the
   original does not even agree with itself between JVM runs - its first two
   actions are `Discoveries, Inventory` in one run and `Inventory,
   Discoveries` in the next.  The harness rebinds `new-delegator` and
   `register` so a handler's priority becomes `[priority, registration
   counter]`: a total order, and the same rule the port uses.  Two JVM runs now
   both start `Inventory Discoveries Look FarLook Search`.
3. **Frame boundaries** (`tools/pty_tap.py`).  The tap detects that NetHack is
   blocked in `read()` (`/proc/<pid>/syscall`, `PTY_TAP_IDLE=0` to disable) and
   closes the group there, instead of waiting out a fixed window: about ten
   times faster - 31 interactions/s against 3.5 - and *more* deterministic,
   because the boundary no longer depends on how the scheduler spaced the
   game's writes.  The old timing rule survives as a fallback
   (`PTY_TAP_SETTLE`) and is described next, since it is what the earlier
   measurements used.
4. **The old timing rule** (`PTY_TAP_SETTLE`).  Both
   scrapers react to *frames*, and a frame is whatever one `read()` returned,
   so the boundaries depended on process scheduling: the two bots saw the same
   bytes cut in different places.  The tap now accumulates the game's output
   until the game goes quiet **or the bot writes its next key**, then emits it
   in fixed 256-byte pieces - framing becomes a function of the exchange
   instead of of how fast either bot runs.
5. **The bots' own RNG** - the shared LCG, `--lcg` for the port and
   `cljcmp.runner` for the original - plus the same player name, nethackrc,
   terminal size and binary.

```
BOTHACK_SRC=… JDK8_HOME=… LEIN_DIR=… \
  NETHACK_FIXED_SEED=4242 BOTHACK_SEED=12345 \
  tools/live_compare.sh artifacts/live_4242 600
```

`tools/compare_taps.py` then reports the first differing keystroke byte, and
how much of the two games was identical.  Because the port runs faster than
the original, the two runs cover different amounts of game in the same wall
clock; the claim the test can support is that the bots agree over the whole
**common prefix** of their keystroke streams.

Two harness faults, both found by this test and both fixed, are worth
recording because they produced convincing-looking false divergences:

* every run plays as the same user, and killing the original's `lein` wrapper
  leaves its NetHack child alive - the stray process then deletes the *current*
  game's level files as it exits (`Cannot open file "1000claudebot.0"`), which
  ends the running game mid-stream.  `live_compare.sh` kills strays before
  touching `var/`.
* editing a shell script while bash is running it corrupts the run: bash reads
  the file incrementally.  Two runs were lost this way.

## 2c-bis. The reference is not deterministic by default — and what makes it so

Before comparing anything to BotHack you have to know whether BotHack agrees
with *itself*.  It does not.  Recording the same seed twice, with handlers
pinned and both RNGs fixed, the original's own keystrokes diverge:

| seed | run 1 | run 2 | first difference |
| --- | --- | --- | --- |
| 40005 | 51 341 | 71 756 | byte 5 271 |
| 40001 | 59 210 | 59 399 | byte 16 126 |
| 40004 | 71 212 | 70 881 | byte 45 441 |

Two sources, both measured:

1. **The exploration cache is a `future`.**  `reset-exploration` stores
   `(future (curlvl-exploration game))`, which runs on `send-off-pool-1` while
   the agent threads drive the bot — and it draws from the RNG through
   `navigate` → `pass-monster` → `fidget` → `arbitrary-move`.  Which thread
   gets which draw is up to the scheduler.  `tools/cljcmp/det_cache.clj`
   computes the same value **synchronously on the calling thread** and stores
   it in an already-completed future, so `deref`, `exploration-index` and
   `future-cancel` all keep working.  Disable with `BOTHACK_DET_CACHE=0`.
2. **The JVM's terminal reader is its own thread** (`term.clj` starts one), and
   how many delivered pieces it swallows per `read()` varies — the scrapers
   react to *frames*.  `PTY_TAP_PIECE_DELAY=0.05` gives each frame room to be
   consumed on its own.

With both in place the original **is** reproducible against itself:

| seed | run 1 | run 2 | first difference |
| --- | --- | --- | --- |
| 40004 | 32 469 | 32 339 | none |
| 40005 | 28 035 | 27 958 | none |
| 40001 | 25 684 | 25 684 | none |

This is a **deliberate change of contract**, not a bug fix: it defines a
deterministic reference to compare against.  Captures recorded without it are
not retroactively explained by it, and any fidelity number measured against
the unpinned original is measured against a moving target.

It costs throughput: the same 600 s buys roughly a third to a half as much
game.  Budget from a measured pilot, never from the fast mode's numbers.

## 2d. Whole games: record once, replay often (`tools/fidelity_batch.sh`)

Playing both bots live costs twice as much as it needs to and has to be redone
after every fix.  Because the game is deterministic, the loop that actually
scales is:

1. `tools/record_orig.sh SEED OUT NAME SECS` plays **one full game** of the
   original with everything pinned and records it (`tap.log`).  Parallel runs
   get different NetHack user names so their lock/level files in `var/` do not
   collide - that collision destroyed a run before it was found.
2. `tools/replay_port.sh OUT` replays that recording into the port and compares
   its keystrokes with the ones the original actually sent.  No NetHack, no
   JVM, ~46 MB of RSS: it can be re-run after every fix.
3. `tools/classify_divergence.py A.tap B.keys` splits both streams on the
   scraper's `##'` sync and reports *which command* first differed, which is
   what says where to look in the code.

`tools/fidelity_batch.sh OUT N PAR SECS` does the whole thing.  The measure of
success is a whole game reproduced end to end, not a number of actions: a game
lasts 1 400-8 600 actions and then the bot dies.

Two harness lessons from building this, both of which cost long runs: never
`pkill -f` a pattern that also appears in your own command line (it kills the
calling shell), and never edit a shell script while bash is executing it.

A third lesson is about the tests themselves.  The differential suite happily
passed 1821/1821 while the port built the inventory map the wrong way, because
the oracle case and the port both built it with `into` - the scenario did not
reproduce the real code path.  What found the bug was tracing the *original*
during a real game (`tools/cljcmp/dbg_inv.clj`, enabled by an environment
variable, BotHack unmodified) and reading its actual iteration order.  When a
differential case and a live divergence disagree, trust the live one.

## 3. Real games (`tools/batch_py.sh`, `tools/batch_orig.sh`)

Both bots play the same locally built NetHack 3.4.3-NAO, no wizard mode, no
human intervention, each game capped by wall-clock time.  NetHack's own
`xlogfile` records the outcome of every finished game
(`tools/summarize_xlog.py`); it is the evidence used in `docs/RESULTS.md`.

Two whole-batch comparisons are worth more than the score table:

* **the distribution of action types.**  Both bots' logs name the action they
  perform; normalising by the number of actions makes the two batches
  comparable.  This is what found the `seek-fountain` bug: `dip` was 0.08 % of
  the original's actions and 0.00 % of the port's.
* **the vocabulary of `with-reason` strings.**  Every decision the bot makes
  carries a reason chain, and the two bots use the same strings, so the set of
  reasons each bot produced — and how often — says which strategies actually
  ran.  After the fix the port produces every reason the original does at a
  comparable rate, except situational ones neither bot is guaranteed to hit
  (`kick sink`, `exploring main until sokoban`).

## Known limits of the comparison

* **Handler priority ties.**  The delegator keeps handlers in a
  `clojure.data.priority-map`; ties are iterated in the hash order of the
  handler objects, which are `reify` instances with identity hashes, so the
  original itself picks a different order from run to run (observed: the very
  first pair of actions is `Discoveries, Inventory` in one run and
  `Inventory, Discoveries` in the next).  The port uses registration order.
* **Randomness.**  The bot calls `rand-int` in combat and exploration.  The
  comparison harness replaces it with the same LCG on both sides; ordinary
  runs use Python's RNG.  `tools/replay_compare.py --trace-rng FILE` and
  `BOTHACK_RNG_TRACE=FILE` (for `tools/cljcmp/runner.clj`) dump every draw of
  either bot, which is how the limitation below was measured; the two dumps
  from the same recording are in `artifacts/rng_trace/`.
* **Which draw is used.**  The two bots consume the *same* LCG values in the
  *same* number of draws — the first 24 draws of `artifacts/rng_trace/` match
  one for one — but they do not always use the same one.  While the player is
  stuck in a trap, `kick` calls `untrap-move`, which draws a random escape
  direction; the pathfinder's cost function calls `kick` for every kickable
  door it expands, so one `navigate` burns several draws and only the one
  from `path-step` becomes the action.  Measured on the recording in
  `artifacts/compare_final`: both bots make exactly three draws for that
  action, from the same three values, but the direction the original performs
  is the one from the **first** draw (1889 → index 1 → NE) and the port's is
  the one from the **third** (22087 → index 3 → SE).  What is not established
  is which of the three calls supplies each bot's action — the port's stacks
  were traced (two from the Dijkstra cost function, then `_path_step`), the
  original's were not.  It changes only randomised decisions, but it ends
  keystroke-level comparability wherever a recording contains one.
* A replay only stays meaningful up to the first divergence: after that the
  port is reacting to a game that answered someone else's keystrokes.
