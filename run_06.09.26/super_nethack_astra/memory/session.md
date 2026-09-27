# Expedition memory — Claude, reproduction pure à la Astra

Styles (registry: config/styles.json, shown in the dashboard tab Styles):
- tariru      = memory/tariru-style.md (slot 1 always; slot 6).
- astra       = memory/astra-style.md (original Astra method, no BotHack).
- tariru_v2   = tariru-style.md + memory/style-tariru-v2.md (hard HP/AC/depth targets).
- wish_abuser = start-scum on miniforum-worker (scripts/wish_scum.py) until a
  start offers a wish, then Astra: memory/style-wish-abuser.md.
The style of your slot is "style" in .runtime/slot-N.json: read its files
before playing. Assignment after a death (user plan 2026-09-27): target 2
games per style over the 8 slots; `python3 scripts/next_style.py N` gives the
next style (a slot playing a style in surplus takes the most-missing style,
otherwise it keeps its own). Slot 1 stays Tariru-family (tariru/tariru_v2).
Games in progress are never switched.
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

## Slots (8 games at once since 2026-09-27)

- Slot 1 = player Claude (journal memory/run-N.md), played by the main session.
- Slot 2 = Claude2 (memory/slot2-run-N.md), slot 3 = Claude3 (memory/slot3-run-N.md).
- Everything is selected by the env var NH_SLOT. Easiest: use the wrappers in
  slots/2/ and slots/3/ (k v t go fight look doors say explore runto flee route
  session) which export NH_SLOT for you. Slot 1 uses scripts/ directly.
- Never send keys to another slot's game. Do not edit shared files in scripts/
  or web/ (other games depend on them); note bugs in your journal instead.
- New game after a death: `NH_SLOT=N python3 scripts/session.py start`, then
  set "journal"/"run" in .runtime/slot-N.json and create the new journal file.

## Recording, dashboard, replay

- scripts/recorder.py (tmux session `recorder`) records every screen change of
  every slot into runs/games/<game_id>/frames.jsonl (+ meta.json, log.jsonl).
- scripts/dashboard.py (tmux session `viewer`) serves http://127.0.0.1:8766/ :
  tab Live (any slot) and tab Dashboard (3 live cards, replay with timeline,
  events, HP/depth chart, bookmarks, lessons, history of all games).
- `chronicle --importance 1-3 --kind item|monster|danger|progress|decision|death "Titre" "Explication"` (scripts/chronicle.py or slots/N/chronicle) = truly important moments, expandable on the dashboard; also feeds the "3 moments clés des 1000 derniers tours".
- `waitpet [n]` wait for the pet (stops on HP loss or adjacent monster). NEVER pass turns in a loop without an HP check.
- `say "texte"` (scripts/say or slots/N/say) = public AI commentary, shown live
  and as replay captions. Use it at every real decision, in French (but keep original English NetHack names for items and monsters: "plate mail", "master mind flayer", "wand of digging"..., and HP, Dlvl N, T1234, XL, AC, altar, fountain, shop, trap). scripts/nh_terms.py normalizes old texts.
- Old ttyrecs can be imported: scripts/import_ttyrec.py <ttyrec> <game_id>.

## Tools on miniforum-worker (user request 2026-09-27 13h)
Only the Claude agents run on the PC. Recorder, dashboard (tunnelled to
127.0.0.1:8766), and every game started from now on live on miniforum-worker
(same absolute path). `.runtime/where-N` = worker makes the slots/N wrappers
run there (scripts/slotrun); your own helpers in slots/N/ must be run with
`slots/N/w <command>`. scripts/worker_sync.sh (PC tmux `sync`) copies data
both ways. Games started on the PC finish on the PC (saves never move).
Do not edit .runtime/slot-N.json by hand for a worker slot.

## Heavy computation → miniforum worker (user rule, 2026-09-27)
Never run solvers/searches/analyses on this machine (8 games share 4 cores).
Use `slots/N/onworker [--timeout S] <command>`: copies slots/N to
miniforum-worker (~/nethack-compute/slotN), runs there (time limit, 8 GB cap),
copies results back. A watchdog kills local helper processes above 2.5 GB.

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
