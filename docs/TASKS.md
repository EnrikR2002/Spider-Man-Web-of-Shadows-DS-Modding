# Current work and handoff

Updated 2026-10-28 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

Boarding with Wing Ripper is implemented, qualified and published as v0.38.0.
Previous work was pushed to GitHub main through `28620b1` before implementation.
Task source is on `codex/2099-boarding`; new work is committed locally, not pushed.
No additional skill or sound rework is requested.

The independent 275 XP Black row (event397/bit88) latches a supported boss during
a jump or heavy Web Yank zip while holding toward. Y rakes; A tears and kicks
off; R releases. Native attacks shake the rider off. Twelve Black rows total
1,925 XP; prior purchase records, abilities and the 32 KiB kit remain exact.
Conductor and MiniBoss29/2A/2C/2D are qualified; Mega Venom and future Up-pounce
integration remain unqualified. Riding has no timer or NPC movement writes.

GPT-6.1 Terra closes all six metrics: presentation8.0, feel8.0, gameplay8.5,
safety8.5, regression/save8.5 and evidence/scope8.0. The player watched the exact
normal-speed preview and says it looks pretty good. The bad existing Conductor
effect is explicitly a separate deferred issue. This is preview-motion
acceptance, not an in-game, audio-quality or hardware verdict by the model.

Crane Row finale, merged onto v0.38.0 and being released as v0.39.0 (player,
2026-10-28: Crane Row felt lame next to Midnight Line). `tools/crane_arm.py`
makes the Long Arm a three-act fight with the native boss meter, makes the
Freight, Dry Dock and Crown crews arrive by crane cargo drop (`crane_drop.py`)
and chains the ring map (`crane_map.py`) and harbour backdrop (`crane_vista.py`).
Receipts: `reference/crane_arm.json`, `crane_map.json`, `crane_vista.json`;
contracts: TECHNICAL "Long Arm three acts", "Crane cargo drops", "Crane Row ring
map"; design: ROADMAP "Crane Row". Agent-tested only.


## Published build

Stable `build/Spider-Man-WoS-modded.nds` is **v0.38.0**, SHA256
`21c7a05140a4ac17bf1061f5336c53e9a7480e8152c2797243329bd8799643ca`.
Protected playtest publication matches the canonical clean build, metadata,
recipe and release history. American/English boot and Options both show
v0.38.0. Previous v0.37 ROM/metadata and recipe remain preserved.

Latest actual Battery: valid 634-byte DSV, opaque 512-byte payload, SHA256
`dc013246987865a5cd2d32dffe04e2e23254a233f8b43cd04b5bb6aa2c7133c7`.
It matches the new before-build checkpoint byte-for-byte; no research save was
adopted. Future saves may legitimately differ; read them freshly.

All 727 strict tests pass with zero skips, plus 26 exact-ROM gameplay/save
controls, six code-identical exact-position/timing native pairs, independent
focused/doc tests and both-facing/small-rig every-frame motion review.
Fixtures and limits are in `reference/boarding.json`; final protection checks
are `work/boarding/publication-verification.json`. The nested-worktree doc-check
fix preserves the separate `.claude/worktrees/` checkout and the contract policy.

## Blockers and next exact action

The Crane build is not yet qualified or published. Not verified: the Conductor's
meter in-engine, the full 30-door and Midnight sweeps, the Black no-refill fight
on the cargo build, any save/Continue case and any hardware run. Fairness and fun
are player gates. Next exact action: see the end of this file once the release
step lands.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
