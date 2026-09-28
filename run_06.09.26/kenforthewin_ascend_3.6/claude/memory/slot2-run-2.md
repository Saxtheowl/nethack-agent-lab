# Emplacement 2, run 2 — journal (état le plus récent en haut)

STYLE TARIRU (memory/tariru-style.md, obligatoire) : familier = arme principale au
début, tester le curse par le familier/altar puis porter TOUTE armure non maudite,
daggers en quiver lancées avec f, Elbereth = pause/fuite seulement (jamais de combat
dessus, vérifier avec ':'), Minetown (temple : protection 400×XL) → Sokoban → Mines' End.
Lire aussi les « Lessons » de memory/run-1.md, run-2.md, run-3.md, slot2-run-1.md, slot3-run-1.md.

## DEATH T8469, Dlvl 5 (donjon principal), XL6, 2546 pts : « poisoned by an orcish arrow »
Chaîne : un `t` (travel) vers un ring dans une room sombre du Dlvl 5 ; un Uruk-hai (archer) dans la room a tiré 2 poisoned
orcish arrows ; la 2e touche : « The poison was deadly... » (mort instantanée, pas de poison resistance). HP 56/58 juste avant.
Leçons :
- Sans POISON RESISTANCE, chaque projectile/morsure empoisonné a ~1/30 de chance de tuer net, quels que soient les HP.
  Priorité : poison res (manger des corpses qui la donnent : killer bee, scorpion, soldier ant... ; ring ; Minetown ?).
- Les Uruk-hai/orcs archers tirent de loin : les tuer à distance (wand) ou les approcher en diagonale, jamais traverser
  une room sombre en `t` quand des 'o' hostiles sont sur le niveau (ils ont déjà tiré en Minetown).
- Identifié à la mort : jungle boots = JUMPING BOOTS, VERR YED HORRE = charging (béni), VENZAR BORGAVVE = teleportation,
  spellbooks cancellation + restore ability, effervescent = gain energy, wand of cold (0:2).
- Bilan : Excalibur au 1er dip T5797, télépathie T8393 ; 6 prayers (faim ×4, lycanthropie, food poisoning) : la faim a été
  le vrai problème de toute la partie (garder 2 food rations, manger chaque corpse frais sûr).

## Current state
T7280 Dlvl 7 MINETOWN, XL6, HP 58(58), AC1, $99. Excalibur (Skilled). Chien perdu. Hungry (prier quand Weak : dernière T5170, OK).
PRAYERS : T1878, T3103, T4158, T4887, T5170, T7830 (Weak) -> prochaine sûre ~T8900. Or : 0 (leprechaun D4 a tout volé).
Minetown (Dlvl 7) : '<' 76,18 ; '>' 15,20 ; temple d'ODIN (neutre, prêtresse) altar 52,21 ; Izchak ; bones de Claude (slot 1) + son FANTÔME
 près du temple ; blue jelly 27,15 (ne pas toucher). Protection = 400×XL (2400 à XL6) : pas assez d'or.
Inventaire (BUC testé altar) : a Excalibur, F dagger (quiver), A 10 darts, c +3 small shield, s ring mail, j jungle boots,
C orcish helm, B mummy wrapping, r gauntlets of fumbling (unc), w pick-axe, e lamp, g wand of cold, p jeweled + x copper wands (unc),
v BLESSED scroll VERR YED HORRE, G 2 cursed VENZAR BORGAVVE, D 2 unc effervescent potions, cursed potions H/I/J/K, L cursed agate ring,
n/o spellbooks, gems : 2 red, 2 violet, white, 2 yellowish brown (+1 white/+1 brown maudits), t cursed wolfsbane.
Plan : retour donjon principal (D4 : '>' principal pas encore trouvé, partie est) -> Oracle -> Sokoban (nourriture).
D1 : ALTAR LAWFUL (Tyr) 3,14 ; fountains 6,23 et 22,15 ; '<' 9,24 ; '>' 22,16.
D2 : '<' 11,17 ; '>' 73,25 (room SE, atteinte par la porte du bas 66,16 de la room NE) ; anti-magic trap 10,17.
D3 : '<' 16,25 ; shop quelque part (cash register) ; vault (guard) ; teleport trap 62,26 ; room SE 55-66,24-28.
## Lessons
- '>' introuvable : pick-axe, apply > (2 applications) = trou vers le niveau suivant. PUIS re-wield Excalibur (w a) !
- Leprechaun : le tuer à distance (wand/dagger) avant qu'il ne touche ; sinon tout l'or part.
- Valkyrie : ~1 nutrition/tour ; un corpse de 500 = ~400 tours. Prier quand Weak si la dernière prayer date de >1200 tours.
- Les corpses d'elf peuvent venir d'elf ZOMBIES (déjà vieux) : jamais les manger.
- NE JAMAIS manger un corpse dont je n'ai pas vu la mort il y a < 30 tours (elf tué par le chien = tainted, T5166).
- #force avec une dagger : elle casse (≈1/125 par tour mais arrive). Jamais avec la long sword.
- Rolling boulder trap : deux '0' aux deux bouts d'une rangée = piège au milieu.
- « You flounder » / « trip » = Fumbling : retirer les gants/bottes inconnus portés en dernier.
- AVANT de chercher des portes secrètes : vérifier CHAQUE porte/doorway connue (le '>' du D2 était derrière une porte jamais franchie ; 300 tours perdus).
- Wererat : le tuer à distance (wand/dagger) ; morsure = lycanthropie -> prayer. Transformée en rat : tout l'équipement tombe ; mourir en rat = retour forme naine.
- Risque de prayer : P(échec) = P(rnz(350) >= tours_depuis + 200) ; ~7 % à 870 tours, ~2 % à 1200.
- INCIDENT T3167 : le scratchpad est PARTAGÉ avec d'autres agents ; mon script « ex » avait été écrasé par celui du slot 6 et j'ai lancé UNE fois `slots/6/explore --steps 30` (Claude6, T425). Utiliser uniquement scratchpad/slot2only/ et vérifier « Claude2 » sur la ligne de statut.
- explore marque des cases « mortes » trop vite : vider la liste (garder s/d) si « no reachable frontier » à tort.
- Un script de recherche doit vérifier la position après `t` (travel échoue si un monstre est à côté) et s'arrêter sur perte de HP.
- Le chien mange les corpses avant moi : manger vite les corpses frais ; lichen = réserve.
- Boulder « in vain » dans un couloir : on peut se faufiler si l'inventaire ≤ ~75 de poids (squeeze), mais ici impasse.
