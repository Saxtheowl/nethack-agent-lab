# Emplacement 2, run 2 — journal (état le plus récent en haut)

STYLE TARIRU (memory/tariru-style.md, obligatoire) : familier = arme principale au
début, tester le curse par le familier/altar puis porter TOUTE armure non maudite,
daggers en quiver lancées avec f, Elbereth = pause/fuite seulement (jamais de combat
dessus, vérifier avec ':'), Minetown (temple : protection 400×XL) → Sokoban → Mines' End.
Lire aussi les « Lessons » de memory/run-1.md, run-2.md, run-3.md, slot2-run-1.md, slot3-run-1.md.

## Current state
T5797 Dlvl 3, XL5, HP 48(48), AC2, $32. EXCALIBUR (1er dip, fountain D3 disparue). Long sword Skilled. Chien PERDU (Mines D5).
PRAYERS : T1878, T3103, T4158, T4887, T5170 -> prochaine pas avant ~T6400.
Inventaire : a Excalibur, c +3 small shield, s ring mail, j jungle boots, r gauntlets of fumbling (à vendre), w PICK-AXE,
e oil lamp, g WAND OF COLD, p jeweled wand + x copper wand (engrave : rien), t sprig of wolfsbane, v scroll VERR YED HORRE,
n mottled + o thin spellbooks, gems u white, y violet, z 2 yellowish brown. Pas de dagger (cassée). Pas de nourriture.
D4 : '<' 59,20 ; '>' 22,26 = ENTRÉE DES MINES (le '>' principal du D4 pas trouvé) ; rolling boulder trap 22,24.
D5 (Mines 1) : '<' 3,24 ; '>' 70,23 ; anti-magic 60,23.
D6 (Mines 2) : '<' 38,27 ; '>' 29,15 ; land mine (pit) 21,26 ; gray stone 8,25 (ne pas prendre).
D3 : '>' 68,17 (room NE), liquor emporium d'Ossipewsk (porte 20,15).
D1 : ALTAR LAWFUL (Tyr) 3,14 ; fountains 6,23 et 22,15 ; '<' 9,24 ; '>' 22,16.
D2 : '<' 11,17 ; '>' 73,25 (room SE, atteinte par la porte du bas 66,16 de la room NE) ; anti-magic trap 10,17.
D3 : '<' 16,25 ; shop quelque part (cash register) ; vault (guard) ; teleport trap 62,26 ; room SE 55-66,24-28.
## Lessons
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
