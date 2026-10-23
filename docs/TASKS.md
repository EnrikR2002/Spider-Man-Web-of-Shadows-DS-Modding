# Current work and handoff

Updated 2026-10-23 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns workflow;
TECHNICAL owns contracts; CHANGES owns releases; TASM_ROADMAP owns design.

## Current objective and player direction

All eight repository audit findings in developer tooling are corrected. Publisher
recovery/receipt retention, candidate defaults, occupied-gap protection,
prototype assembly validation, live-player sampling, current texture audit and
camera parsing are implemented. All 563 source/regression tests pass; exact-source
rebuild verification matches installed v0.32.1 across all 5,952 resources.
No ROM publication is part of this maintenance task.

Both Hunter's Return review findings are corrected in v0.32.1. Per-victim hit
restoration prevents a selected target's launch from leaking into shared hit
records. New player allocation clears a departed owner's private phase so the
move remains available after reload. Native hit credit and damage arguments
remain intact; 324 bytes fit the existing zero tail with no heap/autoload growth.

2099's controls remain: after a ground dash hits, release A and tap A again for
eligible recall into a rising rake; native-unrecallable foes get a short physical
attempt. R cancels; B remains manual. The existing Webbed Fury 100 XP purchase,
event 329 / bit 20 and owned/refund progress stay. His fuller cape-free chest/arms,
37-node rig, texture and 516 triangles are unchanged from v0.32. Other six
proposed Black moves remain deferred.

Red retains the combined TASM1/2 kit; Overclock/Dragnet/Vortex are its final added
skills. Native abilities, dependencies, Both Suits traversal, story gates and
earned rewards stay. No new prices, third suit, shop/save expansion or campaign
branch is active. Player feel and appearance acceptance remain open.

## Published build and save

Stable build/Spider-Man-WoS-modded.nds is **v0.32.1**, installed through
tools/playtest.py build. Accepted A, canonical final, normal-source rebuild,
publisher candidate and stable match; boot/Options agree. Publication scope,
original source hashes and gameplay evidence are in reference/hunters_return_fix.json. CHANGES
and releases.json record publication. Prior ROM/recipe/build metadata remain.
This maintenance changes tooling source while reproducing the same ROM.

The actual latest DSV wrapper, 512-byte payload and publication checkpoint match
exactly. Clean original is unchanged and no research save was adopted. Never
restore a historical battery hash. All testing uses private copies/volatile RAM.
Fresh installed-ROM Continue retains current purchases, XP, HP and checkpoint.

## Implemented and agent-tested

The earlier Hunter correction's 59 source/regression tests passed. They cover both victim orders, shared
info/contact records, native credit before restoration, skipped/ignored hits,
nested calls, ARM ABI/flags, replaced players in both forms, reactivation, three
hook destinations and byte scope. The 32 KiB player kit, all assets/motion/XBDs,
rooms/audio, purchases, ARM7 and other NitroFS files match v0.32.

Native crowd control damages both opponents, launches the selected target and
keeps the bystander in normal knockdown. It uses temporary NPC eligibility,
one-time bystander placement and an idle prefix; no balance claim. That alignment
also passes on v0.32: the target-first leak is established by the ARM regression.
The parent native reload control keeps the old phase and cannot reactivate;
the corrected build clears it and activates again on the new player. Arrival
and stale-owner injection are explicit fixtures. Red/unowned, R and stale-target
controls pass. Earlier ineffective fixture timings remain documented in receipt.

Tooling checks cover failures after every publication write, removal of a partial
first install, continuing recovery after one restore fails, unchanged receipt
links after more play, candidate defaults, occupied internal/trailing gaps,
frozen relocation compatibility, self-calling assembly, lone stale/unaligned
players, kit overlay acceptance and camera counts 1..15. Frozen generators retain
explicit historical gap reuse under their existing pins; raw repacks are strict.

## Next exact action and remaining gates

All audit corrections are qualified; no current blocker or further tooling fix
is queued. No additional DeSmuME/DS-hardware qualification is claimed.

Use the normal launcher to play the correction and review Hunter's Return/physique.
Player feel/appearance, full-route balance and actual DeSmuME pacing stay open.
Other 2099 proposals require a new request; no further move is queued.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
