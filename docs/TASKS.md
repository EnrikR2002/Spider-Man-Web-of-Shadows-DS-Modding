# Current work, backend queue and handoff

Updated 2026-10-12 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.11.0 stable `4f387a21` (2026-10-12): feedback pass on v0.10.0.** Player
2026-10-11, answering "Round two": new moves "not really that impressed ...
come up with new ones"; "just vitality for now"; quick fixes first; then
research only ("don't create anything yet") so a later session can build
fast. Shipped (CHANGES): Reflex 1.10 / Sense 1.20 and Momentum one tier
earlier, restoring native speed from tier 3; Vitality I..III (Both Suits);
the chapter's own map screen; closed hatches; Nest strength ramp.
Agent-tested, not player-confirmed.

Next (in order): 1) player verdict: speed feel, Vitality prices and bar
colours (seen only in the lab's melonDS: check DeSmuME), map, Nest
difficulty; 2) the player's picks from TASM_ROADMAP "Round three" (Rodeo,
combo wheel, Wall Bounce, Thwip Barrage, Live Wire, Ceiling Stalk); 3) when
asked for new places or a boss, start from TECHNICAL "Room compiler
research" (collision from boxes is proven in game; next textured quads on a
Test_Surfaces01 template, format-5 textures, camera bounds) and "Script boss
research" (a script loop toggling hazards is proven; next smashable health).
Older open items: Yard verdict, Leapfrog's pop does not ricochet, R during
the rush dash rolls forward, Perch B in the cycle gap swings, proposals of
2026-10-07.

**Chapter state:** v0.9.0 rooms (walkable Nest, Yard) with the v0.11.0 map,
hatches and dial. **Release rule:** a chapter room ships only after a walk
route crosses it through real doors and needs no story ability the player
lacks (0..4 owned). Tools: `tools/midnight_walk.py`,
`tools/room_collision.py` (`compile_boxes`), `room_doors.add_spawn/add_exit`.

Limits known: room 91 may use visited flag 267; locals left: 140..165 and
245; map area 5 holds rooms up to 114 (free colour slots remain). Chapter
lines cover the touch screen until the room changes. Finale rooms
Hive_Map08..10 are spoilers and Downtown_Map13/14 are the player's next story
rooms: do not clone them.

### Handoff commands

Run `python -m unittest discover -s tests` (260). Kit dev candidate
without pins: `python work/shop/dev_build.py NAME` (`build/dev-kit/NAME`).
Release: `python tools/tasm_kit.py` (`build/version-X`), lab gates, copy its
`mods/*` and `gameplay_profile.json` into `mods/` and `reference/`, then
`python tools/playtest.py build`. Lab gates (copied saves; `--rom R`):
`python tools/kit_lab.py qualify R` (48, about 40 minutes), `python
tools/crash_hunt.py batch 1 12`, `python tools/midnight_walk.py all`,
`python tools/midnight_line.py tour | puzzle | save-test [--room R]`,
`work/shop/vit_shop_lab.py R`. Scratch labs in `work/midnight-line/scratch/`:
`damage_probe.py`, `map_view.py`, `surface_exp.py`, `hatch_exp.py`,
`bsp_proof_build.py`. Evidence: `work/kit/v0.11.0/`, `work/kit/evidence.json`,
`work/midnight-line/walk-*.json`.

**Crowd performance:** JIT12 is player-confirmed as the accepted baseline.
AUTOGL 1x + JIT12 renderer trial is pending player verdict
(`work/performance/renderer-player-trial-2026-10-06.json`).

**Shared crowd-hit backend staged, unpublished.** Its validation is over the
v0.9.0 kit; the candidates still assemble over v0.10.0 but need requalifying
(TECHNICAL "Shared crowd-hit backend candidates").

**v0.5.0 Test Upgrades sparring** (included since v0.6.0): feel not
player-confirmed. It is the place to try the new skills (three Brutes).

## Previous queue (deferred)

1. Midnight Line: Signal Leech, teaser, more rooms.
2. Await renderer verdict; then requalify/integrate the staged crowd backend.
3. Later research: enemy state 24/action 41, boss rooms.

## Deferred ideas

Training room ideas offered 2026-10-06: mixed enemy types, wave/timer
challenge, dummy toggle, aggression presets, damage readout, position reset.
Queued research: HUD/Sense warning, camera, AI, extra suits
(reference/suit_roadmap.json; shop rows and 19 free ability bits now exist),
audio.

2099 replaces Black after TASM; preserve A/story gates. Theorycraft only:
TASM_ROADMAP "Spider-Man 2099" (2026-10-11).

## Evidence and safe resumption

- Kit: source `tools/tasm_kit.{py,s,hex}` and `tools/tasm_kit2.{s,hex}`
  (second block), `tools/kit_choreography.py`, `tools/kit_clips.py`,
  `tools/training_room.py`; candidate `build/version-0.11.0`. Constants only
  via the `lit_`/`lit2_` tables; `assemble_tasm_kit.py` checks literals and
  outside branches for both blocks. The blocks call each other only through
  their entry tables. Kit code checks other actors with `kit_alive`.
- Research/qualification: `tools/kit_lab.py` (inputs
  `reference/combat-inputs/kit/`). A placed Spidey keeps his stance until a
  real jump; training `--place` needs dy 0.06. Workflow: TECHNICAL "Research
  workflow", "Second kit block".
- Prior releases (ROM rollback in build/releases/<sha>/): v0.10.0 `a928843c`, v0.9.0 `f109a525`,
  v0.8.1 `f68a082e`, v0.8.0 `d84ae539` and v0.7.0 `c56095be` (Nest not
  walkable), v0.6.1 `c3010cba`, v0.6.0 `36aa52f8`, v0.5.0 `fd7e4420`, v0.4.1
  `da324b3c`. Kit releases before v0.4.1 carry the Sense heap bug. A save
  with the new skills bought is harmless on older ROMs (they never read
  those bits).
- Real Battery path: work/playtest.json. Re-read the latest save while DeSmuME
  is closed before publication/checkpoints; verify wrapper/snapshot bytes.
  Player only launches/Continues/plays/saves/closes. Saves made inside the
  chapter are rejected by ROMs before v0.6.0 (battery intact).
- Docs can change between sessions: re-read a section before editing it.

No new Markdown files. Update the six owning documents; keep this under 900 words.
Read archives through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.
