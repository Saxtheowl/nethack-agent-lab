# Run 9 (emplacement 1) — journal (état le plus récent en haut)

STYLE TARIRU (memory/tariru-style.md). Règles anti-mort (runs 4-8) :
1. Jamais de boucle sans contrôle HP à CHAQUE tour : repos = slots/1/sw N [TARGET] (1 's' par tour,
   stop perte HP / monstre à <=6 / message). Plus de n5s/n10s. slots/1/wait et srest = NE PAS utiliser.
2. Aucun objet de BUC inconnu en crise (pick-axe soudé run 8, scroll teleport cursed run 8). Test altar/pet AVANT.
3. Elbereth à la main : E, '-', n si "add?", Elbereth, Enter, puis ':' pour relire.
4. Food : 1 ration / 800 T ; manger les cadavres frais sûrs ; garder 2+ rations.
5. Nymphs/monkeys/leprechauns : tuer à distance à vue.
6. Consolider Dlvl1-4 jusqu'à AC<=3 et XL>=5 avant les Mines.

URGENT: PARTIE TERMINÉE — mort T6539, Mines Dlvl9, XL8, 8156 pts (meilleur score slot 1), « killed by a succubus, while praying ».


## DEATH T6539, Gnomish Mines Dlvl 9, XL8, 8156 pts: "killed by a succubus, while praying"
Chaîne : retour à Minetown (Dlvl8) pour remonter vers le donjon principal. Près de la fontaine :
wolf + small mimic + succubus, puis le LEOCROTTA (déjà rencontré au même endroit à T6195) :
HP 50 → 18 en un tour. Prière impossible (dernière T6274, 255 tours avant). Trou à la wand of
digging vers le bas → Dlvl9, mais la SUCCUBUS adjacente m'a suivi dans le trou (HP 15).
Elbereth gravé et relu : elle fuit, puis frappe quand même (monstre en fuite coincé) et
l'engraving se dégrade (« El|e?etn »), HP 10. Prière trop tôt (timeout rnz(350) − 263 tours) :
pas de lumière, la succubus me tue pendant la prière.
Inventaire identifié à la mort : wand of fire (0:3) — il restait 3 charges ! — wand of polymorph
(0:3) (le glass wand), wand of digging (0:0) (vide), amulet versus poison, jumping boots,
potions : see invisible, 2 confusion, blindness (blessed), 2 gain ability (!), object detection ;
scroll = identify (cursed). 4 green gems.
Lessons:
- Ne JAMAIS retraverser une zone où rôde un monstre qui m'a déjà mis à 15 HP (leocrotta à Minetown)
  sans plan : j'aurais dû creuser vers le haut ? (impossible) → attendre la prière disponible
  (~1000 tours) ou partir par un autre chemin. Avec AC6 à XL8, Minetown Dlvl8 est trop dur.
- Après une prière, pendant ~1000 tours je n'ai plus de filet : jouer beaucoup plus prudemment
  (rester près d'un escalier, ne pas explorer de nouvelles zones).
- La wand of fire avait encore 3 charges : à HP 10 face à une succubus, zapper le feu (6d6)
  valait mieux qu'une prière à 62 %. Compter les charges : engrave-ID = 1 charge.
- Tomber dans un trou avec un monstre adjacent : il peut suivre. S'éloigner d'abord d'une case,
  ou graver Elbereth AVANT de creuser.
- Un Elbereth n'empêche pas un monstre en fuite coincé de frapper, et chaque coup reçu peut
  l'abîmer : relire ':' à chaque tour quand un monstre est adjacent.
- AC reste le problème n°1 (AC6 à XL8, Dlvl8-9) : Tariru vise AC ≤ 3 avant Minetown. J'aurais dû
  retourner au donjon principal (Sokoban) au lieu de rester dans les Mines profondes.
- Les unknown potions valaient le coup d'être testées plus tôt (2 gain ability !).

## Plans
- T4650 : remonter Dlvl5 → Dlvl4 est ; dans la salle du > (65,26) zapper digging vers l'ouest (4) pour percer jusqu'à la salle du < (53-60). Récupérer le kitten, explorer Dlvl4 ouest et Dlvl3 est → entrée des Mines → Minetown.
- Explorer Dlvl1-4 avec le kitten, ramasser daggers/armure, BUC-test (pet/altar).
- AC<=3, XL>=5 → Mines → Minetown (protection 400×XL) → Sokoban.

## Journal
- T1 : dwarven Valkyrie, kitten, full moon (lucky).
- T1-890 Dlvl1: lock pick, ivory ring g, dark potion f, scroll PRATYAVAYAH i. Lichen mangé T815.
- T1033 Dlvl2 Weak → prière réussie (Tyr pleased).
- Dlvl2: orcish helm + mud boots (pet-testés) → AC4. Dlvl3: food ration, chest → food ration + WAND OF FIRE (Elbereth brûlé 53,25), shop fermé 73,18 (« closed for inventory »). XL2 (green mold aux daggers).
- Dlvl4: floating eye tué aux daggers (pas de cadavre). Hobgoblin a lu un scroll of earth → boulders bloquent 62-63,20-22 ; kitten perdu à l'ouest.
- T5800-6310 Minetown Dlvl8 (Loki). Lizard corpse, rust monster (mangé), wolves+quasit+LEOCROTTA → HP 15 → digging vers le bas → Dlvl9 ; Elbereth, stone giant frappe quand même (boulder sur ma case) → HP 10 → PRIÈRE T6274 OK ; giant tué et mangé (St+). 4 green gems.
- T4880-5800 Mines 1-3 (Dlvl5-7): 5 daggers, enchant weapon (+3), long sword Skilled, XL8 (giant beetle). Prière T5308 (Weak). Yellow light → aveugle 90 tours (attendu sur place). Lynx+dog Dlvl7 (HP 38/77), brown pudding tué aux daggers.
- T4700 Dlvl4: tunnel creusé (digging) 65,26→60,26. Kitten retrouvé. Mountain nymph (boots volées) tuée fire+daggers, food ration. Scroll PHOL ENDE WODAN = remove curse. MINES : > Dlvl4 42,16.
- Dlvl6 T3875 prière (Weak). Altar lawful 34,15 : BUC de tout (ring ivory cursed laissé sur l'altar). Leprechaun hall 7-20,14-16 : ~15 tués, XL4→7. Wood nymph a volé le shield dans le noir (T~4300) ; tuée à la wand of fire, shield récupéré (burnt). Scrolls identifiés : PRATYAVAYAH=teleportation, JUYED AWK YACC=create monster, LEP GEX VEN ZEA=enchant weapon.
- Dlvl5: chest → tripe, scroll LEP GEX, milky + yellow potion, glass wand. XL4 (rock mole). Leprechaun (or posé au sol). Gray ooze tué à mains nues (casque rouillé AC5). Level teleport trap Dlvl5 (vers 25,14?) → retour Dlvl4 est.

## Lessons
- Leocrotta (q, vitesse 18, 3×2d6) : à Minetown il m'a fait 37→15 en un tour. Dès qu'un q inconnu apparaît : farlook, et fuite/Elbereth AVANT d'être à 40%.
- Prière seulement si HP < 1/7 max (ou < 6) : à HP 15/77 elle n'aurait pas soigné. La wand of digging vers le bas est l'évasion instantanée.
- Un Elbereth ne protège pas si un boulder est sur ma case / si le géant a une arme… vérifier ':' après tout événement.
- LEPRECHAUNS : ne jamais porter d'or quand un l est vivant sur le niveau. J'ai perdu 1644 gold du vault en 2 vols (T4505). Poser l'or loin, ou tuer tous les l d'abord.
- NYMPH encore (run 8, run 9) : dans une salle sombre, je ne vois pas la n arriver. Allumer le lantern / ne pas balader le travel dans le noir ; vérifier AC après chaque série de déplacements.
- Script de ramassage : ',' sur une case à objet unique ramasse sans menu (j'ai pris 8 cadavres + rocks). Toujours vérifier « Things that are here » avant.
- scripts/explore : le cache « dead » est indexé par Dlvl@position du '<'. Si le '<' est caché (objet dessus, ou je suis dessus), la clé devient « N » partagée avec les anciennes parties → « no reachable frontier ». Remède : ramasser l'objet sur '<' / sortir de la case.
- Les scripts de slots/1 qui appellent slots/1/k|v (brawl, thr, sw, wait) tournent sur le PC ; ceux qui appellent scripts/session.py (shoot, hit) via slots/1/w ./shoot.
- Tripe ration : vomissement (confusion/stun ~25 tours) → la manger seulement en zone sûre.
