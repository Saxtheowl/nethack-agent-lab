# Emplacement 6, run 1 — journal (état le plus récent en haut)

## DEATH T10049, Sokoban niveau 3 (Dlvl3), XL7, AC1 : "killed by a soldier ant" (piqûre empoisonnée)
Chaîne : Sokoban 3 résolu, en ouvrant la porte vers l'escalier, 3 soldier ants attendaient. Combat dans l'embrasure :
wand of cold (1 tuée, 1 bolt raté), mêlée HP 49 -> 22 -> 11. Elbereth dans l'embrasure les a fait fuir, mais le dust
s'est dégradé en ~15 tours (El?creth) pendant le repos ; réécrit, puis re-dégradé entre deux contrôles : 17 -> 0 en un tour.
Leçons :
- Soldier ants (a bleus, vitesse 18, 2 attaques + poison) : ne pas ouvrir une porte / entrer au contact sans HP pleins ;
  zapper la wand of cold DÈS qu'elles sont alignées, au moins 2 fois, AVANT la mêlée ; reculer dans le couloir.
- Elbereth en poussière face à 3 monstres rapides s'use en quelques tours : le rest script (chunks de 2-3 tours) ne suffit
  pas ; il fallait prier dès HP < 1/7 (9 HP) — la prayer (dernière T8512, ~1500 tours) était sûrement disponible.
  => Sous ~20 HP avec des monstres dangereux : PRIER si timeout probablement OK, ne pas parier sur Elbereth.
- Les scripts Sokoban automatiques doivent s'arrêter sur « Hungry », sur toute perte de HP, et sur un blocage (pas continuer
  à envoyer les touches depuis une mauvaise case).
- Le familier bloque constamment les poussées dans Sokoban ; les pets volés par les nymphs et trap doors des Mines ont coûté cher.


STYLE TARIRU (memory/tariru-style.md, obligatoire)
Lire aussi les « Lessons » de memory/run-1..run-4, slot2-run-1, slot3-run-1.
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore).

## Current state
URGENT: T9926 Sokoban niveau 3 (Dlvl3) RÉSOLU (niveau 2 aussi), XL7 HP67 AC1 $192, large dog, magic whistle G, unicorn horn h.
Prayers: ... T6481, T8512 -> prochaine >= ~T9500-9600. FOOD: AUCUNE (dernière ration mangée T9262) -> chercher nourriture Sokoban 3.
Rings: l shiny ring (inconnu). Wands: k aluminum (engrave: rien), j hexagonal, g SDD, m light, R tele (0:0).
Scrolls: i 2 NR 9 (earth probable), v teleportation, Y 3 blank, d HACKEM MUCHE, X FOOBIE BLETCH.
Outils Sokoban: /tmp/claude-1000/soko_try.sh X Y PUSHES (planner scripts/sokoban.py + envoi touche par touche, s'arrête HP/faim).
Solutions: nethackwiki Sokoban_Level_Nx (WebFetch), recalculer le nombre final de 'r' selon les trous restants.
D6 main: '<' 52,15, Sokoban '<' 64,26. D4: Mines '>' 20,24. Minetown D8: temple, deli.

## Lessons
- Sokoban : le familier bloque les poussées (« monster behind the boulder ») ; découper les plans et marcher vers lui pour échanger.
- Pendant les scripts automatiques : une nymph a volé le bouclier, un panther m'a mise à 8 HP. Vérifier les messages (stole/hits) et les HP à chaque pas.
- T8509 : FAINTING pendant les scripts Sokoban (aucun contrôle de faim) -> prayer T8512. Tout script en boucle doit vérifier Hungry/Weak.
- Sokoban = niveau JUSTE EN DESSOUS de l'Oracle (Oracle D5 -> entrée Sokoban D6, 2e '<'), pas au-dessus. #overview confirme.
- explore.py continue même quand une nymph est adjacente : la water nymph du Mines D7 m'a volé magic whistle + hexagonal wand SANS que je le voie. Chercher « stole » dans les messages après chaque explore ; tuer les nymphs à vue.
- Zapper une wand sur un monstre DEPUIS Elbereth = « You feel like a hypocrite » (alignement) et l'engraving s'efface : quitter la case avant de zapper.
- Giant spider au Mines D11 et à Minetown : wand of teleportation dessus quand alignée.
- NE PAS attaquer un gray unicorn au XL5 (butt+kick, speed 24) : 54 -> 16 HP en quelques tours.
- Elbereth en poussière s'use aussi quand les monstres fuient (observé 3.6.7) : scripts/rest le réécrit.
- explore --all continue même quand '<' est visible : en fuite, utiliser t X Y directement.
- Mines: trap doors fréquentes (3 chutes !). explore/travel marchent dessus : pas de parade sauf chercher (s) ; garder le whistle pour le chien.
- Pour tester le curse par le chien, il doit marcher DESSUS : peut prendre des dizaines de tours ; sinon altar.
- Red mold: son feu passif touche même quand on RATE (−8 HP). Ne l'attaquer que HP pleins ; tuer à distance si possible.
- explore.py rate souvent les portes ("no reachable frontier") : ouvrir/traverser la porte à la main.
- scripts/session.py sans NH_SLOT affiche le slot 1 : toujours slots/6/session.
