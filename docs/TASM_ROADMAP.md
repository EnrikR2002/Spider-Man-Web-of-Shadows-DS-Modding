# TASM: never stand still

Current design and player feedback, reviewed 2026-10-23 (America/Edmonton).
[TASKS](TASKS.md) owns the live build and next action; [CHANGES](CHANGES.md)
owns shipped behavior; [TECHNICAL](TECHNICAL.md) owns engine evidence and
unknowns. Build and review procedures are in [DEVELOPMENT](DEVELOPMENT.md).

## Current direction and acceptance

Keep one combined TASM1/2 Red kit: fast, acrobatic, spider-like combat against
strong and web-resistant enemies. The loop is **strike -> cancel with R ->
reposition -> resume**. Native A/B/base strings/evade, purchases, dependencies,
Both Suits traversal, story gates and earned rewards remain the foundation.
Overclock, Dragnet and Vortex are the final added Red skills. Fun and spectacle
lead. The 2026-10-22 request activates the selected 2099 Black-slot rework,
appearance first. The 2026-10-23 request replaces its combat proposal with the
film-faithful Hunter design below (not implemented). Prices, third suits and
campaign expansion remain deferred.

The current release is **v0.31.0**. Vortex is now a cocoon-only tethered
catapult/slam, the Conductor has a larger symbiote war-machine body and one boss
meter, and low-HP Vitality damage is corrected. The player's liked boss combat
programs remain. Cape-free Across the Spider-Verse 2099 and the compact Terminal
atlas remain. Native purchases, traversal and chapter progression stay intact.
Agent qualification does not establish player feel/appearance acceptance or
actual DeSmuME pacing.

| Player evidence | Decision that still matters | Later implementation / limit |
|---|---|---|
| 2026-10-23: make Black play and fight as close as possible to Across the Spider-Verse's Miguel O'Hara; make it fun to play | Replace the comic-style juggle proposal with a grappling pursuer (hunt -> seize -> punish -> hurl) on the exact native A foundation. | Design only, below. The first slice is Pin & Pound after the listed engineering gates; no player verdict exists until a slice ships. |
| 2026-10-22: Vortex is boring; keep it conditional on regular-web/Dragnet cocoons. Boss fights well but needs larger symbiote metal war-machine anatomy, one boss bar, and a low-HP damage fix. | Rework Vortex inside its existing paid row; preserve liked boss combat; separate a shared Vitality clamp defect from boss behavior. | v0.31.0 ships the tether catapult/slam, larger articulated armor, boss-only texture and raw-damage fix; native boss timings/AI remain. Agent qualification is in TASKS; player feel/appearance acceptance remains open. |
| v0.30.2 Terminal enemies were white while the 2099 player rendered | Restore the custom enemy texture bindings in the crowded scene while retaining artwork and geometry. | v0.30.3 I4 atlas binds all three observed enemy materials. One qualified scene, not all-room or player-acceptance evidence. |
| v0.30.1 appearance liked overall; latest supplied Across the Spider-Verse image; remove the red web cape | Use the movie's navy/red mask, angular chest spider and shoulder panels; remove cape geometry rather than hiding it. | v0.30.2 implements and agent-tests this appearance. Player visual acceptance is still open. At v0.30.2, Terminal enemies remained unbound; v0.30.3 resolves the sampled crowd. |
| v0.30 appearance is a good start, but cape and forearm blades look bad; correct placement and add Spider-Verse-like muscle | Prioritize the web cape, surface-mounted blades and a stronger upper-body silhouette before combat implementation. | 0.30.1 E ships actual shared-mesh selection, a larger crimson web and balanced muscle volume; the player's new visual verdict is open. |
| Early kit play, v0.2-v0.4 | Keep responsive cancels, continuous movement and crowd play. Snap Sweep and original Web Vault are player-confirmed. | Later revisions require their own feel verdict; early praise does not approve every subsequent move. |
| v0.23 rejection, 2026-10-18 | Unconvincing hits, slow/odd animation and recognizable voices were unacceptable; room shapes were repetitive. | v0.24 repaired contact, lifecycle/audio scope and actual room envelopes. |
| v0.24 replay, 2026-10-18 | Preserve the improved environment and more distinctive enemy direction. Rigid motion, poor SFX and the slow/easy boss were rejected. | v0.25-v0.27 change motion, sound and anatomy; final enemy quality remains unconfirmed. |
| v0.25 replay, 2026-10-18 | The boss still lacked effective pressure responses; monsters seemed silent. | v0.26 adds physical responses and paired in-game audio evidence. Playback evidence does not establish sound quality. |
| v0.26 replay, 2026-10-19 | Harder/cooler mobility was welcome; blanket stagger suppression prevented combos and frustrated the player. | v0.27 restores ordinary hurt openings and limits protected commitment. |
| v0.27 replay, 2026-10-19; latest feedback | Combos are only slightly better; the boss is too easy, appears idle or misses, and the ramp is not felt. Remove two save rooms and fix the upper map order. | v0.28 addresses these requests. No v0.28 player verdict is recorded. |

Crane Row's earlier creature/presentation rejections also remain relevant.
Published fixes to rewards, voices, routes and the hoist do not establish that
its final enemies, encounter rhythm or finale are player-approved.

## Current player kit

The seven original Red slots retain ownership and native input gates. This is
the implemented kit's role map; it does not promise every interaction in an old
design draft. Unowned/native behavior and Black ownership remain protected.

| Native slot | Current move | Input / purpose |
|---|---|---|
| Web Kick | Leapfrog | Y during grapple; cross-up vault/kick. |
| Web Launch | Skyjack | Up during grapple; rise, aerial pressure and spike. |
| Mid-Air Snare | Spider Perch | Air A toward enemy; perched attacks, hop/spring exits. |
| Spider Dance | Split Decision | Y, pause, Y sequence; crowd-facing string. |
| Scissor-Kick Special | Spin Cycle | Split Decision extension/repeated Y; steerable spinning pressure. |
| Amazing Speed Boost | Spider Reflex | R during Red attacks; cancel, reposition and resume. |
| Ultimate Speed Boost | Spider-Sense | Timed R against supported threats; reversal with Reflex dependency. |

Additional shipped Red purchases are Web Rush, Ricochet, Momentum, Overclock,
Dragnet and Vortex. Both Suits Vitality I-III already exist. Preserve these rows,
their ownership and refund rules; they are not a queue for more skills or stats.
The current move/price catalog is [suit metadata](../reference/suit_roadmap.json)
and [upgrade metadata](../reference/tasm_upgrade_plan.json). Prices are retained,
with balance tuning deferred.

The v0.15.1 seven-contact Vortex was rejected as boring on2026-10-22. Its
replacement uses Down+Y with an actually webbed nearby enemy (regular A or
Dragnet), then one continuous tethered catapult and floor slam; R can cancel.
Keep the same paid Red row and the original A/B/base strings/evade. Current
candidate qualification is in TASKS; its new feel needs a player verdict.

## Recommended build order

The three Vortex/boss/health fixes requested on2026-10-22 take priority. The
2099 Hunter combat design waits for the player's go-ahead and its first-slice gates.
The chapter reviews below remain player gates when campaign iteration resumes.

The three requested follow-ups now ship in v0.29. Use its published route as
the comparison baseline; further changes need a new version.

| Delivered follow-up | Agent evidence | Remaining player question |
|---|---|---|
| Skyjack native movement | Open contacts, both walls, R exits and all 68 kit checks pass. Native/Black and unowned controls retained. | Does the corrected drift retain the desired aerial reach and responsiveness? |
| One complete Rail Skitter | Private mesh, full lifecycle motion and eight cues; all three attacks hit, native death rewards and current-owned mixed Terminal clear pass. | Does it feel fluid, distinct and satisfying at normal speed in the actual mix? |
| Ballast/Long Arm finish | Parent Freight ceiling loop reproduced; edge-clear/return works on two roofs. Red/Black wins/save/Continue and visible hoist states pass. | Are vertical pressure, warning readability, openings and the finale satisfying? |

### 1. Establish the v0.29 full-route verdict

Replay with actual purchases and ordinary native damage. Check whether the
Conductor lands fair attacks, accepts meaningful combos, counters sustained
pressure and leaves readable recovery. Compare Terminal, Floodworks, Turbine
Rise and Observatory for a felt rise in pressure, with quiet travel and safe
arrivals between fights. Check map order, the return loop, retry travel and earned
save/Continue. Assess Skitter's whole body and tell/contact/hurt/death cues at
native scale and normal speed; numerical audio playback evidence is insufficient
to decide quality. These are player verdicts, separate from lab fixtures.

Midnight has eight active rooms. Signal House/Pump Refuge remain retired; Relay
Sanctuary is the main-route save room. Keep the environment/direction the player
accepted. The final skills remain Overclock, Dragnet and Vortex.

### 2. Refine encounter decisions from the replay

The reliable counter carrier, bounded guard response, ordinary combo openings
and late-room ramp already ship. Target observed unfair overlap, idle gaps, weak
pursuit or repetitive pressure. Teach roles before combining them and retain
reachable combat landings. Prefer purposeful staging and decisions over raising
every room's HP/crowd count. Retain native boss damage/death, health meter and
saved shutdown. Keep protected commitment bounded and recovery punishable.

### 3. Review Crane's complete vertical route and payoff

Crane already has twelve rooms, two exploration loops, maps, saved power and
shortcuts, original enemies/rewards, a hoist finale and an approach checkpoint.
v0.29 corrects the reproduced Ballast overhead case and improves the hoist's
warning/guard/open/wreck presentation. Review actual traversal through the whole
route before deciding whether upper roofs need further navigation work or the
finale needs pacing changes. Two tested roofs do not prove every pursuit path.
Keep quiet checkpoints/cache, restrained harbor art, short map goals and detailed
Objectives. Moving counterweights remain scenery above fixed landings.

### 4. Extend creature presentation only after the example works

If the player accepts Skitter's normal-speed motion, silhouette and mixed audio,
apply the proven authoring approach to Warden, Eye and Conductor one at a time.
Each needs distinct patterns/voice plus complete hurt, knockdown/get-up and death.
If Skitter still fails the standard, refine it first. Pose sheets, sample counts
and clearability alone do not authorize another roster-wide pass.

## Acceptance for a future candidate

- Gameplay: native movement/collision, fair contacts, meaningful combos/R exits,
  baseline Red/Black viability and complete enemy lifecycles in mixed terrain.
- Presentation: review native-scale normal-speed footage and mixed audio before
  expanding the example. Clearability and sample counts do not decide fun.
- Persistence: preserve purchases, dependencies, rewards, story abilities and
  earned clears; test retries and fresh Continue using copied latest batteries.
- Composition: prove changed-byte scope, real-input doors for changed rooms and
  appropriate broad controls on one stable final candidate, then publish a new
  version through the guarded workflow.
- Player confirmation: record the actual verdict separately. Full-route fun,
  final creature quality and DeSmuME frame pacing remain open until observed.

## Spider-Man 2099: Black-slot rework

**Appearance (published).** v0.30.3 keeps the guarded shared-model selector and
native Red list, with Black wearing the cape-free navy/red Across the
Spider-Verse look requested on 2026-10-22 (movie reference supplied, red web cape
removed; the player liked the prior 2099 overall). Its model and native motion
are unchanged from v0.30.2. The same release compacts the shared Midnight enemy
atlas to 8 KiB I4, which binds the sampled Terminal crowd. One mixed scene is not
all-room residency, player visual acceptance or DeSmuME pacing. Details are in
`reference/spider2099_movie.json` and `reference/spider2099_enemy_texture.json`.

### Combat: the Hunter (design, 2026-10-23)

On 2026-10-23 the player asked for Black to play and fight as close as possible
to Miguel O'Hara in *Across the Spider-Verse*, and to be fun enough to make them
want to play it. This **replaces** the 2026-10-22 "catch -> carry -> crash ->
chase" proposal. Nothing below is implemented, agent-tested or player-confirmed.

**What the film shows.** Miguel is not an acrobat. He is big, serious and
relentless: he leads the whole Spider Society after Miles, runs him down across
Nueva York and ends the chase by pinning Miles to the roof of a speeding train.
He is reportedly animated on ones,
the smoothest motion in the film, so his weight comes from fluid anticipation
and follow-through rather than stiffness
([film](https://en.wikipedia.org/wiki/Spider-Man:_Across_the_Spider-Verse),
[chase](https://intothespiderverse.fandom.com/wiki/Hunt_for_Miles_Morales)).

**Identity: Red never stands still; 2099 never lets go.** Red slips around a
crowd and resumes. 2099 picks one target, closes the gap, seizes it and turns
its body into a weapon against the rest. The loop is
**hunt -> seize -> punish -> hurl -> hunt**.

- Each move is a different physical verb: pounce, tackle, throw, dive, rake,
  pin, chain. No move is "another rake with a talon trail".
- Power reads through mass: a low coiled crouch, shoulder-first contact, carried
  bodies, floor impacts and enemies flying into other enemies. No freezes, slow
  motion or player teleports.
- Holding a target is the risk. While Miguel pins or hoists, the others can hit
  him (native hurt interrupts). Choosing when to pin and when to throw is the skill.
- R always lets go and evades natively. 2099 does not borrow Red's
  combo-keeping Reflex; his continuity comes from Relentless (below).

**Native foundation stays exact.** Ground A Power Dash is the tackle, air A
Hammer Spike the dive, air Down+A Hammer Slam the crash. Their inputs, movement,
barrier/floor story use, B, base Y strings, unowned R and shared upgrades stay
native and never need a target or charge. Purchases change what happens **on
enemy contact** and add follow-ups. Unowned rows keep native behavior; no
ownership moves, and native dependencies remain (Widowmaker before Pin & Pound,
Super Charge before Relentless).

| Native purchase (bit) | 2099 move | Input | Ordinary enemies | Bosses and resistant enemies |
|---|---|---|---|---|
| Webbed Fury (20) | **Rundown** | A again after a Power Dash hit; up to two more links | Each link is a real dash at the tumbling target or the next enemy ahead; the last drives its target into the floor. Pinball through a crowd. | Shoulder check that stops on contact; the boss never moves. |
| Power Launch (21) | **Collar Toss** | Grounded Up+A | Seize the nearest enemy in front, hoist it overhead and throw it along the held direction: forward bowls it through the crowd, back turns and hurls it behind, Down slams it at Miguel's feet into a pin. | Two-hand overhead hammer strike. |
| Ground Rebound (22) | **Freefall** | Native Down+A slam | Head-first, talons-first dive. Impact strength and radius grow with drop height up to a cap. Bystanders keep the native bounce; the enemy under Miguel stays down for Pin & Pound. | Height-scaled direct damage; no bounce. |
| Black Widowmaker (23) | **Talon Line** | Y,Y,Y, pause, Y,Y | Three slashes that walk Miguel through his target, then a hook: the talons catch it and drag it across his body, flinging it behind him. Back hooks the enemy behind instead. | Two close slashes; no drag. |
| Poison Pummel (24) | **Pin & Pound** | Y,Y,Y, pause, repeated Y | The signature. Miguel bears the enemy down, plants a knee and talons, and hammers once per Y up to a cap. Direction+Y or the cap ends it with a throw that way; R lets go. | Talon cling: close rakes per Y without moving the boss; R exits. |
| Super Charge (25) | **Talon Pounce** | Hold Y, release | Miguel coils low; release fires a long flat leap, talons first, at the enemy ahead (range grows with the coil, capped). A hit tackles and lands on it: Pin & Pound if owned, otherwise a knockdown. | Pounce strike only. |
| Quick Charge (26) | **Relentless** | Passive | Halves the coil. Y can be held through any 2099 finisher (Rundown's last link, Collar Toss, Freefall, Talon Line's hook, Pin's throw), so Pounce fires the instant it ends and the hunt never resets. One stored pounce; hurt or R clears it. | Same. |

**Routes this should make possible** (purchases and nearby targets required):

- **Nueva York chase:** Pounce the nearest -> Pin & Pound -> throw into the pair
  behind -> held-Y pounce onto the one getting up -> Talon Line hook -> Rundown
  through the rest.
- **Bowling:** Collar Toss into a group -> Power Dash Rundown through the falling
  bodies -> wall climb -> Freefall onto the pile.
- **Dive bomb:** climb a Hive shaft or Crane roof -> Freefall from the ceiling ->
  Pin & Pound the enemy left under him -> throw.
- **Tag team:** Red cocoons a group with web or Dragnet -> L -> Collar Toss a
  cocoon into the rest. Needs a cocoon-throw lab; Vortex stays Red-only.
- **Boss:** Pounce strike -> Talon Line slashes -> R out of a telegraph -> climb
  -> high Freefall -> Pounce back in. No forced boss movement, permanent stun or
  invented armor breaks.

**Starting feel targets** (tuning starts here; the player's verdict decides):
Pounce crosses about 25 units in under half a second and never passes a wall; a
pin lasts only while Y keeps coming, capped near six pounds; a thrown body
knocks down each enemy it meets once and lands where the D-pad pointed;
Freefall adds nothing below a held jump's height.

**Presentation.** Author every clip with continuous curves at full sample
density, heavy anticipation, shoulder- or talon-led contacts and overlap; no
per-key holds. Poses: a low wide crouch, splayed talons, a body stretched through
the pounce, a head-first dive and a knee-and-talon pin. Optional cue: a brief red
talon/eye accent while Relentless holds a pounce, if the palette path allows.
Use native impact audio; do not rename stock punches as new moves.

**Engineering gates before the first slice:**

1. **Space:** the 32 KiB kit stays exact for Red. 2099 needs its own guarded
   code/state block, as v0.31's autoload page did. That is a deliberate contract
   change; measure headroom first.
2. **Black-only resources:** list the actions/SCA/GMB used by Black string nodes
   5..10, dash, slam, Widowmaker, Pummel and charge. Re-author only Black-only
   ones: GroundAttack15 is shared and G11/16/17 have m6.xbd users.
3. **Hooks:** map dash contact, slam contact, the bit-23 late branch and the
   native hold-Y charge state in the lab. Whether a charge can start from
   idle/run is open; if not, Pounce starts from a held strike.
4. **Body control:** Vortex already steers enemy bodies with bounded native
   velocity and native hit kinds (knockdown 0x1F, far throw 0x24, launch 0x25,
   floor drag 0x26), and a floor hit on a lying enemy re-bounces it. Prove one
   pinned-then-thrown enemy, its boss fallback and its R exit first.

**Build order:** one complete slice at a time, each with a player verdict
before the next.

1. **Pin & Pound** with its throw, boss cling and R exit: the film's signature
   moment and the body-control backend every other move reuses.
2. **Freefall:** the cheapest spectacle; it turns vertical rooms into dive-bomb
   arenas.
3. **Talon Pounce + Relentless:** the glue that keeps the hunt continuous.
4. **Collar Toss + Rundown:** crowd bowling.
5. **Talon Line:** last, because it replaces the most animation.

**From the superseded pitch:** kept native A parity, no forced boss movement, R
exits, a single stored charge, the wall-pounce idea (now a later Pounce variant)
and the crimson cue (now Relentless's cue). Dropped the aerial juggle routes
(Talon Lift, manual-B follow, rebound catch), per-move charged variants and
Raking Cross as the first prototype: they read as comic or Red-style juggling,
not the film's grappling pursuer. The full dated pitch stays in the archive
under this document's 2099 heading.

## Deferred work

| Idea | Current boundary |
|---|---|
| More Red skills, extra stat rows, prices/balance, shop/save expansion | Deferred. Iterate the existing kit; Overclock/Dragnet/Vortex are the final added skills. |
| Spider-Man 2099 combat | The Hunter design above replaces the 2026-10-22 proposal; nothing is built until the player approves the Pin & Pound slice. Preserve native A traversal, paid ownership and shared upgrades. |
| Third suit and other suit concepts | Deferred; TASM1/2 share one kit. No suit selector or migration is implemented by this roadmap. |
| Downtown Grid/Lost Lab, Residential Skyline Run, Hive Quarantine Heart | Deferred concepts. No new allocations are authorized by the old pitches; audit current flags/storage before any future expansion. Hive stays post-story. |
| Midnight Express, gauntlets, timed replays, collectibles/reward systems | Backlog ideas, not unfinished work required for the current chapters. |
| Moving trains, rideable loads, changing solid platforms | Need a complete native collision/ownership prototype before promising a set piece. |
| Cross-room timers/pursuit and broader music routing | Need lifecycle/channel-budget evidence. Existing timers and audible cues do not prove these larger features. |

## Historical designs

The full pre-cleanup roadmap and three planning catalogs are preserved byte for
byte in the existing verified archive, snapshot 2026-10-21. They retain detailed
early kit fantasies, rejected moves, Signal Leech/Crane construction pitches,
old allocation estimates and the seven-skill 2099 theorycraft (superseded on
2026-10-23 by the Hunter design). They are historical
context, not a second active plan. Later implementations and player decisions
above supersede their original next/proposed wording.

```powershell
python tools/doc_archive.py list roadmap
python tools/doc_archive.py read docs/TASM_ROADMAP.md --toc
python tools/doc_archive.py read docs/TASM_ROADMAP.md --section 'Spider-Man 2099'
python tools/doc_archive.py read reference/tasm_upgrade_plan.json --lines 40
```

Shipped release history stays in CHANGES; format/engine discoveries stay in
TECHNICAL. Neither belongs in a new session or release Markdown file.
