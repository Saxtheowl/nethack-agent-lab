# Handoff 2026-09-13

`codex_3` contient une implémentation neuve Python, indépendante de
`pybothack`. La tranche actuelle lance NetHack via PTY, émule ANSI par flux,
répond aux prompts de démarrage/menu/direction, explore avec une politique
déterministe et récupère après cinq secondes sans I/O. Chaque run possède son
répertoire, son terminal brut, ses décisions et son manifeste. Le moteur a été
exécuté contre le binaire cible sur plusieurs runs réels ; il atteint le niveau
1 et environ 2 500 tours dans les meilleurs essais de cette itération.

## État de preuve

Aucune ascension n'est revendiquée. `victory_message_observed` est seulement
un signal de terminal ; le manifeste devra être enrichi avec une vérification
xlogfile isolée avant de classer une ascension. Le prototype n'implémente pas
encore la stratégie de quête, Château, Gehennom, Amulette et Plan Astral.

## Diagnostic courant

Les premières causes corrigées sont le prompt de partie abandonnée, les
options NetHack refusées, les pagers `--More--`, les messages effacés des
redraws, la faim et l'attaque accidentelle des familiers. L'émulateur terminal
a ensuite été remplacé par `pyte` pour gérer l'écran ANSI incrémental et les
écrans alternatifs ; les 17 tests restent verts. Le bot inspecte maintenant
l'inventaire avant de manger et exclut les corps de monstres connus. Le blocage actuel est
la survie tactique face à plusieurs ennemis pendant `Hungry/Fainted` : l'écran
partiel ne suffit pas toujours à retrouver la menace adjacente et la route
vers les escaliers n'est pas encore stable. Le meilleur run a atteint
`Dlvl:1`, `T:2918`, puis est mort après des attaques de jackal ; un contrôle
ultérieur a atteint `T:1993` avant une mort contre un newt pendant `Fainting`.
La mémorisation des escaliers, le BFS et la garde contre les tours sans
progrès ont été ajoutés. `pickup_types:$%!` n'a pas encore produit une preuve
de ramassage alimentaire : le dernier run d'endurance avec le profil Caveman
est mort à `Dlvl:1`, `T:1063`, sous attaques de goblin pendant `Fainted`.
Le garde-fou d'incapacité est maintenant testé ; le dernier contrôle est mort
à `T:2096`, toujours à `Dlvl:1`. Aucune ascension n'est attestée.
Les essais récents : `20260913T035640Z` (Tourist, mort à `T:400` contre un
jackal), `20260913T035710Z` (Valkyrie, mort de maladie à `T:1922`) et
`20260913T035819Z` (Valkyrie, mort au message `The grid bug bites!` à
`T:2035`). La tentative `20260913T040021Z`, après déplacement déterministe
sur huit directions, est restée indéterminée à `Dlvl:1`, `T:638`, avec 59
récupérations et aucun écran final ; elle constitue un cas de blocage à
reproduire, pas une partie gagnée. Les prières et leurs confirmations sont bornées,
mais une prière unique ne constitue pas une stratégie de survie.

## Suite immédiate

1. Valider la première interaction avec le binaire cible et améliorer la
   reconnaissance des écrans de création de personnage.
2. Ajouter des fixtures de prompts réels, le timeout indépendant du scraper et
   un observateur xlogfile dont le chemin est prouvé.
3. Remplacer l'exploration circulaire par des compétences testées : survie,
   inventaire, combat/retrait, cartographie et objectifs de branche.
4. Produire des parties longues et classer toutes les fins sans exclure les
   abandons du dénominateur.
