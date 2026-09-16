# Analyse du portage de BotHack vers un autre langage

Date : 12 septembre 2026

## Réponse courte

Un portage complet vers Rust ne paraît pas être la meilleure prochaine étape pour obtenir une ascension. Le port Python peut aller profond dans le donjon, mais il finit surtout par mourir sur une décision dangereuse ou abandonner après un blocage de synchronisation. Rien dans les résultats disponibles ne montre que Python est la cause principale de l'échec.

Rust pourrait améliorer l'entrée-sortie terminal, la gestion des processus et la consommation mémoire. Il ne corrigerait pas automatiquement la stratégie, les priorités de BotHack, les menus de NetHack, les attentes sur les rafraîchissements terminal ou les séquences aléatoires. Une réécriture complète recommencerait aussi une grande partie du travail de fidélité déjà réalisé.

La meilleure option est donc de continuer à corriger et mesurer le port Python, puis d'utiliser éventuellement Rust pour un composant isolé. Un portage complet ne deviendrait intéressant qu'après avoir identifié un goulot d'étranglement mesurable que Python ne permet pas de résoudre.

## Ce que montrent les campagnes existantes

Les chiffres ne constituent pas une probabilité théorique fiable : les parties ne sont pas indépendantes et le bot change au fil des corrections. Ils donnent toutefois un ordre de grandeur utile.

| Expérience | Parties observées | Ascensions | Résultat le plus profond connu |
| --- | ---: | ---: | --- |
| Port Python actuel, xlogfile partagé | 169 | 0 | Dlvl:29 atteint à plusieurs reprises |
| Campagnes Claude documentées | environ 167 | 0 | une partie signalée jusqu'à Dlvl:39 dans pool_f/game2 |

Dans le workspace actuel, upstream/nh343/var/xlogfile contient 169 résultats de parties et aucune ligne death=ascended. Les journaux Python montrent deux progressions jusqu'à Dlvl:29, puis un abandon ou une mort. C'est plus loin que plusieurs campagnes précédentes, mais ce n'est pas encore une preuve de maîtrise de Gehennom et de la fin du jeu.

Les documents de Claude donnent deux profondeurs maximales selon la campagne ou la version du rapport : le README parle de Dlvl:28, tandis que le rapport détaillé mentionne une partie pool_f/game2 jusqu'à Dlvl:39. Cette différence doit être conservée comme une différence de mesure, pas comme une ascension. Dans tous les cas, Claude rapporte zéro ascension.

Avec zéro succès en 169 essais, la règle empirique des trois donne une borne supérieure d'environ 1,8 % pour le taux de réussite à 95 % dans cette campagne. Ce n'est pas le vrai taux de BotHack : les parties sont corrélées, certains essais sont interrompus et le code évolue. C'est seulement un signal indiquant que le taux mesuré est actuellement inférieur à 1 sur 169. Les résultats de Claude présentent le même signal.

La fidélité fonctionnelle du port est déjà élevée. Les contrôles différentiels réalisés dans ce workspace ont donné 1829/1829 cas concordants, et les contrôles de hachage Clojure ont également réussi. Les résultats de Claude documentent en plus une longue comparaison octet par octet des entrées et sorties. Le problème apparaît donc surtout pendant l'exécution prolongée d'une partie réelle.

Voir [les résultats du port](RESULTS.md), [les limites connues](LIMITATIONS.md), [l'architecture](PORT.md), et les rapports de Claude dans [RESULTS de Claude](../claude/docs/RESULTS.md) et [LIMITATIONS de Claude](../claude/docs/LIMITATIONS.md).

## Pourquoi le portage bloque

### Synchronisation avec NetHack

BotHack ne reçoit pas un état structuré. Il le reconstruit à partir d'une interface terminal : caractères affichés, curseur, messages, menus, fenêtres et rafraîchissements partiels. Une action peut produire plusieurs cadres d'écran, ou un cadre qui ressemble à l'ancien état.

Un mauvais découpage de cadre peut faire attendre le bot sur une information qui n'arrivera plus. Le bot est alors vivant, mais ne choisit plus d'action. Claude a corrigé plusieurs cas liés à l'inactivité, à unpause, aux séquences d'ESC et aux attentes bornées. Les parties profondes montrent qu'il reste des cas de blocage.

Le port actuel a aussi dû corriger les menus avec plusieurs objets sur une même case, les messages de localisation et des boucles de récupération. Une divergence d'écran peut rendre toutes les actions suivantes incorrectes.

### Sémantique de l'implémentation originale

Le projet d'origine n'est pas simplement une application Java. Il combine le bot Clojure, une infrastructure Java/JVM et des bibliothèques dont les comportements sont visibles par le bot. Le port doit reproduire les structures immuables, les valeurs nil, l'ordre d'itération des maps et sets, le hachage HAMT et celui des records Clojure, l'ordre différé des agents et futures, les tirages aléatoires, la logique de recherche d'objets et les frontières exactes des cadres terminal.

Une autre implémentation peut modifier l'ordre des priorités, les égalités, les tirages aléatoires ou le moment où une action est envoyée. Ces différences peuvent rester invisibles dans les tests courts et apparaître seulement après plusieurs heures de jeu.

### Décisions stratégiques dangereuses

Une ascension demande une séquence très longue : équipement initial, Excalibur, Sokoban, Mines, quête, château, Medusa, Vlad, invocation, Amulette et plan astral. Une seule erreur peut annuler une partie qui progressait bien.

Les journaux actuels montrent notamment les risques suivants :

- Medusa peut tuer le bot si le traitement de l'aveuglement et du bandeau n'est pas conservé assez longtemps ;
- une baguette de wishing vide peut provoquer une répétition sans progrès ;
- la recherche d'un objet volé, notamment Excalibur, peut maintenir le bot dans une boucle ;
- une paralysie sur un piège face à un monstre dangereux laisse peu de marge ;
- le farming et les seuils de score peuvent attendre un événement qui ne se produira plus ;
- la route complète de fin de partie n'est pas validée par une ascension réelle.

Ces problèmes relèvent principalement des règles de décision et de récupération. Rust ne change pas ces règles.

### Abandon avant la mort

Le rapport de Claude identifie le principal symptôme : le bot n'est pas toujours tué, il abandonne. Dans une série de 76 parties terminées, Claude classe environ 32 % des fins comme abandon, boucle d'inactivité ou blocage, et non comme mort directe. Des parties profondes ont cessé d'agir alors que le personnage avait encore beaucoup de points de vie et un équipement viable.

C'est un argument pour améliorer l'observabilité et la récupération avant de changer de langage.

## Comparaison des langages

| Option | Atout principal | Difficulté du port | Chance d'améliorer l'ascension maintenant |
| --- | --- | --- | --- |
| Python | Port avancé, instrumentation et corrections rapides | Performance et concurrence à surveiller | Meilleure à court terme |
| Rust | E/S robuste, mémoire contrôlée, état explicite, déploiement simple | Très élevée : terminal, sémantique Clojure, concurrence et stratégie | Faible gain immédiat |
| Go | Processus, concurrence et déploiement simples | Modèle fonctionnel et structures dynamiques à reconstruire | Gain opérationnel possible, gameplay incertain |
| Kotlin/Java | Proximité de l'écosystème JVM et du code original | Le bot Clojure et ses sémantiques doivent quand même être reproduits | Réutilisation plus facile, fiabilité non garantie |
| Clojure | Fidélité maximale au comportement original | Coût d'apprentissage et outillage | Meilleur oracle de référence |

Rust est le meilleur candidat pour un moteur robuste à long terme. Il n'est pas le meilleur candidat pour la prochaine ascension. Kotlin ou Java réduiraient la distance avec la JVM sans supprimer les difficultés de stratégie et de synchronisation. Python reste le choix le plus rentable tant que le temps d'action du bot n'est pas le facteur limitant.

## Difficultés spécifiques d'un port vers Rust

Il faudrait définir un modèle Rust stable pour :

1. les états immuables et les mises à jour atomiques ;
2. les files d'événements et l'ordre exact des actions différées ;
3. les menus et écrans partiels du terminal ;
4. les objets identifiés ou non identifiés et les valeurs absentes ;
5. l'itération déterministe des collections ;
6. les priorités et les égalités de sélection ;
7. la reproductibilité des tirages aléatoires ;
8. les délais, interruptions, reprises et watchdogs ;
9. le rejeu d'une partie à partir d'une trace d'octets ;
10. la stratégie complète des niveaux et du plan astral.

Le système de types de Rust aiderait à rendre certains états invalides plus difficiles à produire. En contrepartie, la traduction des structures dynamiques et des mutations différées de Clojure serait coûteuse. Le gain de vitesse ne résoudrait pas un bot qui prend la mauvaise décision ou attend le mauvais rafraîchissement.

## Recommandation

1. Classifier chaque fin : mort NetHack, abandon d'inactivité, répétition d'état, crash, attente de menu ou progression normale.
2. Enregistrer autour de chaque blocage l'écran brut, l'état parsé, la dernière décision, le compteur de progrès et la raison du watchdog.
3. Ajouter des limites de tentatives et une sortie sûre pour la baguette vide, l'objet volé, le piège paralysant, le monstre invulnérable, le farming sans gain et les menus non résolus.
4. Rejouer les traces des parties Python et Claude qui ont dépassé Dlvl:20 pour séparer erreur stratégique et défaut du scraper.
5. Stabiliser le comportement profond et réduire fortement les abandons inexpliqués avant tout changement de runtime.
6. Si Rust est testé, commencer par un composant isolé : lecteur PTY, parseur terminal ou outil de rejeu. Il devra produire les mêmes octets et les mêmes décisions que Python sur les traces de référence.
7. Ne porter toute la stratégie qu'après avoir mesuré un problème que ce composant résout réellement.

Le critère pertinent n'est pas seulement la vitesse de Rust, mais la classe de fins qu'il éliminerait avec une mesure reproductible. En l'état actuel, les abandons et les décisions dangereuses sont déjà visibles en Python. Continuer le port Python puis porter les composants mesurés donne donc une meilleure chance d'ascension qu'une réécriture complète immédiate.

