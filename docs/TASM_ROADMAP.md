# TASM: never stand still

Design of 2026-10-05. **First versions of all seven shipped in v0.2.0** (see
"Status" below and [CHANGES](CHANGES.md)); none is player-confirmed yet. Shipped behavior belongs in [CHANGES](CHANGES.md), engine facts in
[TECHNICAL](TECHNICAL.md). This replaces the bounce/zip/sling/burst draft and
the web-tag draft. Tags are parked for later skills (see the end).

## Player direction (2026-10-05)

- Garfield's Spider-Man is **spider-like, jumpy and all over the place**, like the
  Lizard fights: on walls and ceilings, on the enemy, flipping over him.
- The game has strong enemies and **web-resistant bosses**. The kit must beat
  them up with real combos, not just web crooks.
- Current problems: it plays like base red; **combos only hit in front** while
  enemies behind hit you; and **combos can't be cancelled**, so crowds dogpile you.
- **Leave native abilities alone** (A web, B jump, base strings, R evade when the
  upgrade isn't owned). All changes rewrite the **7 Red purchase slots**. More Red
  skills can come later. Fun over balance.

## The identity

Spider-Man doesn't stand in front of one enemy and press Y. He **strikes, cancels,
flips somewhere better and keeps the combo going**: on top of an enemy, behind the
one about to hit him, upside down in a spinning kick. Every Red skill either
moves him while it hits, hits more than one side, or lets him leave and come back
without losing the combo.

The loop is **strike → cancel → reposition → resume**. Two passives make that
loop work. The five active skills give it places to go.

## The 7 Red slots, redesigned

Each skill keeps its native slot, ownership bit and input. Players who own a slot
own its replacement. Without the purchase, native behavior is untouched.

| Slot (bit) | Native skill → new skill | Input (native slot input) | Role |
|---|---|---|---|
| 13 | Web Kick → **Leapfrog** | Y during grapple | Vault over and land behind |
| 14 | Web Launch → **Skyjack** | Up during grapple | Take one enemy out of the crowd, into the air |
| 15 | Mid-Air Snare → **Spider Perch** | A toward an enemy in the air | Ride an enemy or boss |
| 16 | Spider Dance → **Split Decision** | Y, pause, Y, Y, Y | Ground string that hits front *and* back |
| 17 | Scissor-Kick → **Spin Cycle** (needs 16) | Y, pause, Y, repeated Y | Steerable 360° handstand spin kicks |
| 18 | Amazing Speed → **Spider Reflex** (passive) | R during any attack | Cancel any combo, resume it after |
| 19 | Ultimate Speed → **Spider-Sense** (needs 18) | R just before a hit lands | Flip behind the attacker and counter |

Native parent/child rules stay meaningful: Spin Cycle extends Split Decision, and
Spider-Sense sharpens Spider Reflex. Both passives keep the native attack-speed
bonus they replace, so nobody loses speed.

### 18 · Spider Reflex: the foundation

R during **any** Red attack, string or skill cancels it immediately into a quick
directional flip. Spider-Man lands **facing the direction you hold**. Press Y
within a short window and the string **continues from the next hit** instead of
restarting. Dodge-cancelling keeps your combo; it doesn't cost it.

- *Crowd:* hit the front enemy twice, R back over the dogpile, finish the string
  on the enemy that was behind you.
- *Boss:* commit to damage, cancel the moment he winds up, resume after he misses.
- *Links:* cancels every other skill: out of Perch, mid-Spin Cycle, before
  Leapfrog lands.

### 19 · Spider-Sense: the reward

Press R just before an enemy hit lands to trigger a **sense flip**: Spider-Man
flips over the attacker in a fraction of a second (a fast, visible dash, never
a teleport: v0.4.1; no slow-motion: the player wants the game super fast paced,
2026-10-05), lands behind
him and delivers a **reversal strike that staggers even heavies and bosses**. The
combo resumes from there. A mistimed press is still a normal Reflex dodge.

It also adds the **tingle**: a small spider-sense marker over any enemy starting
an attack off-screen or behind you. You learn to read the crowd and turn the
threat into an opening. This is the subway and Times Square spider-sense,
playable.

### 15 · Spider Perch: the signature

A toward an enemy while airborne zips Spider-Man **onto** him, crouched on the
shoulders like a spider. From the perch:
- **Y:** a flurry of hammering strikes on the head, his best damage on a single target.
- **A toward another enemy:** hop straight onto the next head (head-hopping).
- **B:** spring off high (into Skyjack range, a wall, or another Perch).
- **R:** flip off in any direction (Reflex).

In crowds you're above the dogpile: in the generous prototype, others can't hit
you while you're perched. On bosses this is the Lizard-riding moment: stay on
and pound until he rears to throw you off, then Reflex away. Web-resistant
bosses still work, because the web pulls *you*, not him. If a boss blocks the
zip, falling onto him from a jump or wall also perches (see feasibility).

### 16 · Split Decision: the crowd string

The Spider Dance branch (Snap, pause, then three moves) **picks a side each hit**:
1. Corkscrew: spinning mule kick, hop snap kick, backflip flash kick (three contacts)
2. Split kick: leap into a full split, scissor, split again (two contacts)
3. Breakdance sweep: 360° low leg sweep, kip-up

Hits 1-2 turn toward an enemy behind; the sweep takes the nearest. Hold a
direction to choose. Y with a held back direction continues the branch instead of
the native turn attack. Its damage stays native, so bosses still take it.

### 17 · Spin Cycle: the payoff

From Split Decision, mash Y: Spider-Man drops into a **handstand helicopter
kick**, legs whirling and hitting all around. **The D-pad steers him** across the
floor while it spins. Drive into a cluster, grind a boss's legs, or steer away
from a charge. Release or R exits with a flip-up. It turns the native scissor
barrage from standing still to moving.

### 13 · Leapfrog: the cross-up

Y during a grapple: instead of yanking the enemy in, Spider-Man **pulls himself
in, plants his hands on the enemy's shoulders, vaults over and double-heel-kicks
his back**. He lands behind him, facing the enemies that were behind you. The
kicked enemy stumbles forward into his friends. It repositions and attacks in
one move. Into Split Decision for the cleanup.

### 14 · Skyjack: the escape upward

Up during a grapple launches the enemy, and Spider-Man rises with him (the
player-confirmed Web Vault rise is kept). In the air, Y strings a flipping
aerial combo where nobody below can reach you. The last hit **spikes the enemy
into the crowd below** as a bowling ball. Then drop into Perch on whoever is
standing.

## How it plays together

| From \ into | Reflex | Sense | Perch | Split | Spin | Leapfrog | Skyjack |
|---|---|---|---|---|---|---|---|
| **Any attack** | cancel, keep string | counter if timed | — | resume here | resume here | — | — |
| **Perch** | flip off anywhere | counter the shake-off | hop to next head | land into it | land into it | — | B springs up |
| **Leapfrog** | cancel the landing | — | B + A onto a head | now facing the back row | — | — | — |
| **Skyjack** | cancel in air | — | dive onto someone | land into it | — | — | spike bowls crowd |
| **Sense flip** | — | — | — | resume behind attacker | resume behind attacker | — | — |

Moments the prototype must produce:
1. **Dogpile break.** Split Decision on the front thug, tingle from behind, R just
   in time: sense flip, reversal kick, split kick hits both. You were never stuck.
2. **Head-hopping.** Jump, Perch, hammer, A to the next head, hammer, B spring,
   Skyjack the last one and spike him into the first two.
3. **Boss ride.** Perch the boss, pound until he rears, Reflex off, sense-counter
   his swipe, land behind, Spin Cycle his legs, R out before the tail sweep.
4. **Reverse the crowd.** Grapple a thug, Leapfrog over him into his friends,
   Split Decision the front and back rows, Spin Cycle through the pile.

## Feasibility

Known starting points: Web Kick gate `0x020B603C` (bit 13, state 42), Web Launch
query `0x020B6264` (bit 14, state 40), the shipped Sling/Snare (bit 15) and Rush
(bit 16) routes, Scissor gate (bit 17), the player position at motion
+0x7C/+0x80, enemy projection from the health bars, and SCA authoring (strong).
Every change is gated on its ownership bit and limited to Red attack states, so
an unowned or non-Red state stays native.

| Skill | Native base | Unknown to prove first | Fallback |
|---|---|---|---|
| Reflex | Native evade state | Interrupt any Red attack state into evade (clear hitboxes); write facing; keep string index | Cancel only after a hit or in recovery; resume skips the opener |
| Sense | Reflex + evade | Detect an incoming active hit before damage; detect enemy wind-up for the tingle | Window right after hit registration; no tingle |
| Perch | Snare zip (bit 15) | New attached state following an enemy's position each frame; boss targeting | Pogo: multi-hit stomp on the head and auto-bounce up |
| Split Decision | Spider Dance branch (bit 16) | Contact geometry behind/both sides in GMB | Auto-turn toward the chosen target before each hit |
| Spin Cycle | Scissor repeat (bit 17) | D-pad-driven root motion during a repeat loop | Fixed spin with forward drift |
| Leapfrog | Web Kick state 42 | Landing exactly behind targets at any distance | Authored arc with a position correction at landing |
| Skyjack | Web Vault rise (bit 14) | Aerial string lock-on; spike knockdown on others | Native air attacks after the rise |

Also needed: where bits 18/19 are queried (passive speed), so the bonus is kept
while new gates are added. Heap headroom with the 24 KiB reserve: TECHNICAL
"Kit extension contract" (large untouched arena in the sewer fight).

## Status (v0.4.1) and next iterations

All seven shipped in v0.2.0 as simplest working versions. Player verdict on
v0.2.0 (2026-10-05): "very good"; only the helicopter spin missed every other
hit and looked like breakdancing, fixed in v0.2.1 (CHANGES). v0.3.0 added the
queued Perch exits, the neutral Reflex flip and Sense vs ranged attackers.
Player verdict on v0.3.0 (2026-10-05): "looks feels way better", no specific
issues; keep it fast (no slow-motion). v0.4.0 adds Skyjack bowling via a reusable
native "hit any enemy" replay (TECHNICAL "Hit pipeline"), which can also power
later ideas (Leapfrog kick-through, Spin Cycle crowd hits, Stop Hitting
Yourself).
Player verdict on v0.4.0 (2026-10-06): having lots of fun, smooth overall, but
Spider-Sense and Leapfrog felt "teleporty"; Sense clipped him out of the level
and a crowd fight froze the game. v0.4.1 fixes both (Sense teleport corrupted
the heap) and converts Sense, Leapfrog and Perch to velocity. A 2026-10-06 audit
found remaining direct Skyjack juggle drift; velocity and combined crowd-backend
candidates passed agent checks, including native wall bounds. They remain
unpublished and player feel is untested (TECHNICAL "Shared crowd-hit backend candidates").

| Skill | Shipped version | Next iteration once mapped/played |
|---|---|---|
| Spider Reflex | Ground/air R cancel, directional roll (front flip), neutral back tuck (v0.3.0), 28-update resume | Enhanced Dodge interplay; dodge-cancel from more paid states |
| Spider-Sense | Melee state 15 (12 units) or ranged state 16 (16 units, v0.3.0) → v0.4.1: 4-update dash through/over him (walls stop it), 7-update guard, flip + back roundhouse | Hit-anticipation timing, tingle marker (never slow-motion); state 24 if confirmed |
| Spider Perch | Snare follow-up → held stomp pounding, Y chains; v0.3.0: B flip spring, A flip head-hop to the next enemy; v0.4.1: ride/hop steer by velocity | Boss shake-off, entry from jumps/walls; hop feel on real crowds |
| Split Decision | Auto-face per hit (behind preference within 12 units) + new choreography | True two-sided contact geometry |
| Spin Cycle | v0.2.1: straight blade-leg handstand spin; each contact aims (other side within 7, else nearest within 16), glide into reach, any-direction repeats | Exit flourish, spin-to-launch |
| Leapfrog | Native kick + vault over the popped target; v0.4.1: continuous 6-update velocity vault, recoil cancelled | Vault before the kick once grappled targets can be hit mid-pull; kick-through into the crowd |
| Skyjack | Floating juggle, drift, spike finisher; v0.4.0: landing bowls enemies within 8 units (native knockdown hit) | Tune radius/strength from play; bosses |

Player builds come after each iteration; the playtest below decides what stays.

## The playtest that decides what stays

- Is the player ever stuck in a combo while being hit from behind? (Should be never.)
- Do they cancel and resume without thinking about it?
- Does a web-resistant boss go down to Perch, Split and Spin without cheese?
- Does it look and feel unlike base red within ten seconds?
- The success test: "Let me try that boss again, I want to ride him longer."

Measure time spent being hit while committed, wrong-direction hits and failed
cancels. Real HP is telemetry, not a target yet.

## Parked for later Red skills

2026-10-06: the player wants combat left steady while learning it; authorized
Midnight Line chapter work takes priority (reference/midnight_line.json).
Previously offered slot extensions remain deferred: air Reflex web-zip hops
between enemies, wall-rebound flying kick, Split sweep-to-juggle, steerable
Skyjack spike and Perch spring-to-dive-kick. Additional web spray/crowd stun and
object/crate yanks need shop/ownership research alongside the tools below.

These need extra shop rows (research): web tags shared across tools, Clap,
bowling-spread tags, Reel/Net, Orbit tetherball, tier-5 Cocoon. Wall/ceiling
pounce dive. *Stop Hitting Yourself* (redirecting an enemy's swing into his
friend). Later suits stay in reference/suit_roadmap.json.

## Proposals awaiting the player (2026-10-07, not approved)

Asked for while away from the game: a Midnight Line roadmap, later areas,
features and XP sinks (player has ~3000 unspent XP). Proposed, nothing built:

- **Midnight Line limits.** Room ids are bytes (<= 255); the map/visited rule
  works up to room 114 (25 more rooms) without code changes; ~8.5 MiB free in
  the 64 MiB cart (~80 KB per cloned room); flags are the binding limit (1
  spare; 138..165 need a backup-save scan). New geometry beyond clones,
  mirrors or the debug rooms is unproven research. 2026-10-11: room collision
  is decoded (TECHNICAL "Room collision tree"), so collision can be read and,
  later, authored. Rule since v0.8.1: a cloned room ships only after a walk
  route crosses it with real doors (`tools/midnight_walk.py`) and it needs no
  story ability the player lacks.
- **Next chapter content.** Power puzzle and objective board (shipped in
  v0.8.0, CHANGES), Signal Leech, Conductor teaser, then a "Midnight
  Express" network: station doors to save rooms in every district (fast travel),
  a Lost Lab built from the unused proto01/Test rooms (proto01 shipped as the
  Yard in v0.9.0, cleaned of its test objects; the grey Test rooms remain),
  boss gauntlet from the mini-boss rooms, timed escape rooms (TimerWatcher).
- **Features.** Difficulty option via variable 0x125, elite enemies (kit-side
  HP scaling), finishers, crowd backend publication, suit unlocks.
- **XP sinks.** Gate: expanded shop rows and free ownership bits (research).
  Fallback without new rows: a Refuge workbench (Button Press trigger sets a
  chapter flag; kit tick spends XP and grants stat/kit upgrades), Mk II tiers
  for the seven Red skills, the parked Red skills, repeatable health/damage
  training, suit unlocks.
