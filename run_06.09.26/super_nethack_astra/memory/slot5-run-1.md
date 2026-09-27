# Emplacement 5, run 1 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md, obligatoire) : la méthode d'origine qui a gagné,
sans BotHack. Lire aussi les « Lessons » de memory/run-1..run-4, slot2-run-1, slot3-run-1.
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore).

## Current state
URGENT: T6753 Dlvl3 HP68(68) AC2 XL6, LAST PRAYER T6540 (lycanthropie guérie) → prochaine sûre ~T7600+.
TELEPATHY. large dog avec moi. $17.
Porté: a THOROUGHLY RUSTY +1 long sword, c +3 small shield, O orcish helm (pet-testé), P ring mail (pet-testé).
(splint mail DÉTRUITE par la transformation en wolf à T6540.)
Sac: b dagger, f 3 orcish daggers, i ~15 darts, x candle. Nourriture: N lichen corpse, M 2 carrots.
Inconnus: e thick spellbook ; potions h black, p orange, q murky, w cyan, J dark green ; scrolls l GHOTI, o DUAM XNAHT,
r 2 KO BATE, G ANDOVA BEGARIN, K unlabeled ; rings F diamond, L brass ; wand E platinum (engrave: rien) ; gems divers.
DANGER: werewolf sur Dlvl 6 près du '<' (67,28) — ne JAMAIS se laisser mordre en forme d (lycanthropie).
Plan: Mines → Minetown (altar pour BUC, temple), puis Oracle (fountains) pour Excalibur, Sokoban.
Carte: D3 '<' 14,14 '>' 50,24 ; D4 '<' 38,13 '>' 26,25, MINES '>' 70,19 ; D5 '<' 50,14 '>' 34,24, deli 59-61,12-16 ;
D6 '<' 67,28.

## Lessons
- scripts/rest NE regarde PAS la faim : Fainting à T6485 pendant un repos. Vérifier la ligne 34 (Hungry/Weak) entre chaque appel ; slots/5/rest2 s'arrête sur changement de faim.
- Épée thoroughly rusty = dégâts ridicules (d8+1-3) : les combats durent, les wolves font mal. Excalibur ou autre arme à trouver vite.
- T5452 : boucle F2 sans garde HP contre un small mimic + cave spider → 60 → 9 HP. TOUJOURS mettre une sortie HP dans les boucles de combat (break si HP < 50%).
- #dip à une fountain : chaque essai peut rouiller l'épée et tarir la fountain ; à 1/6 par essai, prévoir plusieurs fountains.
- Prayer pour la faim : T2356 et T4869 — acheter de la nourriture dès qu'on a de l'or, manger les corpses frais.
- Faim : une seule ration au départ ; à T2356 Weak → prayer. Acheter/garder 2+ rations dès que possible.
