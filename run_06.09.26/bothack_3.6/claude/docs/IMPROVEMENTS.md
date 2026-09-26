# IMPROVEMENTS — plus de 100 pistes pour augmenter le taux d'ascension et retirer les aides

État au 2026-09-23. Point de départ :
- **1 ascension complète sur ~85 parties continues** (≈ 1-2 %) ;
- 2 ascensions sur scénario `planes` ;
- aides actives : invincibilité, anti-famine, kit.

Le fonctionnement du bot est décrit dans `docs/MEGADOC.md`.

---

## 0. Ce que disent les données (point d'appui)

**Ce que signifie « 52 630 morts »** : ce ne sont pas des parties perdues.
Avec l'invincibilité, chaque fois que le héros *aurait dû mourir*, le moteur
annule la mort et le journalise (événement `lifesave`). Le chiffre est la
somme de ces morts annulées sur **toutes** les parties des séries continues
full-c01, full-c02 et full-c04, soit ~85 parties et ~600 par partie. La
partie ascensionnée en a eu 506. Sans l'aide, chacune de ces morts aurait
terminé la partie. C'est donc la mesure du chemin qui reste pour jouer sans
invincibilité, et surtout de **où** et **par quoi** le bot meurt.

Détail sur les séries continues full-c01, full-c02 et full-c04 :

| mesure | valeur |
| --- | --- |
| **total** | **52 630**, soit ~600 par partie ; la partie ascensionnée : 506 |
| par profondeur | Dlvl 1-10 : 2 403 (5 %) ; 11-25 : 4 309 (8 %) ; **26-45 : 40 331 (77 %)** ; 46+ : 4 520 (9 %) ; Plans : 1 067 (2 %) |

**Tueurs principaux** :

| tueur | morts |
| --- | --- |
| **xorn** | 8 545 |
| nalfeshnee invisible | 2 738 |
| **nuage de gaz** | 1 812 |
| xorn invisible | 1 471 |
| baluchitherium | 1 452 |
| démon d'eau | 1 380 |
| marilith | 1 296 |
| dragon d'argent | 1 290 |
| diable osseux | 1 149 |
| golem de fer | 1 121 |
| Olog-hai | 1 024 |
| jabberwock | 1 009 |
| … | … |
| **Demogorgon** | 890 |
| **le Sorcier invisible** | 575 |

**Entonnoir** (full-c01, 45 parties) :

| étape | parties |
| --- | --- |
| Château | 37 |
| Livre | ~10 |
| Amulette | 4 |
| Plans | 1 |
| Ascension | 1 |

Principales pertes :
- limite de temps (6 h) ;
- vol de l'Amulette ;
- Terre et Air ;
- fixations et blocages divers.

**Conclusion** : sans invincibilité, le bot meurt surtout **en Gehennom**, face
à des **monstres invisibles ou qui traversent les murs**, et aux **nuages de
gaz**. Le début de partie est déjà presque viable. C'est là qu'il faut porter
l'effort, pas sur un grand nombre de petits cas.

Chaque piste est notée **[gain attendu / effort]**, de 1 à 3.

---

## A. Mesure, infrastructure, reproductibilité (1-12)

1. **Enregistrer toutes les parties** (`--record`) et ne garder la trace que
   des parties intéressantes (ascension, Astral, Plans, crash). Le replay de
   chaque réussite est alors garanti. [3/1]
2. **Déterminisme strict** : fixer `PYTHONHASHSEED` dans `rungame`, pour que
   seed + code donnent toujours la même partie, même si un ordre de set/dict
   dépendait du hash. [3/1]
3. **Tableau de bord des séries continues** : entonnoir par étape, taux par
   étape, tueurs principaux, top-10 des signatures d'échec, mis à jour à
   chaque point. [2/2]
4. **Signatures d'échec normalisées par cause** (raison BotHack sans
   coordonnées + dernier message du jeu) au lieu de la raison tronquée : les
   « fixation examining tile » cachent 10 causes différentes. [3/1]
5. **Détection automatique des prompts inconnus** : alerte dès qu'un prompt
   dépasse 10 occurrences sur une série. La leçon des 12 000 « Attach your »
   ignorés. [3/1]
6. **Rejeu jusqu'au tour N** : `rungame --until-turn N --record`, pour
   obtenir un replay et un `trace.jsonl` complets autour d'un échec, sans
   rejouer toute la partie. [3/1]
7. **Sauvegarde et reprise en cours de partie** : le mode `SAVE` de
   NetHack, piloté par le harnais, pour repartir d'un état juste avant un
   blocage et tester un correctif en minutes. [3/3]
8. **Bibliothèque de scénarios de régression** construite depuis les échecs
   réels (sauvegardes de parties réelles, pas le mode wizard) : chaque bug
   corrigé devient un test rejoué à chaque version. [3/2]
9. **Versionner le code dans git** et écrire le hash dans chaque manifest
   (aujourd'hui `git_head: null`) pour savoir exactement quel code a produit
   quelle partie. [2/1]
10. **Passage à l'échelle Vast AI** : image Docker (moteur headless + Python),
    rapatriement des seuls résumés et des traces intéressantes. 1 000
    parties par jour permettent de mesurer des taux de 1 % avec précision.
    [3/2]
11. **Budget par partie adaptatif** : couper tôt une partie qui piétine
    (pas de nouvelle étape depuis 20 000 tours) et donner plus de temps à
    celles qui progressent (Amulette obtenue : +6 h). [2/1]
12. **Tests A/B statistiques** : deux versions sur les mêmes seeds, avec
    comparaison de l'entonnoir, avant d'adopter un changement de stratégie.
    [3/2]

## B. Fiabilité du contrôle (13-24)

13. **Audit systématique des prompts et messages 3.6** : extraire tous les
    `yn_function`, `getobj`, `pline` du C 3.6.7 et les confronter aux regex
    BotHack (script `tools/audit_messages.py` à étendre aux prompts). [3/2]
14. **Table des refus sans tour de 3.6** (« You can't… », « Never mind »,
    « cannot be confined »…) générée depuis le C, pour que le veto soit
    exhaustif. [2/1]
15. **Farlook plus économe** : ne pas examiner les monstres vus par
    télépathie à plus de 8 cases. C'est la première action en volume
    (50 %+ des requêtes sur les Plans). [2/1]
16. **Résolution des fixations « examining tile »** : après deux `:` sans
    changement, marquer la case comme connue. C'est la première cause
    d'arrêt restante. [3/1]
17. **Repli de ramassage** : si le menu ne contient pas le libellé voulu,
    comparer par nom normalisé (sans BUC, prix ni « named ») avant
    d'abandonner. [2/1]
18. **Identification robuste** : trouver le fait faux qui élimine toutes
    les identités (logs `identity facts exclude…`) ; probablement la lecture
    des découvertes `\` en 3.6. [2/2]
19. **Menus de plus d'une page et menus « PICK_ANY »** : test unitaire par
    type de menu 3.6 (ramasser, déposer, #loot, #enhance, #name). [2/1]
20. **Horloge du jeu vs requêtes** : un détecteur « même action, tour
    identique » par type d'action, avec récupération spécifique (pas
    seulement l'arrêt). [2/1]
21. **Mémoire des monstres par niveau** : garder les monstres connus d'un
    niveau quand on le quitte, marqués « vus au tour T », pour retrouver
    Vlad, le némésis ou le Sorcier. [3/2]
22. **Cohérence carte/mémoire** : si le rendu d'une case contredit la
    mémoire du bot depuis plus de N tours, faire confiance à l'écran
    (chaîne ≠ autel, rocher ≠ monstre). [2/2]
23. **Gestion générique « objet d'objectif introuvable »** : quand un objet
    d'invocation manque, remonter la liste des jalons `item_lost` et aller
    au dernier lieu connu. [3/2]
24. **Watchdog des handlers** : compter les exceptions par handler et
    désactiver temporairement un handler qui plante en boucle (le crash Kop
    a coûté des parties entières). [2/1]

## C. Vitesse (25-34)

25. **Profil par étape** (Gehennom, Plans) à chaque version, pour garder un
    budget ≤ 50 ms par décision. [2/1]
26. **Farlook et `look` groupés** : un seul `;` par monstre nouveau et par
    niveau, pas à chaque changement de glyphe. [2/1]
27. **Pathfinding incrémental** : réutiliser l'arbre de Dijkstra entre deux
    décisions si la carte a peu changé. [3/3]
28. **Navigation hiérarchique** (salles et couloirs) sur les grands niveaux
    de Gehennom, au lieu d'un Dijkstra sur 1 680 cases. [2/3]
29. **PyPy** pour le bot : BotHack est du Python pur, gain ×3 à ×5
    probable. [3/2]
30. **Réduire les copies persistantes** (`update_in` en chaîne) sur les
    chemins chauds : regrouper les mises à jour d'un tour, comme pour le
    suivi des monstres. [2/2]
31. **Commandes groupées** : `travel` (`_`) pour les longs déplacements
    connus au lieu de pas unitaires, avec interruption sur événement. [3/2]
32. **Compter N** pour les recherches et attentes (`20s`), déjà partiel ;
    l'étendre aux attentes de guérison. [1/1]
33. **Compiler les prédicats chauds** (`walkable`, `explorable`) en tables
    numpy par niveau. [2/2]
34. **Moins de journaux par requête** : l'anneau et `live.json` coûtent en
    fin de partie ; échantillonner quand rien ne se passe. [1/1]

## D. Début de partie et survie réelle (35-44)

35. **Mesurer d'abord** : lancer des séries **sans invincibilité jusqu'au
    Dlvl 10**. Il n'y a que 5 % des morts annulées dans cette zone, donc
    c'est le premier palier à gagner. [3/1]
36. **Réactiver la retraite et la prière** de BotHack (tactiques
    « normales ») sur les niveaux sans aide : elles sont désactivées en mode
    assisté. [3/1]
37. **Elbereth 3.6 correctement exploité** : graver dans la poussière avant
    un combat difficile contre les monstres qui la respectent, sans attaquer
    depuis la case. [2/2]
38. **Gestion des PV** : se retirer vers l'escalier, boire des potions de
    soin identifiées, prier quand le seuil 3.6 est atteint. [3/2]
39. **Sokoban sûr** : BotHack le réussit déjà. Vérifier les pertes de temps
    et les pièges 3.6 (air currents). [1/1]
40. **Mines** : Minetown, temple et achat de protection (déjà dans
    BotHack) ; éviter les Mines profondes sans lumière. [1/1]
41. **Soin des maladies et poisons** sans aide : licorne, prière,
    eucalyptus. [2/1]
42. **Gestion de la charge** : les prompts « trouble lifting » corrigés ;
    ajuster les seuils de ramassage pour rester non chargé. [1/1]
43. **Excalibur tôt** : Valkyrie, trempage à XL5 ; déjà dans BotHack,
    vérifier le taux de réussite. [2/1]
44. **Choix de rôle** : la Valkyrie naine est le meilleur rôle ; garder le
    Samouraï en second pour comparer. [1/1]

## E. Milieu de partie : Méduse, Château, Vallée (45-54)

45. **Méduse sans réflexion** : serviette ou bandeau obligatoire avant le
    Dlvl 21 ; le bot s'est pétrifié en boucle après la perte de l'amulette
    de réflexion. [3/1]
46. **Traversée de Méduse** : lévitation ou bottes de marche sur l'eau ;
    garder une seconde source de lévitation (la perte de l'anneau a bloqué
    2 parties sur une île). [3/1]
47. **Château** : la baguette de souhaits, et des **souhaits orientés
    survie** : 2 × armure dorée (SDSM si pas de réflexion), amulette de vie,
    anneau de liberté d'action et résistances. BotHack a sa liste ;
    l'adapter à 3.6. [3/2]
48. **Trappe du Château** vers la Vallée : fiable ; vérifier le temps
    perdu. [1/1]
49. **Protection achetée** aux prêtres : CA −20 ou mieux avant Gehennom.
    [2/1]
50. **Enchanter l'armure** : parchemins d'enchantement lus en portant
    l'armure ; BotHack le fait, vérifier la fréquence. [2/1]
51. **Clé de squelette et portes** du Château : éviter les coups de pied
    inutiles (les coups de pied dans un mur ont été corrigés). [1/1]
52. **Anneau de régénération et de liberté d'action** portés dès qu'ils
    sont identifiés. [2/1]
53. **Voir l'invisible** (anneau, potion bénie, casque de télépathie
    + cécité) : priorité haute, beaucoup de tueurs sont invisibles. [3/2]
54. **Résistance au poison** : c'est le « nuage de gaz », 1 812 morts ;
    manger des cadavres qui la donnent, souhait, ou éviter les nuages. [3/2]

## F. Gehennom, quête, Vlad, tour du Sorcier (55-68)

55. **Stratégie anti-xorn** (8 545 morts, premier tueur) : ils traversent
    les murs. Il faut une CA très basse, voir l'invisible pour les xorns
    invisibles, ou fuir par l'escalier plutôt que combattre dans les
    couloirs. [3/2]
56. **Démons majeurs** (nalfeshnee, marilith, pit fiend, Demogorgon) : ne
    pas combattre ce qui n'est pas sur le chemin ; `#pray` ou Elbereth
    selon le cas ; objets anti-démons. [3/2]
57. **Traverser Gehennom vite** : descendre par les labyrinthes connus
    (creuser vers le bas quand c'est permis) plutôt qu'explorer. 77 % des
    morts sont là, donc moins de temps passé = moins de morts. [3/2]
58. **Mémoire des niveaux de Gehennom** : cartographie connue de Juiblex,
    Orcus, Baalzebub, Asmodeus ; ne pas les explorer si ce n'est pas
    nécessaire. [2/2]
59. **Quête plus tôt et mieux** : la Cloche (19/32 au mieux). Traquer le
    némésis dès l'arrivée, avec les portes et la mémoire des monstres.
    [3/2]
60. **Vlad** : le Chandelier (11/32). Carte fixe de la tour, portes du
    sommet, attaque de Vlad ; il est souvent derrière une porte. [3/1]
61. **Bougies** : en ramasser 7 tôt (Minetown, Izchak) ou les souhaiter ;
    vérifier qu'elles sont bien fixées (prompt corrigé). [2/1]
62. **Tour du Sorcier** : le Livre (14/32). Trouver le portail des faux
    niveaux, creuser vers la tour, tuer le Sorcier. [3/2]
63. **Porte secrète supposée** : la limite de 60 recherches est en place ;
    vérifier qu'elle ne cache pas de vraies portes secrètes. [1/1]
64. **Niveaux « no novelty » en Gehennom** (~10 parties par série) :
    analyser chaque cas, souvent une cible que le bot ne sait pas
    atteindre. [2/2]
65. **Lévitation maudite** : parchemin de délivrance de malédiction ou eau
    bénite gardés en réserve. [2/1]
66. **Contrôle des objets volés** : nymphes, et Sorcier pour la Cloche, le
    Livre et le Chandelier. Poursuivre et tuer le voleur, grâce à la mémoire
    `item_lost`. [3/2]
67. **Magic mapping** et cristal : parchemins de cartographie utilisés en
    Gehennom pour trouver l'escalier directement. [2/1]
68. **Creuser vers le bas** en Gehennom quand c'est permis : le moyen le
    plus rapide pour descendre. [2/1]

## G. Invocation, Sanctuaire, remontée (69-80)

69. **Remontée rapide** : de l'escalier du Sanctuaire au Dlvl 1, le
    trajet est connu. Utiliser `travel` et la mémoire des escaliers ; le
    Sorcier vole pendant les longues remontées. [3/2]
70. **Anti-vol de l'Amulette** : le Sorcier la vole sur contact. Il faut le
    **tuer à vue** (il revient), le tenir à distance (Elbereth ne marche pas
    sur lui), ou porter une arme efficace (Excalibur). [3/2]
71. **Récupération de l'Amulette volée** : suivre le Sorcier, qui téléporte
    vers l'escalier du niveau. Aller directement à l'escalier ou au
    portail. [3/2]
72. **Force mystérieuse** (Gehennom, Amulette portée) : elle renvoie vers
    le bas. Prévoir de remonter plusieurs fois, sans considérer cela comme
    un blocage. [2/1]
73. **Invocation fiable** : sur le carré vibrant, allumer le Chandelier,
    sonner la Cloche, lire le Livre. Ordre et BUC vérifiés, pas de
    Chandelier maudit. [2/1]
74. **Grand prêtre de Moloch** : le combat pour l'Amulette. Déjà réussi ;
    mesurer le taux. [1/1]
75. **Sanctuaire** : ne pas y rester ; sortir par l'escalier dès que
    l'Amulette est prise. [1/1]
76. **Vérification « vraie Amulette »** : BotHack nomme l'Amulette réelle
    `REAL` ; vérifier le cas des fausses Amulettes de 3.6. [1/1]
77. **Budget de temps** : une partie avec l'Amulette mérite +6 h (piste
    11). [2/1]
78. **Priorité à la remontée** : désactiver les détours (ramassage,
    identification, boutiques) une fois l'Amulette en main. [2/1]
79. **Escalier Dlvl 1** : l'Amulette doit être hors du sac et portée,
    sinon le jeu propose de quitter le donjon (risque d'abandon). Test
    dédié. [2/1]
80. **Prière et invocation** : Luck > 0 (pierre de chance des Mines) pour
    éviter les ratés du jeu. [1/1]

## H. Plans et Astral (81-92)

81. **Terre** : creuser vers la zone chaude de l'Amulette ; les
    élémentaires de terre traversent la roche. Mesurer par scénario
    (plusieurs scénarios y restent bloqués). [3/2]
82. **Air** : nuages et élémentaires d'air, avec l'engloutissement déjà
    traité. Portail côté est (logique BotHack) ; vitesse et lévitation.
    [3/2]
83. **Feu** : lave, résistance au feu (GDSM ne la donne pas), bottes de
    marche sur l'eau ou lévitation. [2/2]
84. **Eau** : bulles d'air mobiles, magical breathing ou lévitation. La
    carte mémorisée « tout eau » trompe le bot : oublier la mémoire des
    cases d'eau à chaque tour sur ce Plan. [3/2]
85. **Astral** : aller directement à l'autel de son alignement (cases
    fixes) ; les Cavaliers bloquent. Gérer leur contournement et le temps de
    résurrection. [3/2]
86. **Identifier l'alignement des autels à distance** (farlook sur `_`)
    pour ne pas visiter les mauvais temples. [2/1]
87. **Préparation avant les Plans** : se soigner, se désensorceler,
    remettre la réflexion, et avoir la vitesse, la lévitation, la
    résistance au feu et à la noyade. [3/2]
88. **Parchemin de téléportation confus** et autres « lifts » interdits
    sur les Plans : vérifier que le bot ne gaspille pas de tours. [1/1]
89. **Amulette portée au cou sur les Plans** : c'est fait. Remettre
    l'amulette de réflexion sur l'Astral si elle est plus utile. [1/1]
90. **Scénarios par Plan** (départ Air, Feu, Eau, Astral) pour itérer
    chaque étape en minutes. [3/1]
91. **Combat Astral** : ne jamais taper les Anges pacifiques ; prêtres
    hostiles ; éviter les Cavaliers. [2/1]
92. **Offrande** : vérifier que `#offer` reçoit l'Amulette même si elle est
    en main ou portée. [1/1]

## I. Retirer l'invincibilité (93-110)

Principe : **retirer l'aide étape par étape, en mesurant**, jamais d'un coup.

93. **Invincibilité à budget** : N morts annulées au total (100, puis 20,
    puis 5, puis 0), avec un journal de la mort qui aurait terminé la
    partie. Donne un « taux d'ascension à N vies ». [3/1]
94. **Invincibilité par profondeur** : désactivée aux Dlvl 1-10 d'abord
    (5 % des morts), puis 11-25, puis Gehennom. [3/1]
95. **Invincibilité par étape** : sans aide jusqu'au Château, avec aide
    ensuite ; mesurer chaque tronçon séparément. [3/1]
96. **Tableau « tueur × profondeur »** à chaque série : liste de travail
    pour la survie réelle. [3/1]
97. **Rendre aux tactiques normales** (fuite, prière, Elbereth, repos) les
    niveaux où l'invincibilité est coupée. Elles existent dans BotHack mais
    sont désactivées en mode assisté. [3/1]
98. **Évaluer le danger d'un monstre avant d'engager le combat**, avec les
    dégâts attendus (BotHack a des éléments) ; fuir si les PV ne suffisent
    pas. [3/2]
99. **Amulette de vie** comme vraie assurance : la souhaiter au Château,
    la porter en Gehennom. [3/1]
100. **Liste des morts instantanées** (pétrification, digestion,
     désintégration, étranglement, noyade, lave, slime) avec un contre
     explicite pour chacune : lézard/acidité, réflexion, respiration,
     résistance, prière. [3/2]
101. **Ne plus restaurer les niveaux et PV max drainés** : mesurer combien
     de parties l'invincibilité « nue » laisse en XL bas, puis ajouter
     l'anneau ou la potion de restauration. [2/1]
102. **Anti-slime** : prière ou feu pour se guérir (l'aide le fait
     aujourd'hui). [2/1]
103. **Anti-cerveau (mind flayers)** : casque, voir l'invisible, les tuer à
     distance. [2/2]
104. **Monstres qui traversent les murs** (xorns, fantômes) : se tenir
     dans les pièces, pas dans les couloirs. [2/2]
105. **Nuages de gaz** : résistance au poison, ou quitter la zone ; ne pas
     combattre dedans. [3/1]
106. **Dragons** : réflexion obligatoire, résistances correspondantes. [2/1]
107. **Golems de fer et géants** : ne pas combattre au corps à corps sans
     arme adéquate ; les éviter. [2/1]
108. **Mode « danger »** : si les PV < 30 % et qu'aucune issue sûre
     n'existe, lire un parchemin de téléportation, zapper une baguette de
     téléportation ou d'excavation vers le bas. [3/2]
109. **Mesure finale** : série sans invincibilité, avec anti-famine et kit,
     et taux d'ascension comparé. [3/1]
110. **Ascension sans aucune aide** : série `--no-assist` avec la
     Valkyrie, objectif ultime. Le Sokoban et le Château comme jalons
     intermédiaires. [3/3]

## J. Retirer l'anti-famine et le kit (111-118)

111. **Anti-famine : mesurer d'abord** : seulement 3 interventions dans la
     partie ascensionnée, donc probablement retirable tôt. [3/1]
112. **Réserves de nourriture** : garder des rations ou du lembas et
     manger les cadavres sûrs (BotHack sait le faire). [2/1]
113. **Prière contre la faim** (Weak) quand la prière est disponible.
     [2/1]
114. **Kit : retirer un objet à la fois** et mesurer l'effet de chacun sur
     l'entonnoir : GDSM, réflexion, vitesse, lévitation, sac, pioche. [3/1]
115. **Trouver les objets du kit** : GDSM via souhait au Château, réflexion
     via Perseus ou le bouclier de Méduse, vitesse via souhait, lévitation
     via Sokoban ou souhait. [3/2]
116. **Pioche** : les nains des Mines en portent ; BotHack sait la prendre.
     [2/1]
117. **Sac** : sac de Sokoban (bag of holding au prix). [2/1]
118. **Kit « réaliste »** : n'équiper que ce qu'un joueur a
     raisonnablement au Dlvl 1 (armure de départ), puis mesurer. [2/1]

## K. Nouvelles idées et approches (119-132)

119. **Hybride BotHack + politique apprise** : garder BotHack pour la
     stratégie et apprendre les micro-décisions de combat (fuir, frapper,
     Elbereth, objet) sur des milliers de combats journalisés. [3/3]
120. **Imitation depuis les parties réussies** : les traces `--record`
     donnent des états et actions ; entraîner un modèle sur les décisions
     qui ont mené loin. [2/3]
121. **Recherche locale en combat** : simulation courte (1 à 3 tours) des
     dégâts attendus pour choisir l'action, à la façon des bots
     d'échecs. [2/3]
122. **Planificateur de fin de partie** : un plan explicite (objets manquants,
     positions connues, trajet), recalculé à chaque niveau, au lieu de
     l'enchaînement de handlers. [3/2]
123. **Base de connaissances NetHack 3.6** (monstres : résistances,
     dangers, contre-mesures) générée depuis `monst.c` pour les décisions de
     combat. [2/2]
124. **Base de connaissances des niveaux spéciaux** (cartes `.des`
     compilées) : portails, autels, escaliers fixes, comme nous l'avons fait
     pour l'Astral. [3/2]
125. **Méta-seeds** : choisir des seeds « faciles » pour l'entraînement,
     puis tester sur des seeds aléatoires. [1/1]
126. **Multi-rôles** : Samouraï, Valkyrie humaine, Prêtre ; voir quels
     handlers BotHack sont spécifiques à la Valkyrie. [2/2]
127. **LLM en superviseur** : un modèle qui lit l'état résumé quand le bot
     bloque (fixation, no novelty) et propose une action, journalisée et
     rare. [2/3]
128. **Portage sur NLE** : notre protocole et notre bot sur l'interface
     NLE 3.6.x, pour comparer aux bots de la NeurIPS Challenge. [2/3]
129. **Mode tournoi** : parties comptées uniquement sans mode wizard ni
     scénario, avec la `version` du code et `--record`. [2/1]
130. **Analyse des parties longues** : les parties de plus de 100 000
     tours révèlent des boucles lentes ; les détecter et les corriger. [2/1]
131. **Rapports d'échec automatiques** : pour chaque signature, extraire
     les 50 derniers pas, les messages et l'écran, puis générer une fiche
     prête à corriger. [2/2]
132. **Documentation vivante** : `docs/DEVLOG.md` mis à jour par série,
     avec la raison de chaque correctif. C'est ce qui a permis la
     progression. [1/1]

---

## Plan proposé (ordre)

1. **Semaine 1 — mesurer et fiabiliser**
   - pistes 1, 2, 4, 5, 11, 16 ;
   - `--record` partout ;
   - tableau de bord (3) ;
   - scénarios Air, Feu, Eau (90).
2. **Semaine 2 — taux d'ascension assistée**
   - Cloche et Chandelier : 59, 60, 66 ;
   - remontée et anti-vol : 69-71 ;
   - Plans : 81-85.

   Objectif : 5-10 % d'ascensions assistées.
3. **Semaine 3 — premiers retraits d'aide**
   - invincibilité désactivée aux Dlvl 1-10 : 94, 97, 36 ;
   - anti-famine retirée : 111 ;
   - mesure du taux (93).
4. **Semaine 4+ — survie en Gehennom**
   - voir l'invisible, résistance au poison, anti-xorn, démons : 53-57,
     104, 105 ;
   - invincibilité à budget décroissant (93).

---

# Partie 2 — 100 pistes pour le taux d'ascension **avec invincibilité** (variantes de bot à comparer)

**Cadre** : l'invincibilité reste active. L'objectif est de **finir plus
souvent et plus vite**. Chaque piste est pensée comme une **variante
activable** (drapeau `BOTHACK_VARIANT=...` ou option), pour lancer plusieurs
versions du bot en parallèle sur les mêmes seeds et garder les meilleures.

**Mesures de comparaison** :
- taux d'ascension ;
- tours médians jusqu'à l'ascension ;
- entonnoir (Château → Cloche → Chandelier → Livre → Amulette → Plans →
  Astral) ;
- parties coupées par la limite de temps.

**Rappel des pertes actuelles** (avec invincibilité) :
1. limite de temps, parce que la partie est lente ;
2. Cloche et Chandelier non obtenus ;
3. vol de l'Amulette ;
4. Plans (Terre et Air) ;
5. fixations et blocages.

## L. Profiter vraiment de l'invincibilité (133-147)

133. **« Bulldozer »** : sous invincibilité, ne plus jamais contourner un
     monstre hostile sur le chemin ; tout traverser en frappant. Moins de
     détours, moins de tours.
134. **Ne combattre que ce qui bloque** : désactiver la chasse aux monstres
     hors du chemin (handler `hunt`, combats opportunistes). La mort ne coûte
     rien, le temps si.
135. **Ignorer les monstres lents à distance** : pas de farlook ni de
     combat pour ceux qui ne peuvent pas nous rattraper.
136. **Pas de soin** : ne jamais attendre la régénération ni prier pour les
     PV (inutile sous invincibilité), sauf pour guérir un statut bloquant.
137. **Pas de retraite, jamais** : déjà en partie fait ; vérifier chaque
     handler de fuite restant (escaliers, Elbereth défensif).
138. **Mourir exprès pour se libérer** : englouti, tenu, piégé dans un
     mur, lave… Si la mort annulée remet le héros en état jouable, la
     provoquer plutôt que d'attendre. À tester comme variante.
139. **Nager et marcher dans la lave** si le chemin le plus court y passe :
     la mort est annulée et on ressort de l'autre côté. Variante à mesurer
     avec prudence (objets détruits).
140. **Ignorer les pièges connus sur le chemin** (sauf téléporteurs de
     niveau et trous) : moins de détours.
141. **Désactiver la gestion de la faim** au profit de l'anti-famine :
     ne plus manger de cadavres (gain de temps), en gardant
     l'identification par goût seulement si utile.
142. **Ne plus identifier les objets inutiles à l'ascension** :
     identification limitée aux baguettes, anneaux, amulettes et
     parchemins utiles (souhaits, téléportation, enchantement).
143. **Ne plus visiter les boutiques** : pas de prix, pas d'achats (sauf
     bougies si manquantes).
144. **Ne plus trier l'inventaire** et ne plus déposer sur les autels
     pour le BUC, sauf pour les objets clés. Économie de milliers de tours.
145. **Moins de recherches** de portes secrètes : sous invincibilité,
     creuser tout droit (pioche du kit) plutôt que chercher.
146. **« Speedrun Gehennom »** : creuser vers le bas à chaque niveau de
     Gehennom où c'est permis, jusqu'aux niveaux utiles.
147. **Profil `fast` par défaut** (déjà existant pour les scénarios) :
     pas de retour en arrière, pas d'exploration complète des niveaux
     sans intérêt.

## M. Aller droit aux objets d'invocation (148-165)

148. **Ordre de parcours alternatif** : Château → Vallée → **Vlad d'abord**
     (le Chandelier, le plus manquant) → quête → tour du Sorcier. Comparer
     avec l'ordre actuel.
149. **Ordre alternatif 2** : quête **avant** Méduse (dès XL14). La
     Cloche serait obtenue plus tôt, avant la baisse de vitesse en
     Gehennom.
150. **Quête dès XL14 sans exiger DSM ni lévitation** (conditions
     actuelles de BotHack) : l'invincibilité remplace l'armure.
151. **Carte connue de la tour de Vlad** (`tower1-3.des`) : aller
     directement à la salle de Vlad au sommet, comme pour les autels de
     l'Astral.
152. **Cartes connues des niveaux de quête Valkyrie** (`Val-goal.des`) :
     aller directement à la salle de Lord Surtur.
153. **Tuer le porteur à vue** : Vlad, le némésis et le Sorcier ciblés en
     priorité absolue dès qu'ils sont vus, avant tout autre handler.
154. **Ramasser ce que lâche le porteur** avant toute autre action (la
     Cloche, le Chandelier et le Livre tombent au sol).
155. **Souhaiter les bougies** au Château si moins de 7 sont connues, pour
     éviter la chasse aux bougies.
156. **Bougies achetées** à Izchak (Minetown) systématiquement.
157. **Vérifier les 7 bougies fixées** avant de descendre au Sanctuaire,
     avec les prompts corrigés.
158. **Portail de la tour du Sorcier** : aller directement au faux niveau
     connu (`fakewiz`) et au portail, sans explorer.
159. **Creuser vers la tour du Sorcier** depuis le niveau au-dessus
     (technique humaine classique) au lieu de chercher le portail.
160. **Carré vibrant** : le détecter par le message et `#terrain`, au lieu
     d'explorer tout le fond de Gehennom.
161. **Invocation en une séquence** : Chandelier allumé, Cloche, Livre,
     sans handler intermédiaire (la foule peut interrompre).
162. **Sanctuaire éclair** : entrer, frapper le grand prêtre, prendre
     l'Amulette, ressortir.
163. **Mémoire de tous les objets clés vus** (sol, monstres) avec leur
     niveau : planifier leur récupération au lieu de les redécouvrir.
164. **Détecteur d'objets** : parchemins de détection d'objets et cristal
     utilisés dans les niveaux où un objet clé est attendu.
165. **Relance automatique d'une étape échouée** : si la Cloche n'est pas
     obtenue après 3 000 tours de traque, revenir plus tard, plutôt que
     d'abandonner définitivement.

## N. Remontée et Amulette (166-178)

166. **Tuer le Sorcier à chaque réapparition** : handler « Sorcier à
     vue » prioritaire. Il revient toujours, mais chaque mort donne du
     répit.
167. **Arme anti-Sorcier** : Excalibur ou meilleure arme souhaitée au
     Château.
168. **Réflexion toujours portée** pendant la remontée (sorts du Sorcier).
169. **Remonter par `travel`** vers les escaliers connus, sans explorer.
170. **Escaliers mémorisés** : au premier passage, noter l'escalier
     montant de chaque niveau ; la remontée devient un trajet connu.
171. **Ne pas s'arrêter pour les objets** pendant la remontée
     (ramassage désactivé).
172. **Poursuite du voleur** : après un vol, aller directement à
     l'escalier montant du niveau, où le Sorcier fuit.
173. **Ne pas combattre les « covetous » hors du chemin** (ils
     suivent et volent) : les tuer seulement s'ils touchent.
174. **Force mystérieuse** : compter les renvois et ne pas les traiter
     comme des échecs de navigation.
175. **Cadence de l'Amulette** : si elle est volée plus de 3 fois,
     changer de stratégie (rester sur l'escalier, frapper dès
     l'apparition).
176. **Plus de temps pour les parties avec l'Amulette** (+6 h) : le
     harnais le décide automatiquement.
177. **Limite de temps plus longue pour toutes les parties** (8-12 h) :
     plusieurs parties ont été coupées en progression. Variante de
     harnais, pas de bot.
178. **Prioriser le CPU** : baisser la priorité (`nice`) des parties sans
     Amulette quand une partie avec l'Amulette tourne.

## O. Plans et Astral (179-195)

179. **Scénario par Plan** (Air, Feu, Eau, Astral) pour régler chaque
     Plan séparément ; objectif > 80 % par Plan.
180. **Terre : creuser en ligne droite** vers la zone indiquée par
     l'Amulette, sans la logique d'exploration.
181. **Terre : se diriger vers l'est par défaut** (position habituelle du
     portail) avant les indices, à vérifier dans `earth.des`.
182. **Air : se déplacer par grands pas** (`travel`) vers l'est, en
     ignorant les nuages et les élémentaires.
183. **Air : lévitation ou vol permanents** (anneau du kit), pour ne pas
     subir les courants.
184. **Feu : marcher dans la lave** sous invincibilité (piste 139) ;
     sinon lévitation ou bottes de marche sur l'eau.
185. **Eau : oublier la carte mémorisée** à chaque tour (les bulles
     bougent), naviguer seulement sur ce qui est visible.
186. **Eau : se laisser noyer** (mort annulée) plutôt que de rester
     coincé dans une bulle ; variante à tester.
187. **Astral : chemin fixe** vers chaque temple, en contournant le centre
     (Cavaliers).
188. **Astral : identifier l'autel à distance** (farlook) et n'aller qu'au
     bon temple.
189. **Astral : ignorer tous les combats** sauf ceux qui bloquent le
     chemin.
190. **Astral : Amulette en main à l'arrivée** pour offrir dès qu'on est
     sur l'autel.
191. **Préparation avant l'escalier du Dlvl 1** : se soigner des
     statuts, réflexion, vitesse, lévitation prête.
192. **Scénario « Dlvl 1 avec l'Amulette »** : départ au Dlvl 1 avec
     l'Amulette, pour tester l'entrée des Plans et toute la fin.
193. **Détection des portails par la carte** : sur certains Plans, le
     portail est visible une fois découvert ; le mémoriser à vie.
194. **Ne pas s'asseoir sur un faux portail** (boucle « sit » vue sur
     l'Air) : vérifier le message avant de répéter.
195. **Compteur de progression par Plan** : si aucun progrès depuis
     3 000 tours, changer de méthode (creuser, attendre, explorer autrement).

## P. Vitesse de jeu (196-210)

196. **PyPy** : gain ×3 à ×5 attendu sur le bot en Python pur ; variante
     d'exécution à mesurer.
197. **Farlook limité** aux monstres à moins de 8 cases.
198. **Pas de `look` automatique** sur chaque case d'objet déjà vue avec
     le même glyphe.
199. **`travel` pour tous les longs trajets** au lieu du pas à pas.
200. **Compte `n20s`** pour les attentes.
201. **Cache du pathfinding** entre les décisions.
202. **Exploration par zones** plutôt que par cases.
203. **Journaux allégés** (anneau, `live.json`) en fin de partie.
204. **Moins de handlers actifs** en fin de partie (plus de boutiques, de
     farming, d'identification).
205. **Profil par niveau** : si un niveau dépasse 20 000 requêtes, le
     signaler et analyser automatiquement.
206. **Priorités recalculées moins souvent** : `explore_cache` gardé
     plusieurs tours quand rien n'a changé.
207. **Moteur plus rapide** : `-O2`, sans vérifications de debug, en
     headless.
208. **Réduire les copies persistantes** sur les chemins chauds restants
     (update_in).
209. **Un processus par partie, épinglé à un cœur** (affinité CPU) pour
     éviter les migrations.
210. **Mesurer les tours par seconde par étape** dans `progress.jsonl`,
     pour voir où la partie ralentit.

## Q. Idées créatives (211-232)

211. **Suicide stratégique contrôlé** : sous invincibilité, une mort
     annulée remet les PV au maximum ; l'utiliser comme soin gratuit en
     plein combat (se laisser tuer plutôt que fuir).
212. **Portail de niveau et téléportation** : parchemins de téléportation
     confus et pièges de téléportation de niveau pour sauter des niveaux
     de Gehennom.
213. **Baguette d'excavation vers le bas** en série pour descendre
     Gehennom en quelques tours.
214. **Cursed scroll of teleportation** comme ascenseur de niveau.
215. **Souhait de « cursed potion of gain level »** pour remonter d'un
     niveau à travers le plafond pendant la remontée (technique classique).
     Variante : 2 souhaits au Château.
216. **Tenir l'escalier** pendant la remontée : attendre sur l'escalier
     montant et le prendre dès que le Sorcier apparaît.
217. **Monture** : un cheval rapide (Valkyrie) pour se déplacer plus vite
     dans les grands niveaux.
218. **Familier Anti-vol** : garder un familier fort qui tue les voleurs.
219. **Polymorphe contrôlé** en une forme rapide ou volante (souhait
     d'anneau de contrôle et de polymorphie) pour les Plans.
220. **« Mode humain »** : reproduire les routes des speedruns humains
     (dig-for-victory, mines skip) comme variante complète.
221. **Tournoi de variantes** : 10 variantes × 50 seeds en continu, élimination
     des 5 pires chaque jour, mutation des meilleures (algorithme génétique
     sur les drapeaux de variante).
222. **Bandit multi-bras** : allouer plus de parties aux variantes qui
     gagnent (Thompson sampling) pour converger plus vite.
223. **Paramètres continus optimisés** (seuils de fixation, budgets de
     traque, distance de farlook) par recherche bayésienne sur l'entonnoir.
224. **Rejouer les ascensions** avec d'autres variantes sur la même seed,
     pour savoir si une variante accélère la même partie.
225. **Carte de chaleur des blocages** (niveau × position) sur toutes les
     parties : révèle les pièges de navigation récurrents.
226. **Handler « méta »** : si l'entonnoir montre qu'une étape est
     rarement réussie, lui donner plus de budget et de priorité en
     cours de partie.
227. **Seeds difficiles en scénario** : prendre l'état juste avant un
     échec fréquent, via une sauvegarde, et itérer dessus.
228. **Assistant LLM rare** : quand le superviseur détecte un blocage, un
     modèle résume l'état et propose une action BotHack ; journalisé,
     et mesuré contre la variante sans LLM.
229. **Apprentissage des « bons moments de mourir »** : sous invincibilité,
     apprendre quand se laisser tuer fait gagner du temps (données
     `lifesave` + progression).
230. **Double bot** : un deuxième profil de BotHack (plus agressif) prend
     la main quand le premier bloque depuis N tours.
231. **Ascension race** : récompenser les variantes au temps médian
     d'ascension, pas seulement au taux, pour réduire les coupures par la
     limite.
232. **Base de replays** : toutes les ascensions en `--record` ; les
     comparer étape par étape entre variantes (où l'une perd du temps).

## Plan « variantes avec invincibilité »

1. Ajouter un **registre de variantes** (`BOTHACK_VARIANT=a,b,c`) et le
   nom de la variante dans chaque manifest.
2. **Première vague**, chacune sur les mêmes 50 seeds, en série
   continue :
   - A = actuelle ;
   - B = 133+134+147 (bulldozer + fast) ;
   - C = 148 (Vlad d'abord) ;
   - D = 150+152 (quête tôt + carte) ;
   - E = 166+172 (anti-Sorcier) ;
   - F = 196 (PyPy).
3. Garder les 2 meilleures, combiner, puis ajouter la vague suivante
   (Plans, Astral, créatives), avec le tournoi en continu (221-222).
