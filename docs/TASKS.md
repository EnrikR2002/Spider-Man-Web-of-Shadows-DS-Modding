# Current work and handoff

Updated 2026-10-28 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

Codex's Boarding (v0.38.0) and the Crane Row finale (v0.39.0) are merged and
published from `main`. Nothing is pushed; `main` is ahead of `origin/main`.
`codex/2099-boarding` is deleted; `claude/crane-row-improvements-edb9b0` (the Crane
Row worktree under `.claude/worktrees`) is an ancestor of `main` and can be removed.

Crane Row (player, 2026-10-28: it felt lame next to Midnight Line): the Long Arm
is a three-act fight with the native boss meter; Freight Exchange, Dry Dock and
Crane Crown crews arrive by crane cargo drop; the map is one connected ring; the
harbour opens behind the boss. `tools/crane_arm.py` is an exact v0.38.0 post-pass
(flag `crane_arm`) composing `crane_drop`, `crane_vista` and `crane_map` (layout
`crane_ring`). Receipts: `reference/crane_arm.json`, `crane_map.json`,
`crane_vista.json`. Contracts: TECHNICAL "Long Arm three acts", "Crane cargo
drops", "Crane Row ring map"; design: ROADMAP "Crane Row". Agent-tested only.

Boarding (independent 275 XP Black row, event397/bit88): jump or heavy Web Yank
zip toward a supported boss; Y rakes, A tears and kicks off, R releases. Receipt:
`reference/boarding.json`. The player liked the preview motion; the Conductor
sound issue is deferred by request.

Review of codex's Boarding found no crash-level defect. Lower-severity notes,
unfixed: `boarding.apply_rom` reads `build/version-0.37.0-final` build json instead
of the chain's reports; its asm is spliced from other modules by text anchors; the
MiniBoss `attacking` list ejects the rider on any unlisted state; the effect hook
dereferences caller registers unchecked; its pin check is skipped when no pin exists.

## Published build

Stable `build/Spider-Man-WoS-modded.nds` is **v0.39.0**, SHA256
`b53e3879cc575e63979f1a65a7d29fc610a3d1d44080f2205b29aec26075d37c`, built by
`tools/playtest.py build` and equal to the clean-chain and standalone builds.
American and English boot and Options both read v0.39.0. The v0.38.0 ROM, build
metadata and recipe are kept under `build/releases` and `build/version-0.38.0-final`.
The actual Battery (634-byte DSV, SHA256 `dc013246...`) is unchanged and matches
its before-build checkpoint; future saves may differ, so read them freshly.

Evidence: 774 strict tests, zero skips, passed before publication except the two
version checks that need this release recorded; those pass now. Native-input Long
Arm fights win (Red frame 2045 with saved victory and cleared revisit; Black without
healing frame 2809). Crane doors: 23 of 30 pass, the same seven fail identically on
published v0.38.0 (lab findings). Midnight Line: 9 of 9 pairs, 18 doors. Harbour
Office save and reload pass. Boarding Conductor ride, lethal tear and shop
purchase/refund/repurchase/Continue pass on this ROM.

## Blockers and next exact action

No blocker. Launch normally and try the Long Arm (three acts, boss meter), the
Freight Exchange, Dry Dock and Crown cargo drops, the Crane map and the harbour
backdrop; then try Boarding. Give in-game verdicts before another skill or Crane
change. Unverified: fun and fairness, hardware pacing, full-route balance, the
seven lab-failing Crane doors in real play. Build, test and publish only in the
full checkout; a fresh worktree cannot reproduce pinned hashes. Do not push
without a request.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
