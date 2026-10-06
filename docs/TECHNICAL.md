# ROM technical knowledge

Updated 2026-10-05. This is the single technical notebook. Search its headings and
read only the relevant section; never bulk-read it to start a session. Confirmed
fields, hypotheses, unknown bytes, editing confidence and test evidence belong
here. Release behavior/history belongs in [CHANGES](CHANGES.md), native gameplay
in [OG_GAMEPLAY](OG_GAMEPLAY.md), current work in [TASKS](TASKS.md).

## ROM baseline and inventory

### ROM
- Title: `SPIDERMANWOS`
- Game code: `CS5E`
- Maker code: `52`
- ROM image: 64 MiB
- Used ROM size: `0x03630800`
- ARM9 size: 1,325,496 bytes
- ARM7 size: 159,192 bytes
- ARM9 overlays: none
- ARM7 overlays: none

### NitroFS
Only two files exist:
- `Glob.bin`: 35,637,872 bytes
- `sound_data.sdat`: 19,678,720 bytes

This is unusually convenient: nearly all game-specific content lives in one archive.

### Glob.bin container
Confirmed from the supplied ROM:
- Offset table begins at byte 0.
- `offsets[0] == 0x3A58 == 14,936`, so the table contains 3,734 u32 offsets.
- There are 3,733 resources.
- `offsets[-1] == 0x021FCA70 == len(Glob.bin)`.
- Resource `i` is `Glob[offsets[i]:offsets[i+1]]`.
- Resource index 805 is `GlobFiles.txt`.
- `GlobFiles.txt` is 238,912 bytes = `3,733 * 64`.
- Each 64-byte record is a padded filename + newline and maps 1:1 to the resource index.
- No duplicate filenames were found.

### Resource inventory
Counts observed:
- `.sca` 869
- `.gmb` 769
- `.nsbmd` 280
- `.nsbtx` 272
- `.xbd` 248
- `.gab` 227
- `.2lz` 153
- `.dat` 153
- `.pal` 153
- `.cbmp` 142
- `.nsbta` 89
- `.bsp` 75
- `.obj` 75
- `.mdat` 65
- `.mgfx` 65
- `.mpal` 65
- `.font` 14
- `.gaftx` 10
- `.strings` 6
- `.tfb` 2
- `.txt` 1 (`GlobFiles.txt`)

### Standard Nintendo Nitro formats already exposed
- `.nsbmd` has `BMD0` magic: 3D models
- `.nsbtx` has `BTX0` magic: texture archives
- `.nsbta` has `BTA0` magic: material/texture animations
- `sound_data.sdat`: Nintendo SDAT audio archive

These can be investigated with existing DS tooling such as apicula, NitroPaint, and Tinke/TinkeDSi.

### Important custom formats / likely responsibilities
- `.bsp` starts with `BSP\0`; paired with map `_app.obj` files. Strong candidate for room collision/geometry/navigation/region data.
- `.obj` paired with maps; likely placed objects/entities/triggers/encounters.
- `.xbd` associated with character/object model sets; likely definitions/bindings/state metadata.
- `.gab`, `.gmb`, `.sca` appear in animation/attack/state triplets. Player `spd_*` assets expose hundreds of named moves, making these high-value combat targets.
- `.mdat/.mgfx/.mpal` occur in visual scene/cutscene groups.
- `.2lz/.dat/.pal` occur in UI/minimap/tutorial sprite groups.
- `.strings` files are not plaintext; likely compressed/encoded and deserve separate RE work.
- `.cbmp` is a custom bitmap-like format.

### Player assets
The playable Spider-Man set is clearly exposed with prefix `spd`:
- `spd.nsbmd` (15,108 bytes)
- `spd.nsbtx` (4,772 bytes)
- `spd.xbd` (2,024 bytes)
- `spdB.nsbmd` (15,108 bytes), likely the alternate/black-suit model
- hundreds of named action assets, e.g. `spd_GroundAttack1.*`, `spd_Dash.*`, `spd_WebSwing*`, etc.

This is a strong sign that gameplay expansion can eventually be data-driven rather than requiring a full source decompilation.

### Map assets
Named room pairs expose the world structure directly. Confirmed regions include:
- Downtown: Map01..Map14 + save rooms
- Hive: Map01..Map10 + save rooms
- Pier: Map01..Map08 + save rooms
- Residential: Map01..Map09 + save rooms
- Sewer: Map01..Map13 + save rooms
- several test maps (`Test_Combat01`, `Test_Collision01`, `Test_Challenge01`, etc.)

The presence of shipped test maps is especially useful for reverse-engineering room formats and experimentation.

### Repacking
The included `tools/wos_tool.py` can already:
- parse NitroFS
- extract `Glob.bin` / `sound_data.sdat`
- unpack all 3,733 named Glob resources
- repack Glob after arbitrary same-file-count edits, including changed resource sizes
- rebuild the ROM and update NitroFS FAT offsets, keeping the original 64 MiB cart capacity

Next milestone: boot-test an unmodified round trip, then one visible asset modification.

### Validated workflow update — 2026-10-02

The original facts above were reproduced against the supplied clean ROM. Glob and
full ROM no-op rebuilds are byte-identical, with all 3,733 extracted resource hashes
verified. `mod.py` now provides validated overlay builds, extraction, listing,
search and verification; size changes update FAT/header CRC and stay within capacity.

The unmodified round-trip build and a single `spd.nsbtx` palette edit both reached
Residential gameplay in melonDS DS 1.1.5. The edited player's red suit appears green.
Reverting the overlay reproduces the original ROM hash. The next milestone above
has therefore been completed for this bounded boot/visible-change experiment.

Further confirmed structures include actor XBD references to archive IDs and
GMB compression (749 PuCrunch, 20 LZ77). 149 UI 2LZ files also use PuCrunch.
Since this baseline survey, bounded gameplay/purchase routes, sampled SCA
animation and English/American text slots have been decoded and tested. Room
semantics and many gameplay fields remain unknown; consult current references.

See [FORMAT_NOTES](TECHNICAL.md), [MODDABILITY_MATRIX](TECHNICAL.md),
[GAMEPLAY](OG_GAMEPLAY.md) and [TASKS](TASKS.md) for current findings/status. Original
validation and visible experiment evidence are preserved in the documentation
archive; read with `python tools/doc_archive.py read VALIDATION.md --toc` or
`read VISIBLE_MOD.md --toc`.

## Format boundaries and confirmed structures

Updated 2026-10-05. Confirmed facts below apply to USA **CS5E** only. Unknown
fields remain unknown and must survive editing. This is a compact technical
entry point; the complete earlier specifications/experiments are preserved in
the archive. Read a named note/section with `python tools/doc_archive.py read
<name> --section '<heading>'`; use `--toc` to locate exact headings.

[Baseline inventory](TECHNICAL.md), [editing confidence](TECHNICAL.md),
[gameplay map](OG_GAMEPLAY.md), [animation layout/tools](TECHNICAL.md).

### NDS / NitroFS

Clean image: 64 MiB. FNT `0x0016E800`/34 bytes, FAT `0x0016EA00`/16 bytes,
banner `0x0016EC00` version1. No ARM9/ARM7 overlays.

| FAT ID / file | Start | Exclusive end | Bytes |
|---|---:|---:|---:|
| 0 / Glob.bin | 0x0016F600 | 0x0236C070 | 35,637,872 |
| 1 / sound_data.sdat | 0x0236C200 | 0x03630800 | 19,678,720 |

FAT fields are LE u32. Header used-size field is at `0x80`; CRC16 at `0x15E`
covers `[0,0x15E)`, initial FFFF, reflected polynomial A001. No-op ROM rebuild
is byte-exact, including unknown headers, gaps/tails, executables and banner.
Resized resources update FAT/CRC within capacity; unknown/vacated bytes are
preserved. Implementation: `tools/wos_tool.py`, `mod.py`.
Detailed original verification: archived `VALIDATION.md`, `FORMAT_NOTES.md`
section `NitroFS / ROM`.

### Glob.bin and bounded additions

Archive is `N+1` LE u32 offsets, followed immediately by resource payloads.
`offsets[0]=(N+1)*4`; resource i is `[offsets[i],offsets[i+1])`; final offset
is exact archive length. Original N=3,733, table `0x3A58`, length `0x021FCA70`.
ID805 `GlobFiles.txt` has one 64-byte padded filename/newline record per ID,
238,912 original bytes. Exact filename/case and monotonic/bounded offsets are
validated. Ordinary overlays cannot alter names or add arbitrary resources.

Authored Rush appends only three fixed SCAs at IDs3733..3735, preserving every
old ID/name record. N=3,736; table grows12 bytes. Loader `0x02007758` reads
count+1 offsets; count literal at ARM9 source `0x77F8` / runtime `0x020077F8`
is patched3733 ->3736. Getter `0x020079F0`, name lookup `0x02007A04` remain
native. Fixed-name/layout/hash guards, append/repack/strip-exact-revert tests
and runtime qualification are confirmed; general additions remain unsupported.
Details: [ANIMATION](TECHNICAL.md), `tools/oscorp_resources.py`.

### XBD bindings

All248 envelopes round-trip. LE u32@0 is an **unknown numeric kind**, repeated
as final word; u32@4 equals file length-12. u16@8/@10 and other flags/tails
remain unknown. Only kind `0x8E3E7B2B` (155 actor files) has decoded references
from `0x14`: repeated `<s16 index,u16 tag>`. Tags0/1/3/4 bind SCA/NSBTA/GMB/GAB.
Negative tail entries are not assumed to be asset IDs. Other kinds (92 mostly
UI plus one other) have envelope-only parsing.

Snap uses G15's SCA/GMB/GAB through its base route. Original G11/16/17 are
also referenced by `m6.xbd`; all original player animations have actor users.
Authored Rush changes only three player SCA bindings, with other actors and
GMB/GAB bindings retained. Source: `tools/custom_formats.py`. Archived
`FORMAT_NOTES.md` section `XBD` holds precise counts/boundaries.

### GAB / GMB / compression

GAB: 227 lossless round trips, six-byte records plus terminator/padding.
Event7/8/9 have bounded reset/action-marker findings; event8 is not meter credit.
Event1 parameter meanings and generalized event semantics remain unknown.

GMB decoded header has four LE u16 words: +2 record count per channel,
+4 channel count; +0/+6 unknown. Each channel begins `<s16 kind,u16 unknown>`.
Confirmed record strides: kind0=28,2=44,3=32,4=48,5=36,6=44,12=32 bytes.
Kind2 supplies bounded movement: sampler `0x02071BAC` reads +8 horizontally
with facing sign and +4 vertically; normal physics adds roots before collision.
Other geometry/contact fields have limited correlations, not a complete schema.
All769 structured round trips pass; all126 player layouts validated.

Native GMB wrappers:749 PuCrunch,20 LZ77;149 UI 2LZ use PuCrunch. Four 2LZ
00 wrappers remain unknown. No-op compression retains original bytes.
Literal encoding plus decoded equality was tested across918 supported GMB/2LZ
files. Compact0x60 encoding additionally passes all769 native GMB decoded
round trips. Only two changed Rush GMBs use compact encoding; smaller files
are confirmed, decompression/FPS gains are unmeasured.
Sources: `tools/gmb.py`, `grip_compression.py`; archive `COMBO_ENGINE.md` /
`FORMAT_NOTES.md` headings `GMB channel boundaries`, `Compression wrappers`,
`GAB record boundaries`. Never infer HP damage from response/credit fields.

### SCA / model / textures

SCA layout, descriptor encoding, canonical37-bone rig, independent-track growth,
current authored clips and all869 byte-exact/sample-document round trips are
summarized in [ANIMATION](TECHNICAL.md). Native scale/inverse-scale fields,
unknown bytes and sample clocks remain preserved; scale edits/retiming/Blender
calibration and heap headroom are unproved.

NSBTX: all272 archives parse losslessly; native census1654 textures. Bounded
player I8 repaint grows64x64 ->128x128 using confirmed model UV/material changes;
1x identity/inverse checks and gameplay boot pass. Palette editing works;
general format5 compressed-texture authoring does not. NSBMD supports bounded
UV/material inspection and the read-only rig map, no topology/skin editor.
NSBTA actor references are mapped; its payload has no local editor.
Tools: `nitro_texture.py`, `movie_suit.py`, `visual_audit.py`, `animation_rig.py`.
Archive `MOVIE_SUIT_EXPERIMENT.md` and `FORMAT_NOTES.md` heading `NSBTX / TEX0`.

### Text / UI / rooms / audio

English/American STRINGS: hash-bounded Huffman tree plus1,049 UTF-16LE slots
round-trip; unknown prefix and untouched slot tails survive. Same-slot localized
names/input/prerequisite edits are supported, other languages unproved. Native
FONT/canvas/UTF16 rendering is traced, no font-file editor. Archived
`FORMAT_NOTES.md` section `Bounded English/American text slots`, `QOL_CLARITY.md`.

Two hash-identified minimap sheets have coherent4bpp tiled previews and exact
round trips. DAT first two bytes fit those two dimension candidates; other DAT
fields/palette ownership are unknown. The mission palette's original red is
restored.153 UI families/142 CBMP files are inventoried; no general UI schema
or CBMP editor. Archive section `Minimap investigation`.

All75 BSP envelopes parse losslessly: `BSP\0`, LE u32@4=7/@8=2 (meanings
unknown), @12=file length, @16=table end, bounded monotonic even offsets,
last table word01000000. Spatial/collision/node semantics remain hypotheses.
Paired OBJ starts u32=2; placements/triggers/encounters are hypothesized,
not decoded. Downtown_Save02/03 has a useful104-byte OBJ difference.65
MDAT/MGFX/MPAL scene groups are inventoried, unedited. SDAT is preserved as a
whole file; individual audio editing is untested. Archive section `BSP + paired OBJ`.

### Engine / saves / qualification

Native21 purchase records, flags, costs and dependencies are mapped; read
[GAMEPLAY](OG_GAMEPLAY.md) before paid route changes. Current recipe is guarded by
`reference/gameplay_profile.json` (now tasm-v0.2.0: v0.1.1 parent + Red kit;
Sling's hooks restored, Rebound response retuned for Leapfrog). The HUD + kit
extension reserves 24 KiB; free heap/VRAM peaks are unknown. Common player/enemy
HP telemetry is actual loss, with specialized health coverage still incomplete.
Training SELECT+Down refill has positive/flag-clear controls and preserves
position/reaction/XP/meter; other target flags are unknown.

DSVv0 wrapper is lossless/validated; game payload/checksum remains opaque.
Snapshots are byte-preserving, not a save editor. Native purchase/refund/save/
reload checks pass for released moves; real-save protection is separate from
copied-save fixtures. Follow [WORKFLOW](../README.md).

Latest authored Rush: eight choreography tests, all3,736-resource build check,
both-facing contact/HP/credit/final-position parity. Prior compact source passed
125 tests; latest gameplay revision did not rerun that full suite. Original
archive extension shifted all observed contacts two emulator frames, including
unchanged Snap; count-only control has the same shift. Relative clocks/timing
remain exact, with no established FPS change. Player/ordinary encounter,
walls/bosses/interruption/long-play acceptance remains open.

Documentation cleanup preserved every original note byte and SHA256 in the
archive before consolidation; all36 entries verify and the ZIP repacks exactly.
All131 current source tests pass during maintenance, including four archive
integrity/reader checks. No additional emulator/player coverage was added.
New facts should update the relevant section here,
with focused evidence links; avoid appending another duplicate release log.

## Animation authoring and current evidence

Updated 2026-10-05. **Current authoring path: `tools/kit_choreography.py` +
`tools/kit_clips.py` (see "Kit animation authoring" below).** The Oscorp Rush
material in this section is history: v0.2.0 re-authored its three resources as
Split Decision. Full choreography on the existing37-bone player rig works
through procedural FK/IK. Blender conversion, new rigs/models and variable
clip duration remain research. Read [TASKS](TASKS.md) for current acceptance and
[WORKFLOW](../README.md) before publication. Exact original investigations are
archived as `ANIMATION_RESEARCH.md`, `ANIMATION_AUTHORING.md`,
`OSCORP_RUSH_ANIMATION.md` (use the archive reader's `--toc/--section`).

### Confirmed SCA layout

Original SCA loader `0x0201C958`, frame reader `0x0201CAA0`, evaluator ITCM
`0x01FF8BC0` (ARM9 source `0x13ED00`; ordinary load-base subtraction is wrong).
All integers are LE. Header28 bytes:

| Offset | Meaning |
|---|---|
| 0 | `4ACS` tag |
| 4 / 8 | u32 sample count / joint count |
| 0xC / 0x10 | u32 static-pool byte length / per-frame stride |
| 0x14..0x16 | u8 static translation/scale/rotation counts |
| 0x17..0x19 | u8 dynamic translation/scale/rotation counts |
| 0x1A..0x1B | Unknown; preserved |

Three descriptor bytes per joint, **T/R/S** order. Each has index=`byte>>1`,
static=`byte&1`. Pools store **T/S/R**: translation3*i32 Q12/12 bytes,
scale+inverse6*i32 Q12/24 bytes, rotation9*i16 Q12 matrix/18 bytes.
4096=1.0. Matrices are not Euler angles/quaternions; the native evaluator
interpolates coefficients. Shared/constant descriptors alias consumers.

```text
static_start = 28 + align4(3 * joints)
static_bytes = 12*static_T + 24*static_S + 18*static_R
frames_start = static_start + align4(static_bytes)
stride = align4(12*dynamic_T + 24*dynamic_S + 18*dynamic_R)
file_size = frames_start + samples*stride
```

All869 originals satisfy this layout and round-trip byte-for-byte;126 player
clips have37 joints. Zero stride is valid. Unknown/alignment bytes remain exact.
`tools/sca.py` provides structural parsing/bounded edits. `sca_author.py`
exports sample JSON and imports independently appended rotation/translation
tracks: unchanged import is exact; source hash/joint/sample counts are guarded.
It preserves original pools, untouched tracks and unknown bytes. Scale/inverse
scale authoring is disabled; nonzero discarded alignment is rejected;
indices cannot exceed the7-bit descriptor range.126 player independent bakes
and all869 unchanged sample-document round trips are established.

### Rig and coordinate contract

`tools/animation_rig.py` verifies original NSBMD names/parents against SBC matrix
stack ancestry. Canonical indices: Chest3, shoulders7/17, hips26/30. Apicula's
DAE exports34 joints in a different order and omits helpers34..36; never map
its joint ordinals directly to SCA. The model is preserved, not edited.

Rush FK uses the stored SCA rotation transpose for column-vector matrices:
Y up, Z forward. In its explicit straight-root authoring basis local X maps
world Y, local Y world Z, local Z world X. This is calibrated for this rig/basis,
not a universal axis assumption. BackA twists about local X; the previous
local-Y choice tipped the torso. Controls use smooth curves, quaternions and
two-bone IK, then quantize/re-read the native SCA.

Blender bridge still needs bind/axis calibration, evaluated constrained pose
sampling and parent-local Q12 conversion. Rest/world matrices cannot simply be
copied into SCA. Calibrate with neutral pose and isolated positive-axis rotations;
retain omitted helpers. Detailed conversion hypothesis and primary-source links
are preserved in archived `ANIMATION_AUTHORING.md`, section `Rig mapping and
Blender conversion`. No tested Blender import/export is claimed.

### Oscorp Rush (historical, superseded by Split Decision in v0.2.0)

400 XP/event325/bit16. Input **Y, let Snap finish, Y,Y,Y**. The player confirmed
novel choreography, rejected dance-like sway, then rejected compact boxing as
stubby. Latest published revision uses larger windups, camera-plane reach,
a rising uppercut, full high kick and lunging overhand; player quality acceptance
remains open. It retains native clocks, six paid contacts, HP/credit and prior
root advance/commitment, with native ownership/refunds.

| Action | Samples / contact clocks | Dedicated SCA / ID / player binding offset |
|---|---|---|
| 61: loaded straight, high cross, uppercut | 39 / 5,12,18 | zz_tasm_RushEntry.sca / 3734 / 416 |
| 60: high knee/recoil/full kick | 12 / 4,9 | zz_tasm_RushBridge.sca / 3733 / 404 |
| 62: loaded lunging overhand | 20 / 6 | zz_tasm_RushFinish.sca / 3735 / 428 |

Original G11/16/17 are also used by `m6.xbd`; no globally free spare exists.
All original3,733 IDs/name records/animation payloads and other actor bindings
stay exact against the accepted parent. Only three player SCA bindings change;
Snap triple356/360/364 and GMB/GAB bindings remain. The archive appends three
64-byte name records at ID805 and patches the confirmed count literal3733->3736
(source0x77F8). Ordinary overlays still reject arbitrary additions.

Entry/finish foot IK retains ground height with small forward adjustments;
bridge deliberately lifts its knee. Wrists align to forearms, fingers/scales
remain native; post-blend ankle correction prevents the known recovery dip.
Final sample19 matches native Idle0 rotations/translations. Brief keyed limb
translation stretch is bounded: entry arms12%, finish arm16%, kick8%; native
lengths return outside windows. No unknown scale field is authored.

Re-read pose evidence: kick two-bone reach0.353->0.990; ankle Y2.26/Z1.13 ->
Y4.80/Z5.79; entry contact wrists Z2.38/2.51 ->3.76/4.02; uppercut Y6.10->8.41.
These are pose coordinates, not hitbox reach/screen pixels. New bridge/entry/
finish sizes12,376/53,848/31,768 bytes; strides956/1364/1560. Heap high-water,
unused-track compaction and extra metadata remain unmeasured.

Scissor bit17 still repeats this bridge, not redesigned Barrage. One rapid-input
fixture repeats action60 four times/eight contacts; late contacts cross a native
meter tier and both parent/new builds agree on HP loss. No universal cap is
established. Next research is distinct bit17 Barrage entry/limit/control/routing.

### Reproduction and qualification

```powershell
python tools/oscorp_animation.py --out build/oscorp-anime
python mod.py verify --mods build/oscorp-anime/mods -o build/oscorp-anime/OscorpAuthored.nds --gameplay-profile build/oscorp-anime/gameplay_profile.json
python -m unittest discover -s tests -p test_rush_choreography.py -v
```

Generators: `oscorp_animation.py`, `oscorp_resources.py`, `rush_choreography.py`.
They accept exact known parents/compositions; historical move generators must
not overwrite an authored profile. Use copied battery fresh boots, never stale
states. Export/import CLI details: archived `ANIMATION_AUTHORING.md`, section
`New working authoring tools`; original native schema/loader evidence:
`ANIMATION_RESEARCH.md`, sections `SCA4 header`, `Joint descriptors`.

Stable published ROM hash is in TASKS; ARM9 SHA256
`72ab438e0998ec2b021bd79a4f36adf5e88a456ccbe51afff100c81461390b12`.
Current revision passed eight choreography tests including two baked reach/stretch
checks; build verifies3,736 resources. Prior compact source passed125 tests;
latest pose release did not rerun the complete suite.
Maintenance subsequently passed all131 current source tests; it added no new
runtime/player coverage. Both-facing copied-battery
floor replays match parent contact frames, HP/credit/final position; only three
SCAs and two localized instruction resources change against f0382e98. Bindings,
GMB/GAB and ARM9 are exact. Candidate/stable/fresh regeneration are byte-identical.

Initial append shifted all contacts (including unchanged Snap) two emulator
frames earlier; count-only control with old bindings/text shows the same shift.
Relative timing/clocks/loss/credit remain equal; it proves no FPS change.
Control: `build/oscorp-count-control/CountControl.nds`,
`build/boot-tests/CountControl-409c6d41/count-only-owned/`.

Current proof: `work/animation-research/anime-evidence.json`, `check-anime.py`,
`anime-tests.log`, `anime-publication.log`; poses `build/oscorp-anime/choreography.json`;
replays `build/boot-tests/OscorpAuthored-4d36970e/{anime-right,anime-left}/`.
Regeneration `build/oscorp-anime-regenerated/`. Historical compact proof
`visual-refinement-evidence.json`, replays `OscorpAuthored-f0382e98/`; initial
proof `dedicated-evidence.json`, `check-dedicated.py`, `qualify-dedicated.py`,
replays `OscorpAuthored-8bc72be4/`, poses `build/oscorp-dedicated/choreography.json`.
Those JSON/scripts live under `work/animation-research/`; replay folders under
`build/boot-tests/`.

Original paid buy/refund/save/reload/locked checks remain recorded; gates match.
Publication preserved the then-current real battery and prior releases; TASKS
records its hash/checkpoints. Ordinary/dense AI, walls/ceilings, specialized
enemies/bosses, interruption, long play and current player feel remain open.
Floor contact parity and reviewed contact sheets do not cover those encounters.

## Performance and visuals

2026-10-04. The best next performance experiments are the actual DeSmuME CPU,
ROM loading and renderer settings. The clearest visual upgrade is higher internal
3D resolution, followed by selective texture/pose work. Neither a whole-game
speedup nor a new HD art pack has been established by this investigation.

### What was measured and implemented

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

### Actual DeSmuME configuration and next tests

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

### ROM-side performance priorities

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

### Visual upgrade feasibility

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

## Editing status and confidence

Updated 2026-10-05, private USA CS5E. Confidence refers to the stated structure;
runtime/player acceptance requires separate checks. [Format entry points](TECHNICAL.md),
[current release](TASKS.md). Detailed former matrix is preserved in the archive.

| Format / area | Likely or confirmed control | Parsing | Editing | Confidence / limitation |
|---|---|---|---|---|
| NDS / NitroFS | Executables/top-level resources | FNT/FAT/CRC/bounds/capacity validated | Exact no-op; resized files in64 MiB | High for tested no-overlay layout |
| Glob.bin | Ordered named assets | 3,733 original; 3,742 authored resources verified | Variable sizes; Rush 3 + kit 6 guarded additions; IDs retained | High for tested append/revert; arbitrary names/manual GlobFiles rejected |
| NSBTX | 3D pixels/palettes | 272 lossless;1654-texture census | Palette and bounded128x128 player I8 repaint | High bounded path; general format5 encoding absent |
| NSBMD | Models/UVs/materials | Player export and rig/SBC mapped | Bounded player UV/material changes | No topology/skin/skeleton editor |
| NSBTA | Material/texture animation | Inventory, XBD tag1 bindings | No local editor | Bindings confirmed; payload undecoded |
| XBD actors | Asset bindings; other state unknown | All248 envelopes;155 actor binding sets | Synchronized Snap triple; three isolated paid SCAs | High bounded routes; opaque tails preserved |
| XBD other kinds | UI/configuration, inferred | 92 UI-associated plus one envelope | Raw replacement only | Payload unknown |
| GAB | Timed action events | 227 lossless record round trips | Existing bindings; no general event editor | Bounded event7/8/9 findings; event1 parameters unknown |
| GMB | Root motion/contact geometry | 769 lossless;126 player layouts; compact codec decoded round trips | Single-word/root/response edits; no-op wrappers retained | Confirmed strides/selected motion; unknown geometry preserved |
| SCA | Joint T/S/R animation | 869 exact/sample round trips;126 independent player bakes | Kit FK/IK clips (flips, spins, handstand) at native sample counts; runtime routing | High tested growth/poses; scale/retime/Blender/heap/broad encounters open |
| Player rig | Canonical37 names/ancestry | Model dictionary/SBC ancestry agree | Read-only map/authoring controls | DAE34-bone ordinals differ; no skin editor |
| BSP | Room spatial/collision, hypothesis | 75 lossless envelopes/offsets | No geometry editor | High envelope; node/coordinate semantics unknown |
| OBJ | Placements/triggers/encounters, hypothesis | 75 pairs;word0=2 | No object editor | Low;104-byte Save02/03 difference is a lead |
| STRINGS | Localized instructions | English/American Huffman/1,049 slots round-trip | Bounded same-slot names/descriptions | High bounded codec; other languages/popups unqualified |
| FONT | Glyphs/metrics | Inventory/native draw traced | Reuse stock font/canvas | File editor absent |
| 2LZ | UI/sprites, likely | 149 PuCrunch;two minimap previews round-trip | Bounded tiled conversion | Four00 wrappers/general schema unknown |
| DAT / PAL | UI metadata/palettes, likely | 153 families;two dimension candidates | Guarded marker palette/revert; red restored | Wider ownership/DAT fields unknown |
| CBMP | Custom bitmap, likely | 142 inventoried | No editor | Low |
| MDAT / MGFX / MPAL | Scene groups, likely | 65 sets inventoried | No editor | Low |
| SDAT | DS audio | Whole file preserved/hashed | Whole-file replacement surface only | Internal audio edits untested |
| ARM9 | Rules/gates/health/movement | Hash-guarded known tables/hooks/autoload | Bounded HUD/refill/count patches + Red kit hooks | Unknown health/counter/speed paths; 24 KiB reserved, headroom unmeasured |
| Combo / health HUD | Native combo rewards, wounded bars | Model/category/common HP/projection mapped | Transient combo numeral/continuous bars | Specialized HP/density/ordinary hits and player feel open; no inferred damage |
| Saves | Progress/ownership | DSVv0 wrapper exact;game payload opaque | Byte-preserving backups/guarded restores | Native buy/refund/save/reload tested; no game-save editor |
| Purchases | Native7+7+7 rows | All21 costs/flags/dependencies mapped | Kit: Leapfrog13 Skyjack14 Perch15 Split16 Spin17 Reflex18 Sense19 | Expanded rows/ownership/save migration unproved |
| Third suit | Independent selectable kit | Red/alternate routes partly mapped | Red prototype only | Selector/UI/persistent slot unimplemented |
| Training refill | Common target max HP | Native flag4/chord/setter mapped | SELECT+Down in existing observer | Positive/flag-clear controls pass; no full state reset |
| Performance/graphics | Host emulation/rendering/resolution | INI/source inference, host benchmarks, texture census | Optional inactive previews, compact changed GMBs | Idle threaded mean~15.9% lower; actual DeSmuME hitch/FPS/2x acceptance unproved |

Released composition (v0.2.0): 22 overlays, original IDs retained, 3,742
verified resources (Rush 3 + kit 6 appended). Kit qualification 20/20
(`python tools/kit_lab.py qualify`); 151 source tests pass.
Player acceptance and ordinary/dense AI,
specialized enemies/bosses, walls/ceilings/interruption/long play remain open.
No game assets/saves/captures are included in source documentation.

## Native engine purchase and combo mapping

Original engine baseline; released prices now differ.

### Purchase records and native ownership

Original ARM9 Red table: runtime `0x02120340`, source `0x120340`, seven32-byte
records/eight LE u32 words. Record fields: +0 first ownership event,
+4 required event, +8 dependent event, +0xC/+0x10 name IDs, +0x14 description
ID, +0x18 consecutive levels, +0x1C price per level.382 is the no-event sentinel.
A dependent event prevents refunding/selecting an owned parent while its child
is owned; it is not an extra granted skill. Table pointer list `0x02120170`,
counts `0x02120188`.

| Native Red slot | Event / bit | XP | Required / dependent |
|---|---|---:|---|
| Web Kick | 322 / 13 | 100 | None / none |
| Web Launch | 323 / 14 | 200 | None / none |
| Mid-Air Snare | 324 / 15 | 600 | None / none |
| Spider Dance | 325 / 16 | 400 | None / 326 |
| Scissor-Kick Special | 326 / 17 | 600 | 325 / none |
| Amazing Speed Boost | 327 / 18 | 800 | None / 328 |
| Ultimate Speed Boost | 328 / 19 | 1,000 | 327 / none |

Event query `0x020D22AC` / setter `0x020D24D8` map309..381 to bit event-309.
Stats pointer `0x02145C5C`, ability words+0xC, currency+0x44. Player+0xE8
aliases stats abilities; getter `0x02060240` uses native bit test `0x0203B98C`.
Menu predicate `0x020F1150`, buy `0x020F1AA0`, refund `0x020F1B4C` retain
native costs/dependencies. Runtime bits are not decoded on-disk save offsets.
`tools/upgrade_trace.py` reads guarded RAM; no save editor is established.

Preserve Web Kick gate `0x020B603C` (bit13; success state42), Web Launch query
`0x020B6264` (bit14; success state40), Rush bit16 and Scissor bit17 gates.
Controller states, animation action IDs, GMB IDs and contact/credit categories
are different namespaces. Position getters use signed motion+0x7C/+0x160 and
+0x80/+0x164; geometry dimensions+0x88/+0x8C/+0x90 are not position.

### Combo resource and HP are different

Native combo model pointer cell `0x02145C44`; heap addresses vary. Model offsets:
+0 tier (max5), +4 signed Q12 gauge0..100, +8..+0xC repetition history,
+0x10 decay grace, +0x14 decay (initial0.5), +0x18 active, +0x19 grouped-contact
credit marker (complete lifecycle unknown). HUD initially becomes visible at
tier>0 or gauge>30. Snap can earn real credit below that threshold.

Initializer `0x020836E4`, decay `0x02083718`, category registration `0x020837D8`,
accumulator `0x02083BF0`. Crossing100 advances a tier/subtracts75 with at least30
updates' grace; ordinary gain supplies at least15. Decay can lose tiers and
accelerate. These are game updates, not established seconds. Penalty path
`0x02083A9C` subtracts two tiers; its exact trigger needs runtime confirmation.

Credit table `0x0211BCB0` is `<u8 base,u8 repetition%,u16 expiry>` indexed by
category, not asset ID. Tier scaling `0x0211B894` approximates
0.8/0.65/0.5/0.4/0.3/0.2. Red logical opener56 maps category0, black55 maps7;
both records15/100/180. Snap retains red56/native credit (first observed gain
~12), with no boost. The native meter improves XP rewards; exact multipliers
remain unknown. It is not a hit counter or an HP-damage display.


## Versioned text growth and pricing (v0.1.0)

String tree at0x1064/size0x16C;1049 LE u32 offsets at0x11D0 are relative to0x1064.
The variable-size repacker preserves unknown prefix/tree and every unedited slot
byte, updates these offsets, and retains an oversized replacement's complete old
slot after its new terminated stream. No-op variants round-trip exactly. Native
boot/pause/Options renders confirm enlarged slot74 without label/panel corruption.
Changed IDs50 (boot prompt),74 (Options). Other languages remain unsupported.

Seven LE u32 price words at ARM9 source0x120340 + row*32 +28 change to
50/100/150/150/200/250/350. All other engine bytes, purchase events, prerequisites,
levels and black/shared rows are retained. Engine hash
`da50ad8a0f249ad95461fe63157c61957bb6bfa6b5c1361a7bdef6d107d3e86e`.
Known profile tasm-v0.1.0 composes the authored Rush parent plus this price patch.
Build logs/publication metadata include the displayed version; the release registry
rejects different ROM bytes under the same published number. Historical generators
refuse this newer composition instead of discarding its versioned text.

Sources: tools/qol_suits_menu.py, tools/release_info.py, tools/playtest.py; evidence
in work/version-research and build/boot-tests/Versioned-e1b66ebd. Pricing refinements
are user-authorized; exact game payload/checksum remains opaque and unchanged by
release tooling. Native refunds intentionally use the new lower table price.

Native emulator proof: disposable 2,000-XP fixture buys Rush for 150 XP, retains
1,850 XP/bit16 through the game's save and reload. Separate copied checkpoint
buys then refunds Rush: 267 -> 417 XP and bit16 clears. Title, pause and Options
captures visually verify both labels. Deterministic regeneration equals the
published ROM; only the two locale resources and seven price words differ from
the prior stable release. All 3,736 resource IDs/other bytes survive. The latest
real 634-byte DSV (512-byte opaque game payload) is unchanged; snapshot and wrapper
verified at publication. Research saves remain private copies.

The existing bounded text composer also accepts offset-grown variants, retaining
the version slots when future move instructions are composed. Ordinary old-size
generation retains its earlier hash-pinned output. Compatibility tests cover
both routes; new release generators must explicitly accept the current recipe.
All 139 source tests pass against the published composition; 36 archived notes
verify by CRC, size and SHA256. Logs: work/version-research/final-tests.log.

## Both Suits price table and independent purchases (v0.1.1)

Shared table runtime 0x02120260/source 0x120260: seven 32-byte records, +28 price,
all single-level. Native order/bit/old->new XP:
Launching Uppercut 6/50->25; Enemy Kick-Off 12/200->50; Drill Kick 7/400->100;
Jackhammer Stomp 8/600->150; Air Dodge 10/200->50; Enhanced Dodge 9/800->200;
Quick Recovery 11/800->150. These bits are not allocated in numerical row order.
All seven have native 382 required/dependent sentinels. Adjacent Red begins 0x120340.
No price/header/ownership field is inferred from labels; exact original records
are matched to reference/original_gameplay.json and guarded authored-parent ARM9.

New engine hash 322fbd7bd597f91f875957f65eadc6fcb7611480c64e76db6a14a0ef736ed6f6.
The delta from v0.1.0 is confined to the seven shared price words. Inverse edits
reproduce its entire engine exactly. Red discounts, all other engine bytes and
purchase record fields survive. Original asset IDs/bindings/clips are unchanged;
only English/American version slots 50/74 are composed to v0.1.1.

Native copied-battery tests clear only shared bits/set 5,000 XP in disposable RAM,
then use actual menu confirmations. Per-row XP/flag observations match all seven
prices; buy total 725 vs native 3,050 control. Real native save/reload retains
4,275 XP/all seven owned bits; individual refunds return 5,000/clear all seven;
refunded save/reload confirms it. Nonshared flags remain unchanged. The fixture
is not a save editor and never writes the source battery. The latest real DSV
wrapper/payload/snapshot match exactly before/after stable publication.

tools/release_info.py owns per-profile price/hash/date/version data so historical
recipes rebuild under their original number; later balance values cannot replace
a published profile's prices. Build metadata selects the recipe's own version.
Evidence: work/shared-economy; replays build/boot-tests/Versioned-bcc6974a.
All 141 source tests pass against the published files, including the historical
v0.1.0 reconstruction. Log: work/shared-economy/full-tests.log.

These findings prove the existing shared purchase routes only. Additional rows,
scroll/menu limits, spare persistent flags, save checksums and migration remain
unproved. Event query/setter support 309..381 is not evidence that any unassigned
looking bit is safe. The 26-tool catalog requires separately qualified ownership
and crowd controller work; no new targeting/evasion/crowd mechanics are claimed.

## Player state machine and Red kit hooks (v0.2.0)

Updated 2026-10-05. Clean-ARM9 addresses; confirmed by disassembly plus paired
emulator traces (work/kit/trace.py, training room, copied save, disposable RAM).
Source/hooks: `tools/tasm_kit.{py,s}`; clips `tools/kit_{choreography,clips}.py`.

### Transitions, states and inputs

`SpideyStateMachine` (vtable `0x021352A4`; derived vtable `+0xA8` think
`0x020AA3D4`) runs every update from `0x020776BC`: update `+0xA4`, think, apply.
Normal think `0x020B4888` picks one transition list (default `0x021346FC`, air
`0x0213478C`, plus `0x021346B4/0x02134590/0x02134560` by condition) and
`0x020B4A7C` evaluates its pointer-to-member entries in order; the first result
other than `0x7FFFFFFF` wins and `0x020CD1B0` applies it. Returning the current
state means "stay"; controller byte `+4` = 1 forces a re-enter of the same state.
Controller: `+0x08` updates in state, `+0x14` state, `+0x18` previous, `+0x28`
input-command queue, `+0x44` actor, `+0x54` target interface (actor+4),
`+0x64` flags (`0x8000` Scissor repeat; `0x40` set while dodging), `+0x80`
string node, `+0x8C` evade lock, `+0x90` node keep-alive timer, `+0x93` repeat
count. Queue commands (`0x020CFF0C` peek / `0x020CFC34` consume): 1 attack (Y),
2 jump (B), 3 evade (R), 4 object (X). Ability query: actor vtable `+0x184`
(bit) / `[[actor+0xE8]] & (1<<bit)`. Form: actor+0x34 = 1 Black.
REG_KEYINPUT `0x04000130` gives held D-pad/R on ARM9 (X/Y are ARM7-only).

| State | Meaning (observed) | State | Meaning |
|---:|---|---:|---|
| 0/1/4/5/6 | idle, walk, skid, duck, run | 15/19/24 | jump, fall, land |
| 30/31/51 | Snare aim, zip, follow-up / air attack | 37/38 | grapple shoot/hold |
| 40 | Web Launch (Vault) | 42/43 | web-kick pull / kick |
| 46 | ground string | 47 | Y+back turn attack |
| 52/53/54/57 | air dodge, dodge, Enhanced chain, roll | 63 | player hurt |

Blockers: `0x020B52F8` (states 43..49) returns stay unless actor+0x28 = 1
(animation cancel window) or, for 46, the node is cancelable; `0x020B7AA4` does
the same for the air attack. Evade `0x020B5774` (generic path `0x020B5C28`):
lock, then R → roll 57 (Down/running), Enhanced 54, air 55/52 or dodge 53.
Y transition `0x020B6968` returns 47 for Y+back. Web-kick pull → kick switches
at `0x020B6574` when the target is within `[0x021341F4+0x58]`.

### Ground string nodes

Node table `0x0211BB70 + 16*node`: {action, next, pause-next, flags(+9 cancel)}.
Red: 11 Snap(56) → 12(57) → 13(58) → 14(59); pause branch 11 → 15(61) → 16(60)
→ 17(62); node 16 repeats with Scissor. Black uses 5..10. String update
`0x020C32D8` refreshes `+0x90`=10 every update, so the node survives 10 updates
after leaving 46; entering 46 with a live node advances via `0x020C2F94`
(alt branch if bit16 Red / bit23 Black and enough pause). Scissor limit
`6+2*tier` (`0x020B5434`); `0x020B5464` is reached only on the Red bit-17 path.

### Actions, resources and actors

Action request `0x020728F0` (motion+0x258); commit `0x02070428` looks up the
action record (`0x02001F44` → stack {SCA, NSBTA, ?, GMB, GAB, valid}) then sets
SCA/GMB/GAB. Repeats of the same action skip the lookup unless motion+0x2FC bit1
is set. Player actions: 1-4 air string, 5 back attack, 6 back handspring, 29 zip,
45/46 grapple, 49/50 pull/kick, 51 launch, 56-62 string, 130 rapid stomp,
133 roll, 139 side-step dodge. Positions: motion+0x7C/+0x80 plus locals
+0x160/+0x164; a teleport must also update actor copies +0x148/+0x180/+0x210/
+0x2CC or physics stalls. Velocity actor+0x18/+0x1C (Q12). Common enemies:
`NormalEnemy` vtable `0x021301D0`, `EnemyStateMachine` `0x02133368`; attack
state 15 (actions 55/63 seen). Training dummy flag 4 does not gate its AI.

### Kit extension contract

The kit is appended after the HUD/flow image: code at `0x02152C20`, route table
`+0x1F00` (12-byte {action, kind, resource}), state `0x02154C20` (copied zeros),
reserve 16 -> 24 KiB, Glob count 3736 + 6. Hooks are listed in `HOOKS`; Sling's
contact site is restored to native. The enemy registry (12 slots, refreshed from
the per-actor observer `0x02073A68`) is trusted for two ticks, so despawned
actors are never dereferenced. Heap headroom after the larger reserve is not yet
measured in dense scenes.

### Kit animation authoring

`kit_choreography.Clip` channels are keyed per sample: root (pelvis position),
yaw/pitch/roll (full flips/spins; pitch + = forward), spine, head, chest-relative
hand targets, pelvis-relative foot targets (or `plant_*` world ankles), knee/elbow
poles and `point_*` toes. Body frame: X = Spidey's left, Y up, Z forward; the side
camera shows Y/Z, so flips about X read best. Catmull-Rom curves keep velocity
continuous. The player rejected per-key-eased clips (Rush) as "dancing": avoid
holds at every key, use anticipation, overlap and follow-through. A clip must
match its source action's sample count (2 emulator frames per sample) and place
impacts on the native contact clocks. Workflow: edit `kit_clips.py` →
`python tools/kit_lab.py preview CLIP 4,9` (stick figures, marked contact samples)
→ `python tools/tasm_kit.py` (candidate) → `kit_lab trace ... --cap` + `sheet
--box ... --scale 2` for in-game frames. Root height in a clip is visual only;
gameplay movement comes from GMB root motion or kit code.

## Research workflow and pitfalls (Red kit sessions)

Tools: `tools/kit_lab.py` (trace/arena/qualify/preview/sheet/disasm/xrefs/words/
patch); inputs `reference/combat-inputs/kit/`. Each emulator run happens in a
quiet child process; read `build/boot-tests/<rom>-<hash>/<label>/trace.txt` or
observations.json (state, action, node, facing, position, enemies).

- Training room is deterministic; the story arena (room left of the save) is not:
  spawns differ between runs. Use the dummy plus `--enemy-state F0:F1:15` to force
  an attack for Spider-Sense-style logic, then confirm once in the arena.
- Runtime RAM patches (`kit_lab patch` → `--patch`) need JIT disabled (the lab
  does this). Put a branch table at the start of patch code: Keystone cannot
  resolve labels from a source prefix.
- Kit code: never read a pointer without a null check (a crash shows as a black
  screen). ARM immediates must be encodable (use `ldr rX,=value`). Preserve flags
  when hooking mid-function (`mrs/msr`).
- A teleport must update motion+0x7C/+0x80 and actor copies +0x148/+0x180/+0x210/
  +0x2CC. Repeating the same action skips resource lookup unless motion+0x2FC
  bit1 is set (Spin Cycle uses this).
- Growing the Glob shifts everything by about one emulator frame; parity checks
  allow one constant phase (`kit_lab.same_behavior`).
- Strings: no `;` in the text Huffman table. Button glyphs: `` B, ``
  Y, `` A, `` X, `` R, `` L. Keep them as escapes in
  source (editors may write raw private-use characters).
- Kit change loop: edit `tools/tasm_kit.s` → `python tools/assemble_tasm_kit.py`
  → update `CODE_SHA256`/`ARM9_SHA256` in tasm_kit.py and the profile's
  `arm9_sha256` in release_info.py → bump VERSION/TEXT_EDITS for a new release
  (a published version never changes bytes) → `python tools/tasm_kit.py` →
  `python tools/kit_lab.py qualify build/version-X/Versioned.nds` → tests →
  copy candidate mods + gameplay_profile.json → `python tools/playtest.py build`.
  The kit source pins one code/ARM9 hash, so an older kit release profile is not
  rebuildable from newer source; its rollback is the retained ROM in
  `build/releases/<sha>/`.
