# Emplacement 6, run 1 — journal (état le plus récent en haut)

STYLE TARIRU (memory/tariru-style.md, obligatoire)
Lire aussi les « Lessons » de memory/run-1..run-4, slot2-run-1, slot3-run-1.
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore).

## Current state
URGENT: T7892 Dlvl6 XL7 HP51/67 AC1 $192, large dog tame, magic whistle G, UNICORN HORN h (pet-testée non maudite).
Prayers: T2826, T4203, T4957, T6481, T8512 -> prochaine >= ~T9500. Food: 1 food ration f.
D6: '<' main 52,15 (salle fermée, portes cachées 48,16 et 63,16), '<' SOKOBAN 64,26, '>' ?. 
Wand of teleportation R (0:0). j hexagonal. v scroll of teleportation. Y 3 unlabeled (blank), d HACKEM MUCHE, X FOOBIE BLETCH.
Oracle D5: '<' 12,13, '>' 62,22. D4: '>' Mines 20,24, HOLE 21,24, '>' main 46,14, bookstore. Minetown D8: temple Loki, deli.
Outils: /tmp/claude-1000/xp6 N (explore), scripts/sokoban.py X Y PUSHES [--execute] (slots/6 n'a pas de wrapper: NH_SLOT=6).

## Lessons
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
