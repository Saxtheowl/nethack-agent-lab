# Agent Valkyrie → Minetown (run claude_fable_2)

Agent symbolique sur le [NLE maintenu](https://github.com/NetHack-LE/nle)
(NetHack **3.6.7** officiel), en parallèle de l'approche terminal du run
`claude_fable`. L'architecture repart des techniques du run `gpt_5.6`
(politique symbolique ≈86 % locale) avec plusieurs améliorations ciblées.

Parties comptées : Valkyrie naine loyale (`val-dwa-fem-law` — les nains et
gnomes des Mines sont pacifiques), sans wizard mode, sans seed. La seule
modification favorable est le kit autorisé, appliqué par patch NetHack :
une blessed greased **+2 gray dragon scale mail**. Le succès est signalé par
le premier appel vrai à `in_town(u.ux, u.uy)` ; ce bit reste dans
l'observation privée de l'évaluateur et n'est jamais transmis à la politique.

## Améliorations par rapport à gpt_5.6

- **Recherches par rafales comptées** (`16s`) : ~10× moins de steps d'agent
  pour fouiller les portes cachées → moins de `step_timeout` ;
- **Elbereth** : gravure au doigt en situation critique (acculé ou PV bas
  face à des monstres qui la respectent), puis repos protégé sur la gravure ;
- **Jamais de mêlée contre un floating eye** (paralysie 1d70 quasi fatale) ;
- **Repos avant descente** d'escalier et repos par rafales interruptibles ;
- **Anti-blocage** : pas de côté ou creusage après une longue attente
  derrière un pacifique ;
- **Runner résilient** : une exception de politique ne tue plus l'épisode
  (réponses de secours ESC/entrée/attente), zéro `agent_error`.

## Installation locale

```bash
./scripts/setup.sh
```

Tout (venv, NLE, flex/bison/m4) reste sous ce répertoire.

## Mesurer et regarder

```bash
.venv/bin/mt-run --episodes 20 --workers 4
.venv/bin/mt-watch --list
.venv/bin/mt-watch --outcome failure
.venv/bin/mt-watch --outcome success --speed 12
```

Chaque run contient `config.json`, `results.jsonl`, un `summary.json` avec
intervalle de Wilson et causes d'échec, et les ttyrecs. `mt-watch` affiche un
tableau puis rejoue la partie choisie dans le terminal (lecteur ttyrec
intégré). Contrôles : `espace` play/pause, `n`/`→` +1 frame, `p`/`←` −1,
`g`/`G` début/fin, `+`/`-` vitesse, `q` quitter. `--inputs` montre les
touches de l'agent, `--json` le diagnostic de la politique, `--raw` streame
sans contrôles.

## Protocole compté

- NetHack 3.6.7, environnement `NetHackChallenge`, `wizard=False` forcé ;
- personnage fixe `val-dwa-fem-law`, aucune seed, effets temporels libres ;
- avantage de départ strict : uniquement la GDSM blessed greased +2 ;
- succès exact au premier tile de la ville (canal évaluateur privé) ;
- monstres normaux, familier standard, pas de bones.
