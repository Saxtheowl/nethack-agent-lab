# Slot 8 — run 5 (Claude8, astra, lawful female dwarven Valkyrie, kitten)

## Current state
- T9505: zapped C (copper) at a boulder in Soko L4: boulder VANISHED -> C = probably WAND OF TELEPORTATION. Monkey stole S (create monster), dropped at 34,25 L4.
URGENT: DEAD T13453 (Dlvl11 Big Room). Game over, screens closed. Next: new run (run-6).

## Map
- D1: '<' 17,15, '>' 39,14; bear trap 16,14. No fountain.
- D2: '<' 10,19, MAIN '>' 30,13, MINES '>' 40,23, fountain 13,18 DRIED UP T4832 (2 dips, no Excalibur, sword very rusty), sink 62,14. Peaceful hobbit blocks corridors.
- D3: '<' 5,13, '>' 60,25 (dark SE room, yellow mold 58,27).
- D5 = ORACLE: '<' 64,15, '>' 16,15. Delphi fountains 40,20 41,21 40,22 (39,21 gone: EXCALIBUR T6740). Chain mail 62,27 (BUC?), tinning kit 15,17, crossbow 61,16. SOKOBAN = up stairs on D6.
- D4: '<' 50,13, '>' 29,24. Peaceful dwarf+gnome (digging).

## Items

## Lessons (this run)
- T11486 read unknown scroll in a corridor = EARTH, boulders walled me in; prayer did NOT fix it (fixed something else). Escape: take off armor, drop all but Excalibur (weight<=100) -> 'you can squeeze' past boulders (straight moves only), push the far boulder away, return for items. Read unknown scrolls in a ROOM, not a corridor.
- T10576 Mines D4: meleed an AWAKE mountain nymph -> she stole wand of TELEPORTATION, orcish helm, shuriken, lichens, made me take off mail+shield, then teleported. Sleeping nymph (D3) died in 2 hits, awake one did not. NEVER melee an awake nymph: throw daggers from range / Elbereth / avoid.
- ZOO (Soko L4): a wood nymph in the zoo stole shield, wands, food via 'charm' in the doorway; a gelatinous cube then ATE my +3 small shield (wood) and other organics. Kill nymphs at range BEFORE opening a zoo; kill gel cubes before they reach item piles.
- HP 81 -> 11 in a few turns vs tiger+sphere at the zoo door: Elbereth + prayer saved me. Don't fight a zoo below 60% HP.
- grabat/tv then ',' picks up WHATEVER is under you if travel stopped early (picked a jaguar corpse -> Burdened). Check position first.
- Food: rations from old boxes can be rotten (1/7); prayer every ~1000-1050 turns for Weak worked 5 times (T1827, 2683, 3746, 4843, 5885).
- Dipping at D2 fountain rusted the sword twice then dried it; Oracle fountain gave Excalibur at XL6 (rust erased).

## Lessons (carried over)
- Stone/Slime: eat lizard FIRST; never loop a helper after a STOP without reading status.
- Never kick locked doors into unknown dark rooms. Food: keep 2+ rations, buy early.
- Excalibur: dip at XL5 in a NON-town fountain. Protection from co-aligned priest (400*XL gold at XL<=... ).
- Sokoban entrance = level below... actually up stairs on the level BELOW the Oracle (Oracle Dlvl+1).

## Sokoban: L1 solved T7682, L2 (2a) T8330, L3 (3b, nethackwiki) T8718, L4 (4a) holes filled T9900. Executor: slots/8/w soko5/run3.sh FROM TO plan.txt (travel+push, verifies). plan2.py computes plans.
## Sokoban L1 (Dlvl5 branch, variant soko4-1 "1a"), screen = map+(33,15)
Plan (my own, J sacrificed at (11,3)): sk 42 18 rr | 43 19 ddd | 42 24 l | 41 25 l | 43 25 llll | 42 23 dd ; 42 25 llll |
41 24 d ; 41 25 llll | 41 22 ddd ; 41 25 llllll ; 35 25 u | 43 22 ddd ; 43 25 llllllll ; 35 25 uu |
H 43 17 dddddddd ; 43 25 llllllll ; 35 25 uuuu ; 35 21 r | I 35 18 rrrrrrrr ; 43 18 ddddddd ; 43 25 l*8 ; 35 25 uuuu ; 35 21 rr |
G 35 17 d ; 35 18 r*8 ; 43 18 d*7 ; 43 25 l*8 ; 35 25 uuuu ; 35 21 rrr


## DEATH (T13453, Dlvl11 = Big Room, XL9, AC2, HP 86 max)
Killed by a Green-elf, in the Big Room, while praying (prayer too soon).
Sequence: arrived by stairs into the Big Room (full: troll, red naga, killer bees, 2 Green-elves, tengu, cockatrices...).
Dashed along the top wall toward '>' (19 squares away) -> got pinned at 29,14. A Green-elf had a WAND OF LIGHTNING:
one bolt blinded me and EXPLODED 3 wands (fire, slow monster, zinc) = ~45 dmg. HP 12 -> prayer OK (T13449, full HP).
One turn of troll+naga+bees+2 elves = -49. Elbereth: elves (@) ignore it; the troll hit anyway. Died -> AMULET OF LIFE SAVING
(the spherical amulet bought in Minetown) saved me. Lightning blinded me again (no scroll reading), zapped invisible, fled 1 step,
another lightning bolt -> HP 6, prayer 4 turns after the last one = too soon -> dead.

## Lessons (death run 5)
- BIG ROOM (Dlvl 10-12, lit, full of monsters): when you arrive and see 30+ monsters, GO BACK UP at once and come down
  later / by another way (or wait on the stairs and fight only what comes, with the '<' under your feet as an exit).
  NEVER leave the stairs to dash 19 squares across it.
- Fight ON the up-stairs when outnumbered: '<' is a one-key escape; monsters only follow if adjacent.
- A monster zapping lightning/fire: wands in main inventory EXPLODE (bag of holding protects them? no - put spare wands
  in the bag only if not cancellation). Kill wand-users first or break line of sight.
- Life saving is one-shot: after it triggers, treat HP as the only life left and LEAVE (stairs/teleport), don't stay 2 more turns.
- Keep an escape item usable WHILE BLIND: potion (not in bag), or wand of digging. Scrolls are useless blind.
  Don't put ALL potions in the bag: keep healing potions in main inventory.
- Unicorn horn + Elbereth do not stop @-elves; with 2 elves + troll adjacent, the only answer is to not be there.
