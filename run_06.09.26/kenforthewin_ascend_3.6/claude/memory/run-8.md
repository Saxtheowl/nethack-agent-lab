# Run 8 (emplacement 1) — journal (état le plus récent en haut)

STYLE TARIRU (memory/tariru-style.md). Lessons run-4..7: jamais de boucle sans seuil HP
(brawl N MINHP / shoot / hit) ; <50% HP vs monstre rapide = wand/Elbereth/fuite d'abord ;
lycanthropie = urgence (prière/holy water/wolfsbane) ; aveugle + monstre invisible = partir ;
fire ants/nymphs/monkeys à distance ; 2+ food rations (1 ration/800 T).

URGENT: PARTIE TERMINÉE — mort T5385 Dlvl10 (Big Room), XL5, 2084 pts, "killed by a winter wolf cub, while helpless".

## DEATH T5385, Dlvl 10 (Big Room), XL5, 2084 pts: "killed by a winter wolf cub, while helpless"
Chaîne: Dlvl9 T5160 human mummy + rabid rat (HP 15) → scroll of teleportation x ; Elbereth + repos ;
une GIANT SPIDER arrive pendant mon script `wait` (n5s = 5 tours entre deux contrôles HP) → HP 9 ;
2e scroll de teleportation (J, BUC inconnu = CURSED) → level teleport en Dlvl10 = BIG ROOM pleine
de monstres (4 winter wolf cubs, tengu, straw golem, dogs, mummy, yellow light...). Potions de soin
toutes bues, Elbereth tenu (le froid ne me touche pas : Valkyrie cold res). Mon helper `hold`/`elb`
a envoyé E puis, un popup étant affiché, le '-' a été refusé : NetHack a demandé l'outil, et la
suite de touches a choisi la DAGUE → gravure longue (helpless) au milieu des cubs → mort.
Lessons:
- JAMAIS de script qui envoie E sans vérifier CHAQUE prompt : "write with?" doit recevoir '-' et
  uniquement '-'. Si un popup/--More-- est à l'écran, le dissiper d'abord. Graver avec une arme =
  plusieurs tours sans défense.
- Boucles de repos : 1 tour par pas (s), pas n5s/n10s, quand un monstre peut arriver.
- Un scroll de teleportation de BUC inconnu peut être cursed = level teleport vers pire (Big Room).
  En urgence, préférer le scroll dont le BUC est connu (uncursed) ou tester sur un altar avant.
- Food : ~1 nutrition/tour ; les food rations anciennes peuvent être "rotten" (moitié). Il faut une
  vraie source de nourriture (acheter, cadavres systématiques) dès Dlvl1-4.
- Pick-axe inconnu : tester le BUC (altar/pet) AVANT de l'appliquer (soudé 3600 tours).
- Nymphs : les tuer à vue ; elles volent aussi l'armure portée.

## Plans
- Dlvl1-4 : explorer, trouver daggers/armure, Sokoban entrée (Oracle-1) plus tard.
- Mines → Minetown (protection 400×XL, altar curse-test), puis Sokoban.

## Journal
- T1-800 Dlvl1: leather armor (pet-testée), potions cloudy/milky, scrolls STRC/FOOBIE, spellbook turquoise, red+white gems, chest forcé à la dague.
- T519 bear trap → HP3, jackal → prière T559 réussie.
- T742 pick-axe sur arrow trap ; T1374 appliqué = CURSED, soudé. Weak à T858 (normal : 1 nutrition/tour).
- T2048 prière (Weak). T2372 prière (coyote, HP5). Scroll identify → light. T3050 prière (hobgoblin, HP5).
- T3400-3600 Dlvl5-6: rothes (tués aux daggers), XL4. Creusé Dlvl6→7. Altar lawful Dlvl7, 2 large box + chest (identify ×2, teleportation ×2, potions).
- T4195 wood nymph : shield/leather/towel volés ; tuée au pick-axe (chase), tout récupéré sauf la leather armor. Sacrifice nymph → clover (timeout 0) ; prière T4308 sans effet sur le pick-axe.
- XL2 T1586 (goblin). Autopickup coupé (ramassait des rocks).

## Lessons
- Une nymph adjacente au détour d'un couloir sombre = vol immédiat. Dans les couloirs sombres, avancer avec prudence quand on a des objets précieux ; tuer toute n dès qu'elle est visible (chase n / thr).
- Les nymphs ramassent les daggers lancés (M2_COLLECT) : ne pas lancer tout son stock sur une nymph.
- Prière "well-pleased" ne fixe les troubles mineurs (objet cursed soudé) qu'avec assez de Luck/alignement : ne pas compter dessus.
- Se reposer (search) dans un couloir sans Elbereth = les monstres errants arrivent (imp, hobgoblin) : HP 41→5. Se reposer sur un Elbereth vérifié, près de l'escalier.
- Un monstre en fuite sur Elbereth peut quand même frapper s'il est adjacent (hobgoblin T3040).
- Ne JAMAIS appliquer/brandir un outil-arme non testé (pick-axe) : le curse le soude. Tester avec le pet d'abord (il l'avait vu ? non).
- scripts/explore marque « dead » des cibles bloquées par le kitten : j'utilise slots/1/xplore.py (cache local, oublie les dead simples).
