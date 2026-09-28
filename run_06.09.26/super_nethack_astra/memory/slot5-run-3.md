# Emplacement 5, run 3 — journal (état le plus récent en haut)

## DEATH T2489, Dlvl 7 (Gnomish Mines, ORCISH TOWN), XL5, 1250 pts : « killed by a magic missile »
Chaîne : tombée par un trou de Mines D5 à D7 (T~2330) ; le niveau était Orcish Town (Minetown saccagé : orcs nommés
« of Ogbaneog », orc-captain, orc shamans, pas de prêtre ni de boutiques). Wand of sleep sur l'orc-captain (tué, XL5),
mais une potion de cécité lancée m'aveugle ; en frappant « l'air » je prends des coups, un orc shaman et un orc avec
une WAND OF MAGIC MISSILE me font passer de 31 à 8 HP en un tour, puis à 0 pendant la gravure d'Elbereth.
Leçons :
- Orcish Town à XL4-5 / AC5 = piège mortel : des dizaines d'orcs armés de wands et potions. Dès qu'on voit des orcs nommés
  « of <clan> » ou un orc-captain dans Minetown, REPARTIR par l'escalier.
- Wand of magic missile d'un monstre : ~2d6 par zap, plusieurs zappeurs = mort en 1-2 tours. Avoir de l'AC et fuir.
- Elbereth ne protège pas des attaques à distance (wands, potions lancées) ; à 8 HP il fallait fuir ou quaffer, pas graver.
- La prayer n'était pas utilisable car HP 8 > 1/7 de 46 ; il fallait prier AVANT (à 1/7) ou garder une évasion (scroll de téléportation).
- Ne pas descendre les Mines sans nourriture ni armure correcte ; les trous (trapdoors) font sauter des niveaux.

STYLE ASTRA (memory/astra-style.md). Lire DEATH/Lessons de slot5-run-1.md (fire ant) et slot5-run-2.md (gold golem).
Règles tirées des runs 1-2 :
- Jamais de boucle de déplacement sans arrêt sur perte de HP (slots/5/goto et grab2 sont HP-safe ; pas scripts/t, pas grab).
- Relire HP après CHAQUE appel ; un seul helper par commande quand un monstre est en vue.
- 2+ rations toujours ; acheter la nourriture quand on n'a pas faim (prix ×2..×4 sinon).
- Nymphs/monkeys/leprechauns : tuer à distance (daggers) dès qu'on les voit ; ils volent l'armure portée.
- Excalibur : bénir l'épée avant de tremper (les objets bénis résistent à la rouille) ; fountains Oracle.
- Sous 50 % HP face à un monstre rapide : Elbereth vérifié / escalier, pas de contact.
- Helpers : gf (combat gardé), elb, rest2 (s'arrête faim/HP), goto, grab2, doorfight, map, chase, dip1.

## Current state
URGENT: T2452 Dlvl7 (Mines 4 = MINETOWN ?) HP31(41) AC5 XL4, LAST PRAYER T1269 → OK. AUCUNE nourriture. $48.
Tombée par un trou/trapdoor de Mines D5 à D7 vers T2330.
Porté: a +1 long sword, c +3 small shield, p low boots (BUC ?). s WAND OF SLEEP (identifiée).
Sac: potions f sky blue, i dark, n brown, o 2 clear, q yellow ; j velvet spellbook ; scrolls l READ ME, t DUAM XNAHT, u LOREM IPSUM ; r lamp.
D7 : fountains 37,20 et 46,20, altar 41,24, '<' 20,23, iron bars 22,16.
Carte: D1 '>' 31,15 ; D2 '<' 76,24 '>' 65,15 ; D3 '<' 68,27 '>' 19,27 = MINES ; Mines1 D4 '<' 6,14 '>' 53,17 ; D5 '<' 19,20 '>' 30,27.

## Lessons
- T690 : boucle d'évasion de bear trap sans regarder les messages → un jackal m'a mordue 5 fois. Toute boucle doit lire HP/messages à chaque tour.
