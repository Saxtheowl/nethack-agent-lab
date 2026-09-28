# Slot 8 — run 5 (Claude8, astra, lawful female dwarven Valkyrie, kitten)

## Current state
- T9505: zapped C (copper) at a boulder in Soko L4: boulder VANISHED -> C = probably WAND OF TELEPORTATION. Monkey stole S (create monster), dropped at 34,25 L4.
URGENT: T10139 left Sokoban, on D6 at soko-stairs; heading UP to D2 then Mines->Minetown temple. (T10036 SOKOBAN DONE (Dlvl2 soko top, closet 43,28). c = BAG OF HOLDING (Soko prize, unverified). $~3900 -> BUY PROTECTION from a LAWFUL priest (400*(XL+1) = 3600 at XL8, 4000 at XL9 - hurry). HP~70(81) AC5 (small shield EATEN by gel cube; need a shield) XL8 Fast. LAST PRAYER T9981 (next ~T11000). Wield EXCALIBUR. Worn m scale mail, N orcish helm. TELEPATHY. Wands: C TELEPORTATION (few charges?), Z make invisible, W zinc (unknown), S create monster. Food: z rations, G tripe, lichens. No stoning cure! Route out: L4 '>' 28,14 -> L3 '>' 37,25 -> L2 '>' 30,16 -> L1 '>' 39,19 -> D6; Mines branch D2 '>' 40,23.)

## Map
- D1: '<' 17,15, '>' 39,14; bear trap 16,14. No fountain.
- D2: '<' 10,19, MAIN '>' 30,13, MINES '>' 40,23, fountain 13,18 DRIED UP T4832 (2 dips, no Excalibur, sword very rusty), sink 62,14. Peaceful hobbit blocks corridors.
- D3: '<' 5,13, '>' 60,25 (dark SE room, yellow mold 58,27).
- D5 = ORACLE: '<' 64,15, '>' 16,15. Delphi fountains 40,20 41,21 40,22 (39,21 gone: EXCALIBUR T6740). Chain mail 62,27 (BUC?), tinning kit 15,17, crossbow 61,16. SOKOBAN = up stairs on D6.
- D4: '<' 50,13, '>' 29,24. Peaceful dwarf+gnome (digging).

## Items

## Lessons (this run)
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
