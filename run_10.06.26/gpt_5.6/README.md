# Agent Valkyrie → Minetown

Ce projet exécute un agent symbolique sur le NLE maintenu, basé sur la version
officielle NetHack **3.6.7**. Les parties comptées sont des Valkyries naines,
loyales et féminines, sans wizard mode et sans seed contrôlée. La seule
modification favorable du jeu est le kit explicitement autorisé et documenté
dans le patch NetHack : `+1 long sword`, 8 blessed `+1 daggers`, `+3 small
shield`, blessed greased `+2 gray dragon scale mail`, `+0 pick-axe`, 12 blessed
scrolls of magic mapping, 5 blessed potions of extra healing, 2 potions of holy
water et 1 food ration. Le pet est désactivé.

Le succès est mesuré au premier tile que NetHack considère comme appartenant à
la ville. Ce signal reste dans l’observation privée de l’évaluateur : il termine
la partie mais n’est jamais transmis à la politique.

## Installation locale

```bash
./scripts/setup.sh
```

Le script garde l’environnement Python, NLE, `flex`, `bison` et `m4` sous ce
répertoire. Il n’installe rien globalement.

## Mesurer et regarder

```bash
.venv/bin/mt-run --episodes 20 --workers 4
.venv/bin/mt-watch --list
.venv/bin/mt-watch --outcome failure
.venv/bin/mt-watch --outcome success --speed 12
.venv/bin/mt-watch --root runs/vast-validation-001 --episode 0 --speed 20
```

Chaque run contient sa configuration, un `results.jsonl`, un résumé avec
intervalle de confiance de Wilson, la cause principale de chaque échec et les
ttyrecs. `mt-watch` affiche un petit tableau puis rejoue la partie choisie dans
le terminal avec un lecteur ttyrec intégré, avec `--inputs` pour voir les
touches de l’agent. `--root` accepte soit le dossier `runs`, soit un run précis.

## Résultat actuel

Validation Vast AI `runs/vast-validation-001`, 200 parties comptées, 24 workers,
NetHack 3.6.7 non-wizard :

- 187/200 arrivées Minetown, soit **93,5 %** ;
- intervalle Wilson 95 % : **89,2 %–96,2 %** ;
- médiane des succès : 719 pas agent ;
- échecs principaux : `step_timeout=8`, puis combats isolés (`giant spider`,
  `rabid rat`, `Green-elf`, `acid blob`, poison).

## Protocole compté

- NetHack 3.6.7, environnement `NetHackChallenge`, `wizard=False` forcé ;
- personnage fixe `val-dwa-fem-law` ;
- aucune seed injectée et effets temporels non figés ;
- monstres normaux activés, pas de sauvegardes/bones, pas de pet ;
- succès exact au premier appel vrai à `in_town(u.ux, u.uy)` ;
- le canal interne contenant ce bit est supprimé avant l’appel à la politique.

La politique combine navigation cartographique, recherche ciblée des portes
secrètes, gestion des portes verrouillées, pacifisme envers les habitants
nains/gnomes, combat et fuite selon les PV, repos, ration et prière de faim.
À partir du niveau d’expérience 5, elle sait également tremper sa longue épée
dans une fontaine hors Minetown pour tenter d’obtenir Excalibur.
