# Emplacement 8, run 1 — journal (état le plus récent en haut)

## DEATH T10741, Dlvl 9, XL8, 10007 pts: "killed by a mumak"
Chain: arrived on Dlvl 9 Hungry, a Green-elf threw daggers; while I fought toward it a MUMAK (q, butt 4d12 + bite 2d6)
came in: 95 -> 47 -> 16 HP in ~4 turns. Fled into a small room (door 50,24), dust Elbereth on 50,25, verified with ':'.
Killed the Green-elf (@ ignores Elbereth) from the square, rewrote Elbereth, prayed for Weak at T10675, rested.
Then I got BLIND (unknown cause) while resting: rest's ':' check says "You feel no objects" instead of reading
the engraving, so it kept re-engraving while the mumak stood in the doorway; two butts took me from 67 to 0.
Had: Excalibur (expert), elven mithril, telepathy, unicorn horn, lizard corpse; Sokoban 1-3 solved, L4 blocked by a mimic.

### Lessons (run 1)
- A mumak/other big hitter on a level: LEAVE the level (stairs were 12 squares away) instead of resting on dust
  Elbereth next to it. Elbereth scuffs every time it scares, and resting there is a gamble.
- Farlook every glyph before engaging: I chased a Green-elf and never looked at the 'q' coming.
- Resting script: stop immediately when Blind (it cannot read dust engravings blind) and apply the unicorn horn.
- AC 1 is not enough for Dlvl 9+ melee monsters; get AC <= -3 (iron shoes, cloak, better shield) before Dlvl 8+.
- Food was the main problem all game: prayed 5 times for Weak. Pick up every food item; eat safe corpses.
- Sokoban: follow the nethackwiki solution from the very first push; a static '0' in the hole row may be a mimic.


STYLE ASTRA (memory/astra-style.md, obligatoire) : la méthode d'origine qui a gagné, sans BotHack.
Lire aussi les « Lessons » de memory/run-1..run-4, slot2-run-1, slot3-run-1.
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore).

## Current state
URGENT: T10215 SOKOBAN level 4 (Dlvl4, top) HP85(95) AC1 XL8 Fast, Expert long sword. LAST PRAYER T10675 (Weak; next safe ~T11700). 
Wield a Excalibur. Worn: c +3 small shield (burnt), x elven mithril-coat, S orcish helm. TELEPATHY. No poison/fire res known.
Food: z 2 food rations, m 2 candy bars, I slime mold, P tripe, L LIZARD CORPSE (stoning cure).
Wands: v brass = cancellation OR make invisible (zap at mimic did nothing visible); h ebony = PROBING (now empty: "Nothing happens"); H ebony = probing too; l tin (engrave: no msg); q slow monster; y secret door det; R light.
X unicorn horn (works). Y iron shoes (BUC unknown, from Uruk-hai), V ornamental cope (probably cursed). Rings: k ivory, U ivory (diff BUC), p iron, N steel, F granite (unknown). Scrolls: e 2 FNORD (earth), A 4 blank, G/J ASHPD SODALG. Many unknown potions.
Escape: none reliable! (no teleport). Gold 301.

SOKOBAN L4 STUCK: holes 47(under mimic),48,49,50 left. A GIANT MIMIC (46 HP, ~17 left) sits on hole 47 at (47,14) behind my boulder at (46,14); it cannot move (Sokoban monsters avoid holes). Thrown junk mostly misses. Remaining boulders: A (30,18), E (38,18), O (30,25), Q (36,25) (+ the one at 46,14). Come back with daggers/wand of striking or force bolt (breaking the 46 boulder = -1 Luck only) to kill the mimic, then finish (prize: bag of holding or amulet of reflection).
Soko levels: L1=Dlvl7 (branch from D8 '<' 19,14), L2=Dlvl6, L3=Dlvl5, L4=Dlvl4 ('>' at 28,14).

- D1: fountain 75,23; '>' 72,13. D2: '<' 36,14, main '>' 55,14, MINES '>' 13,17; fountain 33,28.
- Mines: D3 '>' 9,27; D4 '<' 69,15 '>' 52,25; D5 '<' 32,27 '>' 30,18. MINETOWN = Mines Dlvl6: temple altar Odin (neutral) 39,18; general store 49-51,24-26; '<' 14,15.
- Main D3 '<' 30,23 '>' 7,14. D4 '<' 49,20 '>' 33,15. D5 '<' 45,23 '>' 28,14. D6 '<' 61,14 '>' 56,23. D7 ORACLE '<' 57,14 '>' 65,22. D8 '<' 41,25, Soko '<' 19,14, fountain 47,16.

## Lessons
- Sokoban: a '0' that doesn't move may be a GIANT MIMIC. Probe/farlook suspicious boulders; never leave a boulder between you and a stuck monster in the hole row.
- Monsters that fall into a Soko hole reappear on the level below (the gnome king did).
- Soko L3 = 3b: wiki solution worked exactly. Hold chokepoints with slots/8/hold X Y DIR n minHP.
- h ebony wand: zapped at locked door, nothing -> locking/probing/undead turning/nothing.
- Soko L2 (2b): follow the nethackwiki solution exactly from the start; my greedy solver pushed P (29,24) up and locked P/H/F. Brute-force solver too slow for 15+ boulders.
- Rings found: k ivory, p iron, N steel, F granite (unknown).
- Sokoban: never throw items into a hole square - boulder filling buries them. Kill with melee or from another line.
- Sokoban tools: slots/8/sk X Y pushes [--hidden-hole X,Y] (slots/8/sokoban8.py: stops only for monsters within 3).
- SOKOBAN entrance = level BELOW the Oracle (dungeon.def: "oracle" + (1,0) up). Oracle = D7 here -> Sokoban '<' on D8. Wasted ~800 turns searching D6.
- Never run scripts/session.py without NH_SLOT=8 (it shows slot 1).
- Gray ooze: never melee (rusts weapon) nor kick at low HP: its bite did 11. Throw daggers, then leave (speed 1).
- Rothes: fight them from a doorway (one at a time).
- Hunger comes fast: prayed for Weak at T1063. Food ration can be rotten (T1803).
- Chests/boxes can be trapped (gas: stun+hallu). After a trap message, Escape before other keys ('o' became Open).
- Travel/go refuse with peaceful gnomes adjacent: use slots/8/runto X Y n.
