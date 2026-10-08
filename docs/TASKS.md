# Current work, backend queue and handoff

Updated 2026-10-07 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.7.0 stable `c56095be`: Midnight Line + The Nest + boss + map.**
Player (2026-10-07, v0.6.1 untested): keep building as much content as
possible. v0.7.0: 8 Hive-room clones under the tracks (rooms 81..88, two
saves, symbiote crowds, ichor-lock ambushes), boss arena from Downtown_Map14
(room 89, reward withheld, death = completed flag), chapter diagram on the
Sewer touch-screen map, message continuations kept, text tree grown for
digit 7. Rooms 76..89; visited flags 252..265; locals from the 245..275 pool
(build report). Agent-tested (CHANGES v0.7.0); not player-confirmed.
Spec `reference/midnight_line.json`; TECHNICAL "Midnight Line chapter build",
"Minimap screens and area room lists", "The Nest and the boss room".

Next (in order): 1) player verdict on v0.7.0 (difficulty of Nest/boss, map
readability, Hive spoiler OK?); 2) power puzzle on the Platform (native
boiler/electric hazards) and objective board in the Refuge; 3) Signal Leech
(original art, ceiling charge/discharge); 4) Conductor teaser. Flag budget is
nearly spent (1 spare): verify 138..165 before adding stateful rooms.
Roadmap/feature/XP-sink proposals sent 2026-10-07 await the player's picks
(TASM_ROADMAP "Proposals awaiting the player"). Research done 2026-10-07
(TECHNICAL "Content toolbox research"): flags 138..165 safe; custom dialogue
proven (message table relocation + bounds + appended strings); spawner byte
mixes any area's enemies; switch/boiler/electric puzzle wiring and timers
(0x23) understood; proto01 is a playable textured prototype level. Build
order when approved: shared cross-room flags + 138..165 pool, dialogue
pipeline, power puzzle, proto01 as a chapter room.

### Handoff commands

Run `python -m unittest discover -s tests` (222/222). Chapter dev candidate from
stable v0.5.0: `python tools/midnight_chapter.py` (from the kept v0.5.0 ROM; `build/midnight-line/
chapter.nds`). Release: `python tools/tasm_kit.py` composes kit + chapter
(`mod.create_build` applies `midnight_chapter.apply_rom` for profiles with
`chapter`). Lab checks (copied saves; add `--rom R`): `python
tools/midnight_line.py tour`, `save-test [--room R]`, `ambush [--native] [--seed N]`,
`visit ROOM [--spawn S --goto X Y --weak --boss-max N --leave X Y]` (any room,
fights, exits). Map screens: `tools/minimap_cbmp.py`. Evidence:
`work/midnight-line/{chapter-*,weak-*,venom-*}.json`, `work/kit/v0.{6,7}.*/`. The older
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
  `build/version-0.6.1` (regenerate: `python tools/tasm_kit.py`). Constants only via the `lit_` table (TECHNICAL
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
  build/releases/<sha>/): v0.6.1 `c3010cba`, v0.6.0 `36aa52f8`, v0.5.0 `fd7e4420`, v0.4.1 `da324b3c`, v0.4.0 `5e6465d8` (freeze bug), v0.3.0 `34736eeb`,
  v0.2.1 `00ca471c`, v0.2.0 `935d486b`, v0.1.1 `bcc6974a`. All kit releases before
  v0.4.1 carry the Sense heap bug; do not roll back to them.
- Real Battery path: work/playtest.json. Re-read the latest save while DeSmuME is
  closed before publication/checkpoints; verify wrapper/snapshot bytes. Player only
  launches/Continues/plays/saves/closes. Agent owns other operations. Saves made
  inside the chapter are rejected by ROMs before v0.6.0 (battery intact).

No new Markdown files. Update the six owning documents; keep this under 900 words.
Read archives through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.
