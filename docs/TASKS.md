# Current work and handoff

Updated 2026-10-28 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

Crane Row feels lame next to Midnight Line (player, 2026-10-28). An Opus
advisor diagnosed nine same-spawner rooms with no ramp, a crane that never acts
and a wall-box hoist with no boss meter. First slice, **unpublished and
agent-tested only**: `tools/crane_arm.py` makes the Long Arm a three-act fight
(no start add; Maw backup at two thirds health; 28-frame tells, chained second
slam and a left-side Maw at a third) with the native boss meter. Receipt:
`reference/crane_arm.json`; design: ROADMAP "Crane Row"; contracts: TECHNICAL
"Long Arm three acts".

Second slice, same date, **unpublished**: the player also found the Crane map
weird and unconnected. `tools/crane_navigation.py` now draws one ring of touching
rooms with short necks, and `tools/crane_map.py` is a structure-found, chainable
post-pass for it (receipt `reference/crane_map.json`; TECHNICAL "Crane Row ring
map"). It must run last on the composed candidate.

Third slice, same date, **unpublished**: `tools/crane_vista.py` opens the Long
Arm's backdrop (lattice towers, rail, moored freighter, far quay; collision
byte-identical; receipt `reference/crane_vista.json`). The map and vista passes
commute; chain them after the composed `crane_arm` build.

Evidence: 11 new unit checks run the assembled ARM against fixtures and the
script edits against the published room. Native-input Black no-refill and Red
hoist fights reach all three acts; Red wins untouched, the Black bot is
marginal. Win, 700 quiet frames and a cleared revisit pass; the four Long Arm
doors pass like the parent. No gameplay or release bytes were published.

## Published build

Stable `build/Spider-Man-WoS-modded.nds` remains **v0.37.0** and matches its
immutable publication pin, build metadata, recipe and release history. No ROM
was rebuilt or published for these tooling fixes. The previous v0.36.0 ROM,
metadata and recipe remain preserved.

The freshly read actual Battery has a valid 634-byte DSV wrapper and 512-byte
payload. It contains later progress than the publication checkpoint; that old
checkpoint is an observation, not a restore instruction. No research save was
adopted or written to the actual Battery.

Meteor Catch still costs 200 XP after Sky Rake; eleven Black rows total 1,650
XP. Its prior six-metric Terra gate, 30 gameplay/save cases and six native input
pairs are recorded in `reference/meteor_catch.json`. Those results belong to the
published game; this tooling task adds no gameplay qualification or player verdict.

## Blockers and next exact action

The ring map is agent-tested (unit tests, one melonDS capture on v0.37.0) and
not yet chained into the composed candidate. Not verified: the Conductor's boss
meter in-engine (build with `--no-meter` to
drop the change), the full 30-door and Midnight sweeps, and any save/Continue
case; the JIT-warp labs fail in a fresh worktree and `crane_walk entry` fails on
the published build too (DEVELOPMENT "Labs in a fresh git worktree"). Fairness
and fun are player gates. Next exact action: the player decides whether to try
the candidate; to publish, add its profile, run the missing controls serially and
use `tools/playtest.py build`. Unbuilt follow-ups are in ROADMAP. Meteor Catch's
verdict is still pending.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
