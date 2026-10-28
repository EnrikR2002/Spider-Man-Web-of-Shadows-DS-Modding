# Current work and handoff

Updated 2026-10-28 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

All six repository-audit findings are fixed: failed qualifications return a
failing exit code, enemy scans reject stale
motion ownership, checkpoint failures allow retry, archive failures recover the
ZIP/index pair, the spectacle lab refreshes its player copy, and publication
rejects mismatched retained build metadata. Navigator report APIs remain usable
by their callers. No gameplay or release bytes were edited.

All 45 focused tooling tests pass, including actual command exit codes,
synthetic stale actors, refreshed copies, injected write/verification/rename
failures, recovery retries and retained backups after a failed rollback.
All 705 strict tests pass with zero skips across 96 module subprocesses. The
final archive interruption checks also pass. The documentation contract holds;
exact protected-file observations and validation receipts are in
`reference/tooling_safety.json`.

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

No implementation blocker remains. Meteor Catch's player feel, hardware pacing
and full-route balance remain unconfirmed. Next exact action: launch normally,
buy Meteor Catch after Sky Rake, and try Talon Lift -> hold B -> Y -> plain air A
-> Up+A on the bounce.
Check both facings and R release, then give a verdict before the next skill.
No new skill, release publication or push is requested.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
