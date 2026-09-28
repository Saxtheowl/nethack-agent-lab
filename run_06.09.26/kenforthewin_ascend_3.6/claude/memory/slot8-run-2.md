# Emplacement 8, run 2 — journal (état le plus récent en haut)

## DEATH T4307, Mines Dlvl 5 (Orcish Town), XL6, 2140 pts: "killed by an Uruk-hai"
Chain: no food all game (only 1 ration + 2 cookies found; hunger ~1/turn + amulet). Went down the Mines for
Minetown/food; Mines Dlvl 5 was ORCISH TOWN (dozens of named orcs, shamans, poisoned arrows, orc-captain).
I held a 1-wide corridor and killed ~10 orcs (XL6), but poisoned arrows took me to 9 HP; kicked a boulder to
reach the 1/7 threshold and prayed at T4238 (full heal). Then orc-captain + Weak; Elbereth held the melee orcs,
but I FAINTED from hunger and an Uruk-hai hit me while unconscious (HP 7). Prayed again only 67 turns later
(too soon): helpless during the prayer, killed.

### Lessons (run 2)
- ORCISH TOWN: at the first named "X of Y" orcs / poisoned arrows, LEAVE via the up stairs immediately.
  Never fight an orc army at XL5-6 without poison resistance and food.
- Food first: with no food, do not go deeper; kill and eat fresh safe corpses right away (jackals, orcs,
  rats), keep 2+ rations; old corpses (>~50 turns) can be tainted = death.
- A failed/too-soon prayer leaves you helpless 3 turns next to monsters = death. Never pray within ~500
  turns of the last prayer unless there is no other option AND no monster adjacent.
- Fainting ignores Elbereth protection in practice (monsters hit you while you are out): fix hunger BEFORE resting on Elbereth.
- The dog/cat is precious: never detonate a gas spore next to the pet (killed my kitten T1775: -15 align, -1 Luck).
- Tools that worked: slots/8/play (auto-fight whitelisted weak monsters), elb/guardrest (Elbereth rewrite:
  send 'E' then 'lbereth'), kick-then-pray HP trick, darts at range for floating eyes/molds.


STYLE ASTRA (memory/astra-style.md, obligatoire). Lire aussi les « Lessons » de slot8-run-1.md (mort : mumak Dlvl 9).
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore). Stopper rest si Blind.
Outils perso : slots/8/ex (explore compact), sk/s4/sokoban8.py (Sokoban), hold (tenir un goulot), dip.

## Current state
URGENT: T4238 Mines Dlvl5 = ORCISH TOWN (dozens of orcs, poisoned arrows 10% instadeath/hit). HP59(59) AC0 XL6. LAST PRAYER T4238 (HP 6, well-pleased). Hungry, no food. Holding chokepoint (53,27) corridor, boulder 52,27 west.
Wield a +1 long sword; worn c +3 small shield, j uncursed +1 chain mail, f amulet of ESP. m 13 darts (throw at gas spores/molds from range 2+), b dagger.
Wands: q jeweled (engrave no msg). Scrolls: h identify, confuse monster known. i dark potion.
D1: '<' 75,20, '>' 41,18. D2: '<' 27,16, main '>' 49,22, MINES '>' 69,20. D3 main: '<' 40,27, '>' NOT FOUND (west room 1-7,12-17 via broken door 14,18).

## Lessons
- Prayer HP trick: trouble needs HP <= 5 or HP*7 <= maxHP; at HP just above, kick a boulder/wall (1-5 dmg) then pray. Worked T4238.
- Orcish Town (Mines 5-8 variant): huge orc band with poisoned arrows; don't wander in at XL5.
- Elbereth typed text: send 'E' then 'lbereth' separately (first char got mangled when sent in one burst).
- T1775: killed my OWN KITTEN with a gas spore explosion (dagger thrown at spore, kitten adjacent to it): alignment -15, Luck -1. Check pet position before detonating a gas spore. Avoid praying until alignment recovers (many hostile kills).
- Amulet adds hunger; food ration eaten T1627. No food left -> eat corpses.
