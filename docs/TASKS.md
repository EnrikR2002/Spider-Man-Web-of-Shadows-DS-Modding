# Current work, backend queue and handoff

Updated 2026-10-13 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.13.0 stable `75faa3ff` (2026-10-13): Overclock, Dragnet, Vortex and a
reworked Substation.** Player 2026-10-13 on v0.12.0: artwork impressive;
background "like a painting", "some roofs pure pitch black", "enemies were
too weak ... my main gripe"; picks: Overclock, a web-focused ground string,
webbing about five enemies with Y to throw them all to him; **"only these 3
more and no more skills"**. Done: three shop rows (TASM_ROADMAP "Round
five"), strength dial on the Yard and the Substation, far skylines, black
gaps filled (CHANGES v0.13.0). Agent-tested, not player-confirmed.

Next (in order): 1) player verdict on the three skills (is held A right
for Dragnet, the Vortex pause window, does Overclock ever show at tier 5,
the four clips) and on the Substation (strength, looks); still open on
v0.11.0: speed feel, Vitality prices and bar colours in DeSmuME, map, Nest;
2) iterate the skills from that verdict (ROADMAP "Round five", last
column): **no new skills**; 3) the agent's recommendation for "what else":
a script boss on the Control Roof or in a fourth Substation room (the kit
now needs crowds and something strong to hit; pieces proven: TECHNICAL
"Script boss research", five lab questions left), then a save room by the
Switchyard (the Refuge is two rooms back and the Roof is hard now), then a
section in a main district with the compiler; 4) the staged crowd backend
(below).
Open: the roof's rare stalled wave, a Substation detail-map screen, Yard
verdict, Leapfrog's pop does not ricochet, R during the rush dash rolls
forward, Perch B in the cycle gap swings, proposals of 2026-10-07.

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
Downtown_Map13/14. A room model is at most 511 units wide. Kit: second
block 6204 of 6400 code bytes, first 7004 of 7936; ability bits 83..95 free;
state below +0x280 (the Both Suits rows sit above it).

### Handoff commands

Run `python -m unittest discover -s tests` (283). Dev candidate of the whole
game without pins: `python work/shop/dev_build.py NAME` (`build/dev-kit/NAME`,
prints the hashes to pin). Lab: `python work/kit/weblab.py ROM LABEL INPUTS`
(sparring Brutes, RAM pokes, summary), `work/kit/newchecks.py ROM`. Look at a
room: `python work/rooms/lab_view.py ROM NAME ROOM X,Y ...` then
`work/rooms/sheet.py OUT.png FRAMES`. Release: `python tools/tasm_kit.py`
(`build/version-X`), lab gates, copy its `mods/*` and `gameplay_profile.json`
into `mods/` and `reference/`, then `python tools/playtest.py build`. Lab
gates (copied saves; `--rom R`): `python tools/kit_lab.py qualify R` (63,
about 50 minutes), `python tools/crash_hunt.py batch 1 12` (now also holds A,
yanks and pauses; odd seeds at tier 5), `python tools/midnight_walk.py all`
(10 routes; a failing route reruns up to three times, fights vary), `python
tools/midnight_line.py tour | puzzle | save-test [--room R]`,
`work/shop/vit_shop_lab.py R`, `work/shop/web_shop_lab.py R`. Evidence:
`work/kit/v0.13.0/`, `work/midnight-line/walk-*.json`, frames under
`build/boot-tests/`.

**Crowd performance:** JIT12 is player-confirmed as the accepted baseline.
AUTOGL 1x + JIT12 renderer trial is pending player verdict
(`work/performance/renderer-player-trial-2026-10-06.json`). Dragnet's
web-line actors are unmeasured in DeSmuME.

**Shared crowd-hit backend staged, unpublished.** Its validation is over the
v0.9.0 kit; the candidates still assemble over the v0.13.0 source and need
requalifying (TECHNICAL "Shared crowd-hit backend candidates").

## Previous queue (deferred)

1. Midnight Line: Signal Leech, teaser, more rooms.
2. Await renderer verdict; then requalify/integrate the staged crowd backend.

## Deferred ideas

Training room ideas (2026-10-06): mixed enemy types, dummy toggle,
aggression presets, damage readout, position reset. Queued research:
HUD/Sense warning, camera, AI, extra suits (reference/suit_roadmap.json), audio.

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
- Prior releases (ROM rollback in build/releases/<sha>/): v0.12.0
  `0ede0422`, v0.11.0 `4f387a21`, v0.10.0 `a928843c`, v0.9.0 `f109a525`,
  v0.8.1 `f68a082e`, v0.8.0 `d84ae539`, v0.7.0 `c56095be`, v0.6.1
  `c3010cba`, v0.6.0 `36aa52f8`, v0.5.0 `fd7e4420`, v0.4.1 `da324b3c`. Kit
  releases before v0.4.1 carry the Sense heap bug. A save made in a room an
  older ROM does not have is rejected by it (battery intact).
- Real Battery path: work/playtest.json. Re-read the latest save while DeSmuME
  is closed before publication/checkpoints; verify wrapper/snapshot bytes.
  Player only launches/Continues/plays/saves/closes.
- Docs can change between sessions: re-read a section before editing it.

No new Markdown files. Update the six owning documents; keep this under 900 words.
Read archives through tools/doc_archive.py in bounded sections. Cache files remain ignored;
prior deletion was rejected by automatic approval review.
