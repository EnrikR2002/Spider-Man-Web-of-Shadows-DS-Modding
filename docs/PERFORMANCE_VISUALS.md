# Performance and visual upgrade investigation

2026-10-04. The best next performance experiments are the actual DeSmuME CPU,
ROM loading and renderer settings. The clearest visual upgrade is higher internal
3D resolution, followed by selective texture/pose work. Neither a whole-game
speedup nor a new HD art pack has been established by this investigation.

## What was measured and implemented

The accepted HUD already halves its redraw cadence, skips idle work, clears only
owned rectangles, caches projection scale and prewarms its font. Direct counters
show less HUD work, but prior whole-core measurements were roughly flat. Further
HUD optimization is a lower priority until profiling identifies meaningful cost.
The new training chord reuses that observer's existing code block and allocation.

Added `tools/emulator_benchmark.py` and optional timing/core options to the existing
smoke harness. Each worker fresh-boots the same ROM, copied battery and scripted
Continue input; workers run serially. Timing covers host `retro_run`, including its
video callback, and excludes image/RAM exports. It measures host processing cost,
not Nintendo DS frame rate or the user's DeSmuME performance. No old save state
is loaded and the source battery remains byte-identical.

Two rounds alternated software-renderer serial/threaded order. Each ran5000
emulator calls, timing calls3000..4999 after Continue to the Sewer save area.
The scene has idle player/NPC activity, not a dense battle. The tested ROM is
541f62af (same gameplay code/assets as final ecb07b9a, different final wording).

| Mode / round | Mean host ms/call | Median | p95 | Maximum |
|---|---:|---:|---:|---:|
| Serial0 | 5.641 | 6.756 | 7.615 | 13.079 |
| Threaded0 | 4.686 | 5.071 | 7.214 | 10.570 |
| Threaded1 | 4.753 | 5.729 | 7.355 | 10.195 |
| Serial1 | 5.575 | 5.707 | 7.518 | 8.746 |

Across rounds, average cost falls5.608 ->4.719ms, about15.9%. This is a useful
renderer lead, not a proven hitch fix: medians vary and slow tails overlap.
All runs retain the same417 XP/ownership and player position. Final PNGs and
complete player snapshots are not identical: one serial run selects native idle
action102 instead of100. Visually inspected captures are coherent, but exact
framebuffer parity is not established. Host scheduling, Python callbacks and
native idle variation limit precision. Do not compare these timings directly
with different cores, scenes or prior harnesses.

Private report: `work/performance/benchmark.json`; four complete run folders under
`build/boot-tests/OscorpRush-541f62af/benchmark-*`. Reproduce with a closed-emulator
battery checkpoint and a suitable Continue script:

```powershell
python tools/emulator_benchmark.py build/Spider-Man-WoS-modded.nds --save work/save-backups/before-oscorp-rush/save.dsv --script reference/combat-inputs/oscorp-performance-continue.json --rounds 3 --frames 5000 --start 3000
```

## Actual DeSmuME configuration and next tests

Read the configured DeSmuME0.9.13 executable's adjacent INI without changing it.
It specifies Renderer2 (software), Filter0 and a256x384 two-screen source. CPUmode,
JitSize, ROM Loading Mode and PrescaleHD are absent. Release source defaults imply
JIT off, block size12, disk streaming and1x internal rendering. These defaults
are an inference from the release source, not a runtime settings-panel inspection.
The window is already639x958; a larger window alone does not add 3D detail.
[Windows release initialization](https://github.com/TASEmulators/desmume/blob/release_0_9_13/desmume/src/frontend/windows/main.cpp).

The release CLI supports ROM preloading, JIT, block-size control, OpenGL selection
and a2x GPU resolution multiplier. Prepared optional `playtest.py launch --preset`
choices: `performance-preview` preloads/JIT12; `hd-preview` adds AUTOGL/2x.
The normal `Play Spider-Man.cmd` retains its current launch path. Neither preview
was launched or accepted here. The launcher itself does not edit INI files, but
DeSmuME's startup saves the selected renderer, including a CLI override; back up
the INI before an HD trial and restore it while closed if reverting.
[CLI implementation](https://github.com/TASEmulators/desmume/blob/release_0_9_13/desmume/src/commandline.cpp),
[renderer persistence](https://github.com/TASEmulators/desmume/blob/release_0_9_13/desmume/src/frontend/windows/main.cpp#L5410).

| Next isolated trial | Why it might help | Measurement / acceptance |
|---|---|---|
| JIT12 at current renderer/resolution | Reduce host CPU emulation cost; the apparent current default is interpreter | Same save-room and battle routes, at least3 alternating runs; retain correct purchase/input/audio behavior |
| Preload the64-MiB ROM only | Remove host disk reads from streamed ROM access | Compare first/cached room transitions and hitch percentiles; it cannot eliminate the game's own decompression/allocation work |
| OpenGL at1x only | Shift raster work toward the host GPU | Check alpha effects, shadows, fog, UI/health bars and combat behavior before2x |
| Accepted renderer at2x only | Improve 3D edge clarity | Compare same poses/rooms and timing;2x in each axis has4x as many raster pixels |
| Dense combat versus idle on unchanged settings | Determine scene dependence | Compare same enemy count, camera path and incoming hits; idle results are not density coverage |

For direct DeSmuME measurement, record speed percentage, host frame times and
room-transition durations separately. A DS game that produces fewer distinct
frames while the emulator stays at full speed has a different bottleneck from
host emulation slowdown. Current evidence does not distinguish those cases for
the reported intermittent lag. Keep frame limiter, timing accuracy, audio and
purchase/save behavior fixed while isolating each variable.

## ROM-side performance priorities

The new deterministic PuCrunch back-reference encoder prevents changed movement
assets from ballooning under the older literal-only encoder. Rush's two GMBs
take892 combined bytes versus15092 literal-encoded bytes (94.1% smaller), though
the original unmodified pair was664 bytes. Decoded contents, fixed clip lengths
and unknown fields are preserved. All769 native GMBs re-encode/decode correctly;
no-op edits retain original wrappers byte-for-byte. Only two modified GMBs use
the compact mode in this release. Smaller storage is established; decompression
time and FPS improvement are not measured. Do not mass-repack native assets.

If lag persists after the emulator trials, investigate the game in this order:

1. Record native update/render cadence, frame counters and room transitions in
   isolated runs. Establish whether dropped presentation comes from the game or
   host, and whether the same stall occurs in both emulators.
2. Time bounded ARM9 regions for update, common enemy processing, contact checks,
   HUD and resource loading. Begin with read-only sampling; any instrumentation
   must have an original control and its own overhead measurement.
3. Trace allocation high-water marks and texture residency around a specific
   hitch. The current16-KiB HUD reservation is known, but free heap/VRAM peaks and
   room lifetimes are not. Archive sizes cannot substitute for residency.
4. Only after identifying a hotspot, change one asset or algorithm, compare
   fixed and dense scenes, and retain traversal/story/AI correctness. Enemy caps,
   simpler effects, lower texture detail and relaxed timing would trade away
   gameplay or quality; they are not supported performance fixes at present.

## Visual upgrade feasibility

Added `tools/visual_audit.py`: read-only lossless parsing of all272 texture archives,
1654 textures, with dimensions/formats and per-archive pixel/palette pools. The
current player texture is already128x128 I8 (16384 pixel bytes); it was64x64 before
the accepted suit repaint. This investigation does not count that earlier work
as a new upgrade. Native census:1019 textures at128x128,474 at64x64 and133 at32x32;
the rest are smaller/rectangular, including one256x256 texture. Format5 accounts
for1362 textures (82.3%); general compressed-texture authoring is not yet supported.
Private complete report: `work/performance/visual-audit.json`.

| Upgrade | Feasibility now | Expected value and limits |
|---|---|---|
| Internal3D2x, then3x if performance permits | Supported emulator option; prepared preview, actual visual acceptance open | Clearer silhouettes/edges without changing models; no added texel art, polygons or HUD detail |
| Selective same-size environment repaint/palette cleanup | Bounded palette edits supported; format5 recompression needs tooling | More coherent color and readability; first choose one visible texture and prove room/material ownership |
| Improve suit detail at existing128x128 | Existing player texture/material/UV path works | Better painted detail with unchanged pixel allocation; inspect seams and actual small-screen readability |
| Recovery/wind-up pose polish | Existing independent dynamic SCA tracks editable | Rush now adds bounded recovery keys; other attacks need contact/timing tests, not wholesale rig changes |
| Better HUD/icon typography | Native font/canvas reusable; some tiled sprites decoded | Current bars/text fit; global font/UI rebuild and options widgets remain research |
| Higher-poly models, new rigs, broad HD texture pack | Substantial tooling/memory work | Topology, skeleton authoring, room texture ownership and resident budgets are unproved |

Largest native pixel pools include Downtown_Map07 (161280 bytes/45 textures),
Downtown_Map11 (149504/29), Downtown_Map06 (144640/37) and Sewer_Map03 (134144/23).
These are storage totals, not simultaneous VRAM or proof that these rooms cause
lag. Enlarging many textures before residency tracing is not justified.

Begin with2x internal3D and the existing suit. Then select one high-visibility room
texture, map its model/material use, add a format-appropriate round-trip editor
and compare one same-size repaint in normal play. This yields a concrete visual
trial while keeping memory growth measurable. Broad environment, lighting,
animation and model redesign remains a separate incremental project.
