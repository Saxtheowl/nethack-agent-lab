# PLAN v2 — Minetown ≥80 % (repensé après session de jeu manuelle, 2026-07-10)

## Ce que jouer moi-même a révélé

J'ai piloté une vraie partie touche par touche (daemon `tools/play_daemon.py`,
partie enregistrée dans /tmp/nh-play). Constats décisifs :

1. **Le jeu a déjà un autopilote.** La commande travel `_` + `>` + `.` déplace
   le personnage vers l'escalier connu avec le pathfinding INTERNE de NetHack
   (portes, diagonales, doorways gérés nativement, zéro oscillation). `G<dir>`
   court le long des couloirs. Mon bot refait (mal) en ~2500 pas par niveau ce
   que le jeu fait parfaitement en 3 touches. **~80 % de mes bugs de
   navigation disparaissent si je délègue au jeu.**
2. **La wand of digging vers le bas est fiable à 100 %** (Dlvl 1→4 en ~100
   tours pendant ma partie). Le creusage latéral perce murs et roche (pièces
   fermées résolues instantanément) mais échoue parfois en silence — piste :
   à n'utiliser que comme plan B.
3. **Les barreaux de fer sont des `#`** — mon bot les classait "couloir"
   (source d'échecs silencieux identifiée pendant la partie).
4. **Les charges de wand sont lisibles** dans l'inventaire (`(0:8)`).
5. `^P` = historique des messages (debug in-game).

## Nouvelle architecture (bot v2)

Remplacer le cœur navigation par la délégation au jeu :
- **Aller à un escalier connu** : `_` `>` `.` (ou `<`), une séquence, fini.
- **Explorer** : G-runs dans les 8 directions + visite des ouvertures ;
  le pathfinding maison ne sert plus qu'à choisir la PROCHAINE destination,
  le jeu exécute le déplacement.
- **Niveau récalcitrant** (pas d'escalier trouvé après exploration rapide) :
  percer/creuser à la wand plutôt que fouiller les murs pendant 900 tours.

## Route Minetown optimale

1. Dlvl 1 : trouver `>` (exploration G-run), descendre (l'entrée des Mines
   n'est jamais sur 1).
2. Dlvl 2-4 : explorer pour trouver les `>` ; en essayer un → overview :
   si Mines ✓ ; sinon noter, revenir tenter l'autre. La wand débloque les
   pièces fermées.
3. **Dans les Mines : forer niveau par niveau.** À chaque atterrissage,
   balayage rapide (G-runs) à la recherche des traits de la ville
   (fontaine `{`, portes, autel, boutiques). Ville vue → y marcher (travel).
   Pas de ville après balayage → re-forer. Si on atteint Mine's End (pas de
   descente) → remonter d'un niveau et balayer à fond.
4. Budgets serrés : ~500 tours/niveau max, wand en échappatoire (fuite par
   le sol en cas de danger mortel).

## Mesure

- Local d'abord (12-24 parties) pour dégrossir, Vast (~0,07 $/h, 100-120
  parties/batch) pour valider ≥80 % — sur accord de l'utilisateur.

## Kit labo actuel (consigne user 11/07 : STRICT)

Kit par défaut de la Valkyrie + **une seule modification : GDSM bénie
graissée +2** (auto-portée). Plus de dagues bonus, plus de wands of
digging, plus de rations bonus. Excalibur par trempage (XL5+) reste
(mécanique normale du jeu). Le bot peut utiliser les wands trouvées
dans le donjon (butin légitime).

## Mesures bot v2 (2026-07-10)

| Batch | Taux | Notes |
|---|---|---|
| 3 tests | 2/3 | T=752, 1276 — travel+forage validés |
| v2core (12) | 5/12 (42%) | échecs : 4× timeout Doom:2 (branche), 2 morts Mines profondes (sur-forage) |
| v2b (12) | 5/12 (42%) | succès médian ~1050 tours (T=532 min !) ; restent : timeout Doom:3, un sur-forage Mines:12, morts balayage |

## Migration NetHack 3.6.7 (consigne user 11/07)

Base : 3.6.7 officiel (NetHack-3.6.7_Released), wizard DÉSACTIVÉ (WIZARDS=nobody).
Kit labo porté dans u_init.c 3.6.7 (GDSM+2 bénie graissée, 3 dagues, 2 wands digging, épée déjà de base).
Adaptations bot : NH_PREFIX=nh367, rc sans statuslines/tutorial/suppress_alert, rocher='0', retry inventaire ≥6 items.

| Batch 3.6.7 | Taux | Enseignements |
|---|---|---|
| m367-1 | 4/32 (12%) interrompu | Doom:1 sans `>` trouvable (forage étendu au Dlvl 1) ; **cadavres d'ex-zombies = toujours avariés** (gnome zombie → "gnome corpse" piégeux) ; parties lentes |
| m367-2 | 15/53 (28%) interrompu | Restait : cadavres partagés (vieux cadavre + kill frais sur la même case → manger le vieux), parties lentes 2,9 ticks/s (blocages), Doom:1 avec monstre adjacent bloquant le forage |
| m367-3 | 11/37 (30%) interrompu | 17 terminated : le check wall-time était placé APRÈS le `return` du watchdog → jamais atteint une fois coincé ; diag type : Doom:4, frontier=None mais chemin dispo en ignorant un glyphe de monstre périmé ; le forage (compté en TOURS) ne part pas quand les tours sont gelés |
| m367-4 | 30/93 (32%) | Plus aucun "terminated" (wall-time coupe à 600 s) mais les coincements demeurent : **boutique** (commerçant pacifique dans la porte → l'escalade re-marche en boucle, il fallait forer) ; **Doom:5+ (10 parties)** : arrivé par trou, `<` inconnu, et rush=True poursuivait les `>` → toujours plus profond (1 bot à Doom:14 est tombé dans la Quête !) ; "You don't have anything to zap" non géré → zaps infinis à 0 charge ; morts (26) très variées, surtout en profondeur excessive |
| m367-5 | 47/97 (48%) | Record. Restait : **Doom:4 bloqué (12)** — 2 `>` connus jamais pris, pathfinding maison empoisonné par les bans, oscillation ; **Mines profondes 9-12 (~15)** — g0008 : remonté jusqu'à Mines:5 puis RE-plongé en rush 5→11 en 120 tours sans explorer (la ville re-ratée aller ET retour) ; faim présente dans 20/51 échecs |
| m367-6 | 42/98 (43%) | Aborts en chute (7 familles wall-time contre 24) mais morts dominantes (29) : autopsie grid bug = **mort de faim** (évanouissements, prière unique refusée "Tyr is displeased", 0 nourriture depuis 1000 tours) ; Doom:4 encore 17 (oscillation 2↔3 remettait le timer de forage à zéro à chaque arrivée) ; 2 morts shopkeeper = trou foré dans le plancher de boutique |
| m367-7 | 24/47 (51%) interrompu | 3 rations + corpses élargis + tours cumulés/niveau + amnistie bans + pas de forage près d'un `@`. Interrompu par la consigne kit strict |
| m367-8 | 15/99 (15%) | **Baseline kit strict.** 41 parties bloquées Doom:1-2 → autopsie : **BUG MAJEUR "Invalid direction for 'm' prefix"** — en 3.6.7 `m` exige une direction, la syntaxe `m10s` (héritée 3.7) était invalide : TOUTES les fouilles ne duraient que 1 tour au lieu de 10 depuis la migration ! (masqué avant par les wands qui contournaient les passages cachés) ; portes verrouillées 25, boulders coincés 20 |
| m367-9 | 23/99 (23%) | Syntaxe fouille 3.6.7 : `10s`/`20s`/`s` (sans préfixe m) ; ramassage des wands trouvées + zap-test en dernier recours. Restait : Doom:1-2 timeout ×32 avec carte à peine explorée |
| m367-10 | interrompu | amnistie bans+fouilles (relancé avec l'explorateur en plus) |
| m367-11 | 25/100 (25%) | Explorateur occupancy-map (best_search_spot : composantes inexplorées, bonus impasse, malus fouilles², distance). **Autopsie clé : les timeouts Doom:2 (29) avaient le `>` CONNU** — c'est la chasse à l'escalier de branche qui campait sur le niveau 2 pendant 2500 tours alors que l'escalier des Mines est sur 2, 3 OU 4 équiprobables |
| m367-12 | ? | **Rotation de chasse Doom 2-3-4** : fouiller le niveau le moins travaillé (turns_spent), y rester tant que l'écart <300 tours, préférer les `>` jamais testés au-dessus. Vérifié empiriquement : `10s` fonctionne bien sur le binaire 3.6.7 |

Axes restants (par impact) :
1. Doom 2-4 : trouver l'escalier de branche — le forage descend mais ne "branche" pas ;
   idée : à chaque niveau 2-4, si un seul `>` connu → le tenter systématiquement AVANT de forer
   (l'overview après descente tranche), et re-monter par l'escalier (pas le trou) pour tenter l'autre.
2. Sur-forage : fiabiliser le compteur (reset parasite via mal-parse overview) ;
   mieux : borne absolue Mines dlvl ≥ 9 → remonter.
3. Balayage ville : prioriser la direction des traits de ville dès qu'un seul est aperçu.
