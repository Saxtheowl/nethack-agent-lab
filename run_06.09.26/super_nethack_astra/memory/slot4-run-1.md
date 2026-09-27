# Emplacement 4, run 1 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md, obligatoire) : la méthode d'origine qui a gagné,
sans BotHack. Lire aussi les « Lessons » de memory/run-1..run-4, slot2-run-1, slot3-run-1.
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore).

## DEATH T2592, Dlvl 4, XL3, 447 pts : « killed by a giant bat »
Chaîne : HP 31(33) dans un couloir, un giant bat (speed 22, 1d6, erratique) arrive ; j'ai lancé
`fight B 6` (le helper partagé fait jusqu'à 6 attaques SANS vérifier les HP). J'ai raté 4 fois,
le bat a mordu ~8 fois (2 morsures/tour) : 31 → 0 en 4 tours. J'avais 2 potions of healing (k, s
= cloudy, non identifiées) et prayer jamais utilisée (T2592, prayer timeout OK) : une prayer à HP<5 m'aurait sauvée.
Leçons :
- NE JAMAIS utiliser scripts/fight (ni slots/4/fight) : il ne regarde pas les HP. Combat = F+dir UN coup,
  relire HP, recommencer (ou slots/4/ff qui s'arrête dès la perte de HP).
- Giant bat : dégâts rapides (2 attaques/tour) ; à XL1-3 avec AC5, se battre dos au mur/couloir mais surveiller chaque coup.
- Prier dès HP < 1/7 (ici <5) : la prière n'avait jamais servi.
- Une cloudy potion trouvée à côté d'une autre de BUC différent : quaffer une potion inconnue en urgence peut sauver (ici healing).

## Current state
URGENT: T1165 Dlvl2 HP27(27) AC5 XL2, prayer jamais (OK), little dog vivant.
Porté: a +1 long sword (main), c +3 small shield, g orcish helm (testé chien). b dagger (+0 unc), i orcish dagger, j elven dagger (à lancer).
Food: e food ration, f lichen corpse. h orange gem, m red gem, k cloudy potion, l scroll PRATYAVAYAH. Pas d'évasion.
D1: fountain 41,18, '<' 41,16, '>' 4,14. BEAR TRAP 44,17. Silver spear 4,17, key 63,19.
D2: '<' 13,27, '>' 53,13, FOUNTAIN 76,17 (Excalibur à XL5), shop quelque part (non trouvé), boulder corridor 50-63,20.


## Lessons
- T970 : boucle « 6 puis s » sans contrôle HP → goblin m'a mise de 18 à 5 HP. Toujours slots/4/kk (arrêt sur perte HP / monstre adjacent).
- #force avec la dagger b (pas l'épée : lame = risque de casse).
- Bear trap : les déplacements en DIAGONALE décrémentent toujours u.utrap (orthogonal 1/5) → sortir en diagonale.
- explore/travel passe sur un trap caché sous un objet : noter les traps.
