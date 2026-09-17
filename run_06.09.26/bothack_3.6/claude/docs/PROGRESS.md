# Avancement — BotHack sur NetHack 3.6.7 (ascension assistée)

Point au 2026-09-17. Le journal détaillé des bugs est dans `docs/DEVLOG.md`,
l'architecture et les commandes dans `README.md`.

## En une phrase

Le bot joue seul, avec les aides de test (invincibilité, anti-famine, kit),
de Dlvl 1 jusqu'à Gehennom. Le Château est atteint dans 9 parties sur 14.
Dans la dernière série, une partie est allée jusqu'à la tour du Sorcier en
passant par la Vallée, la Cloche et Vlad. L'offrande finale fonctionne en
situation préparée : 2 ascensions sur 4, vérifiées par le moteur. Aucune
ascension complète du début à la fin pour l'instant.

## Ce qui est en place

- **Moteur** : NetHack 3.6.7 officiel, patché avec un *window port* « bot ».
  Le jeu dit exactement ce qu'il attend (commande, oui/non, menu, position,
  texte), en JSON. On élimine ainsi la classe de bugs « désynchronisation
  du terminal », qui causait 37 % des abandons en 3.4.3.
- **Aides de test** (désactivables, chaque intervention est journalisée) :
  - invincibilité ;
  - anti-famine ;
  - kit d'équipement.

  Elles ne remplissent jamais un objectif à la place du bot. Aujourd'hui,
  l'invincibilité a été complétée pour rester utile au combat :
  - plus de tour perdu à chaque mort annulée ;
  - niveaux et PV max drainés restaurés ;
  - mort par slime évitée avant qu'elle ne détruise l'armure.
- **Bot** : le port Python de BotHack (qui a fait 2 ascensions en 3.4.3),
  adapté aux règles 3.6.7 :
  - Elbereth strict ;
  - pas de pudding farming ;
  - nouveaux menus, messages, objets, monstres et prix.
- **Supervision** : détection des boucles de prompt, d'action, de cible
  (fixation) et de mort, des tempêtes de requêtes et des blocages sans
  nouveauté. Récupération d'abord, arrêt classé « stuck » ensuite.
- **Lanceur** :
  - `rungame` : une partie ;
  - `series` : N parties en parallèle, résumé, arrêt si le même échec se
    répète ;
  - `analyze` : explication d'une partie ou d'une série.

  Pour chaque partie, on garde :
  - version et hash du code ;
  - seed et aides actives ;
  - jalons de progression, et désormais les objets clés gagnés ou perdus ;
  - les 800 dernières observations et actions ;
  - le verdict du moteur, recoupé avec le xlogfile.
- **Scénarios préparés** (mode wizard, jamais comptés comme parties) :
  Méduse, Château, Vallée, Plans, Astral, offrande.

## Progression mesurée

| étape / série | résultat |
| --- | --- |
| Minetown (mt-w02, 20 parties) | 18/20 |
| Château, mêmes 14 seeds : ca-w01 → ca-w06 | 3 → 6 → 6 → 5 → 5 → **9/14** |
| Parcours complet full-w01 (ancien code, arrêtée) | 1 partie jusqu'à la Cloche (Château, Vallée, quête) |
| Parcours complet full-w02 (en cours, 14 parties) | 9 parties au-delà du Dlvl 10 ; 7 au Château ; 6 à la Vallée ; 1 à la Cloche, Vlad et la tour du Sorcier (Dlvl 51) |
| Scénario Méduse → Château | réussi |
| Scénario Château → Vallée | réussi |
| Scénario `astral-altar` (offrande) | **2/4 ascensions vérifiées par le moteur** ; les 2 échecs viennent du combat contre la foule de l'Astral (Cavaliers) |
| Scénario `astral` (depuis le point d'arrivée) | échec : foule trop dense |

Principaux bugs corrigés aujourd'hui, trouvés en jouant :

- **Autels** :
  - un autel sous des objets était lu comme du sol, et le bot y gravait
    sans fin ;
  - « high altar » n'était pas reconnu : le bot quittait l'autel de son
    propre dieu.
- **Objets et monstres** :
  - Keystone Kops et roman absents des données du bot ;
  - nouvelles étiquettes de parchemins mal classées, sans leur pluriel ;
  - prix de pile divisé deux fois, et surtaxe de commerçant fâché oubliée.
    Ces erreurs faisaient rejeter toutes les identités possibles.
- **Combat et déplacements** :
  - attaque sans fin d'un rocher ;
  - rocher bloqué par un monstre invisible ;
  - refus de manger en boutique ;
  - incube qui retire l'armure pendant que le bot continue à se battre nu ;
  - licorne maudite appliquée sans fin.
- **Lanceur** : un SIGTERM pouvait être ignoré.

## Utilisation du miniforum (worker)

**Depuis le 2026-09-17, tous les runs passent par le miniforum.**

- **Séries** : `tools/worker_series.sh` travaille dans `~/bothack36`. Il
  refuse de synchroniser le code tant qu'une série tourne, pour qu'une série
  ne mélange jamais deux versions du bot.
- **Parties isolées, scénarios et rejeux de débogage** : `tools/worker_dev.sh`
  travaille dans un second répertoire, `~/bothack36-dev`. Celui-ci se
  synchronise à tout moment et recompile le moteur si besoin, donc je peux
  tester un correctif pendant qu'une série tourne.
- **Local** : seulement l'édition du code, les tests unitaires et la lecture
  des résultats rapatriés (`runs/worker/`, `runs/worker-dev/`).

Avant ce changement, les scénarios et rejeux tournaient en local, justement
parce qu'on ne pouvait pas mettre le code à jour sous une série en cours.
Le répertoire dev séparé supprime cette contrainte.

## Problèmes ouverts, par priorité

1. **Fixations « examining tile »** en milieu et fin de partie. C'est la
   première cause d'arrêt dans full-w02, à analyser partie par partie.
2. **Combat contre les foules** (Astral, Vallée) sous invincibilité : le bot
   avance trop lentement vers ses objectifs.
3. **Perte de l'anneau de lévitation** avant Méduse : 2 parties bloquées sur
   une île. Le nouveau jalon `item_lost` dira comment la perte se produit.
4. **Scénarios de quête** : un héros téléporté ne reconnaît pas la structure
   du donjon. La quête se teste mieux dans les parties complètes.
5. **Objectif final** : première ascension assistée complète, du début à
   l'offrande, dans une série.
