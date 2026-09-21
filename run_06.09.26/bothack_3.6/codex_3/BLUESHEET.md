# Bluesheet expérimental BotHack × Jev

## Questions et hypothèses neutres

| Variante | Question mesurée | Unité de décision | Critère initial |
| --- | --- | --- | --- |
| Baseline | Jusqu'où va BotHack dans ces conditions ? | handlers BotHack | référence |
| JEV_RAW | Jusqu'où va Jev avec seulement une interface correcte ? | action directe | Minetown |
| JEV_PRIMITIVES | Jev dirige-t-il utilement les capacités fiables de BotHack ? | intention | Minetown |
| JEV_SHADOW | Jev diverge-t-il utilement près des échecs de BotHack ? | intention non exécutée | analyse contrefactuelle |

Aucune hypothèse de supériorité n'est posée. Le résultat principal est la
distribution des étapes atteintes par seed, accompagnée des raisons d'arrêt,
du nombre de boucles, du temps et du coût.

## Variables contrôlées

Pour une matrice donnée, conserver les mêmes seeds moteur, personnage, options
NetHack, kit/aides, objectif, limites de tours et version exacte de la
baseline. Le seed BotHack est égal au seed moteur par défaut. Le manifest de
chaque partie contient ces valeurs et les hashes de code.

Ne pas mélanger les résultats assistés et non assistés. Ne pas compter les
runs `--jev-offline`, les scénarios wizard, ni deux modèles Jev différents
dans la même série.

## Mesures

Mesures communes : issue finale, étape maximale, profondeur, tours, vitesse,
stagnations/récupérations, morts assistées et histogramme d'actions.

Mesures Jev : état présenté, choix proposés, choix retenu, distribution des
probabilités, confiance, exécution réelle, observation suivante, latence,
tokens, coût et erreurs API. Pour Shadow, conserver en plus l'action exacte de
BotHack et le déclencheur (`goal_change`, `loop_detected`, `branch_change`,
`important_item_change`, `near_*_limit`, etc.).

## Progression des essais

1. Smoke hors ligne : une seed, 20–100 tours, uniquement pour valider le
   protocole et les fichiers.
2. Minetown pilote : trois seeds identiques, aides identiques, quatre modes.
3. Minetown mesure : au moins 20 seeds après gel du modèle, des prompts et des
   candidats.
4. Rejouer les seeds d'échec et examiner `jev_decisions.jsonl`, les dernières
   étapes et les probabilités avant de modifier une politique.
5. Si la réussite Minetown et les coûts le justifient, répéter avec les mêmes
   règles vers Château, Vallée, quête/invocation, puis ascension.

Toute modification de représentation, prompt, candidat ou seuil Shadow crée
une nouvelle série ; ne pas agréger avant/après comme une seule expérience.

## Commande pilote

```bash
export OPENROUTER_API_KEY=...
python3 run_matrix.py --out runs/minetown-pilot \
  --seeds 42001,42002,42003 --goal minetown --max-turns 30000
python3 compare_experiments.py runs/minetown-pilot
```

Le premier run réel doit rester petit : RAW peut appeler Jev presque à chaque
tour, tandis que PRIMITIVES réduit parfois plusieurs tours à une intention et
SHADOW ne consulte le modèle que sur événement intéressant.

