# Running things

## Build the game

```
tools/build_nethack343_nao.sh <path to a nh343-nao checkout>
```

Builds NetHack 3.4.3 + the nethack.alt.org patchset into `upstream/nh343`
(source: the NAO git repo linked from <https://alt.org/nethack/naonh.php>; a
mirror is at github.com/neoascetic/nh343-nao).  The script points HACKDIR and
VAR_PLAYGROUND at this repository, disables the mail daemon, links ncurses
(NAO builds the curses windowport) and uses the pre-generated lex/yacc output
NetHack ships (verified byte-identical to vanilla 3.4.3, which NAO does not
patch).  It also turns `_FORTIFY_SOURCE` off: 3.4.3 trips glibc's hardened
`sprintf` checks on a modern toolchain and aborts on the first screen.

## Play a game with the port

```
python3 -m pybothack.main config/shell-config.edn \
        --seed 42 --max-seconds 600 --log INFO --logfile game.log \
        --ttyrec game.ttyrec
```

`config/shell-config.edn` is BotHack's own config format (a subset).
`--watchdog N` dumps a stack trace if no action is chosen for N seconds.

## Play a game with the original (for comparison)

Needs a JDK 8 (Clojure 1.6 and `dynapath` do not run on 9+) and Leiningen:

```
BOTHACK_SRC=<bothack checkout> JDK8_HOME=<jdk8> LEIN_DIR=<dir with lein> \
    tools/batch_orig.sh 1 600 mygame
```

Keep the original's DEBUG logging on: with logging turned down its scraper
loses its synchronisation with the local pty before the first action (see
`docs/LIMITATIONS.md`).

## Reproduce the comparison

```
# unit-level differential (needs the original)
BOTHACK_SRC=… JDK8_HOME=… LEIN_DIR=… tools/run_oracle.sh
python3 tests/test_differential.py

# record a game of the original, replay it into both bots, compare
BOTHACK_SRC=… JDK8_HOME=… LEIN_DIR=… tools/compare_pipeline.sh out 300

# batches of real games + summary
tools/batch_py.sh 6 600 py
BOTHACK_SRC=… JDK8_HOME=… LEIN_DIR=… tools/batch_orig.sh 6 600 orig
python3 tools/summarize_games.py .
python3 tools/summarize_xlog.py upstream/nh343/var/xlogfile
```

The bots' own logs under `artifacts/games/` are kept gzipped (they run to
12-58 MB each); `tools/summarize_games.py` reads either form, and `zgrep`
works on them directly.

Note: kill a bot mid-game and NetHack leaves a lock behind; the next game then
stops at "There is already a game in progress under your name.  Do what?",
which neither bot answers (the original's recovery predates the NAO patch that
turned that prompt into a menu).  The batch scripts delete the stale lock
before each game.

## The deterministic fidelity loop

```
# record N games of the original with everything pinned, judge each recording,
# replay it into the port, aggregate
BOTHACK_SRC=… JDK8_HOME=… LEIN_DIR=… tools/fidelity_batch.sh out 6 1 3600

# just the cheap half, after a fix (no NetHack, no JVM)
tools/replay_port.sh out/seed40001
python3 tools/fidelity_manifest.py out
```

Record on an **idle** machine: the original stops agreeing with its own earlier
runs when the machine is loaded (`docs/TESTS.md`, "The pinning is partial").
Replaying is unaffected - a capture is self-contained.

The cap is an upper bound.  `record_orig.sh` stops early when the capture has
gone quiet *and* attests an end (the bot dies, NetHack waits at a DYWYPI prompt
it never answers, and the JVM would otherwise sit there for the rest of the cap),
and after `RECORD_IDLE_STALL` seconds of silence with no attested end it stops
and says "stalled" instead of burning the clock.  Tune with `RECORD_IDLE_DONE`
(default 60 s) and `RECORD_IDLE_STALL` (default 600 s).

When a replay diverges, name the decision before reading any code:

```
python3 tools/compare_decisions.py out/seed40002/bothack.log \
        out/seed40002/replay/port_actions.tsv
```

and if the disagreement is about what each bot could *see*:

```
python3 tools/align_check.py out/seed40002/tap.log 23 11 --from 63000 --to 63200
python3 tools/replay_compare.py out/seed40002/tap.log --align-out port.txt \
        --align-pos 23,11
```

## Clojure hashing

Set iteration order is part of the behaviour (menu answers, monster sets).  The
values are dumped from the JVM, never derived:

```
BOTHACK_SRC=… JDK8_HOME=… LEIN_DIR=… \
  lein run -m cljcmp.dump-hash        # -> pybothack/_hashdata.json
  lein run -m cljcmp.dump-setorder    # -> the expected (seq (set …)) orders
python3 tests/test_clj_hash.py
```

## Tracing the original

`tools/cljcmp/dbg_inv.clj` adds env-gated traces without modifying BotHack
(the harness only appends its own namespaces to Leiningen's source path and
rebinds vars with `alter-var-root`):

| variable | what it logs |
| --- | --- |
| `BOTHACK_INV_TRACE` | inventory key order and the slot `choose-food` picks |
| `BOTHACK_ARB_TRACE` | `arbitrary-move` candidates |
| `BOTHACK_BLOCKED_TRACE` | `fidget` target / `:blocked` / return |
| `BOTHACK_EXAMINE_TRACE` | `examine-tile` predicates |
| `BOTHACK_VISIBLE_TRACE` | `visible?` / `in-fov?` / `lit?` plus the FOV window |
| `BOTHACK_UPDTILE_TRACE` | `update-at-player-when-known` REGISTER/FIRE |
| `BOTHACK_NEWITEMS_TRACE` | every `:new-items` transition on one tile, **with the call stack** |

The last one is the lesson: trace the *writer* of a piece of state, not its
readers.  Sixteen candidate causes had been eliminated by measuring readers; two
lines from the writer trace named the bug.

## Real games (the mission's own test)

```
# N games, PAR at a time, no cap - each game runs until it ends by itself
tools/ascend_batch.sh out 16 4 0
python3 tools/ascend_summary.py out
```

Uses `config/play-config.edn`, **not** `config/shell-config.edn`: the latter sets
`:no-exit true`, which disables `quit-when-idle`, `quit-when-looping` and
`quit-when-stuck` (in the original too), so a deadlocked game never ends.

Outcomes are read from NetHack's own xlogfile, matched by the per-slot player
name and a time window.  A game that finishes **without** an xlogfile entry is
the signal that the harness or the bot broke rather than the bot losing - that is
how the pick-axe deadlock was caught.

Each slot gets its own NetHack user name and HOME so games can run in parallel
without deleting each other's level files, and the script only ever kills the
processes belonging to its own slots.

## Class audits over the original's source

Each of these takes the original's `src/bothack` directory and reports a whole
*class* of faithfulness trap, so a bug found once can be shown to be the only
one of its kind (`docs/TESTS.md` §2h):

```
SRC=<bothack checkout>/src/bothack
python3 tools/audit_atom_args.py       $SRC   # the atom where a map is wanted
python3 tools/audit_or_side_effects.py $SRC   # an `or` clause that is a statement
python3 tools/audit_set_order_uses.py  $SRC   # sets whose iteration order is observed
python3 tools/audit_map_order_uses.py  $SRC   # the same for maps
python3 tools/audit_set_elements.py    $SRC   # Characters vs one-char Strings
python3 tools/audit_iflet_destructuring.py $SRC  # if-let testing the container
python3 tools/audit_port_condp.py              # port side: lost condp short-circuits
python3 tools/audit_port_condp.py --self-test  # proves that audit can still detect one
```

They share `tools/cljread.py`, a small Clojure reader.  Before trusting a "no
hits" result, check that the audit still finds the bug it was written for - all
five do.

## The rented pilot

`docs/VAST.md` has the plan, the cost cap and the go/no-go criteria;
`tools/vast/provision.sh`, `worker.sh` and `collect.sh` are the worker side.
