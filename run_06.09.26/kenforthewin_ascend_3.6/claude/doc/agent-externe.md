# Brancher un agent externe (ex. Codex) sur une partie

Ce document explique comment un agent qui **n'est pas Claude** (Codex, un autre
LLM, un script…) peut jouer sa propre partie de NetHack **à côté des parties de
Claude**, avec les mêmes outils, les mêmes garde-fous, et apparaître sur le
dashboard (http://127.0.0.1:8766/) comme les autres.

Dossier du projet (même chemin sur le PC et sur le worker) :

    /home/roro/work/projects/super_nethack/run_06.09.26/kenforthewin_ascend_3.6/claude

Dans la suite, `R` désigne ce dossier.

---

## 1. Ce que l'agent reçoit

- **Un emplacement** (slot) numéroté de 1 à 8. Les emplacements 1, 3 et 8 sont
  joués par Claude ; le **4** est prévu pour Codex (il était retiré).
- **Une partie NetHack 3.6.7 vanilla** (Valkyrie naine loyale, comme les autres),
  qui tourne sur la machine **miniforum-worker** dans une session tmux.
- **Des commandes** dans `R/slots/4/` : chacune envoie des touches ou lit l'écran
  de *sa* partie, et rien d'autre.
- **Un enregistrement automatique** : chaque écran est filmé par le recorder du
  worker ; le dashboard montre la partie en direct, en replay, dans l'historique.

## 2. Ouvrir l'emplacement (une seule fois, par l'humain ou par Claude)

    cd R
    scripts/external_slot.sh 4 Codex

Ce script :

1. retire l'emplacement 4 de la liste des emplacements arrêtés
   (`.runtime/style-plan.json`) pour qu'il réapparaisse sur le dashboard ;
2. démarre une nouvelle partie sur le worker, avec le nom de joueur **Codex**
   (les sauvegardes et le score sont à ce nom) ;
3. enregistre le style `codex` et le journal `memory/codex-run-1.md`.

Le nom de joueur doit être composé de lettres/chiffres (16 max). Un autre nom
ou un autre emplacement libre marchent pareil : `scripts/external_slot.sh 5 Gemini`.

## 3. Où l'agent peut tourner

Deux possibilités, au choix :

**a) Sur ce PC** (le plus simple) : les commandes `slots/4/*` détectent que la
partie vit sur le worker (`.runtime/where-4` = `worker`) et s'y exécutent
automatiquement par ssh (connexion partagée, rapide). L'agent n'a rien à savoir
du worker.

    cd R
    slots/4/v                 # voir l'écran

**b) Directement sur le worker** (`ssh miniforum-worker`) : même dossier, en
ajoutant `NH_HOST=worker` pour que les commandes s'exécutent sur place.

    cd R && export NH_HOST=worker NH_SLOT=4
    slots/4/v

Règle du projet : **aucun calcul lourd sur le PC** (solveurs, recherches…) ;
les scripts personnels de l'agent se lancent avec `slots/4/w <commande>`, qui
les exécute sur le worker, à côté de la partie.

## 4. Les commandes essentielles

Toutes dans `R/slots/4/` (elles fixent `NH_SLOT=4` toutes seules) :

| Commande | Effet |
|---|---|
| `v` | écran compact : messages, carte avec coordonnées, statut, voisins, animaux |
| `session screen` | écran brut complet (144×36) |
| `k <touches>` | envoie des touches. Chiffres = déplacements (pavé numérique : 7 8 9 / 4 6 / 1 2 3). `--named Enter`, `--named Escape` pour les touches spéciales, `--raw` pour du texte de menu |
| `t X Y` | se déplace (travel) vers la case X,Y de l'écran |
| `look X Y` | farlook : identifie ce qu'il y a en X,Y |
| `inv` | inventaire **complet** (le panneau de droite est coupé après ~33 lignes), avec le contenu des sacs déjà connus (bag of holding seulement s’il est connu non maudit ; « bag » d’état inconnu seulement si le bag of holding est déjà identifié) ; sinon le dashboard montre le dernier contenu que l’agent a vu en regardant dedans |
| `fight <lettre>` | attaque un monstre adjacent désigné par sa lettre (s'arrête sous 50 % HP) |
| `explore` | exploration automatique prudente (s'arrête sur tout danger) |
| `rest` | repos contrôlé (s'arrête à la moindre perte de HP) |
| `say "texte"` | **commentaire public** affiché en direct sur le dashboard et en sous-titre du replay |
| `chronicle --importance 1-3 --kind item\|monster\|danger\|progress\|decision\|death "Titre" "Explication"` | enregistre un moment important (chronique du dashboard) |
| `session ack-hp` | acquitte l'alarme HP (voir §6) |
| `w <commande>` | lance un script perso de l'agent sur le worker, dans `slots/4/` |

Repères d'écran : la carte occupe les lignes 10 à 30, la ligne de statut
(`Dlvl … HP … T:…`) la ligne 34. **La position du héros est la ligne
« Terminal cursor (x,y) »** de `v` (la ligne « Neighbors » ne concerne que lui).

## 5. Les règles de l'expérience (« PURE »)

- NetHack vanilla, **pas de mode wizard/explore, pas de bot**.
- **Jamais de save-scum** : ne jamais copier/restaurer un fichier de sauvegarde.
  `S` (sauvegarder) seulement pour faire une pause ; la reprise se fait avec
  `slots/4/session start`.
- Chaque décision est prise par l'agent lui-même, après avoir lu l'écran.
  Les scripts ne font que des actions bornées qui s'arrêtent au moindre danger.
- Spoilers, wiki, code source (`R/engine/nethack-3.6.7/src`) : autorisés.
- **Ne jamais envoyer de touches à une autre partie**, ne jamais modifier les
  fichiers partagés (`scripts/`, `web/`, `config/`) ni `.runtime/` à la main.
- En cas de mort : écrire la section `DEATH` et les leçons dans le journal,
  fermer les écrans de fin (Escape / q / Entrée), et s'arrêter.

## 6. Les garde-fous intégrés (identiques pour tous les agents)

Le harnais refuse certaines touches et explique pourquoi :

- **Alarme HP** : après une chute rapide des HP (1/5 du max, sous 60 %), plus
  aucune touche n'est acceptée (sauf Escape) jusqu'à `slots/4/session ack-hp`.
  Il faut lire l'écran et décider (prier, fuir, se soigner) avant d'acquitter.
- **Repos comptés** (`n20s`) refusés sous 70 % HP ; **plusieurs pas d'un coup**
  refusés sous 50 % HP.
- **« Really attack? »** : répondre `y` est refusé (pacifiques, prêtres,
  marchands) sauf `k --really y`. **F vers un @** : le harnais fait d’abord un
  farlook automatique de la case (gratuit) et refuse si le jeu dit « peaceful »
  ou « tame » ; un **pas vers un `e`** (floating eye) est refusé sans `--really`.
- **Stone / Slime** : seuls les gestes qui soignent passent (manger un lizard, prier…).
- `explore` s'arrête devant une porte verrouillée (souvent une boutique), un vol,
  une nymphe/leprechaun, un lich/démon/géant/troll/cockatrice.

## 7. Le journal (mémoire de l'agent)

`R/memory/codex-run-1.md` : l'agent y tient à jour, **en tête**, une ligne
`URGENT:` (T, Dlvl, HP, AC, XL, dernière prière, équipement, dangers), puis ses
plans et ses leçons. À chaque reprise (nouvelle session de l'agent), il relit
ce journal avant de jouer. Le dashboard affiche la fin et les leçons du journal
dans l'Historique.

Lectures conseillées avant la première partie :

- `R/memory/session.md` — règles et outils (source de vérité) ;
- `R/memory/astra-style.md` — la méthode Astra et les **leçons de ~40 morts**
  (zoo de Sokoban, Castle, fontaines, prières, marchands…).

## 8. Sur le dashboard

Une fois l'emplacement ouvert, la partie apparaît automatiquement :

- **Dashboard** : une carte « Partie 4 » (style *Codex (agent externe)*) avec
  écran en direct, commentaires `say`, moments forts ;
- **Live** : un bouton « Partie 4 » ;
- **Historique / Stratégie** : ses statistiques et sa chronique à côté de celles
  de Claude, pour comparer.

## 9. Démarrage rapide (à donner à Codex)

```text
Tu joues à NetHack 3.6.7 dans l'emplacement 4 du projet
/home/roro/work/projects/super_nethack/run_06.09.26/kenforthewin_ascend_3.6/claude.
Lis doc/agent-externe.md, memory/session.md et memory/astra-style.md.
Ta partie est déjà lancée (joueur Codex). Utilise uniquement les commandes
slots/4/* ; commence par `slots/4/v`. Tiens ton journal memory/codex-run-1.md
(ligne URGENT en tête). Commente tes décisions avec `slots/4/say "..."`
(en français, noms NetHack en anglais). Objectif : survivre et progresser
vers l'ascension, sans jamais tricher.
```
