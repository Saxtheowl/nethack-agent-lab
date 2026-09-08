# Portage : méthode, correspondance des modules, fidélité

## Objectif et statut

L'objectif demandé — réécrire **tout** BotHack en Python, conserver son
comportement, puis obtenir une ascension sans mode wizard ni intervention
humaine, avec des résultats comparables à l'original — **n'est pas atteint**.
Ce document décrit ce qui a été fait, comment, et ce qui reste.

## Original retenu

- Dépôt : <https://github.com/krajj7/BotHack>, commit `70226b3` (HEAD du dépôt).
- ~17 161 lignes de Clojure + ~2 664 lignes de Java (JTA, NHFov, API JVM).
- Version cible : **NetHack 3.4.3 + patches nethack.alt.org (NAO)**,
  explicitement indiquée dans `doc/compiling.md` (« The only supported version
  of NetHack is 3.4.3 with the nethack.alt.org patchset »).
- Jeu : <https://github.com/altorg/NetHack> (source NAO), commit historique
  `b60bd44c` (17 décembre 2014), contemporain de la première ascension.

## Méthode : extraire plutôt que retranscrire

Les grosses tables de données ne sont **pas** retranscrites : `tools/cljdump/dumpdata.clj`
s'exécute dans le projet original et sérialise ses propres structures vers
`bothack/_data.json` :

| donnée | source originale | taille extraite |
| --- | --- | --- |
| 1 722 types d'objets | `itemdata.clj` | items, kind, glyph, prix, poids… |
| 376 types de monstres | `montype.clj` | attaques, tags, résistances… |
| 33 plans de niveaux spéciaux | `level.clj` | blueprint `blueprints` |
| 8 solutions Sokoban + rochers initiaux | `sokoban.clj` | `solutions`, `initial-boulders`, `soko-items` |
| candidats d'identification (ordre core.logic) | `itemid.clj` | `appearance-candidates` |
| pluriels, noms japonais, apparences | `itemdata.clj`/`itemtype.clj` | `plural->singular`, `jap->eng`, … |

Rien des 3 675 lignes d'`itemdata.clj` ni des 620 lignes de `montype.clj` n'a été
re-écrit à la main, donc ces tables ne peuvent pas dériver.

## Correspondance des modules portés

| original (Clojure) | port (Python) | état |
| --- | --- | --- |
| `util.clj` | `bothack/util.py` | porté, testé |
| `position.clj` | `bothack/position.py` | porté, testé |
| `frame.clj` | `bothack/frame.py` | porté (partiel) |
| `itemdata.clj`/`itemtype.clj` | `bothack/itemtype.py` + `_data.json` | données extraites |
| `item.clj` | `bothack/item.py` | `parse-label` + prédicats, testé |
| `itemid.clj` (core.logic) | `bothack/itemid.py` | filtres déterministes, testé |
| `montype.clj` | `bothack/montype.py` | données extraites + prédicats |
| `monster.clj` | `bothack/monster.py` | porté |
| `tile.clj` | `bothack/tile.py` | prédicats, testé |
| `level.clj` | `bothack/level.py` | porté (partiel) |

Modules **non encore portés** : `delegator.clj`, `scraper.clj`, `action.clj`,
`actions.clj`, `handlers.clj`, `tracker.clj`, `dungeon.clj`, `game.clj`,
`player.clj`, `pathing.clj`, `fov.clj` + `NHFov.java`, `behaviors.clj`,
`sokoban.clj`, `bothack.clj`, `main.clj`, `term.clj`/`jta.clj`/`ttyrec.clj`,
et `bots/mainbot.clj` (la stratégie du bot ascendant).

## Décisions qui portent du sens (et qui sont conservées)

- `effective-str` associe `18/00…49` → 20 et `18/50…99` → 19 ; cette conversion
  surprenante est conservée et testée (`bothack/util.py:effective_str`).
- `(= true 1)` est faux en Clojure et vrai en Python ; `itemid.clj_eq` restaure
  la sémantique Clojure là où les enregistrements d'objets sont fusionnés.
- `towards` renvoie `nil` (pas une direction) quand `from == to`, comme l'original.
- `position.distance` est la distance de Chebyshev ; `distance-manhattan` la
  distance de Manhattan.
- Les prédicats `monster?`/`item?`/`corpse?` de l'original renvoient parfois des
  valeurs *vraies non booléennes* (la couleur du monstre, le glyphe, la séquence
  de `re-seq`) plutôt que strictement `true`. Le portage normalise en `bool`, ce
  qui préserve le comportement observable (testé par l'oracle sur la valeur de
  vérité). Divergence de type volontaire, sans effet fonctionnel.

## Harnais différentiel (oracle)

`tools/cljcmp/oracle.clj` appelle les fonctions originales (y compris leur
comportement exact) sur des entrées EDN sérialisées, et renvoie les résultats en
EDN. `tools/oracle.py` pilote le sous-processus et `tests/test_differential.py`
compare les résultats avec le portage Python. Les résultats attendus **ne sont
pas** calculés par le code Python testé ; ils viennent du Clojure original.

Sans `BOTHACK_ORACLE=1` (ou sans JDK8/lein), les tests différentiels sont
ignorés — leur absence n'équivaut pas à une validation.
