# BotHack on NetHack 3.6.7 — assisted, fully automatic

A Python BotHack (the `pybothack` port that ascended NetHack 3.4.3) adapted to
**NetHack 3.6.7**, playing through a **structured window port** added to the
game, with **optional, logged test assistance** and a local harness that runs
series of games and keeps what is needed to understand each failure.

Status and measured results: see [docs/RESULTS.md](docs/RESULTS.md).

## Layout

| path | what |
| --- | --- |
| `vendor/NetHack-NetHack-3.6.7_Released/` | official 3.6.7 sources (tag tarball, sha256 in docs) — untouched |
| `engine/nethack-3.6.7/` | the patched tree; `engine/nethack-3.6.7-bot.patch` is the diff against vendor |
| `engine/nethack-3.6.7/win/bot/winbot.c` | the "bot" window port (JSON lines protocol) |
| `engine/nethack-3.6.7/src/botassist.c` | assists, seed, engine verdict |
| `engine/build.sh` | builds into `build/install/` |
| `nhbot/engine.py` | protocol client, one isolated directory per game |
| `pybothack/` | BotHack strategy (copied from the 3.4.3 port) + `nhbridge.py`, `compat36.py`, `rules36.py`, `bh36.py` |
| `nhbot/rungame.py` | run one game, write manifest/result/logs |
| `nhbot/series.py` | run a series locally (N workers), summary, early stop on repeated failures |
| `nhbot/analyze.py` | explain a game or a series |
| `nhbot/supervisor.py` | limits, goals, loop/stall detection and recovery |
| `nhbot/scenarios.py`, `scenarios/*.json` | prepared situations (wizard mode, never counted) |
| `config/kit-default.txt` | default assist kit |
| `tests/` | unit tests (3.6 translations, 3.6 rules) |
| `tools/audit_messages.py` | audit of BotHack message regexes against 3.6.7 strings |

## Why a window port and not NLE / a terminal

BotHack's 3.4.3 port lost 37% of its games to terminal synchronisation (the
scraper).  The `bot` window port removes that class of bugs: NetHack itself
says what it waits for.  Each input the game needs is one JSON request:

* `cmd` (a new command), `cmdcont` (count digits / prefix continuation),
  `key` (any other single key), `yn` (with the query, allowed choices and
  default), `line` (getlin, with the query), `ext` (extended command),
  `menu` (prompt, how, every item with identifier/accelerator/text),
  `pos` (getpos, with the goal text and cursor);
* every request carries the events since the previous one (messages, text
  windows, display-only menus, assist interventions), the changed map cells
  (glyph, char, color, flags), the status values, the inventory when it
  changed, the hero position;
* identities are not leaked: glyphs of unidentified object types are masked;
  `priv` (achievements, luck, alignment record...) is for logs and verdicts
  only, the bot never reads it.

The bot answers one line (`k`, `y`, `l`, `x`, `m`, `p`, `e`).  The game ends
with an `end` record written by `done()` itself (how, killer, depth, turns,
achievements, assist counters), and NetHack writes its own `xlogfile` in the
per-game directory; the verdict uses both.

`pybothack` still "types keys": `nhbridge.py` turns them into structured
answers (a direction key answers a `yn` direction prompt, `#pray\n` answers
`cmd` then `ext`, menu letters are mapped to item identifiers, getpos cursor
keys are simulated).  When nothing is queued, the bridge asks the BotHack
prompt handlers exactly as the scraper did; unknown prompts get a
conservative, logged answer.

## Assistance (test version)

All off by default in the engine, on by default in `rungame` (use flags to
disable).  Every intervention is an `assist` event in the protocol, a line in
`assist.jsonl` and a milestone in `progress.jsonl`.

| assist | engine variable | rungame flag to disable |
| --- | --- | --- |
| invincibility: a death (not genocide/quit) is undone like an unconsumed amulet of life saving, without the helpless turn; drained attributes, experience levels and maximum HP are restored (else brainlessness or drains make the hero useless); fatal sliming is cured before it destroys the armor; a mind flayer cannot eat the last point of Int | `NH_ASSIST_INVINCIBLE=1` | `--no-invincible` |
| no starvation: nutrition < 50 is reset to 900; fatal choking prevented | `NH_ASSIST_NOSTARVE=1` | `--no-nostarve` |
| starting kit (wish syntax, identified, worn/wielded as asked) | `NH_ASSIST_KIT=file` | `--kit none` |
| all of the above | | `--no-assist` |

The kit never contains goal items (Bell, Candelabrum, Book, candles, Amulet,
quest artifact) and the assistance never moves the hero, answers prompts or
opens levels.  An ascension with any assist enabled is reported as
`outcome: ascended, assisted: true`.

## 3.6.7 rules adapted (see `pybothack/rules36.py`, `compat36.py`)

* **Pudding farming** removed (3.6: clones drop nothing, XP diminishes); the
  farm handlers are not registered and `farm-done?` keeps only its
  non-score arm.
* **Elbereth**: exact text only (never append), useless in Gehennom and the
  planes, not respected by @, minotaurs, peacefuls, shopkeepers, guards; the
  bot never attacks (melee/ranged) from an Elbereth square a monster that
  respects it ("You feel like a hypocrite": −5 alignment), the
  "engrave then keep fighting" tactic is gone, prayer is blocked for 1000
  turns after a hypocrite message.
* **Prayer** uses `critically_low_hp()` of 3.6.7.
* **Interaction differences** translated: container menu ("Do what with
  ...?"), `#name` menu, object names ("containing N items", "empty",
  "locked", "(at the ready)", "(in quiver pouch)", shop prices), messages
  (locked containers, bag opening, legs, remove curse) — each translation is
  counted in the game result.

## Commands

Build the engine (once, ~2 min):

    engine/build.sh            # or engine/build.sh --clean

One game:

    python3 -m nhbot.rungame --out runs/manual/g1 --seed 42
    python3 -m nhbot.rungame --out runs/manual/g2 --seed 42 --goal minetown
    python3 -m nhbot.rungame --out runs/manual/g3 --no-assist --max-turns 20000
    python3 -m nhbot.rungame --out runs/manual/s1 --scenario smoke-levelport
    python3 -m nhbot.rungame --out runs/manual/s2 --scenario astral-altar --seed 101

Scenarios (`scenarios/*.json`, wizard mode, never counted as full games):
`smoke-levelport`, `medusa-to-castle`, `medusa-unmapped`, `castle-to-valley`,
`valley-to-vlad`, `quest-bell`, `invocation`, `planes`, `astral` (arrival
point of the Astral Plane) and `astral-altar` (next to the central temple).
Steps available: `xl`, `wish`, `identify`, `wear`/`wield`/`puton`,
`levelport`, `levelport_rel`, `levelport_menu`, `teleport`, `map`, `keys`
(see `nhbot/scenarios.py`).

A series (each game in its own process, N in parallel):

    python3 -m nhbot.series --name mt01 --games 8 --jobs 2 --goal minetown \
        --max-turns 30000
    python3 -m nhbot.series --name asc01 --games 4 --jobs 2 --seed-base 5000

Explain:

    python3 -m nhbot.analyze runs/mt01            # series summary
    python3 -m nhbot.analyze runs/mt01/g003 --steps 150

Tests:

    python3 -m pytest -q tests

## What is kept for every game (`runs/<series>/gNNN/`)

| file | content |
| --- | --- |
| `manifest.json` | engine binary sha256, patch sha256, bot code hash, git head, engine seed, bot seed, assists and kit lines, wizard/scenario, goal, limits |
| `result.json` | outcome (`ascended`, `died`, `quit`, `escaped`, `goal_reached`, `stuck`, `limit`, `crash_bot`, `crash_engine`, `unknown`), reason, engine verdict, NetHack xlogfile record, turns, depth, stages reached with turn, assist counts, translation/fallback counters, action histogram, speed, final screen |
| `progress.jsonl` | milestones: depth, branches, special levels (Minetown variant, Oracle, Medusa variant, Castle...), XL, achievements, every assist intervention, heartbeat every 1000 turns |
| `last_steps.jsonl` | ring buffer (800): each request (turn, level, position, HP, prompt), messages, the answer, the action chosen with BotHack's reasons, notes (recoveries, fallbacks, unknown prompts) |
| `live.json` | current state while running |
| `bot.log` | bot warnings/errors (tracebacks) |
| `assist.jsonl` | engine-side assist log |
| `nhdir/xlogfile`, `nhdir/dumplog.txt` | NetHack's own records |
| `stacks.txt` | Python stacks (slow decisions, `kill -USR1`) |
| `engine.stderr` | engine diagnostics |

## Remote worker (local network or Vast AI)

A headless engine build needs only a C compiler and Python 3 (no ncurses,
no pyte, no pip packages):

    HEADLESS=1 engine/build.sh            # "bot" window port only

Scripts used for the local 8-core worker (`miniforum-worker`):

    tools/sync_worker.sh                  # rsync code (no runs/builds)
    tools/worker_series.sh --name ca-w01 --games 14 --jobs 7 \
        --seed-base 5000 --goal castle --max-turns 60000   # detached
    tools/fetch_worker.sh ca-w01          # results -> runs/worker/ca-w01
    python3 -m nhbot.analyze runs/worker/ca-w01

Single games, scenarios and debug replays also run on the worker, in a
separate code directory (`~/bothack36-dev`) that can be synced at any time
without touching a running series (the series script refuses to sync under
a running series, so that one series never mixes two bot versions):

    tools/worker_dev.sh sync                                  # code + engine rebuild if needed
    tools/worker_dev.sh run astral1 --scenario astral-altar --seed 101 --trace
    tools/worker_dev.sh status                                # all dev runs
    tools/worker_dev.sh wait astral1 && tools/worker_dev.sh fetch astral1
    python3 -m nhbot.analyze runs/worker-dev/astral1 --steps 40

The local machine is only used to edit code and run `pytest`.

## Scaling out (e.g. Vast AI)

Nothing here is tied to the local machine: `engine/build.sh` +
`python3 -m nhbot.series --jobs N` on each host; every game directory is
self-contained and `summary.json` merges trivially.  `--stop-on-repeat`
prevents burning hours on a known bug.
