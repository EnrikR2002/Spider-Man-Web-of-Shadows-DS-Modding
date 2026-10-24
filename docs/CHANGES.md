# Implemented changes and releases

Current stable release status is in [TASKS](TASKS.md). Proposed mechanics are
in the [roadmap](ROADMAP.md) (formerly TASM_ROADMAP); a proposal is not shipped
behavior. Historical exact evidence is preserved in the archive.

The latest numbered release below is v0.33.1. Each section records behavior,
tests and limits at that publication; later fixes and player feedback supersede
earlier pending work. Historical battery hashes are observations, never restore
instructions. The current design queue and verdicts are in ROADMAP/TASKS.

## Version policy

Use **major.minor.patch**, displayed identically at boot and in Options. Minor
versions introduce/overhaul mechanics; patch versions fix/polish/rebalance them.
Major marks a finished overhaul or incompatible progression/save contract.
During development we start at 0.1.0. Each published number identifies one exact
ROM; the publisher rejects a reused version with a different hash. Build logs,
`reference/releases.json` and per-ROM release metadata record what shipped when.
This file is the only human-readable release/change log. No per-release Markdown.

## v0.33.1 - 2026-10-23 - Taller 2099 and neon red webs

2099's complete animated pose is 12.5% taller, retaining the fuller cape-free
body, original mesh/rig/clips and grounded feet. The guarded appearance selector
submits a native Y-scale command only for Black. Native web lines and the
companion WebTrap/effect tint use bright scarlet RGB555 `(31,3,5)`. Red keeps its
native height and both original tints. Native shading and line texture remain.

Both cosmetic adapters fit existing zero space without heap/autoload growth.
The 32 KiB kit, Hunter's Return, Talon Lift, other actor assets, movement,
collision/hitboxes, purchases, rooms, audio and save format remain exact.
Only boot/Options text resources change, displaying v0.33.1 identically.

**Qualification.** All 580 source tests and 15 final appearance/archive/document
checks pass. The tests cover the selector guards, fresh model pointers, all
condition flags, caller registers, native Red tint defaults and exact ROM scope.
Paired final/parent positions match; settled Red hero pixels after L are exact.
Real B/B swinging proves scarlet owned lines and native white Red lines.
Talon Lift's manual air damage and Hunter's Return's physical attempt pass.
Fresh ordinary Continue and real-input suit/room transitions retain the current
purchases, XP, HP and checkpoint. A no-heal Terminal sample binds the I8 hero and
two I4 enemy materials; the player eventually dies, so this is presentation
evidence rather than a clear. Native-size move frames and a normal-rate mixed
audio capture are retained. Perceptual listening is unavailable in this runtime;
the audio payload remains byte-identical to the qualified parent.

The canonical, independent full-source rebuild, publisher's rebuild and stable
ROM agree exactly. Publication uses `tools/playtest.py build`; the latest actual
DSV wrapper/payload equals its fresh checkpoint, with the prior ROM/composition
preserved and the original unchanged. No research save is adopted. Exact
identities, controls, source/receipt links and limitations are in
`reference/spider2099_presence.json`. Player appearance/feel, full-route balance,
exhaustive screen-edge culling and actual DeSmuME/hardware pacing remain open.

## v0.33.0 - 2026-10-23 - 2099 Talon Lift

Talon Lift replaces Power Launch's presentation in its existing Black purchase:
200 XP, event 330 / bit 21, with native ownership, dependencies and refunds.
Up+A coils low into an authored rising talon rake while staying grounded.
Hold B for the native full jump, then Y to catch the launch with air hits.
R cancels early through the native evade queue. Native movement, collision,
hitboxes, damage and launch resistance remain; B and the air string stay native.
There is no automatic follow-up or custom jump/target state.

One private 14-sample SCA and a 416-byte stateless adapter fit the existing image
tail without heap/autoload growth. The 32 KiB player kit, Hunter's Return,
other actor bindings/motion, geometry/textures, purchases, rooms and audio stay
exact. Archive growth shifts the following file by 23 KiB to preserve the entire
occupied gap and file tail. No save migration or research save adoption occurs.

**Qualification.** The full source run passed 570 tests; nine final Talon tests
cover ABI, pointer/ownership isolation, native B, R, animation and exact scope,
including occupied-gap preservation. Eleven focused C controls carry forward
through explicit executable/resource identity. Final F proves actual held-B air
damage in both directions, R exit, miss recovery, current Vortex and fresh Continue.
Earlier short B taps played an air animation but missed; those traces establish
why the final manual check requires actual additional HP loss. Native-scale
frames and a normal-speed capture with native mixed audio are retained.

The legacy 68-check kit run passes 58 expectations. All ten failures also fail on
v0.32.1 in nine selected replay cases; two further Dragnet expectations fail only
in the parent replay. Those fixture/AI and pre-v0.31 Vortex expectations are not
new regressions. Native gate/snare/Black parity and the current Vortex control
pass. Scope, raw reports and limits are in `reference/talon_lift.json`.

Canonical F, publisher's normal-source build and installed stable ROM match;
boot/Options agree. The actual latest DSV wrapper and 512-byte payload match the
publication checkpoint exactly. Prior ROM, metadata and recipe/overlays remain.
Player feel/appearance, full-route balance and actual DeSmuME/hardware pacing
remain open.

## v0.32.1 - 2026-10-23 - Isolate Hunter hits and reset replaced owners

Hunter's Return now restores both shared hit-type fields after a victim's native
ReceiveHit and hit credit finish, before the dispatcher advances to another
victim. Only the selected target receives the launch override. Skipped/ignored
victims and nested dispatches are covered. A current player allocated at a new
address also clears a departed owner's private phase, so room reloads cannot
leave the move locked out. Native movement, damage arguments and hit credit stay.

The 324-byte correction occupies the previous image's unused tail. There is no
new heap/autoload reservation. Models, textures, private motion, other actors,
rooms/audio, purchases, save format and the 32 KiB kit match v0.32; only two version
strings, three branches and the correction code change. v0.32 remains immutable.

**Qualification.** All 59 source/regression checks pass, including target-first/
last shared records, nested/ignored/skipped hits, ABI/flags, new-player cleanup,
reactivation and exact scope. Native crowd control damages both opponents,
launches the selected target and leaves the bystander in normal knockdown.
That particular alignment also passes on the parent; the shared-record leak is
proved by the ARM regression. The old build fails native reload/reactivation;
the correction passes. Red/unowned, R and stale-target controls pass. Arrival,
NPC eligibility/bystander setup and stale-owner injections are labelled private
fixtures. Accepted/canonical/normal/publisher/stable ROMs, boot/Options and latest
DSV/checkpoint bytes agree. Details: `reference/hunters_return_fix.json`.
No research save was adopted. Full-route balance and DeSmuME pacing remain open.

## v0.32.0 - 2026-10-23 - Hunter's Return and fuller 2099 physique

The first planned 2099 move replaces Webbed Fury's presentation in its existing
Black purchase: event 329 / bit 20, native 100 XP price, ownership and refund rules.
After a successful ground dash, release A and tap A again. An eligible target
is recalled through the native line/pull and met with an authored rising talon
rake that uses the native launch reaction. B remains a manual jump; R exits.
When native recall is unavailable, a short physical pursuit attempts the rake
through actual collision. It does not force launches on the Conductor.
Native A traversal, base strings and other purchased skills remain intact.

2099 has fuller chest/back, deltoids, biceps and forearms, retaining the tapered
waist, height, 37-node rig, mounted blades/talons, cape-free texture and 516
triangles. Red's GPU list, both texture pools and the guarded selector remain
exact. The native purchase tables, 32 KiB kit, rooms/doors/audio and all other
actor bindings/clips are preserved; one 4 KiB runtime extension and three private
motion resources implement the skill. No save migration or research save adoption.

**Qualification.** Forty-nine source/regression checks plus one lab-output guard;
12 focused owned/unowned/Red/whiff/held-A/optional-A/mirror/wall/cancel/hurt/form/
stale controls; a separate full native recall/launch; and 12 actual damaging
physical follow-ups against the live Conductor with zero forced launches.
Boss healing and initial cleared-encounter/arrival fixtures are labelled.
The latest copied-save Terminal scene keeps the player I8 and both observed
enemy species I4 bound across 218 crowded samples; no third enemy was observed.
Native-scale rake/launch, physical rake and crowded hurt captures were reviewed.
The shop instructions/owned checkmark fit. Canonical, accepted candidate,
normal-source build, publisher candidate and stable ROM match; boot/Options,
latest DSV wrapper/payload/checkpoint and clean original agree. Details and
diagnostic exclusions: `reference/hunters_return.json`. Player feel/physique
preference, full-route balance and actual DeSmuME pacing remain open.

## v0.31.0 - 2026-10-22 - Tether Vortex, armored Conductor and lethal damage

Vortex keeps its existing paid Red row and now requires an actual webbed enemy.
Web with regular A or Dragnet, release A, then Down+Y: capture up to four nearby
cocoons, swing their bodies through a continuous two-turn catapult and haul
them into a floor slam. Bodies can knock nearby enemies down. R/hurt/jump exits
release the private move. The old Y,Y,Down+Y/seven-strike entry is superseded.
Motion uses native actor velocity/collision; no position or clock writes ship.
Native A/B/base strings/evade, purchases and Both Suits abilities remain.

The Conductor is 28% larger, with broad engine-block armor, rib plates, visible
turbines, piston gauntlets, exhausts and a symbiote split jaw. Its 39 private
motion routes retain exact rotations/timing and its liked native attack programs,
HP, AI, voices and collision remain. A compact boss-only 64px RGB555 texture
also fixes a persistent magenta palette defect reproduced on the old build;
the shared Terminal I4 atlas and other actors remain exact. The duplicate red
enemy bar is suppressed only for this boss; the native top meter remains.

Vitality previously scaled old HP minus the already-clamped remainder. Lethal
hits therefore removed a fraction of remaining HP repeatedly. The corrected
operand uses full native incoming damage, applies room/Vitality scaling, then
clamps once. The latest copied-save 1536-Q12 control takes eleven damaging hits
to die on the old release and one on the corrected build. Vitality still gives
its intended protection. Ownership, prices, save format, rooms/doors, rewards,
2099 and the 32KiB kit reserve remain.

**Qualification.** Twenty-six scoped tests include 256 damage combinations,
ownership/cocoon gates, interrupt/stale-pointer handling and HUD ABI/flags.
Native regular/Dragnet, mirrored and cancellation examples run; an isolated
body-contact example hits a real bystander. It parks unwebbed standing enemies
through frame 100 and is not ordinary-play crowd-balance proof. Final composition
earns Red victory/save with labelled player healing and retains it through fresh
Continue; an identical-boss/Black-path control earns a no-refill Black win/save.
Earlier failed crowd interruptions and exact byte-scope reuse are retained.
Fresh unmodified normal Continue preserves current abilities, XP, HP and save.
Canonical/normal/published identities, boot/Options, latest DSV/checkpoint bytes
and clean original agree. Full evidence: `reference/vortex_forge.json`.
Player feel/appearance acceptance and actual DeSmuME pacing remain open.

## v0.30.3 - 2026-10-22 - Restore crowded Midnight enemy textures

Custom Midnight enemies appeared white in the Terminal crowd because their
shared 128x128 direct-color creature atlas used 32 KiB and stayed unbound in
live enemy materials. An exact resource-only experiment keeps the atlas artwork,
UVs, material names/palette IDs, model sheet and every XBD/model/animation byte
exact, while packing it as 128x128 I4: 16 colors and 8 KiB of pixels. In a fresh
copied-save encounter, all three observed enemy materials bind as I4; the 2099
player still binds its original I8 texture. This supports texture-residency
pressure as the cause, though format and footprint change together.

The shared artwork is quantized without dithering. Model geometry, texture UVs,
128x128 material dimensions, rooms, enemy AI/HP, movement, audio, ARM9/ARM7,
the player suit, its I8 atlas, purchases and the entire 32 KiB kit remain exact
to v0.30.2. Only the creature atlas and English/American version strings change.
This fixes the sampled Terminal enemy textures; it does not qualify all rooms
or DeSmuME pacing.

**Qualification.** The resource-only residency experiment and the full numbered
candidate bind three live enemy materials in the crowded Terminal scene. The
native route passes from a copied latest save with only initial room/current-owned/
initial-HP fixtures; native enemy AI, damage and positions run after arrival, with
no healing. The actual battery remains unchanged. Player appearance/gameplay
and enemy model/motion/XBD data retain v0.30.2. Full normal-source/canonical/
accepted/installed identities, release pins, fresh battery checkpoint and
version labels agree; exact evidence is in
`reference/spider2099_enemy_texture.json`.

## v0.30.2 - 2026-10-22 - Cape-free Spider-Verse 2099

The player's supplied Across the Spider-Verse reference replaces the prior
classic/cape direction. The red web cape and its entire appended stream/atlas
region are removed. 2099 now has darker navy with cobalt edge shading, red
negative-space mask fields, a larger angular chest spider, broad shoulder caps,
red knee chevrons and cleaner glove accents. Broader chest/lats/traps/deltoids,
athletic thighs and a narrower jaw refine the silhouette. Six swept blades remain
mounted on actual forearm skin, with small talon tips. Black draws 516 triangles
on the unchanged native 37-node rig/SBC and animation set.

The fully opaque 128x128 I8 atlas keeps the parent's 16 KiB pixel pool. Its actual
original dimensions are declared; palette zero is opaque navy. The shared model
retains Red's exact GPU list/texture. Only the existing cosmetic selector's
size/footer literals change; its instruction bytes, hook/allocation, native
controls/physics, entire 32 KiB kit, purchases, rewards, rooms/audio and save
contract remain exact. No new Black moves or animation clips are installed.

**Qualification.** Accepted B, canonical final, independent normal-source build
and guarded installed stable match SHA-256
`214282a5ddf6ac71bbbddd8b5aa3854a13754313a3c66ac29d27ceb55b4f3808`.
All 45 focused source/ABI/release/document checks pass. Fresh copied-latest
native-input motion/attack/suit-switch and real door controls pass. Ten live RAM
captures prove list selection, dimensions, I8 binding and opaque palette zero in
both forms, including a reallocated model and Black attacks in the next room.
Native motion/state/purchase/XP/HP comparisons agree, apart from one transient
newly initialized room-load position sample retained in the raw evidence.

The crowded Terminal control renders the new player under native attacks/hurt.
It has initial room/current-owned/initial-HP fixtures and does not prove balance
or a clear. Its white untextured enemies also occur in the fresh v0.30.1 parent
and retained v0.30/D/E controls. Earlier broad enemy-binding success claims were
too strong; the older recovery proved player binding only. Enemy texture repair
remains outstanding. Native mixed rosters/arrival timing differ, so the two
crowded runs are not a gameplay parity claim. Player appearance preference and
actual DeSmuME pacing remain unconfirmed.

The whole latest actual DSV wrapper/payload matches the qualification copy and
publication checkpoint. Previous ROM/recipe/metadata and the clean original are
retained. Exact identities, controls, corrections, captures and publication
verification are in `reference/spider2099_movie.json`.

## v0.30.1 - 2026-10-22 - Active 2099 sculpt, blades and web cape

**Later qualification correction (0.30.2 audit):** retained parent/D/E RAM and
captures contain untextured enemy materials. The older crowded-binding recovery
establishes player binding, not restored enemy textures; that issue remains open.

The Black slot now actually selects its new geometry. The first-pass audit found
both forms using shared `spd.nsbmd`, leaving v0.30's authored `spdB` mesh inactive.
The shared resource now retains the exact original Red list and selects Black's
sculpt immediately before native draw. A bounded cosmetic adapter checks the
live wrapper/model/tag/form, preserves registers and CPSR flags, and changes only
shape/material appearance fields. No RAM pointer is cached across room loads.

2099 gains wider pecs/lats/traps, fuller upper arms, balanced forearms and modest
thigh volume. Six swept blades mount on ray-qualified forearm skin; the larger
curved crimson web cape anchors behind the actual back surface and deforms with
native bones. Small talon tips remain. Black draws 676 triangles on the unchanged
37-node rig. Native animations, physics, combat, ownership, prices, rewards and
chapter/audio resources retain their contracts; the entire 32 KiB kit is exact.

The transparent-index 256x128 I4 atlas uses 15 opaque colors and the parent's
16 KiB pixel pool. The body half is opaque; the web has real holes. The rejected
32 KiB I8 trial leaves crowded Terminal actor textures unbound despite passing
its route checks. The lower-footprint D/E controls restore binding. Red's original
geometry/texture and native material dimensions/transparency return on switching.

**Qualification.** Accepted E, canonical final, guarded normal-source build and
installed stable match SHA-256
`7286d0536b6e29d0ebdc355563c6ece8e974058534c9676024ee67928cae530c`.
All 54 source/ABI/release checks pass. Fresh copied-latest native-input Continue,
motion and door runs cover both forms/facings, jumps/air attacks, spike/slam,
ground strings, dodges and reload. Six RAM snapshots prove actual list, texture
format, dimensions and transparency, including a different live model allocation
after a door. Purchases/XP/HP match; motion positions agree exactly. One transient
newly initialized room-load position sample differs and is retained in evidence.
An exact-current-owned, no-heal mixed Terminal observation renders three native
enemies and the textured hero/cape under attacks and hurt. Its initial arrival/
owned-state fixtures and passive driver do not establish balance or a clear.

Only the shared player model, Black texture, two version resources and the scoped
draw adapter/autoload metadata change from v0.30. The entire actual DSV wrapper/
payload matches its latest qualification copy and publication checkpoint. Prior
ROM/recipe/metadata and clean original are preserved. Player visual preference
and actual DeSmuME pacing remain open. Exact controls, rejected trials and
verification are in `reference/spider2099_polish.json`.

## v0.30.0 - 2026-10-22 - Classic Spider-Man 2099 appearance

**Later validation correction:** the next appearance iteration proves that both
forms actually load shared `spd.nsbmd`. v0.30 activated its texture, while its
authored `spdB.nsbmd` geometry remained inactive. Its source/pose checks did not
establish that the fins/cape were drawn in-game. The original release bytes and
receipts remain intact; the real draw-selection fix and controls are tracked in
`reference/spider2099_polish.json` and TECHNICAL.

The Black slot now wears an authored 128x128 I8 blue/crimson atlas with pointed
red mask fields and skull-spider markings. Six forearm fins, six small talon
tips and a short open web mantle add 100 triangles on native stored matrices.
Original skin, 37-node rig/SBC, material tint and animation bindings remain exact.
This is the first appearance stage of the requested 2099 rework. Its seven
proposed purchased moves, new combat animations, charge banking and gliding are
not implemented by this release.

Only `spdB.nsbmd`, `spdB.nsbtx` and the English/American version strings differ
from v0.29. ARM9/ARM7, the complete native Black and TASM kits, ownership,
dependencies, traversal/story barriers, prices, rewards, rooms and audio remain
byte-identical. Prior chapter qualification keeps its actual v0.29 scope.

**Qualification.** Accepted A, canonical final, independent normal-source build
and guarded installed ROM match SHA-256
`2ebdf894ae723ce6ead2cfbe15a4b11151243f639958bdeea18e9149bdabf088`.
Forty-three source/release checks pass, with a separate seven-test GPU/atlas
round-trip regression rerun. Fresh copied-latest Continue observations use real
inputs without RAM writes, HP/ownership/position fixtures or stale states. They
cover both forms/facings, walking, jumps, air attacks, Hammer Spike, Hammer Slam,
ground strings, air/ground dodges and a room transition. Both comparisons retain
all purchases, XP/HP and every jointly valid position sample; the airborne state
sequence agrees exactly. Initial idle variation and one-frame loading/action
phases in the Continue run remain in raw receipts. Model views and native-scale
in-engine pose sheets are reviewed; player visual preference and actual DeSmuME
pacing remain unconfirmed.

The complete latest real DSV wrapper/payload matches its pre-publication copy
and checkpoint. v0.29 ROM, recipe and metadata are retained; clean original is
unchanged. Exact scope, qualification, retained failed test-module invocation and
publication verification are in `reference/spider2099.json`.

## v0.29.0 - 2026-10-22 - Skyjack, Skitter and Crane finish

Skyjack's horizontal juggle correction now uses native velocity and collision.
The parent could drift past a wall; the corrected move respects both walls while
retaining air hits, spike/bowling and R exits. Only the first kit code region
changes; its entry offsets, route/state layout, second block and 32 KiB reserve
remain. Purchases, prices, dependencies, native/Black controls and rewards stay.

Rail Skitter receives a 276-quad low silhouette, 57 bound lifecycle clips with
planted support, carried scythes and overlapping motion, and eight short dry
cues. Native attacks, damage, hurt, launch/prone/get-up/death and physical XP/HP
rewards remain. All other actor bindings and sound waveforms stay exact.

Freight Ballast now clears a roof edge before jumping toward an overhead player,
then returns over the roof and retains its navigation phase until landing. The
helper is scoped to the owned Freight actor and allows native hurt/death. Six
existing hoist meshes improve warning limits, hook contrast, guarded versus open
motor, damaged guard and saved wrecked aftermath. Hoist timing, collisions,
damage, checkpoints and saved victory retain their contracts.

**Qualification.** Installed, canonical and independent normal-source builds all
match SHA-256 `3c9aeacca6bbc446e2f61815b341e5c5106d0f30a4c9510bcbf9384fbea16db2`.
All 68 kit checks, 18 Midnight and 30 Crane directed doors pass. Source validation
passes 106 broad checks and 31 final focused checks. Final C clears the mixed
Terminal roster with current purchases, native HP and no refills. Native Freight
bait reproduces the parent ceiling loop; corrected pursuit reaches both tested
roofs and deals damage. Skitter's three attacks hit; a native lifecycle control
earns XP/HP. Red/Black hoist and Conductor wins, returns, saves and fresh Continue
retain their actual candidate identities and unchanged-byte inheritance in
`reference/chapter_finish.json`. C's Black earned checkpoint reaches Save Options
using native movement and X. Door controls park enemies/heal the player; boss
wins have explicit initial setup fixtures. They are not full-route play evidence.

The actual latest battery, wrapper and checkpoint remain byte-identical; v0.28's
ROM, recipe and metadata are retained. Native-scale presentation is reviewed and
all eight Skitter cue waveforms match the rendered mix without clipping. Audio
quality, full-route fun and actual DeSmuME pacing remain player gates. B/C differ
only in six hoist meshes; inherited controls are not relabelled as C runs.

## v0.28.0 - 2026-10-19 - Midnight combo reliability and escalation

Midnight's Conductor could look active while failing to connect attacks, and
late-room budgets did not create a felt rise in pressure. The boss now uses a
verified native counter route with real contact and damage, bounded counter
commitment, and brief ordinary hit reactions that keep combo openings. Its
native knockdown resistance, damage, death and rewards remain. Boss movement
brakes and faces within strike range during openings; arena retries clear the
mod's private decision state.

Signal House 77 and Pump Refuge 82, their active entrances and map branches are
removed. Old checkpoints retain safe one-way recovery. The unfolded map follows
the playable route 76, 78, 81, 83, 86, 87, 89, 88 and shows the return loop; Relay
Sanctuary 87 is the remaining main-route save room. Late encounters use stronger mixed
groups, staged native HP, a four-actor cap, faster Skitter pursuit and committed
Warden windups. Terminal and Turbine Rise were tuned again after current-owned
tests showed the first ramp pass was insufficient; Turbine's later wave now
fights on its continuous upper landing. Native guide text no longer points to
the removed saves.

**Qualification.** The final installed ROM and canonical candidate match at
SHA-256 `6819cb91e824961552b86690c3fdd112930bbd1cbb70d5c3c76978b5ce932a20`.
The publisher retained v0.27 and preserved the then-current real battery against
its pre-build checkpoint. 190 broad checks and 45 focused/publication checks passed.
Current-owned Red and Black saves, fresh Continue, boss phase programs, the four
ramp rooms, removed-room entry, legacy recovery and all 18 directed doors pass on
the qualified candidates with the unchanged-byte inheritance recorded in the
receipt. No-R pressure loses to native damage; reactive R/B
controls win. Player confirmation of full-route fun and actual DeSmuME pacing
remains open. Detailed scope and limits: `reference/midnight_reliability.json`.

## v0.27.0 - 2026-10-19 - Combo openings and Midnight creature renewal

The player likes0.26's stronger, mobile boss but finds its constant stagger
suppression frustrating. Normal boss attacks now accept native hurt, allowing
real strings. Knockback/floor reactions become a standing recoil, retaining
knockdown resistance. Four actual owned HP reductions queue an escape/counter;
only that counter's commitment has armour. Its shorter recoil, earlier return
and lower leap put the strikes back in reach of grounded targets. Recovery
remains punishable, and HP damage/death/rewards remain native throughout.

- Conductor, Skitter, Warden and Eye have new closed anatomical meshes and
  authored continuous poses. A coherent symbiote body, readable side eyes,
  working claws/scythes and articulated plates/aperture replace crown/shard
  clutter. Carried hand targets, restrained body turns, coordinated weight
  shifts and longer boss recovery improve continuity. Native lifecycle routes,
  including get-up attacks, remain complete. Final meshes use 298..364 quads
  and retain the existing shared painted atlas/material-tint behavior.
- Terminal, Floodworks, Turbine Rise and Observatory use progressively stronger
  mixed encounters. Native cost budgets are8/8/7/12 with live limits3/3/3/4;
  these are cost units, not enemy counts. Sanctuaries and the return corridor
  retain breathing room. Room geometry, collisions, maps and doors stay exact.
- Audio/voices, Crane creature resources and the 32KiB player kit remain exact
  to 0.26. Native A/B/evade, purchases, ownership, Both Suits abilities and
  rewards retain their contracts. No skills, prices, save fields or branches
  are added.

**Qualification and scope.** Final C Red earns native victory/save without
refills; both earned suit saves pass fresh Continue and cleared-boss return on C.
Black's victory/save uses B, with identical ARM9/motion/audio/room data; C changes
only four meshes. B's no-refill base-Y control observes68 standing staggers,
30 HP reductions during counter armour,15 responses and five real player hits,
then wins/returns. Final C's healed full-phase run crosses contacts in all four
normal programs; all four expanded full-HP room rosters clear, with later-spawn
waits in the first three. All 22 directed doors pass native-input qualification.
Skitter/Warden A and Eye B each demonstrate actual HP contact in all three
programs; ordinary motion/contact resources stay exact across these candidates.
Native-scale final boss/mixed presentation was reviewed separately.177 changed
binary resources round-trip;180 relevant broad tests and 16 publication/document
checks pass with explicit inheritance. Early weak-counter/dense-mesh candidates
remain in the receipt. These fixtures establish mechanics/clearance, not fun,
complete-route balance or actual DeSmuME pacing.

Guarded clean-source publication reproduces the qualified final ROM exactly.
Boot and Options both show0.27.0; a fresh actual-player-copy Continue reaches
the correct sewer checkpoint. The latest actual DSV remains byte exact to its
publisher checkpoint and startup observation. Original ROM is unchanged;
previous0.26 ROM, metadata and exact active recipe are backed up. Identity,
selected evidence, source hashes and publication audit:
`reference/midnight_finale.json`. Player replay/quality acceptance is pending.

## v0.26.0 - 2026-10-19 - Voltage predator and audible creatures

The player found0.25 somewhat better but still slow and easy to combo-lock;
Midnight enemies seemed silent. This correction makes incoming hit pressure
cause an actual physical escape/return attack and restores audible effects.

- **Reactive Conductor:** three real HP reductions within 80 decision updates
  queue a backward leap and returning strike, including from flinch. Matching
  running clips consume hurt transitions without restarting. Actual HP damage,
  vulnerable recovery, death, native rewards and the original boss bar remain.
- **Mobile electronic symbiote:** low forward-loaded posture, twisting/spinning
  leaps, dark shell/conductive accents, immediate native drives, faster pursuit
  and turns in authored gaps. Four fast normal programs and two counter
  trajectories use five owned action slots; a private HammerSlamLand GAB is
  appended and only the boss's binding/attack flag changes. All movement uses
  native velocity, gravity and collision. No player/actor coordinate writes.
- **Audible creatures:**0.25 voices/tells were extremely quiet despite accepted
  sound requests.57 owned samples now use role-based RMS levels, peak control,
  PCM16 and hostile-cue priority. An isolated alert renders about 11x stronger.
  Actual Skitter/Warden live/muted pairs have matching gameplay and about 0.99
  tell/strike waveform matches. Eye's divergent control is labelled; its live
  tell/burst also match about 0.99. Native/player/music rows remain unchanged.
- **Preservation:** accepted rooms, collision, maps, textures, other actor
  bindings, purchases/abilities and 32KiB kit remain exact. The complete0.25
  lifecycle is retained, including the get-up attack's synchronized GMB/GAB.

Red/Black controls earn native boss victories/saves without refills and both
earned batteries pass fresh unmodified Continue on final E. A healed pursuit
control observes22 counter responses.455 broad D checks and 17 final focused /
document checks pass; C/D/E inheritance is byte/template-scoped.33 existing
resources change and one private GAB is appended;31 changed binary resources
parse/round-trip. Boot/Options0.26 and actual-player-copy Continue are visually
confirmed. Guarded clean-source publication produces the qualified bytes and
preserves the latest actual634-byte DSV exactly against its checkpoint.

The mixed audio/first-wave control is retained as limited evidence: later native
spawns invalidate its old short empty-room assertion. Failed driver/Black
probes are preserved. Player quality, full-route balance and actual DeSmuME
pacing remain open. Exact identity, source hashes, selected/failed controls and
publication audit: `reference/midnight_voltage.json`.

## v0.25.0 - 2026-10-18 - Creature motion, sound and Conductor overhaul

Responds to the player's0.24 verdict: the environment and more distinctive
enemies were welcome, while rigid animation, poor sound and a slow/easy boss
were rejected. The accepted terrain remains byte exact.

- **Creature motion:** crossing figure-eight slashes, larger torso/hip loads,
  delayed head/shoulder motion, raking follow-through, twisting low pounces and
  recoil.125 private SCA payloads actually change; native lifecycle clips remain.
  87 contact geometries and 52 event streams match the shorter attack programs.
- **The Conductor:** tapered mask, articulated serrated forearms, faster native
  pursuit, advancing multi-hit combinations, travelling floor shocks, a long-range
  execution beam and a half-health leaping slam. Base HP rises to 132. Floor tells
  can overlap the creature's attacks. Limited committed-attack/get-up counter
  poise prevents repeated knockdowns from suppressing the whole fight; actual
  HP damage, vulnerable openings and native death/rewards still apply.
- **Original boss HUD:** the original game's purple boss meter follows actual
  current/max HP, disappears after defeat and uses the native renderer/lifecycle.
  Exact room/config/controller/actor/motion ownership protects other encounters.
- **Sound:**57 new frozen CC0-derived vocals, tells, steps and strikes use short
  dry layers, restrained midrange voices and different levels for different roles.
  Quiet foley and transient impacts replace the previous blanket echo/normalization.
- **Freight recovery:** a Maw under the narrow recovery walkway now walks past
  its edge and uses a native-impulse vault to regain the deck. Native Land is
  eligible for that existing recovery; no actor or player coordinates are written.

Both suits earn native boss victories/saves without refills; fresh unmodified
Continue retains victory and reaches the cleared arena. The final B candidate
also passes real-player-copy Continue, native Maw escapes and the full mixed
Freight clear. All 22 programs have observed native HP-loss controls. Original
Mega Venom HUD, Observatory mixed play and six species contact/base-string clears
are covered by selected A controls with explicit A-to-B byte/template inheritance.
447 broad A tests,8 focused B tests and 2 document checks pass.754 regenerated
payloads parse/round-trip;267 actually differ. Rooms/maps/bindings/textures and
the 32KiB kit are exact to 0.24. Boot and Options visually show0.25.0. Clean-source
reproduction and guarded publication produce the same final ROM; the latest
actual634-byte DSV equals its publisher checkpoint and remains unchanged.

Native-scale captures and mixed PCM were inspected; selected mixes do not clip.
Presentation/fun acceptance, full-route balance and actual DeSmuME pacing still
need player replay. The unchanged Ballast elevated-pursuit limitation from 0.24
remains separate from ground attack coverage. Exact identity, selected/failed
receipts, inheritance and source hashes: `reference/midnight_encore.json`.

## v0.24.0 - 2026-10-18 - Enemy contact correction and Midnight room rebuild

Corrects the player-rejected0.23 enemy implementation and replaces Midnight's
repeated rectangular envelopes with different playable shapes and proportions.

- **Working attacks:** private GMB activation now agrees with the authored
  contact windows. Warden's march and Ballast's charge use a verified native
  RunAttack carrier; Conductor's verdict uses DropDownAttack. The former ranged
  carriers could count contacts without damaging the player. New ground programs
  wait for a real landing instead of interrupting navigation jumps/falls.
- **Enemy presentation:** seven private meshes gain substantial limbs, bell
  fists and closed blades/petals. Shorter whole-body attack curves, low pounces,
  loaded heavy downstrokes and continuous recovery replace the slow poses.
  Warden/Ballast fists meet their planted feet at impact; the Conductor conducts
  its Fugue and loads its Crownfall landing. The private lifecycle includes
  native recoil, knockdown, prone, get-up and death.347 clips are regenerated;
  230 SCA and 234 GMB payloads actually differ from 0.23.
- **Audio:**57 frozen recording-based cues give the seven species their own
  voices, short tells, footsteps and move-specific strikes. Exact actor ownership
  is checked at the queued spatial request, covering stock events missed by the
  old vocal filter. Fall/landing continuations stop repeating hurt vocals.
- **Midnight structures:** an L-shaped street/tower, T-shaped terminal, bent
  service hall, diagonal turbine shaft, sunken sloping Observatory, vaulted
  checkpoint chapel, stepped Crown descent and crowned boss amphitheatre.
  Signal House shrinks to 80x56, Pump Refuge becomes112x48, Sanctuary128x80,
  Crown Return256x112; Observatory gains16 units below its old floor with rooted
  combat terraces. Collision, visible trim, cameras, anchors, doors, detailed maps
  and overview silhouettes follow the new layouts. Existing terrain materials stay.

Published ROM SHA `c31bae4c60869133f9cf4dd3e8b0b2895123d1a2e99d91599231cc8d983b1393`;
128MiB, boot/Options0.24.0. The full clean-ROM/overlay production recipe reproduces
these exact bytes. Source/qualification/publication: `reference/midnight_rebuild.json`.
All 813 regenerated resources parse/round-trip;570 actually change. The32KiB player
kit, original actor bindings/clips, first two SDK rows, native abilities,
purchases, ownership, reactions, rewards and save schema remain. Crane room
geometry stays exact to 0.23; its three creature styles receive the enemy changes.

Agent checks: all 18 regular programs cause actual player HP loss, with native
base-string clears; exact ARM/audio/private-resource comparisons carry selected
F/G/I cases to the final J, and Ballast is checked on J. All four final Conductor
programs cause HP loss after actual half-HP progression. J passes22 directed
Midnight doors, Black tower/reverse stairs, Red return to the original sewer,
roof pursuit, native pump interaction and full-HP mixed Observatory/Freight
clears. Mixed controls heal the player; they are not balance tests. Both suits
clear both bosses without refills: Conductor uses the actual19-unit maximum,
hoist uses the labelled copied-save Vitality/kit fixture. Both earned saves
survive fresh unmodified Continue. Final mixed PCM has no clipping.440 broad
and 13 final focused checks pass; native boot/Options were visually confirmed.

The latest actual battery is unchanged and matches its exact publisher
checkpoint;0.23 ROM/metadata/recipe remain available for rollback. Failed
controllers are retained and excluded from selected evidence. Full-route
balance, actual DeSmuME pacing and player quality acceptance remain unconfirmed.
Ballast can still repeat navigation hops when the hero stays directly above a
Freight overhang; ground attack coverage does not establish complete elevated
pursuit. This release does not claim a player-approved enemy presentation.


## v0.23.0 - 2026-10-17 - Chapter spectacle and authored encounters

Published through the normal playtest builder. Both districts gain more distinct
spaces, encounters and consequences while retaining their accepted connections.

- **Midnight Line:** real carriage-roof slabs above an open platform, physical
  enemy ascent through carriage gaps, room-specific patrol compositions and
  approach triggers. A native Floodworks lever stabilizes the pumps; saved
  lights connect the terminal, pumps and turbine. The Conductor and floor lanes
  take turns committing pressure, followed by a persistent electrical shutdown.
- **Crane Row:** painted harbor materials, a more continuous ship silhouette,
  stronger supports and machinery. Restoring power lights several rooms and
  starts the counterweight. The hoist has a larger motor/guard/grabber, shorter
  warnings, longer combo openings and a real half-HP damaged-guard phase. Victory
  leaves a disabled motor. A native save sphere on the Long Arm approach gives
  a safe Continue position, closes during combat and returns after victory.
  Crane's map now selects its own area; its overview marks the new checkpoint.
  Crown's two native waves each use the three enemy roles, replacing the longer
  repeating heavy roster; the unlocked hoist route leads straight to its save.
- **Shared:** all 22 active rooms receive new materials and architectural depth.
  Seven creature meshes have heavier limbs/body mass and side-facing cores that
  remain visible when turning. Existing authored moves now respond to spacing;
  native-velocity obstacle recovery replaces several vertical pursuit stalls.
  Nine layered recording-based cues add sparse ambience, machinery tells and
  boss releases. Existing Winch Cache supplies gain a small native reserve stash.

ROM SHA `534c9df52d91f6dbb4102f4deb9143fbaea6b8324f9e7525db4a3880d226e18c`;
128MiB, boot/Options0.23.0. Recipe/pins/canonical output reproduce byte for byte.
Sources: `chapter_spectacle` tools; exact receipts: `reference/chapter_spectacle.json`.
The32KiB player kit, native abilities, purchases, ownership, reactions, rewards
and save schema remain. All 3910 existing motion/actor-binding resources are exact
to 0.22.1. Enemy HP still uses the native strength dial; room budgets/compositions
are deliberately changed.

J's52 directed door controls pass with real inputs; K carries them by exact room,
script and instruction identity, changing only three Crown spawn-data bytes.
Final Black Conductor/hoist wins use native HP without refills; Red controls use
J's identical boss code. Earned post-victory saves/fresh Continue retain both
victories. K's complete Crown clear earns the actual hoist door. A focused
settled-arrival checkpoint control, with the already-earned crew flags preset,
and fresh Continue retain the crew clear and safe pre-boss retry position.
Terminal's Black roof control reaches the roofs with attacking Skitters/Wardens.
Mixed Freight/Crown controls use native HP/damage/callbacks and a healed60-unit
player. Captured PCM verifies all nine new cues and release timing. Failed
controls remain recorded, including the earlier overlong Crown staging.
Broad428 tests pass before the OBJ audio adapter;56 final focused checks pass on K.
The actual battery and its exact publisher checkpoint remain unchanged.

These are agent checks with the fixtures/limits in the catalog. Full-route
difficulty, the player's presentation/fun verdict and actual DeSmuME frame pacing
remain unconfirmed. Moving trains and rideable loads remain deferred.


## v0.22.1 - 2026-10-17 - Creature texture sampling correction

Published through the normal playtest builder. Seven private model materials now
declare128x128 original dimensions, matching their shared atlas. The old64x64
values incorrectly magnified/cropped the painted UVs. Only those dimension words
and boot/Options labels change from immutable0.22.0; executable, audio, all
animation/contact resources and every room are byte exact. Sources:
`tools/creature_texture_fix.py`; two tests verify exact byte scope and rig/mesh
preservation. ROM SHA
`1613d74662c7dfa9d5166da0b8c8ed08ec048c605a7e9167edf3e320ac4d2a75`;
ARM9 `571d0d51090d427e024306b55a86728c7adcfda2068e8683c47e125c3eee5eb2`.

On the exact final ROM, all six full-HP isolated native-input duels clear with
contacts in all 18 species moves. Conductor executes all four moves after actual
damage unlocks Crownfall, then dies through native damage. These runs heal the
player and isolate rosters. Fresh boot/Continue from an earned copied battery
retains victory and returns to the cleared boss. The actual634-byte DSV and its
publisher checkpoint remain byte exact. Final24 focused checks pass after the
earlier418-test broad pass. Captured previews and machine receipts are in
`work/creature-forge` and `reference/creature_forge.json`. Player assessment and
actual DeSmuME performance remain pending.

## v0.22.0 - 2026-10-17 - Creature models, choreography and combat programs

Published, then superseded by the texture correction in0.22.1. ROM SHA
`69082fda16d7c0491f9bc945e6ebef11c526f7c7622a98a89959ea294b4f2eb2`.
The player accepted the map improvement but rejected0.21's enemy art, movement,
ordered stock attacks and oscillator voices. This pass replaces those layers.

- **Seven new textured meshes:** sculpted shells, split scythes, articulated
  claws/jaws/petals, fluted bell armor and the Conductor's broken crown. A
  shared UV-painted atlas supplies chitin, bone, brass, ceramic and luminous
  cores. Correct shoulder/elbow/wrist chains and longer creature proportions
  replace the elbow-targeted poses and rigid decorative limbs.
- **Authored contact programs:**22 moves have their own duration, contact
  volumes, windup, recovery, movement and impact cues. Crane gets the Maw's
  scissor/vault/feint, Ballast's dredger sweep/expanding rupture/hull charge,
  and Lantern's traveling seeds/recoil bloom/lance. Midnight gets Railcut,
  switchback rush and airborne shear; pendulum, peal and toll march; sweeping
  high/low arcs, capacitor bloom and twin bolts. Conductor adds Cadenza,
  Blackout fugue, Storm verdict and half-health Crownfall.
- **Motion throughout combat:**347 private routes include continuous wrist
  arcs, spine/head/digit follow-through, stance/swing gait, recoil, air hit,
  prone landing, supported get-up and death. Latent native air/strong attack
  routes also use the new choreography/contact data; rising retaliation has
  its own push-off and late claw strike. Ground pulses can be jumped; beams
  and bolts have visible lanes. Engine ground detachment starts actual vaults;
  a scoped secondary-state guard keeps their attack clips through airtime.
- **New recorded sound design:**57 mono22050Hz ADPCM assets layer creature
  growls, metallic cracks, rock, bells and electrical foley. Original CC0
  sources/licenses are preserved. Spawn alerts, attack tells, common hurt
  states, death and move-specific contact cues are wired separately. Old
  chapter vocal requests are muted; native world/combat foley remains.
- **Spacing and movement:**species approach/retreat at their own ranges and
  speeds, commit to descending a catwalk when the target is below, and close
  in for short-range moves instead of waiting forever at ranged distance.
  Freight Spore recovers from two narrow service pits through native-velocity
  walks/jumps, including retries after ceiling cancellation or landing.
  Native collision, gravity, damage, interruptions and physical rewards remain.

The accepted0.21 room resources, connections, roofs, doors and maps are exact.
Player abilities, purchases, ownership and the 32KiB kit are retained. Creature
HP is14/20/10 for Crane,12/18/10 for Midnight,80 for Conductor before the existing
room strength dial. Enemy counts/costs and chapter progress IDs remain.

Sources: `tools/creature_forge*.py`; tests `test_creature_forge`; machine receipts
and final qualification are recorded in TASKS and `reference/creature_forge.json`.
Red and Black defeat full-HP Conductor without refills; native save/exit/revisit
passes. Rendered audio proves new tell/contact/hurt playback for all six species.
Early frozen-clock, canceled-air-attack and ranged-spacing candidates were
rejected during emulator qualification, never published under this version.

## v0.21.0 - 2026-10-17 - Chapter combat and connection overhaul

Published through the normal playtest builder; final ROM and save verified. The
player subsequently rejected enemy quality; see0.22. Player
feedback rejected shared/native enemy patterns, missing reactions, reused
voices, invisible roofs/doors, bad room approaches and Midnight repetition.

ROM `60a974f33a3ca2f57dbe2cf11a7a12b585c172be8565cc0968301544b3a11340`,
ARM9 `0439571a1bf87182caf548bbc33cdc4ce1f867f09430c0541c4bb7b60c430fc3`.
Boot/Options0.21.0;128MiB. Sources: `chapter_renewal` tools and `actor_actions`.

- **Different combat rhythms:** six species and Conductor use private ordered
  attack/recovery programs: Maw strike/pounce/backhand, Ballast slam/double
  strike, Lantern double burst, Skitter repeated pounces, Warden strike/double
  slam and Arc Eye triple burst. Native movement, damage and interruptions
  remain. Every selected action is validated against that actor's actual XBD
  binding; no absent action can silently play Idle and freeze an attacker.
- **Full motion lifecycles:**347 private animation routes include distinct
  species attacks, movement, recoil, airborne reactions, actual prone
  knockdown/landing, get-up and death. Fast slam/pounce anticipation is extended
  to the real contact clock. Native rigs/models remain; poses, contact geometry
  and effect references are authored privately. No player abilities are added.
- **Distinct voices:**35 original synthesized samples are appended; private
  actor state entry reliably plays attack/hurt/death cues. Old creature vocal
  requests are silenced only inside the two chapters. Native impact foley and
  every other area's sounds remain. All six species' attack waves are observed
  in actual emulator mixes (correlation0.488..0.989); five-category authoring
  includes reserved alert/idle samples, not a claim all 35 are heard in play.
- **Ten-room Midnight circuit:** eight main-route rooms plus two save branches.
  Terminal, floodworks, turbine climb, observatory, sanctuary and Conductor
  form a readable loop with a victory return. Old room/save IDs retain recovery
  exits, off the new route/map. Room shapes, visible machinery and setwork
  distinguish the stops; the final wall-depth repair exposes pumps/turbines
  previously hidden behind back panels.
- **Roofs and doors:** real visible ceilings, framed/lit shutters and thresholds
  match collision. All Midnight shutters use X. Same-wall stacked Crane exits
  also use X at ground level, preventing an upper-hatch approach from entering
  the lower automatic exit. Port aisles are cleared; the wall-crawl channel is
  retained. Turbine's long final gap has intermediate landings. Maps/arrivals
  reflect the actual circuit, with short Objectives.
- **Preservation:** original creature/sound resources, exact 32KiB player kit, purchases, rewards and
  saved IDs remain. Latest634-byte DSVb800c4ec is protected by a content-addressed
  checkpoint; the prior0.20.0 ROM/composition is retained. The larger image and
  backward autoload copy provide space without rebasing the kit.

Validation: initial407-test broad run had only a startup-document-size failure,
corrected in the focused run; final renewal/document checks pass.52 directed
doors use native input after copied-save arrivals (foes parked/player healed;
Cargo Canyon follows its authored roof landings). Six full-native-HP isolated
species clears also observe at least three custom attack selections; those
combat drivers heal the player. Red and Black beat the full-HP Conductor without
refills, leave and revisit. Earned victory saves at Sanctuary, survives fresh
boot/Continue, and returns to a cleared boss with no flag/warp fixture. Final
room-model-only repairs inherit executable/physics/audio/creature controls by
exact asset identity; final Midnight traversal and visual combat are rerun.
Fun, average difficulty/duration and actual DeSmuME FPS await player feedback.

Evidence: `work/dual-rework/` door/combat/audio/save reports, visual-scope audit
and publication receipt; catalog `reference/chapter_renewal.json`. Failed
diagnostics are retained and do not qualify production behavior.

## v0.20.0 - 2026-10-16 - Midnight Line storm-terminal overhaul

Published through playtest in response to the request to remove sewer/Hive
recolours, author original places like Substation, introduce distinct creatures
and make the finale an actual combat encounter. Implemented and agent-tested;
player rejected animation/AI, connections and repetition on 2026-10-17; see0.21.0.

Release `4b4e739eb9e85699942afe29cb0f9e809d7f9302dcee9154e338717516139888`,
ARM9 `854b07a0e37faa49df3dd895df126aa4eb32e0243ca986190e0373aafe24f8b7`.
Stable ROM equals `build/version-0.20.0-final/Versioned.nds`; normal publisher
rebuild is byte exact. Boot/Options both show0.20.0. Cartridge remains64MiB.

- **Fifteen original areas:** rooms76..90 now use authored models, collision,
  materials, anchors and cameras: Storm Gate, Signal House, Midnight Terminal,
  Switch Tower, Skyrail Viaduct, Floodworks, Pump Refuge, Turbine Rise, Lightning
  Bridge, Capacitor Hall, Storm Observatory, Relay Sanctuary, Crown Approach,
  Conductor arena and Train Sheds. No cloned sewer/Hive room remains active in
  this route. Five Substation rooms remain. The storm panorama is original
  generated art in three continuous panels at far depth. Glass sheds/trains,
  turbine rings, suspended bridges, capacitor banks and stepped climbs provide
  distinct setwork. Turbine/Crown jumps use clear16-unit rises. Maps show the new
  geometry, door destinations and short Objectives; marked stacked hatches use X.
- **Original creatures:** Rail Skitter, Bell Warden and Arc Eye have new meshes,
  colour atlases and voices; Conductor has a separate crowned silhouette/voice.
  Native AI/rigs and shared full-lifecycle authored choreography remain. No new
  AI framework is claimed. Twenty original synthesized cues are appended;
  native and Crane sound entries/payloads remain intact. Private physical XP/HP
  rewards, finite patrols and upper encounters keep the route populated.
- **Actual creature finale:** Conductor takes normal combat damage. Its storm
  lanes warn before live arcs and escalate at half/quarter HP. Actual defeat
  unlocks both exits, stops scheduled hazards and persists on flag147; legacy246
  is also retained. Old completed saves can fight this replacement. No timed
  auto-victory, new skill, full-screen boss HUD, slow motion or player teleport.
- **Preservation:** exact 32KiB player kit, purchases/native abilities, accepted
  Crane room assets/code and saved room IDs/arrival IDs. Its shared area5 map
  count changes at Crane block+0x6DC; other Crane bytes remain exact. Three rebuilt saves
  plus Service Bay remain. Latest actual634-byte battery `3d21ee63` is byte exact;
  wrapper/snapshot roundtrips, prior ROM and compositions retained.

Validation:399 test cases covered by the broad394-case run (one document-size
failure corrected) and final focused29-case passing run. Final42 directed doors
pass via21 bidirectional cases. Every replacement room uses native movement;
the unchanged Relay upper doorway uses its established landing-position fixture,
so the full active-arc ascent is not qualified. Route enemies are parked/player
healed. Red and native-L-switched Black defeat the full-HP Conductor without
refills; exit/revisit, actual earned victory save/Continue and return to cleared
arena pass. Mixed full-HP Terminal crew clears all three species and collects72
XP with player healing explicitly enabled. Separate idle1HP reward controls use
no healing/position writes: each species physically collects XP6 plus1024/2048
Q12 HP before the driver ends; these are partial pickup receipts. Paired zero
reward gives0/0. Death IDs599/604/609 and waveform matches prove original voices
render. Signal Leech warning/live damage and save controls remain valid through
audited runtime/effective-asset identity. Final UI/art reviewed.

Evidence: `work/midnight-rework/publication.json`, scope audit, door manifest,
audio/reward/save reports and `chapter-preview.png`; machine catalog
`reference/midnight_rework.json`. Agent controls do not establish player fun,
difficulty, average duration or emulator frame rate. Current source composition
uses 2188/2560 new runtime bytes; native texture allocation stays below 128KiB.

## v0.19.0 - 2026-10-16 - Crane Row rework

Comprehensive response to the player's rejection of 0.18.0: recognizable enemy
reactions/shared voices, missing rewards/death tint, sparse saved revisits and
cluttered text/coarse repeated art. Published through playtest; implemented and agent-tested. Player acceptance
is pending.

Release `9b2b948f6030a60246a0ca9ae477ae51c22f4aa349645fb2c6cef367c4557582`,
ARM9 `9b04b02a74cd634901c1435a5bb7708c073c127467cc9971b3bc9a5d1c6a10e3`,
`build/version-0.19.0-final/Versioned.nds`. Boot and Options both display0.19.0;
normal composition is byte-exact. Crane code uses 7864/8192 bytes; max365 room quads.

- **Creature identity:** revised Maw/Ballast/Spore silhouettes and 154 authored
  animation routes, covering movement, attacks, bound/hurt/air reactions and
  deaths. The earlier47 routes left recognizable native reactions. Native rigs
  and AI framework remain. Texture-based face colour allows the engine's native
  hurt/death tint to show; baked per-face GPU colour had hidden it.
- **Original sound:**15 deterministic synthesized alert/attack/death/hurt/idle
  voices. Scoped native sound routing selects them only in Crane rooms; Spore
  gets explicit native state-entry cues because its chassis emitted no voice
  request. All 582 original sound entries and unrelated files remain exact.
- **Real rewards:** cloned enemy configs had copied a zero reward-set field.
  Private set31 now uses native physical XP/HP orbs,10..12 XP and small health
  rolls. It preserves native LP behavior and does not directly credit stats.
  Reward controls disable player healing and measure actual currency at+0x44.
- **Pressure and coverage:** persistent cleared crews retain callback-free
  patrols; Engine/Shaft/Breakwater gain encounters. Main crews use 12 total/4 live
  spawn-cost units; patrols8/4. Upper Quay/Shaft/Gantry use a bounded4/2 central
  wave; global live-cost ceiling4 stays intact. Spawning reaches roofs/shelves,
  and Quay gains a suspended upper combat loft. Office/Cache remain safe.
- **Cleaner presentation:** outdoor destination/action boards and first-visit/
  clear speech bubbles removed. High hatches retain one small X; the Engine
  lever gets a painted bolt. Maps show a short current goal, landmark icons,
  actual connections and loop letters. Route details stay on Objectives.
  Fine low-contrast deck/steel/cargo/wood replace coarse repeated patterns.
  Original painted harbor panorama has three continuous panels at far depth;
  source and built-in ImageGen prompt/provenance are in reference/art.
- **Preservation:** exact frozen Red kit/strength dial and Midnight block;
  native assets retained outside owned Crane resources/version text/audio
  additions. Existing doors/trigger records remain exact. Collision remains
  exact except the added Quay loft. No save ownership migration or paid grants.

Validation:387 automated tests;9 expanded adapter/driver/reward regressions;
30 Crane real-door cases;13 Midnight native routes;11 arrival/revisit patrol
probes;8 power/cache/save/safety and Red/Black no-refill hoist controls. All pass.
Native-HP mixed Freight fight damages all 3 and earns its actual clear callback
(XP1850->2028). Separate Dry Dock/Crown controls earn their callbacks and Crown
opens its shortcut. All three isolated native kills collect10XP and 1024/1024/
2048 Q12 health for Maw/Spore/Ballast; paired zero-set real kill awards0/0.
Private voice calls and recorded PCM waveform matches establish all three death
sounds render. Four goal/Objective phases and final Quay/Engine/native Pier UI
visually reviewed;65 prior art poses inherit through exact art bytes.

Stable publication matches the qualified ROM exactly. Latest634-byte battery
`3d21ee63` and DSV wrapper remain byte-exact; its lossless checkpoint, prior ROM
and compositions are retained. Player continues through the usual launcher.
Final receipts: `work/crane-row/rework/publication.json`; research and explicit
lab limitations in TECHNICAL. The natural-HP mixed fight heals the 60-unit lab
player; separate callback and reward controls cap foes. These do not establish
encounter difficulty. No frame-rate or player-fun claim.

## v0.18.0 - 2026-10-15 - Original Crane Row creatures

Player found the Pier enemies weak/boring and explicitly requested entirely new
creatures with new attack animations. Crane Row now has three original shipyard
mutations and tougher mixed encounters. Published through playtest; implemented
and agent-tested. The player rejected its creature identity, rewards, density
and presentation;0.19.0 responds to that feedback.

Release `f6d09cfcc41f76a3484648b828755a52726f5378f936fee3faa0640b9461930a`,
ARM9 `805460f9bcdccdc5d0c7ad674fd6270640b3fa26519d1a6bee74db7fd107f87e`,
`build/version-0.18.0-final/Versioned.nds`; normal composition is byte-exact.
Boot and Options both display0.18.0.

- **Mooring Maw:** low four-limbed predator with four eyes, paired jaws, claws,
  spines and tail. Authored scuttling, claw attacks and leap prep/pounce replace
  the old silhouette and attack poses. Natural leap selection is traced during
  the production mixed fight.
- **Ballast Beast:** asymmetric armoured claws, shell spines and forked tail,
  with new sweeps, charge and two-arm slams. Its fast slam has a clearer windup
  inside the same native17 samples. It takes real combo damage with both suits.
- **Lantern Spore:** hovering bell/core and tentacles, with new casting and
  melee motion. Its ranged attacks land in native story-context controls.
- **Mixed pressure:** main crews use 8 total/4 live native spawn-cost units,
  admitting all three types together (costs1/2/1 for Maw/Ballast/Spore).
  Patrols use 3/2 and the hoist opens with one Maw. Nominal HP10/14/7 is applied
  before existing room scaling; these numbers are not attack damage.
- **Original authored assets:** three models and 47 SCA routes, including31
  attack routes, use preserved native rigs/AI/controllers and defeat callbacks.
  Models fit a conservative6144-vertex crowd budget. Original actor resources
  and config tables remain intact; appended groups/private records are selected
  only in rooms96..107.
- **Progress compatibility:**0.17.0 geometry, doors, maps, locks, earned clears,
  native abilities/purchases, kit/dial and Midnight block remain exact. Existing
  crew clears stay earned; repeatable patrols and uncleared encounters use the
  new roster. No save migration is required.

Qualification on the exact release:374 tests, all 30 Crane door cases, all 13
Midnight routes, three native crew callbacks, Red extra-kit/Vitality and Black
Vitality no-refill hoist wins with cleanup/exit/revisit, plus a production mixed
fight with all three species concurrently (max4 live) and real defeat callback.
The mixed fight heals Spidey, retains native enemy HP, and uses native inputs
without actor placements. Four uncapped-health duels on C carry through proved
C->D mesh-only equivalence: every gameplay/config/motion/event/texture byte is
exact, with only the Maw/Spore meshes trimmed. Duel healing proves contact,
combo and defeat compatibility; it does not establish encounter difficulty.
Seven prior native-input terrain routes inherit through exact room bytes.
Player fun, full-chapter duration and frame-rate remain unmeasured.

Latest actual battery `ac9896ff` is byte-identical before/after publication,
DSV wrapper/checkpoint verified; prior0.17.0 ROM and prior/active compositions
retained. Evidence: `work/crane-row/creatures/publication.json`; source/catalog:
`tools/crane_creatures.py`, `crane_creature_art.py`, `crane_creature_motion.py`,
`crane_creature_lab.py`, `actor_resources.py`, `reference/crane_creatures.json`.
Player flow remains `Play Spider-Man.cmd -> Continue`.

## v0.17.0 - 2026-10-15 - Crane Row terrain and encounter overhaul

Player finds the partly explored district boring and bland; the hoist has not
been played. This overhaul makes the journey itself more active: substantial
cargo routes, a playable ship, broken spans, vertical movement and varied crews.
Published through playtest. Implemented and agent-tested; player verdict pending.

Release `c5fc05127ca98923ca01b35b7f2bd686e30bdece821fd07d97b5b6fb03841dfa`,
ARM9 `51c8273fa174eac3527ebbf2cf66a50be707640a972c01e5874081baebecaf22`,
`build/version-0.17.0-final/Versioned.nds`; normal composition is byte-exact.
Boot and Options both display0.17.0.

- **Broken waterfront routes.** Quay, Freight, Warren, Gantry and Breakwater
  have segmented docks/platforms above solid maintenance decks. Missed jumps
  lose height rather than falling into a death pit. Cameras/detail maps cover
  the lower levels. Quay starts the district with suspended cargo landings.
- **Cargo rooftops.** Freight gains a complete rising roof express over its
  fight deck; Warren's tall solid container stacks, intermediate steps and
  hanging platforms replace the repeated low-crate course. Upper cargo barrels
  give the optional route something to find and smash.
- **Board the ship.** The Dry Dock vessel now has real deck/hull collision,
  dive-through hold openings and upper rigging platforms. Rust/navy hull art,
  windows, rails and rigging follow the playable architecture.
- **Climb the crane.** Counterweight becomes a switchback climb around the
  existing scenery mover; Gantry becomes a fractured bridge with lower service
  landings. Crown has a broad raised combat stage and upper launch platforms.
  The Long Arm approach gains stepped machinery and overhead platforms; its
  final fighting pocket, native hoist models/HP/attack cycle remain unchanged.
- **Different fights.** Dry Dock uses the native Sewer0x0E crew; Gantry uses
  Residential0x0C. Crown's Pier crew calls one bounded hunter reinforcement,
  and the second real defeat callback earns its clear/shortcut. No timer can
  award victory. Native throwable barrels populate the principal arenas.
- **Progress compatibility.** Existing room IDs, door connections/spawns/input
  modes, locks, visits, purchases, crew clears, cache, lever and save checkpoint
  remain valid. Previously cleared crews stay cleared. The complete kit/dial,
  Midnight block, native assets/mission/ownership code and overview/goal screens
  remain exact; no new skill, stat balance or slow-motion effect is introduced.

Qualification:357 unit tests, all 30 Crane door cases, seven complete native-input
terrain routes, all 13 Midnight routes, six lever/cache/save/hazard controls,
three native crew callbacks, and Red extra-kit/Vitality plus Black Vitality III
no-refill hoist victories/cleanup/exit/revisit pass on the exact final ROM.
Midnight Span needed one retry; its earlier failure remains recorded. The Crown
chase fixture twice waited outside the reinforcement zone after the first crew;
returning into the arena with native D-pad input fixes that driver stall without
changing game waves. Failed reports/RAM and earlier terrain/controller trials
remain in `work/crane-row/overhaul/`. Crew checks use 1HP enemies/chase placements;
they establish callbacks rather than difficulty. Movement routes use native
inputs after room arrival, parked enemies and bounded live destination checks.
Visual
review covers twelve rooms: eleven retain exactly the reviewed J model/texture
bytes, and the repaired Long Arm is recaptured on K. Models remain below the
existing400-quad budget (largest370), with texture/palette and lossless
model/texture/BSP/OBJ checks. The box compiler also gains a regression-tested
terminal encoding for valid adjacent solid cells; native parsers stay lossless.
Player fun, full exploration duration and actual frame-rate remain unmeasured.

Publication proof: `work/crane-row/overhaul/publication.json`. The latest actual
battery `ac9896ff` is byte-identical; DSV wrapper/checkpoint bytes are verified.
Previous0.16.3 ROM, prior/active compositions and progress are retained. The
stable launcher ROM matches the qualified candidate exactly.
Another24 post-publication release/document/capacity/lab checks pass; the stable
ROM, latest battery and unique release-history record were rechecked afterwards.

## v0.16.3 - 2026-10-15 - Crane Row map connections and next-action guidance

Published through Play Spider-Man.cmd. ROM SHA256
`18c90eb829f4ec9f116d3fde269ba73c88eafc69e15bbbfc105ad1398b09d494`;
ARM9 `2dea0314...`. Normal composition reproduces the exact qualified ROM at
`build/version-0.16.3-qualified/Versioned.nds`. Boot/Options both display0.16.3.
Latest player battery `ac9896ff...` remains byte-identical, with lossless
wrapper/checkpoints and prior0.16.2 ROM/prior/active compositions retained.
Agent-tested; player verdict on this navigation repair is pending.

- **A map that follows the actual doors.** All twelve rooms have names,
  connections leave the correct sides, and drawn routes avoid false crossings.
  Matching A..D endpoints identify longer loops/shortcuts; P identifies the
  Pier. The Office save marker is legible. Detailed room maps now label each
  door destination and identify upper X hatches.
- **A visible next goal throughout the chapter.** Map headers and amber goal
  borders advance from cargo power to the Crown crew, hoist and return to Pier.
  Red endpoints identify locked routes. Native current/visited colours remain
  distinct, and the dim unvisited plan gives route context. Objectives now
  explains the current Crane route/action instead of showing the sewer mission.
  Earned save flags select both pages without changing native mission progress.
- **Door purpose beside its destination.** WALK IN/X ENTER, shortcut, save-room,
  optional-cache, hoist and return boards explain the input. Local first-visit
  and lock hints explain what unlocks a route and where to go next. Crane hints
  clear after five native seconds, restoring the map while play continues;
  the lever refreshes its next goal without leaving the room.
- **Progress and gameplay preserved.** No migration/new paid moves or balance
  changes. Kit/dial and Midnight code are byte-exact to 0.16.2. All collision,
  door destinations/input modes, spawns, anchors and cameras remain exact.
  Encounter logic is unchanged apart from messages and first-visit selection;
  moved entity callback indices resolve to the same named groups. Two scoped
  native UI adapters preserve other rooms/areas and native Objectives fallback.

Passed:352 full-suite tests,37 navigation/build checks,19 post-probe/document/
release checks, then10 post-publication metadata checks; all 30 Crane real-door
cases with live arrivals, all 13 Midnight
routes (Signal entry needed one rerun), and eight gameplay controls. All 29 exit
boards/12 detailed maps/four map-and-Objectives phases/native UI fallback were
reviewed in emulator captures. Real lever -> Office save -> fresh native
Continue restores the earned power goal. Red extra kit/Vitality and Black
Vitality III win without lab refills and pass cleanup/real exit/revisit.
Initial lab failures are retained: the probe counted a freed actor/motion as
another player; validated controller ownership now disambiguates it. Partial
sample logging and live-arrival waits were corrected without changing ROM bytes.
Exact kit/native combat contracts retain prior68-kit/12-crash evidence; those
batches were not rerun on this ROM. Held poses prove rendering, real-door cases
prove traversal. Full-chapter duration, performance and player feel remain
unmeasured. Evidence/preview/publication proof: `work/crane-row/navigation/`,
especially `publication.json`, `audit.json` and `preview.png`.

## v0.16.2 - 2026-10-15 - Visible Crane Row exits, roofs and destinations

Published through the normal Play Spider-Man.cmd setup. ROM SHA256
`1bd288f171d0cc58fc94190a68bb52a9752ff59a9636bea376eb3608d04ea139`.
Qualified composition: `build/version-0.16.2-qualified/Versioned.nds`.
Latest battery `54417ed4...` remains byte-identical, with wrapper/snapshots
verified; prior0.16.1 ROM and prior/active compositions are retained.
Player reported major improvements in0.16.1 but invisible exits/ceilings;
the player subsequently confirmed visual improvements, then prioritized map
connections and next-action clarity (addressed in0.16.3).

- **Visible exits throughout the district.** All 29 Crane shutters now face
  the room, correcting back-face culling. Recessed steel jambs and a lintel
  lamp make each doorway legible from either approach. High hatches retain X;
  ground exits keep their walk-in behavior.
- **Visible ceilings and finished upper corners.** Nine formerly hidden
  ceiling shells gain steel undersides at their actual collision boundary.
  All 12 rooms receive roof fascia, hazard edging and flush trim. World-scale
  texture repeats avoid giant flat patches at upper corners.
- **A destination at every exit.** Labels follow the actual links, including
  Freight's Engine House return. Compact boards clear stacked Engine House
  landings and Crown's low platform; their depth clears Warren cargo and
  Engine pipes. Old floating bars, overlapping Office text and duplicate signs
  are removed; Quay's district sign moves clear of the Pier label.
- **Existing gameplay remains exact.** The only changed resources are the 12
  Crane model/texture pairs and English/American version labels. ARM9
  `abfbb112...`, all BSP/OBJ, doors, anchors, cameras, scripts, maps, native
  assets and kit are byte-identical to 0.16.1. No enemy, purchase or balance
  changes. Boot and Options display0.16.2.

Passed:342 full-suite tests,25 targeted tests,10 document/release checks,
11 post-driver checks, all 30 Crane real-door cases and 8 gameplay controls,
exact-byte scope/version audit, and 65 reviewed emulator poses (29 exits/36
roof-and-corner views) covering all 12 rooms. All 13 corrected Midnight routes
pass on this exact ROM (Signal entry needed one rerun). The old Span masher
stalled at its native12-unit neck on both
0.16.1 and this ROM; native duck/roll inputs pass the full route on both.
No ROM change for that lab correction; original failures are retained.
Red extra kit/Vitality and Black Vitality III beat the hoist without lab health
refills and pass post-win cleanup/real exit/revisit. Office native save/Continue,
power, cache and warning/live/refuge controls pass. Exact executable/collision/
kit inheritance retains prior68 kit/12 crash/native parity evidence. Held poses
prove rendering; real-door routes prove traversal. Performance, first-visit
duration and player feel remain unmeasured. Evidence/preview and exact
publication/save proof: `work/crane-row/repair/publication.json` and its folder.

## v0.16.1 - 2026-10-14 - Crane Row visual and readability sweep

Published through Play Spider-Man.cmd. ROM SHA256
`5b0d6f552ac0da040ce0ee3f6a650e2b629614a9b73ea56ddbadc062efef705e`;
ARM9 `abfbb112...`, byte-identical to v0.16.0. Boot and Options both show
0.16.1 in English/American. Latest battery `3a4e7c9b...` is byte-identical,
with wrapper/checkpoints verified; prior ROM and both compositions retained.
Agent-tested at release. Subsequent player feedback confirmed visual
improvements but reported invisible exits/ceilings;0.16.2 addresses those.

- **All twelve rooms receive an art pass.** Original riveted steel, deck,
  hull, water, lamp, amber girder and sign textures; lattice cranes with
  cabs/cables, boats, ship superstructure/windows, cargo fittings, power
  pipes and shaft bracing. Three broad Pier skyline pictures form a single
  harbor panorama rather than small repeating city tiles.
- **Clearer routes and landings.** Steel catwalk lips, rear rails and
  underside supports; signs for the office, power, gantry, Crown, cache and
  hoist; shorter objective hints. Softer deck highlights keep actors legible.
  The office gains warm walls, a desk and chart board; the finale retains
  clear warning pads, exposed motor and green refuge marks.
- **Exact gameplay compatibility.** Only the twelve visual models/texture
  archives and two language string files differ from v0.16.0. All executable,
  collision, objects, cameras, anchors, doors, encounter scripts, maps, machine
  models and unrelated assets stay exact. Kit, native controls, purchases,
  prices and progress are preserved.

Validation:339 full-suite tests, then30 targeted checks after correcting the
Roof lab driver; all 30 Crane door cases and all 13 Midnight routes pass on this
exact ROM. Signal entry needed one rerun. The former Roof gather helper left
fighters below melee range; the corrected fixture leaves enemy movement native,
keeps its player chase away from doors and settles after earned victory. It
also passes on v0.16.0; no ROM behavior was changed for this driver correction.
Red with purchased extra kit/Vitality and Black with Vitality III beat the
hoist without lab health refills, then pass cleanup/exit/revisit. Native health
gains remain allowed. Office save/Continue, lever, cache, harmless-warning/live
damage and measured refuge controls pass. All twelve rooms and extra elevated
views were inspected in emulator captures. Performance, first-visit duration
and player feel remain unconfirmed. Evidence and before/after preview:
`work/crane-row/polish/`; exact publication/save proof: `publication.json`.

## v0.16.0 - 2026-10-14 - Crane Row: The Hanging Harbor

Published through the usual Play Spider-Man.cmd setup. ROM SHA256
`39fcf89e46487e4cc80eed7414871891e6f0ca1a21ed86d4e3f26844f095d299`;
ARM9 `abfbb112...`. Boot and Options both display0.16.0 in English/American.
Agent-tested; player feel and first-visit duration remain unconfirmed.
Latest battery `3a4e7c9b...` is byte-identical; wrapper and snapshots verified.
The previous v0.15.1 ROM and both active compositions are retained.

- **Twelve authored rooms:** Quayside, Freight Exchange, Harbor Office,
  Container Warren, Dry Dock, Engine House, Counterweight Shaft, Gantry Spine,
  Winch Cache, Crane Crown, Long Arm and Breakwater. Outdoor rooms reach
  360..420 units wide; the shaft rises224. Original geometry, container
  routes, a supported ship hull, crane silhouettes, dock lighting and distant
  city/water layers give the branch its own architecture.
- **Connected district:** a new right exit in Pier_Save02, native Office
  checkpoint, cargo-power lever, maintenance return, Crown descent, optional
  native smashable stash and victory return to Quayside. Upper hatches show
  X markers; ground doors remain walk-in. A local overview and detailed maps
  cover the district. Native story routes/ability gates remain intact.
- **Long Arm:** a moving grabber commits to a warned lane, slams or sweeps,
  then exposes one motor. Native animated hit geometry supplies actual melee
  damage; protected motor HP is guarded. Green floor marks tested safe
  positions. Supporting enemies spawn during the opening burst; surviving
  adds can remain after victory, while hazards/future spawns stop and the
  exit opens. The shaft counterweight moves behind fixed traversal landings;
  it is scenery rather than a rideable platform.
- **Integration:** rooms96..107, area6 and private persistent flags live in
  an independent8KiB extension. Midnight's4KiB block and every unrelated
  resource stay exact. Existing kit, native A/B, purchases, dependencies,
  prices and save progress are preserved. No new skills or time slowing.

Validation: 332 unit-suite checks plus3 health-window tests; all 30 Crane and
13 Midnight real-door cases;12 crash seeds. Full68-kit regression passed
before the final hoist refinement. Final native gate/snare/Black controls
match that baseline; an equivalence audit proves only the hoist's three
resources/owned adapter storage changed, with unchanged collision/maps/doors
and kit. Final gateway execution tests cover native fallback arguments in
every other room/kind combination. Red with purchased extra kit/Vitality and
Black with Vitality III win without lab health refills. Native health gains
are allowed and measured separately. Actual victory survives Office save/
reload; warning/live damage, safe coordinates, guard, return and revisit
controls pass. Evidence: `work/crane-row/`,
`work/area-research/crane-*.log`, `work/kit/v0.16.0/qualification.json`.
Native health-orb recovery resumes play without granting victory. Exact
publication/save verification: `work/crane-row/publication.json`.

## v0.15.1 - 2026-10-14 - Clearer Signal Leech/Substation and smoother Vortex

Published to the usual Play Spider-Man.cmd ROM. SHA256
`160d01cbda3320bc2c70eb2ab55359263e4b64272808e2d1fde9a704296de44c`;
ARM9 `117c9f7c...`, kit ARM9 `02f85aa3...`. Boot and Options both display
v0.15.1 in English/American. Latest battery `3a4e7c9b...` stayed byte-identical;
DSV wrapper/snapshots verified. Prior v0.15.0 ROM and both active compositions
are retained. Agent-tested; revised player feel remains unconfirmed.

- **Signal Leech:** each native smashable core now has a bright pink/white
  beacon that disappears through that core's destruction callback. Break
  any core in any order. Native core hit geometry/health and victory
  persistence are retained. Suspended shelves are removed, leaving a flat
  arena. Green floor marks permanent safe gaps; yellow lights illuminate
  the incoming powered strip below the targets, then blue arcs become
  damaging. Warning lead is longer and two arcs replace three per lane.
  The tall entrance bulkhead still blocks a jump/swing past the seal.
- **Substation:** brighter construction surfaces/undersides replace dark
  cutaway or repeated light tiles. Control Roof entrances have visible
  roof caps. Distant skyline bases are darkened to remove stretched neon
  columns. Detailed maps follow the revised geometry.
- **Vortex:** **Y, Y, Down+Y**, then release Down and keep pressing Y.
  Old pause and Dragnet-yank entries remain. Whip/return lash, double lash,
  double lash, slam provide seven contact opportunities. Authored arm
  follow-through and matching loop poses smooth the joins. R retains the
  web steps through the dodge/landing; an active owned Vortex prevents
  native Drill Kick from stealing the resume. Up/A/B retain their exits.
  Plain strings, Black/unowned behavior, purchases/prices and ownership
  dependencies are preserved. No skills added, teleports or time slowing.

Validation: 311 unit tests, 68 kit checks, 12 crash seeds and all 13 real-door
routes passed. The Signal entry route needed one retry for a lab predicate
that read an absent position; its corrected stable-pose run also passed.
Red and Black each won without health refills. Boss flow/seal/victory/revisit
and native save/reload passed. Each green control held 1,440 captured frames
without HP loss; the warning was harmless and the live lane removed 6,656
Q12. Evidence: `work/kit/v0.15.1/qualification.json`,
`work/kit/cleanup-{units-final,crash}.log`,
`work/midnight-line/walk-all-160d01cb.json`, `leech-*`,
`cleanup-publication.json`. Source/clock/preview lessons are in TECHNICAL.

Limits: seven strikes are contact opportunities, not guaranteed HP drops
or combo-gauge counts. Maps remain static apart from the player marker.
Actual DeSmuME performance and the revised feel need player feedback.
Native OBJ timers run in delay units: the unchanged 300-unit breaker
measures about ten seconds, correcting earlier five-second descriptions.

## v0.15.0 - 2026-10-13 - Substation checkpoint, detailed maps and Roof wave fix

Published through Play Spider-Man.cmd's usual ROM with DeSmuME closed. SHA256
`f0e53056f04bc498dc253a1ded5ca854c0f94535f7cf7f27313d099ff9c06ae9`;
ARM9 `f4b5fdc9...`, kit ARM9 remains `ccd7f003...`.
Latest battery stayed byte-identical (`f9edc1cd...`); its wrapper/snapshot
verified, and v0.14.0 plus the prior active composition were retained.
Agent-tested; player verdict pending.

- **Service Bay checkpoint:** a quiet maintenance room off the Switchyard's
  upper-left fire escape. Jump from the dock to the ledge and enter the
  left door. Native save sphere supplies Save, Upgrades and Test Upgrades.
  Continue restores Spidey beside the sphere. No new abilities required.
- **Five detailed maps:** Switchyard, Relay Hall, Control Roof, Signal Core
  and Service Bay now show their actual layouts in the detail view.
  Platforms, doors, electrical hazards, core locations and checkpoint are
  marked, with the native player marker. The chapter overview gains the
  bay's save icon and branch arrows.
- **Roof wave stall:** a defeated NormalEnemy could retain a non-null weak
  reference and active spawn cost forever. A small router scoped to room 93
  sends zero-HP enemies through native list cleanup. Living enemies keep
  the wave active; there is no automatic timed win. The next crew can start
  before the last corpse finishes fading, with the existing 45-frame gap.
- Kit, prices, purchases and boss behavior remain unchanged. Research
  fixtures now validate motion ownership, avoid chasing across Roof exits
  and retain RAM on an aborted walk. The boss driver steps off a shelf
  before attacking a ground core; this changes lab inputs only.

Validation: 300 unit tests, all 13 real-door routes, new checkpoint native
save/Yes -> fresh Continue, map/player-marker captures, reproduced stalled
wave -> fixed stress pass, living-crew/no-victory control. Boot and Options
use v0.15.0. Kit code is identical to the v0.14.0 qualified kit; its 63 checks
and crash qualification carry forward. Boss flow passed: full core health,
physical seal, actual victory, exit and cleared revisit (Spidey kept alive).
Evidence: `work/midnight-line/service-qualified-*`, `roof-live-final.log`,
`walk-substation-roof-fixed-f0e53056.json`, TECHNICAL checkpoint/map section.

Limits: the spawner stall is reproduced in the agent lab, not player-confirmed.
Map landmarks are static; only the native player icon moves. Actual DeSmuME
performance and human pacing remain for player feedback.

## v0.14.0 - 2026-10-13 - Signal Leech, the Midnight Line machine boss

Published through the usual Play Spider-Man.cmd ROM, with DeSmuME closed.
SHA256 `7cb3933889c1185acf3d60fceebf155dbeed7e08bda90eb21193e5bcc1f40fc0`;
ARM9 `f0f82245...`, unchanged kit ARM9 `ccd7f003...`. Boot and Options show
v0.14.0. The actual battery stayed byte-identical (`f9edc1cd...`), its DSV
wrapper round-tripped, and v0.13.0 plus the prior active composition were
preserved. Agent-tested, not player-confirmed.

- **Signal Core, room 94:** a new left passage from the Control Roof leads
  to an original machine arena with a far skyline and landing shelves. The
  Roof keeps its repeatable waves. The chapter map shows the new boss, and
  the Refuge points to it after the Nest.
- **Signal Leech:** three visible infected cores, 12 health units each,
  remain hittable throughout. Destroying them advances three pressure
  phases and then permanently disables the fight after normal saving.
  Actual Red and Black attacks work. The machine does not use a native boss
  health bar or require a paid move.
- **Warned electrical lanes:** original yellow panels flash before steady
  live arcs. Warnings are harmless. Single lanes become pairs, always
  leaving a safe route, then outer/middle alternation. Three bounded strong
  crews provide combo targets; health/damage use the Roof's dial.
- **Emergency breaker:** X buys a one-use five-second power cut. Power
  returns through another warning. Victory shuts down arcs/future spawns
  and opens the seal immediately. Living enemies can remain until exit.
- Native controls, purchases, kit clips, slow-motion settings and story
  abilities are preserved. Native near-death recovery continues the current
  attempt with partial core progress. Fresh pre-victory entry resets it.

Validation: 293 unit tests, 63 kit checks, 12 crash seeds, all 12 real-door
walk routes, tour, power puzzle and save/Continue passed. Red and Black won
unweakened boss runs without player refills. Actual victory -> Refuge save
-> reboot/Continue -> cleared boss revisit passed with copied SRAM. A
physical seal check after the nearest core was destroyed, harmless/live HP
comparison, native near-death recovery and guarded scheduler tests passed.
The Roof route needed one retry for its known wave stall. Final help/map
polish has identical gameplay code/assets to the qualified candidate; only
map colour-slot ARM9 bytes differ (`final-equivalence.json`). Map source
colours are protected, and all-visited colours were checked in the emulator.

Limits: a minimal-purchase, six-health-unit driver broke two cores then lost
after rushing overlapping crews. Player difficulty/readability and actual
DeSmuME/JIT12 performance remain to be confirmed. Props do not acquire the
kit's enemy-only Perch/Dragnet targeting. Evidence: `work/kit/v0.14.0/`,
`work/midnight-line/leech-*`, `leech-publication.json`; implementation and
reproduction details are in TECHNICAL "Signal Leech implementation".

## v0.13.0 - 2026-10-13 - Three web skills (Overclock, Dragnet, Vortex) and a tougher, better-looking Substation

Published through Play Spider-Man.cmd's stable ROM (DeSmuME closed; the build does not touch the battery). SHA256
`75faa3ff7759f29212b6c92c6d9d0859298a23c13d228df73c798adef032cb9d`
(ARM9 `db091184...`, kit ARM9 `ccd7f003...`).
Title and Options show v0.13.0. Player (2026-10-13), on v0.12.0: "super
impressed with the original artwork", but the background "looked like it
was a painting rather than real", "some roofs were pure pitch black" and
"the enemies were too weak though is my main gripe"; of the web ideas:
Overclock, a new web-focused ground string, and webbing about five enemies
at once with Y to throw them all toward Spidey. "Only these 3 more and no
more skills."

Three new rows at the end of the Red list (Upgrades at a save point; scroll
down past Momentum). Nothing is granted: each is bought with XP, can be
refunded like any other, and works in the red suit only.

- **Overclock** (400 XP). Passive. While the combo meter is at tier 5, every
  hit you land also fires a web shot at the nearest other standing enemy
  within about a screen: he staggers and loses half a health unit, and a web
  line flashes out to him. One shot per hit; the same enemy at most about
  twice a second.
- **Dragnet** (500 XP). Web an enemy with A as usual, but **keep A held**:
  after about 0.4 s up to four more standing enemies in front of you (within
  48 units, on your level) are webbed too, each on a line of his own, in the
  game's own cocoon. A tap of A is still the single web. From that hold:
  - **Y yanks all of them**, the first one included: they fly to you and
    land in a pile 6 to 10 units in front of you (half a health unit each)
    while Spidey heaves the lines back with a back hop. Press Y again and
    Vortex continues from there (if you own it; otherwise the base string).
  - Anything else works as before for the first enemy (A again lets go, Up
    is Skyjack, a jump leaves) and the others simply stay webbed where they
    stand until they break out: walk up and hit them.
- **Vortex** (500 XP). A third ground string: **Y, Y, pause, Y, Y, Y**. The
  pause is the same idea as Split Decision's, one hit later: let the second
  hit finish so Spidey is back on his feet, then press Y (the window is
  about half a second). Three steps with new animations: a spinning web
  whip, a hopping double lash, and an overhead slam that knocks everyone
  away. Each hit also lands on every enemy within 14 units on either side
  of you, in front and behind, and a web line flashes to each one. R cancels
  and resumes it like any string; A still Web Rushes out of it. A fast Y, Y,
  Y, Y is unchanged, and so is Y after an R cancel.

**The Substation** (rooms behind the door at the far left of the Yard):

- **Stronger crews.** Enemy health is 2.25 times native in the Switchyard,
  2.5 times in the Relay Hall and 3 times on the Control Roof, and they hit
  1.4, 1.5 and 1.6 times as hard. The Yard on the way there, which has the
  same early-story gang, is 2 times and 1.3 times (the agent's addition: say
  so if the Yard should go back).
- **Backgrounds.** The two skylines no longer hang on the back wall. They
  stand far behind the rooms, the way the original game places its own, so
  they are small, distant and drift slowly as you move; above them the sky
  continues instead of ending in a straight edge.
- **No more black patches.** Where a catwalk or a block met a wall there was
  a strip nothing was drawn on (pure black); those are filled. Doorway
  ceilings were a near-black texture and are concrete or steel now; ceilings
  and the faces turned toward you are lit a little more; the Relay Hall's
  door walls are no longer flat dark slabs; the Switchyard dock is concrete
  with a warning stripe on its edge instead of one huge striped block.

How: the second kit block gains a web block (`tools/tasm_kit2.s`): the
game's own WebLine actor spawned and tied to enemies by the kit, hits built
from nothing with a chosen kind and damage (hold 0x22, yank 0x21, stagger,
knockdown), one hook where Y is tested in the web hold, a string without
table nodes for Vortex, four authored clips (`tools/kit_clips.py`). Ability
bits 80..82. Room compiler: fills, open back-wall panels, far backdrops
(TECHNICAL "Web lines, built hits and the web skills", "Room compiler",
"The Substation").

Agent-tested on this ROM, not player-confirmed:
283 unit tests; kit qualification 63/63 (15 new checks: Dragnet webs the
three enemies behind the first, the yank plays the heave, brings all four
within 14 units and continues into the three Vortex steps, the lines let
go, A again leaves them webbed, unowned is native; Vortex from the pause,
its damage and knockdown, unowned and a Reflex resume keep the native third
hit, area hits on Brutes 9 and 12 units away; Overclock fires at tier 5,
not at tier 4, not unowned); crash hunt 24/24 fights (the fights now also
hold A, yank, release and pause; odd seeds at tier 5); 10/10 walk routes
on the first try, the roof's three waves at three times health included;
the door tour (steps 0..18, then 19..37: it stops at the Nest Span ambush
as it did for v0.11.0), the power puzzle, save and Continue in the Refuge;
the shop run for the three rows (buy each, refund Vortex: 400, 500, 500 XP)
and the Vitality shop run. **Found by the crash hunt before release:** the
first candidates hung whenever Dragnet's lines were dropped without a yank
(the assembler had encoded one conditional call as a branch to itself).
Fixed; the assembler and a unit test now reject that, and a qualification
check covers the path. Evidence: `work/kit/v0.13.0/`,
`work/midnight-line/walk-*-75faa3ff.json`, sheets `work/kit/web5-*.png`,
`work/kit/oc-sheet.png`, `work/shop/web-shop.png`, `work/rooms/sub13-*.png`,
frames under `build/boot-tests/Versioned-75faa3ff/`.
Limits: no gesture of Spidey's for the Dragnet burst (he keeps the hold
pose); Overclock needs tier 5 exactly as proposed, which may be rare in
normal play; the web hits do not get the meter's damage bonus; bosses,
fliers and enemy types other than the gangs and symbiotes the lab met are
untried with Dragnet; a Vortex step does not turn Spidey toward the crowd;
prices are placeholders. The stronger crews were measured by the dial's
numbers and by the walk routes, not by a human fight: the Roof may now be
hard. The roof's left third could not be viewed by lab placement (a
placement artifact that v0.12.0 has too), only fought across.

## v0.12.0 - 2026-10-12 - The Substation: three rooms built from nothing

Published through Play Spider-Man.cmd's stable ROM (DeSmuME closed; the build does not touch the battery). SHA256
`0ede04222aa250e97c4348551ae61fdc5c4b586072088768bef8c8d7692dc812`
(ARM9 `a212585a...`, kit ARM9 `3c6a34e0...`: the combat kit is unchanged).
Title and Options show v0.12.0. Player (2026-10-11): the Midnight Line was
"basically just the sewers with different colors", wanted "new map assets"
and more places; (2026-10-12): go ahead with the planned changes.

- **A new door at the far left of the Yard.** From the Refuge take the left
  door into the Yard and cross it to its left wall: a grey door leads to the
  Substation, three rooms that are not copies of any room in the game. Their
  walls, floors, platforms, collision and camera are built from a box plan
  by a new room compiler; the pictures on them are borrowed from Pier,
  Downtown and Residential rooms you have already seen.
- **Switchyard.** An open yard at dusk with the skyline behind a fence: a
  loading dock, two stacked containers, a transformer, a steel gantry
  overhead, a fire escape on each building, pylons and wires. A crew appears
  once you walk in. Two barrels and a trash can to throw. Doors at both ends.
- **Relay Hall.** A tall machine hall. Its outer walls are smooth steel that
  Spidey cannot hold on to, so the way up is five catwalks: a held jump
  (keep B down) reaches the next one, a tap does not. Electric arcs run along
  four of them, the two on the left and the two on the right in turn: 1.5 s
  live, then just under a second with nothing live. The lowest catwalk and
  the ledge by the upper door are never live. A small crew waits on the
  floor. The door out is at the top left.
- **Control Roof.** A roof at night. Three waves, each from another district
  (Pier, Sewer, Residential enemies): the next starts when the one before is
  beaten, or after 90 seconds at the latest. Beating the third shows a
  line. Leave and come back and it starts over: it is meant as a sparring
  arena with real enemies. Two barrels.
- **Map.** The three rooms are drawn in the lower left of the Midnight Line
  screen; the Yard door and the Switchyard door are a pair of arrows.
- **Yard.** The metal barrel by its left wall now stands further along the
  floor (it stood where you arrive from the Switchyard).

How: `tools/nitro_build.py`, `tools/room_compiler.py`, `tools/room_author.py`
and `tools/midnight_rooms.py` (TECHNICAL "Room compiler", "The Substation").
Rooms 91..93; visited flags 267, 165, 164 and flag 150 for the cleared roof;
one instruction of the map's visited test now calls a stub so that rooms
above 91 can have a visited flag. Two things the original game needs in a
room were found on the way: camera regions and anchor points for spawners.

Agent-tested on this ROM, not player-confirmed:
279 unit tests; kit qualification 48/48; crash hunt 12/12; 10/10 walk
routes on the first try (four new ones: real doors both ways between the
Yard and all three rooms, a real held jump onto the first catwalk, a live
catwalk shocks, all three waves beaten sets the flag); eight further roof
fights started seconds apart all cleared; the door tour (every link, the
visited flags, no other chapter flag), the power puzzle, save and Continue
in the Refuge, the Vitality shop run. Evidence: `work/kit/v0.12.0/`,
`work/midnight-line/walk-*-0ede0422.json`, frames under
`build/boot-tests/Versioned-0ede0422/`.
Limits: the climb is scripted for the first hop only (the rest is placed;
a human climb follows from the measured jump heights); in the lab one roof
fight in about a dozen never reported its second wave beaten (cause not
found), which is why a wave also starts after 90 s; enemies have native
strength (no dial); the zoom's third step shows the debug placeholder in
these rooms; the nearest save point is the Refuge, two rooms back; a fall
from the catwalks only costs the climb.

## v0.11.0 - 2026-10-12 - Feedback pass: speed, Vitality, a chapter map, closed hatches, a gentler Nest

Published through Play Spider-Man.cmd's stable ROM (DeSmuME closed; the build
does not touch the battery). SHA256
`4f387a21821cf071c08a797d0daa997814b50b335c9da4e6e088c24610163ca5`
(ARM9 `caa84033...`, kit ARM9 `3c6a34e0...`). Title and Options show v0.11.0.
Player (2026-10-11, after finishing the Midnight Line on v0.10.0; verdict
under v0.10.0 below): do the quick fixes before bigger work, and of the
proposed stat upgrades "just vitality for now".

- **Speed rebalance.** Spider Reflex now speeds Red attacks by 10% (was 15%)
  and Spider-Sense by 20% (was 30%). Momentum starts a tier earlier (tier 1
  shortens two of five free steps, tier 4 all of them; still nothing at tier
  0) and from combo tier 3 up gives the old 15% / 30% back. Measured Y,Y,Y,Y
  with Sense and Momentum: 122, 106, 100, 88, 86, 86 frames at tiers 0..5
  (v0.10.0: 113, 105, 99, 93, 91, 87), the same hits at every tier. With no
  combo you are a little slower than before, from tier 3 a little faster, and
  Momentum's swing is 36 frames instead of 26.
- **Vitality I, II, III.** Buy Upgrades, Both Suits list, below Quick
  Recovery: 500, 750 and 1000 XP. Each needs the one before; refund them in
  reverse order. Your health bar holds 25%, 50%, 75% more: every hit takes
  that much less of it. The bar keeps its length; in the Red suit the bar
  and the spider emblem turn orange, gold, green. Healing is unchanged.
- **The Midnight Line has its own map.** In chapter rooms the touch screen
  shows a screen titled "Midnight Line": rooms drawn by their shape and
  joined on the side their doors are on, save rooms with a dot, the boss
  with a cross, an arrow back to the Sewer. The Gate's climb into the
  Stairs' floor grate is two dotted arrows (those rooms cannot sit next to
  each other on a flat plan). The zoom button's third step now shows the
  detailed room map in chapter rooms. The Sewer map is the original again.
- **Dead hatches closed.** The Entry's first ceiling grate and the
  Platform's top trapdoor are locked shut: nothing to crawl into.
- **A gentler Nest.** Enemy health / the damage they deal, as a share of
  native: Shaft 59% / 55%, Throat 66% / 59%, Span 70% / 66%, Hollow 75% /
  70%, Gate 80% / 75%. The boss room is unchanged. Measured before, in the
  lab's save: chapter sewer enemies 22k..37k health and 4,096 per hit, Nest
  enemies 74k..106k and 8,192..9,554.

How: the second kit block and the chapter build (TECHNICAL "Second kit
block", "Player health and the top-screen HUD", "Chapter map, closed hatches
and the strength dial"). Vitality is three chained rows on free ownership
bits 77..79 and scales the health Spidey loses, not his maximum, so the HUD
needs no change. The map uses the game's spare sixth area.

Found by the lab before release, never shipped: with the new speeds
Momentum jumped over the last sample of the Spin Cycle loop, so the spin
never ended (it now never skips an attack's last sample); the first map
build stayed locked on the objectives page (the game gives its sixth area
no map: three small patches) and a later one drew two rooms magenta and
black (three of the screen's palettes cannot hold rooms); a scaled enemy at
full health now stays exactly full.

Known limits: the Vitality colours show in the Red suit only (the Black
suit's purple is shared with the combo meter) and were seen in the lab's
emulator, not in DeSmuME; the shop shows no level number; rooms appear on
the map as you visit them, like native ones; the world view (zoom x2) has no
"you are here" for the chapter; the Yard's detailed map is a placeholder; a
chapter message covers the map until you change rooms (as before); B pressed
in the two updates between Perch stomp cycles still fires the native web
swing (older than this release); only chapter rooms have a strength dial;
Momentum does not show its tier.

Agent-tested on `4f387a21`: kit qualification 48/48 (the Perch spring check
now presses B ten frames earlier, off the gap between stomp cycles); the
three Vitality rows bought in order in the real menu, level I not refundable
under level II, level III refunded (XP 3000 -> 2500 -> 1750 -> 750 -> 1750);
a sparring Brute's hit 4,096 -> 3,280 / 2,736 / 2,336 with levels I..III; bar
colours and the map views x1, x2, x3 reviewed in frames (the whole map with
every room marked visited, from Gate, Hollow and Yard); crash hunt 12/12
with every new skill and Vitality III owned; chapter walk routes 6/6 on the
first try (75 checks); door tour 32/32 in two runs (links 0..16, then from
17: the tour's teleport dropped a knocked-back Spidey out of bounds in the
Throat, a lab artifact); power puzzle; save and Continue in Refuge, Rest and
Shrine; neither hatch can be crawled into; Span enemies 90,112 -> 63,361
(x 45/64), Hollow 81,108 -> 60,831 (x 48/64); 260 unit tests. Feel, prices,
colours and the Nest's new strength are untested by the player. Evidence:
`work/kit/v0.11.0/`, `work/kit/evidence.json`, `work/midnight-line/walk-*.json`.

## v0.10.0 - 2026-10-11 - Three new Red skills: Web Rush, Ricochet, Momentum

Published through Play Spider-Man.cmd's stable ROM (DeSmuME closed, battery
unchanged since 2026-10-07). SHA256
`a928843cb520d82568e703b3710f4177da4160addab5f8a61dbddd78ca7ae271`
(ARM9 `c6e2992a...`, kit ARM9 `7200e357...`). Title and Options show v0.10.0.
Player (2026-10-11): has mastered the seven skills, "everything feels very
bread and butter basic", wants "a bit more spice"; picked these three from
eight ideas and asked for real new Red shop slots. The Midnight Line is the
same as in v0.9.0.

- **Three new rows in the Red upgrade list**, below Spider-Sense (scroll
  down): Web Rush 300 XP, Ricochet 300, Momentum 400. They are bought and
  refunded like the others. Nothing is given for free and your purchases, XP
  and prices are untouched. Prices are placeholders.
- **Web Rush.** In a ground combo press A. Spidey fires a line and flies to
  the nearest enemy he cannot already reach (hold Left or Right to choose a
  side), runs three bicycle kicks up his chest and back-flips off. Y then
  carries the combo on where you left it; after the first hit that is Split
  Decision if you own it. A again after the kicks zips to the next enemy. It
  works out of Split Decision and Spin Cycle (the spin restarts with Y), R
  still cancels it, and with an enemy already in reach A does what it always
  did. Up to 56 units away (about two thirds of the screen), same floor.
- **Ricochet** (passive). An enemy you send flying knocks down and hurts
  everyone standing in his path, and they go flying too. It needs a real
  throw (1 unit per update sideways or more): the string finisher and the
  Sense counter throw at 1.5. Leapfrog's kick only pops him at 0.75 and a
  Skyjack spike goes straight down, so those do not count yet.
- **Momentum** (passive). Each combo meter tier shortens the wind-up and
  recovery of your ground combo attacks. Hits land exactly when they did
  before, so nothing whiffs: a Y,Y,Y,Y string that takes 113 frames at tier 0
  takes 99 at tier 2 and 87 at tier 5 with fixed button timing.

How: a second kit code block (the first was nearly full), a Red purchase
table of ten rows, and three ownership bits in unused space the game already
saves (TECHNICAL "Shop tables, menu and free ownership bits", "Second kit
block"). Unowned, Black-suit and native behavior are unchanged.

Known limits: Web Rush has no invulnerability and only targets enemies on
about the same level; R during the dash always rolls forward; Ricochet hits
with the strength of your last hit; Momentum leaves air strings, Perch and
the Spider-Sense counter at native speed.

Agent-tested on `a928843c`: kit qualification 48/48 (the 31 earlier
checks plus Web Rush near/far/chain/unowned/in-reach, Ricochet with a fixed
bystander and with four real Brutes, Momentum hit counts and speed at tier 0
and 5, with Spin Cycle and the Sense counter); the three rows bought, refunded,
re-bought and cleared in the real menu, and kept across save and Continue;
crash hunt 12/12 with the three skills owned; chapter walk routes 6/6 on the
first try (75 checks), power puzzle, save/Continue in Refuge, Rest and Shrine;
door tour 32/32 on a second run (the first, run beside six other emulator
jobs, missed one Nest door; alone it passes); 252 unit tests; frames reviewed
(shop rows and texts, the rush near and far). Rush out of the spin and a
Reflex cancel during the dash were traced once each. Not measured: bosses,
walls between Spidey and the target, enemies above or below him. Feel,
prices and whether tier 5 is too fast are untested by the player. Evidence:
`work/kit/v0.10.0/`, `work/kit/evidence.json`.

Player verdict (2026-10-11, after playing `a928843c`): Web Rush "was cool",
the passives "nice". Spider Reflex and Spider-Sense still carry the native
speed bonuses, so total speed is high and Momentum is hard to notice: the
player wants those two slightly slower and Momentum slightly stronger. The
chapter (v0.9.0 content) was finished on foot, boss included: that it can be
completed is player-confirmed. Complaints: the boss is one of the game's own;
the diagram does not show how rooms connect; some hatches can be crawled into
and lead nowhere; the terrain reads as recoloured sewers plus a hive section;
Nest enemies are far stronger than the sewer ones. The Yard was not
mentioned. Follow-up proposals: TASM_ROADMAP "Round two (2026-10-11)".

## v0.9.0 - 2026-10-11 - Midnight Line: the Yard

Published through Play Spider-Man.cmd's stable ROM. SHA256
`f109a5255b82f57e5290795e566a8f16ec1fbd8711b7c4b6a142a090dbd7432f`
(ARM9 `e54fa1aa...`; kit code unchanged). Title and Options show v0.9.0.
Player (2026-10-11): "keep advancing the map as much as you can and make sure
everything works well". Includes every v0.8.1 fix.

- **New room: the Yard.** The Refuge has a grey door in its left wall. Behind
  it is a freight yard above the line: a warehouse front with shutters, a
  wooden dock, a roof walkway with crates and boilers to throw, and a gang
  that has made camp there (the Pier's thugs). This is a room the game ships
  but never uses, so you have not seen it anywhere. You arrive in a rock
  tunnel at its right end; walk down into the yard. The same tunnel leads
  back. It is right next to the Refuge's save point, with no boss or puzzle
  in the way: a place to fight and use the kit.
- The Yard is on the touch-screen diagram under the Refuge.
- Its test leftovers are gone (ability orbs, red ichor floor and wall, ichor
  gates, hazards), so nothing in it gives or needs a story ability.

Agent-tested on `f109a525`: walk routes 6/6 on the first try, 75 checks (the
five v0.8.1 routes plus the Yard: Refuge door, tunnel arrival, down into the
yard, gang appears, back out, on to the Stairs), door tour 32/32, power
puzzle, save/Continue in Refuge, Rest and Shrine, kit qualification 31/31,
crash hunt 12/12, 248 unit tests; frames reviewed (door in the Refuge, Yard
at night, diagram). Gang strength and count were not balance-tested; not
player-confirmed. Evidence: `work/midnight-line/walk-*`, `work/kit/v0.9.0/`.

## v0.8.1 - 2026-10-11 - Midnight Line: a Nest you can actually walk through

Published through Play Spider-Man.cmd's stable ROM. SHA256
`f68a082e1829a97d2b2d0b4238050918e7c875d80e745c9569b615232385ce1b`
(ARM9 `4bdceb45...`; kit code unchanged). Title and Options show v0.8.1.
Player report (2026-10-11, v0.8.0): went down "this hive section", the top
entrance was sealed by goo, could not break "the red platform thing" without
the power-up, had to quit and lost a little progress. That was the Gate,
entered backwards through the Stairs grate. Walking the chapter with real
inputs showed the Nest could not be finished at all in v0.7.0/v0.8.0.

- **Fix: no room needs Sledgehammer Slam.** The red ichor floors in the Gate,
  the Hollow and the boss room only break to Sledgehammer Slam, the story
  ability of the very boss this chapter borrows and never grants. They are
  gone (the rooms' own "already smashed" state).
- **Fix: Nest fights no longer seal the doors.** Shaft, Throat, Span, Hollow
  and Gate keep their enemies, but the purple crystals never close the exits.
  With the rooms run against their native direction a seal could leave you
  with enemies you cannot reach (the lab reproduced it in the Throat and
  in the Gate). Fight or run; the boss arena is the one sealed fight.
- **Fix: the boss can be reached and fought.** You arrive in the arena's
  lower-right exit corridor. Climb the alcove and step into the arena: the
  ichor walls rise behind you and the fight starts. Before, the walls and a
  hidden timer locked you in the corridor with the boss on the other side.
  When the boss falls the walls and both lower doors open; the touch screen
  says to take the left passage, whose shaft (the Gate) climbs to the Stairs.
- **The Stairs grate is the way out, then a shortcut.** It is locked until
  you have reached the Gate from below; standing on it says so. After the
  loop it drops you straight back to the Gate.
- **Grate hint.** Breaking the boiler now also says how the grate works: stand
  on it, X opens it, Down drops in (the pit is barely wider than Spidey, so X
  alone only drops you when you stand dead centre).
- Needs from your save: Bulldozer Dash for the Span's two red walls (black
  suit, A); you own it.

Agent-tested on `f68a082e` with the new walk routes (`tools/midnight_walk.py`:
real inputs and real doors; lab fixtures: warp into the first room, enemies at
1 HP or parked, boss at 1 HP, health refilled, your ability bits): way in
(sealed grate and hint, breaker, boiler, grate), descent on foot through Shaft,
Rest and Throat into the Span, both red walls dashed, Hollow open where the red
floor was, Gallery, Shrine, boss room (500 frames in the corridor change
nothing; walls rise with the fight; boss; walls gone; left alcove open), Gate
(gap open, top never seals, out through the neck by wall crawl), Stairs,
grate back down: 5/5 routes, 67 checks. Door tour 30/30, power puzzle,
save/Continue in Refuge, Rest and Shrine, kit qualification 31/31, crash
hunt 12/12, 246 unit tests. The two dead
hatches (Entry chimney, Platform trapdoor) cannot trap Spidey. Fights were
not balance-tested; not player-confirmed. Evidence:
`work/midnight-line/walk-*`, `work/kit/v0.8.1/`.

## v0.8.0 - 2026-10-08 - Midnight Line: the power puzzle, hints and an objective board

*Superseded by v0.8.1: the "way into the Nest works" claim below held, but the
Nest itself could not be crossed on foot (red floors, door seals, boss room).*

Published through Play Spider-Man.cmd's stable ROM. SHA256
`d84ae5393d2e3f5cf0c82c3aaa346e087f7804b31f2b6e4a0b67bb8098f2557b`
(ARM9 `dc4911d7...`; kit code unchanged). Title and Options show v0.8.0.
Player (2026-10-08) was about to playtest v0.7.0 and asked the agent to work
on whatever it found worthwhile; the lab then found the Nest blocker below.
The player's battery was last saved before v0.7.0 shipped.

- **Fix: the way into the Nest works.** In v0.7.0 the boiler sitting on the
  Last Platform's floor grate stayed electrified forever (it shocks and knocks
  Spidey back), so the grate never opened and the Nest could only be entered
  backwards through the Stairs' floor grate, reaching the boss first.
- **Power puzzle.** The Platform's tracks are live. On the Stairs landing
  (left of the trash can) there is now a wall breaker: stand at it and press
  X to pull the lever and cut the track power for good. Back on the tracks,
  X lifts the boiler, throw it to smash it, then X on the striped grate drops
  into the Nest. This is the game's own switch/boiler/grate chain, rebuilt
  across chapter rooms; after the breaker is thrown the lever stays down.
- **Hints and objective board.** Short lines on the touch screen (play keeps
  going): entering the Platform while the power is on, pulling the breaker,
  and on entering the Refuge the current objective (cut the power -> go down
  into the Nest -> "The Midnight Line is quiet. For now." after the boss).
  The board checks completion first, so a v0.7.0 player who beat the boss
  through the back way sees "quiet", not "cut the power".

Agent-tested on `d84ae539` (and candidate `bc3aa3a1`, identical except the
Refuge OBJ): `midnight_line.py puzzle` (breaker -> Platform -> lift, throw ->
grate -> Nest Shaft, real presses) passes; v0.7.0 control shocks and never
lifts; thrown-lever pose and no prompt on re-entry; hint, breaker and the
objective lines (incl. completed-without-power) render; native training
message unchanged; door tour steps 0..22 on `bc3aa3a1` (step 23 hit the
Gate's ambush seal mid-run) plus `tour --start 24` on `d84ae539`, and the
Gate -> Stairs exit after fights (seeds 11, 12), i.e. all 30 links;
save/Continue in Refuge, Rest and Shrine; kit qualification 31/31; crash hunt
12/12 (`work/kit/v0.8.0/`); 230 unit tests. Not player-confirmed.

## v0.7.0 - 2026-10-07 - Midnight Line: The Nest, a boss, and the chapter on the map

Published through Play Spider-Man.cmd's stable ROM. SHA256
`c56095be2dfd999adb475c93f5238bd916289dbfe9dce1eb9b3cf4f8563d43b8`
(ARM9 `a19896db...`; kit code unchanged). Title and Options show v0.7.0.
Player asked (2026-10-07, before testing v0.6.1) for as much new content as
possible. v0.6.1 changes are included.

- **The Nest (8 rooms).** The floor grate on the Last Platform's tracks now
  drops into a symbiote nest under the line: Shaft, Rest (save), Throat,
  Span, Hollow, Gallery, Shrine (save), Gate. These are the game's Hive rooms
  (you have only seen Hive_Map01), recoloured and cloned with their own
  encounters: symbiote crowds and fliers (about twice the health of sewer
  thugs), ambushes that seal the doors with purple ichor crystals you smash
  to get out, and two save spheres. All Nest doors are the game's own pairs.
  The Gate's ceiling exit climbs back out through the Stairs' floor grate,
  next to the Refuge, so the chapter is a loop.
- **Boss: the rooftop arena.** Between the Shrine and the Gate is the
  Downtown_Map14 arena (a room you have not visited): an orange symbiote
  mini-boss with its own health bar, ichor gates and timed platforms. Beating
  it marks the chapter completed. Its native reward (Sledgehammer Slam and a
  story collectible) is *not* given, so the main story is untouched.
- **The chapter is on the map.** The Sewer touch-screen map now has a
  subway-style diagram in its empty lower-left corner: the line from the
  arrow (back to the Sewer) through Entry, Station, Platform, Stairs and
  Refuge, with the Nest loop below and the boss marked with a cross; save
  rooms have a dot. Rooms appear as you visit them; the current room is lit.
- Sealed: the Entry's second ceiling hatch and the Platform's top trapdoor
  (their floor-grate partners now lead into the Nest). Entry -> Station ->
  Platform is the way in.
- Dialogue removed from cloned rooms no longer cuts off the script steps
  that followed it (the follow-up group still runs).
- Version text needed the digit 7, which the game's compressed text table
  lacked; the table now gains that symbol (all 1049 strings re-encoded).

Agent-tested on `c56095be`: door tour 30/30 (rooms, arrival points, 14
visited flags, no other flags), save/Continue in the Refuge, Rest and Shrine,
fights end with working exits in Station, Shaft, Throat, Span, Hollow and
Gate (enemies capped at 1 HP), boss fight starts, boss death (HP capped)
sets the completed flag without the native reward and the exit opens, map
diagram drawn and highlighted in game, title shows v0.7.0, kit
qualification 31/31, crash hunt 12/12 (`work/kit/v0.7.0/`), Station ambush
seeds 11/12. Not player-confirmed. Still
missing: power puzzle, Signal Leech (original enemy), Conductor teaser.

## v0.6.1 - 2026-10-07 - Midnight Line: doors that make sense, a visible way in

Published through Play Spider-Man.cmd's stable ROM. SHA256
`c3010cba9255a30645ad9f020d3af284550f42da26b98f728e93b4c94f8ef590`
(ARM9 `817c23a4...`; kit ARM9 unchanged). Title and Options show v0.6.1.
Player feedback on v0.6.0 (2026-10-07): "really cool"; but the entrance was
hard to find (no visible door, "Sewer Map 7" meant nothing in game), doors led
to unexpected places (a ceiling trapdoor came out of a side door and vice
versa), fights were low-level sewer enemies, rooms are recognisably recoloured
sewer rooms, and having no working map was unnerving.

- **Doors now match.** Every chapter door pairs left with right and ceiling
  with floor: climb out through a ceiling hatch and you come up through the
  next room's floor grate. Three of the six links are the game's own
  connections. New layout: Maintenance Entry (arrival) -> up to the Station or
  up to the Last Platform; Station -> right -> Platform; Platform <-> Stairs
  (side door and top trapdoor); Stairs -> left -> Refuge (save sphere).
- **Visible entrance.** A grey doorway now stands at the right wall of the
  sewer save room behind the desk (Sewer_Save02: the save point in the lower
  middle of the Sewer map). Walk through it.
- **Last Platform fight.** The tracks room now runs its native encounter
  record: a crowd including red suits on the roof of a parked subway car.
  Station ambush and the Stairs' three groups remain.
- **Map.** Chapter rooms show the real Sewer map (your explored sewer and its
  save points) instead of an empty "Pier" map. The chapter's own rooms and
  your position are not drawn on it yet.
- Rooms renamed for what they are (Entry, Station, Platform, Stairs, Refuge);
  saves made in the v0.6.0 Refuge still Continue into the Refuge.

Agent-tested: all 14 doors (door kinds checked from trigger/spawn geometry
against 175 native pairs), Refuge save -> Continue, Station fights end with a
working exit (seed 11 also completed the ambush), Platform spawns up to 6
enemies on the train roof, kit qualification 31/31, crash hunt 12/12, native
Sewer_Save02 exit unchanged. Not player-confirmed. Still missing: chapter
rooms on the map, puzzle, Signal Leech, teaser; enemies are native sewer types.

## v0.6.0 - 2026-10-07 - Midnight Line: first station (exploration slice)

Published through Play Spider-Man.cmd's stable ROM. SHA256
`36aa52f8e5aef674d12f18f31aac1ac98aa874c9fed7d7b0d63264cfd9216021`
(ARM9 `efab33e0...` = v0.5.0 kit ARM9 `88328d56...` plus the chapter stage).
Title and Options show v0.6.0. Kit, prices and all native rooms' behaviour
are unchanged except Sewer_Save02, which gains one doorway.

- **Finding it.** In the sewer save room off Sewer Map 7 (Sewer_Save02, the
  one with the save sphere and the man at the desk), walk into the far right
  wall past the desk. Walking back out the Platform's left door returns you
  beside the desk.
- **Five new rooms** of an abandoned, cold-lit subway line (rooms 76-80, built
  from the native sewer subway section with a midnight colour grade):
  Last Platform (tracks; quiet arrival), Service Passage (station with the
  timetable; enemies and a one-time ambush), Switching House (station stairs;
  three enemy groups), Overhead Gallery (upper return route) and the
  Maintenance Refuge (amber emergency light, up the Platform's top-right
  stairs, no enemies, **save sphere**). The rooms form a loop: Platform ->
  Service -> Switching -> Gallery -> back to the Platform.
- **Saving inside the chapter works**: save at the Refuge sphere and Continue
  returns you to the Refuge. Visits and the Service ambush are remembered.
- Not in this slice yet: the power puzzle, the Signal Leech, the Conductor
  teaser and a chapter map (the bottom screen shows the source rooms' map).

Agent-tested (copied saves, lab warps/teleports): all 14 doors in one tour
with correct arrivals; Refuge save -> fresh boot -> Continue restores room 77
(control build without the room guard patch fails); death in the chapter runs
the native health-orb minigame and resumes there; Switching spawns the same 4
enemies as its native room; Service fights end with a working exit (seeds 11,
12; seed 13 inconclusive); native Sewer_Save02 exit unchanged; kit
qualification 31/31; crash hunt 12/12 clean. Not player-confirmed: route feel,
discoverability, encounter difficulty, lighting.
Rollback caveat: a save made inside the chapter is ignored by v0.5.0 and older
ROMs (the battery itself stays intact). Details: TECHNICAL "Midnight Line
chapter build (v0.6.0)".

## v0.5.0 - 2026-10-06 - Test Upgrades sparring room

Published through Play Spider-Man.cmd's stable ROM. SHA256
`fd7e4420f97645dd55011504843ce62f068d1276234c3cd781931c85bb1eb193`
(ARM9 `88328d56...`, kit code `395e9bfa...`). Title and Options show v0.5.0.
Player request (2026-10-06): several enemies in the training room that hit
back, with automatic healing so Spidey does not die. Applies to every suit
(training room only); the Red kit is unchanged.

- **Three sparring Brutes** join Test Upgrades: one left of Spidey's start,
  two at the far right. They use the native Brute AI (walk in, swing, hit
  for one health unit). The original practice dummy stays as a passive
  punching bag.
- **Enemies get back up.** Training enemies have 8 health units instead of 1;
  "defeating" one refills it to full instead of killing it, so the fight
  never empties.
- **Spidey cannot die in training.** He heals to full every 30 seconds, and
  holding SELECT+Down now refills him as well as the enemies. A hit that
  would kill him leaves him on an empty bar instead.
- Help text: "Sparring: you heal every 30 s. SELECT and Down: refill all.
  Pause: Return to Save Point."

Agent-tested: qualification 31/31 (solo-dummy room, unchanged checks), crash
hunt 12/12 sewer fights clean, 163 unit tests. Training room (copied save,
`--sparring`):
idle 3000 frames among the Brutes (healed at 30 s, lethal hits leave him
alive), three 4000-frame random Y/R fights (no stall, all four enemies alive
with 9-12 defeat refills each, SELECT+Down healed him); sewer arena: training
logic never active. Frames reviewed. Not yet player-confirmed: sparring feel,
heal interval, Brute count and spacing.

Launcher-only player performance trial (2026-10-06): `Play Spider-Man.cmd` now
selects `jit-preview` (DeSmuME JIT enabled, block size 12) so the normal play flow
uses the trial. Same v0.5.0 ROM and save; no renderer/resolution/timing overrides.
Launch arguments verified. Player confirmed overall performance was better,
with occasional dips that "weren't bad"; keep JIT12 in the normal launcher.
Broader gameplay/save compatibility was not separately confirmed. Details and
settings/launcher rollback baselines: TECHNICAL "Crowd combat performance".

Next renderer trial launched on 2026-10-06: normal shortcut now selects AUTOGL
at 1x while retaining accepted JIT12, the same v0.5.0 ROM and latest progress.
Prior software/JIT launcher and INI preserved; arguments and renderer setting
change verified. Renderer performance/visual acceptance pending.

## v0.4.1 - 2026-10-06 - Freeze and clip fix; smoother Sense and Leapfrog

Published through Play Spider-Man.cmd's stable ROM. SHA256
`da324b3c5b812fc941f58179386f0489ea151091518c350a5df1bbaf662fed29`
(ARM9 `b806e508...`, kit code `3826b452...`). Title and Options show v0.4.1.
Player report on v0.4.0 (2026-10-06): loving the kit, smooth overall, but
Spider-Sense and Leapfrog feel "teleporty"; a Sense flip clipped Spidey down
into an unreachable area; and the game froze for good during Y/R spam in a
crowd with Enhanced Dodge held.

- **Freeze fixed.** Every Spider-Sense teleport since v0.2.0 wrote Spidey's
  position past the end of his actor object, corrupting nearby heap memory; a
  later allocation then crashed the game (a data abort, which looks like a
  freeze). Spider-Sense no longer writes positions. The kit also checks every
  other enemy's pointers before reading them (a second crash in the Sense scan).
  Details: TECHNICAL "Freeze root cause and crash hunting".
- **Spider-Sense is a dash, not a teleport.** R as an enemy attacks: Spidey
  springs into a tucked front flip over the attacker (4 updates, top speed
  about 3 units per update), turns in the air and whips a roundhouse into his
  back. Walls stop the dash (he counters from the front instead of going
  through the wall). He ignores hits for 7 updates (about 0.23 s) from the
  press, like the old instant teleport did. New counter animation.
- **Leapfrog vault is continuous.** After the kick's hit-stop he moves forward
  every update (6 updates, about 2 units each, cancelling the kick's built-in
  recoil step) and lands about 3 units past the target, facing him; no more
  overshoot, snap back and drop. The flip goes higher in the animation.
- **Spider Perch** rides and head-hops by steering velocity instead of
  writing positions, so walls and ceilings can no longer be passed through.
- **Neutral Spider Reflex** (R with no direction) now consumes the R press; it
  used to consume a queued Y and leave the R queued.

Agent-tested: qualification 31/31 (new: Sense never moves more than 6 units in
one update, Sense next to the training wall stops at the wall where v0.4.0 put
Spidey 2 units inside it, Leapfrog vault continuous). Crash hunt
(`tools/crash_hunt.py`, sewer arena, random Y/R/held-R crowd fights of 4,000
frames with endless enemies, same setup for both): v0.4.1 0 crashes and 0 heap
corruption in 48 fights; v0.4.0 showed fresh heap corruption in 9 of 48 and
crashed in 2 (plus 4 freezes in about 90 earlier fights), every crash the same
abort in a heap pool whose node sits right after Spidey's actor. Frames reviewed for the Sense flip and
the Leapfrog vault. Not yet player-confirmed: Sense and Leapfrog feel, the
guard window, freeze-free long play.

## v0.4.0 - 2026-10-05 - Skyjack spike bowls the crowd

Published through Play Spider-Man.cmd's stable ROM. SHA256
`5e6465d824ef0a27c9372363806deb669703f1d8cbee2e26d2c54402f1d51207`
(ARM9 `b4e91fdd...`, kit code `68b1129e...`). Title and Options show v0.4.0.
Player confirmed v0.3.0 ("looks feels way better") and asked to keep the game
fast: no slow-motion anywhere.

- **Skyjack bowling.** When the spiked enemy hits the ground (it stops falling,
  within 40 updates of the spike), every other enemy within 8 units across and
  6 up/down of the impact takes a native heavy-kick hit: damage (4096 observed)
  and a full knockdown (launched, down, get-up). One impact per spike.
- How: a new hook on the native hit dispatcher keeps a copy of the latest hit
  Spidey deals; the kit replays it (as attack kind 0x1F, the heavy kick's
  knockdown) through each bystander's own ReceiveHit. Enemies in their get-up
  ignore it, as natively. Pointers are range-checked before use.

Agent-tested: qualification 28/28 (new check: hits captured and the landing
detected, nobody bowled with a lone dummy; native/Black parity unchanged with the
always-on capture hook). Sewer arena with live symbiotes (non-deterministic, a
second enemy placed near the landing; most runs have nobody within 8 units of
the landing): on the final bytes the bowl fired in run 2 of 2 (result "taken",
bystander HP -4096, states 41 -> 48 -> 49; frames show the impact spark and the
bystander launched); two earlier candidate builds showed the same. All 153 source tests
pass. Real DSV `75bb8efc...` checkpointed (unchanged). Not yet player-confirmed:
feel, bowling radius, bosses (not tested).

## v0.3.0 - 2026-10-05 - Perch exits, Reflex back tuck, Sense vs ranged

Published through Play Spider-Man.cmd's stable ROM. SHA256
`34736eeb50ae36dfb427ce16e232c3055a87589a9a0d2165a7e241c1880c1647`
(ARM9 `0483dc40...`, kit code `d2c1d4df...` + text). Title and Options show
v0.3.0. Queued roadmap iterations after the v0.2.1 fix; prices/ownership unchanged.

- **Spider Perch: B springs off.** While riding (air attack state 51), B launches
  him high off the head (initial 4.75 units/update up, Left/Right drift) in the Reflex front
  flip. That B is used up, so a second B is needed to web-swing.
- **Spider Perch: A hops to the next head.** A while riding picks the nearest other
  enemy within 24 units (held Left/Right picks the side), faces it and arcs onto
  its head over 8 updates (6-unit peak) in the front flip, landing straight into a
  pound. The perch lets go without a spring if he is hit, Snares or swings; in the
  short falls between pounds native A/B work as before.
- **Spider Reflex: neutral R back tuck.** With no direction held, the in-place
  dodge plays a new 7-sample back tuck (route kind 8 on action 139) instead of
  the native side-step; directional R still rolls with the front flip.
- **Spider-Sense reads ranged attacks.** Besides melee state 15 (within 12
  units), an enemy in state 16 (the ranged attack, see TECHNICAL) within 16 units
  now triggers the flip-behind counter.
- Perch shop text: "Y pound, A next head, B spring."

Agent-tested (training room, copied save): qualification 27/27
(`work/kit/evidence.json`), four new checks that fail on v0.2.1 (Sense vs forced
state 16, B spring height without a swing, head-hop onto a phantom enemy,
back-tuck routing flag). The head-hop target is a lab phantom (fake registry
enemy without AI or hitbox) because arena placements were unreliable; its landing
pound therefore whiffs, and chaining Y after a hop on a real enemy is untested.
Frames checked: spring flip, hop arc, back tuck, Perch text in Powers & Stats,
Options v0.3.0. All 153 source tests pass. Real DSV `75bb8efc...` checkpointed;
v0.2.1 ROM retained for rollback. **Player-confirmed (2026-10-05):** overall
"looks feels way better" after playing v0.3.0; no specific skill was singled out,
so head-hop on bosses and Sense vs spitters remain individually unconfirmed.

## v0.2.1 - 2026-10-05 - Spin Cycle reach and blade legs

Published through Play Spider-Man.cmd's stable ROM. SHA256
`00ca471c9627cf389cce4850423a7dc6a91938f6cc315ad9fbecbe9f72f03bc1`
(ARM9 `e0f1c3d3...`, kit code `d3851f52...`). Title and Options show v0.2.1.
Player feedback on v0.2.0: kit "very good"; the helicopter spin hit only every
other time and looked like breakdancing.

- **Spin Cycle aims every contact.** v0.2.0 flipped facing once per loop, so
  against one enemy every second contact kicked empty air (measured: 7 of 14
  contacts landed). Now, before each of the loop's two contacts, Spidey faces an
  enemy on the other side within 7 units (crowds still get both sides), else the
  nearest within 16 units.
- **Longer reach.** With no direction held, he glides (2 units/update) toward the
  enemy he faces until it is within 4.5 units, from up to 16 units away.
- **Steering no longer ends the spin.** Native Scissor repeats rejected Y with a
  back (or up/down) direction and fell into the sweep; during an owned spin any
  direction now repeats (new hook `0x020B5508`).
- **No slide after the spin.** Steering/glide velocity is cleared when the spin
  ends (v0.2.0 kept drifting ~9 units into the sweep, which then missed).
- **Split Decision never turns off a close target.** Hits 1-2 prefer an enemy
  behind only within 12 units (was 40); otherwise they face the nearest.
- **Blade legs.** New spin clip: legs locked straight (96-99% extension) in a wide
  near-horizontal split (9.5-unit span, 3-33 degrees above horizontal, was 80% and
  45-60 degrees, a V); the forward leg flattens through each contact.

Agent-tested (training dummy, copied save): qualification 23/23
(`work/kit/evidence.json`), including three new spin checks that fail on v0.2.0
(contacts landing vs a lone dummy 14/14, back-steer then glide back, sweep still
in reach). Captured in-game frames show straight blade legs and hit sparks on
contacts. All 153 source tests pass. Real DSV `75bb8efc...` checkpointed; v0.2.0 ROM
retained for rollback. **Player-confirmed (2026-10-05, via v0.3.0):** spin look
and hits feel "way better".

## v0.2.0 - 2026-10-05 - "Never stand still" Red kit

Published through Play Spider-Man.cmd's stable ROM. SHA256
`935d486b93f4aadbd63cbe01c932c7c12f90dcab7c0b51fdfe5b42a002b18537`
(ARM9 `99392f5d...`). Title and Options show v0.2.0. All seven Red purchase
slots are rewritten (design: TASM_ROADMAP). Native A/B/strings/evade, Black form,
shared purchases and unowned play keep native behavior; every hook checks Red
form (actor+0x34 != 1) and the slot's existing ownership bit. Prices, ownership
bits, dependencies and saves are unchanged.

| Slot (bit, XP) | New skill | Implemented first version |
|---|---|---|
| Web Kick (13, 50) | Leapfrog | Native pull + kick connect (lower pop-up); Spidey front-flips over the target in six updates, lands 3 units past and turns back |
| Web Launch (14, 100) | Skyjack | After the Web Vault launch both fall at quarter speed; Spidey drifts to stay within reach; air finisher (action 4) within reach spikes the target to the floor |
| Mid-Air Snare (15, 150) | Spider Perch | Snare follow-ups become the stomp action while Spidey is held on the target's head; Y during the pound chains another pound; spring-off when it ends. Replaces Sling Strike (its hooks restored) |
| Spider Dance (16, 150) | Split Decision | Branch hits 1-2 turn to an enemy behind (held Left/Right wins), sweep takes the nearest; Y+back continues the branch |
| Scissor (17, 200) | Spin Cycle | Repeats run 10 more times; Left/Right steers; facing flips each loop so contacts alternate sides |
| Amazing Speed (18, 250) | Spider Reflex | R cancels Red ground/air attack states immediately; held Left/Right turns and rolls, neutral dodges; the string node survives 28 updates so Y resumes at the next hit. Native speed bonus kept |
| Ultimate Speed (19, 350) | Spider-Sense | R while an enemy within reach is in its attack state (15): Spidey appears behind it, facing it, straight into the heavy string kick (node 14). Native speed bonus kept |

New authored animations (procedural FK/IK, Catmull-Rom curves) replace the Rush
clips (Split Decision corkscrew/split kick/breakdance sweep) and add six routed
clips: Reflex flip, handstand helicopter, perch pound, Leapfrog kick-vault,
Skyjack axe kick and Spider-Sense tornado kick. Routing swaps an action's SCA only
while its skill is active; native actions keep their bindings.

Agent-tested (training room, copied save, disposable RAM; work/kit/evidence.json,
20/20 checks): every mechanic above, including damage/contact and positions; Red
bits cleared and Black-form inputs match v0.1.1 state/action/facing/position
sequences up to a uniform one-frame load phase. Spider-Sense also triggered
against live symbiote attacks in the Sewer room left of the save (story-room copy).
Menu text, purchase and boot version visually checked. All 149 source tests pass;
candidate regeneration is byte-identical. Real DSV `3f65dfac...` checkpointed and
unchanged; v0.1.1 ROM and composition retained for rollback.

Not yet player-confirmed: feel, readability, crowds/bosses, walls/ceilings,
camera, heap headroom (reserve grew 16 -> 24 KiB) and Enhanced Dodge interplay
(its native successive dodge can delay a Reflex resume). Perch requires a target
the Snare can lock; Spider-Sense reads enemy state 15 only (other attack states
unknown). No slow-motion or tingle marker yet.

## v0.1.1 - 2026-10-05 - Affordable Both Suits tools

Published through Play Spider-Man.cmd's stable ROM. SHA256
`bcc6974a08b899a2def261b550b8bf9a31b005e201c7c4e276fc46dbf3e5d842`.
Title, pause label and Options header show v0.1.1. Red prices and current combat
carry over unchanged. All seven Both Suits purchase prices are reduced:

| Shared purchase | Previous XP | v0.1.1 XP |
|---|---:|---:|
| Launching Uppercut | 50 | 25 |
| Enemy Kick-Off | 200 | 50 |
| Drill Kick | 400 | 100 |
| Jackhammer Stomp | 600 | 150 |
| Air Dodge | 200 | 50 |
| Enhanced Dodge | 800 | 200 |
| Quick Recovery | 800 | 150 |

Total 3,050 -> 725 XP (-76.2%). Existing ownership, story/traversal gates, native
shared moves, black/Core rows and save format remain intact. Native refunds use
the new prices; the publisher never changes XP or purchase flags in the real save.

Agent qualification: native menu buys each row separately, taking a disposable
5,000-XP fixture to 4,275 XP. All seven purchase bits/XP survive native save/reload.
Each native refund restores its new price; full refund returns 5,000 XP and clears
all seven bits, also verified after save/reload. Nonshared flags stay unchanged.
The same seven buys on v0.1.0 cost 3,050 XP (5,000 -> 1,950 control). Title/pause/
Options visually checked; regeneration byte-identical; all 3,736 resources verify.
Only seven shared price words in ARM9 and two versioned text resources differ
from v0.1.0. Original ROM and exact 634-byte real DSV are unchanged, with checkpoint
and old/new compositions retained. All 141 source tests pass against the published
files, including exact reconstruction of the previous numbered release.

Evidence: work/shared-economy/publication.json and full-tests.log;
build/boot-tests/Versioned-bcc6974a/{buy-all,reload-all,refund-all,reload-refunded,
boot-version,options-version}; candidate build/version-0.1.1.
Historical numbered profiles retain their own pinned prices/version metadata;
v0.1.0 still reconstructs to its exact published hash.

Current combat design lives in TASM_ROADMAP. New movements, cancels and crowd
webs remain proposals/research; this price release does not claim that overhaul
or player acceptance of earlier combat motion.

## v0.1.0 - 2026-10-05 - Versioning and affordable progression

Published through the stable launcher. Exact ROM SHA256
`e1b66ebdad90856f7af5a508bd2bcd78ade0640c6926e6668da2c6b36cee1451`.

- Boot prompt shows TASM v0.1.0. Pause-menu Options label and Options-page header
  show Options v0.1.0, with native audio/control entries intact.
- Seven Red-row XP prices change below. Ownership, requirements, levels, strings
  other than version labels, black/shared rows and native buy/refund/save routing
  remain. Existing ownership carries over; refunds use the new row prices.
- Documentation now has exactly six core roles. A layout/size test prevents new
  feature/release/session Markdown and long startup handoffs. Machine catalogs
  moved to reference/; research is consolidated in TECHNICAL.
- The ambitious TASM redesign is recorded as future work. Its new names/behaviors
  are not displayed/granted as if implemented. Current combat mechanics carry over.

| Current Red purchase | Old XP | v0.1.0 XP |
|---|---:|---:|
| Rebound | 100 | 50 |
| Web Vault | 200 | 100 |
| Sling Strike | 600 | 150 |
| Oscorp Rush | 400 | 150 |
| Scissor-Kick Special | 600 | 200 |
| Amazing Speed Boost | 800 | 250 |
| Ultimate Speed Boost | 1,000 | 350 |

Total 3,700 -> 1,250 XP (-66.2%). Existing ownership and progress are preserved.
Agent validation: title/pause/options visual captures pass; all 1,049 strings in
both locales round-trip, unedited slot bytes/prefix/tree preserved; price patch
changes only seven 32-bit words. A native Rush purchase takes 2,000 -> 1,850 XP;
its purchase bit and XP survive save/reload. Native refund takes 267 -> 417 XP and
relocks the row. Deterministic regeneration is byte-identical and all 3,736 ROM
resources verify. All 139 source tests pass against the published composition.
The player's exact 634-byte DSV and wrapper are unchanged; prior ROM and old/new
compositions are retained. Publication evidence: work/version-research/publication.json.
Player acceptance of the overall gameplay/old authored motion remains open.
Evidence: `build/version-0.1.0/`, `work/version-research/`,
`build/boot-tests/Versioned-e1b66ebd/`. Build/read-only tests never write research
save results into the player's Battery directory.

## Included legacy gameplay and visuals (before numbering)

- Movie-inspired128x128 red suit with cleaned panels/black lenses; white alternate
  appearance, clearer menus, red mission marker and bounded instruction changes.
- Free Snap Sweep replaces the red opener's resource binding while retaining its
  logical credit/follow-ups; player-confirmed. Other actor bindings remain.
- Rebound replaces Web Kick; shorter recoil plus a closer/higher enemy juggle.
  Native purchase/refund/save checks pass. Retuned feel needs player acceptance.
- Web Vault replaces Web Launch, with paid player rise alongside a successful
  enemy launch. Initial version player-confirmed; matched rise/no backward drift
  revision is agent-tested, revised feel/ceiling/boss checks remain open.
- Sling Strike replaces Mid-Air Snare: finite passing kick, clean stop/turnaround.
  Gates/native total budget/save routing agent-tested; ordinary encounters/feel open.
- Oscorp Rush replaces Spider Dance with three completely authored clips: punches,
  uppercut, knee/high kick, overhand finish. Latest revision uses larger windups,
  camera-plane extensions and brief bounded limb translations. Dedicated IDs3733..3735
  isolate choreography; native six paid contacts/clocks/HP/credit/root data stay.
- Compact continuous wounded-enemy health bars and transient composite combo
  numeral. Visible damage panels were removed per player request; actual common
  HP telemetry remains private for balance. Specialized coverage/crowding open.
- SELECT+Down restores native training-target HP without leaving Test Upgrades;
  positive/flag-clear controls preserve position, reaction, XP and combo.
- Stable launcher, byte-preserving DSV checkpoints, prior ROM/composition retention,
  guarded profiles/resource append and deterministic compact changed GMB encoding.

Rejected/reverted experiments: green-suit first proof, yellow mission marker,
dance-like Rush sway and compact/stubby boxing revision. They are evidence/history,
not current shipped claims. Threaded idle benchmarks, JIT/preload/HD previews and
Blender bridge investigations are technical research, not proven lag/HD fixes.

## Selected historical milestones

| Date / identity | Meaning and validation |
|---|---|
| 2026-10-02 / clean round trip + green proof | Exact no-op ROM; one visible texture edit cold-boots |
| 2026-10-04 / Web Vault | 81 tests and isolated checks; player later confirmed initial move |
| 2026-10-04 / feedback -> Sling -> combat flow | Higher/closer Rebound, compact bars, paid Sling, matched Vault;92 then96 tests; player refinements open |
| 2026-10-04 / original Rush + training | 102 tests/native gate/refill controls; authored-animation tooling followed |
| 2026-10-04 / 8bc72be4 | Full authored Rush, dedicated isolation and count-only control;125 tests |
| 2026-10-04 / f0382e98 | Compact refinement;125 tests; rejected by player as stubby |
| 2026-10-05 / 4d36970e | Exaggerated authored Rush;8 pose tests,3,736 verified resources; maintenance later passed131 source tests; feel still open |

Full hashes, recipes, checkpoints and replay evidence are in retained private
release/candidate folders and archived original notes. Do not invent version
numbers for these previously unnumbered builds. Ordinary/dense AI, incoming hits,
walls/ceilings, specialized enemies/bosses, interruptions and long play remain
checks for any substantial combat release.
