# Emplacement 6, run 1 — journal (état le plus récent en haut)

STYLE TARIRU (memory/tariru-style.md, obligatoire)
Lire aussi les « Lessons » de memory/run-1..run-4, slot2-run-1, slot3-run-1.
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore).

## Current state
URGENT: T5302 Minetown Dlvl8 XL6 HP60/60 AC1 $183, SANS familier (dog laissé Mines D6, whistle). Prayers T2826, T4203, T4957 (lycanthropie guérie) -> prochaine >= ~T6000.
Food: 2 food rations, fortune cookie, tripe. Wand of teleportation R (0:0 ! 3 zaps utilisés ; on peut encore la « wrest » 1 fois).
Portés: rotted studded leather, +3 small shield, blessed iron shoes, dwarvish cloak. Manquent: helm, gloves.
Minetown (variante grotte, beaucoup d'undead: elf zombies, human mummy téléportée) : temple Loki (chaotique) altar 56,26 porte 51,26 ;
deli 43-45,25-26 (egg 14) ; general store 44-46,14-16 ; lighting shop 37-38,17-19 ; '>' 71,19 ; '<' 19,14 (NW). Gray unicorn hostile rôde (NE PAS attaquer).
Scrolls: v ASHPD SODALG (base 100, uncursed), I VE FORBRYDERNE (base 50?). Potions: fizzy (1 blessed, 1 uncursed), puce, brilliant blue, clear=water.
D4 Mines '>' 20,24 ; D5 = Oracle ; Sokoban '<' à trouver sur D4. D10: dwarvish mithril-coat à 38,21.

## Lessons
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
