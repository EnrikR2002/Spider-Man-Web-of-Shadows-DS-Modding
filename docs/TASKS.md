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

Fourth slice, same date, **unpublished**: `tools/crane_drop.py`, composed into
`tools/crane_arm.py`, makes the crane act. Freight and Dry Dock hang a container
that lowers on its hook when the player nears, lands, opens and releases the crew;
Crown's Hunters arrive the same way (TECHNICAL "Crane cargo drops"). Scenery only;
the published crew spawners and callbacks are untouched. The four passes compose
into `build/crane-composed-vm/Versioned.nds` (sha `372dfecc...`, vista and map in
either order give the same ROM). `crane_arm` also rebases onto a later ROM:
`--source <rom>` asserts every hook, room and table and bumps the next minor.

Evidence: 24 unit checks for the hoist and cargo drops run the assembled ARM
against fixtures and the script edits against the published rooms. Native-input
Red hoist fights win untouched on the cargo and the composed candidates (frame
2044) with a saved win, 700 quiet frames and a cleared revisit; the Black bot is
marginal. Lab frame sheets show the drop in Freight and Dry Dock; Crown's was
traced by variables. Six of nine cleared-room door crossings pass; the other three
fail identically on v0.37.0. No gameplay or release bytes were published.

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

The composed candidate is agent-tested only. Not verified: the Conductor's boss
meter in-engine (build with `--no-meter` to drop the change), the full 30-door and
Midnight sweeps, the Black no-refill fight on the cargo build, any save/Continue
case and any hardware run; the JIT-warp labs fail in a fresh worktree and
`crane_walk entry` and three ground-door crossings fail on the published build too
(DEVELOPMENT "Labs in a fresh git worktree"). Fairness and fun are player gates.
Next exact action: the player tries `build/crane-composed-vm/Versioned.nds` (or
regenerates it from the tools) and gives a verdict; to publish, rebase onto the
then-current published ROM (the unpublished boarding v0.38 candidate lives on
another branch), add the profile, run the missing controls serially and use
`tools/playtest.py build`. Unbuilt follow-ups are in ROADMAP. Meteor Catch's
verdict is still pending.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
