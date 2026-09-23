# Passation — bot BotHack pour NetHack 3.6.7 (ascension assistée)

Document écrit pour un autre LLM ou un développeur qui reprend ou aide le
projet. État au **2026-09-17, 17h30 UTC**.

Racine du projet : `run_06.09.26/bothack_3.6/claude/`. Le répertoire frère
`codex/` est un autre agent : ne pas y toucher.

---

## Résultat principal (2026-09-22)

**Première ascension assistée complète et entièrement automatique** :
partie `full-c01/g011` (seed moteur 8011), du Dlvl 1 à l'offrande sur
l'Astral, en **51 834 tours**. Verdict du moteur `ascended`, identique au
xlogfile (`death: ascended`, 4 497 576 points, XL 19). Pas de mode wizard ni
de scénario.

Aides actives et journalisées :
- invincibilité : 506 morts annulées ;
- anti-famine : 3 interventions ;
- kit de départ.

Chronologie (tours) :

| tour | étape |
| --- | --- |
| 226 | Dlvl 2 |
| 989 | Minetown |
| 3 713 | Sokoban |
| 12 593 | Château |
| 14 202 | Vallée |
| 16 083 | Quête |
| 23 859 | Vlad |
| 25 415 | Chandelier |
| 35 476 | Cloche |
| 38 047 | Livre |
| 38 390 | Invocation |
| 38 806 | Amulette |
| 43 942 | Plans |
| 48 869 | Astral |
| **51 834** | **Ascension** |

Données : `runs/worker/full-c01/g011/` (manifest, result, progress, dumplog).

Scénario `planes` (départ sur la Terre avec l'Amulette) : 2 ascensions
vérifiées par le moteur. Les séries continuent en mode continu sur le
miniforum : `full-c01`, `full-c02`, `planes-c01`.

Corrections décisives des derniers jours :
- prompt 3.6 « Attach your candles » (bougies jamais fixées) ;
- récupération de la Cloche et du Chandelier chez leurs porteurs ;
- noms des Plans en 3.6 (« Earth »… au lieu de « End Game ») ;
- recherche de portail BotHack avant le combat ;
- repli « search » quand aucune action n'est proposée ;
- veto des actions refusées sans consommer de tour.

## 1. Objectif

Demande initiale de l'utilisateur :

- **But** : un bot Python qui joue à NetHack **3.6.7**, sans intervention
  humaine, et atteint d'abord une **ascension assistée**.
- **Méthode** : avancer étape par étape (Minetown, puis Château, etc.),
  corriger le maximum d'erreurs, fiabiliser le contrôle du jeu avant de
  travailler la survie réelle.
- **Aides de test** : invincibilité, anti-famine, kit d'équipement. Elles
  doivent être désactivables et journalisées, et ne jamais accomplir un
  objectif à la place du bot.
- **Règles 3.6.7** : adapter BotHack, notamment Elbereth et le pudding
  farming.
- **Lanceur de séries** : garder de quoi comprendre chaque échec, distinguer
  ascension / mort / crash / blocage / limite, vérifier la victoire par le
  moteur, ne pas relancer 100 parties sur le même bug, pouvoir passer à
  l'échelle (Vast AI, 1000 parties).
- **Rythme actuel** : lots de runs de **2 h** sur la VM `miniforum-worker`,
  puis pause, puis correction groupée des échecs. Ça économise des tokens.

**Critère de succès** : `result.json` avec `outcome: ascended`. C'est le
verdict du moteur (`end` émis par `done()`), recoupé avec le `xlogfile`.

---

## 2. Architecture (ce qui existe)

| composant | rôle |
| --- | --- |
| `vendor/NetHack-NetHack-3.6.7_Released/` | sources officielles, intactes |
| `engine/nethack-3.6.7/` | arbre patché ; `engine/nethack-3.6.7-bot.patch` = diff |
| `engine/nethack-3.6.7/win/bot/winbot.c` | *window port* « bot » : protocole JSON-lines sur deux pipes |
| `engine/nethack-3.6.7/src/botassist.c` | aides (invincibilité, anti-famine, kit), seed, verdict de fin |
| `engine/build.sh` | build vers `build/install/` (`HEADLESS=1` : sans ncurses, pour le worker) |
| `nhbot/engine.py` | client du protocole, un répertoire isolé par partie, options nethackrc |
| `nhbot/rungame.py` | une partie : manifest, result, logs, classification de fin |
| `nhbot/series.py` | N parties (sous-process), résumé, arrêt si la même signature se répète |
| `nhbot/supervisor.py` | limites et détecteurs de boucles/blocages (voir 2.3) |
| `nhbot/recorder.py` | anneau des 800 dernières observations/actions, jalons `progress.jsonl`, objets clés gagnés/perdus |
| `nhbot/analyze.py` | explication d'une partie (`--steps N`) ou d'une série |
| `nhbot/scenarios.py` + `scenarios/*.json` | situations préparées en mode wizard, jamais comptées comme parties |
| `pybothack/` | port Python fidèle du BotHack Clojure (2 ascensions en 3.4.3) + adaptations 3.6 |
| `pybothack/nhbridge.py` | passerelle : transforme les « touches » de BotHack en réponses structurées, rend les glyphes |
| `pybothack/compat36.py` | traductions 3.6 → 3.4.3 (menus, messages, libellés d'objets) |
| `pybothack/rules36.py` | règles 3.6 : Elbereth strict, prière, pas de farming, profils, tactiques assistées |
| `tests/` | 48 tests unitaires (`python3 -m pytest -q tests`) |
| `tools/worker_series.sh`, `tools/worker_dev.sh`, `tools/fetch_worker.sh`, `tools/live.py` | exécution sur le worker (voir section 3) |
| `docs/DEVLOG.md` | journal numéroté des bugs trouvés en jouant et de leurs correctifs |

### 2.1 Protocole moteur ↔ bot

Le jeu envoie une **requête** à chaque entrée attendue : `cmd`, `cmdcont`,
`key`, `yn`, `line`, `ext`, `menu`, `pos`. Chaque requête contient :

- les événements depuis la précédente : `msg`, `text`, `menu_show`,
  `assist`, `protoerr` ;
- les cases de carte modifiées (glyphe, caractère, couleur, drapeaux) ;
- le statut ;
- l'inventaire, s'il a changé ;
- la position du héros ;
- un bloc `priv` (succès, chance…) réservé aux logs et au verdict. **Le bot
  ne le lit jamais.**

Les glyphes des objets non identifiés sont masqués. Le bot répond une ligne
(`k`/`y`/`l`/`x`/`m`/`p`/`e`). Ce choix supprime la désynchronisation de
terminal, qui causait 37 % des abandons en 3.4.3.

### 2.2 Aides (moteur, variables d'environnement, toutes journalisées)

- **`NH_ASSIST_INVINCIBLE`** : une mort est annulée par `savelife()`.
  Ajouts faits pour qu'elle reste utile sous une foule :
  - pas de tour d'impuissance après la mort annulée ;
  - attributs, niveaux (jusqu'à `u.ulevelmax`) et PV max (plus haut vu)
    restaurés ;
  - slime guéri avant la transformation, qui détruit l'armure (`noslime`) ;
  - le cerveau ne tombe jamais sous le minimum face aux mind flayers
    (`brainsave`).
- **`NH_ASSIST_NOSTARVE`** : nutrition < 50 remise à 900 ; étouffement mortel
  évité.
- **`NH_ASSIST_KIT`** : `config/kit-default.txt`, avec :
  - portés : GDSM +2, amulette de réflexion, bottes de vitesse +2 ;
  - en inventaire : anneau de lévitation, licorne, sac sans fond, pioche,
    2 rations.

  Le kit est identifié ; il ne contient aucun objet d'objectif.
- **`NH_SEED`** : partie déterministe (seed moteur).

### 2.3 Supervision (`nhbot/supervisor.py`, valeurs par défaut)

| détecteur | déclenchement | réaction |
| --- | --- | --- |
| boucle de prompt | 40 réponses | Échap à 20 |
| boucle d'action | même action, même position, même tour ×8 | récupération |
| | ×40 | arrêt |
| fixation de cible | même position citée dans la raison ≥150 fois ou ≥400 tours | oublier la cible |
| | revient après 3 oublis | arrêt |
| progression de tour | trop de requêtes sans que le tour avance | recherche forcée, puis arrêt |
| emballement de requêtes | 3000 requêtes pour < 30 tours | arrêt |
| absence de nouveauté | 6000 tours sans case/profondeur/XL nouvelle | reset exploration à 3000, arrêt à 6000 |
| boucle de mort | 150 morts annulées en 300 tours sans progrès | arrêt |
| décision lente | 60 s | dump des piles |
| | 600 s | arrêt |

Classification de fin : `ascended`, `died`, `quit`, `escaped`,
`goal_reached`, `stuck`, `limit`, `crash_bot`, `crash_engine`, `unknown`.

### 2.4 Mesures « port » propres à 3.6 et au mode assisté

- **Tactiques assistées** (`BOTHACK_TACTICS=assisted`, défaut si
  invincible) : pas de fuite ni de repos (inutiles sous invincibilité).
  Rhabillage avant combat, sauf dans les 100 tours qui suivent un retrait
  volontaire.
- **Astral** : `assisted_astral_rush` (avant le combat) vise les trois cases
  d'autel fixes de `astral.des`, écran BotHack (9,11) (39,7) (69,11).
- **Veto d'actions refusées** (délégateur + passerelle) : une action refusée
  par le jeu sans que le tour avance (objet maudit, main non libre…) est
  bloquée 300 tours. Le handler suivant est alors consulté.
- **Identification** : si les faits observés (prix, propriétés) excluent
  toutes les identités d'une apparence, repli sans ces faits, avec un
  warning `identity facts exclude every candidate` qui contient les faits.

---

## 3. Comment travailler (commandes)

Principes :
- **Tout run se fait sur le worker** (demande utilisateur).
- **Le local** sert seulement à éditer le code, lancer `pytest` et lire les
  résultats rapatriés.

```bash
# séries (répertoire ~/bothack36 du worker ; refuse de synchroniser si une série tourne)
tools/worker_series.sh --name cyc-02 --seeds 7003,7007 --jobs 3 \
    --max-turns 120000 --max-seconds 6600 --stop-on-repeat 25
tools/fetch_worker.sh cyc-02                   # -> runs/worker/cyc-02
python3 -m nhbot.analyze runs/worker/cyc-02    # résumé
python3 -m nhbot.analyze runs/worker/cyc-02/g003 --steps 60

# parties isolées / scénarios / rejeux (répertoire ~/bothack36-dev, synchronisable à tout moment)
tools/worker_dev.sh sync                       # code + rebuild moteur si nécessaire
tools/worker_dev.sh run rej1 --seed 7031 --max-turns 30000 --trace
tools/worker_dev.sh status ; tools/worker_dev.sh wait rej1 ; tools/worker_dev.sh fetch rej1
```

### Fichiers d'une partie (`gNNN/`)

| fichier | contenu |
| --- | --- |
| `manifest.json` | hashes, seed, aides, limites |
| `result.json` | issue, raison, verdict moteur, étapes, compteurs, écran final |
| `progress.jsonl` | jalons (étapes, niveaux, XL, aides, `item_gained`/`item_lost` avec messages) |
| `last_steps.jsonl` | 800 dernières entrées : requêtes, messages, réponses, actions avec raisons BotHack |
| `bot.log` | warnings et erreurs Python |
| `nhdir/dumplog.txt` | carte et inventaire de fin (absent si la partie est tuée par la limite de temps) |
| `trace.jsonl` | tout, si `--trace` ; lourd, réservé aux rejeux |

### Worker

- **Accès** : `ssh miniforum-worker` (192.168.1.19), pas de sudo, pas de
  ncurses.
- **Capacité réelle** : 8 vCPU annoncés, mais **~70 % de *steal time*
  depuis le 17/09**, soit ~2 à 2,5 cœurs réels. **Utiliser `--jobs 3`.**
- **Vitesse** : 15-25 tours/s par partie en parallèle. Une partie qui va en
  Gehennom fait 40 000 à 60 000 tours, soit 45-90 min.

### Pièges déjà payés dans le harnais

- **Jamais `pkill -f motif`** : le motif matche le shell lui-même (exit
  144). Tuer par PID, avec un motif du type `pgrep -f "[n]hbot.rungame"`.
- **Ne pas modifier un script bash pendant son exécution** : bash lit le
  fichier au fil de l'eau.
- **Ne pas synchroniser le code d'une série en cours** : une série
  mélangerait deux versions du bot. `worker_series.sh` s'y oppose ;
  `worker_dev.sh` travaille dans un autre répertoire.
- **SIGTERM** : une exception levée dans le handler de signal peut être
  avalée par le `except Exception` du délégateur. `rungame` pose donc aussi
  `sup.terminated`, que le superviseur vérifie.
- **`--stop-on-repeat`** : les signatures sont tronquées, donc toutes les
  « fixation … examining tile » se ressemblent. Avec 12, big-w01 s'est
  arrêté trop tôt. Mettre 25 ou plus.

---

## 4. Ce qui a été appris (3.6.7 vs BotHack 3.4.3)

Détail et références de parties dans `docs/DEVLOG.md`. Classes de pièges,
pour savoir où chercher :

1. **Interface 3.6** :
   - conteneurs (« Do what with … ? ») et `#name` passent par des menus ;
   - « Continue eating? » est l'inverse de « Stop eating? » ;
   - le menu « Current skills » est affiché, pas choisi ;
   - le `getpos` forcé doit répondre -1 sur Échap ;
   - l'option `verbose` doit rester activée (les regex BotHack visent les
     textes longs) ;
   - l'option `color` est **obligatoire** : sans elle, le moteur n'envoie
     pas la couleur des objets, et une chaîne de fer `_` passait pour un
     autel.
2. **Noms d'objets 3.6** :
   - suffixes « containing N items », « (at the ready) »,
     « (being donned/doffed) » ;
   - prix « for sale », prix de pile = total ;
   - 16 nouvelles étiquettes de parchemins, exclusives, avec leur pluriel ;
   - livre « leathery » ; roman « paperback book » ; globs.
3. **Données** : Keystone Kops, Twoflower et le guide manquaient ; les
   minions « renegade X of Dieu » n'étaient pas compris.
4. **Prix 3.6.7** :
   - multiplicateur/diviseur cumulés, arrondi unique ;
   - surtaxe de commerçant fâché `+(t+2)/3` ;
   - la vente divise par 2 ou 3, puis ×3/4.
5. **Messages 3.6 non compris par BotHack** :
   - « You harmlessly attack a boulder » ;
   - « Perhaps that's why you cannot move it » ;
   - « There is a high altar to X (lawful) here » ;
   - l'autel sous des objets, annoncé en tête de la fenêtre « Things that
     are here » ;
   - « You can't reach the bottom of the pit » (bord de fosse connue) ;
   - « You cannot reach the bottom of the abyss » ;
   - « weapon is welded to your hand » ;
   - « strange object in water » ;
   - l'invite de sol pour manger, sans le prix.
6. **Menus > 52 entrées** : les lettres se répètent. La passerelle donne des
   clés privées (U+E000…) aux doublons.
7. **Branches** : un héros téléporté (scénario) doit régler la branche
   depuis la ligne de statut (« Astral Plane », « Home N »). Le mode wizard
   pose « adjust? » au chef de quête ; la passerelle répond `y`.
8. **Invincibilité** : voir 2.2. Sans ses compléments, un héros sous une
   foule ne jouait plus jamais, finissait XL1, ou perdait son armure (slime,
   incube).
9. **Cycles décisionnels BotHack** (souvent révélés par 3.6) :
   - ramasser puis jeter : mémoire des objets jetés, 2000 tours ;
   - gravure sur autel ou fosse ;
   - licorne maudite appliquée sans fin : défiance après 6 essais ;
   - frotter la lampe malgré une arme collée ;
   - retirer un anneau en sortant d'abord de la fosse (seules les bottes le
     demandent) ;
   - porte secrète supposée cherchée sans fin : limite de 60 recherches.

---

## 5. Où on en est (mesures)

Séries de parties complètes (Valkyrie naine, kit + invincibilité +
anti-famine) :

| série | parties | Château | Vallée | Cloche | Vlad | Chandelier | tour Sorcier | Livre | invocation | ascension |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ca-w01 (objectif Château) | 11 | 3 | – | – | – | – | – | – | – | – |
| ca-w06 (objectif Château) | 14 | 9 | – | – | – | – | – | – | – | – |
| big-w01 (seeds 7001-7049) | 49 | 38 | 32 | 14 | 17 | 8 | 17 | 5 | 0 | 0 |
| big-w02 (mêmes seeds, 62 parties) | 62 | 46 | 41 | 26 | 30 | 14 | 30 | 13 | 0 | 0 |

- **big-w02** : 37 `stuck`, 25 `limit` (1 h par partie, souvent atteinte
  après le Livre), **0 crash**.
- **Scénarios** :
  - `astral-altar` (héros préparé près du temple central de l'Astral) :
    2 ascensions sur 4 vérifiées par le moteur ;
  - Méduse → Château et Château → Vallée : réussis ;
  - `astral` depuis le point d'arrivée : échec (foule) ;
  - `quest-bell` : non représentatif (BotHack fait la quête après la
    Vallée).
- **En cours** : cycle **cyc-01** (seeds 7003, 7007, 7012, 7031, 7033,
  7008, 7047, 7034, 7049 ; 3 jobs ; 1h50 max par partie), lancé à 17h27 UTC
  avec les derniers correctifs (veto, renegade, surveillance des objets
  d'invocation non identifiés).

---

## 6. Là où ça bloque (priorités)

### A. Pas d'invocation après le Livre des Morts

Cause la plus proche de l'objectif. Beaucoup de parties atteignent le Livre
puis tournent 10 000 à 20 000 tours jusqu'à la limite de temps.
`behaviors.invocation()` journalise « invocation impossible, missing … ».
Constats sur big-w02 :

- **g007** : a le Livre, le Chandelier et 7 bougies, mais **plus la Cloche**
  (obtenue au tour ~20 000, perdue ensuite).
- **g012** : a le Livre, la Cloche et les bougies, mais **jamais le
  Chandelier** (pas d'étape `candelabrum`, alors que Vlad est exploré).
- Cause des pertes inconnue : la surveillance ne suivait que les noms
  identifiés. Corrigé pour cyc-01 : `silver bell`, `candelabrum`,
  `papyrus spellbook`, bougies.
- **Hypothèses à vérifier** :
  - BotHack jette ou vend un objet d'invocation encore non identifié ;
  - vol par un nymphe ou un démon ;
  - le Chandelier n'est pas ramassé sur le cadavre de Vlad : handler
  `explore_level vlad end`, ou objet en haut de la tour pas vu.
- **À faire** : regarder `item_lost` dans cyc-01. Au besoin, rejouer
  `--seed 7012 --trace` jusqu'à Vlad (~25 000 tours) et lire autour de la
  mort de Vlad.

### B. Fixations « examining tile » / « new or desired item »

Première cause de `stuck` (~11 dans big-w02). Mécanisme général : BotHack
croit qu'une case a de « nouveaux objets », y va, fait `:`, repart, recommence.
Causes déjà trouvées :

- type d'objet inconnu, donc glyphe jamais mémorisé ;
- libellé non apparié au menu de ramassage ;
- décor mal lu (autel, fosse) ;
- `:` qui ne met pas à jour la case.

Méthode : pour chaque partie, lire les derniers « You see here » et les
`unknown itemtype` de `bot.log` (script dans l'historique : parcourir
`last_steps.jsonl`), puis rejouer la seed avec `--trace`.

### C. Emballements de requêtes (6 dans big-w02)

Actions refusées sans consommer de tour :
- retirer un anneau maudit ;
- appliquer le sac sans main libre ;
- mettre un anneau avec une arme collée ;
- farlook sur un minion « renegade ».

Correctif générique (veto) et farlook corrigés, à vérifier dans cyc-01.

### D. « No novelty » en Gehennom profond (Dlvl 39-45)

~10 parties. Le bot « cherchait l'escalier montant » en fouillant une porte
secrète supposée (limite de 60 ajoutée). Vérifier s'il reste des cas :
cartes de labyrinthe sombres, faux niveaux de la tour du Sorcier.

### E. Foules et boucles de mort

Astral, Vallée, Gehennom avec monstres invisibles. L'invincibilité évite la
mort, mais le bot avance trop lentement.

- **Astral** : les Cavaliers bloquent le passage ; le coût de traversée
  d'un Cavalier (40) n'a rien changé.
- **Méduse sans réflexion** (amulette perdue) : pétrification en boucle,
  pas de serviette ni de bandeau.

### F. Limites de temps

`--max-seconds 3600` est trop court pour une partie complète sur le worker
bridé. Mettre ≥ 6600 s, voire relancer par seeds ciblées.

### G. Détails connus non traités

- **Anneau de lévitation perdu avant Méduse** (2 parties) : la cause sera
  visible via `item_lost`.
- **Oscillation entre deux objectifs** : « get protection » ↔ exploration
  (big-w01 g020).
- **Chaîne de fer / autel dans la quête** (full-w01 g002) : couleur
  corrigée depuis, à reconfirmer.
- **`unknown itemtype for item ''`** : une fois en début de partie, bénin.

---

## 7. Suite proposée

1. **Analyser cyc-01** : pertes d'objets d'invocation, veto effectif,
   parties au-delà du Livre. Corriger A en priorité.
2. **Obtenir une première invocation**, puis vérifier la suite :
   - Sanctum (« high altar ») ;
   - prise de l'Amulette au grand prêtre ;
   - montée ;
   - plans élémentaires (portails ; l'eau exige la lévitation) ;
   - Astral.

   Le scénario `planes` existe mais n'a pas été validé (combat long sur la
   Terre).
3. **Lancer des cycles de 2 h** de 3 parties en parallèle sur les seeds qui
   vont le plus loin (7003, 7007, 7011-7014, 7034, 7041, 7043, 7047). Élargir
   à des seeds neuves quand A et B sont réglés.
4. **Améliorer la signature d'échec** de `series.py` pour distinguer les
   causes : garder la raison BotHack sans les coordonnées, et « You see
   here … ».
5. **À plus long terme** :
   - retirer progressivement les aides (tester `--no-invincible` sur les
     étapes validées) ;
   - passer à l'échelle (Vast AI) : `engine/build.sh` et
     `python3 -m nhbot.series --jobs N` suffisent sur chaque hôte.

---

## 8. Conseils pour aider efficacement

- **Commencer par les données**, pas par le code. Pour une partie `stuck` :
  1. `python3 -m nhbot.analyze runs/worker/<série>/gNNN --steps 60` ;
  2. les dernières lignes de `last_steps.jsonl` (actions avec raisons et
     messages) ;
  3. `grep WARNING bot.log` ;
  4. `progress.jsonl` (étapes, `item_lost`).
- **Un bug = un test** dans `tests/test_compat36.py` quand c'est testable
  hors partie (parsing de libellés, messages, prix, données).
- **Chaque correctif « port » est commenté** avec la partie qui l'a révélé.
  Garder cette convention et ajouter une entrée dans `docs/DEVLOG.md`.
- **Le code `pybothack/`** suit le Clojure original. Préférer des
  correctifs ciblés et commentés plutôt que des réécritures.
- **Ne jamais laisser les aides accomplir un objectif**. Toute nouvelle aide
  va dans `botassist.c`, est journalisée et s'accompagne d'une variable de
  désactivation.
