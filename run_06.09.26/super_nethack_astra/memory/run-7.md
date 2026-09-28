# Run 7 (emplacement 1) — journal (état le plus récent en haut)

STYLE TARIRU (memory/tariru-style.md, obligatoire pour l'emplacement 1).
Lire les Lessons de run-1..run-6. Rappels : pas de Mines profondes avant XL 6+ ;
farlook chaque ^ ; objets d'urgence avant la mêlée sous 50 % HP ; nourriture.

## DEATH T8289, Dlvl 6 (main), XL7, 4423 pts: "killed by a fire ant"
Chain: T7780 yellow light blinded me on Dlvl6 stairs; an unseen were (werewolf in @ form?)
bit me to HP 1 → prayer T7791 OK (HP 56). "You feel feverish" = LYCANTHROPY from the same
biter. T7822 turned into a werewolf: ring mail and mummy wrapping DESTROYED, sword/shield/
helm/boots dropped. Wolf form killed → back to dwarf naked; Elbereth + re-equip worked; then
transformed again T8222 (#monster gave 2 tame wolves incl. a warg). A fire ant set me on fire
(potions boiled, confusion); wolf HP 0 → dwarf form at 34 HP, naked AC ~10, confused, and my
inline attack loop had NO HP threshold: 34 → 23 → 20 → 1 → 0 in four swings.
Lessons:
- NEVER write an inline fight loop without an HP stop (run 4 lesson, repeated). Use
  slots/1/brawl N MINHP or shoot/hit (they stop under 50%).
- Blind + adjacent unseen monster: do not rest next to it; leave by the stairs at once.
- Lycanthropy ("You feel feverish") is an emergency: cure BEFORE it triggers (pray if the
  timeout allows, holy water, wolfsbane). Remove body armor / cloak if a transformation is
  likely (they are destroyed when you "break out"); keep gear dropped on a known square.
- After reverting to human form next to enemies: Elbereth FIRST (worked the first time),
  then re-equip; never melee naked.
- Fire ants burn potions/scrolls: kill them at range or flee.
- Food ran short (≈1 ration per 800 T): pick up every safe corpse, buy food in Minetown.

## Current state
URGENT: PARTIE TERMINÉE (mort T8289). Ancien état T7225 main Dlvl6 XL7 HP43/56 AC0 (mummy wrapping +1, iron shoes, ring mail rusty, orcish helm, +3 small shield).
Long sword +2 (Skilled). Daggers b,I,x,n,D (tous uncursed). Dwarvish mattock Q (creuser en urgence).
Food: 2 food rations, tripe, slime mold, garlic. Gold 5. Gems: black, violet, white, yellow, green (non testés).
Potions: u CURSED gain level, J CURSED clear (unholy water), z CURSED sky blue(300), i dark(100), l dark green(50), B brilliant blue(50) — uncursed.
Scrolls: V 2 unlabeled. Ring r wooden uncursed (100, pas d'effet visible : hunger? stealth? warning?). Amulet d pyramidal (inconnu, NE PAS porter).
Wands: h speed monster, Z silver = slow monster, e glass (engrave sans message). Spellbook m magenta (ne pas lire).
Minetown = Dlvl7 des Mines (temple Loki chaotic, altar 47,21, lighting shop, delicatessen). Dlvl6 main: > en 68,27.
Prayer: T7791 (HP1, succès). Plan: trouver l'Oracle (Dlvl7-9?) puis Sokoban (niveau au-dessus de l'Oracle).

## Lessons
- T7791 PRAYER (HP 1) : aveugle (yellow light) + monstre invisible qui mord 9-11. Ne pas se reposer aveugle à côté d'un I ; fuir/monter plutôt. Prochaine prière pas avant ~T8800.
- Spotted jelly (j) : son acide passif m'a pris 24 HP en 3 coups de mêlée. Jamais de mêlée contre j/F passifs : `NOMELEE=1 slots/1/shoot j`.
- T~4800: un monkey a volé le +3 small shield PENDANT autoexplore (il ne s'arrête pas pour un voleur qui ne blesse pas). Vérifier AC après chaque autoexplore ; tuer tout Y à distance. Récupéré en tuant le monkey (slots/1/shoot GLYPH).
- Un objet que le pet a porté (il le ramasse puis le lâche) n'est PAS cursed : bon test gratuit.
- Bug harness: `k --named Enter` dans un menu contenant « e) a gray stone » est refusé
  (la lettre e de "Enter"); utiliser `k --raw $'\r'`.
- L'explorateur marque des cibles « dead » dans .runtime/explore-1.json : le vider si
  « no reachable frontier » alors que la carte n'est pas finie.
