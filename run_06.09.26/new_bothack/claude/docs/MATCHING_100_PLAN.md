# Atteindre l’identité comportementale avec BotHack

Document de décision et protocole d’exécution — 8 septembre 2026.

La mission de [HANDOFF.md](HANDOFF.md) est de reproduire les frappes de
BotHack, octet pour octet, avec un port autonome en Python. La voie proposée
est de fiabiliser le verdict, comparer les transitions internes au premier
écart, corriger les causes mesurées, puis élargir la validation. Un budget
d’environ **5 USD sur Vast.ai** peut financer une campagne supplémentaire de
calcul ; il ne remplace pas ces corrections et ne garantit pas l’absence de
bugs sur toutes les parties possibles.

Ce document est le livrable demandé. Les constats ci-dessous proviennent de
l’inspection du code et d’une nouvelle comparaison des fichiers déjà présents.
Aucun bot n’a été modifié, aucune nouvelle partie n’a été lancée et aucune
instance payante n’a été louée pendant cet audit. Les expériences et extensions
d’outillage proposées restent à réaliser.

## 1. Ce que les preuves locales établissent

Le checkout original cité dans les journaux existe et son commit a été vérifié :
`70226b3c8ed12d29c64068aec0acc0ca71d57adf`. La référence conserve Clojure 1.6.0
et `data.priority-map` 0.0.7. Les résultats s’appliquent au mainbot et à NetHack
3.4.3-NAO décrits dans HANDOFF, avec les paramètres du harnais de comparaison.

La relecture binaire des neuf `tap.log` a vérifié les types d’enregistrements,
leurs longueurs et l’absence d’octets résiduels. Les neuf captures sont
structurellement lisibles. La comparaison de leurs enregistrements `I` avec
les `port_keys.bin` existants retrouve exactement les offsets des rapports :

| Seed | Actions originales | Premier octet différent, index 0 | Frappes originales | Premier écart original → Python | Fin naturelle dans le journal |
| --- | ---: | ---: | ---: | --- | --- |
| 40001 | 6 400 | 14 132 | 113 186 | search → sud | `You die...` |
| 40002 | 3 894 | 6 528 | 72 470 | ouest → nord, après Pay | `You die...` |
| 40003 | 1 515 | 7 770 | 22 729 | sud-est → est, après Pay | `You die...` |
| 40004 | 8 559 | 30 170 | 149 556 | look → throw | Non établie |
| 40005 | 7 985 | 5 615 | 152 351 | nord-est → est, après Pay | Non établie |
| 40006 | 7 488 | 11 920 | 128 407 | nord → search | Non établie |
| 40007 | 2 622 | 15 310 | 44 757 | look → ouest | Non établie ; erreur PTY |
| 40008 | 1 381 | 19 685 | 21 174 | look → sud-ouest | `You die...` |
| 40009 | 2 376 | 39 027 | 41 794 | est → search | `You die...` |

Sources : [résumé existant](../artifacts/fidelity/summary.txt), `tap.log`,
`port_keys.bin` et `bothack.log` de chaque sous-dossier de
[fidelity](../artifacts/fidelity). Les commandes ont été reclassifiées avec
[classify_divergence.py](../tools/classify_divergence.py). Ses numéros de
commandes issus de la synchronisation ne sont pas les numéros d’actions du bot.

**Le résultat démontré reste 0/9 captures intégralement identiques.** Les
fichiers de 40008 et 40009 ont même exactement la même longueur des deux côtés,
mais contiennent des octets différents : comparer les longueurs ne suffit pas.

Une correction à HANDOFF est nécessaire dans la lecture de ses résultats :
les « neuf parties complètes » ne sont pas toutes attestées comme telles.
40004–40006 s’arrêtent vers 23:12:16 en pleine activité ; 40005 affiche encore
118/118 HP au tour 9 175. Le journal de 40007 finit avec 82/83 HP puis
`Terminal: reader broke out of loop, ending`, et son stdout contient
`HandlerPTY.read: Input/output error`. L’arrêt simultané des trois premières
évoque une limite de campagne, sans en démontrer la cause. Pour ces quatre
captures, retenir « fin non attestée », pas « mort naturelle ».

Les cinq autres présentent un message de mort ; le `xlogfile` contient des
entrées concordantes par nom et horaire. Il reste à formaliser cette association
dans un manifeste et à vérifier la séquence terminale complète. Le nom seul
ne suffit pas : `bot1`, `bot2` et `bot3` ont été réutilisés.

Enfin, **1821/1821** est le résultat historique annoncé par HANDOFF, pas un
nouveau résultat de cet audit. RESULTS et TESTS affichent aussi des totaux
antérieurs, 1779 et 1799. Une prochaine exécution devra publier le total réel
et la version testée, plutôt que fusionner ces chiffres.

## 2. Définir précisément le « 100 % »

Trois propriétés doivent être rapportées séparément :

1. **Capture identique** : tous les octets attendus ont été produits, sans
   ajout, suppression ou substitution, dans l’interaction enregistrée.
2. **Partie complète identique** : même propriété jusqu’à une fin naturelle
   attestée, réponses aux écrans de fin comprises ; un timeout ne satisfait
   jamais ce critère.
3. **Campagne sans divergence** : N parties complètes identiques sur un corpus
   explicitement défini, avec les échecs techniques et parties inachevées
   publiés séparément.

La référence actuelle est déjà un **BotHack sous harnais déterministe** :
priorités égales ordonnées par enregistrement, LCG partagé et RNG NetHack fixé.
Il faut publier ces adaptations. Une identité avec cette référence ne signifie
pas une identité avec toute exécution non instrumentée de BotHack, dont l’ordre
des handlers varie entre JVM et dont le cache utilise un `future`.

Une campagne finie ne prouve pas l’équivalence universelle. Si N graines
indépendantes, tirées selon une distribution annoncée, donnent zéro divergence
sur des parties complètes, la borne supérieure unilatérale exacte à 95 % du
taux d’échec par partie est `1 - 0,05^(1/N)` : environ 2,95 % pour N=100,
0,994 % pour N=300 et 0,299 % pour N=1000. Ce calcul ne s’applique pas tel quel
à des graines sélectionnées après débogage, à des timeouts écartés du corpus,
ou à des répétitions de la même partie. Dire « 100/100 sur le corpus gelé »
est exact ; dire « garanti pour toute partie » ne l’est pas.

## 3. Fiabiliser le verdict avant de multiplier les essais

L’inspection révèle plusieurs différences entre l’intention des outils et ce
qu’ils vérifient réellement.

| Outil | Comportement constaté | Changement requis pour certifier |
| --- | --- | --- |
| [compare_taps.py](../tools/compare_taps.py) | Retourne 0 et affiche `IDENTICAL over the common prefix` si les longueurs diffèrent sans écart dans le préfixe | Statut distinct `PREFIX_ONLY`, jamais réussite d’une partie complète |
| [replay_compare.py](../tools/replay_compare.py) | Vérifie les octets et les longueurs finales, mais ne fournit à `ReplayInterface` que les enregistrements `O` | Ajouter une validation de l’alternance causale I/O ; conserver ce replay rapide comme outil de diagnostic |
| [replay_server.py](../tools/replay_server.py) | Attend un nombre d’octets aux étapes `I`, sans vérifier leur contenu ; continue après timeout | Comparer les octets attendus au fil de l’eau et arrêter au premier écart ou défaut de synchronisation |
| Lecteurs de tap | Plusieurs s’arrêtent silencieusement devant un dernier enregistrement tronqué | Refuser type invalide, charge tronquée et octets résiduels |
| [replay_port.sh](../tools/replay_port.sh) | Masque le code retour avec `|| true`, puis lit `report.txt` | Conserver le statut, produire un résultat propre par exécution, empêcher la lecture d’un ancien rapport |
| [fidelity_batch.sh](../tools/fidelity_batch.sh) | Réutilise un tap non vide, choisit `40000+i`, compte les lignes `IDENTICAL` sans preuve de terminaison | Manifeste de validité, liste explicite de graines et agrégation de statuts structurés |
| [record_orig.sh](../tools/record_orig.sh) | Limite murale et nettoyage du processus, sans verdict explicite de fin de partie | Enregistrer terminaison, timeout, erreur, codes de sortie et correspondance avec le xlog |

Le replay rapide reste précieux : son premier écart est un point de départ
de diagnostic. Mais il n’impose pas la causalité revendiquée pour l’autre
serveur de replay. Une égalité du flux concaténé ne démontre pas à elle seule
que chaque réponse a été envoyée au bon moment.

Le validateur strict proposé maintient un curseur dans les octets `I` attendus.
Il autorise leur fragmentation en plusieurs écritures, mais n’avance au prochain
groupe de sortie qu’après réception des octets requis. Une écriture anticipée
doit être vérifiée selon l’interaction enregistrée, sans déplacer arbitrairement
des commandes d’un côté à l’autre d’une réponse du jeu. Il conserve les trames
`O` et s’arrête au premier octet incorrect. Le découpage des appels système
`write()` n’est pas en soi une propriété à rendre identique.

Produire au minimum les statuts `PASS_COMPLETE`, `PASS_CAPTURE`, `PREFIX_ONLY`,
`DIVERGENCE`, `TIMEOUT`, `INVALID_TRACE`, `HARNESS_ERROR`. Une exception ou un
replay incomplet ne peut donner `PASS_COMPLETE`, même si tous les octets
produits jusque-là coïncident. Pour une fin valide, définir explicitement les
éventuelles trames de fermeture sans décision à traiter.

Tests du validateur : flux égaux, substitution d’un octet, octet supplémentaire,
préfixe strict, tap tronqué, mauvaise causalité, timeout et ancien rapport
présent. Ces tests empêchent de financer une campagne qui compterait des faux
succès. Le classificateur de commandes aide à lire les écarts ; il retire du
bruit de synchronisation et ne doit pas servir de verdict d’égalité brute.

## 4. Méthode de résolution : comparer les transitions, puis réduire l’écart

### 4.1 Vérifier d’abord la stabilité de la référence

Sur 40005, réaliser trois exécutions de l’original sous les mêmes paramètres,
puis des replays original→original. Comparer les frappes, les trames et les
préfixes valides ; augmenter les répétitions si elles se contredisent. Répéter
ensuite sur une graine de chacune des deux autres classes. Tester également
la reproductibilité Python→Python avec plusieurs `PYTHONHASHSEED`.

Si l’original diffère de lui-même, attribuer l’écart au port serait prématuré.
Localiser le premier événement instable : trame, handler, cache ou attribution
d’un tirage. Si l’original est stable dans ces essais, cela renforce la
comparaison sans prouver qu’il le sera sur toutes les graines.

### 4.2 Traiter 40005 sans refaire les diagnostics déjà tranchés

HANDOFF a écarté, sur le cas tracé, un désaccord des valeurs RNG, des voisins
dans `arbitrary-move`, du compteur `blocked` et du retour observé de `fidget`.
Ces mesures restent acquises pour ce cas. Elles ne suffisent pas à attribuer
le même mécanisme à 40002, 40003 ou au cas du piège d’un ancien enregistrement.

Le code confirme la différence d’évaluation : `reset-exploration` crée un
`future` dans l’original ; [reset_exploration](../pybothack/pathing.py) calcule
`_curlvl_exploration(game)` immédiatement. Mais cela **ne démontre pas** que
l’ordonnancement cause le déplacement NE/E. La chaîne de raisons est un indice,
pas une preuve de provenance suffisante.

Étendre l’instrumentation opt-in de
[dbg_inv.clj](../tools/cljcmp/dbg_inv.clj), sans modifier le checkout original,
et ajouter l’observation équivalente côté Python. Autour du premier écart,
journaliser :

- numéro d’action, tour, branche, niveau, position et génération du cache ;
- état capturé à sa création, début/fin du calcul, lectures et annulation ;
- identifiant du calcul de navigation, ordre des nœuds développés, coûts,
  égalités de priorité, prédécesseurs et chemin finalement retenu ;
- candidat d’action créé à chaque arête et celui retenu par `path-step` ;
- pour chaque tirage : index, état avant/après, type, argument, appelant,
  thread et candidat consommateur ;
- champs décisionnels de l’action retournée, cache lu, raisons et octets émis.

Le tracer RNG actuel de [runner.clj](../tools/cljcmp/runner.clj) met à jour
le LCG, puis journalise avec un autre compteur. En présence de concurrence,
l’ordre d’écriture des lignes n’est donc pas une preuve suffisante de l’ordre
atomique des tirages. Associer l’index à la transition RNG elle-même, et
signaler que l’instrumentation peut modifier l’ordonnancement. Préférer des
événements tamponnés et une fenêtre de trace réduite ; comparer aussi avec
les traces détaillées désactivées.

L’expérience doit distinguer trois issues :

| Premier écart interne | Conséquence |
| --- | --- |
| État capturé différent | Remonter vers les mises à jour du jeu, l’ordre des handlers ou les trames |
| Même état et mêmes tirages attribués, chemin différent | Examiner ordre des collections, tie-break, évaluation et réutilisation du candidat d’action |
| Attribution des tirages ou durée de vie du cache différente | Étudier explicitement le contrat d’ordonnancement et d’annulation |

Ne pas ajouter simplement un thread Python : son ordonnanceur et son modèle
d’annulation ne reproduisent pas automatiquement le `future` Clojure. Ne pas
séparer le RNG du cache du RNG principal sans mesure : cela change le
comportement de référence.

Si une politique d’exécution déterministe du cache devient nécessaire,
l’expérimenter dans un **mode distinct du harnais**, documenté. Comparer
original actuel, original avec politique fixée et Python. Une référence
sérialisée qui diffère des anciennes captures définit un nouveau contrat ;
elle ne résout pas rétroactivement leurs divergences. Conserver ces captures
et leurs verdicts dans le rapport.

### 4.3 Remonter à la première différence d’état

Pour `search`/déplacement, suivre les compteurs `searched`, la connaissance
des cases, les objectifs d’exploration, le cache, les ensembles de candidats
et les tie-breaks. Pour `look`/action, suivre les mises à jour après lancer et
inventaire : `new-items`, contenu de la case, marquage de visite, état du scraper,
handlers enregistrés et file d’événements. Ce sont des points à observer,
pas des causes déjà établies.

Comparer après chaque événement significatif : trame traitée, mise à jour
d’état, `about-to-choose`, sélection, émission des touches. Chercher la première
différence de champ, éventuellement bien avant la première frappe différente.
Une empreinte stable permet le repérage ; un diff structuré explique l’écart.

La représentation de diagnostic doit distinguer `nil`, `false`, zéro, map vide,
Character et String ; conserver l’ordre des maps/sets et leur mode de
construction si cela influence l’itération. Trier toutes les clés ferait
disparaître précisément les bugs rencontrés dans ce projet. Exclure les
adresses mémoire et horodatages sans rôle décisionnel ; représenter closures,
handlers et futures par leur rôle et leur cycle de vie.

Un simple export JSON de `game` n’est pas forcément un checkpoint exécutable :
des états résident dans les closures, files, handlers, RNG et terminal. Pour
commencer, rejouer le préfixe exact reste plus sûr que reconstruire un faux
état équivalent. Un checkpoint restaurable vient ensuite, avec un test
reprise→suite identique.

### 4.4 Transformer chaque cause en régression fidèle

Pour chaque bug : conserver la capture, isoler la première transition fautive,
réduire le scénario en préservant son historique pertinent, puis créer un test
différentiel qui emprunte le vrai chemin de construction. L’inventaire doit
être construit par ses mises à jour réelles quand c’est le sujet du test,
pas initialisé artificiellement avec un `into` des deux côtés.

Après correction : cas réduit, suite différentielle, neuf replays, puis
validation live du cas. Reprendre au nouvel écart si la capture ne passe pas
entièrement. Les divergences situées après le premier écart d’un ancien replay
ne constituent pas neuf nouveaux bugs indépendants.

## 5. Ce que serait la « grosse méthode »

L’extension la plus utile est un banc différentiel par transitions : génération
de suites d’événements valides, exécution dans l’original et le port,
comparaison de l’état et des octets, puis réduction automatique du premier
contre-exemple. Il complète les parties réelles et leurs replays.

Cibler d’abord les frontières connues : maps de 8/9/10 éléments, promotions et
suppressions, égalités de coûts, piles de nourriture équivalentes, objets mal
identifiés, monstres pacifiques, portes et pièges qui consomment du RNG,
lancers suivis d’inventaire, changements de niveau et cycle du cache.
Construire les états depuis des préfixes réels ou des événements valides ; un
million d’états impossibles serait moins informatif que cent cas fidèles.

La campagne doit ensuite inclure des parties nouvelles et longues pour les
zones peu couvertes : Sokoban, quête, branches tardives et fin de partie.
Les neuf graines actuelles ne certifient pas ces comportements. Une ascension
peut fournir une trace intéressante, mais n’est ni nécessaire à l’identité
d’une partie donnée ni une preuve suffisante de fidélité globale.

Une preuve formelle ou une traduction systématique avec sémantique Clojure
explicite serait une autre voie, beaucoup plus vaste : collections persistantes,
évaluation paresseuse, événements, exceptions, concurrence et terminal entrent
dans le périmètre. Ce n’est pas un objectif réaliste pour une simple campagne
à 5 USD. Entraîner un modèle pour imiter les décisions n’apporte pas non plus
une garantie d’identité exacte. Le calcul supplémentaire doit d’abord chercher
et réduire des contre-exemples au port existant.

## 6. Campagne Vast.ai avec environ 5 USD

### 6.1 Ressource et offre à sélectionner

Le pipeline inspecté exécute Python, une JVM, NetHack et des traitements de
traces, sans calcul CUDA. **Privilégier CPU, RAM et disque** ; une grosse carte
graphique n’accélère pas directement ces programmes. Une offre avec GPU peut
néanmoins être intéressante pour les ressources CPU associées. Vast décrit
ses instances comme des conteneurs dotés de GPU et de ressources CPU/RAM
associées : [présentation des instances](https://docs.vast.ai/guides/instances/overview).

Objectif de sélection, pas promesse de disponibilité : Linux x86_64, 8 à 16
vCPU effectivement alloués, 16 à 32 Gio de RAM et disque dimensionné après
mesure des journaux. L’API distingue `cpu_cores` de `cpu_cores_effective` ;
contrôler aussi `cpu_ram`, les unités et le détail de l’offre plutôt que
supposer disposer de toute la machine :
[champs de recherche officiels](https://docs.vast.ai/api-reference/search/search-offers).

Commencer avec 2 workers, mesurer RSS total, CPU et temps par partie, puis
essayer 4. Prévoir initialement 2 Gio par worker original comme marge de
planification, à confirmer : `-Xmx768m` borne le tas de la JVM du bot, pas le
RSS total ni la JVM Leiningen, les bibliothèques natives et NetHack. Le replay
Python est historiquement annoncé autour de 46 Mo ; remesurer sa consommation
avec la nouvelle instrumentation. Les neuf dossiers actuels occupent 724 Mio.

Vérifier au démarrage la disponibilité de JDK 8, Leiningen et de ses dépendances,
Python, les bibliothèques natives JTA/ncurses, `LD_PRELOAD`, les PTY et l’accès
à `/proc/<pid>/syscall`. Le tap suppose que le numéro d’appel système 0 est
`read` sur x86_64. Un conteneur qui empêche cette observation active le repli
temporel et doit repasser les contrôles original→original avant toute campagne.

Les chemins du binaire NetHack sont compilés en dur par le script de build.
Préparer un environnement au chemin stable, ou reconstruire dans une copie
isolée et refaire les contrôles croisés ; ne pas traiter un binaire recompilé
comme identique sans vérification. Le build actuel supprime et recrée ses
répertoires `upstream/nh343*` : le réserver à l’environnement de campagne neuf.

### 6.2 Budget calculable

Les prix Vast sont ceux d’un marché et changent selon l’offre. Calcul,
stockage et trafic constituent des postes distincts ; le stockage reste
facturé lorsque l’instance est arrêtée. Les tarifs ci-dessous sont donc des
**scénarios de calcul**, pas des offres observées :
[tarification officielle](https://docs.vast.ai/guides/instances/pricing).

Réserver 1 USD aux transferts, au stockage, à la récupération et aux imprévus ;
affecter au maximum 4 USD au calcul. Si le devis des autres postes dépasse
1 USD, réduire le calcul en conséquence. Le budget couvre toute la location,
y compris installation, essais ratés et export.

| Prix de calcul supposé par heure d’instance | Durée achetable avec 4 USD | Capacité théorique à 4 workers, plafond de 40 min par tâche |
| ---: | ---: | ---: |
| 0,20 USD | 20 h | 120 tâches |
| 0,40 USD | 10 h | 60 tâches |
| 0,80 USD | 5 h | 30 tâches |

Ces capacités supposent que les quatre workers tiennent en ressources et
utilisent tout le temps ; elles excluent installation, replays, validation
live et transferts. Ce ne sont pas des nombres de parties terminées. Le
script actuel peut attendre toute la limite même après une mort à cause de
`:no-exit true` : corriger la détection de fin améliore directement le rendement.

Formules de planification :

`heures disponibles = (5 - frais hors calcul - marge) / prix horaire`

`tâches ≈ workers × heures réellement consacrées aux tâches / durée moyenne`

Choisir l’offre après un petit essai en **parties complètes validées par dollar**,
et non en nombre de GPU ou en TFLOPS. Une offre à la demande simplifie une
première campagne courte ; une offre interruptible nécessite de supporter
les interruptions et d’exporter les résultats progressivement.

### 6.3 Déroulement et conditions de passage

1. **Avant location, localement** : validateur strict, manifeste, reproductibilité
   de la référence, traitement du premier cas 40005. Le calcul cloud peut aussi
   servir ponctuellement à l’instrumentation si la RAM locale bloque ; ne pas
   lancer un grand corpus pour retrouver en masse un écart déjà connu.
2. **Préparer le paquet** : sources et dépendances figées, compilation vérifiée,
   petit corpus représentatif, lanceur isolé et arrêt propre. Garder les traces
   originales immuables, sortir les replays dans des dossiers nouveaux.
3. **Pilote payant plafonné** : au plus 0,50 USD de l’enveloppe calcul de 4 USD,
   installation comprise. Tester 2 puis 4 workers, le framing et une paire
   original→original. Si instabilité ou débit insuffisant, exporter et arrêter
   cette tentative avant d’engager le reste.
4. **Régression** : rejouer les neuf captures ; ne déclarer les quatre sans fin
   attestée que `PASS_CAPTURE` si elles deviennent identiques. Refaire des
   enregistrements jusqu’à terminaison pour les certifier comme parties.
5. **Exploration de nouvelles graines** : liste explicite, tirée une fois et
   archivée, hors 40001–40009, avec seed du bot enregistrée. Enregistrer
   l’original une fois et réutiliser la capture après chaque correction.
   Conserver les timeouts et échecs dans le manifeste.
6. **Validation finale** : réserver dès le devis du temps aux deux bots live
   et à un corpus neuf gelé après la dernière correction. Ne pas consommer
   tout le budget en enregistrements sans vérifier le port. Si une nouvelle
   correction est faite sur ce corpus, il devient corpus de régression.
7. **Clôture** : récupérer et contrôler les empreintes des résultats, puis
   détruire l’instance de campagne et tout stockage payant temporaire après
   vérification de la copie. Confirmer leur disparition et le coût facturé.

Ne pas considérer le solde comme un coupe-circuit suffisant : vérifier les
réglages de recharge et piloter la limite depuis un contrôleur extérieur au
worker. Prévoir un arrêt anticipé qui conserve la marge d’export et de
facturation. Arrêter seulement le processus du bot n’arrête pas la location.
L’arrêt simple d’une instance laisse du stockage facturé, selon la
[documentation de tarification](https://docs.vast.ai/guides/instances/pricing).

### 6.4 Isolation requise pour les workers

Les scripts actuels ne doivent pas être lancés en parallèle sans adaptation :
`live_compare.sh` tue tous les processus nommés `nethack.343-nao` visibles.
`record_orig.sh` nettoie les fichiers contenant le nom du joueur ; les noms
de slots ne sont uniques qu’à l’intérieur d’un batch. Des batches simultanés
peuvent donc se détruire mutuellement.

Préférer un espace de processus et un répertoire de jeu par worker, avec
arrêt par groupe de processus/cgroup propre à sa tâche. À défaut, un seul
batch et des noms globalement uniques, avec nettoyage limité aux ressources
possédées par ce worker. Pour une paire live, conserver le même nom des deux
côtés : il apparaît dans les écrans. Archiver également la configuration
initiale des fichiers partagés tels que bones ; le RNG seul ne fixe pas tout
l’environnement du jeu.

`fidelity_batch.sh OUT N PAR SECS` ne tire pas de graines aléatoires : il faut
l’étendre pour accepter le manifeste, ou utiliser un nouveau lanceur. Ses
résultats actuels ne constituent pas le rapport final de certification.

## 7. Livrables techniques et ordre de réalisation

| Étape | Livrable | Critère de sortie |
| --- | --- | --- |
| A | Comparateur causal strict et manifeste | Cas négatifs du validateur correctement rejetés |
| B | Rapport original→original et Python→Python | Répétabilité observée dans les conditions déclarées |
| C | Trace et cas réduit de 40005 | Première cause interne mesurée, correction et non-régression |
| D | Diagnostic des autres premiers écarts | 9/9 captures identiques, avec statut de fin explicite |
| E | Pilote Vast et débit mesuré | Coût, ressources, framing et isolation validés |
| F | Corpus supplémentaire et parties live | N/N parties complètes identiques sur le corpus final, ou liste précise des écarts restants |

Le manifeste doit contenir : identifiant de campagne/run, hashes des sources,
version du harnais et de sa politique de cache, hash du binaire et du shim RNG,
versions JDK/Python/dépendances, paramètres PTY, configuration et état initial
du jeu, deux seeds, nom de joueur, limites, temps/RSS, statut terminal,
correspondance xlog, hashes des traces, longueurs des frappes, premier écart,
statut de comparaison et coût attribuable. Un nouveau commit du port invalide
le verdict précédent pour ce commit jusqu’au replay ; il n’invalide pas
automatiquement la capture originale.

Commandes de diagnostic déjà disponibles, depuis la racine `claude/` :

```bash
# Lecture seule : classer l'écart présent dans les artefacts existants.
python3 tools/classify_divergence.py \
  artifacts/fidelity/seed40005/tap.log \
  artifacts/fidelity/seed40005/port_keys.bin

# Nouveau replay de diagnostic, sorties séparées des preuves historiques.
# Créer d'abord un répertoire neuf artifacts/matching_audit_run1.
REPLAY_DIFFLIB_LIMIT=0 python3 tools/replay_compare.py \
  artifacts/fidelity/seed40005/tap.log \
  --seed 12345 \
  --keys-out artifacts/matching_audit_run1/seed40005.keys \
  --actions-out artifacts/matching_audit_run1/seed40005.actions \
  --report artifacts/matching_audit_run1/seed40005.report
```

Le deuxième exemple utilise encore le replay rapide existant et n’est donc
pas une commande de certification causale. Les extensions des étapes A–F ne
sont pas présentées comme déjà implémentées.

Le prochain travail utile est l’étape A, suivie de l’attribution du candidat
de navigation et du cache sur 40005. Le budget Vast.ai devient alors un moyen
de tester plus de transitions et de parties, avec un verdict dont le « 100 % »
désigne exactement le corpus et les conditions effectivement vérifiés.
