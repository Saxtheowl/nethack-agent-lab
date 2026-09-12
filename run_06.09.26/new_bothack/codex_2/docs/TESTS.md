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

A stronger check, run days apart on different `var/` contents: seed 40002
recorded once with a 2 400 s cap (84 892 keystrokes) and once with a 700 s cap
(30 085 keystrokes) agrees on **30 085 of 30 085** bytes - the shorter run is an
exact prefix of the longer.  The reference is reproducible across sessions, not
just back to back.

This is a **deliberate change of contract**, not a bug fix: it defines a
deterministic reference to compare against.  Captures recorded without it are
not retroactively explained by it, and any fidelity number measured against
the unpinned original is measured against a moving target.

It costs throughput, and the cost is now measured rather than estimated: on
seed 40002 the piece delay accounts for **56 578 pieces x 0.05 s = 2 829 s of
deliberate sleep out of 3 644 s elapsed, 78 %** of the recording's wall clock.
That is an upper bound on what a smaller delay could recover - some of the
sleeping overlaps with the JVM's own work - but nothing else in the protocol is
close.  The delay's job is to make the JVM's reader consume one piece per
`read()`, so that the recorded piece boundaries *are* the frames the original
reasoned about.

`tools/piece_delay_probe.sh` measures how low it can go, and the test is the
*replay verdict*, not an agreement between two runs.  On seed 40001, idle 4-core
box: **0.02 records 28 % faster and the original plays the byte-identical game**
(so the piece boundaries did not move), while 0.01 records 43 % faster but plays
a *different* game - the symptom of shifted boundaries - even though the port
still reproduces that capture exactly.  Below ~0.02 the JVM is the bottleneck
anyway.  So 0.02 is the safe operating point, and the probe should be re-run on
any new machine and at the slot count actually used, because coalescing is a
scheduling property.  Until it is answered, budget from
the measured rate: **~3.4 game turns per second**, and roughly one game in six
finishing inside a 1 800 s cap.

### The pinning is partial, and load breaks it

Re-recording four of the same seeds in a later campaign, this time **while
CPU-heavy replays were running on the same machine**, the original no longer
agrees with its earlier self past a point:

| seed | campaign 1 | campaign 2 | common prefix |
| --- | --- | --- | --- |
| 40001 | 25 672 | 25 672 | 25 672 (100 %) |
| 40002 | 84 892 | 78 763 | 41 671 (52.9 %) |
| 40004 | 98 962 | 94 058 | 16 860 (17.9 %) |
| 40005 | 95 922 | 82 753 | 5 271 (6.4 %) |

`var/` held no bones files in either campaign, and `logfile`/`record`/`xlogfile`
do not feed gameplay, so the shared state is not the explanation.  The known
difference between the two campaigns is the concurrent load: the JVM's terminal
reader is its own thread and `PTY_TAP_PIECE_DELAY` only widens the window in
which it consumes one piece per read - it does not close it.  Saying which of
"residual thread nondeterminism" and "CPU contention" dominates would be a
guess; what is measured is that a loaded machine loses reproducibility, and that
the shortest game (which dies early) keeps it.

Two consequences, and the first one matters most:

1. **This does not weaken the replay measurements.**  A recording is a
   self-contained reference: the replay feeds recorded bytes to the port with no
   NetHack, no JVM and no threads, so it is deterministic whatever produced the
   capture.  "The port reproduces this recording" stands on its own.
2. It does mean recordings must be made on an **otherwise idle machine** if two
   campaigns are ever to be compared with each other, and that a campaign's
   recordings should be kept, not regenerated on demand.

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

Three harness lessons from building this, each of which cost a long run: never
`pkill -f` a pattern that also appears in your own command line (it kills the
calling shell); never edit a shell script while bash is executing it; and never
kill by *binary* name.  `pgrep -x nethack.343-nao` matches every NetHack on the
machine, so a comparison run clearing its own leftovers would kill a recording
campaign's game mid-flight.  `live_compare.sh` now matches the player name on the
process's own command line (`-u NAME`) and prints what it is leaving alone, and
`LIVE_PLAYER` lets parallel runs pick distinct names so their lock and level
files in `var/` cannot collide either.

A third lesson is about the tests themselves.  The differential suite happily
passed 1821/1821 while the port built the inventory map the wrong way, because
the oracle case and the port both built it with `into` - the scenario did not
reproduce the real code path.  What found the bug was tracing the *original*
during a real game (`tools/cljcmp/dbg_inv.clj`, enabled by an environment
variable, BotHack unmodified) and reading its actual iteration order.  When a
differential case and a live divergence disagree, trust the live one.

## 2e. Comparing decisions, not bytes (`tools/compare_decisions.py`)

A keystroke offset says *where* two runs part company; it does not say *which
decision* went wrong, and "byte 63 137" is not a lead.  The original logs every
chosen action together with its `with-reason` stack at DEBUG level, and the port
records the same pair (`replay_compare.py --actions-out`), so the two decision
streams align directly and the first differing pair names the function to read:

```
tools/compare_decisions.py OUT/bothack.log OUT/port_actions.tsv
```

```
first differing decision: index 3312 (64.1% in)
>>  3312  orig search   baiting monsters | targetting enemy #...Monster{...}
>>        port move     targetting enemy {'x': 59, 'y': 12, ...}
```

That one line pointed at `mainbot.clj:1331` and, from there, at Clojure set
iteration order.  Action *indices* are comparable here - unlike keystroke
offsets - only because both sides count one entry per chosen action, and
`Repeated` writes a single trigger and so counts once on both sides.

Parsing note that cost an hour: log4j writes the reason vector as continuation
lines of the same event and one reason can be a whole printed record spanning
several lines, so the block has to run until the next timestamped event.
Counting brackets instead swallows the rest of the log, because a printed record
carries its own vectors and its strings hold stray brackets - that bug silently
reported 607 actions instead of 5 084.

## 2f. Calibrating Clojure's hashing against the JVM (`tests/test_clj_hash.py`)

Clojure set iteration order is the HAMT order of the elements' `hasheq`, and the
bot keeps monsters in sets, so the port has to compute `hasheq` for a record.
Reading the algorithm out of Clojure's source is not enough - two of the pieces
are wrong in ways that pass most inputs:

* `Util.hashCombine`'s `seed >> 2` is Java's **arithmetic** shift on a signed
  int.  Masking to 32 bits first makes it logical and still gives the right
  answer for every non-negative seed, so `:white`, `:fleeing`, `:first-known`
  and `:remembered` matched the JVM while `:x`, `:y` and `:known` did not.
* `map->Monster` materialises every declared record field the literal omits, as
  nil, so the map has an entry the port's dict did not - and the entry *count*
  goes into the hash.

So the numbers are **dumped from the JVM** rather than derived:
`tools/cljcmp/dump_hash.clj` prints the calibration table (one value of every
type a Monster field can hold), the record type-hashes, all 376 monster-type
hashes, four whole monsters with their `mapHasheq` and `hasheq`, and the seq
order of a set of them.  `pybothack/_hashdata.json` is the extracted table and
`tests/test_clj_hash.py` checks the port against every value.

The monster-type table is keyed by name **plus glyph and colour**: three names
(werejackal, werewolf, wererat) carry two distinct type records each, and keying
by name alone silently gives one of them the other's hash.

## 2g. Judging a recording before judging the port (`tools/recording_verdict.py`)

A capture cut off by the wall clock is a *prefix* of a game, and no amount of
fidelity can make it PASS_COMPLETE.  `recording_verdict.py` labels each
recording GAME or TRUNCATED from the end markers in the capture itself, and
correlates it with NetHack's own xlogfile entry - matched by player name **and**
an endtime inside the recording's window, because `var/` is shared and matching
by name alone attributes another run's turn count to this one.  In that entry
`death=a trickery` is the discriminator: it is what NAO's hangup path writes
when our wall-clock cap killed the process, while a game that really ended
carries its death reason and a non-positive hp.

`tools/fidelity_manifest.py` aggregates a batch into `manifest.json` and keeps
the two verdicts apart, so the headline is "PASS_COMPLETE out of recordings that
are whole games" and the truncated captures are listed rather than diluting
either side.

### Length is a test dimension, not a detail

Eleven captures of 21 000-99 000 keystrokes were all reproduced byte for byte.
The first capture recorded under a 7 200 s cap - seed 40002, where the bot
survived the whole two hours and produced **313 786 keystrokes**, 3.2x the
longest previous - diverged at byte 110 316, which is *past the end of every one
of those eleven*.  The cause (`should-try?` applied to the item-id record,
`docs/LIMITATIONS.md`) needs a wand whose appearance has been engrave-tested and
then zap-identified: a state the bot only reaches deep into a game.

So a corpus of short captures is not a small version of a corpus of long ones.
Budget for length, not just for count.

## 2h. Auditing the class, not the instance (`tools/audit_*.py`)

Three of the fidelity bugs found so far were each one *instance* of a class that
could have more members.  Reading the source by hand does not settle that; a
structural scan does.  `tools/cljread.py` is a small Clojure reader (lists,
vectors, maps, sets, strings, character literals, and `@x` expanded to
`(deref x)` - that last one matters, see below), and three audits run over the
form tree.

| audit | class | verdict on BotHack |
| --- | --- | --- |
| `audit_atom_args.py` | a bare `game` (the **atom**) reaching a function that wants the map, so `(:k atom)` and `(get-in atom …)` silently answer nil | **exactly 2 sites**: `Throw`'s `visible?` and `Discoveries`' `:used-names`.  Both reproduced deliberately. |
| `audit_or_side_effects.py` | a non-final `or`/`and` clause whose *value* comes from a side-effecting call, so the `or` short-circuits where the code reads like a statement | 12 sites; 11 are deliberate or return nil, 1 was a real port divergence (`FarLook`'s altar clause) and is fixed |
| `audit_set_order_uses.py` | a Clojure set whose **iteration order** reaches a decision, because Python's set order is unrelated | **6 sites, all accounted for** (below) |
| `audit_port_condp.py` | the mirror direction: port code that behaves like `condp-all` (every matching clause fires) where the original wrote `condp` (first match wins) | **3 runs, all inside the one legitimate `condp-all`** - `game.clj:344`, 66 clauses, split by intervening assignments.  Has a `--self-test` that proves it detects a lost short-circuit |
| `audit_iflet_destructuring.py` | `(if-let [{:keys [step]} (navigate …)] step else)` tests the **container**, so a Path with a nil step runs the *then* branch and yields nil - the else branch never gets a chance | **4 sites**; one was the Excalibur bug (`seek-fountain`, fixed), the other three are faithful - two guard the nil themselves with `(or step …)`, and `seek` reproduces the quirk on purpose |
| `audit_map_order_uses.py` | the same for maps: array-map `assoc` prepends, `(into {} …)` appends, the ninth or tenth entry promotes to hash order | **10 sites, all accounted for**: 6 are booleans or counts over every entry, 3 are `track-monsters`/`hunt-action` which already use `CljMap`/`clj_vals` with `max_by`'s last-extreme tie rule, and 1 (`apply-blueprint`'s reduce over `:monsters`) is vacuous - no extracted blueprint carries a monster |

The six order-sensitive set uses, and why only one needed a fix:

| site | use | verdict |
| --- | --- | --- |
| `bots/mainbot.clj:1323` | `(find-first #(= 2 (distance player %)) … threats)` | **the bug**; `clj_set_order` + `monster_hasheq` |
| `pathing.clj:420` | `(first goal-set)` | reached only from `(case (count goal-set) … 1 …)`, so there is one element |
| `dungeon.clj:582` | `(first open)`, a flood-fill frontier of tiles | the result is min/max corners over the same closed set, and reachability through non-door tiles does not depend on visitation order - order-independent |
| `actions.clj:1030` | `(seq path)` | a truthiness test |
| `bots/wizbot.clj:187,188` | `(into res …)` | `wizbot` is the wizard-mode test bot and is not ported |

`audit_set_elements.py` answers the companion question - which sets hold Clojure
*Strings* rather than Characters, since the two hash differently.  96 of them
do, but only a set whose order is observed can be affected, so the list is read
against `audit_set_order_uses.py`: all but the menu answers are membership tests whose order is never observed,
and `impaired?`/`dizzy?`, whose `(some (:state player) #{...})` *does* return the
element found, are used only in boolean position (checked at every call site).

Three lessons from building these, each of which produced a wrong answer first:

* **Recurse into subdirectories.**  `bots/mainbot.clj` is the densest decision
  code in the project and a flat `os.listdir` skips it silently.  The first run
  of all three audits reported "nothing in mainbot" - because it had never
  looked.
* **Expand `@`.**  A reader that treats `@game` as transparent sees the deref as
  a bare `game`, and the atom audit then reports 46 sites, every one of them a
  correct deref.
* **Look through `if`.**  `navigate` binds its goal collection with
  `(let [goal-set (if (set? x) (->> x … set) (->> … set))] …)`.  A check that only
  understood `(-> … set)` reported nothing for the most load-bearing function in
  the project, and missed the flood-fill frontier too.
* **Respect rebinding.**  `(choose-action [_ game] ...)` rebinds `game` to a
  *value*; a line-based scan that assumes "atom until the next top-level form"
  turned 2 real sites into 114.  And `defaction`, BotHack's own macro, carries
  the `(handler [_ {:keys [game] :as bh}] ...)` that holds *both* real bugs -
  leaving it out of the method-bearing forms made the audit report one
  irrelevant site and neither real one.

Two more things were checked by hand rather than by audit, because neither has
an instance to validate against.

**Bounds.**  Clojure's `get-in` answers nil out of range, but `position/at`
carries a `:pre` assertion and *throws*, which the delegator catches - so the
original loses the handler that asked.  Python has a third behaviour: a negative
index wraps to the far end of the row and answers confidently with the wrong
tile.  The port now asserts like the original.  Checked on both complete games
with DEBUG logging: the guard never fires, so it is a latent fix.

**Integer division.**  Clojure's `quot` truncates toward zero, Python's `//`
floors, and they differ for negative operands.  The original has 16 `quot`/`mod`
sites (charge and price arithmetic in `itemid.clj`, `(quot maxhp 7)`, turn
arithmetic in the farming predicates, a ttyrec timestamp); every operand is
non-negative by construction, so `//` and `%` are exact there.  Worth
re-checking if arithmetic on a signed quantity is ever added.

**The min/max tie rule.** `(min-key f)` / `(max-key f)` keep the **last**
extreme.  The original has 8 call sites outside `util.clj`; the port has 8 uses
of `min_by`/`max_by`/`first_min_by`, whose docstrings state the rule, and no
`min(...)`/`max(...)` with a `key=` anywhere (Python's would keep the *first*).
The two remaining `(partial min-key first)` are the pathfinder's cost merge -
`_PriorityMap.put` replaces an entry on an *equal* priority, which is what
`min-key` does with two arguments - and the port truncates the accumulated
distance with `int()` exactly where the original writes `(int (+ dist cost))`.

An audit that reports nothing is worthless until it has been shown to find a bug
you already know about.  All six are checked against their own known instance,
except the one above, which is a hand check and is labelled as such.

## 2i. Diagnosing a live stall without drowning in DEBUG

A stalled game leaves nothing useful behind: the INFO log's last line is an
ordinary action, and running a three-hour game at DEBUG costs about 1.2 GB.  So
the scraper keeps its last 60 state transitions in memory
(`scraper.RECENT` / `recent_transitions()`), and `main.py`'s watchdog dumps them
next to the stack trace when no action has been chosen for a while:

```
WATCHDOG=120 tools/ascend_batch.sh out 12 6 0     # or tools/ascend_pool.sh
```

The stack says *where* the process is waiting - invariably
`iface.wait_readable`, i.e. blocked on the game, not computing.  The ring buffer
says *why*: which scraper state it settled in, and what the cursor and topline
looked like on each frame leading there.  That is what turned "the bot sometimes
freezes deep in the game" into the three-line reproduction in
`docs/LIMITATIONS.md`.

Two earlier attempts that did not work, worth not repeating: the "slow decision"
warning fires *after* an action is chosen, so a bot that never chooses another
one never logs anything; and the game's ttyrec is contaminated by the `#` that
`quit-when-idle` writes to unstick, so its final frames are not the stalled
state.

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

## 2j. Playing the original at volume (`tools/ascend_pool_orig.sh`)

The mission asks for both bots' results to be compared, and the replay gate only
compares them on *recorded* games, which are short.  This plays the original in
real games under the same conditions the port plays under - same NetHack build,
same `bothack.nethackrc`, no wizard mode, no fixed seed, and a config **without**
`:no-exit` so the original's own quit handlers stay enabled.  BotHack is not
modified; Leiningen's source path is the only thing the harness touches.

`tools/compare_realgames.py` then reads NetHack's own xlogfile - written by the
game, not by either bot or by the harness - and splits it by player-name prefix.
It prints a warning of its own when the original has fewer than 20 games,
because a table with n=5 on one side invites a conclusion it cannot support.

### The original must be run at log level DEBUG

Twelve original games in a row connected, sat at turn 1, and were quit by their
own `quit-when-idle` three minutes later.  No exception, no error - it looks
exactly like a bot that refuses to play.  Bisected, one variable at a time:

| invocation | rendered frames | result |
| --- | --- | --- |
| `JVM_OPTS`, log4j **INFO**, FileAppender, `-Xmx1500m` | 3 | frozen at T:1 |
| `JVM_OPTS`, log4j **INFO**, FileAppender | 3 | frozen at T:1 |
| `lein update-in :jvm-opts conj`, log4j **INFO** | 3 | frozen at T:1 |
| `JVM_OPTS`, log4j **INFO**, RollingFileAppender | 3 | frozen at T:1 |
| `JVM_OPTS`, log4j **DEBUG**, RollingFileAppender | 241 | **T:30, playing** |
| no `JVM_OPTS` (BotHack's shipped `src/log4j.properties`: DEBUG) | 4023 | **T:679, Dlvl:2** |

The log **level** is the discriminator.  Not `JVM_OPTS`, not the heap, not the
appender class - each of those was suspected in turn and each was exonerated by
holding it constant while the level changed.

Why a log level should decide whether a bot plays: DEBUG logging is slow, and
BotHack is timing-sensitive at startup - the same property that
`PTY_TAP_PIECE_DELAY` exists for elsewhere in this harness.  The likeliest
reading is a startup race that DEBUG's slowness masks.  DEBUG is also what
BotHack ships in `src/log4j.properties`, so it is the faithful setting as well
as the working one; `tools/ascend_pool_orig.sh` sets it and says why.  Do not
"tidy" it to INFO.

Two things this cost, both worth recording.  First, I wrote up `JVM_OPTS` as the
cause after a two-point comparison, before bisecting - the first table row and
the last differ in four things at once, and I read a four-variable difference as
a one-variable one.  Second, for a while this looked like evidence about the
*original's* behaviour, when it was evidence about my invocation of it.  A
comparison harness that silently cripples one side produces numbers worse than
none.

## 2k. Do the comments still quote real Clojure? (`tools/audit_quoted_clojure.py`)

The port documents itself by quoting the Clojure it implements, and those quotes
are load-bearing: they are what a reader checks the port against, and what I
check it against when hunting a divergence.  A quote that has drifted from the
source turns the comment into a confident lie.

    BOTHACK_SRC=<checkout> python3 tools/audit_quoted_clojure.py

It extracts every comment and string literal, finds the Clojure forms in them,
splits each on `...` (elision is normal and is not drift), and requires every
remaining segment of 24 characters or more to appear in the BotHack source with
whitespace normalised.  Forms using metasyntactic argument names - `(assoc m k
v)`, `(update-in m path f & args)` - are skipped: those explain a core Clojure
function rather than quoting BotHack, and BotHack's own code never names
arguments that way.

Validated the way the other audits are, against a deliberate corruption:
changing a quoted `"3+ min idle - quitting"` to `"4+ ..."` makes it report that
segment and nothing else; restoring returns it to clean.  **18 segments checked,
0 missing** at the time of writing.

It found one real drift on its first run: `bots/mainbot.py` quoted
`(and (not minetown) (navigate game fountain?))` where the original says
`(and (not (:minetown (curlvl-tags game))) (navigate game fountain?))`.  The
*code* was right - including the `if-let`-binds-on-the-container subtlety that
makes `seek-fountain` return nil when already standing on the fountain - only
the comment had been paraphrased.

### What it cannot catch

The defect that motivated it.  In `quit-when-idle` the comment quoted

    (defn- u "unpause" [] (r) (if (:inhibited ...) (unpause a)))

verbatim and correctly, and then the port implemented `u` where the original
calls `unpause`.  The quote was right; the *attribution* was wrong.  No textual
check finds that - only reading the call site does.  This audit lowers the cost
of the failure next to it, and that is all it claims.

## 2l. Two seeds, and the day one cost

A replay campaign reported `DIVERGENCE` on four captures that had been
`PASS_COMPLETE` the same morning, against recordings unchanged on disk since
two days earlier.  The divergence was a **single byte** at offset 14 132 of
25 672 - the original moved (`j`), the port searched (`s`) - with the same 1 750
actions and the same 10 292 chunks replayed on both sides.

It was not a regression.  There are two seeds in this harness and they are easy
to confuse:

| | what it seeds | set by | value |
| --- | --- | --- | --- |
| NetHack seed | the *game* - level layout, item randomisation | `NETHACK_FIXED_SEED` via `tools/det_rng.so` | 40001, 40002, … |
| bot seed | the *bot's own* RNG, `LCG` | `BOTHACK_SEED` in `tools/record_orig.sh` | **12345** |

The corpus directories are named after the **NetHack** seed (`seed40001/`).
`replay_compare.py --seed` wants the **bot** seed.  A batch loop that derived
the flag from the directory name - `seed=$(basename "$d" | sed 's/seed//')` -
therefore handed the port an RNG stream the original never had.  Almost every
decision is forced by the recorded frames, so the streams stayed identical for
55% of the game until one genuinely random choice landed differently.  That is
the worst possible failure shape: too deep to look like a configuration error,
too small to look like anything but a subtle fidelity bug.

### What settled it

Not reasoning - a control.  Every candidate cause was eliminated on evidence
(the farlook at the divergence is a jackal, so the String-typed path is not
involved; no description in the recording carries `saddled ` or `invisible `;
the replay config sets `:no-exit`, so the idle handler is not registered;
`monster_hasheq` is identical across processes).  That left an empty candidate
set, which is itself the signal that an *assumption* is wrong rather than a
hypothesis.  Building an exact inverse of the day's edits and replaying it -
**same divergence, same byte** - proved the code was never implicated, and
attention moved to the invocation, where the bug was.

Three identical runs at the wrong seed all diverge at 14 132, so the replay is
deterministic exactly as §2c-bis claims; determinism was never the problem.

### The harness now refuses the mistake

* `tools/recording_verdict.py` writes `bot_seed` into `recording.json` beside
  the existing (NetHack) `seed`, so a recording states both.
* `tools/replay_compare.py` reads the sibling `recording.json` and **errors out**
  when `--seed` disagrees with `bot_seed`, or when `--seed` is passed the
  recording's NetHack seed.  Validated both ways: the wrong seed is rejected by
  name, the correct invocation runs.

The lesson worth keeping is not "check the seed".  It is that when every
hypothesis has been eliminated, the next move is to test an *assumption* with a
control, not to pick the least-eliminated hypothesis.  One step further down the
other path and three genuine fixes would have been reverted to chase a defect
that did not exist.
