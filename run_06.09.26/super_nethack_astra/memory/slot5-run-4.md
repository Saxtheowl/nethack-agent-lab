# Slot 5 — run 4 (Wish3, style wish_abuser, partie trouvée par le start-scum, tentative 768)

## Current state
URGENT: MORTE T12362 — killed by a giant mimic, Sokoban 4 (zoo), XL9. Partie terminée.
SOKOBAN : les 4 niveaux ont leurs trous bouchés. RESTE LE ZOO du niveau 4 (monter le < 46,21 → arrivée au > 33,28 ; zoo = salle 45-49,22-28, porte est 50,25 ouverte avec corpse dedans, couloir x=51). Déjà tués : 2 Grey-elves, yellow light, plusieurs autres à l'aveugle. Restent probablement : CHICKATRICE (pas de lizard !), pyrolisk, WEREWOLF (lycanthropie, prière pas dispo avant T11150), mumak, soldier ant, leprechaun (poser l'or avant), ochre jelly, floating eye (jamais au contact). Tactique : combattre depuis le couloir x=51 / la porte (un seul adversaire), F4 un coup à la fois, reculer sous 40 HP ; NE PAS zapper sleep/fire vers l'ouest si le mur est à < 7 cases (rebond). Idéalement attendre T11150 (prayer dispo) avant d'y retourner.
Porté: a EXCALIBUR, c +3 small shield, F blessed +2 GDSM, E faded pall (elven cloak), m hexagonal amulet portée (inconnue, non cursed), L high boots, S rusty orcish helm. b blessed dagger, l orcish dagger. WANDS: y FIRE, T DIGGING, Z SLEEP (copper), K+p spiked (base 150). Daggers : t 4, R 2 elven. d+Y BAGS OF TRICKS. I PICK-AXE. J harp (?). z key. e oil lamp, g oil lamp (presque vide).
Potions: A milky (base 300), M swirly, O clear (water ? BUC ?). Throne room D7 (46-50,21-24) nettoyée, throne disparu (T7658 : +1 St, choc). t 5 daggers, q twisted ring, s scroll THARR, n 2 yellow gems.
Ring: N silver = base 300 (conflict/poly/poly control/TC) NE PAS mettre. Amulet V circular (inconnu). Scrolls W KIRJE & LEP GEX = base 100. Swirly = base 150/200. Scrolls: f cursed FNORD, h LEP GEX VEN ZEA. Gems: v red, B white, C yellowish brown, Q orange, R 2 violet.
LAMP: FAITE. g = maintenant blessed oil lamp (allumée, s'use). Historique : g = MAGIC LAMP (UNCURSED confirmé à l'altar D3, T1648) (certain : le type "oil lamp" est déjà découvert via e = oil lamp de départ, donc
"lamp" non identifiée = magic lamp). Pas cursed (le little dog l'a portée). BUC inconnu : blessed 1/3, uncursed 2/3.
NE PAS #rub avant de la savoir BLESSED (altar) ou de l'avoir bénie (holy water). Blessed #rub = 80 % wish.
Wish prévu : "blessed +2 gray dragon scale mail".
Dangers : aucun pour l'instant.

## DEATH (T12362)
Tuée par un giant mimic dans le zoo du dernier niveau de Sokoban (Dlvl 3 affiché), XL9, HP 0(84), AC4 (sans armure de corps).
Enchaînement : zoo nettoyé depuis la porte (mumak, cockatrice, leocrotta, nymph...), mais : pyrolisk+gargoyle+werewolf dans le couloir → HP 3 → prière T11310 ;
black lights (Hallu x2) ; werewolf (forme d) m'a mordue pendant l'Hallu → lycanthropie ; transformation → GDSM DÉTRUITE ; giant mimic caché sous l'or m'a collée
deux fois ; guérie par prière T12311 ; en retraversant le zoo vers le prix (43,23) le 2e giant mimic m'a collée, HP 30 → 8 pendant un rest2 sur Elbereth ;
dernier recours zZ7 : la wand of sleep était VIDE (0:0) → « Nothing happens », puis le « 7 » a été lu comme une attaque au corps à corps → morte.
Identifié à la mort : V = AMULET OF LIFE SAVING (jamais portée !), u = RING OF PROTECTION FROM SHAPE CHANGERS (aurait bloqué la lycanthropie), N = ring of conflict,
q = cursed ring of teleportation, K = wand of make invisible, X = scroll of teleportation, s = blessed stinking cloud, f = cursed enchant weapon.

## Lessons (mort)
- Porter les amulettes inconnues non maudites quand on n'a rien de mieux : l'amulette V (circular) était une LIFE SAVING. Tester/porter tôt (m hexagonal = versus poison, remplaçable).
- Mettre les anneaux inconnus non maudits (à l'altar) un par un pour les identifier : u = protection from shape changers aurait sauvé la GDSM.
- Compter les charges des wands d'urgence ; une wand zappée souvent peut être à 0 : « Nothing happens » + la touche suivante part en mouvement/attaque. Envoyer z, lettre, direction SÉPARÉMENT et relire.
- Sokoban top : 2 GIANT MIMICS (sokoban.des : m_object boulder / objets). Chaque '$' ou objet du zoo peut être un mimic : traverser en regardant (farlook) et jamais s'arrêter/fouiller à côté d'un objet suspect ; les tuer de loin (daggers) ou pas du tout.
- Les helpers de repos (rest2) doivent relire les HP à CHAQUE bloc ; avec --raw l'état du parseur changeait : mon rest2 a laissé passer 30 → 8 HP. Sous 50 % HP ne jamais faire de repos en blocs à côté d'un monstre hostile.
- Elbereth ne tient pas : le relire (`:`) avant chaque bloc de repos ; il s'efface.

## Plan
FAIT : wish GDSM (T4354), Excalibur (T4496 ; les 2 fountains de D3 ont disparu). ENSUITE : Minetown (Mines depuis D4 '>' 62,15 ; attention level teleport trap Mines 2 ~27,21), Sokoban (up depuis Oracle-1), nourriture !
0. (T4000) Sacrifier un corpse frais sur l'altar D3 : si pas de « hopeful feeling » → prayer timeout 0 → poser m (water) sur l'altar, #pray → holy water → #dip g dans la holy water → #rub g (80 % wish).
1. Trouver un altar (BUC de g) ; si blessed → #rub (à XL bas, 20 % djinni sans wish mais jamais hostile si blessed... blessed: 80% wish, 20% autre (pet/peaceful/vanish/hostile rnd(4))).
2. Sinon : obtenir holy water (acheter, ou water sur altar co-aligné + prayer), #dip g.
3. Allumer g (apply) comme lumière infinie dans les Mines.

## Carte
D6 = ORACLE : '<' 22,15, '>' 75,12. D7 : '<' 6,20 (arrivée), throne room 46-50,21-24, SOKOBAN '<' 62,13 (petite salle 60-64,12-17, atteinte en creusant au nord depuis 63,22).
D5 main : '<' 41,25, '>' 48,12 (explorée + creusée). ERREUR corrigée : Sokoban = niveau SOUS l'Oracle (dungeon.def : oracle + 1, up) → Dlvl 7. D6 : '<' 22,15.
MINES : ORCISH TOWN (orcs « of Aigoraz » vus en Mines 3 = D7, T4947) → pas de Minetown. Mines 2 (D6) : '<' 20,15, '>' 54,24, LEVEL TELEPORT TRAP 27,21.
D4 : '<' 14,23, '>' 62,15, fountains 14,15 et 28,14, porte cachée 43,16 (trouvée), coffre vide 69,15 (piège gaz).
D3 : '<' 64,14, ALTAR CHAOTIC (Loki) 67,14 (2 conversions ratées T2087, T2203), '>' 42,28, sink 42,16, fountains 13,24 et 77,26.
  GENERAL STORE (Annootok) 55-64,24-26, porte 62,23 : COPPER WAND 233 (= base 175 : cold/fire/lightning/sleep), 2 bags 133/178 (base 100 : holding/oilskin/tricks !), ruby potion 400 (base 300), cloudy 178, VELOX NEB 267, PRATYAVAYAH 133, READ ME 178, food ration 60. Puce et white = base 50 (vendues).
D1 : '<' 51,15, '>' 71,16.
D2 : '<' 70,12, '>' 45,13 ; HEALTH FOOD STORE (Tsurphu) 73-77,22-25 porte 77,21 : food ration 60 zm, READ ME = food detection (133), bubbly = fruit juice.

## Lessons
- T11478 : LYCANTHROPIE = forme werewolf (d, taille medium non humanoïde) qui BRISE l'armure de corps et déchire la cape : GDSM perdue. Dès « You feel feverish » sans prière dispo : ENLEVER l'armure de corps/cape précieuses et les porter à la main jusqu'à la guérison (prière, holy water, wolfsbane). Ne jamais mêler un werewolf en forme d : le tuer au sleep/à distance.
- T11308 : ZAPPER une wand depuis Elbereth l'efface aussi (« You feel like a hypocrite », -align). Pyrolisk + gargoyle + werewolf alignés dans un couloir m'ont descendue à HP 3 → prière. Dans un couloir en ligne droite, le pyrolisk voit loin : sortir de sa ligne AVANT de se reposer.
- T10143 : FAINTED pendant les poussées Sokoban (sokoraw/sokostep ne regardent pas la faim, un dog me mordait). Prière OK (T10144). Vérifier la faim (ligne 34) avant CHAQUE étape de Sokoban.
- (orchestrateur) HP ALARM : session.py refuse les touches si HP a baissé de 1/5 et < 60 % ; lire l'écran, décider, puis `slots/5/session ack-hp` (jamais dans une boucle).
- T7160 : wand of SLEEP zappée en diagonale près des murs : le rayon a rebondi et M'A ENDORMIE au milieu d'une meute (werejackal + jackals). Zapper sleep/fire seulement en ligne droite dégagée, jamais vers un mur proche. Werejackal m'a mordue (forme jackal) : surveiller « You feel feverish » → prier (lycanthropie = major trouble).
- T4630 : gf "kh" a frappé un DWARF PEACEFUL (F ne demande pas confirmation) → il devient hostile, tué. Dans les Mines : farlook AVANT gf, ne jamais mettre G/h dans gf sans vérifier.
- Level teleport trap dans Mines 2 (Dlvl 6, vers 27,21 '^') → renvoyée à Dlvl 1.
- Milky potion = base 300 (offre 113) : gain ability/gain level/paralysis. Dark green = base 150 (vendue). Wand tin = fire.
- T744 : prayer Hungry avec timeout 0 → « Tyr is pleased » mais faim NON réparée : en début de partie l'alignment record est < STRIDENT, action=1 ne répare que les MAJOR troubles (Weak). Prier pour la faim seulement quand Weak.
- Depuis 13:15 les outils du slot tournent sur le worker : lancer mes helpers avec slots/5/w ./helper ; dans mes helpers appeler scripts/go, scripts/explore.py directement (les wrappers slots/5/* re-sshent depuis le worker : Host key verification failed).

## Sokoban (niveau 1 = variante 1a de nethackwiki ; offset écran = wiki +33 en x, +15 en y)
Boulders : A 38,17 B 39,17 C 44,17 D 39,18 E 40,18 F 43,18 G 45,18 H 42,20 I 40,23 J 41,23 K 42,23 L 43,23.
Solution wiki : A d | B rrrr | H dd | J u | I l* | L u | K llll* | L dlllllll* | H dlllllll* | J dllllllllu* |
F r | B ddlddddlllllllluu* | G dllldddddllllllllluuu* | F llddddllllllllluuu* | C ddlldddddllllllllluuuuu* | E urrrddlddddllllllllluuuuuu*
Progrès : niveau 1 RÉSOLU (T8405). Niveau 2 RÉSOLU (T8954). Niveau 3 = variante 3a (offset x+31,y+15), plan slots/5/soko3.txt (slots/5/w ./sokostep N slots/5/soko3.txt). NIVEAU 3 RÉSOLU T9319. Niveau 4 = variante 4b (offset x+27,y+13), plan slots/5/soko4.txt (31 étapes). Niveau 4 : trous tous bouchés T10319. Zoo à nettoyer. Si un monstre lointain bloque --execute : slots/5/w ./sokoraw X Y PUSHES. Niveau 2 = variante 2b (offset x+25, y+15), plan dans slots/5/soko2.txt, exécuter slots/5/w ./sokostep N.
