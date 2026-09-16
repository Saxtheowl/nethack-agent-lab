# BotHack Ascension

Nouvelle implémentation autonome de BotHack, orientée vers une ascension
attestée dans NetHack 3.4.3-NAO. Le projet courant ne copie pas `pybothack` et
ne charge pas l'ancien bot à l'exécution.

## Démarrage

```bash
python3 -m bothack_new.play --game ../codex_2/upstream/nh343/nethack.343-nao --seconds 60
python3 -m bothack_new.campaign --game ../codex_2/upstream/nh343/nethack.343-nao --runs 3 --seconds 60
python3 -m pytest -q
```

Les runs sont écrits dans `runs/` (répertoire ignoré par git). Une sortie de
processus n'est pas interprétée comme une victoire : le verdict exige un
message d'ascension et, si disponible, une entrée concordante dans xlogfile.

## Architecture

`session.py` possède seul l'écriture dans le PTY. `terminal.py` applique les
séquences ANSI par incréments et produit des snapshots indépendants.
`dialogue.py` décrit les transactions et les prompts. `world.py` conserve un
état immuable minimal. `strategy.py` choisit des actions déterministes avec
préconditions. `supervisor.py` distingue silence I/O, calcul lent, absence de
progrès et activité normale. `evidence.py` produit le manifeste de campagne.

La stratégie actuelle est une tranche jouable de survie et d'exploration ;
elle n'est pas encore certifiée pour l'ascension. Les choix non triviaux sont
journalisés afin de pouvoir remplacer progressivement cette stratégie par des
objectifs de fin de partie attestés.

## Provenance

Les rapports de `../codex_2/docs/` et le code NetHack accessible dans
`../codex_2/upstream/nh343` sont des références de diagnostic. Aucun module de
`pybothack` n'est importé. Le build déclaré est vérifié au démarrage par le
chemin du binaire et son empreinte SHA-256.
