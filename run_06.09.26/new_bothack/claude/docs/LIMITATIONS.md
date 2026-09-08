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
* **The "different direction after a Pay" class (3 of 9 games), narrowed but
  not closed.**  The performed action differs by exactly one reason: the port's
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
* **The blocking class: what has been ruled out.**  The whole difference is one
  boolean: at turn 1356, tile (5,18), the original has `new-items true` and the
  port `false`; everything else about that tile and the four preceding turns is
  identical.  Every writer of that flag has been compared *and measured*, and
  none of them explains it:

  | candidate | verdict | how it was measured |
  | --- | --- | --- |
  | `--More--` message partitioning | ruled out | the port's 464 messages are identical to the original's first 464 |
  | `examine-tile` | ruled out | compared line by line; both traces agree at turns 1353-1355 |
  | engraving parsing (`etype`/`etext`) | ruled out | same regexes, same table |
  | `move-message-handler` | ruled out | same six patterns |
  | `update-tile` call sites | ruled out | same nine actions |
  | `update-at-player-when-known` | ruled out | REGISTER/FIRE traces identical on both sides, including at turns 1353-1367 |
  | multiline "Things that are here" | ruled out | no such message between offsets 12230 and 12802 on either side |
  | `Throw`'s `(not (visible? …))` branch | ruled out | the original's `visible?` on (5,18) is **true**, like the port's |
  | `visible?` / `lit?` / `in-fov?` / `update-fov` / `transparent?` | ruled out | compared; the tile is adjacent to the player so `lit` is true both sides |
  | `mark-item` (map scan) | ruled out | faithful |
  | `mark-death` / `death-tracker` | ruled out | same regex and gating; the message at that point is "The dagger hits…", not a kill |

  The port never sets the flag after turn 684 (traced through both
  `update_at` and `update_at_player`).  The remaining hypothesis is the map
  scan seeing the thrown dagger's glyph on (5,18) at turn 1355 in one bot and
  the homunculus still standing there in the other - i.e. *when* the monster
  vacates the tile in each bot's model.  Not yet measured.
* **The one blocking class, against the deterministic reference.**  Of five
  recordings replayed under the deterministic protocol, one is `PASS_COMPLETE`
  and four diverge - **all four at the same kind of decision**: the original
  performs a `Look` that the port does not (seeds 40002/40004/40005/40008, at
  commands 833/1681/1651/1334).  Traced on seed 40002: after looking at tile
  (4,17) the original's tile still has `:new-items true` and `:engraving nil`,
  so it looks again; the port's tile has `new-items false` and
  `engraving 'Elbereth'`, so it moves on.  Both bots received the *same bytes*
  - `tools/replay_compare.py --log-messages` shows the port getting
  `There is a doorway here.  Something is written here in the dust.` and
  `You read: "..."` **within the same action**.  The two therefore partition
  the messages that arrive after a `--More--` differently between actions, and
  that changes both the engraving capture and the `new-items` flag.  This is
  the single blocker before a paid campaign is worth running.
* **Nine full games, nine divergences.**  Recording nine complete games of the
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
