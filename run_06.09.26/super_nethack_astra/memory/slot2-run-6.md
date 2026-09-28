# Emplacement 2, run 6 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md). Modèle : run 5 (83768 pts, Castle).

## Current state
URGENT : PARTIE TERMINÉE — DEATH T3549 Dlvl7 (Minetown), tuée par le watch captain, XL5. Ne pas relancer sans consigne (python3 scripts/next_style.py 2).

## Map notes
D1 : fountain 44,19.

D3 : '>' 45,17 et '>' 11,27 (l'un = Mines) ; GENERAL STORE Asidonhopo 73-77,15-20 (porte 72,15) : glass wand 200 (base 150), tin wand 178 (base 100 surtaxé?), food rations 60, 2 food rations 77,19, fizzy potion 400, spellbook dark brown 133, gems. Scroll DUAM XNAHT = light (base 50, vendue), XIXAXA = base 100 (vendue).

D3 '>' 45,17 = MINES. D4 (Mines 1) : '<' 19,13, '>' 69,15 (chien perdu ici). D5 : '<' 51,25, '>' 42,23. D6 : '<' 27,25, '>' 26,18. D8 : '<' 42,21 ; '>' 5,24 ; traps 71,18 21,19 52,19 (rolling boulder).
D7 MINETOWN : '<' 6,23 ; '>' 63,20 ; TEMPLE de Odin (neutre, priestess) altar 56,26 ; fountains 43,20, 30,26 ; shop 30-32,20-21 ((!().

## DEATH (T3549, Dlvl 7 = MINETOWN, XL5) — killed by a watch captain
Déroulé : XL5 à T3423 ; dip de la +2 long sword dans la fountain 43,20 (rouille x3, puis « flow reduces to a trickle » -> changé de fountain) ; fountain 30,26 : WATER DEMON reconnaissant -> WISH blessed +2 fixed gray dragon scale mail (AC -5) ; dip suivant : EXCALIBUR, mais « the fountain disappears » -> watch de Minetown hostile. Un watchman attaque, je le tue : « You murderer! » (-2 Luck -> Luck -1 : PRIÈRE IMPOSSIBLE). Le watch captain (2 attaques silver saber ~10-18/tour) m'a descendue de 58 à 20 ; scroll inconnu = charging (inutile) ; fuite bloquée par un 2e watchman (knife) + captain(s) ; swirly potion = confusion, effervescent cursed = gain energy ; mort à T3549.

## Lessons (run 6)
- NE JAMAIS dipper pour Excalibur dans une fountain de Minetown : le 1/6 Excalibur fait AUSSI disparaître la fountain (« the fountain disappears ») -> watch hostile. Toujours une fountain hors Minetown (D1 44,19 ici, ou autre niveau).
- Tuer un watchman (humain, même hostile) = « You murderer! » : -2 Luck -> Luck < 0 -> prière « too naughty » (pray.c l.1823). Fuir la watch sans la tuer, ou fuir le niveau AVANT le combat.
- Le watch captain à XL5 = mort : ~15-20 dégâts/tour même à AC -5. Dès « guard's whistle », aller à l'escalier le plus proche SANS détour ; ne jamais le laisser adjacent.
- Avant tout acte risqué dans une ville, repérer le trajet libre vers '<' ET '>'.
- Boucle d'attente : exclure le chien par POSITION (PETS), pas par la lettre d : un jackal m'a mordue 12 HP. Helper slots/2/prest (pets exclus, stop HP drop).
- Boucle de marche dans une shop sans relire : un small mimic m'a mis à 6/18. Dans une shop, farlook les ']' et avancer case par case.
D2 : '<' 57,23 ; '>' 9,23 ; sink? 8,23 ; porte verrouillée 61,27 (non ouverte).
D3 : '<' 5,12 (large box vidée : scrolls i DUAM XNAHT, j VE FORBRYDERNE, ring k ivory).
- w uranium wand : engrave sans message (opening/locking/probing/undead turning/nothing/striking)
