# The target game: NetHack 3.4.3 with the nethack.alt.org patchset

BotHack's own documentation is unambiguous:

> The only supported version of NetHack is 3.4.3 with the nethack.alt.org
> patchset, available here: http://alt.org/nethack/naonh.php
> — `doc/compiling.md` and `doc/running.md` of the original

and its shipped configs run `/nh343/nethack.343-nao`
(`config/shell-config.edn`).  That is what this repository builds and plays.

## What was fetched

| what | source | id |
| --- | --- | --- |
| BotHack | github.com/krajj7/BotHack | `70226b3` (2016-06-12, master) |
| NetHack 3.4.3-NAO | github.com/neoascetic/nh343-nao (mirror of `alt.org/nethack/nh343-nao.git`, which no longer resolves) | `d643449` (2014-11-03) |
| vanilla NetHack 3.4.3 | nethack.org/download/3.4.3/nethack-343-src.tgz | sha256 `bb39c3d2a9ee2df4a0c8fdde708fbc63740853a7608d2f4c560b488124866fe4` |

The NAO diff linked from `naonh.php` (`nh343-nao.diff`) now 404s and the
upstream git URL is gone, so the tree comes from a mirror.

## How it was checked

* `include/patchlevel.h` says VERSION_MAJOR 3, VERSION_MINOR 4, PATCHLEVEL 3 —
  it is 3.4.3, and the built binary prints `NetHack, Copyright 1985-2003`.
* Every distinctive NAO feature from the list on `naonh.php` is present in the
  source: `vt_tiledata`, `STATUS_COLORS`, `showborn`, `dumplog`, `livelog`,
  `WHEREIS_FILE`, menucolors, `msgtype`, `hilite_hidden_stairs`,
  `hilite_obj_piles`, `show_shop_prices`, `msg_wall_hits`, paranoid quit,
  `use_darkgray`, `hitpointbar`, sortloot, `quiver_fired`, `botl_updates`,
  `hp_notify`, `item_use_menu`, plus the curses windowport.
* The tree's own defaults are `HACKDIR "/nh343"` and
  `VAR_PLAYGROUND "/nh343/var"` — the exact paths BotHack's configs expect.
* The lex/yacc grammars (`util/*.y`, `util/*.l`) and the pre-generated parsers
  in `sys/share` are byte-identical to vanilla 3.4.3, so building with the
  shipped parsers (this host has no bison/flex) changes nothing.

## Why the bot's behaviour depends on it

BotHack's `bothack.nethackrc` reconfigures the display so that the screen is
unambiguous for a scraper, and the port relies on exactly the same mapping:
traps all show as `^`, monsters use the full letter set plus `@X';:~m`,
closed doors are `]`, sinks `{`, trees/bars/drawbridges `}` (told apart by
colour), graves `\`, boulders `8`, and `!legacy`, `!tombstone`, `!mail`,
`showscore` and `time` keep the status line in the shape both scrapers parse.
The NAO patchset matters for the same reason - e.g. the bot depends on NAO's
message when a diagonal move fails ("It's a wall.") to map walls it cannot
see (`actions.clj`, `Move`).
