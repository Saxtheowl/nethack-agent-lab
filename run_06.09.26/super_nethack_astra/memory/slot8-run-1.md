# Emplacement 8, run 1 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md, obligatoire) : la méthode d'origine qui a gagné, sans BotHack.
Lire aussi les « Lessons » de memory/run-1..run-4, slot2-run-1, slot3-run-1.
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore).

## Current state
URGENT: T6507 Dlvl7 (ORACLE level) HP66(66) AC0 XL6. LAST PRAYER T6506 (Weak; prayers T1063,T2306,T4334,T6506). Next safe ~T7600.
Wield a Excalibur (skilled long sword). Worn: c +3 small shield, x elven mithril-coat, S orcish helm (pet-tested). TELEPATHY.
Food: I lichen corpse, P 2 tripe rations. Hunger is the main problem: eat every safe corpse.
Escape: v brass wand (tele/cancel/invis). q slow monster, y secret door det (several charges used), R light.
Pet: large dog. Daggers b, w, orcish U to throw. V ornamental cope = PROBABLY CURSED (dog avoided it 30 turns) - do not wear until uncursed. T orcish helm spare.
Oracle D7: '<' 57,14, '>' 65,22. Next: D8 has Sokoban '<'.

- D1: fountain 75,23; '>' 72,13. D2: '<' 36,14, main '>' 55,14, MINES '>' 13,17; fountain 33,28.
- Mines: D3 '>' 9,27; D4 '<' 69,15 '>' 52,25; D5 '<' 32,27 '>' 30,18.
- MINETOWN = Mines Dlvl 6: temple altar Odin (neutral) 39,18; Akalapi general store (49-51,24-26: sapphire ring 450zm = base 300, orange potion 300zm, carrot); tool shops ((( 48-50,16-17 and 30-32,25-26; fountains 34,21 and 44,21; '<' 14,15.
- Main D6: '<' 61,14, '>' 56,23 (fountain 18,15 used up by Excalibur).
- Main D3: '<' 30,23, '>' 7,14. D4: '<' 49,20, '>' 33,15. D5: '<' 45,23, '>' 28,14.
- IDs: q slow monster, y secret door detection, t oil lamp (blessed). Unknown potions: f emerald(unc), i orange(unc; shop base 200/150), n fizzy(unc), B cloudy, C dark green. Rings: N steel (unc? from box). Potions also M magenta, Q bubbly, K dark green (diff BUC from C). R = wand of light. Scrolls: A 4 unlabeled (blank), G ASHPD SODALG, J ASHPD SODALG (different BUC). Gems g white, j 2 orange, r 4 yellowish brown, s violet, u black.

## Lessons
- SOKOBAN entrance = level BELOW the Oracle (dungeon.def: "oracle" + (1,0) up). Oracle = D7 here -> Sokoban '<' on D8. Wasted ~800 turns searching D6.
- Never run scripts/session.py without NH_SLOT=8 (it shows slot 1).
- Gray ooze: never melee (rusts weapon) nor kick at low HP: its bite did 11. Throw daggers, then leave (speed 1).
- Rothes: fight them from a doorway (one at a time).
- Hunger comes fast: prayed for Weak at T1063. Food ration can be rotten (T1803).
- Chests/boxes can be trapped (gas: stun+hallu). After a trap message, Escape before other keys ('o' became Open).
- Travel/go refuse with peaceful gnomes adjacent: use slots/8/runto X Y n.
