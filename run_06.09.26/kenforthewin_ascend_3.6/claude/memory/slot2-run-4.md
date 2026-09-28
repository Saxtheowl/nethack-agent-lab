# Emplacement 2, run 4 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md).

## DEATH T5695, Dlvl 8, XL6, 3040 pts : « killed by a soldier ant »
Chaîne : Excalibur T2471, AC2. Au Dlvl 8 une MOUNTAIN NYMPH me charme pendant un explore : vole Excalibur, bouclier,
bottes (T4579). Puis, toujours pendant explore (qui ne s'arrête pas sur un vol), elle revient et vole TOUT le reste.
Nue : hill orcs à mains nues, jaguar (prayer à 2 HP T4704), faim (prayer Fainting T5639). 56 tours plus tard un soldier
ant attaque à travers Elbereth : 52 -> 0 HP en 3 tours.
Leçons :
- NYMPHES = menace n°1 : dès qu'un 'n' est sur le niveau, plus d'explore ; la tuer à distance (daggers en quiver) ;
  garder toujours de quoi lancer ; ne jamais la laisser adjacente.
- explore.py ne s'arrête que sur perte de HP : un vol ne l'arrête pas.
- Soldier ants et jaguars attaquent souvent malgré Elbereth quand ils sont adjacents.
- Après avoir tout perdu, remonter tout de suite vers des niveaux faciles au lieu de rester au D8.
- Prières rapprochées = plus de filet ; la faim en a consommé 2 sur 4 -> acheter/garder de la nourriture.

## Dernier état
T5695 Dlvl 8.
 PRAYERS T2279, T4354, T4704 (HP2), T5639 (Fainting) -> PAS avant ~T6700. Pas de nourriture.
 La MOUNTAIN NYMPH du D8 a TOUT (Excalibur, +3 shield, high boots, leather armor, lizard corpse, clé, wand, food...).
 Nue, elle ne peut rien voler mais elle se téléporte quand même. Throne room (court) en 60-69,19-24 : éviter.
IDs : YUM YUM = identify ; VERR YED HORRE = enchant weapon ; HAPAX LEGOMENON & ELAM EBOW base 100 ; VELOX NEB & GNIK SISI VLE base 200 ;
 DAIYEN FOOELS base 300 ; ETAOIN SHRDLU base 50 ; effervescent potion base 150 ; fizzy base 50.
D8 : '<' 7,22 ; '>' 32,14 (room 19-34,13-16) ; throne room 60-69,19-24 (monstres) ; statue Y 38,27.
D7 : '<' 24,24 ; '>' 69,27 ; ALTAR LOKI (chaotique) 55,24 room 49-56,21-27.
D6 : '<' 62,24 (bear trap 60,24) ; '>' 6,15 (room NW 4-8,12-18) ; water nymph en fuite (a mon scroll ELAM EBOW) ; KILGARVAN'S BOOKSTORE 66-71,12-14 (porte 65,12).
D5 : '<' 5,26 (fountain 4,26) ; '>' 38,26.
D4 : '<' 22,17 ; '>' 9,15 ; sink 19,16 ; fountain 41,21.
D3 : '<' 37,12 ; '>' 11,27 ; (fountain 12,27 disparue) ; ANNOOTOK'S GENERAL STORE 8-17,14-17 (porte 9,18) : FORKED WAND 263 zm = base 175
 (cold/fire/lightning/sleep) -> revenir avec de l'or ; square amulet 225 ; mimics tuées. Prix CHA7 = x1.5.
D2 : '<' 13,15 ; '>' 58,21 ; Urignac's weapons (petite, 73-76,23-25, pas de dagger) ; arrow trap 54,22.
D1 : '<' 21,15 ; '>' 15,23 (room SW, porte cachée 10,24) ; FOUNTAINS 9,15 et 16,26 (Excalibur à XL5).

## Lessons
- explore NE S'ARRÊTE PAS quand une nymph vole (pas de perte de HP) : avec une nymph sur le niveau, jamais d'explore ; avancer à la main.
- NYMPHES : ne jamais laisser une nymph approcher ; elles charment et volent même l'arme en main (Excalibur perdue T4579).
  explore ne s'arrête pas sur un monstre visible : regarder chaque 'n' et la tuer à distance (daggers en quiver, jamais vider la quiver).
- `k ,` (non --raw) envoie parfois ',' deux fois (présélection) : utiliser `k , --raw` pour ramasser.
- explore près d'une shop : il peut foncer dans le shopkeeper (« Really attack ? ») : répondre n, et explorer à la main autour des shops.
- Profondeur max ≈ XL+2 tant que XL < 8. Faire les kills soi-même (XP), le familier aide.
- Pas de lecture de scroll inconnue avec une armure de corps irremplaçable portée.
- Elbereth dès qu'un monstre fait >25 % des HP par tour et avant 50 % HP ; vérifier avec ':'.
- Faim : garder 2+ rations, manger les corpses frais (vus mourir < 30 tours), jamais d'elf/zombie.
- Poison instadeath (flèches empoisonnées d'orcs) : poison resistance prioritaire.
- Mes scripts : scratchpad/slot2only/ (le scratchpad est partagé). explore gaspille des tours : préférer G+direction et t.
