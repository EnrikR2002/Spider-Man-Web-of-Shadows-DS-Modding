# Current work and handoff

Updated 2026-11-05 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

The player requested improved Crane Row enemy models using Blender, with an
independent Luna rating of at least 8/10 before completion. A private Ballast
study retains its rig, texture and 266-quad budget; its exact v0.40.0-based
candidate is `build/crane-models/ballast-v5/Versioned.nds`, SHA256
`5f011cbe2e0aa5125aed335c28e044e9a9d3cb24194090e78d768165e9f90652`.
Luna rated Ballast's Blender stills and sampled gameplay frames 8/10, but could
not review the clip's normal-speed motion or audio. That is not an overall
rating or completion of the three-enemy request. Reproduce the study with
`python tools/crane_blender.py --out build/crane-models/reproduce/Versioned.nds`;
evidence and limitations are in `reference/crane_blender_research_20261105.json`.
The strict suite passed 800 tests across 107 isolated modules, with no skips.

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

Review Ballast's captured normal-speed motion and mixed audio before expanding
to Maw and Spore: neither available reviewer can play or hear the clip, so the
player was asked to check `work/crane-models/ballast-v5-4sec.mp4`. The healed
6,000-frame mixed fight timed out but sampled a get-up; a separate 1-HP RAM
fixture observed a native Ballast death, not a normal-HP clear. Then test the
remaining models, review the final composition with Luna, and publish only
after all required qualification. The player can still play stable v0.40.0
through the normal Play -> Continue -> save -> close flow. Do not push.

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
