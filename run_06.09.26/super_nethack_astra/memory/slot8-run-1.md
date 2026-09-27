# Emplacement 8, run 1 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md, obligatoire) : la méthode d'origine qui a gagné, sans BotHack.
Lire aussi les « Lessons » de memory/run-1..run-4, slot2-run-1, slot3-run-1.
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore).

## Current state
URGENT: T8830 SOKOBAN level 3 SOLVED, going to level 4 (top, prize). HP94(95) AC1 (small shield burnt) XL8 Fast. LAST PRAYER T6506 (safe now). Food: 2 food rations (z).
Wield a Excalibur (skilled long sword). Worn: c +3 small shield, x elven mithril-coat, S orcish helm (pet-tested). TELEPATHY.
 Hunger is the main problem: eat every safe corpse.
Wands: h ebony (engrave: no effect; opening/locking/probing/undead/nothing/striking). Rings: k ivory, N steel (unknown). e 2 scrolls FNORD (= earth, Sokoban).
Escape: v brass wand (tele/cancel/invis). q slow monster, y secret door det (several charges used), R light.
Pet: large dog. Daggers b, w, orcish U to throw. V ornamental cope = PROBABLY CURSED (dog avoided it 30 turns) - do not wear until uncursed. T orcish helm spare.
Oracle D7: '<' 57,14, '>' 65,22.
D8: '<' 41,25 (from D7), SOKOBAN '<' 19,14, fountain 47,16, boulder stuck 60,13; iron shoes carried by the dog somewhere.
X unicorn horn (works: cured hallucination T8376; BUC unknown, from gray unicorn kill T6679).

- D1: fountain 75,23; '>' 72,13. D2: '<' 36,14, main '>' 55,14, MINES '>' 13,17; fountain 33,28.
- Mines: D3 '>' 9,27; D4 '<' 69,15 '>' 52,25; D5 '<' 32,27 '>' 30,18.
- MINETOWN = Mines Dlvl 6: temple altar Odin (neutral) 39,18; Akalapi general store (49-51,24-26: sapphire ring 450zm = base 300, orange potion 300zm, carrot); tool shops ((( 48-50,16-17 and 30-32,25-26; fountains 34,21 and 44,21; '<' 14,15.
- Main D6: '<' 61,14, '>' 56,23 (fountain 18,15 used up by Excalibur).
- Main D3: '<' 30,23, '>' 7,14. D4: '<' 49,20, '>' 33,15. D5: '<' 45,23, '>' 28,14.
- IDs: q slow monster, y secret door detection, t oil lamp (blessed). Unknown potions: f emerald(unc), i orange(unc; shop base 200/150), n fizzy(unc), B cloudy, C dark green. Rings: N steel (unc? from box). Potions also M magenta, Q bubbly, K dark green (diff BUC from C). R = wand of light. Scrolls: A 4 unlabeled (blank), G ASHPD SODALG, J ASHPD SODALG (different BUC). Gems g white, j 2 orange, r 4 yellowish brown, s violet, u black.

## Lessons
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
