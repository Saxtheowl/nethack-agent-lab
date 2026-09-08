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
