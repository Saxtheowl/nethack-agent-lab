# Style "wish_abuser" — start-scum for an early wish, then Astra

User decision 2026-09-27. Start-scumming (quitting brand-new games until the
start is good) is allowed for this style; SAVE-scumming stays forbidden.

## 1. The automatic part (scripts/wish_scum.py, on miniforum-worker)
- Chains new games (lawful female dwarven Valkyrie, same options as every
  slot, players Wish1..Wish4 on the worker) and looks at the FIRST ROOM only.
- Fountain `{` in the room: travel onto it and quaff (`q`, `y`) until the
  fountain dries up. Checked in fountain.c (3.6.7): fate = rnd(30); 23 = water
  demon; dowaterdemon grants a wish if rnd(100) > 80 + level_difficulty(),
  i.e. 19% on Dlvl 1. Per quaff: ~0.63% wish, ~2.7% HOSTILE water demon
  (deadly at XL1), 1/30 water moccasins, 1/30 water nymph. dryup(): 1/3 per
  quaff. A fountain exists in ~10% of first rooms (mklev.c: !rn2(10) per room).
- Lamp `(` in the room (farlook): oil lamp (prob 45) or magic lamp (prob 15),
  so 25% magic. The script stops and hands over.
- Anything else (no fountain/lamp, hostile demon, snakes, nymph, dried up):
  `#quit`, next game. Counters: runs/wish_scum/status.json on the worker
  (dashboard tab Styles).
- Start: `ssh miniforum-worker "cd <root> && setsid nohup python3 scripts/wish_scum.py --workers 4 > runs/wish_scum/driver.log 2>&1 &"`.
- It stops by itself when a game is found (status.json "found").

## 2. Handover to the LLM (you)
- `python3 scripts/wish_handover.py <slot> <wishK>` points the local slot at
  the worker game: the local tmux session nethackN runs
  `ssh -t miniforum-worker tmux -S /tmp/wishscum.sock attach -t wishK`.
  The save file NEVER leaves the worker (PURE rule); `S` saves on the worker
  and `NH_SLOT=N session.py start` re-attaches (and restores it there).
- All helpers (k, v, t, fight, look...) work unchanged through the slot.

## 3. The wish (prompt "For what do you wish?" is on screen)
- Default: `blessed +2 gray dragon scale mail` (magic resistance, AC 9 body
  armor). Type it exactly, then Enter. Then wear it with `W` (a Valkyrie
  starts with no body armor, so nothing to take off first).
- Write the wish and turn in the journal and `chronicle --importance 3`.

## 4. A lamp was found
- 75% of the time it is an oil lamp. Do NOT #rub it uncursed (20% wish,
  20% hostile djinni at XL1). Pick it up. You may quit and let the scum loop
  continue ONLY within the first 50 turns and only if you decide the lamp is
  not worth it (write why); after that the game is played normally.
- Identify: price in a shop (magic lamp base 500 vs 10), e.g. Izchak's
  lighting shop in Minetown. A magic lamp never runs out when lit.
- If magic: make it blessed (holy water: #dip), wield-free #rub (it wields
  itself) → djinni 1/3 per rub, blessed = 80% wish.

## 5. Then play Astra
After the wish, play the game in the Astra style: read memory/astra-style.md.
Same journal rules (memory/slotN-run-M.md), same safety habits.
