# Agent Valkyrie → Minetown

Ce projet exécute un agent symbolique sur le NLE maintenu, basé sur la version
officielle NetHack **3.6.7**. Les parties comptées sont des Valkyries naines,
loyales et féminines, sans wizard mode et sans seed contrôlée. La seule
modification favorable du jeu est le kit explicitement autorisé : une
**blessed greased +2 gray dragon scale mail**, portée dès le départ.

Le succès est mesuré au premier tile que NetHack considère comme appartenant à
la ville. Ce signal reste dans l’observation privée de l’évaluateur : il termine
la partie mais n’est jamais transmis à la politique.

## Installation locale

```bash
./scripts/setup.sh
```

Le script garde l’environnement Python, NLE, `flex` et `bison` sous ce
répertoire. Il n’installe rien globalement.

## Mesurer et regarder

```bash
.venv/bin/mt-run --episodes 20 --workers 4
.venv/bin/mt-watch --list
.venv/bin/mt-watch --outcome failure
.venv/bin/mt-watch --outcome success --speed 12
```

Chaque run contient sa configuration, un `results.jsonl`, un résumé avec
intervalle de confiance de Wilson, la cause principale de chaque échec et les
ttyrecs. `mt-watch` affiche un petit tableau puis rejoue la partie choisie dans
le terminal, avec `--inputs` pour voir les touches de l’agent.

## Protocole compté

- NetHack 3.6.7, environnement `NetHackChallenge`, `wizard=False` forcé ;
- personnage fixe `val-dwa-fem-law` ;
- aucune seed injectée et effets temporels non figés ;
- monstres normaux activés, pas de sauvegardes/bones ;
- succès exact au premier appel vrai à `in_town(u.ux, u.uy)` ;
- le canal interne contenant ce bit est supprimé avant l’appel à la politique.

La politique combine navigation cartographique, recherche ciblée des portes
secrètes, gestion des portes verrouillées, pacifisme envers les habitants
nains/gnomes, combat et fuite selon les PV, repos, ration et prière de faim.
À partir du niveau d’expérience 5, elle sait également tremper sa longue épée
dans une fontaine hors Minetown pour tenter d’obtenir Excalibur.

