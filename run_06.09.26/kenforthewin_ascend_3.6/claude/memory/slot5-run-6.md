# Slot 5 — run 6 (Wish2, style wish_abuser, start-scum tentative 1003)

## Current state
URGENT: T3902 Dlvl8 (mines) HP61(63) AC3 XL6 HUNGRY, AUCUNE nourriture. a +1 long sword, c +3 small shield, n thoroughly rusty splint, p amulet (vs poison probable). PRIÈRES T1889, T3093, T3931 (faim, OK). D MAGIC MARKER. s MAGIC LAMP uncursed. l WAND OF LIGHTNING. z cursed elven mithril. E scroll GNIK SISI VLE (à vendre au bookstore pour acheter à manger). 13 zm.
LAMP e : NE PAS #rub avant qu'elle soit BLESSED. Identifier par prix en shop (magic base 500, oil base 10).
NOURRITURE : 1 seule ration → acheter des food rations dès que possible, garder 2+.

## Plan
MAGIC LAMP s (uncursed) : trouver un potion → dip 2x dans une fountain (34,21 / 44,21) → water → poser sur l'altar lawful 39,18 → #pray quand timeout 0 ou quand Weak (≤200) → holy water → #dip s → #rub s → wish "blessed +2 gray dragon scale mail". Sacrifier des corpses frais sur l'altar : « hopeful feeling » = timeout encore >0, « reconciliation » = 0.
1. Explorer D1-D4, or + nourriture. Shop → estimer la lamp.
2. Altar co-aligné (lawful) → BUC ; holy water → bénir e → #rub (wish blessed +2 GDSM).

## Carte
D6 MINETOWN : '<' 71,16 (hors murs, est), '>' 6,19 (salle ouest, porte 11,17 déverrouillée). Temple LAWFUL (Tyr, priestess) altar 39,18, porte 40,21. Izchak lighting 48-50,16-18 porte 49,19. Delicatessen Tjibarusa 37-39,25-26 porte 40,26 : 2 food rations 60 zm, 2 slime molds 46, ice box 107. Fountains 34,21 et 44,21. Shop ?/+ 30-32,16-17. Entrée ville par la porte est 56,14.
D8 (mines) : '<' 62,14, '>' 75,14, splint mail 21,22, whistle 56,26, rolling boulder traps 30,13 et 37,13, bear trap 26,18.
D7 (mines) : '<' 38,23, '>' 25,12.
D5 (mines) : '>' 5,24, '<' 66,17 (salle NE), hole 68,13, rolling boulder trap ~39,15. D3 (mines) : MAGIC MARKER sur une TRAP DOOR en 73,27 (tombée → D5). Plate mail 61,17. '>' 29,23. D3 '<' 5,16.
D1 : '<' 39,17, '>' 24,15.
D2 : '<' 6,22, '>' 21,19 et '>' 64,17 (une = Mines). Elbereth BRÛLÉ en 48,22 (salle 47-50,22-25).

## Lessons
- T3090 : un simple rabid rat m'a descendue de 45 à 5 HP (je ratais tout) : sous 50 % HP, graver Elbereth AVANT, pas après ; ne pas zapper lightning vers un mur proche (rebond).
- Excalibur dans une fountain de Minetown = watch en colère (fountain.c:403) : le faire ailleurs.
- D3 Mines : l'orc shaman/rock mole ont percé les murs de Minetown.
- 3.6.7 : magic lamp base 50 (pas 500) ! offre de vente 25 (ou 19) ; oil lamp 5 (ou 4).
- Prier sans trouble avec timeout >0 = p_type 0 : Luck -3 + dieux fâchés. Pour la holy water, prier quand Weak (timeout ≤200 suffit) avec la water sur l'altar.
- T1343 : un objet posé sur une trap door (magic marker D3 73,27) : on tombe en allant le chercher. Farlook la case / chercher un ^ avant.
- T1850 : la guard refuse les pas groupés quand Hungry ; les mouvements un par un passent.

## ABANDONNÉE — décision de l’utilisateur (27/09 ~22h45)
Plus de style wish_abuser : partie quittée (#quit), l’emplacement repart en style Astra.
