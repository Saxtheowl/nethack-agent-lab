# BotHack en Python — portage fidèle (agent openrouteur/deepseek_v4_0813)

Réécriture **en cours** du framework et du bot [BotHack](https://github.com/krajj7/BotHack)
de krajj7 — le premier bot à avoir fait une ascension à NetHack sans mode wizard
ni intervention humaine (25 janvier 2015) — en Python pur, sans déléguer aucune
décision au code Clojure/Java à l'exécution.

Cible historique vérifiée : **NetHack 3.4.3 avec le patchset nethack.alt.org (NAO)**,
seule version supportée par BotHack (`doc/compiling.md` de l'original).

## État réel (lire avant de faire confiance)

Ce dépôt contient **une partie** du portage : les données extraites fidèlement de
l'original, les modules « noyau » du moteur (position, util, frame, item, itemtype,
montype, monster, itemid, tile, level), et un **harnais de tests différentiels** qui
vérifie ces modules contre l'original Clojure utilisé comme oracle (857 cas, tous
verts).

**Le moteur complet (delegator, scraper, actions, game, dungeon, pathing, fov,
tracker, mainbot) et la boucle de jeu ne sont pas portés. Aucune ascension n'a été
réalisée.** Rien ici ne doit être lu comme un portage terminé ou vérifié équivalent.

Voir `docs/PORT.md`, `docs/RESULTS.md` et `docs/LIMITATIONS.md`.

## Arborescence

| chemin | contenu |
| --- | --- |
| `bothack/` | portage Python (framework, données `_data.json`) |
| `tools/` | scripts de build, extraction des données, oracle, harnais de comparaison |
| `tests/` | tests différentiels + tests unitaires |
| `docs/` | documentation détaillée (portage, résultats, limites) |
| `artifacts/` | journaux, sorties de test, preuves |
| `upstream/` | BotHack et NetHack 3.4.3-NAO (référence) |

## Prérequis / commandes

```sh
# construire NetHack 3.4.3-NAO
tools/build_nethack343_nao.sh upstream/NetHack

# extraire les données de l'original (nécessite JDK8 + lein, voir tools/)
tools/dump_data.sh

# tests unitaires (sans oracle)
python3 -m pytest -q

# tests différentiels contre l'original Clojure (oracle)
JDK8_HOME=$PWD/.local/jdk8 BOTHACK_ORACLE=1 python3 -m pytest -q

# smoke-test de la cible (lance une vraie partie, quelques déplacements)
python3 tools/pty_smoke.py
```

Linux, Python 3.12+, `uv`, Git, GCC, Make, en-têtes ncurses. JDK8 et `lein` sont
requis uniquement pour l'extraction des données et l'oracle (jamais à l'exécution
du portage Python).
