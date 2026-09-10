# The Vast AI pilot: what it buys, what it costs, and when to stop

## Why rent anything at all

There are two very different workloads here, and an earlier version of this
document recommended renting the wrong one.

**Recording games of the original** needs a JVM and a NetHack, ~1.2 GB per game,
and is bounded by wall clock: the bot plays in real time and the pinning delay
throttles it deliberately.  A two-hour recording still ended with the bot alive.
This is the *reference* side of the fidelity loop, and after fifteen captures at
100 % it is no longer the bottleneck.

**Playing real games with the port** needs NetHack and Python only - no JVM,
~100 MB per game - and runs at full speed, because the piece delay exists to make
*recordings* deterministic and nothing is being recorded.  Measured: **15.7 game
turns per second**, so a whole game ends in **15-20 minutes** rather than hours.

| | recording the original | playing the port |
| --- | --- | --- |
| needs | JVM + NetHack | NetHack only |
| memory per game | ~1.2 GB | ~100 MB |
| one game | 2 h and still alive | 15-20 min, ends by itself |
| concurrent on 4 cores / 11 GB | 3 | 4 |
| concurrent on 32 cores / 64 GB | ~25 | **~30** |

**A faster machine does not make one game deeper.**  The bot plays in real time;
turns do not arrive faster on better silicon.  What a big machine buys is
*parallelism* - thirty games at once instead of four - and that is exactly what
the remaining question needs.

## The question the rented machine is for

Not fidelity: the replay gate answers that, locally, in minutes.  The open
question is the one the mission actually asks - **does the port finish the game
without wizard mode and without human intervention?**

The original's own README says the ascension only came once pudding farming was
implemented, so it is rare and long.  Rare events need volume, volume needs
parallelism, and parallelism is the one thing renting actually provides.

Local evidence so far (`tools/ascend_batch.sh`, uncapped games that end by
themselves): games run 14-19 minutes, reach Dlvl 6-12, score around 20 000, and
die to ordinary monsters with no crash, no stall and no intervention.  Nothing
in the port stops a long game; what is missing is *how many* games an ascension
takes.

So the sizing argument is arithmetic: if an ascension is on the order of one game
in a hundred, that is roughly **six hours locally against forty-five minutes on a
32-core box** - and it is the same money either way, because the machine is
rented by the hour and the work is embarrassingly parallel.

Replaying is the second beneficiary: the fifteen-capture gate takes about an hour
here at four-way parallelism and would take minutes on thirty cores.  Since that
gate is re-run after *every* fix, it sets the iteration speed.

## Shape of the campaign

| step | where | what it costs |
| --- | --- | --- |
| provision one instance | rented | ~90 s, already verified |
| piece-delay probe at the real slot count | rented | 10 min, only if recording |
| **N port games in parallel until each ends** | rented | the bulk |
| collect outcomes, replay any capture | local or rented | free |

```
# on the worker, from the repo root
tools/vast/provision.sh
export BOTHACK_SRC=$HOME/nhwork/bothack-src \
       JDK8_HOME=$HOME/nhwork/jdk8 LEIN_DIR=$HOME/nhwork

# the campaign: real games, no wizard mode, no cap, one slot per core
tools/ascend_batch.sh out 200 30 0
python3 tools/ascend_summary.py out
```

`ascend_batch.sh` needs neither `BOTHACK_SRC` nor the JDK - only the NetHack
build - so a machine that will *only* play port games can skip most of
provisioning.  Export them anyway if the same instance is also to record.

`worker.sh` gives each slot its own NetHack user name (the lock and level files
in `var/` are named after it, and two games sharing a name delete each other's
levels) and cleans `var/` once per campaign, recording its initial state next to
the captures.  It never kills by binary name: on a shared worker that would
kill another slot's game.

## The cap, and how to hold it (both workloads)

**0.50 USD for the pilot.**  Two workers first, four only after the first two
have produced recordings that pass locally.  Concretely:

* pick the cheapest instance that has 2 cores and 4 GB - recording is
  wall-clock bound, not CPU bound, so a faster instance buys nothing;
* set the instance's own spending limit before starting it, so an unattended
  overrun is impossible rather than merely unlikely;
* the cap (`SECS`) is an **upper** bound, not the bill.  `record_orig.sh` stops
  as soon as the capture stops growing *and* attests an end, because a bot that
  dies leaves NetHack at the DYWYPI prompt it never answers - with a 7 200 s cap
  and a game that dies at 600 s, the old behaviour paid for nearly two hours of
  a worker staring at a death screen.  It also stops after
  `RECORD_IDLE_STALL` (default 600 s) of silence *without* an attested end and
  says so, so a lost scraper costs ten minutes rather than the whole cap;
* so budget from the *median game length* a pilot measures, not from the cap:
  choose the game count from the budget and let the cap only catch the outliers;
* stop the instance from the local side as soon as `collect.sh` has run.  Do not
  leave a worker idle waiting for a decision.

## Recording only: choosing the cap, from measurements

Three numbers, all measured on this machine under the pinned recording protocol:

* **the original records at ~3.4 game turns per second** (12 246 turns in 3 644 s,
  measured mid-run on seed 40002).  `PTY_TAP_PIECE_DELAY` is what buys
  determinism and it is also what costs throughput, so this is a property of the
  protocol, not of Clojure;
* **at a 1 800 s cap, 1 of 6 games finished.**  The bot survives past 30 minutes
  on most seeds; the five others produced 78 000-94 000 keystroke captures that
  can only ever be PREFIX_ONLY;
* **the bot is still alive at turn 12 000 after an hour** on seed 40002, so a
  "long" game is not 30 minutes, it is hours.

So a PASS_COMPLETE is expensive and a long identical prefix is cheap.  Budget
accordingly:

* the cap is an upper bound, not the bill - `record_orig.sh` stops as soon as the
  capture attests an end, so a game that dies at 600 s costs 600 s even under a
  7 200 s cap.  Only the *survivors* cost the full cap;
* expect roughly one finished game in six at 1 800 s.  Raising the cap raises
  that fraction and the cost of the survivors at the same time - measure the
  completion rate the pilot actually gets before scaling;
* a campaign of prefixes is not worthless: a 94 000-byte identical prefix is
  strong evidence, and prefixes are what the budget buys most of.  It simply
  cannot answer "does the port reproduce a whole game", and a table of
  PREFIX_ONLY rows must never be reported as reproduced games.

## Recording only: the piece delay, measured

`pty_tap.py` forwards the game's output in 256-byte pieces with
`PTY_TAP_PIECE_DELAY` between them (0.05 s).  On seed 40002 that is **56 578
pieces x 0.05 s = 2 829 s of deliberate sleep out of 3 644 s elapsed - 78 %** of
the recording's wall clock.

**What the delay is for.**  Not for making the game reproducible - a capture is
self-contained and the replay feeds the port exactly the pieces recorded.  The
delay exists so the JVM's terminal reader consumes **one piece per `read()`**,
which is what makes the recorded piece boundaries equal to the frames the
original reasoned about.  Too small, and two pieces land in one read: the
original sees one redraw where the recording holds two.

So the test is the *replay verdict*, not an agreement between runs.
`tools/piece_delay_probe.sh` runs it.  Measured on seed 40001 (which dies at
2 775 turns), on an idle 4-core box:

| delay | wall clock | pieces | sleep | capture | replay | same game as 0.05? |
| --- | --- | --- | --- | --- | --- | --- |
| 0.05 | ~550 s | 10 298 | 515 s | GAME, 25 672 keystrokes | PASS_COMPLETE | reference |
| **0.02** | **397 s** | 10 296 | 206 s | GAME, 25 672 keystrokes | **PASS_COMPLETE** | **yes, byte for byte** |
| 0.01 | 312 s | 10 307 | 103 s | GAME, 25 687 keystrokes | PASS_COMPLETE | no - diverges at keystroke 6 325 |

Read it carefully, because the two fast rows do not mean the same thing:

* **0.02 is the safe operating point.**  It cuts 28 % of the wall clock and the
  original plays the *identical game*, so the piece boundaries did not move: the
  reader still got one piece per read.
* **0.01 works but is past that line.**  The capture is a *different game*, which
  is exactly the symptom of shifted frame boundaries.  The port still reproduces
  it - a capture is a self-contained reference, so PASS_COMPLETE is honest - but
  the margin against coalescing is now thin, and a worker running several slots
  has less of it than this idle box did.
* Below ~0.02 the JVM becomes the bottleneck anyway: halving the delay again
  bought only 397 s -> 312 s, because the sleeping now overlaps the JVM's own
  work rather than dominating it.  The 78 % figure was an upper bound and this is
  what it actually converts to.

**Recommendation: record at 0.02, and re-run the probe on the rented instance
before scaling** - once idle, once at the slot count the campaign will use.
Coalescing is a scheduling property and this measurement is one short game on one
idle machine; a long game has five times the pieces and a loaded worker has less
headroom.  The probe costs ten minutes and it is the first thing to run.

## What would make the campaign not worth continuing

* a port game that ends without an xlogfile entry, or with a Python traceback in
  its log - that is the harness or the port breaking, not the bot losing, and
  more instances will only produce more of it;
* any capture whose recording verdict is `INVALID_TRACE` - same reasoning on the
  recording side;
* a divergence class that reproduces on more than one seed: stop, fix it
  locally, then re-replay the captures already paid for.  Recordings keep their
  value across fixes, which is the whole point of recording once and replaying
  often;
* recordings that all hit the cap: raise the cap or accept prefixes, but say
  which - a table of PREFIX_ONLY rows must never be reported as reproduced
  games.

## What the pilot cannot tell us

Two campaigns' captures are **not** comparable with each other.  The original
stops agreeing with its own earlier runs once the machine is loaded
(`docs/TESTS.md`, "The pinning is partial"), and a rented worker running two
slots is a loaded machine.  Each capture is still a valid self-contained
reference - the replay has no NetHack and no threads - but "seed 41003 recorded
on worker A" and "seed 41003 recorded on worker B" are different games and only
look like a contradiction if they are lined up against each other.
