# Current work and handoff

Updated 2026-11-04 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

The player requested Crane Row improvements, starting with the magenta enemy
and Freight cargo visibility, with an independent GPT-6.1 Terra rating of at
least 8/10. v0.40.0 implements those scoped improvements; Terra's final overall
score was 8.0/10 with no must-fix findings. The player approved two short cargo
sound clips. Visual and gameplay feedback has not yet been given.

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

Stable `build/Spider-Man-WoS-modded.nds` is **v0.40.0**, SHA256
`bf9b63a95bff3c1edfea1e3f8acbc4503a9521fb87bdcb333a87bedfef9fd0c6`,
installed by `tools/playtest.py build` and equal to the clean-chain candidate.
Boot and Options show v0.40.0. The v0.39.0 ROM, metadata and recipe are preserved
under `build/releases` and `build/version-0.39.0-final`. The actual 634-byte DSV
was `ea33136000a3938c96769d67ec65f13d0b1d3b4764bdcb3413f4fbb5a44750fc` at publication and matched its checkpoint; always read the
latest battery afresh because future saves may differ.

The strict suite passed 788 tests in 104 isolated modules, with no skips. All
nine Midnight pairs and eight Freight-connected crossings passed with native
movement, enemies parked and the player healed. Assisted Freight/Crown clears,
earned Office save/reload, and an interrupted Freight re-entry/retrigger passed.
One native-HP Ballast-only driver observed a death but lost the overall fight.
Those controls do not establish unassisted normal-HP balance or hardware quality.

## Blockers and next exact action

The player can now use Play Spider-Man.cmd -> Continue -> play -> save in-game ->
close, then report whether Ballast and Freight feel and look right. Hardware,
full unassisted normal-HP play and the remaining enemy/encounter priorities are
open. Do not push without a request.

Side research (2026-11-03): the external EUR decompilation was read for asset
pipeline knowledge. Its findings, limits and the EUR-to-USA address rule are in
TECHNICAL "External EUR decompilation and asset load path"; query it with
`tools/decomp_xref.py` over a private `work/decomp` clone. It adds no asset
format parsers. Its 2026-11-05 follow-up maps the native heaps (models in heap 2,
textures freed after VRAM upload); measure main-RAM headroom with
`tools/heap_report.py`. Texture VRAM headroom is still unmeasured.
Blender model bridge (2026-11-05): `tools/model_bridge.py` exports in-scope
character models to glTF and imports Blender edits on the native rig; DEVELOPMENT
"Blender model bridge" has the workflow. No bridged model is in a release.
The Crane objective above is unchanged.
