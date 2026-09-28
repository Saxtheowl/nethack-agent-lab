# Slot 8 — run 3 (Wish4, style wish_abuser, game on miniforum-worker)

STYLE: memory/style-wish-abuser.md then ASTRA (memory/astra-style.md). Read Lessons of slot8-run-1 (mumak D9) and slot8-run-2 (Orcish Town, hunger, prayer too soon).
Never pass turns in a loop without HP/hunger/"stole" check. Never touch save files.

## DEATH (T17585)
DIED T17585 Dlvl26, XL11, HP 0(122) AC-11: TURNED TO STONE. A cockatrice/chickatrice in a dark room full of orcs (after kicking open a locked door at 36,16) hissed/touched me; status 'Stone' appeared and the explore helper stopped with 'STOP: status', but MY OWN shell loop (for k in 1 2; play8) launched play8 again, which kept walking for the 5 stoning turns. W LIZARD CORPSE was in inventory the whole time: eating it would have cured it.

## Current state
URGENT: T17431 Dlvl25 ('<' 5,25, '>' 15,14; CHAOTIC temple altar 40,19 with priest; peaceful fire giants). HP122(122) AC-11 XL11. TELEPATHY, POISON RES, SHOCK RES, COLD RES(?), FREE ACTION (ring V left hand), Excalibur drain res. LAST PRAYER T17051 (next ok ~T18150). Worn Z +4 cloak, e GDSM (MR), c +4 small shield, q orcish helm, L +1 speed boots. f RING OF CONFLICT, R searching, j/K shock res. w WAND OF DIGGING, z pick-axe, Q unicorn horn, W lizard, l UNCURSED MAGIC LAMP. No missiles. $1932. FOOD: G 3 royal jelly, g tin, n+O 2 eggs. No magic mapping left.

## The wish
- Start-scum attempt 502, fountain quaff at T6 on Dlvl 1: water demon granted a wish.
- Wished "blessed +2 gray dragon scale mail" -> e, worn at T12: AC 6 -> -5. Fountain dried up.

## Map
- D2: '<' 62,27, '>' 70,15 (boulder corridors blocked at bends; dead door 64,26).
- D3: '<' 42,19, '>' 29,17 = GNOMISH MINES; MAIN '>' 5,23 (hidden closet, via hidden door 8,22). ALTAR (neutral, Odin) 41,17. GENERAL STORE (Pakka Pakka) 67-69,18-20, door 66,18: cloudy potion 267 (base 200), yellow gem 2000, blindfold, food ration 60. Sold cursed smoky potion (base 100).
- Mines D4: '<' 26,22, '>' 72,18. BEAR TRAP 46,21.
- Mines D5: '<' 6,25, '>' 73,25. Dart trap 60,14.
- Mines D6: '<' 42,20, '>' 40,28.
- MINETOWN Dlvl7: '<' 12,16. Temple of LOKI (chaotic, priestess) altar 52,21 (entry 49,21 side). Fountain 38,21 (no dipping in town!). Chibougamau general store 39-41,24-26 door 41,23 (scale mail 60, chain mail 100, purple-red potion 533=base 300). Tool shop? 31,25-26.
- Main D4: '<' 4,28, '>' 59,26. Hidden door 20,16 (east wall of top-left room). GRAY OOZE around 52,21. Boulder corridor 40,21 dead.
- ORACLE Dlvl6: '<' 76,14; Delphi center ~40,21 (2 fountains left 41,21 / 40,22). '>' 70,25 (SE room, falling rock trap nearby). SOKOBAN = up stairs on Dlvl7.
- Dlvl7: '<' 63,23, '>' 50,13. Sokoban up-stairs NOT found after ~1700 turns (unexplored: bottom rows 27-30, top-right). Killer bees around (hive?). Skipped Sokoban for now.
- Dlvl8: '<' 61,14, '>' 70,25.
- Dlvl11: '<' 27,12, '>' not found; quantum mechanic (don't eat corpse). Dug down at 42,15.
- Dlvl12: '<' 20,16, '>' 21,24 (boulder at 23,24; enter via door 22,26). Fountains 5,14 / 3,25. Cockatrice killed at 40,23 (corpse).
- Dlvl14: '>' 7,17, '<' 7,26. Trapped (shock) large box 22,27 empty.
- D1: '<' 75,23 (start room, fountain dried). '>' 29,18. Fountains 47,24 and 31,17 (EXCALIBUR at XL5). Hidden door 57,24.

## Lessons
- EXCALIBUR: fountain.c: dipping for Excalibur in MINETOWN makes the fountain disappear -> angry_guards() even on success. Dip OUTSIDE town (Oracle fountains, D1 fountains 47,24 / 31,17). 1/6 per dip at XL5+.
- Homunculus bite = sleep (no sleep res). Monkeys in Minetown steal darts/food (can't take worn armor).
- T2673: raw-moved '2' into a FLOATING EYE (missed, luckily). Never send --raw moves when an 'e' is adjacent; check Neighbors first. Travel (_) avoids falling-rock traps: that's why it 'refused' paths on Mines D5 (trap 20,21).
- Items: z scroll XIXAXA XOXAXA XUXAXA, A scroll XOR OTA, B light blue spellbook (sell for gold/price-id).
- Hunger ~1 nutrition/turn: a food ration lasts ~800 turns. Food is THE constraint: pick up every food item, eat fresh corpses (<30 turns) of safe monsters when Hungry.
- Main D5: '>' 63,14 was HIDDEN UNDER 5 ROCKS ('*' in a room). Check ':' under items in rooms when no '>' is found. '<' 37,23. Sink 30,12. Wood nymph (asleep) in '<' room 29,24.
- T5180: 4 of 6 meals 'Rotten' -> the 2 merged food rations x were probably CURSED (cursed food always triggers rottenfood, half nutrition). Only 1 x left (cursed). Next Weak: PRAY (last prayer T3749).
- Oracle loot: K bronze ring, L combat boots (BUC?), M scroll ASHPD SODALG (not cursed), N orange potion, O tripe, P white gem.
- mkobj.c: a unicorn horn dropped by a killed unicorn is always UNCURSED (no blessorcurse for tools like it). Q = uncursed unicorn horn.
- NEVER read unknown scrolls without a CLOAK: destroy armor takes cloak first, else the BODY ARMOR (GDSM!).
- T8255 Dlvl9: water nymph adjacent at arrival; one hit didn't kill, she STOLE 2 FOOD RATIONS (all my food) and teleported. Hunt her (wounded) to get them back. Next time: step away / go back up if a nymph is adjacent and asleep.
- scripts/session.py pickup_guard bug: '--named Enter' is scanned letter by letter ('e' matched 'e) gray stone'); confirm menus with '--named C-m' instead.
- Dlvl9 THRONE 59,15 is covered by a LOADSTONE ('Thump!' on kick) -> #sit sits on the stone; throne unusable. Throne room 54-68,14-15 cleared, '>' 57,15, '<' 62,27, fountain 62,25.
- IDENTIFIED T8410: DAIYEN FOOELS = identify. L = uncursed +0 SPEED BOOTS (worn). f = uncursed RING OF CONFLICT (emergency). K = uncursed ring of shock resistance. Z +2 dwarvish cloak worn. AC -8.
- Scrolls IDed by reading: ASHPD SODALG=light, XIXAXA=enchant weapon (Excalibur now +2), XOR OTA=magic mapping, ZELGO MER=confuse monster, TEMOV=enchant armor (cloak glowed silver: +2/+3 more), VAS CORP BET MANI=nothing obvious.
- Harness: session.py refuses keys after HP drops 1/5 max below last ack AND <60% max (HP ALARM). Then: stop loops, decide, run slots/8/session ack-hp once (never in a loop).
- Dlvl10: throne 60,20 (Elvenking killed, sat 7x: Wis+1, Con+1, then vanished). Got PICK-AXE z (dig down = escape). '<' 11,16, '>' 38,16.
- Brown pudding bite ROTS leather/cloth (speed boots rotted). Never stand next to one; pick-axe dig down to bypass.
- T9178: ate a monkey corpse found under me (killed by the explore helper long before) -> TAINTED, deathly sick; prayer cured. ONLY eat corpses whose kill turn I know (< 30 turns).
- Dlvl13: '<' 37,28, '>' 60,25. Beehive 50-58,14-16 cleared (T10000, ~20 killer bees at the door chokepoint, asleep). QUEST PORTAL level ('Look for a ...ic transporter'). Quest needs XL14.
- G = lump of royal jelly (1 left, never rots).

## Session end (T10148)
Stopped cleanly for context size, game left running on Dlvl14 '>' (not saved). Next session: read this URGENT line;
priorities: FOOD (1 ration left) -> eat fresh kills, buy rations in any shop; then continue down carefully
(Medusa ~21-24 needs reflection or blindfold/levitation plan; Castle wand of wishing). Quest portal on Dlvl13 (need XL14).
Helpers (run via slots/8/w): play8 (explore+fight whitelist), killadj, tv X Y (travel), grabat X,Y..., lootc X,Y, dipx, rst, m (map).

- T11122 black pudding glob -> POISON RES. T11843 gelatinous cube corpse -> shock res. Gel cube melee = 'frozen' a few turns (ok when alone).
- T11530 Dlvl16: thrown potion -> hallucination while an elf band + yetis + mind flayer + mumak surrounded me (HP 114->40). RING OF CONFLICT turned it around. Unicorn horn took ~8 tries.
- T12113 werejackal bite -> lycanthropy; prayed 820 turns after the last prayer (rnz(350) math ~92% ok) -> purified. Never melee were-critters in @ or d form without need; kill them fast.
- Dlvl15 = rogue level (dark, explore helper useless): dug down with pick-axe. Dlvl16: '<' 25,14, '>' 54,16, fountain 8,17.
- Dlvl17: '<' 44,14, '>' 73,21. Dlvl18: '<' 53,27, '>' 6,17; giant eel pool 12-17,13-18.
- play8 explorer fails in DARK rooms ('no reachable frontier'): travel into the room / to its doors by hand, then rerun.
- Dlvl21: '<' 66,14, fountain 56,16 and 71,22; '>' not found (dug down at 61,20). Dlvl22: THRONE ROOM 21-30,19-22 with BLACK dragon, red/white/green dragons, trolls, ogre king, centaurs: AVOID (fled by zapping digging down at 32,20).
- Floating eye in a corridor with no missiles = stuck: keep daggers/darts; buy/collect missiles.
- Dlvl23: beehive 52-56,21-24 cleared (queen dead, T15569). Fountain 27,25. Trap door somewhere near 28,25.
- STRATEGY (T15990): Medusa = next level probably. No reflection, no blindfold. Medusa level diggable (not hardfloor) -> falling lands at Castle's left side, but the CASTLE needs an instrument (passtune), wand of striking/opening or force bolt/knock to open the drawbridge (zap digging does NOT). Magic lamp needs HOLY WATER (lawful altar + water potions + prayer, or buy clear potions) -> 80% wish (amulet of reflection). Blindfold for sale in Dlvl3 general store. Sustainable food: pray at Weak every ~1000 turns (rnz(350) math: ~96% ok after 1100 turns).
- Dlvl24: '<' 15,17, '>' 55,23, peaceful white unicorn (throw gems for luck when in line). Dlvl25: '<' 5,25, '>' 15,14, chaotic temple 40,19.
- Up-stairs route known for all levels 25->3 EXCEPT Dlvl22 (throne court, arrived by hole) and Dlvl15 (rogue level, arrived by hole).
- play8: look output wraps on 2 lines (fixed: tail -2). A 'Really attack?' prompt can stay on screen after explore bumps a peaceful: answer n.

## Lessons (death of run 3)
- NEVER wrap a helper that can stop on a status in an outer loop that ignores its STOP line. After ANY 'STOP: status' read the status line yourself before the next command.
- 'Stone' / 'You are slowing down' / 'Your limbs are stiffening' = eat the lizard corpse (or acidic corpse) IMMEDIATELY, before anything else. Make helpers treat Stone/Slime as an emergency that aborts the whole command chain (exit code != 0) and prints the cure.
- Cockatrices/chickatrices in DARK rooms are invisible until adjacent; with a lizard on hand the risk is fine only if the agent actually reads the status after every step.
- Whitelisting cockatrice/chickatrice in play8 (auto-melee) was a mistake: they must be handled by hand.
- Run summary: wish GDSM T6 -> Excalibur -> Dlvl26 at T17585, XL11, AC-11, magic lamp (never rubbed), free action, poison/shock/cold res, telepathy. Food was the chronic constraint; prayer at Weak every ~1100 turns worked 4 times.
