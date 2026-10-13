# Current work, backend queue and handoff

Updated 2026-10-12 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.12.0 stable `0ede0422` (2026-10-12): the Substation.** Player 2026-10-12: Round three's
move ideas "weren't that interesting", Thwip Barrage "did sound kinda cool
... more web based ideas. Don't implement just theory craft"; "free to
implement all those other changes you planned". Done: TASM_ROADMAP "Round
four" (eight web-shooter ideas, none built) and three rooms built from
nothing behind a door at the Yard's left wall: Switchyard, Relay Hall (timed
arcs on catwalks), Control Roof (three waves). Status and hash: CHANGES
v0.12.0. Agent-tested, not player-confirmed.

Next (in order): 1) player verdict on the Substation (looks, the climb, arc
timing, roof difficulty) and still on v0.11.0 (speed feel, Vitality prices
and bar colours in DeSmuME, map, Nest); 2) the player's picks from "Round
four": one lab session first settles the shared unknowns (enemy moved by
velocity, a stuck state, hold-A, whether X and Down + A are free); 3) more
places with the compiler (a room is a plan plus a short script in
`tools/midnight_rooms.py`; a save room and a section in a main district are
the obvious next ones); 4) a boss: script pieces are proven (waves, cycling
hazards, a flag), a new character boss is still research (TECHNICAL "Script
boss research").
Open on the Substation: the rare stalled wave (TECHNICAL "The Substation"),
enemy strength dial, a detail-map screen. Older open items: Yard verdict,
Leapfrog's pop does not ricochet, R during the rush dash rolls forward,
Perch B in the cycle gap swings, proposals of 2026-10-07.

**Chapter state:** rooms 76..93. **Release rule:** a chapter room ships only
after a walk route crosses it through real doors and needs no story ability
the player lacks (0..4 owned). Tools: `tools/midnight_walk.py`,
`tools/room_compiler.py`, `tools/midnight_rooms.py`,
`room_doors.add_spawn/add_exit`.

Limits known: visited flags 165 downwards for rooms 92.. (163 next), room
flags from 150 (151 next), locals left 140..149 and 245; the chapter block
has about 900 of 4096 bytes left; the map panel's free space is the middle
(x 30..95, y 66..90) and the top band. Authored rooms may borrow textures
only from districts the player has seen: never Hive_Map08..10 or
Downtown_Map13/14 (finale and the player's next story rooms).

### Handoff commands

Run `python -m unittest discover -s tests` (279). Dev candidate of the whole
game without the chapter pin: `python work/rooms/dev.py NAME`
(`build/dev-kit/NAME`); kit only: `python work/shop/dev_build.py NAME`.
Look at a room: `python work/rooms/lab_view.py ROM NAME ROOM X,Y ...` then
`work/rooms/sheet.py OUT.png FRAMES`. Textures: `work/rooms/tex_sheet.py`,
`tex_big.py`. Release: `python tools/tasm_kit.py` (`build/version-X`), lab
gates, copy its `mods/*` and `gameplay_profile.json` into `mods/` and
`reference/`, then `python tools/playtest.py build`. Lab gates (copied
saves; `--rom R`): `python tools/kit_lab.py qualify R` (48, about 40
minutes), `python tools/crash_hunt.py batch 1 12`, `python
tools/midnight_walk.py all` (10 routes; a failing route reruns up to three
times, fights vary), `python tools/midnight_line.py tour | puzzle |
save-test [--room R]`, `work/shop/vit_shop_lab.py R`. Evidence:
`work/kit/v0.12.0/`, `work/midnight-line/walk-*.json`, frames under
`build/boot-tests/`.

**Crowd performance:** JIT12 is player-confirmed as the accepted baseline.
AUTOGL 1x + JIT12 renderer trial is pending player verdict
(`work/performance/renderer-player-trial-2026-10-06.json`).

**Shared crowd-hit backend staged, unpublished.** Its validation is over the
v0.9.0 kit; the candidates need requalifying (TECHNICAL "Shared crowd-hit
backend candidates").

**v0.5.0 Test Upgrades sparring** (included since v0.6.0): feel not
player-confirmed. The Control Roof is the second place to try skills.

## Previous queue (deferred)

1. Midnight Line: Signal Leech, teaser, more rooms.
2. Await renderer verdict; then requalify/integrate the staged crowd backend.
3. Later research: enemy state 24/action 41, boss rooms.

## Deferred ideas

Training room ideas offered 2026-10-06: mixed enemy types, wave/timer
challenge (the Control Roof is a first one), dummy toggle, aggression
presets, damage readout, position reset. Queued research: HUD/Sense warning,
camera, AI, extra suits (reference/suit_roadmap.json; shop rows and 19 free
ability bits exist), audio.

2099 replaces Black after TASM; preserve A/story gates. Theorycraft only:
TASM_ROADMAP "Spider-Man 2099" (2026-10-11).

## Evidence and safe resumption

- Kit: source `tools/tasm_kit.{py,s,hex}` and `tools/tasm_kit2.{s,hex}`
  (second block), `tools/kit_choreography.py`, `tools/kit_clips.py`,
  `tools/training_room.py`. Constants only via the `lit_`/`lit2_` tables;
  `assemble_tasm_kit.py` checks literals and outside branches for both
  blocks. Kit code checks other actors with `kit_alive`.
- Research/qualification: `tools/kit_lab.py` (inputs
  `reference/combat-inputs/kit/`). A placed Spidey keeps his stance until a
  real jump. Workflow: TECHNICAL "Research workflow", "Second kit block",
  "Room compiler" (harness limits).
- Prior releases (ROM rollback in build/releases/<sha>/): v0.11.0
  `4f387a21`, v0.10.0 `a928843c`, v0.9.0 `f109a525`, v0.8.1 `f68a082e`,
  v0.8.0 `d84ae539`, v0.7.0 `c56095be`, v0.6.1 `c3010cba`, v0.6.0
  `36aa52f8`, v0.5.0 `fd7e4420`, v0.4.1 `da324b3c`. Kit releases before
  v0.4.1 carry the Sense heap bug. A save made in a room an older ROM does
  not have is rejected by it (battery intact): the Substation needs v0.12.0.
- Real Battery path: work/playtest.json. Re-read the latest save while DeSmuME
  is closed before publication/checkpoints; verify wrapper/snapshot bytes.
  Player only launches/Continues/plays/saves/closes.
- Docs can change between sessions: re-read a section before editing it.

No new Markdown files. Update the six owning documents; keep this under 900 words.
Read archives through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.
