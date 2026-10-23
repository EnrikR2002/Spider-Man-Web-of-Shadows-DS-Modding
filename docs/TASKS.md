# Current work and handoff

Updated 2026-10-23 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns workflow;
TECHNICAL owns contracts; CHANGES owns releases; TASM_ROADMAP owns design.

## Current objective and player direction

The latest request develops the full 2099 kit: flesh out every move, add proper
air combo routes, and explore blocking or instantly answering enemy attacks.
The expanded working design is recorded in TASM_ROADMAP and the suit catalog.
**No gameplay implementation or new release is selected by this design task.**
Stable remains **v0.33.1**; appearance and move feel remain player-unconfirmed.

The recommended new loop is meet the attack -> counter/catch -> grounded
pressure or manual launch/jump -> air pressure -> spike/slam -> re-engage.
Talon Guard is a proposed grounded Up+R chord in Hunter's Return's existing
purchase. A well-timed real frontal melee contact would trigger a short
automatic physical answer. Ordinary R/rolls and paid shared defenses remain.
The player selected **timed block -> automatic counter** on 2026-10-23.
Up+R, purchase placement and timing remain working proposals, not approved or
engine-qualified details. Damage-taking Reprisal is the unselected alternative;
paid Quick Recovery keeps its native role.

The native air Y string remains. Proposed Talon Maul (former Cyclone working
name) adds Y,Y,Up+Y,Y; charged Relentless Pursuit spends its bank on the first
air Forward+Y, then actual contact permits Y,Y,Y. Both require their purchases
and real contact for follow-ups; one advanced extension
between landings. Native air A/Down+A, purchased Down+Y stomp, Enemy Kick-Off,
Air Dodge and B/B swing behavior retain their distinct roles. Seven Black shop
slots, prices, ownership/dependencies and save format remain the boundary.

Hunter's Return and Talon Lift remain the only implemented Black replacements.
Lift keeps Up+A rake -> hold B -> air Y, with native R exit. Red retains the
combined TASM kit; Overclock, Dragnet and Vortex are its final added skills.
Other five Black replacements, guard/air extensions, prices, third suits,
shop/save expansion and campaign branches remain unimplemented/deferred.

## Published build and actual save

Stable `build/Spider-Man-WoS-modded.nds` is **v0.33.1**, installed through
`tools/playtest.py build`. Canonical, independent normal-source rebuild,
publisher rebuild and stable bytes match. Boot/Options, recipe, pin, metadata
and history agree. Exact identities and receipts belong in
`reference/spider2099_presence.json`.

The freshly read actual DSV wrapper and 512-byte payload equal the new
publication checkpoint exactly. Fresh ordinary Continue from those exact ROM
bytes retains purchases, XP, HP and checkpoint. No research save was adopted or
historical battery restored. Prior ROM/build metadata/recipe remain retained;
the clean original is unchanged.

## Implemented and agent-tested

All **580 source tests** and **15 final focused appearance/archive/document
checks** pass. The selector and tint adapters fit existing zero space without
heap/autoload growth; the 32 KiB player kit and all 5,951 non-text resources
remain exact. Tests cover pointer/footer/form guards, all condition flags,
register preservation, native Red tints and exact executable/resource scope.

Paired final/parent position tracks match. The taller Black pose retains its
floor line; settled Red hero pixels after L are exact. Real B jump/B swing
produces scarlet owned lines, while Red lines remain native white. Talon manual
air damage and Hunter physical pursuit pass. A native-input run without RAM
fixtures proves Continue, both forms and a real room reload. The no-heal
Terminal sample binds an I8 hero and two I4 enemy materials; the player later
dies, so this is presentation evidence, not a clear or balance verdict.
Native-size motion frames and a normal-rate capture with unchanged mixed audio
are retained. Perceptual listening is unavailable in this runtime. Companion
WebTrap/effect tints are source/ABI-tested; the full effect roster is not
visually surveyed.

## Expanded design and next exact action

The roadmap now maps all seven Black purchases, two advanced air routes,
finishes/exits, the player-selected timed guard/automatic counter direction,
the unselected paid-recovery reprisal, and example duel/crowd/boss sequences. The previous
film-only draft and suit catalog have dated verified archive snapshots. Native
controls and hit contracts were inspected; this task adds no emulator evidence
or gameplay changes. Block/counter timings and air conversions are untested.

No blocker for the design task remains. Next: discuss/refine this working kit.
If implementation is requested, first prove one planted guard and one actual
riposte against one ordinary melee attack, with both facings, miss/late/heavy/
rear controls, shared/unowned R controls, contact isolation and cleanup. Then
qualify Raking Cross and one air branch before expanding the roster or whole
kit. This supersedes the earlier Cross-first recommendation, without queuing
implementation automatically.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
