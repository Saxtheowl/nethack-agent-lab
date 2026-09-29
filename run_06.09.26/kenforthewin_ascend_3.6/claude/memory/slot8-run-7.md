# Slot 8 — run 7 (Claude8, astra, lawful female dwarven Valkyrie, kitten)

URGENT: RUN 7 IS OVER - DIED T25676 on D29 (Castle): drowned in the moat, 'while taking off clothes' (338098 points, #2 top ten). Start the next slot-8 run with `python3 scripts/next_style.py 8` (astra) and a new journal slot8-run-8.md.

## DEATH (T25676, D29 Castle, XL14, 338098 points)
Standing on the moat square 14,20 in front of the destroyed drawbridge doorway (water walking boots, the only thing
keeping me afloat), fighting the antechamber monsters one at a time. A MOUNTAIN NYMPH (summoned or wandering) came
adjacent on the courtyard side; my sortie script attacked her but she acted first: "The mountain nymph charms you.
You gladly start removing your boots. You fall into the water! You sink like a rock. You drown."
Identified at death: octagonal amulet = versus poison, ruby ring V = FREE ACTION (cursed by the titan), gold ring = regeneration.
Run 7 summary this session (T19992 -> T25676): D26 throne room cleared by Stealth (poison res from a green dragon),
blessed gain level -> XL14, QUEST DONE (Lord Surtur killed, Orb of Fate + Bell of Opening), fire res from a fire giant,
Castle drawbridge destroyed by wresting a wand of striking, minotaurs killed, many Castle monsters killed.

## Lessons of the death (for every slot)
- NEVER stand on water (moat/pool) held up only by water walking boots (or levitation boots/ring) when a nymph,
  succubus/incubus or anything that can make you take off armor may reach you: one charm = instant drowning.
  Kill nymphs at range the moment they appear; better, freeze the square (wand of cold) or fight from land.
- A monster wielding a cockatrice/chickatrice corpse ("swings her corpse") stones you on every hit: leave, wait
  ~300 turns for the corpse to rot away, or kill it at range. A lizard eaten mid-fight can be undone by the next hit.
- An invisible caster that summons nasties (ki-rin, demilich grown to level ~17) FOLLOWS you through level teleport
  if adjacent; kill or teleport it away (wand of teleportation) first.
- Polymorph traps without magic resistance destroyed my elven mithril and cloak of displacement (quest level).
- Wands found on monsters are often EMPTY: 3 wands (striking x2, cold) were (x:0) when I needed them;
  wresting (1/121 per zap) saved two situations (7 and 58 tries).

## Castle notes (T18012+, this session)
- SCREEN COORDS: castle.des map (mx,my) -> screen (mx+9, my+13). East door des(56,8) = screen (65,21), land at (66,21); eels at (66,20)/(66,22). Trap doors screen row 21 x 49,53,57,61,64. Secret doors to dragon alcoves (56,20)/(56,22); dragons (56,18-19),(56,23-24). Storerooms NW (48-54,18-19) NE (58-64,18-19) SW (48-54,23-24) SE (58-64,23-24); their locked secret doors (55,18)(57,18)(55,24)(57,24). North land strip = screen row 13 x 18-62 (water x 9-17 and 63-71); moat west column x=9 rows 13-18, west courtyard (9-13,19-23), maze entrance to it (8,23).
- Telepathy scan (camera at self) T18012: west strip had soldier ant (killed), 2 xans (1 killed), 2 MINOTAURS, a stone giant; throne room has 3 L (liches), N, O, T, X, R, H...; barracks full of soldiers; 8 tower soldiers; 4 D in the alcoves; eels/sharks in the moat.
- LOREM IPSUM is NOT scare monster (a xan attacked me while I stood on it); left on the Castle up stairs (3,16). LOREM = confuse monster / destroy armor / magic mapping.
- Minotaur on the stairs: one round did 37, then 54 (max 76). 3 Excalibur hits did not kill it (15d8 HP). Rule: hit only at HP >= ~110, go up below that; they never follow upstairs.

## Current state
- T416 (resumed by a new agent after the move to kenforthewin_ascend_3.6/claude): D1 mostly explored; '<' 38,15, '>' 46,26. Unexplored west (doors 15,15 and 5,17), ) at 4,28, % at 63,21.
- T1 start room 37-46,13-16, kitten at 38,16. Potion 38,14, food 40,14, tool 39,16, door 39,17.

## Map
- D1: '<' 38,15, '>' 46,26, FOUNTAIN 14,14 (NW room) -> Excalibur dip at XL5 (not a town fountain).
- MINETOWN D7 (mines): '<' 8,26, '>' 68,17. Temple of ODIN (neutral, heard; not found). Izchak? lighting shop 30-32,20-21 (door 31,23). Bnowr Falr's HARDWARE 37-38,17-19 (door 40,18): chest 1022zm, saddle, camera, grease. General store 44-46,14-15 (door 45,17): MIMIC at 44,14, pyramidal amulet 200zm, eggs, tin, scroll. Fountains 43,20 30,26 (NO DIP in town).
- MINES: D4 '<' 16,22 '>' 40,16. D5 '<' 69,25 '>' 29,26 (bugbear killed). D6 '<' 75,12 '>' 28,22 (path west crosses a PIT at 48,22).
- SOKOBAN L1 (Dlvl9 branch, variant 1b = soko4-2, origin 33,15): plan slots/8/soko7/plan1.txt, executor `slots/8/w ./soko7/run.sh FROM TO` (ALL 40 steps done T7270: L1 SOLVED). L2 = variant 2a SOLVED T8300. L3 = variant 3b SOLVED T8700 (plan3.txt + plan3b.txt). L4 (Dlvl6) = variant 4b (ZOO room 45-49,22-28, doors 44,23/25/27 closets, 50,25): wiki solution simulated OK -> slots/8/soko7/plan4.txt (31 lines, origin des (c,r)->(27+c,13+r)). Food ration + 2 slime molds found in L3 '<' room. L4 steps 1-25 done T9160 (Uruk-hai band, pyrolisk, floating eye killed). L4 SOLVED T9439 (Mordor orcs, red naga, 2nd pyrolisk killed; XL9). g = POTION OF HEALING (keep for emergencies). (wiki solution https://nethackwiki.com/wiki/Sokoban_Level_2a; sim script in plan generation; ORTHO=1 mex for push squares). Got 2 food rations S, egg T, ruby ring R, 2 PRIRUTSENIE (=earth) U V.
- D10: '<' 54,24 (fountain 56,23), '>' 58,15, SOKOBAN '<' 13,27 (SW room). Sinks 20,15 and 11,24. POTION SHOP? 7-11,11-16 (door 8,16, not visited). Vault guard heard. Iron bars 36,13.
- D9 = ORACLE (Delphi ~36-47,16-21, Oracle @ ~40,21, centaur statues): '<' 77,13 (NE room, spellbook 71,17), '>' 56,18 (room 54-60,17-19, door 53,18). SOKOBAN = up stairs on D10.
- D8 (main): '<' 14,20, '>' 38,28 (room 38-41,25-28, hidden door 42,26). W room 2-5,22-24 (box emptied, bag of tricks+sleeping potion dropped there).
- D7 (main): '<' 44,28 (T16109), arrived by digging at ~6,16 room 3-6,13-17: '>' 3,17, fountain 4,16 (non-town: dip ok), banded mail 3,15 left.
- D6: '<' 15,15, '>' 71,21 (east), DUG DOWN at 14,16 (hole). (searched SE room east wall 64,26). Rooms NW, middle, small 49-53, NE 62-66, SE 55-65,24-28, SW 9-13. Boulders 35,15 and 45,19 in corridors.
- D5: '<' 57,22, '>' 8,13 (W room with SINK 10,16, peaceful gnome lord). Rust trap 44,17? (arrow ^ at 44,17). East unexplored.
- D4 (main): '<' 6,23, '>' 15,15 (NW room). Arrow trap 34,16. Scale mail 24,25 (left).
- D3: '<' 34,12, '>' 34,27 = probably MINES (the NW '>' 7,14 leads to main D4). SKIBBEREEN'S BOOKSTORE 61-66,23-26 (door 62,22). Locked door 20,26 (no 'Closed' engraving). Large box 49,28 (emptied). SECOND '>' 7,14 (NW room 5-19,13-16; one of the two '>' = Mines). FOUNTAIN 17,25 (SW room, grave 13,26) and FOUNTAIN 51,14 (room 48-52,14-17): EXCALIBUR at XL5. Rolling boulder trap 51,17, squeaky board 52,16.
- D2: '<' 30,18, '>' 72,23 (SE). Locked door 18,22. No Mines branch seen (SW quadrant unexplored).

## Items
- PRICE-ID (D3 bookstore, Cha8 x4/3): KO BATE = IDENTIFY (27). DAIYEN FOOELS = light (50). ELAM EBOW = ENCHANT WEAPON (80). VERR YED HORRE = base 80 (enchant armor/remove curse). base 100: LOREM IPSUM, VELOX NEB, VE FORBRYDERNE, ASHPD SODALG, MAPIRO MAHAMA DIROMAT (mine, o). base 200: XIXAXA XOXAXA XUXAXA.
- p purple-red potion (from box).
- POTIONS IDed by quaffing (T5733, D8): smoky=BLINDNESS, purple-red=HALLUCINATION, cyan=LEVITATION, swirly=HEALING, ruby=fruit juice or see invisible, dark green=SLEEPING.
- SCROLLS: VE FORBRYDERNE = FIRE (read T7676). PRIRUTSENIE = earth. LOREM IPSUM & MAPIRO burned (pyrolisk), unknown.
- ABRA KA DABRA: read by a homunculus on D5 with no visible effect (named 'teleport' but UNSURE).
- w orange gem (unknown). u 2nd ELAM EBOW (enchant weapon) found D4.
- PET THEFT at the bookstore door (kitten drops on the door square 62,22 = free): q KO BATE (IDENTIFY), r ELAM EBOW (ENCHANT WEAPON), s unlabeled (blank), t VE FORBRYDERNE (base 100).
- m BAG OF TRICKS (bit me on #loot). l 7 darts, j orcish dagger. k smoky potion, e dark green potion, o scroll MAPIRO MAHAMA DIROMAT.

## Plan
(T17930) Medusa dead, reflection + water walking in hand. Next: Castle (see URGENT) or level up first (XL14 for the Quest: portal D15 35,27). Get magic resistance before Gehennom if at all possible (wand of wishing -> GDSM; or a cloak of MR).
0. (T12722) Sokoban DONE (bag of holding), Minetown protection DONE (AC-6 then helm stolen -> AC-4). Now descending the main dungeon from D18.
1. Before Medusa (~D21-24): need a way over water (identify snow boots/jungle boots: water walking? levitation?) and gaze protection (reflection, or be blind: no blindfold yet). Price-ID boots at a shop (water walking base 50, elven/kicking 8, fumble 30, levitation 30, jumping 50, speed 50). Unknown scrolls: read in a quiet room with body armor still ON only if needed (destroy armor risk) — better price-ID first.
2. Get a new helmet (any). Keep 2+ food: eat fresh corpses (troll, yeti, owlbear...). Pray only when Weak/low HP and >~1000 turns after T11482.
3. XL14 -> Quest (portal D15 35,27; Valkyrie quest needs fire resistance for lava: gold/ruby ring may be fire res).
4. Castle: wand of wishing; wishes: gray dragon scale mail (MR) or silver (reflection), then the other.

## Lessons (carried over, slot 8 and slot 3)
- Stone/Slime: eat lizard at once; never loop a helper after a STOP without reading status.
- Big Room full: go back up, never dash across. Wand users first. Life saving triggered -> leave.
- Prayer timeout random: never pray twice within ~1000 turns. Food first.
- Never melee an awake nymph; never step into an 'e'; never 'y' at Really attack.
- Read unknown scrolls in a ROOM (earth in corridor), body armor off/with cloak.
- Never dig down next to water/lava; lava = one step out only.

## Lessons (this run)
- T22581-22815 QUEST: Surtur's goal level can have BOTH drawbridges raised (12.5% x 50%): bring a wand of striking or opening (tune does not work there). POLYMORPH TRAPS on quest levels: without magic resistance, becoming a big/handless form DESTROYS body armor and cloak; the trap disappears after triggering. Dying in the polymorphed form returns you to normal with full HP. Fire traps burn boots; sleeping gas traps too. Fire giants carry boulders/wands/food rations; stone giant had a wand of digging.
- T21342-21866 CASTLE FRONT DOOR: the wand of striking was EMPTY: zapping a (0:0) wand wrests the last charge 1/121 per try (took 7 tries) and the portcullis fell ('The portcullis of the drawbridge falls into the moat!'). Minotaurs: 74 damage in one exchange; the CAMERA FLASH at an adjacent minotaur = blind + flee, then finish it. The Castle arrival stairs (3,16) have one access square (3,15) when boulders block 3,17/4,17: fight arrivals there, climb to rest. A monster's CURSED scroll of create monster made a 13-monster zoo (nymphs, werewolf, trapper, baluchitherium...). Castle maze traps: land mine at 5,25, anti-magic 5,27. At the broken drawbridge, standing on the moat square with water walking = 1 attacker at a time, BUT a summoner inside cast summon nasties around me (storm giant, barbed devil, ogre king, dragon) -> 159 -> 77 HP; escaped with a CURSED teleportation scroll (level teleport works from the Castle).
- T20763-21290 D26 THRONE ROOM (dark, court asleep): blinded by a dust vortex, TELEPATHY showed the whole court; with STEALTH I killed 9 dragons, ettin (ettins wake on their own: kill first), trolls, centaurs, ogre king one sleeper at a time (+12k XP). Green dragon corpse = poison res (100%), eat it only when NOT Satiated (resume after interruptions keeps canchoke FALSE). LEAVE A SLEEPING TITAN ALONE... but a troll's wand of magic missile bounced and woke it: summon nasties (purple worm, ape) + curse items (helm, shield, food cursed). Purple worm engulf: kill it from inside (2 hits). Throne sits: Luck>0 -> blindness (not curse), full heal, Wis+1, then it vanished. Trolls revive every ~20-40 turns: kill again for XP. Scanning a dark room for the royal chest: light it (wand of light) then walk it square by square.
- T18660-19830: Valley of the Dead = 3 morgues (wraiths: eat corpses at once = +1 level; ghosts named after players incl. 'Claude8' are NOT bones), vampire bats that rise as vampires, demons, a chameleon (became a purple worm and engulfed me: kill it from inside), liches (a lich cast destroy armor = gloves gone, curse items). An ARCH-LICH arrived at the Valley stairs and summoned nasties: without MR its touch of death is ~2-3% per turn adjacent -> fled upstairs (liches do not follow). Stalkers (trolls, zombies, wraiths, ghosts) FOLLOW you up the stairs: a rock troll followed me and took me to HP 10 (prayer). Rock trolls revive every ~40 turns: eat the corpse (not while Satiated) or leave it on an island it cannot leave. Black pudding: Excalibur hits split it, its bite corrodes the helm; eating its glob gave SHOCK resistance. Werewolf bite (@ or d form) = lycanthropy ('You feel feverish'): the silver shield of reflection falls off at once; pray immediately (cures it). Level teleport OUT of the Castle works (confusion potion + scroll of teleportation) even though the level is no-teleport. Regeneration ring doubles healing but costs ~0.5 nutrition/turn: food rations vanished fast (Weak 520 turns after a ration).
- T18012-18650 CASTLE: minotaurs camp at the arrival stairs and strike first -> better arrive by digging a hole on D28 (random spot in the west strip), cut a gap to the moat with the wand of digging and walk on the water (land monsters cannot follow). A camera flash at yourself = full telepathic scan of the level (camera has 30-99 charges). Engraved Elbereth on the north land strip = safe rest vs sea monsters (not in Gehennom). Quaffing LEVITATION before a fight means you cannot eat the corpses: the red dragon (fire resistance!) was TAINTED at age ~70 -> food poisoning, cured by an uncursed potion of extra healing (it cures sickness). Eat corpses within ~50 turns. Lightning breath destroys closed doors (a blue dragon broke the north alcove door, exposing 2 dragons at once). Close/lock doors behind you: the open back door let a captain in (2 weapon hits ~30/round). Giant eels give +1000 xp each (S_EEL bonus when not amphibious).
- T17685-17741 MEDUSA DONE RIGHT (medusa-1): water walking boots to cross; a WAND OF DIGGING razes closed/locked/secret doors silently even in non-diggable walls (lets you enter her room diagonally without the squeaky board); APPLY AN EXPENSIVE CAMERA AT YOURSELF = blind 1-25 turns (gaze harmless), telepathy shows her; re-flash the camera the moment sight returns (you act before monsters that turn). Zapping teleportation at her sends her away (it ALSO teleports the objects on her square: the Perseus statue flew away; find it later). Then kill her blind in melee (3-4 hits). Perseus statue broken with a wand of striking: shield of reflection. Grease the cloak before walking on water: 2 giant eel wraps slipped off.
- T17100-17320 FOOD CRISIS: fainted once (T17269). Tripe and a rotten egg made me VOMIT (lost nutrition). Tin 'smells like dwarves' = CANNIBALISM for a dwarf: always answer n. Eat big fresh corpses whenever Hungry; carry real rations.
- T16487-16568 MINETOWN DISASTER: blinded by a yellow light (killed it adjacent), then while BLIND my F-direction on an adjacent peaceful gnome did NOT ask 'Really attack?' -> killed it -> 'shrill sound of a guard's whistle' = WATCH ANGRY. Then I killed an attacking (hostile) WATCHMAN -> 'You murderer!' = LUCK -2 AND INTRINSIC TELEPATHY LOST (angry_guards keeps the peaceful malign, so killing them is murder). RULES: while blind never F an unidentified adjacent glyph in a town; never kill watchmen even when they attack - walk away. Luck is now negative: NO PRAYER until fixed (sacrifice at the D27 co-aligned altar resets negative luck to 0 when prayer timeout is 0). Need a floating eye corpse to regain telepathy. T16474 bought EXPENSIVE CAMERA y + CAN OF GREASE z (hardware). T16588 bought 4 CANDLES (A x3 tallow, D x1) at Izchak (need 7 for the Candelabrum; Izchak had no more). Izchak sells oil: BROWN = OIL (333zm) => MAGENTA (mine) = ACID (quaff = cures stoning!). HAPAX LEGOMENON = base 100 (Izchak 133zm) = {destroy armor, confuse/scare monster, magic mapping}. The pyramidal amulet in the general store = STRANGULATION (skip).
- T8321 Sokoban L2 '<' room full (3 wargs, chameleon): an OPEN DOOR does not stop diagonal bites; HP 99->8 in ~6 turns; prayer saved me. Enter such rooms only at full HP, retreat into the corridor behind the door so only the door square touches you.
- T8012 Sokoban L2: 'You hear a monster behind the boulder' for 50 turns = a sleeping guardian naga hatchling in the dark hole corridor. I broke the boulder (Luck -1) needlessly: next time wait more / it was just asleep; spare boulder D used instead (plan2b.txt).
- T7288 ENGRAVE-TESTING an unknown wand = create monster: a wood nymph appeared adjacent and STOLE EXCALIBUR (Sokoban no-teleport saved me: killed her with the pick-axe). Engrave-test wands only with nothing valuable at stake... better: test far from danger and be ready; kill nymphs before anything else.
- T6781 Sokoban L1: 2 soldier ants took 87->22 HP in 3 turns. Soldier ants are the most dangerous early monster: fight at full HP only, pray at HP<=12.
- T4006 EXCALIBUR on the 1st dip (D3 SW fountain, XL5). Both ELAM EBOW read -> +4.
- Pet theft works: stand outside the shop door; the pet drops items on the door square (free).
- WEIGHT > 600 (pick-axe bought) = 'You are carrying too much to get through' on diagonal squeezes between rock: dig one corner with the pick-axe (then re-wield Excalibur!) or drop weight.
- D5: hidden door 33,14 found (east of middle room); D5 door 55,21 unlocked with key.
- slots/8/mex = single-step explorer (no travel): `slots/8/w env IGN=G ./mex 40` (IGN=Gh hid a hostile BUGBEAR: use IGN=G only).
- explore.py is slow in dark rooms and leaves items; follow/walk helpers in slots/8 (run with slots/8/w ./follow N, ./walk DIR N).
- SOKOBAN METHOD that worked: identify the variant from the screen, WebFetch https://nethackwiki.com/wiki/Sokoban_Level_<N><a|b> (ask for the lettered map), expand the move groups, SIMULATE them (walls/boulders/holes, truncate each '*' sequence at the hole it falls into), write "n LABEL X Y moves" plans, run `slots/8/w ./soko7/run.sh FROM TO planX.txt` in background; on FAIL: kill the blocking monster (farlook first), reach the push square with `slots/8/w env ORTHO=1 ./mex 40 --to X,Y`, then resume. Travel refuses to start next to any monster (even peacefuls): use mex with IGN=<glyph>.
- Helpers (all run via slots/8/w): mex (single-step explore/goto), srest TARGET% (single-turn rest under 70%), holdat DIR N (hold a door), shopwait X Y N (wait for the pet at a shop door), walk/follow.
- Hunger: prayer at Weak worked at T2876, T4048, T5310 (~1200 turns apart); fresh ape/tiger corpses are great food.
- T9494-10023 SOKOBAN ZOO DONE with ZERO danger by using STEALTH: opened the LOCKED door with the KEY (never kick: dokick calls wake_nearby()), then walked in and killed every sleeping monster one at a time (disturb() never wakes anything while Stealth; only the attacked one wakes). Zoo had yellow light x2, water elemental, mumak, 4 fire ants, jaguar, owlbear, 3 elf-lords (each had an elven MITHRIL-COAT), warhorse, centaurs, Uruk-hai x10, blue jelly, gold golem; ~5000 gold. From a doorway you do NOT see squares hugging the wall (x=49 rows 22/28): look again after stepping in. A 'boulder' inside a zoo / on a Sokoban level after solving = GIANT MIMIC (2 on soko1-2): telepathy (blind) shows them as 'm'. Giant mimic hits 2x3d6 (26 in one round): attack at full HP.
- Attacking from a square with Elbereth = 'You feel like a hypocrite' = -5 alignment and the engraving is erased (scare monster scroll still works).
- Sokoban prize: the 3 closets 43,23/25/27 (soko1-2), prize closet has burned Elbereth + cursed scare monster = refuge to rest (srest).
- T10288-10312 D7 THRONE: put ALL gold in the bag first (throne 'take gold' only takes open gold), clear the throne square (items on it = 'You sit on the X'), then sit repeatedly: got courtiers (XP), IDENTIFY x3 (Z = wand of teleportation 0:6, BoH uncursed, pink = gain level -> XL11), GENOCIDE (master mind flayer), shock (resisted), lost 13 open gold. Throne vanished after 9 sits.
- Price-ID D10 liquor emporium (Cha 8): golden = EXTRA HEALING (quaffed 'much better'), white = base 100 (restore ability or confusion), puce = 150/200. Shop had 2 mimics (large + giant): in shops, step on items only after farlook of ']' / strange objects.
- F on a peaceful gnome did NOT ask 'Really attack?' here (gnome got angry, -1 align). Farlook every G/h before F near the Mines.
- T10926 PROTECTION: donating 400*XL (<600*XL) to ANY temple priest (cross-aligned OK) gives 2-4 AC the first time (rn1(3,2)): got 3.
- T10961 Selling in a shop: an invisible BLACK LIGHT exploded -> HALLUCINATION ~70 turns. While hallucinating 'Really attack?' is NOT asked for peacefuls (uhitm.c: !Hallucination): never F anything in a shop/town while Hallu; walk away (found a hidden shop door) and wait it out.
- BUC testing: drop everything on any altar with D -> X (unknown BUC) -> '.' select all; pick back up with ',' '.'.
- T11558 D11: mex stopped with a mountain nymph ADJACENT; my first hit did not kill it; she charmed me and STOLE THE DWARVISH IRON HELM (AC -5 -> -3) and teleported. With a nymph adjacent: throwing is too late; hit is ~85%. Better: when mex reports 'n' at distance, throw daggers (b, E) first.
- T12291 Yellow lights: killing one adjacent can still blind (it exploded as I attacked). Waiting out blindness ON the upstairs with telepathy is safe.
- T12535 Rogue level D17: a vampire bat 'dies' and rises as a VAMPIRE LORD (shapeshifter). Rogue level: stairs are '%', food ':', doors are real doors (no diagonal entry), rooms dark: zap the wand of light to see; downstairs can be behind hidden passages -> just dig down with the pick-axe.
- T12675 Soldier ant on D18 came alone: 2 hits, took ~8 HP at AC-4. Fine at full HP.
- T13045 D20 baluchitherium: ~20 HP per round at AC-4 (129 -> 76 in 3 rounds), died after 4 hits. Big hitters: fight at full HP; wand of teleportation Z at them if HP < 50.
- Corpses: 4 of ~10 fresh corpses were 'Rotten' (1/7 each): do not count on one corpse; eat when Hungry, not Weak.
- mex does NOT avoid known traps (walked twice into a falling rock trap): after a trap message, step off manually and travel around it.
