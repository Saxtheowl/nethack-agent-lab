# Sauvegarde — version qui a ascensionné (2026-09-22)

- `bothack36-code.tar.gz` : tout le projet (moteur patché, bot, harnais, docs,
  scénarios, tests), sans les runs ni le build. Rebuild : `engine/build.sh`
  (ou `HEADLESS=1 engine/build.sh`).
- `g011-ascension-run.tar.gz` : la partie `full-c01/g011` (seed moteur 8011),
  première ascension assistée complète, 51 834 tours, verdict moteur =
  xlogfile.
- `nethack-3.6.7-bot.patch` : diff du moteur par rapport à NetHack 3.6.7.
- `SHA256SUMS` : empreintes.

Le code sauvegardé contient, en plus de la version qui a joué g011 :
l'optimisation du suivi des monstres (même résultat, plus rapide), la
tolérance de fixation sur l'Astral, l'option `--record` et
`tools/trace2ttyrec.py`.
