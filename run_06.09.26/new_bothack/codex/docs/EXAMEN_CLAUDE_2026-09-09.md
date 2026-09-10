# Examen du travail de Claude — 9 septembre 2026

Examen en lecture seule du répertoire `../../claude/`. Aucun de ses fichiers
n'a été modifié. Les chiffres ci-dessous sont des résultats enregistrés par
l'autre agent, inspectés ici ; ses campagnes n'ont pas été relancées par Codex.

## Avancement constaté

Le portage de Claude est plus avancé que celui de Codex : sa boucle de jeu et
sa stratégie `pybothack/bots/mainbot.py` permettent déjà des parties autonomes.
Son code comporte une émulation des collections Clojure, un transport terminal,
les actions et la navigation. L'inspection ciblée des références à Java ne révèle
pas de délégation des décisions à la JVM ; ce n'est pas un audit exhaustif.

Les **15 rapports JSON présents dans `claude/artifacts/gate_v2/`** déclarent
1 182 022 octets attendus et autant d'octets de préfixe commun : six
`PASS_COMPLETE`, huit `PREFIX_ONLY`, un `PASS_CAPTURE`. Ce relevé est plus récent
que les quatorze captures décrites en tête du README. Un succès de replay signifie
que les touches correspondent à la capture ; il ne prouve ni une ascension ni
l'équivalence sur toutes les situations possibles.

Les documents annoncent 1 821 cas différentiels réussis et des parties ayant
atteint la profondeur 18. Ces deux mesures n'ont pas été reproduites ici.
Le fichier `claude/upstream/nh343/var/xlogfile` inspecté contient 99 entrées,
aucune avec une mort contenant « ascend », au plus 13 630 tours et une profondeur
maximale de 13. Ce fichier ne suffit donc pas à vérifier les meilleurs résultats
historiques annoncés ; sa portée ne doit pas être confondue avec toutes les campagnes.
**Aucune ascension n'est attestée par les éléments examinés.**

## Ce que les essais révèlent

- La référence doit être reproductible avant une comparaison des touches :
  Claude contrôle les graines, l'ordre des gestionnaires, le cache d'exploration
  et les frontières des lectures du terminal dans son banc de comparaison.
  Ces adaptations de la référence doivent accompagner toute annonce de fidélité.
- L'ordre des ensembles et dictionnaires Clojure influence les cibles et les menus.
  Les chaînes d'un caractère et les caractères n'ont pas le même hash.
- Un écran portant encore le marqueur `# #` ne doit pas déclencher immédiatement
  la décision. Le problème devient visible sous hallucination, quand les monstres
  affichés changent entre deux rafraîchissements. Le scraper Codex possède déjà
  le retour anticipé correspondant ; un test comparatif supplémentaire couvre
  maintenant plusieurs marqueurs successifs avec des glyphes différents.
- Certains comportements erronés de l'original doivent rester reproduits :
  Claude a notamment diagnostiqué des passages d'atomes à la place de valeurs
  dans `Throw` et `Discoveries`. À vérifier directement dans l'original lors
  du portage de ces gestionnaires dans Codex.
- Un délai d'expiration ajouté au lecteur peut tuer une partie qui fonctionne.
  Le watchdog doit d'abord conserver les piles d'exécution pour distinguer
  un calcul lent d'une attente de données.

## Blocages concrets observés dans les journaux

Dans `ascend_run7/game12/stdout.log`, trois captures de piles pendant une absence
d'action montrent le thread principal dans `iface.wait_readable`, appelé par
`bothack.run`. À ces instants, il attend des données ; ces piles ne montrent pas
un calcul de navigation saturant le CPU. Elles ne suffisent pas à identifier
la cause de l'attente : il faut corréler le dernier prompt et les touches envoyées.

Dans `ascend_run7/game10/run.log`, à 17:32:37, la navigation lève
`RuntimeError: stuck :-(` lors d'une tentative de sortie de Sokoban vers la quête.
Le bot termine avec 12 102 tours, 59 256 points et 130 PV selon son état interne.
Il s'agit d'un arrêt du bot, pas d'une mort attestée. Le `summary.json` de cette
campagne conserve pour cette partie un état plus ancien et incomplet : les
journaux récents doivent être consultés avant d'interpréter le résumé.

## Conséquence pour Codex

Ces traces servent à choisir des tests et à éviter de reproduire les mêmes
erreurs de portage. Le code de Claude n'est pas réétiqueté comme travail Codex.
L'objectif reste le portage fidèle dans `codex/`, relié à une vraie partie, puis
une ascension autonome vérifiable. Les 59 derniers tests d'événements et de
runtime conservés dans `artifacts/event-runtime-tests.log` sont réussis ; ils
ne remplacent pas cette validation en jeu.

Vérification effectuée après l'examen : **129 tests réussis** sur les actions,
les événements et le runtime (`artifacts/resume-tests.log`), plus le nouveau
test des rafraîchissements successifs, **réussi contre l'oracle Clojure**.
