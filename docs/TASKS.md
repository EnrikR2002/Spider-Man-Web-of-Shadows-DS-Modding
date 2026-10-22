# Current work and handoff

Updated 2026-10-22 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow; TECHNICAL owns contracts; CHANGES owns releases; TASM_ROADMAP owns design.

## Current objective and player direction

The player likes 2099 overall and requested the supplied Across the Spider-Verse
appearance with its red web cape removed. The cape-free revision remains in
v0.30.3. The enemy texture issue from v0.30.2 is fixed for the Terminal crowd:
the three observed custom enemies now render with a compact shared I4 atlas.
Player appearance acceptance remains open. No moves or animation clips changed.

The seven Black catch/carry/crash/chase moves remain proposals. Red keeps one
combined TASM1/2 kit; Overclock/Dragnet/Vortex are its final added skills. Prices,
third suit, shop/save expansion and other branches stay deferred. Preserve native
controls, purchases/dependencies, traversal, story barriers and rewards.

## Published build

Stable build/Spider-Man-WoS-modded.nds is **v0.30.3**, published 2026-10-22 via
tools/playtest.py build. Accepted A, canonical final, normal-source rebuild,
publication candidate and installed stable match. Recipe, pins/history, metadata,
boot/Options and exact evidence are in reference/spider2099_enemy_texture.json.
Previous ROM/recipe/metadata are retained; no source commit/push was requested.

The latest actual Battery was freshly read. Its complete DSV wrapper/payload
matches the private qualification copy and publication checkpoint. Clean original
and unrelated workspace changes remain intact.

## Implemented and agent-tested

The native 128x128 `Forge128` artwork and `ForgePal` name now use I4: 16 colors
and 8 KiB instead of 32 KiB direct color. The atlas retains its UVs and dimensions.
Only this shared creature texture and boot/Options strings change from v0.30.2.
Player I8/2099 appearance, exact models/XBD/animations, ARM9/ARM7, rooms, audio,
enemy stats/AI and player kit/purchases remain exact.

A resource-only control and full v0.30.3 candidate both bind all three live enemy
materials in the Terminal crowd; the 2099 player still binds I8. Fresh copied-save
native runs pass the route and leave the real DSV unchanged. The initial scene has
room/current-owned/initial-HP fixtures; native enemies then act with no healing.
One crowd scene does not establish every room or DeSmuME pacing.

## Next exact action and remaining gates

Use the usual launcher and L to review the cape-free 2099 and resolved Terminal
textures. Player visual preference, actual DeSmuME pacing and full-route combat
balance remain open. Other rooms still need residency qualification before making
a whole-game texture claim. No mechanical Black prototype is authorized until the
appearance verdict and proposed skill recap are discussed.

Prior campaign feedback remains: v0.27 combos were only slightly better, the
boss was easy/idle/missing and the ramp was not felt. Later repairs preserve the
v0.24 accepted environment; broader enemy quality and full-route balance remain
unconfirmed. v0.29 chapter qualification keeps its scope in chapter_finish.json.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
