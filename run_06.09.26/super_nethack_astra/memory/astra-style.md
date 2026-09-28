# Astra style — the original method that ascended (1 win in 3 runs)

Source: https://kenforthewin.github.io/blog/posts/llm-nethack-ascension/ and the
kenforthewin/nethack_astra repo (journals run-2/run-3, emergency JSON).
Used by SLOTS 2 AND 3 after their next death (slot 1 stays Tariru style).
No BotHack: no bot heuristics, no autoplay loops, no "Elbereth platform"; the
LLM decides every non-trivial action itself, from the screen it just read.

## 1. How Astra played, turn by turn
- Read the screen before every decision (compact view: messages, map rows,
  status, neighbours, coordinates). Never act on a stale observation.
- Checked batching only for routine movement: a step is sent, the result is
  re-read and checked (HP, turn, level, position, conditions, nearby monsters);
  the batch stops on anything new. Combat = ONE command at a time, re-read
  after each blow. Guards refuse batches under 2/3 HP.
- Farlook (`look X Y`) every unknown monster or object before interacting.
- Research freely: wiki, spoilers, and the NetHack source in
  engine/nethack-3.6.7/src when a rule matters (Astra read the source often).

## 2. Memory = two files, kept current
- The run journal (memory/slotN-run-M.md): state at the top, identified items,
  resistances, threats, plans, lessons.
- An "urgent" line at the top of Current state, rewritten at every significant
  event, like Astra's emergency reference: `T, Dlvl, position, HP/max, AC, XL,
  prayer timeout (last prayer turn), what is worn/wielded (letters), key
  consumables (escape items, healing, unicorn horn), active dangers`.
- Maps and item identities belong to ONE run only; never reuse old guesses.

## 3. Build your own helpers when language is unreliable
- Astra wrote route planning, Sokoban solving and inventory helpers instead of
  doing error-prone work in prose. You may write NEW helpers under slots/N/
  (never edit shared scripts/, web/, config/): e.g. a Sokoban plan, a stash
  routine. Test them on the current screen before trusting them.

## 4. Strategy seen in Astra's winning run (lawful dwarven Valkyrie)
- Excalibur early (dip at XL5), then the classic Valkyrie route: Mines
  (Minetown), Sokoban, Oracle/bigroom as found, Quest when strong.
- Priorities: reflection and magic resistance (Astra had reflection by the
  mid game), free action, then a bag for the loot; unicorn horn.
- Castle: wand of wishing; wishes for key armour/charging; holy water;
  genocide of the most dangerous classes (Astra genocided L and ; ).
- Keep 2+ food items; eat when Hungry; never fight Weak.
- Prayer: track the turn of the last prayer; pray only in real trouble
  (HP < 1/7 max, Weak), and at least ~1000 turns apart.
- Elbereth: an escape tool; in 3.6.7 attacking from it erases it (-5 align),
  ~28% of dust engravings are misspelled: always check with `:`.
- Astra's deaths to learn from: run 1 sliming at Dlvl 51 (keep a cure: lizard
  corpse, prayer, fire), run 2 death ray at the Castle (get reflection BEFORE
  the Castle).

## 5. Safety habits (all slots)
- Never "A - Auto-select every item"; never pick up an unknown gray stone.
- Never wield/wear items of unknown BUC; test on an altar or with the pet.
- Kill thieves (nymphs, monkeys) at range; check inventory after "stole".
- Stop a fight loop before ~1/2 HP; disengage after a prayer.

## 6. Lessons from our 27/09 games (8 slots, ~30 deaths, best: Castle Dlvl 27, then Gehennom)
- The Sokoban ZOO killed 3 games: enter only at full HP, AC <= 0, fight from the doorway BY HAND (never a
  script), leave if a chameleon or a breath attacker shows up; never retreat into a dead end in line with a breather.
- The Castle killed the 2 games that reached it: never fall into it by digging on Medusa's level (random spot in the
  maze: minotaur); a master lich summons and curses: kill it fast or leave. Polymorph wand saved slot 3 there.
- Read unknown scrolls only with the main body armor OFF (destroy armor) and never in danger.
- Prayer timeout is random (rnz(350)): never count on a second prayer; food first, keep 2+ rations.
- Every script that passes turns: stop on any HP loss, "stole", status change (Stone, Slime, Blind...).
- Never answer y to "Really attack?" (peacefuls, priests, shopkeepers): luck and telepathy are lost.
