# Fable Replay Viewer

Lecteur de replays NetHack pour les parties du projet voisin `gpt_5.6`
(agent Valkyrie → Minetown). Le projet `gpt_5.6` n'est **pas modifié** : ses
`runs/` sont lus en seule lecture.

## Lecteur CLI (principal)

Rejoue un ttyrec **directement dans le terminal** : les couleurs et le rendu
sont ceux de NetHack, sans réinterprétation. Navigation image par image ou par
sauts de 50 frames.

```bash
cd fable_replay_viewer
pip install pyte                      # seule dépendance hors stdlib
python3 play.py                       # menu : choisir un run puis un épisode
```

Direct sans menu :

```bash
python3 play.py --run vast-validation-001 --episode 3
python3 play.py --outcome success     # ne proposer que les succès
python3 play.py --list                # lister les runs et leur taux, sans jouer
python3 play.py --run baseline-005 --list   # lister les épisodes d'un run
python3 play.py --runs /autre/chemin  # autre répertoire de runs
python3 play.py --speed 8             # vitesse de départ
```

### Touches pendant la lecture

| Touche        | Action                          |
|---------------|---------------------------------|
| `espace`      | lecture / pause                 |
| `→` ou `n`    | +1 frame                        |
| `←` ou `p`    | −1 frame                        |
| `↑` ou `f`    | **+50 frames**                  |
| `↓` ou `b`    | **−50 frames**                  |
| `g` / `G`     | aller au début / à la fin       |
| `+` / `-`     | plus vite / moins vite          |
| `q`           | quitter                         |

La barre de statut (bas de l'écran) indique la frame courante, le temps, la
vitesse et la touche envoyée par l'agent pour la frame affichée.

## Comment ça marche

`play.py` scanne le répertoire `runs/` (via `results.jsonl`,
`episodes/*/result.json`, ou à défaut un `xlogfile` racine pour les smoke
tests), présente un menu classé par taux de réussite, puis rejoue le ttyrec
choisi. Le décodage du format **ttyrec3** du NLE (entêtes `<iiiB`, canaux
0 = sortie terminal, 1 = touche agent, 2 = score interne) est dans
`replay_core.py`. La lecture avant est incrémentale (on n'écrit que les
nouvelles frames) ; un retour arrière ré-affiche depuis le début jusqu'à la
frame visée — simple et fidèle au terminal réel.

## Viewer navigateur (optionnel)

Une version web existe aussi, avec classement des runs, tableaux triables et
lecteur graphique :

```bash
python3 server.py --host 0.0.0.0 --port 8791   # http://localhost:8791/
```

Voir `server.py` / `static/`. La CLI reste l'outil recommandé pour un usage
rapide en terminal.

## Format attendu

Un `runs/` contenant des dossiers de run, chacun avec au choix :

- `results.jsonl` + `episodes/000000/…ttyrec…` (format standard `mt-run`), ou
- `episodes/*/result.json`, ou
- un `*.ttyrec*` + `*.xlogfile` à la racine (smoke tests).
