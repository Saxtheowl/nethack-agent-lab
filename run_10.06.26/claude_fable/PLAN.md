# Mission : terminer NetHack 3.7 (ascension) par un agent autonome

Date : 2026-06-10. Répertoire de travail unique : `claude_fable/`.

## 1. État de l'art (juin 2026)

**Personne n'a jamais ascensionné NetHack avec un agent non humain sur les
versions modernes.** Résumé des approches :

| Approche | Meilleur résultat | Référence |
|---|---|---|
| Bot symbolique (terminal scraping) | **Ascensions réelles** sur NetHack 3.4.3+NAO (~5–15 %/partie, Valkyrie naine) | BotHack (krajj7, 2015) |
| Bot symbolique sur NLE (3.6.6) | Vainqueur NetHack Challenge 2021, score médian ~10k, jamais d'ascension | AutoAscend |
| RL (PPO, IMPALA…) | Très loin derrière AutoAscend ; le score incite à farmer, pas à descendre | NLE papers, "Revisiting the NLE" (ICLR 2026) |
| Imitation (transformers sur 3G de parties humaines) | 1.7× le SOTA offline, niveau humain non atteint | Tuyls et al. 2023, Dungeons & Data |
| LLM agents | Dlvl 10 max (GPT 5.2, BALROG ~12.6 %), Claude Opus 4.5 dlvl 5 | BALROG (ICLR 2025), glyphbox (2026) |

Leçons : (a) seule l'approche **symbolique** a déjà gagné une partie complète ;
(b) le RL/LLM échoue sur l'horizon long (~50k tours) et le raisonnement spatial ;
(c) la version cible 3.7 n'a **aucun environnement NLE** (NLE = 3.6.6) ni bot existant.

## 2. Stratégie retenue

1. **Harnais maison pour NetHack 3.7 réel** (pas NLE) : pty + émulation
   d'écran (pyte), parsing carte/statut/menus — comme BotHack mais en Python,
   contre le binaire 3.7.0 compilé depuis la branche officielle `NetHack-3.7`.
2. **Bot symbolique incrémental**, validé par jalons mesurables :
   - **Jalon 1 (en cours)** : Valkyrie naine → Minetown, ≥ 80 % de réussite.
   - Jalon 2 : Mine's End (pioche) + Sokoban (préparation) ;
   - Jalon 3 : Quête Valkyrie + Château (wand of wishing) ;
   - Jalon 4 : Géhenne, vol de l'Amulette, Planes — ascension.
3. **Itération pilotée par les statistiques de mort** : lancer des centaines de
   parties, agréger `xlogfile` (cause, niveau), corriger la première cause,
   re-mesurer. C'est la méthode qui a fait gagner BotHack.
4. **Vast AI** pour la masse : le harnais est CPU-only, ~1 cœur/partie.
   Une machine 32–64 cœurs fait des batchs de centaines de parties/heure.
   Livrable : image Docker reproductible + script de collecte des résultats.

## 3. Choix techniques clés

- **Valkyrie naine, loyale, sans familier** (`pettype:none`) : meilleure
  survie early game, nains/gnomes des Mines pacifiques, prière fiable.
- Détection de branche par `^O` (overview) : fiable, format vérifié.
- Détection Minetown : niveau des Mines avec portes/fontaines/autel.
- Morts analysées via `xlogfile` (death=, deathlev=, turns=).
- Playgrounds isolés par partie (symlinks) → parallélisme sans verrous.
- Bones désactivés (`!bones`) pour la reproductibilité.

## 4. Layout du dépôt

```
claude_fable/
├── PLAN.md             ← ce fichier
├── config/nethackrc    ← options du bot
├── nh370/              ← NetHack 3.7.0 compilé (préfixe local)
├── third_party/        ← sources: nethack-3.7, bothack, autoascend, nle
├── bot/                ← le bot (term, screen, game, level, brain, main)
├── runner/             ← batchs parallèles + agrégation stats
└── venv/               ← python + pyte
```

## 5. Journal d'itération (jalon Minetown)

| Batch | N | Succès | Enseignements / correctifs |
|---|---|---|---|
| 002 | 6 | 0 | Mort de faim avec ration (flag Weak≠Hungry) ; porte de boutique défoncée → tué par commerçant ; boucle Elbereth mortelle |
| 003 | 8 | 0 | Bump infini sur commerçant `@` (pas de prompt) ; `s` refusé si monstre visible (3.7 : préfixe `m` requis) ; collé au lichen ; glyphes fantômes (overlays incrustés dans la mémoire de carte) |
| 004 | 10 | 0 | Pollution carte par popups (`--More--` multi-lignes) ; descente à HP bas (mort/chaton) ; cadavre pourri mangé (kill d'autrui) ; poches sombres inexplorées → entrée des Mines ratée → morts à Doom:4-5 |
| 005 | 12 | 0 | Boucle prompt "Call a scroll" (getlin) ; piège connu en boucle ; coincé 9500 tours derrière un œil flottant (ban de tuile jamais levé) ; "hobbit is in the way" |
| 006 | 12 | **2** | Premiers succès ! Boucle eat ("cannot eat that" → lettres du prompt = vérité) ; colère de Tyr (prière sur-utilisée → stop si dieu fâché) ; curseur pas sur '@' → validation assouplie ; lichen harceleur |
| 007 | 15 | 1 | Dédup messages cassait les bans ; pending_eat en diagonale de porte (ban partagé dans step_dir) ; wererat `@` intouchable → riposte autorisée ; seuils Elbereth recalés (prière seulement ≤max/7) |
| 008 | 7 (tué) | 0 | Escalier non testé sur niveau supérieur → remonter le chercher ; sondes depuis bouts de couloirs ; **mur de gnomes pacifiques bloquait même le pathfinding de secours** ; Elbereth effacé par nos attaques → attendre ; budget de recherche 400/niveau |
| 009 | 15 | 0* | (*mixte, fixes en cours de batch) Porte boutique = ban dur ; pièce fermée → recherche périmétrale ; budget sondes 250 + recherche 400-800 ; timeout niveau 3000 tours ; lichen toujours mangeable ; **descente paresseuse** (escalier connu → on y va, fini le perfectionnisme) |
| 010 | 15 | **3 (20%)** | `\`` = rocher/statue 3.7 (pas un objet !) ; monstre invisible ; oscillation → perturbation aléatoire ; "under attack" → ignorer les marquages périmés ; mindless ≠ Elbereth → fuir les lents ; ne plus effacer Elbereth en frappant |
| 011 | 15 | **3 (20%)** | Morts ↓, aborts "route bloquée" ↑ : grappes de bans diagonaux sol-sol (transitoires devenus permanents) partitionnaient le graphe → **bans expirables (400 tours)** ; #enhance ; mêlée forcée après 6 attentes ; budget Mines réduit ; branche "Other" = relecture |
| 012 | 15 | 0 | **Régression** : porte "différée" re-traversée par les chemins ignore → boucle 3000 tours. Retour au ban dur + phase désespoir (débannir et kicker en dernier recours). Aussi : chasse-remontée si aucun `>` ; chute dans les Mines → remonter chercher la ville ; funnel anti-meute ; commerçant attaqué (flag were périmé → timer 25 tours) ; "thunders" |
| 013 | 15 | **4 (26,7%)** | Code gelé — meilleur batch. Restant : meutes/combats à HP bas (6 morts), routes bloquées (5 timeouts). Mêlée d'œil = mort différée (paralysie + arrivant) → abandonnée ; force-attaque sur nuage de vapeur → monstres uniquement ; nuage persistant → traverser après 3 refus |
| 014 | 15 | 0 | Vague mi-batch (lance pas encore là) — abandonné au profit de Vast |
| Vast v1 | 31 | 1 | (pré-armure) 61% morts combat |
| Vast v2 | 120 | 10 (8%) | **GDSM départ** : morts 61%→13% ; blocages nav = 65% → analyse de masse (mass_diag.py) |
| Vast v3 | 120 | 13 (11%) | **Statues 3.7 = glyphes de monstres !** (corrigé) ; 3 dagues départ ; critère "entrer dans la ville" ; reste : **oscillation de cible** (23 cas probe-reachable) |
| Vast v5 | 119 | 13 (11%) | Sticky targets + épée/Excalibur + prière 500 — insuffisant : "stairs-unreachable-hard" domine (21) = exploration trop restrictive |
| Vast v6 | 120 | ? | **Explorateur unifié** : BFS où l'inconnu est traversable (remplace frontière-visited + sondes restreintes), bans expirables comme seul filtre |

## 6. Prochaines étapes

- [ ] Jalon 1 : ≥80 % Minetown sur ≥50 parties (itération en cours)
- [ ] Runner Vast AI (Dockerfile + provisioning par API)
- [ ] Étendre la couche tactique (Elbereth systématique, fuite, lancer de dagues)
- [ ] Port des stratégies BotHack phase par phase (réf. `third_party/bothack`)
