# The port, module by module

The port mirrors the original's structure one namespace per module, keeping
the original's function names (kebab-case → snake_case) so the two can be read
side by side.

| original (Clojure) | port (Python) | notes |
| --- | --- | --- |
| `bothack/util.clj` | `pybothack/util.py` | plus `LCG` (comparison harness only) |
| `bothack/position.clj` | `pybothack/position.py` | `Pos` supports `['x']` so it is interchangeable with tile maps |
| `bothack/frame.clj` | `pybothack/frame.py` | |
| `bothack/term.clj` (JTA vt320) | `pybothack/term.py` (pyte) | see *Terminal* below |
| `bothack/jta.clj` | `pybothack/iface.py` | local pty / telnet instead of the JTA library |
| `bothack/ttyrec.clj` | `pybothack/iface.py` (`Ttyrec`) | same file format |
| `bothack/delegator.clj` | `pybothack/delegator.py` | see *Agent semantics* below |
| `bothack/action.clj`, `actions.clj` | `pybothack/action.py`, `actions.py` | actions are maps, as in the original |
| `bothack/handlers.clj` | `pybothack/handlers.py` | |
| `bothack/scraper.clj` | `pybothack/scraper.py` | the `##'` synchronisation state machine, step for step |
| `bothack/tile.clj` | `pybothack/tile.py` | |
| `bothack/level.clj` | `pybothack/level.py` | blueprints extracted verbatim |
| `bothack/dungeon.clj` | `pybothack/dungeon.py` | |
| `bothack/monster.clj`, `montype.clj` | `pybothack/monster.py`, `montype.py` | 376 monster types extracted verbatim |
| `bothack/item.clj`, `itemtype.clj`, `itemdata.clj` | `pybothack/item.py`, `itemtype.py`, `_data.json` | 1722 item types extracted verbatim |
| `bothack/itemid.clj` (core.logic) | `pybothack/itemid.py` | see *Item identification* below |
| `bothack/player.clj` | `pybothack/player.py` | |
| `bothack/game.clj` | `pybothack/game.py` | |
| `bothack/fov.clj` + `java/bothack/NHFov.java` | `pybothack/fov.py` | line-for-line transcription of the Java |
| `bothack/pathing.clj` | `pybothack/pathing.py` | |
| `bothack/sokoban.clj` | `pybothack/sokoban.py` | solutions extracted verbatim |
| `bothack/behaviors.clj` | `pybothack/behaviors.py` | |
| `bothack/bothack.clj`, `main.clj` | `pybothack/bothack.py`, `main.py` | |
| `bothack/bots/mainbot.clj` | `pybothack/bots/mainbot.py` | the ascending bot's strategy |

Not ported: the Java/JVM bot API (`java/bothack/**`, `javabots/**`) — it only
exists to let JVM bots drive the framework; the wizard-mode test bot
(`bots/wizbot.clj`) and `bots/simplebot.clj`.

## Data: extracted, not transcribed

`tools/cljdump/dumpdata.clj` runs inside the original project and serialises
its own data structures: every item type (with the per-kind defaults already
merged), every monster type, the special level blueprints, the sokoban
solutions and the boulder maps.  `pybothack/_data.json` and `_leveldata.json`
are that dump.  Nothing in the 3675-line `itemdata.clj` or the 620-line
`montype.clj` was retyped, so those tables cannot drift.

The dump also carries `appearance-names`: for every unidentified appearance,
the candidate item ids **in the order core.logic enumerates them**.  The port
reuses that order because `item-type`/`item-subtype`/`item-weight` take the
first candidate, and for 24 appearances (e.g. `gray stone` → luckstone vs.
loadstone) the candidates differ in weight.

## Design decisions that carry meaning

### Immutable state
BotHack keeps the whole world in immutable maps and takes cheap snapshots
(`(:last-state game)`) to diff turn to turn.  `pybothack/clj.py` provides
`assoc`/`update_in`/`dissoc_in`… with copy-on-write: only the maps along the
updated path are shallow-copied.  No code in the port mutates a map in place,
so `last-state` snapshots stay valid exactly as in the original.

### Agent semantics (this one bites)
The original's delegator is a Clojure **agent**: every call a handler makes on
it (`(send delegator write " ")`, `(send delegator full-frame frame)`,
handler (de)registration…) is *queued* and only runs after the current
dispatch finishes.  The ordering is load-bearing: the scraper resets its state
machine in `action-chosen`, which must happen **after** the redraw that
triggered the action has stored its next state.  `Delegator._send`/`drain`
reproduce that; the calls the original makes directly on the delegator value
(`response-chosen`, `action-chosen`, `write` inside `respond-*`,
`dlvl-changed` from the botl handler) stay synchronous and have `_direct`
variants.

### Terminal
JTA's `vt320.putString` emits exactly one redraw per non-empty read, and the
reader reads at most 256 bytes at a time.  The scraper's state machine reacts
to *frames*, so those boundaries are part of the observable behaviour;
`pybothack/term.py` + `bothack.run()` reproduce them (`os.read(fd, 256)`, one
`redraw` per chunk).  Character attributes are converted with JTA's packing
rules (`bothack.term/unpack-colors`), including the inverse-video case where
the background colour index is used.

### Item identification
`itemid.clj` is a core.logic program, but every relation in it is a set of
ground facts and every goal is a deterministic `conda`/`condu` chain, so it
translates directly into explicit filters (`itemid._possible`).  The
translation keeps the original's semantics exactly, including the ones that
look like bugs:

* `pricec`/`propc` succeed if **any** observed price/property fact is
  consistent, so several observations widen rather than narrow the candidate
  set;
* group elimination (`eliminatedo`) runs after every new fact and only fires
  when an appearance has exactly one remaining candidate.

The three worked examples left as comments in `itemid.clj` (scroll of
identify from two prices, from a sell price, wand of wishing from
engrave-id + price) reproduce exactly.

### Clojure semantics that Python does not share
* **Map iteration order.**  A Clojure map of nine or fewer entries is a
  PersistentArrayMap whose `assoc` *prepends*, so `vals`/`keys`/`seq` walk it
  in reverse insertion order; the tenth entry promotes it to a
  PersistentHashMap, which walks in hash order.  Python's dicts always walk in
  insertion order, so `clj.clj_vals`/`clj_keys`/`clj_items` reproduce both
  regimes (hash order via `position.hamt_key`).  This is load-bearing for
  `(:monsters level)`: it picks the monster to farlook and the pairing order
  in `track-monsters`.
* **Set iteration order.**  A Clojure set of menu answers is a
  PersistentHashSet and reaches NetHack in hash order; Python's `set` order
  depends on the per-process string hash seed and is not even stable between
  runs of the same code.  `delegator._respond_menu` imposes Clojure's order,
  using `util.clj_hasheq`: `Character.hashCode` (the code point) for a single
  character, `Murmur3.hashInt(String.hashCode())` for the `count + slot`
  strings `take-out-what` returns.  The port tells the two apart by length,
  which is correct because no set the bot builds mixes them.
* `(min-key f)` / `(max-key f)` keep the **last** extreme on ties;
  `util.min_by`/`max_by` do the same (`first_min_by` keeps the first).  Getting
  this wrong silently changes which level the bot picks as a branch candidate.
* `(= true 1)` is false in Clojure and true in Python; `itemid._clj_eq`
  restores Clojure's behaviour where item records are merged.
* An `or`-chain clause that evaluates to `nil` continues to the next clause,
  while `(if-let [{:keys [step]} (navigate …)] …)` tests the **Path**, not the
  step — `seek` therefore returns nil (rather than exploring) when the target
  is already reached.  Both patterns are reproduced literally.

### The exploration cache is a future in the original
`reset-exploration` stores `(future (curlvl-exploration game))` in
`:explore-cache` at *about-to-choose*, `explore` blocks on `@` to get it, and
`action-chosen` calls `future-cancel` on it.  The port computes
`_curlvl_exploration(game)` eagerly at the same point and stores the value.
Both capture the same pre-action game state, so the cached value should be the
same - but `curlvl-exploration` runs `navigate`, whose cost function calls
`fidget` and therefore draws from the RNG, and in the original those draws
happen **on another thread**.  This is the current lead for the one class of
live divergence that is narrowed but not closed (see `docs/LIMITATIONS.md`).

### Faithfully reproduced upstream quirks
* `parse-botls` emits no `:blind` key, so `update-player` always clears
  `:ext-blind` — the external-blindness memory of the original is effectively
  a no-op, and it is here too.
* `by-description` returns a role *string* (not a monster type) for rank
  descriptions such as "a stripling", so `(:name …)` on it is nil.
* `initial-ids` of `"a bag called bag2"` includes `bag of tricks`.
