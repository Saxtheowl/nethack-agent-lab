# BotHack on NetHack 3.4.3 — recording & replay

Isolates the only bot known to have ascended NetHack 3.4.3 (**BotHack** by
@krajj7, first ascension 2015-02-15), makes it play until 10 winning games
are recorded, and serves a web replay viewer.

## What you get

- A container (`bothack-nh343`) with:
  - NetHack 3.4.3 + NAO patchset built from source
  - A small source patch (`patches/01-seed-env.patch`) so `NETHACK_SEED`
    deterministically seeds the RNG (replaces the `time(NULL) + /dev/urandom`
    mix) → the same seed always produces the same game.
  - BotHack uberjar built against Java 17, with the jta26 JNI lib.
- A runner (`/opt/runner/loop.py`) that:
  - Picks a fresh seed per attempt,
  - Spawns BotHack with `:interface :shell` against the local NetHack binary
    via a wrapper that exports `NETHACK_SEED`,
  - Records the session as `game.ttyrec` (BotHack's built-in `:ttyrec true`),
  - Detects ascension by scanning the recording for the `You ascended` /
    `reached the status of Demigod{,dess}` markers,
  - Keeps every attempt under `/data/games/attempts/`,
  - Promotes winning games to `/data/games/winning/NNNN_seed.../`,
  - Saves a `meta.json` with seed, turn count, timestamps, exit code.
- A replay web app on port 8080:
  - `index.html` — table of all games and a separate table of wins
  - `replay.html` — xterm.js rendering of a ttyrec, with:
    - play/pause, speeds ¼× → 32× and "no delay"
    - step ±1 frame
    - jump ±1 / ±10 / ±100 turns (uses the turn index built server-side from
      the status line `T:NNN`)
    - "jump to turn N"
    - scrubber over frames
    - keyboard shortcuts (Space, ←/→, Ctrl/Shift+arrows, [/], Home/End)

## Layout

```
.
├── Dockerfile, docker-compose.yml
├── config/        — nethackrc + shell-config.edn + sshd_config
├── patches/       — NETHACK_SEED source patch
├── runner/        — loop.py, run_one.sh, nh-launcher.sh, detect_ascension.py
├── replay/        — FastAPI server + xterm.js front-end (static/)
└── scripts/       — entrypoint.sh
```

## Ports (no conflict with sibling containers)

| service       | container | host   |
|---------------|-----------|--------|
| SSH (bot)     | 22        | 2225   |
| Replay UI     | 8080      | 8085   |

`super-nethack` (2222) and `super-nethack-bothack-lab` (2223/8080) keep their ports — unchanged.

## Build & run

```bash
docker compose build         # ~10 min the first time (NetHack + lein deps)
docker compose up -d
```

### Inside the container

```bash
# kick off the auto-collection (5 games in parallel by default)
ssh -p 2225 bot@localhost
/opt/runner/loop.py --target 10 --parallel 5           # in foreground
nohup /opt/runner/loop.py --target 10 --parallel 5 \
    > /data/logs/loop.log 2>&1 &                       # in background
tail -F /data/logs/loop.log
```

Progress is in `/data/games/index.json` and live on the web UI.

Each worker uses its own `/nh343-wN` playground (separate `save/`, `perm`,
`record`), so the fcntl lock on `perm` is per-worker — concurrent games
don't block each other. `--parallel` accepts 1..8 (8 worker dirs are
provisioned at build time; bump the loop in the Dockerfile for more).

### Reproducing a recorded game

Every game's seed is in `meta.json`. To re-run from a seed:

```bash
NETHACK_SEED=<seed> NETHACKOPTIONS=/opt/bothack/bothack.nethackrc \
  /nh343/nethack.343-nao   # play manually
```

…or to have the bot redo it:

```bash
/opt/runner/run_one.sh test-replay <seed> /tmp/replay-test
```

## Notes / caveats

- BotHack's ascension rate is ~5–15% per game on Valk-Dwa-Fem-Law — the
  defaults from `bothack.nethackrc`. Reaching 10 wins is hours to a day or
  two of wall-clock on a single container.
- The seed patch covers the *RNG only*. Game artifacts that read other
  external state (current date for bones, server flags) are not used in this
  setup (`!bones`), so a given seed reproduces the game faithfully.
- The replay UI loads the ttyrec into memory client-side. Practical for
  ttyrecs up to ~20 MB; bigger games may want streaming.
