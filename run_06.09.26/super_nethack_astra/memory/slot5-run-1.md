# Emplacement 5, run 1 — journal (état le plus récent en haut)

STYLE ASTRA (memory/astra-style.md, obligatoire) : la méthode d'origine qui a gagné,
sans BotHack. Lire aussi les « Lessons » de memory/run-1..run-4, slot2-run-1, slot3-run-1.
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore).

## Current state
URGENT: T8514 Dlvl8 (Mines 4, Minetown ?) HP67(68) AC2 XL6, LAST PRAYER T8508 (faim) → prochaine sûre ~T9600+.
W scroll TEMOV = probablement TELEPORTATION (un hobgoblin l'a lue et a disparu).
TELEPATHY. large dog (suit à peu près). $17. AUCUNE nourriture → Hungry vers T8350 : trouver à manger (Minetown ?).
Porté: a THOROUGHLY RUSTY +1 long sword, c +3 small shield, O orcish helm, P ring mail.
Sac: b dagger, f 3 orcish daggers, i ~15 darts, x candle, Q key. Wands: E platinum (engrave: rien), S LIGHT, V CREATE MONSTER.
Inconnus: e thick spellbook ; potions h black, p orange, q murky, w cyan, J dark green ; scrolls l GHOTI, o DUAM XNAHT,
r 2 KO BATE, G ANDOVA BEGARIN, K unlabeled, R READ ME ; rings F diamond, L brass ; gems divers.
DANGERS: black unicorn hostile sur D7 (butt+kick ~14/tour) ; werewolf sur D6 main.
Plan: Minetown (D8 ?) altar/temple/food ; puis Oracle (fountains) pour Excalibur ; Sokoban.
Carte: D4 MINES '>' 70,19. Mines: D5 '<' 69,15 '>' 21,23 ; D6 '<' 29,18 '>' 45,29 ; D7 '<' 38,28.

## Lessons
- Monkeys volent (le small shield porté !) : les tuer à distance ou dès qu'ils sont adjacents ; ils lâchent le butin en mourant.
- chase/explore peuvent buter sur un peaceful (« Really attack? ») : toujours répondre n.
- scripts/rest NE regarde PAS la faim : Fainting à T6485 pendant un repos. Vérifier la ligne 34 (Hungry/Weak) entre chaque appel ; slots/5/rest2 s'arrête sur changement de faim.
- Épée thoroughly rusty = dégâts ridicules (d8+1-3) : les combats durent, les wolves font mal. Excalibur ou autre arme à trouver vite.
- T5452 : boucle F2 sans garde HP contre un small mimic + cave spider → 60 → 9 HP. TOUJOURS mettre une sortie HP dans les boucles de combat (break si HP < 50%).
- #dip à une fountain : chaque essai peut rouiller l'épée et tarir la fountain ; à 1/6 par essai, prévoir plusieurs fountains.
- Prayer pour la faim : T2356 et T4869 — acheter de la nourriture dès qu'on a de l'or, manger les corpses frais.
- Faim : une seule ration au départ ; à T2356 Weak → prayer. Acheter/garder 2+ rations dès que possible.
