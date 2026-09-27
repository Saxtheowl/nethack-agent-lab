# Emplacement 3, run 2 — journal (état le plus récent en haut)

STYLE TARIRU (memory/tariru-style.md, obligatoire) : familier = arme principale au
début, tester le curse par le familier/altar puis porter TOUTE armure non maudite,
daggers en quiver lancées avec f, Elbereth = pause/fuite seulement (jamais de combat
dessus, vérifier avec ':'), Minetown (temple : protection 400×XL) → Sokoban → Mines' End.
Lire aussi les « Lessons » de memory/run-1.md, run-2.md, run-3.md, slot2-run-1.md, slot3-run-1.md.

## Current state
T5090 Dlvl8 (throne room vidée, chest pillé), XL7, HP65/89, AC1, $158. Large dog avec moi (porte ma dagger b).
PRAYERS : T2068, T3582, T4634 (faim) -> prochaine pas avant ~T5700.
Armes : a Excalibur ; quiver i 2 orcish daggers ; H 3 daggers (BUC inconnu) ; f 3 darts.
Nourriture : E 2 tripe rations, C slime mold, D tin, A LIZARD corpse (garder !).
Outils : B UNICORN HORN (BUC inconnu : tester avant d'appliquer). Wands : m forked (engrave rien), x copper = SLOW MONSTER (« bugs slow down »).
Potions : q murky, v cyan, z orange ; white = invisibility (vu un leprechaun la boire), brown = soin (leprechaun « looks much better »).
Scrolls : k THARR, l GHOTI, n unlabeled, o VELOX NEB, p + F HAPAX LEGOMENON (ne s'empilent pas -> BUC différents), y PHOL ENDE WODAN.
Gems : u 2 yellowish brown, w green, G 2 yellow.
D6 : leprechaun hall 46-51,20-24 (hole 47,22 -> D7), '<' 58,16, '>' 74,13. D7 : '<' 64,19, '>' 22,14.
D8 : '<' 47,16, '>' 61,18 (dans la throne room 61-65,17-20). Oracle pas encore vu (D5-D8) -> Sokoban = niveau au-dessus de l'Oracle.
Des leprechauns invisibles volent mon or en boucle sur D6-D7.
--- état précédent ---
T3870 Dlvl4, XL5, HP64/66, AC1, $8. EXCALIBUR (a, béni, rustproof +1) obtenu au 2e #dip (fountain D4 disparue).
PRAYERS : T2068 (faim), T3582 (Fainting + lycanthropie guérie « purified ») -> pas avant ~T4600.
Dog (grandi) vivant ; il porte ma dagger b (uncursed +0). Quiver : i 2 orcish daggers ; f 3 darts.
Nouveau : cyan potion v, 2 yellowish brown gems u. Nourriture : AUCUNE -> manger les corpses frais (pas kobold, pas chien, pas dwarf).
D5 : '<' 20,14, '>' 53,16. D4 '>' 50,27.
Plan : descendre vers l'Oracle (D5-9) -> Sokoban (niveau au-dessus de l'Oracle, 2e '<').
--- état précédent ---
T2270 Dlvl3, XL3, HP41/41, AC1, $3. Little dog vivant (avec moi). PRAYER T2068 (faim) -> pas avant ~T3100.
Inventaire : +1 long sword, dagger b + 2 orcish daggers i (quiver), 3 darts f, +3 small shield, orcish helm (testé par le chien),
+2 leather armor (achetée 33zm), tripe ration r, scrolls THARR k, GHOTI l, unlabeled n, VELOX NEB o, HAPAX LEGOMENON p,
murky potion q, forked wand m (engrave : aucun message).
D1 : '>' 70,13. D2 : '<' 46,27 ; '>' MINES 67,15 (NE) ; '>' main 30,28 + FOUNTAIN 30,27 (Excalibur à XL5 !).
D3 : '<' 24,15, '>' 38,17. TRAP DOOR vers D4 vers 62-64,12-14 (près de la potion à 65,13, jamais ramassée) : éviter.
D3 : Boyabai's used armor shop 3-15,14-16 (porte 14,17) : « piece of cloth » (cloak magique, 67zm) au sol 13,16,
jungle boots 11zm (elven/kicking), +1 low boots 24zm, leather armor 7zm, crested helmet 67, +1 ring mail 147, ']' à 11,14 = mimic probable.
D4 : '<' 17,17, '>' 50,27, fountain 34,23.

## Lessons
- FAIM : une Valkyrie a faim toutes les ~700 tours ; vérifier Hungry sur la ligne 34 après CHAQUE action groupée (rest, waitpet,
  combat). J'ai raté Hungry/Weak et me suis évanouie (Fainting) au milieu de rats + wererat -> lycanthropie. Prayer a sauvé.
- Ne jamais enchaîner plusieurs explore dans une boucle for : la boucle ne s'arrête pas sur la perte de HP.
- Le chien peut manger le corpse du floating eye : le tuer quand le chien est loin, ou se placer dessus tout de suite.
- explore/travel ne connaissent pas les trap doors jamais vues : je suis tombée 2 fois dans la même trap door au D3 et le chien est resté en haut.
- Le chien ne ramasse jamais d'objet cursed : s'il ramasse/lâche un objet, il est sûr (orcish helm testé ainsi).
- Prix shop : une armure avec enchantement positif n'est jamais cursed à la génération (+2 leather armor = 33zm à Cha 8).
- n<count>s pour chercher (number_pad) ; « 10s » ne marche pas.
