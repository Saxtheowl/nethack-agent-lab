# Bot NetHack 3.6.7 — Valkyrie → Minetown (objectif ≥80 %)

Agent symbolique (Python, pty + pyte) qui joue à **NetHack 3.6.7 officiel
compilé des sources, SANS mode wizard** (`WIZARDS=nobody`), personnage
Valkyrie naine. Succès = entrer dans Minetown (≤3 cases d'une
porte/fontaine/autel de la ville). Objectif long terme : l'ascension.

## Le seul avantage par rapport au jeu par défaut

Une modification unique du source (`u_init.c`, kit de départ Valkyrie) :

| Objet | Défaut | Bot |
|---|---|---|
| **Gray dragon scale mail bénie graissée +2** | — | 1 (portée au tour 1) |

Tout le reste est le kit standard (épée longue +1, dague, petit bouclier +3,
1 ration). RNG/monstres/règles normaux, pas de bones, pas de familier
(options standard). Le bot peut ramasser et utiliser ce qu'il trouve dans le
donjon (wands, nourriture…) — butin légitime. Excalibur par trempage à XL5
et prière quand Weak = mécaniques normales du jeu.

## Win rate (batchs de ~100 parties sur instance Vast AI)

**Ancien kit large** (3 dagues, 2 wands of digging, 3 rations — retiré) :
12 → 28 → 32 → 48 → 43 → 51 % (interrompu).

**Kit strict** (GDSM seule) :
- m367-8 : **15 %** (baseline)
- m367-9 : **23 %** (fix majeur : la syntaxe de fouille `m10s` héritée de la
  3.7 était invalide en 3.6.7 — toutes les fouilles ne duraient qu'1 tour)
- m367-10 : amnistie bans+fouilles (interrompu pour le suivant)
- m367-11 : **en cours** — explorateur "occupancy map"

Journal détaillé batch par batch : `PLAN-v2.md`.

## Stratégie d'exploration (inspirée d'autoascend et BotHack)

Sources : [autoascend](https://github.com/maciej-sypetkowski/autoascend)
(1er du NeurIPS 2021 NetHack Challenge), [BotHack](https://github.com/krajj7/BotHack)
(1re ascension autonome, 3.4.3), et le papier
[Exploration in NetHack With Secret Discovery](https://arxiv.org/abs/1711.03087)
(occupancy maps : -30 % d'actions, 90 % des pièces secrètes en <500 actions).

1. **Déléguer les déplacements au jeu** : commande travel `_` (pathfinding
   natif), G-runs dans les couloirs ; le BFS maison ne sert qu'à choisir la
   prochaine destination.
2. **Fouille ciblée** (`level.best_search_spot`) : détecter les « composantes
   cachées » (régions jamais vues, flood-fill), et ne fouiller QUE les murs
   qui leur font face et les culs-de-sac de couloirs. Score par case :
   bonus impasse (+25), bonus taille de la région cachée (jusqu'à +50),
   malus fouilles répétées (−4·passes²), malus distance (−0,5/case).
3. **Amnisties** : quand tout paraît épuisé mais qu'il reste de l'inconnu,
   on efface bans d'arêtes + compteurs de fouille (3× max par niveau) —
   la mémoire empoisonnée par des monstres disparus était une cause majeure
   de fausses impasses.
4. **Route Minetown** : Doom 1-4 → trouver l'escalier de branche des Mines
   (tester chaque `>`, lire l'overview `^O`) ; dans les Mines, jamais de
   rush : balayer chaque niveau (la ville est à Mines 5-8), jamais
   descendre sous Mines:9.
5. **Watchdogs à escalade** : coincé 30 ticks → travel du jeu vers l'objectif
   → marche ignore-monstres → fouille de poche → zap-test des wands
   trouvées ; garde-fou 600 s temps réel par niveau.

## Voir des replays (CLI local, comme mt-watch)

```bash
# rapatrier 3 succès + 3 échecs d'un batch depuis l'instance Vast
./venv/bin/python tools/watch.py --fetch m367-11

# tableau des parties locales
./venv/bin/python tools/watch.py --list

# rejouer (interactif) : espace play/pause, n/→ +1 frame, p/← −1,
# g début, G fin, +/- vitesse, q quitter
./venv/bin/python tools/watch.py --outcome minetown
./venv/bin/python tools/watch.py --outcome died --speed 12
./venv/bin/python tools/watch.py --game m367-9__g0007
```

Les parties vivent dans `runs/replays/` (meta.json + game.ttyrec).

## Infra

- **Instance Vast AI** 44497883 (24 cœurs, 0,073 $/h, budget dur 2 $,
  ~1,0 $ consommé) : `ssh -p 17882 root@ssh1.vast.ai` ; batchs de 100
  parties, 20 en parallèle, ~1 h.
- Sources du jeu sur l'instance : `/root/third_party/nethack-3.6.7`
  (rebuild : `make -C src -j8` puis `cp src/nethack
  /root/nh367/games/lib/nethackdir/`).
- Local : `bot/` (brain/level/game/screen/term), `runner/run_batch.py`,
  `tools/watch.py`, `tools/play_daemon.py` (jouer soi-même via fichiers).
