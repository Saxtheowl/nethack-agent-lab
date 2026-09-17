# Development log — bugs found by playing, and their fixes

Each entry: how it showed up (game id / detector), root cause, fix, how it is
guarded now.  Newest last.

## Interface / engine

1. **Object names in `hello` were all "strange object"** (boulders rendered as
   `` ` ``, bot pushed a "desired item" forever, `runs/dev/g011`).  `hello` is
   sent from `init_nhwindows`, before `init_objects()` sets `oc_name_idx`.
   Fix: read the static `obj_descr[]`.  Guard: `tests/test_bridge.py`
   (boulder renders as `8`, from a captured hello table).
2. **Protocol fds closed by `close_fds`** when dup2'ed in `preexec_fn`.
   Fix: pass the real pipe fds through `NH_BOT_IN_FD/NH_BOT_OUT_FD`.
3. **`!verbose` option shortened prompts** ("Dip it into the fountain?"),
   BotHack did not recognise them and a fallback answered `n` 1050 times
   (`runs/mt-s02/g001`, caught by the request-storm detector).  Fix: keep
   `verbose` on; the dip regex also accepts the short form.
4. **Display-only menus were not dispatched**: 3.6 shows "Current skills"
   as a PICK_NONE menu; BotHack clears its `can-enhance` flag only when it
   sees that menu, so it typed `#enhance` forever (`runs/mt-s01/g001`,
   action-loop detector).  Fix: `menu_show` events are dispatched by title
   like the scraper did.

## 3.6.7 interaction differences (compat36)

5. **Container menu** "Do what with the large box?" replaced 3.4.3 yes/no
   questions (loot loop, first game).  Translated into BotHack's
   `take_something_out` / `put_something_in` answers.
6. **Empty container**: 3.6 puts "Your bag is empty." inside the menu prompt,
   3.4.3 printed a message that BotHack uses to empty its record of the
   container; it re-applied the bag forever.  The translation now emits that
   message.
7. **Object names**: "containing N items", "empty", "locked/unlocked/broken",
   "(at the ready)", "(in quiver pouch)", shop suffixes — the kit's bag of
   holding was unparseable and dropped as junk on turn 3.  Normalised before
   `ITEM_RE`.  Guard: `tests/test_compat36.py`.
8. **Messages**: "You open the bag..." (3.4.3 "carefully open"), locked
   containers, legs, remove curse, "What a pity--".  **Regression found**:
   the first "locked container" pattern also matched "This door is locked."
   and hid locked doors from BotHack (open-door loop, `runs/dev-s01/g002`).
   Pattern restricted to containers; regression test added.
9. **`#name` menu** "What do you want to name?" (m/i/o/f/d/a) vs NAO's
   (b = individual, c = type): 2593 unknown-prompt fallbacks in
   `runs/mt-s01/g003`.  Translated.
10. **Shop prices**: 3.6.7 `get_cost`/`set_cost` accumulate a
    multiplier/divisor and round once; BotHack's table modelled 3.4.3's
    successive integer divisions, so observed prices excluded every candidate
    identity ("unknown itemtype for item scroll labeled ..."). Table
    regenerated from the 3.6.7 formula; tested.

11. **16 new random scroll labels** in 3.6.7 (`SCROLL(None, "ZLORFIK", ...)`)
    and the "leathery" spellbook: BotHack could not classify them ("unknown
    itemtype"), wanted them and never picked them up — the bot walked back
    and forth to a scroll for hundreds of turns (Medusa scenario).  Found the
    complete list with `tools/objects_appearances.py` (balanced macro
    parsing; a first regex diff had missed them); patched the item data at
    load.  Tested.
12. **"Continue eating?"** (3.6.7) inverts 3.4.3's "Stop eating?": the
    default "stop" answer would have meant "continue".  Translated, tested.
13. **Dip prompt with an article** ("Dip a blessed +1 long sword ... into
    the fountain?"): BotHack's regex expected "the"; 46 fallbacks and an
    Excalibur loop (`runs/mt-s03/g001`).  Regex widened; tested with real
    prompt texts.
14. **Pickup menu labels**: labels were stored normalised, menu entries are
    verbatim, so PickUp never matched (`runs/mt-s02/g002`, 2111 fallbacks).
    `label` keeps the game's text, only parsing is normalised.  Tested.
15. **Medusa variants 3 and 4** (3.6.7) were not recognised; `below-medusa`
    stayed false and the bot wanted to explore up to Dlvl 20.  Added a
    recognition from the seen map (mostly water on Dlvl 21-28, trees vs iron
    bars for the variant).

## 3.6.7 rules (rules36)

- Pudding farming disabled; `farm-done?` keeps only "wiztower known".
- Elbereth strict text, not in Gehennom/planes, never attack a
    respecting monster from the square, no "engrave then fight", prayer
    blocked after "You feel like a hypocrite.".
- Prayer threshold `critically_low_hp()` ported and tested.

## Tactics and progression (declared, recorded in every manifest)

* `--tactics assisted` (default when invincibility is on): BotHack's retreat
  (flee upstairs, pray/Elbereth for HP) and resting are not registered —
  under invincibility they only waste time; in the Medusa scenario the bot
  fled upstairs from 30 ravens and then wandered back up the dungeon.
* `--profile fast`: no Mines/Sokoban detours, no backtracking to finish
  shallower main levels.
* `BOTHACK_SKIP` (scenarios): skip full-explore steps to test one stage.

## Supervision

16. **A recovery hid the loop it was meant to break**: the no-turn-progress
    recovery forces a search, which advances the turn and reset the detector
    (15 000 requests at turn 50).  Added the *request storm* detector (3000
    requests for < 30 turns, independent of recoveries).
17. **Action loop** (same action, same position, same turn): first recovery
    blocks the target square for path finding, then abort after 40.
18. **Death loop** under invincibility (lava/water/gaze): 150 assisted
    lifesaves within 300 turns without progress (stage, depth, XL, new
    square) aborts as stuck (first version: 25, too strict for fights).

## Performance

17. BotHack computed the exploration cache synchronously every decision
    (the original used a Clojure future): 60% of the time.  Lazy, then
    `explorable_tile` memoised on tile identity (tiles are persistent),
    `unlockable_chest` test order, hashed-key memo, hoisted imports:
    218 s → 80 s for the same 250 requests under the profiler.


## Castle series and endgame scenarios (2026-09-17)

Series `ca-w04`/`ca-w05` (14 games, seeds 5001-5014, goal Castle, worker)
and the prepared Astral scenarios.

* **Look window lost the dungeon feature**: with objects on a square, 3.6
  puts "There is an altar to Moloch (unaligned) here." at the top of the
  "Things that are here:" window; BotHack only parsed the items, reset the
  square to `floor` and engraved on the altar forever ("You make a motion
  towards the altar", `ca-w05/g010`, fixation detector).  Feature lines of
  the window are parsed now.
* **engrave-id on a non-engravable square**: when no engravable square was
  reachable BotHack engraved where it stood; guarded by `engravable()`.
* **"high altar"**: 3.6 says "There is a high altar to Tyr (lawful) here."
  on the Astral Plane/Sanctum; the alignment was not parsed and the bot
  walked away from its own god's altar (`scen/astralalt01`).  Tested.
* **Missing monsters**: Keystone Kops, Twoflower and the tourist quest guide
  were absent from BotHack's data; farlook raised "Failed to parse monster
  description: Kop Kaptain" and the same Kop was examined 40 times
  (`ca-w05/g012`).  Added; a test checks every monster of the 3.6.7 table.
* **Novel** ("paperback book", new object): unknown type, so its map glyph
  was never remembered and the shop square became "new items" each time
  the hero left it (`ca-w05/g011`).  Added as an `other` item.  Tested.
* **Stack price divided twice**: `normalize_label` already gives the unit
  price of a 3.6 shop stack, the price-identification handler divided it by
  the quantity again, eliminating every candidate ("unknown itemtype for
  item sky blue potion").  Tested.
* **Floor food prompt without price**: "There is a rabid rat corpse here;
  eat it?" has no "(no charge)" in 3.6; the eat handler compared it with the
  shop label and answered `n` forever (`ca-w04/g011`).
* **"You harmlessly attack a boulder."** (3.6 hack.c) was not understood as
  "no monster there": F-fight against a boulder where a monster had been
  remembered (`ca-w04/g004`).
* **Boulder with an unseen monster behind it** ("Perhaps that's why you
  cannot move it."): no time passes, 40 identical moves.  The square is
  avoided for 30 turns (`move-blocked`), also set by the action-loop
  recovery (which only blocked squares holding a monster before).
* **Action-loop signature** now includes the farlook position: examining 40
  different telepathically seen monsters in one turn is not a loop.
* **Astral Plane branch** was only set when arriving through the Water
  portal; a level-teleported hero (scenario) was "main" and never looked for
  the altars.  Set from the status line.
* **Astral drive under assisted tactics**: fight has priority over progress
  and the bot fought the crowd around the arrival point.  With the Amulet,
  `assisted_astral_rush` (before fight) heads for the three fixed altar
  squares of `astral.des` that are not known to be cross-aligned (the
  temples are dark; generic exploration pushed boulders in vain), applies
  the unicorn horn against stun/confusion/blindness at most every 3 turns.
* **Death-loop detector**: a newly occupied square counts as progress (slow
  advance through the Astral crowd), and the limit is 150 lifesaves / 300
  turns.

### Invincibility assist refinements (engine, logged)

* `savelife()` makes the hero helpless for a turn; a crowd killing every
  turn made the invincible hero unable to act at all.  The assist does not
  cost the turn.
* Sliming polymorphs the hero into a green slime (destroying armor) *before*
  `done()`; the lifesave cannot give the armor back.  `assist_noslime`
  cures the sliming when its timer runs out (event `noslime`).
* Repeated undone deaths also drain levels and maximum HP (Death's touch,
  level drainers); the hero ended at XL1 with 10 HP.  Lifesave now restores
  levels up to `u.ulevelmax` and max HP to the highest seen
  (`restored_levels`, `restored_hpmax` in the event).
