# Current work and handoff

Updated 2026-11-16 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

Trial [Relentless Pursuit](ROADMAP.md#relentless-pursuit-ground-evade-follow-up),
Miguel's ground evade follow-up, in the existing 225 XP Super Charge slot.
The player rejected v0.42.0's Talon Pounce because A was faster, chained
better and avoided accidental charging in ground strings. Implementation and
playtesting are pending.

The [Pounce receipt](../reference/talon_pounce.json) covers the shipped move.
Red Spider Reflex carries a string node across a dodge. The existing Vortex
interaction shows where Drill Kick can take priority.

**Engine map (2026-11-14, no game change).** `python tools/engine_map.py`
answers what an engine address, class, state, action, ability bit or
mod-changed site is. All 365 game classes, both state machines' tables, the
action list, the native ability bits and every native word the mod changed are
catalogued in `reference/engine_*.json`. Evidence and unknowns: TECHNICAL
"Engine map". Commands: DEVELOPMENT "Engine map lookups".

Freefall remains in the existing Ground Rebound purchase. Evidence and Luna's
separate review are in `reference/freefall.json`. The player verdict is open.

Separate Crane Row Blender request: the private Ballast study retains its rig,
texture and 266-quad budget. Luna's 8/10 covers Ballast stills and sampled
frames. Normal-speed motion, mixed audio and the other two enemies remain open.
Reproduce the study with
`python tools/crane_blender.py --out build/crane-models/reproduce/Versioned.nds`;
evidence and limitations are in `reference/crane_blender_research_20261105.json`.
The strict suite passed 810 tests across 109 isolated modules, with no skips.

The prior v0.40.0 Crane color/cargo changes received Terra's 8/10 overall
review; the player approved two short cargo sounds, with visual and gameplay
feedback still open.

Ballast uses a private direct-color material. Freight stages its container for
upper and right-ground approaches and uses two existing native floor anchors per
approach with native occupancy and crew callbacks. The burst can still be
blocked if both points are occupied. The remaining ranked ideas and player
feedback are in ROADMAP "Crane Row"; evidence is in TECHNICAL and
`reference/crane_visibility_research_20261029.json`.

Boarding (independent 275 XP Black row, event397/bit88): jump or heavy Web Yank
zip toward a supported boss; Y rakes, A tears and kicks off, R releases. Receipt:
`reference/boarding.json`. The player liked the preview motion; the Conductor
sound issue is deferred by request.

The prior Boarding review found no crash-level defect. Unfixed lower-severity
notes: `boarding.apply_rom` reads v0.37 metadata instead of chain reports; its asm
uses text anchors; unlisted MiniBoss states eject the rider; the effect hook has
unchecked caller registers; and its pin check is skipped when no pin exists.

## Published build

Stable `build/Spider-Man-WoS-modded.nds` is **v0.42.0**, SHA256
`41bb7db548c40dee7c0c290ff88c14dbbcc86be1c139facd0fc15e8784039cd0`.
`tools/playtest.py build` installed the exact reviewed ROM from the clean
source. Boot and Options show v0.42.0. The v0.41.0 ROM, metadata and recipe
are preserved under `build/releases` and `build/version-0.41.0-final`.
The actual 634-byte DSV matched its validated checkpoint byte for byte.
Read the actual battery afresh before the next lab or release.

## Blockers and next exact action

Next session, implement a private candidate against exact v0.42.0. Follow
DEVELOPMENT's guarded post-pass workflow and read the latest actual battery
before creating a disposable copy. Lead and workers split each step (AGENTS).

1. Trace a native Black grounded Y hit → R → Y with Drill Kick and Enhanced
   Dodge toggled on the copy. Read TECHNICAL's [player state machine](TECHNICAL.md#player-state-machine-and-red-kit-hooks-v020)
   and [Vortex evade precedent](TECHNICAL.md#conditional-tether-vortex-and-conductor-armor-v031-research).
   Use current string contact evidence, the native node and the actual evade
   transition. Check how a buffered Y survives to the normal attack window.
   Static head start, unconfirmed in a trace (`engine_map.py table
   GroundTransitions`, `dis 0x020B5950`): in dodge state 53 the evade
   transition ignores a queued Y for 8 updates, then lets the attack
   transition take it; the string node lives 10 updates after state 46.
   Existing hooks there: `0x020B57A0`, `0x020B5C58`.
2. Replace the Pounce routes for owned Black bit 25, including the coil and
   upward Boarding handoff. Keep event 334, the 225 XP price, existing save
   ownership and the bit 26 dependency. Update shop text to describe the
   follow-up and retire the coil description. Defer Quick Charge's new effect.
3. Qualify the candidate with real inputs against a counterattacking enemy:
   Y → Y → R → one buffered Y must land the next strike and deal real HP
   damage. Repeat turning toward a second enemy. Check late taps, holding Y,
   whiffs, ignored hits, second R, terminal and late-branch nodes, and cleanup
   on hurt, death, leaving the ground, room or form change. Check deliberate
   Down+R → Drill Kick and ordinary evade priority with both shared upgrades,
   Red and unowned behavior, Web Yank/Talon Lift, native air and
   Boarding routes, and the existing purchase on fresh Continue.
4. Prepare the qualified candidate and normal-speed footage for the player
   trial. Responsiveness, spacing and value against real counters still need
   the player's verdict.

For the Crane Row study, review Ballast's motion and mixed audio before expanding
to Maw and Spore: neither available reviewer can play or hear the clip, so the
player was asked to check `work/crane-models/ballast-v5-4sec.mp4`. The healed
6,000-frame mixed fight timed out but sampled a get-up; a separate 1-HP RAM
fixture observed a native Ballast death, not a normal-HP clear. Then test the
remaining models, review the final composition with Luna, and publish after
all required qualification. Do not push.

Engine map follow-ups: name more vtable slots and fields, decode the enemy
brain's `Decide`/`Act` conditions, map OBJ commands to factory classes. Run `python tools/arm9_hooks.py` after each publication.
Other research tools (see DEVELOPMENT): `decomp_xref.py`, `heap_report.py`
(texture VRAM still unmeasured) and `model_bridge.py` (no bridged model is in
a release).
