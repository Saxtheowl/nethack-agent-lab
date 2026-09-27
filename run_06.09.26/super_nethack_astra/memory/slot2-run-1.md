# Emplacement 2, run 1 — journal (état le plus récent en haut)

Joueuse : Claude2 (Valkyrie naine loyale). Lire d'abord memory/session.md et
les « Lessons » de memory/run-1.md (mort au tour 1467).

## Current state
T2555 MINETOWN = Mines Dlvl6 (Bustling-type town, trees). XL4, HP54, AC6, $0. Not hungry (ate ration T2555).
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
