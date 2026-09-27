# Emplacement 3, run 1 — journal (état le plus récent en haut)

Joueuse : Claude3 (Valkyrie naine loyale). Lire d'abord memory/session.md et
les « Lessons » de memory/run-1.md (mort au tour 1467).

## ABANDONNÉE T5795 — décision de l'utilisateur, pas une mort
État : Dlvl7 (donjon principal), XL7, HP43/65, AC2, $1285, Hungry, debout sur Elbereth dans un zoo
(2 ogres dont un archer avec elven bow, giant beetle, floating eye, spotted jelly autour).
Faits marquants : Excalibur au 1er #dip (T2853), amulet of ESP, jumping boots, elven mithril-coat ;
3 prayers réussies (T3737 faim, T4751 HP3, T5517 HP7) ; puis une water nymph a volé Excalibur,
l'amulette et l'elven shield pendant un repos, et une elven dagger ramassée était maudite (soudée).
Leçons principales :
- Les nymphes volent pendant le repos : les tuer à vue (ou fuir le niveau) avant de se reposer ;
  ne jamais se reposer sans vérifier l'inventaire (arme en main !) après « stole ».
- Ne jamais wield une arme ramassée sans BUC connu (dagger maudite soudée à la main).
- Elbereth en poussière rate ~28 % et s'efface : vérifier avec ':' après chaque gravure et chaque coup reçu ;
  ne protège pas des tirs (ogre avec arc) — sortir de la ligne de tir.
- Les zoos : ne pas y combattre sans issue ; le bruit attire les monstres errants (ogres).
- Surveiller Hungry/Weak : une food ration « Rotten » ne nourrit pas (Fainting à T3737).
- Le niveau Mines dlvl 2 (Dlvl5 ici) contenait le bones de la partie 1 avec le master mind flayer :
  retirer l'amulet of ESP près d'un flayer (sinon chaque blast touche).

## Current state
T4757 Dlvl7, XL7, HP64/65, AC2, $387. PRAYERS : T3737 (faim) et T4751 (HP3) -> NE PAS prier avant ~T5800+.
Nouveau : I/food ration mangée T4722 ; z tripe, H LIZARD CORPSE ; potions J pink, K magenta, D purple-red, x dark ;
scroll G THARR ; F pine wand (engrave: aucun effet -> opening/locking/probing/undead turning/nothing) ;
wand o striking peut-être vide (« Nothing happens »). Werewolf tué T4738 (pas de « feverish » vu).
D7 : '<' 16,12, coffre vide 30,17.
--- état précédent ---
T3502 Dlvl6 (donjon principal), XL6, HP38/59, AC2. $9.
Arme : a EXCALIBUR (+2, béni, rustproof ; obtenu au 1er #dip, fountain D2 disparue). Long sword Basic->Skilled.
Armure : t scale mail (+1?), B elven leather helm, C leather gloves, A riding boots = JUMPING BOOTS.
i amulet of ESP portée + TÉLÉPATHIE intrinsèque (floating eye mangé T3370).
Autres : b dagger, m javelin, o copper wand = STRIKING (quelques charges utilisées), e scroll PRATYAVAYAH MAUDIT,
f fizzy potion BÉNIE, l brilliant blue (unc), x dark potion, v tin, z tripe ration, h lichen corpse,
gems p/y red, q blue, r/w black.
Scrolls identifiés : GARVEN DEH = enchant weapon, KO BATE = destroy armor.
DANGER Dlvl5 des Mines (bones partie 1, MASTER MIND FLAYER). Mines lvl1 = Dlvl4 : '<' 72,28 '>' 8,18.
Donjon : D2 neutral altar 74,17 ; D3 armor shop (petite) ; D4 '<' 9,24 '>' 10,14 ; D5 '<' 35,28 '>' 16,18 (large box vide) ;
D6 '<' 47,16, GRANDE ARMOR SHOP de Ermenak porte 62,17 (GIANT MIMIC à 72,18 déguisé en scale mail : ne pas toucher !).
 Reste en vente : fencing gloves 67 / padded gloves 89 (base 50 : power/dex/fumbling), jungle boots 11 (elven/kicking),
 dwarvish cloak 67, orcish cloak 53, plate mail 800, etc.
Plan : trouver l'Oracle (D5-9) ; Sokoban = '<' supplémentaire du niveau au-dessus de l'Oracle.
Prayer jamais utilisée (OK en cas d'urgence : HP<1/7).

## Lessons
- Ne jamais laisser la boucle de combat continuer sous ~25 HP : à T4749 golem+wolf m'ont mise de 20 à 3 HP en 2 tours.
- explore ne regarde PAS la faim : vérifier Hungry/Weak sur la ligne 34 à chaque appel. Une food ration
  « Blecch! Rotten food! » peut ne rien nourrir -> Fainting à T3737 (sauvée par prayer).
- .runtime/explore-3.json garde des cases « mortes » par numéro de Dlvl (mélange Mines/donjon) :
  si explore dit « no reachable frontier » à tort, supprimer la clé du Dlvl courant.
- Ne pas faire n10s en boucle sans vérifier les HP (un iguana m'a mordue pendant le repos, une wood nymph a volé le helm).
- Deux '@' à l'écran (shopkeeper) : la ligne Neighbors peut être celle du shk ; se fier à « Terminal cursor ».
- Engraver Elbereth dans la poussière échoue ~28% (1/25 par lettre) : toujours vérifier avec ':'.
- Sans casque, les tentacules du mind flayer mangent le cerveau (Int) : un casque bloque 7/8.
- Ne pas lire de scroll inconnu en urgence : KO BATE = destroy armor m'a pris mon bouclier.
- Un monstre qui vient de se déplacer n'attaque pas au même tour : graver Elbereth quand il est à distance 2.
- Ne pas boucler aveuglément les coups de pied (k) : « Dumb move! You strain a muscle ».
- explore dit parfois « no reachable frontier » alors qu'il reste des couloirs : marcher à la main.
- Acid blob / yellow mold : lancer la dagger (t b dir) plutôt que frapper à l'épée.
- NE JAMAIS lancer scripts/session.py sans NH_SLOT=3 (c'est l'écran du slot 1) : utiliser slots/3/session.
