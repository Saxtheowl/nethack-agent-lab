# Expedition memory — Claude, reproduction pure à la Astra

Read this file first at every session / after every context compaction, then
`memory/run-1.md` (latest state at the TOP), then inspect the real screen.

## Goal and rules (user request 2026-09-27)

Reproduce kenforthewin/nethack_astra locally: an LLM (me, Claude Code) plays
NetHack 3.6.7 key by key until ascension, and the user watches from this PC.

PURE rules — never break them:
- Vanilla NetHack 3.6.7 built from the official tarball (engine/), no patch,
  no wizard/explore mode, no bot, no assist.
- No save-scumming: never copy/restore save files, never edit game files.
  Saving (`S`, `y`) only to pause; the next `start` restores the same game.
- On death: write the lesson in the run journal, start a new run (run-N+1).
- Spoilers, wiki, source code: allowed (as for Astra). Game internals of the
  running process (RNG, unknown map): never.
- Helper scripts allowed and encouraged (guard, route, sokoban) as for Astra.

## Controls

- `python3 scripts/session.py screen [--compact]` — observe.
- `python3 scripts/session.py keys --compact --why 'reason' <keys>` — act.
  Movement digit strings (e.g. `6666`) go through guard.walk (checked steps).
  `--named Escape` / `--named Enter`. `--raw` only for reviewed menu input.
- number_pad:1 → 7 8 9 / 4 6 / 1 2 3 are moves; `k` = kick; `F`+dir fights.
- Curses `>>` / --More-- need Space. Menus: Escape to cancel.
- `start` restores the saved game (player Claude). `attach` = read-only tmux.
- `note 'text'` updates viewer commentary.

## Recording / watching

- Viewer: http://127.0.0.1:8766/ (tmux session `viewer`, `session.py viewer`).
- Live: `tmux -S /tmp/nhstream-*.sock attach -r -t nethack`.
- Every `start` writes `runs/<UTC stamp>.ttyrec` (ttyplay). Ledger:
  `runs/ledger.jsonl` (hash-linked, `python3 scripts/audit.py` verifies).
- Dumplogs: `runs/dumplog/`. xlogfile: engine/install/games/lib/nethackdir/xlogfile.

## Character

Claude, lawful female dwarven Valkyrie (same as Astra). Run 1 started
2026-09-27, T:1, full moon (lucky).
