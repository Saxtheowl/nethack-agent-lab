# Emplacement 5, run 1 — journal (état le plus récent en haut)

## DEATH T9719, Dlvl 5 (donjon principal), XL7, 2967 pts : « killed by a fire ant »
Chaîne : une mountain nymph vole le +3 small shield (AC 2 → 6) à T9590 ; en la cherchant sur Dlvl 5,
une fire ant (rapide, 2 morsures + feu) me met de 64 à 19 HP ; une potion orange explose (aveugle).
Prayer impossible (dernière T9483, 236 tours). Scroll of teleportation lu (connu, lisible aveugle) :
fuite réussie, Elbereth gravé, mais l'ant me retrouve, Elbereth s'érode (« lbcreth ») ; j'attaque une
fois à 17 HP → la ant enchaîne feu + morsures (potions/scrolls brûlent) → mort.
Leçons :
- Une fire ant à AC 6 est mortelle : sous ~50 % HP face à un monstre rapide, ne PAS rester au contact.
  Prévoir l'évasion AVANT (Elbereth vérifié + repos loin des couloirs, ou quitter le niveau par l'escalier).
- Après une évasion (teleport), s'éloigner / changer de niveau plutôt que se reposer sur place : les monstres rapides reviennent.
- La prayer comme seule source de nourriture (6 prayers en 9500 tours) laisse sans filet de sécurité en combat.
  Acheter/garder 2+ rations QUAND on n'a pas faim (prix ×2..×4 si Hungry/Weak/Fainting), et manger les corpses frais.
- Épée thoroughly rusty (fountain) = dégâts ridicules : les combats durent trop. Ne tremper qu'à XL5+ et sur une
  fountain qu'on peut « perdre » ; sinon changer d'arme.
- Nymphs/monkeys volent l'armure portée : les tuer à distance (darts/daggers) dès qu'on les voit.
- Mines : les chickatrices de Grotto Town, la black unicorn — trop pour un personnage AC 2 / arme rouillée.

STYLE ASTRA (memory/astra-style.md, obligatoire) : la méthode d'origine qui a gagné,
sans BotHack. Lire aussi les « Lessons » de memory/run-1..run-4, slot2-run-1, slot3-run-1.
Jamais de boucle qui passe des tours sans vérifier les HP (waitpet, rest, explore).

## Current state
URGENT: T9492 Dlvl5 (deli) HP53(68) AC2 XL6, LAST PRAYER T9483 (Fainting) → prochaine sûre ~T10500+.
Prayers réussies: T2356, T4869, T6540 (lycanthropie), T7598, T8508, T9483 — la prayer est ma source de nourriture.
TELEPATHY (visible seulement aveugle). Pas de pet (large dog perdu à Mines D7). $1.
Porté: a THOROUGHLY RUSTY +1 long sword, c +3 small shield, O orcish helm, P ring mail.
Sac: b dagger, f 2 orcish daggers, i 10 darts, x candle, Q key. Wands: E platinum (engrave: rien), S light (x2?), V CREATE MONSTER.
W scroll of TELEPORTATION (identifié). Nourriture: X apple, Y tin.
Inconnus: e thick spellbook ; potions h black, p orange, w cyan, J dark green ; scrolls l GHOTI, o DUAM XNAHT,
r 2 KO BATE, G ANDOVA BEGARIN, K unlabeled, R READ ME ; rings F diamond, L brass ; gems.
Plan: donjon principal : Dlvl 6 (giant ants/wolves près du '<' 67,28), chercher '>' et l'Oracle (fountains) → Excalibur.
Minetown = Mines D8 (Grotto Town, sombre) : CHICKATRICES, fountain 37,27 (interdite), watchmen. Mines D8 '<' 67,15.
Carte: D4 MINES '>' 70,19 ; D4 '>' 26,25 ; D5 '<' 50,14 '>' 34,24, deli 59-61,12-16 (porte 61,17 ; accès par 64,24→63,22→61,18).
D5 mines: anti-magic trap 34,14 bloque le travel (passer à pied).

## Lessons
- Shops : prix de la NOURRITURE ×2 Hungry, ×3 Weak, ×4 Fainting (getprice u.uhs). Acheter quand on n'a pas faim.
- Dlvl 6 : werewolf tué à T9043 (sans nouvelle lycanthropie).
- Monkeys volent (le small shield porté !) : les tuer à distance ou dès qu'ils sont adjacents ; ils lâchent le butin en mourant.
- chase/explore peuvent buter sur un peaceful (« Really attack? ») : toujours répondre n.
- scripts/rest NE regarde PAS la faim : Fainting à T6485 pendant un repos. Vérifier la ligne 34 (Hungry/Weak) entre chaque appel ; slots/5/rest2 s'arrête sur changement de faim.
- Épée thoroughly rusty = dégâts ridicules (d8+1-3) : les combats durent, les wolves font mal. Excalibur ou autre arme à trouver vite.
- T5452 : boucle F2 sans garde HP contre un small mimic + cave spider → 60 → 9 HP. TOUJOURS mettre une sortie HP dans les boucles de combat (break si HP < 50%).
- #dip à une fountain : chaque essai peut rouiller l'épée et tarir la fountain ; à 1/6 par essai, prévoir plusieurs fountains.
- Prayer pour la faim : T2356 et T4869 — acheter de la nourriture dès qu'on a de l'or, manger les corpses frais.
- Faim : une seule ration au départ ; à T2356 Weak → prayer. Acheter/garder 2+ rations dès que possible.
