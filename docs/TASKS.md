# Current work, backend queue and handoff

Updated 2026-10-14 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.16.1 stable `5b0d6f55` (2026-10-14): Crane Row polish.**
Published through playtest; latest battery `3a4e7c9b` byte-identical,
wrapper/snapshots verified, prior ROM/compositions retained. Agent-tested;
player verdict pending. **No more skills.**

v0.15.1's Signal Leech/Substation/Vortex changes remain player-pending;
CHANGES owns their release evidence.

**Crane Row:** `build/version-0.16.1-qualified/Versioned.nds` reproduces
through normal composition. User requested an ambitious pre-player visual/feel
sweep. All12 rooms have new materials, lattice cranes, ship/cargo detail,
broader harbor panorama, catwalk fittings, wayfinding and distinct interiors
(`tools/crane_art.py`). ARM9 `abfbb112`, BSP/OBJ/maps/kit stay byte-exact
against0.16.0; only24 visual resources and2 strings change. Twelve rooms,
two loops, Office save, lever/shortcuts, cache, Crown crew and hoist remain.
Rooms96..107/area6/visits161..152/149/148/milestones140..146 own an8KiB block.
Passed:339 suite +30 post-driver targeted checks; all30 Crane/all13 Midnight
real-door cases;12-room/elevated visual review; Office save/Continue, power,
cache, warning/live and refuge controls. Red extra kit/Vitality and Black
Vitality III win and exit/revisit without lab health refills. Roof lab now
leaves enemies native and avoids post-win door drift; baseline control passes.
Exact-code inheritance retains0.16.0's68 kit/12 crash/native parity evidence.
Publication/save proof and preview: `work/crane-row/polish/`; CHANGES owns limits.
Next: player feedback on visuals, routes, encounters and hoist; iterate existing
content. No player verdict, frame-rate gain or first-visit duration measured.
Player enters through Pier_Save02's new right door, uses X at high markers
and otherwise follows the usual launch/Continue/save/close flow. Player
verdict and first-visit duration unmeasured. TECHNICAL "Crane Row construction"
owns details; Grid/Skyline deferred, Hive post-story.

Signal Leech: room94/visited163/defeated151. Prior death/save evidence:
TECHNICAL "Signal Leech implementation".

Pending verdict: Dragnet held A, Overclock tier5; v0.11.0 speed, Vitality,
map, Nest/Yard. Crowd backend remains deferred.
Open: Leapfrog's pop does not ricochet, R during the rush dash rolls
forward, Perch B in the cycle gap swings, proposals of 2026-10-07.

**Chapter state:** shipped rooms76..95 plus Crane96..107. **Release rule:** a chapter room ships only
after a walk route crosses it through real doors and needs no story ability
the player lacks (0..4 owned). Tools: `tools/midnight_walk.py`,
`tools/room_compiler.py`, `tools/midnight_rooms.py`,
`room_doors.add_spawn/add_exit`.

Limits known: Crane allocates rooms96..107 and visits161..152/149/148;
milestones140..146 leave147/245 in the audited pool. Its8KiB extension
owns lookup/map/message/adapters, retaining Midnight's4KiB exactly.
Authored rooms may borrow textures
only from districts the player has seen: never Hive_Map08..10 or
Downtown_Map13/14. Vertex scale128 supports wider scenery (not a511-unit
global limit). Kit: second
block 6628 of 6656 code bytes, first 7096 of 7936; ability bits 83..95 free;
state below +0x280 (the Both Suits rows sit above it).

### Handoff commands

Run `python -m unittest discover -s tests` (339 expected). Crane full-release
generator: `python tools/crane_row.py --release-dir build/NAME`; tasm_kit is
the frozen0.15.1 parent component. Dev candidate of the whole
game without pins: `python work/shop/dev_build.py NAME` (`build/dev-kit/NAME`,
prints the hashes to pin). Lab: `python work/kit/weblab.py ROM LABEL INPUTS`
(sparring Brutes, RAM pokes, summary), `work/kit/newchecks.py ROM`. Look at a
room: `python work/rooms/lab_view.py ROM NAME ROOM X,Y ...` then
`work/rooms/sheet.py OUT.png FRAMES`. Preserve Crane when changing the kit:
deliberately rebase its parent ARM9 guard/profile and qualify the combined
build. Publish the accepted recipe through `python tools/playtest.py build`. Lab
gates (copied saves; `--rom R`): `python tools/kit_lab.py qualify R` (68,
about 50 minutes), `python tools/crash_hunt.py batch 1 12` (now also holds A,
yanks and pauses; odd seeds at tier 5), `python tools/midnight_walk.py all`
(13 routes; a failing route reruns up to three times, fights vary), `python
tools/midnight_line.py tour | puzzle | save-test [--room R]`,
`work/shop/vit_shop_lab.py R`, `work/shop/web_shop_lab.py R`. Evidence:
`work/kit/v0.14.0/`, `work/midnight-line/walk-*.json`, frames under
`build/boot-tests/`.

**Crowd performance:** JIT12 is player-confirmed. AUTOGL 1x trial pending
(`work/performance/renderer-player-trial-2026-10-06.json`). Dragnet lines
are unmeasured in DeSmuME.

**Shared crowd-hit backend staged, unpublished.** Its validation is over the
v0.9.0 kit; the candidates still assemble over the v0.13.0 source and need
requalifying (TECHNICAL "Shared crowd-hit backend candidates").

## Previous queue (deferred)

Training/HUD/art proposals deferred; Conductor teaser remains an idea.

1. Midnight Line: player verdict on Signal Leech, teaser, more rooms.
2. Await renderer verdict; then requalify/integrate the staged crowd backend.

## Deferred ideas

Training: mixed enemies, dummy toggle, aggression presets, position reset.
HUD/Sense cues, campaign art, camera, AI, suits (reference/suit_roadmap.json),
audio remain ideas. Visible damage panels were rejected (CHANGES);
damage telemetry stays private.

2099 replaces Black after TASM; preserve A/story gates. Theorycraft only:
TASM_ROADMAP "Spider-Man 2099" (2026-10-11).

## Evidence and safe resumption

- Kit: source `tools/tasm_kit.{py,s,hex}` and `tools/tasm_kit2.{s,hex}`
  (second block; its web block has its own literal table), `tools/kit_choreography.py`,
  `tools/kit_clips.py`, `tools/training_room.py`. Constants only via the
  `lit_`/`lit2_`/`lit3_` tables, tables as `.word` (never `.byte`);
  `assemble_tasm_kit.py` checks literals and outside branches for both
  blocks. Kit code checks other actors with `kit_alive`.
- Research/qualification: `tools/kit_lab.py` (inputs
  `reference/combat-inputs/kit/`). A placed Spidey keeps his stance until a
  real jump. Workflow: TECHNICAL "Research workflow", "Second kit block",
  "Web lines, built hits and the web skills", "Room compiler".
- Rollback: build/releases/<sha>/; exact releases in reference/releases.json
  and CHANGES. Releases before v0.4.1 carry the Sense heap bug. A save in a room an
  older ROM does not have is rejected by it (battery intact).
- Real Battery path: work/playtest.json. Re-read the latest save while DeSmuME
  is closed before publication/checkpoints; verify wrapper/snapshot bytes.
  Player only launches/Continues/plays/saves/closes.
- Docs can change between sessions: re-read a section before editing it.

No new Markdown. Update owning documents; stay under 900 words.
Read archives through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.
