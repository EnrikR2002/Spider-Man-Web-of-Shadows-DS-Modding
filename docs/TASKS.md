# Current work and handoff

Updated 2026-11-06 (America/Edmonton). Read AGENTS first. DEVELOPMENT owns
workflow, TECHNICAL engine contracts, CHANGES releases and ROADMAP design.

## Current objective

Freefall, the next 2099 skill after Boarding, is installed through Ground
Rebound's existing purchase. The player required Luna to score both look and
feel at least 8/10.
It reaches an enemy nine units away where the parent misses, and a 53-unit
drop bounces three Brutes into a manual Talon Lift. The earlier review found
a stale contact on the same update as a ground R cancel. The final candidate
clears that contact on both neutral and backward R. All 14 copied-save
controls and 83 targeted strict tests passed. Luna independently rechecked
both cancels and rated the installed ROM 8.5/10 look and 8.2/10 in-engine feel
from timestamped frames and controller traces. Evidence is in
`reference/freefall.json`.

Separate Crane Row Blender request: the private Ballast study retains its rig,
texture and 266-quad budget. Luna's 8/10 covers Ballast stills and sampled
frames. Normal-speed motion, mixed audio and the other two enemies remain open.
Reproduce the study with
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

Stable `build/Spider-Man-WoS-modded.nds` is **v0.41.0**, SHA256
`d411a9cbce8cb0d679da23673b32b4be2de543ecd60b9ceb2ff25ffeeb7ff70d`.
`tools/playtest.py build` installed the exact reviewed ROM from the clean
source. Boot and Options show v0.41.0. The v0.40.0 ROM, metadata and recipe
are preserved under `build/releases` and `build/version-0.40.0-final`.
The actual 634-byte DSV matched its validated checkpoint byte for byte.
Read the actual battery afresh before the next lab or release.

## Blockers and next exact action

Open `Play Spider-Man.cmd`, Continue, and try Black Freefall on air Down+A
from both a jump and a taller fall. Buy Freefall for 150 XP if the Ground
Rebound slot is still unowned. A player feel and hardware verdict is open.

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
