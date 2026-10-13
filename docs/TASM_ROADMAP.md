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

2026-10-06: the player wanted combat left steady while learning it. Superseded
2026-10-11: the kit is mastered and more skills are wanted ("Spice pack"
below). Previously offered slot extensions: air Reflex web-zip hops
between enemies, wall-rebound flying kick, Split sweep-to-juggle, steerable
Skyjack spike and Perch spring-to-dive-kick. Additional web spray/crowd stun and
object/crate yanks can now be their own shop rows.

Extra shop rows exist since v0.10.0 (19 free ability bits left). Candidates
that wanted them: web tags shared across tools, Clap,
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
- **XP sinks.** New shop rows work since v0.10.0 (three Red rows, 1000 XP in
  total; rows may also have several levels like the native collectible
  table). Still open: Mk II tiers for the seven Red skills, the parked Red
  skills, repeatable health/damage training, suit unlocks, a Refuge workbench.

## Spice pack (2026-10-11): three new Red shop skills in v0.10.0

Player, 2026-10-11: enjoys the seven skills a lot but has mastered them;
everything now feels "bread and butter basic" and they want "a bit more
spice". Of eight ideas they picked **Web Rush, Ricochet and Momentum** ("most
interesting right now"), asked for **real new Red shop slots** ("we will need
it for future suits anyways") and added: "your suggestions are good but none
really blew me away much". Lab work may run in the background while they play.

Shipped in v0.10.0 as first versions (CHANGES; engine facts in TECHNICAL
"Second kit block" and "Shop tables, menu and free ownership bits"). Agent-
tested, not player-confirmed.

| Skill (ability bit, XP) | Input | First version | Next iteration from play |
|---|---|---|---|
| **Web Rush** (74, 300) | A during a Red ground string | Zips to the nearest standing enemy 7..56 units away (held Left/Right picks the side), three bicycle kicks, back tuck; the string continues after the node he left; A again after the kicks chains to the next enemy | Guard frames or not; air and wall targets; rush from Y+back and air strings; reach |
| **Ricochet** (75, 300) | Passive | An enemy sent flying (1 unit per update or more) floors every standing enemy within 3.5 units of his path, who then flies too | Radius, damage, a boost to flight distance; Leapfrog's pop (0.75 units per update) and pulled or launched bodies do not count yet |
| **Momentum** (76, 400) | Passive | Each combo tier doubles more of the free animation steps of ground string attacks (tier t: t of 5), never across an active hit window: wind-up and recovery shrink, hits and hit timing do not change | Air strings and Perch; a visible cue; whether tier 5 is too fast to read |

The rows cost 300/300/400 XP, have no prerequisites and can be refunded like
native ones. Prices are placeholders (balance is deferred).

Still only proposals (unapproved, nothing built):

| Idea | Input (unproven) | What it does | Prove first |
|---|---|---|---|
| **Web Blitz** | X with combo tier >= 1, away from liftables | Spends combo tiers: pinball between enemies, one flip-kick each | Whether queue command 4 (X) is free without a liftable; writing the tier |
| **Tetherball** | Down while holding a grapple | Swing the webbed enemy overhead as a flail, release to throw him (Ricochet) | Native `spd_GrapplePullDown.sca` suggests Down is bound; moving an enemy on an arc by velocity |
| **Wall Pounce / ceiling hoist** | Y or A from a wall cling or ceiling hang | Spring off into a dive that lands in Perch; yank an enemy up from the ceiling | Wall, ceiling and swing controller states are unmapped |
| **Sense chain + tingle** | R timing | Back-to-back counters escalate; marker over an enemy winding up behind or off-screen | HUD marker drawing; anticipation timing |
| **Air extensions** | Parked list above | Dive kick after the Perch spring, Split sweep-to-juggle, steerable spike | Per move |

Garnish: a quip/taunt that tops up the combo gauge (native `spd_Taunt.sca`
exists; whether any state plays it is unknown).

For the next round (agent's note): the player wants something that blows them
away, so bring bigger fantasies than slot extensions. The pieces now exist:
new shop rows are cheap (19 free ability bits, table and texts in the second
block), a move can be inserted into a string without spending a node, any
enemy can be hit by replay, and the rate getter can hold or skip animation.
Native clip names in `reference/format_survey.json` (`spd_WebSwingKick`,
`spd_DiveKick`, `spd_DiveSlantKick`, `spd_WebHangIdle`, `spd_WallRunBackflip`,
`spd_DuckAttack`) hint at native bindings: check before claiming an input.
Every new move needs an authored clip, travels by velocity and uses no
slow-motion.

## Round two (2026-10-11): verdict on v0.10.0 and proposals

Player, 2026-10-11 (second session; finished the Midnight Line, beat its
boss, used the new skills): Web Rush "was cool", the passives "nice", but "I
still want way more new moves" (3-5, "get as creative as you want ... impress
me"). Spider Reflex and Spider-Sense "already give huge move speed boosts":
slightly nerf them and slightly buff Momentum so it is "more noticeable and
more rewarding". Stat upgrades in the shop are welcome and may cost more: max
health shown by the bar changing colour per upgrade instead of a new bar;
unsure about damage or tankiness because enemies would then need buffs. Wants
a new section in each main area after improving the Midnight Line ("without
more stuff to do the base game moves way too fast"), a boss that is really
new, a clearer map, no dead hatches, terrain that is not recoloured sewers
and a smaller sewer/hive enemy gap. They asked to brainstorm first:
**everything below is proposed; nothing is approved or built.** Answered
2026-10-11, see "Round three": the five moves were rejected, only Vitality
was chosen of the stat rows, and the speed rebalance, map, hatches and Nest
ramp shipped in v0.11.0.

**Speed rebalance.** Reflex 1.15 -> 1.10 and Sense 1.30 -> 1.20 (kit side, in
the rate getter); Momentum one tier earlier (tier t doubles t+1 of 5 free
steps, full at tier 4) and on air strings, with a visible cue. Re-measure
string hit counts at the new rates (TECHNICAL "Second kit block").

| Move | Input (unproven) | Fantasy | Prove first |
|---|---|---|---|
| **Slingshot** | Hold Down + A on the ground | Two lines to the sides, he walks back stretching them, release fires him across the room through every enemy in the lane and he sticks to the far wall; also crosses gaps, so rooms can be built around it | Speed cap outside state 46; hand-off into wall cling (state 7); whether Down + A is free |
| **Head Banger** | A toward a second enemy during a grapple | A second line; both are yanked together while he back-flips up, they collide under him and he lands on the pile | Moving two enemies by velocity |
| **Pendulum** | Passive on the native web swing (states 26..28) | Swinging through a crowd kicks everyone in the arc flying (Ricochet); B at the top releases into a flip | Swing speed and position in those states; `spd_WebSwingKick` binding |
| **Cat's Cradle** | Second A held on a grappled enemy | Over, under, over: three wraps cocoon him; three wraps hold even a web-resistant boss for a short window | Long stun on bosses; whether a grapple attaches to them (else from Perch) |
| **Paddle Ball** | Hold A in the air after Skyjack | Hanging from a line he bounces the launched enemy on a web; Y on each return hits harder, the last one spikes him into the crowd | Rhythm window without slow-motion; vertical enemy velocity |

Agent's order: Slingshot, Head Banger and Pendulum first; Cat's Cradle with
the new boss; Paddle Ball as the toy. A section can unlock its move's shop
row (the purchase record's required event may be a game flag: one lab run).

**Stat rows** (Both Suits list; rows may have several levels natively, one
ownership bit per level, 19 free): Vitality (+1 health unit per level; bar
recoloured per level, or layered so the new colour drains first: the player
bar's drawing is unmapped); Flow (slower combo decay per level: damage and
Momentum speed are earned through the meter, +10% per tier, instead of a
flat damage stat); Second Wind (the near-death minigame restores more);
Adrenaline (a new combo tier heals a sliver). No flat damage or armour. The
story stays native; chapter rooms get a per-room enemy strength dial (also
the fix for the Nest gap, and later elites and a hard mode via 0x125).

**New places.** Lesson: recoloured clones of known rooms read as the same
place. Options: unused or unseen rooms (nearly spent, or spoilers), remixes
(mirrors, props from other districts, repainted textures) and original rooms.
Original rooms need a spike first: the collision tree is decoded and authored
quads rendered in the lab, but no room has been built from nothing. Budget:
about 24 more mapped rooms (ids up to 114), 26 spare flags. Sections, one
mechanic, move and boss each: Midnight Line 2.0 as the hub (stations to the
others, own map screen); Pier "Crane Row" (Slingshot); Downtown "The Grid"
(electrified floor patterns, breakers; boss of generator cores); Residential
rooftop chase (timer); Hive only after the story (spoilers).

**Bosses.** Machine/arena bosses from room script (hazards, timed platforms,
throwables, breakers) are new fights within reach. A new character boss
(model, animation, AI) is research; wild option: a rival on Spidey's own
skeleton who uses the kit against him, if an enemy can bind the player rig.

**Other ideas.** Danger Room terminals (wave and time-attack medals paying
XP), bounty elites roaming old story rooms, tokens hidden in native rooms
that only new moves reach (paying stat levels), a style rank on the HUD.

## Round three (2026-10-12): the player's answers, v0.11.0, new move ideas

Player, 2026-10-11 (answering "Round two"): 1) "I'm not really that impressed
by any of these new moves you suggested, come up with new ones"; 2) "Let's do
just vitality for now"; 3) quick fixes before the bigger work: yes; 4) spend
whatever time is needed mapping things out, "don't create anything yet": do
the research so that a later session can do the work fast.

**Built in v0.11.0** (CHANGES): Reflex 1.10 and Sense 1.20, Momentum one tier
earlier and giving the native 1.15 / 1.3 back from combo tier 3 (string of
four: 122 frames at tier 0, 86 at tier 5; v0.10.0 113 and 87), Vitality
I..III, the chapter's own map, closed hatches, the Nest strength ramp. Not built: Flow, Second Wind and Adrenaline (not chosen),
Momentum on air strings and a visible cue, sections and bosses (research
only: TECHNICAL "Room compiler", "Script boss research"). 2026-10-12, later
the same day: the player turned Round three down as well ("they weren't that
interesting"), except Thwip Barrage ("did sound kinda cool ... give me more
web based ideas"): see "Round four".

Agent's reading of the two rejections (an interpretation, not the player's
words): the picks so far (Web Rush, Ricochet, Momentum) all deepen the combo
itself, while the rejected ideas were set pieces that need a setup (a
grapple, a charge, a swing). Round three puts new answers inside the string
and adds one headline that changes what a fight looks like. **All
unapproved; none built.**

| Idea | Input (unproven) | What happens | Prove first |
|---|---|---|---|
| **Rodeo** | On a Perch: hold a direction, Y, B | Spidey steers the enemy he rides: the D-pad runs him through the crowd, Y makes him swing at whoever is in front (his own attack, hits replayed on his friends), B jumps off and sends him stumbling into the rest (Ricochet) | Driving an enemy by velocity while perched; forcing his attack state on demand (the lab already forces state 15); whether his hit can land on enemies or must be replayed |
| **Combo wheel: Kickflip and Flapjack** | B and X in a ground string (A is Web Rush) | B: a flip kick that launches the enemy and carries Spidey up with him, straight into the air string. X: a web suplex that throws the enemy overhead onto whoever stands behind. With A, every face button has an answer mid-combo | Whether B and X (queue commands 2 and 4) are free in non-cancelable nodes; an overhead arc for an enemy by velocity |
| **Wall Bounce** | Passive (Ricochet upgrade) | A flying enemy who hits a wall bounces back toward Spidey instead of sliding down; hit him before he lands and he flies again | Seeing a flying body stop at a wall (velocity clamps); re-launching by hit replay |
| **Thwip Barrage** | Hold A on the ground | Rapid web shots walk the target backward; at a wall he is pinned there for a few seconds, and so is everyone in the lane (the car-thief scene) | Hold versus tap on A; a pinned state (the native grapple hold); the native grapple line as the shot |
| **Live Wire** | Passive at combo tier 3+ | Charged web-shooters (TASM2): grapple, Web Rush and Thwip hits arc to two nearby enemies and stun them, drawn with the game's own electric effects | Spawning a native effect actor (`ElecShock`, `ElectricLg`) from kit code |
| **Ceiling Stalk** | A while hanging from a ceiling above an enemy | Drops a line, hauls him up and leaves him stuck there for a few seconds | Wall and ceiling states (7 cling, crawl and ceiling hang, 9 wall run: seen 2026-10-12); holding an enemy at ceiling height by velocity |

Agent's order: Rodeo (headline), the combo wheel and Wall Bounce (cheap, and
they feed Ricochet and Momentum), then Thwip Barrage. Live Wire and Ceiling
Stalk need the most research. Known Perch limit to fix with Rodeo: B pressed
in the two updates between stomp cycles fires the native web swing instead of
the spring (TECHNICAL "Second kit block", qualification note).

## Round four (2026-10-12): web-shooter ideas

Player, 2026-10-12 (answering "Round three"): "they weren't that interesting
so try again"; Thwip Barrage "did sound kinda cool so give me more web based
ideas. Don't implement just theory craft". **Everything below was a
proposal.** Answered 2026-10-13 ("Round five"): Overclock was built as
proposed, Flypaper and Vortex became Dragnet and the Vortex string, the
rest is not approved.

Agent's reading (an interpretation): three rounds of set pieces and
passives were turned down; the two things that landed are Web Rush and Thwip
Barrage. Both are the web-shooters used as a weapon in the middle of a
fight, with no setup. So this round is one suite: **every button gets a web
answer, and webs leave a mark.** The mark is a shared status, **Webbed**: an
enemy hit by any web move wears strands for a few seconds; a Webbed enemy
who is knocked into a wall or the floor sticks there for a moment (a free
combo starter). That one rule makes the moves below feed each other and
Ricochet.

| Idea | Input (unproven) | What happens | Prove first |
|---|---|---|---|
| **Thwip Barrage** | Hold A, ground or air; D-pad aims | Rapid web shots, each a small hit that shoves the target and marks him Webbed; the fourth on one enemy pastes him to whatever is behind him. In the air every shot kicks Spidey up a little, so he hovers over the crowd while he fires | Tap versus hold on A (A is readable on ARM9); an enemy pushed by velocity while staggered; a held "stuck" state (what state a grappled enemy sits in) |
| **Face Full of Web** | A just as an enemy swings (the Spider-Sense moment, with A instead of R) | A web to the face: he finishes the swing blind and it lands on his nearest friend; blinded for a few seconds he keeps hitting whoever is beside him. R still dodges: R is the safe answer, A the greedy one | The Sense detection exists; replaying the attacker's own hit on another enemy (the kit replays Spidey's hits today) |
| **Yoink** | A during an air string, or A + away from the target in a ground string | The mirror of Web Rush: a line to the farthest enemy in front and he is ripped across the room into the next hit; anyone in his way goes down (Ricochet). Rush goes to them, Yoink brings them | An enemy moved by velocity over 40+ units; which input is free in the air string |
| **Fastball** | X with nothing to lift nearby | Webs the nearest loose thing (a barrel, a crate, or an enemy who is on the floor) and whips it at the enemy in the held direction. A downed goon is always there to throw | Whether X (queue command 4) is free away from liftables; throwing a native object by velocity and breaking it on contact |
| **Flypaper** | Down + A on the ground | Sprays a web patch on the floor for about six seconds: anyone who steps in is rooted and Webbed. One patch at a time. The answer to a dogpile | Whether Down + A is free (`spd_GrapplePullDown.sca` hints at a native use); a floor mark (the unused `WebBrake` effect resource, or a scenery quad) |
| **Vortex** | Hold A during Spin Cycle | Every turn of the helicopter throws a line and drags everyone within about 30 units a step closer: the spin becomes a blender that fills itself | Enemy velocity toward a point each update; whether it stays readable with six enemies |
| **String 'Em Up** | A in the air above a staggered or downed enemy who is nearly beaten | The finisher from every comic: he is hauled up and left hanging from the ceiling, out of the fight, for bonus XP and a combo tier. Uses the ceiling anchor points every room carries | Finding "nearly beaten" (health is readable); lifting an enemy to an anchor by velocity; removing him cleanly |
| **Overclock** | Passive at combo tier 5 | The web-shooters run hot: every Y hit also fires a web shot at a second enemy, who is staggered and Webbed. Tier 5 becomes a state you fight to keep | A second hit replay per contact without the freeze the v0.4.0 lab patch showed |

Agent's order: **Thwip Barrage** and **Face Full of Web** first (the pick
plus the cheapest strong one: its detection and hit replay already exist),
then **Yoink** and **Vortex** (both are "move an enemy by velocity", one
proof), then **Fastball**. Flypaper, String 'Em Up and Overclock after
play. One lab session can settle the shared unknowns: enemy velocity, the
stuck state, hold-A, and whether X and Down + A are free. New rooms help
here: the Control Roof and the Switchyard have barrels to throw and walls
to paste people on. Rules unchanged: authored clips, velocity only, no
slow-motion.

## Round five (2026-10-13): Overclock, Dragnet and Vortex in v0.13.0

Player, 2026-10-13 (answering "Round four"): "let's implement overclock.
Vortex does sound cool but i was thinking let's make a new ground string
(right now we have the base Y spam and spin cycle) and find a way to make it
web focused. flypaper does sound cool as well but i was thinking a different
variant where instead of how base A lets you web one enemy ... bust a bunch
of webs on like 5 enemies at once in front of you and then you have the
option to Y and throw them all towards me so i can combo all of them at the
same time. So could have something like flypaper and then vortex them, where
the vortex is a combo designed to combo multiple enemies at once (can change
names of everything if you want). **I think only these 3 more and no more
skills.**"

Shipped in v0.13.0 as first versions (CHANGES; engine facts in TECHNICAL
"Web lines, built hits and the web skills"). Agent-tested, not
player-confirmed. Names are the agent's (the player allowed renaming): the
multi-web is **Dragnet**, the string kept the player's word **Vortex**.

| Skill (ability bit, XP) | Input | First version | Next iteration from play |
|---|---|---|---|
| **Overclock** (80, 400) | Passive at combo tier 5 | Every hit Spidey lands also fires a web shot at the nearest other standing enemy within 60 units: a stagger for half a health unit, with a web line that flashes out to him. One shot per hit, the same enemy at most every 16 updates | Whether tier 5 is reached often enough (tier 4, or a shot every second hit below 5); shot damage; a different reaction (a short web hold instead of a stagger) |
| **Dragnet** (81, 500) | Keep A held on the web grapple (about 0.4 s into the hold) | Up to four more standing enemies in front within 48 units get a web line and the web hold (the game's own cocoon), without damage. **Y yanks all of them and the first target**: they fly to Spidey and land 6 to 10 units in front of him (half a unit of damage) while he plays the heave. Letting go any other way (A again, a jump, Up for Skyjack) leaves them webbed where they stand | A gesture for the burst (he keeps the hold pose); reach and count; whether held is the right input (a tap stays the native single web); catching the pile in the air instead of on the floor; fliers and bosses |
| **Vortex** (82, 500) | Y, Y, pause, Y, Y, Y (the third Y once he is back on his feet), or Y after a Dragnet yank | Three steps with their own clips: a spinning web whip, a hopping double lash, an overhead slam that sends everyone flying. Every contact also lands on each enemy within 14 units on either side, with a web line flashing to each. R cancels and resumes, A still Web Rushes out of it | The pause window (16 updates); clips from player feel; facing the crowd on each step; a pull toward Spidey on the lash (the "vortex"); its own finisher reaction (a launch) |

What the three share (worth knowing for any later work): the kit can now
draw the game's own web lines between Spidey and any enemy, and can build a
hit of any kind from nothing (hold, yank, stagger, knockdown, launch, pull),
with chosen damage. Left over from "Round four" and still only ideas: Thwip
Barrage, Face Full of Web, Yoink (the yank now exists), Fastball, Flypaper's
floor patch, String 'Em Up.

**The player wants no further skills after these three.** Iterate them, and
the ten before them, from play; do not propose new ones unless asked.

## Spider-Man 2099: future Black kit (2026-10-11, theorycraft)

**Player chose 2099:** "alright 2099 it is. Just theorycraft it" and requested
in-depth play/combo design. He is the future replacement for the existing Black
slot, after TASM Red is more fleshed out. Selection is confirmed; the mechanics
below are agent proposals, not approved implementation, agent-tested or shipped.
The player describes the current recolour as Anti-Venom, done for fun. Earlier
alternatives Miles, Kaine and Superior were considered; 2099 won this slot.

### Identity and foundation

**Catch -> carry -> crash -> chase.** A fast aerial hunter with coiled anticipation,
low pounces, crossing talon strikes, scissors kicks and abrupt diving finishes.
TASM creates new angles around enemies; Miguel drives the engagement through a
chosen line, then changes its height. Each impact should offer a next decision:
keep the target close, launch, drop it into the crowd, or disengage. Weight comes
from pose, contact and follow-through, never long freezes or slow-motion.

Character grounding: retractable talons, venomous fangs and a glide airfoil in
[Marvel's Miguel profile](https://www.marvel.com/characters/spider-man-2099-miguel-o-hara)
and [Marvel's Spider-Verse overview](https://www.marvel.com/amp/articles/comics/most-powerful-spider-verse-characters).
The seven-slot core prioritizes physical pursuit over a poison/bleed system.

**A remains native:** ground Power Dash, airborne Hammer Spike, airborne Down+A
Hammer Slam retain input, baseline movement and story barrier/unlock behavior.
Neither a charge nor a combat target is required to use them. Extra purchased
effects happen on enemy contacts/follow-up choices; do not intercept traversal
slams or dash-to-barrier use. No airborne A reinterpretation as a claw pursuit.
Ordinary B jump, base Y strings and unowned/native R behavior remain intact.
New moves live behind Black-form/purchase gates; preserve existing ownership,
refund/dependency rules, shared upgrades and progress. Prices/balance deferred.

### Seven purchased skills

| Native purchase | Proposed replacement | Main job |
|---|---|---|
| Webbed Fury | Hunter's Return | Recover a target after dash contact |
| Power Launch | Talon Lift | Choose grounded pressure or an aerial route |
| Ground Rebound | Predator Rebound | Turn a slam landing into another opening |
| Black Widowmaker | Raking Cross | New mobile string with front/back coverage |
| Poison Pummel | Talon Cyclone | Short crowd extension that exits into air |
| Super Charge | Predator Wind-Up | Charge purchased strikes during action |
| Quick Charge | Relentless Pursuit | Faster charge and one carried charged strike |

**Hunter's Return.** Native starting trigger: grounded A again after a successful
Power Dash hit, with a finite follow-up window. Miguel plants low, webs the struck
enemy back and rakes upward as it returns. Player chooses Y to start close pressure
or Up+A for Talon Lift; waiting leaves the original knockback useful. Aim/facing
selects the struck target, not an arbitrary distant enemy. For a recall-resistant
enemy, proposed fallback is a short visible pouncing strike toward it, without
moving the enemy or granting invulnerability. The attack must still connect in
range. Reject stale/dead targets; no auto-follow into a wall or off a platform.

**Talon Lift.** Native starting trigger: grounded Up+A. A crouched upward rake and
twisting shoulder lift launch a susceptible enemy. Miguel stays grounded unless
the player presses ordinary B to follow. At close range, the first purchased
aerial Y follow-up is a reaching rake; aim can favour the near side or pass across
the target. Then use normal air attacks, A spike, or Down+A slam as appropriate.
Against an unlaunchable enemy the rake still lands a direct attack; optional B
jumps Miguel, not the boss. Keep normal jump height/traversal available.

**Predator Rebound.** Keep the native purchased slam bounce as the starting role.
Down+A executes the normal slam; qualifying enemy contacts bounce susceptible
targets. Miguel does not automatically jump back up: B jumps manually, then a
timely Y can perform an angled catch/rake on a nearby rebound target. Staying
grounded allows Raking Cross instead. A hit against an immovable boss can open
the same short aerial follow-up opportunity, without bouncing that boss or giving
free airtime to Miguel. A floor/barrier impact alone never starts target pursuit.
Crowd slams provide multiple candidates; direction prefers one, with no unlimited
air magnetism. Rebounds create a route, not a promise of infinite stun.

**Raking Cross.** Native late-pause branch: Y,Y,Y, pause, Y,Y. New choreography:
low outside rake, passing heel kick, then a planted turn/back rake. Forward input
favours advancing across a close enemy; neutral stays compact; opposite direction
turns toward the threat behind. Both sides need real contacts. Ordinary enemies
can receive a modest pop at the end for manual jump pursuit; resistant enemies
receive close strikes with Miguel moving around them. Travel is short, collision
resolved and interruptible with R; avoid mandatory long lunges on ledges.

**Talon Cyclone.** Native late-pause repeated-Y extension of the purchased string.
A short travelling corkscrew claw/kick sequence sweeps front and rear, then ends
in a rising scissors kick that puts Miguel into a small, bounded airborne exit.
From there choose air Y to continue, A to spike, Down+A to slam, or owned air R
to leave. End after a compact sequence rather than indefinite mashing/spinning.
It differs from TASM Spin Cycle through forward travel, a defined rising exit
and its link into slam/rebound; no stationary handstand loop. Extra enemies can
be swept, but walls/bosses never have to move for the attack to function.

**Predator Wind-Up.** Keep hold-Y charging as the starting interaction, with
charged purchased strikes rather than a standing charge meter. Miguel coils as
the preceding motion completes; the next appropriate strike releases the charge.
The proposed charged version depends on the purchased move: Return gains a
pronounced pouncing rake; Lift gains an emphatic rising strike; Cross gains a
longer, still capped crossing attack; Cyclone gains a stronger sweeping finale.
The aim is a different attack shape/rhythm, not simply a scalar damage buff.
Quick uncharged attacks remain complete routes. R can abandon a charge; no
mandatory full wind-up, baseline dash/slam charging, blanket armour or new A hold.

**Relentless Pursuit.** Shorter charge time plus permission to carry one completed
charge through a brief evade or manual pursuit jump. Clear talon/pose cue shows
the next purchased strike is primed. The next eligible attack attempt consumes
it (even a miss); it expires after a short gap, getting hit, form/room change,
or a finished disengagement. Charging again replaces it; no stacked charges.
This enables wind-up -> R dodge -> charged Cross, or wind-up -> R dodge -> B
manual jump -> charged aerial rake against a target within reach. A charged
Lift spends the stored charge itself; it cannot also give a free charged catch.
Native A dash/spike/slam do not consume it, while their eligible purchased
follow-up strikes can. No perfect-dodge automatic counters, time slowing,
or permanent global move-speed buff. It rewards carrying an attack opportunity,
distinct from TASM's whole-string resume identity.

### How the complete kit connects

Proposed routes below require the named purchases and close-enough targets.
Inputs beyond native entry triggers, windows and movement remain unproven.

- **First chase:** ground A dash -> A Return -> Up+A Lift -> B normal jump ->
  Y aerial rake/normal air hits -> Down+A native slam -> rebound -> B,Y catch.
  At the rebound, staying down instead starts the next ground string. Air A spike
  is an alternative ender, not a guarantee that another slam is available.
- **Crowd lane:** dash a flank enemy -> Return -> Y,Y,Y,pause into Cross ->
  repeated Y Cyclone -> small airborne exit -> Down+A slam -> choose a bounced
  target with B/Y, or stay down and turn Cross toward the next threat.
- **Charged re-entry:** charge during purchased pressure -> complete/bank ->
  R out of a telegraphed attack -> short reposition -> next eligible Cross/Return
  strike spends the charge. Normal dodges still need timing; no automatic hit.
- **Resistant boss:** dash contact -> Return's short pursuit fallback -> compact
  Cross/direct charged rake -> R escape when the boss retaliates -> native A dash
  re-entry. Use manual jump/rakes/slam when an actual opening permits. No forced
  launches/recalls/rebounds, permanent stagger, or unproved boss armour breaks.
- **Mob beside boss:** use the mob's launch/Cyclone as an air entry toward the
  boss, strike within reach, and slam nearby enemies during its recovery. Target
  switching never teleports Miguel; closing the distance still matters.

Every purchased sequence should offer R exits, with ordinary dodge behavior and
ownership requirements retained (especially shared Air Dodge). Cancelling before
contact gives up the hit; after contact it can cut recovery. Hunter's Return is
optional, Lift never auto-jumps and Rebound never auto-catches. Steering, target
eligibility, geometry and enemy retaliation keep the player involved. Repeated
relaunches may need reduced lift/rebound on ordinary enemies to prevent one-button
locks, without imposing long waits or killing varied combos. Details await play.

### Presentation, growth and later possibilities

New purchased clips need continuous motion, anticipation, overlap and matched
contacts (TECHNICAL "Kit animation authoring"). Silhouette: low crouch and splayed
hands on entry, body stretching through a pounce, torso leading a crossing rake,
feet leading the downward finish. Cape/airfoil trails motion if feasible; subdued
talon trails and distinct contact cues should remain readable at DS resolution.
Do not reuse generic native punches with claw effects and call them new moves.

Early Return+Lift teaches dash -> recall -> ground/air choice. Rebound completes
the vertical loop; Cross+Cyclone gives crowd routing; Wind-Up+Relentless adds
charge decisions while moving. Existing owned slots migrate only in a later
qualified release, no free paid moves or loss of story progress. Both Suits
Kick-Off/Drill Kick/air evade/recovery can bridge routes when separately owned.

Possible later skills, outside these seven: a purchased short glide-to-rake,
wall/ceiling pounce, or a close fang finisher during an earned enemy opening.
Glide must not hijack B jumps or A spike/slam; fangs must not require bosses to
accept paralysis. All are optional research; core fun should work without them.
First eventual prototype should prove native A parity plus Return -> Lift ->
slam/Rebound and a resistant-boss direct-contact route before extra effects.
