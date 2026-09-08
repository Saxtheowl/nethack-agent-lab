# pybothack — a faithful Python rewrite of BotHack

A from-scratch Python port of [BotHack](https://github.com/krajj7/BotHack) by
krajj7 — the first NetHack bot that ascended the game without wizard mode or
human intervention (25 Jan 2015).  Framework *and* bot are reimplemented in
Python: no Clojure or Java code is used at run time, and no decision is
delegated to the original.

Target game: **NetHack 3.4.3 with the nethack.alt.org (NAO) patchset**, the
only version BotHack supports (`doc/compiling.md` of the original).  A build
script for it is included.

```
tools/build_nethack343_nao.sh <nh343-nao-checkout>   # builds upstream/nh343
python3 -m pybothack.main config/shell-config.edn    # plays a game
```

## Layout

| path | what |
| --- | --- |
| `pybothack/` | the port (framework + `bots/mainbot.py`) |
| `pybothack/_data.json` | item/monster/level data extracted verbatim from the original |
| `tools/` | build scripts, the comparison harness, the Clojure oracle |
| `tests/` | differential tests against the original |
| `docs/` | detailed documentation (port, tests, results, limitations) |
| `artifacts/` | build output, run logs, ttyrecs, evidence |

## Status

Read `docs/RESULTS.md` and `docs/LIMITATIONS.md` before trusting anything
here.  Where it stands, in three numbers:

* **1821/1821** differential cases identical to the live original
  (`python3 tests/test_differential.py`);
* both bots playing **the same live NetHack game** — same pinned game seed,
  same binary, no wizard mode — stay **byte-for-byte identical for 1 969
  actions / 37 810 keystrokes / 1.66 MB of game output** before their first
  difference, and are identical over the whole comparison on the shorter runs
  (`docs/RESULTS.md` §2c);
* **12 real games** (6 per bot, 600 s each, sequential on an idle machine, no
  wizard mode, no human input): the port is **behind** — median max depth 6 vs
  6.5, median score 7046 vs 11 606, 3 deaths in 6 against 2.  Its action-type
  distribution overlaps the original's by 93.7 % (96.1 % once one 948-action
  farlook livelock in the *original* is discounted).

**The port has not ascended, and neither did the original in these runs.**
Known gaps and reproduced upstream bugs are listed in `docs/LIMITATIONS.md`.
Nothing here should be read as a finished, fully verified-equivalent port.
