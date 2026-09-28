# Slot 5 — run 7 (Claude5, style astra)

## Current state
URGENT: MORTE T7033 au Dlvl 8 (Oracle), tuée par une INVISIBLE GOLDEN NAGA (psi bolt). Partie terminée.

## Plan
FAIT : Excalibur T4888 (fountain D2 disparue).
1. Explorer D1-D4 prudemment, ramasser nourriture/or ; acheter rations (garder 2+).
2. XL5 → Excalibur dans une fountain hors Minetown (D1 fountain 76,13).
3. Mines → Minetown (temple, protection) ; Sokoban ; AC <= 3 avant le fond des Mines.

## Carte
D2 : '<' 26,18. HEALTH FOOD STORE (Blaze) 4-10,15-17 porte 11,16 : food ration 60, PURPLE-RED = FULL HEALING (267, x2-3), BUBBLY = HEALING (178), magenta = fruit juice (67), HACKEM MUCHE = food detection (133).
D6 main : '<' 55,15, '>' 35,14 (salle sombre 35-44,12-15, porte 44,16). Killer bees, manes, Uruk-hai (archer) autour ; yellow lights (cécité).
D5 main : '<' 23,12, '>' 32,12.
D7 main : '<' 13,13, '>' 44,28, fountain 64,25.
MINETOWN = D7 (College Town) : '<' 12,17, '>' 77,16. Temple NEUTRE (Odin, priestess) altar 39,18 porte 39,21. Bookstore (Ballingeary) 30-32,16-18 porte 31,19 (achète spellbooks 200). Delicatessen (Siboga) 37-39,25-26 porte 40,26 (GIANT MIMIC dedans, 26 dégâts/tour !). Tool shop (Eed-morra) 30-32,25-26 porte 30,23 : camera 267, towel 67, ice box 102, figurine 107 ; SMALL MIMIC en 32,25. Fountains 34,21 et 44,21 (NE PAS dipper : garde en colère).
MINES 2 = D6 : '<' 29,13, '>' 48,22. LEVEL TELEPORT TRAP vers 38,14 (sous l'objet '(') — renvoie au D5 ! Bear trap 21,23.
MINES 1 = D5 : '<' 72,14, '>' 50,15.
D4 : '<' 22,13, DEUX '>' : 49,17 et 45,26 (l'un = Mines). BOOKSTORE (Kilmihil) 74-77,27-28 porte 73,28 (1 small mimic tué). Magic trap 34,27.
D3 : '<' 17,25, '>' 54,26, fountain 67,18. Chien perdu sur D3.
D2 : '>' 40,14 (coin sombre salle fountain 38-40,12-14 ; porte 37,12 enfoncée). Red mold 64,13.
D1 : '<' 46,13, '>' 32,16, FOUNTAIN 76,13 (salle NE). Porte verrouillée 32,24.

## Identifié
GARVEN DEH = remove curse ; GNIK SISI VLE = enchant armor ; DUAM XNAHT = identify ; YUM YUM = light (base 50) ; MAPIRO = base 300 ; JUYED = base 100. Purple-red = full healing, bubbly = healing, magenta = fruit juice (prix D2).

## Lessons
- explore.py NE ramasse PAS les objets et passe à côté : lire "Map features" après chaque explore et aller chercher %, ?, !, /, =, $.
- explore.py dit « no reachable frontier » alors que des coins de salles SOMBRES restent inconnus (le '>' du D2 était là) : regarder les salles sombres en entier.
- Le travel `_` passe par les portes verrouillées connues et bute dessus : contourner par étapes ou enfoncer la porte (si ce n'est pas une boutique).
- T4469 : un ']' dans une boutique était un GIANT MIMIC (2x3d6) : 38→12 HP en un tour. Dans les boutiques, ne marcher que sur des objets déjà vus de près ; les ']' isolés = mimics. Elbereth le 1er coup mal écrit (« Elberet= ») : toujours relire avec ':'.
- Yellow light = explosion aveuglante (2 fois !). Tuer à distance ou fermer les yeux... sinon combattre aveugle avec F et Elbereth. Prier à HP<=1/7 a sauvé (T6340).

## DEATH (T7033)
Tuée au Dlvl 8 (niveau de l'Oracle, salle aux statues de centaurs, 45,17) par une golden naga INVISIBLE, XL7, HP 0(63), AC5, 3976 points.
Enchaînement : hallucination (source inconnue) en entrant dans la salle de l'Oracle ; combat contre des loups dans l'embrasure 44,16 (porte cassée : attaques en diagonale possibles) → HP 30/63 ;
repos tour par tour sur place (srest) au lieu de partir ; « It bites! Something casts a spell » : destroy armor (orcish helm +3 détruit, AC 1→5), 37→28 ; F7 sur le « I » : 28→16 ;
gravure d'Elbereth à 16 HP : pendant ce tour, morsure + psi bolt (« Your head suddenly aches very painfully ») → 0. Prière déjà utilisée à T6340 (700 tours avant).
Identifié à la mort : T = SCROLL OF TELEPORTATION (non lu, aurait sauvé), f = blessed potion of SEE INVISIBLE, G = hallucination, N = levitation, h = blessed stinking cloud,
m = gold detection, C = ring of warning, i = wand of nothing, P = slow monster (0:3). Excalibur depuis T4888.

## Lessons (mort)
- Monstre invisible qui mord ET lance des sorts (golden naga, ~2x2d6 + psi bolt) = fuir IMMÉDIATEMENT, pas combattre au jugé. À 28/63 HP contre un « I » inconnu : lire un scroll inconnu de base 100 (téléportation possible) ou monter/partir, au lieu de rester.
- Ne jamais se reposer (srest) dans une salle ouverte à moitié de HP après un combat : s'éloigner d'abord (escalier '<', couloir en cul-de-sac + Elbereth vérifié).
- Elbereth se grave en 1 tour pendant lequel on prend encore les coups : le graver AVANT de descendre sous ~50 % HP, pas à 16/63.
- Identifier/boire tôt les potions bénies inconnues : f (blessed) était see invisible. Price-ID les scrolls de base 100 (JUYED/GHOTI) et garder l'éventuelle téléportation comme évasion.
- Après une prière (T6340), considérer qu'on n'a PLUS de filet pendant ~1000 tours : jouer plus prudemment (HP > 60 % avant d'avancer).
- Yellow lights et hallucination rendent aveugle/confus : attendre la fin dans un couloir sûr avant d'entrer dans une nouvelle salle.
