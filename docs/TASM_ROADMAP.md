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
The latest 2026-10-23 request adds height/neon red webs and film research;
it does not activate another combat move. The remaining five Black moves,
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
The remaining five Black proposals stay deferred. If combat work is requested
next, the revised Raking Cross is the strongest next prototype; resolve its
native contact/recovery before expanding the rest of the kit.
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
The latest request adds height/neon red webs and a film-based design reassessment.
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

The recommendations below supersede the earlier proposed choreography, keeping
the same purchase slots. Only the first two moves are implemented:

| Native Black purchase | Move / status | Reassessed role and decision |
|---|---|---|
| Webbed Fury | Hunter's Return (implemented) | Keep the successful-dash/optional-A catch. It is the clearest tether-and-pursuit fit. Any later motion polish should stress line tension and a forceful catch; preserve resistance and R. |
| Power Launch | Talon Lift (implemented) | Keep the compact coil/rake and manual held-B air catch as a gameplay bridge. It is an adaptation, not a literal film attack; do not add automatic ascent or repeat launches. |
| Ground Rebound | Predator Rebound (deferred) | Emphasize a heavy downward drive and short grounded recovery. Treat the native bounce as an optional opening, not the kit's main recurring spectacle. |
| Black Widowmaker | Raking Cross (deferred) | Best next prototype: low rake into a short crossing pounce/body drive, then a turning claw exit. Drop the decorative passing heel kick. A wall pin needs real collision/release proof; use a grounded drive until that exists. |
| Poison Pummel | Talon Cyclone (deferred; rethink most) | Replace the long rotation/rising-scissors concept with one compact airborne catch, brief claw contact and a downward drive. Working name can remain until selected. Preserve the existing purchase; do not infer a venom status from its native name. |
| Super Charge | Predator Wind-Up (deferred) | A brief loaded pounce/heavy catch with readable shoulder/hip compression. Keep ordinary movement available while priming it; contact and misses need recovery. |
| Quick Charge | Relentless Pursuit (deferred) | Support quick re-entry after one evade/manual jump, spending the carried charge on the next attempt, including a miss. It should reward the player's chase, without automatic tracking or permanent stun. |

The recommended identity is **close/cut off -> tether or catch -> drive/slam ->
re-engage**. Air strings remain a choice after Lift, rather than the required
destination of every attack. Show weight through anticipation, overlap, impact
and recovery while retaining responsive inputs. Qualify continuous paths,
misses, both facings, armor/resistant bosses and native R exits before expanding.

Native ground A dash, air spike, Down+A slam, B, base strings and unowned R keep
their traversal/story roles without a target or charge. No forced boss movement,
teleports, time slowing, new purchases or save expansion. A future pin or air
catch must prove native victim ownership, release on interruption/death/room
changes and ordinary collision first. Review the two shipped moves before
activating any further proposal.

## Deferred work

| Idea | Current boundary |
|---|---|
| More Red skills, extra stat rows, prices/balance, shop/save expansion | Deferred. Iterate the existing kit; Overclock/Dragnet/Vortex are the final added skills. |
| Spider-Man 2099 combat | Hunter's Return ships in v0.32; Talon Lift is implemented for v0.33. The other five proposals remain deferred. Preserve native A traversal, paid ownership and shared upgrades. |
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
python tools/doc_archive.py read reference/tasm_upgrade_plan.json --lines 40
```

Shipped release history stays in CHANGES; format/engine discoveries stay in
TECHNICAL. Neither belongs in a new session or release Markdown file.
