# MEGA DOC — pybothack : comment on a ascensionné NetHack 3.4.3, et comment transposer ce savoir vers NLE (NetHack 3.6.x)

| | |
| --- | --- |
| **Auteur** | Claude Opus 5 (`claude-opus-5`, Anthropic), via Claude Code |
| **Date** | 2026-09-16 |
| **Périmètre** | `run_06.09.26/new_bothack/claude/` (le port Python) + le NLE local de `run_10.06.26/claude_fable_2/vendor/nle` (NetHack 3.6.7) |
| **Statut** | Document de synthèse et de planification. Les faits sont sourcés (fichier, commande ou ligne de code). Ce qui est une hypothèse est marqué comme telle. |

Ce document fait trois choses, dans l'ordre :

1. **confirmer** (ou non) l'ascension annoncée dans le commit `92b5789` ;
2. **expliquer comment on y est arrivé** : le BotHack original, la méthode du port, les défauts qui ont empêché l'ascension pendant des jours, la campagne qui l'a produite, et *comment le bot gagne* ;
3. **transposer** : ce qui, dans ce savoir, survit au passage à NetHack 3.6.x sous NLE, ce qui casse, où précisément, et un plan pour obtenir **au moins une ascension bot sur NLE**.

Les documents déjà présents (`README.md`, `HANDOFF.md`, `PORT.md`, `TESTS.md`, `RESULTS.md`, `LIMITATIONS.md`, `RUNNING.md`, `VAST.md`, `NETHACK.md`) restent la référence détaillée. **Attention : ils ont été écrits avant l'ascension** et disent encore « no ascension » à plusieurs endroits (`RESULTS.md` §4, `LIMITATIONS.md` dernière section, `README.md`). La section 1 ci-dessous remplace ces affirmations.

---

## Sommaire

- [0. TL;DR](#0-tldr)
- [1. Vérification de l'ascension](#1-vérification-de-lascension)
- [2. Le point de départ : BotHack (krajj7, 2015)](#2-le-point-de-départ--bothack-krajj7-2015)
- [3. Comment le port a été fait](#3-comment-le-port-a-été-fait)
- [4. Du port fidèle à l'ascension : les défauts qui bloquaient](#4-du-port-fidèle-à-lascension--les-défauts-qui-bloquaient)
- [5. Comment le bot gagne : anatomie de `mainbot`](#5-comment-le-bot-gagne--anatomie-de-mainbot)
- [6. Le savoir accumulé, classé par transférabilité](#6-le-savoir-accumulé-classé-par-transférabilité)
- [7. La cible : NLE et NetHack 3.6.x](#7-la-cible--nle-et-nethack-36x)
- [8. Où ça va casser : analyse de risques 3.4.3 → 3.6.x/NLE](#8-où-ça-va-casser--analyse-de-risques-343--36xnle)
- [9. Plan d'action pour une ascension bot sur NLE](#9-plan-daction-pour-une-ascension-bot-sur-nle)
- [10. Annexes](#10-annexes)

---

## 0. TL;DR

- **L'ascension est confirmée, et il y en a deux**, pas une. Deux parties du port Python, jouées le 2026-09-14 sur une machine Vast AI, sans mode wizard, sans mode exploration, sans bones, sans intervention humaine : `vp6` (16 813 686 points, 72 121 tours, 7 h 31) et `vp2` (18 738 500 points, 90 023 tours, 7 h 44). Preuves : la ligne `xlogfile` écrite **par NetHack**, et deux ttyrecs dont le dernier écran est « You ascend to the status of Demigoddess... » sur le Plan Astral, avec des horodatages identiques à la seconde près à ceux du xlogfile.
- **Réserve honnête** : les logs du bot (`run.log`) de la machine Vast n'ont pas été rapatriés. L'attribution au port (et non au BotHack Clojure) repose sur la convention du harnais (`tools/ascend_pool.sh` : préfixe `vp`, `gameN/game.ttyrec`, lancé uniquement avec `python3 -m pybothack.main`), que le harnais de l'original n'utilise pas (il n'écrit pas de ttyrec). C'est solide, mais ce n'est pas la même force de preuve qu'un log. Le dénominateur (combien de parties au total) n'est pas connu non plus : au moins 49 parties lancées.
- **Comment** : un port *fidèle* (1 839 cas différentiels identiques, 1 182 022 octets de frappes identiques sur 15 enregistrements rejoués), **puis** la chasse aux défauts qui n'apparaissent qu'en jouant longtemps. Ce n'est pas la stratégie qui manquait : c'est la robustesse de la synchronisation avec le terminal. 37 % des parties étaient abandonnées par le bot, 92 % au-delà de 3 h de jeu, alors qu'une ascension en demande 7 à 20.
- **Pour NLE / 3.6.x** : la moitié la plus fragile de BotHack (le scraper de terminal) **disparaît** avec NLE, qui donne glyphes, stats et état des prompts directement. C'est le plus gros avantage, devant le kit de départ (GDSM +2). Mais la stratégie qui a gagné repose sur **des mécaniques que 3.6 a cassées** : le pudding farming (plus de death drops sur les clones, XP dégressive) alors qu'il occupe **la moitié des tours** de nos deux ascensions ; Elbereth (texte exact exigé, effacé avec −5 d'alignement si on attaque depuis la case, **inopérant en Géhennom et au Plan Astral**, là même où nos ascensions l'utilisaient) ; le seuil de prière d'urgence (une prière « trop tôt » fâche le dieu) ; et plusieurs blueprints de niveaux (Méduse 3/4 = **50 % des parties**, Orcish Town, quête Valkyrie redessinée). Section 8 : 14 risques chiffrés avec correctif ; section 9 : un plan par étapes avec critères de passage.
- **Précision de version** : il n'existe pas de NLE en 3.6.3. Le NLE de Meta (v0.x–1.1) embarque **3.6.6** ; le NLE maintenu (`NetHack-LE/nle`), celui de `claude_fable_2`, embarque **3.6.7** (`include/patchlevel.h` : `PATCHLEVEL 7`). Les écarts entre 3.6.3, 3.6.6 et 3.6.7 sont des corrections de bugs ; tout ce qui suit vaut pour la série 3.6.x. Toutes les vérifications de code source ont été faites sur le 3.6.7 local.

---

## 1. Vérification de l'ascension

### 1.1 Ce qui a été examiné

| preuve | chemin | écrit par |
| --- | --- | --- |
| xlogfile (2 lignes `death=ascended`) | `artifacts/ASCENSION/tmp/asc.xlog` | NetHack lui-même (`topten.c`) |
| record (tableau des scores) | `artifacts/ASCENSION/tmp/asc.record` | NetHack |
| ttyrec de la partie `vp6` | `artifacts/ASCENSION/artifacts/vast/game30/game.ttyrec` (114,7 Mo, 684 756 trames) | le bot (`--ttyrec`) |
| ttyrec de la partie `vp2` | `artifacts/ASCENSION/artifacts/vast/game49/game.ttyrec` (136,0 Mo, 808 475 trames) | le bot |
| 400 dernières lignes de message | `artifacts/ASCENSION/tmp/asc_toplines.txt` (vp6), `vp2_toplines.txt` | extraction |
| archive d'origine | `artifacts/ASCENSION/ascension.tgz` (contient xlog, record, toplines, ttyrec game30) | machine Vast (fichiers `root`) |

Les ttyrecs ont été rejoués intégralement dans un émulateur de terminal (`pyte`, 80×24) pour lire l'écran final, et pas seulement grepés.

### 1.2 Résultat

| | **vp6** (`game30`) | **vp2** (`game49`) |
| --- | --- | --- |
| xlogfile `death=` | `ascended` | `ascended` |
| points (xlogfile) | **16 813 686** | **18 738 500** |
| tours | 72 121 | 90 023 |
| niveau max atteint (`maxlvl`) | 50 | 48 |
| lieu de fin (`deathdnum=7 deathlev=-5`) | Plan Astral | Plan Astral |
| PV à la fin | 261 (284) | 268 (268) |
| AC / niveau d'XP (écran final) | −15 / XL 25 | −23 / XL 30 |
| durée réelle | 27 110 s = **7 h 31** | 27 845 s = **7 h 44** |
| début → fin (UTC, 2026-09-14) | 09:21:10 → 16:53:01 | 09:30:29 → 17:14:34 |
| 1ʳᵉ trame ttyrec → dernière trame | 09:21:10.11 → 16:53:01.08 | 09:30:29.71 → 17:14:34.49 |
| personnage | Val Dwa Fem Law | Val Dwa Fem Law |
| `flags` | `0x0` | `0x0` |
| dernier message | « You ascend to the status of Demigoddess... » | idem |

**Concordance** : les horodatages de début et de fin des ttyrecs tombent sur la même seconde que `starttime`/`endtime` du xlogfile. Les deux sources sont indépendantes (l'une écrite par NetHack, l'autre par le bot).

**Écran final de vp6**, reconstruit depuis le ttyrec :

```
You ascend to the status of Demigoddess...--More--
...
Vp6 the Heroine St:25 Dx:18 Co:20 In:8 Wi:15 Ch:10 Lawful S:8397168
Astral Plane $:0  HP:261(284) Pw:49(49) AC:-15 Exp:25 T:72121 Satiated
```

(Le score affiché, 8 397 168, est celui d'avant le calcul final ; NetHack double le score d'une ascension et ajoute les bonus, d'où les 16,8 M du xlogfile.)

### 1.3 Décodage des champs (source : `upstream/nh343-nao-build/src/topten.c`)

`flags=0x0` : bit `0x1` = mode wizard, `0x2` = mode exploration, `0x20` = bones chargés. **Aucun n'est levé.** C'est la preuve la plus directe du « sans wizard mode ».

`achieve` (`encodeachieve()`, lignes 1053-1064) :

| bit | signification | vp6 `0xdff` | vp2 `0x9ff` |
| --- | --- | --- | --- |
| 0 | Cloche d'ouverture | ✔ | ✔ |
| 1 | entré en Géhennom | ✔ | ✔ |
| 2 | Candélabre | ✔ | ✔ |
| 3 | Livre des Morts | ✔ | ✔ |
| 4 | invocation effectuée | ✔ | ✔ |
| 5 | Amulette de Yendor | ✔ | ✔ |
| 6-7 | Plans élémentaires / Astral | ✔ | ✔ |
| 8 | ascensionné | ✔ | ✔ |
| 9 | luckstone des Mines | ✘ | ✘ |
| 10 | Sokoban terminé | ✔ | **✘** |
| 11 | Méduse tuée | ✔ | ✔ |

`conduct` (bits inversés = conduites **tenues**) : vp6 `0x480` = jamais polypilé, jamais souhaité d'artefact ; vp2 `0x580` = idem + jamais polymorphé. Les deux ont fait des vœux et des génocides (bits `0x200`/`0x800` absents), ce qui colle à la stratégie (section 5.4).

Détail qui a son importance pour la suite : **vp2 n'a pas l'accomplissement Sokoban** (en 3.4.3-NAO il est levé en ramassant le prix du dernier niveau). Le prix de Sokoban n'est donc pas un passage obligé de cette stratégie.

### 1.4 Est-ce bien le port Python, et pas BotHack Clojure ?

Arguments pour :

- `tools/ascend_pool.sh` (le seul harnais du dépôt qui produit `OUT/gameN/game.ttyrec` avec des noms `PREFIX<slot>`) lance exclusivement `python3 -m pybothack.main config/play-config.edn ... --ttyrec "$d/game.ttyrec"`. Il s'arrête sur le premier `death=ascended` du xlogfile, ce qui colle avec deux ascensions presque simultanées récupérées ensemble.
- `tools/ascend_pool_orig.sh` (harnais de l'original) utilise le préfixe `orig`, écrit `nh.sh`/`config.edn`/`bothack.log` par partie, **et aucun ttyrec** (vérifié sur `artifacts/orig_run/game1`).
- Les noms `vp2`/`vp6` = préfixe `vp` + slots 2 et 6 ; `game30`/`game49` = index de partie du pool, un format propre à ces harnais.
- Le commit `92b5789` (« pybothack ascended successfuly ») ajoute, en plus des preuves, les deux derniers correctifs du port (`scraper.py` borne `lastmsg`, `pathing.py` `_tile_member`) et les outils de relecture `tools/watch_ascension.sh` / `tools/replay_ascension.py`.

Ce qui manque pour une preuve complète :

- le `run.log` / `stdout.log` des parties Vast (non rapatriés) ;
- le hash du commit exécuté sur Vast (le pool l'affiche au démarrage, `port commit ...`, mais ce log n'est pas dans le dépôt) ;
- le nombre total de parties jouées par le pool (au moins 49 lancées ; combien terminées est inconnu).

**Verdict** : ascension confirmée par NetHack lui-même ; attribution au port Python très probable et cohérente avec tout ce que contient le dépôt, sans être attestée par un log du bot. Si la machine Vast existe encore, rapatrier `OUT/game30/run.log` et `OUT/game49/run.log` fermerait la question. Les docs `RESULTS.md` §4, `LIMITATIONS.md` (« The big one: no ascension ») et `README.md` (« The port has not ascended ») sont désormais **obsolètes sur ce point**.

### 1.5 Comment revérifier soi-même

```bash
cd run_06.09.26/new_bothack/claude
cat artifacts/ASCENSION/tmp/asc.xlog                      # écrit par NetHack
tools/watch_ascension.sh                                   # liste les ascensions
tools/watch_ascension.sh 1 -s 200                          # rejoue en ~2 min
python3 tools/replay_ascension.py artifacts/ASCENSION/artifacts/vast/game30/game.ttyrec --fin
```

---

## 2. Le point de départ : BotHack (krajj7, 2015)

### 2.1 Ce qu'est BotHack

Un framework de bot NetHack en Clojure (JVM) de Jan Krajíček, avec un bot principal, `mainbot`, qui est **le premier bot à avoir ascensionné NetHack sans mode wizard** (25 janvier 2015, sur nethack.xd.cm). Source étudiée : `github.com/krajj7/BotHack`, commit `70226b3` (copie locale : `/home/roro/nhwork/bothack-src`).

Chronologie tirée du README de l'original, utile parce qu'elle montre **dans quel ordre les capacités ont été nécessaires** :

| date | jalon |
| --- | --- |
| 2014-03 | émulateur de terminal, dialogue avec le menu de nethack.alt.org |
| 2014-04 | synchronisation avec NetHack résolue (« only hinted at on the TAEB blog ») |
| 2014-06 | navigation jusqu'à Minetown/Oracle, portes cachées ; en wizmode jusqu'à Méduse |
| 2014-07/08 | tous les monstres et objets reconnus ; farlook automatique des ambiguïtés |
| 2014-09/10 | actions sur objets, pioche/lévitation dans le pathfinding ; **ascension en wizmode** avec équipement fourni |
| 2014-11 | bot non-wizmode : Excalibur, vol d'armures aux nains, Elbereth |
| 2014-11 | identification par prix/gravure (core.logic) |
| 2014-12 | solveur Sokoban ; bot au Château, quête, Vlad, mort face à Demogorgon |
| **2015-01-25** | **pudding farming implémenté → première ascension non-wizmode** |
| 2015-06 | Junethack : Samouraï et Chevalier ascensionnés par des versions modifiées |

La phrase clé est celle de janvier 2015 : l'ascension est arrivée **quand le farming a été ajouté**. C'est exactement la mécanique que NetHack 3.6 a supprimée (section 8, R1).

### 2.2 La cible historique

BotHack ne supporte que **NetHack 3.4.3 avec le patchset nethack.alt.org (NAO)** (`doc/compiling.md` de l'original). Le port utilise le même jeu, reconstruit par `tools/build_nethack343_nao.sh` depuis le miroir `github.com/neoascetic/nh343-nao` (commit `d643449`), le dépôt d'alt.org n'existant plus. Détails et vérifications : `docs/NETHACK.md`.

Deux dépendances fortes à cette version, qui comptent pour la transposition :

- `bothack.nethackrc` **remappe l'affichage** pour qu'il soit non ambigu pour un scraper (portes fermées `]`, pièges tous `^`, rochers `8`, lettres de monstres réassignées, etc.) ;
- le bot dépend de messages propres à NAO, par exemple « It's a wall. » (`msg_wall_hits`) pour cartographier les murs invisibles.

### 2.3 La mission donnée aux agents

Texte de `run_06.09.26/new_bothack/codex/PROMPT.md` (la même mission a été confiée à plusieurs agents : `claude`, `codex`, `codex_2`, `codex_3`, `opencode`, `openrouteur`) :

> Réécris entièrement le bot et son moteur en Python, fidèlement aux règles, stratégies, données et comportements originaux, sans déléguer les décisions au code Clojure/Java. Vérifie cette fidélité par des tests comparatifs avec l'original et des parties réelles sans mode wizard ni intervention humaine, jusqu'à obtenir une ascension.

Le port de `claude/` est celui qui a abouti.

---

## 3. Comment le port a été fait

### 3.1 Architecture : un module Python par namespace Clojure

~14 500 lignes de Python (`pybothack/`), en miroir exact de l'original (~17 000 lignes de Clojure), noms de fonctions conservés (`kebab-case` → `snake_case`) pour lire les deux côte à côte. Table complète : `docs/PORT.md`.

```
pybothack/
  iface.py      pty local / telnet + écriture ttyrec          (jta.clj, ttyrec.clj)
  term.py       émulateur vt (pyte), lectures de 256 octets   (term.clj / JTA vt320)
  scraper.py    machine à états de synchronisation            (scraper.clj)
  delegator.py  bus d'événements + sémantique d'agent Clojure (delegator.clj)
  frame.py, tile.py, level.py, dungeon.py, position.py, fov.py
  monster.py, montype.py, item.py, itemtype.py, itemid.py, player.py, game.py
  pathing.py    A*/Dijkstra avec le coût et les départages d'origine (1 613 l.)
  actions.py    toutes les actions et leurs handlers de messages (1 942 l.)
  sokoban.py    solutions extraites
  behaviors.py, handlers.py, bothack.py, main.py
  bots/mainbot.py   la stratégie qui ascensionne (2 960 l.)
  clj.py        émulation des sémantiques Clojure (maps, sets, hash)
  _data.json, _leveldata.json, _hashdata.json   données extraites de la JVM
```

Non porté : l'API Java, `wizbot`, `simplebot`, le bot de menu dgamelaunch.

### 3.2 Données extraites, jamais retapées

`tools/cljdump/dumpdata.clj` s'exécute **dans** le projet original et sérialise ses propres structures : 1 722 types d'objets, 376 types de monstres, les blueprints de niveaux spéciaux, les solutions Sokoban, l'ordre d'énumération core.logic des apparences. Rien des 3 675 lignes d'`itemdata.clj` n'a été recopié à la main, donc rien ne peut dériver.

> **Transposable tel quel vers NLE** : cette idée. Les tables 3.6 doivent être extraites de la même façon, mais **depuis les sources C de 3.6.7** (`src/objects.c`, `src/monst.c`, `dat/*.des`), pas depuis BotHack.

### 3.3 Le plus dur : les sémantiques Clojure que Python n'a pas

Tous les bugs de fidélité trouvés sont de la même espèce. La liste (détails dans `HANDOFF.md` §4.4 et `PORT.md`) :

- `(into {} …)` ajoute en fin et passe en hash-map à la **9ᵉ** entrée ; une chaîne d'`assoc` **préfixe** et passe à la **10ᵉ**. Même séquence d'insertion, ordre d'itération opposé. Modélisé par `clj.CljMap`.
- L'ordre d'itération d'un `PersistentHashSet` décide des lettres envoyées dans un menu et du monstre que `fight` attaque. Le `hasheq` Clojure (Murmur3, décalage **arithmétique** dans `hashCombine`, champs de record omis matérialisés à nil) est réimplémenté et vérifié contre un dump JVM.
- Une `String` d'un caractère n'est pas un `Character` et ne hache pas pareil.
- `min-key`/`max-key` gardent le **dernier** extrême en cas d'égalité.
- `(if-let [{:keys [step]} (navigate …)] …)` teste le **Path**, pas le `step`.
- Un `(if …)` qui est une clause d'un `or` et renvoie une valeur vraie court-circuite le `or` : le scraper original attend **une trame de plus**.
- `{:pre …}` lève une `AssertionError` (une `Error`, pas une `Exception`) qui **traverse** le `catch Exception` du délégateur.
- Deux bugs d'origine où un **atom** est passé à la place de la map (`Throw`, `Discoveries`) : reproduits volontairement.

> **Pour NLE, ce paragraphe entier devient sans objet** si on ne cherche plus l'identité octet par octet avec l'original. C'était le prix de la preuve de fidélité, pas celui de l'ascension. On garde les *décisions*, pas les accidents de hachage.

### 3.4 Le banc de fidélité, en trois étages

1. **Tests différentiels** (`tests/test_differential.py` + oracle Clojure `tools/cljcmp/oracle.clj`) : l'original tourne en sous-processus et répond aux mêmes questions que le port. **1 839/1 839** cas identiques (parsing d'objets, identification, monstres, status line, FOV, navigation, nourriture, 51 situations de combat, 60 scénarios Excalibur, 25 ordres de menus, `farm-done?`).
2. **Rejeu** : une partie de l'original est enregistrée (`tools/pty_tap.py`), puis rejouée dans le port ; on compare les frappes envoyées. **15 enregistrements, 1 182 022 octets, 1 182 022 identiques, zéro divergence** (6 parties complètes en PASS_COMPLETE). Revalidé après les derniers correctifs : 13/15 captures, 842 549/842 549 octets.
3. **Jeu comparé en direct** (`tools/live_compare.sh`) : les deux bots sur la même partie seedée.

Pour que la comparaison ait un sens, **tout ce qui n'est pas le bot a dû être rendu déterministe** — c'est ce qui a coûté le plus :

- **RNG de NetHack** : le patchset NAO re-seede le RNG toutes les 10 à 710 tirages. `tools/det_rng.c`, chargé en `LD_PRELOAD`, ne laisse passer que le premier `srandom()`. Binaire et règles inchangés.
- **Départage des handlers de l'original** : priorités égales départagées par des hash d'identité JVM, différents à chaque lancement ; le harnais épingle l'ordre d'enregistrement.
- **Frontières de trames** : le tap détecte que NetHack est bloqué dans `read()` (`/proc/<pid>/syscall`) et découpe là.
- **Le `future` du cache d'exploration** de l'original et la coalescence de trames par le lecteur JVM (`PTY_TAP_PIECE_DELAY=0.02`).

Boucle d'itération : enregistrer une fois (cher, JVM), rejouer après chaque correctif (46 Mo, sans JVM, quelques minutes).

### 3.5 Leçons de méthode qui valent pour la suite

Elles sont écrites dans les docs existants, mais ce sont les plus transférables de tout le projet :

1. **Faire confiance à la trace vivante plutôt qu'au code et aux tests.** La suite différentielle passait à 1 821/1 821 pendant que le port construisait l'inventaire dans le mauvais ordre : le cas de test ne reproduisait pas le vrai chemin de code.
2. **Tracer l'écrivain d'un état, pas ses lecteurs.** Seize causes éliminées en mesurant des lecteurs ; deux lignes de trace sur l'écrivain ont nommé le bug.
3. **Une sauvegarde qui n'a jamais été vue se déclencher n'est pas une sauvegarde.** La borne `LASTMSG_WAIT_LIMIT` était documentée comme protection pendant deux jours et n'avait jamais tiré une seule fois (section 4).
4. **Un compteur par état n'a pas de sens si l'état est réentrant** : il faut une horloge.
5. **Une courte fenêtre d'observation n'est pas un état permanent.** L'« oscillation » de lévitation au Château, prise pour une boucle, était la manœuvre correcte.
6. **Les toplines et les transitions de niveau sont fiables ; les comptes de mots-clés dans des logs qui contiennent des dumps d'état ne le sont pas.**
7. **Éditer un fichier source n'atteint pas un interpréteur déjà lancé.**
8. **Un test écrit depuis le port au lieu de l'original affirme le bug.** `test_idle_recovery.py` affirmait l'inverse de l'original sur deux points et passait pendant que 17 parties étaient perdues.
9. Pièges d'exploitation : `pkill -f` se tue lui-même ; ne jamais éditer un script bash en cours d'exécution ; noms de joueur distincts par slot sinon les parties s'effacent leurs niveaux ; `:no-exit true` désactive toute récupération.

---

## 4. Du port fidèle à l'ascension : les défauts qui bloquaient

Le point le plus important de toute l'histoire : **le rejeu à 100 % ne voyait aucun de ces défauts**, parce que les parties enregistrées de l'original (2 300 à 2 800 tours) n'atteignent jamais les états qui les déclenchent. Une ascension, c'est 70 000 à 90 000 tours et 7 h 30 de jeu. Tous ont été trouvés **en jouant**.

| # | défaut | symptôme | coût mesuré |
| --- | --- | --- | --- |
| 1 | `quit-when-idle` non porté | deadlock sur « In what direction do you want to dig? », partie figée | 1 partie sur 5 du premier lot |
| 2 | timeout de lecture de 180 s inventé par le port | tuait le bot **pendant qu'il réfléchissait** | 7 parties sur 16, la meilleure à Dlvl 15 |
| 3 | `quit-when-stuck` retournait au lieu de quitter | exception, meilleure partie (Dlvl 28, 6,9 M points) perdue | — |
| 4 | `unpause` confondu avec l'utilitaire REPL `u` : **les 4 ESC n'étaient jamais envoyés** | le « déblocage » écrivait `#` et ne débloquait rien | **17 parties**, jusqu'à Dlvl 18 |
| 5 | `montype['name']` au lieu d'un accès nil-safe | `TypeError` avalé, farlook ignoré | 3 002 occurrences |
| 6 | seuil inventé dans `farm_done` (`score > 10 M et tour > 75 000`) | décision de jeu non conforme | 1 partie arrêtée à 7 tours du seuil |
| 7 | clause en trop dans `castle-plan-b` | plan B du Château déclenché à tort | — |
| 8 | **borne `lastmsg` jamais déclenchée** (compteur remis à zéro à chaque tour du protocole ctrl-P) | bot bloqué à attendre une trame que NetHack n'enverra jamais | **37 % des parties abandonnées ; 92 % au-delà de 3 h**. A tué `pool_f/game2` à **Dlvl 40 en Géhennom, PV 230/230, après 9 h 20** |
| 9 | `set()` sur des dicts dans `_switch_dlvl` (`TypeError: unhashable type: 'dict'`) | crash sur le niveau de la quête avec le leader à saluer | une partie de 4 h 22 à Dlvl 29 **et dix autres, toujours les longues** |

Les correctifs 8 et 9 sont ceux du commit final. Le 8 (`scraper.py`) : le compteur n'est remis à zéro que sur une sortie normale vers `sink`, et une **borne en temps réel** de 20 s (`LASTMSG_WAIT_SECONDS`) s'ajoute à la borne en nombre de trames, testée par `tests/test_lastmsg_bound.py` qui la regarde vraiment se déclencher. Le 9 (`pathing.py`, `_tile_member`) reproduit la sémantique Clojure « un set utilisé comme prédicat teste l'appartenance par égalité structurelle ».

**Ce que ça dit pour la suite** : le critère de validation fixé le 12/09 était « une partie qui passe six heures sans abandon ». Deux jours plus tard, deux parties dépassaient 7 h 30 **et ascensionnaient**. Autrement dit, une fois le bot capable de *survivre au temps*, la stratégie de 2015 suffisait. **Sur NLE, cette classe entière de défauts (1, 2, 4, 8) n'existe pas**, parce qu'il n'y a plus de terminal à synchroniser (section 7.3).

### 4.1 La campagne qui a produit l'ascension

- Harnais : `tools/ascend_pool.sh OUT SLOTS vp` — N slots en parallèle, une nouvelle partie démarre dès qu'un slot se libère (contrairement à `ascend_batch.sh` qui attend la vague entière, et laissait 5 slots sur 6 inactifs pendant qu'une partie farmait 3 h), arrêt sur le premier `death=ascended` du xlogfile.
- Config : `config/play-config.edn` (**sans** `:no-exit`, donc récupérations actives).
- Machine : Vast AI (`tools/vast/provision.sh`, `worker.sh`, `collect.sh`). Le port consomme ~100 Mo par partie et joue ~15,7 tours/s.
- Vitesse mesurée sur les ascensions : 72 121 tours en 27 110 s = **2,66 tours/s** en moyenne (le farming et les combats de fin de partie sont beaucoup plus lents que l'exploration du début).

---

## 5. Comment le bot gagne : anatomie de `mainbot`

Source : `bots/mainbot.clj` (2 388 lignes) / `pybothack/bots/mainbot.py`.

### 5.1 Une pile de handlers par priorité

À chaque tour, le délégateur interroge les handlers dans l'ordre de priorité ; **le premier qui renvoie une action gagne**. C'est toute l'architecture de décision (fonction `init`) :

| prio | handler | rôle |
| --- | --- | --- |
| −99 | `offer-amulet` | offrir l'Amulette sur l'autel coaligné (Astral) |
| −16 | `enhance` | #enhance dès que possible |
| −15 | `name-first-amulet` | nommer la première amulette ramassée (fausses Amulettes) |
| −13 | `handle-drowning` | se sortir de l'eau / étranglement |
| −11 | `handle-starvation` | manger, prier si Weak/Fainting |
| −10 | `detect-portal` | repérer les portails (quête, Ludios) |
| −9 | `handle-illness` | maladie, pétrification, visqueux, lycanthropie |
| −8 | `farm` | le pudding farming, une fois lancé |
| −7 | `retreat` | PV bas : prier, Elbereth, fuir à l'escalier |
| −6 | `fight` | combat |
| −5 | `cursed-levi` | se débarrasser d'une lévitation maudite |
| −4 | `kill-medusa` | tuer Méduse (aveuglé) si pas de réflexion |
| −3 | `handle-impairment` | confusion, étourdissement, cécité, hallucination |
| −2 | `fight-covetous` | monstres qui veulent l'Amulette / le Sorcier |
| −1 / 0 | `reequip` / `reequip-weapon` | meilleur équipement |
| 1 | `feed` | manger des cadavres sûrs et utiles |
| 2-6 | `consider-items-here`, `recover`, `examine-containers*`, `consider-items` | objets, repos |
| 7-8 | `use-items`, `random-unihorn` | utiliser ce qu'on a |
| 9 | `hunt` | chasser le Sorcier qui a volé quelque chose |
| 10-13 | `itemid`, `use-features`, `shop`, `bag-items` | identification (prix, gravure), fontaines/éviers/trônes, boutiques, sac |
| 15 | `get-protection` | acheter la protection au prêtre |
| 16 | `excal-handler` | tremper pour Excalibur (XL ≥ 5) |
| 17 | `rob-peacefuls` | tuer les nains pacifiques armés (pioche, mithril) |
| 18 | `init-farm?` → `farm-init` | préparer la ferme |
| 19 | `progress` | l'avancée dans le donjon |

> **Transposable tel quel** : cette table *est* le savoir stratégique de BotHack sous sa forme la plus compacte. Elle ne dépend presque pas de la version.

### 5.2 L'ordre de progression (`full-explore`)

```
tant que le Sanctuaire n'est pas connu :
  1. Minetown (Mines)
  2. Sokoban (repérer) ; le résoudre si on a Excalibur et de quoi lancer
  3. repérer le portail de la quête
  4. le bout des Mines, si pas sous Méduse et (clé ou pas la variante Grotto) et (AC > −7 ou pas de pioche/clé)
  5. descendre jusqu'à Dlvl 20, sauf si farm-done? ou sous Méduse
  6. castle-plan-b (lévitation, génocide des ; et anguilles, réflexion)
  7. le Château, si (AC < −7 ou pas de DSM ou pas de génocide ;) et baguette de frappe
  8. le bout de la quête, si lévitation + XL ≥ 14 + DSM
  9. Vlad → bas du Géhennom → tour du Sorcier → invocation
puis : l'Amulette → Plans → autel du haut
```

### 5.3 Le cœur de l'ascension 3.4.3 : le pudding farming

Conditions d'entrée (`init-farm?`) : pas `farm-done?`, XL ≥ 7, Sokoban fini, parchemin d'identification connu, pioche, licorne, clé/crochet, **baguette de feu ou de foudre** (Elbereth permanent), > 2 000 de nutrition, **parchemin de terre**.

Mise en place (`farm-init`) : aller au **niveau de l'évier**, creuser un carré 9×9 autour, se placer à côté de l'évier, lire le parchemin de terre (rochers autour), graver `Elbereth*` au feu. Les puddings (noirs/bruns) se divisent quand on les frappe avec du fer ; chaque clone tué rapporte XP, score **et un death drop aléatoire**. Le bot frappe depuis son carré Elbereth, laisse les puddings « guérir » pour les refaire se diviser, alterne arme (clé en fer / Excalibur au moment de récolter).

Sortie (`farm-done?`) :

```
branche wiztower connue
OU score > 15 000 000
OU (score > 6 000 000 ET (≥ 3 vœux OU (lévitation/speed boots, MR ou génocide L, réflexion, AC < −10))
                       ET sac ET ≥ 6 remove curse ET identify ET (bougies OU Château pas encore vu))
```

Ce que la ferme apporte vraiment, et qu'il faudra **remplacer** en 3.6 :
1. **les niveaux d'XP** (XL 25 et 30 à la fin de nos deux parties) ;
2. **le score** comme horloge de sortie (15 M / 6 M) ;
3. **les objets** : parchemins de remove curse, d'identify, bougies, anneaux, baguettes, armures — tout vient des death drops ;
4. **le temps** : la ferme occupe une grande partie des 72 000 à 90 000 tours.

### 5.4 Les vœux (`wish`)

Ordre de priorité (le premier qui s'applique) :

1. si on vient de tester une baguette par gravure : `2 blessed scrolls of charging`
2. sous Méduse sans lévitation : `blessed ring of levitation`
3. sous Méduse sans génocide `;`/anguille : `2 blessed scrolls of genocide`
4. pas de DSM ni de cape de MR : `blessed greased +3 gray dragon scale mail`
5. pas de DSM : `blessed greased +3 silver dragon scale mail`
6. DSM sans réflexion : `blessed greased fixed +3 shield of reflection`
7. remove curse si besoin ; génocides `L` et `;` ; 7 bougies de cire sous Méduse ; speed boots ; génocide mind flayers ; helm of telepathy ; wand of death ; génocide `R`/disenchanter ; réflexion ; enchant armor ; amulette de vie ; puis cycle vie/mort/enchant.

**Avec le kit NLE (GDSM +2 bénie graissée), les points 4 et 5 sont déjà acquis** : le premier vœu du Château passe directement à la réflexion (point 6), ce qui résout d'emblée le problème de Méduse (R3).

### 5.5 La fin de partie (vérifiée dans nos parties)

- Château : baguette de vœux dans le coffre, rechargée (`pool_f/game2` : 16 vœux avec deux recharges), puis **chute volontaire par la trappe** du Château sous lévitation contrôlée (retirer l'anneau au bon moment).
- Vallée des Morts, Géhennom, Juiblex (mis en fuite), Vlad (cloche), tour du Sorcier (livre), bas du Géhennom, invocation, Amulette, Plans.
- Plan Astral : dans les 400 dernières lignes de vp6, **Elbereth est gravé 12 fois et 24 monstres « turn to flee »** (titanothère, baluchithérium, dragon rouge, titan, xorn...). C'est un détail décisif pour 3.6 (R2).

### 5.6 Chronologie reconstruite des deux ascensions

Reconstruite en rejouant les deux ttyrecs dans `pyte` et en lisant la status line et la topline toutes les 50 trames (script ad hoc, non versionné ; les tours marqués ~ sont approximatifs à quelques centaines près). Temps = heures depuis la première trame.

**vp6** (72 121 tours, 7 h 31)

| temps | tour | score affiché | événement |
| --- | --- | --- | --- |
| 0,18 h | 4 721 | 8 351 | **Excalibur** (bénie, rustproof +2), trempage dès XL 5 |
| 0,6 h | 11 525 | 35 139 | portail de la quête repéré (Dlvl 11) |
| 0,6-0,9 h | 11 600-17 400 | → 66 000 | allers-retours Dlvl 2-13 (Mines, Sokoban, objets) |
| **0,9-1,6 h** | **17 442-~53 300** | **66 360 → 6 925 842** | **ferme à puddings noirs, Dlvl 9** ; Excalibur +6 et un parchemin de génocide en cours de route |
| 1,6-2,0 h | 53 300-55 400 | 6,93 M → 7,02 M | descente Dlvl 10 → 29 |
| 2,33 h | 56 770 | 7 096 074 | **baguette de vœux** du Château, premier vœu |
| 2,7-2,9 h | 58 190-59 039 | 7,14 M → 7,19 M | quête (Home 1 → 5 et retour) |
| 3,0 h | 59 562 | 7 202 036 | Dlvl 30, entrée en Géhennom |
| 4,0 h | 62 635 | 7 456 132 | **Cloche d'ouverture** (Vlad) |
| 4,1-6,1 h | 62 973-67 019 | → 7,75 M | Dlvl 41-49, tour du Sorcier, Livre des Morts |
| 6,1 h | 67 019-67 025 | 7 752 732 | **Candélabre allumé, invocation**, Dlvl 50 (Sanctuaire) |
| 6,25-7,39 h | 67 807-71 254 | 7,89 M → 8,16 M | remontée Dlvl 50 → 1 avec l'Amulette (3 400 tours) |
| 7,39 h | 71 262 | 8 156 832 | Plans élémentaires |
| 7,42 h | 71 559 | 8 212 584 | Amulette nommée « REAL » après vérification |
| 7,50 h | 72 025 | 8 325 076 | Plan Astral |
| 7,53 h | 72 121 | 8 397 168 | offrande à Tyr, **ascension** |

**vp2** (90 023 tours, 7 h 44)

| temps | tour | score affiché | événement |
| --- | --- | --- | --- |
| 0,35 h | 8 399 | 28 820 | Excalibur (+1) |
| **0,93-2,2 h** | **19 327-~68 300** | **94 280 → 7 662 046** | **ferme à puddings noirs, Dlvl 8** ; Excalibur +6, 4 parchemins de génocide ensachés, génocides pendant la ferme |
| 2,2-2,6 h | 68 300-70 900 | → 7,74 M | descente Dlvl 9 → 28 |
| 3,14-3,34 h | 73 240-74 270 | 7,85 M → 7,90 M | quête (Home 1 → 5 et retour) |
| 3,47 h | 75 288 | 8 008 522 | **baguette de vœux** du Château |
| 3,75 h | 76 482 | 8 089 610 | Dlvl 31, Géhennom |
| 5,35 h | 81 503 | 8 410 492 | combat contre Vlad (« Vlad the Impaler zaps a wand of striking! ») |
| 6,96-7,15 h | 85 741-86 540 | 8,81 M → 8,88 M | « A mysterious force momentarily surrounds you » : remontée avec l'Amulette |
| 7,60 h | 88 482 | 8 973 100 | Plans élémentaires |
| 7,71 h | 89 827 | 9 185 488 | Plan Astral |
| 7,74 h | 90 023 | 9 359 500 | **ascension** |

**Ce que ces chronologies apprennent**

1. **La ferme est la moitié de la partie** : ~36 000 tours (50 %) pour vp6, ~49 000 (54 %) pour vp2, et 82-99 % du score affiché. Elle se fait tôt (Dlvl 8-9, vers le tour 17-19 000, après Excalibur, et après que le bot juge Sokoban terminé, condition de `init-farm?`).
2. **Le chemin de fin est rapide en tours et lent en temps réel** : de la baguette de vœux à l'ascension, ~15 350 tours pour vp6 et ~14 700 pour vp2, mais **5 h 12 et 4 h 16** de temps réel. C'est là que se situent les décisions coûteuses (et c'est là que les blocages de scraper tuaient les parties avant le correctif n° 8).
3. **Ordre réel** : Excalibur → Mines/Sokoban → ferme → descente → Château (vœux) → quête → Géhennom → Vlad → tour du Sorcier → invocation → remontée → Plans. Le Château vient avant la quête dans vp6 et après dans vp2 : `full-explore` est un ordre de préférence, pas un script.


---

## 6. Le savoir accumulé, classé par transférabilité

On peut ranger tout ce que contient le dépôt en quatre couches. La couche détermine ce qu'on fait en passant à NLE.

| couche | contenu | vers NLE 3.6.x |
| --- | --- | --- |
| **A. Stratégie** (indépendante de la version) | table des handlers, ordre de progression, liste d'équipement désiré, liste de vœux, logique de retraite, choix de nourriture, logique d'identification (prix, gravure, élimination), pathfinding avec coûts (portes, pièges, rochers, pioche, lévitation), solveur Sokoban, stratégie du Château, invocation, offrande | **réutiliser**, en retirant les dépendances de B |
| **B. Règles du jeu** (dépendantes de la version) | Elbereth, farming, seuils de prière, blueprints de niveaux spéciaux, chaînes d'objets, messages, prompts, variantes de Minetown/Méduse/Bigroom, formules d'XP | **réauditer une par une contre les sources 3.6.7** (section 8) |
| **C. Interface** | scraper ctrl-P/`##'`, émulateur vt, `bothack.nethackrc` et son remappage de symboles, farlook systématique des ambiguïtés, récupérations idle/stuck | **remplacer** par les observations NLE (section 7.3) |
| **D. Méthode** | harnais différentiel, rejeu déterministe, pool à slots, xlogfile comme vérité, leçons de la §3.5 | **réutiliser** ; NLE rend le déterminisme beaucoup plus simple (`set_initial_seeds`) |

La conséquence pratique : **ne pas re-porter pybothack à l'identique sur NLE**. Garder A et D, réécrire C comme un adaptateur, patcher B.

---

## 7. La cible : NLE et NetHack 3.6.x

### 7.1 Quelle version exactement

| NLE | NetHack embarqué | remarque |
| --- | --- | --- |
| `facebookresearch/nle` v0.x → 1.1 | **3.6.6** | NetHack Challenge (NeurIPS 2021), jeux de données NLD |
| `NetHack-LE/nle` (maintenu) | **3.6.7** | celui de `run_10.06.26/claude_fable_2/vendor/nle`, commit `2319f29` |

Aucune version de NLE n'utilise 3.6.3. La série 3.6.x partage les règles décrites ici (les `.des` de 3.6.7 portent des dates 2018-2019, branche 3.6.2-beta). Si c'est bien le NLE maintenu qui sert (c'est le cas dans le dépôt), c'est **3.6.7**.

### 7.2 Ce qu'on a déjà sur NLE dans ce dépôt

- `run_10.06.26/claude_fable_2/patches/nle-367-minetown.patch` : ajoute à la Valkyrie une **gray dragon scale mail +2, bénie, graissée** (`src/u_init.c`) et un bit privé `internal[9] = in_town` pour l'évaluateur.
- `claude_fable_2/minetown2/` : un agent symbolique Valkyrie → Minetown. Ses résultats (`runs/iter-00x/summary.json`, 20 à 24 parties par itération) : **1 à 7 succès par lot de 20 à 24 parties** ; causes d'échec dominantes : `step_timeout`, `blocked_or_stuck`, famine, **tués par des commerçants**, lycanthropie. Toutes sont des choses que BotHack sait déjà gérer (paiement/évitement des commerçants, pacifiques, choix de nourriture, maladie). C'est l'argument le plus concret pour réutiliser la couche A.
- Protocole compté du dépôt : `val-dwa-fem-law`, `wizard=False`, pas de seed, pas de bones, familier standard.

**Heureuse coïncidence** : BotHack joue exactement ce personnage (`"nvd"` = naine valkyrie, qui est forcément loyale et, dans ses parties, féminine). Tout le savoir de la quête Valkyrie, d'Excalibur et des Mines pacifiques pour un nain s'applique sans changement de rôle.

### 7.3 Ce que NLE remplace dans BotHack (couche C)

| besoin de BotHack | solution 3.4.3/pty | équivalent NLE |
| --- | --- | --- |
| savoir quand NetHack attend une entrée | protocole ctrl-P + `##'`, machine à états `scraper.py` (832 l.), bornes, `quit-when-idle` | **implicite** : `step()` rend la main quand NetHack attend une touche |
| quel prompt est ouvert | regex sur la topline et la position du curseur | `misc = [in_yn_function, in_getlin, xwaitingforspace]` + `tty_chars` |
| carte | parsing des caractères + couleurs, `nethackrc` remappé | `glyphs` (21×79) : **un identifiant unique par monstre/objet/décor** |
| identité des monstres ambigus | farlook `;` systématique (10 % des actions de l'original) | le glyphe donne l'espèce ; farlook seulement pour pacifique/apprivoisé/invisible |
| status line | regex sur 2 lignes | `blstats` (27 champs numériques) |
| inventaire | écran `i` parsé | `inv_letters`, `inv_oclasses`, `inv_strs`, `inv_glyphs` à chaque pas |
| message | topline + `--More--` | `message` + `xwaitingforspace` |
| ttyrec | filtre JTA / `iface.Ttyrec` | natif (`ttyrec.bz2`) |
| déterminisme pour le débogage | `det_rng.c` en `LD_PRELOAD` | `nle.nethack.Nethack.set_initial_seeds(core, disp, reseed=False)` (+ `get_current_seeds()` pour rejouer) |

Tous les défauts n° 1, 2, 4 et 8 de la section 4, qui ont coûté des centaines d'heures de jeu, **n'ont pas d'équivalent**. Le défaut 5 (farlook qui échoue) est largement évité par les glyphes.

---

## 8. Où ça va casser : analyse de risques 3.4.3 → 3.6.x/NLE

Méthode : chaque risque est vérifié **dans le code source 3.6.7** du NLE local (`vendor/nle/src`, `dat`, `doc/fixes36.*`) et comparé à la source 3.4.3-NAO (`upstream/nh343-nao-build`) et au code de BotHack. Gravité : 🔴 bloque l'ascension, 🟠 la rend beaucoup moins probable, 🟡 gêne.

### Vue d'ensemble

| # | risque | gravité | où dans BotHack |
| --- | --- | --- | --- |
| R1 | Pudding farming inopérant | 🔴 | `farm`, `init-farm?`, `farm-done?`, `full-explore` |
| R2 | Elbereth : règles 3.6 et inutile en Géhennom/Plans | 🔴 | `engrave-e`, `retreat`, `fight`, `recover` |
| R3 | Méduse : variantes 3 et 4 non reconnues (50 % des parties) | 🔴 | `dungeon.clj` (reconnaissance), `kill-medusa`, `medusa-spot` |
| R4 | Prière : nouveau seuil de « PV critiques » | 🔴 | `pray-for-hp`, `handle-starvation` |
| R5 | Chaînes d'objets : `(at the ready)`, `(in quiver pouch)` | 🟠 | `item.clj` / `ITEM_RE` |
| R6 | Orcish Town (1 Minetown sur 7) | 🟠 | `get-protection`, `shop`, bougies, repli Excalibur |
| R7 | Quête Valkyrie redessinée | 🟠 | blueprints `quest Home 1..6`, `hit-surtur` |
| R8 | Autres niveaux modifiés (Baalzebub, Juiblex, Air, Wizard3, Ludios, Bigroom 6-10) | 🟡→🟠 | blueprints, reconnaissance |
| R9 | Prompts et messages 3.6 | 🟠 | tous les handlers de prompt de `actions.clj` |
| R10 | Environnement NLE : limite de pas, actions, options | 🔴 si oublié | harnais |
| R11 | Familier présent (NLE) vs `pettype:none` (BotHack) | 🟡 | déplacement, vol en boutique, combat |
| R12 | Or comme objet d'inventaire (GOLDOBJ) | 🟡 | gestion de l'or, `bribe-demon` |
| R13 | Problèmes connus de BotHack qui restent vrais | 🟠 | `doc/issues.md` |
| R14 | Le Sorcier vole aussi l'artefact de quête ; offrande à Moloch fatale | 🟡 | `hunt`, `offer-amulet` |

### R1 — Le pudding farming est mort 🔴

**Faits (sources 3.6.7)** :
- `doc/fixes36.0` : « weaken "farming" strategies », « **cloned creatures (of any type) don't deathdrop items** », « pudding corpses behave somewhat differently than before ».
- `src/exper.c`, `experience()` : pour un monstre `mrevived || mcloned`, l'XP est réduite après 20 morts de l'espèce, puis encore par tranches (« 1..20 full experience », boucle `for (i = 0, tmp2 = 20; nk > tmp2 && tmp > 1; ++i)`).
- NetHackWiki, *Pudding farming* : « puddings no longer drop corpses at all (and thus cannot drop items either), and cloned puddings give significantly fewer points ».

**Poids de la ferme dans une ascension réelle** (chronologie de vp6, §5.6) : du tour 17 442 au tour ~53 300 sur Dlvl 9, soit **~36 000 tours = la moitié de la partie**, et le score passe de 66 360 à 6 925 842, soit **99 % du score** avant le bonus d'ascension. On ne retire pas un détail : on retire la moitié du plan.

**Ce qui casse dans BotHack** :
1. la ferme ne produit plus d'objets → la liste de `farm-done?` (6 remove curse, identify, bougies) n'est jamais remplie par elle ;
2. le score monte très lentement → **ni 6 M ni 15 M ne sont jamais atteints** → `farm-done?` reste faux → le bot **farme indéfiniment** (seule sortie : `botched-farm?`, si aucun pudding n'est vu pendant 500 tours) ;
3. dès que `init-farm?` est vrai, `farm-init` (priorité 18) passe **avant** `progress` (priorité 19) : le bot abandonne la progression pour aller farmer ; une fois installé, le handler `farm` (priorité −8) ne rend la main que sur `end-farm?` (qui exige `farm-done?`) ou `botched-farm?` ;
4. la ferme utilise `Elbereth*` et attaque depuis ce carré : double rupture avec R2.

**Correctif** :
- supprimer le handler `farm` et `init-farm?` ;
- remplacer `farm-done?` par un prédicat d'**état de préparation** sans score : par exemple `XL ≥ 14 ∧ réflexion ∧ MR ∧ (lévitation ∨ quête faite) ∧ AC ≤ −10 ∧ ≥ 2 remove curse ∧ licorne` ;
- trouver d'autres sources pour ce que la ferme donnait :
  - **MR** : fournie par la GDSM du kit (déjà là dès le tour 1) ;
  - **réflexion** : prix de Sokoban (amulette de réflexion 50 %), bouclier de réflexion de Perseus (statue de Méduse), ou **premier vœu du Château** (la liste de vœux saute déjà les DSM) ;
  - **XP** : combat normal (les Valkyries montent vite), potions de gain level (vœu si nécessaire), et les niveaux XL 14 exigés par la quête viennent naturellement vers Dlvl 15-25 ;
  - **objets** : boutiques de Minetown (identification par prix, déjà codée), autels (BUC), sacrifice coaligné (dons d'artefacts), vœux ;
  - **remove curse** : prière (corrige les objets maudits gênants), eau bénite (`#pray` sur autel coaligné / eau), vœu ;
  - **bougies** : Izchak à Minetown (sauf Orcish Town, qui en garantit 7 posées au sol : `mines.des`, « Guarantee 7 candles since we won't have Izchak available ») ; vœu `7 blessed wax candles` déjà dans la liste.

### R2 — Elbereth 🔴

**Faits (sources 3.6.7)** :
- `src/monmove.c`, `onscary()` : Elbereth ne fait peur que si `sengr_at("Elbereth", x, y, TRUE)` **et** si le héros est sur la case (ou son image déplacée), et **jamais** pour les commerçants, gardes, monstres aveugles ou pacifiques, `@` humains et elfes, minotaures, **ni en Géhennom (`Inhell`) ni dans les Plans (`In_endgame`)**.
- `src/engrave.c`, `sengr_at(..., strict=TRUE)` → `fuzzymatch(engr_txt, "Elbereth", "", TRUE)` : **le texte doit être exactement « Elbereth »** (casse ignorée). « ElberethElbereth », « Elbereth* » ou un Elbereth ajouté à un vieux texte **ne protègent pas**.
- `src/mon.c`, `setmangry(mtmp, via_attack)` : attaquer (mêlée `uhitm.c`, projectiles `dothrow.c` via `wakeup(mon, TRUE)`, certains zaps `zap.c`) un monstre qu'Elbereth effraie, **depuis la case Elbereth**, affiche « You feel like a hypocrite. », **retire 5 points d'alignement** et **efface la gravure, quel que soit son type (brûlée comprise)**.
- `doc/fixes36.0` : « engraving Elbereth is less efficient as protection ».

**Ce qui casse dans BotHack** :
1. `engrave-e` **ajoute** au texte existant quand il y a déjà un E ou moins de 200 caractères (`append?`). Nos toplines d'ascension montrent le résultat : `"||e?c rElbcrXthEl,crctnElberctnElbereth"`. En 3.6 ce texte vaut zéro ;
2. la ferme grave `Elbereth*` (marqueur) : zéro ;
3. `fight` (lignes 1246 et 1302 de `mainbot.clj`) grave puis **se bat depuis la case** : en 3.6 chaque coup contre un monstre effrayé coûte −5 d'alignement et efface la gravure. Quelques combats suffisent à rendre l'alignement négatif → en 3.6.7 `pray.c`, `alignment < 0` donne `p_type = 1` puis `angrygods()` : **la prière d'urgence punit au lieu de sauver**. C'est le mode de défaillance le plus dangereux de la liste, parce qu'il est silencieux et différé ;
4. **Géhennom et Plan Astral** : dans nos deux ascensions, la retraite finale repose sur Elbereth (12 gravures et 24 fuites dans les 400 dernières lignes de vp6). En 3.6, ces tours sont perdus, là où la partie se gagne ou se perd.

**Correctif** :
- `engrave-e` : ne graver que si la case n'a **pas** d'autre gravure ; sinon répondre **non** à « Do you want to add to the current engraving? » (ce qui efface et réécrit) ou se déplacer ;
- **ne jamais attaquer depuis une case Elbereth** : le handler `fight` doit d'abord quitter la case, ou n'utiliser Elbereth que pour se reposer (`recover`) ;
- désactiver toute logique Elbereth si `Inhell ∨ endgame` (branche `:vlad`, `:wiztower`, niveaux Géhennom, Plans) et la remplacer par : fuite par escalier, parchemin de téléportation, `wand of digging` vers le bas (hors Plans), potion de pleine guérison, prière (si alignement et timeout le permettent) ;
- surveiller l'alignement : NLE ne l'expose pas dans `blstats`, mais les messages « You feel like a hypocrite. » sont détectables et on peut interdire toute prière après l'un d'eux tant qu'on n'a pas regagné de l'alignement (tuer des hostiles le fait remonter).

### R3 — Méduse : les variantes 3 et 4 🔴

**Faits** : `dat/dungeon.def` 3.4.3 `RNDLEVEL: "medusa" "none" @ (-5, 4) 2` → 3.6.7 `... 4`. `dat/medusa.des` 3.6.7 définit `medusa-1` à `medusa-4` ; `medusa-1` et `medusa-2` ont une carte **identique** à 3.4.3 (comparaison automatique des blocs `MAP`). `fixes36.1` : « make the raven medusa level shortsighted ».

**Ce qui casse** : la reconnaissance (`dungeon.py`, lignes ~400-420) cherche la géométrie de `medusa-1`/`-2` ; un troisième test générique (Méduse vue, ou colonne d'eau en x=2) peut poser le tag `:medusa` sans variante. Alors `medusa-spot` renvoie `nil`, `medusa-action` ne renvoie aucune action, et c'est la progression normale qui emmène le bot traverser le niveau **sans la tactique aveuglée prévue pour Méduse**. Sans réflexion, c'est la pétrification par le regard. Une fois sur deux.

**Correctif, par ordre de préférence** :
1. **avoir la réflexion avant Dlvl 21** : avec la GDSM de départ, le premier vœu donne directement le bouclier de réflexion (§5.4) ; sinon amulette de Sokoban ;
2. à défaut, remplacer la tactique « case fixe + recherche » par une tactique **générique** : aveugle (bandeau/serviette) + télépathie (casque de télépathie, ou avoir mangé un floating eye — déjà une priorité de BotHack) + attaquer le glyphe de Méduse en mêlée ;
3. extraire les blueprints `medusa-3`/`-4` depuis `dat/medusa.des` avec le même outil que la §3.2.

### R4 — La prière 🔴

**Faits** : 3.4.3 (`pray.c:145`) : trouble « PV bas » si `u.uhp <= 5 || u.uhp*7 <= u.uhpmax`. 3.6.7 (`pray.c`, `critically_low_hp()`) : PV max **plafonnés à 15 × XL**, et diviseur **5 (XL 1-5), 6 (6-13), 7 (14-21), 8 (22-29), 9 (30)**. Et `paranoid_confirm:pray` est actif par défaut (`fixes36.0`) : « Are you sure you want to pray? [yn] ».

**Ce qui casse** : `pray-for-hp` prie à `hp ≤ maxhp/7`. Exemple avec vp6 en fin de partie (XL 25, 284 PV max) : 3.6 considère les PV critiques sous `min(284, 375)/8 = 35` ; BotHack prie sous `284/7 = 40`. Entre 36 et 40 PV, **le bot prie sans être en « big trouble »** au sens du jeu. Or 3.6.7 `pray.c` (`can_pray`) juge alors la prière « too soon » dès que `u.ublesscnt > 0` (ou `> 100` si trouble mineur, par ex. la faim) ; `p_type = 0` → délai de prière `+rnz(250)`, **Chance −3**, `gods_upset()` → colère divine (`ugangr++`) et `angrygods()` (malédiction, éclair, minion...). Et toute prière ultérieure avec `ugangr` ou Chance < 0 est `p_type = 1` (« too naughty ») : **la prière d'urgence suivante ne sauve plus**. La règle « trop tôt » existait en 3.4.3 ; ce qui change est le seuil, donc la fenêtre où BotHack croit être en danger alors que le jeu ne l'est pas. Aux bas niveaux c'est l'inverse (3.6 est plus généreux, le bot ne profite pas de la marge).

**Correctif** : porter `critically_low_hp()` à l'identique (10 lignes) ; répondre `y` au prompt de confirmation ; conserver le suivi du délai de prière de BotHack.

### R5 — Les chaînes d'objets 🟠

**Faits** : 3.6.7 `src/objnam.c` : un objet au carquois s'affiche `(in quiver)` seulement pour les munitions d'arc ; les autres munitions et petits objets `(in quiver pouch)` ; les armes non-munitions (**les dagues de la Valkyrie**) `(at the ready)`. En 3.4.3 : toujours `(in quiver)`. La regex du port (`pybothack/item.py`, `ITEM_RE`) ne connaît que `(in quiver)`.

**Ce qui casse** : « b - 3 +0 daggers (at the ready) » est mal découpé → nom d'objet « daggers (at the ready) » → type inconnu (`unknown itemtype`) → le bot peut jeter, ignorer ou ne jamais relancer ses dagues. D'autres différences de libellés sont probables (à inventorier systématiquement).

**Correctif** : avec NLE, **ne plus parser les noms pour l'identité de base** : `inv_glyphs` donne le type d'objet (ou l'apparence non identifiée) et `inv_oclasses` la classe ; garder la regex seulement pour BUC/enchantement/charges/état, et l'étendre à `(at the ready)`, `(in quiver pouch)`. Faire un test de non-régression qui passe **toutes** les chaînes d'`objnam.c` 3.6.7 (générées en mode wizard, voir §9 étape 2).

### R6 — Orcish Town 🟠

**Faits** : 3.6.7 `dat/mines.des` : `minetn-1` n'est plus Frontier Town mais **Orcish Town** (« a variant of Frontier Town that has been overrun by orcs ») : barricades de barreaux, boutiques pillées sans commerçants, **temple profané sans prêtre** (« the altar's defiled; useful for BUC but never coaligned »), une armée d'orques, 7 bougies posées. Probabilité : 1/7 (7 variantes).

**Ce qui casse** : `get-protection` (achat de protection au prêtre), `shop` (identification par prix), le repli « tremper pour Excalibur dans la fontaine de Minetown » (qui énerve déjà les gardes dans l'original, `issues.md`), et une horde d'orques hostiles pour un bot qui s'attend à une ville pacifique à XL bas.

**Correctif** : détecter la variante (glyphes d'orques + barreaux + pas de prêtre), marquer Minetown comme « sans services », aller chercher les bougies, rester prudent (bot niveau 5-8 contre des dizaines d'orques ; la GDSM aide beaucoup ici).

### R7 — La quête Valkyrie 🟠

**Faits** (comparaison des blocs `MAP` de `dat/Valkyrie.des`, caractères différents) : `Val-strt` **1 253**, `Val-goal` 113, `Val-loca` 38 ; `Val-fila`/`Val-filb` identiques. Le port contient des blueprints `quest Home 1..6`. `fixes36.0` : « melted ice on Valkyrie quest should be pool, not moat ». Le crash n° 9 de la §4 était justement sur le chemin « saluer le leader de quête ».

**Correctif** : réextraire les blueprints de quête depuis 3.6.7 ; sur NLE, localiser le leader par son glyphe plutôt que par coordonnées ; retester `hit-surtur` sur la nouvelle carte du but.

### R8 — Les autres niveaux spéciaux 🟡→🟠

Résultat de la comparaison automatique de toutes les cartes `MAP` 3.4.3-NAO vs 3.6.7 :

| identiques (blueprints BotHack réutilisables) | modifiés | nouveaux en 3.6 |
| --- | --- | --- |
| **Sokoban ×8**, **Château**, Oracle, Vallée, Asmodeus, Orcus, **Sanctuaire**, **Astral**, Terre, Feu, Eau, tours de Vlad ×3, wizard1/2, fakewiz1/2, Méduse 1/2, bigrm 1-5, minefill, minend 1-3, minetn 2-7 | Baalzebub (15 car.), Juiblex (110), **Air** (242), wizard3 (1), Fort Ludios (8), minetn-1 (Orcish Town), quête Val | **medusa-3/4**, **bigrm-6 à 10** (et Bigroom plus probable : `40 5` → `40 10`) |

C'est une **très bonne nouvelle** : Sokoban (donc toutes les solutions extraites), le Château et le Sanctuaire sont identiques. Les petites différences (wizard3 : 1 caractère, Ludios : 8) sont probablement sans effet, mais doivent être vérifiées sur les coordonnées précises utilisées (`wiztower-boundary`, `fake-wiztower-portal`, etc.). `baalz` (15 caractères) touche le niveau que l'original « creuse déjà dans des motifs bizarres » (`issues.md`).

### R9 — Prompts et messages 🟠

BotHack reconnaît des dizaines de prompts et de messages par regex (`actions.clj`, `handlers.clj`). 3.6 a reformulé une partie des messages, ajouté des prompts (`paranoid_confirm`, « Do you want to add to the current engraving? » inchangé mais autres variantes de gravure, `#terrain`, `autodescribe`...), et NLE ne fait pas tourner NAO (plus de « There is already a game in progress » par exemple).

**Correctif** :
- utiliser `misc` pour savoir **qu'**un prompt est ouvert, indépendamment de son texte ;
- politique de repli générique et journalisée : prompt `[yn]` inconnu → `n` ou ESC ; `getlin` inconnu → ESC ; `--More--` → espace ; menu inconnu → ESC ;
- **compter** ces replis par partie : c'est l'équivalent NLE du « bot abandonné » de la §4, et c'est ce qui dit quelles regex porter en priorité ;
- vérifier « It's a wall. » : 3.6.7 `hack.c` l'émet bien avec `mention_walls` (`pline("It's %s.", ...)`), option **présente dans les options NLE par défaut**.

### R10 — L'environnement NLE lui-même 🔴 si oublié

Vérifié dans `vendor/nle/nle/env/base.py` et `nle/nethack/nethack.py` :

- **`max_episode_steps=5000` par défaut**. Une ascension BotHack, c'est 72 000 à 90 000 **tours**, donc plus de 100 000 pas d'agent. Les `step_timeout` de `claude_fable_2` en sont une illustration à petite échelle. → passer une valeur énorme ou piloter `nle.nethack.Nethack` directement ;
- **options par défaut** (`NETHACKOPTIONS`) : `autopickup` avec `pickup_types:$?!/` (BotHack : `!autopickup`, `pickup_types:$`), `pickup_burden:unencumbered`, `showexp`, `mention_walls`, `nobones`, `nolegacy`... → passer `options=` explicitement, alignées sur ce que la stratégie suppose (autopickup de l'or seulement) ;
- **actions** : l'environnement gym expose un ensemble fini d'actions ; graver « Elbereth », formuler un vœu (« blessed greased fixed +3 shield of reflection »), nommer une amulette ou `#enhance` exigent de taper du texte libre et des commandes étendues. `nle.nethack.Nethack.step(keycode)` accepte un code de touche : c'est le niveau à utiliser pour un bot symbolique ;
- **`allow_all_yn_questions` / `allow_all_modes`** : à activer ou à contourner via l'interface bas niveau ;
- **vitesse** : NLE exécute le jeu en C sans terminal ; le goulot sera la décision Python (quelques dizaines de ms, jusqu'à la seconde pour `search-level`). Dans vp6, les 36 000 tours de ferme ont pris ~0,7 h de temps réel, alors que les ~9 400 tours entre la Cloche d'ouverture (T 62 635, 4,0 h) et le Plan Astral (T 72 025, 7,5 h) en ont pris ~3,5 h : **c'est la fin de partie (labyrinthes du Géhennom, combats, pathfinding) qui coûte le temps réel**, pas le nombre de tours. Mesurer et profiler tôt sur ces niveaux-là ;
- **preuves** : garder ttyrec + xlogfile de NLE et un fichier de log du bot **rapatrié systématiquement** (la réserve de la §1.4 ne doit pas se reproduire).

### R11 — Le familier 🟡

BotHack joue avec `pettype:none` ; le protocole NLE du dépôt garde le familier (chaton ou petit chien, tiré au hasard pour une Valkyrie). Effets : « You stop. Your kitten is in the way », échanges de place, familier qui vole en boutique, dégâts collatéraux, et les heuristiques de `fight`/`fidget` n'ont jamais vu de familier. → Traiter le familier comme un obstacle mobile échangeable, ne jamais l'attaquer (`hilite_pet` n'existe pas, mais NLE a des glyphes distincts pour les monstres apprivoisés), ou le laisser derrière au premier escalier.

### R12 — L'or est un objet 🟡

`fixes36.0` : `GOLDOBJ` devient inconditionnel. L'or occupe l'emplacement `$` de l'inventaire et se manipule comme un objet (poids, sac, menus). → Vérifier `bribe-demon`, les paiements, le « unbagging gold piece by piece » déjà signalé dans `issues.md`.

### R13 — Les limites connues de BotHack restent vraies 🟠

Extraits de `doc/issues.md` de l'original, qui ne dépendent pas de la version et tueront des parties sur NLE aussi :

- atteindre le Château sans baguette de frappe et rester coincé ;
- échec à débénir les objets d'invocation → blocage ;
- pas d'anneau de lévitation utilisable → ne peut pas entrer dans la tour de Rodney ;
- Rodney vole l'Amulette et est téléporté en bas par la force mystérieuse → le bot le cherche en haut ;
- objets d'invocation tombés dans l'eau ou la lave ;
- frappe des pacifiques quand aveugle ; frappe des gas spores près de pacifiques ;
- trop d'exploration pendant la course finale ; monstres « covetous » mal gérés.

Ajoutés par le port : un blocage dans la couche de décision (`pool_g/game15` : trames reçues, aucune action pendant 3 min) jamais attribué ; les gardes défensifs de `desired-food` là où l'original lève une exception (`LIMITATIONS.md`).

→ Chacun mérite un **scénario de test en mode wizard** (§9 étape 4) plutôt que d'attendre qu'il se produise en partie réelle au bout de 6 h.

### R14 — Détails de fin de partie 🟡

- `fixes36.1` : le Sorcier vole n'importe quel artefact de quête, pas seulement celui du rôle → l'Orbe du Destin (lévitation du bot !) peut partir ; `hunt` existe déjà.
- `fixes36.0` : l'Amulette peut être offerte à Moloch (mort). `offer-amulet` ne donne l'Amulette qu'à un autel coaligné ; garder cette vérification.
- 3.6.7 `pager.c` : sur le Plan Astral, l'alignement d'un autel n'est lisible **qu'adjacent** (« aligned altar » sinon). Le farlook de BotHack (`actions.clj`) ignore déjà la valeur `"aligned"` : **rien à changer**, mais le bot devra visiter les autels de près.

---

## 9. Plan d'action pour une ascension bot sur NLE

Principe : **d'abord la survie dans la durée, ensuite la stratégie**. C'est exactement ce que la §4 a appris : la stratégie de 2015 suffisait, c'est la capacité à jouer 8 h sans se bloquer qui manquait.

### Étape 0 — Décider de la base de code (1 jour)

Recommandation : **partir de `pybothack` (couche A + modèle du monde), pas d'un nouveau bot**, et abandonner l'objectif d'identité octet par octet avec l'original. Créer un nouveau répertoire (par ex. `run_xx/nle_bothack/`), copier `pybothack/`, **geler** la copie 3.4.3 comme référence.

### Étape 1 — Adaptateur NLE (couche C)

Écrire `nle_iface.py` qui produit, à partir d'une observation NLE, **les mêmes événements** que le scraper envoyait au délégateur : `full-frame`, `botl` (depuis `blstats`), `message`, `inventory`, prompts `choice-fn`/`yn`/`getlin`/`menu`, `know-position`, `dlvl-changed`. Remplacer le parsing de tuiles par une table `glyphe → (feature, monstre, objet)` générée depuis `nle.nethack` (`glyph_is_monster`, `glyph_to_mon`, `glyph_is_object`, `glyph_to_obj`, `glyph_is_cmap`...).

Critère de passage : le bot joue 100 parties jusqu'à la mort ou 20 000 tours avec **zéro exception non gérée et zéro partie sans action pendant plus de 60 s**.

### Étape 2 — Règles 3.6 (couche B), une par une, avec test

Pour chaque risque R1-R9 : correctif + test unitaire **construit depuis la source C 3.6.7**, pas depuis le port (leçon n° 8 de la §3.5). Outils :
- NLE en `wizard=True` **uniquement pour les tests** (jamais pour les parties comptées) : `^G` pour créer un monstre, `^W` pour un vœu, `^V` pour téléporter de niveau, et `wizkit` pour démarrer avec un inventaire donné ;
- générer toutes les chaînes d'objets et de messages visées en wizard mode et les passer au parseur (R5, R9).

Ordre : R10 → R2 → R4 → R1 → R5 → R9 → R3 → R6 → R7 → R8.

Critère de passage : les tests passent ; 50 parties : taux d'arrivée à Minetown ≥ 80 % (c'est le jalon existant du dépôt, qu'un BotHack correct doit écraser), zéro « You feel like a hypocrite. », zéro prière hors trouble.

### Étape 3 — Remplacer le farming

Nouveau prédicat de préparation (R1), nouvelle version de `full-explore` qui ne conditionne plus Dlvl > 20 à la ferme, et exploitation du kit :
- MR dès le départ → pas de vœu de DSM, la cape peut être n'importe quelle cape utile (déplacement, protection) ;
- AC de départ très basse (GDSM : base 9 + 2 = **−11 d'AC** dès le tour 1) → survivre aux Mines et à Sokoban à XL bas, l'étape la plus meurtrière des 161 parties locales (médiane Dlvl 6) ;
- premier vœu → réflexion (résout R3 d'avance).

Critère : 50 parties, taux d'arrivée au Château mesuré et > 0 ; journal des causes de mort.

### Étape 4 — Scénarios de fin de partie en mode wizard

Le coût d'une ascension (7-8 h) rend l'itération sur la fin de partie impossible en parties réelles. Construire une **batterie de scénarios** (wizard mode, tests seulement) qui démarrent au Château, à la Vallée, à Vlad, à la tour du Sorcier, au niveau de l'invocation, sur chaque Plan et sur l'Astral avec l'inventaire typique d'un bot qui y arrive (celui de nos deux ascensions est lisible dans les ttyrecs). Chaque problème de R13 devient un scénario.

Critère : chaque scénario atteint son objectif sur ≥ 8/10 essais seedés.

### Étape 5 — Campagne en volume

Réutiliser l'idée de `ascend_pool.sh` (slots toujours occupés, arrêt sur `death=ascended` du xlogfile NLE), avec :
- **rapatriement du log du bot pour chaque partie** et du hash de commit ;
- `tools/ending_mix.py` adapté : mort / abandon / repli de prompt / timeout ;
- l'enregistrement du seed (`get_current_seeds()`) pour rejouer toute partie intéressante à l'identique — l'équivalent NLE de `det_rng.c`, gratuit.

Estimation de volume, **hypothèse** fondée sur notre seul point de mesure (2 ascensions pour au moins 49 parties lancées en 3.4.3, dont beaucoup courtes) : il faut s'attendre à devoir jouer **plusieurs centaines de parties** tant que le taux d'arrivée au Château n'est pas élevé. Parallélisme élevé et peu de mémoire par partie : un gros CPU loué à l'heure est adapté, comme pour `VAST.md`.

### Ce qu'il ne faut pas faire

- réimplémenter le scraper ou le remappage de symboles « pour rester fidèle » ;
- garder le score comme horloge de progression ;
- conserver une seule ligne de logique Elbereth non auditée ;
- valider un correctif sur une fenêtre d'observation courte (leçon n° 5) ;
- compter une partie jouée en mode wizard, même partiellement.

---

## 10. Annexes

### 10.1 Fichiers clés

| quoi | où |
| --- | --- |
| preuves d'ascension | `run_06.09.26/new_bothack/claude/artifacts/ASCENSION/` |
| relecture | `tools/watch_ascension.sh`, `tools/replay_ascension.py` |
| harnais de campagne | `tools/ascend_pool.sh`, `tools/ascend_summary.py`, `tools/ending_mix.py`, `tools/vast/` |
| stratégie | `pybothack/bots/mainbot.py` ; original `/home/roro/nhwork/bothack-src/src/bothack/bots/mainbot.clj` |
| défauts et correctifs | `docs/LIMITATIONS.md`, `docs/RESULTS.md` §2e et suivantes |
| méthode de fidélité | `docs/HANDOFF.md`, `docs/TESTS.md` |
| NLE 3.6.7 + patch GDSM | `run_10.06.26/claude_fable_2/vendor/nle`, `patches/nle-367-minetown.patch` |
| changements 3.6 (source primaire) | `vendor/nle/doc/fixes36.0` … `fixes36.7` |
| sources 3.4.3-NAO | `upstream/nh343-nao-build/` |

### 10.2 Lignes de code 3.6.7 citées

| sujet | fichier : fonction |
| --- | --- |
| Elbereth effraie qui, où | `src/monmove.c : onscary()` |
| texte exact exigé | `src/engrave.c : sengr_at()` |
| effacement « hypocrite » −5 | `src/mon.c : setmangry()` |
| XP dégressive des clones | `src/exper.c : experience()` |
| pas de death drop des clones | `doc/fixes36.0` |
| seuil de prière | `src/pray.c : critically_low_hp()` |
| libellés du carquois | `src/objnam.c` (`(at the ready)`, `(in quiver pouch)`) |
| autel Astral lisible adjacent | `src/pager.c` (`"aligned"`) |
| « It's a wall. » | `src/hack.c` (`iflags.mention_walls`) |
| Méduse ×4, Bigroom ×10 | `dat/dungeon.def`, `dat/medusa.des`, `dat/bigroom.des` |
| Orcish Town | `dat/mines.des` (`minetn-1`) |
| limite de pas, options | `nle/env/base.py`, `nle/nethack/nethack.py` (`NETHACKOPTIONS`) |

### 10.3 Comparaison des cartes 3.4.3-NAO / 3.6.7 (reproductible)

Extraction de chaque bloc `MAP … ENDMAP` par niveau nommé (`MAZE:`/`LEVEL:`) dans `sokoban`, `castle`, `medusa`, `oracle`, `mines`, `knox`, `yendor`, `gehennom`, `endgame`, `bigroom`, `tower`, `Valkyrie`, puis comparaison ligne à ligne (espaces de fin ignorés) et comptage des caractères différents. Résultats en §8 R7-R8.

### 10.4 Sources externes

- BotHack : <https://github.com/krajj7/BotHack> (README, `doc/issues.md`)
- NetHackWiki, *Pudding farming* : <https://nethackwiki.com/wiki/Pudding_farming>
- NetHackWiki, *Elbereth* : <https://nethackwiki.com/wiki/Elbereth>
- NetHackWiki, *NetHack 3.6.0* : <https://nethackwiki.com/wiki/NetHack_3.6.0>
- NLE maintenu : <https://github.com/NetHack-LE/nle> ; NLE d'origine : <https://github.com/facebookresearch/nle>

Là où le wiki et le code divergent, le code 3.6.7 local fait foi (exemple : le wiki évoque une érosion d'Elbereth à chaque fuite de monstre ; aucun chemin de code correspondant n'a été trouvé dans `monmove.c` 3.6.7, donc ce document ne s'appuie pas dessus).
