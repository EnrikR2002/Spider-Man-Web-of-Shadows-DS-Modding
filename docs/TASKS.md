# Current work, backend queue and handoff

Updated 2026-10-16 (America/Edmonton). Read AGENTS and this first. Shipped facts:
[CHANGES](CHANGES.md); research: [TECHNICAL](TECHNICAL.md); combat design:
[TASM_ROADMAP](TASM_ROADMAP.md). No new Markdown.

## Current state

**Published0.19.0: Crane Row rework, agent-tested; player verdict pending.**
The player rejected0.18.0: familiar enemies/sounds, missing death/reward feedback,
sparse spawns, text clutter and coarse/repeated art. User explicitly requested
finishing and pushing source to Git; this release commit includes all related
pre-existing0.16.2..0.18.0 changes. Main/origin main; no ROM/extracted assets in Git.
Original generated panorama reference/art is safe to commit, RGB555 marked binary.

Stable `build/Spider-Man-WoS-modded.nds` is exact full composition
`build/version-0.19.0-final/Versioned.nds`, SHA9b2b948f6030a60246a0ca9ae477ae51c22f4aa349645fb2c6cef367c4557582,
ARM9 9b04b02a74cd634901c1435a5bb7708c073c127467cc9971b3bc9a5d1c6a10e3.
Boot/Options0.19.0. Crane7864/8192 bytes, max365 room quads. Keep exact frozen
Red kit/strength dial and Midnight4KiB. Crane parent remains frozen0.15.1.

Implemented: revised three silhouettes,154 authored full-lifecycle clips and
15 original voices; native rigs/AI retained. Texture atlas allows native death
tint. Private reward set31 fixes the copied zero field: actual physical XP/HP
orbs, no stat credit. Saved clears retain patrols; Engine/Shaft/Breakwater gain
encounters; upper Quay/Shaft/Gantry gain central waves. Global live cost4 stays.
Quiet materials, original painted harbor panorama, no destination boards or
first-visit/clear speech bubbles; small hatch X/lever bolt, map icons/short goal,
route details on Objectives. Office/Cache remain safe.

**Final evidence:** work/crane-row/rework/publication.json, exact scope audit,
387 tests +9 expanded adapter/driver/reward regressions;30 real Crane doors;
13 Midnight routes;11 native arrival/revisit patrol probes;8 progression controls
including Red/Black no-refill bosses. All pass. Patrols2..4 live, safe rooms0,
high Quay/Shaft covered. Native-HP mixed Freight clears all3 species and earns
178XP; player60-unit healing is explicit. Capped DryDock/Crown callbacks pass;
Crown opens upper return. Actual no-heal reward kills give each10XP plus1024/
1024/2048 health (Maw/Spore/Ballast); zero-set actual kill0/0. Private death IDs
and recorded waveform matches prove all3 voices render. Four map/Objective
phases, Quay/Engine/native Pier UI reviewed;65 prior art poses inherit.

**Progress retained:** latest actual634-byte battery3d21ee63 is byte-exact,
wrapper and snapshot round trips verified. Checkpoint before-v0-19-0-dsv-<fullhash>
and prior0.18.0 ROM/compositions retained. Publication used playtest.py build.
No fixture/stale emulator state entered the real save. Player uses the usual cmd,
Continue, play, save in-game, close. Agent manages builds/checkpoints.

Next: collect player verdict on creature identity, pacing, pickups and visual
clarity. Agent tests do not prove fun, difficulty, duration or frame-rate. Native
AI is still reused. No further feature expansion is requested.

## Deferred queue

No more skills; no slow effects/teleports. Signal Leech/Substation/Vortex verdict
pending. Dragnet held A, Overclock tier5, speed/Vitality/map/Nest/Yard and earlier
Leapfrog/R/Perch feedback remain. Crowd backend staged on older kit: requalify
before integrating. JIT12 confirmed; AUTOGL1x/Dragnet lines unmeasured. Training,
HUD/camera/suits/Conductor deferred.2099 later replaces Black (theorycraft).
Grid/Skyline deferred; Hive post-story.

## Commands and safety

`python -m unittest discover -s tests`; crane_row --release-dir build/NAME after
pinning. Labs: crane_walk, crane_boss_lab, crane_creature_lab, crane_reward_lab;
private qualification/UI scripts in work/crane-row. Read TECHNICAL rework section
for driver corrections and rejected E/F camera experiment; never publish E/F.
Reward currency is stats+0x44; config+0x50 is ERewardSetType. Camera functions
must never be inferred to produce rewards. Native arrival/inputs qualify drops;
held poses and teleports do not qualify traversal/difficulty.

Rooms96..107/area6, visits161..152/149/148, milestones140..146; only147/245 remain
audited. Kit changes need explicit rebase. Kit second6628/6656, first7096/7936;
bits83..95 free, state below+0x280. Literal tables, no mid-code byte/ltorg;
validate actors. Actual Battery/emulator: work/playtest.json. Re-read latest
while DeSmuME closed before publishing; preserve wrapper/snapshot/prior ROM and
compositions. Research always uses copied saves/disposable RAM.
