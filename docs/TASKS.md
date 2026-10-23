# Current work and handoff

Updated 2026-10-22 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow; TECHNICAL owns contracts; CHANGES owns releases; TASM_ROADMAP owns design.

## Current objective and player direction

The three requested fixes are implemented and agent-qualified in v0.31.0:
conditional, more spectacular Vortex; a larger symbiote metal war-machine
Conductor with one boss meter; and the repeated lethal-hit/low-HP Vitality bug.
The player likes the boss fight behavior, which remains intact. New Vortex feel
and boss appearance require the player's own verdict; agent clearance is distinct.

Red retains one combined TASM1/2 kit. Overclock/Dragnet/Vortex are its final
added skills. Black mechanical proposals, prices, third suit, shop/save expansion
and other campaign branches remain deferred. Cape-free 2099 and the compact
Terminal crowd atlas remain. Preserve native controls, ownership/dependencies,
traversal, story barriers and earned rewards.

## Published build

Stable build/Spider-Man-WoS-modded.nds is **v0.31.0**, published through
tools/playtest.py build. Accepted F, canonical final, normal-source rebuild,
publisher candidate and installed stable match. Recipe, release pins/history,
boot/Options and full scope/evidence are in reference/vortex_forge.json.
Previous ROM/recipe/metadata are retained; no source commit/push was requested.

The latest actual Battery was freshly read again. Its complete DSV wrapper,
payload and publication checkpoint match before/after. Clean original and
unrelated files remain intact. A fresh native Continue keeps current abilities,
XP, initial HP and checkpoint; no research battery was adopted.

## Implemented and agent-tested

Web with A or Dragnet, release A, then Down+Y: Vortex captures actual cocoons,
catapults their bodies through a two-turn tether animation and slams them down.
R/hurt interrupts cleanly; native movement/collision remain. Regular/Dragnet,
mirror, unwebbed/unowned/Black, stale-pointer, ABI and cancellation controls pass.
The isolated body-contact control knocks down a real bystander; it parks only
unwebbed standing enemies through frame100. Earlier unparked interruptions are
retained, not treated as guaranteed crowd clears.

The Conductor has articulated armor/turbines/pistons/exhausts, 1.28x body scale,
a compact boss-only RGB555 texture and no duplicate red bar. All39 private
motion timings/rotations and native attack/AI/HP/audio/collision stay exact.
The shared I4 crowd atlas and other actors remain exact. The old boss's magenta
palette issue is reproduced and corrected in this arena.

Vitality now scales full incoming damage before the final HP clamp. A latest
copied-save control needs eleven old-build hits to finish low HP, versus one
real damaging hit on the corrected build. Twenty-six tests include256 damage
combinations. Final Red victory/save/fresh Continue pass with labelled healing;
an identical-boss E Black control earns a no-refill win/save. Exact reuse scope
and limitations are in the receipt. Room/door resources are unchanged.

## Next exact action and remaining gates

Use the normal launcher to review Vortex and the larger boss. Player feel,
appearance preference, full-route balance and actual DeSmuME pacing remain
open. Prior environment improvements remain accepted; broader enemy quality
is not implied by this boss/art/kit qualification.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
