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
lead. Hunter's Return and Talon Lift are the two implemented 2099 skills.
The latest 2026-10-23 request develops the full 2099 kit, specifically real air
combo routes and a physical block/counter or hit-retaliation mechanic. This is
design work; it does not select a new move for implementation. The remaining five Black moves,
prices, third suits and campaign expansion remain deferred.

The current appearance release is **v0.33.1**, over v0.33.0:
12.5% taller 2099 with scarlet native web tints. Hunter's Return's hit isolation
and owner cleanup, Talon Lift and the fuller cape-free body remain. Appearance
and move feel await the player's verdict. TASKS owns publication status.
The inherited Vortex is a cocoon-only tethered
catapult/slam, the Conductor has a larger symbiote war-machine body and one boss
meter, and low-HP Vitality damage is corrected. The player's liked boss combat
programs remain. Cape-free Across the Spider-Verse 2099 and the compact Terminal
atlas remain. Native purchases, traversal and chapter progression stay intact.
Agent qualification does not establish player feel/appearance acceptance or
actual DeSmuME pacing.

| Player evidence | Decision that still matters | Later implementation / limit |
|---|---|---|
| 2026-10-23: flesh out the full 2099 kit, add air combos, and explore blocking or instantly countering an attack | Make ground-to-air play central; develop a planted contact counter that supports Miguel's scrapper identity. | Expanded working proposal below. Timed guard with an automatic answer is the recommended default; damage-taking reprisal remains an alternative. No new mechanic is implemented or player-tested. |
| 2026-10-23: make 2099 taller, make his webs neon red like Across the Spider-Verse, then research/reassess his abilities | Apply the appearance change; ground the existing proposals in the film's pursuit, catches and surface pressure. | v0.33.1 ships render height and web tints. The film reassessment below is a recommendation; no extra move or mechanic is activated. |
| 2026-10-23: implement the next 2099 skill | Talon Lift retains the native Power Launch purchase and manual B follow-up. | v0.33.0 ships the authored rake and R exit; actual air hits require holding B. Player feel verdict remains open. |
| 2026-10-23: approve both Hunter's Return review fixes | Isolate shared victim records and clear a departed player's move when the actor is replaced. Preserve the approved skill/model scope. | v0.32.1 corrects both with ARM regressions and labelled native controls. The artwork and private motion remain exact; player feel verdict remains open. |
| 2026-10-23: add the first 2099 skill and make his model a bit more muscular like Spider-Verse | Implement Hunter's Return in the existing Webbed Fury purchase and broaden the current mesh. Keep other Black proposals deferred. | v0.32.0 implements and agent-tests the move and fuller physique. Player feel/appearance verdict remains open. |
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

Review the taller 2099/web appearance and both shipped moves first. The earlier
Vortex/boss/health fixes ship in v0.31 and retain their pending player verdicts.
The remaining five Black proposals stay deferred. The air/counter design request
supersedes the prior Cross-first recommendation: if implementation is requested,
first qualify one planted guard/riposte against one ordinary melee attack, then
Raking Cross and one advanced air route. Neither the new defense nor the whole
kit is an active implementation queue.
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

The player's 2026-10-22 appearance request supplies an Across the Spider-Verse
reference and explicitly removes the red web cape. They like the prior 2099
overall. This supersedes the earlier classic foundation/larger-cape direction.
The first 2026-10-23 request selects Hunter's Return and a more muscular body.
The next-skill request activates Talon Lift; the remaining five moves stay proposals.
The appearance request adds height/neon red webs and a film-based reassessment.
The subsequent request explicitly asks for a deeper kit, air combos and a
block/contact counter or instant retaliation after being attacked.
The previous section, including the earlier move roles, is retained byte for byte
in the verified archive as `docs/TASM_ROADMAP_2099_PRE_FILM_2026-10-23.md`.

Published v0.30.3 keeps the guarded shared-model selector and native Red list,
with Black wearing the requested cape-free navy/red movie-inspired appearance.
That appearance is the foundation for v0.32's fuller chest/arms and two private
Hunter motion clips; other native clips remain. The v0.30.3 release
also changes the shared Midnight enemy atlas from 32 KiB direct color to 8 KiB I4.
Three live enemy materials bind in the crowded Terminal capture, while the hero
retains I8. One mixed scene establishes that scene's texture binding, not
all-room residency, player visual acceptance or DeSmuME pacing. Both releases
retain native controls, ownership/progression and previous chapter work. Details
and scope are in `reference/spider2099_enemy_texture.json` and
`reference/spider2099_movie.json`.


**Hunter's Return is implemented in v0.32.0 and corrected in v0.32.1.** Its existing
Webbed Fury 100 XP purchase remains; release A after the dash hit, then tap A for
native eligible recall and a rising rake. Native-unrecallable targets receive
a short physical attempt. R cancels, and B remains manual. The fuller model
keeps the current atlas, rig and 516 triangles. Player feel/appearance remain
open; scoped evidence is in `reference/hunters_return.json`.

**Talon Lift is published in v0.33.0** through the guarded publisher.
It retains Power Launch's native 200 XP purchase, event 330 / bit 21 and ownership.
Up+A coils low into an authored rising rake while staying grounded. Hold B for
the native full jump, then Y to catch the launch with real air hits; R cancels.
Native movement, collision, damage and launch resistance stay. No B bypass,
automatic follow-up, new target state or save migration is needed. Agent tests
pass in both directions; player feel/appearance acceptance remains open.

**v0.33.1 appearance release:** the whole animated Black pose is 12.5% taller,
with its feet anchored and the fuller body/cape-free artwork retained. Native
web lines and web-effect tints become bright scarlet. Red retains its height
and original web tints. Collision, attacks, purchases and save progress remain
native; this appearance request does not authorize combat changes.

### Across the Spider-Verse reassessment - 2026-10-23

The screenplay supplies two useful references: the museum's hardlight arm
lasso and exposed fangs, then the train chase's claw grip, waist reel and forceful
surface pin. The train's crane kick belongs to Miles. These support a kit built
around closing distance and controlling contact. See the authors' [screenplay,
printed pp.12-17 and130-133](https://assets.scriptslug.com/live/pdf/scripts/spider-man-across-the-spider-verse-2023.pdf?v=1729114995).

Supervising animator Daniel Pozo describes research into an intimidating, large
physique using bodybuilder references. That supports the stronger silhouette;
it does not prescribe slow inputs. [Pozo's interview](https://www.abc.net.au/news/2023-06-10/spider-man-across-the-spider-verse-animation/102463650).

The practical film vocabulary is strength, explosive agility, gripping claws,
fangs and bright hardlight tethers. The wrist portal system is equipment, not
permission for a teleport attack. Marvel explicitly gives **comics** Miguel
paralyzing fang venom; the film evidence here does not establish its gameplay
duration, repeatable poison damage or a healing mechanic. Keep those outside
the move plan. Avoid claiming a precognitive counter from these scenes.
[Marvel's character profile](https://www.marvel.com/characters/spider-man-2099-miguel-o-hara).

**Design inference:** make him a powerful, acrobatic pursuer: low coil, rapid
diagonal entry, committed body contact and a weighted recovery that R can exit.
Use claws to show grip and red tethers to show tension. Extended pirouettes,
repeated floaty relaunches and a long stationary charging pose would weaken that
identity. This is an interpretation for a playable DS kit, not a claim that the
film supplies these named moves or a particular martial-art system.

### Full kit, air routes and physical counters - 2026-10-23 working proposal

The player correctly identifies the prior proposal's missing air detail. The
new identity is **meet the attack -> take control -> launch or drive -> air
pressure -> decisive landing -> re-engage**. Ground pressure remains useful
against resistant enemies. Fast entries, a stable center of mass, short claw
strings and visible impact/recovery give Miguel weight without slowing inputs.
This is a gameplay interpretation, not a claim that the film contains these
named moves or a formal guard system.

Only Hunter's Return and Talon Lift are implemented. Every extra input, animation
branch, defensive rule and timing below is a proposal. Keep seven Black shop
slots, their current prices, native ownership/dependencies and refunds. Fold
the proposed basic guard into the early Hunter's Return purchase, without an
eighth row, new save bit or borrowing a Red skill. Existing owned Return saves
would unlock it naturally in a future release; unowned behavior remains native.
The earlier film-only draft is preserved in the verified archive as
`docs/TASM_ROADMAP_2099_BEFORE_AIR_COUNTER_2026-10-23.md`.

| Native Black purchase | Move / status | Proposed complete role |
|---|---|---|
| Webbed Fury | Hunter's Return (existing move; guard extension proposed) | Ground A still dashes; release/tap A after contact recalls an eligible victim or makes the current physical pursuit attempt. Add the planted Talon Guard below through this same purchase. This gives the early kit both an entry and a way to answer pressure. |
| Power Launch | Talon Lift (implemented) | Up+A coils into the rising rake while Miguel stays grounded. Hold B to jump manually, then start air Y. A counter or Cross gives a deliberate opportunity to choose Lift; neither automatically launches the player. Resistant victims keep native reactions. |
| Ground Rebound | Predator Rebound (deferred) | Keep Down+A's native ground impact and traversal role. Eligible struck enemies bounce; after Miguel lands, choose a manual B chase or remain grounded and hit another enemy. Avoid automatic jumping and repeated floor-bounce loops. |
| Black Widowmaker | Raking Cross (deferred) | Preserve the late Y,Y,Y,pause,Y,Y purchase entry. A low rake rolls into a short shoulder/pounce drive and close turning exit, with hip/arm overlap. It may cross a small victim through actual movement; a resistant body or wall stops it normally. A hard wall pin is deferred until release/collision ownership is proven. |
| Poison Pummel | Talon Maul (deferred; replaces the Talon Cyclone working name) | Retain a compact purchased continuation of Cross on the ground. Its major new role is the optional two-hit air branch after two connected air Y hits: Up+Y rising rake, then Y close forearm/claw follow-through. Finish with native A or Down+A. No long spins, forced attachment, poison status or borrowed Red Snare ownership. |
| Super Charge | Predator Wind-Up (deferred) | Hold Y through pressure to load a distinct heavy claw/body drive. A low shoulder/hip coil visibly releases through contact; ordinary movement stays available. It can use the opening after a counter, but a block does not grant free full charge. A miss spends the committed attempt and has recovery. Damage/strength remain separately measured. |
| Quick Charge | Relentless Pursuit (deferred) | Retain faster charging, then allow one already-earned charge to survive one evade or manual jump. Forward+Y as the first air attack can spend it on a short forward body drive, followed by the remaining native Y string. The next committed attack, including a counter or miss, spends the charge. |

#### A complete air game

**Foundation:** preserve the native four-hit Y,Y,Y,Y air string and its
successful-contact chaining. The new kit adds choices around that foundation.
Talon Lift, the purchased shared Launching Uppercut, an eligible rebound and
ordinary jumps provide different ways to enter air pressure. Hold B after
Lift; short taps are not equivalent to the qualified full jump.

**Close air route:** Y,Y,Up+Y,Y selects Talon Maul when its purchase is owned
and the first two air contacts actually connected. The rising third rake and
compact fourth hit keep the opponent reachable for a short finishing choice.
The authored arms/body suggest a close catch; there is no teleport, hard
attachment or promise that a new native grab state already exists. A or Down+A
then chooses a single-victim spike or the ground-impact finish.

**Chase air route:** Forward+Y,Y,Y,Y selects Relentless Pursuit only as the
first air attack, with an already loaded carried charge and the relevant
purchases. Miguel spends it immediately on a brief forward forearm/body drive,
then actual contact permits the remaining native air hits. This closes the gap
before the string. Starting with a neutral attack or counter already spends
the bank and removes that chase option; there is no reserved charge surviving
two intervening attacks. If blocked by a wall or if the enemy escapes, he
misses and continues falling normally. Without a carried charge, the same Y
input falls back to the native air string.

The player chooses **one advanced air extension between landings**, vertical
Maul or charged forward Pursuit. No repeat relaunch, floating hold, second air
branch or wall-state reset extends it forever. Gravity and enemy resistance
remain active. A whiff cannot fabricate a contact to progress the branch.

**Finishes and exits stay readable:** air A is Hammer Spike; Down+A is Hammer
Slam/Predator Rebound. Down+Y remains the purchased Jackhammer Stomp, not a new
Maul shortcut. B against an air enemy remains purchased Enemy Kick-Off; a second
B in open air can become the native web swing, so it is not an unrestricted air
jump. Air R remains purchased Air Dodge. Ground Up+Y retains shared Launching
Uppercut. None of these shared abilities becomes free through a Black move.

#### Talon Guard and the automatic counter

**Recommended working version:** grounded **Up+R**, without horizontal steering,
enters a short, forward-facing brace when Hunter's Return is owned, from neutral
or a legitimate attack-cancel window. Horizontal steering plus R takes the native
evasion path. Ordinary R retains evade/cancel behavior, Down+R retains the native roll,
and holding R/steering retains purchased Enhanced Dodge. Air Up+R follows native
Air Dodge rules. Invalid states or unowned inputs fall back to native behavior.
The dedicated chord preserves existing movement contracts while we test the
physical defense. Do not quietly reassign ordinary R to guard.

Miguel sets his feet and raises his forearms/claws. Start with about **0.2 s**
for a clean counter timing and **0.6 s** maximum total brace, then tune against
actual logical updates. These are proposed targets, not calibrated timings.
There is no new stamina meter or permanent block stance.

- A real eligible frontal melee hit during the opening window is blocked without
  HP loss or native hurt, then Miguel automatically answers that attacker with
  one short elbow/body check into a claw rake. No Y is required to trigger it.
  The response starts promptly, but damage lands at its visible contact.
- A later ordinary frontal hit can consume the one-hit guard without giving the
  automatic answer. The brace ends with brief pushback/recovery. Holding the
  chord cannot refresh it; release and re-arm after recovery.
- The unit is one distinct incoming attack, not each collision part. Duplicate
  limbs from the same punch must not cause repeated blocks/counters or sneak
  the original blocked hit through. Another enemy or a later distinct strike
  can still interrupt. Counter-origin hits cannot recursively trigger counters.
- Rear attacks, grabs, projectiles, ground hazards and deliberately unguardable
  heavy attacks retain their normal danger. Heavy charges/overheads need a
  readable guard-break distinction before broad rollout. The first prototype
  supports one known ordinary melee attack, not an inferred whole roster.
- The counter stays close and uses the actual live source of the blocked hit.
  It can miss when that attacker moves away and can fail to stagger armor. It
  does not force launches, cross behind the target, grant broad invulnerability,
  clear the room, heal damage, resurrect Miguel or override a protected boss.

A successful counter gives a short grounded decision: Y into pressure/Cross,
owned Up+A into Lift and manual air play, a loaded Y heavy, or ordinary R to exit.
The real counter hit earns normal native combo credit; guard animation alone
does not manufacture damage, hits or combo gauge. The existing Red suit already
has an evasive reversal. Miguel's proposed version waits for actual contact,
holds his ground and answers it physically.

**Alternative if the player prefers taking the hit:** a committed Reprisal can
follow a real recoverable hurt event, using the existing paid Quick Recovery
opportunity and a deliberate R/guard input. The HP loss stays; the answer occurs
only when a valid recovery is permitted. Do not make it an always-on automatic
attack for every received hit, or a way to cancel death, grabs, heavy knockdown
and hazards. This is an alternative experiment, not another simultaneously
queued mechanic or extra purchase. Pending preference, timed guard/automatic
counter is the working recommendation.

#### How encounters would play

All routes below describe the proposed full kit with the named purchases;
they are not claims that v0.33.1 already accepts the new inputs. Inputs wait for
real contact/cancel windows, rather than being entered simultaneously.

| Situation | Route and decision |
|---|---|
| One susceptible enemy | Dash hit -> optional A Return -> Up+A Lift -> hold B -> Y,Y -> Up+Y,Y Maul -> A spike. Return and Lift remain independently chosen. |
| Enemy attacks first | Up+R timed brace -> automatic grounded counter -> Up+A -> hold B -> air Y string or owned Maul -> A/Down+A finish. Stay grounded with Y instead when air pressure is unsafe. |
| Enemy drifts out of reach | Load Wind-Up, carry it through the manual jump with Pursuit -> Forward+Y -> Y,Y,Y on contact -> spike or land. No charge or lost contact means the native string/miss, not a free chase. |
| A crowd gathers below | Launch one enemy -> manual jump and short air pressure -> Down+A into the group -> native eligible rebound -> choose manual B after landing or grounded Cross against another threat. |
| Armor or an immovable boss | Use short ground strings/Cross, guard only qualified ordinary swipes, land a physical counter when vulnerability permits, then R out. Heavy tells, ranged pressure and protected phases demand native evasion/positioning. No guaranteed air conversion. |

Counter, air branch and finish should each have readable anticipation, actual
contact and recovery, with continuous trajectories and overlapping body motion.
Do not add per-key pose resets, slow motion, teleport catches, new shop rows,
save expansion or forced player jumps to manufacture spectacle. Native A dash,
spike and slam still work for traversal without a target or charge.

#### Prototype order and unresolved engine work

If implementation is requested, prove **one planted guard plus one real riposte**
first: one enemy, both facings, correct/late/missed timing, rear/heavy controls,
one actual blocked HP event and one subsequent actual enemy HP loss. Compare
ordinary R, Down+R, Air Dodge, Enhanced Dodge, paid Quick Recovery and unowned
Black/Red behavior. Include duplicate contacts, two attackers, stale/dead sources,
wall contact, interruption, suit switch and room/player replacement cleanup.

The known native contact dispatcher can ignore a hit and the native air string
requires connected contacts, but these facts do not prove the new guard or air
branches. Some native attacks call ReceiveHit directly and bypass the general
observer. Trace a supported attack's real path; do not fake protection by writing
HP back or invent an attacker by scanning nearby windups. Keep shared contact
credit isolated. Enemy resistance, actual damage arguments and ownership must
remain explicit. Then qualify Cross and **one** Maul air route before adding the
charged Pursuit branch or expanding counter coverage. No new engine behavior
has been tested by this design work.

## Deferred work

| Idea | Current boundary |
|---|---|
| More Red skills, extra stat rows, prices/balance, shop/save expansion | Deferred. Iterate the existing kit; Overclock/Dragnet/Vortex are the final added skills. |
| Spider-Man 2099 combat | Hunter's Return and Talon Lift are shipped. The other five replacements plus the guard and air extensions remain design proposals. If implementation is requested, qualify one physical guard/riposte first; retain native/shared controls and purchases. |
| Third suit and other suit concepts | Deferred; TASM1/2 share one kit. No suit selector or migration is implemented by this roadmap. |
| Downtown Grid/Lost Lab, Residential Skyline Run, Hive Quarantine Heart | Deferred concepts. No new allocations are authorized by the old pitches; audit current flags/storage before any future expansion. Hive stays post-story. |
| Midnight Express, gauntlets, timed replays, collectibles/reward systems | Backlog ideas, not unfinished work required for the current chapters. |
| Moving trains, rideable loads, changing solid platforms | Need a complete native collision/ownership prototype before promising a set piece. |
| Cross-room timers/pursuit and broader music routing | Need lifecycle/channel-budget evidence. Existing timers and audible cues do not prove these larger features. |

## Historical designs

The full pre-cleanup roadmap and three planning catalogs are preserved byte for
byte in the existing verified archive, snapshot 2026-10-21. They retain detailed
early kit fantasies, rejected moves, Signal Leech/Crane construction pitches,
old allocation estimates and the seven-skill 2099 theorycraft. They are historical
context, not a second active plan. Later implementations and player decisions
above supersede their original next/proposed wording.

```powershell
python tools/doc_archive.py list roadmap
python tools/doc_archive.py read docs/TASM_ROADMAP.md --toc
python tools/doc_archive.py read docs/TASM_ROADMAP.md --section 'Spider-Man 2099'
python tools/doc_archive.py read docs/TASM_ROADMAP_2099_PRE_FILM_2026-10-23.md --toc
python tools/doc_archive.py read docs/TASM_ROADMAP_2099_BEFORE_AIR_COUNTER_2026-10-23.md --toc
python tools/doc_archive.py read reference/tasm_upgrade_plan.json --lines 40
```

Shipped release history stays in CHANGES; format/engine discoveries stay in
TECHNICAL. Neither belongs in a new session or release Markdown file.
