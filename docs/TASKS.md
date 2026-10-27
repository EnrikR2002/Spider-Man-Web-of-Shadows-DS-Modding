# Current work and handoff

Updated 2026-10-26 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

Reel In is implemented, qualified and published. The player's independent
8/10 gate passes: 8.53/10 weighted overall (8.5 displayed), presentation 8.2,
feel 8.4, correctness/isolation 9.0 and evidence/lean implementation 8.5, with
no must-fix findings. These are agent scores; the player's verdict is open.

Black airborne Up+A reels an eligible foe below/ahead into claw range, then
chosen Y continues Sky Rake. Heavy targets pull Miguel toward them. The new
150 XP row requires Web Yank (event393 / bit84); existing purchases and native
inputs remain. Ten Black rows total 1,450 XP.

All 674 strict tests pass with zero skips across 94 module subprocesses, plus
28 final-ROM gameplay/save cases and seven paired native-input controls.
The reviewer independently reran all sixteen focused tests and inspected
native-resolution timed motion, both facings, the second-foe extension and
heavy tether attachment. Separate failed attempts/fixtures are retained and
not counted as mechanics proof. Exact evidence and limits: `reference/reel_in.json`.

## Published build

Stable `build/Spider-Man-WoS-modded.nds` is **v0.36.0**, installed by the
protected publisher. Clean-source composition, canonical, publisher candidate
and stable ROM match SHA399bf220 / ARM9 8e497f9d and the immutable release pins.
English/American boot and Options both identify 0.36.0. The previous v0.35.2
ROM, metadata and recipe remain preserved.

The freshly read actual Battery equals its pre-build checkpoint byte for byte
(SHA07c2b3b0, 634-byte DSV wrapper / 512-byte payload). DeSmuME stayed closed;
no research save was adopted. Receipt: `reference/reel_in.json`.

## Blockers and next exact action

No implementation blocker remains. Player feel, full-route economy and hardware
pacing still need a verdict. Native mini-boss target adapters remain deferred;
unhandled targets retain native A. The declared native-jump diagnostic proves
posed tether attachment only; unmodified final-ROM Conductor input separately
qualifies heavy mechanics. It is never installed as the stable ROM.

Next exact action: launch normally, buy Reel In in Black upgrades after Web
Yank, and try Talon Lift -> hold B -> Y -> airborne Up+A on a fresh foe -> Y.
Check both facings, R release and a heavy zip, then give a verdict before
Meteor Catch. No further skill or push is requested in this task.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
