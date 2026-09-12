# Results

All numbers below come from this repository's `artifacts/` directory and can
be regenerated with the scripts in `tools/`.  Every game was played by the bot
alone against the local NetHack 3.4.3-NAO build in `upstream/nh343`, with
BotHack's own `bothack.nethackrc`, **no wizard mode and no human input**.

## 1. Differential agreement with the original

`python3 tests/test_differential.py` — **1821/1821 cases identical** to the
original Clojure implementation, covering item parsing and identification,
monster data, status-line parsing, tile parsing, NetHack's FOV, navigation
(A*/Dijkstra with the original's cost function and tie-breaking), the
inventory/desire/pick-up strategy, the food logic, 51 full combat situations
(`fight` / `retreat` / `feed` / `progress` / the farlook chain all produce the
same action, on the same target), 60 Excalibur/fountain scenarios and 25
menu-answer orderings.  See `docs/TESTS.md` for the breakdown and for the bugs
it found.

## 2. Replaying a real game of the original into the port

Games of the original are recorded with `tools/pty_tap.py` and replayed into
both bots under identical conditions and with the same deterministic RNG.  Two
recordings were used; both are reported, because the difference between them
is itself the result.

| metric | recording A (4 min, 11 630 chunks) | recording B (10 min, 16 843 chunks) |
| --- | --- | --- |
| keystroke bytes, original | 24 086 | 26 001 |
| keystroke bytes, port | 24 491 | 52 778 |
| **identical leading keystrokes** | **11 326 (47.0 %)** | 287 (1.1 %) |
| keystroke-stream similarity (difflib) | **98.8 %** | 55.5 % |
| aligned action agreement | **97.8 %** (1615/1652) | 41.9 % (908/2166) |
| identical leading actions | 0 | 55 |

Evidence: `artifacts/replay_orig/compare8.txt` + `port_actions8.txt`
(recording A) and `artifacts/compare_final/report.txt` (recording B); both
were re-measured with the current port.

Three things have to be said about these numbers.

**The "identical leading actions" row is nearly worthless.**  The original's
first two actions are `Discoveries, Inventory` in one run and
`Inventory, Discoveries` in the next — the delegator keeps handlers in a
`clojure.data.priority-map` and breaks ties by the *identity* hash of `reify`
objects, so the original is not self-consistent here.  The port uses
registration order, which matched the capture behind recording B (55 actions,
up to the first random decision) and not the one behind recording A (0).  An
earlier capture of recording A did match, which is where this file's older
"983 identical actions" figure came from; it was luck of that JVM run, so it
has been dropped.

**Recording A is the deterministic core, and the port reproduces it.**  47 %
of the original's keystroke stream is reproduced byte for byte before the
first difference, the streams are 98.8 % similar overall, and 97.8 % of the
aligned actions agree.  The first difference is one extra `l`: the port takes
one step further east before a farlook, so its cursor then needs one `H` less.

**Recording B measures noise after its 20th action.**  There the bot walks
into a bear trap, which is its first *randomised* decision, and the two bots
disagree about which random draw to use (see the last bullet of "Known limits"
in `docs/TESTS.md`: they draw the same three values from the shared LCG but
perform a different one of the three).  Recording A contains no randomised
decision at all — `arbitrary direction` appears zero times in its 1652
actions.

After the first difference the comparison is meaningless in either recording:
in a replay neither bot's keystrokes affect the recorded game, so the loser of
the first difference is reacting to a game that answered someone else's keys.

The progression while the port was being debugged is the best summary of what
the differential tests were worth (measured on recording A against the capture
that shared the original's handler-tie order):

| after fixing | identical actions | keystroke similarity |
| --- | --- | --- |
| (first working port) | 0 | 44 % |
| `charged?` / `take-selector` | 0 | 63 % |
| Clojure's priority-map tie order in A* | 0 (tie in handler order) | 76 % |
| deferred `@game` deref in the delegator | 212 | 89 % |
| `want-to-eat?` argument order | 983 | 98.8 % |

The four bugs found after that table are not in it, and each needed a
different comparison to surface:

* `seek-fountain` (the bot never dipped for Excalibur) — found in §3, by the
  two bots' action-type distributions: `dip` was 0.08 % of the original's
  actions and 0.00 % of the port's;
* the monster map iteration order and the `nil`-glyph crash — found in §1,
  once `examine-monsters` and `(vals (:monsters level))` were added to the
  oracle;
* the menu answer order — found here in §2, as a divergence at keystroke
  byte 910 of recording A that moved between runs of the *same* port build.

Recording A's four minutes never reach a known Oracle level, never hold ten
monsters on a level and never meet a monster whose type has no glyph, so no
amount of replaying it would have found the first three.

## 2c. The same game, played live by both bots, byte for byte

`tools/live_compare.sh` (method in `docs/TESTS.md` §2b): both bots play the
*same* NetHack game — same pinned game seed, same binary, no wizard mode — and
their keystroke streams are compared byte for byte.

| game seed | original | port | identical prefix | identical game output |
| --- | --- | --- | --- | --- |
| 4242 (90 s, slow harness) | 4 197 | 5 886 | **all 4 197 bytes** | 182 KB |
| 4242 (900 s, slow harness) | 9 651 | 9 686 | **all 9 651 bytes** | 487 KB |
| 777 (420 s, slow harness) | 3 944 | 4 196 | **all 3 944 bytes** | 211 KB |
| 4242 (600 s, fast harness) | 42 961 | 68 069 | 28 371 bytes (66 %) | **1.36 MB** |
| 31337 (600 s, fast harness) | 69 302 | 57 389 | 37 810 bytes (66 %) | **1.66 MB** |

The port runs faster than the original, so in the same wall clock the two cover
different amounts of game; what the test asserts is agreement over every byte
the slower one produced.

The last two rows are the interesting ones.  With the idle-detecting tap (see
`docs/TESTS.md` §2b) the harness covers about ten times more game per second,
and at that depth both seeds do eventually diverge - after **1 969 identical
actions** on seed 31337 and a comparable run on 4242.  Neither divergence is
the same kind of thing:

* seed 31337, action 1969: the original inserts a `Look` on arriving at a tile
  where the port moves on and looks a step later - an `examine-tile` state
  difference;
* seed 4242, keystroke 28 371: in a fight next to an Elbereth engraving the
  original moves/attacks north-west and the port south-east.

Both are open.  What changed today is the depth at which they appear: seed
31337 used to diverge at keystroke **286**, and now runs identically for
**37 810** - a 132x improvement - after the monster-map ordering fix described
in `docs/TESTS.md` §1.

Three earlier "divergences" on these seeds were faults in the measurement, not
in the port, and each is worth recording because each looked convincing:

* a stray NetHack process left over from a killed JVM deleted the *running*
  game's level files (`Cannot open file "1000claudebot.0"`), ending a game
  mid-stream;
* frame boundaries depended on how fast each bot ran, so the two saw the same
  bytes cut in different places - fixed by closing an output group when the bot
  writes its next key;
* a travel command's output arrives in bursts with scheduler-dependent gaps, so
  a 30 ms settle window sliced one response into two frames at a point that
  moved with load.  Proof that this was the apparatus and not the port: the
  same port binary, at DEBUG logging speed, produced the original's keystroke
  where at INFO speed it produced a different one.  A 250 ms window removed the
  divergence with no change to either bot.

## 2d. Whole games under the deterministic protocol (2026-09-09)

This is the number that matters, and the one to read in preference to §2 and
§2c: those were measured against the reference *before* it was made
reproducible against itself (`docs/TESTS.md` §2c-bis), so they were measured
against a moving target.

Fifteen recordings of the original - two independent campaigns, one two-hour
capture, and two made at reduced piece delays - replayed with
`tools/replay_compare.py`:

| capture | recording | orig keystrokes | replay verdict | identical |
| --- | --- | --- | --- | --- |
| corpus_det 40001 | GAME (2 775 turns) | 25 672 | **PASS_COMPLETE** | 25 672 |
| corpus_det 40008 | GAME (2 325 turns) | 21 176 | **PASS_COMPLETE** | 21 176 |
| corpus_v2 40001 | GAME | 25 672 | **PASS_COMPLETE** | 25 672 |
| delay_probe 0.02 | GAME | 25 672 | **PASS_COMPLETE** | 25 672 |
| delay_probe 0.01 | GAME | 25 687 | **PASS_COMPLETE** | 25 687 |
| corpus_long 40002 | TRUNCATED (7 200 s cap) | 313 786 | PREFIX_ONLY | 313 786 |
| corpus_det 40004 | TRUNCATED | 98 962 | PREFIX_ONLY | 98 962 |
| corpus_det 40005 | TRUNCATED | 95 922 | PREFIX_ONLY | 95 922 |
| corpus_v2 40004 | TRUNCATED | 94 058 | PREFIX_ONLY | 94 058 |
| corpus_v2 40003 | TRUNCATED | 87 106 | PASS_CAPTURE | 87 106 |
| corpus_v2 40006 | TRUNCATED | 85 101 | PREFIX_ONLY | 85 101 |
| corpus_det 40002 | TRUNCATED | 84 892 | PREFIX_ONLY | 84 892 |
| corpus_v2 40005 | TRUNCATED | 82 753 | PREFIX_ONLY | 82 753 |
| corpus_v2 40002 | TRUNCATED | 78 763 | PREFIX_ONLY | 78 763 |

**1 182 022 keystroke bytes of the original, 1 182 022 identical - 100.00 %, no
divergence anywhere.**  Six of the fifteen recordings are complete games and
all six are PASS_COMPLETE, first keystroke to last; the other nine are captures
the wall clock cut short and each matches over its whole length, which is the
best verdict a prefix can receive.  Evidence: `artifacts/gate_v2/`.

> **Re-verification status (2026-09-11).**  The 1 182 022-byte figure was
> measured **before** the six fidelity fixes of 2026-09-10 (`unpause`,
> `kw`/nil-safe monster type, `_strip_modifier`, `castle_plan_b`, the invented
> `farm_done` threshold, and the 14 `type_map` sites).  Re-run against the
> current code: **13 of the 15 captures, 842 549 / 842 549 bytes, 100.00 %, 0
> divergences** (5 PASS_COMPLETE, 7 PREFIX_ONLY at their full recorded length,
> 1 PASS_CAPTURE).  The two not re-measured are the longest captures, which
> exceeded a 2400 s cap while another workspace's games shared the machine -
> a timeout, not a failure; `corpus_long_seed40002` returned PREFIX_ONLY
> 313 786/313 786 in the original campaign.  So: no fidelity regression from
> any of the six fixes, on every capture that produced a verdict.

Read it as "these fifteen recordings are reproduced", not "the port is
equivalent".  The five complete games are 2 300-2 800 turns each; none is an
ascension, and the longest capture (313 786 keystrokes, the bot still alive after
two hours) is a prefix precisely because the interesting late game lies beyond
it.

### What it took

The same fourteen captures scored 5 PASS + 1 PREFIX_ONLY + 8 DIVERGENCE before
the day's work, the earliest divergence at 6.4 % of its stream.  Nine fixes, each
found by measurement and each carrying a regression test or a reusable trace:

1. **`Throw` marks the tile unconditionally** - the original passes the game
   *atom* to `visible?`, so the guard is always true.  Reproduced as the upstream
   bug it is; closed the class "the original does a `Look` the port does not".
2. **`Discoveries` never forgets a name**, same atom-for-value shape.
3. **Clojure set iteration order for `Monster` records** - `hostile-threats`
   returns a PersistentHashSet and `find-first` over it picks the monster `fight`
   baits.  `hasheq` implemented and verified against a JVM dump.
4. **`map->Monster` materialises `awake` as nil** where the port's dict had no
   key: 11 map entries instead of 12, a different hash, a different place in the
   set.
5. **The scraper chose one redraw too early** - an `(if …)` that is a clause of
   an enclosing `or` returns a truthy Position, so the original waits for another
   frame.  Invisible until a hallucination episode re-randomises every glyph per
   redraw.
6. **A one-character Clojure String is not a Character** and hashes differently,
   so `put-in-what`'s menu answer reached NetHack in the wrong order.
7. **`should-try?` applies its predicates to the item-*id* record**, not the
   item, so a wand whose appearance was engrave-tested still counts as untried.
   The port dropped the glass wand the original kept and then livelocked.  Found
   only by the two-hour capture, 110 316 bytes in - past the end of every other
   recording.
8. **`FarLook`'s altar clause, the menu options map, `at`'s bounds assertion and
   `:pre` failures escaping the delegator** - four fixes found by structural
   audits rather than by a divergence, each neutral on all fourteen captures and
   fixed because the next capture might not be.

## 2e. Real games: playing to the end (2026-09-10)

The replay gate answers "does the port send the same keystrokes".  It cannot
answer the question the mission actually asks - **does the port play the game?**
Those are different properties, and playing found six defects that fifteen
byte-identical captures could not, because each is a property of the live
dialogue with NetHack rather than of keystroke agreement:

| # | defect | how it showed |
| --- | --- | --- |
| 1 | scraper deadlock on `In what direction do you want to dig?` | game froze at Dlvl 9 |
| 2 | `quit-when-idle` not ported - the only recovery below the action layer | 1 game in 5 sat until the reader gave up |
| 3 | a reader idle timeout the original does not have | killed 7 of 16 games *while the bot was thinking* |
| 4 | `lastmsg-get` recording a cursor that was still on the topline | permanent deadlock |
| 5 | `lastmsg+action` waiting unbounded on a poisoned position | permanent deadlock, always the deepest games |
| 6 | `quit-when-stuck` raising instead of exiting | ended the best game on an exception |

`tools/ascend_batch.sh` plays N games in waves; `tools/ascend_pool.sh` keeps
every slot busy, which matters because a farming game runs for hours and a wave
would leave the other slots idle for all of it.  Outcomes come from NetHack's own
xlogfile.

### What the bot achieves

Two records exist and they are not the same population, so both are given with
their source.  NetHack writes an xlogfile line only when the *game* ends; when
the bot abandons a game instead, NetHack records nothing and only the bot's log
attests to it.  Quoting one number from each without saying so - which an
earlier draft of this file did - overstates the result.

| | from NetHack's xlogfile | from the bot's own log |
| --- | --- | --- |
| games covered | 161 (games that ended *in NetHack*) | 139 (every game launched) |
| deepest level | Dlvl 21 | **Dlvl 39** (`pool_f/game2`, in Gehennom) |
| highest score | 120 050 | **15 669 164** |
| longest game | 17 478 turns | 121 580 turns |
| ascensions | **0** | **0** |

Counts refreshed 2026-09-11 with the neighbouring workspace's games excluded
(see the correction below).  The **maxima did not move**: no foreign game had set
any record, so only the totals and the longest-game figure were stale.  The
bot-log column's depth is now 39 rather than 28 because `pool_f/game2` went
past the Castle.

The right reading: Dlvl 28 and the seven-figure scores are real and are attested
by NetHack's own status line, which the scraper reads - but they belong to games
that ended *without* a NetHack record, because the bot stopped rather than died.
The xlogfile column is the stricter one, and it is the one to quote against
another bot.

The seven-figure scores are **sink farming**, an upstream strategy: `farm-sink`,
`FarmAttack` and `farm-done?` in `bots/mainbot.clj`.  `farm-done?` releases the
bot to descend at 15M points, or at 6M once it also holds a bag, six scrolls of
remove curse, identify, reflection and AC below -10.  The port reproduces this:
one game reached 9.9M and was observed pulling remove-curse scrolls out of its
bag and reading identify - assembling exactly `farm-done?`'s checklist.  So the
port reaches the phase the original credits for its own first win.

### Three defects found by playing, not by replaying

All three were invisible to a replay gate sitting at 100%, because the games the
original recorded never reach the states that trigger them.  Listed by what they
cost:

| # | defect | how it showed | cost |
| --- | --- | --- | --- |
| 1 | `quit-when-idle` called the private REPL helper's logic instead of `unpause`, so the four ESCs that cancel NetHack's pending prompt were never sent | games hung, then quit themselves 50 s later | **17 games**, deepest Dlvl 18 |
| 2 | `montype['name']` where the original writes `(:name montype)` - nil-safe on a String, which `montype` genuinely is | `TypeError`, caught by the delegator, farlook silently discarded | **3002 occurrences** |
| 3 | `_strip_modifier` carried a `"saddled invisible "` clause `condp` does not have | a saddled invisible pony became `"pony"` instead of `"invisible pony"` | wrong monster identity |

Defect 2 deserves its own note, because the surprise is upstream.  BotHack's
`rank->monster` is `(comp by-rank-map string/lower-case)` and `by-rank-map` maps
a player rank to a **role name String**, not a MonsterType.  So farlooking
`a human or elf (vagrant)` makes `by-description` return `"caveman"`, the
original stores that String as the monster's `:type`, and every later
`(:tags (:type m))` quietly yields nil.  The port has to reproduce that, not
correct it.

Fixing 2 also **unmasked fourteen latent crashes**: `(m.get('type') or {})` is
unsafe the same way, since a String is truthy and `.get` then raises.  They had
never fired only because the TypeError aborted before the String was ever
stored.  That was checked against the logs - no `AttributeError` appears in any
of them - rather than assumed, and all fourteen now go through a nil-safe
`monster.type_map`.

Regression coverage was taken from the JVM, not from my reading of it: a new
`monster-preds-desc` oracle case builds the monster through `by-description`
instead of `name->monster`, which is the path the existing 1821 cases could
never reach.  The port matches Clojure on all of it, including the vacuous
`demon-lord: true` and `passive: true` that a String type produces.  The suite
is now **1829/1829**.

### Both bots, played at volume, in the same environment

`tools/compare_realgames.py`, reading NetHack's own xlogfile - written by the
game, not by either bot or by this harness:

| | original | port |
| --- | --- | --- |
| games recorded | 12 | 161 |
| ascensions | **0** | **0** |
| median Dlvl | 8 | 6 |
| p90 Dlvl | 14 | 9 |
| max Dlvl | 19 | **21** |
| median score | 11 772 | 4 212 |
| median turns | 5 393 | 3 408 |

**Corrected on 2026-09-11.**  An earlier version of this table read 11 vs 156
games with identical medians of 6, and concluded "the port is not
underperforming the original".  Two things were wrong with it.

NetHack writes its xlogfile to a path fixed at compile time, and a neighbouring
workspace on this machine shares that destination for some runs.  **19 of the
lines were not ours**, and since `compare_realgames.py` counted anything without
an `orig` prefix as the port, they were being reported as the port's.  The tool
now excludes them by player-name prefix and prints how many it dropped.

With that fixed the medians are 8 against 6, not 6 against 6 - so the earlier
conclusion was not supported.  Nor is its opposite: n=12 is far too small (the
tool warns below twenty), and one extra original game moved the median from 6 to
8, which is itself the measure of how unstable the figure is.  The populations
are also not comparable: the port's 161 games span its whole history, including
the 17 lost to the `unpause` defect - disproportionately the *deep* ones - games
killed by pool restarts, and everything before the five fidelity fixes.  The
port is measured with its bugs in; the original is not.

The honest statement is that **this comparison is not yet conclusive in either
direction**.

### What an ascension actually costs, in the author's own words

Worth stating plainly, because it sets the expectation for "run until it
ascends".  From BotHack's README:

* *27.12.2014* - "can reach the castle fairly regularly ... eventually dying to
  Orcus-spawned Demogorgon";
* *25.1.2015* - pudding farming landed and the bot "has **finally** managed to
  win the game" - one win, after months;
* *22.6.2015* - the two tournament ascensions were by "**slightly modified**
  versions" of the bot.

And `doc/issues.md` lists a long tail of *terminal* states in the ascension run:
reaching the castle without a wand of striking, failing to uncurse the
invocation artifacts, missing a ring of levitation for Rodney's tower, farming
broken by a trapdoor or a djinni at the sink.  Each ends a run that has already
cost hours.

So an ascension is a rare event **for the original too**, and neither bot here
has produced one in 167 games.  Nothing in the data so far distinguishes the
port from the original on that axis; what distinguishes them is that only one of
them has 156 games behind it.

One line in that file is direct corroboration of today's `unpause` fix: *"very
rarely the scraper gets stuck in unusual situations (eg. many potions breaking
during farming). ... the auto-unstuck mechanism after 3 idle minutes usually
fixes the situation however."*  That auto-unstuck is exactly `quit-when-idle`
calling `unpause`, and "usually fixes the situation" is the behaviour the port
was missing.

### The unstick fix, measured in real play

Two unsticks fired in the first pool run after the fix.  They disagree, and the
disagreement is the useful part:

| game | outcome | evidence |
| --- | --- | --- |
| `pool_f/game2` | **recovered** | unstick at 17:34:50, `unpaused`, then **11 375 further actions** and no idle-quit |
| `pool_f/game1` | not recovered | same hallucination trigger, unstick fired, 0 actions after, quit 50 s later |

Under the old code `game2` was a lost game, so the fix does what it was meant to
do.  One in two is also exactly the author's own claim for this mechanism -
*"the auto-unstuck mechanism after 3 idle minutes **usually** fixes the
situation"* (`doc/issues.md`).

`game1`'s trigger is worth recording because it is precise: the bot sent `;`
(farlook), NetHack answered **"Pick an object."**, and *while that prompt was
open* a gas spore exploded - "You feel an unseen monster!  It explodes!  You are
caught in a blast of kaleidoscopic light!" - leaving it hallucinating mid-prompt.
That is the same class the author lists as the framework's own residual bug:
*"very rarely the scraper gets stuck in unusual situations (eg. many potions
breaking during farming)"*.

**Why it did not recover is unresolved.**  The ttyrec shows NetHack answering
the unstick's `#` and sending a full redraw within milliseconds, so the game was
recoverable at the NetHack end and the four ESCs did cancel the prompt.  What
the bot did with that redraw is not known: the watchdog's scraper dump fires on
its own 120 s clock and landed in the *same second* as the unstick, so it covers
none of the 50 s grace window.  An earlier draft of this section read that dump
as proof the scraper processed nothing - it is not evidence either way.

`_quit_when_idle` now dumps the scraper trace itself at the end of the grace
window, immediately before giving up, so the next occurrence is diagnosable
rather than inferred.

### Did the fix move the abandonment rate?  Not demonstrably, yet.

`tools/ending_mix.py`, split at the fix:

| | before (pools a/b/c + ascend_run*) | after (pools e/f) |
| --- | --- | --- |
| games finished | 67 | 17 |
| ended in NetHack | 66% | 82% |
| **abandoned by the bot** | **34%** (23) | **18%** (3) |

The direction is right and it agrees with the mechanism evidence above.  It is
also **not statistically significant**: Fisher's exact test on 23/67 against
3/17 gives **p = 0.246**.  At a true rate of 18% it would take roughly **80**
post-fix games to reach p < 0.05, against 17 so far.

Stating it plainly because it would be easy to quote the 34% -> 18% and stop:
that pair of percentages, on its own, is consistent with chance.  The evidence
that the fix works is not the rate - it is `pool_f/game2`, where an unstick was
followed by 11 375 further actions in a game the old code would have quit.  A
mechanism observed once beats a proportion measured on seventeen samples, and
the rate will become quotable only after the games accumulate.

### Gehennom reached (2026-09-10, `pool_f/game2`)

The deepest run of the campaign by a wide margin, and the first to leave the
Dungeons of Doom.  Every step below is attested by a `Topline message:` line or
a `dlvl changed` transition - the two log sources that are actually reliable
here, as opposed to keyword counts over a file that embeds game-state dicts.

| step | evidence |
| --- | --- |
| descended to Dlvl 30 (Castle) | `dlvl changed` chain |
| got the Castle wand of wishing | `D - a wand of wishing (0:2)` |
| recharged it twice, spent 16 wishes | "Your wand of wishing glows blue"; "You may wish for an object." x16 |
| **survived a scraper deadlock** | unstick at 17:34:50, then **11 375 further actions** |
| climbed 26 -> 14, swept the Quest end level (49 min) | `explore-level :quest :end` |
| returned 14 -> 30 in six minutes | `dlvl changed` chain |
| **fell through the Castle trapdoor** | "You float gently to the floor.  A trap door opens up under you!" |
| **entered Gehennom** | "You arrive at the Valley of the Dead..." then "You are standing at the gate to Gehennom." |

Two things this settles.

**The port executes the Castle -> Gehennom transition.**  That is the stretch of
code no test covers - no recording in the corpus goes near it - and it is where
the `castle-plan-b` defect was found the same evening.

**The levitation "oscillation" was the solution, not a failure.**  It was
reported here as a probable wall: the bot alternating `puton 'need levi for next
move'` with `remove "don't want levi"` for twenty minutes, with no watchdog able
to see it.  That reading was wrong.  Crossing the Castle *requires* levitation
to move and *forbids* it at the instant the trapdoor opens, so the alternation
is the manoeuvre.  The bot completed it: "A trap door opens up under you!  You
don't fall in" (levitating) became "You float gently to the floor" (levitation
ended) and the fall followed in the same second.

The error was structural, not incidental: a twenty-minute observation window was
read as a permanent state.  The same mistake produced the "8 h with no unstick"
claim from a watcher whose pool had died after 1 h 02, and the "reached the
Castle" claim from 602 grep hits that were tile dumps.  Short windows and
keyword counts have both now failed here; toplines and level transitions have
not.

Without the `unpause` fix made that morning, this game would have ended at
17:34:50 like the seventeen before it.

### How `pool_f/game2` ended, and what it identified

Lost at **01:52 on 2026-09-11, Dlvl 40, turn 57 631, score 7 925 266, HP
230/230, AC -30** - to `3+ min idle - quitting`, after nine hours and twenty
minutes.  It did not die: it was abandoned while in perfect health.

The ttyrec names the state, and it is more specific than the previous one.  The
last frame before the 240 s silence ends with `\x1b[H# \x1b[K` - NetHack had
**`# ` on the topline**, sitting at the extended-command prompt.  The scraper's
last recorded state was `lastmsg_get`, whose guard is

```clojure
(when (and (= "# #" (topline frame)) (< (-> frame :cursor :y) 22)) ...)
```

exactly **two** `#`.  With one, the guard fails, the state returns nil, and it
waits for a redraw that says something it will never say.

The escape for that exact frame exists - in `marked`:

```clojure
(when (and (zero? (-> frame :cursor :y)) (before-cursor? frame "# '"))
  (send delegator write (str esc esc))
  initial)
```

and the port carries it verbatim.  But it is reachable only from `marked`, not
from `lastmsg_get`, **in both implementations**.  So the deadlock is upstream,
and it matches the author's own note: *"very rarely the scraper gets stuck in
unusual situations ... the auto-unstuck mechanism after 3 idle minutes usually
fixes the situation however."*

Here it did not, and **why is still unknown**.  The unstick wrote `#`, called
`unpause` (scraper to nil, inhibition cleared, ESC x4), NetHack answered and
redrew - and the bot still chose no action in the 50 s that followed.

The instrumentation added the previous evening to dump the scraper trace at the
end of the grace window **produced nothing here, and the reason is my own
oversight**: the process had been running since 16:30 and the edit landed around
midnight, so Python was executing the old module.  Editing a source file does
not reach a running interpreter.  It is armed for every game started since.

What this run did establish, before it was lost: the port reaches Gehennom,
fights its demon lords (Juiblex, put to flight at 23:06), and pursues Vlad's
Tower level by level for the Bell of Opening - `trying to enter vlad from
Dlvl:34/38/39/40`.  The ascension path works; this deadlock is what ends it.

### The endgame path, audited by reading

No test exercises the endgame: the differential suite covers item and monster
predicates, and no recording in the corpus gets near the Castle.  With a live
game approaching it, the ten endgame functions were compared against the Clojure
by hand.

**One real defect, in `castle-plan-b`.**  The original's guard is

```clojure
(or (not (have-levi game))
    (not-any? (:genocided game) #{";" "electric eel"})
    (not (reflection? game)))
```

The port carried a **fourth** clause, `";" not in genocided`, with no counterpart
upstream - a leftover from a first attempt at `not-any?`, and implied by the real
one.  Inside an `or` a surplus clause can only make the guard fire more often, so
the port engaged plan B when `;` was ungenocided but the eel was genocided, where
the original declines.  Fixed; suite still 1829/1829.

**`offer-amulet` is faithful**, which matters because it is the last step of an
ascension.  Checked case by case, including the `if-let` subtlety: upstream the
"same alignment -> Offer" test is the *else* branch of the helm-of-opposite-
alignment `if-let`, and the port reproduces all three outcomes.  `(some-> (have
game real-amulet?) key ->Offer)` maps to `Offer(found[0])`.

A note on method, because the first attempt was wasted.  Counting `or`/`and`
tokens on both sides to spot arity mismatches flagged 8 of 10 functions and was
pure noise: `(and a b c)` is one form in Clojure and two `and` tokens in Python,
so the counts are not comparable.  The real defect was found by reading, and the
counter would not have distinguished it from the noise.

### How games end - the actual blocker

`tools/ending_mix.py` classifies every game from the bot's own log, which is the
half `tools/compare_realgames.py` cannot see:

| ending | games | share |
| --- | --- | --- |
| death in NetHack | 52 | 48.6% |
| bot quit: idle | 16 | 15.0% |
| bot quit: stuck | 4 | 3.7% |
| bot quit: no action chosen | 3 | 2.8% |
| crash | 1 | 0.9% |
| interrupted or still running | 31 | 29.0% |

**Of the 76 games that actually finished, 32% ended because the bot gave up, not
because it died.**

(An earlier count put this at 35% by treating `unknown itemtype for item` as a
crash.  It is not one: it is a faithful port of the original's own `log/error`
at `itemid.clj:188`, which returns nil and lets play continue.  The port differs
from it only in log shape - the original passes an `IllegalArgumentException`
as the throwable argument and the appearance as the message - which changes no
decision.)  That, and not the death rate, is what stands between this and
an ascension - a game abandoned at Dlvl 17 was not lost to NetHack.

### The idle-quits were one port defect, and it is fixed

They looked at first like *decision* loops, because the last few actions before
each quit repeat an action name.  Timestamping them says otherwise: in **all 17**
the bot issues an action and then nothing is logged for 138-259 s, so these are
I/O deadlocks, not loops.  (The repeated names are just a bot walking - 119
distinct tiles in 138 `exploring` actions in one case.)

One game had a ttyrec, and it settles the mechanism:

* the bot dropped a lembas wafer on Odin's altar; it exploded - *"You are caught
  in a blast of kaleidoscopic light!"* - and it was **hallucinating**;
* under hallucination it read a glyph as a monster (`'type': None`) and attacked
  it; the glyph was the temple priest.  *"Odin roars in anger"*, a bolt of
  lightning, *"You are blinded by the flash!"*;
* then silence.  NetHack was **not** dead: when the handler later wrote `#`, it
  echoed it within milliseconds.  It was simply waiting for input;
* the watchdog's scraper trace names the state: `lastmsg_action`, topline
  `'# #'`.  The scraper was inside BotHack's ctrl-P last-message protocol,
  waiting for a redraw; NetHack was waiting for a keystroke.  Deadlock.

The recovery that exists for exactly this is `quit-when-idle`, and the port had
it wrong.  The original (`main.clj:98`) does:

```clojure
(w "#") (unpause a) (Thread/sleep 50000) (when-not @chosen ... (q))
```

`(unpause a)` is `bothack.bothack/unpause`: reset the scraper, clear inhibition,
**write ESC ESC ESC ESC** - called unconditionally.  The port had confused it
with the private REPL helper `u` (no argument, adds a ctrl-R, conditional on
inhibition), so it sent a ctrl-R and, whenever the bot was not inhibited - the
ordinary case - **never sent the ESCs**.  The ESCs are the whole recovery: they
cancel the prompt NetHack is holding.  Without them the unstick wrote `#`, got
its echo, and changed nothing; 50 s later the handler gave up.

Fixed in `pybothack/main.py`; `tests/test_idle_recovery.py` now asserts the four
ESCs, the unconditional unpause and the scraper reset, and asserts that no
ctrl-R is sent.  That test previously asserted the *opposite* on both counts -
it had been written from the port instead of from the Clojure, so it passed
while seventeen games were lost.

Depths lost to it: 1, 3, 4, 4, 4, 5, 5, 5, 5, 8, 9, 10, 11, 17, 17, 18.

The comparison against the original at equal volume is still worth having and is
still the plan (`tools/ascend_pool_orig.sh`, `tools/compare_realgames.py`) - but
this particular question no longer needs it, because the Clojure answered it
directly.

## 3. Real games

`tools/batch_py.sh` / `tools/batch_orig.sh`, 6 games each, 600 s of wall clock
per game, summarised by `tools/summarize_games.py --markdown` from each bot's
own log.  A game that hit the time limit is counted as it stood.  The two
batches ran **one after the other on an otherwise idle machine** (original
09:03-10:03, port 12:30-13:07), against the same build and the same
`bothack.nethackrc`, so neither paid for the other's CPU.  The port here is the
version with every fix in §1.

**python port** (6 games)

| game | max dlvl | turns | score | actions | died |
| --- | --- | --- | --- | --- | --- |
| game1 | 5 | 2682 | 2492 | 1749 | yes |
| game2 | 6 | 4368 | 7099 | 3050 | yes |
| game3 | 8 | 3923 | 6992 | 2722 | yes |
| game4 | 7 | 8418 | 22509 | 5493 | no |
| game5 | 6 | 3927 | 6444 | 2589 | no |
| game6 | 5 | 7516 | 14726 | 6760 | no |
| **median** | **6** | **4147.5** | **7045.5** | **2886** | 3/6 |

**original BotHack** (6 games)

| game | max dlvl | turns | score | actions | died |
| --- | --- | --- | --- | --- | --- |
| game1 | 8 | 5334 | 11400 | 2969 | no |
| game2 | 6 | 5393 | 11811 | 3209 | yes |
| game3 | 7 | 6091 | 13263 | 4774 | no |
| game4 | 4 | 3291 | 2312 | 1463 | yes |
| game5 | 8 | 6410 | 16078 | 4107 | no |
| game6 | 6 | 6380 | 10749 | 4275 | no |
| **median** | **6.5** | **5742** | **11605.5** | **3658** | 2/6 |

The five games that really ended are confirmed independently by NetHack's own
`xlogfile` (`upstream/nh343/var/xlogfile`), which the bots cannot write:

| bot | turns | points | maxlvl | death |
| --- | --- | --- | --- | --- |
| port | 2682 | 2488 | 5 | killed by a dwarf |
| port | 4377 | 7043 | 6 | killed by a Green-elf, while sleeping |
| port | 3923 | 6936 | 8 | killed by a large dog |
| original | 5393 | 11 811 | 6 | killed by a soldier ant |
| original | 3291 | 2253 | 4 | killed by a dwarf |

**Reading this table.**  The port is **behind the original**, and this is the
honest summary of the whole deliverable: same order of magnitude, not parity.
Median max depth 6 against 6.5; median score 7046 against 11 606 — about 60 %;
3 deaths in 6 games against 2.  Its best game (Dlvl 7, 22 509 points, alive at
the time limit) is the best of either side, and its worst is worse.  Six games
per side is a small sample and the medians are close enough that the ordering
of two individual games could flip them, but nothing here supports a claim of
equivalence in play strength.

Throughput is not the explanation: alone on the machine the port took
7.4-12.4 actions/s against the original's 5.0-8.1 (the original must run with
DEBUG logging on — see `docs/LIMITATIONS.md` — and writes 12-58 MB of log per
game).  The two bots spend their actions on nearly the same things:

| action | port | original |
| --- | --- | --- |
| move | 57.3 % | 53.6 % |
| farlook | 6.9 % | 10.3 % |
| repeated (multi-turn search/rest) | 5.6 % | 7.3 % |
| autotravel | 4.7 % | 4.2 % |
| inventory | 3.9 % | 3.5 % |
| everything else | within 0.5 points of each other | |

Overlap of the two distributions: **93.7 %**, against **86.9 %** for the
pre-fix batches in `artifacts/games/py_prefix_fix` vs `orig_run1`, where the
port spent 74.6 % of its actions moving (61.8 % for the original) and never
dipped for Excalibur at all.

The `farlook` row is the only one still more than a point apart, and it turns
out not to be a difference in the port.  Per game, the original's farlook rate
ranges from 7.6 to 185.4 per 1000 turns and the port's from 27.8 to 62.0; by
*median* the port farlooks slightly **more** (47.1 vs 32.8 per 1000 turns).
The pooled figure is dominated by one game: the original's game 3 contains a
run of **948 consecutive farlooks** of the same tile — an ambiguous square
with a dust engraving that its `examine-tile` chain never resolved.  No other
game on either side has a run longer than 9.  Discounting runs of more than 20
consecutive farlooks, the shares are port 6.9 % against the original's 6.1 %,
and the distribution overlap rises to **96.1 %**.

That livelock is the original's, not a behaviour the port fails to copy, and
it is a fair reminder of what the score table is measuring: 40 seconds of one
of the original's six games were spent looking at a single square.

Scanning all twelve games for the longest run of any one repeated action type
finds nothing pathological on the port's side: its longest runs are 32-62
consecutive `move`s, plus one run of 206 in game 6 which the log shows is the
bot chasing a monster that stole its daggers and then fidgeting past a
peaceful blocker — both behaviours the original has too.  The original's
longest runs are 24-56 `move`s, and the 948 farlooks.

Both bots also throw the occasional exception and recover: 2 in the original's
six games, 4 in the port's, and one of the port's is the *original's own*
deliberate `"Unexpected direction prompt"` throw, reproduced faithfully.

Best single game of the port (`artifacts/games/py/game4`): Dlvl 7, 22 509
points, 8418 turns, still alive when the 600 s ran out — the highest-scoring
game of either bot in these batches.  Its best *finished* game is
`artifacts/games/py/game3`, from NetHack's own xlogfile:

```
points=6936 deathlev=8 maxlvl=8 turns=3923 role=Val race=Dwa
death=killed by a large dog
```

## 4. Ascension

**No ascension.**  In the 12 games above (6 per bot, 600 s each) neither bot
got past Dlvl 8, let alone ascended, and the port has never ascended in any
run in `artifacts/`.  The original's own ascension was a rare event: krajj7
reported it after months of tuning, and the ascending game itself took hours
of real time.  What this repository shows is agreement with the original's
decisions, not a reproduction of its ascension.
