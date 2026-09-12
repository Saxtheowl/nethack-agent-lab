# What is not done, and what is known to differ

This is the honest list.  Nothing here is hidden in a footnote elsewhere.

## Not implemented / not ported

* **The Java/JVM bot API** (`java/bothack/**`, `javabots/**`).  It exists in
  the original only so that bots written in JVM languages can drive the
  framework; the port has no equivalent and none of it is used by the bot.
* **`bots/wizbot.clj`** (the wizard-mode test bot) and **`bots/simplebot.clj`**.
  Only `bots/mainbot` — the bot that ascended — is ported.
* **The dgamelaunch menu bot** (`bots/dgl_menu.clj`).  The port only plays
  against a local NetHack (`:interface :shell`) or a plain telnet server; it
  cannot log into a public server's menu on its own.  `pybothack/iface.py`
  has the telnet client, but no menu bot drives it.
* Everything the original itself leaves unimplemented is still unimplemented
  (zapping spells, multidrop, quest maps for roles other than valkyrie and
  samurai, …) — see `doc/issues.md` in the original.

## Deliberate deviations from the original

Everything else in the port reproduces BotHack's behaviour, including its bugs.
These two do not, and each is here because the original's behaviour makes a live
game unrecoverable rather than because it was inconvenient to port.  Both are in
the scraper's synchronisation path, both were found by *playing* rather than by
replaying, and neither fires on any recorded game of the original - the replay
gate stays at **1 182 022/1 182 022 identical keystrokes over fifteen
recordings** with them in place, which is the evidence that they only remove
pathological states.

| deviation | the original | the port | why |
| --- | --- | --- | --- |
| `lastmsg-get` cursor guard | records the cursor when `y < 22`, which admits the topline | requires `0 < y < 22` | a cursor on the topline cannot be the hero's position; recording it makes `lastmsg+action` wait for a position no later frame can have |
| `lastmsg+action` wait bound | waits for a matching frame with no bound | gives up after `LASTMSG_WAIT_LIMIT` (40) redraws and proceeds | the `"# #"` clause re-records the position to *correct* it, and a stale frame corrupts it instead; unbounded then means permanent |

There was a third entry here - "`quit-when-idle` also resets the scraper" - and
it was **not a deviation at all, it was a port defect wearing a deviation's
label**.  The original's `quit-when-idle` (`main.clj:98`) calls `(unpause a)`
unconditionally, and `bothack.bothack/unpause` resets the scraper, clears
inhibition *and writes ESC ESC ESC ESC*.  The port had conflated that with the
private REPL helper defined a few lines above `-main`:

```clojure
(defn- u "unpause" [] (r) (if (:inhibited @(:delegator a)) (unpause a)))
```

which takes no argument, adds a ctrl-R, and is never called from the handler.
`(unpause a)` takes one, so it can only be the real function.  Because of the
mix-up the port added a ctrl-R and made the unpause conditional on inhibition,
so in the ordinary un-inhibited case **the four ESCs were never sent** - and
those ESCs are the entire recovery, since they cancel whatever prompt NetHack is
holding.  Cost: seventeen real games, the deepest at Dlvl 18.  See
`docs/RESULTS.md` for how it was found.

The lesson worth keeping: the port reset the scraper and *called that a
deliberate improvement*, when the original was already doing it - and doing more
besides.  A deviation claimed without re-reading the Clojure it deviates from is
just an unexamined bug.

## Undocumented divergences found on 2026-09-10, and one still open

### Fixed: a third `farm-done?` threshold the original does not have

`farm_done` carried an invented arm:

```python
if score > 10_000_000 and turn > 75_000:
    return True
```

The original has exactly three: wiztower branch known, `score > 15M`, or
`score > 6M` with the full consumable checklist.  The comment that came with it
argued in strategic terms - a farm that has already paid for itself should not
sit on its sink waiting for a missing consumable.  That may even be good play.
It is still a **gameplay decision**, and inheriting those rather than improving
on them is the whole point of this port.  It is not the same class as the two
scraper deviations above, which break deadlocks in which the game cannot
proceed at all.

It was not hypothetical: `game9` ended at **14 770 000 points on turn 74 993**,
seven turns and 230 000 points short of the invented threshold.  The JVM was
asked directly and answers `farm-done: false` for that exact state, and for
`score 12M / turn 80000`.  The port now agrees.

Removed, and covered: `tools/cljcmp/oracle.clj` gained a `farm-done` case that
builds a whole game state (score, turn, wishes, AC, genocided set, branches,
inventory) and ten states exercise it, two of them aimed at the invented
threshold's zone.  Suite is **1839/1839**.

Why it survived so long is the part worth keeping: the differential suite's
1829 earlier cases are all item and monster *predicates*.  No strategic decision
function was covered by anything, and `farm-done?` is among the most
consequential the bot makes.

### Open: defensive guards where the original throws

A sweep of every numeric literal in `mainbot` found no other invented threshold.
It did surface a different class, in `desired-food` / `nw-ratio-avg`:

| situation | original | port |
| --- | --- | --- |
| no food carried | nil | `None` - matches |
| food carried, total weight 0 | `(/ n 0)` **throws** | returns `None` |
| an unidentified food with no weight | `(+ nil res)` **NPEs** | reads `or 0` |
| `min-nw` nil reaching the comparison | `(> x nil)` **throws** | falls back to `24` |

The port is systematically more defensive here.  Reproducing the original means
reintroducing exceptions - which the delegator catches, aborting the handler,
exactly as it does for the `unknown itemtype` error already reproduced
elsewhere.  **This has not been done**, and the reason is scheduling rather than
judgement: it was found with a nine-hour game in Gehennom and live pools on the
machine, and destabilising those for a divergence that only affects food
selection is a bad trade tonight.  It is recorded here rather than quietly left
out, and no claim is made that the guards elsewhere in the port have been
audited for the same pattern - they have not.

## Differences that are known and measured

* **Handler priority ties.**  `clojure.data.priority-map` iterates
  equal-priority handlers in the hash order of the handler objects, which are
  `reify` instances with identity hashes; the original therefore picks a
  different order from run to run (observed).  The port uses registration
  order.  This is the reason the two bots' very first two actions can be
  swapped.
* **Randomness.**  The bot uses `rand-int`/`rand-nth` in combat and
  exploration decisions.  For comparisons both sides use the same LCG; in
  normal play the port uses Python's RNG, so runs are not comparable
  action-by-action to a Clojure run.
* **Superseded, kept for the measurement record: the "different direction after
  a Pay" class (3 of 9 games).**  Measured against the *non-deterministic*
  reference, before the pinning protocol of `docs/TESTS.md` §2b made the
  original reproducible against itself.  Those numbers were taken against a
  moving target and none of them should be quoted as current.  The performed action differs by exactly one reason: the port's
  carries `arbitrary direction` (i.e. it came from `arbitrary-move`), the
  original's does not, though both chains start with `fidgeting to make
  peacefuls move` / `peaceful blocker`.  Ruled out by measurement, in order:
  the RNG (538 draws compared - identical values *and* identical kinds, 13
  `rand-nth` / 193 `rand-int 10` / 187 `rand-int 200` on each side);
  `arbitrary-move` itself (same position, same 8 neighbours in the same order,
  both return `E` for the deciding draw 7092); and the `:blocked` counter (nil
  on both sides, because the blocker is a shopkeeper in a shop and both
  implementations skip the increment there).  Tracing every `fidget` return of
  the original shows **777/777** of its fidget-produced moves carry
  `arbitrary direction`, so the performed action did not come from `fidget` -
  it inherited the fidget reasons through the exploration-step cache
  (`using cached exploration step` is in both chains).  That cache is the
  current lead: the original fills it with a **future** evaluated on another
  thread and cancels it at `action-chosen`, while the port computes the same
  value eagerly and synchronously (`docs/PORT.md`).  Both capture the same
  pre-action state, so the difference is not obviously in the value - but
  `curlvl-exploration` draws from the RNG through `fidget`, and that happens
  off-thread in the original.
* **The blocking class of 2026-09-08: closed.**  It was `Throw`'s
  `(not (visible? game level to-update))` at `actions.clj:1463`, and the earlier
  entry in this table calling that branch "ruled out" was **wrong**: it compared
  the `visible?` of the *game value*, which is indeed true on (5,18), while the
  original passes the game **atom**.  `visible?` then destructures
  `{:keys [player]}` out of an atom (nil) and asks `(get-in atom [:fov ...])`,
  which Clojure answers with nil for a non-collection, so the guard is *always*
  true and `Throw` marks the tile unconditionally.  The port derefed and
  computed a real `visible?`, so it never marked the tile, never came back for
  the item, and stopped doing the `Look` the original does.  Reproduced as the
  upstream bug it is (`pybothack/actions.py`, `Throw`).

  How it was found, after sixteen candidates had been eliminated by
  measurement: an env-gated hook on `bothack.dungeon/update-at`
  (`BOTHACK_NEWITEMS_TRACE` in `tools/cljcmp/dbg_inv.clj`) logging every
  transition of `:new-items` on one tile **with the calling stack**.  Two lines
  of output named the writer.  The lesson: trace the *writer of the state*, not
  its readers - all sixteen eliminations were readers.

* **A second upstream atom-for-value bug, also reproduced.**
  `Discoveries`' about-to-choose does
  `(swap! game forget-names (difference (:used-names game) @known-names))`
  with `game` the atom, so `(:used-names game)` is nil, `difference` returns
  nil, and `forget-names` returns its game unchanged: the handler never forgets
  a name.  The port used to deref and actually forget them; now it reproduces
  the no-op.

  `tools/audit_atom_args.py` scans the original for this whole class (a bare
  `game` reaching a function that wants the map, inside a scope where `game` is
  the atom).  It reports 29 sites; triaging them by hand leaves exactly these
  two, the other 27 being inner `(fn [game] ...)` rebindings, `:as game`
  destructurings of a value, or functions that legitimately take the atom
  (`handle-door-message`, `swap!`).

* **Clojure set iteration order for records: implemented and verified.**
  `hostile-threats` ends in `set`, so the bot holds its monsters in a
  PersistentHashSet, and `find-first` over it walks the HAMT order of the
  elements' `hasheq`.  Getting that wrong changes which monster `fight` baits:
  with one fleeing and one standing monster both at distance 2, picking the
  fleeing one makes the bot step where the original searches.  Measured on
  seed 40002 (turn 4396) and seed 40005 (turn 4518).

  `hasheq` of a record is `(bit-xor type-hash (APersistentMap/mapHasheq r))`.
  The port implements the Murmur3 pieces in `pybothack/util.py`, takes the 376
  monster-type hashes and the record type-hash as *dumped data*
  (`pybothack/_hashdata.json`, from `tools/cljcmp/dump_hash.clj`), and checks
  every value against that dump in `tests/test_clj_hash.py`.  Two traps found
  by comparing against the JVM rather than by reading the algorithm:

  - `Util.hashCombine` does `seed >> 2` on a **signed** Java int - an
    arithmetic shift.  Masking to 32 bits first (the obvious transcription)
    makes it logical and gives the right answer for every non-negative seed,
    which is why `:white` and `:remembered` matched while `:x`, `:y` and
    `:known` did not.
  - `map->Monster` materialises every *declared* record field the literal
    omits, as nil.  The port's `new_monster` left `awake` out entirely, so its
    monsters carried 11 map entries where the record has 12 - a different hash
    and a different place in the set.  `monster_hasheq` now refuses a dict that
    is missing a declared field rather than hashing it anyway.

  `Tile` records are deliberately *not* covered, and that is now a measured
  decision rather than a gap: `tools/audit_set_order_uses.py` finds exactly one
  set of tiles whose order is walked, the flood-fill frontier in
  `floodfill-room`, and its result is the min/max corners over the closed set -
  reachability through non-door tiles does not depend on visitation order, so the
  rectangle is the same whatever order the frontier is drained in.  The Tile
  type-hash is in `_hashdata.json` should that ever change.

* **The scraper decided one redraw too early** - the last of the day's four
  fidelity bugs, and the one with the widest reach.  `lastmsg+action` is:

  ```clojure
  (or (when (and (more-prompt? frame) (extra-topline-cursor? frame)) ...)
      (if (= "# #" (topline frame)) (ref-set player (:cursor frame)))
      (when (= (:cursor frame) @player) ... sink)
      (log/debug "lastmsg expecting further redraw"))
  ```

  The middle `if` is a **clause of the `or`**, and `ref-set` returns the Position
  it just set, which is truthy, so the `or` short-circuits there.  `apply-scraper`
  keeps the current scraper for any non-function return, so on a frame whose
  topline still reads `"# #"` the original records the player position and
  **waits for the next redraw**.  The port set the position and fell through to
  the `sink` branch on the same frame, so it chose its action one redraw earlier.

  Invisible while consecutive redraws carry the same picture - which is nearly
  always.  Decisive when they do not: during a hallucination episode NetHack
  re-randomises every monster glyph on every redraw, so one redraw of slack
  becomes a different monster map, a different threat set and a different
  target.  Measured on seed 40002 at keystroke 63 137, where the original had
  consumed three `"# #"` frames before deciding and the port none.

  Found by comparing what each bot could see at the *same keystroke offset*
  (`tools/align_check.py` + `replay_compare.py --align-out`) and then reading the
  original's own DEBUG log, which interleaves `writing to terminal:` with the
  scraper's state transitions and so shows exactly how many frames it waited.

* **One-character Clojure Strings are not Characters.**  `put-in-what` answers
  with `(set (map #(str (val %) (key %)) amt-map))`; with a nil amount that is
  the one-character *String* `"x"`, which `Util.hasheq` hashes as a String
  (`Murmur3.hashInt(String.hashCode())`), not as a Character (its code point).
  The set therefore reaches NetHack in a different order: the original sent
  `xGigAo`, the port `AGgiox`.  The port used to tell the two apart by length,
  with a comment claiming "no set the bot builds mixes them" - the flaw was not
  mixing but that a String can be one character long.  `clj.CljStr` now marks
  the producing site (`put-in-what`, `take-out-what`, the default
  `identify-what`), while `pick-up-what` and `loot-what`, which answer with
  inventory slots, stay Characters.  `tests/test_clj_hash.py` checks both
  orders against a JVM dump of `(seq (set ...))`.

* **The port's reader had an idle timeout the original does not have.**
  `bothack.run` gave up after 180 s without data; JTA's reader simply blocks.
  Two things were wrong with it: it ends the whole run while the bot may only be
  *thinking*, and it always won the race against `quit-when-idle`, which notices
  an idle bot on a 130 s tick and so can take up to 310 s to give up.  Seven of
  sixteen real games ended that way, the best of them at Dlvl 15 with 66 778
  points - killed, not lost.  The timeout is now off by default and available as
  `--idle-timeout` for comparison runs, where `:no-exit` has disabled the
  recovery handlers anyway.

* **Open: the bot stops choosing actions deep in the game.**  With the timeout
  gone, five of twelve games stalled - and they are the five deepest (Dlvl 17,
  18, 11; scores up to 179 008).  The bot moves about every 220 ms, then stops,
  logging nothing, until `quit-when-idle` writes `#` and quits four minutes
  later.  Not yet attributed: computing versus deadlocked is exactly what has to
  be measured first, with `WATCHDOG=60`, since the "slow decision" warning fires
  only after an action is chosen and here none is.  It is the main thing between
  the port and an ascension attempt.

* **`lastmsg+action` waited without a bound, and a stale frame made that wait
  permanent.**  The scraper records the hero's cursor in `lastmsg-get` and the
  `"# #"` clause in `lastmsg+action` re-records it, to *correct* the value from a
  later frame.  When a `"# #"` frame carries a **stale** cursor the correction
  goes the wrong way and no later frame can ever match.  Captured verbatim by the
  scraper's ring buffer:

  ```
  lastmsg_get     cursor=(59,20) topline=''      -> player=(59,20)
  lastmsg_action  cursor=(58,20) topline='# #'   -> player=(58,20)   stale
  lastmsg_action  cursor=(59,20) topline='#'     -> stuck for good
  ```

  The game then sat until `quit-when-idle` ended it, and it is the long games
  that lose the most: before the fix, five of twenty-four real games stalled and
  they were the five deepest.

  **Deliberate deviation:** the original waits here with no bound; the port keeps
  the same logic and gives up after `LASTMSG_WAIT_LIMIT` (40) redraws, proceeding
  as the matching branch would.  A legitimate wait is one to three redraws, so
  normal play never reaches the bound - checked: the guard fires **zero** times
  across the recorded games of the original, which still replay identically.
  Bounding the wait fixes the whole class rather than one cause of a poisoned
  position.

  This replaced an earlier, narrower guard (requiring the recorded cursor to be
  off the topline, `0 < y < 22`), which closed one path to the same deadlock and
  is still in `lastmsg-get`.

* **`quit-when-stuck` raised where the original exits.**  `(q)` ends with
  `(System/exit 0)`, so it never returns; the port returned `None`, the delegator
  kept looking for a handler, found none, and raised `No handler responded to
  prompt of choose_action`.  That is how the deepest game so far ended - Dlvl 28,
  6 941 840 points - instead of quitting cleanly.  `_quit` now raises
  `SystemExit` on the main thread (checked: it escapes the delegator's
  `except Exception`, exactly as `System/exit` escapes the JVM's `catch
  Exception`) and stops the reader loop when called from `quit-when-idle`'s
  thread, where raising would only end that thread.

* **`quit-when-idle` was not ported**, and it is the only recovery the framework
  has for a *scraper* deadlock.  Found by playing real games rather than by
  replaying recordings: the bot wielded a pick-axe, applied it, and NetHack asked
  `In what direction do you want to dig? [ulnj>]`.  Both implementations throw
  when a direction prompt reaches `choice-fn` - the original's own comment there
  reads "should recover itself" - and what recovers it is a background thread:

  ```clojure
  (future (while true
            (Thread/sleep (- (* 3 60 1000) 50000))
            (when-not (:inhibited @(:delegator a))
              (if-not @chosen
                (do (log/warn "attempting to unstuck")
                    (w "#") (u) (Thread/sleep 50000)
                    (when-not @chosen (log/error "3+ min idle - quitting") (q)))
                (reset! chosen false)))))
  ```

  `quit-when-looping` and `quit-when-stuck` cannot help: they are `choose-action`
  handlers, and a bot waiting on a prompt it cannot classify never reaches
  `choose-action`.  Without the thread the game sat until the reader's own idle
  timeout, with the bot alive at Dlvl 9 - one game in five of the first batch.

  Ported with the original's exact sequence, including that `(u)` writes a redraw
  (ctrl-R) and unpauses *only if* the delegator is inhibited.
  `tests/test_idle_recovery.py` drives the thread with the timings shortened and
  checks it fires when idle and stays quiet when not - an untested recovery path
  is the one that fails unattended.

* **`:no-exit true` disables all three recovery handlers**, in the original as
  well as the port (`main.clj:117`).  It exists so the harness owns the process
  lifetime during comparison runs; using it for a real game means a deadlocked
  bot never reaches an outcome.  Real games now use `config/play-config.edn`,
  which leaves them on.  The first batch was run with the wrong config, which is
  how the deadlock above stayed invisible instead of ending the game.

* **`should-try?` applies its predicates to the item-*id* record, not the item.**
  Found by the first long capture (seed 40002 under a 7 200 s cap, 313 786
  keystrokes - the bot survived the full two hours), and it sat 110 316 bytes
  into that stream, past the end of every shorter capture.

  ```clojure
  (and (wand? item)
       ((some-fn (every-pred (complement :engrave)
                             (complement (partial tried? game)))
                 (comp nil? :target))
        (item-id game item)))
  ```

  Every predicate in that `some-fn` receives `(item-id game item)` - including
  `tried?`, which then asks `((:tried game) (appearance-of id-record))`.  An id
  record that still has several candidates has **no `:name`**, so `appearance-of`
  is nil and the wand counts as never tried no matter how often its appearance
  was engrave-tested.  (`tried?`'s own docstring says zapping a wand is not a
  use, which suggests the author meant to pass the item; the call site passes the
  id record, and that is what the bot does.)

  The port passed `item`.  Its appearance *had* been engrave-tested, so
  `should-try?` was false, the glass wand failed `worthwhile?`, and the port
  dropped what the original kept - then livelocked retrying the drop, ending the
  replay with 507 449 keystrokes against the original's 313 786.  Fixed by
  passing the id record, and `appearance-of` now reads `:name` the nil-safe way
  Clojure does, because it is called on things that are not items.

* **A failed precondition escapes the delegator in Clojure and was caught in
  Python.**  `(catch Exception e ...)` in `invoke-handler` does not catch
  `java.lang.AssertionError`, so the original's `{:pre ...}` failures propagate
  out of the handler and the agent.  The port raised Python `AssertionError`,
  which *is* an `Exception` and was therefore caught and logged, leaving the bot
  running with a handler quietly skipped.  Now `clj.CljAssertionError` derives
  from `BaseException` and `clj.clj_assert` is used at all ten ported `:pre`
  sites, so both implementations fail in the same place.  Latent as well - no
  precondition fires on any of the eleven captures.

* **`at` asserts in Clojure and wrapped silently in Python.**  `position/at`
  carries `{:pre [(valid-position? x y)]}`, so an out-of-range coordinate throws
  and the delegator catches it, skipping the handler that asked.  The port
  indexed straight into the tile list, where `tiles[y - 1][-1]` is the **last
  column**: `(at level (update tile :x dec))` on a tile at x=0 - which
  `searchable-extremity` can produce, since it scans `(range col -1 -1)` down to
  zero - would compare against column 79 instead of failing.  The port now
  raises the same way.

  Latent, like the two below: the guard never fires on any of the eleven
  captures (checked with DEBUG logging on both complete games), and both still
  pass.  It is there so that when the situation does arise the two
  implementations fail in the same place rather than one of them answering
  confidently with the wrong tile.

* **The menu options map is built with `into`, and promotes at the ninth entry.**
  `menu-options` is `(into {} (map menu-line ...))`, a *transient* array map: it
  appends in screen order until the ninth entry promotes it to a hash map, after
  which `vals`/`keys` walk in the hash order of the slot Characters.  The port
  used a plain dict, which stays in screen order for ever.  A full inventory page
  has well over nine entries, and the order is observed twice: `take-out-what`
  appends `(map label->item (vals options))` to the container's `:items`, and
  `pick-up-what` walks `options` while `disj`-ing labels off its wanted set, so
  two identically labelled stacks are taken in that order.  Fixed with
  `clj.into_map`.

  Found by the class audits rather than by a divergence - none of the eleven
  captures loots a container from a nine-plus-item menu with duplicate labels, so
  the corpus is byte-identical either way.  It is fixed because the next capture
  might, not because a measurement demanded it, and that is stated here rather
  than dressed up as a closed divergence.

* **Where the deterministic corpus stands (2026-09-10).**  Fifteen recordings
  of the original - two independent campaigns, one 7 200 s capture, two made at
  reduced piece delays - replayed into the port: **1 182 022 keystroke bytes,
  1 182 022 identical, no divergence**.  Six are whole games and all six are
  PASS_COMPLETE; the other nine are captures the wall clock cut short and each
  matches over its whole length.  Table in `docs/RESULTS.md` §2d, evidence in
  `artifacts/gate_v2/`.

  What this does **not** say: that the port is equivalent to the original.  It
  says these fifteen recordings are reproduced.  Six are complete games of
  2 300-2 800 turns, none is an ascension, and the longest capture is a prefix
  *because the bot was still alive after two hours* - the deepest, rarest parts
  of a game are exactly what the corpus does not contain.  The one bug that the
  two-hour capture found (`should-try?`, above) sat 110 316 bytes in, past the
  end of every shorter recording, which is the whole argument for recording
  longer games rather than more of them.

* **Superseded, kept for the measurement record: nine full games, nine
  divergences.**  Also measured before the pinning protocol.  Recording nine complete games of the
  original (1 381-8 559 actions) and replaying each into the port
  (`docs/TESTS.md` §2d) reproduces none of them end to end.  The first
  divergences fall into three equal classes: a different move direction just
  after a `Pay`, `search` where the other bot moves, and `look here` where the
  other bot acts.  The inventory-order fix below moved two of the nine
  (seed40004 from 5.1 % to 20.2 % of the stream); the rest are open.
* **Which random draw is used.**  With the shared LCG the two bots consume the
  same values in the same number of draws (verified draw by draw in
  `artifacts/rng_trace/`), but they do not always *use* the same one.  While
  the player is trapped, `kick` calls `untrap-move`, which draws a random
  escape direction, and the pathfinder's cost function calls `kick` for every
  kickable door it expands — so one `navigate` burns several draws and only
  one of them becomes the action.  Measured on a trap: the original performs the
  direction from the first draw of the group, the port the one from the third.
  It is **not** fixed.  Note that this does *not* explain the "different
  direction after a Pay" class above: there the two draw streams are identical
  draw for draw (538/538 values, and both bots' `arbitrary-move` return the
  same direction for the deciding draw) - the two bots simply fidget a
  different number of times before moving on, which is a difference in the
  `:blocked` counter, not in the RNG.
* **Timing.**  The original's scraper is timing sensitive: driven against the
  local pty with logging turned down it stalls before its first action (it
  only plays with DEBUG logging, which slows the I/O enough), and with
  `:no-exit true` its idle-unstuck handler is not registered so it hangs.
  The port is fully synchronous - one redraw is processed to completion
  before the next chunk is read - so it does not have that race.  This is a
  deliberate difference in the port's favour; it changes *when* the bot acts,
  never *what* it decides.
* **The Amulet-of-Yendor ordering quirk** in the extracted appearance table:
  the dumped candidate order for `"Amulet of Yendor"` contains one entry
  because the original short-circuits that appearance before the logic query;
  the port keeps the second candidate at the end of its own list.  Nothing
  queries that list for that appearance.

## Faithfully reproduced upstream bugs

These are wrong in the original and are wrong here on purpose (removing them
would change the bot's play):

* `utility` adds its "+1 for uncursed" via `(uncursed? (:buc item))`, i.e.
  applied to the keyword rather than the item, so it never fires.
* `parse-botls` never emits `:blind`, so `update-player` clears `:ext-blind`
  on every status line.
* `want-to-eat?` evaluates `(parse-int strength)` before checking the
  monster's tags, so it throws for a character whose displayed strength is
  `18/**` (the exception is swallowed by the delegator, and the bot then
  never eats "beneficial" corpses).
* `pricec`/`propc` in `itemid` accept an item if *any* observed price or
  property fact fits, so extra observations can widen rather than narrow the
  possibilities.

* **Two divergences deep in a shared game.**  With the fast harness the two
  bots play identically for 1 969 actions / 37 810 keystrokes and then differ
  (`docs/RESULTS.md` §2c): on seed 31337 the original inserts a `Look` on
  arriving at a tile where the port looks a step later (an `examine-tile` state
  difference), and on seed 4242 they choose different directions in a fight
  next to an Elbereth engraving.  Both are open; neither is diagnosed.

## Open issues in the port

* **Occasional stall.**  In one of the long runs the port stopped choosing
  actions and spun at 100 % CPU after ~2500 actions; it has not been
  reproduced since (the profiling work that followed made navigation ~2x
  faster, which may or may not be related).  `--watchdog N` dumps a stack
  trace when no action is chosen for N seconds; use it if you see this.
* **Speed.**  A single decision costs milliseconds in the JVM and tens of
  milliseconds here, and a search-heavy one (`search-level` runs up to ~25
  Dijkstra passes) can take a second or more.  Measured end to end on the
  6-game batches this does *not* show up as fewer turns — the port managed
  6.8-10.4 actions/s against the original's 5.1-6.3 — but only because the
  original is forced to run with DEBUG logging (see the timing bullet above)
  and writes 16-58 MB of log per game.  Do not read the port as faster than
  the original; read it as fast enough that the comparison is not distorted.
* Neither bot answers NAO's "There is already a game in progress under your
  name.  Do what?" menu (the original's recovery was written for vanilla
  3.4.3's `[yn]` prompt), so a stale lock file stops the next game before its
  first action.  The batch scripts delete the lock first.

## The big one: no ascension

The port has **not ascended**, and this deliverable does not claim it has.
See `docs/RESULTS.md` for what it actually achieves and how that compares with
the original on the same build.  Reaching an ascension is a matter of both
remaining fidelity work and a lot of wall-clock time: the original needed
tuning plus many games, and a single ascending game of the original takes
hours of real time.
