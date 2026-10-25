# Current work and handoff

Updated 2026-10-25 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

The player says v0.34.1 feels better, but rejects its misplaced blue hit effect,
point-blank slap spam, X as a combat input and the upward variant. Explicitly
approved: make it a pure pull; choose Y or Talon Lift afterward. Move the owned
ground move to Down+A, retaining native air Down+A and other A actions.
The player also requested up to five enemies in one simultaneous pull, each
with independent line, weak ownership and cleanup. Retain the heavy zip rule.

Published v0.34.2 implements those requests. Each target has its own native
scarlet line and native reel velocity, settling 6..9 units ahead. X delegates
to native interactions; the utility causes no HP damage or cosmetic hit flash.
The 300 XP row, purchases, Red and other native abilities stay intact. Other
Hunter slices wait for a player verdict on this move.

## Published build

Stable `build/Spider-Man-WoS-modded.nds` is **v0.34.2**, installed through
`tools/playtest.py build`. Canonical `build/version-0.34.2-final/Versioned.nds`,
the normal-source publisher candidate and installed bytes match (SHA1068aba4;
ARM9 aa7b0687). Both boot/Options labels, recipe, pins, history and receipt agree.
Exact identities and evidence are in `reference/web_yank_combo.json`.
The previous ROM/build metadata and source recipe are preserved.

The latest actual Battery wrapper and 512-byte payload equal this publication's
checkpoint (SHA7181d147). A fresh ordinary Continue from the installed ROM on a
private copy preserves the measured purchases, XP4382, HP77824 and room38.
Web Yank was already purchased in that actual save; no ability, research save
or historical battery was adopted. The clean original is unchanged. Never
restore an earlier publication checkpoint as part of the player's normal flow.

## Blockers and next exact action

All 648 full-suite tests, seventeen focused tests and twenty-seven final
copied-save emulator controls pass. They cover medium/long/moving pulls, both
facings, combo entry, chosen Y/Lift, four distinct casts, held input, R and other
interruptions, ownership, native A/Up+A/air Down+A/X isolation, Return/manual Lift
and Conductor. Five-of-six proof uses a labelled lab-only training OBJ with the
exact production executable and every other asset; the production four-target
crowd also passes. No chapter room changed. Down can no longer duck out of an
active cast before reeling; queued R/L still exit. Original failed controls are
retained and explained in the receipt.
All prior executable bytes outside eight guarded hook words/loader metadata,
assets/bindings outside two instruction/version resources, the frozen 32 KiB
kit, shop/save data, rooms and audio remain exact. The new block is 8 KiB.

No publication blocker remains. Native-size motion/menu were inspected and
mixed PCM captured. Player feel, perceptual audio, full-route balance and
hardware pacing remain unconfirmed; native mini-bosses outside the common-health
registry still need their adapter.

Next exact action: player tests Black ground Down+A gathering up to five targets,
then chooses Y or Up+A, including within combos. Wait for that verdict before
another Hunter slice; iterate this move first if needed. Native queued A outside
supported ground states retains native behavior. No other slice is requested.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
