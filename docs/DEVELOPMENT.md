# Development and validation

Read the section for the task; this guide is not mandatory startup reading.
AGENTS owns constraints, TASKS owns the live handoff, TECHNICAL owns engine facts,
CHANGES owns shipped behavior, and ROADMAP owns design and player feedback.

## Know your environment

Check what this workspace can do before planning work:

| Workspace | Signs | You can | You cannot |
|---|---|---|---|
| Full local setup (Windows) | Clean ROM in `original/`, `build/`, `work/emulator`, `work/research-libs` | Build, run labs, qualify and publish | - |
| Fresh clone or cloud container | `original/` holds only `PUT_ROM_HERE.txt`; no `build/` or `work/` | Edit docs, design and Python; run `python tools/run_tests.py` | Build ROMs, run emulator labs, read batteries or claim in-game results |

In a fresh clone, `python tools/run_tests.py` reports tests blocked by a missing
ROM, `build/`/`work/` file or the Keystone assembler as "private input missing"
skips, and fails only on real errors. On a full setup, or with `--strict`, every
error counts. Plain `python -m unittest` still works but shows those as errors.

Find tools with `python tools/tool_index.py <word>`: it lists every `tools/`
module with its purpose, grouped by feature family. Check links and anchors with
`python tools/doc_links.py`, and every documentation rule with
`python tools/doc_contract.py check` (both run by `tests.test_document_layout`).

## Establish the current state

Read AGENTS/TASKS, inspect the working tree, then verify the relevant files.
`reference/gameplay_profile.json` selects the composition;
`tools/release_info.py` pins supported release hashes;
`reference/releases.json` records publication history. The stable ROM's adjacent
`.build.json` describes its composition. `build/releases/<SHA>/release.json`
records publication, previous ROM and battery checkpoint. Match their hashes
before treating a candidate or old report as the current build.

These are separate states: published, agent-tested, player-confirmed. A completed
duel establishes execution/clearability under its fixtures; the player's quality
verdict remains separate. Dated save hashes describe that observation only.
Always re-read the actual battery via `work/playtest.json`; never select a save
from old notes. A new clone lacks private ROMs, overlays, batteries and research
dependencies. Check availability before starting a long build.

## How a release is built

`python mod.py build` reads `reference/gameplay_profile.json` (the profile name
and the hash of every required overlay in `mods/`), packs those overlays into
`Glob.bin`, applies `tools/combat_profile.apply_rom` for the profile's compose
parent, then runs the post-passes in `mod.create_build` in a fixed order. Each
post-pass runs only when `tools/release_info.PROFILE_INFO[profile]` sets its
flag: `chapter`, `crane`, `midnight_rework`, `chapter_renewal`,
`creature_forge`, `creature_texture_fix`, `chapter_spectacle`,
`midnight_rebuild`, `midnight_encore`, `midnight_voltage`, `midnight_finale`,
`midnight_reliability`, `chapter_finish`, `spider2099`, `spider2099_polish`,
`spider2099_movie`, `spider2099_enemy_texture`, `vortex_forge`,
`hunters_return`, `hunters_return_fix`, `talon_lift`, `spider2099_presence`,
`hunter_kit`, `web_yank_fix`, `web_yank_combo`, `sky_rake`, `sky_rake_polish`, `sky_rake_front`, `reel_in`, `meteor_catch`, `boarding`. Recent
profiles copy their parent's flags and add one (v0.31.0 is v0.30.3 plus
`vortex_forge`), so the current release is the whole stack. A post-pass refuses
any input except its exact published parent ROM and checks its output against
the release pin.

`python tools/playtest.py build` wraps that build, protects the actual battery,
installs the stable ROM and records the release. Older generators reproduce
their own release only; never change their bytes under a published version.

## Add a feature as a new post-pass

New gameplay or art ships as one more post-pass over the current published ROM.
Copy the established shape (`tools/vortex_forge.py`, `.s`, `_art.py`,
`_lab.py`, `tests/test_vortex_forge.py`, `reference/vortex_forge.json`):

1. Start only from a ROADMAP item the player approved, with acceptance criteria.
2. `tools/<feature>.py` pins `PARENT` to the published ROM SHA
   (`release_info.PROFILE_INFO['tasm-v<current>']['rom_sha256']`) and its path
   under `build/version-<current>-final/`. `apply_rom(rom)` rejects any other
   parent, changes only an explicit allow-list of resources and ARM9 ranges,
   rewrites the boot/Options version strings (string slots 50 and 74), compares
   against its release pin when one exists, and returns `(rom, log)`.
   `generate(out)` writes a candidate under `build/` with `.build.json`,
   `gameplay_profile.json` and `changes.json`.
3. ARM code goes in `tools/<feature>.s`, assembled with Keystone from
   `work/research-libs`; run the literal/branch checks from
   `tools/assemble_tasm_kit.py`. Keep the 32 KiB player kit exact unless the
   change deliberately extends it, and give new code its own guarded block.
4. Authored motion uses `tools/kit_choreography.py` (see TECHNICAL
   [Kit animation authoring](TECHNICAL.md#kit-animation-authoring)).
5. `tools/<feature>_lab.py` runs cases on copied latest batteries and disposable
   RAM with an explicit `--rom`.
6. `tests/test_<feature>.py`: pure-Python checks that run anywhere; guard
   ROM-dependent classes with `unittest.skipUnless(mod.DEFAULT_ROM.exists(), ...)`.
7. Register the release: add `PROFILE_INFO['tasm-v<next>']` as
   `{**PROFILE_INFO['tasm-v<current>'], 'version': ..., 'date': ..., '<feature>': True}`,
   add the guarded block (and its log key) at the end of `mod.create_build`,
   then add the ROM/ARM9 pins once the candidate is accepted.
8. Qualify (below), publish with `playtest.py build`, then record the receipt in
   `reference/<feature>.json`, the release as a new top CHANGES section, the
   README "Current release" line and TASKS "Published build" (the contract
   checks that all of them name the same version), then run
   `python tools/doc_contract.py freeze` to freeze the new CHANGES section.

## Find the implementation

| Task | Read first in TECHNICAL | Implementation / evidence |
|---|---|---|
| v0.29 Skyjack/Skitter/Crane finish and current qualification | [Scoped finish](TECHNICAL.md#scoped-movement-and-chapter-finish-v0290) | `chapter_finish.py`, `_kit`, `_motion`, `_skitter`, `_audio`, `_crane`, `_lab`; `reference/chapter_finish.json` |
| Current Midnight route/map and reliable boss/ramp contact | [Reliability correction](TECHNICAL.md#reliability-and-active-route-correction-028-research) | `midnight_reliability.py`, helpers `_combat/_rooms/_lab`; `owned_player_lab.py`; `reference/midnight_reliability.json` |
| Inherited Midnight anatomy/motion and ordinary combo openings; apply the newer reliability layer too | [Combo openings](TECHNICAL.md#combo-openings-and-coherent-creature-motion-027-research) | `midnight_finale.py`, helpers `_combat/_motion/_art`; `reference/midnight_finale.json` |
| v0.24 contact/lifecycle/voice and room-envelope corrections beneath later Midnight layers | [Midnight rejection diagnosis](TECHNICAL.md#midnight-enemy-rejection-contact-diagnosis-2026-10-18) | `midnight_rebuild.py` exact 0.23 post-pass; `midnight_enemy_*`, `midnight_rebuild_rooms.py`, `room_envelope.py`; `reference/midnight_rebuild.json` |
| Shared enemy model/motion/attack/audio foundations | [Creature Forge](TECHNICAL.md#creature-forge), then later correction subsections | `creature_forge.py`; helpers `_design`, `_art`, `_motion`, `_combat`, `_audio`; `reference/creature_forge.json` |
| Texture/material correction | [Creature Forge](TECHNICAL.md#creature-forge), material-size correction | `creature_texture_fix.py`; its exact parent pin and scope |
| v0.23 staging, materials, machinery and roof pursuit beneath later room corrections | [Chapter spectacle](TECHNICAL.md#chapter-spectacle-implementation-v0230-2026-10-17) | `chapter_spectacle.py` exact 0.22.1 post-pass; helpers `_rooms`, `_art`, `_events`, `_combat`, `_audio`, `_lab`; `reference/chapter_spectacle.json` |
| Chapter connections/roofs/objects underneath the post-pass | [Chapter renewal](TECHNICAL.md#chapter-renewal-v0210-2026-10-17) | `chapter_renewal_rooms.py`, `midnight_walk.py`, `chapter_renewal_lab.py`; `reference/chapter_renewal.json` |
| Room compilation and collision | [Room compiler](TECHNICAL.md#room-compiler-v0120), [Room collision tree](TECHNICAL.md#room-collision-tree-2026-10-11) | `room_compiler.py`; room/BSP tools and topic tests |
| Player combat/hooks | [Player state machine and Red kit hooks](TECHNICAL.md#player-state-machine-and-red-kit-hooks-v020), [Kit animation authoring](TECHNICAL.md#kit-animation-authoring) | `tasm_kit.s`, `tasm_kit2.s`, `assemble_tasm_kit.py`, `kit_lab.py` |
| Hunter revision-3 Web Yank | [Web Yank](TECHNICAL.md#hunter-revision-3-web-yank-v0340) | `hunter_kit.py`, `.s`, `_art`, `_lab`; `reference/hunter_kit.json`. Exact v0.33.1 post-pass, one independent Black row, X prompt priority, private clips/weak refs and heavy-target velocity. |
| Firm Web Yank and arrival-timed rake | [Web Yank](TECHNICAL.md#hunter-revision-3-web-yank-v0340) | `web_yank_fix.py`, `.s`, `_art`; `reference/web_yank_fix.json`. Exact v0.34.0 post-pass in the existing private page; `hunter_kit_lab.py --distance` measures actual gaps after its pre-input layout fixture. |
| Down+A pure pull and five-target lines | [Pure-pull research](TECHNICAL.md#pure-pull-input-and-catch-effects-v0342-research) | `web_yank_combo.py`, `.s`, `_lab`; `reference/web_yank_combo.json`. Exact v0.34.1 post-pass; extra 8 KiB block, five weak target/line records and guarded zero-HP catch VFX. `--six-enemies` changes only the disposable training OBJ; its executable/other assets match production. |
| Purchased 2099 Talon Lift | [Kit animation authoring](TECHNICAL.md#kit-animation-authoring) | `talon_lift.py`, `.s`, `_lab`; `reference/talon_lift.json`. Exact v0.32.1 post-pass; private 14-sample SCA and native R queue, retaining Power Launch movement/contact/damage and native held B. |
| Purchased Black air string and affordable Hunter shop | [Kit animation authoring](TECHNICAL.md#kit-animation-authoring) | `sky_rake.py`, `.s`, `_art`, `_lab`; `reference/sky_rake.json`. Exact v0.34.2 post-pass; private clips and stateless native-hit receiver, bit85 row, nine implemented Black prices within the fourteen-row budget. |
| Taller 2099 and neon red webs | [SCA / model / textures](TECHNICAL.md#sca--model--textures) | `spider2099_presence.py`; `reference/spider2099_presence.json`. Exact v0.33.0 post-pass; guarded whole-pose draw scale and form-specific native web tints, with native collisions and assets retained. |
| Conditional Vortex, Conductor armor/HUD and low-HP Vitality correction | [Conditional tether Vortex](TECHNICAL.md#conditional-tether-vortex-and-conductor-armor-v031-research), [Player health](TECHNICAL.md#player-health-and-the-top-screen-hud-v0110) | `vortex_forge.py`, `_art`, `.s`, `_lab`; `reference/vortex_forge.json`. The old kit sources/hex remain immutable. |
| Hunter hit isolation and player replacement | [Kit animation authoring](TECHNICAL.md#kit-animation-authoring) | `hunters_return_fix.py`, `.s`; `reference/hunters_return_fix.json`. Exact v0.32 post-pass in the unused image tail; preserve per-victim native credit and reset replaced player owners. |
| First 2099 skill and fuller physique | [Kit animation authoring](TECHNICAL.md#kit-animation-authoring) | `hunters_return.py`, `.s`, `_motion`, `_art`, `_lab`; `reference/hunters_return.json`. Exact v0.31 post-pass; native Webbed Fury ownership/recall, private motion and collision-driven pursuit. |
| Historical Skyjack drift and unshipped crowd prototype | [Movement audit](TECHNICAL.md#shared-crowd-hit-backend-candidates) | Old `tasm_kit.s` / hex reproduce the parent; the current correction is a separate frozen post-pass, not a disposable RAM patch |
| Baseline formats, bindings, animation events | [Format boundaries](TECHNICAL.md#format-boundaries-and-confirmed-structures) | `wos_tool.py`, `actor_actions.py`, `animation_rig.py`, `model_geometry.py` |
| Classic 2099 Black-slot appearance | [SCA / model / textures](TECHNICAL.md#sca--model--textures) | `spider2099.py`, `spider2099_art.py`; `reference/spider2099.json`; native rig/skin preservation and exact v0.29 parent |
| Current 2099 physique/cape/blades and real draw selection | [2099 draw correction](TECHNICAL.md#sca--model--textures) | `spider2099_polish.py`, `_sculpt`, `_visual`; `reference/spider2099_polish.json`. Both forms load shared `spd`; qualify actual lists and crowded texture residency, not only previews. |
| Cape-free Across the Spider-Verse 2099 | [SCA / model / textures](TECHNICAL.md#sca--model--textures) | `spider2099_movie.py`, `spider2099_movie_art.py`; `reference/spider2099_movie.json`. Exact v0.30.1 post-pass, existing selector literals only; the v0.30.3 I4 follow-up resolves the sampled crowd. |
| Crowded Midnight enemy texture residency | [SCA / model / textures](TECHNICAL.md#sca--model--textures) | `spider2099_enemy_texture.py`; `reference/spider2099_enemy_texture.json`. Preserve 128px artwork/UVs, compact to I4, validate live materials on a copied-save mixed scene. |
| Save safety and publication | AGENTS and this guide's release section | `playtest.py`, `desmume_save.py`, `save_backups.py` |
| Shop rows, ability bits and prices | [Purchase records](TECHNICAL.md#purchase-records-and-native-ownership), [Shop tables](TECHNICAL.md#shop-tables-menu-and-free-ownership-bits-v0100) | `tasm_kit.py` (Red/Both Suits rows), `release_info.py` (prices), `upgrade_trace.py` |
| Purchased airborne Reel In | [Reel In](TECHNICAL.md#airborne-reel-in-v036-research) | `reel_in.py`, `.s`, `_art`, `_lab`; exact v0.35.2 post-pass, bit84 with Web Yank dependency. Lab `--case` covers native controls, real floor-contact release, heavy zip and native purchase/save. |
| Purchased airborne Meteor Catch | [Meteor Catch](TECHNICAL.md#meteor-catch-v037-research) | `meteor_catch.py`, `.s`, `_art`, `_lab`; exact v0.36.0 post-pass, bit86 requiring Sky Rake. Lab cases include low-floor contact, chosen follow-up, lethal cleanup, native fallbacks, Conductor and purchase/save. |
| Purchased 2099 Boarding / Wing Ripper | [Boarding](TECHNICAL.md#boarding-v038-research) | `boarding.py`, `.s`, `_art`, `_lab`; exact v0.37.0 post-pass, independent bit88. Copied-save Conductor, native MiniBoss and wall fixtures, interruption and shop controls; exact v0.38.0 qualification is in `reference/boarding.json`. |
| Remaining 2099 Black kit | ROADMAP [implementation guide](ROADMAP.md#implementation-guide) | Follow [Add a feature](#add-a-feature-as-a-new-post-pass); native mini-boss adapters still require qualification. |

Tool filenames in this table are under `tools/`. Find a CLI's actual arguments
with `--help`; do not infer a new command from a similar older tool. Search topic
headings (`rg -n '^#{1,4} ' docs/TECHNICAL.md`) and read bounded sections. For
historical notes use `doc_archive.py list`, then `read --toc/--section`.

## Prove one complete example first

1. Turn the feedback into observable acceptance criteria: silhouette at native
   resolution, weighted motion, original movement/contact behavior, complete
   hurt/knockdown/get-up/death, distinct audible cues and ordinary traversal.
2. For an unfamiliar pipeline, finish one representative creature/room before
   expanding it across the roster. Include real collision, contact timing, sound
   and interruptions. Use a control to isolate one unknown engine behavior.
3. Review actual emulator footage at native scale and normal speed. Check the
   texture in-engine, anticipation/contact/recovery, grounded feet, airborne
   transitions, landing, occlusion and sound in the mix. A pose sheet or valid
   parser output alone cannot establish these qualities.
4. Expand after that example works. Capture short clips early for visual review;
   counters establish mechanics, while watching/listening establishes presentation.
5. Check mixed encounters and terrain separately from isolated species. A route
   timeout needs a trace: distinguish a driver mistake, inaccessible actor and
   actual game bug before changing combat or room geometry.

The v0.22 work found clocks in whole samples, a second AI pass canceling jumps,
and native material dimensions affecting UV sampling. Those discoveries belong
in the engine contract and regressions. The reusable workflow lesson is to test
the complete native path before scaling authoring or publishing.

### Labs in a fresh git worktree

A worktree has none of the ignored private inputs. Before any lab copy from the
full checkout: the clean ROM to `original/`, `mods/*` (then `git checkout --
mods/README.md`, which the copy overwrites), the parent `build/version-<n>-final`,
and `work/{emulator,research-libs,playtest.json,save-backups,glob,rom,kit}`.
Missing `save-backups`/`glob` makes a lab boot a fresh game and stall on the
health-orb tutorial. Run labs one at a time. `crane_walk.py machine --rom <rom>
[--black] --no-heal --purchased-kit --combat-frames 10000 [--verify-clear]`
fights the hoist with native inputs; `chapter_spectacle_lab hoist*` and
`chapter_finish_lab` use a JIT static warp that starts in room 96 here.

## Run focused qualification

Always pass the candidate ROM explicitly; some legacy defaults point to old
chapters. Keep its adjacent build metadata. Examples below use a candidate path
chosen for the task; they do not create or publish a release.

```powershell
$candidateRom = 'build/your-candidate/Versioned.nds'
python tools/creature_forge_lab.py duel --rom $candidateRom --creature skitter --tag=-trial --capture-every 6
python tools/creature_forge_lab.py duel-all --rom $candidateRom --tag=-trial
python tools/creature_forge_lab.py phase --rom $candidateRom --tag=-trial
python tools/creature_forge_lab.py boss --rom $candidateRom --no-heal --persist --tag=-trial
python tools/creature_forge_lab.py boss --rom $candidateRom --black --no-heal --tag=-trial-black
python tools/creature_forge_lab.py continue --rom $candidateRom
```

Run only cases relevant to the change. `phase`/ordinary duels heal the player;
`--no-heal` is a separate boss control. `--persist` earns a research save through
native play. `continue` requires `work/creature-forge/conductor-earned.sav` and
fresh-boots it; never substitute the actual battery. Initial room arrival and
roster isolation are lab fixtures. Read each report's limits before making claims.

For v0.27 generate a new private candidate with `midnight_finale.py --out <build-dir>`.
`midnight_voltage_lab.py boss|press --rom <candidate> --out <work-dir>` selects
the candidate's current counter state and contact timings from its metadata.
`midnight_enemy_lab.py` resolves the candidate's actual roster-table pointers;
an older cached pattern pointer can silently fail to isolate an enemy after a
post-pass replaces the table entry. Ordinary A/B motion tests can be inherited
only with an explicit byte-scope proof; final native-scale presentation and mixed
composition still need review on the exact final ROM.
`midnight_rebuild_lab.py terminal-wave|floodworks-wave|turbine-wave` checks
the current full-HP wave, waits for later native spawns and clears again; the
player is healed and contained by inputs. Pair with `observatory` for the late
mixed roster. These are clearance controls, not difficulty/player-acceptance tests.

For v0.23 use `chapter_spectacle_lab.py --help`. Its `duel` fixture targets the
new per-room pattern/goal tables; older isolation fixtures no longer isolate
the production roster. `freight` uses the live native cost budget (Ballast costs
two), so two simultaneous species and actual damage/clearance of all three is
the expected mixed control. `conductor`, `hoist-save`, `arm-continue`, `engine`
and `pump` cover the new sequence; pass an explicit ROM and unique tag.
`crown-checkpoint` isolates settled arrival/save interaction with already-earned
progress preset; pair its result with `arm-retry-continue --save <private.sav>`.
A RAM flag observation alone cannot establish a successful save.

For v0.25, `midnight_encore_lab.py conductor --rom <candidate> --no-heal --persist`
observes the native boss meter alongside an earned victory/save. `--reactive`
adds native R/B responses; it does not make the run a no-damage demonstration.
`pressure` labels between-program player refills and real HP phase progression;
`native-boss` checks original Mega Venom HUD isolation in its original arena.
For a fresh Continue pass `conductor-continue --save <exact-earned-work.sav>`.
Continue may use the native room's entry spawn rather than the save sphere's
last X; drive the actual chapel/door from observed state. Fixed short scripts
can stop before a wider room's exit and falsely report a persistence failure.

For v0.24 use `midnight_enemy_lab.py --rom $candidateRom --style <style>` for
actual player-HP contact checks. `--reset-between` restores the native player
maximum between programs; `--finish` permits separate refills during the ending
base-string clear. `--counterplay` uses native R/B inputs. Reports distinguish
real HP loss from contact-window counters. Pass a unique `--tag` and output
directory; follow the report's fixture labels instead of treating these as
difficulty runs. `--approach-x` chooses a native walking destination; a passive
probe trapped against a crate cannot establish an attack's range or damage.
`midnight_rebuild_lab.py` copies the latest actual battery on
each invocation and wraps the current chapter controls. `tower-loop`,
`crown-reverse` and `return-loop` qualify the new tower/stairs with native
physics; use `--black` for a native suit switch. Its `hoist-save` returns over
the beam/crate landings before interacting with the sphere; the generic walker
can loop below the low beam. Pair an earned save with `arm-continue`.

For changed rooms, `python tools/midnight_walk.py all --rom $candidateRom`
selects the renewal navigator when the candidate metadata identifies it.
`python tools/chapter_renewal_lab.py crane-all --rom $candidateRom` covers Crane.
Real-input doors are required; teleports establish graph links only. For player
kit changes use `kit_lab.py qualify <rom>` and the relevant crash/room controls.

Set `WOS_CHAPTER_LAB_OUT` to an absolute directory under `work/` for a new
qualification batch. Renewal/Midnight reports and Crane child processes inherit
it, preserving older receipts with fixed filenames. With it unset the historical
output locations remain unchanged. Keep each batch tied to one immutable ROM.

Run topic tests while iterating, then the appropriate broader suite once the
candidate is stable. Example enemy checks:
`python -m unittest tests.test_creature_forge tests.test_creature_texture_fix tests.test_chapter_renewal -q`.
Inspect the final summary and exit status, including when output is redirected.
Qualification CLIs return exit 1 for failed cases or batches; direct navigator
functions still return report dictionaries for callers.
Reuse earlier controls only with an explicit byte-scope or unchanged-mechanics
argument; identify which ROM was actually tested. Re-run after relevant changes,
failures or unresolved concerns, rather than repeatedly running every suite.

For current-owned combat, first run `owned_player_lab.py measure --rom <candidate>
--out <work-dir>`. It fresh-boots a latest actual DSV copy with ordinary Continue,
then records the three ability words, XP and initial HP. Pass the resulting
`--owned <profile.json>` to `midnight_reliability_lab.py boss|press|terminal-wave|
floodworks-wave|turbine-wave|observatory`. `--no-heal` separates survival pressure
from healed clearance. This restores measured values only in disposable RAM
after the older temporary purchase prefix; the real battery is never written.
`owned-at-combat.json` must match. `WOS_CHAPTER_PLAYER_PROFILE` applies the same
fixture to child door controls. A changed actual battery requires remeasurement.

For the current reliability composition, a complete example is:

```powershell
$candidateRom = 'build/your-candidate/Versioned.nds'
python tools/owned_player_lab.py measure --rom $candidateRom --out work/your-batch/owned
$ownedProfile = 'work/your-batch/owned/owned-player-profile.json'
python tools/midnight_reliability_lab.py boss --rom $candidateRom --out work/your-batch/boss-red --owned $ownedProfile --no-heal --reactive --persist
python tools/midnight_reliability_lab.py turbine-wave --rom $candidateRom --out work/your-batch/turbine --owned $ownedProfile --no-heal
```

`chapter_finish_lab.py` adds final-ROM Skyjack open/wall/cancel, native Freight
roof pursuit, Skitter lifecycle/currency and existing hoist/save wrappers.
Pass `--owned <profile>` for current-owned lifecycle/combat. `midnight_enemy_lab.py`
also accepts `--owned`; its between-program resets remain labelled fixtures.
Use compact distinct tags: long nested labels can make the native core reject a
valid fixture path before boot. Read each report's actual `route`, capture/audio
paths and schema rather than constructing a filename from an older case.

Kit isolation is distinct from current-owned play. A latest battery may already
own all added rows. Qualification clears only their word2 mask in disposable RAM
before setting each case's explicit `bits2`; native/Black/story/unknown bits stay
intact. Do not call an OR-only fixture unowned. JIT is safe for immutable ROM
code plus data fixtures; runtime code patches still require JIT off. `kit_lab`
serializes core options through its child protocol; native CLI option values
are restored as bytes there. Keep the source battery unchanged throughout.

Select the other relevant cases with `--help`. The earlier version-labelled
commands above reproduce their recorded fixtures; they are not instructions
to replace the current composition with a v0.23/v0.25/v0.27 generator.

Boss cursor/selection counts do not prove damage. The reliability post-ReceiveHit
observer distinguishes the real boss attacker, native result and player HP.
`native-hits-live.json` is bounded; the phase control drains only its private log
counter into `native-hits-drained.json`. Keep initial warp/purchase/HP fixture
limits with every claim. For removed rooms run `legacy --name signal|refuge` and
`removed-door --name terminal|floodworks` on the explicit final ROM. Legacy starts
at a copied-save sphere: walk away before pressing X or the save prompt absorbs
the exit input.

## Read the lab evidence correctly

For v0.26 sound, use `midnight_voltage_lab.py analyze --live <probe-dir> --muted
<zero-owned-wave-dir> --style <species> --out <work-dir>` with the bundled NumPy
runtime. The zero-wave control keeps sequence priority, file sizes and timing.
Only subtract mixes when the gameplay traces match exactly; otherwise use
specific live waveform matches and label the divergent control. A silent-channel
mix with no clipping can still fail audibility. Compare source/render levels
against a real native effect and check tells/impacts during combat.

`midnight_voltage_lab.py boss|press --rom <candidate> --out <work-dir>` records
the actual HP-loss response state. `--no-heal --reactive --black --persist`
uses native aerial evasion/stomps for the Black control. `press` heals unless
`--no-heal` is explicit and is not a difficulty proof. Keep failed controls.

| Output | Contract / trap |
|---|---|
| Creature Forge runtime | `move_calls` counts selections; `contact_move_calls` counts crossed contact windows. Neither alone proves a hit or HP damage. Observe native HP/clear checks too. |
| Crane duel | `work/creature-forge/duel-<style>-proof<tag>.json` holds counters; detailed `work/crane-row/creatures/creature-duel-*.json` holds `route` and `observations`. |
| Midnight/boss duel | `work/creature-forge/walk-*.json` holds `checks`, `forge_trace`, `captures`, ROM hash and fixture limits. |
| Continue/door reports | Some filenames ignore `--tag` (e.g. `earned-continue.json`, `walk-pair-78-2.json`). Preserve the prior report before a run that would replace evidence. |
| Frame numbers | Training/Forge traces are relative to frame 3030; capture filenames are absolute. Prefer the report's `frame_offset` when present. |
| JIT and hooks | Runtime RAM code patches need JIT off. Normal Forge probes compile arrival patches before boot. Run lab cases in separate processes: helpers temporarily replace module hooks. |
| Audio | A decoded sound reel proves sample authoring; captured PCM establishes in-game playback. Verify cues in the mix as well as runtime request counts. |

Reports have different schemas: inspect top-level keys before scripting extraction.
Native updates can straddle a video capture, exposing a new controller state
beside the old animation for one frame. Keep raw rows. For controlled native
pairs, compare all state-entry events and separately compare action events that
persist for a full update; declare the capture window, timing tolerance and
initial controller/velocity fixtures. Do not silently discard an unexplained
gameplay difference or count a setup fixture as mechanics proof.
Use unique labels and keep failed controls; do not silently replace a failed
batch with a passing individual result. Promote the selected passing reports,
fixture limits, ROM hashes and any inherited controls into a compact
`reference/` receipt. Huge traces/captures stay in ignored work/build directories;
their paths are local evidence, not files guaranteed to exist in a new clone.

## Release and handoff

Qualify the exact final candidate, including in-engine visual/audio review, before
publication. A published version identifies immutable bytes. Later fixes need a
new version/post-pass; a pinned old generator reproduces that old release and
is not the starting command for silently changing it. Preserve the full accepted
composition, source recipe, original ROM, prior release and latest real battery.

`python mod.py build` and `python mod.py verify` default to
`build/candidate/Spider-Man-WoS-modded.nds`; the raw `repack-rom` command uses
that candidate path too. Pass `--out build/Spider-Man-WoS-modded.nds` explicitly
to verify the installed build. Raw builds do not perform publication safeguards.

Close DeSmuME and publish through `python tools/playtest.py build`. The publisher
checks the actual battery before/after, creates its content-addressed checkpoint,
requires matching candidate metadata, retains the previous ROM/build metadata,
rejects differing existing rollback ROM/metadata copies and reused versions,
then installs the stable ROM. Checkpoints appear under their final name only
after both data and metadata pass verification; caught checkpoint failures can
be retried without removing a partial named snapshot. Caught publication errors
restore the prior ROM, metadata, receipt and history; incomplete recovery reports
the failed paths and backup location. Abrupt termination/power loss still requires
manual recovery from the retained artifacts. Reinstalling identical bytes keeps
the original publication receipt and its original checkpoint/predecessor links.
Afterward compare stable/canonical SHA, boot/Options version, build/release
metadata and the freshly read battery/checkpoint bytes. Later player saves can
differ from the publication checkpoint; never restore it automatically.
No research save writes to the real battery and no stale emulator states across
ROM changes. Then add the CHANGES section, update README and TASKS to the new
version and run `python tools/doc_contract.py freeze` followed by `check`.

Update TASKS at candidate acceptance, before a long qualification batch, at
publication and before handing off. Record only current objective, candidate /
published identity, completed evidence, unresolved issue and next exact action.
Put detailed receipts in reference, engine discoveries in TECHNICAL, shipped
behavior in CHANGES and user acceptance/rejection in the ROADMAP feedback log. Mark a new
discovery or superseded assumption in its owning section immediately; a late
session summary is too easy to lose. Keep session transcripts out of the docs.

## Maintain documentation

`reference/doc_contract.json` is the machine-checked contract for every
document: what it owns, word limits, required headings and text, an edit policy,
routing (which content goes where), forbidden edits, the version sources that
must agree and the frozen CHANGES sections. `python tools/doc_contract.py check`
lists every violation and `tests.test_document_layout` runs one test per rule.
Before editing a document, read its contract entry. When a check fails, fix the
document; change the contract only when the user changes documentation policy.
A published CHANGES section is frozen: re-freeze it with
`python tools/doc_contract.py freeze --update <version>` only when the user asked
for that correction. ROADMAP and TASKS are written for the player; the other
documents are written for agents and may favor dense, exact reference text.

Use the approved ownership map in AGENTS. Check current profile/source pins,
release history and stable/canonical metadata before updating a version claim;
read the actual battery/checkpoint rather than copying a historical save hash.
Keep implemented, agent-tested and player-confirmed claims separate. Preserve
release dates and immutable receipts when later documentation is reviewed.

Replace TASKS' stale objective/next action rather than appending. The live
roadmap holds current decisions, acceptance criteria and deferred concepts;
old construction pitches must not remain a second active queue. Planning JSON
may retain dated baseline allocations/receipts, but label that scope and point
its current status to the live composition. Do not relabel an old artifact with
a newer version or change a production recipe merely to refresh prose.

Preserve retired designs/catalogs byte for byte in the existing archive before
removing them from live docs:
`python tools/doc_archive.py add <unique-name> --from <file> --title <title> --date <YYYY-MM-DD>`
appends the bytes, records the snapshot date and source revision, and re-pins
the archive hash. Read with `python tools/doc_archive.py list <topic>`, then
`read <name> --toc` or a bounded `--section`. Verify the archive and the whole
documentation contract with
`python -m unittest tests.test_doc_archive tests.test_document_layout -q`.
Archive appends retain the original ZIP/index pair until the new pair verifies.
Caught failures restore both files. Recovery write errors identify the retained
`.archive-recovery-*` directory; an interruption can leave it beside the archive.
Preserve that pair for manual recovery after an interruption or failed rollback.
A documentation-only cleanup does not add emulator coverage or player acceptance.

## Local runtime dependencies

Production generators use standard-library Python plus the existing pinned ARM
assembler support (Keystone in `work/research-libs`, loaded by the kit tools), plus Pillow
when building painted creature materials. Emulator tools
use the pinned melonDS core under `work/emulator`; its fetch/integrity code is in
`emulator_smoke.py`. Image review also needs Pillow. Offline sound authoring additionally
needs NumPy and FFmpeg (`creature_forge_sound_author.py` declares its local path);
shipping builds consume frozen sample hashes and do not regenerate that bank.
Check these once, use the configured interpreter, and record a dependency failure
instead of rediscovering/installing alternate runtimes throughout the task.

Keep emulator tags short and unique. During Reel In pose review, long repeated
tags were associated with native-core faults before emulated execution; a short
tag retry succeeded. A path-length limit is suspected, not proven. Such a host
failure is not a gameplay result. The Reel In boss lab uses its tag once; retain
failed logs when retrying the same explicit candidate with a shorter tag.
