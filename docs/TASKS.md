# Current work and handoff

Updated 2026-10-25 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

The player likes Web Yank and says Down+A feels much better. The requested next
2099 ability is implemented: Sky Rake, a 100 XP independent Black row. Air Y
chains four original talon rakes and a rising flip kick. Up+A Talon Lift, hold B,
then keep tapping Y; R exits using owned Air Dodge or native fall when unowned.
Native air-chain eligibility, movement/collision and damage remain.

Black's nine current prices are 50/75/100/100/125/150/75/75/100 XP, total 850;
Web Yank now costs 75. The full fourteen-skill budget is 1,600 XP (50..200 per
row); the five later rows remain designed. Existing purchases/dependencies,
XP, Red/Both Suits prices, rewards and native abilities are retained. Player
feedback and current design are in ROADMAP.

## Published build

Stable `build/Spider-Man-WoS-modded.nds` is **v0.35.0**, installed through
`tools/playtest.py build`. Canonical `build/version-0.35.0-final/Versioned.nds`,
clean-ROM reproduction, publisher candidate and stable bytes match: ROM
SHA65dc457f / ARM9 41749bf4. Both supported boot/Options labels, recipe, pins,
history and release receipt agree. Details are in `reference/sky_rake.json`.
The previous v0.34.2 ROM/build metadata and source recipe are preserved.

The freshly read actual Battery is still the exact pre-task/publication
checkpoint (DSV SHA7181d147, valid 512-byte payload). Fresh ordinary Continue
from the installed ROM on a private copy preserves all measured purchases,
XP4382, HP77824 and room38. Sky Rake is not granted to the actual save; buy its
100 XP row normally. No research save or historical battery was adopted, and
the clean original is unchanged. Never restore an earlier checkpoint as part
of the normal player flow.

## Blockers and next exact action

All 655 full-suite tests, seven final focused tests and twenty copied-save
emulator controls pass. They cover five contacts, both facings/native approach,
wall launch, whiff, ownership/Red/native A isolation, paid/unpaid R, hurt,
actual ground form switch, shop purchase/refund/repurchase/save/Continue,
chapter-enemy death and preserved pure Web Yank. Natural Conductor air hits
stagger; a separately labelled native action4/node2 fixture proves the real
kind16 kick also damages/staggers without launching the heavy. That probe does
not prove a full natural five-hit combo against a standing boss.

The 896-byte stateless adapter, shop and clip routes use 1,232 existing zero
bytes; no allocation or frozen 32 KiB kit change. All original clips/bindings,
other assets/code outside the explicit guards, rooms and audio remain exact.
No chapter room changed. Native-size motion/menu were inspected; a normal-speed
preview and mixed PCM are in `work/sky-rake/`. Earlier failed controls and their
corrected expectations are retained and explained in the receipt.

No publication blocker remains. Player feel, perceptual audio, full-route
balance and DeSmuME/hardware pacing are unconfirmed. Native mini-boss adapters
for later targeting/Boarding remain pending.

Next exact action: player buys Sky Rake, tests Talon Lift -> held B -> repeated Y,
including after Down+A Web Yank and with R exits, then gives a verdict. Wait for
that verdict before another ability. Reel In's air combat binding remains to
be chosen before its own slice; X stays native.

Player flow: Play Spider-Man.cmd -> Continue -> play -> save in-game -> close.
