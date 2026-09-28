# Slot 2 — run 8 (Claude2, astra style)

STYLE ASTRA (memory/astra-style.md section 6 obligatoire). Lessons: run 5 (Castle), run 6 (fountain Minetown), run 7 (dips en boucle).

## Current state
URGENT : PARTIE TERMINÉE — DEATH T2755 Dlvl6 (Minetown), tuée par Banjoewangi (shopkeeper, wand of striking pendant le sommeil), XL5, 988 pts. Ne pas relancer sans consigne (python3 scripts/next_style.py 2).

## Plan
- Excalibur à XL5 dans une fountain HORS Minetown, UN dip par commande, plein HP, sortie proche.
- Mines -> Minetown (temple, co-aligned ?) ; Sokoban ; altar BUC.

## Map notes
D1 : < 38,27 ; > 49,16 ; FOUNTAIN 52,16 (Excalibur XL5, escalier > à 3 cases).

D2 : < 56,15 ; > 52,27 et > 11,22 (un = Mines) ; ALTAR Odin (neutral) 20,15 ; trap 23,15 (anti-magic?) ; porte verrouillée 31,13 (non ouverte).
D2 > 11,22 = MINES. D3 (Mines 1) : < 72,24.
D3 trap door -> D5. D4 (mines) : < 30,14 ; > 75,17.
D6 MINETOWN (arbres) : < 4,17 ; > 72,22 ; TEMPLE LAWFUL (Tyr, co-aligné !) altar 56,26, porte 51,26 ; fountains 43,20 30,26 (NE PAS DIPPER) ; shop outils ((( 37-38,17-19 ; shop 44-46,14-15 (%=*?+(). Protection : 400*(XL+1) or.

## IDs
- l orcish helm BLESSED +1 (porté, AC4). Scrolls : VAS CORP BET MANI = identify ; MAPIRO = punishment ; FOOBIE et ZLORFIK = base 200 (vendus).
- scrolls e MAPIRO, f FOOBIE : uncursed (altar D2).

## Lessons
- T312 kill1 (boucle de coups dans une direction fixe) a TUÉ mon little dog qui avait pris la place du jackal (thunder = -15 alignement, -1 Luck). Pet adjacent : UN coup à la fois, relire l'écran avant chaque coup.
- T1300 Minetown : fog cloud + rabid rat + coyotes -> HP 4/27 à XL3 (to-hit faible, beaucoup de ratés). Elbereth marche sur les coyotes mais s'est dégradé en ~70 tours ; prière T1402 OK. À XL3 AC6, même des coyotes en groupe sont dangereux : fuir/Elbereth dès HP < 50 %.
- Food ration "rotten" (rare) = presque rien mangé ; faim revenue vite.

## DEATH (T2755, Dlvl 6 = MINETOWN, XL5) — killed by a wand, while sleeping (shopkeeper Banjoewangi)
Déroulé : achat de food au delicatessen (cram, tripe, fortune cookie, tout payé) ; une human zombie blessée
revient m'attaquer devant la porte du deli (HP 31 -> 12). Plusieurs @ à l'écran (watch captain, watchman,
shopkeeper). J'ai lu la PREMIÈRE ligne « Neighbors of @(48,23) » comme étant moi (c'était un watchman) et j'ai
lancé `hit 1` (F1) en croyant viser la zombie en 47,24. En réalité j'étais en 46,25 : F1 a frappé le
shopkeeper Banjoewangi (45,26) — sans « Really attack? » visible. Shopkeeper furieux + watch : sleep ray
(wand) puis wand of striking pendant le sommeil -> mort en 1 tour. Apaiser un shopkeeper attaqué = 1000 gold
(j'en avais 121).

## Lessons (run 8)
- MINETOWN / plusieurs @ : la position du héros = « Terminal cursor (x,y) » (1re ligne de v), JAMAIS la première
  ligne « Neighbors of @ » (le script en affiche une par @). Avant chaque F<dir> : relire le curseur, farlook la
  case cible (look X Y) juste avant, et ne jamais combattre en étant adjacent à un shopkeeper/watchman/priest.
- Combattre à côté d'une porte de shop = interdit : reculer d'abord (le shopkeeper se place dans l'entrée).
- Attaquer un shopkeeper = mort certaine à bas niveau (sleep + striking). Il faut 1000 gold pour l'apaiser.
- Tueur principal de la run : faim (rotten ration) + peu d'XP ; j'ai dû prier 2 fois (T1402 HP 4, T2610 Weak).
  Garder de la food ; manger chaque corpse frais sûr.
- Gas spore : la tuer au corps à corps seulement avec HP > 24 (4d6) ; ça a marché à 27 HP.
- Human zombie : d8, AC8, ~20 HP ; à XL5 AC4 elle m'a mise à 5/33 : ne pas l'engager sous 2/3 HP.
- Helpers : slots/2/elb (Elbereth + vérif), slots/2/erest2 (repos Elbereth avec réécriture auto).
- scripts/go : sa fonction pos() prend la 1re ligne Neighbors -> faux « no progress » quand d'autres @ sont
  visibles (bug noté, fichier partagé non modifié).
