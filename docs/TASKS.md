# Current work and handoff

Updated 2026-11-06 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

Talon Pounce is installed through Super Charge's existing 225 XP purchase.
Luna rated the exact ROM 8.1/10 for look and 8.0/10 for in-engine feel. A low
pounce connected across 24.69 units. A rising pounce fed manual Sky Rake and
handed off to Boarding on the Conductor. Nineteen copied-save gameplay and
shop controls passed, plus the Freefall cancel regression. Ground R, paid and
unpaid air R, the wall and form-change controls passed. The full qualification
and review limits are in `reference/talon_pounce.json`.

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

Open `Play Spider-Man.cmd`, Continue, and buy Talon Pounce in the Black
upgrade list if Super Charge was unowned. Hold Y until Miguel coils, then
release. Try Up on release against a jumping enemy or while holding toward
a boss with Boarding owned. Player feel, audible mix and hardware verdicts
are open. Relentless is next in the approved order.

For the Crane Row study, review Ballast's motion and mixed audio before expanding
to Maw and Spore: neither available reviewer can play or hear the clip, so the
player was asked to check `work/crane-models/ballast-v5-4sec.mp4`. The healed
6,000-frame mixed fight timed out but sampled a get-up; a separate 1-HP RAM
fixture observed a native Ballast death, not a normal-HP clear. Then test the
remaining models, review the final composition with Luna, and publish after
all required qualification. Do not push.

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
