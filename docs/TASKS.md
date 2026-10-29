# Current work and handoff

Updated 2026-10-29 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

The player requested an agent playthrough and comprehensive improvement analysis
of Crane Row. The v0.39.0 review is complete; proposals and their priorities are
in ROADMAP "Crane Row", and the scoped evidence is in
`reference/crane_review_20261029.json`. This is an agent assessment, not a player
verdict or an implementation request. `main` remains unpushed.

From a copy of the latest battery, frame-stepped Black inputs traversed Pier,
Quay, Freight, Warren, Dry Dock, Engine, Shaft and Gantry to Crown. The agent
restored power but did not clear Crown. All 12 rooms were seen across that run
and labelled room-start inspections; Office and Cache were brief. In a separate
unhealed Long Arm room-start fixture, the agent defeated the hoist and returned
through Breakwater and Quay to Pier. No save/reload was tested.

Two high-priority visual findings: Crown shows an intense magenta enemy before
either sampled enemy loses HP; cause and emulator parity remain unknown. A fresh
Freight drop can be triggered from the upper deck, but its landing and opening
were not visible in sampled frames. Engine's map objective remained "POWER:
ENGINE" after the lever, updating to "CROWN: CREW" on the next room entry.
Technical observations and limits are in the corresponding TECHNICAL sections.

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
The actual Battery is a 634-byte DSV. At this review its SHA256 was
`ff62fa34c48e2bf1530449209d162b2254ddca8e95c44e9ee8ea75998a05aea1` and it
remained unchanged; future saves may differ, so read them freshly.

Evidence: 774 strict tests, zero skips, passed before publication except the two
version checks that need this release recorded; those pass now. Native-input Long
Arm fights win (Red frame 2045 with saved victory and cleared revisit; Black without
healing frame 2809). Crane doors: 23 of 30 pass, the same seven fail identically on
published v0.38.0 (lab findings). Midnight Line: 9 of 9 pairs, 18 doors. Harbour
Office save and reload pass. Boarding Conductor ride, lethal tear and shop
purchase/refund/repurchase/Continue pass on this ROM.

## Blockers and next exact action

No implementation was requested in this review. Next, use the ROADMAP priorities
to choose a Crane slice; first reproduce the magenta enemy with controlled
species/status and DeSmuME, and check the cargo camera from upper and lower
approaches. Do not call the seven lab door failures regressions: this review
crossed several affected doors in different real-input conditions. Still open:
a continuous full-route clear, fresh Dry Dock/Crown drops, actual mixed audio,
Red, hardware pacing, save/reload and a player verdict. Build, test and publish
only in the full checkout; a fresh worktree cannot reproduce pinned hashes. Do
not push without a request.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
