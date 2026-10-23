# Current work and handoff

Updated 2026-10-23 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns workflow;
TECHNICAL owns contracts; CHANGES owns releases; TASM_ROADMAP owns design.

## Current objective and player direction

The next requested 2099 skill, **Talon Lift**, is implemented and published in
**v0.33.0**. No further move is queued. The other five 2099 proposals remain
deferred pending a new request. Player feel/appearance acceptance stays open.

Talon Lift keeps the existing Power Launch purchase: 200 XP, event 330 / bit 21,
native ownership, dependencies and refunds. In Black form, Up+A coils low into
a rising talon rake while staying grounded. **Hold B**, then Y, manually catches
the launch with actual air hits. R cancels early. B, air strings, movement,
collision, hitboxes, damage and launch resistance stay native.

Hunter's Return keeps its current dash-hit recall/physical attempt and v0.32.1
hit-isolation/owner correction. Red retains the combined TASM kit; Overclock,
Dragnet and Vortex remain its final added skills. No price rebalance, third suit,
shop/save expansion or campaign branch is active. Native traversal, purchases,
Both Suits, story gates and rewards remain.

## Published build and actual save

Stable `build/Spider-Man-WoS-modded.nds` is **v0.33.0**, installed by
`tools/playtest.py build`. Canonical F, publisher's normal-source rebuild and
stable ROM match exactly; boot/Options, recipe, pin, metadata and history agree.
Identities, release receipt and verification are in `reference/talon_lift.json`.

The freshly read actual DSV wrapper and 512-byte payload match the publication
checkpoint exactly. Fresh Continue from the exact final ROM preserves purchases,
XP, HP and checkpoint. The current player does not own bit 21: buy Talon Lift
normally. No research save was adopted, and no historical battery was restored.
Prior ROM/metadata/recipe/overlays and the current release composition are retained.
The clean original is unchanged.

## Implemented and agent-tested

A continuous private 14-sample SCA and stateless 416-byte adapter fit the existing
zero tail without heap/autoload growth. The 32 KiB player kit, Hunter's Return,
Red, other actor bindings/motion, geometry/textures, rooms and audio remain exact.
Archive growth shifts the following file by 23 KiB, preserving the entire
occupied gap and file tail.

The full source run passed 570 tests before final packing/instruction refinements.
Nine final Talon tests pass, covering ABI, pointer/ownership/controller isolation,
native B timing, R queue, animation and exact resource/text/executable scope,
including occupied-gap preservation. All 5,953 final resources validate.

Eleven focused C controls pass and carry forward through explicit executable/
resource identity. Final F proves real held-B air damage in both directions, R,
miss recovery, current Vortex and fresh Continue. D's Hunter R control remains
applicable through exact gameplay payload identity. Native-size frames and a
normal-speed capture with native mixed audio are retained.

Short B taps initially played an air animation without hitting. Holding B for
the native full jump lands three actual air HP losses after the grounded rake.
The unnecessary experimental B bypass is excluded. The final manual check
requires additional actual damage, not just animation/counters.

The legacy 68-check kit run passes 58 expectations. All ten failures also fail
on v0.32.1 in nine selected replay cases; two further Dragnet expectations fail
only in the parent replay. Those fixture/AI and pre-v0.31 Vortex assumptions are
not new regressions. Native gate/snare/Black parity and current Vortex pass.
Full receipts and limits are in the catalog.

## Next exact action and remaining gates

Use the normal launcher and review Talon Lift's coil/rake, held-B air catch and
R exit. Implementation/publication have no remaining blocker or queued code fix.
Player feel/appearance, full-route balance and actual DeSmuME/hardware pacing
remain unconfirmed. Do not activate another proposal automatically.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
