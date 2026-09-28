# Slot 5 — run 5 (Wish1, wish_abuser, sur miniforum-worker)

URGENT: MORTE T3536 (Dlvl 2, large kobold pendant un évanouissement de faim). Partie terminée — ne pas relancer.

## État
- Wish T5 (water demon, fountain Dlvl 1, tentative 815 du start-scum) : blessed +2 gray dragon scale mail = magic resistance, portée T11.
- Inventaire : a +1 long sword, b dagger, c +3 small shield, d food ration, e GDSM.

## Règles héritées de run-4
- Lycanthropie : guérir tout de suite (prière, holy water, wolfsbane) ; "You feel feverish" → ENLEVER la GDSM.
- Porter amulettes/anneaux inconnus non maudits (BUC d'abord).
- Compter les charges des wands ; z, lettre, direction séparément.
- Combattre depuis les portes ; jamais de repos compté à côté d'un monstre.

## Carte
D1 : '<' 27,25, '>' 37,24, fountain 29,25, ALTAR NEUTRAL (Odin) 52,26.

## Lessons
D2 : '<' 32,23, '>' 45,15. GENERAL STORE (Upernavik) 2-10,23-26, porte 11,25 : Ch9 (+33%). copper wand 356 (base 200 : create monster/poly/tele/cancel), curved wand 267 (base 150/200), jeweled wand 200 (base 150), dwarvish mithril-coat 333, food ration 60, studded leather 20.
D3 : '<' 14,13, '>' 3,14, fountains 37,14 et 27,17, trap teleport 51,22.
D4 : '<' 8,15 (salle fermée, porte cachée 11,12), '>' 19,23 et '>' 43,24 (un des deux = Mines).
D5 : '<' 61,27, '>' 45,27, sink 60,27, fountain 71,15, boutique FERMÉE « Closed for inventory » porte 54,13.
- T2776 : prière trop tôt (1134 tours après T1642) → « Tyr is displeased » : Luck -3 + colère divine. Leçon : l'intervalle ~1000 n'est pas garanti (timeout rnz(350) peut être >1000).

## DEATH (T3536)
Tuée par un large kobold au Dlvl 2 (12,18), à 7 cases du general store, XL3, HP 0(31), AC -6, en état Fainted (famine).
Enchaînement : une seule food ration (mangée T757) ; prière pour Weak T1642 OK ; lichen + rothe ; Hungry T2683, Weak T2773 ;
2e prière T2776 (1134 tours après) → « Tyr is displeased » (trop tôt : Luck -3, colère) ; remontée D5 → D2 pour acheter une food ration
(66 zm) en Fainting : évanouissements de 20-30 tours ; un large kobold m'a frappée pendant les évanouissements (31 → 8 → 0).
Identifié à la mort : q = amulet of ESP, s = ring of fire resistance, p = potion of object detection, k = scroll of fire, m = identify,
n = BLESSED scroll of charging, i = spellbook of levitation. GDSM blessed +2 (wish T5).

## Lessons (mort)
- NOURRITURE = priorité n°1 dès le début : acheter la food ration du D2 dès qu'on a 60 zm (j'en avais 66 à T2808, trop tard), garder 2+ rations, ramasser TOUS les corpses sûrs (newt, jackal, rothe) et manger dès Hungry. Ne jamais descendre sans réserve.
- La prière « tous les ~1000 tours » n'est PAS sûre : le timeout après une prière réussie est rnz(350), parfois >1000. Une prière de faim ratée = Luck -3 + colère divine = plus aucune prière. Ne pas compter sur la prière comme seule source de nourriture.
- Dès Weak sans nourriture : agir tout de suite vers la source la plus proche (je suis restée ~90 tours à explorer D5 en Hungry/Weak au lieu de remonter au shop).
- Fainting : chaque tour ~45 % d'évanouissement de 20-30 tours ; n'importe quel monstre lent (speed 6) tue pendant ce temps malgré AC -6. Avant de marcher en Fainting, graver Elbereth ou éliminer les monstres visibles.
- Le travel `_` prend parfois de longs détours (D3 : par la salle du bas) : en urgence, suivre le couloir case par case.
- explore.py s'arrête souvent sur « no reachable frontier » juste après « The door opens » : franchir la porte à la main puis relancer.
