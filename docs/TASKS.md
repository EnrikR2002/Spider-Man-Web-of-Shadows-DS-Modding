# Current work, backend queue and handoff

Updated 2026-10-11 (America/Edmonton). Read this and AGENTS at startup; then only
the section relevant to the task. Shipped history: [CHANGES](CHANGES.md); ROM
knowledge: [TECHNICAL](TECHNICAL.md); combat design: [TASM_ROADMAP](TASM_ROADMAP.md).

## Current work

**v0.10.0 stable `a928843c`: three new Red shop skills on v0.9.0's chapter.**
Player 2026-10-11: has mastered the seven skills ("bread and butter basic"),
wants "more spice"; picked Web Rush, Ricochet and Momentum from eight ideas,
asked for real new Red shop slots (needed for later suits too), said the
ideas were good "but none really blew me away", and allowed background lab
runs while they play. Shipped: ten Red rows (three new, 300/300/400 XP,
ability bits 74..76 in unused saved space), a second kit code block, Web Rush
(A in a ground string), Ricochet and Momentum (passives). Published with
DeSmuME closed; battery unchanged (last saved 2026-10-07 in Sewer_Save02, so
v0.8.1/v0.9.0 are still unplayed). Agent-tested (CHANGES); not player-confirmed.

Next (in order): 1) player verdict on v0.10.0: does Web Rush feel like a
zip (speed, reach, the three kicks, the back tuck)? Ricochet radius and
damage? Momentum too fast or invisible at high tiers? prices? 2) from that,
the "next iteration" column in TASM_ROADMAP "Spice pack" (Leapfrog's pop does
not ricochet yet; R during the rush dash always rolls forward); 3) bring
bolder skill ideas (their words above); 4) player verdict on v0.9.0's
chapter: breaker/boiler/grate hints clear? Nest fights without seals fun?
boss from the corridor OK? Yard door findable, gang strength, roof crates?
5) more Yard, Signal Leech, Conductor teaser, original geometry.
Proposals of 2026-10-07 still await the player's picks (TASM_ROADMAP).

**Chapter state (v0.9.0, unchanged):** walkable Nest (v0.8.1: no red floors
or door seals, boss staged for the corridor, Stairs grate locked until the
Gate) plus the Yard (unused proto01 warehouse behind a Refuge door, Pier
gang). **Release rule:** a chapter room ships only after a walk route crosses
it through real doors and needs no story ability the player lacks (0..4
owned). Tools: `tools/midnight_walk.py`, `tools/room_collision.py`,
`room_doors.add_spawn/add_exit(template=)`; TECHNICAL "Room collision tree",
"Chapter routes on foot", "The Yard".

Limits known: room 91 may use visited flag 267; locals left: 140..165 and
245; the 15 map slots are used. Chapter lines stay on the touch screen until
the room changes (lab). Finale rooms Hive_Map08..10 are spoilers and
Downtown_Map13/14 are the player's next story rooms: do not clone them.

### Handoff commands

Run `python -m unittest discover -s tests` (252). Kit dev candidate without
pins: `python work/shop/dev_build.py NAME` (`build/dev-kit/NAME`); chapter
dev: `python work/midnight-line/scratch/dev_build.py NAME`. Release: `python
tools/tasm_kit.py` (`build/version-X`), lab gates, copy its `mods/*` and
`gameplay_profile.json` into `mods/` and `reference/`, then `python
tools/playtest.py build`. Lab gates (copied saves; `--rom R`): `python
tools/kit_lab.py qualify R` (48), `python tools/crash_hunt.py batch 1 12`
(owns the new skills), `python tools/midnight_walk.py all`, `python
tools/midnight_line.py tour | puzzle | save-test [--room R]`. Run the door
tour alone: beside six other emulator jobs it missed one Nest door once.
New-skill traces: `kit_lab trace ... --bits2 0x1C00 [--tier N]`; shop menu
runs: `work/shop/shop_lab.py`, `shop_refund_lab.py`, `bits_save_lab.py`.
Evidence: `work/kit/v0.10.0/`, `work/kit/evidence.json`,
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

## Evidence and safe resumption

- Kit: source `tools/tasm_kit.{py,s,hex}` and `tools/tasm_kit2.{s,hex}`
  (second block, v0.10.0), `tools/kit_choreography.py`, `tools/kit_clips.py`,
  `tools/training_room.py`; candidate `build/version-0.10.0`. Constants only
  via the `lit_`/`lit2_` tables; `assemble_tasm_kit.py` checks literals and
  outside branches for both blocks. The blocks call each other only through
  their entry tables. Kit code checks other actors with `kit_alive`.
- Research/qualification: `tools/kit_lab.py` (inputs
  `reference/combat-inputs/kit/`). A placed Spidey keeps his stance until a
  real jump; training `--place` needs dy 0.06. Workflow: TECHNICAL "Research
  workflow", "Second kit block".
- Prior releases (ROM rollback in build/releases/<sha>/): v0.9.0 `f109a525`,
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
