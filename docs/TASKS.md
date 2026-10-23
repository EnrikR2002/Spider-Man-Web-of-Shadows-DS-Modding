# Current work and handoff

Updated 2026-10-23 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns workflow;
TECHNICAL owns contracts; CHANGES owns releases; TASM_ROADMAP owns design.

## Current objective and player direction

The latest request is complete in **v0.33.1**: make 2099 taller, make his webs
neon red like Across the Spider-Verse, then research and reassess the existing
2099 ability proposals. No additional combat move is queued. Appearance and
move feel remain unconfirmed by the player.

2099's complete animated pose is **12.5% taller** with grounded feet and the
fuller cape-free body retained. Native web lines and companion WebTrap/effect
tints become scarlet. Red retains its native height and original web colors.
Native collision/hitboxes, movement, rig, mesh, textures, clips, attacks,
purchases, Both Suits traversal, story gates and save format remain.

Hunter's Return and Talon Lift remain the two implemented Black replacements.
Lift keeps Power Launch's 200 XP ownership: Up+A rake, hold B, then Y for actual
air hits; R exits. The actual player still needs to buy Lift normally. Red keeps
the combined TASM kit; Overclock, Dragnet and Vortex are its final added skills.
Other Black moves, prices, third suits, shop/save expansion and campaign branches
remain deferred.

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

## Film reassessment and next exact action

TASM_ROADMAP records the sourced film research and recommended identity:
**close/cut off -> tether or catch -> drive/slam -> re-engage**. Keep the two
shipped moves; recommend a short Raking Cross pounce/body drive as the next
prototype only if requested. Talon Cyclone needs the largest redesign toward a
compact air catch/downward drive. The previous proposals have a dated verified
archive snapshot. Research recommendations have not changed combat mechanics.

No implementation/publication blocker remains. Next: launch normally and review
Black's height, red swing webs, Hunter and Lift. Player appearance/feel,
full-route balance, exhaustive edge culling and actual DeSmuME/hardware pacing
remain open. Do not activate another proposal automatically.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
