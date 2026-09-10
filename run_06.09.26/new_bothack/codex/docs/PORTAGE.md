# Portage fidèle de BotHack en Python

## Objectif et état réel

L’objectif demandé est de réécrire tout BotHack en Python, conserver son comportement, puis obtenir une ascension sans mode wizard ni intervention humaine, avec des résultats comparables à l’original. **Cet objectif n’est pas encore atteint.** Le travail présent est un ensemble de modules traduits et vérifiés ainsi qu’un environnement de référence fonctionnel. Il ne constitue pas encore un bot Python capable de jouer une partie complète.

Tout le travail de cet agent se trouve dans `codex/`. Les répertoires voisins `opencode/` et `claude/` sont réservés aux autres agents.

## Original retenu et recherche

- Dépôt : <https://github.com/krajj7/BotHack>, commit `70226b3c8ed12d29c64068aec0acc0ca71d57adf`.
- Code : environ 17 161 lignes de Clojure, auxquelles s’ajoutent les interfaces Java, le terminal JTA et le calcul de visibilité.
- Version prise en charge : **NetHack 3.4.3 avec les patches nethack.alt.org**, explicitement indiquée dans [les instructions de compilation originales](https://github.com/krajj7/BotHack/blob/master/doc/compiling.md).
- L’annonce de l’auteur décrit une ascension automatique le 25 janvier 2015, après introduction du farming de puddings : [annonce et discussion](https://groups.google.com/g/rec.games.roguelike.nethack/c/TOoX7ptqBEQ), [historique du dépôt](https://github.com/krajj7/BotHack).
- Jeu : <https://github.com/altorg/NetHack>, commit historique `b60bd44c46ed263e89fcebafd5d7271c700446e9`, du 17 décembre 2014.

Le BotHack choisi est le dernier commit du dépôt, pas le commit exact de sa première victoire. Le jeu est une révision NAO contemporaine de cette victoire ; je n’ai pas établi qu’il s’agit du binaire exact du serveur de la première ascension. Ces choix sont figés pour rendre les comparaisons locales répétables.

## Comment fonctionne BotHack

Le bot communique avec un véritable terminal, sans lire la mémoire du jeu. JTA produit une grille de 80 colonnes et 24 lignes. Deux lignes inférieures contiennent l’état du personnage ; la carte occupe les lignes 1 à 21. Le scraper distingue messages, menus, questions et commandes. Il utilise notamment des marqueurs de synchronisation `##'` : un simple délai entre les frappes ne reproduit pas ce protocole.

Les événements alimentent un modèle persistant : carte connue, monstres mémorisés, inventaire, identifications, branches, pièges, fraîcheur des cadavres, intrinsics et historique des actions. Une action comporte un déclencheur clavier et souvent un gestionnaire temporaire de questions et d’effets sur le modèle.

`mainbot.clj` enregistre ses décisions avec des priorités numériques. L’offre de l’Amulette passe avant tout, puis l’amélioration des compétences, les urgences, le farming, la retraite, le combat, l’équipement, la nourriture, les objets, la récupération et finalement la progression. Le premier gestionnaire qui propose une action gagne. Changer cet ordre peut changer la survie du bot même si chaque fonction semble correcte isolément.

Les solutions Sokoban sont huit scripts de déplacements, indexés par le nombre de rochers restants. Leur exécution nécessite également navigation, distinction rocher/mimic et mémoire des poussées. Les tables seules ne constituent donc pas un solveur intégré complet.

## Ce qui a été réalisé

| Module Python | Travail présent | Limite |
|---|---|---|
| `position.py` | Coordonnées, directions, distances, voisins et déplacement du curseur | Testé exhaustivement pour les opérations unaires sur les 1 680 positions |
| `frame.py` | Lignes, curseur, messages débordants, couleurs inversées, détection d’engloutissement | Comparaisons avec des frames Clojure |
| `terminal.py` | Adaptateur ANSI `pyte`, couleurs BotHack, lecture/écriture ttyrec | Comparé à JTA sur des séquences ciblées et un extrait réel ; pas de garantie sur toutes les séquences ANSI |
| `scraper.py` | État, reconnaissance des questions, machine de synchronisation, messages et menus à plusieurs pages | Produit une file d’appels ; reste à connecter aux protocoles d’actions et au transport du jeu |
| `item.py` | Traduction du parseur de libellés et de plusieurs prédicats | Les effets des actions et tous les helpers d’inventaire manquent |
| `catalog.py` / données JSON | Export des 1 722 identités d’objets, 376 types de monstres, pluriels et huit scripts Sokoban | Les tables ne remplacent pas la logique de jeu |
| `itemid.py` | Identités initiales, prix, découvertes, contraintes observées, élimination, oubli et réutilisation des noms | Comparaisons sur cas ciblés et générés ; intégration aux événements et cas contradictoires à approfondir |
| `player.py` | État initial, faim, santé, nourriture, inventaire et contenu des sacs, poids et capacité | Équipement, blocages et modèle complet du joueur restent à porter |
| `monster.py` | Reconnaissance par description et glyphe/couleur, construction et prédicats | Le suivi des déplacements et la mémoire des monstres restent à intégrer |
| `mainbot.py` | Premiers helpers : seuils de santé, utilité, choix de nourriture et quelques prédicats de combat | La chaîne de décisions et ses actions restent à porter |
| `tile.py` | Mémoire et transitions des cases, terrain, objets, gravures | Le modèle complet des niveaux et événements n’est pas intégré |
| `pathing.py` | A*, Dijkstra et coûts de base | Les actions de déplacement et la navigation entre niveaux restent à porter |
| `fov.py` | Traduction de l’algorithme Java de visibilité | L’éclairage, l’ESP et la perception des monstres restent à intégrer |
| `delegator.py` | Priorités, événements, réponses, inhibition, remplacement des gestionnaires | Les protocoles complets du jeu restent à connecter |
| `protocols.py` | Registre des événements/questions, encodage oui/non, texte, directions, positions et menus, distribution des appels du scraper | Le transport et les gestionnaires de décisions restent à intégrer ; les actions complètes restent à porter |
| `actions.py` | Commandes des 44 types d’actions ; premiers gestionnaires pour attente, farming, prière, paiement, nettoyage, compétences, arme, carquois, nommage et inventaire ; délégation des actions répétées | Les autres gestionnaires lèvent explicitement `NotImplementedError` ; les requêtes de mise à jour différée doivent encore être intégrées au moteur |
| `defaults.py` | Réponses de repli originales et bornes de priorité | Ne remplace pas les choix de la stratégie ; les réponses absentes restent absentes |
| `benchmark.py` | Lecture du xlogfile NAO et exclusion des victoires wizard/exploration | Aucun taux d’ascension Python mesurable actuellement |

Les fichiers Python traduits portent leur provenance. La licence GPLv2 de l’original est conservée. Le Python d’exécution n’appelle pas le bot Clojure : Java est utilisé uniquement par les outils explicites d’export, de comparaison et d’exécution de référence.

### Synchronisation traduite

`Scraper.feed(frame)` traite une grille de terminal et renvoie une liste ordonnée d’appels. `protocols.dispatch(delegator, call)` distribue chaque appel aux gestionnaires ou écrit les octets demandés. Les gestionnaires pourront réinitialiser le scraper pendant cette distribution ; ils ne doivent donc pas être appelés à l’intérieur de `feed`. En cas d’exception, le scraper restaure son état précédent, comme les références Clojure dans `dosync`.

Exemple de cycle normal, lorsque ni menu ni question ne détourne le protocole :

| Observation | Réaction |
|---|---|
| Les deux lignes d’état semblent complètes | Envoi du marqueur `##'` |
| Le jeu affiche `# #'` devant le curseur | Retour arrière puis deux Entrées |
| La première ligne est effacée | Deux `Ctrl-P` pour consulter les derniers messages |
| Le marqueur `# #` est retrouvé | Mémorisation du curseur et nouveau `Ctrl-P` |
| Le curseur rejoint la position mémorisée | Émission du message, de l’état, de la position, des éventuelles listes et de `full-frame` |
| Des redraws supplémentaires arrivent | Ignorés jusqu’à la prochaine action |

Les actions susceptibles d’ouvrir une demande de direction utilisent un état sans marqueur. Les attaques de farming possèdent également leur propre entrée dans le cycle. Pour les menus à plusieurs pages, les options sont d’abord collectées, les pages rembobinées avec `<`, puis les réponses distribuées page par page ; l’identification reçoit l’ensemble des options fusionnées.

### Actions et mémoire d’inventaire

Une `Action` contient le type original, ses arguments et ses gestionnaires supplémentaires. `trigger()` produit les frappes ; `handler(context)` prépare les effets et les réponses temporaires. Ces deux parties sont vérifiées séparément. Les 44 commandes sont traduites, mais cela ne signifie pas que les 44 actions sont intégrées : la plupart de leurs effets sur le donjon et les identifications restent à porter. `Repeated` délègue son gestionnaire à l’action enveloppée, tout en préfixant ses frappes par le nombre de répétitions. Les gestionnaires ajoutés sont stockés dans l’ordre inverse des ajouts, comme le `conj` Clojure sur le champ initialement nul.

Le gestionnaire d’inventaire relit les libellés, puis transfère les connaissances de l’ancien objet au même emplacement : contenu, verrouillage et bénédiction si le nouveau libellé ne la précise pas. Pour un libellé de plus de 72 caractères, il conserve aussi les indications d’utilisation et de port lorsque l’ancien objet était utilisé. Cette logique par emplacement, même imparfaite, est celle de l’original. `label_to_item` conserve les champs explicitement nuls du record `Item`, tandis que `parse_label` garde son contrat antérieur de simple analyse de texte.

Les gestionnaires portés qui demandent une nouvelle lecture d’inventaire ou une identification automatique appellent des opérations du contexte. Dans les tests, seules ces dépendances sont remplacées par un journal d’appels ; les gestionnaires Clojure s’exécutent sur une véritable instance `BotHack` et leur état final, leurs retours et l’ordre des demandes sont comparés au Python. Le moteur chargé d’exécuter ces demandes n’est pas encore complet.

### Détails conservés intentionnellement

- Une position est adjacente à elle-même dans l’original.
- Une réponse `false` signifie « non » ; elle ne signifie pas qu’aucun gestionnaire n’a répondu. Une collection vide est également une réponse valide.
- L’ordre à priorité égale n’est pas spécifié par l’original. Python conserve l’ordre d’enregistrement ; cela reste une différence possible lorsque des règles se concurrencent à priorité égale.
- `effective-str` associe `18/00…49` à 20 et `18/50…99` à 19. Cette conversion surprenante est conservée et testée.
- L’A* original tronque certains coûts en entiers et peut inclure un objectif non franchissable dans le chemin. Ces comportements sont conservés. Les départages des chemins de même coût nécessitent encore une étude comparative.
- Le ratio de prix reprend l’ordre des divisions entières de Clojure ; une formule simplifiée avec arrondi final donnerait parfois un résultat différent.
- Plusieurs observations de prix produisent des alternatives dans la requête originale ; elles ne sont pas toutes imposées simultanément. Les propriétés distinctes, elles, se cumulent.
- Le choix de nourriture conserve le dernier candidat en cas d’égalité. Le poids des sacs reprend les arrondis par objet de l’original.
- Le scraper attend le curseur et les marqueurs avant d’émettre `full-frame`, ignore ensuite les redraws jusqu’au changement d’action, et rembobine les menus avant de répondre. Ses appels sont collectés puis doivent être exécutés dans l’ordre après le traitement du redraw, pour permettre les réinitialisations déclenchées par une action.
- La reconnaissance des questions conserve leur ordre et les captures : cible attaquée, objet mangé, charge soulevée, prix proposé. Les messages inconnus lèvent une erreur. La première ligne entièrement vide d’un menu provoque aussi une erreur d’index dans l’original.

## Environnement historique

`tools/bootstrap.py` vérifie les révisions des dépôts et prépare Java 8 et la bibliothèque native JTA. Le JDK est téléchargé à une URL versionnée et son SHA-256 est contrôlé. Java 17 provoquait une erreur de compilation de l’ancienne bibliothèque `multiset` ; l’original compile avec Java 8.

`tools/build_nethack.py` compile une copie distincte dans `.build/nethack/` et installe dans `.local/nethack/`. Les sources de référence restent intactes. Les changements apportés au jeu sont limités à l’installation, aux options de compilation modernes `-fcommon -std=gnu89`, et à l’agrandissement du tampon du nom de fichier de compression. Le tampon original de 80 octets débordait avec le chemin du projet ; GDB a localisé le plantage dans `docompress_file`, avant le premier tour. Les patches sont conservés dans `artifacts/`.

L’ancien `HandlerPTY` utilise `execve` sans interpréter les arguments et remplace l’environnement par `TERM=xterm`. Le lanceur de référence crée donc un script exécutable qui définit explicitement `NETHACKOPTIONS` et lance le jeu avec le nom choisi. Le fichier d’options BotHack est recopié sans changement.

## Vérification et essais

```sh
uv sync --extra dev
uv run python tools/bootstrap.py --oracle --game --local-build-tools
BOTHACK_ORACLE=1 uv run python -m pytest --junitxml=artifacts/pytest.xml
uv run python tools/run_original.py --timeout 180 --name Reference1
uv run python -m bothack report .local/nethack/var/xlogfile
```

Sans `BOTHACK_ORACLE=1`, les tests qui nécessitent Java sont explicitement ignorés. Leur absence n’équivaut pas à une validation de fidélité.

L’oracle `tools/oracle.clj` appelle les fonctions originales, y compris certaines fonctions privées, avec des entrées sérialisées. Le pont Python utilise un préfixe de réponse dédié pour empêcher les logs Clojure de décaler les résultats du protocole. Les résultats attendus ne sont pas calculés par le code Python testé.

Les tests du scraper comparent aussi des séquences complètes de redraws. L’oracle exécute la véritable fermeture `new-scraper` et intercepte uniquement ses appels `send` pour enregistrer leur ordre et leurs arguments ; les décisions du scraper restent celles du code Clojure intact. Cela vérifie des scénarios de synchronisation, sans encore valider l’ordonnancement concurrent du bot complet. Le protocole historique qui propose d’effacer une partie existante est traduit ; un futur lanceur Python devra utiliser un nom et un espace de sauvegarde dédiés, comme les essais de référence.

Les protocoles comparent les octets réellement produits par le délégateur original, ainsi que la notification `response-chosen` et l’inhibition. Les tests distinguent une chaîne vide (Échap), une liste vide (sélection vide), `false` et les valeurs vraies selon Clojure comme `0`. Les positions sont converties en déplacements du curseur suivis d’un point ; les réponses textuelles reçoivent un saut de ligne sauf si elles en possèdent déjà un. Les méthodes Python utilisent des underscores, les noms dans la file du scraper restent ceux de l’original.

`tests/fixtures/original-core.json` contient 128 cas capturés auprès du code Clojure, régénérables avec `uv run python tools/freeze_cases.py`. Ce corpus permet une vérification partielle hors ligne : objets, prix, menus, prompts textuels et commandes des 44 types d’actions. Il ne remplace pas la suite différentielle complète. Les rapports de la dernière exécution sont conservés dans `artifacts/tests.log` et `artifacts/pytest.xml`.

Vérification du 6 septembre 2026 après ce lot : **381 tests réussis avec l’oracle en 122,71 secondes** ; sans Java, **95 réussis et 286 ignorés**. Ces nombres désignent des tests de modules et de protocoles, pas des parties gagnées. Le compteur d’ascensions Python reste à zéro.

Lot du 7 septembre 2026 : **581 tests réussis dans la suite complète avec l’oracle, en 108,30 secondes**. Après la correction des gestionnaires pour lire le nouvel état du contexte, les **70 tests d’actions** ont été relancés avec succès, dont trois nouveaux tests sur ce remplacement d’état. La collection actuelle compte donc 584 tests ; son exécution sans Java donne **145 réussis et 439 ignorés**. Les commandes des 44 types d’actions et les réponses de repli sont comparées au code original ; aucune partie Python complète ni ascension Python n’a encore été obtenue.

Pour comparer l’émulation sur un enregistrement réel :

```sh
uv run python tools/compare_ttyrec.py artifacts/original-Ref343d/1788709343666.ttyrec --records 500
uv run python -m bothack replay artifacts/original-Ref343d/1788709343666.ttyrec --records 500
```

Sur cet extrait, 500 enregistrements ont été comparés sans différence de texte, de couleurs ou de curseur. Cela valide cet extrait, pas toutes les situations possibles du jeu.

La partie originale `Ref343d`, sans mode wizard, a duré 2 986 tours : niveau maximal 6, score 4 305, mort contre une fourmi soldat. Le résultat provient du `xlogfile` du jeu. Les tentatives précédentes ont échoué au lancement et ne constituent pas des défaites du bot. Le premier lecteur de résultats cherchait des tabulations alors que cette version emploie des deux-points ; le lecteur a été corrigé, et le rapport actuel lit les deux formats. Le fichier `result.json` de cette première partie conserve son ancienne classification `no-game-result` ; consulter le xlogfile et le rapport corrigé pour son résultat réel.

L’ancienne cible `make install` supprimait le répertoire d’installation à chaque invocation. La vérification du bootstrap a ainsi supprimé le xlogfile global de la première partie ; son export JSON `artifacts/benchmark-corrected.json`, les journaux et le ttyrec restent conservés. Le script utilise désormais `make update` pour toute installation existante, et chaque nouvelle partie archive sa propre ligne brute de xlogfile dans son répertoire de résultats.

## Monde, événements et actions intégrés au modèle Python

Les modules `level`, `dungeon`, `tracker`, `game`, `game_events` et `runtime`
portent maintenant les cartes persistantes, les branches, 33 plans originaux,
la mémoire des monstres, la mise à jour du champ de vision et les événements
du jeu. Le runtime ordonne les mises à jour différées et installe les
gestionnaires temporaires des actions. Il manque encore leur connexion à une
chaîne complète de jeu et à la stratégie originale.

`movement_actions.py` contient les premiers gestionnaires de déplacement,
attaque, recherche, portes, coups de pied et position assise. Leurs déclencheurs
sont comparés à l'original ; leurs effets n'ont pas encore une couverture
différentielle complète.

Le 9 septembre, les gestionnaires `Wear`, `PutOn`, `Remove` et `TakeOff` ont
été ajoutés : demandes d'inventaire, identification éventuelle, mémorisation de
l'utilisation et correction des champs d'équipement après refus du jeu.
Les tests utilisent les véritables caractères Clojure pour les emplacements
d'inventaire. **106 tests d'actions réussis**, dont 36 cas d'équipement avec
et sans confusion, étourdissement, hallucination ou cécité, sont conservés dans
`artifacts/equipment-tests.log`.

`stairs_actions.py` porte les gestionnaires d'ascension et de descente :
choix de branche, passage vers Vlad, tags de niveau, numérotation des branches
inconnues et mémorisation différée du passage à la nouvelle position.
**32 comparaisons avec le Clojure réussissent** dans `artifacts/stairs-tests.log`,
avec et sans familier, y compris Sokoban, mines, quête et entrée dans End Game.
Ce sont des scénarios d'état synthétiques, pas des passages réellement joués.

Une particularité de l'original est conservée : `mark-branch-entrance` utilise
`mapcat` sur les résultats de `monster-at`, donc parcourt les entrées des
records au lieu des monstres. Les prédicats de familier/suiveur ne déclenchent
alors pas le marquage des cases voisines annoncé par le commentaire Clojure.
Les scénarios avec familier vérifient que seule la case d'arrivée est marquée.

`consumption_actions.py` porte `Eat`, `Quaff` et `Offer`, notamment les réponses
aux choix d'objets au sol, les demandes d'inventaire, la mémorisation des
potions utilisées et des fontaines réduites à un filet d'eau. Pour manger ou
sacrifier, utiliser `Slot('a')` pour un emplacement d'inventaire et une chaîne
ordinaire pour un libellé au sol. Même la chaîne `'a'` reste un libellé : Clojure
distingue explicitement `Character` et `String`, et le portage doit conserver
cette distinction. Les outils d'oracle encodent ces arguments avec leur type.

Les sacrifices reproduisent l'écriture de `:last-prayer` dans `:player` après
réconciliation ou les messages de trèfle/herbe ; ce champ n'est pas déplacé
vers le champ homonyme du jeu, malgré la différence avec `Pray`.
Les réponses différées qui valent vrai sont conservées : `eat-it` retourne
le contexte fourni par la demande de mise à jour, plutôt qu'un simple booléen.

## Travail restant pour atteindre l’objectif

1. Porter les protocoles d’actions et connecter la machine de synchronisation du scraper, puis vérifier les interactions sur de vrais flux de jeu.
2. Compléter et intégrer le modèle du joueur, des monstres, des objets, des niveaux et du donjon ; connecter l’identification dynamique aux événements.
3. Porter les règles `mainbot` dans leur ordre original : urgences, combat/retraite, équipement, récupération, exploration, magasins, Excalibur, Sokoban, quête, château, farming et fin de partie.
4. Comparer les décisions Python/Clojure sur des états identiques, puis corriger chaque divergence matérielle.
5. Faire jouer le Python à la vraie version historique sans assistance. Conserver actions, options, versions, ttyrec, journaux et xlogfile pour toute ascension revendiquée.
6. Évaluer les deux bots sur plusieurs parties selon le même protocole : victoires, tours, scores, profondeur, motifs de mort et blocages. Une victoire isolée ne prouve ni une fidélité absolue ni un taux de réussite comparable.

Une relecture de ttyrec, une ascension de l’original, un lancement Java depuis Python ou une victoire en mode wizard ne sera pas compté comme une ascension de ce portage Python.
