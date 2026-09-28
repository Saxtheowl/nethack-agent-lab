# Emplacement 7, run 2 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md). Lire les Lessons de memory/slot7-run-1.md (meilleure partie : Castle, tué par minotaur).

## Current state
DEATH T6178 Dlvl9 (salle SE, près de 58,27) : tuée par un YETI pendant que j'étais PARALYSÉE par une floating eye. Mon helper pricewalk (pas '6' à l'aveugle) a frappé une floating eye invisible dans la salle sombre -> paralysie ~25 tours ; le yeti m'a descendue de 60 à 0. XL7, AC-5, Excalibur, bag of holding. PARTIE TERMINÉE — ne pas relancer ici.

## Plan
T3185 : Mines D7 trop dangereux -> Sokoban d'abord (main D5+ : trouver Oracle, Sokoban = up depuis le niveau au-dessus de l'Oracle).
Explorer D1-D4, Mines -> Minetown (altar BUC), Sokoban, Excalibur à XL5 (fontaine). AC<=3 avant Mines profondes.

## Notes niveaux
D1: trap door vers D2 (côté ouest, près de 24,26 ?), '>' 21,28, '<' 67,28.
D2: bookstore Ennistymon 8-16,12-15 (identify = ANDOVA BEGARIN 27zm ; KO BATE/YUM YUM base 80 ; FNORD 200 ; GNIK SISI VLE 300 ; KERNOD WEL 50). '>' 32,26, '<' 61,16. Vault (guard entendu).
D3: general store Adjama 45-51,21-24 (porte 44,21) : 2 white gems 10666, black potion 400, milky 333, brown 133, VELOX NEB 267, spellbooks. '>' 39,14, '<' 11,17.
D4: '>' principal 69,13 (salle NE, sink 69,12, leprechaun) ; '>' MINES probable 39,16, '<' 45,26, fountain 29,20 DISPARUE (Excalibur obtenue). Pas de branche Mines vue sur D4 ni D3 -> sans doute D2 (zones non explorées).
D5: '<' 25,25 ; grand shop (general?) 63-73,12-18 ; salle ouest 16-26,13-19 (porte 27,14 déverrouillée, 4 hill orcs tués).
Mines: D5 '<' 10,16 '>' 15,17 ; D6 '<' 37,17 '>' 52,27 (gray stone 46,19 NON ramassée) ; D7 (mines 3) : ARRIVÉE '<' 32,20 = 9 HILL ORCS + GIANT SPIDER à côté -> remonté T3185. Peut-être Orcish Town. Revenir plus fort.
Main D5: '<' 25,25, '>' 7,15, general store Kabalebo 63-72,12-18 (porte 61,14 ; mimic 68,16 ; fencing gloves 67zm=base50, wand 66,17, rings) . D6: '<' 38,16, '>' 28,25.
D7 main: '<' ~55,28 ; LEVEL TELEPORTER trap sur le chemin au nord (vers 60,17) -> envoyé sur D2 T4208. L'éviter.
D7 main (suite): '>' 43,25 ; armor shop Aksaray 5-11,20-23 (porte 10,19) : ELVEN MITHRIL-COAT 320zm (10,21), faded pall=elven cloak 80, splint mail 107, plate mail 813, low boots 11 ; fountain 6,12 (salle NW porte verrouillée 9,12).
D8 = ORACLE (centre 33-45,16-25). '<' 8,16, '>' 75,21. Bag of holding trouvé 54,26. SOKOBAN = '<' supplémentaire sur D9 (niveau SOUS l'Oracle, cf. leçon run 1) ; perdu ~300 tours à chercher sur D7.
Identifiés: ANDOVA BEGARIN=identify, THARR=destroy armor, fizzy=polymorph, brilliant blue=extra healing, gold ring=warning.

## Lessons
- MORT : ne JAMAIS enchaîner des pas de déplacement bruts (pricewalk/‘6666’) dans une salle sombre ou inconnue : un pas sur une case occupée = ATTAQUE. Une floating eye non vue = paralysie ~20+ tours = mort si un autre monstre est là. Toujours farlook les 'e' et n'utiliser que travel/explore (qui disent « You move right into » sans attaquer) ou F-dir délibéré.
- Mes helpers de marche doivent s'arrêter si un monstre est affiché sur la case cible (lire Neighbors avant chaque pas) — pricewalk ne le faisait pas.
- Avant de s'aventurer : si un yeti/tigre rôde (déjà tué un yeti sur D8), rester à HP pleins et garder 2 potions de soin HORS du sac (je les avais, mais la paralysie empêche de boire).
- Gelatinous cube : ne pas la frapper (paralysie passive d(lvl+1,4) tours 2/3 du temps) ; le travel peut ramener à côté d'elle.
- Sokoban est sous l'Oracle (Oracle+1), pas au-dessus : relire les leçons AVANT de chercher.
- Les lignes d'écran contenant seulement des murs sont masquées par la vue compacte (rangées 11 et 29+).
- L'helper explore entre dans les shops et bute sur le shopkeeper ('Really attack?') ; les spellbooks '+' d'un shop sont pris pour des portes.
- Dans un script, ne jamais envoyer 'n' via k : en number_pad 'n' = préfixe de compte (Count: 32767). Utiliser Escape.
- Vendre les gems IDENTIFIÉES au shop : jet = 425 zm.
