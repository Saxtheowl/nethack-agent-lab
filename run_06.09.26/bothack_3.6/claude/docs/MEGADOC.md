# MEGADOC — BotHack sur NetHack 3.6.7 : comment le bot fonctionne et comment il a ascensionné

État au **2026-09-23**. Résultat : **première ascension assistée complète et
entièrement automatique** le 2026-09-22. Partie `full-c01/g011`, seed moteur
8011, 51 834 tours. Le verdict du moteur (`ascended`) est confirmé par le
xlogfile officiel de NetHack.

Autres documents :
- `docs/HANDOFF.md` : passation rapide ;
- `docs/DEVLOG.md` : journal bug par bug ;
- `docs/IMPROVEMENTS.md` : plus de 100 pistes d'amélioration ;
- `README.md` : commandes.

---

## Sommaire

1. [En une page](#1-en-une-page)
2. [Architecture](#2-architecture)
3. [Le moteur modifié](#3-le-moteur-modifié)
4. [Le bot](#4-le-bot)
5. [La supervision](#5-la-supervision)
6. [Le harnais d'expérimentation](#6-le-harnais-dexpérimentation)
7. [Comment on a battu NetHack 3.6 : les modifications et leurs conséquences](#7-comment-on-a-battu-nethack-36--les-modifications-et-leurs-conséquences)
8. [La partie qui a ascensionné](#8-la-partie-qui-a-ascensionné)
9. [Où on en est (mesures)](#9-où-on-en-est-mesures)
10. [Regarder les replays](#10-regarder-les-replays)
11. [Leçons de méthode](#11-leçons-de-méthode)

---

## 1. En une page

Nous avons pris **BotHack**, le bot Clojure qui a ascensionné NetHack 3.4.3
en 2015, dans sa version portée en Python (`pybothack`, 2 ascensions en
3.4.3). Nous l'avons fait jouer à **NetHack 3.6.7**, la version officielle,
compilée depuis les sources.

**Trois choix structurants.**

1. **Pas de terminal.** Nous avons écrit un *window port* NetHack, `bot`, qui
   dit au bot exactement ce que le jeu attend (commande, oui/non, menu,
   position, texte), en JSON. Cela supprime la classe de bugs qui avait coûté
   37 % des abandons au port 3.4.3 : la lecture d'écran désynchronisée.
2. **Des aides de test explicites, désactivables et journalisées** :
   invincibilité, anti-famine, kit d'équipement. Elles permettent d'étudier
   le contrôle du jeu jusqu'au bout avant la survie. Elles n'accomplissent
   jamais un objectif : le bot doit trouver, combattre, invoquer et offrir
   lui-même.
3. **Une boucle industrielle** :
   - des séries de parties en parallèle sur une VM (`miniforum-worker`) ;
   - des détecteurs de boucles et de blocages ;
   - des journaux exploitables ;
   - l'analyse des échecs par classes, puis des corrections groupées.

   Plus de 1 500 parties ont été jouées.

**Le chemin.** BotHack est écrit pour 3.4.3. NetHack 3.6.7 change des
dizaines de textes, de menus, d'objets, de règles et d'affichages. Chaque
écart fait « rater » au bot une situation, et il boucle ou abandonne. Nous
avons trouvé et corrigé ces écarts un par un, grâce aux parties jouées :
autels, prix, objets, Kops, bougies, noms des Plans… La section 7 les
détaille avec leurs conséquences. L'ascension est venue quand les derniers
verrous de fin de partie ont sauté :
- les bougies du Chandelier, jamais fixées ;
- la Cloche et le Chandelier, jamais récupérés chez leurs porteurs ;
- les Plans, que le bot ne reconnaissait pas.

---

## 2. Architecture

```
┌────────────── miniforum-worker (11 vCPU) ────────────────────────────────┐
│  nhbot/series.py  ──► N × nhbot/rungame.py (un processus par partie)       │
│                           │                                                │
│         ┌─────────────────┴──────────────────┐                             │
│         │  nhbot/engine.py (client protocole) │◄─ pipes JSON ─► nethack    │
│         │  nhbot/supervisor.py (limites)      │   (window port "bot",       │
│         │  nhbot/recorder.py (journaux)       │    src/botassist.c)         │
│         │  pybothack/nhbridge.py (passerelle) │                             │
│         │  pybothack/* (BotHack porté)        │                             │
│         └─────────────────────────────────────┘                            │
└───────────────────────────────────────────────────────────────────────────┘
      ▲ tools/worker_series.sh, tools/worker_dev.sh (sync, lancement)
      │ tools/fetch_worker.sh (rapatriement) ; local : édition, pytest, analyse
```

| couche | fichiers | rôle |
| --- | --- | --- |
| Moteur | `engine/nethack-3.6.7/` (patché), `engine/build.sh` | NetHack 3.6.7 officiel + window port `bot` + aides |
| Protocole | `win/bot/winbot.c`, `nhbot/engine.py` | requêtes typées, carte en diffs, statut, inventaire |
| Aides | `src/botassist.c` | invincibilité, anti-famine, kit, seed, verdict de fin |
| Passerelle | `pybothack/nhbridge.py`, `compat36.py` | BotHack « tape des touches » ; on les traduit en réponses structurées ; traductions 3.6 → 3.4.3 |
| Stratégie | `pybothack/bots/mainbot.py` et le reste de `pybothack/` | BotHack : handlers priorisés, pathfinding, identification, tactiques |
| Règles 3.6 | `pybothack/rules36.py` | Elbereth, prière, farming, tactiques assistées |
| Supervision | `nhbot/supervisor.py` | limites, détecteurs de boucles, récupérations |
| Journaux | `nhbot/recorder.py` | anneau des 800 derniers pas, jalons, objets clés |
| Harnais | `nhbot/rungame.py`, `series.py`, `analyze.py`, `scenarios.py` | une partie, des séries, l'analyse, des situations préparées |

---

## 3. Le moteur modifié

### 3.1 Window port `bot` (`win/bot/winbot.c`)

NetHack appelle son interface pour chaque entrée : `nhgetch`, `yn_function`,
`getlin`, `select_menu`, `getpos`… Le port `bot` transforme chaque appel en
**requête JSON** sur un pipe, puis attend **une ligne de réponse**.

**Types de requête** : `cmd` (début de commande), `cmdcont` (suite d'une
commande : compte, préfixe), `key`, `yn` (question, choix, défaut), `line`,
`ext` (commande étendue), `menu` (items avec identifiant, lettre, texte),
`pos` (position à choisir).

**Contenu de chaque requête** :
- les événements depuis la précédente : messages, fenêtres de texte, menus
  affichés seuls, interventions d'aide ;
- les **cases de carte changées** : glyphe, caractère, couleur, drapeaux ;
- le **statut** ;
- l'**inventaire** s'il a changé ;
- la position du héros ;
- un bloc `priv` (succès, chance, alignement) **réservé aux logs, jamais lu
  par le bot**.

**Honnêteté** : les glyphes des objets non identifiés sont masqués, comme
pour un joueur. Le bot ne reçoit que ce qu'un humain verrait.

**Fin de partie** : `really_done` émet un enregistrement `end` (cause, tours,
profondeur, succès, compteurs d'aides). NetHack écrit aussi son `xlogfile`.
Le verdict final exige que **les deux concordent**.

### 3.2 Aides de test (`src/botassist.c`)

Variables d'environnement, toutes désactivables (`--no-invincible`,
`--no-nostarve`, `--kit none`, `--no-assist`), avec chaque intervention
journalisée (`assist.jsonl`, `progress.jsonl`, événement protocole).

| aide | ce qu'elle fait | ajouts faits en jouant (et pourquoi) |
| --- | --- | --- |
| **Invincibilité** | une mort (sauf génocide ou abandon) est annulée comme par une amulette de vie | *sans tour d'impuissance* : sinon un héros tué à chaque tour ne jouait plus jamais ; *attributs, niveaux et PV max drainés restaurés* : sinon il finissait XL1 à 10 PV ; *slime guéri avant la transformation* : la transformation détruisait l'armure ; *brainsave* : les mind flayers mangeaient l'Int sous le minimum |
| **Anti-famine** | nutrition < 50 remise à 900 ; étouffement mortel évité | — |
| **Kit** | au départ : GDSM +2, amulette de réflexion, bottes de vitesse +2, anneau de lévitation, licorne, sac sans fond, pioche, 2 rations ; tout identifié | ne contient **aucun** objet d'objectif |

**Règle** : une aide ne déplace jamais le héros, ne répond jamais à une
question et n'ouvre jamais un niveau. La Cloche, le Chandelier, le Livre et
l'Amulette sont obtenus par le bot.

### 3.3 Autres patchs moteur

- `NH_SEED` : parties déterministes. Une même seed avec le même code donne
  la même partie, ce qui a été vérifié par rejeu.
- Build *headless* (`HEADLESS=1`) : sans ncurses, pour le worker.
- Hooks dans `end.c` (lifesave), `eat.c` (famine, étouffement, cerveau),
  `timeout.c` (slime), `u_init.c` (kit), `cmd.c`, `do_name.c` (getpos),
  `unixmain.c` (seed).

---

## 4. Le bot

### 4.1 BotHack en bref

BotHack est un **système de handlers priorisés**. À chaque requête `cmd`,
le délégateur interroge les handlers dans l'ordre de priorité, et le premier
qui propose une action gagne. Les priorités (extrait, plus petit = plus tôt) :

| priorité | handler |
| --- | --- |
| −99 | offrir l'Amulette (Astral) |
| −20 | *assisté* : ruée vers l'autel (Astral) et vers le portail (Plans) |
| −16 | amélioration des compétences |
| −13 | noyade |
| −11 | faim |
| −9 | maladie |
| −7 | *assisté* : se rhabiller (sinon : retraite) |
| −6 | **combat** |
| −3 | handicaps (licorne…) |
| −2 | monstres « covetous » |
| −1 | rééquipement |
| 0 | arme |
| 1 | manger |
| 2 à 13 | objets : ramasser, conteneurs, identification, boutiques… |
| 19 | **progression** : exploration par étapes, Mines, Sokoban, Château, quête, Vlad, tour du Sorcier, invocation, Sanctuaire, Plans, Astral |
| 25 | *port* : dernier recours `unstick` |

La **progression** (`full_explore`) enchaîne les étapes du parcours BotHack :
1. DL1-10, Mines jusqu'à Minetown, Sokoban ;
2. Méduse, Château (baguette de souhaits, souhaits) ;
3. Vallée, quête (Cloche) ;
4. Vlad (Chandelier) ;
5. tour du Sorcier (Livre) ;
6. invocation, Sanctuaire (Amulette) ;
7. remontée, Plans, Astral.

Le **pathfinding** (`pathing.py`) est un A*/Dijkstra avec des coûts :
portes, pièges, monstres (attaquer au passage), creuser, lévitation.
L'**identification** (`itemid.py`) raisonne par apparences, prix, messages
de gravure et propriétés observées.

### 4.2 La passerelle (`nhbridge.py`)

BotHack a été écrit pour lire un écran et taper des touches. La passerelle :
- **rend la carte** du protocole en caractères et couleurs, selon le schéma
  `bothack.nethackrc` : rochers `8`, portes, pièges, arbres, etc. ;
- **traduit les touches** en réponses structurées : une touche de direction
  répond à une question de direction, `#pray\n` devient `cmd` + `ext`, une
  lettre de menu devient un identifiant ;
- appelle **les handlers de prompt de BotHack** avec le texte de la
  question, comme le faisait le scraper ;
- traduit les **différences 3.6** (voir 7.1) ;
- prévoit un **repli** journalisé quand rien ne répond.

### 4.3 Règles 3.6 (`rules36.py`)

- Elbereth : texte exact ; inopérant en Gehennom et sur les Plans ; jamais
  d'attaque depuis la case (« hypocrite » : −5 alignement).
- Seuil de prière `critically_low_hp` de 3.6.
- Pas de pudding farming : en 3.6, les clones ne lâchent plus rien.
- **Tactiques assistées** (quand l'invincibilité est active) : pas de fuite
  ni de repos, qui seraient une perte de temps. Rhabillage avant de combattre.
  Ruée vers l'autel et le portail avant le combat sur les Plans et l'Astral.

---

## 5. La supervision

Le bot peut boucler. Le superviseur **détecte, récupère, puis classe**
l'échec, sans jamais laisser tourner une partie inutile.

| détecteur | récupération | arrêt |
| --- | --- | --- |
| boucle de prompt | Échap | 40 |
| boucle d'action (même action, même tour) | bloquer la case, oublier la cible | 40 |
| fixation (même cible dans les raisons) | oublier la cible | 3 récupérations (tolérance ×5 sur l'Astral) |
| progression du tour | recherche forcée | 600 requêtes |
| emballement de requêtes | — | 3000 requêtes pour < 30 tours |
| absence de nouveauté | reset de l'exploration | 6000 tours |
| boucle de mort (invincibilité) | — | 150 lifesaves en 300 tours sans progrès (×4 sur les Plans) |
| décision lente | dump des piles | 600 s |

Un **veto d'actions** complète le dispositif : une action refusée par le jeu
sans consommer de tour est bloquée 300 tours, à cette position, et le handler
suivant est consulté. Exemples de refus : objet maudit, main non libre, porte
en diagonale.

---

## 6. Le harnais d'expérimentation

**Par partie** (`runs/<série>/gNNN/`) :

| fichier | contenu |
| --- | --- |
| `manifest.json` | hashes, seed, aides |
| `result.json` | issue, raison, verdict, xlog, étapes, compteurs, écran final |
| `progress.jsonl` | jalons, dont `item_gained` et `item_lost` avec les messages |
| `last_steps.jsonl` | 800 derniers pas |
| `bot.log` | journal du bot |
| `nhdir/dumplog.txt` | dumplog NetHack |
| `protocol.trace.gz` | si `--record` : toute la partie, rejouable |

**Issues** : `ascended`, `died`, `quit`, `escaped`, `goal_reached`, `stuck`,
`limit`, `crash_bot`, `crash_engine`.

**Séries** (`series.py`) :
- N parties en parallèle ;
- seeds successives ou choisies ;
- `--stop-on-repeat` pour ne pas rejouer 100 fois le même bug ;
- `summary.txt` : entonnoir d'étapes, signatures d'échec, anomalies.

**Séries continues** (`--games 1000`) : chaque partie terminée est aussitôt
remplacée, ce qui garde le worker saturé.

**Scénarios** (`scenarios/*.json`, mode wizard, jamais comptés comme
parties) :
- Méduse → Château, Château → Vallée ;
- Vallée → Vlad ;
- Plans (départ sur la Terre avec l'Amulette) ;
- Astral, offrande.

Ils testent une étape difficile en une heure au lieu de 40 000 tours.

**Worker** :
- `tools/worker_series.sh` : répertoire `~/bothack36`, refuse de
  synchroniser sous une série en cours ;
- `tools/worker_dev.sh` : répertoires séparés `~/bothack36-dev*`, pour
  tester sans toucher aux séries.

---

## 7. Comment on a battu NetHack 3.6 : les modifications et leurs conséquences

Chaque ligne ci-dessous est un **écart entre 3.4.3 et 3.6.7**, ou une
faiblesse de BotHack révélée par 3.6, qui empêchait d'aller plus loin. Elles
sont regroupées par étape du jeu. Le détail et les parties d'origine sont
dans `docs/DEVLOG.md`.

### 7.1 Interface et textes (sans eux, le bot ne comprend pas le jeu)

| écart 3.6 | conséquence observée | correction |
| --- | --- | --- |
| `hello` envoyé avant `init_objects` | tous les objets sont des « strange object » ; le bot pousse des rochers « désirés » | lire `obj_descr[]` statique |
| option `!verbose` : invites raccourcies | 1050 réponses « non » par erreur | garder `verbose` |
| « Current skills » affiché en menu | `#enhance` en boucle | dispatcher les menus affichés |
| menus de conteneur (« Do what with… ») et `#name` | boucles de fouille | traductions `compat36` |
| « Continue eating? » (inverse de « Stop eating? ») | réponse inversée | traduction |
| libellés : « containing N items », « (at the ready) », prix de boutique, globs | objets non parsés, sac jeté | normalisation, libellé brut gardé pour les menus |
| **option `color` absente en headless** | objets sans couleur ; une chaîne de fer `_` prise pour un autel | activer `color` |
| **deux espaces après le point** dans les prompts | « trouble lifting… Continue? » refusé 12 000 fois | normalisation des espaces |
| **« Attach your candles to your candelabrum? »** (3.4.3 : « Attach the… ») | **bougies jamais fixées, invocation impossible** | regex élargie. *Le déclic de l'invocation.* |
| **noms des Plans « Earth/Air/Fire/Water »** (3.4.3 : « End Game ») | **le bot ne savait pas qu'il était sur les Plans** | normalisation. *Le déclic des Plans.* |
| « There is a high altar to… » | le bot quittait l'autel de son dieu | regex |
| autel annoncé en tête de la fenêtre « Things that are here » | autel pris pour du sol ; gravure en boucle | lire les lignes de décor |
| « You harmlessly attack a boulder », « Perhaps that's why you cannot move it », « bottom of the abyss/pit », « welded to your hand », « strange object in water » | boucles d'actions | messages compris ou refus mis en veto |
| « (being donned/doffed) » | armure portée prise pour jetable | normalisation |
| menus de plus de 52 entrées (lettres répétées) | pile du Château jamais ramassée | clés uniques par entrée |
| invite de sol pour manger sans le prix | refus de manger en boutique | comparaison sans prix |
| prompt wizard « adjust? » | héros expulsé de la quête (scénarios) | réponse `y` |

### 7.2 Données du jeu (objets, monstres, prix)

| écart | conséquence | correction |
| --- | --- | --- |
| 16 nouvelles étiquettes de parchemins, livre « leathery » | objets inconnus, puis désirés à l'infini ; `#call` en boucle | données patchées, apparences **exclusives** et **pluriels** |
| roman « paperback book » | case jamais « vidée », fixation | objet ajouté |
| Keystone Kops, Twoflower, guide absents | farlook en boucle, **crash du combat** contre un Kop (hash manquant) | monstres ajoutés, hash de repli |
| minions « renegade X » | farlook en boucle | analyse |
| **prix 3.6.7** (arrondi unique, surtaxe de commerçant fâché), prix de pile divisé deux fois | toutes les identités d'objets éliminées | modèle de prix refait, repli sûr si les faits se contredisent |
| Méduse 3 et 4 | parcours bloqué | reconnaissance des variantes |

### 7.3 Règles et tactiques 3.6

- Elbereth strict, pudding farming retiré, seuil de prière (section 4.3).
- **Tactiques assistées** : pas de fuite (inutile quand on est invincible),
  rhabillage avant combat (un incube déshabillait le héros, qui se battait
  nu 6 000 tours), licorne maudite repérée par défiance.

### 7.4 Faiblesses de BotHack révélées par les parties

| faiblesse | conséquence | correction |
| --- | --- | --- |
| mémoire des monstres oubliée en quittant un niveau | le bot revenait au niveau final de la quête sans rien à traquer | **aller chercher la Cloche et le Chandelier** : retour au niveau du porteur, traque des hostiles, parcours des cases non foulées, portes ; borné |
| handler « combat » toujours prioritaire | sur les Plans et l'Astral, combat sans fin contre la foule | **ruées assistées** : autel sur l'Astral (cases fixes de `astral.des`), portail sur les Plans (logique native BotHack + Amulette portée au cou pour les indices) |
| actions refusées sans tour, redemandées | emballements de requêtes | **veto** |
| ramasser puis jeter, porte secrète supposée, lévitation maudite, jambe blessée à force de coups de pied | boucles longues | mémoires courtes et bornes |
| aucune action proposée | Échap sans fin | **repli « search »**, un tour passe |
| englouti et étourdi | « attendre » en boucle | attaquer l'englouteur |

### 7.5 Performance

La vitesse compte : une ascension demande ~50 000 tours.

| goulot | mesure | correction |
| --- | --- | --- |
| cache d'exploration à entrée unique | 1 680 recalculs par tour | cache **incrémental** : ×50 moins de recalculs |
| identification recalculée | 9 M appels | cache par version des découvertes |
| suivi des monstres (une copie de structures par monstre) | 58 % du temps sur les Plans | écriture groupée : ~10× plus vite sur la Terre |

**Débit** : ~6 tours/s au début, 7 à 17 tours/s par partie ensuite, avec 13
parties en parallèle.

---

## 8. La partie qui a ascensionné

`runs/worker/full-c01/g011/`, seed moteur 8011 ; Valkyrie naine,
loi (Tyr).

| tour | étape |
| --- | --- |
| 226 | Dlvl 2 |
| 497 | Mines |
| 989 | Minetown |
| 1 894 | Oracle |
| 3 713 | Sokoban |
| 5 907 | Dlvl 10 |
| 12 534 | Méduse |
| 12 593 | Château |
| 14 202 | Vallée |
| 16 083 | Quête |
| 23 811 | tour du Sorcier |
| 23 859 | Vlad |
| 25 415 | Chandelier |
| 29 329 | Gehennom profond |
| 35 476 | Cloche |
| 38 047 | Livre des Morts |
| 38 390 | Invocation |
| 38 391 | Sanctuaire |
| 38 806 | Amulette |
| 43 942 | Plans |
| 48 869 | Astral |
| **51 834** | **Ascension** |

Fin : XL 19, 146/161 PV, CA −24, 4 497 576 points.

**Aides** : 506 morts annulées, 3 anti-famine, kit. L'Amulette a été volée
2 fois par le Sorcier et **récupérée** par le bot.

**Preuves** :
- `result.json` : issue `ascended`, verdict moteur `how_s: ascended` ;
- xlogfile : `death: ascended`, `achieve: 0x9ff` ;
- `dumplog.txt` : « when you ascended ».

---

## 9. Où on en est (mesures)

| étape du projet | résultat |
| --- | --- |
| Minetown (20 parties, 2026-09-17) | 18/20 |
| Château (14 seeds, ca-w01 → ca-w06) | 3 → 9/14 |
| big-w01 → big-w10 (32 parties chacune) | Château ~28/32 ; Cloche 11 → 19 ; Livre 5 → 14 |
| **big-w09** (après la correction des bougies) | **5 invocations et Amulettes** (première fois) |
| **big-w10** | 7 Amulettes, **1 partie sur les Plans** |
| scénario `planes` | **2 ascensions** vérifiées |
| **séries continues full-c01** | **1 ascension sur 45 parties** (2,2 %) |
| full-c04 | 25 parties, 1 partie à l'Astral (coupée par la fixation, corrigé) |

**Entonnoir typique** (full-c01, 45 parties) :

| étape | parties |
| --- | --- |
| Château | 37 |
| Livre des Morts | ~10 |
| Amulette | 4 |
| Plans | 1 |
| Astral | 1 |
| Ascension | 1 |

**Principales pertes actuelles** :
- la limite de temps (6 h), car la partie est lente ;
- le vol de l'Amulette par le Sorcier ;
- les Plans, surtout la Terre et l'Air ;
- des fixations et des blocages divers.

---

## 10. Regarder les replays

Toute partie jouée avec `--record` garde `protocol.trace.gz`, c'est-à-dire
**tout** le flux du jeu.

```bash
# convertir en ttyrec, puis regarder comme pour le port BotHack
python3 tools/trace2ttyrec.py runs/replays/g011/protocol.trace.gz runs/replays/g011.ttyrec
ttyplay runs/replays/g011.ttyrec        # '+' / '-' vitesse, espace = pause
```

Un raccourci regroupe la conversion et la lecture : `tools/replay.sh <partie>`
(voir `README.md`).

**Déterminisme** : le rejeu de la seed 8011 retrouve exactement les mêmes
tours d'étape (Dlvl 2 à 226, Mines à 497, Minetown à 989…). Les ascensions
passées sont donc rejouées avec `--record` pour en obtenir le replay.

---

## 11. Leçons de méthode

1. **Supprimer la lecture d'écran** a été le premier gain.
2. **Jouer beaucoup, analyser par classes d'échec, corriger en lot.**
   Chaque cycle de 32 parties montrait 3 à 6 causes distinctes, souvent de
   simples différences de texte.
3. **Les compteurs d'anomalies mentent par omission.** Les 12 000
   « Attach your… » inconnus étaient là depuis des jours, noyés dans les
   fallbacks. Il faut lister les prompts inconnus à chaque cycle.
4. **Instrumenter avant de deviner** : `item_lost` avec messages, diagnostic
   « planes rush idle », `pickup: wanted labels not in the menu`, profils
   cProfile. Chaque ajout a trouvé une cause en un cycle.
5. **Scénarios préparés** pour la fin de partie : 1 heure au lieu de 40 000
   tours.
6. **Occupation du worker** : séries continues, et vérifier le nombre de
   parties en cours à chaque point.
7. **Honnêteté du verdict** : moteur et xlogfile doivent concorder, et les
   scénarios ne comptent jamais comme des parties.
