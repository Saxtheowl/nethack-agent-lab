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
| `pybothack/_hashdata.json` | Clojure `hasheq` values dumped from the JVM (set iteration order) |
| `tools/` | build scripts, the comparison harness, the Clojure oracle |
| `tests/` | differential tests against the original |
| `docs/` | detailed documentation (port, tests, results, limitations, the rented pilot) |
| `artifacts/` | build output, run logs, ttyrecs, evidence |

## Status

Read `docs/RESULTS.md` and `docs/LIMITATIONS.md` before trusting anything
here.  Where it stands:

* **Whole games, byte for byte.**  Fifteen recordings of the original - two
  independent campaigns, a two-hour capture, and two made at a reduced piece
  delay - replayed into the port under the deterministic protocol
  (`docs/TESTS.md` §2b): **1 182 022 keystroke bytes, 1 182 022 identical, no
  divergence.**  The six recordings that are complete games are reproduced from
  the first keystroke to the last; the nine that the wall clock cut short each
  match over their whole length, up to 313 786 bytes.  It says those fifteen
  recordings are reproduced - not that the port is equivalent, and none of them
  is an ascension;
* **1821/1821** differential cases identical to the live original
  (`python3 tests/test_differential.py`), plus `tests/test_clj_hash.py`
  (Clojure record hashing against a JVM dump) and `tests/test_verdict.py`;
* both bots playing **the same live NetHack game** (`docs/RESULTS.md` §2c) -
  superseded by the bullet above and **measured before the fidelity fixes of
  2026-09-08/09**, so its "1 969 actions before the first difference" is a floor
  from an older port, not the current result;
* **~140 real games** (no wizard mode, no human intervention, each run until it
  ends by itself).  Two records, from two different populations, both stated
  because quoting one number from each would overstate the result: NetHack's own
  xlogfile - which records only games that ended *in NetHack* - gives deepest
  **Dlvl 21** and top score **120 050** over 138 games; the bot's own logs, which
  also cover games the bot abandoned, give deepest **Dlvl 28** and top score
  **15 669 164** over 121 580 turns.  The seven-figure scores are sink farming,
  an upstream strategy (`farm-sink` / `FarmAttack` / `farm-done?`), so the port
  reaches the phase the original credits for its own first win.  Playing found
  nine defects the replay gate cannot see (`docs/RESULTS.md` §2e).  The three
  most recent: an idle-recovery handler that never sent the ESCs that unstick
  NetHack (17 games lost), a `TypeError` that silently discarded 3002 farlooks,
  and a monster-description strip that the original does not do;
* **the blocker is not dying, it is giving up**: of the 76 games that finished,
  32% ended because the bot abandoned them (idle loop, stuck, crash) rather than
  because it died - including games at Dlvl 17 and 18.  Whether the original
  does the same at the same rate is **not yet settled**; `tools/ascend_pool_orig.sh`
  and `tools/compare_realgames.py` exist to settle it and are running;

The port makes **two deliberate deviations** from the original, both in the
scraper's synchronisation path and both listed with their evidence at the top of
`docs/LIMITATIONS.md`.  Each removes a state in which a live game hangs for good;
neither fires on any recorded game of the original.  A third was claimed and
turned out to be a port defect misread as an improvement - that story is in the
same file, because it is the more useful one.

**The port has not ascended, and neither did the original in these runs.**
Known gaps and reproduced upstream bugs are listed in `docs/LIMITATIONS.md`.
Nothing here should be read as a finished, fully verified-equivalent port.
