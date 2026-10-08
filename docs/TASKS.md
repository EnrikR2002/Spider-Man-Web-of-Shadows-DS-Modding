# Current work, backend queue and handoff

Updated 2026-10-08 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.8.0 stable `d84ae539`: power puzzle, chapter dialogue, objective board.**
2026-10-08: player was about to playtest v0.7.0 and said to work on whatever
is worthwhile. Lab found a v0.7.0 blocker: the Platform boiler stayed
electrified, so the Platform grate into the Nest never opened (Nest only via
the Stairs grate, boss first). v0.8.0 fixes it: Stairs breaker sets shared
flag 269; lift/throw the boiler; X on the grate. Plus chapter dialogue (new
message ids 0xC4.., accessor rewritten in place) and a Refuge objective
board. Published while DeSmuME was closed; battery (last saved before
v0.7.0) checkpointed. Agent-tested (CHANGES v0.8.0); not player-confirmed.
TECHNICAL "Room scripting and the power puzzle", "Chapter dialogue"; tools
`room_script.py`, `midnight_chapter.add_breaker/add_power_hint/
add_objectives`, `midnight_line.py puzzle`, `tour --start N`.

Next (in order): 1) player verdict on v0.8.0 (breaker findable? hints clear?
Nest/boss difficulty, map readability, Hive spoiler OK?); 2) Signal Leech (original art,
ceiling charge/discharge); 3) Conductor teaser (tunnel blackout, silhouette);
4) proto01 as a chapter room. Flags: 1 local left in 245..275 (245);
138..165 is a verified-free 28-flag pool for the next stateful rooms.
Proposals of 2026-10-07 still await the player's picks (TASM_ROADMAP).
Room scripting is now understood: append batches/groups with
`room_script`, actions = (entity, AG, EG); spawner byte mixes enemies; timers
0x23.

### Handoff commands

Run `python -m unittest discover -s tests` (230/230). Chapter dev candidate from
stable v0.5.0: `python tools/midnight_chapter.py` (from the kept v0.5.0 ROM; `build/midnight-line/
chapter.nds`). Release: `python tools/tasm_kit.py` composes kit + chapter
(`mod.create_build` applies `midnight_chapter.apply_rom` for profiles with
`chapter`). Lab checks (copied saves; add `--rom R`): `python
tools/midnight_line.py tour`, `save-test [--room R]`, `ambush [--native] [--seed N]`,
`visit ROOM [--spawn S --goto X Y --weak --boss-max N --leave X Y]` (any room,
fights, exits), `puzzle` (breaker -> boiler -> grate -> Nest), `tour --start N`.
Map screens: `tools/minimap_cbmp.py`. Evidence:
`work/midnight-line/{chapter-*,weak-*,venom-*}.json`, `work/kit/v0.{6,7,8}.*/`. The older
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
  `build/version-0.8.0` (regenerate: `python tools/tasm_kit.py`). Constants only via the `lit_` table (TECHNICAL
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
  build/releases/<sha>/): v0.7.0 `c56095be` (Nest blocked from the Platform), v0.6.1 `c3010cba`, v0.6.0 `36aa52f8`, v0.5.0 `fd7e4420`, v0.4.1 `da324b3c`, v0.4.0 `5e6465d8` (freeze bug), v0.3.0 `34736eeb`,
  v0.2.1 `00ca471c`, v0.2.0 `935d486b`, v0.1.1 `bcc6974a`. All kit releases before
  v0.4.1 carry the Sense heap bug; do not roll back to them.
- Real Battery path: work/playtest.json. Re-read the latest save while DeSmuME is
  closed before publication/checkpoints; verify wrapper/snapshot bytes. Player only
  launches/Continues/plays/saves/closes. Agent owns other operations. Saves made
  inside the chapter are rejected by ROMs before v0.6.0 (battery intact).

No new Markdown files. Update the six owning documents; keep this under 900 words.
Read archives through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.
