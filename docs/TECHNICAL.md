# ROM technical knowledge

Updated 2026-10-06. This is the single technical notebook. Search its headings and
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
The 0x1064-byte prefix is zero; at 0x1064 sit u32 tree size (4 + 4*nodes),
the tree, 1,049 offsets relative to 0x1064, then slots. The tree only codes
bytes the original text uses (no '7'). `StringSlots.grown` splits the least
used leaf into (leaf, new byte), re-encodes every slot and rebuilds the
offsets; the game reads the grown tree (v0.7.0 title shows "v0.7.0").
Use `decode_grown` for any variant.

Two hash-identified minimap sheets have coherent4bpp tiled previews and exact
round trips. DAT first two bytes fit those two dimension candidates; other DAT
fields/palette ownership are unknown. The mission palette's original red is
restored.153 UI families/142 CBMP files are inventoried. 4bpp CBMP screens
(all minimaps) are decoded and editable: "Minimap screens and area room lists".

All75 BSP envelopes parse losslessly: `BSP\0`, LE u32@4=7/@8=2 (meanings
unknown), @12=file length, @16=table end, bounded monotonic even offsets,
last table word01000000. Spatial/collision/node semantics remain hypotheses.
Paired OBJ starts u32=2; placements/triggers/encounters are hypothesized,
not decoded. Downtown_Save02/03 has a useful104-byte OBJ difference.65
MDAT/MGFX/MPAL scene groups are inventoried, unedited. SDAT is preserved as a
whole file; individual audio editing is untested. Archive section `BSP + paired OBJ`.

### Engine / saves / qualification

Source-language evidence: the ROM contains ARM9/ARM7 machine code, not source or
compiler metadata. The state-machine and actor dispatch use vtable-like layouts
and virtual calls (see "Player state machine and Red kit hooks"), strong evidence
that the original gameplay engine is C++-style, but not proof of the exact source
language, compiler, or whether some modules were C/assembly. Our Red kit logic is
ARM-state assembly in `tools/tasm_kit.s`, placed in the ARM9; `tools/tasm_kit.py`
and the other Python tools build/patch the ROM and bake animation resources,
they do not run on the DS. `tools/assemble_tasm_kit.py` is optional reassembly;
normal builds use the pinned `tools/tasm_kit.hex`. Confidence: likely C++ for at
least the native object-oriented engine; exact language/toolchain unknown.

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

Updated 2026-10-06. Combat measurements below strengthen the case for testing
DeSmuME JIT first, then renderer settings. The clearest visual upgrade is higher internal
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
Neither combined preview was launched or accepted in the 2026-10-04 investigation.
The later JIT-only player trial uses the normal shortcut (see the crowd section).
The launcher itself does not edit INI files, but
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

### Crowd combat performance (v0.5.0, 2026-10-06)

**Player report:** large rooms with many enemies and long combos slow the whole
scene, like slow motion; not just a brief pause on each impact. Investigation
used the unchanged published v0.5.0 ROM (`fd7e4420...`), copied research saves and
disposable melonDS DS 1.1.5 instances. No player ROM, save or emulator settings
were changed. This is research, not a published FPS fix.

Reusable tool: `tools/combat_benchmark.py`; optional `_run(timing=True,
core_options=...)` in `kit_lab.py`. Workers fresh-boot serially, alternate mode
order across two rounds, and use seeded Y/R/held-R/web/jump inputs for 1,800
combat frames after the existing training/story entry scripts. All seven Red
slots and shared dodge prerequisites are enabled only in disposable RAM. Story
actors/player refill in RAM so combat can continue. The solo scene removes the
sparring placements through `kit_lab.solo_rom`; the sparring scene keeps all four
enemies. Source ROM/save hashes are checked, and captures were inspected.

Host times measure `retro_run` including its video callback, excluding RAM
exports, Python observers and PNG generation. **These are not Nintendo DS FPS or
DeSmuME measurements.** JIT uses this core's default 32-instruction blocks with
fast-memory disabled; the proposed DeSmuME trial explicitly uses block size 12.
The player's emulator was initially open and closed during the first series;
other host workload, scheduling and differing AI trajectories limit precision.
Do not compare absolute times across the two campaigns or multiply their gains.

First campaign: two runs/mode/scene, seeds 600/601. Numbers are medians of the two
run means/p95s, in ms per emulator call:

| Scene | Interpreter mean / p95 | JIT mean / p95 | Lower mean host cost |
|---|---:|---:|---:|
| Solo idle | 5.927 / 7.666 | 4.659 / 6.789 | 21.4% |
| Four-enemy sparring combos | 8.378 / 12.679 | 6.060 / 9.381 | 27.7% |
| Sewer story combos | 11.692 / 20.399 | 8.882 / 15.787 | 24.0% |

The story comparison is weaker: median live common-enemy actor counts varied
4/7 (interpreter) versus 5/5 (JIT), and the count includes small state-6 objects.
It is not a fixed-density comparison. The enclosed sparring scene retained four
live enemies in every mode and is the stronger control.

Second campaign: enclosed sparring only, seeds 630/631, JIT in both modes.
Serial software rendering: mean 5.498 ms, p95 7.814; threaded software rendering:
mean 4.256, p95 5.354. Mean host cost fell 22.6%, supporting a renderer trial after
JIT. It does not establish DeSmuME renderer performance or exact framebuffer/AI
parity; the reviewed frames were coherent with all four enemies present.

**Cadence:** the kit tick at `0x02154C20` counts Spidey updates, not rendered
frames. In the second round of the first campaign and all accepted renderer
runs, the HUD callback counter at `0x0215242C` stayed 29.98-30.02 updates per 60
emulated frames, with at most one intervening frame without an update. Player
updates were about 28-29.5 during combat, with gaps up to 11 frames while the HUD
kept updating: consistent with per-actor impact pauses, not evidence of a global
FPS drop. This strengthens the host-processing lead but does not identify every
large-room/boss bottleneck. Native update/render regional timing remains unmapped.

**Rejected comparison:** story renderer seed 620 crossed through a room exit.
The HUD counter reset; the benchmark guard rejected it. Its apparent low cost
must not be counted as a renderer improvement. Raw evidence/log remains at
`build/boot-tests/Spider-Man-WoS-modded-fd7e4420/perf-arena-combo-jit-threaded-620/`
and `work/performance/perf-arena-combo-jit-threaded-620.log`. Keep both tick series
before deriving cadence so failed trials remain diagnosable. Reject counter
resets, room changes and empty-room comparisons instead of reporting speedups.

Evidence: `work/performance/crowds-2026-10-06.json`,
`crowds-renderer-training-2026-10-06.json` and `crowds-summary-2026-10-06.json`;
each accepted run links its captures, observations, timing and tick arrays.
Repeat with `python tools/combat_benchmark.py build/Spider-Man-WoS-modded.nds
--scenes sparring-combo --modes interpreter,jit --rounds 2 --seed 640` (one line).
Use enclosed sparring for renderer comparisons; random story movement can exit
the encounter. Runtime code patches remain prohibited with JIT enabled.

**Before the player trial:** the configured DeSmuME INI had Renderer=2, no
CPUmode/JitSize setting, and its observed launch command had no JIT override.
Release 0.9.13 defaults CPUmode to false and JitSize to 12 (startup inference,
not a live CPU-settings-panel reading):
[release initialization](https://github.com/TASEmulators/desmume/blob/release_0_9_13/desmume/src/frontend/windows/main.cpp#L1954).
Added `playtest.py launch --preset jit-preview` (only `--jit-enable --jit-size 12`)
so the agent can isolate CPU execution after the player saves/closes, using the
stable filename, latest battery validation/checkpoint and normal Continue flow.
`Play Spider-Man.cmd` selects `jit-preview`, now retained after the player
confirmed improved performance. Ordinary launches use JIT12. ROM preloading is a separate later test; existing
`performance-preview` combines it with JIT. Renderer trials
must retain 1x resolution and check effects/UI before an HD trial. No enemy cap,
effect reduction, timing relaxation or speculative kit rewrite is supported by
these measurements.

Player authorized and the agent launched the JIT12-only trial on 2026-10-06.
The live DeSmuME process command was verified with `--jit-enable --jit-size 12`
and the unchanged stable v0.5.0 ROM. Latest real DSV: 634 bytes, SHA256
`9162423b6acac15768213f3e74ea8915c9866bf0106e1d350fe2490f0a9a2ca1`;
wrapper parsed and full bytes matched the verified `before-jit-test-dsv-<sha>`
snapshot before launch. DeSmuME was closed for the checkpoint. Its original INI
was backed up by content hash (`94b4844a...`) under
`work/performance/emulator-settings/`. Trial record:
`work/performance/jit-player-trial-2026-10-06.json`. Startup/arguments verified;
the player confirmed overall performance was better, with occasional moments
that "weren't bad" (2026-10-06). This is subjective DeSmuME acceptance, not a
measured FPS gain or separate confirmation of every gameplay/save path. The player
asked whether a normal launch would use JIT, so the shortcut was set to this
trial preset. Its prior bytes are preserved in
`work/performance/launcher-before-jit.cmd`; reverting the trial removes only
`--preset jit-preview` from its launch line. No renderer/resolution/preloading/
timing flags added, and no ROM or save changes for the shortcut update.

Next isolated comparison is `playtest.py launch --preset renderer-preview`:
same accepted JIT12, AUTOGL, internal resolution explicitly 1x, no ROM preload.
Player authorized this comparison and the crowd backend on 2026-10-06. The
trial was launched and its live arguments verified; the saved renderer changed
2 -> 1. Performance/visual verdict pending. Current accepted INI, JIT-only
launcher and latest battery `5ec452a1...` were preserved while closed. Record:
`work/performance/renderer-player-trial-2026-10-06.json`. The normal shortcut now
selects `renderer-preview` during the trial. Preserve this baseline for rollback:
renderer CLI overrides can persist. Compare the same crowded fight and check
web transparency, shadows, fog, HUD and audio. Do not infer DeSmuME OpenGL gains
from the melonDS threaded-software result. Retain JIT12 if reverting a renderer
trial; the pre-JIT launcher baseline is historical, not the accepted default.
Only afterward isolate ROM preloading (disk-read hitches, not a proven CPU/FPS
fix) and time native enemy/contact/animation regions if sustained dips remain.

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
| OBJ | Placements; trigger/event graphs mostly unknown | 75 pairs; bounded Test_Combat01 character section decoded | Training Brute placements/count/spacing via training_room.py | High for one guarded training resource; general OBJ/trigger editing unproved |
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
| Performance/graphics | Host emulation/rendering/resolution | INI/source inference, idle/crowd benchmarks, texture census | JIT12 normal launcher; optional 1x renderer/preload/HD trials | Player-confirmed JIT improvement with mild remaining dips; renderer/HD and measured DeSmuME FPS unproved |

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
Y transition `0x020B6968` returns 47 for Y+back. The evade exits consume the
queued command whose type is in r2 (`0x020B5DA4`: dodge 53 expects r2 = 3, R);
v0.2.0-v0.4.0 entered it with r2 = 1 and ate a queued Y instead of the R. Web-kick pull → kick switches
at `0x020B6574` when the target is within `[0x021341F4+0x58]`.

### Ground string nodes

Node table `0x0211BB70 + 16*node`: {action, next, pause-next, flags(+9 cancel)}.
Red: 11 Snap(56) → 12(57) → 13(58) → 14(59); pause branch 11 → 15(61) → 16(60)
→ 17(62); node 16 repeats with Scissor. Black uses 5..10. String update
`0x020C32D8` refreshes `+0x90`=10 every update, so the node survives 10 updates
after leaving 46; entering 46 with a live node advances via `0x020C2F94`
(alt branch if bit16 Red / bit23 Black and enough pause). Scissor limit
`6+2*tier` (`0x020B5434`); `0x020B5464` is reached only on the Red bit-17 path.
Repeats are decided near the end of each loop in the state-46 blocker: a queued
Y (`0x020B54E0`) is fetched and its direction word (+4) read twice
(`0x020B5508`, `0x020B5538`): 2 (up/down) rejects; 0 and 4 repeat only when
forward (actor vfunc `+0xD0` facing test), so Y+back rejects; others accept at
`0x020B5560` (consume, set +0x64 bit 15, stay 46). A rejected Y then reaches the
Y transition, which re-enters 46 and advances 16 -> 17 (the sweep). v0.2.1 hooks
`0x020B5508` to jump to the accept path during an owned spin.

### Actions, resources and actors

Action request `0x020728F0` (motion+0x258); commit `0x02070428` looks up the
action record (`0x02001F44` → stack {SCA, NSBTA, ?, GMB, GAB, valid}) then sets
SCA/GMB/GAB. Repeats of the same action skip the lookup unless motion+0x2FC bit1
is set. Player actions: 1-4 air string, 5 back attack, 6 back handspring, 29 zip,
45/46 grapple, 49/50 pull/kick, 51 launch, 56-62 string, 130 rapid stomp,
133 roll, 139 side-step dodge. Positions: motion+0x7C/+0x80 plus locals
+0x160/+0x164, and three motion probes (x, y + own offset: feet/body points)
at motion+0x44, +0x10C, +0x1C8 (2026-10-06, RAM dumps in training and arena).
**Spidey's actor allocation is only 0xF4 bytes** (heap header magic 0x00035544,
size word at header+4); the "actor copies +0x148/+0x180/+0x210/+0x2CC" used by
v0.2.0-v0.4.0 were false: they lie past that block (motion sits at actor+0xE10
in training, +0x20B4 in the sewer arena) and writing them corrupted the heap
(see "Freeze root cause" below). Motion+0x180 is facing. Velocity actor
+0x18/+0x1C (Q12, units per update, applied the same update when written after
the controller update; ground state 43 ignores vertical velocity, state 51
applies both). Walls clamp velocity motion; overlapping bodies push apart
softly (about 0.5 unit per update), so a fast dash passes through an enemy.
Common enemies:
`NormalEnemy` vtable `0x021301D0`, `EnemyStateMachine` `0x02133368`; attack
state 15 (actions 55/63 seen). Training dummy flag 4 does not gate its AI.
Sewer symbiote attacks (v0.3.0 research, 17 player-hurt events over three
1,500-frame idle arena runs, `sense_research*`): melee state 15 with action 63
lands from ~8 units and action 55 lunges 10 -> 5 units; **state 16 action 71 is
a ranged attack**: the enemy enters it 9-25 units away, backs off, and Spidey is
hit ~20 frames later with no enemy near. State 24 action 41 was seen once near a
hit (unconfirmed). States 0/1/2 idle/move; a small state-6 action-40 object
(HP ~4000) floats around the room.
Air string chaining: controller+0x64 bits 0xC00 are set when an air contact
hits and cleared at the contact clock when it misses; a buffered Y only chains
into the next air attack with them set (a whiffed pound ends the chain).
While riding (state 51) native A and B do nothing; a queued B fires the native
air web-swing (states 26-28) as soon as state 51 ends unless consumed
(`0x020CFC34`, type 2). Action request is just `motion+0x258 = action`
(`0x020728F0`), committed later; set motion+0x2FC bit 1 to force the lookup.

### Hit pipeline (v0.4.0, runtime-probed)

Every actor has an interface sub-object at actor+8 whose vtable slot +0x40 is
ReceiveHit (thunk, e.g. `0x0204BFC8`: this-8 -> `0x02074AC8`, which forwards to
the victim controller's vtable +0x54; enemy `0x02094658` picks the reaction from
0x24-byte attack records at `0x0211A600`/`0x02119E20`/`0x0211ADE0` by kind).
The contact dispatcher `0x020784A4` resolves the victim from a handle and calls
it at `0x02078628` (`blx r4`): r0=&result, r1=victim+8, r2=&attacker actor,
r3=&info (by value on the caller stack), [sp]=0x1000. Result 4 = taken, 1 =
ignored (native protection predicate; see the backend fixtures below). Info: +0 attack kind, +4 strength (Q12),
+8 3, +0xC -> extent record, +0x10 -> contact record {attacker part,3, victim
part, 5, 0, kind, attacker part, strength}, then values. Spidey kinds seen:
string 0x04 (0xC00/0x800), Snap 0x05 (0xC00, observed 2026-10-06), air 1-3 0x14 (0x1000), Skyjack finisher 0x16
(0x1800), stomp 0x15 (0xC00), heavy kick 0x1F (0x1000), web kick 0x20, grapple
0x21/0x22, launch 0x25/0x26. Replaying a captured info later works from any
distance (24 units tested), also with the victim-part pointer cleared: same
damage and reaction. Kind 0x16 on a standing enemy gives a stagger (37); 0x1F
gives a knockdown (41 -> 48 -> 49). The kit hooks `0x02078628` (entry +0x30) to
copy Spidey's latest hit (state +0x36C..+0x3FF) and replays it with
`kit_replay_hit`. A lab replay patch that captured *every* hit stalled the
training Skyjack at the grapple; the kit's version (range-checked) did not.
Guard frames (v0.4.1): the hook writes result 1 and skips the victim's
ReceiveHit; the dispatcher then treats the hit as ignored (native path for
get-up states). The Spider-Sense dash uses this for Spidey for 7 updates.

### Shared crowd-hit backend candidates

Player approved shared crowd targeting/hit work and explicitly authorized
concurrent copied-save checks while testing OpenGL (2026-10-06). Workers use
below-normal priority and one logical CPU each (6/7); live player settings and
affinity are untouched. Prototype source: `tools/crowd_hits.s`; staging/qualification
tool: `tools/crowd_backend.py`. The published source/hex and player ROM remain
unchanged. Staging reproduces the published 6804-byte kit exactly before making
one isolated own-code RAM patch. Both candidates pass the existing literal and
absolute native-branch validators and fit before the route table at +0x1F00.

- **Area replay:** `work/kit/crowd-backend/area-fc29a872/`, 7008 bytes. Replaces
  Skyjack's duplicated scan with `kit_area_hit(x,y,xReach,yReach,skip,maxAge)`.
  It scans the existing 12 registry slots, keeps the two-tick freshness/range
  filters and primary-victim exclusion, rejects empty/stale/non-Spidey captures,
  then delegates each candidate to the existing pointer-checked native replay.
  Preserves Skyjack's 8-by-6-unit reach, kind/strength, ownership gate and debug
  telemetry. Returns replay attempts, sum of native result codes and last
  attempted actor; these are not HP damage or confirmed hit counts. No allocation,
  new save fields or movement writes. Multi-target/contact deduplication for
  future Spin Cycle/Leapfrog callers still needs empirical design/qualification.
- **Skyjack drift:** `work/kit/crowd-backend/sky-velocity-d0a84d97/`, 6796 bytes.
  Audit found that `sky_player` still directly adds its bounded horizontal drift
  (at most 1 unit/update) to motion+0x7C. The earlier claim that *all* kit movement
  was velocity-only was too broad. This separate candidate stores the same
  clamped correction in actor+0x18 for native physics/collision to apply. It is a
  movement-contract correction, not a measured performance improvement.

**Validation:** area and velocity candidates independently passed all 31 existing
kit checks. Composition `combined-1f874330` is 7000 bytes and passed 31/31 too;
paired Skyjack open/wall/cancel passed 9/9. Assembly/source reproduction,
literals/native branches/code space and staging guards passed. These use copied
research saves, disposable RAM and JIT-disabled runtime code patches. Concurrent
checks require explicit `--allow-player-session`; `--cpu-core N` sets the worker
and children to a single Windows logical CPU at below-normal priority.
Final identity/count record: `work/kit/crowd-backend/validation.json` (20 Python
tests passed, three 31/31 qualifications, targeted 19/19 + 6/6 + 9/9). Stable
ROM hash remains `fd7e4420...`; FPS gains and player feel are untested. Staging
records reload retained validation reports so restaging cannot silently relabel
a passed candidate as pending.
Patched qualification requires its own trace prefix/report; it cannot overwrite
the published `work/kit/evidence.json` or patch the native-parity parent control.
The current 31 checks mostly use one dummy; `tools/crowd_area_lab.py` supplements
them with 14 real-actor/API fixtures and 19 assertions, all passed. Native replay
and area replay of the same Snap capture (kind 5, strength 3072 Q12) each remove
4096 Q12 actual HP and produce state 37/action 82. Multi-target replay removes
4096 from each of two separated Brutes (2 attempts, native result sum 8), leaving
the primary victim excluded. Empty/stale/non-Spidey captures, stale registry,
negative reach and exclusion/range controls skip replay; invalid actor/motion
pointers return 0 without damage. Reviewed captures are coherent. Report:
`area-fc29a872/area-coverage.json`; per-case reports link captures/traces.

**Immunity fixture correction:** forcing enemy state 48 did not prevent a hit;
it must not be treated as blanket immunity. Disassembly of ReceiveHit
`0x02094658` and its predicate `0x0209EC9C` finds protected states 25, 33..36,
53, and state 51 while controller+8 <= 1 (other ReceiveHit bypasses can apply).
Setting state 51/clock 0 immediately before replay makes both native and area
return 1 with zero HP loss. Fixtures mutate only disposable RAM. These checks
prove bounded replay behavior, not new Spin/Leapfrog contacts, player feel or a
performance gain. No backend candidate is published yet.

Integrated Skyjack landing in `combined-1f874330/bowling-coverage.json`: 6/6
checks passed. Native and combined callers each replay twice, remove 4096 Q12
HP from each bystander, and produce state 41/action 84 after native reaction
commit. Captured telemetry delta 2050 = 2 attempts + 8 * 256 native-result sum.
RAM fixture moves two idle bystanders beside an already spiked native target;
the third stays distant. Read reactions four frames after dispatch, since the
controller commits the queued state on a later update; immediate state snapshots
can differ with actor update order. General area/API guards remain isolated above.

Paired open Skyjack chains remove 21504 Q12 HP in each mode. R+Left at frame 91
enters air evade at frame 93 in each, preserves 11264 Q12 HP loss, moves left and
eventually clears the Skyjack latch. Do not require an immediate latch reset:
air Reflex retains it to resume the combo. A 6-unit launch gap makes the unchanged
Web Vault overshoot and whiff; use the established ~21-unit gap. A target placed
at the wall failed to enter Snare/Vault in both controls, so bounds alone there
cannot qualify Skyjack drift. The active-wall fixture instead relocates an
established native juggle at frame 60 in disposable RAM (Spidey x=236, target
x=235, heights preserved). Its behind-target correction aims right into the wall.
Published direct drift reaches x=991232 (242 units), beyond the native player
wall limit 968577 (~236.5); the velocity candidate stops at exactly 968577.
The fixture passed and captures were inspected (candidate remains visible beside
the enemy; the control drifts beyond the room boundary). This is a reproduced
movement/collision fix, not a speedup. Both wall runs still have an active juggle
at frame 219; this check establishes bounds, not completed recovery or player feel.

### Kit extension contract

The kit is appended after the HUD/flow image: code at `0x02152C20`, route table
`+0x1F00` (12-byte {action, kind, resource}), state `0x02154C20` (copied zeros),
reserve 16 -> 24 KiB, Glob count 3736 + 7 (v0.3.0). Hooks are listed in `HOOKS`; Sling's
contact site is restored to native. The enemy registry (12 slots, refreshed from
the per-actor observer `0x02073A68`) is trusted for two ticks, and since v0.4.1
`kit_alive` also checks the vtable and motion/controller pointers before any
dereference (`kit_fresh` includes it). State offsets in use: 0 tick, 4/0x10/0x368 Reflex,
8/0x14 spin, 0x20-0xDF registry, 0x2F0-0x2F8 training room (v0.5.0), 0x300-0x30C Perch, 0x310-0x320 Leapfrog,
0x330-0x33C Skyjack, 0x340-0x34C Sense (side, dash/guard counter, attacker,
target x), 0x350-0x35C Perch flip/hop, 0x360/0x364 held/new
keys (edge-detected once per Spidey update), 0x36C-0x3FF hit capture (0x374
bowl telemetry: count + 256 * result, 0x378 last bowled actor). The 1 KiB after KIT_STATE+0x400 up to
the arena is unused (lab phantom lives there).
Heap headroom (v0.3.0, empirical): `OS_GetInitArenaLo` (`0x020FF2E8`, case 0)
returns the patched literal `0x020FF374`; the main arena is now 0x02155420 ..
0x023E0000 (2.54 MiB; the original started at 0x0214F420, so HUD + kit cost
24 KiB). The game does not use an SDK OSHeapInfo layout. In zero-initialised
emulator RAM, 332 of 651 arena pages were never written in the sewer arena at
frame 200 and 324 after a 25 s combo fight (largest untouched runs 748/724 KiB),
so the reserve is small next to the observed headroom. Caveats: zero pages can be
allocated-but-unwritten; bosses/other levels are unmeasured.

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

### Freeze root cause and crash hunting (v0.4.1)

Player report (2026-10-06, v0.4.0): in a crowd, spamming Y and R with Both Suits
Enhanced Dodge held, the game "froze and won't unfreeze"; separately a
Spider-Sense flip clipped Spidey down into an unreachable part of the map.

- **Cause 1, heap corruption (the freeze).** The Sense teleport (v0.2.0-v0.4.0)
  stored Spidey's new x at actor +0x148/+0x180/+0x210/+0x2CC, past his 0xF4-byte
  actor block, into neighbouring heap blocks. Sewer arena crash (fuzz seed 303):
  the global list/node pool at `0x021459E0` (allocator `0x0201DCCC` pops the
  free list at pool+8; list insert `0x0201DBFC`, remove `0x0201DB98`) handed out
  node `0x022A7394` = actor+0x210 whose link held 0xFFFF13C2 = -60478, exactly
  the x of a Sense teleport 380 frames earlier (actor+0x148/+0x180/+0x2CC still
  held it); the insert wrote through it: data abort at `0x0201DC0C`.
- **Cause 2, stale registry pointer.** The Sense scan read [[enemy+0x30]+0x1F8]
  with a null check only; an entry's motion pointer was 0x60000 (freed/reused or
  corrupted actor): data abort at kit `0x02153E54` (seed 504). Fixed by `kit_alive`.
- **Clip.** Every position write ignores collision; the teleport landed 3 units
  past the attacker even inside walls. v0.4.1 kit code writes velocity only.
- A frozen DS screen here is a data abort: CPU mode 0x17, PC 0xFFFF0108 (BIOS
  exception vector, the game installs no handler), SP_abt 0. The interrupted
  SP/LR are banked R_ABT; the main stack is in DTCM (`0x027E3xxx`). A halted CPU
  at `0x020FFA30` (sys mode) is the normal idle wait of a menu/tutorial/pause.
- Lab: the dummy placement and every lab teleport had the same bug (writes past
  the actor); placing the training dummy crashed in the GAB event player
  `0x0200305C` (object +0xC). Fixed with `kit_lab.teleport` (motion probes).
- `tools/crash_hunt.py` reproduces fights (random Y strings, R taps, held R,
  A/B/X, crowd refilled to max HP, ledge start (55000, 376880)), saves state +
  RAM when the kit tick stops outside the tutorial, and decodes melonDS states
  (`ARM9` section: cycles, halted, R0-R15, CPSR, banked FIQ/SVC/ABT/IRQ; the
  DTCM is the last 16 KiB of `CP15`). Evidence (4,000-frame fights, same setup):
  v0.4.0 froze in 4 of about 90 fights with the old lab; with the fixed lab a
  heap-link check flagged fresh corruption in 9 of 48 v0.4.0 fights (mostly
  frames 90-210, right after the first Sense) and 2 crashed (pool abort at
  `0x0201DC0C`/`0x0201DCE8`; in seed 727 the per-frame free-list watch caught
  node actor+0x210 receiving 0xFFFF1406, a Sense x, 100 frames before the
  crash). v0.4.1: 0 corruption, 0 crashes in 48.

### Training room (Test Upgrades, v0.5.0)

- **Room.** Test Upgrades loads `Test_Combat01` (native lookup index 70;
  descriptor at `0x02130DA4`: name pointer, Glob indices 0x805/0x803/0x806 =
  textures/BSP/OBJ, then 1, 1). Earlier notes incorrectly started its descriptor
  four bytes early: 0x51F at `0x02130DA0` is the preceding room's minimap
  resource, not a room ID. `Upgrade_Test` (lookup index 73, Spiderman + "Enemy
  Brute") is a different, unused-here room. Spidey starts at x 120 units
  (491520, the OBJ's Spiderman record); walls about 3.5/236.5 units.
- **OBJ layout (Test_Combat01_app.obj, 2140 bytes, partly decoded).** u32 2,
  u32 end of object records (0x4C8), u32 name-block offset (0x4E0); a 24-byte
  room header at 0x0C (unknown); three object records {u16 size, 01 01, u32 0,
  five u16 section end offsets relative to +0x14, sections}. Object 3 (0x47C)
  is the dummy: characters section {u16 size = 8 + 24n, u8 8, u8 n, n bytes
  0x18, pad to 4} then 24-byte records {x, y, z (Q12), u32 2, u32 angle
  (0x4000 faces right, 0xC000 left), u16 0, u16 character type}; the dummy is
  type 50, the black-suited Brute (Upgrade_Test's "Enemy Brute" is also 50),
  followed by an event-graph section (bytes unknown). After the records come
  one 8-byte entry per object and the name blocks {u32 size, u16 0x14, 7
  cumulative u16 counts per name category (characters first), 32-byte
  space-padded names}; names look editor-only, the editor keeps them matched.
  Object 1 holds Spiderman, an event graph (music/level/timer names) and
  "Enemy Spawn Points"/"SpawnPoint 0" sections (not decoded, apparently unused
  by Test Upgrades). `tools/training_room.py` appends up to three copies of
  the dummy record (lossless round trip with none).
- **AI.** The first placement (native dummy) stays in state 0 action 99
  forever; extra placements of the same record spawn with full Brute AI:
  walk (state 1, action 158), states 2/8, attacks state 15 (actions 55/63),
  4096 Q12 damage per hit to Spidey (6 units = 24576 max in the research
  save: six hits kill). Not every Brute attacks at once (the far two often
  hold back until the near one is busy). Enemy flag actor+0x88 bit 4 (value 4)
  is the native training-target flag: clearing it does not wake the dummy
  and setting it on the Brutes does not change their AI (paired 900-frame
  runs, identical). Its passivity source is unknown (placement order or
  Test Upgrades code). Bit 4 was found on no other enemy in every RAM dump in
  build/boot-tests (story enemies: 0, 1, 3 seen). Native training HP is 4096.
- **Player health.** Spidey HP is stats `[actor+0xE4]+0x84`, max `+0x88`
  (Q12). Damage `0x0205F3F0` only does HP = max(HP - damage, 0) and stores
  it at `0x0205F420`; death is decided later from HP 0. Kit tick: about 30
  Spidey updates per second (148 per 295 frames).
- **Kit training logic** (`train_observe`/`train_update`/`h_train_floor`,
  state +0x2F0 sightings, +0x2F4 active, +0x2F8 heal timer). Active = a bit-4
  enemy passed the observer since the previous Spidey update. While active:
  every common-health enemy gets bit 4 (the native setter clamps a lethal hit
  to 40), native max 4096 becomes 32768 (8 units), HP 1..40 refills to max;
  Spidey heals to max every 900 updates or while SELECT+Down is held; the HP
  store hook keeps him at 1 Q12 instead of 0. Evidence (work/training/*.json,
  scratch `work/training/probe.py`): idle 3000 frames, healed at the 900th
  update, lethal hits leave HP 1 with no death or tutorial; three 4000-frame
  random fights: no stalls, all four enemies alive (9-12 defeat refills
  each), SELECT+Down healed him; sewer arena 1500 frames: never active, no
  enemy got bit 4. Lab: training traces/qualification use a solo-dummy copy
  (`kit_lab.solo_rom`, build/lab-solo/); `trace --sparring` keeps the Brutes
  and native HP.

## Midnight Line room authoring and persistence

Authorized 2026-10-06: optional eerie five-room first station, original Signal
Leech, environmental puzzle/refuge, persistent milestones, Conductor teaser.
Spec: `reference/midnight_line.json`. Production build: "Midnight Line chapter
build (v0.6.0)" below; earlier subsections are the research that led to it.
Tools read clean originals or isolated candidates; real batteries/ROM stay intact.

### Native doors, spawns and game variables

Confirmed on all 75 clean rooms (`tools/room_doors.py`, `tests/test_room_doors.py`)
and in the emulator (2026-10-07):

- **Exit event.** Opcode `0x12` (handler `0x02039A4C`) calls `0x020D6B88`
  with operand bytes (room u8, OBJ record selector, spawn id, 0). Every
  record-0 group k>=1 of a story room is one exit. Story rooms use selector
  1; Downtown_Map01/12 and Sewer_Map07 have a third record (selector 2).
- **Trigger entity.** Type 7, 28 bytes: i32 x/y/z (Q12), u32 7, u32 0 or -1,
  u16 box w/h at +20/+22, u16 0x0A, u8 mode at +26 (2 on every exit), u8 at
  +27 = event group + 1 (same record). Player-collide triggers fire any group.
  Sewer_Save02's left exit (centre x=-18, w=16) fired as Spidey reached
  x=-7.3; box/centre semantics are inferred, not decoded.
- **Spawn table.** OBJ header +13 = spawn count, u16 +14 = 20 x count, records
  at +16: i32 x/y/z, u16 angle (0x4000 faces right, 0xC000 left), unknown
  +14..+17, u8 id at +18, unknown +19. Names are the record-0 name block's
  slots after the last category. A door names the *arrival* spawn beside the
  destination's door back. Spawn 0 without a table entry is the room's default
  Spidey placement (5 native exits). Side-door arrivals auto-walk ~12 units in;
  overhead arrivals drop. Sampled position is ~5 units above the spawn origin.
- **Inter-record table** after the records is `08000000 00000000` in all 156
  records; nothing in the envelope stores absolute offsets, so appending
  spawns/entities/groups only moves the +4/+8 boundaries.
- **Record header** byte +2 = action-group (entity batch) count, +3 =
  event-group count. Conditional `0x1D`: u16 var, u16 frames, op at +4 (0 ==,
  1 !=, 2 <, 3 <=, 4 >, 5 >=, unsigned), value +5; then-action +6..+9, else
  +10..+13 (layout in "Room scripting and the power puzzle"; the older
  "groups at +6..+9" reading was wrong). `0x26` set (u16 var, u8 value), `0x25` increment,
  `0x24` decrement, `0x15` message/VO, `0x19` music, `0x1B` Spidey binding
  (1-based entity).
- **Game variables** (`0x020D22AC` get, `0x020D24D8` set): ids 0..0x122 are
  bit flags at stats+0x1C (saved); 0x123..0x126 bytes at stats+0x48 (0x123 =
  mission counter: entering Sewer_Map01 at 8 sets 9, Sewer_Map03 at 9 sets 10;
  0x125 enemy difficulty); 0x127..0x130 per-room bytes; 0x135+ are ability/
  purchase bits (stats+0xC). Room r's init sets visited flag 0xB0+r.
- **Unused flags.** 245..282 are never set in 62 backed-up save slots
  (up to 44 visited rooms); 251..275 have no event reference, no constant
  get/set in ARM9 and no room-table entry. The chapter uses 252..275 (below).
- **Room-count guards.** 22 `cmp #75` sites: most are action ids or list
  terminators (keep). Two guard the current room: saved-block validation
  `0x02085720` (room >= 75 rejects the save; Continue stays on the title) and
  room reload `0x020D64B8` (room >= 75 takes the fallback path).
- **Death.** HP 0 opens the native touch-screen health-orb minigame, then
  resumes in the same room with little health ("Failure!" path verified in
  room 76). The reload path behind `0x020D64B8` was not exercised.

### Room-object and BSP framing

`tools/room_objects.py` parses all 75 paired OBJ envelopes: u32 version 2;
record-area end/name-block start at +4/+8; u8 record count +12; first record
at 16+u16(+14). Records have a 20-byte prefix, u16 total size and five cumulative
u16 section ends at +8 (relative to payload +20). Their meanings remain unknown.
An 8-byte-per-record opaque table precedes one name block per record: u32 size,
20-byte prefix, seven cumulative u16 name-category ends at +6, then 32-byte
slots. Some slots follow all seven categories; retain them, do not truncate to
the last category count. 156 records parsed; all no-op section repacks exact.
This is not a general entity/event compiler; adding entities needs name and event
reference qualification separately.

`tools/room_entities.py` frames section 0 as consecutive batches: u16 batch size,
u8 header size, u8 record count, one u8 length per record padded to four bytes,
then records. All 586 batches across 156 objects round-trip exactly; concatenated
record counts equal each name block's first category end. The bounded named
24-byte character edit changes only XYZ. Tail kind words remain unknown outside
the empirically tested training type 50; high words in other placements must not
be presented as simple character IDs.

`tools/room_collision.py` adds framing to the BSP envelope (node and tree
meaning: "Room collision tree" below): between table_end
and first listed region lie 12-byte nodes {i32 unknown_word0, u32 unknown_word1,
u16 unknown2, u16 unknown3}. Every listed region is u16 count followed by count
{u16 node_index, u16 unknown} entries. All 75 reconstruct exactly: 8,789 nodes,
5,503 lists. Do not assume every node is axis aligned; many word1 values differ
from the test-room 0x40000000..06 patterns.

Controlled training edit: node 1 word0 983041 (240*4096+1) -> 737281
(180*4096+1). Native right bound changes 968577 -> 722817, exactly 60 Q12 units;
frames reviewed, visible native geometry unchanged. Only this boundary's
coordinate interpretation is empirical; arbitrary geometry/tree generation is
not qualified. Evidence: `work/midnight-line/collision-{stage,control,candidate}.json`.

### Native room lookup and namespace probes

`tools/room_catalog.py`: lookup `0x02084AB4` reads an index then a descriptor
pointer from `0x021321F4` (75 entries). Each descriptor starts at its NAME pointer,
not four bytes earlier: texture/BSP/OBJ indices +4/+8/+12; model-array pointer
+0x20; minimap CBMP resource +0x4C; other fields remain unknown. Test_Combat01
index 70 / descriptor 0x02130DA4; Sewer_Map07 index 57. Preceding 0x51F is the
previous descriptor's minimap, not a room ID. All names/resource associations
validate against the original archive. Survey: `work/midnight-line/room-survey.json`.

`tools/room_extension.py` builds a disposable lookup at KIT_STATE+0x400,
preserving original entries and sentinel 75; clones occupy indices 76..80.
They fit the existing unused 1 KiB reservation. The lab changes the lookup
literal and Test Upgrades entry only in disposable RAM (JIT disabled), never
the player ROM. Clone index 76 loaded with Spidey and native room rendering;
frames reviewed (`room-registration.json`). This is not a production loader.
Native save validation still rejects room indices >=75; exits and expanded-room
saves remain unqualified. Do not globally replace every compare-to-75 instruction.

`tools/model_geometry.py` parses bounded single-model/single-block NSBMD shape
streams and appends authored GPU quads while preserving material/rig/SBC/old
payload bytes. Format source: https://github.com/scurest/nsbmd_docs . A station
shell uses original debug materials, authored background/columns/bench/sign
geometry and an edited boundary. Camera looks from positive Z: placing the back
wall on positive Z occludes Spidey; move it/decorations to negative Z. Frames
reviewed with visible Spidey and new geometry. These are development materials,
not finished station art.

`midnight_line.py stage-platform` appends four zz_ml resources plus a two-byte
alignment resource. The v0.5.0 archive ends at offset mod4=2: unaligned appended
native-copy model/texture controls black-screen; the aligned control renders.
Keep padding in its own unreferenced resource, not opaque asset tails. Every
original resource except the generated filename table remains exact; IDs stable.
Default staging retains native Test_Combat01 OBJ and actors (not a finished
chapter). Candidate `edf0521b...` passes six room/continued-update/movement/
capture/return checks; pause-menu return loads native room 64 and save options.
Evidence: `platform-probe-edf0521b-mode2.json`, per-hash staging JSON and frames
in build/boot-tests; native source ROM unchanged. Runtime lookup patches remain
disposable, not stored in that candidate ROM. Staging/probe commands cannot be
substituted for playtest publication or a production loader.

### OBJ event commands and initialization repair

2026-10-06 follow-up resolves the earlier empty-room initialization gate.
The native entry argument at `0x020ED7DC` is an **OBJ record selector**, not a
generic gameplay mode. Loader `0x02031710` builds two runtime banks: record 0
in bank 0, selected record in bank 1 (argument 0 omits bank 1). Constructor
`0x020D285C` initializes bank 0, then bank 1 if the selector is positive.
Thus Test Upgrades selector 2 needs the third record; two-record challenge/save
OBJ transplants crash in lookup `0x020360BC` because record 2 does not exist.
Changing a record's unknown header word cannot repair this missing selection.

`tools/room_events.py` frames section 1 with record byte +3 event-group count:
u16 operand offsets, then one {u8 command count, opcode bytes} header per group,
word-alignment padding, and operands. Native width table `0x02119CCC` has 39
entries; dispatcher `0x0203B400` uses 12-byte records at `0x021199F8`.
All 75 rooms / 156 records / 1,424 groups / 2,830 commands reconstruct exactly;
native nonzero padding is preserved. Most opcode meanings remain unknown.
Evidence: `work/midnight-line/event-framing-survey.json`; tests verify the native
width table, all section/name counts, bounds and byte-exact round trips.

Training record 2 EG_INIT contains opcodes {0x15, 0x0D, 0x0D}. Both 0x0D
operands (`00010001`, `00010201`) refer to entity 1 in **their own runtime bank**,
not the base Spidey. Handler `0x02039640` derives the bank from event context;
the command selects an entity and changes motion flags / a virtual property.
Deleting the entities/names while retaining either reference reaches the
`0x7FFF` invalid-entity sentinel and aborts at `0x0200177C`. Removing only the
last command still crashes (`5b1a8915`); remove both. Opcode 0x15 writes the
native message/tutorial selection (41 here) and has no entity reference.

`midnight_line.py stage-platform --empty-dummy --repair-empty-init` retains
the base records, empty secondary bank and opcode 0x15 while removing both
deleted-dummy references. Authored shell `9407c67f` passes **7/7**: room 76,
player, continued updates, right/left input response, native jump, rendering,
and pause-menu return to native room 64. Enemy registry is empty; frames reviewed.
Earlier equivalent scratch candidate `0da8575d` passed the older 6-check harness.
Evidence: `platform-probe-9407c67f-mode2.json` and its boot-test trace/frames.
This remains an isolated development shell with debug materials/native tutorial,
not the chapter or a published loader. Existing uncorrected omission probes
remain intentional failing controls.

Independent normal-context path: challenge OBJ selects record 1, where Spidey
and its 0x1B target-binding command live. Selector 1 alone renders/falls but
does not respond to input. Test Upgrades also sets stats+0x7A at `0x020ED7B8`;
changing the preceding `mov r1,#1` at `0x020ED7AC` to `mov r1,#0` in disposable
RAM restores right/left movement, native jump and continued kit updates with
no enemies (`8e2c2f18`). The flag also selects training-only pause text/actions
(`0x020EF3D0`, `0x020EF4AC`), so the training Return action is unavailable.
Use `probe-room --authored --mode 1 --story-context` for this distinct path;
a production chapter needs its own native transitions. Evidence and xrefs:
`work/midnight-line/test-context-xrefs.json`, `normal-entry-native-exit.json`.
Do not infer expanded-room save validation from playable entry.

Normal-context transition fixture passes **8/8**: empty room 76, horizontal
input, native jump, no enemies, rendered captures, queued exit to room 64,
continued updates there and unchanged candidate ROM. Native API `0x020D6B88`
takes `r0=[0x02145C90+8]`, `r1=&destination_room`, `r2=OBJ record selector`,
`r3=spawn selector`; its wrapper forwards to `0x020D6500` and queues a scene
transition. The fixture calls it once after 180 relative lab frames with
destination 64 / record 1 / spawn 0. This proves the native transition path,
not an authored doorway trigger or a persisted chapter checkpoint. The temporary
ARM stub fits at `0x02155334` after the extended lookup; production must allocate
and verify its own loader rather than treat this RAM fixture as a shipped hook.
The 40 native flag bytes at stats+0x1C..+0x43 match before/after that exit;
this is progression parity for the transition fixture, not a persistence audit.

The probe now requires horizontal response in both scripted direction windows
and native jump state 15; gravity-only position changes are not input success.
The kit tick is cumulative across the copied-save entry/menu/rooms, not a
relative frame counter. Schedule one-shot experiments through the lab's frame
hook rather than assuming tick 180 means frame 180. All patches remain in
disposable RAM; original/stable ROMs and real batteries are untouched.

### Candidate persistent flag padding (superseded)

Superseded 2026-10-07 by native flags 252..275 ("Native doors, spawns and game
variables"): they are addressable by native event opcodes and saved by the
native flag copy, so no custom codec or kit code is needed. The padding-bit
codec below is kept as research only; do not ship it.

Native stats allocation is 0x98 bytes (0x020D6CF4); common saved block 0x58 bytes
(read 0x0208608C, write view 0x02085FC4). Flags occupy stats+0x1C..+0x43 (40
bytes); logical flag query/set checks bound 0x123 (291). Constructor clears all
40 bytes. Native save copies all 40 (0x020D67CC..F4). Upper padding in the final
word (stats+0x40, bits 3..31) is therefore a candidate, not an assigned allocation.
Variable IDs >=291 can address other scalar fields; they are not extra flags.

Paired copied-save experiment injects 0x004D4C38 at stats+0x40 in disposable RAM.
Native saved battery differs from control only at three marker bytes and four
checksum bytes. Fresh boot restores marker and retains original logical flags.
All 165 signature-bearing slots sampled from existing backup DSVs have zero
upper padding. Sources stay byte-identical. Captures reviewed; checksums are
still opaque (not zlib CRC32/Adler32). Evidence: save-{control,fixture,reload}.json.

`tools/midnight_progress.py` provides a provisional versioned encoding in bits
291..311, preserving native low bits and other unallocated bits; unknown occupied
data/version is rejected. The actual codec's schema-1 completed state
0x004D4C78 passed the same native write/fresh-boot test; all three milestones
decode true, no unrelated native flags changed (`save-verification.json`, 4/4).
This is not an editor or published runtime hook.
Audit all native reads/writes, reset/copy/refund paths and composed save/reload
before assigning storage or clearing the persistence publication gate.

Source validation at that point: 199/199 on 2026-10-06. Current status (215/215,
release v0.6.0) is in "Midnight Line chapter build (v0.6.0)".

### Midnight Line chapter build (v0.6.0, layout v0.6.1)

`tools/midnight_chapter.py` (`apply_rom`; tests `tests/test_midnight_chapter.py`)
is the final verified stage of `mod.create_build` for profiles with
`'chapter': True` (`tasm-v0.6.x`). It requires the pinned kit ARM9 and clean
native sources, and proves every other resource byte-identical. `ARM9_SHA256`
pins the current release only (v0.6.0's chapter bytes are not rebuildable
from current code). Dev candidate: `python tools/midnight_chapter.py` (from the
kept v0.5.0 ROM in `build/releases/fd7e4420.../`, output `build/midnight-line/`).

- **Rooms 76..80** (75 stays the native invalid sentinel), v0.6.1: 76
  ML_Entry <- Sewer_Map01 (arrival), 77 ML_Refuge <- Sewer_Save04 (save sphere
  in record 0), 78 ML_Station <- Sewer_Map02 (timetable), 79 ML_Stairs <-
  Sewer_Map13, 80 ML_Platform <- Sewer_Map03 (tracks, parked train). v0.6.0
  used Platform/Refuge(Save03)/Service/Switching/Gallery for 76..80. Models, BSP, texture animation and minimaps are shared native
  indices; each room appends `zz_<room>_app.obj` and a palette-graded
  `zz_<room>Textures.nsbtx` (cold "midnight" grade; amber "emergency" in the
  Refuge; only palette bytes change). `zz_ml_alignment.bin` keeps appends
  word-aligned.
- **Room table.** Kit autoload grows from 0x5C00 to 0x7000 (v0.6.x: 0x6800):
  the kit's unused reserve tail (zeros) plus a 0x1000 chapter block at
  `0x02155420` holding the lookup (native 0..74, 0, chapter 76..89), one
  descriptor per room cloned from its source (name, texture, OBJ, model-array
  pointer changed), model arrays, names and (v0.7.0) the relocated Sewer
  area room list. Arena lower moves to `0x02156420` (4 KiB less heap).
  Descriptors +0x28..+0x48 are zero in ROM and filled at boot for native rooms
  only: area id (Pier 0, Residential 1, Sewer 2, Downtown 3, Hive 4), map piece
  position, size and room bounds. Unfilled (zero) chapter descriptors showed an
  empty "Pier" map; v0.6.1 pre-fills the sources' runtime values
  (`MAP_FIELDS`), so the Sewer map appears. The map only draws (and highlights)
  rooms from a list not yet found, so chapter pieces/position are not drawn;
  a different position was tried and ignored. Area table: static init at
  `0x02117F74` writes RAM `0x0213B834` (16-byte rows: map CBMP, unlock var).
  `0x02137xxx` byte lists ending below 0x49 are per-mission *ability* unlock
  lists (`0x020D1334`, bitset `0x0205721C`), not room lists.
  Patches: lookup literal `0x02084AC8`, Glob count `0x020077F8`, and both
  current-room guards `cmp r1,#75` -> `#81`.
- **Sanitized clones.** Record 0 keeps Spidey, exits, camera and ambience;
  exits are retargeted by `LINKS`; messages and writes to mission scalars are
  dropped (reads kept: they only gate the dropped groups); upgrade orbs move
  4000 units below the floor. Record 1 is either the empty Test_Surfaces01
  state record plus the visited flag (Platform, Refuge) or the source's
  encounter record with flags remapped (v0.6.1: Station ambush 0x42 -> 268;
  Platform 0x27/0x62/0x11c -> 269/270/271, so its boiler/ambush logic starts
  fresh and a crowd incl. red suits fights on the train roof; native story
  state blocks Spidey at the train instead). Entry's mini-boss/silhouette stay
  dormant outside their story beat. Spawner byte +22 is an area enemy-table id
  (Sewer 0x0D..0x0F); strength also follows global difficulty 0x125.
- **Links (v0.6.1).** Door kind (`room_doors.door_kind`): trigger offset from
  its nearest spawn; agrees with >=95% of native pairs. Every link joins
  opposite kinds (left/right, up/down), checked by tests. Native pairs reused:
  Entry up<->Station down, Station right<->Platform left, Stairs left<->Refuge
  right; also Entry up<->Platform floor grate, Platform left alcove<->Stairs
  right, Platform top trapdoor<->Stairs floor. v0.6.0 joined mismatched kinds
  (player: trapdoors came out of side doors).
- **Entrance.** Sewer_Save02 gains trigger (61, 4) size 12x24 -> ML_Entry
  spawn 3 (its left door), return spawn id 2 at (44, 2) facing left, and
  (v0.6.1) a copy of its native record-1 "Door (empty)" doorway at x=54 (grey
  door behind the desk). Native exit, entities and events otherwise unchanged.
  It fired at x=51.9 when walking right.
- **Flags (v0.6.x plan, superseded).** Since v0.7.0 252..265 are the visited
  flags of rooms 76..89 (Discovered = 252); locals come from 268..275, 266,
  267, 251..245 in first-use order (build report `local_flags`), with
  269 = track power cut (v0.8.0 shared flag) and 246 = completed.

v0.6.1 release `c3010cba`: tour 14/14, Refuge save/Continue, ambush seeds 11
(ambush completed, flag 268, exit works) and 12, kit 31/31, crash hunt 12/12
(`work/kit/v0.6.1/`), native Save02 exit unchanged. v0.6.0 evidence follows.
Agent-tested on release `36aa52f8` and dev candidate `a023350e` (same chapter
bytes): `midnight_line.py tour` rides all 14 directed links once
(lab warp into Sewer_Save02, teleport onto each trigger): correct rooms,
arrivals at the expected spawns, five visited flags and no other chapter flag.
`midnight_line.py save-test`: saving at the Refuge sphere (X, Save, Yes) and
Continue from a fresh boot restores room 77 with flag 253; control
`chapter-control.nds` without the guard patch leaves Continue on the title.
Native-vs-clone walk: Switching spawns 4 thugs exactly like Sewer_Map13.
`ambush` (crash-hunt fight inputs, Red kit owned, Spidey kept alive, enemy
HP capped at 1): Service exits work after fights (seeds 11, 12; seed 13
inconclusive because teleports do not take while Spidey stands on the station
stairs); flag 268 is written when "Unblock Doors" runs (not every run, natively
too); the native Sewer_Map02 control behaves the same. Death at HP 0 runs the
health-orb minigame and resumes in room 76. Release `36aa52f8`: kit
qualification 31/31, crash hunt 12/12 (`work/kit/v0.6.0/`), native
Sewer_Save02 left exit still reaches Sewer_Map07 record 2, title v0.6.0.
Evidence: `work/midnight-line/chapter-{build,tour,save}*.json`, frames under
`build/boot-tests/chapter-*`. Rollback caveat: a save made inside the chapter
is rejected by any ROM without the guard patch (battery bytes stay intact).

### Minimap screens and area room lists (v0.7.0)

Confirmed 2026-10-07 (`tools/minimap_cbmp.py`, tests; in-game captures).

- **CBMP 4bpp screens** (98 of 142 files, every minimap; `*_8`/HUD/BlackBG UI
  screens use another layout): u16 121, u16 tile count, 256 BGR555 colours
  (16 palettes), u16 width/height in tiles (32x24 = the whole touch screen,
  frame included), width*height NDS text-BG entries, u32 body length, a
  Griptonite 0x60 PuCrunch body *without* its 4-byte type/size word (params,
  RLE table, bitstream; `grip_compression.decode` after prefixing
  `0x60 | tiles*32 << 8`), 2 trailing bytes. All 98 round-trip; a re-encoded
  body (`encode_backrefs`) loads in game (Sewer screen 6150 -> 7694 bytes).
- **Area rows** at `0x0213B840` (ARM9 data, 16 bytes per area 0..4): screen
  resource, map variable, room-list pointer, entry count. Sewer row 2: list
  `0x0211FE38`, 18 entries. Static init `0x02117F74` writes screen/var only.
- **Room-list entry** (20 bytes): u32 room, u32 OBJ record selector, u8 type
  (0 room, 1 save room), u8 first/last palette index of the room's 5-colour
  slot, u8 x4 colour sources `B6 BA BB BF` in every entry, u8 x/y map pixel
  (mission markers, `0x020E1A5C`), 3 zero bytes. Code (`0x020E1858`,
  `0x020E19A4`) tests visited flag 0xB0+room (room <= 114) and copies the
  visited (`0xB6..0xBA`), hidden or current-room colours into the slot; the
  slot's first colour is the background and never changes. Room shapes are
  pixels of those slot colours in the area screen itself.
- **Free slots in MMSewer.cbmp:** palettes 1..3 (magenta fill), `0xAB`,
  palette 0 beyond colour 0, palette 13. Palette 11 holds the colour sources;
  4/5 colours 1..11 are the S icons. Using palettes 0/1..3/13 showed no
  other touch-screen change in captures.
- **Descriptor +0x28..+0x48** (area, piece position, world size, bounds) feed
  the room-detail view (`0x020E56F8`, with descriptor +0x4C screen) when the
  area's map variable is owned (`0x020E361C`). The chapter sets area 2 and
  keeps the source room's other values.
- **Chapter diagram:** 14 rooms drawn as a subway diagram in the empty
  lower-left cells (cols 3..12, rows 15..18) of MMSewer.cbmp, one free slot
  per room; list relocated to the chapter block with 18 + 14 entries
  (patches row +8/+0xC). Visited chapter rooms appear, the current one is
  highlighted (frames: `build/boot-tests/nest-c-*/ml-visit-*`).

### The Nest and the boss room (v0.7.0)

- **Cross-area clones work.** Warping into native Hive/Pier rooms with a
  Sewer-era save spawns their own enemy types; cloned Hive rooms keep their
  symbiote crowds (HP 80k..107k at difficulty 11 vs ~45k sewer red suits).
  Area-specific enemy assets load per room; the descriptor's area id can be 2.
- **Event semantics found:** `0x15` message operand +4 = 1-based event group
  that runs after the dialogue (dropping the message must keep that chain:
  the chapter turns it into a 0-frame `0x1C`); `0x1C` = u16 delay, +4 action
  group, +5 event group (1-based); `0x1F` was read as the "<ability>
  obtained!" grant (Downtown_Map14: Sledgehammer Slam) but is probably the
  reward jingle (see "Chapter routes on foot"); `0x07` spawns a
  pickup (+25 = story ability index, +26 = group run on pickup; the boss
  reward orb is a native collectible: "You found a Collectible!").
- **Per-room scratch bytes** 0x127..0x130 drive room logic such as the
  Venom room's platforms/timer; the chapter keeps their writes.
- **Downtown_Map14 boss**: Mini-Boss 06 (orange symbiote brute, HP 2,048,000
  at `0x022AD460`-style (hp,max) pairs, no NormalEnemy vtable). Its trigger
  needs flag 0xAA (Sewer_Map06 mini-boss beaten); the clone reads it as its
  own visited flag. Boss death runs the reward group directly (no grant,
  no collectible), setting the "completed" flag. "Exits work afterwards" was
  only checked by teleport in v0.7.0; on foot the arena was unreachable from
  the chapter's doors until v0.8.1 ("Chapter routes on foot").
- **Flags:** visited 252..265 (rooms 76..89), locals from 268..275, 266, 267,
  251..245 (first-use order; Station/Platform keep 268..271). Flags 138..165
  have no event/code reference and are unset in the player's save (mission
  28) but are not in the verified-free list; orb entities use ids 19..72.

### Content toolbox research (2026-10-07, after v0.7.0)

Lab-only (scripts `work/midnight-line/scratch/{msg_test,variant}.py`; dev ROMs `build/midnight-line/{msg,mix,timer}-*`; frames in
`build/boot-tests/*/{msg,mix,timer,dev}-*`; sheets in `work/midnight-line/`).
Dialogue and switch wiring shipped in v0.8.0 (sections below); the rest is
not shipped yet.

- **More flags.** Save slot = "SpidermanWoS" + 4-byte checksum + the 0x58
  block (flags at block +0x1C, mission byte +0x48). 21 distinct slots in
  `work/save-backups` and the player battery (missions up to 47, past the
  final boss's 41) never set 138..165 (nor 245..251, 257..267, 269..282
  outside the chapter). Flag writes only come from event opcodes and the
  shop's ability bits (`0x020F1B20`/`0x020F1BC8`, via `0x020D24D8`); no code
  constant targets 138..165. They are a safe 28-flag extension pool.
  Unreferenced low flags (21..49 etc.) overlap the orb id range 19..72: avoid.
- **Dialogue.** Opcode 0x15 operand: u16 display time (0 = default ~8 s;
  tutorial lines use 5), u8 message id, u8 alternate-lookup flag, u8
  continuation group. Message table `0x0211C214`: 196 entries x 44 bytes
  (u32 string index, u16 x2 voice ids or -1, 9 x u32 extra ids or 0x7FFFFFFF),
  reached only through accessor `0x020D0F64` (literal `0x020D0F84`). Two
  bounds `cmp r1,#0xC4` at `0x020DFCFC`/`0x020DFDD8` reject higher ids
  (blank touch screen). Recipe proven in game: copy the table with new
  entries into the chapter block, patch the literal, raise both bounds to
  0xFF (59 new ids 0xC4..0xFE), append strings. Strings: the 0x1064-byte zero
  prefix is 1049*4 (count literal `0x020069AC` = 0x419; loader `0x0200694C`,
  decoder `0x0200C4A8`); appended strings displayed with and without growing
  prefix+count; grow both in production. `StringSlots.grown(..., appended=)`,
  `slot_count`, `decode_grown` handle variants. Shown: "Midnight Line: the
  power is out. Find the breaker." on the touch-screen panel.
- **Enemy mixing.** Spawner byte +22 (area table) can be any area's: the
  Sewer Station clone spawned Hive symbiotes (0x05, ~90k HP) or Pier gang
  (0x08, ~50k HP). Tables: Downtown 1..3, Hive 4..6, Pier 7..9, Residential
  0xA..0xC/0x13, Sewer 0xD..0xF.
- **Puzzle objects.** Switch = Object (Switch) + Trigger (Button Press) (trigger
  +26 mode 0 = press, 2 = touch; +27 group). Sewer_Map04 switch: anim via 0x01
  on the switch entity, INC flag 0x27 (drains the sewer), read by Sewer_Map03
  ("ElecBoilerCheck") whose 11 Hazard_Electric floors are powered by a
  Liftable boiler (Lift_Object_Die INC 0x62). Opcode 0x0F toggles door/gate
  entity state (block/unblock, grate open/close). Cross-room puzzles need one
  chapter flag shared by several clones (the cloner maps flags per room today).
- **Timers.** Opcode 0x23 u8 N: on-screen countdown of N minutes (0 resets);
  TimerWatcher entity (type 11, 20 bytes) +16 = 1-based group run on timeout.
- **Debug rooms.** proto01 (74) is a textured prototype night pier/warehouse
  (rooftop y~88, floor y~5, x -207..7) with crates, ichor, liftables, an ichor
  switch and a normal switch (per-room bytes 0x127/0x128), pickup spawners and
  orbs that grant real abilities (lab run: "Tarantula Strength obtained!") and
  collectibles. Test_Challenge01/Collision01/Surfaces01/02 are grey or grid
  debug boxes. All load and play via the lab warp; no exits or spawn table
  (Spidey in record 1). To use one: copy an exit trigger template from another
  room (add_exit needs one in-room today), add spawns, hide orbs, drop 0x07/0x1F.
- **Room limit.** Room ids are bytes; the map code asserts 0xB0+room < 0x123
  (`0x020E15A8`, `0x020E187C`), so rooms above 114 must stay off the map list;
  otherwise only the two save/reload guards limit the count.

### Room scripting and the power puzzle (v0.8.0)

Confirmed 2026-10-08 from the handlers, all 156 native records
(`tools/room_script.py`, `tests/test_room_script.py`) and lab runs on dev ROMs
`build/midnight-line/pz-*` (frames `build/boot-tests/pz-*`, scripts
`work/midnight-line/scratch/{dump_room,lift_probe,puzzle_chain}.py`).

- **Action groups are entity batches.** Record header +2 = batch count; name
  category 2 names them (`<AG_INIT>`, `EnemySpawners`, `Switch`, ...),
  category 0 the entities in batch order, category 1 the event groups. AG 0
  is live from the start; an appended batch's entities (switch model, trigger)
  stay invisible/inert until activated (lab: no switch, no prompt).
- **Entity reference** = (AG 0-based, entity 1-based in that batch): all 419
  native `0x01` targets (one proto01 outlier) are then characters or objects.
  `0x01` = animate (AG, entity, anim, extra); the switch uses anim 0x19
  (throw) and 0x64 (thrown pose).
- **Action** (4 bytes; delay handler `0x02039DE0`, conditional `0x02039F3C`):
  activate one entity (AG 0-based, entity 1-based; calls `0x0203CAD4`),
  activate a whole AG (1-based; `0x0203CBE4`), run an EG (1-based;
  `0x0203C948`); 0 = none. Delay `0x1C` = u16 frames + action + 2 zero bytes;
  conditional `0x1D` = u16 var, u16 frames, op, value, then-action,
  else-action. A non-zero frames field queues the actions instead. An
  out-of-range entity in an action froze the room load (black screen).
  Natively only ops 0, 2, 4 occur (flags: `== 0`, `== 1`, `> 0`).
- **Native subway puzzle decoded.** Sewer_Map03 record 1 init: `0x27 == 0`
  -> activate AG `Electricity` (rail hazards); `0x62 == 0` (boiler intact)
  -> EG `ElecBoilerCheck` = `0x27 == 0` ? activate `Electric Boiler Object`
  + run `ElectricBoiler` : activate `Lift Object` (the liftable boiler);
  `0x62 == 0` -> `Lock_Grate` (`0x0F`, AG 0 entity 3 = the floor grate under
  the boiler). Destroying the thrown boiler runs `Lift_Object_Die`: INC 0x62,
  unlock that grate; X on the grate drops through it (its exit trigger).
  Sewer_Map04's lever (`Switch` + `Switch_Trigger` AGs, Button Press trigger
  mode 0 = X prompt) INCs 0x27; its init activates the trigger only while
  0x27 is clear, else the switch with its thrown pose.
- **v0.7.0 bug (lab, `c56095be`).** The Platform clone maps 0x27 -> 269,
  which nothing set: the boiler stayed electrified (HP 24576 -> 8192,
  knock-back, never lifted) and the grate locked, so the Nest was only
  reachable backwards through the Stairs grate (Gate, boss first).
- **Fix: shared flag + breaker.** `SHARED_FLAGS` seeds `('ML_Platform', 0x27)`
  -> `TRACK_POWER` 269 before allocation (other locals unchanged). The Stairs
  record 1 gains AG `Breaker` = copies of Sewer_Map04's Switch and Button
  Press trigger at x 211/215, y 87.5/84.5 (landing left of the trashcan, which
  X otherwise grabs at x 236), EGs `Breaker_Throw` (anim 0x19, SET 269, sound
  0xBC, message) and `Breaker_Thrown` (anim 0x64); init: activate the switch
  entity, then `269 == 0` ? activate the trigger : thrown pose (running the
  pose before activation, or via a flag test with op `!=`, showed nothing).
  `midnight_line.py puzzle --rom R` (release `d84ae539`): breaker sets 269,
  Platform has no shock, X lifts the boiler, throw sets 270, X on the grate
  enters room 81. Teleports only place Spidey; presses are real.
- **Tour vs ambush rooms.** The door tour teleports onto triggers without
  fighting; on `bc3aa3a1` the Gate's ambush sealed its ceiling exit before
  the teleport (timing shifts with any ROM change). Resume with
  `tour --start N` and check sealed exits with `visit ROOM --weak --leave X Y
  --frames 3600` (Gate: exit at x -20, y 218).

### Chapter dialogue (v0.8.0)

- **Message ids >= 0xC4** without copying the 196-entry table: the accessor
  `0x020D0F64` (`table + id * 44`, 8 instructions + literal) is rewritten in
  place: `cmp r1,#0xC4; ldrlo r3,=0x0211C214; ldrhs r3,=chapter-0xC4*44;
  mov r2,#0x2C; mla r2,r1,r2,r3; str r2,[r0]; bx lr` + two literals. Both
  bounds `cmp r1,#0xC4` (`0x020DFCFC` blt, `0x020DFDD8` bhs) rise to 0xC4 +
  line count. Native message 41 (training) renders identically. Entries live
  after the Sewer map list in the chapter block: u32 string, u16 voice x2 =
  0xFFFF, nine u32 0x7FFFFFFF (same as natives 0x0E/0x29; other natives use
  the nine ids for extra pages).
- **Strings.** Lines are appended slots (1049+) of both strings files via
  `StringSlots.grown(..., appended=)`. The 1049-word zero prefix is *not*
  grown: loader `0x0200694C` only uses count 0x419 to find the Huffman block
  (file + 0x419*4) and no other code reads the file holder `0x0213FE00`
  (literals at `0x02006948`/`9A8`/`9BC`/`9E8`); decoding indexes the offset
  table, which grows. This supersedes "grow both in production" above.
- **0x15 operand** as authored: u16 display frames (0 = native default),
  message id, lookup flag 0, continuation group 0. Shown on the touch-screen
  panel without pausing play (~8 s).
- **Lines (v0.8.0):** Platform entry while 269 is clear (`live_tracks`),
  breaker thrown (`breaker`), Refuge entry objective board: `269 == 0` ?
  `goal_power` : (`completed == 0` ? `goal_nest` : `goal_done`), completed =
  the Venom room's remapped reward flag (246).

### Room collision tree (2026-10-11)

Decoded from all 75 rooms and confirmed with Spidey in Hive_Map02
(`tools/room_collision.py`: `solid_at`, `floor_below`, `check_tree`, `map_png`;
`python tools/room_collision.py ROOM --out PNG` draws the z=0 slice with
entities; tests). This supersedes "node meanings unknown" above.

- **Node** (12 bytes): i32 word0 = plane distance (Q12) with two flags in bits
  0..1; u32 word1 = normal; u16 unknown; u16 link. Normal `0x4000000N`: axis
  N & 3 (x, y, z), negated when N & 4. Any other word1 is two s16 (Q12) holding
  the *negated* (x, y) normal of a slanted wall. Front = normal . p >= distance.
  Bits 2..3 of word0 are distance fraction, not flags.
- **Tree in preorder.** Flag 1: the front child is a solid leaf whose list
  index is `link`. Flag 2: the back child is empty space. A child that is
  neither is the next node; with two node children the front one follows and
  the back one is node `link`. Each list is the solid leaf of exactly one
  node in every room. List entries (node, 0/10/...) and the u16 at +8 remain
  unknown (probably the leaf's faces and surface types).
- **Measured against the game:** walls at x 0/-40 beside the Gate's pedestal
  (Spidey stops 3.5 units from a wall), pedestal top 180, wedge top 60 under a
  slanted plane, the ledge gap at x -9.5..-0.5. Sampled position = feet + 5.
- **Not in the tree:** doors, ichor gates/crystals, smashable floors and walls,
  liftables and blobs are objects with their own collision.
- **Hive shaft template** (Hive_Map02/04/06/07, 40 wide): neck 9 wide from 200
  up to the ceiling exit (trigger 218); chamber 160..198 with a pedestal
  (top 180, 20 wide); funnel floor at 160 with a 9-wide centre hole;
  platforms at 130 and 34 (centre +-10, an ichor blob on the lower one); a
  ledge at 96..100 with one 9-wide gap at a side wall; a wedge (top 62) under
  that gap; floor 0 with the door corridor. Hive_Map02/04 close the ledge gap
  with a red floor object.
- **9-wide pits and a 7-wide Spidey.** He only drops into such a pit (opened
  floor grate, removed red floor) within about a unit of its centre; walking
  or jumping across carries him over and he stands on the rim. Down drops
  him into an opened grate from the rim; X only opens the grate.
- **Movement seen in the lab:** B again in the air jumps again (three jumps
  reach a neck); holding a direction into a wall in the air clings (state 7),
  then Up crawls up and along the ceiling into a neck; B on a wall jumps off.

### Chapter routes on foot (v0.8.1)

Player 2026-10-11 (v0.8.0): dropped through the Stairs grate into the Gate and
was sealed between its ichor ceiling and a red floor "I don't have the power
up" for. Walking the chapter with real inputs found more of the same; v0.7.0
and v0.8.0 were never walkable past the Span.

- **Story abilities** are ability bits 0..5 (events 309..314, records at
  `0x0212018C..`): Ichor Crawl 0, Ichor Web 1, Tarantula Strength 2,
  Reinforced Web 3, Bulldozer Dash 4, Sledgehammer Slam 5. Each mini-boss
  reward pickup (`0x07` operand +25) names one: Sewer_Map06 0, Downtown_Map05
  1, Residential_Map08 2, Sewer_Map09 3, Pier_Map08 4, Downtown_Map14 5. The
  player's battery (mission 28, word `0x180FFFDF`) has 0..4: Sledgehammer Slam
  is the native reward of the boss the chapter clones and withholds. `0x1F`
  also runs in Test_Combat01's "Music Selection" groups, so it is probably the
  reward jingle, not the grant (unverified).
- **Object kinds** (type 14, byte +22; byte +23 = event group run when it is
  destroyed): `0x09` Floor_Smashable(Ichor) = red floor, Sledgehammer Slam
  only; `0x30` Wall_Smashable/Ichor Wall = red wall, Bulldozer Dash (black
  suit, A on the ground; walking into it with A tapped breaks it from either
  side); `0x0A`/`0x0B`/`0x10` ichor door/floor/wall crystals; `0x21`
  Smashable_IchorBlob (solid, sits on the low platform); `0x16..0x1A`
  liftables. Red floors are raised by the room init while their flag is clear
  (`IF flag == 0 ? AG[Hammer Object]`), so never activating them is the room's
  own "already smashed" state.
- **Red floors in the chapter:** Gate (y 95, the only gap), Hollow (same) and
  two in the boss room's exit alcoves. With the Nest run against the native
  direction (Hollow and Gate are climbed, the boss room is entered from an
  exit corridor) they closed the route in both directions.
- **Hive ambush.** The spawner (type 4) holds a zone box at +16/+18 (width,
  height in units around it; the heap object stores the half sizes), enemy
  table +22, and at +25 the group run when its wave is dead (`Door_Check`).
  `Door_Lock` (called by `AmbushINIT`, or by a trigger at the native entrance in
  Hive_Map02) locks the doors and raises ichor crystals; when the wave is dead
  the crystals crack (anim `0x1B`) and must be *hit* to open
  (`Ichor_Block_Die`: flag, unlock). Walking into a crystal never opens it.
- **Seal softlocks seen in the lab** (weak enemies, real doors): in the Throat
  the last fliers repositioned into the exit corridor behind the crystal
  (1,700 frames, never reachable); in the Gate the trigger at the top seals a
  chamber the ground wave never enters (it spawns below the ledge) and, coming
  from below, would seal after the wave is gone. An earlier lab warp showed a
  ground enemy standing in a door corridor behind a crystal in the Hollow.
- **Fixes** (`tools/midnight_chapter.py`): `open_hammer_floors` (every clone;
  3 rooms, 4 floors), `unseal` (Shaft, Throat, Span, Hollow, Gate: the one
  command calling `Door_Lock` is dropped; spawners, crystals' groups and all
  indices stay), `stage_boss`, `seal_grate`, `add_grate_hint`.
- **Boss arena** (Downtown_Map14): octagon x 30.5..149.5 with four pillars; each
  lower door corridor (y 20..32) rises through an alcove (red floor at y 40)
  to a wall opening (x 24.5..30.5 / 149.5..155.5, y 43..58) into the arena.
  Natively the ichor walls stand in those openings from room load (`Route 1`)
  and the fight starts by triggers near the top or a 450-frame timer: entering
  from a corridor, the timer sealed Spidey outside with the boss inside (lab).
  Now: walls rise in `Gate_Spawn`; `Gate_Spawn` is run by a new trigger box
  x 45..135 inside the arena; no timer. Lab: 500 frames in the corridor
  change nothing, walls rise behind him, the reward group dissolves them.
- **Stairs grate** locks (`0x0F`, like the native `Lock_Grate`) until the Gate's
  visited flag 264: the Nest is entered through the tracks, the boss cannot
  be skipped to, and the grate becomes a shortcut afterwards. A one-shot
  trigger on it shows the "sealed from below" line.
- **Sealed hatches are harmless:** Spidey crawls into the Entry's dead chimney
  and the pocket above the Platform's trapdoor and comes back down.
- **Why earlier checks passed.** The door tour and `visit --leave` teleport
  onto exit triggers, which fire behind locked doors and crystals; `visit`
  used spawn 0 (the native entrance side); a lab warp is not a door arrival
  (no walk-in, spawns can sit inside a trigger). Only real doors and real
  movement show whether a room can be crossed.
- **Walk harness** (`tools/midnight_walk.py`, tests): routes of steps driven
  from the frame hook with live inputs (`emulator_smoke.run(live_buttons=)`;
  a hook returning `'stop'` ends the run). Each route warps into one room and
  takes real doors from there; steps wait on conditions. Fixtures: enemies
  at 1 HP, enemies parked away during a traversal check, boss at 1 HP,
  Spidey's health refilled, ability word = the player's. Pitfalls: runs are
  not deterministic (fights); a placed Spidey keeps his stance (standing in
  the air, clinging to nothing) until a real jump; moving enemies onto him
  broke wave counting; suit form is stats +0x53 (0 red, 1 black). v0.8.1
  `f68a082e`: 5/5 routes, 67 checks, first try (`work/midnight-line/walk-*`).
- **Needs from the player's kit:** Bulldozer Dash for the Span's two red walls
  (owned). Whether Hive walls need Ichor Crawl/Web was not isolated (owned).

### The Yard: proto01 as a chapter room (v0.9.0)

- **proto01** (room 74, never linked natively): one model, own BSP and
  textures, `MMPlaceholder.cbmp`, runtime map fields all zero with area 5.
  OBJ: no spawn table, no exits; record 0 holds one ambient sound, record 1's
  only batch holds Spidey (`0x1B` binds entity 1 there) and 33 test entities.
  Collision: floor 0 for x -264..50, a step and slope up to a tunnel at the
  right end (x 135..174.5, floor 40, ceiling 64), a roof slab at 70..88 with
  liftables and two dead switches, ceiling 145: closed on every side.
- **Authored doors work without a native pair.** `room_doors.add_spawn` and
  `add_exit` take a `template` from another room (`spawns(...)[0]`,
  `exit_trigger(...)`); a room with selector 1 and Spidey in record 1 loads
  through a normal door. A touch trigger fires when Spidey's box (half width
  3.5) overlaps it: the box must reach at least a unit past where a wall
  stops him (first try ended exactly at the reachable 171.5 and never fired).
- **Cleaning** (`stage_yard`): five upgrade orbs (incl. LiftObjectLarge =
  Tarantula Strength) and the ability-pickup chain (`New Event 9..12`) are
  removed; object kinds `0x09`/`0x30` (red test floor and wall standing in the
  tunnel), `0x0C`/`0x0D` (ichor floor gates across the yard, with their two X
  prompts) and `0x11`/`0x13` (electric and fire hazards) are moved out of
  reach. proto01 never sets a visited flag: the clone's init does.
- **Enemies from another area in an appended batch.** A Pier_Map04 spawner
  (table `0x08`, plain) with its zone box set to 300 x 120 spawns the Pier
  gang in the yard (lab: up to three at once, on the floor).
- **Refuge door** (`add_yard_door`): exit box at the left wall, arrival spawn
  2, and Sewer_Map13's left sewer door entity in an appended batch that the
  init activates (visible as a grey door). Objective board and save sphere
  are unchanged; save/Continue in the Refuge still passes.
- **Flags.** Room 90's visited flag is 266. 266/267 belonged to the Span's
  seal flag and the Hollow's red-floor flag, which nothing writes since
  v0.8.1; those two locals now take 138/139 and every other allocation keeps
  its number (`LOCAL_FLAGS`; completed stays 246). 267 is free for room 91.
- **Map.** Slot `0x01` (palette 0, colours 1..5) is a 15th free slot; cells
  (12,16),(13,16) under the Refuge. Fields: Sewer_Save04's piece values and
  proto01's own bounds as (x min, y max, x max, y min).
- **Chapter lines stay up.** In the lab every chapter line (display time 0 or
  60) stayed on the touch screen until the room changed (1,200 frames
  checked in the Stairs and the Yard); the "~8 s" above was not re-measured.
- Lab `f109a525`: walk route `yard` (Refuge door, tunnel, floor, gang,
  back out, on to the Stairs) and the 32-link tour pass.

## Research workflow and pitfalls (Red kit sessions)

Tools: `tools/kit_lab.py` (trace/arena/qualify/preview/sheet/disasm/xrefs/words/
patch; training `--at X` starts at an absolute x, `--place` then puts the dummy
relative to him; walls at about 3.5 and 236.5 units) and `tools/crash_hunt.py`
(freeze/crash fights, see "Freeze root cause"); inputs `reference/combat-inputs/kit/`. Each emulator run happens in a
quiet child process; read `build/boot-tests/<rom>-<hash>/<label>/trace.txt` or
observations.json (state, action, node, facing, position, enemies).

- `trace --near U` starts Spidey U units left of the training dummy (all position
  copies). Native string hits home in to about 5 units; spin contacts land at
  5.4-6 units when facing the dummy and never when facing away. Dummy HP drops
  2048 per spin contact; `kit_lab.spin_hits` counts drops.
- Training room is deterministic; the story arena (room left of the save) is not:
  spawns differ between runs. Use the dummy plus `--enemy-state F0:F1:15` to force
  an attack for Spider-Sense-style logic, then confirm once in the arena.
- Runtime RAM patches (`kit_lab patch` → `--patch`) need JIT disabled (the lab
  does this). Put a branch table at the start of patch code: Keystone cannot
  resolve labels from a source prefix.
- Kit code: never read a pointer without a null check (a crash shows as a black
  screen). ARM immediates must be encodable (use `ldr rX,=value`). Preserve flags
  when hooking mid-function (`mrs/msr`).
- Keystone pitfalls (v0.2.1): a literal more than 4 KiB before the end pool is
  silently wrapped (Reflex read a code word as the state pointer and hung); a
  mid-file `.ltorg` mis-resolves every later absolute branch to native code by the
  pool offset (black screen on room load); plain `.word` data mid-file is safe.
  Since v0.3.0 the kit never uses `ldr rX,=V`: constants live in one labelled
  `lit_xxxxxxxx: .word` table mid-code, loaded with `ldr rX,lit_name`.
  `assemble_tasm_kit.py` verifies every pc-relative load and every native branch
  target against the source and requires a single trailing `.ltorg`. Code is
  ~6.4 KiB of the 7.75 KiB before the route table (v0.4.1).
- Arena `--place DX:DY|skip,...` moves the nearest fighters (HP >= 16384, not state 6) next to
  Spidey (before 2026-10-06 it also corrupted their heap neighbours), but placed
  enemies often stay frozen in their idle state (no attacks)
  and the Snare frequently zips to scenery there; use natural spawns for AI
  research. For kit targeting/movement, `trace --phantom DX` adds a fake registry
  enemy (no AI/hitbox) in the training room; contacts on it whiff.
- Sense, Leapfrog and Perch use velocity (v0.4.1), letting native collision
  resolve walls/floors. Audit found a remaining direct Skyjack juggle drift
  write to motion+0x7C; sky-velocity and combined candidates are now agent-qualified
  but unpublished (see "Shared crowd-hit backend candidates"). A position write ignores
  collision (the v0.4.0 Sense teleport put Spidey 2 units inside the training
  room's right wall at x=968577 and clipped the player out of the level). Lab
  teleports (`kit_lab.teleport`) write the motion base and the three probes
  only. Repeating the same action skips resource lookup unless motion+0x2FC
  bit1 is set (Spin Cycle uses this).
- Never dereference another actor without `kit_alive` (vtable in the class
  range, motion and controller pointers in RAM): registry entries are trusted
  for two ticks and a freed/reused actor once held motion pointer 0x60000
  (data abort in the v0.4.0 Sense scan).
- Growing the Glob shifts everything by about one emulator frame; parity checks
  allow one constant phase (`kit_lab.same_behavior`).
- Room warp fixture (lab only): patch the Test Upgrades entry `0x020ED7AC`
  `mov r1,#0` (story context), `0x020ED7B4` `mov r2,#room`, `0x020ED7DC`
  `mov r2,#selector`, `0x020ED7E0` `mov r3,#spawn` via `--patch`; selecting
  Test Upgrades then loads that room natively (`midnight_line.py tour`).
- Touch: script rows may carry `touch: [x, y]` (pixels of the stacked 256x384
  output; bottom screen y>=192); the harness then sets `melonds_touch_mode`
  to `touch`. `kit_lab._run` forwards whole rows (it used to drop `touch`).
- After room transitions a freed copy of Spidey's actor can stay in RAM;
  `player_trace.sample` keeps the candidate whose motion object points back
  at it (`[motion+0]`), otherwise traces stopped after a few rooms.
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
