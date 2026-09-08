# Limites restantes

Cette section dit honnêtement ce qui n'est pas fait, afin que ce dépôt ne soit
pas lu comme un portage terminé.

## Non porté (le moteur de jeu)

- **`delegator.clj`** — le répartiteur d'événements/prompts à priorité, la
  sémantique d'agent Clojure (appels mis en file), et l'ensemble des protocoles
  de prompts/actions.
- **`scraper.clj`** — la machine à états de synchronisation (`##'`, `--More--`,
  menus multi-pages, prompts de localisation/direction).
- **`actions.clj`** — les ~40 actions et leurs gestionnaires de messages.
- **`game.clj` / `dungeon.clj` / `player.clj` / `tracker.clj`** — le modèle du
  monde, le suivi des monstres, les intrinsics, l'inventaire.
- **`pathing.clj`** — A*, Dijkstra, navigation inter-niveaux/branches.
- **`fov.clj` + `NHFov.java`** — visibilité (éclairage, ESP).
- **`behaviors.clj` / `sokoban.clj`** — invocation, prière, résolution Sokoban.
- **`term.clj` / `jta.clj` / `ttyrec.clj`** — émulateur de terminal et I/O réseau/pty
  (le smoke-test utilise un pty brut, pas encore l'émulateur `pyte`/JTA).
- **`bots/mainbot.clj`** — la stratégie complète du bot ascendant (2 388 lignes).

## Fidélité partielle dans ce qui est porté

- `itemid` : la partie « prix » de l'identification (relations `pricec`/`base-cha-cost`)
  est une réimplémentation simplifiée ; les exemples de prix commentés dans
  `itemid.clj` ne sont pas encore tous reproduits comme tests.
- `frame.py` / `tile.py` / `level.py` : portage partiel (les fonctions de mise à
  jour d'état du tile et les blueprints ne sont pas intégrés).
- `forget_names`/`forget-name` (retrait de faits) est un stub.

## Pas de résultat de partie

Aucune partie réelle n'a été jouée par le portage Python ; par conséquent aucune
ascension, aucun taux de victoire, aucune comparaison de résultats de partie entre
les deux bots n'est disponible. Une victoire isolée ne prouverait de toute façon ni
une fidélité absolue ni un taux de réussite comparable.

## Travail restant (pour atteindre l'objectif)

1. Porter le terminal (pyte + pty/telnet) et la machine de synchronisation du
   scraper, avec les tests différentiels associés.
2. Porter `delegator`, `actions`, `handlers`, puis le modèle `game`/`dungeon`/
   `player`/`tracker`, `pathing`, `fov`, `sokoban`, `behaviors`.
3. Porter `mainbot.clj` dans son ordre de priorités original.
4. Comparer les décisions Python/Clojure sur des états identiques (oracle étendu),
   corriger chaque divergence matérielle.
5. Faire jouer le Python contre la vraie version historique sans assistance,
   conserver ttyrec/xlogfile/options, et comparer les résultats des deux bots sur
   plusieurs parties.
