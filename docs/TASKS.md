# Current work and handoff

Updated 2026-10-25 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

The requested final-kick landing correction ships in v0.35.2. For an accepted
light-target finisher, a stateless ARM helper sets only enemy horizontal
velocity toward a point about three units ahead. Native kind0x25 vertical
launch, gravity and collision remain active. The v0.35.1 look/feel scores
(8/10 each) remain separate; the landing tweak has not had a post-change
emulator check. Player confirmation is open.

## Published build

Stable `build/Spider-Man-WoS-modded.nds` is **v0.35.2**, installed by the
protected publisher. Canonical, publisher candidate and stable ROMs match the
release pins. The previous v0.35.1 ROM/metadata and recipe remain preserved.
Receipt: `reference/sky_rake_front.json`.

The latest actual Battery matches its pre-build snapshot byte for byte (SHA
07c2b3b0; valid 512-byte payload). The publisher kept DeSmuME closed. No
research save was adopted.

## Blockers and next exact action

The full composition rebuilt from the clean ROM and the helper fits the
parent's verified ARM9 zero tail. No test suite or post-change emulator check
was run for this adjustment; the player should confirm the landing in game.
No chapter or price changed.

Next exact action: commit this task and push `main` plus its existing unpushed
commits to `origin` as requested. Then the player tests the final kick on a
nearby foe before another ability. Reel In's air binding and native mini-boss
adapters remain pending; X stays native.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
