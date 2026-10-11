# Current work, backend queue and handoff

Updated 2026-10-11 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.9.0 stable `f109a525`: walkable Nest (v0.8.1) plus the Yard.** Player
2026-10-11 (v0.8.0): sealed in "the hive section" between goo above and a red
platform needing a power-up; quit, lost a little progress; asked to keep
advancing the map and make everything work. That was the Gate, entered
through the Stairs grate. Real-input walks showed the Nest could never be
finished: red floors need Sledgehammer Slam (the withheld boss reward; the
player owns story abilities 0..4), Nest door seals can strand Spidey, the boss
room sealed him in its entry corridor. v0.8.1 `f68a082e` removes the red
floors and seals, stages the boss for the corridor entrance, locks the Stairs
grate until the Gate is reached, adds hint lines. v0.9.0 adds the Yard: the
unused proto01 warehouse behind a new door in the Refuge's left wall, with a
Pier gang. Both published with DeSmuME closed; battery unchanged (last saved
2026-10-07 in Sewer_Save02). Agent-tested (CHANGES); not player-confirmed.

Tools: `tools/midnight_walk.py` (walk routes: real inputs, real doors; `all
--rom R`), `tools/room_collision.py` (collision tree, `solid_at`, map PNG),
`room_doors.add_spawn/add_exit(template=)`. TECHNICAL "Room collision tree",
"Chapter routes on foot", "The Yard".

**Release rule:** a chapter room ships only after a walk route crosses it
through real doors, and it may need no story ability the player lacks. Door
tours that teleport onto triggers prove links only.

Next (in order): 1) player verdict on v0.9.0: breaker/boiler/grate hints
clear? Nest fights without seals fun or too easy to run past? boss from the
corridor OK? Yard door findable, gang too weak/strong, roof crates fun? Hive
spoiler OK? 2) more Yard: second gang wave or a use for its two dead
switches; 3) Signal Leech (original art); 4) Conductor teaser; 5) original
geometry now that collision is decoded (needs a tree builder and model work).
Proposals of 2026-10-07 still await the player's picks (TASM_ROADMAP).

Limits known: room 91 may use visited flag 267; locals left: 140..165 and
245; the 15 map slots are used (find another free 5-colour slot before room
91 goes on the diagram). Chapter lines stay on the touch screen until the
room changes (lab). Finale rooms Hive_Map08..10 are spoilers (Mega Venom) and
Downtown_Map13/14 are the player's next story rooms: do not clone them.

### Handoff commands

Run `python -m unittest discover -s tests` (248). Chapter dev candidate:
`python work/midnight-line/scratch/dev_build.py NAME` (unpinned ARM9) or
`python tools/midnight_chapter.py`. Release: `python tools/tasm_kit.py`
(`build/version-X`), lab gates, copy its `mods/*` and `gameplay_profile.json`
into `mods/` and `reference/`, then `python tools/playtest.py build`. Lab
gates (copied saves; `--rom R`): `python tools/midnight_walk.py all`,
`python tools/midnight_line.py tour | puzzle | save-test [--room R]`,
`python tools/kit_lab.py qualify R`, `python tools/crash_hunt.py batch 1 12`.
Scratch helpers in `work/midnight-line/scratch/`: `dump_ags.py` (decoded room
scripts), `scan.py` (collision scanlines), `probe.py`, `walk_show.py`,
`*_exp.py`. Evidence: `work/midnight-line/walk-*.json`, `work/kit/v0.9.0/`.

**Crowd performance:** JIT12 is player-confirmed as the accepted baseline.
AUTOGL 1x + JIT12 renderer trial is pending player verdict; evidence is
`work/performance/renderer-player-trial-2026-10-06.json` and TECHNICAL
"Crowd combat performance".

**Shared crowd-hit backend staged, player ROM unchanged.** Area, Skyjack and
combined candidates pass their isolated checks; velocity candidates still drift
outside walls. Sources: `tools/crowd_{hits.s,backend.py,area_lab.py}`;
validation: `work/kit/crowd-backend/validation.json`.

**v0.5.0 `fd7e4420` (included since v0.6.0): Test Upgrades sparring.** Feel is
not player-confirmed. Details: CHANGES v0.5.0/TECHNICAL "Training room".

## Previous queue (deferred; Midnight Line first)

1. Midnight Line: Signal Leech, teaser, more rooms (Current work list).
2. Await renderer verdict; then integrate/qualify the staged crowd backend.
3. Player-test v0.5.0 sparring and v0.4.1 move feel. Kit iterations remain
   deferred; later research includes enemy state 24/action 41 and boss rooms.

## Deferred ideas

Kit extensions and shop skills: TASM_ROADMAP; leave combat steady while the
player learns the kit. Training room ideas offered 2026-10-06: mixed enemy
types, wave/timer challenge, dummy toggle, aggression presets, damage readout,
position reset. Queued research: expanded shop/ownership, HUD/Sense warning,
camera, AI, extra suits (reference/suit_roadmap.json), audio.

## Evidence and safe resumption

- Kit: source `tools/tasm_kit.{py,s,hex}`, `tools/kit_choreography.py`,
  `tools/kit_clips.py`, `tools/training_room.py`; candidate
  `build/version-0.9.0` (regenerate: `python tools/tasm_kit.py`). Constants only
  via the `lit_` table (TECHNICAL pitfalls); `assemble_tasm_kit.py` checks
  literals and native branches. Kit code checks other actors with `kit_alive`.
- Research/qualification: `tools/kit_lab.py` (inputs `reference/combat-inputs/kit/`;
  31/31). Lab teleports use `kit_lab.teleport`; a placed Spidey keeps his
  stance until a real jump. Freeze/crash hunting: `python tools/crash_hunt.py
  batch FIRST LAST --rom R` (outputs work/crash/). Workflow: TECHNICAL
  "Research workflow".
- Prior releases (ROM rollback in build/releases/<sha>/): v0.8.1 `f68a082e`,
  v0.8.0 `d84ae539` and v0.7.0 `c56095be` (Nest not walkable), v0.6.1 `c3010cba`, v0.6.0
  `36aa52f8`, v0.5.0 `fd7e4420`, v0.4.1 `da324b3c`. Kit releases before v0.4.1
  carry the Sense heap bug; do not roll back to them.
- Real Battery path: work/playtest.json. Re-read the latest save while DeSmuME is
  closed before publication/checkpoints; verify wrapper/snapshot bytes. Player only
  launches/Continues/plays/saves/closes. Saves made inside the chapter are
  rejected by ROMs before v0.6.0 (battery intact).
- Docs can change between sessions (TECHNICAL gained a source-language note on
  2026-10-11): re-read a section before editing it.

No new Markdown files. Update the six owning documents; keep this under 900 words.
Read archives through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.
