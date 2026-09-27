# Emplacement 2, run 1 — journal (état le plus récent en haut)

Joueuse : Claude2 (Valkyrie naine loyale). Lire d'abord memory/session.md et
les « Lessons » de memory/run-1.md (mort au tour 1467).

## ABANDONNÉE T5530 — décision de l'utilisateur, pas une mort
État : main Dlvl 6 (level above the Oracle, Dlvl 7), XL6, HP 34/75, AC3, $699. Wielding Excalibur (obtained T3172,
first #dip at the Dlvl 1 fountain), telepathy (floating eye eaten T3115), wands of digging and fire, co-aligned
lawful altar on Dlvl 6. Cursed loadstone stuck in pack (from a chest Auto-select). Sokoban '<' not yet found on Dlvl 6.
Leçons principales :
- Never use "A - Auto-select every item" in loot menus; never pick up an unknown gray stone (kick it first: loadstone = "Thump!").
- Peacefuls (gnomes, shopkeepers, priests) block travel silently; always check the cursor position before ',' or raw moves
  (nearly attacked a priest and a shopkeeper; picked up a gray stone by accident).
- Never rest with long search loops without checking HP/messages each call (42 -> 5 HP from a manes).
- Prayer fixes a cursed loadstone (minor trouble) only with Luck >= 1 and prayer timeout < 100.
- Food runs out fast for a Valkyrie: keep 2+ rations, eat fresh corpses, watch Hungry (explore does not stop on it).
- Floating eyes: kill from range with thrown daggers (4th one finally left a corpse -> telepathy).

## Current state
T5165 main Dlvl6, XL6 HP75 AC3, $226. Excalibur (Skilled long sword). Telepathy. Not burdened now (dropped leash etc.)
but CURSED LOADSTONE still in pack (V) -> never pick heavy stuff. Prayer T5107 was "well-pleased" but did NOT fix
the loadstone (needs Luck>=1: action=rn1(Luck+2,1)); next prayer ~T6200+.
Dlvl6: LAWFUL (co-aligned) ALTAR 7,16 in room 4-10,12-17 ; '>' 10,14 SAME ROOM ; '<' 21,27 ; fountain 34,28.
  -> sacrifice fresh corpses here for Luck, then pray to fix loadstone.
IDs: XIXAXA = gold detection, KO BATE = magic mapping, silver wand base150, T jeweled & Y platinum wands (engrave: no msg),
P XOR OTA scroll uncursed unknown, j ABRA KA DABRA (base 50 = light?). Food: d tin, W slime mold.
D4: '<' 9,12, '>' 71,28. D5: '<' 64,16, throne room 73-77,27-28, '>' 14,18.
Next: Dlvl 7+, find Oracle; Sokoban = extra '<' on level above Oracle.
Minetown: '<' 12,25, '>' 68,19. Temple of ODIN (neutral, cross-aligned) altar 56,26 door 51,26.
Dirk's general store 44-46,14-16 (door 45,17): black gem 3333zm = real BLACK OPAL.
Pengalengan's deli 43-45,25-26 (door 46,25). Lighting/tool shops 30-32,20-21 and 37-38,17-19. Fountains 43,20 and 30,26.
Mines D5 '>' 51,24 ; D4 '<' 44,24 '>' 21,23 ; D2 mines '>' 56,21, D2 main '>' 6,15 ; D1 fountain 74,24.
Prayed T1955 (success) -> next prayer not before ~T2900-3000.
Inventory (BUC via altar): a long sword +1, b dagger, n CURSED elven dagger, B orcish dagger, x 7 darts, A cursed dart,
c small shield +3, q CURSED food ration (rotten risk), e oil lamp, o lock pick, t leash, m wand of light,
g silver wand (base 150, engrave no msg: make invisible / striking / undead turning),
scrolls f XIXAXA (sell 50 -> base 100), j ABRA KA DABRA (sell 25 -> base 50 = light?), u KO BATE (sell 50 -> base 100),
potions k CURSED brilliant blue, p 2 murky (base 100), w sky blue (base 100);
sold: emerald (base 150), blessed orange (base 50). gems: several uncursed, r green cursed.
Price ID notes: CHA 8 -> buy x1.33.
Plan: XL5 then Excalibur at D1 fountain 74,24; go main dungeon D2 '>' 6,15 down to Oracle, Sokoban up from level above Oracle.

## Lessons
- NEVER use 'A) Auto-select every item' when looting containers: took a cursed LOADSTONE.
  Take items one by one; never take gray stones.
- NEVER send raw moves right after `t` without checking the cursor: travel silently
  fails when a peaceful is adjacent and the move bumps it ("Really attack the priest/
  shopkeeper?" happened twice — answered n).
- NEVER rest with an 'n20s' loop without checking HP between calls: a manes took me
  42 -> 5 HP (saved by prayer). Rest only in short bursts and read the messages.
- Food: cursed food ration = rotten; Valkyrie gets hungry fast. Buy/keep 2+ rations.
- Peaceful gnomes adjacent block travel (_): travel silently does nothing, so a
  following ',' picks up whatever is at the CURRENT square (picked a gray stone
  once — could have been a loadstone!). Always check position after `t` before ','.
- explore helper keeps "dead" cells per level number in .runtime/explore-2.json;
  when gnomes blocked it, it reports "no reachable frontier" too early — clear
  that level's list.
- Floating eye killed with thrown daggers/darts: no corpse this time.
- Dart traps: 1/10 of poisoned hits can be instadeath without poison res — avoid
  stepping on them repeatedly.
