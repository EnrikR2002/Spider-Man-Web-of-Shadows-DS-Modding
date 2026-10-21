# TASM: never stand still

Design and player feedback, beginning 2026-10-05. First versions of all seven
original Red skills shipped in v0.2.0; the player praised v0.2.0/v0.3.0 and later
requested specific corrections and extensions. Current objective/build/verdict:
[TASKS](TASKS.md). Shipped behavior: [CHANGES](CHANGES.md); engine contracts:
[TECHNICAL](TECHNICAL.md); development/quality review: [DEVELOPMENT](DEVELOPMENT.md).

Dated sections retain design snapshots and decisions. Their original "next" or
"proposed" wording does not override later implementation or player instructions.
Overclock, Dragnet and Vortex are the last added skills; further skills and the
2099/other-suit theorycraft remain deferred. The player accepted0.24's environment
and more distinctive enemy direction, while rejecting rigid motion, poor SFX
and the slow/easy boss.0.25 is the authorized correction; its mechanical tests
and presentation review do not establish the player's fun verdict.

**Delivered0.26.0 (2026-10-19).** The boss now reacts to real hit pressure
with physical escape/return attacks and faster, lower acrobatic movement. The
quiet-cue regression has actual in-game waveform controls for all three
Midnight species. This is agent-tested; the player's replay decides its feel.
Shipped details and limits: [CHANGES](CHANGES.md).

**Delivered0.28.0 (2026-10-19).** The player found the boss more comboable but
still too easy or unreliable because attacks seemed absent or missed, and did
not feel the enemy ramp. They also requested removal of two save rooms, a map
that matches the upper route, and stronger presentation. The release changes
boss contact/counter handling, removes both rooms and entrances, corrects the
map, and escalates the last encounters. Structural and agent gameplay checks
pass; the player's full-route replay and quality verdict remain pending. See
[CHANGES](CHANGES.md) and [TASKS](TASKS.md).

**Latest0.25 replay verdict (2026-10-18).** The boss is somewhat better but
remains too slow and vulnerable to continuous combos; its claimed poise does not
provide an effective counter/escape. Rebuild it as a hyper-mobile electronic
symbiote monster, with real responses to pressure. Midnight's monsters appear
silent: sound rendering must be demonstrated against an isolated silent control.
Earlier agent claims about sound and anti-combo behavior are not player acceptance.

**Latest player verdict on0.24 (2026-10-18).** The environment is much better
and the enemies feel more unique: preserve that accepted direction. Movement
still looks rigid, like a doll, and sound effects sound bad. The Conductor is
visually unimpressive, slow, over-choreographed and too easy. Authorized next
work: much more dynamic continuous animation, better mixed sound, a visually
stronger and genuinely challenging boss, and the original game's boss health
bar. Mechanical clearability is insufficient; review actual native-scale
footage and mixed audio before expanding the prototype or publishing0.25.

**Delivered0.25.0.** The authorized correction is installed and agent-tested;
the player's replay will decide its feel. Shipped behavior and validation
limits belong to [CHANGES](CHANGES.md).

## Midnight0.23 replay feedback (2026-10-18, historical)

The player explicitly rejected0.23.0 enemies again: some attacks do not work,
most sounds are recognizable from existing characters, animations look slow and
odd, and attacks are unconvincing. This supersedes the prior agent assessment of
the Forge/spectacle enemies. Do not defend sample counts or contact counters as
quality evidence. Reproduce actual hits/misses, native frame cadence and all
inherited audio paths; establish one complete fast, fluid, distinctive enemy in
the real engine before extending the result across the roster.

The terrain looks much better. Preserve its material improvements. The playable
room structures remain repetitive rectangles, despite decorative additions.
Change silhouettes, dimensions, proportions and route organization: compact
shelters, long concourses, bent service channels, asymmetrical shafts and broad
chambers must actually play differently. Collision, camera, roofs and doors
must agree with the visible outline; a different wallpaper is insufficient.
Current work/evidence is in TASKS. This is implementation authorization, not a
quality acceptance of any subsequent candidate.


**Implemented in0.24.0 (2026-10-18).** The correction fixes native hit activation
and failing attack carriers, shortens whole-body motion, improves planted heavy
impacts and silhouettes, and scopes57 recorded voices/foley to the seven private
enemies. All ten Midnight room envelopes/collision/maps are rebuilt with actual
L/T spaces, different shelter sizes, diagonal/sloping chambers and a stair return.
Native HP hits, mixed clears, doors, both-suit boss wins and earned-save Continue
are agent-tested; CHANGES and reference/midnight_rebuild.json own the exact scope
and limits. Ballast's directly-overhead Freight pursuit remains a known edge
case. The0.23 player rejection is retained; it is not retroactively acceptance of
these new poses, attacks or layouts. The next player replay decides their feel.

## Chapter evaluation against v0.22.1 (2026-10-17)

**Implementation approved by the player, 2026-10-17.** The evaluation below is
the accepted direction; current candidate/testing/publication is in TASKS.
Player approval of the plan does not establish acceptance of the implementation.

**Implementation status:** shipped in0.23.0. The pass adds collision-honest roof
pursuit, staged encounters, saved pump/power responses, coordinated Conductor
pressure, a damaged hoist phase, an approach checkpoint, new materials/depth,
clearer creature mass and recorded machinery/ambience cues. Crown was tightened
to two three-role waves after the longer heavy repetition failed the pacing
review. CHANGES owns shipped details; reference/chapter_spectacle.json owns
exact controls/fixtures. Player quality acceptance and actual DeSmuME pacing
remain open. Moving trains, rideable loads and new campaign branches are still
deferred. The evaluation below remains the dated0.22.1 assessment.


**Evaluation against 0.22.1.** Reviewed the
published composition, all 22 active room presentations, original Pier/subway
architecture, final Forge creature/boss captures, encounter scripts and progress
contracts. Exact evidence and limits: `reference/chapter_evaluation.json`;
captures/traces: `work/chapter-evaluation`. The 128 renewal room resources are
byte exact to 0.21.0. Earlier room captures therefore remain useful for scenery;
they do not establish the current enemies' appearance. Fresh copied-save probes
use 0.22.1. Neither healed lab observation nor an isolated duel decides difficulty.

**Assessment:** both chapters have usable foundations. Midnight has a coherent
storm identity and compact circuit, but too many stops offer the same activity.
Crane has the stronger exploration structure and distinct terrain, but its
machinery, presentation and finale do not yet deliver the scale its premise
promises. Their next improvements should make existing spaces more purposeful.

The original game's standard is fluid control, readable enemies, atmosphere and
mission flow. Griptonite's studio head explicitly describes those priorities in
his [development retrospective](https://www.gamedeveloper.com/production/five-years-20-lessons-20-ds-games).
The design inference here is to make spectacle support movement and decisions.
A longer map or a more elaborate model only earns its place when it improves
what the player experiences on the route.

### Midnight Line: a storm that builds toward its source

Keep the train terminal, flood infrastructure, turbine ascent, observatory and
Conductor. Make their relationship physical: rail power feeds the storm system;
the Conductor is visibly drawing from it. Introduce a cue safely, complicate it
in an encounter, then combine it in the boss. The chapter should progress from
an abandoned public place into increasingly active machinery.

**First priority is encounter reachability.** A fresh unisolated Terminal probe
finds a carriage-edge perch with a Warden immediately below, outside its vertical
engagement threshold. This needs a terrain/AI correction before adding pressure.
Test the actual perch and nearby ground with native input, full enemy HP and
both suits. Widening every attack volume would hide the navigation problem and
make unrelated fights less readable. Engine details belong in TECHNICAL.

**Replace the generic patrol rhythm with authored encounters.** Six ordinary
rooms use the same table-8 patrol recipe and a room-wide spawn region; species
selection cycles across the same roster. This can populate rooms, but it does
not author a first reveal, a crossfire or a particular traversal choice. Start
with one Skitter on an open stretch, teach the Warden's distinct response on a
wide landing, then introduce the Eye across a clearly reachable lane. Mix them
only after those roles are readable. Keep entrances, save access and recovery
landings free from immediate attacks.

**Give each stop a specific purpose:**

| Existing space | Proposed improvement |
|---|---|
| Storm Gate | Frame the distant destination; one short Skitter introduction and a clear main shutter. The return balcony should become recognizable later. |
| Signal House | A warm, quiet public-service interior, its own silhouette and one concise clue about the rail power problem. Preserve the save. |
| Midnight Terminal | Build a continuous, collision-honest carriage-roof route and a broad platform fight below. Let route choice change the encounter. |
| Floodworks | Put a broad service deck beside a visibly unsafe, warned channel. A local action should visibly stabilize a pump or expose a route. |
| Pump Refuge | Contrast the noisy pumps with a sheltered maintenance nook. Preserve the safe save and distinguish it from Signal House. |
| Turbine Rise | Turn repeated steps into a climb around the turbine's shape, with readable wall movement, recovery shelves and one roomy combat landing. |
| Storm Observatory | Give the player a brief unobstructed view of the source, then a deliberate final mixed encounter using previously taught cues. |
| Relay Sanctuary | Preserve the checkpoint immediately before the boss. Make the next door's significance obvious without a long instruction panel. |
| The Conductor | Connect the creature's gestures, arena lanes and phase changes into one readable performance. |
| Crown Return | Deliver a swift descent through a visibly quieter system. Keep only light, optional patrol pressure and a satisfying return reveal. |

Floodworks should initially use a switch plus a static, saved before/after
configuration. Actual draining water, changing solid platforms and a moving
train are separate research projects. A playable train sequence would be a fine
stretch goal only after moving collision, camera behavior and interruption
recovery work in one complete example. A sweeping background and foreground
supports can already convey scale with fixed native traversal.

**The Conductor needs stage direction.** It already has four authored moves,
real HP damage/death and HP-driven arena phases. Its creature program and the
floor-lane timer are nevertheless separate systems. Coordinate their pressure
so an evasive route remains available; teach the low pulse and high/low attack
lanes earlier. Let each phase change the arrangement or order of familiar
threats, accompanied by a clear body/arena cue. Keep ordinary combo openings and
R repositioning meaningful. Avoid long invulnerability or permanent armor.
Finish with a readable collapse, electrical shutdown and persistent calm.

### Crane Row: a harbor you explore, restart and climb

Keep the twelve-room district, recoverable falls, lower ship route, roof paths,
Engine House shortcut, upper loop and waterfront return. These are substantial
strengths. Make the huge crane seen from Quay consistently recognizable from
the ship, Gantry and Crown, with coherent supports, cab, arm and cable direction.
Repeated skyline wallpaper should give way to room-specific foreground/middle
distance composition and a clear sense of increasing height.

**Make power restoration an event.** Today the lever earns progress and opens
routes, but most of the district remains the same static arrangement. Reuse the
power flag for a visible change: lamps come on, a winch starts behind the play
plane, an access panel opens and the shortcut is revealed. Preserve the lever's
single permanent outcome. Use fixed safe landings first; the existing moving
counterweight is scenery and has not established rideable collision.

| Existing space | Proposed improvement |
|---|---|
| Quay | Compose a strong first crane reveal and teach one safe gap/recovery route. Introduce the Maw where its pounce is readable. |
| Freight Exchange | Make ground combat, cargo roofs and Office access three legible choices. Put threats where each route changes the tactical approach. |
| Harbor Office | Preserve the safe checkpoint; use its window/chart to establish the crane destination and show power returning. |
| Container Warren | Give roof/underpass routes different encounters or discoveries. Break the rectangular stack silhouette with openings and a recognizable central landmark. |
| Dry Dock | Make bow, hold and deck read as parts of one vessel. Stage an encounter through a broad hold with a usable upper escape route. |
| Engine House | Turn the power switch into a short visual/sound payoff that explains the newly available shortcut. |
| Counterweight Shaft | Organize the ascent into a few distinct stages around the machinery, preserving wall channels and safe recovery. Keep combat off cramped jump ledges. |
| Gantry Spine | Pay off the height with a view of earlier landmarks, a flowing exposed traverse and one broad combat pocket. |
| Winch Cache | Make the detour reveal a memorable maintenance space and a clearly valuable native supply stash. Current completion is tied to barrels, not a special upgrade. |
| Crane Crown | Build the two existing finite waves into a deliberate mixed-species test; reveal the final arm and offer a short, safe retry route. |
| Long Arm | Integrate the moving grabber, arm structure and damageable motor into one convincing machine encounter. |
| Breakwater | Show the disabled crane from below and give a fast return with one optional discovery, retaining a small revisit patrol. |

**The hoist is the largest spectacle opportunity.** Its warnings, committed
target lane, moving grabber, protected motor and native damage callback already
work. But the three attack lanes span only 64 units near the end of a 420-unit
room; much of the space is approach. The normal slam/sweep loop exposes the
winch for about 42% of its scripted delay budget. That is an opening for a
stronger encounter, but can also become waiting beside a small target.

First improve framing and physical cause/effect: show the cable tightening,
commit the grabber before impact, connect the vulnerable motor visibly to that
motion, and make the recovery long enough for a satisfying native combo. Build
the other portion of the cycle around useful repositioning or an optional
throwable opportunity. Keep hits local to visible warnings. Later, a real-HP
phase change could damage the guard or change the lane sequence; research the
core HP observer before promising it. Avoid a succession of mandatory switch
presses or a longer damage sponge. Give victory a sagging cable/disabled motor,
sound release and immediately usable return.

**Reduce boss retry friction.** The district's save is the Office, well before
the ascent. The earned Crown/Engine shortcut helps, but a retry should not
replay a long climb or both mandatory waves. Measure the real Office-to-hoist
route with existing progress. If it is still cumbersome, prototype a quiet
native save point on the cleared Crown/approach or a shorter return connection.
Verify the saved default spawn, boss reset and safe sphere access before adding
it. Retain some nonblocking patrol life on saved revisits, as the player asked.

### Shared improvements that determine whether either feels finished

- **Readable art at 256x192.** Native comparison views have strong local light,
  material boundaries and modeled architectural depth. New rooms often expose
  broad, uniformly lit blue/gray slabs. Break those surfaces at structural
  joints, add restrained baked shadow/value gradients, readable fascias,
  recesses and supports. Make the near collision plane clearest, silhouettes
  distinct and distant scenery quieter. Inspect native pixels before increasing
  texture resolution or detail. Keep visible roofs and doors.
- **Different enemy decisions.** Forge already supplies original motions,
  contacts and sounds; another blanket asset replacement misses the next issue.
  Selection still advances through a fixed move list. Give the Maw a committed
  pursuit/punish role, Ballast a slow territory role and Spore a reachable ranged
  support role. Give Skitter rapid lane changes, Warden high/low cadence and Eye
  a clear line-attack role. Choose among the existing moves using distance,
  elevation, facing and recent history, with consistent tells and recoveries.
  Do not respond to hidden player input or attack from outside the camera.
- **Complete, legible bodies.** Current captures still show thin, similarly
  proportioned bodies against busy backdrops. Prioritize silhouette, limb
  separation, side-facing cores, planted support and weight over small texture
  markings. Review locomotion, interrupts, prone land/get-up and death at normal
  speed, including two species together. Sharing a rig is acceptable when the
  resulting motion and tactical response are distinct.
- **Fair mixed pressure.** Audit spawning at both entrances, vertical pursuit,
  recovery pits and offscreen firing. Limit overlapping commitments so the
  player can read a threat and retain a combo with R. Tune encounter placement
  before HP/resistance. Preserve native juggles, throws, reactions and real
  rewards, and keep a route for baseline Red/Black without optional purchases.
- **Sound and music progression.** Build on the 57 new creature cues. Midnight
  needs electrical/bell identities and an increasingly active terminal; Crane
  needs chain, servo, hull and waterfront identities. Add sparse room ambience,
  distinct attack tells and a clear victory release. Check the actual mix so
  ambience or simultaneous voices never mask a contact warning. Per-room audio
  routing/channel budget remains a prototype, not a proven soundtrack feature.
- **Purpose and payoff.** Give each branch a brief reason to enter tied to the
  city's invasion, evidence of what happened, a visible response to the player's
  actions and a saved completion state. Use optional discoveries, native pickups
  and shortcuts as rewards. Preserve the existing shop/skill/save contract.
  Keep main goals short on the map, detailed directions on Objectives and X
  prompts near their actual target; avoid more floating signboards.
- **Performance and continuity.** Profile the busiest mixed encounter with
  normal DeSmuME audio/rendering and normal-speed input. Record frame pacing and
  missed inputs, not just emulator throughput or mesh counts. Compare room
  loading, camera framing, transitions, defeat/re-entry and earned Continue with
  native rooms. A static backdrop cannot substitute for an active set piece,
  but inexpensive staged changes can sell a larger event.

### Recommended order and acceptance

1. Correct the Terminal perch/engagement problem and audit analogous Crane
   terrain with full native-HP mixed crews. Preserve a paired failing/control
   trace; qualify the fix on a new candidate.
2. Finish one representative sequence in each chapter: Terminal's two-level
   encounter feeding a storm cue, and Long Arm's complete hoist cycle with
   convincing art, recovery, sound and victory. These are the standards for
   further room/enemy work, not additional roster-wide experiments.
3. Author the room-specific encounter progression and low-cost saved
   before/after events. Improve materials, silhouettes, audio mix and the short
   narrative thread around those events; preserve the accepted connections.
4. Review ordinary full-route Red/Black play with no healing, no parked/weakened
   enemies, no position fixtures and both sparse/established optional purchases.
   Measure retry travel and frustration separately from clearability. Then run
   final door/save/composition qualification and obtain the player's quality
   verdict before treating the design as accepted.

Moving trains, rideable loads, altered solid geometry during play, major camera
hooks and new boss UI are higher-risk prototypes. Current room scripts, private
move descriptors, meshes, audio assets and saved flags already support most of
the first improvements. No more rooms, skills, third suit or shop/save expansion
is needed for this plan. These proposals do not change v0.22.1's published bytes.

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

2026-10-17 follow-up: the player rejected renewal's enemy quality. Creature
Forge replaces ordered stock attack handlers with22 private movement/contact
programs, UV-painted articulated models and layered recorded foley. Crane's
scissor/vault/charge/rupture attacks and Midnight's switchbacks, tolls and
high/low electrical lanes need distinct anticipation and punishable recovery.
Correct wrist chains, grounded weight transfer and full knockdown lifecycles
matter more than adding decorative parts or merely changing action order.
The player's existing kit stays intact; these enemies give its evade/reposition
loop different rhythms. No additional player skills are added.
Published in0.22.0, with atlas material sampling corrected in0.22.1. Native-input
duels and boss/save controls pass; the player's quality/fun verdict is pending.

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

## Historical kit status (v0.4.1)

This table describes 0.4.1, not the current build. Later dated sections record
subsequent extensions; current shipped behavior is in CHANGES/TASKS.

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

## Historical proposals (2026-10-07)

These were unapproved at the time. Check later decisions/implementations below
before treating a proposal as available, deferred or still awaiting approval.

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

## 3 new skills (2026-10-13): Overclock, Dragnet and Vortex in v0.13.0

Shipped in v0.13.0 as first versions (CHANGES; engine facts in TECHNICAL
"Web lines, built hits and the web skills"). Agent-tested, not
player-confirmed. Names are the agent's (the player allowed renaming): the
multi-web is **Dragnet**, the string kept the player's word **Vortex**.

| Skill (ability bit, XP) | Input | First version | Next iteration from play |
|---|---|---|---|
| **Overclock** (80, 400) | Passive at combo tier 5 | Every hit Spidey lands also fires a web shot at the nearest other standing enemy within 60 units: a stagger for half a health unit, with a web line that flashes out to him. One shot per hit, the same enemy at most every 16 updates | Whether tier 5 is reached often enough (tier 4, or a shot every second hit below 5); shot damage; a different reaction (a short web hold instead of a stagger) |
| **Dragnet** (81, 500) | Keep A held on the web grapple (about 0.4 s into the hold) | Up to four more standing enemies in front within 48 units get a web line and the web hold (the game's own cocoon), without damage. **Y yanks all of them and the first target**: they fly to Spidey and land 6 to 10 units in front of him (half a unit of damage) while he plays the heave. Letting go any other way (A again, a jump, Up for Skyjack) leaves them webbed where they stand | A gesture for the burst (he keeps the hold pose); reach and count; whether held is the right input (a tap stays the native single web); catching the pile in the air instead of on the floor; fliers and bosses |
| **Vortex** (82, 500) | v0.15.1: Y, Y, Down+Y, release Down and mash Y; old pause and Dragnet entries remain | Four steps: spinning whip with a return lash, double lash twice, overhead slam. Seven contact opportunities around Spidey; native range/reactions decide actual hits. Arm follow-through connects the authored clips. R preserves the steps through the native dodge/landing, avoiding Drill Kick stealing the resume; A/B/Up keep their exits | Player feel of the longer string; automatic crowd-facing; an inward lash pull; an authored launch finisher |

What the three share (worth knowing for any later work): the kit can now
draw the game's own web lines between Spidey and any enemy, and can build a
hit of any kind from nothing (hold, yank, stagger, knockdown, launch, pull),
with chosen damage. Left over from "Round four" and still only ideas: Thwip
Barrage, Face Full of Web, Yoink (the yank now exists), Fastball, Flypaper's
floor patch, String 'Em Up.

**The player wants no further skills after these three.** Iterate them, and
the ten before them, from play; do not propose new ones unless asked.

2026-10-14 feedback: Vortex felt short/clunky and hard to enter without
Dragnet. Published v0.15.1 adds the explicit directional entry and extra lash;
early/late/fast entry and R resume passed among all 68 kit checks, with 12
crash seeds. The revised feel is not player-confirmed.

## Midnight Line storm overhaul (2026-10-16)

User requests wholly original areas instead of sewer/Hive recolours, new enemy
identity and a real, impressive combat boss. The0.20.0 implementation replaces
rooms76..90 with a storm terminal, glass sheds, skyrail, floodworks, turbine
climb, capacitor hall and observatory; Substation remains. No additional skills.
Rail Skitter, Bell Warden, Arc Eye and Conductor have original geometry/voices
on native enemy frameworks and shared authored full-lifecycle choreography.
Conductor is a normal damageable creature with storm attacks that escalate at
half/quarter HP. Native combos, R repositioning, fast pace and ownership remain.
Completion requires its actual death callback. Agent qualification/publication
status is in TASKS/CHANGES; fun, spectacle and difficulty need the player's verdict.

**Player feedback,0.26,2026-10-19:** the boss is harder/cooler and its mobility
and strength are welcome, but blanket stagger suppression makes combos impossible
and the difficulty frustrating. Restore meaningful combo openings; retaining
knockdown resistance and counters is acceptable. The boss and other Midnight
creatures still look/animate poorly. Improve their silhouettes and continuous
motion, and build encounter pressure toward the boss without flattening the
chapter into equally crowded rooms.0.27 now implements combo openings, a bounded
counter, cleaner articulated creature anatomy/motion and a four-room encounter
ramp. The player's next verdict rejects0.27 difficulty/contact reliability:
boss combos are slightly better but it is too easy/appears inactive or misses;
the ramp is not felt. Remove Signal House/Pump Refuge plus incoming doors, fix
upper map order and prioritize reliable pressure.0.28 corrects the native counter
route/guard loop, uses current-owned validation and revises the actual staging.
Player quality acceptance remains pending.

## Midnight Line new boss (2026-10-13, Signal Leech v0.14.0)

**Implementation update, same day:** the user requested implementation.
Signal Leech is published in v0.14.0, room 94 beyond a new Roof left
passage. Three durable infected cores, a compact original machine backdrop,
large harmless flashing lane panels, three guarded pressure phases, bounded
strong crews and a one-use X breaker are implemented (about ten seconds,
corrected by v0.15.1 timer measurements). Native
player controls, purchases and the Roof's repeatable fight are preserved.
Actual attacks have won the full-health Red encounter without health
refills; kit/crash/room/save qualification passed. Native near-death recovery
preserves partial progress. Player verdict on fun, cues and difficulty is
pending; no more skills were added.
Technical contracts and evidence: TECHNICAL "Signal Leech implementation".
2026-10-14: player completed the encounter but requested visible cores,
cleaner terrain, clear target order/safe floor/warnings, mostly in the
Substation and boss. Published v0.15.1 makes any-order cores bright,
removes the suspended shelves, marks green refuges and powered strips,
and keeps warning lights below the targets. Readability/HP qualification
is agent-tested; player feel remains pending. See TECHNICAL "Signal Leech readability".
The earlier recommendation/design below is historical research context.

**User request:** explore how to implement a new Midnight Line boss so another
agent can implement it later. User chose **explore both machine/arena and
new-character routes, then recommend**. This section is an agent proposal,
not player-approved identity, mechanics or balance. Nothing was implemented
or played in this research session. Technical evidence, exact engine entry
points, experiment gates and file ownership are in TECHNICAL "New Midnight
Line boss: implementation research handoff".

**Recommendation: start with Signal Leech, a symbiote-infested signal machine
in a fourth Substation room after the Control Roof.** This uses the working
room compiler, hazards and waves to make a new encounter around movement and
combat. Keep the Roof's repeatable fight intact. Signal Leech is a provisional
name from the older queue; its visual identity and final name remain open.
The recommendation is conditional on a core-damage/telegraph prototype being
fun: three instantly broken boxes with waves around them are not enough.

| Route | What can make it new | Evidence and remaining work | Recommendation |
|---|---|---|---|
| Machine/arena | Original arena silhouette, destructible circuits, distinct lane patterns, phase escalation, breaker opening and strong adds | Room generation, cycling hazards and waves already work; core durability/callbacks, harmless cues, locks and cleanup need small experiments | First choice for the next substantial encounter |
| Native character with new encounter rules | Familiar body in a new arena with changed pressure/recovery | Existing native mini-boss works in the chapter; transplant/zone dependence, phase control and kit compatibility remain open | Useful prototype/control, not the promised fully new character by itself |
| Rival on compatible rig | New authored movement/attacks and visual identity using the player-compatible animation setup | New finding: m6 binds 121 player clips at 37 joints, and MiniBossStateMachine derives from SpideyStateMachine; factory/model binding, scoped copies, AI and targeting still need proof | Best character research branch if the player prefers a mobile opponent |
| Entirely new model/skeleton/AI | Fully original character silhouette and moves | Current animation authoring hardcodes player joints; no complete proven enemy model/rig/AI pipeline | Defer until a compatible-rig boss works |

### Proposed Signal Leech fight

The machine occupies the back/upper part of a compact combat space. Three
visible infected relay cores sit within reachable foreground fighting
positions. Cables and warning markings tie each core to its lane so the
player can read what will happen without a dialogue box. Draw the machine
as original room geometry initially; moving tendrils/custom effects need
their own proof. Far skyline, lit undersides and safe floor space follow the
Substation lessons. No unseen late-game texture set.

The basic loop is **read a cue, jump or evade through a safe lane, land a
combo or throw, break a circuit, keep moving**. Direct attacks always offer
a victory route; throwables and the optional breaker create advantages.
Strong, bounded add waves give Dragnet/Vortex/Overclock useful targets, with
no new skills or purchases required. Do not promise that a machine core can
be perched on or web-yanked: those interactions need explicit proof.

| Stage | Pressure | Opening / player response |
|---|---|---|
| Entry | Machine is idle until Spidey is fully inside; brief readable reveal | Inspect the three cores; entry corridor remains safe before the trigger |
| Three cores left | One clearly marked floor lane pulses after a harmless cue; small strong crew | Cross with B/R, keep a combo through repositioning, hit any reachable core |
| Two cores left | Alternate lanes or sweep a short sequence; one fresh add batch | Use upper/lower routes and the visible safe lane; carry the pile with the kit |
| One core left | Faster pattern transitions with a guaranteed safe route; final bounded add batch | Optional breaker gives a short power cut, then an explicit warning before power returns |
| Victory | All damaging circuits stop, exits open, machinery stays visibly dead | Short completion line, persistent chapter flag; no stolen story ability or repeated reward |

These are pattern proposals, not finalized attack timing, HP or enemy counts.
Phases come from actual core destruction, never an elapsed-time auto-win.
The boss must not force idle waiting for long invulnerability windows; keep
cores hittable in the first prototype and let lane pressure create the
openings. Do not use live arcs as a supposedly harmless warning, spawn enemies
endlessly, stun-lock the player on landing or stack damage across every route.
No slow motion, forced teleport, mandatory paid move, or removal of native
A/B/R behavior. Victory must remain possible with the chapter's current
story abilities (0..4) and without all optional kit purchases.

Completion is proposed as one-time and saved normally; death before victory
restarts the encounter. The old Roof remains repeatable. Replay terminal,
XP payout, custom boss health bar, Conductor teaser and a nearby save room
are separate follow-ups; they are not prerequisites quietly added to this
boss. A three-core visual/brief progress line is honest segmented progress,
not a fake native HP bar. If readable progress demands new UI, budget that
work explicitly rather than interrupting every exchange with dialogue.

### Order for the implementing agent

1. Re-read current TASKS and the technical handoff; baseline may change.
   Build a disposable core/cue experiment before final art or a full fight.
2. Prove melee damage, once-only destruction credit, harmless warning,
   hazard shutdown and death/re-entry. Test with ordinary controls; a RAM
   kill cannot qualify core durability or fun.
3. If those pass, build the fourth room, one pattern and three cores; walk
   through its real entrance/exit and complete an unweakened attempt.
4. Add guarded phases, bounded strong adds and the optional breaker. Stress
   simultaneous core breaks, victory during a queued attack and fast re-entry.
5. Finish presentation, map/objective and persistence, then qualify the
   combined candidate and hand it to the player through the normal launcher.

If ordinary props cannot support satisfying damage/recovery without a large
engine patch, stop expanding this version and test the m6-compatible rival
route. Its first deliverable is one independently bound enemy with one new
telegraphed attack and a reliable death callback. A native mini-boss is
excluded from today's common-enemy registry, so kit targeting and damage
adapters belong in that prototype, before promises of riding or webbing it.
Only choose final character identity/art after that vertical slice works.

## Campaign branches outside Midnight Line (2026-10-14, Crane Row approved)

**Construction approved, 2026-10-14:** "yeah sounds super cool, get building".
Build the twelve-room Hanging Harbor pitch, including both loops, checkpoint,
large authored spaces, maps and a crane finale; prototype machinery honestly.
**Design direction:** Crane Row selected. Midnight felt
"small and underwhelming"; take time to design a much bigger, more impressive
map and riff the ideas to the player before construction. The old three-room
Crane slice and nine-room shared first wave are superseded. The twelve-room
pitch shipped in0.16.0; its terrain/encounters are overhauled in0.17.0 after
the player found the early map boring/bland. Current status is in TASKS/CHANGES.
Existing story routes and the present kit remain the foundation. Earlier
Slingshot-dependent designs are obsolete:
these places must work with native jump/swing/wall movement and the player's
existing story abilities; paid TASM moves make combat more expressive rather
than unlocking required terrain. No further skills.

Machine-readable room outlines, materials, entrance candidates, owned
IDs/flags and research gates: `reference/area_roadmap.json`. Engine evidence:
TECHNICAL "Campaign branch research" and `work/area-research/`. None of these
areas is player-confirmed. Crane Row's twelve rooms, Pier entrance, checkpoint,
two returns, local/detail maps and hoist machine are published and agent-tested.
The0.17.0 overhaul awaits player feedback. Other branches remain
designs. Counterweight movement is scenery; fixed landings carry Spidey.

| Branch | Proposed progression | What makes it different | Proposed entrance |
|---|---|---|---|
| **Pier: Crane Row** | Twelve-room district; cargo-yard loop -> upper crane loop -> Long Arm -> waterfront return | Giant crane/grounded ship landmarks, stacked routes, substantial authored spaces and a dedicated machinery finale | Pier_Save02's unused right side; its left door/save stay native |
| **Downtown: The Grid / Lost Lab** | Cable Well -> Lost Lab -> Switchback | Vertical building-services shaft and an abandoned laboratory; redirect one power feed to change the route | A new service access inside Downtown_Save03, retaining both Map12 exits |
| **Residential: Skyline Run** | Roofline -> Water Tower Steps -> Skyline Relay | Broad roof jumps, fire escapes, tower supports and a distant skyline; recover from falls instead of falling into death pits | New access by Residential_Map09's upper roof, or an interior access in Save02 |

### Crane Row: The Hanging Harbor — expanded pitch

**Player feedback, 2026-10-15:** the partly explored map feels boring and bland;
the hoist is unplayed. The route itself must make the player want to continue.
The overhaul replaces repeated flat-floor/crate rooms with an opening broken
quay, a cargo-roof express above the Freight arena, tall container canyons,
a ship deck with dive-through holds, counterweight switchbacks and a fractured
gantry over recoverable service decks. Encounters use varied existing native
crews, throwable cargo and two bounded Crown waves; no new skills, slow motion,
required paid traversal or repeated timed victory. Keep the established graph,
map guidance, checkpoint and persistent clears. Implemented/published in0.17.0;
agent qualification is in CHANGES, and the player's fun verdict remains pending.

**Crane creature direction, 2026-10-15:** Pier enemies feel weak/boring. The player
explicitly selected entirely new creatures with new attack animations. Implemented
original shipyard mutations: a low pouncing Mooring Maw, a ballast-shelled heavy
and a floating spore caster. Distinct authored meshes/attack motion and readable
windup/commit/recovery matter; imported enemies or recolours alone do not meet
this request. Preserve combo/juggle/cancel play, current traversal and earned
progress. Published0.18.0 implements three original meshes and47 authored
clips (31 attack routes), retaining native rigs/AI/spawners. Maw has a low
four-limbed silhouette, paired jaws/four eyes and claw attacks; Ballast has
asymmetric armoured claws, shell spines/forked tail, sweeps/charge/two-arm slam;
Spore has a hovering bell/core and tendrils with authored casting motion.
Windup/commit/recovery remains fast; one private fast-slam event is delayed
inside its original clip. Mixed crews use1+1+2 native costs with4 live/8 total.
Uncapped-health research duels prove base Red can defeat Spore, Red kit can
defeat Maw/Ballast, and Black base can defeat Ballast. Healing fixtures do not
prove encounter difficulty. Final publication/agent gates live in TASKS/CHANGES;
player fun remains unconfirmed. D's production mixed fight selects the authored
leap prep/leap naturally (GMB IDs traced), with all three species concurrently;
native AI remains the framework, rather than a newly implemented AI system.

**Player correction, 2026-10-16:**0.18.0 was rejected: animations still felt
familiar, voices were shared, kills lacked readable death/reward feedback, rooms
felt empty, and signs/maps/materials looked cluttered and coarse. Treat creature
identity as the entire lifecycle: silhouette, locomotion, attacks, reactions,
death tint, sound and physical rewards. Quiet environments and short map goals
are explicit preferences; keep detailed route help on Objectives. Sustain
encounters on saved revisits and near upper entrances while preserving safe save
and cache rooms.0.19.0 implements154 authored routes,15 original voices, native
XP/HP drops, revised patrols and restrained harbor art. Native AI/rigs remain;
agent evidence lives in CHANGES/TECHNICAL. Player acceptance is still required.

The central idea: **enter beneath an enormous cargo crane, explore the docks
and its machinery, then reach the arm that dominated the skyline at arrival**.
Twelve rooms give it two connected exploration loops, a quiet native checkpoint,
an optional maintenance discovery and a victory return. The large spaces target
360..420 units wide, roughly six/seven camera widths; the tallest shaft targets
224 units, about five view heights. These are authored-space goals, not filled
rectangles. Vary architecture, levels, safe landings, camera framing and combat
pockets. A 45–60 minute exploratory first visit is a pacing target, unmeasured.

| Room | Job in the district | Approximate bounds |
|---|---|---|
| Quayside | Open-water arrival; show the giant crane and let the player read the route | 360x96 |
| Freight Exchange | Recognizable central yard: dock floor, container roofs and overhead rails; strong crew | 400x176 |
| Harbor Office | Quiet save/shop checkpoint off the hub, overlooking the docks | 112x64 |
| Container Warren | Interlocking cargo alleys and roofs, recoverable falls and optional routes | 380x160 |
| The Dry Dock | Grounded ship hull, service platforms and a durable crew beneath the yard | 400x144 |
| Engine House | Winch/machinery interior; restore cargo power and open the lower loop's return | 280x144 |
| Counterweight Shaft | Tall climb through crane supports, hanging loads and recovery landings | 176x224 |
| Gantry Spine | Long exposed upper traverse; broad combat pockets and a view of previous routes | 420x112 |
| Winch Cache | Optional maintenance branch with an exploration reward proposal | 160x96 |
| Crane Crown | Upper crew encounter, panorama, final-arm reveal and return descent | 336x176 |
| The Long Arm | Approach along the crane arm into the hoist-machine finale | 420x144 |
| Breakwater | Victory opens a lower waterfront return with one last discovery opportunity | 320x96 |

**Connections.** Entry -> Quayside -> Freight Exchange -> Container Warren ->
Dry Dock -> Engine House -> Counterweight -> Gantry -> Crown -> Long Arm.
Office branches from Freight; Cache branches from Engine. Engine opens a direct
route back to Freight; Crown opens a descent to Engine. Victory opens Long Arm
-> Breakwater -> Quayside. This is schematic topology: actual doors must join
appropriate sides/heights with walkable arrivals and explicit unlock conditions.
No required story bypass, unowned Slam or paid kit move. Main landings support
Red/Black and existing native jump/swing/wall movement; paid moves enrich fights.

**Memorable moments.** The opening crane silhouette becomes a navigable
landmark. The central yard offers three actual paths at different heights.
The ship hull changes the shape/scale of the lower route. Counterweights form
the vertical set piece; moving loads need a native animation/collision prototype
before being promised. Gantry views reveal the recognizable lower landmarks.
Opening the two returns makes the district quicker to revisit. Place native
checkpoint access before the long ascent/finale; avoid repeated mandatory crews
once their persistent clear conditions are met.

**The Long Arm boss pitch.** A huge cargo grabber/hoist machine attacks while
Spidey closes on one clearly visible winch/motor target. Proposed attacks:
track then visibly commit to a marked hook slam, a warned lateral sweep with a
clear jump/evade route, and an exposed recovery window for real combos. Bound
crew pressure and keep attacks local to visible camera space. The room's long
approach is not permission for unseen room-wide hits. This is a prototype gate:
prove native melee HP loss, recovery/protection, movement/collision, death
callback, cleanup and Red/Black viability before the final art/encounter. Keep
the native animated hit binding after the v0.15.1 core-rendering lesson. No new
character AI, moving hook or playable boss is claimed yet.

**Presentation.** Steel silhouettes, a grounded vessel, open sky, warm dock
lights and cooler distant water/city layers. Use three depth layers where
useful, visible supports, readable undersides and clear platform edges. Keep
foreground beams away from Spidey's silhouette. Texture/scenery work should
support the shipyard's distinct architecture and landmark progression. Water
appearance, any animated machinery and custom painted surfaces need real game
captures. Every room still needs a meaningful route or encounter, not empty
distance added to meet a size target.

**The Grid absorbs the old Lost Lab idea.** Use office walls, rails, computers
and authored machinery instead of tinted debug boxes or another subway.
Cable Well introduces safe maintenance pockets beside warned electrical lanes;
Lost Lab puts a strong crew on an open floor with observation ledges. One
branch-private power change opens Switchback and changes the safe approach to
its machinery. A protected machine with an exposed attack window is a proposed
encounter, not proven AI or a character boss. Keep routing quick and physical,
not a list of switches to collect.

**Skyline Run is exploration first.** The normal route always remains usable
and reversible. A timed replay can follow only after traversal works and native
timer survival/reset across rooms, death and exits are measured. No slow-motion.
Use strong crews on wide landings; narrow ledges are traversal space. A mobile
pursuit finale remains research because enemy AI and cross-room pursuit are
unproven. Preserve Map09's ichor wall, sewer grate and Downtown connection;
never require the unowned Sledgehammer Slam or a paid Red move to return.

**Hive: Quarantine Heart is later.** Keep the earlier post-story restriction:
an organic growth chamber and containment perimeter outside the native Hive,
not more Nest corridors. No room IDs, flags or spoiler art are committed.
The native-story completion gate and additional safe flag allocation must be
proven first. Sewer already has Midnight Line as its new section.

Each branch has a nearby native checkpoint, strong bounded crews, readable
maps and a completion/return route. Normal enemy XP is established; any special
one-time reward needs its own grant/save test. Do not tie these places to new
skills or unchosen stat rows. Midnight Express remains a later connection idea:
first prove direct district entrances without bypassing story gates.

**Revised budget:** Crane Row alone targets rooms96..107. Proposed visits use
161..152 then149/148, with seven progress/reward/crew flags140..146. Nineteen
of the current 21 audited free flags are used on paper; 147/245 remain. The
live allocator still rejects room106: an explicit visited map must preserve
all released assignments before these two extra rooms can exist. A dry packing
trial over v0.15.1 fits twelve placeholders in an8-KiB table with2,720 bytes
before adapters; final dialogue, maps, names and runtime headroom remain gates.
These are unallocated proposals. Grid/Skyline retain their designs but no
reserved IDs; future districts need another flag audit/storage plan.

The old three-room map sketch must grow too. Test a readable Pier overview
branch and individual detailed maps. A separate local Crane overview is an
option only after proving how it coexists with native parent/world views;
no seventh area slot is assumed. An unreadable miniature diagram is not a
successful twelve-room map.

The shared expansion, Pier entrance, local/detail maps, twelve authored rooms
and warned hoist are implemented. Next: iterate this district from player
feedback before starting another branch. The counterweight remains moving
scenery above fixed landings; rideable loads and timed pursuit remain research.

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
