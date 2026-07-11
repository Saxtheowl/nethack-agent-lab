# Notes de recherche

## Environnement retenu

Le dépôt maintenu du [NetHack Learning Environment](https://github.com/NetHack-LE/nle)
est désormais basé sur NetHack 3.6.7 et Gymnasium. C’est préférable à l’ancien
dépôt FAIR/NLE 0.9, qui était basé sur 3.6.6. Le moteur est épinglé au commit
`2319f2989f0035685017e9ea13c83b2546fe477c` et patché de façon reproductible.

## Leçons des agents publiés

- Le [rapport du NetHack Challenge 2021](https://nethackchallenge.com/report.html)
  constate que les baselines neuronales restaient très loin du jeu expert et
  met en avant l’intérêt de connaissances externes et d’abstractions.
- [AutoAscend](https://github.com/maciej-sypetkowski/autoascend), vainqueur du
  challenge, organise un agent symbolique en stratégies préemptibles avec état
  explicite, actions atomiques, navigation, inventaire, faim et logique
  d’Excalibur. Pour un objectif aussi net que Minetown, cette structure est
  beaucoup plus économe en données qu’un apprentissage de bout en bout.
- L’article [Insights From the NeurIPS 2021 NetHack Challenge](https://proceedings.mlr.press/v176/hambro22a.html)
  confirme l’avantage des systèmes symboliques dans ce régime. La première
  version locale privilégie donc une politique symbolique instrumentée ; les
  données de ses échecs pourront ensuite entraîner des modules ciblés plutôt
  qu’une politique opaque complète.

## Règles exploitées

La [page fontaine/Excalibur du NetHackWiki](https://nethackwiki.com/wiki/Fountain#Dipping)
indique qu’un personnage loyal de niveau 5 trempant une longue épée ordinaire
dans une fontaine a une chance sur six d’obtenir Excalibur. La politique ne le
fait qu’avec assez de PV, hors Minetown, et arrête lorsque la fontaine sèche ou
que l’artefact apparaît.

Pour la cible immédiate, une Valkyrie naine est volontaire : les gnomes et les
nains des Mines sont normalement pacifiques, ce qui réduit fortement le risque
sans modifier les règles du jeu. La difficulté devient surtout la navigation,
les portes cachées, la faim et les rares monstres réellement hostiles.

