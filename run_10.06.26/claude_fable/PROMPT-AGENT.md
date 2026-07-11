# Question posée (2026-07-11)

> « Réunis l'ensemble de ma demande depuis le début, comme si tu voulais faire
> un prompt complet que tu enverrais à un agent pour qu'il fasse la même tâche
> que toi. » — précisé ensuite : « juste le prompt qui reproduirait ce que tu
> fais, pas tout depuis le début. »

# Le prompt (reproduit la tâche en cours)

```
MISSION : Amener un bot NetHack à ≥80 % de réussite sur l'objectif "entrer dans
Minetown" (être à ≤3 cases d'une porte/fontaine/autel de la ville), en vue à
terme de terminer le jeu (ascension). Travaille en autonomie complète, en
français, dans un unique répertoire de travail.

LE JEU :
- NetHack 3.6.7 officiel (tag git NetHack-3.6.7_Released), compilé depuis les
  sources, interface tty, AUCUN mode wizard ni triche dans les parties mesurées
  (sysconf WIZARDS=nobody).
- Une seule modification autorisée du source (u_init.c, kit de départ de la
  Valkyrie) : gray dragon scale mail bénie graissée +2, 3 dagues, 2 wands of
  digging (12 charges), en plus du kit normal (épée longue +1, bouclier, ration).
- Personnage : Valkyrie naine loyale, sans familier (pettype:none), bones off.

ARCHITECTURE (existante, à maintenir) :
- Harnais Python : pty + émulateur de terminal pyte ; parsing écran (carte
  21x80, ligne de statut "Dlvl/HP/T:", messages ligne 0, menus "(end)") ;
  playgrounds isolés par partie pour le parallélisme ; enregistrement ttyrec.
- Bot symbolique (bot/brain.py) : boucle tick → urgences (prière si HP≤max/7
  et >500 tours depuis la dernière, Elbereth, fuite par forage) → faim (manger
  cadavres frais de ses kills, rations) → combat (mêlée sauf œils
  flottants/moisissures ; dagues lancées sur les œils) → navigation.
- Navigation : DÉLÉGUER au jeu autant que possible — commande travel `_` `>`
  `.` pour rejoindre les escaliers (pathfinding interne du jeu), G-runs pour
  les couloirs ; pathfinding maison (BFS) seulement en secours ; wand of
  digging pour descendre (zap `>`) et percer les niveaux bloqués.
- Route Minetown : Doom 1-4 trouver l'escalier de branche des Mines (explorer,
  tester chaque `>` et lire ^O overview : "The Gnomish Mines"), puis dans les
  Mines forer niveau par niveau avec balayage ~400 tours par atterrissage pour
  détecter la ville (fontaine `{`, portes, autel), y marcher = succès.
- Pièges connus du harnais : `--More--` peut être sur N'IMPORTE quelle ligne ;
  ne jamais ingérer un écran contenant un overlay dans la mémoire de carte ;
  mouvements échoués en silence (!cmdassist) → bannir l'arête après 3 échecs,
  bans expirables 400 tours, permanents à 6 échecs ; les bruits ambiants
  ("You hear...") interrompent les recherches multi-tours (compter les tours
  RÉELS consommés) ; barreaux de fer = `#` bleu infranchissable ; en 3.6.7 le
  rocher est `0` ; prompt "Really attack" = pacifique (répondre n et marquer).

MÉTHODE D'ITÉRATION (le cœur de la tâche) :
1. Mesurer : batch de 100 parties identiques sur une instance CPU Vast.ai
   louée (~24 cœurs, ~0,07 $/h, budget dur 2 $ — détruire l'instance avant
   dépassement ; batchs de 100 ≈ 1 h ≈ 0,08 $). En local (4 cœurs) seulement
   les sanity-checks. runner/run_batch.py -n 100 -j 20.
2. Autopsier : chaque partie écrit meta.json (résultat, cause de mort xlogfile,
   profondeur), state.json (mémoire du bot), bot.log (messages + compteurs
   d'actions par tick), game.ttyrec (replay). Classer les échecs en masse
   (mass_diag.py), identifier LA famille dominante.
3. Corriger LA cause dominante dans le code du bot (une vraie logique, pas un
   paramètre au hasard), sanity locale, redéployer (scp + tar), relancer.
4. Répéter. Ne jamais conclure sur <30 parties (bruit ±15 pts). Si le taux
   stagne 2 batchs de suite : disséquer UN cas à la main (carte + logs tick
   par tick), et envisager de JOUER soi-même une partie via un petit démon
   pty interactif pour découvrir les mécaniques manquantes (c'est ainsi qu'on
   a trouvé travel, les barreaux, le forage latéral).
5. Journal de bord dans PLAN.md : chaque batch, taux, enseignements. Viewer
   web de replays (FastAPI + xterm.js, port 8086) alimenté avec les parties
   notables pour que l'utilisateur puisse regarder et critiquer.

RÈGLES D'EXPLOITATION :
- ssh vers l'instance : jamais `pkill motif` et une commande contenant ce
  motif dans la MÊME ligne (auto-suicide du shell) ; patterns pkill avec
  brackets ("run_batc[h]").
- Budget : suivre le coût (durée × prix/h), tout arrêter et détruire
  l'instance si l'utilisateur le demande ou si 2 $ atteints.
- Rendre compte à l'utilisateur : taux et causes d'échec à chaque jalon,
  transparence totale sur ce qui est modifié dans le jeu, prévenir dès que
  80 % est atteint et confirmé sur 100 parties.
```
