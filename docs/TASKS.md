# Current work and handoff

Updated 2026-10-23 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow; TECHNICAL owns contracts; CHANGES owns releases; TASM_ROADMAP owns design.

## Current objective and player direction

The requested first 2099 skill and fuller Spider-Verse physique are implemented
and agent-qualified in v0.32.0. Hunter's Return uses the existing Webbed Fury
purchase: after a ground dash hits, release A and tap A again. Eligible targets
are recalled into a rising talon rake; native-unrecallable targets get a short
physical pursuit attempt. R cancels; B remains a manual jump. Already-owned
progress remains owned. The native 100 XP price, event 329 / bit 20 and refund rules
remain. Other six proposed Black moves are deferred; no new shop/save system.

2099 has fuller chest/back, shoulders, biceps and forearms, retaining his
cape-free texture, 37-node rig, native height/pivots and 516 triangles. Red's
geometry/texture and previous kit/chapter/boss/Vitality work remain.
Player feel and physique acceptance are open.

Red retains one combined TASM1/2 kit; Overclock/Dragnet/Vortex are its final added
skills. Preserve native abilities, ownership/dependencies, Both Suits traversal,
story gates and earned rewards. Prices, third suit and other campaign branches
remain deferred. Earlier environment acceptance does not accept all enemy art.

## Published build and save

Stable build/Spider-Man-WoS-modded.nds is **v0.32.0**, published through
tools/playtest.py build. Accepted B, canonical final, normal-source rebuild,
publisher candidate and installed stable match. Boot/Options agree. Full scope,
pins, recipe and evidence are in reference/hunters_return.json; CHANGES and
releases.json record publication. Previous ROM/recipe/build metadata are retained.

The player saved and closed DeSmuME before publication. The latest actual DSV
wrapper, 512-byte payload and new publication checkpoint match exactly; clean
original is intact. Fresh Continue from the newly saved copy retains abilities,
XP, initial HP and checkpoint. No research save was adopted. Older battery
hashes remain historical observations, never restore instructions.

## Implemented and agent-tested

Native recall/rake/launch and mirrored physical fallback run through real
contacts. Twelve focused cases cover ownership, Red, whiff, held/optional A,
R/hurt/form/stale exits and left-wall contact. Native R and other abilities stay
available; traversal inputs are not redirected. The 50 source/regression checks
include ARM ABI/flags, pointer/room/form guards, private animation routing,
purchase/32KiB-kit/resource isolation and research-output safety.

The live Conductor receives 12 damaging physical follow-ups and no forced launch.
That resistance study heals the player and resets only the disposable boss flag;
it is not a balance/victory claim. The current copied-save Terminal scene keeps
the hero I8 and both observed enemy species I4 bound across 218 crowded samples;
no third actor was observed. Native-scale pull/rake/launch, physical rake,
crowded hurt and shop text/owned checkmark were inspected. The same texture
footprint/triangle count is preserved. Earlier failed fixture assumptions and
their corrected scope are retained in the receipt.

## Next exact action and remaining gates

Use the normal launcher, switch to 2099/Black with L and review Hunter's Return
and the fuller physique. Player feel/appearance, full-route balance and actual
DeSmuME pacing remain open. Iterate this first move before requesting another
proposal. No additional 2099 move is queued for automatic implementation.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
