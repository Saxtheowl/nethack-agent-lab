# BotHack 3.6.7 — 100 expériences pour améliorer le taux d’ascension

**Audit du dépôt local : 23 septembre 2026.** Document de conception ; les variantes décrites ici ne sont pas implémentées et leurs gains ne sont pas mesurés. Objectif : augmenter les ascensions complètes dans le régime assisté actuel, puis conserver des politiques efficaces lorsque l’on retire l’invincibilité, l’anti-famine et les objets du kit.

Ce document complète [IMPROVEMENTS.md](IMPROVEMENTS.md), qui contient déjà **232 pistes**, et [MEGADOC.md](MEGADOC.md). Il précise des idées existantes et en ajoute ; les renvois « I… » désignent les numéros d’IMPROVEMENTS. Une reprise est explicitement indiquée. Il ne faut pas interpréter ces 100 fiches comme 100 fonctionnalités actuellement absentes : plusieurs sont des variantes d’un mécanisme déjà présent.

## Navigation

- [Ce que l’audit établit](#ce-que-laudit-établit)
- [Profils et règles de comparaison](#profils-et-règles-de-comparaison)
- [P001–P010 : rendre les expériences interprétables](#p001p010--rendre-les-expériences-interprétables)
- [P011–P020 : perception, interface et mémoire](#p011p020--perception-interface-et-mémoire)
- [P021–P030 : priorités et sorties de boucle](#p021p030--priorités-et-sorties-de-boucle)
- [P031–P040 : route et objets d’invocation](#p031p040--route-et-objets-dinvocation)
- [P041–P050 : remontée, Plans et Astral](#p041p050--remontée-plans-et-astral)
- [P051–P060 : combats et déplacements de survie](#p051p060--combats-et-déplacements-de-survie)
- [P061–P070 : statuts, résistances et urgences](#p061p070--statuts-résistances-et-urgences)
- [P071–P080 : équipement, souhaits et ressources](#p071p080--équipement-souhaits-et-ressources)
- [P081–P090 : faim et acquisition sans kit](#p081p090--faim-et-acquisition-sans-kit)
- [P091–P100 : approches exploratoires](#p091p100--approches-exploratoires)
- [Ordre de réalisation et protocole A/B](#ordre-de-réalisation-et-protocole-ab)
- [Commandes disponibles et contrat des futures variantes](#commandes-disponibles-et-contrat-des-futures-variantes)
- [Sources et limites de lecture](#sources-et-limites-de-lecture)

## Ce que l’audit établit

### Architecture et conséquences pour les expériences

Le moteur C NetHack 3.6.7 expose un protocole JSON via `win/bot/winbot.c`. [engine] le reçoit ; [bridge] convertit les observations et prompts vers le modèle BotHack, et les actions en réponses structurées. Le bot conserve une représentation d’écran et beaucoup de logique héritée de 3.4.3 : éliminer le terminal réel ne supprime donc pas les erreurs de parsing et de mémoire.

[bh36] enregistre les handlers de perception ; [mainbot] enregistre les décisions par priorité. Par exemple : offrande −99, ruées assistées des Plans/Astral −20, noyade −13, faim −11, maladie −9, retraite/rhabillage −7, combat −6, objets 2 à 13, progression 19. Ces priorités expliquent comment un objectif peut être affamé par d’autres décisions. [pathing] transforme les objectifs en déplacements, avec des coûts souvent fixes.

[rules36] désactive le farming et adapte Elbereth/prière. `--profile fast` change la progression ; `--tactics assisted` supprime l’enregistrement de retraite et repos. Ce sont deux axes distincts. Avec `--no-invincible`, [rungame] choisit déjà `normal` par défaut : « réactiver la retraite » n’est donc pas une fonctionnalité manquante pour cette ablation statique.

[supervisor] observe boucles, temps, requêtes et nouveauté, et peut modifier l’état du bot ou arrêter la partie. Il fait partie de la politique effectivement évaluée. [recorder] conserve les jalons ; certains viennent de `priv` et des achievements moteur. Cette information sert au diagnostic et au verdict, **pas aux décisions du bot**. Les futures politiques proposées ci-dessous utilisent seulement des observations accessibles au joueur, sa mémoire et des connaissances statiques des règles.

### Résultats réellement consultables ici

Le répertoire local contient 476 fichiers `result.json`, toutes catégories confondues. **Ce n’est pas un dénominateur de winrate** : il mélange versions, scénarios, objectifs partiels, rejeux et budgets.

| Ensemble local lu | Résultats présents | Issues constatées | Ce que cela permet de conclure |
| --- | ---: | --- | --- |
| `runs/worker/big-w01` | 49 | 44 stuck, 2 limit, 3 crash_bot | Ancien code ; 25 raisons commencent par `fixation` |
| `runs/worker/big-w02` | 62 | 37 stuck, 25 limit | Ancien code ; 15 fixations, 6 request storms ; 8 limites sont des SIGTERM |
| `runs/worker/big-w08` | 32 | 6 stuck, 26 limit | Les 26 limites portent `max_seconds 14400` |
| `runs/worker/full-c01` | 1 résultat présent | 1 ascension : g011 | Copie locale sélectionnée, certainement pas un taux de réussite de 100 % |
| `full-c02`, `full-c04`, `planes-c01` sous `runs/worker` | 0 résultat trouvé | — | Leurs agrégats documentés ne sont pas recalculables depuis ces répertoires locaux |

Les ≈85 parties et 52 630 morts annulées d’IMPROVEMENTS restent des **mesures rapportées par la documentation**, non revérifiées ici. Les documents historiques contiennent aussi des paragraphes antérieurs à la première ascension ; leur date et leur version doivent être conservées.

La partie [full-c01/g011](../runs/worker/full-c01/g011/result.json), seed 8011, est en revanche vérifiable :

- moteur et xlogfile concordent sur `ascended`, sans wizard ni scénario ;
- 51 834 tours, 13 235,3 secondes, 121 697 requêtes, 86 043 actions ;
- 506 `lifesave`, 3 `feed` ; première mort annulée au tour 12 671, profondeur 27, tueur `shark` ;
- **494 des 506 morts annulées sont sur les Plans**, 12 à profondeur positive ≥26 ; Pestilence 228, Death 103, Famine 26 ;
- 24 353 `farlook` et 4 831 `look` : 33,9 % des actions, sans que cela signifie 33,9 % du CPU ou des tours ;
- 2 780 `ascend` et 2 750 `descend` : 5 530 actions à expliquer par leurs contextes, pas 5 530 transitions réussies ;
- entrée de quête T16 083 → Cloche T35 476 : 19 393 tours écoulés, **incluant d’autres détours**, pas une mesure du seul combat de quête.

Ce succès montre que des pertes très différentes peuvent dominer selon la partie. Il ne justifie ni « Gehennom est le seul problème », ni « le début est presque viable ». Un faible pourcentage de morts répétées au début peut cacher une première mort précoce dans beaucoup de runs. Après une intervention, trajectoire, PV, niveaux et ressources divergent d’une partie sans aide.

### Corrections de prémisses avant de coder

| Idée ou raccourci à revoir | Vérification dans le dépôt | Conséquence |
| --- | --- | --- |
| Ranger l’Amulette ou les trois objets d’invocation | [pickup-c], `in_container`, les refuse explicitement ; `amulet_safekeeping` existe mais n’est pas enregistré | Ne pas réactiver cette fonction ; développer récupération et anti-vol |
| La corne ne restaure plus les attributs en 3.6 | [apply-c], `use_unicorn_horn`, construit et corrige encore des troubles d’attribut, avec exceptions | Le commentaire d’`assisted_astral_rush` est trop général ; tester P065 |
| Faire tout droit à l’est sur la Terre | [endgame-des] distingue rectangle autorisé et zone exclue ; l’Air a une autre règle | Valider chaque modèle de carte ; aucune direction universelle |
| Absence de chaleur = loin du portail | [wizard-c], `amulet`, ne produit un indice que sur un tirage `!rn2(15)` | Le silence n’est pas une preuve d’absence ; P044 |
| Lévitation = sécurité universelle eau/lave | Plans, déplacements, équipement et formes ont des règles différentes | Modèle de capacités par terrain ; P047 et P066 |
| Plus de morts annulées = pire politique sans aide | L’aide restaure aussi attributs, niveaux, PV max, évite slime/cerveau | Mesurer première intervention et vraies ablations, P004/P100 |
| Une suite de touches rend l’invocation atomique | [spell-c] vérifie notamment une Cloche sonnée depuis moins de 5 tours | Automate interruptible avec vérification des préconditions, P040 |
| Traque, travel, portails, caches sont à créer | Ils existent déjà dans le code lu | Comparer des changements ciblés ; ne pas revendiquer deux fois un correctif |

## Profils et règles de comparaison

Les lettres suivantes désignent des **cohortes expérimentales proposées**, pas de nouveaux flags existants.

| Profil | Invincibilité | Anti-famine | Kit | Tactiques de départ |
| --- | --- | --- | --- | --- |
| A | oui | oui | complet actuel | assisted |
| B | non | oui | complet actuel | normal |
| C | oui | non | complet actuel | assisted |
| D | non | non | complet actuel | normal |
| E | oui puis non dans deux cohortes séparées | fixe dans chaque comparaison | un objet ou une propriété retiré à la fois | cohérentes avec l’invincibilité |
| F | non | non | aucun | normal |

Une variante A ne s’active jamais implicitement en B/F. Déclarer séparément **politique**, **aides**, **kit**, **moteur**, **superviseur**, **budget** et **seeds**. Ajouter des buffs pour gagner ne valide pas une amélioration du bot à aides constantes.

Chaque fiche donne : profils, priorité de recherche, effort, changement concret, test et risque. **Priorité 1** = bon premier candidat ; **2** = seconde vague ; **3** = exploratoire. Effort **S** = modification locale ; **M** = plusieurs mécanismes ; **L** = chantier transversal. Ce sont des estimations de réalisation, pas de gains.

Métriques communes : ascensions vérifiées / parties démarrées éligibles sous budget fixé ; taux d’atteinte de chaque jalon ; issues et causes ; temps/tours/requêtes ; consommation de ressources. Les temps jusqu’aux jalons sont accompagnés du nombre de runs qui les atteignent. En B/D/F : ajouter première mort réelle. En A/C/E assisté : ajouter première intervention, interventions par 1 000 tours et par épisode. Un scénario wizard est toujours rapporté séparément.

## P001–P010 — Rendre les expériences interprétables

### P001 — Registre de variantes et paramètres effectivement résolus

**Tous · priorité 1 · M · précise I12/221.**

- **Modification :** ajouter à [rungame] un registre validé avant démarrage : nom, paramètres, incompatibilités et profils autorisés. Écrire les valeurs résolues dans le manifest et le résultat, notamment les défauts qui changent selon les aides.
- **Expérience :** commencer par des variantes à un seul changement ; vérifier que `off` conserve le comportement de référence et qu’une variante inconnue échoue avant tout lancement.
- **Mesure / risque :** couverture des manifests et comparaison sans configuration ambiguë. C’est un prérequis de mesure, sans gain direct de winrate attendu ; éviter qu’une variable d’environnement oubliée active une seconde variante.

### P002 — Empreinte complète, incluant les données JSON

**Tous · priorité 1 · S · précise I9.**

- **Constat / modification :** `tree_hash` de [rungame] filtre actuellement `.py`, `.c`, `.h` ; `_data.json`, `_hashdata.json`, `_leveldata.json` ne contribuent pas au hash bot. Inclure données chargées, configuration, scénario, version Python complète et contenu des variantes ; distinguer code sale et commit.
- **Expérience :** modifier une copie de chaque type d’entrée et vérifier que son empreinte change ; enregistrer l’empreinte du binaire réellement lancé.
- **Mesure / risque :** zéro collision de configuration connue dans les comparaisons. Ne pas incorporer journaux ou horodatages au hash de code, ce qui rendrait chaque run artificiellement unique.

### P003 — Reproductibilité jusqu’à la première divergence

**Tous · priorité 1 · M · précise I2/6/224.**

- **Modification :** fixer `PYTHONHASHSEED` **avant le démarrage de Python**, moteur et bot seed ; comparer des signatures normalisées des requêtes/actions à chaque décision. Archiver aussi les options et facteurs calendaires éventuels du moteur.
- **Expérience :** trois relectures de la même seed/configuration, puis changement d’un seul paramètre. Localiser la première divergence de politique ; ignorer seulement les champs de temps machine.
- **Mesure / risque :** longueur du préfixe identique et cause de divergence. Deux politiques sur une même seed consomment le RNG différemment : après divergence, elles ne voient pas nécessairement les mêmes niveaux ou combats. L’appariement reste utile, sans être un replay contrefactuel exact.

### P004 — Diagnostic avant la première intervention

**A/C/E assisté, validation B/D/F · priorité 1 · S · précise I35/93/96.**

- **Modification :** résumer depuis [recorder]/[assist-c] première aide de survie (`lifesave`, `noslime`, `brainsave`, `nochoke`), état observable précédent, phase, équipement et action. Séparer aides alimentaires et kit ; exploiter les compteurs moteur car `brainsave` est journalisé une fois sur vingt.
- **Expérience :** croiser ces rapports avec des runs sans invincibilité sous tactiques normales, puis avec une politique identique dans les deux régimes pour étudier l’effet mécanique de l’aide.
- **Mesure / risque :** fraction atteignant Château sans intervention et distribution du premier danger. « Zéro lifesave » ne prouve pas « aucune aide de survie », et une mort après 500 sauvetages ne décrit pas la survie naturelle.

### P005 — Séparer temps de calcul et efficacité dans le jeu

**Tous · priorité 1 · S · précise I25/210.**

- **Modification :** chronométrer familles de handlers, perception, pathfinding, sérialisation et attente moteur ; compter actions à zéro tour, déplacements, combats et transitions réellement confirmées. Produire p50/p95 par phase, pas seulement `turns_per_s`.
- **Expérience :** profiler un échantillon stratifié de débuts, labyrinthes et Plans, puis mesurer sans instrumentation lourde pour confirmer les gains.
- **Mesure / risque :** CPU/décision et tours/jalon séparés. Une optimisation CPU peut augmenter le taux sous limite murale sans améliorer la stratégie ; c’est utile, mais il faut l’annoncer comme tel. Le nombre d’actions `attack` sous-estime le combat exécuté par `move`.

### P006 — Funnel conditionnel et possession actuelle

**Tous · priorité 1 · M · précise I3/23.**

- **Modification :** compléter les jalons monotones de [recorder] par « possédé maintenant », « volé », « récupéré », et les préconditions restantes. Mesurer Cloche obtenue parmi les runs ayant réellement accédé au niveau du némésis, puis conservée à l’invocation.
- **Expérience :** reconstruire les trajectoires de g011 et de runs avec vol ; distinguer absence d’acquisition et perte ultérieure.
- **Mesure / risque :** probabilités de transitions et délai sans l’objet. Un achievement signale une acquisition passée ; le réutiliser comme preuve de possession actuelle ferait masquer précisément les échecs que l’on veut corriger.

### P007 — Scénarios dérivés des états réellement atteints

**Tous · priorité 1 · M · précise I8/90/227.**

- **Modification :** décliner [scenarios] en familles : XL, CA, résistances, objets, malédictions et densité proches des arrivées observées. Le scénario `planes` actuel prépare XL30 et plusieurs pièces +5 ; g011 termine XL19.
- **Expérience :** même modification sur scénario favorable, état médian observé et état dégradé ; confirmer ensuite depuis Dlvl1. Les futurs checkpoints réels doivent aussi restaurer mémoire bot, RNG et superviseur, pas seulement la sauvegarde C.
- **Mesure / risque :** taux de sortie et coût par état. Une réussite wizard suréquipée ne prouve pas le transfert ; la quête préparée peut aussi contourner des préconditions via `adjust?`.

### P008 — Rapport d’échec causal plutôt qu’une raison tronquée

**Tous · priorité 1 · M · précise I4/131.**

- **Modification :** remplacer la seule signature textuelle de [series] par phase, famille d’objectif, dernière action ayant changé l’état, refus rencontré, état du menu et tentative de récupération. Conserver les textes bruts en pièces jointes.
- **Expérience :** annoter manuellement 20 fixations historiques, comparer regroupement actuel et nouveau regroupement ; séparer au moins objet inconnu, inaccessible, menu non apparié et priorité concurrente.
- **Mesure / risque :** proportion de classes menant à un correctif commun, faux regroupements. Ne pas normaliser les noms d’objets/monstres lorsque leur identité explique le bug ; ne pas attribuer causalement l’échec au seul dernier message.

### P009 — Limites de ressources comparables et arrêts explicites

**Tous · priorité 1 · S · précise I11/176–178.**

- **Modification :** déclarer un budget primaire fixe ; séparer timeout mural, tours, requêtes, arrêt opérateur et arrêt anticipé de série. Réserver une expérience distincte aux budgets adaptatifs après acquisition de l’Amulette.
- **Expérience :** même politique avec 2/4/6 heures et budgets de tours fixes ; alterner l’ordre A/B sur le worker. Mesurer charge/temps CPU pour identifier une saturation machine.
- **Mesure / risque :** ascensions sous budget et ascensions par heure machine. Augmenter le budget change l’objectif évalué ; exclure les SIGTERM ou les runs lents du dénominateur gonflerait artificiellement le résultat.

### P010 — Contrôle des informations accessibles à la politique

**Tous · priorité 1 · M · extension de I129.**

- **Modification :** formaliser une vue observable pour les futures politiques et les traces d’apprentissage : messages, carte perçue, statut public, inventaire connu. Garder `priv`, carte cachée, inventaire des monstres et vérité BUC hors de cette vue.
- **Expérience :** perturber uniquement les champs privés sur des observations enregistrées et vérifier l’invariance des décisions hors logique de fin/objectif du harnais.
- **Mesure / risque :** zéro dépendance interdite. Une amélioration apparente obtenue en lisant les coordonnées réelles d’un portail n’évalue plus le même bot ; les templates statiques, eux, sont des connaissances déclarées avec incertitude.

## P011–P020 — Perception, interface et mémoire

### P011 — Farlook déclenché par changement pertinent

**Tous · priorité 1 · M · précise I15/26/197.**

- **Modification :** dans [actions] `examine_monsters` et [tracker], mettre en cache le résultat par observation locale, niveau, apparence, position et génération de suivi. Réexaminer si paix inconnue, transformation, hallucination terminée ou danger proche.
- **Expérience :** comparer cache conservateur à durées 5/20 tours, puis politique « examiner avant interaction ». La base actuelle évite déjà d’examiner un monstre dont type et paix sont connus ; chercher pourquoi cette connaissance se perd.
- **Mesure / risque :** farlooks/décision, CPU, coups portés à des pacifiques et morts. Ne pas fusionner deux monstres visuellement identiques ni supprimer l’information critique au nom de la distance seule.

### P012 — Empreinte de pile d’objets pour stabiliser Look

**Tous · priorité 1 · M · précise I16/198.**

- **Modification :** [actions] `Look`/`examine_tile` et [mainbot] `consider_items_here` mémorisent le dernier résultat, même partiellement inconnu. Un `:` identique clôt l’examen jusqu’à changement de glyphe, dépôt, mort, ramassage ou nouveau message.
- **Expérience :** piles contenant roman, objets en fosse, objets sous autel et libellé inconnu ; comparer relecture systématique et invalidation par événements.
- **Mesure / risque :** visites et `look` par pile, fixations, objets clés manqués. Une pile peut changer sans changer de glyphe : les événements doivent invalider le cache, et les objets d’objectif gardent une possibilité de recontrôle.

### P013 — Transaction d’action avec résultat attendu

**Tous · priorité 1 · M · précise I17/19/20.**

- **Modification :** prolonger `action_serial` de [bridge] par un contexte : action initiale, objet visé, prompts autorisés, résultat attendu. Un ramassage ne réussit qu’après delta d’inventaire ou message explicite ; un menu sans correspondance devient une erreur locale récupérable.
- **Expérience :** menus de plus de 52 entrées, renommage, changement de lettre et interruption entre action et prompt. Ne pas modifier simultanément tous les types d’action : commencer par pickup/loot.
- **Mesure / risque :** échecs silencieux et reprises par transaction. Une attente de preuve trop stricte peut elle-même bloquer ; prévoir expiration et resynchronisation de l’inventaire.

### P014 — Repli de menu par identité non ambiguë

**Tous · priorité 1 · S · précise I17.**

- **Modification :** si le libellé brut attendu n’existe pas, tenter une clé normalisée nom/type/quantité/BUC connu, avec correspondance unique uniquement. Utiliser l’identifiant structuré de l’entrée pour répondre ; rafraîchir si plusieurs candidats subsistent.
- **Expérience :** mêmes noms avec prix différents, objets nommés, piles fusionnées, objets maudits et non maudits. Tester [compat36], [actions] `PickUp`, [bridge] `_consume` ensemble.
- **Mesure / risque :** `menu_letter_unmatched`, sélections correctes et achats involontaires. Retirer trop de différences du libellé ferait choisir la mauvaise pièce ; une ambiguïté vaut une nouvelle observation.

### P015 — Veto conditionné par sa cause

**Tous · priorité 1 · M · précise I14/20.**

- **Modification :** remplacer dans [bridge] le seul délai uniforme de 300 tours par une cause : maudit, main occupée, mauvaise lettre, accès au sol, objet non rangeable. Lever le veto quand inventaire, équipement, position ou BUC pertinent change.
- **Expérience :** anneau maudit puis désensorcelé, arme soudée puis libérée, lettre réattribuée. Comparer TTL actuel et invalidation causale avec TTL de secours.
- **Mesure / risque :** refus répétés et temps entre réparation et action réussie. La clé actuelle dépend parfois du slot ; sans identité d’objet/génération d’inventaire, un veto peut contaminer un autre objet.

### P016 — Identité d’objet persistante dans le journal

**Tous · priorité 1 · M · précise I23/66.**

- **Modification :** [recorder] `_watch_items` doit distinguer disparition, rangement, déballage, renommage, identification et consommation. Associer les deltas aux actions connues et aux contenus de sacs connus, sans inventer d’identifiant moteur caché.
- **Expérience :** ranger une potion, identifier une `silver bell`, fusionner des bougies, se faire voler un anneau. Le rapport doit classer chaque événement avec confiance et garder « indéterminé » si nécessaire.
- **Mesure / risque :** précision des événements de perte. Le suivi actuel est une recherche de sous-chaînes dans l’inventaire direct : il peut signaler une perte lors d’un changement de nom ou d’un rangement.

### P017 — Mémoire des uniques avec incertitude spatiale

**Tous · priorité 1 · M · précise I21/59/60.**

- **Modification :** compléter [tracker] par des observations persistantes de Vlad, Surtur et Sorcier : niveau, dernière case, dernier tour, décès confirmé ou disparition. Après départ du niveau, conserver une région probable plutôt qu’une case présumée occupée.
- **Expérience :** unique vu puis hors champ, changement de niveau, téléportation, retour sur niveau vidé. Comparer au réexamen complet actuel.
- **Mesure / risque :** délai pour retrouver le porteur et attaques de cases vides. Une mémoire ancienne doit guider la recherche, jamais certifier la présence ni l’identité d’un nouveau glyphe.

### P018 — Réconciliation explicite terrain, objets et monstres

**Tous · priorité 2 · M · précise I22.**

- **Modification :** séparer dans [bridge]/[game]/[tile] terrain mémorisé, objet de surface et occupant ; conserver provenance et date de chaque observation. Un monstre ou une pile recouvrant un autel ne doit pas effacer le terrain confirmé.
- **Expérience :** chaîne sur autel, monstre invisible derrière rocher, pile sur escalier, terrain mobile de l’Eau. Définir quels messages peuvent invalider quelle couche.
- **Mesure / risque :** contradictions et tentatives d’actions impossibles. Faire confiance sans condition au dernier caractère détruirait une mémoire valide ; faire confiance sans condition à la mémoire rendrait l’Eau injouable.

### P019 — Rejeu de prompts en mutation contrôlée

**Tous · priorité 2 · M · précise I13/19.**

- **Modification :** bâtir un corpus de requêtes réelles de [bridge]/[compat36], puis varier espaces, articles, suffixes, quantité, prix et ordre des menus tout en conservant leur sens. Définir la réponse sémantique attendue, pas la lettre.
- **Expérience :** priorité aux bougies, retrait d’objet, pickup et choix de direction. Utiliser [audit] comme liste de suspects, non comme oracle : « la regex matche une chaîne » ne prouve pas le bon traitement.
- **Mesure / risque :** prompts compris, faux matchs et sélections correctes. Les mutations doivent rester compatibles avec des messages réellement possibles en 3.6.7.

### P020 — Réparer les faits d’identification contradictoires

**Tous, surtout E/F · priorité 2 · M · précise I18.**

- **Modification :** dans [itemid], associer chaque fait à sa source : prix, boutique, quantité, Charisme observable, essai ou découverte. Si l’ensemble élimine tous les candidats, retirer le fait le moins fiable et journaliser le sous-ensemble contradictoire.
- **Expérience :** rejouer les cas de prix de piles et commerçant fâché, puis comparer au repli actuel qui abandonne les faits incompatibles.
- **Mesure / risque :** identifications correctes, coût d’identification et dangers d’essais. Une contradiction doit diminuer la confiance, pas convertir automatiquement une hypothèse en identité certaine.

## P021–P030 — Priorités et sorties de boucle

### P021 — Remontée prioritaire dès possession de l’Amulette

**A d’abord, B/D après contrôle du danger · priorité 1 · S · précise I69/78/171.**

- **Modification :** créer dans [mainbot] un handler de remontée au-dessus du loot/identification/chasse opportuniste ; laisser urgences, obstacle immédiat et récupération d’Amulette préempter. Aujourd’hui `progress` est à 19 et beaucoup d’activités passent avant.
- **Expérience :** variante seule, du Sanctuaire à Dlvl1 ; conserver un panier de ressources d’urgence admissibles plutôt que ramasser tout objet désirable.
- **Mesure / risque :** taux Amulette→Plans, tours sans Amulette, détours et consommables à l’entrée des Plans. Un rush sans réserve peut déplacer l’échec vers l’Astral.

### P022 — Combat assisté limité à ce qui bloque l’objectif

**A/C, hors danger d’objet · priorité 1 · M · précise I133/134/189.**

- **Modification :** fournir à `fight` un chemin d’objectif ; ignorer les hostiles hors du chemin et ceux qui n’empêchent ni mouvement ni action requise. Conserver englouteurs, voleurs d’objet clé et menaces de destruction d’équipement.
- **Expérience :** comparer rayon de combat 1/2 à la politique actuelle, séparément en Gehennom et sur les Plans. Ne pas simplement supprimer `fight`, utilisé aussi pour débloquer le déplacement.
- **Mesure / risque :** tours de combat par jalon, progression et pertes matérielles. L’invincibilité n’empêche pas l’engorgement, les vols ou tous les dégâts sur l’inventaire.

### P023 — Ramassage immédiat des objets d’objectif visibles

**Tous · priorité 1 · S · précise I154.**

- **Modification :** avant loot générique et reprise de route, vérifier les objets clés sur la case et à proximité du dernier décès du porteur. Distinguer « tuer », « voir l’objet », « ramasser », « confirmer possession » dans [mainbot].
- **Expérience :** piles nombreuses après Vlad/Surtur/prêtre, lévitation active, surcharge ; commencer par l’objet sur la case actuelle, puis étendre à un voisin accessible.
- **Mesure / risque :** morts de porteurs suivies d’acquisition sous 20/100 tours et taux d’objet laissé au sol. En survie réelle, ne pas marcher dans un danger fatal pour un gain qui peut attendre un tour.

### P024 — Engagement temporaire sur un objectif

**Tous · priorité 1 · M · nouvelle formulation de I122/226.**

- **Modification :** un objectif conserve la priorité pendant 20/50/100 décisions utiles, avec raison d’interruption explicite : danger, nouvelle précondition, impossibilité ou accomplissement. Tester d’abord `get_protection`↔exploration et entrée/sortie de quête.
- **Expérience :** comparer nombre de changements de cible et transitions d’escalier sans jalon gagné ; compter les cas où l’engagement expire sans progrès.
- **Mesure / risque :** cycles d’objectifs et délai jusqu’à la cible. Le verrou porte sur l’intention, pas sur une liste aveugle de touches ; les urgences doivent toujours préempter.

### P025 — Nouveauté définie par la phase

**Tous · priorité 1 · M · précise I64/174/195.**

- **Constat / modification :** `_novelty` de [supervisor] valorise cases inédites, profondeur maximale et XL maximal. Pendant la remontée, revisiter des escaliers connus est normal. Ajouter distance restante sur graphe connu, transitions utiles, préconditions satisfaites et possession confirmée.
- **Expérience :** rejouer des remontées et acquisitions sur niveaux déjà explorés ; comparer aux seuils actuels à budget global identique.
- **Mesure / risque :** arrêts prématurés et boucles prolongées. Un aller-retour d’escalier ou la perte/récupération du même objet ne doit pas réinitialiser indéfiniment le budget ; suivre des records de progression, pas tout changement.

### P026 — Détection des cycles de plusieurs actions

**Tous · priorité 1 · M · précise I20/130.**

- **Modification :** compléter `_action_loop` par signatures d’état observable et séquences de longueur 2 à 8 : enlever/remettre, monter/descendre, ramasser/jeter. Exiger absence de progrès sémantique avant de récupérer.
- **Expérience :** annoter cycles connus et séquences légitimes de combat/rhabillage ; comparer avec détecteur de répétition exacte au même tour.
- **Mesure / risque :** tours perdus avant détection, faux positifs et parties sauvées. Un combat alternant arme/attaque peut être valide ; le motif seul n’est pas une preuve de boucle.

### P027 — Récupérations graduées qui préservent les preuves

**Tous · priorité 1 · M · précise I16/24.**

- **Modification :** [bridge] `forget_target` efface les objets et bloque la case. Essayer plutôt rafraîchir → résoudre précondition → autre chemin → différer avec motif → abandon local. Ne pas effacer une observation d’objet clé ; marquer son accès incertain.
- **Expérience :** mêmes fixations avec récupération actuelle et graduée, en conservant les limites du superviseur.
- **Mesure / risque :** réussite après récupération, durée et objets oubliés. Une récupération plus patiente peut prolonger des impasses ; nombre d’essais et coût total restent bornés et journalisés.

### P028 — Budget d’information avant une action temporelle

**Tous · priorité 2 · M · précise I15/20/205.**

- **Modification :** compter dans [bh36]/[actions] farlook, inventaire et découvertes depuis le dernier tour utile. Au-delà de 8/16 examens non critiques, différer l’information distante et laisser choisir une action de progression ; toujours examiner l’obstacle immédiat.
- **Expérience :** foules télépathiques, inventaire instable et nouvelle entrée de niveau. Distinguer vraie tempête sans nouvel état et grand nombre d’examens tous différents.
- **Mesure / risque :** latence avant déplacement et erreurs de combat/interaction. Forcer `search` pour faire avancer l’horloge ne remplace pas une décision utile et peut être mortel en B/F.

### P029 — Plan de rhabillage par pièce et par interruption

**Tous · priorité 2 · M · précise I36/144.**

- **Modification :** remplacer l’inhibition globale de 100 tours après `LAST_BOT_REMOVAL` par un motif attaché à la pièce : enchantement, changement de rôle, vol, séduction, lévitation volontaire. Rééquiper dès la fin du sous-plan, sous réserve du coût en tours.
- **Expérience :** incube, retrait pour enchantement, échange d’amulette sur les Plans ; vérifier absence d’alternance enlever/remettre.
- **Mesure / risque :** tours sans protection utile et temps perdu à s’habiller en danger. Une pièce protectrice n’est pas automatiquement prioritaire si sa remise nécessite plusieurs tours exposés.

### P030 — Traque d’objet avec valeur, expiration et preuve nouvelle

**Tous · priorité 1 · M · précise I165/173.**

- **Modification :** [mainbot] `hunt` conserve actuellement des entrées pendant 3 000 tours ; la récupération d’invocation a un autre budget. Unifier les intentions : objet obligatoire, équipement critique ou confort ; seul le premier reste un objectif stratégique persistant.
- **Expérience :** vol de potion, anneau de lévitation avant Méduse, vraie Amulette ; réactiver une recherche expirée seulement après indice nouveau ou changement de capacité.
- **Mesure / risque :** tours de poursuite par valeur récupérée et abandons d’objets nécessaires. Une expiration locale ne doit jamais signifier que l’Amulette a cessé d’être obligatoire.

## P031–P040 — Route et objets d’invocation

### P031 — Graphe des préconditions d’ascension

**Tous · priorité 1 · L · précise I122/148/149.**

- **Modification :** compléter `full_explore` de [mainbot] par des objectifs explicites : accès quête, Cloche, Chandelier, sept bougies, Livre, carré vibrant, invocation. Choisir le prochain objectif réalisable selon trajet estimé, ressources manquantes et risque.
- **Expérience :** commencer par trois ordres fixes autorisés, puis comparer le choix dynamique. Journaliser les préconditions observées et la raison de chaque changement d’ordre.
- **Mesure / risque :** tours jusqu’au trio d’invocation, allers-retours entre branches et ascensions. Trouver un niveau ne signifie pas l’avoir accompli ; prévoir des tâches de récupération après vol, et ne pas utiliser `priv` pour connaître une entrée encore invisible.

### P032 — Quête conditionnée par les capacités nécessaires

**A/E d’abord, B/F séparément · priorité 1 · M · précise I150.**

- **Constat / modification :** `full_explore` exige XL≥14, DSM et lévitation. Comparer ce filtre à une liste de capacités : admissibilité observée auprès du chef, franchissement du terrain, puissance/échappatoire et protection adaptée au profil.
- **Expérience :** A sans DSM du kit, puis B avec équipement équivalent obtenu autrement ; conserver un budget de préparation si le chef refuse. XL14 seul ne garantit pas toute l’admissibilité à la quête.
- **Mesure / risque :** délai quête→Cloche, rejets du chef et pertes sur le trajet. Enlever le verrou matériel sans remplacer son rôle pourrait envoyer un héros réellement fragile dans une impasse.

### P033 — Budget de récupération compté sur le lieu utile

**Tous · priorité 1 · S · précise I59/165.**

- **Constat / modification :** `fetch_invocation_item` déclenche son compteur avant de rejoindre le niveau cible ; les 3 000 tours peuvent inclure le trajet. Séparer budget de voyage, recherche sur place et combat ; réinitialiser le budget local uniquement sur un indice pertinent.
- **Expérience :** départ loin de Vlad ou de la fin de quête ; comparer 500/1 500/3 000 tours sur place au budget global actuel et cooldown fixe de 5 000 tours.
- **Mesure / risque :** abandons avant arrivée et acquisition par visite. Un budget local renouvelable sans limite globale recréerait une poursuite éternelle.

### P034 — Cibler le porteur plutôt que tous les hostiles

**Tous · priorité 1 · M · précise I153.**

- **Modification :** dans `fetch_invocation_item`, hiérarchiser porteur reconnu, dernier lieu du porteur, objet vu au sol, portes non ouvertes, puis recherche générale. La liste actuelle de cibles contient tous les hostiles non amicaux.
- **Expérience :** niveau de Vlad avec cour intacte, Surtur mêlé à d’autres ennemis ; comparer nombre de combats sans lien avec l’acquisition.
- **Mesure / risque :** temps jusqu’à l’objet et nombre de monstres auxiliaires combattus. Ne pas supposer que l’objet est toujours chez son porteur initial après un vol ou un décès ; basculer sur les preuves de transfert.

### P035 — Déverrouiller la salle de l’objectif avant d’explorer les annexes

**Tous · priorité 1 · M · précise I60/151/152.**

- **Modification :** utiliser [leveldata], [tower-des] et les cartes de quête comme hypothèses de structure ; reconnaître des repères visibles et leurs transformations avant de donner une forte valeur aux portes menant à la salle cible.
- **Expérience :** Vlad avec clé, pioche seule et aucun outil ; inclure une carte partiellement vue et un repère contradictoire. Comparer au parcours des cases non foulées de `fetch_invocation_item`.
- **Mesure / risque :** portes utiles ouvertes, distance et errances. Ne pas transformer un template en carte réelle révélée ; si les observations le contredisent, revenir à l’exploration normale.

### P036 — Trajet en Gehennom avec détours obligatoires explicites

**A d’abord, B/D ensuite · priorité 2 · M · précise I57/146/213.**

- **Modification :** `go_down` et `seek_level` comparent escalier connu, exploration, excavation horizontale et trou autorisé ; pénaliser un saut qui ferait manquer une entrée encore nécessaire. Garder un chemin de retour estimé.
- **Expérience :** « escaliers seulement », « excavation opportuniste », « descente rapide jusqu’au prochain objectif ». Vérifier chaque refus de creusement et mémoriser la contrainte locale.
- **Mesure / risque :** temps par niveau et taux d’accès à Vlad/tour/Sanctuaire. Réduire les tours de descente en sacrifiant une entrée ou les outils de remontée peut dégrader l’ascension.

### P037 — Bougies de Vlad : chercher aussi dans les coffres

**A/E/F · priorité 1 · S · précise I61/155/156.**

- **Constat / modification :** [tower-des] place deux lots de bougies `4d2` dans des coffres. Un profil fast qui compte sur Vlad doit rendre ces conteneurs prioritaires si le total connu est inférieur à sept ; réutiliser `examine_containers` et `count_candles`.
- **Expérience :** coffres fermés/verrouillés, bougies encore non identifiées, quantité répartie entre inventaire et coffre. Comparer achat tôt, récupération à Vlad et souhait de secours.
- **Mesure / risque :** manque de bougies au carré vibrant et souhaits consommés. Une garantie de génération ne garantit ni découverte, ni ouverture, ni conservation du contenu.

### P038 — Reporter l’activation de la pression du Sorcier

**Tous · priorité 1 · M · extension de I148/166.**

- **Modification :** comparer l’ordre actuel à une préparation avant attaque du Sorcier : Cloche, Chandelier équipé, carré vibrant localisé si accessible, réserves et route de sortie prêtes. Les événements post-Sorcier rendent les détours ultérieurs plus coûteux.
- **Expérience :** planification identique sauf ordre Livre/préparation ; vérifier la mécanique dans [wizard-c] et [spell-c] avant de choisir le déclencheur suivi par le bot.
- **Mesure / risque :** tours entre premier Sorcier tué, invocation et Amulette ; réapparitions, malédictions et vols. Attendre trop longtemps le « parfait équipement » peut coûter plus que la pression évitée.

### P039 — Conserver les objets obligatoires dans tous les sélecteurs

**Tous · priorité 1 · S · précise I23/66/76.**

- **Modification :** centraliser dans [mainbot]/[item] un prédicat d’objet d’objectif, incluant apparences connues et statut de vraie Amulette. Le consulter dans dépôt, vente, sacrifice, essai d’objet et rangement ; conserver les commandes légitimes d’invocation/offrande.
- **Expérience :** `silver bell` avant identification, Livre maudit, faux/real Amulet, surcharge à 52 slots. Auditer les sélecteurs actuels avant d’ajouter une protection redondante.
- **Mesure / risque :** aucune perte volontaire inexpliquée. Une apparence ambiguë peut imposer une conservation provisoire ; ne pas certifier une fausse Amulette sur son seul nom.

### P040 — Invocation sous forme d’automate contrôlé

**Tous · priorité 1 · M · précise I73/157/161.**

- **Modification :** [behaviors] suit les états carré confirmé → sept bougies attachées → objets non maudits → Chandelier allumé → Cloche récemment sonnée → Livre lu → escalier confirmé. Priorité temporaire et revalidation après interruption.
- **Expérience :** maudire un objet, éteindre le Chandelier ou interrompre après la Cloche. [spell-c] impose `moves - age < 5` ; résonner si nécessaire au lieu de lire trop tard.
- **Mesure / risque :** invocations par tentative et tours perdus en séquences incomplètes. L’automate ne doit pas masquer une urgence létale en B/F, ni croire qu’un simple escalier quelconque prouve la réussite hors du carré confirmé.

## P041–P050 — Remontée, Plans et Astral

### P041 — Intercepter le voleur à partir d’indices

**Tous · priorité 1 · M · précise I70/71/172/175.**

- **Modification :** [mainbot] `_hunt_action`/`_amulet_escape` passent d’une supposition de niveau à une liste de candidats : position observée du voleur, escaliers connus, dernier lieu du vol, régions inspectées. Priorité absolue à la vraie Amulette manquante.
- **Expérience :** vol suivi de téléportation, voleur invisible, faux double du Sorcier ; comparer poursuite directe, interception d’escalier et recherche bornée. Confirmer chaque reprise par inventaire.
- **Mesure / risque :** taux de récupération et tours sans Amulette. Les escaliers sont une hypothèse tactique, pas une position certaine ; ne pas se condamner à attendre sur la mauvaise case.

### P042 — Graphe de remontée avec coût des obstacles

**Tous · priorité 2 · M · précise I169/170/174.**

- **Modification :** enrichir la mémoire de transitions dans [pathing] par coût de rejoindre l’escalier, obstacles actuels et échecs récents. La force mystérieuse est un événement de jeu ; replanifier depuis le niveau confirmé sans effacer les escaliers valides.
- **Expérience :** remontées avec renvois répétés, porte désormais fermée et escalier occupé ; comparer plus court chemin géométrique et coût dynamique.
- **Mesure / risque :** transitions utiles/tentatives et tours Amulette→Plans. Une pénalité trop forte pour un renvoi aléatoire ferait éviter indéfiniment le seul escalier nécessaire.

### P043 — Contrôle de départ vers les Plans, borné et adapté au kit

**Tous · priorité 1 · M · précise I87/191/192.**

- **Modification :** à l’approche de Dlvl1, inventorier vraie Amulette, états invalidants, arme, creusement, mobilité, soins et moyens de portail. Corriger localement les manques réparables et fixer un plafond de préparation ; ne pas exiger tous les objets idéaux.
- **Expérience :** arrivée avec lévitation perdue, corne maudite, pioche absente, réflexion uniquement au cou. Comparer préparation immédiate, plafonnée à 100 tours et aucune préparation.
- **Mesure / risque :** taux d’entrée→Astral et temps perdu avant départ. L’Amulette doit être possédée pour quitter vers les Plans ; son port au cou sert aux indices, pas à une obligation universelle de sortie.

### P044 — Inférence géométrique exacte des indices de chaleur

**Tous · priorité 1 · M · précise I81/180.**

- **Constat / modification :** [game] `_update_portal_range` utilise un rectangle et marque les autres cases `walked`. Remplacer par un ensemble séparé de candidats, avec distances carrées de [wizard-c] : hot ≤9, very warm >9 et ≤64, warm >64 et ≤144.
- **Expérience :** trajectoires avec plusieurs indices, changement de Plan et silence prolongé ; comparer nombre de candidats et chemin de couverture.
- **Mesure / risque :** tours jusqu’au portail et exclusions erronées. Aucun indice négatif tiré du silence aléatoire ; sur l’Eau, ne pas intersecter comme si le portail était immobile. Préserver la vraie mémoire des cases parcourues.

### P045 — Détection de portail disponible avant la recherche longue

**Tous · priorité 1 · M · précise I164/179/193.**

- **Modification :** `detect_portal` actuel est limité à l’Eau et moins prioritaire que la ruée assistée. Comparer une détection sur chaque Plan après 100/300 tours sans portail, avec réserve de parchemins. [read-c] dirige la détection d’or confuse ou maudite vers `trap_detect` ; commencer par le cas non maudit + confusion contrôlée.
- **Expérience :** scénario avec consommables et sans ; interruption pour danger, guérison de confusion après lecture, validation du rendu de carte dans [bridge].
- **Mesure / risque :** succès par parchemin et tours économisés. Ne pas confondre représentation trompeuse d’une source maudite et détection fiable ; le handler ne doit pas être affamé par la navigation.

### P046 — Terre : choisir l’outil selon le coût de la percée

**A/B/D/E · priorité 2 · M · précise I81/145/180.**

- **Modification :** le chemin vers les candidats de portail compare marche, pioche et baguette d’excavation ; inclure équipement de l’outil, durée de creusement et menace pendant l’occupation. Conserver une charge de secours si elle a une utilité future.
- **Expérience :** roche courte/longue, pioche maudite, Amulette en main ou au cou, élémentaire adjacent. Le bot sait déjà creuser ; tester le choix d’outil et l’ordonnancement.
- **Mesure / risque :** tours Terre→Air et consommables restants. Une baguette rapide n’est rentable que si elle ouvre réellement un trajet permis ; ne pas deviner la position cachée du portail.

### P047 — Eau : mémoire temporelle des bulles et du portail

**Tous · priorité 1 · L · précise I84/185.**

- **Modification :** séparer dans [pathing]/[game] observations récentes de bulles, terrain stable et portail observé à un instant. Planifier sur 1–3 tours, revalider après mouvement des bulles et autoriser une attente utile.
- **Expérience :** comparaison politique actuelle, mémoire très courte et prédiction locale ; inclure absence de respiration magique et absence de lévitation. Vérifier les règles dans le moteur avant de qualifier une case de sûre.
- **Mesure / risque :** tours Eau→Astral, entrée involontaire dans l’eau et oscillations. Effacer toute la carte perdrait aussi les indices utiles ; conserver éternellement une coordonnée de portail mobile est l’erreur inverse.

### P048 — Portail connu : entrée confirmée, pas répétition de Sit

**Tous · priorité 1 · S · précise I194.**

- **Modification :** `seek_portal` propose actuellement de s’asseoir lorsqu’il est déjà sur la cible. Mémoriser tentative, état de lévitation et message reçu ; après un échec sans transition, rafraîchir le terrain puis essayer une autre méthode légale, sans répéter aveuglément.
- **Expérience :** vrai portail, glyphes trompeurs, portail déplacé sur l’Eau et état empêchant l’activation. Définir la réussite par changement de Plan confirmé.
- **Mesure / risque :** répétitions `sit`, faux portails et sorties réussies. Ne pas supprimer définitivement la seule sortie à cause d’une tentative interrompue ; conserver sa dernière observation et son incertitude.

### P049 — Astral : coût du trajet complet jusqu’à une offrande possible

**Tous · priorité 1 · M · précise I85/187/188.**

- **Modification :** `_astral_known_altars` connaît déjà trois cases. Évaluer distance, foule, Cavalier, alignement connu et possibilité d’observer l’autel ; garder le temple choisi avec hystérésis. Un autel visible peut être examiné, un alignement caché ne doit pas être inventé.
- **Expérience :** plus proche géométriquement contre plus faible coût estimé ; reprendre une cible abandonnée seulement sur information nouvelle.
- **Mesure / risque :** temples visités, tours Astral→offrande et changements de cible. Les positions statiques n’impliquent pas un alignement fixe ; le choix peut légitimement nécessiter d’inspecter plusieurs temples.

### P050 — Cavaliers : contourner avec une fenêtre de passage

**Tous · priorité 2 · M · précise I85/91.**

- **Modification :** remplacer le seul coût fixe 40 de [pathing] `pass_monster` par délai estimé de passage, détour disponible et mémoire du dernier décès/réapparition observé. Après neutralisation d’un obstacle, exploiter immédiatement l’ouverture.
- **Expérience :** Astral encombré avec chemins alternatifs ; comparer coût 20/40/80 et coût dynamique. Interdire la manipulation opportuniste de cadavres dangereux dans ce sous-plan.
- **Mesure / risque :** cycles de combat au même endroit et délai jusqu’à l’autel. La résurrection est incertaine ; l’horizon court ne doit pas supposer qu’un Cavalier restera absent.

## P051–P060 — Combats et déplacements de survie

### P051 — Danger estimé sur les prochaines actions ennemies

**B/D/F, puis E · priorité 1 · L · précise I98/121.**

- **Modification :** compléter `low_hp` et `can_handle` par dégâts plausibles à 1–3 actions, vitesse relative, nombre d’adversaires, résistances et effets spéciaux. À défaut d’information exacte, utiliser une borne conservatrice plutôt qu’un HP ennemi caché.
- **Expérience :** même fraction de PV face à un rat, plusieurs soldats et un monstre très rapide ; comparer au seuil fixe de 45 %.
- **Mesure / risque :** première mort, consommables d’urgence utilisés à temps et retraites inutiles. Le modèle n’est pas un simulateur exact ; calibrer ses erreurs avant de lui confier toutes les décisions.

### P052 — Valeur de la case de repli selon les monstres présents

**B/D/F ; A pour la congestion · priorité 1 · M · précise I55/104.**

- **Modification :** `exposed` compte principalement les voisins praticables. Ajouter les voies d’attaque des monstres qui traversent les murs, angles de tir et sorties disponibles. Un couloir peut être bon contre une foule ordinaire et mauvais contre des xorns.
- **Expérience :** même carte contre foule classique, xorn et mixte ; comparer choix couloir/pièce/escalier avec un chemin de fuite vérifié.
- **Mesure / risque :** adversaires capables d’attaquer simultanément, dégâts et sorties réussies. « Toujours dans les pièces » serait une surcorrection ; sélectionner selon la menace réelle.

### P053 — Potion de soin avant le seuil de dernière chance

**B/D/F · priorité 1 · S · précise I38/108.**

- **Modification :** ajouter à `retreat` un choix explicite de soin rapide selon risque au prochain tour et PV récupérables. Prioriser potion accessible directement ; comparer au temps d’extraction d’un sac et à la prière disponible.
- **Expérience :** PV bas avec potion en main, potion dans sac, ennemis rapides et prière indisponible. Conserver une réserve définie en P077.
- **Mesure / risque :** morts avec soin inutilisé et surconsommation. Attendre le seuil de prière ou un pourcentage fixe peut être trop tard ; boire à la moindre blessure épuiserait les réserves avant Gehennom.

### P054 — Évasion choisie parmi les options légales du niveau

**B/D/F · priorité 1 · M · précise I108/212–215.**

- **Modification :** avant combat désespéré, comparer téléportation de soi, téléportation de l’obstacle, excavation, escalier et autre sortie connue. Modéliser séparément les interdictions de téléportation, creusement et changement de niveau.
- **Expérience :** chaque option en situation autorisée et refusée, avec Amulette et sur les Plans. Pour les potions maudites de gain de niveau, dériver les restrictions du moteur avant intégration.
- **Mesure / risque :** évasions confirmées, charges gaspillées et atterrissages dangereux. Ne pas supposer que tous les effets de téléportation partagent les mêmes restrictions.

### P055 — Combat à distance sensible aux rebonds et alliés

**Tous · priorité 2 · M · précise I103/106.**

- **Modification :** enrichir `ranged`, `safe_zap` et `targettable` par ligne de tir, alliés/pacifiques, rebonds, résistances connues et valeur d’une charge. Préférer projectile récupérable contre une menace mineure.
- **Expérience :** couloir réfléchissant, ennemi résistant, pacifique derrière la cible, mind flayer à distance ; comparer règles actuelles et estimation de l’effet utile.
- **Mesure / risque :** dégâts évités au contact, dégâts collatéraux et consommation par élimination. Les identités incertaines et angles de rebond imposent une marge de prudence en survie réelle.

### P056 — Kiting seulement si l’on gagne réellement de la distance

**B/D/F · priorité 2 · M · précise I98/121.**

- **Modification :** `kite` doit tenir compte de vitesse observée, charge, terrain, coin sans issue et distance à une sortie ; mémoriser les échecs récents du motif recul/attaque.
- **Expérience :** bottes de vitesse présentes/absentes, héros burdened, ennemi plus rapide, boucle autour d’un obstacle. Comparer au choix de rester et d’utiliser un objet.
- **Mesure / risque :** attaques ennemies reçues par dégâts infligés et cycles sans progrès. Une vitesse théorique supérieure n’assure pas un tour gratuit à chaque mouvement ; calibrer sur les observations moteur.

### P057 — Limiter le combat opportuniste même sans invincibilité

**B/D/F · priorité 2 · M · précise I56/134.**

- **Modification :** évaluer bénéfice d’XP, cadavre utile ou accès libéré contre dégâts et ressources. `fight` chasse actuellement aussi des ennemis « leftovers » ; éviter ceux qui n’augmentent pas une capacité manquante.
- **Expérience :** conserver les combats utiles à l’XL de quête mais couper la chasse après le seuil ; comparer avec la même politique en début de partie.
- **Mesure / risque :** XL à l’entrée de quête, tours d’exposition et taux de survie. Supprimer tout combat peut produire un héros sous-entraîné ; l’objectif est un arbitrage, pas un évitement universel.

### P058 — Verrouillage des passages étroits avant engagement

**B/D/F · priorité 2 · M · extension de I98.**

- **Modification :** avant d’avancer vers plusieurs ennemis, choisir une case où le nombre d’attaquants simultanés est réduit ; utiliser porte fermable ou angle connu lorsque cela conserve une sortie. Réévaluer si un ennemi traverse les murs.
- **Expérience :** deux ou trois poursuivants, porte ouverte/fermée et monstre fouisseur ; comparer préparation de 1–3 tours au déplacement actuel vers l’ennemi.
- **Mesure / risque :** dégâts cumulés et retards de progression. Préparer un fort contre chaque rat serait coûteux ; réserver la manœuvre aux combats où le modèle de danger prévoit un bénéfice.

### P059 — Escalier de secours sans oscillation de niveaux

**B/D/F · priorité 1 · M · précise I38/97.**

- **Modification :** lorsque `retreat` monte, créer une intention de récupération : niveau cible, condition de retour, danger laissé derrière et limite d’attente. Ne pas laisser `progress` redescendre immédiatement avant réparation.
- **Expérience :** ennemi qui suit, niveau supérieur également dangereux, faim pendant repos ; comparer retour à 60/80/90 % PV ou seuil de risque recalculé.
- **Mesure / risque :** cycles ascend/descend, morts après retour et tours de repos. Un escalier n’est pas une zone sûre par définition ; la décision de se reposer doit vérifier les menaces locales.

### P060 — Charge et dégâts matériels dans le coût du combat assisté

**A/C/E assisté · priorité 2 · M · nuance I133/136/211.**

- **Modification :** estimer coût d’un combat en tours, immobilisation, vols, corrosion, malédictions et perte de capacités, même si la mort est annulée. Autoriser un détour quand il préserve un objet indispensable ou évite un engorgement.
- **Expérience :** chemin direct contre nymphe/incube/corrodeur et petit détour ; journaliser l’état de l’équipement avant/après les sauvetages.
- **Mesure / risque :** ascensions, temps et ressources perdues. La variante « bulldozer » est une hypothèse à comparer ; mourir n’est pas un soin gratuit sans effet secondaire garanti, et ne permet pas automatiquement de traverser lave ou eau.

## P061–P070 — Statuts, résistances et urgences

### P061 — Anti-slime avant la transformation

**B/D/F, diagnostic A · priorité 1 · M · précise I100/102.**

- **Modification :** ajouter un objectif d’urgence déclenché par les messages de sliming, avec remèdes légalement disponibles et temps d’accès. Prioriser un effet de feu approprié quand réalisable, sinon autre remède vérifié ; consulter [timeout-c]/[pray-c].
- **Expérience :** slime avec outil en inventaire direct, outil dans sac, aucun outil et prière interdite. Contrôler les risques secondaires pour objets et PV.
- **Mesure / risque :** guérison avant transformation, morts et armures perdues. `noslime` masque aujourd’hui cette faiblesse sous invincibilité ; une diminution de lifesaves ne suffit pas à valider le traitement.

### P062 — Pétrification : réponse selon temps d’accès au remède

**B/D/F/E · priorité 1 · M · précise I45/100.**

- **Modification :** `handle_illness` possède déjà la réponse lézard/prière. Ajouter choix selon deadline observable, objet accessible, possibilité de manger et sécurité du terrain ; maintenir une ressource adaptée en accès direct quand ce danger est plausible.
- **Expérience :** lézard dans sac contre en inventaire, lévitation, incapacité d’utiliser les mains ; scénarios Méduse et contact avec corps dangereux, avec protections variables.
- **Mesure / risque :** guérisons et décès avec remède présent mais inutilisable. Ne pas généraliser un moyen contre un regard à tous les modes de pétrification ; la prévention doit aussi auditer les manipulations de cadavres.

### P063 — Éviter la dette d’attributs face aux mind flayers

**B/D/F ; A pour conserver le rythme · priorité 1 · M · précise I103.**

- **Modification :** traiter les attaques de cerveau comme un danger distinct des PV : distance minimale, équipement pertinent, attaque à distance ou évasion. Estimer la réserve d’Intelligence depuis le statut public et reclasser le danger après chaque drainage.
- **Expérience :** casque présent/absent, Intelligence basse, monstre invisible ; comparer même CA avec réponse spécifique et réponse générique de combat.
- **Mesure / risque :** drain observé, morts et `brainsave` côté diagnostic. Le casque et la visibilité réduisent certains risques mais ne constituent pas une immunité ; ne pas substituer une hypothèse de protection à la vérification des règles.

### P064 — Maladie : guérir une deadline, pas répéter un rituel

**B/D/F et Astral A · priorité 1 · M · précise I41/91.**

- **Modification :** `handle_illness` choisit corne, feuille, potion, prière ; ajouter âge de la maladie observée, tentatives, accès au remède et risque de réinfection. Si une guérison est immédiatement annulée, déplacer le héros hors de l’exposition lorsque possible.
- **Expérience :** Pestilence adjacente, nourriture contaminée, corne qui échoue aléatoirement et corne maudite. Comparer traitement sur place et mouvement/soin combinés.
- **Mesure / risque :** survie, soins par épisode et tours sans progression. Une maladie sans timer directement connu nécessite une borne prudente ; ne pas attendre d’atteindre une deadline supposée exacte.

### P065 — Corne de licorne : distinguer échec, malédiction et rechute

**Tous · priorité 1 · M · correction de prémisse, précise I41.**

- **Constat / modification :** `_recovery_unihorn` bloque après six usages en trente tours sans analyser la guérison intermédiaire. Suivre symptômes/attributs avant-après, messages et BUC connu ; une nouvelle attaque après guérison n’est pas un échec de corne.
- **Expérience :** drainage d’attribut, déficits non curables, `Fixed_abil`, corne bénie/non maudite/maudite et réinfection. [apply-c] permet encore certaines restaurations d’attributs en 3.6.7 ; conserver un plafond de dépense.
- **Mesure / risque :** troubles guéris par usage et faux blocages de 300 tours. Les échecs aléatoires sont normaux ; inversement une apparence anciennement bénie ne garantit pas le BUC actuel après malédiction.

### P066 — Capacités de traversée par terrain et état courant

**Tous, surtout E/F · priorité 1 · M · précise I46/83/84.**

- **Modification :** centraliser les prédicats eau/lave/air, lévitation/vol/respiration/marche sur l’eau, durée restante connue, équipement retirable et objets exposés. Appeler ce modèle depuis [pathing], combat et actions exigeant le contact au sol.
- **Expérience :** retrait de la source de lévitation, anneau maudit, perte de bottes, accès à un objet en fosse et Plan de l’Eau. Comparer au seul test de présence d’un anneau.
- **Mesure / risque :** trajets interrompus et morts de terrain. Une capacité possédée n’est pas forcément activée ni utilisable ; prévoir une case d’atterrissage sûre avant de changer d’équipement.

### P067 — Nuages : coût d’exposition cumulé

**B/D/F ; A pour les pertes de temps · priorité 2 · M · précise I54/105.**

- **Modification :** enrichir la pénalité fixe `cloud_p` de [pathing] avec protection connue, PV, longueur du passage et possibilité de sortir. Distinguer la traversée de deux cases et un combat stationnaire dans la zone.
- **Expérience :** traversée courte contre détour, résistance au poison acquise/perdue, ennemi bloquant la sortie. Valider la nature des nuages par les règles et observations concernées.
- **Mesure / risque :** tours exposés, dégâts et décès par gaz. La résistance au poison ne doit pas être interprétée comme une autorisation de négliger tous les autres effets du terrain ou du combat.

### P068 — Voir l’invisible et télépathie comme capacités distinctes

**Tous · priorité 1 · M · précise I53/106.**

- **Modification :** différencier identité visible, position télépathique, détection, avertissement et souvenir d’un invisible ; choisir bandeau/serviette seulement si l’information gagnée compense la cécité. Faire porter ce raisonnement à `hit`, `hunt` et au choix de souhait.
- **Expérience :** ennemi invisible, ennemi sans esprit, source de télépathie variable et menace de terrain ; comparer combat aveugle et conservation de vision.
- **Mesure / risque :** attaques de cases vides, farlook inutile et dégâts reçus. Un casque de télépathie n’est pas une source générale de voir l’invisible ; un signal de présence n’est pas une identification certaine.

### P069 — Prière avec état de confiance et valeur de secours

**B/D/F/C · priorité 2 · M · précise I36/38/113.**

- **Modification :** conserver les règles 3.6 de [rules36] et l’interdiction en Gehennom de [game] ; enrichir la décision avec historique observable des prières, actes d’alignement, urgences concurrentes et autres remèdes. Le blocage de 1 000 tours après hypocrisie n’atteste pas, à lui seul, un alignement réparé.
- **Expérience :** faim puis blessure, prière récente, autel contraire et entrée de Gehennom.
- **Mesure / risque :** prières utiles/refusées et morts avec alternative disponible. Ne jamais lire chance, alignement record ou timer privé ; conserver une estimation prudente et expliciter l’incertitude.

### P070 — Elbereth comme fenêtre de réparation et de sortie

**B/D/F, hors Gehennom/Plans · priorité 2 · M · précise I37.**

- **Modification :** après gravure efficace, choisir explicitement soin, dégagement ou attente courte ; interdire la reprise d’une attaque contradictoire depuis la case. Réévaluer texte, adversaires qui respectent la gravure et dégâts à distance.
- **Expérience :** monstre respectueux seul, foule mixte, gravure usée, arrivée d’un humain/minotaure ; comparer au repli actuel sans modifier les règles moteur.
- **Mesure / risque :** fenêtres utiles, messages d’hypocrisie et survie. La gravure n’est ni une protection universelle ni une raison de rester sur place ; conserver les exclusions déjà présentes dans [rules36].

## P071–P080 — Équipement, souhaits et ressources

### P071 — Souhaits guidés par le prochain verrou

**Tous · priorité 1 · M · précise I47/99/155/215.**

- **Modification :** `wish` utilise une liste fixe. Comparer un score par manque : franchissement, défense, guérison, portail, puissance, bougies. Estimer disponibilité d’un substitut proche et valeur du prochain jalon ; séparer politique A et politique B/F.
- **Expérience :** même état de Château avec kit complet, sans lévitation, sans réflexion ou sans MR. Préserver la logique de recharge et les contraintes de souhait du moteur.
- **Mesure / risque :** jalons débloqués par souhait et ascensions. Sous A, une amulette de vie peut avoir peu de valeur ; sous B elle peut en avoir beaucoup. Aucune liste unique ne doit servir d’optimum présumé.

### P072 — Réserve de charges par fonction d’urgence

**Tous · priorité 2 · M · précise I47/108/213.**

- **Modification :** classer les usages de baguettes en combat ordinaire, ouverture de trajet et urgence ; réserver 0/1/2 charges estimées de téléportation/excavation selon phase. Respecter l’incertitude sur les charges et les limites de recharge, notamment souhait.
- **Expérience :** trajet avec nombreux petits obstacles puis vraie impasse ; comparer dépense immédiate et réserve conditionnelle dans `ranged`, `recharge`, `use_items`.
- **Mesure / risque :** échecs avec baguette vide et consommables inutilisés à la mort. Une réserve trop rigide ressemble à ne jamais utiliser les objets ; autoriser sa consommation face au danger vital.

### P073 — Équipement optimisé sous contraintes de capacités

**Tous, surtout E/F · priorité 1 · M · précise I47/52/87.**

- **Modification :** au lieu de préférences pièce par pièce seulement, chercher un ensemble réalisable couvrant MR, réflexion, vitesse, mobilité et mains disponibles. Pénaliser retrait long, malédiction, changement d’arme et slot d’amulette occupé.
- **Expérience :** GDSM + amulette de réflexion contre autre combinaison acquise, puis Amulette de Yendor portée pour indices. Comparer survie et interruptions liées au changement de tenue.
- **Mesure / risque :** tours sans capacité critique et coût d’équipement. L’optimiseur utilise uniquement les propriétés connues ; un meilleur score d’armure ne justifie pas de perdre la seule mobilité nécessaire.

### P074 — BUC utile : identifier ce qui change une décision

**Tous, surtout E/F · priorité 2 · M · précise I142/144.**

- **Modification :** limiter trajets vers autel et essais d’objets à ceux dont le BUC peut changer équipement, urgence ou invocation. Réévaluer après malédiction observée ; conserver une catégorie « anciennement connu ».
- **Expérience :** inventaire de milieu de partie puis préparation d’invocation ; comparer tout identifier, seulement les objets utilisés et seuil de valeur de détour.
- **Mesure / risque :** tours de BUC, blocages maudits et ressources consommées. Économiser des contrôles sur une pièce jamais utilisée est utile ; économiser sur l’unique moyen de lévitation peut coûter la partie.

### P075 — Poche d’urgence en inventaire direct

**B/D/F ; A pour progression · priorité 1 · S · extension de I112.**

- **Modification :** `bag_items` range largement parchemins et potions. Garder accessibles un soin, un moyen d’évasion, un remède critique et éventuellement délivrance de malédiction selon les risques de la phase ; protéger le reste dans un sac adapté.
- **Expérience :** urgence avec main occupée, sac inaccessible et slot libre limité ; comparer latence de deux/trois actions contre accès direct.
- **Mesure / risque :** morts avec remède trop lent, dégâts élémentaires sur objets exposés et charge. L’accès direct et la protection du consommable sont deux coûts à arbitrer ; le panier varie selon les résistances et les ennemis.

### P076 — Réserve de désensorcellement avant les phases critiques

**Tous · priorité 1 · M · précise I65/101.**

- **Modification :** avant Méduse, invocation et Plans, conserver une méthode réellement utilisable pour libérer équipement ou objets obligatoires. `cursed_levi` attend parfois longtemps : basculer vers un objectif explicite d’acquisition/réparation plutôt qu’une attente générique.
- **Expérience :** anneau maudit, corne maudite, Cloche maudite avec eau bénite dans un sac accessible/inaccessible ; comparer préparation préventive et réparation tardive.
- **Mesure / risque :** durée des blocages BUC et coût de réserve. Ne pas immobiliser le bot indéfiniment pour obtenir un second remède alors que le premier suffit et que l’objectif est atteignable.

### P077 — Garder un soin au lieu de tout convertir en PV max

**B/D/F · priorité 1 · S · extension de I38/99.**

- **Constat / modification :** `use_items` peut boire extra/full healing à PV pleins pour augmenter le maximum. Comparer réserve de 0/1/2 potions accessibles avant cette conversion, modulée par autre secours disponible et phase.
- **Expérience :** mêmes états avec potion unique, plusieurs potions, amulette de vie ou aucune assurance ; conserver les bénéfices de PV max lorsque la réserve est déjà satisfaite.
- **Mesure / risque :** morts avec pénurie de soin, PV max et soins restants à l’ascension. Ne pas déduire que toute conversion est mauvaise ; elle peut réduire le besoin futur de soins.

### P078 — Potions de gain de niveau affectées à un usage

**Tous · priorité 2 · M · précise I215.**

- **Modification :** séparer XP nécessaire à la quête, mobilité potentielle d’une potion maudite et consommation opportuniste. `use_items` les boit aujourd’hui dans une logique générale ; réserver une potion identifiée si son usage de déplacement est légal et plus précieux.
- **Expérience :** avant XL14, après quête, pendant remontée avec Amulette et près d’un niveau où l’effet est refusé ; lire les règles de [potion-c] avant de fixer les points d’usage.
- **Mesure / risque :** tours gagnés, accès à la quête et potions gaspillées. Ni le BUC inconnu ni un raccourci supposé sur les Plans ne justifient une consommation aveugle.

### P079 — Génocide sélectionné selon menaces et règles 3.6

**Tous · priorité 2 · M · précise I47/100/103.**

- **Modification :** `respond_geno` dépile des listes fixes. Choisir classe/type selon BUC, race/forme du héros, phase, résistances et ennemis effectivement éliminables ; conserver une liste de réponses interdites et gérer le refus d’une cible.
- **Expérience :** menace visible critique contre prévention tardive, source bénie/non maudite, cible déjà génocidée ou non génocidable. Vérifier chaque réponse via [read-c]/[monst-c].
- **Mesure / risque :** ressources transformées en réduction de danger et pertes évitées. Le génocide du héros n’est pas sauvé par l’invincibilité actuelle ; cette action exige une validation sémantique particulièrement stricte.

### P080 — Valeur d’un objet moins son coût de transport

**Tous · priorité 1 · M · précise I42/144.**

- **Modification :** dans `take_selector`, `drop_junk`, `want_gold` et `bag_items`, intégrer poids, slots, état du sac, vitesse perdue et temps d’accès. Conserver une marge de charge plus forte avant combat, traversée et fuite.
- **Expérience :** seuil « rester unburdened » contre marge 10/20 % et stratégie actuelle ; décliner avec et sans sac sans fond.
- **Mesure / risque :** tours chargés, acquisition d’objets clés et ressources abandonnées. Un score de valeur statique ne doit pas faire jeter le dernier outil de franchissement ; protéger les objets requis et éviter ramassage/dépôt oscillant.

## P081–P090 — Faim et acquisition sans kit

### P081 — Réserve alimentaire en tours jusqu’au prochain point sûr

**C/D/F · priorité 1 · M · précise I111–113.**

- **Modification :** compléter `nutrition_sum` par dépense estimée selon actions, équipement et durée de route. Avant un détour long, viser une réserve en tours plutôt qu’un nombre fixe de rations ; intervalle prudent si nutrition exacte inconnue.
- **Expérience :** exploration prolongée, régénération portée, charge, retour des Mines ; comparer réserves de 500/1 000/2 000 tours estimés.
- **Mesure / risque :** faim/morts, tours de collecte et nourriture inutilement portée. Le bot peut estimer depuis états de faim et aliments connus, sans lire la nutrition privée du moteur.

### P082 — Politique alimentaire indépendante de l’invincibilité

**A/B/C/D · priorité 1 · S · précise I141.**

- **Modification :** exposer au bot la configuration d’anti-famine déclarée, indépendamment de `assisted_tactics`. Sous anti-famine, distinguer manger pour intrinsèque/XP et manger pour nutrition ; couper seulement la seconde activité dans une variante.
- **Expérience :** plan 2×2 anti-famine oui/non et politique nutritionnelle oui/non, invincibilité fixée ; comparer les repas et détours, notamment `feed` sur l’Astral.
- **Mesure / risque :** tours économisés et intrinsèques obtenues. Le profil C garde l’invincibilité mais retire l’anti-famine : assimiler « assisted » à « pas besoin de nourriture » serait un bug de configuration.

### P083 — Cadavres : fraîcheur connue et bénéfice marginal

**Tous, surtout D/F · priorité 1 · M · précise I112.**

- **Modification :** réutiliser [tracker] `fresh_corpse` et [player] `safe_corpse_type` ; ajouter incertitude d’âge, temps de trajet/repas, tabous de race, danger pendant occupation et résistance encore manquante.
- **Expérience :** cadavre vu après retour de niveau, plusieurs cadavres identiques, repas interrompu, résistance déjà acquise. Comparer chasse au cadavre utile et opportunisme sur le chemin.
- **Mesure / risque :** intrinsèques par détour et incidents alimentaires. Un cadavre généré depuis longtemps ne devient pas frais parce qu’il vient d’être observé ; préserver les exclusions de sécurité déjà codées.

### P084 — Manger avant le combat lorsque l’occasion est sûre

**C/D/F · priorité 2 · S · précise I112/113.**

- **Modification :** déclencher repas préventif à Hungry si zone sûre et longue occupation à venir ; à Weak, préférer nourriture rapide directement accessible. Prévoir interruption sur menace nouvelle et réponse correcte à `Continue eating?`.
- **Expérience :** entrée de Méduse, départ de branche, combat suivi d’un trajet sans nourriture ; comparer à l’attente d’un état plus grave.
- **Mesure / risque :** évanouissements, repas interrompus et étouffements. Le régime sans anti-famine retire aussi la protection contre l’étouffement ; la satiété et la quantité prévue doivent limiter le repas.

### P085 — Excalibur : acquisition opportuniste et plafond de risque

**E/F/B · priorité 2 · M · précise I43.**

- **Modification :** `make_excal` existe déjà. Conditionner le détour fontaine à XL admissible, arme adaptée, PV, issues et menaces possibles ; arrêter après budget de tentatives ou dégradation du contexte.
- **Expérience :** politique systématique actuelle contre opportuniste et report après amélioration défensive ; même équipement de départ, sans ajouter Excalibur au kit.
- **Mesure / risque :** Excalibur obtenue avant Château, coût et morts liées à la fontaine. Le gain d’arme est durable mais l’interaction peut créer un danger immédiat ; mesurer les deux côtés.

### P086 — Boutique : acheter une capacité, pas explorer tout le stock

**Tous, surtout E/F · priorité 2 · M · précise I40/143.**

- **Modification :** `shop_action` reçoit une liste courte de manques : nourriture, clé, mobilité, bougies, remède. Limiter identification par prix et détours lorsque le kit couvre déjà ces besoins ; conserver l’achat ciblé d’un objet décisif.
- **Expérience :** boutique riche mais lointaine, objet nécessaire abordable, objet précieux inutile, commerçant fâché. Comparer temps d’inspection et bénéfice obtenu.
- **Mesure / risque :** capacité acquise par tour/gold et incidents de boutique. Désactiver toutes les boutiques sous A ferait aussi perdre une source de bougies ; le filtre doit dépendre du besoin réel.

### P087 — Mines et Sokoban déclenchés par la récompense manquante

**A/E/F · priorité 1 · M · précise I39/40/114/147.**

- **Modification :** entre `full` et `fast`, créer une route conditionnelle : Mines pour outil/temple/lumière/protection, Sokoban pour récompense pertinente et capacités connues. Ne pas attribuer à Sokoban une garantie de lévitation ; raisonner sur les récompenses réellement possibles.
- **Expérience :** kit complet puis retrait isolé pioche, sac et réflexion ; comparer route full, fast et conditionnelle.
- **Mesure / risque :** temps au Château, acquisition des capacités et survie. Une branche évitée peut fournir XP et nourriture en plus de sa récompense finale ; inclure ces effets dans l’évaluation.

### P088 — Familier comme outil de début de partie à budget limité

**E/F · priorité 3 · L · extension de I218.**

- **Modification :** exploiter seulement des signaux observables du familier pour aide au combat et indices BUC, puis abandonner les détours si le coût devient excessif. Commencer par reconnaître sa contribution avant de planifier élevage ou monture.
- **Expérience :** conserver/accompagner le familier jusqu’à Minetown contre route actuelle ; pas d’attente indéfinie pour qu’il teste un objet.
- **Mesure / risque :** première mort, objets maudits évités, tours d’attente et blocages de couloir. Le comportement du familier n’est pas un oracle instantané ; il peut mourir, être affamé ou se trouver hors de portée.

### P089 — Substituts explicites pour chaque objet du kit

**E/F · priorité 1 · M · précise I114–118.**

- **Modification :** créer des objectifs de capacité après retrait d’une pièce : MR/réflexion, déplacement rapide, franchissement, soin des états, portage, creusement, nutrition. Reconnaître plusieurs objets possibles au lieu de chercher seulement le nom fourni par le kit.
- **Expérience :** retirer un seul objet, puis deux objets dont les fonctions interagissent ; comparer acquisition ciblée et souhait tardif. Journaliser aussi connaissance initiale et BUC fournis par le kit.
- **Mesure / risque :** temps jusqu’au remplacement fonctionnel et ascensions. Un objet nommé « équivalent » peut avoir des contraintes de slots, de malédiction ou de retrait très différentes.

### P090 — Amélioration offensive avant le long milieu de partie

**E/F/B · priorité 2 · M · extension de I43/47/107.**

- **Modification :** à des paliers observables, évaluer arme actuelle, compétence disponible, dégâts plausibles, coût d’enchantement et consommation de projectiles. `enhance` existe déjà ; mesurer les promotions effectivement choisies et les changements d’arme utiles.
- **Expérience :** arme de départ, Excalibur, bonne arme ordinaire ; comparer investissement offensif précoce et armure seule, à ressources identiques.
- **Mesure / risque :** tours par combat, dégâts reçus et progression vers XL14. Se focaliser sur les PV/CA peut laisser des combats trop longs ; changer d’arme trop souvent perd aussi compétences et tours d’équipement.

## P091–P100 — Approches exploratoires

### P091 — Micro-planificateur de combat sur observations publiques

**B/D/F puis A · priorité 3 · L · précise I119/121.**

- **Modification :** générer 5–10 actions légales et simuler approximativement 1–3 échanges sous plusieurs hypothèses de vitesse/dégâts ; noter survie, espace gagné, ressources et distance à l’objectif. Garder BotHack pour les longues routes.
- **Expérience :** mode observateur d’abord : proposition sans action, coût plafonné à 10/30/100 ms ; activer ensuite sur combats à haut risque uniquement.
- **Mesure / risque :** erreurs de prédiction, première mort et latence. Utiliser la carte réelle cachée ou cloner le moteur avec toutes ses informations donnerait un avantage d’observation différent ; un modèle incomplet doit pouvoir s’abstenir.

### P092 — Apprendre aussi des décisions qui précèdent les échecs

**Tous · priorité 3 · L · précise I120/232.**

- **Modification :** constituer des épisodes observables autour de vols, transitions, soins tardifs et blocages ; annoter l’effet de l’action et le profil d’aide. Entraîner d’abord un petit classement d’actions ou un détecteur d’impasse, plutôt qu’une politique complète.
- **Expérience :** séparation des seeds et versions entre apprentissage/validation ; g011 et ses rejeux restent dans le même groupe. Comparer au bot sur données jamais utilisées pour régler les seuils.
- **Mesure / risque :** détection anticipée et effet réel après activation. Une action d’un run ascensionné n’est pas automatiquement bonne ; les 506 sauvetages de g011 interdisent de traiter toute sa trajectoire comme démonstration de survie.

### P093 — Bandit de stratégies locales avec validation gelée

**A puis profils séparés · priorité 3 · L · précise I221–223.**

- **Modification :** choisir entre méthodes bornées pour une tâche répétée : explorer, détecter, creuser, contourner. Contexte : phase, équipement connu et historique local ; retour : tâche accomplie, tours et ressources, pas score NetHack brut.
- **Expérience :** apprentissage sur seeds de développement ; geler la règle obtenue avant évaluation finale. Comparer à la meilleure stratégie fixe et à un choix aléatoire contrôlé.
- **Mesure / risque :** coût par tâche et winrate indépendant. L’allocation adaptative des essais peut sélectionner un gagnant chanceux ; ses résultats d’entraînement ne sont pas la preuve finale du gain.

### P094 — Second expert en cas d’impasse, avec état partagé explicite

**Tous · priorité 3 · L · précise I230.**

- **Modification :** conserver une seule mémoire canonique et changer temporairement de politique : explorateur, récupérateur d’objet, rush assisté ou survie. Définir entrée, sortie et budget de chaque expert ; éviter deux bots indépendants avec souvenirs divergents.
- **Expérience :** activation après deux récupérations infructueuses, comparaison au reset d’exploration et à l’augmentation seule du timeout.
- **Mesure / risque :** impasses résolues et boucles entre experts. Plusieurs listes globales et closures stockent déjà de l’état dans [mainbot] ; leur isolation est un prérequis si l’on instancie plusieurs experts ou reprend une sauvegarde.

### P095 — PyPy et optimisations CPU avec preuve de comportement

**Tous · priorité 2 · M · précise I29/196/207/208.**

- **Modification :** comparer CPython actuel, PyPy et optimisations locales du profilage sur les mêmes traces/tâches. Vérifier compatibilité, démarrage, mémoire et sensibilité à la charge du worker ; aucun facteur ×3 ou ×5 présumé.
- **Expérience :** benchmark court après échauffement, puis runs entiers avec mêmes limites de tours et limites murales déclarées. Expliquer toute divergence d’action ; vérifier l’absence de modification involontaire des ordres de parcours.
- **Mesure / risque :** CPU par décision, mémoire maximale et ascensions par heure machine. Un microbenchmark favorable peut perdre sur des parties courtes ou très concurrentes.

### P096 — Rendu incrémental et chemins réutilisés sous conditions

**Tous · priorité 2 · L · précise I27/28/201/206.**

- **Modification :** [bridge] `_update_frame` parcourt toute la carte ; exploiter les deltas déjà reçus. Réutiliser un chemin ou arbre de distances tant que terrain, cible, menaces et capacités pertinentes n’ont pas changé ; réexaminer le prochain pas à chaque décision.
- **Expérience :** couloir stable, porte modifiée, téléportation, changement de lévitation et Eau. Comparer sorties d’état/actions avec implémentation sans cache sur des observations enregistrées.
- **Mesure / risque :** CPU économisé et décisions invalidées. Les caches d’exploration et écritures groupées de monstres existent déjà ; mesurer les coûts restants plutôt que réannoncer leurs gains.

### P097 — Exploration choisie pour l’information qu’elle apporte

**Tous · priorité 3 · L · précise I124/202/225.**

- **Modification :** scorer une frontière par probabilité de révéler sortie, porte, entrée de branche ou objet nécessaire, divisée par coût et risque. Apprendre des fréquences de niveaux/observations, avec une part de recherche générale pour éviter les angles morts.
- **Expérience :** comparer plus proche case inconnue, exploration actuelle et gain d’information ; séparer cartes ordinaires, labyrinthes et niveaux spéciaux reconnus.
- **Mesure / risque :** cases vues avant objectif découvert, chemins sans retour et succès d’exploration. La nouveauté visuelle n’est pas un objectif en soi ; les templates ne doivent pas éliminer une possibilité encore compatible avec les observations.

### P098 — Conseiller LLM rare sur un ensemble d’actions autorisées

**Tous, cohorte spécifique · priorité 3 · L · précise I127/228.**

- **Modification :** après impasse reconnue, fournir résumé observable, essais déjà faits et 3–8 actions candidates validées localement ; demander choix et hypothèse, avec plafond d’appels et de temps. Journaliser modèle, entrée, sortie, coût et action finale.
- **Expérience :** comparaison au choix heuristique parmi les mêmes candidats, au choix aléatoire et à l’absence de conseiller. Mode observateur d’abord, puis activation limitée.
- **Mesure / risque :** impasses sauvées par appel et ascensions sous budget total. Un LLM ne doit ni lire `priv`, ni inventer une commande moteur, ni consommer un budget caché ; les décisions doivent rester rejouables même si le modèle change.

### P099 — Ablations factorielles des buffs et de leurs interactions

**A à F · priorité 1 · M · précise I114/118.**

- **Modification :** après retrait unitaire, tester interactions plausibles : vitesse×charge, réflexion×slot Amulette, lévitation×pioche, anti-famine×régénération. Séparer aussi les avantages du kit : objet fourni, enchantement, BUC, protection et identification initiale.
- **Expérience :** petits plans 2×2 sur seeds appariées, une politique fixe puis une politique adaptée. Une ablation de connaissance seule demanderait une modification explicitement déclarée du mécanisme de kit.
- **Mesure / risque :** effets marginaux et interactions sur étapes et ascension. Additionner les gains de retraits isolés est trompeur ; changer simultanément aide et politique empêche d’attribuer le résultat à l’une seule.

### P100 — Curriculum d’aides qui ne masque pas leur coût

**A→B/D/F · priorité 2 · L · précise I93–95/101.**

- **Modification :** développer séparément budgets de vies 100/20/5/0 et retraits de protections anti-drain/slime/cerveau, avec événements précis et politique informée du régime déclaré. L’option n’existe pas actuellement : elle exigerait [assist-c] et un manifest versionné.
- **Expérience :** chaque palier a sa cohorte ; vérifier qu’après expiration toutes les protections prévues sont bien désactivées. La tactique doit pouvoir changer dynamiquement, car les handlers normaux sont aujourd’hui choisis à l’initialisation.
- **Mesure / risque :** ascensions par palier, première aide et dépendances restantes. Finir avec cinq vies constitue un jalon d’apprentissage ; seule une série complète sans ces aides mesure la survie sans invincibilité.

## Ordre de réalisation et protocole A/B

### Première vague : petits changements à fort pouvoir de diagnostic

P001–P006, P008–P010 forment le socle de comparaison. On peut préparer des variantes en parallèle du travail d’instrumentation, mais ne pas tirer de conclusion définitive avec des manifests incomplets.

| Rang pratique | Variante seule | Pourquoi elle mérite un essai tôt | Indicateur proximal | Validation nécessaire |
| --- | --- | --- | --- | --- |
| 1 | P033 budget local de récupération | Décalage concret entre démarrage du timer et arrivée sur place | Abandons avant arrivée | Cloche/Chandelier puis ascension |
| 2 | P034 porteur ciblé | Recherche actuelle parmi tous les hostiles | Combats sans rapport avec l’objet | Acquisition confirmée |
| 3 | P023 pickup d’objectif prioritaire | Ferme l’écart tuer→posséder | Objet acquis après décès du porteur | Aucun ramassage fatal en B |
| 4 | P025 nouveauté par phase | Remontée naturellement sans nouvelles cases | Faux arrêts de remontée | Budget global inchangé |
| 5 | P021 priorité à la remontée | Beaucoup de handlers avant `progress` | Tours Amulette→Plans | Réserves et sortie des Plans |
| 6 | P040 automate d’invocation | Précondition temporelle explicite dans le C | Invocation par tentative | Interruption et malédiction |
| 7 | P044 chaleur géométrique | Rectangle actuel + mélange avec `walked` | Candidats et temps au portail | Eau traitée séparément |
| 8 | P045 détection de portail | Handler existant limité et peu prioritaire | Sortie par parchemin | Coût d’acquisition des consommables |
| 9 | P048 confirmation de portail | `Sit` peut se répéter | Tentatives sans transition | Sortie réellement confirmée |
| 10 | P012 empreinte de pile | Historique récurrent de fixations | Look/pile et revisites | Aucun objet clé oublié |
| 11 | P065 diagnostic de corne | Code moteur et commentaire divergent | Guérisons/faux blocages | Corne maudite et réinfection |
| 12 | P077 réserve de soins | Conversion explicite de soins en PV max | Morts avec/sans soins restants | Première cohorte B |

Ensuite : P022/P024/P026/P027 pour le contrôle assisté ; P051–P054/P059/P061–P076 pour B/D ; P081–P090 pour C/E/F. Les chantiers P091–P098 viennent après une référence fiable et des traces exploitables.

### Procédure d’une expérience

1. **Écrire la fiche avant les runs.** Hypothèse falsifiable, changement unique, profils admissibles, paramètre testé, critère principal, budgets et critères d’exclusion. « Moins de temps à Vlad » est une hypothèse proximale ; « plus d’ascensions » reste la validation finale.
2. **Figer les entrées.** Copie de code distincte pour référence et candidat, hashes complets, binaire, kit, options, RNG, limites, superviseur, environnement et nombre de jobs. Ne pas resynchroniser une copie pendant qu’elle exécute la campagne.
3. **Vérifier localement le mécanisme.** Quelques cas déterministes de parsing/état lorsque nécessaires ; scénarios ciblés sur le worker. Une modification documentaire seule n’exige pas de runs de jeu.
4. **Déboguer sur 10–20 cas connus.** Ils sont un ensemble de développement, pas le test final. Une seed historiquement gagnante sert de sentinelle de régression, sans devenir l’ensemble de mesure.
5. **Faire un screening de 50–100 seeds neuves appariées.** Même liste pour référence/candidat, départs de Dlvl1, budget identique. À winrate rare, ce lot permet surtout d’identifier les crashes, blocages et déplacements de l’entonnoir.
6. **Confirmer les candidats prometteurs sur des seeds réservées.** Prévoir typiquement plusieurs centaines à plus de mille runs par bras selon taux de base, précision recherchée et coût ; calculer le besoin à partir du pilote, sans promettre qu’un nombre fixe suffira.
7. **Combiner seulement après essais séparés.** Référence, X, Y, X+Y sur une même nouvelle liste. Garder la combinaison seulement si elle confirme son intérêt : caches, priorités et limites interagissent.
8. **Transférer à un autre régime d’aides.** Refaire la comparaison dans B/C/E, puis D/F. Une victoire sous A ne promeut pas automatiquement une règle en survie réelle.

### Lire les statistiques sans surinterpréter les petites séries

- **Critère primaire :** taux opérationnel d’ascension vérifiée sous budgets fixés, toutes les parties éligibles démarrées au dénominateur. Un `limit` vaut échec à ce critère ; un crash et un blocage également.
- **Éligibilité :** départ normal depuis Dlvl1, aucun wizard/scénario, objectif complet. Ne pas se contenter de `counted_as_full_game` : dans [rungame], ce champ exclut wizard/scénario mais pas un `--goal castle` volontairement tronqué. Séparer objectifs partiels, replay choisi, entraînement et validation.
- **Arrêts opérateur / infrastructure :** les présenter séparément et garder leur effet dans la mesure opérationnelle. Une analyse secondaire peut suivre une règle d’exclusion préétablie et symétrique, avec effectifs et résultats complets affichés ; jamais exclure après avoir vu quel bras perd.
- **Incertitude :** intervalle de Wilson ou exact pour chaque proportion ; différence appariée avec intervalle rééchantillonné par seed, et test exact sur les paires discordantes si l’on teste la supériorité. Les répétitions d’une même seed ne sont pas de nouvelles seeds indépendantes.
- **Événements rares :** si le vrai taux était 1 %, la probabilité de zéro ascension en 50 runs serait `0,99^50 ≈ 60,5 %`. Zéro contre une victoire n’autorise pas à déclarer une variante supérieure. Avec zéro sur N, l’ordre de grandeur de la borne supérieure à 95 % est `3/N`, pas zéro.
- **Temps :** médiane des ascensions avec effectif, plus coût moyen pénalisé sur tous les runs : `T = temps jusqu’à ascension` si succès, sinon `T = budget mural`. Publier également total CPU et taux par heure machine. Cela évite de qualifier de rapide une variante qui ne réussit que les seeds faciles.
- **Multiplicité :** 100 idées testées produiront des gagnants par hasard. Garder un jeu de validation final intact ; pour un tournoi adaptatif, distinguer sélection exploratoire et confirmation gelée. Préannoncer tailles/points d’analyse si l’on consulte les résultats en cours de campagne.
- **Funnel :** afficher taux non conditionnels depuis Dlvl1 et taux conditionnels depuis une étape. Une politique qui n’amène que des héros très équipés à l’Astral peut améliorer le taux conditionnel en dégradant le taux total.

### Critères d’adoption et de rejet

**Adopter provisoirement** si le mécanisme attendu apparaît, les contrôles ciblés passent, le taux complet n’indique pas de régression matérielle selon la marge choisie avant l’essai, et le coût est acceptable. En manque de puissance, écrire **« candidat prometteur, effet sur winrate indéterminé »**, pas « amélioration prouvée ».

**Rejeter ou revoir** si le gain proximal déplace simplement l’échec : plus vite au Livre mais plus d’objets manquants ; plus vite aux Plans mais aucune réserve ; moins de farlooks mais plus d’attaques de pacifiques ; moins de lifesaves parce que le run reste bloqué tôt ; davantage de succès uniquement parce que le budget a doublé.

**Conserver plusieurs politiques** si les effets changent de signe selon les aides. Par exemple P022 peut devenir la référence A sans être activé en F. L’objectif n’est pas d’obtenir un seul réglage universel à tout prix.

### Dépendances et combinaisons à surveiller

| Ensemble | Prérequis | Interaction à mesurer |
| --- | --- | --- |
| P011/P012/P096 caches | Générations d’état et invalidation testées | Gain CPU contre perte d’information |
| P021/P022/P024 priorités | P006/P025 progression sémantique | Rush contre famine d’un handler critique |
| P023/P034/P039 objets clés | P013/P016/P017 acquisition et mémoire | Tuer le bon porteur ne garantit pas le pickup |
| P040 invocation | P037/P076 bougies et BUC | Préparation contre interruption |
| P044/P045/P047 portails | P010 observation et modèle par Plan | Détection contre confusion ; Eau mobile |
| P051/P053/P054/P075/P077 survie | Profil B fixé, remèdes accessibles | Réserve d’objets contre latence d’accès |
| P073/P080/P081 équipement | Modèle de capacités/charge/nutrition | Vitesse, nourriture et slots d’équipement |
| P087/P089/P099 retrait du kit | Relevé des ressources réellement acquises | Route rapide contre besoin d’XP/outils |
| P094/P100 changements de régime | État des handlers et mémoire sérialisables | Basculer de profil sans conserver une tactique inadaptée |

## Commandes disponibles et contrat des futures variantes

### Lancer les cohortes avec le CLI actuel

Exemples **à exécuter sur le worker**, dans une copie figée de `bothack_3.6/claude`, conformément à l’organisation décrite dans [HANDOFF.md](HANDOFF.md). Ces commandes sont de la documentation : aucune campagne n’a été lancée pour rédiger ce fichier. Adapter le nombre de jobs à la capacité mesurée, pas à une ancienne estimation de vCPU.

Le CLI de [series] transmet les arguments après `--` à [rungame]. `--seed-base 200000 --games 50` produit **200001…200050**. Les noms de sortie doivent être nouveaux : les lanceurs actuels ne constituent pas un gestionnaire de versions immuable.

```bash
# A : référence assistée, 50 seeds, seuils de campagne explicités.
PYTHONHASHSEED=0 python3 -m nhbot.series \
  --name exp-a-reference-01 --seed-base 200000 --games 50 --jobs 3 \
  --max-turns 300000 --max-seconds 21600 --stop-on-repeat 0 \
  -- --profile full --tactics assisted --record

# B : retrait de l’invincibilité, anti-famine et kit conservés.
PYTHONHASHSEED=0 python3 -m nhbot.series \
  --name exp-b-reference-01 --seed-base 200000 --games 50 --jobs 3 \
  --max-turns 300000 --max-seconds 21600 --stop-on-repeat 0 \
  -- --no-invincible --profile full --tactics normal --record

# C : retrait de l’anti-famine, invincibilité et kit conservés.
PYTHONHASHSEED=0 python3 -m nhbot.series \
  --name exp-c-reference-01 --seed-base 200000 --games 50 --jobs 3 \
  --max-turns 300000 --max-seconds 21600 --stop-on-repeat 0 \
  -- --no-nostarve --profile full --tactics assisted --record

# F : aucune des trois aides ; première référence sans aide.
PYTHONHASHSEED=0 python3 -m nhbot.series \
  --name exp-f-reference-01 --seed-base 200000 --games 50 --jobs 3 \
  --max-turns 300000 --max-seconds 21600 --stop-on-repeat 0 \
  -- --no-assist --profile full --tactics normal --record
```

Pour D : `--no-invincible --no-nostarve --tactics normal`, kit par défaut. Pour E : copie du fichier [kit] avec la ligne retirée, passée par `--kit config/kit-experience.txt` après création de ce fichier. `--kit none` retire tout le kit sans retirer les autres aides. Chaque comparaison de politique se fait **à l’intérieur d’une cohorte** ; comparer directement A à F mesure simultanément de nombreux changements.

`--stop-on-repeat 0` évite une sélection dépendant des premières seeds dans une campagne figée. En développement, garder un arrêt anticipé pour ne pas gaspiller du calcul sur un même bug, puis exclure cette série de la confirmation complète. `--record` a un coût CPU/disque : appliquer la même règle aux deux bras et prévoir conservation des traces utiles.

Les wrappers `tools/worker_series.sh` et `tools/worker_dev.sh` restent utiles, mais ne pas présumer qu’un `PYTHONHASHSEED` défini localement est transmis par SSH : le définir dans le processus Python **sur le worker**. Le wrapper de séries refuse de synchroniser lorsqu’une série tourne ; pour plusieurs versions simultanées, préparer des répertoires distincts.

### Ce qui est encore à développer

Il n’existe pas, dans le CLI lu, de `--variant`, `--assist-budget`, `--until-turn` ni de checkpoint bot+moteur prêt à reprendre. `BOTHACK_VARIANT=...` est une proposition d’IMPROVEMENTS, pas un interrupteur déjà fonctionnel. Ne pas lancer une campagne en pensant qu’une variable ignorée active une fiche.

Contrat suggéré pour P001, à implémenter avant usage :

```json
{
  "experiment_id": "p033-local-fetch-budget-v1",
  "variant": {
    "id": "fetch_budget_local",
    "parameters": {"search_turns": 1500, "travel_turns": 3000},
    "resolved": true
  },
  "cohort": "A",
  "reference_hash": "...",
  "candidate_hash": "...",
  "seed_set_id": "validation-01",
  "primary_metric": "ascended_within_fixed_budget",
  "primary_hypothesis": "moins d'abandons avant arrivée, puis plus d'ascensions",
  "supervisor_version": "..."
}
```

Les valeurs `search_turns`/`travel_turns` de cet exemple sont des paramètres à étudier, pas des optimums établis. Une reprise depuis checkpoint devra conserver RNG, mémoire de niveaux, closures de traque, files de touches, actions en cours et superviseur ; reprendre seulement NetHack avec un BotHack vierge est une autre expérience.

### Fiche de résultat à conserver pour chaque candidat

```text
ID / commit / hashes / paramètres :
Hypothèse et profil d’aides :
Référence / candidat / nombre de seeds prévu et exécuté :
Budgets / jobs / conditions machine :
Ascensions vérifiées, taux, intervalles, différence appariée :
Entonnoir depuis Dlvl1 et transitions conditionnelles :
Temps, tours, CPU, requêtes, coût pénalisé :
Première mort ou première aide ; ressources consommées/perdues :
Crashes, limites, blocages, signatures nouvelles :
Effet mécanique attendu observé ou non :
Régressions sentinelles et interactions :
Décision : rejeter / revoir / confirmer / adopter pour tel profil :
Seeds réservées utilisées et seeds restant intactes :
```

## Sources et limites de lecture

Les propositions sont ancrées dans les documents du dépôt, les fonctions citées et les résultats locaux listés plus haut. Les fichiers Python les plus utiles pour l’implémentation sont :

| Source | Points d’entrée |
| --- | --- |
| [mainbot] | `init`, `full_explore`, `fetch_invocation_item`, `fight`, `retreat`, `wish`, `hunt`, `feed`, `use_items`, `assisted_planes_rush`, `assisted_astral_rush` |
| [bridge] | `handle`, `_consume`, `_update_frame`, `_check_refusal`, `_veto`, `forget_target`, `recover_action_loop` |
| [pathing] | `navigate`, `base_cost`, `pass_monster`, `seek_portal`, `go_down`, `seek_level`, `explore` |
| [actions] / [behaviors] | `Look`, `PickUp`, `examine_monsters`, `make_use`, `invocation` |
| [player] / [tracker] / [game] | capacités, nourriture, `track_monsters`, `fresh_corpse`, `can_pray`, `_update_portal_range` |
| [rungame] / [series] | CLI, hashes, manifest, classification, seeds, signatures |
| [recorder] / [supervisor] | acquisition/perte, jalons, nouveauté, récupération, limites |
| [rules36] / [compat36] | règles 3.6, profils, adaptations de messages/menus |

Les constats moteur explicitement vérifiés concernent notamment `assist_lifesave`, le refus de rangement des quatre objets, les conditions d’invocation, les indices de chaleur, la restauration par corne, la détection d’or confuse/maudite et les coffres de bougies de Vlad. Les autres fiches décrivent des mécanismes à vérifier par un cas ciblé avant implémentation ; elles ne promettent pas qu’une action est légale sur tous les niveaux.

### Reproduire les comptes locaux essentiels

Ce script lit uniquement les fichiers existants. À exécuter depuis la racine `bothack_3.6/claude`. Il accepte les deux formes de lignes rencontrées dans `assist.jsonl` : objet JSON et paire `["assist", objet]`.

```python
import collections
import json
from pathlib import Path

root = Path("runs/worker")
for name in ("big-w01", "big-w02", "big-w08", "full-c01",
             "full-c02", "full-c04", "planes-c01"):
    rows = [json.loads(p.read_text())
            for p in sorted((root / name).glob("*/result.json"))]
    outcomes = collections.Counter(r.get("outcome") for r in rows)
    print(name, len(rows), dict(outcomes))

game = root / "full-c01/g011"
result = json.loads((game / "result.json").read_text())
saves = []
for line in (game / "assist.jsonl").read_text().splitlines():
    event = json.loads(line)
    if isinstance(event, list):
        event = event[1]
    if event.get("kind") == "lifesave":
        saves.append(event)
print("premier lifesave", saves[0] if saves else None)
print("lifesaves", len(saves))
print("sur les Plans", sum(e["depth"] < 0 for e in saves))
print("tueurs", collections.Counter(e.get("killer") for e in saves))
hist = result["action_hist"]
print("fraction look/farlook",
      (hist.get("look", 0) + hist.get("farlook", 0)) / result["actions"])
print("ascend/descend", hist.get("ascend", 0) + hist.get("descend", 0))
```

**Livrable de cet audit :** cette documentation et 100 fiches numérotées. Aucun changement de politique, d’aide moteur ou de configuration de run n’est compris dans ce document ; aucune augmentation de winrate n’est revendiquée avant les expériences.

[mainbot]: ../pybothack/bots/mainbot.py
[bridge]: ../pybothack/nhbridge.py
[bh36]: ../pybothack/bh36.py
[engine]: ../nhbot/engine.py
[pathing]: ../pybothack/pathing.py
[actions]: ../pybothack/actions.py
[behaviors]: ../pybothack/behaviors.py
[player]: ../pybothack/player.py
[tracker]: ../pybothack/tracker.py
[game]: ../pybothack/game.py
[tile]: ../pybothack/tile.py
[item]: ../pybothack/item.py
[itemid]: ../pybothack/itemid.py
[leveldata]: ../pybothack/_leveldata.json
[rungame]: ../nhbot/rungame.py
[series]: ../nhbot/series.py
[recorder]: ../nhbot/recorder.py
[supervisor]: ../nhbot/supervisor.py
[rules36]: ../pybothack/rules36.py
[compat36]: ../pybothack/compat36.py
[scenarios]: ../nhbot/scenarios.py
[kit]: ../config/kit-default.txt
[audit]: AUDIT_MESSAGES.md
[assist-c]: ../engine/nethack-3.6.7/src/botassist.c
[pickup-c]: ../engine/nethack-3.6.7/src/pickup.c
[apply-c]: ../engine/nethack-3.6.7/src/apply.c
[spell-c]: ../engine/nethack-3.6.7/src/spell.c
[wizard-c]: ../engine/nethack-3.6.7/src/wizard.c
[read-c]: ../engine/nethack-3.6.7/src/read.c
[timeout-c]: ../engine/nethack-3.6.7/src/timeout.c
[pray-c]: ../engine/nethack-3.6.7/src/pray.c
[potion-c]: ../engine/nethack-3.6.7/src/potion.c
[monst-c]: ../engine/nethack-3.6.7/src/monst.c
[endgame-des]: ../engine/nethack-3.6.7/dat/endgame.des
[tower-des]: ../engine/nethack-3.6.7/dat/tower.des
