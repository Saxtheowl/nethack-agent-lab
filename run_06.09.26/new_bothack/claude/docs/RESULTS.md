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
