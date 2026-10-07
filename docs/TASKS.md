# Current work, backend queue and handoff

Updated 2026-10-07 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.6.0 stable `36aa52f8`: Midnight Line first station (exploration slice).**
Authorized 2026-10-06 and prioritized over new combat mechanics. Entrance:
Sewer_Save02's far right wall. Five rooms 76-80 (sanitized native subway
clones, midnight palette grade), loop Platform -> Service -> Switching ->
Gallery -> Platform, Refuge with a working save sphere, encounters in Service
and Switching. Persistence uses native flags 252..275 (visited 252..256,
milestones 257..259, puzzle 260..267, remapped encounters 268..275).
Agent-tested: 14/14 doors, Refuge save/Continue, death minigame, kit 31/31,
crash hunt 12/12, 215 unit tests. Not player-confirmed. Spec:
`reference/midnight_line.json`; build: TECHNICAL "Midnight Line chapter build
(v0.6.0)"; formats: "Native doors, spawns and game variables".

Next (in order): 1) player feedback on route feel, discoverability and fights;
2) power puzzle (Switching House: native switch/gate entities and `0x1D`/`0x26`
on flags 257/260+, objective board in the Refuge); 3) Signal Leech (original
model/texture on an existing rig, ceiling charge/discharge, defeatable with
native attacks); 4) Conductor teaser (light blackout + silhouette; Sewer_Map01's
route-following silhouette NPC is a candidate); 5) chapter minimap/area label
(bottom screen shows the source rooms' maps, Refuge says "Pier"). Gallery's
mini-boss stays dormant outside its story beat.

### Handoff commands

Run `python -m unittest discover -s tests` (215/215). Chapter dev candidate from
stable v0.5.0: `python tools/midnight_chapter.py` (`build/midnight-line/
chapter.nds`). Release: `python tools/tasm_kit.py` composes kit + chapter
(`mod.create_build` applies `midnight_chapter.apply_rom` for profiles with
`chapter`). Lab checks (copied saves; add `--rom R`): `python
tools/midnight_line.py tour`, `save-test`, `ambush [--native] [--seed N]`.
Evidence: `work/midnight-line/chapter-*.json`, `work/kit/v0.6.0/`. The older
`stage-platform`/`probe-room` shells and the padding-bit codec
(`midnight_progress.py`) are superseded research; do not ship them.

**Crowd performance:** JIT12 is player-confirmed as the accepted baseline.
AUTOGL 1x + JIT12 renderer trial is pending player verdict; evidence is
`work/performance/renderer-player-trial-2026-10-06.json` and TECHNICAL
"Crowd combat performance".

**Shared crowd-hit backend staged, player ROM unchanged.** Area, Skyjack and
combined candidates pass their isolated checks; velocity candidates still drift
outside walls. Sources: `tools/crowd_{hits.s,backend.py,area_lab.py}`;
validation: `work/kit/crowd-backend/validation.json`.

**v0.5.0 `fd7e4420` (included in v0.6.0): Test Upgrades sparring.** Feel is
not player-confirmed. Details: CHANGES v0.5.0/TECHNICAL "Training room".

## Previous queue (deferred; Midnight Line first)

1. Midnight Line puzzle, Signal Leech and teaser (Current work list).
2. Await renderer verdict; then integrate/qualify the staged crowd backend.
3. Player-test v0.5.0 sparring and v0.4.1 move feel. Kit iterations remain
   deferred; later research includes enemy state 24/action 41 and boss rooms.

## Deferred combat ideas

Kit extensions and additional shop skills remain in TASM_ROADMAP. Midnight Line
is now the authorized priority; leave combat mechanics steady while the player
learns the kit.

## Training room ideas offered to the player (2026-10-06)

Mixed enemy types (needs character-type ids and loaded assets), a wave
counter or timer challenge, a toggle for the passive dummy, enemy aggression
or count presets, a combo/damage readout, quick reset of positions.

## Backend ideas retained

Training controls/challenges, expanded shop/ownership/refund migration, HUD/Sense
warning, camera, AI, extra suits and audio remain queued research. Selected suits:
reference/suit_roadmap.json. Preserve shared progression/traversal. Renderer and
crowd-backend work are approved but unpublished; Midnight Line now takes priority.

## Evidence and safe resumption

- Kit: source `tools/tasm_kit.{py,s,hex}`, `tools/kit_choreography.py`,
  `tools/kit_clips.py`, `tools/training_room.py`; candidate
  `build/version-0.6.0` (regenerate: `python tools/tasm_kit.py`). Constants only via the `lit_` table (TECHNICAL
  pitfalls); `assemble_tasm_kit.py` checks literals and native branches. Kit code
  checks other actors with `kit_alive`; remaining Skyjack position drift has
  the separate velocity-only candidate above.
- Research/qualification: `tools/kit_lab.py` (inputs `reference/combat-inputs/kit/`;
  evidence work/kit/evidence.json, 31/31). Fixtures: `--near U`, `--at X`,
  `--phantom DX`, `--place DX:DY|skip` (training and arena; arena is
  non-deterministic). Lab teleports now use `kit_lab.teleport` (motion base and
  probes); older lab runs corrupted the heap. Freeze/crash hunting:
  `python tools/crash_hunt.py batch FIRST LAST --rom R` (outputs work/crash/),
  `regs STATE --ram RAM` decodes aborts. Workflow: TECHNICAL "Research workflow".
- Prior releases (candidate mods + recipe in build/version-X, ROM rollback in
  build/releases/<sha>/): v0.5.0 `fd7e4420`, v0.4.1 `da324b3c`, v0.4.0 `5e6465d8` (freeze bug), v0.3.0 `34736eeb`,
  v0.2.1 `00ca471c`, v0.2.0 `935d486b`, v0.1.1 `bcc6974a`. All kit releases before
  v0.4.1 carry the Sense heap bug; do not roll back to them.
- Real Battery path: work/playtest.json. Re-read the latest save while DeSmuME is
  closed before publication/checkpoints; verify wrapper/snapshot bytes. Player only
  launches/Continues/plays/saves/closes. Agent owns other operations. Saves made
  inside the chapter are rejected by ROMs before v0.6.0 (battery intact).

No new Markdown files. Update the six owning documents; keep this under 900 words.
Read archives through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.
