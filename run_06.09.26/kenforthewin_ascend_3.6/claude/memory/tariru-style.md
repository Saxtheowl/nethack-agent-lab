# Tariru style — playbook for ALL SLOTS (fresh restart 2026-09-27, user decision)

Tariru (NAO) ascended 144 of 156 NetHack 3.6 games, and 6 of 6 dwarven
Valkyries. His replays are not reachable; this sheet is built from his xlog,
end-of-game dumps, options file, and the 3.6.7 source. Compared with our slot 1
deaths (run 1: Mines D4 XL3, run 2: Minetown AC 9 XL5).

All 3 slots play this style from their next game. It replaces BotHack/3.4.3
habits (Elbereth melee platform, Elbereth resting as a default).

## 1. Fill every armor slot (run 2 died with AC 9)
- Any armor piece for an EMPTY slot (helm, gloves, boots, cloak, body armor,
  shirt) is worth wearing once it is known not cursed. Something beats nothing.
- Curse test before wearing: drop it on an altar (black flash = cursed), or
  watch the pet: "moves only reluctantly" onto it = cursed. Shops: price it.
- Go and look at every '[' you see (`;` farlook, then walk over it).
- Dwarven Valk: Mines gnomes/dwarves are mostly PEACEFUL, so no free armor
  from them. Use shops, floors, hostile dwarves, altar-tested finds.
- Target AC <= 3 before Minetown, AC <= 0 before going below Dlvl 10.

## 2. Fight at range (Tariru: stacks of blessed +5 shuriken quivered, ~11 wands)
- For a Valkyrie the ranged weapon is the DAGGER (Valk can reach Expert).
  Pick up every dagger (orcish/elven/plain, BUC-test them), quiver them (`Q`),
  throw with `f` + direction at monsters while they approach, pick them back up.
- #enhance dagger when possible. Kill thieves (monkeys, nymphs) at range
  before they get adjacent — a monkey stole the shield in run 2.
- Engrave-test every unknown wand when safe (`E`, then the wand); name it.
  Striking/sleep/cold/fire wands are ranged weapons too.

## 3. Elbereth — 3.6.7 rules (checked in source), NOT the BotHack/3.4.3 way
In 3.4.3 (BotHack era) you could melee from an Elbereth square for free. In
3.6.7 that tactic is dead. Exact 3.6.7 rules:
- Works only while YOU stand on it, and only if "Elbereth" is the ONLY text
  on the square (answer `n` to "add to the current engraving?").
- Attacking a scared monster from it (melee OR thrown weapon) ERASES it at
  once, even burned, and costs -5 alignment ("You feel like a hypocrite").
- Ignored by: @ (humans AND elves, e.g. Woodland-elves, watchmen), minotaurs,
  shopkeepers, guards, priests, peacefuls, blind monsters; useless in
  Gehennom. It never stops ranged attacks (arrows, wands, spells, breath).
- Dust: 1/25 typo per letter (~28% broken at write). In 3.6.7 it does NOT
  erode when monsters flee from it, only from your own actions (fighting,
  throwing, walking on/off, rarely by itself). Always `:` after engraving.
- Run 1+2 data: 19 engravings, about half read back broken ("E5Pereth",
  "F|bereth"...), then resting or fighting on them. Slot 2 never uses it and
  is the healthiest player.
How Tariru used it (video reviews of his 3.6.0 streak): a lot EARLY, before
eating a corpse or when something too strong keeps coming, as a pause while
his PET fights or until he can THROW at the monster once it steps away. Much
less once strong (AC -8). Never as a melee platform.

## 4. Route (Tariru: Sokoban prize 137/144, Mines' End luckstone 92/144)
- He finishes Sokoban and gets the luckstone almost every game.
- Do not go deep into the Mines at XL < 5 or AC > 4. Minetown for temple/altar
  and shops, then Sokoban, then Mines' End when strong enough.

## 5. Stop signals (from Tariru's MSGTYPE=stop list)
Stop everything and deal with it when you read: "You are beginning to feel
weak", "You feel deathly sick", "You are slowing down", "Your limbs are
stiffening", "turning a little green", "It constricts your throat", "The
python grabs you", "You find a polymorph trap".
- Keep 2+ food items. Never fight while Weak: eat, or pray if timeout is OK.
- After a prayer: DISENGAGE (upstairs, rest far away). Prayer timeout ~500-1000.

## 6. Early-game habits seen in Tariru's games (video reviews, 3.6.0 streak)
- Traps: in rooms he steps where his PET has already walked; searches a lot
  early; #untrap-checks boxes many times before opening.
- Pet = main weapon early: waits for the pet before fighting anything
  dangerous, keeps it alive (leash later: a leashed pet whines near traps).
- Mines: fights next to the UPSTAIRS, kills from range, lets the pet work,
  goes back up to heal when hurt. Levels are cleared before going deeper.
- Curse test with the pet ("moves only reluctantly" = cursed), then puts on
  EVERY non-cursed armor: even heavy plate mail at AC 10 ("he takes anything
  at the moment"), AC 10 → 3 at once. AC 0 by the Mines, -4 with protection.
- Buys PROTECTION early from the Minetown temple priest: #chat, donate
  EXACTLY 400×XL gold (must be < 600×XL; checked in priest.c). First time
  = -2 to -4 AC, then -1 each time. Cheaper at low XL: keep gold, sell gems.
- Engrave-tests every new wand IMMEDIATELY, not later.
- Shops: price-identifies; throws a gold piece along each row to find mimics.
- Tracks his prayer timeout. The reviewer says he sometimes uses a low-HP
  prayer early (~T600) to raise max HP; not seen in game #47 (section 8).
- Route: Minetown (temple, protection) → back to the main dungeon → Sokoban
  → Mines' End later (with AC -7).

## 7. Safety habits
- Unknown scrolls/potions only when safe and HP near full, never in an emergency.
- Never select "A - Auto-select every item" in pickup/loot menus; pick items one
  by one. Never pick up an unknown gray stone `*`: kick it first (a loadstone
  goes "Thump!" and does not move). Slot 2 is stuck with a cursed loadstone.
- Check the PETS line before any `F` attack; answer `n` to "Really attack?".
- Luck matters (Tariru ends "extremely lucky"): no pet/peaceful kills.
