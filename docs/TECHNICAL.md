# ROM technical knowledge

This is the technical notebook; sections carry their own version/date and evidence.
Older sections describe earlier contracts or experiments. Start with the topic map
below, search headings and read bounded sections. Never bulk-read it at startup.
Confirmed fields, hypotheses, unknown bytes and confidence belong here. Reusable
commands/evidence workflow: [DEVELOPMENT](DEVELOPMENT.md); shipped behavior/history:
[CHANGES](CHANGES.md); native gameplay: [OG_GAMEPLAY](OG_GAMEPLAY.md); current
objective/build and next action: [TASKS](TASKS.md).

## Topic map

| Working on | Start here | Historical context when needed |
|---|---|---|
| Current Midnight boss contact, guard/counter handling, active route/map and ramp | [Reliability correction (0.28)](#reliability-and-active-route-correction-028-research) | [Combo openings/anatomy (0.27)](#combo-openings-and-coherent-creature-motion-027-research), [audio/poise (0.26)](#voltage-correction-quiet-cues-and-ineffective-poise-026-research) |
| Current Skitter and Crane pursuit/hoist finish | [Scoped finish (0.29)](#scoped-movement-and-chapter-finish-v0290) | [Contact/lifecycle correction (0.24)](#midnight-enemy-rejection-contact-diagnosis-2026-10-18), [Midnight anatomy (0.27)](#combo-openings-and-coherent-creature-motion-027-research), [Creature Forge](#creature-forge) |
| Current room envelopes, roofs, shutters and persistence | [Room/contact correction (0.24)](#midnight-enemy-rejection-contact-diagnosis-2026-10-18), [active-route correction (0.28)](#reliability-and-active-route-correction-028-research) | [Chapter spectacle](#chapter-spectacle-implementation-v0230-2026-10-17), [chapter renewal](#chapter-renewal-v0210-2026-10-17), [Crane terrain](#crane-row-terrain-overhaul-v0170-2026-10-15) |
| Rooms/collision/doors/maps | [Room compiler](#room-compiler-v0120), [collision tree](#room-collision-tree-2026-10-11), [native doors](#native-doors-spawns-and-game-variables) | [Minimap screens](#minimap-screens-and-area-room-lists-v070) |
| Player kit and native combat | [Player state machine and Red kit hooks](#player-state-machine-and-red-kit-hooks-v020), [animation authoring](#kit-animation-authoring) | Later named kit sections describe extensions; use the current release recipe |
| Skyjack velocity correction | [Scoped finish (0.29)](#scoped-movement-and-chapter-finish-v0290) | [Parent audit and unshipped prototypes](#shared-crowd-hit-backend-candidates); the old source/hex still reproduce their historical releases |
| Binary formats and preservation | [Format boundaries](#format-boundaries-and-confirmed-structures), [SCA/rig contract](#animation-authoring-and-current-evidence) | [Baseline inventory](#rom-baseline-and-inventory) |
| Emulator/rendering and performance | [Performance and visuals](#performance-and-visuals) | Dated renderer/JIT observations are not current performance guarantees |
| Hook/trace failures | [Research workflow and pitfalls](#research-workflow-and-pitfalls-red-kit-sessions), then the affected feature | Old candidate claims remain scoped to their recorded build |

Read the latest applicable section first. A later confirmed correction supersedes
an earlier hypothesis; retain the earlier observation as history, not as a second
current contract. Exact published identities and selected controls are in source
recipes/release pins and the owning `reference/` receipts.

Current capability summary: [Editing status and confidence](#editing-status-and-confidence),
reviewed against published v0.29. Dated prototype/qualification sections retain their
original fixture scope; a pending test in an old candidate is not automatically
an open task in the published composition. Player verdicts belong in the live
roadmap, not in historical agent test counts.

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

Initial milestone (completed by the 2026-10-02 update below): boot-test an
unmodified round trip, then one visible asset modification.

### Validated workflow update — 2026-10-02

The original facts above were reproduced against the supplied clean ROM. Glob and
full ROM no-op rebuilds are byte-identical, with all 3,733 extracted resource hashes
verified. `mod.py` now provides validated overlay builds, extraction, listing,
search and verification; size changes update FAT/header CRC and stay within capacity.

The unmodified round-trip build and a single `spd.nsbtx` palette edit both reached
Residential gameplay in melonDS DS 1.1.5. The edited player's red suit appears green.
Reverting the overlay reproduces the original ROM hash. This completed the
initial bounded boot/visible-change experiment.

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

**Gap protection correction (2026-10-23, high confidence; v0.32.1 tooling):**
ordinary `wos_tool.rebuild_rom`/raw repacks reject writes over non-padding bytes
in internal gaps and in the gap before used-size, as well as after used-size.
Previously only the last case was guarded. Frozen chapter/release generators
explicitly use `legacy_gaps=True` with their existing parent/output pins: past
relocations left old file bytes in newly formed alignment gaps, and rejecting
those bytes would prevent exact historical reproduction. This compatibility
path changes no published bytes. Synthetic regressions distinguish protected
unknown gaps from that historical relocation residue.

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
The texture census accepts the build loader's bounded Rush/kit overlay additions
(2026-10-23, high confidence in source regression and current-overlay command).
It inventories native archives plus their overlays; generated chapter post-pass
resources and simultaneous texture residency require separate ROM/runtime review.
Archive `MOVIE_SUIT_EXPERIMENT.md` and `FORMAT_NOTES.md` heading `NSBTX / TEX0`.

**2099 appearance research (2026-10-22, v0.29 parent; high confidence):**
`spider2099_art.py` decodes the native player GPU strips and unscaled bind nodes.
All 480 decoded triangles agree with the independent apicula DAE vertex positions
within 0.000001 game unit. Red/Black geometry, UVs and 37-node rigs agree; their
native model differences are two dictionary-name bytes. Stored matrices can bind
each added triangle vertex separately, permitting forearm fins/fingertips and an
open mantle to follow existing bones without editing SBC, skin, animation or AI.
The native shape begins with restored head matrix 3. Native scale and all opaque
node bytes must remain exact. This bounded player path supersedes the blanket
"no topology/skin editor" limitation above only for appended GPU geometry.

The old `nsbmd_docs.txt` pivot prose incorrectly states c=±a, d=±b. Actual
[apicula rotation source](https://github.com/scurest/apicula/blob/master/src/nitro/rotation.rs)
uses c=±b, d=±a, with column-major entries. Following the prose produces singular
matrices; use the executable source and independent mesh agreement. This does
not change `Sca` rotation conventions or authorize changing any bind transforms.

**2099 draw-ownership correction (2026-10-22, v0.30.0 / unshipped 0.30.1 A;
high confidence):** the game loads `spd.nsbmd` for both forms and switches the
texture. At a freshly continued Black-form frame, live RAM contains the shared
15,108-byte `spd` model and no `spdB` model. Solid-cape-atlas and solid-cape-UV
controls on `spdB.nsbmd` have no visual effect. Replacing the shared `spd` model
in a labelled research-only control makes the cape geometry draw. This supersedes
the earlier assumption that editing `spdB.nsbmd` selected Black geometry. v0.30
shipped its texture and authored inactive model; its screenshots did not prove
the fins/cape were drawn. Preserve its immutable bytes and original receipts.

The live player chain is actor+0x30 -> motion, motion+0x58 -> model wrapper,
wrapper+0x14 -> MDL resource. Model wrapper vtable is 0x021284B4. Its ITCM draw
method is 0x01FF8658; 0x01FF87C0 moves that wrapper (r5) into r0 just before its
draw call. The execution address differs from its ARM9 autoload source offset;
derive it from the autoload table, never patch a negative ARM9 offset.

Material+0x24/+0x28 are binding magnification fields. The shared 128px material
has 0.5 values after binding a texture whose TEX0 extra word still declares 64px
original dimensions. TEX0 extra word low 11 / next 11 bits carry original width /
height; preserve upper bits when correcting a new atlas. A pixel UV-scale claim
still needs a rendered control; these fields alone do not prove GPU texgen use.

**Published 0.30.1 draw correction (2026-10-22, E; high confidence):**
`spider2099_sculpt.py` ray-qualifies six dorsal forearm blade mounts against the
reshaped skin and sweeps the tips toward each elbow. Collar points sit 0.07 unit
behind the actual back surface and bind to its native bones. A curved 8x5-panel
crimson cape reaches the upper thighs and billows in Z so the side camera sees
its web. Wider pecs/lats/traps, fuller upper arms, restrained forearms and modest
thigh volume retain all 37 bind nodes, SBC records and native animation data.

`spider2099_visual.py` keeps the exact original Red GPU list in shared `spd` and
appends the Black list, with a private 64-byte footer. The pre-draw adapter resolves
the current wrapper/MDL afresh, checks RAM bounds, vtable, model size, footer tag,
offsets, stream bounds and native form, then changes only shape list pointer/length
and material dimensions/magnification. It preserves all registers/CPSR flags and
replays native `mov r0,r5`. One list is submitted per draw. The 4 KiB autoload
extension preserves the entire 32 KiB kit; its ITCM hook is patched at the derived
ARM9 source offset. Model counts/box cover either appearance. `spdB.nsbmd` remains
the inactive historical asset; previews explicitly select the shared Black list.

E's six live captures prove Red/Black/Red list selection, I8/I4/I8 texture formats,
matching dimensions and transparency, including a newly allocated model after a
native door transition. Motion positions and purchases/XP/HP match the parent;
the room run retains one transient newly initialized actor position sample.
Exact identities and raw evidence are in `reference/spider2099_polish.json`.

**Observed texture residency boundary:** C's 256x128 I8 atlas adds 16 KiB of
pixel storage and leaves crowded Terminal actor materials unbound (`format=0`),
although the mechanical route passes. The parent and the same-geometry I4 control
bind correctly. D/E use 15 opaque colors plus transparent zero, packing 256x128
I4 into the parent's 16 KiB pixel pool. The entire body half is opaque; the cape
half has actual holes. Native original-dimension bits are corrected and upper
flags preserved. E's crowded scene has bound player I4 textures and visible native
enemies/hurt poses. The configured global VRAM bank capacity is not established by
these observations; do not infer texture headroom from a sparse room or a route
pass. Preserve the paired failed C control and qualify the final crowded scene.

**Published cape-free movie appearance (2026-10-22, 0.30.2 B; high confidence):**
`spider2099_movie_art.py` starts from the exact native mesh, retains its 37-node
rig/SBC and reshapes chest/deltoid/trap/jaw vertices continuously in bind space.
Only six mounted blades and six small talons remain as added geometry: 516 total
triangles, with the old cape stream/footer removed before recomposing shared
`spd`. The movie-inspired atlas returns to opaque 128x128 I8 at the same 16 KiB
pixel footprint. Actual original dimensions are declared and transparent-zero
is disabled; palette index zero is an opaque navy color. Red retains its exact
GPU list and texture. `spider2099_movie.py` changes only the existing selector's
model-size/footer literals; all its instruction bytes, hook, autoload size and
32 KiB kit stay exact. Forty-five source/ABI/release/document checks and ten
fresh native-input live RAM captures qualify both forms and a real door reload,
including Black attacks in the newly allocated model. The crowded player binds
I8 and renders during native hurt. Settled motion and purchases/XP/HP match;
one transient new-room position sample is retained. Full normal-source,
canonical, accepted and installed ROMs agree. Exact receipts are in
`reference/spider2099_movie.json`. Player visual acceptance and actual DeSmuME
pacing remain open; enemy texture success is explicitly excluded below.

**Crowded-scene evidence correction (2026-10-22; high confidence, actual retained
v0.30 parent/D/E and 0.30.2 B RAM):** all four observations have custom creature
materials with `format=0`, and the captures show white untextured enemies.
The earlier claim that D/E restored crowded actor binding was too broad: the
recorded improvement establishes the **player's** I4 binding/rendering only.
B's 128x128 I8 player binds/renders, as do both forms after reload, while the
same pre-existing enemy failure remains. Thus byte footprint alone neither
explains nor qualifies all scene textures. Enemy texture success is not a passed
gate for these older releases; preserve their ROMs and raw receipts. The current
cosmetic scope keeps those enemy resources exact and requires a paired parent
comparison. That v0.30.2 enemy-binding issue is resolved for the sampled Terminal crowd in v0.30.3; room-wide residency remains unqualified.

**Shared creature atlas residency fix candidate (2026-10-22, v0.30.3 A; high confidence for the sampled Terminal scene):** v0.30.2's correct `Forge128` / `ForgePal` material names and 128x128 dimensions still yielded live enemy texture format0 with its 32 KiB direct-color atlas. A disposable resource-only control keeping the same artwork, UV dimensions, model sheets, XBDs and gameplay executable changes only the shared atlas to I4: packed I4 pixels take8 KiB with a 16-color RGB555 palette. On the same copied-save Terminal route all three live enemies then bind 128x128 I4 (`format=3`); the player remains textured I8. The numbered v0.30.3 candidate applies that same atlas plus boot/Options strings; ARM9/ARM7 and every model, XBD, animation and room stay exact. This strongly supports texture residency pressure as the cause; format and pool size move together, so it does not identify a lower-level allocator limit. One mixed scene is not whole-game texture qualification or a DeSmuME pacing result. Keep the direct-color control and full scene evidence in `reference/spider2099_enemy_texture.json`.

**Compact shared creature atlas restores Terminal texture residency (2026-10-22, v0.30.3; high confidence for the tested scene):** the v0.30.2 shared `Forge128` model texture and `ForgePal` palette dictionary names were correct, yet all live enemy materials read `format=0` with a 32 KiB format-7 direct-color atlas. `spider2099_enemy_texture.py` replaces only `zz_F22_Atlas.nsbtx` with the same 128x128 UV artwork represented as I4, an 8 KiB pixel pool and a 16-color `ForgePal`; native material UV dimensions and every model sheet/XBD/NSBMD/SCA/GMB/GAB remain exact. The version strings advance to 0.30.3. A fresh copied-save experiment and full numbered candidate show three live enemy materials bound at format3/dimensions128x128, while the hero retains its I8. The native route passes; enemy AI/HP/positions stay live after initial fixtures, no healing, and the actual battery is unchanged. The paired format/footprint change strongly supports texture residency pressure, but does not prove a hardware allocation threshold. It qualifies the Terminal crowd, not every room or DeSmuME pacing. Detailed receipts are in `reference/spider2099_enemy_texture.json`.



### Text / UI / rooms / audio

**Boss-only palette rendering defect (2026-10-22; high confidence in copied-save
v0.30.3 and v0.31 research arena controls):** the Conductor renders persistently
magenta even without incoming player hits. Both old and newly sculpted meshes
show it, while the live material reports bound I4/128px. Thus a nonzero bound
format alone does not prove valid colors, and the v0.30.3 Terminal qualification
does not cover the boss. A compact boss-only 64px RGB555 texture with halved UVs
is qualified in v0.31.0 with format7 and actual rendered colors; shared crowd I4 artwork remains unchanged. The precise
native palette ownership failure is unconfirmed.

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
[GAMEPLAY](OG_GAMEPLAY.md) before paid route changes. The v0.2.0 snapshot used
a v0.1.1 parent plus Red kit and a 24 KiB HUD/kit reserve. It is superseded as
current composition by `reference/gameplay_profile.json`; the current kit's
reserve is 32 KiB (`tasm_kit.RESERVE`). Free heap/VRAM peaks remain unknown.
Common player/enemy
HP telemetry is actual loss, with specialized health coverage still incomplete.
Training SELECT+Down refill has positive/flag-clear controls and preserves
position/reaction/XP/meter; other target flags are unknown.

DSVv0 wrapper is lossless/validated; game payload/checksum remains opaque.
Snapshots are byte-preserving, not a save editor. Native purchase/refund/save/
reload checks pass for released moves; real-save protection is separate from
copied-save fixtures. Follow [WORKFLOW](../README.md).

**Publication/probe correction (2026-10-23, high confidence; v0.32.1 tooling):**
`playtest.build` validates the candidate metadata hash, retains prior build
metadata with its ROM, rolls back caught publication failures across the ROM,
metadata, receipt and history, and preserves an existing matching release receipt.
Fault-injection tests cover every write, first install, and a failed recovery
write without skipping the other recoveries. `player_trace.sample` now requires
aligned motion ownership even when only one player layout remains; a lone freed
layout is not evidence of a live actor. Both are tooling/source tests, not new
in-engine gameplay qualification.

Historical authored Rush qualification (before v0.2.0): eight choreography tests,
all 3,736-resource build check,
both-facing contact/HP/credit/final-position parity. Prior compact source passed
125 tests; latest gameplay revision did not rerun that full suite. Original
archive extension shifted all observed contacts two emulator frames, including
unchanged Snap; count-only control has the same shift. Relative clocks/timing
remain exact, with no established FPS change. Player/ordinary encounter,
walls/bosses/interruption/long-play acceptance remains open.

The 2026-10-05 documentation cleanup preserved every original note byte and
SHA256 before consolidation: 36 entries and 131 maintenance source tests,
including four archive integrity/reader checks. Those are historical counts;
`doc_archive.py verify` checks the expanded archive's current index. No additional
emulator/player coverage was established by that maintenance.
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

Reviewed against published v0.29 on 2026-10-22, private USA CS5E.
This replaces the v0.2.0 capability matrix; its original format notes remain in
the archive. Confidence applies to the bounded paths actually implemented, not
arbitrary files or player acceptance. Use the topic map for exact contracts and
the current recipe/adjacent metadata for counts and composition.

| Format / area | Confirmed control | Editing / confidence limit |
|---|---|---|
| NDS / NitroFS | Validated FNT/FAT/CRC/bounds, exact baseline no-op, resized/generated ROMs | Guarded known layout and capacity growth; preserve opaque bytes and original ROM. |
| Glob.bin | Ordered original IDs, size changes and bounded generated additions | Three Rush + twelve kit SCAs are fixed overlay additions; chapter/creature builders append their own scoped resources. Arbitrary names/manual GlobFiles edits remain rejected. |
| NSBTX / textures | Player I8 repaint and RGB555 shared creature/room atlases | Bounded palette/material/UV paths; native material dimensions and alignment matter. General format-5 authoring remains outside the proven path. |
| NSBMD / rig | Authored creature meshes/weights on native rigs, room geometry, native SBC/material tint preservation | This is a deterministic bounded authoring pipeline, not a general skeleton/skin editor. |
| NSBTA | Inventory and XBD material-animation bindings | General payload editing remains unproved. |
| XBD actors | Actor/action/resource bindings and scoped private animation/model routes | Preserve other users and opaque tails. GroundAttack15 is shared; G11/16/17 have m6 users. |
| GAB / GMB | Lossless original framing, timed contact events, resampled motion/contact volumes | Bounded native event/carrier contracts; active windows and counters alone do not prove native contacts or damage. |
| SCA | Lossless/sample-document round trips, authored translation/rotation/scale, player and creature motion | Preserve rig/sample/clock contracts; verify native-scale continuity, contact and complete lifecycle in-engine. |
| BSP / OBJ | Decoded collision tree, room compiler, placements, camera/anchors, doors and selected event commands | Authored envelopes/geometry and real-input routes ship. Preserve unknown commands/fields; parser validity is not traversal proof. |
| STRINGS | English/American Huffman round trip, growth, shop/dialogue and version labels | Boot/Options must agree. Other languages/popups are not generally qualified. |
| FONT / 2LZ / DAT / PAL | Native font/canvas reuse, selected sprite/palette conversions and map metadata | Wider UI/font families remain partly unknown; preserve unowned fields and localized behavior. |
| CBMP / minimaps | Authored local/detail maps, ports, visited/current colors and chapter area selection | Bounded chapter paths; no general editor for every bitmap family. |
| MDAT / MGFX / MPAL | Scene-family inventory | General editing remains unproved. |
| SDAT | Lossless container framing, appended sequence/bank/wave rows, scoped voice remaps and captured PCM | Preserve untouched files, native IDs/pitch/pan and distinct internal/FAT lengths. Playback evidence and mixed-audio quality are separate. |
| ARM9 / extensions | Hash-guarded hooks, native tables, private controller/room/boss adapters | Player HUD/kit reserve is 32 KiB. Check ABI, flags, actor ownership/freshness and final composition; heap/VRAM peaks remain unmeasured. |
| Player movement | Native velocity/collision for Sense, Leapfrog and Perch; v0.29 composes the scoped Skyjack correction | Historical base source still contains the v0.28 drift; current composition applies frozen corrected code afterward. The broader crowd-hit prototype remains unshipped. |
| Combo / health / HUD | Distinct combo credit, response strength and actual HP; native boss HUD isolation | Specialized coverage and ordinary-play balance require measured controls. The combo gauge is not a hit count. |
| Purchases / progression | Original 21 rows plus released Red/Both Suits additions, native dependencies/refunds/save persistence | Preserve paid ownership, Black bits, story abilities and shared traversal. No general shop/save migration or third suit selector is implemented. |
| Saves | Lossless DSV v0 wrapper and opaque native battery checkpoints | Byte-preserving backups/guarded publication; not a game-payload/checksum editor. Use actual latest batteries and disposable fixtures. |
| Training / lab controls | Native training/refill hooks and version-scoped enemy/door/combat fixtures | Temporary grants, healing, isolation and initial arrival warps must stay labelled; they do not establish current-owned difficulty. |
| Performance / graphics | Accepted JIT improvement and dated emulator/rendering controls | Actual full-route DeSmuME frame pacing and later renderer/HD quality remain separate gates; old idle throughput is not a current FPS guarantee. |

Published, agent-tested and player-confirmed are separate states. Exact selected
qualification/inheritance belongs in reference receipts; do not promote historical
test totals or an isolated clear into a current whole-game quality claim. Game
assets, batteries, emulator captures and local build outputs remain private.

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

### Shop tables, menu and free ownership bits (v0.10.0)

Confirmed 2026-10-11 by disassembly, RAM and real-menu runs (`work/shop/`).

- **Six purchase tables.** Pointer list `0x02120170` / counts `0x02120188`:
  Both Suits `0x02120260` (7), Red `0x02120340` (7), Black `0x02120420` (7),
  base moves `0x02120680` (12, price 0, bits 56..67), story abilities
  `0x021201A0` (6, bits 0..5), collectibles/stats `0x02120500` (12, some
  with 2..18 levels; events 306..308 are not ability bits). Only the list
  references a table, so a table can move: v0.10.0 points Red at ten rows in
  the kit's second block.
- **Menu.** Object +0x104 category, +0x10C cursor, +0x108 first visible row.
  Four rows show; Down/Up (`0x020F12A4`/`0x020F1388`) scroll and wrap by the
  category's count, so a longer list needs no menu change. Buy, refund and
  "Clear All Upgrades" are table-driven (all three exercised on new rows).
- **Events.** Query `0x020D22AC` / setter `0x020D24D8`: ids below 0x123 are
  game flags (stats+0x1C), 291..308 scalars/special cases, 309..381 ability
  bits 0..72 (asserted `< 0x49`), 382 and up nothing; 382 is the menu's "no
  event" value. The notifier `0x020D2704` only acts on 0x114..0x11A and 0x123.
- **Free bits.** Ability words are stats+0xC/+0x10/+0x14. Every bit 0..72 is
  owned by a table row except 55, which saves carry set and gameplay queries
  (`0x020B4C94`, `0x020B7630`, `0x020B9DBC`): not free. Bits 73..95 (third
  word, bits 9..31) are unused, and a native save + Continue keeps them
  (`work/shop/bits_save_lab.py`: `0xFFFFFE0F` before and after). stats+0x18 is
  a running counter (it changed between save and reload): never use it.
- **v0.10.0 bounds.** `add rX,#0x5b` -> `#0x72` at `0x020D2460`/`0x020D2634`
  and `cmp #0x49` -> `#0x60` at `0x020D2478`/`0x020D2658`/`0x020D26A8` make
  events 383..404 ability bits 74..95. Bit 73 (event 382) stays never set.
  Used: 383/384/385 = bits 74/75/76 (third-word masks 0x400/0x800/0x1000) for Web
  Rush, Ricochet, Momentum. 19 bits (77..95) remain for later rows and suits.
- **Texts.** Row name/title/description ids may be appended string slots
  (1049+); the chapter appends its lines after whatever the kit ROM holds.
  The kit overlay in `mods/` therefore has 1058 slots: `StringSlots.repack`
  re-encodes through `grown()` when the slot count is not the native 1049
  (it used to reject such an overlay), and `tasm_kit.shop_strings` rewrites
  the nine slots instead of appending again.
- Bought, refunded, re-bought and cleared through the real menu; bought rows
  survive save + Continue (third word `0x1C0F`, XP 1000): `work/shop/shop-*.json`.
- **v0.11.0: Both Suits rows.** The Both Suits list (pointer `0x02120170`,
  count `0x02120188`) moves to block +0x1940 with ten rows: the seven parent
  rows and Vitality I..III on events 386..388 (bits 77..79, third-word masks
  0x2000/0x4000/0x8000; 500/750/1000 XP). Each needs the row before (required
  event) and names the next as dependent, the native Spider Dance/Scissor
  rule. Bits 80..95 remain free (16). Real menu on `ea5376f7`
  (`work/shop/vit_shop_lab.py`, frames `work/shop/vit-shop.png`): bought in
  order (third word 0x200F, 0x600F, 0xE00F; XP 3000 -> 2500 -> 1750 -> 750),
  refunding level I under level II is refused, level III refunds.
- **Multi-level rows are not safe in the three shop lists.** Buy
  (`0x020F1AA0`) and refund (`0x020F1B4C`) count owned levels with
  `0x020F123C` (consecutive events from the first) and A buys the next level
  until the row is full, then refunds one. But the row predicate
  (`0x020F1150`) only tests "can afford" while the *first* event is unowned,
  so a second level could be bought without the XP. Use chained one-level
  rows. The native stat pickups (resources `OrbUpHP`, `OrbUpLP`, `OrbUpDam`,
  `OrbUpDef`, `OrbUpMap`; table `0x02120500`) are the game's own levelled
  stats and were not studied.

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
For a grown variant use `decode_grown(raw, id)`: `StringSlots(clean).decode`
uses the clean tree/table layout and can silently return another valid slot.
Published v0.15.1 was checked with the variant decoder: both locales contain
`TASM v0.15.1` at50 and `Options v0.15.1` at74.

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
the menu scroll and spare ability bits were proved in v0.10.0 ("Shop tables,
menu and free ownership bits"); save checksums and migration remain unproved. Event query/setter support 309..381 is not evidence that any unassigned
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
2 jump (B), 3 evade (R), 4 object (X), 5 suit action (A; native Webbed Fury control). Ability query: actor vtable `+0x184`
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
**The fifth argument is the health the hit takes** (Q12; lab 2026-10-13: 0
costs nothing, 0x800 costs 2048, 0x1000 costs 4096, whatever info +4, +0x18
or +0x2C hold). The dispatcher passes 0x1000 and the meter's tier scaling is
applied elsewhere; a kit replay with 0x1000 therefore always costs one unit.
A hit can also be **built from nothing** (no captured template): info {kind,
strength 0xC00, 3, &extent, &contact, +0x18 0x4000, +0x1C 7, +0x2C 0x1000},
a zero extent record, contact record {motion+0x2B4, 3, 0, 5, 0, kind,
motion+0x310, strength} (the two attacker parts are fixed offsets inside
Spidey's motion object), attacker cell = Spidey's actor (`web_hit`, "Web
lines, built hits and the web skills"). The web grapple and its follow-ups
do not pass the dispatcher (nothing is captured before the web kick's 0x20):
the state code calls ReceiveHit itself. Reactions of a standing Brute to a
built or replayed kind (lab, sparring room; enemy state / action):

| Kind | Reaction |
|---:|---|
| 0x04, 0x16 | stagger 37 (21 and 25 frames) |
| 0x1F, 0x20 | knockdown 41 -> 48 -> 49, thrown about 16 units away |
| 0x21 | **web yank**: 44 / 87, flies to Spidey at about 3.5 units per update and lands 6 to 10 units in front of him (48, then 49 for about 60 frames, get-up 51). Needs a web line on him: without one he drops where he stands (48) |
| 0x22, 0x23 | **web hold**: 46 / 53 (the cocoon); stays for a long time after the line lets go |
| 0x24 | thrown toward and far past Spidey (41 / 85; 70 units) |
| 0x25 | launched 39 / 88 to about 25 units up |
| 0x26 | pulled along the floor 45 / 87 at 4 units per update, slides on past Spidey if nothing stops him |

An enemy in the air or on the floor can be hit again: 0x04 or 0x16 on a
yanked (44/48) or lying (49) enemy gives 41 again (a small bounce, about 20
frames), 0x14 on a flying one the air juggle 42, 0x25 launches even from the
floor. A jumping enemy (state 4) answers 0x22 with a knockdown.

### Shared crowd-hit backend candidates

**Prototype validator correction (2026-10-23, high confidence; source test):**
`crowd_backend.assemble` imports the shared validators directly and includes
`self_branch_errors`. A conditional call that Keystone resolves to itself is
rejected before staging. The old AST extraction was unnecessary after the shared
assembler's writes were moved under its main guard. Published kit source/hex stay
unchanged; the prototype remains unshipped.

**v0.29 published validation, 2026-10-22 (high confidence):**
The fresh compiled correction preserves open-air native contacts. In the same
active right-wall juggle fixture, v0.28 reaches X991232, past the native bound;
the corrected kit stops at X968577. A left-wall control stops at X14463. These
are one-time disposable RAM setups of an established juggle, not gameplay
placement. The first wall report's 240-frame latch-release assertion ended
before its slow native descent completed; retain that failed driver assertion
separately from the passing collision bound. Final C passes both walls, native
R exits and all 68 kit checks; the qualified composition is now published. Source: `chapter_finish_kit.py` and
`work/chapter-finish/sky-*`; the original source/hex remains immutable.

The prototype controls below are a **2026-10-06 historical snapshot**.

**Current source/binary recheck, v0.28.0, 2026-10-21 (high confidence):**
`tools/tasm_kit.s` still ends `sky_player` by adding the clamped horizontal
correction directly to player motion+0x7C. The pinned first kit block from
`tasm_kit.code_bytes()` matches the installed v0.28 ROM; at block+0x1278 it
contains ARM words E595107C/E0811002/E585107C (load/add/store). The old velocity
candidate therefore remains unshipped. This is a known movement-contract debt,
not a newly observed wall clip or performance regression. A future correction
must use native velocity/collision and requalify open/wall/cancel behavior on a
new composed release; do not install the old disposable RAM patch as a fix.

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

2026-10-11: v0.10.0 changed the published kit (6940 bytes plus the second
block), so the validations above describe candidates over the v0.9.0 kit.
`crowd_backend.py stage` still assembles all three over the new source
(anchors intact); requalify before publishing one. Ricochet (v0.10.0) is its
own scan in the second block, not `kit_area_hit`.

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
v0.10.0: the first block had 1132 of 7936 code bytes left, so a second block
follows the old reserve: KIT2 `0x02155420` (TARGET+0x6000), 8 KiB: code up to
0x1800, the ten Red shop rows at +0x1800, zeroed state at +0x1C00
(`0x02157020`). IMAGE = RESERVE = 0x8000, Glob count 3736 + 8; the main arena
and the chapter block (`kit.TARGET + kit.RESERVE`) now start at `0x02157420`.
The lab phantom area (`0x02155020`, KIT_STATE+0x400) is unchanged.
v0.13.0: the second block's code space is 0x1900 (6204 bytes used), the 13
Red rows follow at +0x1900 (to +0x1AA0), the dial stays at +0x1B00 and the
ten Both Suits rows moved to +0x1E80, the tail of the state area (the code
uses state offsets below 0x280: `KIT2_STATE_USED`). Glob count 3736 + 12.
First block: capture also stores the victim (+0x37C) and a ring of the last
four {victim, tick} at +0x2B4 (index +0x2B0); route kinds 9 and up ask the
second block (`k2_route(kind)`); the string node hook passes the previous
state ([r6]) to `k2_node`. Its literal table moved behind Leapfrog: the
staged crowd-hit candidates add code and their last loads were out of reach.

### Second kit block: Web Rush, Ricochet, Momentum (v0.10.0)

Source `tools/tasm_kit2.s` (2140 bytes), assembled with the first block by
`tools/assemble_tasm_kit.py` (same literal/branch checks; `lit2_` table).
The blocks call each other only through fixed entry tables: kit1 exports
`kit_owned`, `kit_keys`, `kit_face`, `kit_alive`, `kit_fresh`,
`kit_replay_hit` at KIT_BASE+0x38..+0x4C; KIT2+0x00 per update, +0x04 string
blocker, +0x08 node start, +0x0C route flag, +0x10 native hook `0x020B21B8`
(`HOOKS2`). Ownership is the third ability word (stats+0x14, `[[actor+0xE8]+8]`): 0x400 Web Rush,
0x800 Ricochet, 0x1000 Momentum, Red form only. State offsets are listed at
the top of the source. Lab: `kit_lab trace --bits2 0x1C00 --tier N`; rows
carry `k2` (rush phase, dash step, Ricochet count, Momentum doubled steps).

- **Input queue.** Command 5 is A (suit power; peeked by the grapple and Black
  power transitions), next to 1 Y, 2 B, 3 R, 4 X. In a non-cancelable string
  node A does nothing natively; in a cancelable one it cancels into the grapple.
- **State 46 entry.** The blocker's state-46 arm starts at `0x020B5334` (kit
  hook +04) and runs every update of the state. Returning 46 with controller
  +4 = 1 re-enters: entry `0x020C2F94` advances the node, then `0x020C31E4`
  requests `table[node].action` through the slot at sp+0x18. The kit's node
  hook can swap that action and put the node back, which is how a move is
  inserted into a string without spending a node.
- **Web Rush.** A queued in a Red ground string picks the nearest standing
  enemy 7..56 units away on the same level (6 units; a held Left/Right picks
  the side; states 41/48/49/51 are skipped). State 46 re-enters and plays
  action 58 with the routed clip (kind 9) while the node stays the cancelled
  one (a spin's 16 becomes 15), so the next Y continues after it: from node 11
  the pause branch (15) with bit 16, else 12. The request is committed after
  the per-update hook, so the first update still shows the old action and
  clock: test `motion+0x258` (requested), not `+0x254`. Dash: velocity =
  remaining / (6 - clock) toward a point 4.5 units short of him, one last step
  when the clock reaches 6, kicks at 7, 9, 10. **The engine moves Spidey at
  most 5 units per update in state 46** whatever the velocity says, so for far
  targets the rate getter returns 1 (clock held on sample 2, the laid-out
  dive) until 15 units are left, at most 16 updates. A second A chains from
  clock 10. Same-action requests skip the resource lookup, so the node hook
  sets motion+0x2FC bit 1 when the rush starts and once more on the next
  node (node 13 also plays 58). No guard frames.
- **Ricochet.** Per Spidey update: a registry enemy in state 41/48/49 with
  |actor+0x18| >= 1 unit per update is a flying body (the string finisher
  throws one 22 units at 1.5 per update). Every other live enemy within 3.5
  units (5 vertically) that is not itself in 41/48/49/51 gets
  `kit_replay_hit` with kind 0x1F and flies the same way; 24-tick cooldown
  per registry slot, template at most 150 ticks old. Measured: four Brutes in
  a line all go down from one finisher (two natively, two by Ricochet, 4096
  Q12 each).
- **Animation rate and contacts.** `0x020B2098` is Spidey's per-update rate
  getter (r6 controller, r7 &rate Q12). Actions 1, 2, 3, 5, 32, 56..62, 130
  (4 after an extra test) take the Red branch at `0x020B21B8`: 1.0, or with
  bit 18 `[0x021341F4+0x230]` = 0x1266 (1.15), with bit 19 `[+0x22C]` =
  0x14CC (1.3); the block is filled at run time. Without bit 18, state 46
  with controller+0x64 bit 0x4000 returns 0 (string freeze). `0x020B33F4`
  separately shortens a per-attack byte (actor+0x20) for bits 18/19. **The
  engine tests the attack box of the GMB sample the clock lands on.** Attack
  channel word 5 marks active samples: G11 [4,5], G12 [2,3], G13 [7..10],
  G14 [4,5], G15 [4,5,9,10] (Snap plays this payload), G16
  [5,6,12,13,18,19], G17 [6,7]; air attacks have single samples (5, 2, 3, 5).
  Two-sample windows survive any rate below 2; G13's four samples are a
  multi-hit by duration. Measured string hits on action 58 at a constant
  rate: 1.3 -> 3, 1.37 -> 2, 1.44 -> 3, 1.51 -> 3, 1.58 -> 2, 1.65 -> 1.
  Never raise the rate through an active window.
- **Momentum.** Therefore it only doubles a step: the clock stays on the
  native grid and skips one grid point, and only where the samples that point
  can fall in (clock+1, clock+2) are inactive (`momentum_blocked`, checked
  against the GMBs by a unit test). An accumulator gains the combo tier per
  free step and doubles at 5 (tier t doubles t of 5). Ground string actions
  56..62 only; native during the Spider-Sense counter and a Web Rush dash.
  Measured Y,Y,Y,Y on the dummy: identical hits at every tier (56: 2, 57: 1,
  58: 3, 59: 1); the string ends at frame 113/105/99/93/91/87 for tiers 0..5.
- **Combo tier damage.** The same runs show the native meter scaling damage
  by 10% per tier (22528 Q12 at tier 0, 33777 at tier 5 for the same hits).
- **Lab note.** `--place` in the training room needs dy 0.06 (the floor is at
  5.03; at 0 the sparring Brutes sink through it once they move).
- **v0.11.0 additions** (2700 bytes; entries +0x14 `k2_observe`, +0x18
  `k2_damage`, called by the first block's enemy observer and player-HP store
  hook). *Speed:* `k2_update` writes 1.10 (0x119A) and 1.20 (0x1333) into the
  tuning block `+0x230`/`+0x22C` every update; the native getter and Momentum
  read them there (only `0x020B2218`/`0x020B222C` read those two words).
  With Momentum owned and the combo tier at 3 or more it writes the native
  1.15/1.3 instead. Actions 1, 2, 3, 5, 32, 56..62 and 130 follow, so Perch's
  stomp cycle is 41 frames instead of 37 below tier 3. *Momentum:* the
  accumulator gains tier + 1 (0 at tier 0), so tier t doubles t+1 of 5 free
  steps and tier 4 doubles all. Y,Y,Y,Y with Sense and Momentum (kit ARM9
  `3c6a34e0`, the release's): 122 / 106 / 100 / 88 / 86 / 86 frames at tiers
  0..5 (v0.10.0: 113 / 105 / 99 / 93 / 91 / 87), hits 2, 1, 3, 1 per action
  at every tier; Sense without Momentum 122 at any tier.
- **Momentum must not skip an action's last sample.** The string blocker
  (`0x020B53F8`: clip length - 1 > clock means "stay") only decides "repeat or
  end" on the last sample. At rate 1.2 a doubled step (2.4) from clock 10 of
  the spin loop (12 samples) jumped over sample 11 every loop: the spin never
  set its repeat flag and never ended (lab, tier 5; at 1.3 the grid happened
  to land on 11). `momentum_last` (last sample per action 56..62) now blocks
  doubling from clocks >= last - 2. After the fix: 190 repeat rows and 25
  hits at tier 5, 150 and 19 at tier 3, then the sweep and idle when the
  mashing stops.
- **Perch and the cycle gap.** B during a stomp cycle springs; B in the two
  updates between cycles (state 19; frame 160 of the qualification script at
  1.2, 156 at 1.3) goes to the native web swing (state 26). Older than
  v0.11.0; the qualification now presses B at frame 150.
- **Strength dial.** Table at `0x02156F20` (block +0x1B00, zero in a kit
  ROM): two bytes per room 76..115, enemy health and damage-to-Spidey scale in
  1/64ths (0 or 64 = native). `k2_observe` scales a common-health enemy's
  health and max once (max >= 0x4000; a scaled max is odd, native values are
  not; an enemy at full health stays exactly full, so no health bar appears
  over an untouched one) and `k2_damage` scales the health Spidey loses in
  the store hook
  (`0x0205F420`: r1 old, r3 new). The chapter build fills the table
  (`midnight_chapter.STRENGTH`). Lab on `4f387a21`: Span enemies 90,112 ->
  63,361 (x 45/64), Hollow 81,108 -> 60,831 (x 48/64); a native 8,192 hit
  takes 5,760 in the Hollow (x 45/64).
- **Vitality.** `k2_damage` also multiplies by 205, 171 or 146 /256 for bits
  77/78/79 (health worth 1.25, 1.5, 1.75 times): lab sparring Brute hit 4,096
  -> 3,280 / 2,736 / 2,336. Health and max are untouched, so the bar keeps its
  length. `vit_update` writes four BGR555 colours to the main-screen BG
  palette `0x05000032` (colours 25..28) every update: see "Player health and
  the top-screen HUD".

### Web lines, built hits and the web skills (v0.13.0)

Source: the web block at the end of `tools/tasm_kit2.s` (own literal table
`lit3_`), hook `0x020B6030` (HOOKS2, entry +0x1C). Ownership: ability word 2
bits 0x10000 Overclock, 0x20000 Dragnet, 0x40000 Vortex (ability bits
80..82, events 389..391). Lab: `kit_lab trace --bits2 0x70000`; rows carry
`k2` `oc`, `web`, `hits`, `drag`, `webbed`; scratch `work/kit/weblab.py`
(RAM pokes, compact summary) and `work/kit/newchecks.py`.

- **WebLine is an actor** (vtable `0x0212EFBC`, 0xB0 bytes) and the web
  grapple's picture: Spidey keeps a weak link to one at actor+0x40. Spawn:
  `0x0205F844(&out, &spidey, &from, &to, &colour)` (colour u16 0x7FFF; `from`
  natively the hand: position + actor+0xD4/+0xD8, about +0.87, +0.54 units).
  `0x0206632C(line, &from)` moves its start, `0x0206673C(line, &to)` its end,
  `0x020672D0(line, &actor, 1)` ties it to an actor (state +0xA8 = 3; the end
  then follows him; it calls his interface +0x24 with the line), `0x02067210`
  unties, `0x02066FDC` lets go (the line retracts and deletes itself: the
  native release `0x0205FAE8` calls it and drops the link). Fields: +0x54
  link to Spidey, +0x5C to the target, +0x64/+0x68 from, +0x78/+0x7C to,
  +0xA8 state (3 tied, 4..6 retracting). A line with a dead Spidey link
  retracts by itself. Spidey's own code is `0x0205F520` (shoot: spawn or
  re-aim, called every update of the grapple state) and `0x0205FA50` (tie).
- **Tying a line does not web the enemy**: the hold is ReceiveHit kind 0x22
  (see "Hit pipeline"). The kit ties a line of its own and builds that hit.
- **Weak links.** A reference is {pointer to target+4, next} and the target
  keeps the list head at +4; the destructor clears every referrer. Kit line
  slots (eight 16-byte slots at K2+0x100: link, next, enemy, age) are such
  referrers, so a line that dies (room change, retraction) empties its slot.
  Age 0 = held by Dragnet (and released as soon as Dragnet's phase is 0),
  otherwise the updates left ("flash" lines: 4 for a Vortex hit, 5 for an
  Overclock shot). `web_tick` moves every line's start to (x +-0.875, y +0.5)
  from Spidey each update.
- **The web hold natively** (lab): A at 21 units grapples in 6 frames (state
  37, then 38 with action 45); the hold lasts as long as nothing is pressed
  (400 frames seen); **A again lets go and the enemy stays webbed**; Y is the
  web kick only when the target is farther than `[0x021341F4+0x58]`
  (`0x020B61D0`; about 13 units), otherwise a plain string starts; the Y test
  is at `0x020B6014` (peek) / `0x020B6030`, before the ability 13 check.
- **Dragnet.** `drag_update` counts the updates A stays held in states 37 /
  38 (+0xC8; held keys are KIT_STATE+0x360 bit 0). At 12 in state 38 (once
  per press) every other live fighter (max health 4 units and up, not down)
  in front within 48 units and 10 vertically, up to four, gets a held line
  and kind 0x22 with no damage; phase +0xC0 = 1, count +0xC4. While he
  holds, a line whose enemy left state 46 is released (after 8 updates:
  the reaction is committed late). Leaving 37 / 38 any other way releases
  the lines (the enemies stay webbed). **Yank:** with phase 1 the hook
  consumes the Y, sends kind 0x21 (half a unit) to every held enemy, arms
  the heave (+0x94) and returns state 46. The game lets go of its own line
  as the hold ends and a yanked enemy without a line drops in place, so the
  first target gets a kit line and his yank one update later (+0xD0). Phase
  2 releases each line when its enemy leaves state 44 (from 6 updates on),
  all after 30. Measured: four Brutes 21..46 units away all lie 6..10 units
  in front of him about 20 frames after the Y.
- **Vortex** is a string without nodes of its own (the table ends at node
  17; 18 and 19 are zero records). `web_node` runs in the node hook after
  Web Rush: step +0x7C (1 whip on action 57, 2 double lash on 56, 3 slam on
  59, 4 the Dragnet heave on 49); the node is parked on 12 (14 for the slam)
  so the next Y arrives as node 13, which continues the step. Entry by
  pause: node 13, previous state not 46, and the "clean" flag (+0x8C: set
  while hit 2 plays, cleared by any state other than idle, walk, skid, run,
  so a Reflex resume keeps the native third hit). Back on his feet after
  hit 2 the node's keep-alive (+0x90) is raised to 16 updates once. A step
  routes its clip by kind 10 + (step & 3) and sets motion+0x2FC bit 1
  (hit 2 and the whip are the same action). Contacts (`web_contacts`: first
  active sample, kind, damage / 256): whip 2 / 0x04 / 0xC00, lash 4 and 9 /
  0x04 / 0x800, slam 4 / 0x1F / 0x1000. One update after the clock reaches
  a contact (or when the action ends) `web_area` builds that hit for every
  fighter within 14 units on either side (8 vertically) who is not in the
  capture ring of the last two ticks, and gives each a flash line. **The
  native attack box already hits every enemy inside it** (three piled
  Brutes all took the lash natively), so the area hit is the reach beyond
  about 6 units. The heave has no contact. Step 0 when the node dies.
- **Overclock.** `oc_update`: a new capture (tick +0x36C differs from
  +0x70, at most two ticks old, attacker Spidey, kind outside 0x20..0x26),
  owned, combo tier 5: the nearest other standing fighter within 60 units
  (10 vertically), not the victim, not shot in the last 16 ticks, takes kind
  0x16 for half a unit and a flash line. Built hits are not captured, so
  shots and area hits never chain.
- **Other inputs read on the way** (`0x020B6968`, the Y transition; queue
  direction word +4): 2 = Up (with ability 6, Launching Uppercut: state
  50), 6 = Down at rest (state 48, as from duck 5 / run 6), 4 / 0 with the
  facing test = back / forward. With ability 7 a Y from states 0x39, 0x3A,
  0x19 within 3 updates gives state 49 (Drill Kick). The string entry
  `0x020C2F94` gets the previous state in r6 and the new one in r5; its
  pause branch needs table +8, the ability and (previous state not 46 or
  animation time at least 12.0 Red / 16.0 Black). `spd.xbd` lists 126
  animation groups alphabetically; action ids are another numbering (49 is
  GrapplePullAttack, 10 samples).
- **Not done / limits.** No Spidey gesture for the burst (he keeps the hold
  pose); tier scaling does not apply to built hits; bosses and other actor
  classes are untested with web hits (the registry only holds common-health
  actors); a Vortex step does not turn him toward the crowd (the area is
  symmetric).
- **Gates** (ROM `75faa3ff`): qualification 63/63 (`work/kit/v0.13.0/`),
  crash hunt 24 fights with held A, yanks, releases and pauses (odd seeds
  at tier 5), ten walk routes. The fixtures: `reference/combat-inputs/kit/`
  `dragnet`, `dragnetrelease`, `vortex`; four sparring Brutes placed 21,
  30, 38, 46 units ahead and held idle until the web is out.

### Conditional tether Vortex and Conductor armor (v0.31 research)

Source: `vortex_forge.py`, `_art.py`, `.s`, `_lab.py`, exact published v0.30.3
parent. This supersedes the old four-step Vortex entry below. Ability82 remains
the same paid Red row. Down+Y in a grounded string/idle or native web hold
captures at most four fresh common-health actors in actual cocoon state46,
within30 horizontal/12 vertical units. Regular A and Dragnet share that native
reaction. An unwebbed, stale or out-of-range target cannot arm it. Native queued
Y is consumed only after eligibility; Black/unowned behavior falls through.
Native web-hold entry uses its exact stack epilogue. The armed timestamp lasts
two native ticks; captured pointers also retain motion/config ownership.

The single19-sample WebSlam route plays an authored continuous two-turn body
coil and overhead catapult, then a downward haul. Native kind25 launches each
cocoon; bounded actor X/Y velocities steer the tether arc through native physics
and collision. No player/enemy coordinate stores or clock writes ship. Native
kind1F delivers the finish. Actual nearby bystanders can receive body/ground
impact hits, once per fresh registry slot in each phase. R/hurt/jump or lost
ownership releases the private move; web actors expire through the existing
line system. The32KiB kit reserve and paid/native ownership remain; four helper
entries, the web-hold branch and raw-damage operand are scoped patches, with
the new adapter/state in one guarded SDK-autoload extension page.

The Conductor alone gains a500-quad engine/armor mesh and1.28x body translation
scale across all39 private SCA routes. Rotations, sample counts, scale tracks,
GMB/GAB attack windows, programs, HP/difficulty, voices and native collision
stay exact. A boss-only64px RGB555 atlas uses8KiB, halved UV coordinates and
one appended texture group reference; it fixes observed magenta I4 colors in
this arena. The shared crowd I4 atlas remains exact. A cheap-HUD observer
filter suppresses only the exact NormalEnemy/private-Conductor config and
retains its native prologue/flags for all other actors. The top boss meter stays
native. Agent-tested presentation is distinct from player approval; final
qualification/publication identity belongs in `reference/vortex_forge.json`.

### Vortex entry and recovery (v0.15.1, superseded by v0.31)

Published `160d01cb` after the player's short/clunky/hard-to-enter feedback.
Red ability bit82/word2 `0x40000` gates everything. Y,Y,Down+Y starts from
native node12 after its contact clocks2..3, or during its keep-alive window;
plain Y retains the original string. Old pause/Dragnet entries remain.
`web_try` consumes only a queued Y and returns state46. Up/A/B/R retain
their exits; no position/time writes or new ownership bits.

Steps are 1,2,2,3: whip action57, lash56 twice, slam59. Node stays12 until
the slam parks14. K2+0xA0 arms direct entry; +0xA4 records the extra lash.
Seven contact opportunities: whip2 and authored return8, lash4/9 twice,
slam4. The return is a built area hit; native GMB payloads remain unchanged.
Native hits still exclude the same victim from area replay for two ticks.
Whip arm follow-through and lash start/end arm/yaw poses connect the
authored clips rather than resetting to guard between the lashes.

**R/Drill Kick interaction:** native evade transition `0x020B5774` selects
49 at `0x020B5894` before ordinary Y think runs. A hook at `0x020B57A0`
(kit1 entry+0x50) bypasses only that choice for owned Red Vortex with a
parked node12. The native roll finishes into landing24; the Y hook at
`0x020B69B8` (kit2 entry+0x20) resumes state46 there. Never force entry
directly from roll57: entry `0x020C2F94` itself recognizes57/58/25 and
requests Drill Kick. Direct/active-step helper preserves the queue during
those evades; landing24 is an allowed ground resume. Jump/hurt/web-hold
states cannot ground-enter through it. Standard unowned/Black behavior
was compared against the unchanged parent and passed.

**Budget:** kit1 7,096/7,936 code bytes; kit2 6,628/6,656. Shop rows move
to kit2+0x1A00 (13*32 bytes end1BA0); strength dial moves to +0x1BA0,
address `0x02156FC0`, ending1BF0. State remains +0x1C00/`0x02157020`,
used below+0x280; Both rows remain+0x1E80. The total 0x8000 reserve and
heap boundary are unchanged. Both assembly literal/native-branch validators
pass. Evidence: `work/kit/v0.15.1/qualification.json` (68 checks),
`cleanup-crash.log` (12 seeds), fixtures `vortexdirect{,late}.json` and
`vortexcancel.json`. Revised feel remains a player check.

### Player health and the top-screen HUD (v0.11.0)

**Confirmed low-HP Vitality defect (2026-10-22, published v0.30.3 source/native
disassembly):** `0x0205F40C` computes raw remaining HP into r0; r3 is clamped
to zero before the kit HP-store hook at `0x0205F420`. `k2_damage` incorrectly
reconstructs damage as old HP minus clamped r3. With a protective multiplier,
every lethal native hit therefore removes only a fraction of remaining HP,
creating a geometrically shrinking tail. This is shared player damage, not a
Conductor-specific shield. A new composition must scale the original damage
(old HP minus raw r0) and clamp only the final result. Native raw subtraction
and its stack copies remain intact. The v0.31 raw-operand correction passes
256 damage combinations (all Vitality levels, four room scales, small/ordinary/
lethal hits), preserving the native no-Vitality route. A fresh actual-DSV-copy
standstill control at1536 Q12 HP needs eleven damaging hits to die on v0.30.3;
the corrected candidate dies on its first actual damaging contact. This is a
bounded reproduction, not a claim that every native hit must deal the same HP.

- **Health calls.** Spidey's vtable (`0x0212E3F0`) +0x15C `0x0205F388` sets
  health (clamped to 0..max), +0x160 `0x0205F3F0` subtracts damage, +0x170 /
  +0x174 (`0x02060178`/`0x02060188`) read health and max; the interface vtable
  at actor+8 (`0x0212E40C`) has the same three at +0x5C/+0x60/+0x64 through
  this-8 thunks. Health and max live at stats +0x84/+0x88, outside the 0x58
  bytes a save stores: max is rebuilt after loading (where is unknown).
- **Bar.** One segment per health unit (4096): the lab save shows six. The
  blue pips under it are a second resource (unstudied; resources `OrbLP`).
- **`HUDTop_8.cbmp`** is an 8bpp CBMP: u16 249 (4bpp files: 121), u16 tile
  count, 256 colours, 16 x 28 tiles, 64-byte tiles in the same PuCrunch body.
  It holds the red and the purple (Black suit) emblem and bar, the pips and
  the combo-meter art. Colours: 25 bar shade, 26 bar and emblem, 27 emblem
  light, 28 bar light (reds `0x000D 0x0C77 0x18DA 0x253D`); 29..31 purple,
  shared by the Black bar and the combo meter.
- **Palette at run time:** the main engine's BG palette RAM, colour n at
  `0x05000000 + 2n`. Writing 25..28 there every update recolours the Red bar
  and emblem at once (lab frames `work/shop/vit-hud.png`: orange, gold,
  green; melonDS). The purple bar cannot be tinted without tinting the meter.

### Kit animation authoring

**Talon Lift native foundation (2026-10-23, v0.32.1 control; high confidence
for copied-save Test Upgrades):** purchased Black Power Launch (event 330 / bit 21,
200 XP) is grounded state 45/action 128, `spd_PowerLauncherAttack` with 14 samples.
Native GMB contact is active at samples 5..6; a Brute takes real HP loss at 5 and
enters native launch 39. Native horizontal velocity decays from 1.3 units/update;
the player remains grounded until manual B. A B buffered near recovery enters
state 15, then Y enters the ordinary air string. The live SCA ID is in the model
wrapper at `+0x1C4 + 0x78*[wrapper+0x29C]` (blend slot0/1), confirmed by the
native animator at 0x02013BF8/0x02013884 and the loaded 14-sample SCA. Motion+0x2F4
is the XBD ID, not the active SCA ID; older Hunter lab's `sca` observation must
not be interpreted as proof of clip binding. Raw baseline:
`work/talon-lift/native/result.json` and its linked native RAM/captures.

**Talon Lift candidate C (2026-10-23, v0.33.0; high confidence within focused
controls):** a private 14-sample SCA changes only the current owned Black hero's
state 45/action 128 action record, chaining into Hunter's existing animation route.
The second hook admits queued R through the native ground blocker; the native
evade transition consumes it. Parent R stays locked until recovery; candidate R
exits before contact without damage/launch. No new target/private state, movement,
hit dispatch, ownership writes or allocation is needed. 416 bytes occupy the
v0.32.1 unused tail. GMB/GAB, native launch resistance, every original motion/XBD,
geometry/texture/rooms/audio and the frozen player kit remain exact. A Brute
loses 10752 HP units at sample 5 and launches39 while the hero stays grounded.
The low coil, staggered rising hands and recovery use continuous curves and
planted feet; active in-engine SCA 5952, Black draw list and I8 residency agree.

The early native/A controls also establish a fixture pitfall: forcing only
controller state 0 does not cancel an existing action 63 hitbox. A bounded prefix
must request idle re-entry (controller+4=1), then stop before contact and preserve
actual hurt/launch states. The initial failures and corrected paired R control
remain in `work/talon-lift/`; they are not gameplay regressions. Further controls
and publication status belong in `reference/talon_lift.json`/TASKS.

**Talon final packing correction (2026-10-23, v0.33.0 D; high confidence from
whole-byte comparison):** C's inherited legacy packing reused occupied bytes
after Glob.bin. D instead inserts 23,552 bytes before the entire old gap and
shifts the subsequent sound file/tail, then uses the strict repacker. Original
gap/tail bytes survive verbatim, the cart size stays 128 MiB, and every 5,953 resource,
ARM9/ARM7 and audio payload is identical to C. Only FAT/used-size/header CRC and
file positions differ. Final D manual B/Y, early R and Hunter R controls pass
on fresh boots; unchanged payload identity justifies inheriting C mechanics,
not DeSmuME/hardware timing. This supersedes C's packing for publication.

**Manual air-follow qualification correction (2026-10-23, v0.33.0 D/F;
high confidence from paired actual HP traces):** a six-frame B tap cuts the native
jump short. C/D's initial manual control established input/animation execution,
but its air Y missed the launched Brute. Holding B from 96..128, then Y 112..118,
uses native recovery/jump/air movement and lands three real air HP losses after
the grounded rake. No custom B cancel or jump velocity is needed. The experimental
E hit-confirm B bypass is rejected as unnecessary; F keeps D's 416-byte runtime
and explicitly says **Hold B** in the menu. The final manual check requires an
additional actual HP loss, not merely state 51/action 1. Detailed traces retain
both the short-tap misses and the successful held-jump controls.

**Hunter's Return foundation (2026-10-23, published v0.31 control / v0.32 A;
high confidence for the observed path):** native Webbed Fury's transition is
`0x020B4DA0`. It checks Black bit20, state44 (or native late-string nodes),
controller+0x64 bit0x400 contact credit, the weak last-hit reference at+0x4C,
target eligibility and queued A (command5). A successful recall returns state42,
action49; native arrival enters43/action50. The observed ground dash plays
action23 after action24; action22 must not be assumed to be the only dash.
On the copied-current-save Brute control, recall moves the enemy through native
reaction45, then the kick dispatches kind0x20. Candidate A substitutes private
10/9-sample continuous pull/rake clips and changes that one target's rake contact
to native launch kind0x25. The damage argument and strength remain native.
Do not idle-lock enemy state across recall: it erases the actual yank reaction
and falsely makes the target unpullable. Raw controls are in
`work/hunters-return/native-extra.json` and the native-free/candidate traces.

**Published Hunter composition (2026-10-23, v0.32.0 B; high confidence within
the scoped controls):** six native-site adapters preserve the frozen 32 KiB kit,
including later Vortex/Vitality/boss layers. The 64-byte private state and 1660
bytes of code occupy one 4 KiB autoload extension. Ground dash contact credit,
Black bit 20 and a fresh weak target gate activation. Original native recall
eligibility remains authoritative; its interface query checks target capability
bit1, and an unavailable recall falls back only with a new neutral A, a live
target within 24 horizontal / 5 vertical units and no held Up/Down/R.

Private action 49/50 SCA routes play the 10/9-sample pull/rake. The pull's last
authored pose exactly equals the rake's first pose across every channel. The
full native recall contact changes kind 0x20 to 0x25 only for the owned Black
hero, matching active target, motion/config identity and state 43 / action 50.
Attack strength and native HP damage stay unchanged. Physical fallback uses
the native ground-string entry/node 5 and private rake resources; velocity is
bounded to 2 units/update, stops at 6-unit reach, and never writes position/time.
Native hitboxes and actual ReceiveHit decide contact. Native R exits through
the existing evade queue; hurt/form/room/owner change, death, stale registry or
recycled motion/config clears private state. No target is held after interruption.

Twelve Conductor follow-ups cause 12 real HP drops with no launch conversion;
player healing and a cleared boss flag 147 are disposable fixtures. A separate
eligible Brute control proves native recall/rake/launch. Mirrored native refusal
correctly uses physical pursuit. The Terminal qualification observes two enemy
species, not an assumed third actor: 218 crowded samples bind hero I8 and both
enemy I4 materials. All other room/audio/motion/XBD resources stay exact.

`hunters_return_art.py` reshapes the already-published Black list in bind space,
using continuous torso volume and radial arm envelopes around unchanged pivots.
It preserves every UV/matrix slot, 516 triangles, atlas, rig/SBC, Red GPU stream
and the existing selector footer/literals. Only the bounding box and Black
vertex coordinates change. Live skill captures select the actual Black list
and bind 128x128 I8. Recipe, scope, raw evidence and limits belong in
`reference/hunters_return.json`; player aesthetics and DeSmuME pacing remain open.

**Hunter isolation/owner correction (2026-10-23, v0.32.1 A; high confidence from
native disassembly and ARM regressions, published with scoped native controls):**
v0.32's isolated victim test did not establish target-only behavior. The native
dispatcher loops at 0x020784D4 with the same info at SP+0x8C; changing its kind
and the nested contact kind without restoration leaks the launch to later
victims. Its saved argument copies SP+0x80..0x88 are not read after entry and
are discarded at return. A records originals there per victim, preserves native
ReceiveHit/credit with the converted kind, then restores at 0x0207866C before the
next iteration. Skipped victims retain a pointer rather than the 0x20 marker;
nested dispatch uses independent call frames. The old post-hit observer stays.

The v0.32 update also returned on a different current-player address before
clearing private state; the 120-update timeout could never advance. Real room
captures show actor replacement. A first recognizes the native player type and
clears a departed owner without reading its old address, then runs the old
guarded update. The 324-byte adapter fits the previous image's zero tail: no new
autoload allocation, asset/motion/purchase/save changes or old-generator edits.
These findings supersede the earlier multi-victim/reallocated-player cleanup
assumptions; preserve v0.32 and its limited evidence as published. Canonical/
normal/published v0.32.1 match. The native reload control fails on the parent and
passes with cleanup plus another real button-driven activation. Native crowd
control preserves normal bystander knockdown; this alignment also passes on the
parent, so the target-first multi-victim regression is specifically the ARM
proof. Detailed fixtures and limits are in `reference/hunters_return_fix.json`.

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
v0.13.0 clips: `web_heave` (action 49's 10 samples: rip both lines back
into a back hop), `web_whip` (57, 17: uncoil into a backhand lash at samples
2-3, a full hopping turn), `web_lash` (56, 12: a hop with a lash from each
arm at 4 and 9), `web_slam` (59, 19: overhead two-handed slam at 4-5; the
native action carries him about 12 units forward). In-game sheets:
`work/kit/web5-c.png`, `web5-d.png`.

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
  `0x02117F74` writes RAM `0x0213B834` (16-byte rows: map CBMP, area name string).
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
- **Area rows** at `0x0213B840` (ARM9 data, 16 bytes per area 0..5): screen
  resource, area name string (379 Downtown, 380 Hive, 381 Pier, 382
  Residential, 383 Sewer: printed under the map; read as a "map variable"
  before 2026-10-12), room-list pointer, entry count. Sewer row 2: list
  `0x0211FE38`, 18 entries. Static init `0x02117F74` writes screen and name
  from literals. **Row 5 is a spare area**: screen `GenericBGBot_4.cbmp`
  (0x320), name string 20 (' '), no list (literals `0x0211802C`/`0x02118030`,
  list/count words `0x0213B898`/`9C`); native proto01 carries area 5. The
  chapter owns it since v0.11.0 ("Chapter map" below).
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
- **Descriptor +0x28..+0x48** (area, map rectangle endpoints, world bounds) feed
  the room-detail view (`0x020E56F8`, with descriptor +0x4C screen; the x3
  zoom of the touch screen) unless the area's map is locked. `0x020E361C`
  answers "locked" from one map-item event per area (0x17B Pier, 0x17C
  Residential, 0x17D Sewer, 0x179 Downtown, 0x17A Hive: ability bits 68..72)
  and for every other area; a locked area shows `MMLocked.cbmp` (resource
  0x4FE, "Detailed Mini-Map unavailable"). v0.7.0..v0.10.0 set area 2 on
  chapter rooms and kept the source room's other values; v0.11.0 sets 5.
- **Areas above 4 have no map natively:** `0x020E3480` refuses the map views
  (modes 6..8) and `0x020E2194` opens the touch screen on the objectives page
  when the room's area is >= 5 (`cmp r0,#5` at `0x020E34B8`, `0x020E21CC`);
  `0x020E1558` ("nothing visited in this area") returns early for areas >= 5
  and the world view (x2 zoom, loop `0x020E6CD8`) draws areas 0..4 only.
- **Chapter diagram:** 14 rooms drawn as a subway diagram in the empty
  lower-left cells (cols 3..12, rows 15..18) of MMSewer.cbmp, one free slot
  per room; list relocated to the chapter block with 18 + 14 entries
  (patches row +8/+0xC). Visited chapter rooms appear, the current one is
  highlighted (frames: `build/boot-tests/nest-c-*/ml-visit-*`). Superseded in
  v0.11.0 by the chapter's own screen; the Sewer screen and list are native
  again.

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

- **More flags.** Save slot has a 16-byte padded "SpidermanWoS" header,
  then a 4-byte checksum and the 0x58 block at slot +20 (flags at block
  +0x1C, mission byte +0x48). 21 distinct slots in
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
  Natively only ops 0, 2, 4 occur (`==`, unsigned `<`, unsigned `>`;
  confirmed directly in the handler during the 2026-10-13 boss research).
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
- **0x15 operand:** u16 duration in seconds (legacy helper keyword `frames`),
  message id, lookup flag0, continuation group0. Correction measured during
  Crane navigation,2026-10-15: handler0x02039B0C multiplies the u16 by30 at
  0x02039BA8 and stores the native-update countdown.180 means minutes, not180
  frames; five seconds clears to the map while play continues. Zero retains
  native/default behaviour and has left authored hints covering the map until
  the next room. Native update/clear:0x020E0144..0x020E01A4.
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
  the back one is node `link` (a node with only an empty back has link 0).
  Each list is the solid leaf of exactly one node in every room.
- **Lists are the faces of a solid leaf** (2026-10-12): every entry names a
  node above the leaf (26,105 of 26,105), the planes that bound its cell and
  are not made redundant by a tighter one; front-side ancestors come first,
  deepest first, then back-side ones. The second u16 is the face's **surface
  value**. The node u16 at +8 (0 in 57%, 2, 3, 8, 24 and stray values such as
  15668) can be written as 0 ("Room compiler").
- **Surface values**, measured in the two debug rooms built for them
  (Test_Surfaces01/02, rooms 71/72: 80-unit cells at x 100, 200, 300, 500,
  600, 700, 800 whose floor, ceiling, walls above y 20 and back wall carry
  one value; `work/midnight-line/scratch/surface_exp.py`, lab save with the
  player's abilities): **10** ordinary (87% of all entries; every face of
  Test_Combat01; clings and crawls), **9** clings and crawls, **0** clings
  only with the ichor story abilities (bits 0/1 cleared: he slides off; 2,895
  faces in the game: the Ichor Crawl gating), **1, 2, 6** never cling, **7**
  hurts (4,096 and a knock-back from floor or wall). 4 and 5 (10 faces in
  real rooms) are untested. What separates 1/2/6 and 9/10 (sound, web
  attachment?) is unknown.
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
  2026-10-12: a jump beside a wall while holding toward it runs up it (state
  9) to the ceiling and hangs there (state 7 again, position = ceiling - 5);
  7 is also the ceiling crawl. States 8 and 13 were seen on another wall,
  67/74/75/77/79 after touching a hurting surface.

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

**Native Span low-neck driver (2026-10-15).** The right exit of Hive_Map05 /
ML_NestSpan has a12-unit opening at x0 (BSP empty at y11.75, solid at12;
floor0). Standing/attacking reached x-3.5 without entering it. The old masher
timed out three times on the0.16.2 visual candidate. Paired0.16.1/current
controls also failed with plain walking, including with the crew parked away;
Right+Down+tapR passed the full Span/Hollow/Gallery/Shrine route on both
builds. `midnight_walk` now keeps its existing traversal crew fixture and uses
native duck/roll inputs at this neck. No ROM or player save changes. Native
input improvements require a baseline control; do not alter game geometry or
mark a release broken solely from an incapable driver. Original failures and
paired controls: `work/crane-row/repair/`, `walk-span-driver-roll-*` in
`work/midnight-line/`. Rendering candidates must finish their full port/corner
review before launching expensive gameplay gates.

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

### Chapter map, closed hatches and the strength dial (v0.11.0)

Player 2026-10-11: the diagram on the Sewer screen did not show how the rooms
connect; hatches could be crawled into and led nowhere; the Nest's enemies
were far above the sewer ones.

- **Own map screen** (`midnight_chapter.map_layout`, `MAP_ROOMS`, `MAP_LINKS`).
  Chapter rooms carry area 5; row 5 gets a new screen `zz_MMMidnight.cbmp`, an
  appended title string "Midnight Line" and a room list in the chapter block
  (patches: row +8/+0xC, the two literals, `cmp r0,#5` -> `#6` at
  `0x020E21CC`/`0x020E34B8`, `mov r0,#1` -> `#0` at `0x020E3724`). Without the
  three code patches the touch screen stayed on the objectives page and the
  Mini-Map button did nothing (lab, candidate `ec02ef05`).
- **Screen.** The Sewer screen's frame and palettes with the panel (cells
  3..27 x 3..18, 200 x 128 pixels) cleared and the border cells the Sewer
  rooms reached into restored from plain neighbours. Rooms are outlined
  rectangles at about 1 pixel per 6..8 units; every link strip leaves both
  rooms on the side `room_doors.door_kind` reports (test). A tile has one
  palette, so each cell gets a palette in which every room it shows has a
  5-colour slot; a room spanning palettes has one list entry per palette
  (19 entries for 15 rooms; the native Sewer_Map07 has two). Slots: the free
  ones of palettes 0..3 and 6..10 (those no kept cell uses). **Palettes
  13..15 cannot hold rooms:** with every room marked visited, a room in 14
  drew magenta, one in 15 black and a visited one in 13 dark grey; it only
  looked right while it was the current room (candidates `dfeb84ea`,
  `0fbb62a3`; `scratch/map_view.py ROM NAME ROOM --visited`).
- **The door pairs do not fit one flat plan.** The Platform alcove enters the
  Stairs' right end going left, the Gate rises into the Stairs' left end, and
  the Nest hangs from the Platform's grate: at true scale the Stairs would
  have to be on both sides of the Platform. The Gate <-> Stairs grate pair is
  therefore two dotted arrows, like the native stubs to other areas.
- **What the views show now** (lab `4f387a21`, touch on the buttons): x1 the
  chapter screen with its title, visited rooms, the current one lit; x2 the
  world view (areas 0..4, no "you are here" for area 5); x3 the *source
  room's* detailed map (Sewer_Map01, Hive_Map05 ...), which v0.10.0 showed as
  "unavailable" in the lab save. The Yard's detail screen is `MMPlaceholder`.
  A chapter line shown on entry covers the panel until the room changes.
- **Hatches.** Sewer_Map01's first 'Door (Sewer Grate Ceiling)' (kind 0x09 at
  (0, 0.8)) and Sewer_Map03's 'Door (Sewer Grate Floor) 1' at (435, 165.8)
  with its type-5 zone 'Trigger (Main|Grate_Open)' are the dead hatches.
  `close_hatch` locks the grate from the room init (`0x0F`, as
  `Lock_Grate`) and moves the zone away. Lab `4f387a21`
  (`scratch/hatch_exp.py entry-wall | platform-cling`): he no longer gets
  above either grate (before: crawled in and came back).
- **Strength dial** values and lab numbers: "Second kit block". Research
  save, stable `a928843c`: chapter sewer rooms 22k..37k health and 4,096 per
  hit; Nest 74k..106k and 8,192..9,554; Yard gang 52k (one 131k) and 2,187.
  `scratch/damage_probe.py ROM ROOM [--fight] [--bits2 B]` logs both.
- **The door tour can lose Spidey.** On `dfeb84ea` `midnight_line.py tour`
  stopped after step 17 and, in a second run, after step 19 with no error:
  `player_trace.sample` no longer found him after a room change while the
  game kept running (captured frames kept changing). Resume with `tour
  --start N`; the walk routes are the real gate.
- **`COLLISION`** (`midnight_chapter`): a room may ship its own collision file
  (appended last as `zz_<room>.bsp`; collision files need no alignment).
  Empty in the release.

### Room compiler (v0.12.0)

A room built from nothing is three files and an object script, all made from
one plan. Tools: `tools/nitro_build.py` (file writers), `tools/room_compiler.py`
(plan -> model, textures, collision), `tools/room_author.py` (camera, anchor
points), `tools/midnight_rooms.py` (the shipped plans and their scripts);
tests `test_nitro_build`, `test_room_compiler`, `test_room_author`,
`test_midnight_rooms`. Lab scripts and contact sheets: `work/rooms/`.

- **Writers checked against the game's own files.** `dictionary_bytes` builds
  a Nitro name dictionary; the search tree is the standard insertion with the
  nodes then numbered in preorder, left child first (bit n of a name = byte
  n >> 3, bit n & 7; root bit 127). `texture_archive` lays the pools out as
  natives do (plain, 4x4-compressed, its index words, palettes); `room_model`
  writes a one-node model: node, SBC (`26 00 00 00 00 02 00 01 0B`, a
  `04 mat 05 shape` pair per shape, `2B 01`), materials with their
  texture/palette name dictionaries, shapes. Rebuilding from parsed parts is
  byte-identical for 259 of 272 texture archives (the rest share data or use
  4-colour palettes) and all 69 one-node room models but BoxRoom.
- **Model conventions (native).** One shape per material, one texture per
  material (bound by name at load: palette `<texture>_pl`). Material record
  44 bytes: polygon attribute `0x001F0080` (front faces only, no light),
  diffuse `0xE739` with the vertex-colour bit, repeat on both axes. A quad is
  counter-clockwise for its viewer (e1 x e2 points at him); a face wound the
  other way is culled and shows black. Stream commands used: `0x40` quads,
  `0x20` colour, `0x22` texture coordinate (s | t << 16, 1/16 texel, origin
  top left), `0x23` vertex, `0x41`. Vertex scale 64 holds +-512 units.
  x right, y up, the camera looks from +z; the play space is |z| < 25.
- **Plan** (`room_compiler.Room`): `bounds` of the interior, `Solid` boxes
  with a collision surface value and looks per face, back-wall `Panel`s,
  scenery quads/boxes (drawn only). Everything outside the bounds is solid.
  The same boxes give the collision tree (`compile_boxes`) and the faces: top,
  underside and sides where a solid meets empty space, a face toward the
  camera, a back wall behind empty space. `depth` below 25 makes a solid
  stand free (its body ends at that z and the floor it stands on continues in
  front): at full depth a tall block is a black slab across the foreground.
  `hidden` solids collide and are never drawn (an outdoor room's ceiling).
  Texture coordinates are anchored to the world, so repeats line up across
  quads; long faces are cut to stay inside +-2048 texels.
- **Fills (v0.13.0).** The plan is 2-D, so where a free-standing solid met
  a deeper one sideways (a catwalk end at a wall) nothing was drawn between
  its front and z 25: a pitch black gap (the player's "black roofs"). The
  deeper solid's side goes on there now ('left_fill' / 'right_fill'), and
  its underside where it sits on a shallower one ('under_fill'); fills are
  not walls for anchor points.
- **Far backdrops (v0.13.0).** A skyline on the back wall (z -25) reads as
  a painting. The native Pier keeps its skyline quads at z -171 (about 90
  units a tile, 111 tall; a floor plane even reaches z -202), so they drift
  slowly as Spidey moves. `Panel(..., look=None)` leaves the back wall open
  and `rcm.backdrop(look, x0, x1, y0, y1, tile, sky, ground)` puts the
  picture there as scenery, every second tile mirrored, its top fifth
  folded on above (a mirrored upper half showed upside-down towers) and its
  bottom row stretched below (from a high platform the fence no longer
  covered the picture's lower edge). View arithmetic: 58 units wide at z 0
  and 82 at z -25 put the camera about 60.4 units in front of z 0, so at
  z -170 it sees 221 x 166 units and a point there moves 0.26 times as far
  on screen as one at z 0. A model is at most 511 units wide (vertex scale
  64; the bounding box is s16): six 72-unit tiles fit behind the Switchyard.
- **Textures.** `borrow(archive, name)` copies a native texture and palette
  as they are (296 distinct room textures; sheets by `work/rooms/tex_sheet.py`
  and `tex_big.py`). `paint` makes 16- or 256-colour textures from pixels
  (formats 3 and 4; tested, not used in a shipped room). Appended models and
  texture archives must start on a word: `midnight_chapter.aligned` inserts
  padding resources (the strings and the map screen are not word multiples,
  so one fixed pad was only right by luck).
- **Camera regions** live in the object file: record 0, section 4. One u16
  offset per polygon, one u8 point count per polygon, zero padding to a word,
  then 20-byte points (x, y, three zero words). 67 native rooms have one to
  three polygons; the debug rooms have none (free camera). The camera object
  (vtable `0x02130684`; found at `0x022AD9D4` in the Refuge) holds its
  look-at point at +0xC: Spidey's x and y + 4 clamped into the polygon, z 60;
  +0x50 points at the polygon copy, +0x54 is its point count. Native rule for
  a box room: the room narrowed by 20 units left and right, full height. The
  view is about 58 x 43.5 units at z 0 and 82 x 62 at the back wall. The
  descriptor's bounds at +0x3C..+0x48 do **not** steer the camera (changing
  them changed nothing).
  **Parser correction (2026-10-23, high confidence; v0.32.1 tooling source
  tests):** padded header size alone cannot distinguish 3/4, 7/8 or 11/12
  regions. `room_author.camera` resolves the count using all polygon offsets,
  zero padding and exact section length. Counts 1..15 round-trip; corrupt
  offsets/padding/lengths are rejected. Native camera bytes are unchanged.
- **Anchor points** are record 0, section 3: 20-byte points (x, y, z, 0,
  kind) in entity-batch framing. Kinds as the training room lays them out:
  1 on a floor (2 above it, every 20 units), 2 beside a left wall, 3 beside a
  right wall, 4 under a ceiling, 5 in open air. **Enemy spawners place their
  enemies on them: a room without any spawns nobody** (the first Switchyard;
  the native debug geometry behaved the same, so it was not the compiled
  files). `plan_anchors` derives them from the plan; floor points only on low
  floors, because a gang put on a platform stays there.
- **Spawners** (lab, authored rooms). A spawner starts once Spidey stands
  well inside its zone box (6 units inside was not enough, 10 was). Byte +24
  = 1 with +25 = an event group (1-based): that group runs when the wave is
  beaten, with +23 = 0 or 2 alike; chained that way three spawners ran one
  after another (Pier `0x08`, Sewer `0x0E`, Residential `0x0C`) and the last
  group set a flag. Sewer `0x0F` ("Medium Red Suit", byte +26 = 1) spawned
  nobody in the lab save. A spawner batch activated while Spidey is already
  inside its zone starts about 95 frames later. What +23 and +26 select is
  unknown. Record 1 of the empty debug room has one empty batch (AG 0, live
  from the start), so every appended batch must be started by the init group.
- **Movement numbers** (lab, flat floor): a tapped B rises 10.3 units, B
  held 25 frames 27.0; B again in the air starts the native web swing
  (state 26), which carried him 66 units. After a jump into a catwalk's edge
  he hung in state 16 (probably a ledge grab; not studied).
- **Harness limits.** `player_trace.sample` can lose Spidey after the third
  room change of one run (the game keeps running): keep routes to two or
  three doors. The mash fixture cannot reach fliers or enemies on blocks:
  `fixtures(chase=True)` puts Spidey beside the nearest enemy instead (moving
  enemies breaks wave counting). The enemy list can hold a half-freed actor
  (health 1, no state, wild coordinates): chasing one threw Spidey out of
  the level, so the fixture skips those. Runs started in the same second
  play out identically (the fights follow the clock): start repeats a few
  seconds apart to sample different fights.

### The Substation (v0.12.0)

Three authored rooms behind a door in the Yard's left wall (x -264.75 at
floor height; a copy of Sewer_Map13's left door stands there). Source of
their descriptor and object file: the empty debug room Test_Surfaces01
(`midnight_rooms.SOURCE`); Spidey's entity stays in record 0.

- **Rooms.** 91 `ML_Switchyard`: outdoor yard at dusk, 260 x 84 (Pier
  skyline trio, brick and window facades, loading dock, two stacked
  containers, a transformer, a gantry at 42, pylons and wires as scenery);
  Pier gang spawner, two barrels and a trash can. 92 `ML_RelayHall`: 130 x
  140 machine hall whose outer walls have surface value 1 (no cling); five
  catwalks 18 apart and a ledge at 110 by the upper left door; two batches of
  `Hazard_Electric` objects (proto01's, a point every 10 units, 1 above the
  catwalk) take turns: 90 frames live, 50 frames with nothing live. 93
  `ML_Roof`: 214 x 90 roof at night (Residential skyline, every second tile
  mirrored), two vent blocks, a 34-unit passage to the door; three waves.
- **Doors** (`midnight_rooms.Door`): a doorway is a 10-unit alcove under a
  solid; the exit box is centred 3.5 units behind the wall and 12 wide (it
  reaches 2.5 units into the doorway), the arrival point 12 units in front
  of the wall (10 in the Yard). In a doorway Spidey stopped 4.4 to 4.65 units
  from the wall, not 3.5: a box reaching only 1.5 overlapped him by 0.6 and
  one walk of about a dozen never fired (candidate `f8761be4`). The Yard's
  native metal barrel stood 11 units from its left wall and pushed an
  arriving Spidey 2 units back toward the door: it moves to x -165. Exits
  are record-0 groups 1.. in door order.
- **Waves** (`midnight_rooms.stage`): each spawner names a guard group
  (`Wave_2`, `Wave_3`, `Waves_Clear`) that runs its go group once: a scratch
  byte (0x12A..0x12C, cleared by the init group) is tested with `== 0` and
  set by the go group. A go group starts the next spawner batch 45 frames
  later and calls the next guard again after 5,400 frames, so a wave also
  starts 90 s after the one before. Reason: on `f8761be4` one roof fight of
  about a dozen stopped after the second wave (five enemies instead of the
  usual eight to twelve, the last one beaten against the left wall, nothing
  for the next 4,000 frames; cause not found). The clear step has no timer.
- **Flags.** Visited: room 91 = 267 (the native rule), rooms 92.. take 165
  downwards (`midnight_chapter.visited`); `LOCAL_FLAGS` now ends at 149 and
  150 = `substation_cleared`. The map's visited test `add r5, r7, #0xB0` at
  `0x020E1878` becomes a `bl` to a 7-instruction stub in the chapter block
  that reads rooms 92.. from a byte table after it (`visited_stub`).
- **Map.** The three rooms sit in the panel's lower left; the Yard's left
  door and the Switchyard's right door are a pair of arrows
  (`MAP_DOOR_ARROWS`), like the Gate/Stairs shaft.
- **Lab** (release ROM `0ede0422`): routes `substation-in`, `-climb`, `-roof`,
  `-out` of `tools/midnight_walk.py` (real doors both ways, a real held jump
  onto the first catwalk, a live catwalk shocks, all three waves beaten sets
  flag 150). The other hops of the climb are placements: a human climb is
  expected from the jump numbers, not scripted. Wave experiments:
  `work/rooms/wave_exp.py` (`midnight_rooms.LAB` switches, never set in a
  build).
- **v0.13.0** (player, 2026-10-13: "super impressed with the original
  artwork"; the background "looked like it was a painting rather than
  real", "some roofs were pure pitch black", "the enemies were too weak
  though is my main gripe"). Strength dial: Switchyard 144 / 90, Relay Hall
  160 / 96, Roof 192 / 104 (health 2.25, 2.5, 3 times native; damage to
  Spidey 1.4, 1.5, 1.6). Both skylines are far backdrops behind an open
  back wall (the roof's city lights sit just above the parapet: lower, they
  hid behind it and the sky looked black). The black gaps at catwalk ends
  and doorway corners are filled; doorway ceilings use concrete or steel
  instead of the cutaway texture; ceilings are lit 0.72 and camera-facing
  faces 0.34 (`midnight_rooms.LIT`); the Relay Hall's door walls show the
  cutaway pattern instead of a flat dark slab; the dock's side is concrete
  with a warning stripe on its edge. Sheets: `work/rooms/sub13-*.png`.
- **Lab artifact, not a hole:** the first placement in the roof at x 20
  drops Spidey out of the level in v0.12.0 and v0.13.0 alike; the compiled
  floor has no gap (`solid_at` along the whole width) and the walks cross it.
- **Open.** Player verdict on strength and looks; whether the arcs read well and
  the 50-frame rest is fair. Detailed maps replace the debug placeholder in v0.15.0.

### Substation checkpoint and detailed maps (v0.15.0)

Implemented and agent-tested; player verdict pending. Sources
`tools/midnight_rooms.py`, `midnight_chapter.py`, `room_minimap.py`;
`tests/test_room_minimap.py` and room tests preserve native unknown bytes.

- **Service Bay:** room 95, visited flag 162, no new persistent room flag.
  The Switchyard's upper-left fire escape at y33 has a left doorway (exit/
  spawn 3); Bay right doorway is exit/spawn 1. Its matching wall opens only
  y33..49. Normal jump from the existing y10 dock reaches the y33 ledge;
  `walk-substation-save` crosses both real doors with story bits 0..4 only.
  The bay has no gangs, waves or hazards, and uses already-seen textures.
- **Native checkpoint:** copy the type-10, 16-byte SavePoint entity from
  `Sewer_Save04` record 0, preserving bytes beyond XYZ; activate its appended
  batch from record-0 init. Sphere at (40,7). **Continue uses the envelope
  spawn table, overriding the player entity's placement**: preserve the
  existing spawn-0 unknown bytes and change XYZ/facing to (40,2,0), right.
  Moving only the player entity left him at x0, too far to save. Native
  Save/Yes -> captured SRAM -> fresh Continue restores room 95 and flag162
  with copied batteries (`chapter-save-Versioned-ML_ServiceBay-*.json`).
- **Detailed map fields:** descriptor +2C/+30 = map top-left, +34/+38 =
  bottom-right endpoints, **not width/height**. `0x02084ACC` subtracts them;
  +3C/+40 = world (xmin,ymax), +44/+48 = (xmax,ymin), all Q12. Descriptor
  +4C selects the private detailed CBMP. The five authored rooms fit their
  collision bounds into pixels (30,30)..(218,146), preserving aspect ratio.
  `room_minimap.Projection` is shared by raster and descriptor generation.
- **CBMP preservation:** borrow the native MMSewer frame, keep existing tiles,
  screen cells outside the interior and unknown/trailing bytes. Append 400
  panel tiles using unused palette 1; only its first ten colours change.
  Raster shows solid platforms, door markers, electric hazard positions,
  boss core locations and save sphere. Landmarks are static; native player
  icon moves through the projection. Native chapter overview keeps its own
  visited/current colours and gains the bay's save icon and branch arrows.
- **Map evidence:** `work/midnight-line/detailmap-ML_*.json` records RAM
  positions/projected pixels; corresponding `detailmap-*` emulator captures
  show correct horizontal and vertical orientation on all four combat rooms.
  Bay captures `mapview-service-maps2`; save/walk captures also show its menu.
  Marking visited in disposable RAM avoids first-visit dialogue consuming
  map touch input. Warp to spawn 1 for Roof/Signal, since spawn 0 can put
  Spidey into the new boss doorway. These are lab fixtures only.

#### Roof wave reliability fix

`work/midnight-line/roof-observe-obs1/2/3.json` traces
three complete native fights; the scripts' three guarded callbacks all run.
The alleged v0.14.0 stall (`walk-substation-roof-25fc42b6.json`) actually
left room 93 for 94: the lab chase placed Spidey across the new left exit.
Older `-u4` reached x8878/y9000 after chasing a freed actor; this also was
a fixture failure. The older `f8761be4` report stayed at x3.5 with no traced
enemy; its exact cause remains unproven, since spawner RAM was not captured.

`midnight_walk.Walker.fixtures` validates the enemy motion back-pointer and
rejects out-of-room Roof chase targets. Actual door use remains unmodified;
native wave timers/guards remain, with no timed automatic victory. After a
lab placement, a normal B hop releases stale native movement stances.

**2026-10-14 fixture correction:** the former Roof gather driver stalled
three times on art candidate `5b0d6f55`: wave2 active cost8192, two live
HP1 actors, repeated below-melee-range positions around y-25. The gathering
helper repeatedly rewrote those fighters' roots. Their native weak references
were live, so the zero-HP cleanup below correctly did not declare them dead.
Paired controls leaving enemy movement native clear the waves on both this
candidate and original0.16.0 `39fcf89e`. The candidate then drifted through
the Signal door during its post-win wait (last kill at x9.7), exposing the
old x12 chase limit's insufficient margin. The corrected route uses chase,
never gather, clamps Roof placement to x24..176/y5..65, stops combat fixtures
immediately on the earned clear flag and settles at the explicit lab centre
before its wait/real right-door exit. No ROM/script/AI change. Existing
route/placement/chase tests cover the correction. Failed/paired evidence:
`work/crane-row/polish/driver-evidence/` and `midnight-gather-failures.json`;
final all-route qualification and baseline control live alongside them.

**A separate, actual spawner stall was then reproduced:**
`walk-substation-roof-gather-b515ab99-aborted-ram.bin` stayed in room93 with
wave2's cumulative cost32768, active cost4096 and one non-null weak reference
to a NormalEnemy at HP0. Native completion still waited for active0. This
corrects the earlier interpretation that all stalls were fixture exits.
The old enemy was unhittable, and its weak reference never became null in
the remaining run. Player reproduction and prevalence remain unconfirmed.

**v0.15.0 fix:** `tools/roof_waves.py`, 72-byte ARM router at chapter offset
E80, hooks the non-null branch0x0204C2C8 (old1A00001C). With current room93,
NormalEnemy vtable0x021301D0 and signed HP<=0 at actor+44, take the existing
native null-reference cleanup0x0204C2CC. It subtracts active cost and removes
that list node, retaining cumulative kill credit. It neither destroys nor
modifies the enemy actor. Live actors, other classes, other rooms and null
references keep their native paths. A last defeated enemy can therefore
start the next wave before its corpse finishes fading. The usual 45-frame
inter-wave delay and guarded scripts remain. No timers declare victory.

`tests/test_roof_waves.py` executes the actual ARM loads/comparisons/branches
against guarded memory: zero/negative HP, positive HP, wrong room/class,
null stats, original conditional hook. Same gather stress passes on fixed
ROM `f0e53056`; `walk-substation-roof-fixed-f0e53056.json`. Final living-crew
control, full walks, boss flow and native save checks use that exact ROM.
The helper occupies 72 of the 128 bytes before the existing core adapter;
the room-table builder validates both budgets and the original patch word.
Table payload is3584 bytes: 128 spare before the Roof helper, 56 between it
and the core adapter, 40 after the latter. Another room likely needs a
block-budget change. The chapter's runtime base is0x02157420; physical ARM9
bytes live at `tasm_kit.SOURCE + RESERVE`, via autoload, not runtime-base
minus0x02000000. Current map/control/save/boss evidence is ROM `f0e53056`.

Boss lab lesson: a driver on a core shelf at head y25 swings above its
ground core at y8 forever. `midnight_boss_lab.attack_core` now uses normal
Left/Right to walk off the shelf before attacking, instead of inferring a
boss failure from a ground-only input loop. Original failed run is in
`service-qualified-leech.log`; corrected victory/revisit in
`service-qualified-leech2.log`. No actor weakening or gameplay teleport.

Confirmed native `EnemySpawner`: primary vtable 0x0212BDA4, interface +8
0x0212BDC0, allocation 0x58 bytes, constructor0x0204C118 and update0x0204C27C.
+18 points at wave parameters (first words total cost / simultaneous cost),
+28/+2C center, +30/+34 half-width/half-height, +38 cumulative charged cost,
+54 active cost, +4C sentinel for a linked list of weak enemy references.
List nodes carry next/+4 weak reference/+C cost. These are **spawn costs,
not enemy count or HP**. Native update removes null weak refs and subtracts
their cost; completion0x0204C3F4 requires cumulative >= target and active0,
then calls script action0x0203C948 and removes the spawner. A non-null escape
test0x0204A478 can subtract from both costs. Retained allocations after room
exit are not proof of an active spawner. Disassembly/evidence:
`work/midnight-line/spawner-{update,tail,load}.txt`, `roof-analysis1.txt`.

### Script boss research (2026-10-12)

Goal: a boss that is not one of the game's own, built from room script
(a machine or arena that attacks), ahead of any new character boss.

- **Pieces that exist** (object type 14, kind at +22, event group run on
  destruction at +23; counts over all rooms): hazards `0x11` Hazard_Electric
  (12, Sewer_Map03) and `0x13` Hazard_Fire (proto01); `0x31` Bomb_Symbiote
  (Downtown_Map06, Pier_Map01 x3, Residential_Map06, Sewer_Map11); `0x08`
  Crane (Pier_Map06) and `0x06` Boss_Floor (Residential_Map08), both
  unstudied; liftables `0x16..0x1A` (boiler, copier, dumpster, file cabinet,
  fridge); smashables `0x1F` box, `0x23` metal barrel, `0x21` ichor blob,
  `0x27` trash can, `0x29` water cooler and more; ichor gates and walls
  `0x0A..0x10`; switches `0x2A..0x2C`. Unused effect resources: `Explosion2`,
  `Explosion_Burst`, `Explosion_Cloud`, `Tnt`, `ExpUnstable`, `PumpBomb`,
  `Homing`, `ElecShock`, `ElectricLg`, `Fire`, `Smoke0`, `Bamf`, `WebBrake`.
- **Script verbs proven in the chapter:** activate one entity or a batch
  after a delay (`0x1C`), deactivate (`0x03`), compare a variable and branch
  (`0x1D`), set/increment (`0x26`/`0x25`), animate (`0x01`), lock a door or
  raise a gate (`0x0F`), sound (`0x22`), message (`0x15`), on-screen timer
  (`0x23`) with a TimerWatcher (type 11; Hive_Map01/08/09/10), spawners with
  a "wave dead" group (+25), touch triggers (type 7) and **zone triggers
  (type 5, 24 bytes: width, height, 0x0A, group on entering, group on
  leaving)**.
- **How the native arena uses them** (Downtown_Map14, dump in
  `work/midnight-line/scratch/Downtown_Map14.txt`): three zones set scratch
  bytes 0x127..0x129 while Spidey stands on the left, middle or right
  platform (read by the boss's AI, not by the script: "timed platforms" was
  a misreading); the mini-boss character's +23 names `Reward_Spawn`; the two
  red floors increment flags when they break; delays chain groups (`Trigger
  Delete` -> 2 frames -> `Ambush` -> `Gate_Spawn`).
- **Plan for a script boss.** *Health:* destructible cores (objects with a
  destruction group) counted in a scratch byte; when the count reaches N the
  reward group runs. *Attacks:* batches of hazards switched on and off by two
  groups that call each other through delays, the delay shortening by phase
  (`0x1D` on the core count); warn with a short on/off flicker and a sound.
  *Adds:* spawner batches per phase. *Arena:* zone triggers to punish
  camping, liftables to throw at cores, a breaker to cut power for a few
  seconds. *Bar:* none without a boss actor; show "2 of 3" lines instead.
- **Lab: a script loop switches hazards on and off** (2026-10-12,
  `scratch/boss_loop_build.py NAME --period N`, `boss_loop_walk.py`; ROMs
  `build/dev-kit/loop90|loop300`). The Platform gets two groups: `Loop_On` =
  activate the `Electricity` batch, then after N frames run `Loop_Off`;
  `Loop_Off` = deactivate it (`0x03`), then after N frames run `Loop_On`; the
  init starts `Loop_On`. With the track power cut (so natively the rails are
  dead): control without the loop, 24 walks over the rails, never hurt;
  native power on, hurt on every walk; loop of 300 frames, hurt at about
  frame 110 and 1330 and not at 643, 969 and 1654 (one on/off cycle is 600
  frames); loop of 90, not hurt at 81..143, hurt at 163. So a delayed group
  call from another group works, a deactivated hazard batch can be activated
  again, and the loop was still cycling after 1,600 frames. The exact phase
  was not pinned down (the walk fixture is crude: after a shock Spidey lies
  in state 75 for a long time, and a teleport keeps that state). A hazard
  only hurts on contact while moving: standing still on a live rail after a
  teleport did nothing.
- **Proven since (v0.12.0, "Room compiler" and "The Substation"):** hazard
  batches cycling in an authored room (two batches of 8 and 6 arcs), waves
  chained through a spawner's beaten-group, a flag set by the last one.
- **Still to prove (lab, one test room):** 1) which attacks damage which
  smashable kinds and their health; 2) what Bomb_Symbiote, Crane and
  Boss_Floor do; 3) whether a beaten spawner can be re-armed without leaving
  the room; 4) a warning before a batch goes live (a short flicker or a
  sound); 5) a smashable's destruction group (+23) in an authored batch.
- **A new character boss** stays research: enemy models are separate rigs
  (`m6`, `brt`, `bzkr`, `hLpr` ...), the animation tools are proven on
  Spidey's 37 bones only, and the mini-boss AI is unmapped (no NormalEnemy
  vtable; health pairs near `0x022AD460`). Open question for the "rival"
  idea: whether an enemy actor can bind `spd.nsbmd`.

### New Midnight Line boss: implementation research handoff (2026-10-13)

**Scope and status.** User requested exploration/planning only, for another
agent to implement, and explicitly chose **explore both machine/arena and
character routes and recommend one**. No boss, ROM patch, release, save edit,
or new skill was implemented in this session. Baseline is v0.13.0 ROM
`75faa3ff7759f29212b6c92c6d9d0859298a23c13d228df73c798adef032cb9d`.
Design/recommendation: TASM_ROADMAP "Midnight Line new boss". The previous
"Script boss research" contains earlier emulator evidence; findings below
are **static source/ROM analysis**, not fresh gameplay confirmation.

#### Evidence and corrections to earlier assumptions

Reproduce the bounded native inventory with
`python work/midnight-line/boss_recon.py`: output
`work/midnight-line/boss-recon-2026-10-13.json` includes 139 selected object
placements across native state records, nine boss-labelled character
placements, callback commands, RTTI references and animation bindings. These
counts include alternate records, not distinct playable objects. Disassembly
excerpts: `work/midnight-line/boss-disasm-2026-10-13.txt`; individual addresses
below reproduce with `python tools/kit_lab.py disasm ADDRESS COUNT` (COUNT is
positional). Scratch reports/scripts are ignored; the durable findings and
reproduction addresses are in this section.

- **Ordinary smashable callback exists natively.** Residential_Map02,
  record 1, AG 4, entity 2, `Object (Smashable_Box) 1`: type 14, kind +22
  `0x1F`, destruction EG +23 = 16, `Message_Clear` (opcode `0x15`).
  Hive_Map03 record 1 AG 2 entity 1, ichor blob kind `0x21`, EG 16 sets
  scratch `0x128=1`. Sewer_Map03 record 1 AG 2 entity 1, liftable kind
  `0x16`, EG 2 increments flag `0x62` and unlocks a grate (already lab-proven
  in the chapter). These are precise templates for testing callbacks in an
  authored batch. Native presence does **not** establish HP, attack
  vulnerability, callback timing or repeatability for a new core.
- **Copying a prop copies its callback.** `midnight_rooms.stage` copies
  native prop bytes and changes XYZ only. Any newly borrowed core, bomb or
  liftable with nonzero +23 needs that byte explicitly rebound to its new
  record's EG (or zero for a control). Otherwise it calls an unrelated group
  with the same number. Entity labels are editor names, not a reliable type
  specification: Pier_Map04's `Liftable_BigCrate` has the same kind `0x16`
  as a boiler; Residential_Map08's label says Mini-Boss 01 but kind is `0x2E`.
- **Bombs have script consequences.** Kind `0x31` at Downtown_Map06 has
  `Bomb_Destroyed` EG 8: sets native flag `0x114`, runs EG 7. Other examples
  set `0x115..0x117` (Pier_Map01/Residential_Map06/Sewer_Map11). Do not port
  those events verbatim. Explosion/contact/fuse behavior is still unknown.
  Crane (Pier_Map06, record 1 AG 10 entity 1, kind `0x08`) and Boss_Floor
  (Residential_Map08, record 1 AG 5 entity 2, kind `0x06`) have +23 = 0;
  their names alone do not make them reusable attacks or moving platforms.
- **Conditional operators are decoded.** Handler `0x02039F3C`, jump table
  `0x02039F74..88`: 0 `==`, 1 `!=`, 2 unsigned `<`, 3 `<=`, 4 `>`, 5 `>=`.
  This agrees with `room_script.COMPARE`. The earlier note "2 = ==1" was
  incorrect: on Boolean flags `flag < 1` means clear, not set.
  The condition is evaluated when the command executes; a delayed selected
  action is not a future condition recheck. Queue a guard EG, then test
  running/completed/phase inside that EG at execution time.
- **Scratch versus persistent state.** Getter `0x020D22AC`: ids below
  `0x123` access flag bits; `0x127..0x130` access ten bytes in the game-variable
  manager (`manager + id + 0x99`). Use these for counters and explicitly
  initialize them on room entry; persistent flag 151 cannot store three HP
  segments. Do not infer persistence or cleanup from the room-local name.

#### Character route: concrete engine starting points

Native 24-byte character placements have type 2 at +12, character kind
at +22, and death EG at +23. Preserve unknown bytes at +16..21. Useful
baselines (record 1; AG zero-based, entity one-based):

| Room | Kind | AG/entity | Death EG |
|---|---|---|---|
| Sewer_Map09 | `0x29` | 1/1 | 3, Reward_Spawn |
| Pier_Map08 | `0x2A` | 1/1 | 3, Reward_Spawn |
| Sewer_Map06 | `0x2C` | 1/1 | 4, Reward_Spawn |
| Downtown_Map14 | `0x2D` | 2/1 | 5, Reward_Spawn |

The existing ML_Venom is the last of these: an orange mini-boss, **not
the native Mega Venom** (Hive_Map09, kind `0x31`). Start with the already
used `0x2D` actor in a disposable authored arena; import only its placement,
bind a new death callback, then discover room/zone dependencies. Its native
platform-zone reads of scratch 0x127..129 must not collide with custom logic.
A native actor with a new texture remains an asset/AI reuse prototype, not
proof of a new character with authored attacks.

| Entry point (clean ARM9) | Static finding / next use |
|---|---|
| `0x02052748` | MiniBoss constructor; writes primary vtable `0x0212CE38`, interfaces at actor+8 (`0x0212CE54`) and +0x14 (`0x0212CF58`) |
| `0x020D12A0` | Character parameter accessor: kinds 2..0x32 -> `0x02136880 + (kind-2)*0x54`, otherwise fallback `0x0213682C`. Bounds are real; inventing kind 0x33 does not create a new actor |
| `0x020527A0..BC` | Constructor stores parameter pointer at actor+0xF8 and parameter+0x0C into actor+0xFC/+0x100; kind 0x2D's value is 2,048,000, matching earlier measured boss max HP |
| `0x02052F50` / `0x02052F5C` | Accessors return actor+0xFC/+0x100; strong current/max-health evidence, still identify the live allocation and damage writes before patching |
| `0x02052D70` | Maps kinds 0x29/2A/2C/2D to subtype indices 0/1/2/3; other input defaults 0. Creating another kind also needs factory/subtype/resource work |
| `0x020A9A44` | MiniBossStateMachine constructor, calls shared constructor `0x020B1A00`, installs vtable `0x02133C18`; derived fields +0x98..A8 |
| RTTI `0x02133BA4` | MiniBossStateMachine base RTTI is SpideyStateMachine (`0x02133BB0`). This is code reuse, not proof of player control or kit compatibility |
| `0x020E7730`, `0x020E77B4` | HUDBossMeter construction/update; vtable `0x0213C81C`. Update gets a managed boss via `0x02063008`, reads health through actor+8 interface slots +0x5C/+0x60. A room flag alone does not feed this bar |

**Targeting blocker:** `tasm_kit.s:h_observer` only registers actors whose
primary vtable +0x150 equals `0x02049304`. MiniBoss vtable `0x0212CE38` has
`0x0205337C` there, so it is excluded by that check. The room strength dial
is invoked *after* this filter and assumes common enemy HP +0x44/+0x48.
Do not add MiniBoss to the registry by deleting the filter: its health and
other interfaces differ. Native contact damage may still work; every kit
feature that depends on registry acquisition requires its own boss test.
`kit_lab.enemies` likewise scans only NormalEnemy; an empty enemy list is
not evidence that a boss failed to spawn. Build a bounded class-specific
observer before evaluating a character candidate. Never copy the old
max-HP-pattern search into production (it is a disposable lab shortcut).

**Animation lead, stronger than the earlier separate-rigs assumption:**
`custom_formats.Xbd.parse` plus `sca.Sca.parse`, byte-identical round trips,
shows `m6.xbd` has **121 SCA bindings, all `spd_*`, all 37 joints**.
`spd.xbd` has 126 at 37 joints; `brt`, `bzkr`, `hLpr` have 39/56/57 bindings
at 28 joints. Thus m6 is the first candidate for a rival using the player
animation pipeline. Still unproven: which factory/resource mapping selects
m6, model bone names/order/bind matrices, action table compatibility, weapon
and hit volumes, and attaching `spd.nsbmd` to an enemy. Joint count alone is
insufficient. `kit_choreography.Rig` hardcodes player joint indices; don't
run it on a 28-joint rig. Keep native m6 and shared player resources intact;
append copies and scope any lookup redirection to the new room/actor.

Character implementation gates, in dependency order:
1. Trace unmodified native `0x2D` in its original arena and in a scratch
   authored arena: identify actor, motion, controller, health, state/action,
   target, death callback and bar lifecycle. Record required zone bytes.
2. Map actor factory and character->model/XBD/action lookup, trace m6 users;
   prove an independently bound copy without changing any native encounter.
3. Add one clearly telegraphed attack/recovery on the compatible rig, with
   native collision and damage. Prove it can be interrupted/countered as
   designed, uses continuous velocity, and resets safely on defeat/re-entry.
4. Introduce an explicit boss health/target adapter if needed; verify Perch,
   Rush, Reflex/Sense, Vortex, Dragnet resistance and Black/native attacks.
   Do not apply NormalEnemy health scaling to MiniBoss memory.
5. Only then expand AI states, bespoke clips/visuals, phases and HUD. A new
   skeletal model exporter, arbitrary new actor IDs or a generic AI framework
   are separate research tasks, not prerequisites assumed solved here.

#### Machine route: implementation boundaries and state contract

Recommended first implementation is a dedicated authored fourth Substation
room, provisional `ML_SignalCore` (94), preserving ML_Roof's repeatable waves.
Use the room compiler for original machine geometry, foreground core
locations and a far backdrop; geometry has no AI or damage by itself.
Native smashables supply damage/callbacks only after the tests below.
Ordinary strong enemies supply combo targets; machines/props are not assumed
to support Perch, Dragnet, Web Rush or registry-based area hits.

**Proposed script state, not allocated or implemented:** persistent
`ROOM_FLAGS['signal_leech_defeated']=151`, visited(94)=163. Scratch
0x127 running; 0x128 core count; 0x129..12B three core-dead guards;
0x12C breaker active; 0x12D breaker used; 0x12E attack step;
0x12F/130 phase-2/3 adds-started guards. This consumes all ten scratch bytes
in the new room: do not also instantiate the generic wave logic using
`WAVE_GUARDS` 0x12A..12C. These are proposed meanings only in this room.

- Entry resets scratch, reads defeated flag, and chooses idle encounter or
  cleared room. Begin only after a trigger well inside the arena; set running
  before activating cores/adds or scheduling attacks; consume start trigger.
- Each core has its own AG and callback guard: if not already dead, mark it
  first, increment core count, then dispatch phase/completion. One repeated
  callback or a simultaneous area hit must not increment twice or spawn two
  add waves. Prefer all three cores active once; toggling a core for exposure
  may reset health or resurrect it and is unproven. Do not base the first
  version on destructible reactivation or spawner re-arming.
- One attack scheduler owns progression (warning -> active lanes -> rest).
  Every delayed destination checks running, completion and breaker state
  **on execution**, including already queued hazard activations. Phase changes
  select patterns at a safe cycle boundary; do not start another infinite
  loop per destroyed core. A queued command is not canceled merely because
  its initiating trigger was deactivated. Room-unload cancellation remains
  a required test, especially leaving/re-entering while a timer is pending.
- Warnings must be harmless and readable on DS screens. Use a verified
  sound and a tested visual state; live electric flicker is damaging, not a
  harmless telegraph. No custom effects actor/animation is presumed available
  just because a named resource exists. If an arc/switch visual cannot warn
  clearly, solve the cue before adding multiple patterns.
- Breaker is optional and one-use per attempt for the first version: guard
  its input, cut active hazards, keep the single scheduler alive, resume only
  through another warning after its timeout. It must never be mandatory for
  victory. Defer a reusable breaker until cooldown/retrigger behavior passes.
- Core 3 completion sets running=0 and the persistent flag before cleanup;
  disable hazards, pending attack guards, start/breaker triggers and future
  spawns, then open exits and show completion. Remaining adds must not block
  completion. Validate whether deactivating a spawner removes living enemies;
  do not assume it does. No automatic story reward orb, new ability or skill.
- First version is one-time completion, persistent after normal save/reload.
  Death before completion resets the attempt. Replay terminal/reward economy
  and mid-fight checkpoint persistence are explicitly deferred designs.

**Physical locking needs its own spike.** Authored doors are currently exit
triggers and scenery, not guaranteed lockable native door actors. A record-1
`room_script.door((ag,e), ...)` cannot blindly refer to a record-0 exit.
Use a tested record-1 gate/lock object with a local reference, or prove
record-0 trigger activation/deactivation with correct start callbacks.
Copy ML_Venom's late-start principle: the player enters before walls rise.
Do not seal every route until death, victory and re-entry cleanup work.

#### Small experiments required before building the encounter

Use a disposable room/ROM under build/dev-kit, a copied save, real button
hits and frame/HP/flag traces. Each row has an unchanged control and changes
one variable. No experiment here has been run during this planning session.

| Gate | Experiment and evidence required | Decision/fallback |
|---|---|---|
| Core damage | Compare box 0x1F, barrel 0x23, blob 0x21; native Y string, Black Y, air hit, A and thrown liftable separately. Identify object/HP and count native damage events, callback frame and disappearance | Select a core only if ordinary attacks work without unowned abilities; one-hit props require a durability solution or a deliberately short multi-component design, not fake HP text |
| Core callback | Clone Residential_Map02 box with +23=0 control, then bind +23 to one EG setting scratch; repeat melee, throw, simultaneous multi-hit, reload and deactivation | Require exactly one logical credit per core; distinguish destruction from removing an entity |
| Warning/hazard | Control silent/dead hazard, then sound cue, then visual cue, then live arc. Capture both screens and motion-crossing HP loss; verify safe lanes while moving | No unavoidable/on-contact warning damage; measure actual timing, don't inherit crude loop phase estimates |
| Lifecycle | Trigger entry twice, destroy 2/3 cores, die, re-enter, win during warning/active/rest, wait several cycles, leave/re-enter immediately, save/reload after victory | No duplicate loops/adds, stale hazards, permanently locked door, respawned defeated boss or repeat reward |
| Adds | Separate native spawner batches per phase; observe full unweakened fights, phase overlap, offscreen enemies and delayed wave callbacks | Progress must depend on cores, not unreliable wave-dead callbacks or the Roof's 5,400-frame fallback |
| Optional objects | Isolate Bomb_Symbiote, Crane, Boss_Floor, then examine fuse/motion/damage/callback/deactivate | Cut from first version unless they add proven value; not a gate for the basic boss |
| Kit/fairness | Minimal save (story abilities 0..4), no new purchases, then copied all-owned Red and Black; inspect acquisition, HP damage, hit reactions and R exits | Keep victory accessible; strong adds let the purchased kit contribute without claiming prop/boss compatibility |

Do not pad boss length with mandatory long waits or an HP sponge. The damage
matrix determines whether a core fight is substantial enough; if not, do
the scoped durability spike or move to the compatible-character prototype
before producing final art. Timing, HP, add count and cue choices are tuning
hypotheses, not approved balance values.

#### Integration map, budgets and final acceptance

| Owner | Required implementation work |
|---|---|
| `tools/midnight_rooms.py` | New plan/texture sources/camera/anchors/door and dedicated boss stage; register `AUTHORED` and resource dependencies. Existing `Authored.props` has no callback field; avoid hiding callback edits in generic placement |
| `tools/midnight_chapter.py` | Append room 94 without renumbering; `BY_NAME`, bidirectional `LINKS`, `AUTHORED_EXITS`, room flags, `MAP_FIELDS`, `MAP_ROOMS`/links, `BOSS_ROOMS`, sparse lines/objective board, optional strength entry. Derivatives built at import must see the new definition |
| `tools/room_script.py` | Existing append/builder APIs suffice for the prototype; if adding zone/object helpers, preserve unknown bytes and add focused round-trip/target-bound tests |
| `tools/midnight_walk.py` | Real-door routes Roof->boss and back, corridor before trigger, locked fight, victory/unlock; do not let weaken/teleport fixtures count as combat validation |
| `tools/midnight_line.py`, lab scripts | Copied-save persistence and phase/HP observations. Dedicated observer required for MiniBoss and smashables |
| `tests/test_midnight_rooms.py`, `test_midnight_chapter.py`, `test_midnight_walk.py` | Object/group targets, reference scope, unchanged room ids/flags, one-time guards, safe initialization/cleanup, accessible anchors/doors and map uniqueness |
| `reference/midnight_line.json` | Refresh chapter metadata after implementation; its current_research_gate still mentions v0.9.0 and must not be treated as current authority |
| `tools/release_info.py`, `tools/tasm_kit.py`, `mods/`, release/profile records | Only at publication: compose all accepted overlays, new minor version, exact new hashes, matching boot/Options text, CHANGES + releases.json |

Source/report arithmetic at v0.13.0: chapter block **3,164/4,096 bytes**
(932 free), 18 chapter rooms, 23 map-list entries and 13 custom messages.
One `ML_SignalCore` descriptor/name/model pointer/lookup/map entry plus four
44-byte lines costs roughly 300 bytes before map links and alignment; exact
build assertion remains authoritative. Object scripts live in Glob, not
this ARM9 table block. The kit's second code block has only 196 bytes spare;
do not put a new boss AI there casually. Persistent flags 151 upward grow
toward visited flags 165 downward; re-run collision checks after room growth.
Room 94 is within the byte/map limits. Width <=511 units; arrange the local
fight around the ~58-unit-wide camera view so an offscreen attack is not
invisible. Reserve safe landing space and keep a readable far backdrop.

After implementation: parser/room tests, then full
`python -m unittest discover -s tests`; clean candidate boot; full-health
boss runs without kill/chase fixtures; copied-save death/victory/revisit and
save/reload; `python tools/midnight_walk.py all --rom R` plus the new routes;
`python tools/midnight_line.py tour --rom R`, puzzle and save-test; kit
qualification/crash hunts if hooks or combat assets change. Existing boss
walks cap HP to 1 and place Spidey: they prove flow, not boss difficulty.
Check actual DeSmuME at player-accepted JIT12, especially adds+arcs+Dragnet
lines. Report agent-tested versus player-confirmed separately. Publish only
through `python tools/playtest.py build`, with DeSmuME closed and the latest
actual Battery protected, following AGENTS. None of those release actions
is authorized as part of this research-only handoff.

**Handoff checks (2026-10-13):** five inspected XBDs and all 399 referenced
SCA bindings parsed and round-tripped byte-identically; 15 existing
document-layout/room-script/entity/object tests passed. Only TASKS,
TECHNICAL and TASM_ROADMAP changed in tracked files. No fresh emulator
experiment or player test was performed; all new behavior gates remain open.

### Signal Leech implementation (v0.14.0)

User authorized implementation on 2026-10-13 after the research handoff.
Published v0.14.0 `7cb39338` through playtest, battery unchanged and prior
ROM/composition retained (`leech-publication.json`). Sources: `tools/midnight_boss.py`,
`midnight_rooms.py`, `midnight_chapter.py`; semantic tests
`tests/test_midnight_boss.py`. Current player kit code and native assets are
unchanged. Room 94 `ML_SignalCore`, visited 163, defeated 151, connects to a
new left passage on Roof 93. Refuge's post-Nest objective points there.

**Core data and coordinates (emulator-proven).** World-object parameter
accessor `0x020D1610` normally returns `0x02138FD8 + kind*64`. A room-94-only
replacement returns a private native data copy for kind 0x21: only health
(data+0x14) changes, from 4096 to 49152. Other kinds/rooms return their native
pointer. Object kind is +0x10C, current HP +0x110; native damage decrement
is `0x0206AFA8`, callback/death follows the native path. Mobile world-object
vtable `0x0212F7A0`. An ichor blob placed at y=0 starts below collision and
falls through; y=8 settles at about y=1.531 and is hittable. Actual Red
melee destroyed the 8-unit spike in 194 frames (HP drops recorded, callback
once); the final three 12-unit cores have each been destroyed by actual Y
attacks. Boxes/barrels were too short-lived at native 1/2-unit health.
Evidence: `work/midnight-line/core-durable.json`, `leech-flow.json`,
`leech-combat.json`; current run labels include the candidate ROM hash.

**Original scripted visual objects are possible.** Kind 0x12 has the same
native electric parameter flags (0x4000) as live kind 0x11 and no native
room placements. Its private data in room 94 clears environmental damage
flags: `0x020699A0..AC` skips the hazard damage path unless flags & 0x6000.
It uses the native static rendering path: data+4 >= 0xB6 at
`0x02068FA0..C4`, data+8 = appended model resource. The generated
`zz_SignalWarning.nsbmd` is an original one-node, untextured, vertex-colour
panel (20 x 7 units, eight quads, scale 4), no texture/animation dependency.
It round-trips through `nitro_build.model_parts/room_model`. This avoids
global asset replacement and the tiny native switch/electric-node visual.
The yellow panel flashes three times across the incoming lane before native
kind-0x11 arcs become live. A copied-save movement test lost no HP during
the warning and 6656 Q12 when the live lane contacted Spidey. Captures:
`build/boot-tests/Versioned-4e36287e/walk-leech-cue/frame-03270.png`.
No supposedly harmless warning uses damaging native parameters.

**Lifecycle.** Ten room scratch bytes 0x127..130 implement running, core
count, three per-core credits, breaker active/used, attack step and two add
guards. Duplicate callbacks credit once. One scheduler chooses phase at
cycle boundaries; every delayed destination checks running/completion and
power as appropriate. Warning/live/rest frames: 96/60/60, 80/66/48,
64/72/36. Phase 1 cycles single lanes; phase 2 pairs, always leaving one
safe; phase 3 alternates outer lanes/middle. Three bounded native crews,
same 3x health/1.625x incoming damage dial as the Roof. A one-use X breaker
cuts power for 300 frames; the existing scheduler resumes with another full
warning. Victory writes running=0 and flag151 before cleanup, removes the
seal, cores/warnings/arcs and future spawns, and clears its completion line
after 240 frames. Existing living adds survive spawner deactivation; they
cannot hold the exit shut and disappear on room change. No custom story
reward, new skill or boss HP bar. Native prop/enemy drops remain native.

**Entry trap corrected in the lab.** Touch-trigger extents reached the
player earlier than expected: centre74/width12 raised the gate while he was
at x88, outside it. Centre64/width4 triggers once inside. Native ichor wall
at x82 seals the passage; optional breaker sits inside at x60. The arrival
at x92 is safe until entry. First-visit message is explicitly cleared when
combat begins (native message command 0x15 with all-zero operand).

**Validation limits.** An unweakened, all-owned Red run won and walked out
without health refills (`leech-combat.json`, 25fc predecessor 8e7f73e2;
lowest HP 129 Q12, six enemies observed). A minimal-ownership 6-health-unit
driver broke two cores and died after rushing into overlapping crews; this
is not a player difficulty verdict or a mandatory-purchase gate. Separate
flow runs refill only Spidey and prove actual core damage, victory and
revisit; do not describe them as survival tests. Final ROM regression,
Black/minimal attack and copied-save reload checks are recorded below.
Actual DeSmuME/JIT12 performance remains a player test.

**Final qualification:** 293 unit tests, all 63 kit checks, 12 crash seeds,
all 12 real-door walk routes, chapter tour and power puzzle passed. The Roof
route needed one rerun for its known stalled-wave case. Red and Black each
won an unweakened fight without player refills; actual native near-death
minigame recovery was completed with real pen/button inputs (a lab HP-zero
fixture starts it). **Native near-death recovery resumes this same attempt,
keeping the core count**, as OG_GAMEPLAY describes; it does not reload a
room. A fresh pre-victory load/room entry resets all ten scratch bytes.
Normal save at the Refuge after actual victory, reboot/Continue and re-entry
kept flag151 and spawned no cores (`leech-persist*.json`, copied SRAM only).
The seal also held at x76/y12 after jumping past the destroyed nearest core.
Reusable driver/observer: `tools/midnight_boss_lab.py run MODE --rom R`,
tests `test_midnight_boss_lab`; its hazard observations can include retained
allocations, so use HP/frame evidence for activity, not the raw scan count.

Kit/crash/walk regression candidate was `25fc42b6`; final `7cb39338` differs
only in the first-visit help wording and map presentation. Native/kit ARM9
and the whole 216-byte boss adapter, all gameplay assets, room objects and
models are byte-identical. The only ARM9 differences are five map colour-slot
pairs. `work/midnight-line/final-equivalence.json` records the comparison.
Source map-state colours 0xB6/BA/BB/BF must also be reserved: allocating a
room across palette slot182 overwrote source186 (visited highlight). This
was caught and fixed before publication; a focused test preserves all four,
and the all-visited map capture reads correctly at
`build/boot-tests/Versioned-7cb39338/mapview-leech-final/frame-03320.png`.

**Budgets.** Chapter tables use 3396 bytes before the adapter's fixed
offset 0xF00 (444 bytes left there). Adapter/code + two native data copies
use 216 of the last 256 bytes (40 left); total meaningful use 3612/4096.
The room map now also uses free palettes 11/12/4/5 after checking all kept
UI cells; palettes 13..15 remain excluded. Roof map piece narrows so Signal
Core can sit on its left with door directions intact. Existing room IDs and
flags are preserved. Registry still excludes these world props/MiniBoss.

### Signal Leech readability (v0.15.1)

Player feedback 2026-10-14: completed Leech, but barely visible cores,
messy terrain and unclear target order, safe footing and electrical timing.
Roof/material issues were mostly Substation/boss (explicit clarification).
Scope: clean those rooms; Vortex feels short/clunky and pause entry is hard
without Dragnet. Published `160d01cb`; latest real battery `3a4e7c9b`
unchanged and previous ROM/compositions retained (`cleanup-publication.json`).

**Core rendering trap:** private core-only `2dc78726` changed core data+4/+8
to the static-renderable path and a bright authored mesh. Cores rendered
and retained HP, but Y never reduced their HP: the animated binding supplies
their native hit geometry. Discarded. Keep all native core data except HP.
The implementation uses a separate harmless kind0x13 static beacon,
copied from the harmless warning data and scoped to room94, at the core's
x/y with its own model. Three callbacks remove the corresponding beacons;
victory also cleans all three. Beacons round-trip through the native model
writer and have no texture dependency. Original kind0x13 outside room94
retains native data. Adapter is 108 bytes plus three 64-byte data records
(300 total) in a 320-byte tail; Roof adapter moves 64 bytes earlier. Read-only
old-release audits retain the prior 216-byte adapter/layout when their
resource map lacks `core_model`.

**Geometry trap:** removing the three suspended combat shelves is safe;
lowering the right entrance bulkhead to 28 allowed a real jump/swing over
the seal (flow `99d491dc`, x100.5/y59.2). Restore the full 70-unit bulkhead;
do not weaken the seal to fix that test. Control Roof's independent entrance
huts have visible 32/38-unit roof caps. The release brightens solid fronts
and undersides, uses construction textures instead of cutaway/light tiles,
and paints distinct arena lanes/green gaps without adding collision solids.
Warnings (108/96/84 native delay units) light the floor with side posts below the cores;
two live arcs at x+-4 per lane replace the cluttered three at x+-8/0.
Exact `160d01cb` clarity qualification passed: green x34/58/8 each held
1,440 captured frames with HP unchanged at 24,576; floor x14.5 was harmless
for 200 warning frames, then lost 6,656 Q12 on the live arc. All three
beacons were observed before combat. Sources and report:
`tools/midnight_boss_lab.py run clarity`, `work/midnight-line/walk-leech-clarity-160d01cb.json`.

**Clock/observer corrections:** native OBJ delay units take two captured
DS frames here (warning 108 -> 216, old breaker 300 -> 600 frames). The
unchanged breaker is approximately ten seconds, despite the historical
five-second description. Use measured HP/captures and STEP transitions:
world-object allocations may survive deactivation and report capability
without rendering. Standing on a core puts Spidey at y8 and above the
electricity; x14.5/y5 is the adjacent-floor control. Keep the real battery
out of all these fixtures.

**Room preview correction:** `work/rooms/lab_view.py` formerly used spawn0.
On Roof that position touched its new left door before the control frame
and loaded Signal Core; teleports to Roof coordinates then fell outside
the boss collision. Use an authored door's actual spawn id and verify the
observed room before evaluating captures. Updated helper uses door1.
Roofs are capped; far skyline ground extensions are shaded to 20% to
avoid stretched neon columns. Relay/Switchyard/Service use brighter
construction surfaces in place of dark cutaway or repeating light tiles.

Evidence during development: `build/dev-kit/cleanup-*`,
`work/midnight-line/{leech-flow,leech-clarity}*.json`; actual native core
damage and all three destruction callbacks passed the beacon/flat-floor
trial; its seal test identified the bulkhead regression above. No player
confirmation of the revised visuals or Vortex feel yet.

Final gates: 311 units, 68 kit, 12 crash seeds, all13 real doors, Red/Black
wins without refills, boss flow/seal/revisit and save/reload. A later seal
test falsely rejected x80.5/y65: this is the normal contact with the wall
at84 minus Spidey's3.5 half-width, still outside the entrance. Its bound
is now80.75 (quarter-unit probe tolerance); the actual x100.5 bypass above
was fixed, not excused. Control report: `leech-flow-coordinate-control-160d01cb.json`.
Signal-in also had one lab predicate read an absent pose during transition;
it now waits for a stable pose and passed `walk-signal-in-stable-pose-160d01cb.json`.

### Midnight storm-terminal overhaul (v0.20.0, 2026-10-16)

User supersedes the old clone/Nest plan: remove every sewer/Hive recolour,
author places like Substation, original creatures and a real combat finale.
Sources: `midnight_rework.py`, `midnight_rework_rooms.py`,
`midnight_rework_creatures.py`, `midnight_rework_boss.py`; copied-save lab:
`midnight_rework_lab.py`. Qualification/publication state is in TASKS/CHANGES.

**Composition/save contract.** Strict post-pass over exact0.19.0 `9b2b948f`.
Rooms76..90 are all compiled from empty Test_Surfaces objects and original
geometry/materials; internal ML/Nest/Venom names remain saved-ID contracts.
Five authored Substation rooms91..95 remain. Native entrance/room graph,
visited bits, native/Crane assets and complete32KiB kit image remain intact.
New compiled model/BSP/detail maps and one shared texture archive are appended;
old graded archives remain inert. New objects replace owned chapter objects.
Actual old player progress has legacy246 set and new147 clear; do not reset
either or edit the real battery. New boss victory writes147 and legacy246.

**Original presentation.** Storm Gate, Signal House, Midnight Terminal, Switch
Tower, Skyrail Viaduct, Floodworks, Pump Refuge, Turbine Rise, Lightning Bridge,
Capacitor Hall, Storm Observatory, Relay Sanctuary, Crown Approach, Conductor
arena and Train Sheds replace all fifteen cloned areas. Plans share original
low-contrast stone/steel/glass/rail materials, deep storm panorama and distinct
architectural setwork; bounded environment meshes (exact counts in the catalog).
Original image/prompt/provenance: `reference/art/midnight-storm-v1.*`.
Panorama is one continuous triptych at z=-170, not mirrored tiles. Three safe
spheres preserve77/82/87; Service Bay95 remains a fourth safe checkpoint.

**Texture-bank trap (empirical).** A single archive with three256x256 indexed
panorama textures (about207KiB) loaded the authored geometry but every room
surface rendered white. A controlled change to three256x128 panels plus the
same materials restores textures. The production bank is about109KiB and the
builder rejects archives >=128KiB. Treat128KiB as this loader allocation's
empirical ceiling, not the DS's total VRAM. Native models/creatures rendered
during the white-room control; it was not a bad model pointer or black screen.

**Autoload overlap trap.** Native kit destination0x0214F420 is fixed. The
accepted0.19.0 source image ends at raw ARM9+0x14E9A0, leaving only0xA80 to
that destination. Appending8KiB moved the autoload table into its copy target:
white boot, stats pointer0; discarded before publication. Extra source bytes
plus the36-byte autoload table must end <=0x0214F420. The new block reserves
0xA00 at runtime0x0215A420 (source/table ends0x0214F3C4,92 bytes clear).
It uses2188 bytes after compact sound routing and reuse of owned chapter model
pointer/map-list storage. A build guard enforces the source/destination gap.
Arena starts0x0215AE20. No kit rebase or kit-byte reuse is involved.
The old Crane8KiB block differs only at+0x6DC (Midnight area's map-list count);
Crane executable code, room data and resources remain exact. Do not describe
the entire shared block as byte-identical.

**Creatures.** Private 28-bone Rail Skitter/21(hLpr), Bell Warden/36(brt),
Arc Eye/20(hRng), and Conductor/36 have entirely authored GPU geometry and
face-colour atlases. Native rigs/AI, hit pipeline and costs1/2/1 remain.
Existing full-lifecycle Crane-authored SCA/GMB choreography is shared by exact
payload hash; private XBDs/model-sheet groups bind the new silhouettes. Do not
claim a new AI or unique choreography for every species. Models have238/178/
186/278 quads. Private health config bases7/10/6; existing chapter strength
dial still applies. Conductor base64; observed max268224 Q12 in the lab.
Native death tint remains available because display lists do not override COLOR.
Private physical reward31 uses the accepted native XP/HP row and native drop
pipeline. No direct stat credit. Twenty new synthesized alert/attack/death/hurt/
idle voices occupy597..616;582 native and15 accepted Crane entries remain exact.
Arc Eye has explicit state-entry cues like the Crane ranged chassis.

**Scoped code.** Config, variant, finite-goal, reward, sound, ranged state-entry,
Objectives, world-object warning and wave callbacks tail-chain the accepted
Crane/Leech hooks. Scope is76..95; room89 always selects one cost2 Conductor.
Ordinary crews use8 total/4 live cost and upper crews4/2. Saves spawn no crew.
Native accessor initializations still run. No native enemy table is overwritten.

**Conductor phases.** NormalEnemy native setter0x02049304 has r0=actor,
r1=new HP; +0x44/current and +0x48/max. A guarded observer of room89's
NormalEnemy vtable advances room scratch0x129 to1 below half HP and2 below
quarter; preserves all registers/flags and executes the exact native prologue.
No damage, HP or player position is changed. One finite cost2 spawner owns
victory; no timer can credit a kill. Start/phase/clear use0x127/128/129, reset
on entry. Three storm lanes44/112/180 warn before native live arcs; patterns
are centre, outers, then left+centre, always with room to evade. Guarded delayed
callbacks stop after victory. Record0 exit groups check earned147, so both
doors open on actual defeat. No new skill or custom full-screen HP HUD.

**Door contract and lab corrections.** Incoming spawn IDs must match the
*reverse exit*, not its numeric group. The first draft swapped85/86 arrivals;
round-trip input tests caught arrival at the wrong door. Test every reciprocal
pair and opposite sides. High/stacked doors now require X with one small glyph;
otherwise approaching an upper door can trip the lower automatic exit. Native
jump/swing landings qualify the ascent: holding Up underneath a landing is a
driver failure. Conditional lab landings skip only stable nearby ground,
never a high airborne sample across the room. Turbine/Crown geometry now uses
one explicit sequence of16-unit rises rather than overlapping generic edge
ladders and central scenery platforms. Every replacement room is crossed with
native input after initial entry; enemies are parked and the player healed.

`midnight_walk.py all --rom R` dispatches overhaul metadata to bidirectional
pair runs (21 pairs/42 directed doors including native entrance). The faster
lab compiles four research-warp words into a disposable ROM before boot, then
enables JIT with block12; no runtime instruction patch or savestate. The unchanged
Relay upper doorway retains the established landing-placement isolation fixture:
it is walked, but its full active-arc ascent is not qualified. Attempts at full
native traversal and harmless-arc controls did not qualify that ascent. The
release ROM is unchanged; fixture/capture hashes differ and are labelled.
No-JIT controls use the original RAM-warp route. `manifest --rom R` audits all
21 passed case reports for the exact source hash and rejects unexpected position
fixtures outside that one unchanged Relay case.

**Actual receipts.** A full-HP mixed Terminal crew clears with all three species
observed and72 XP physically collected (player healing enabled, no enemy HP
cap). Native-arrival idle1HP reward controls disable healing/position writes:
all three collect XP6 before the driver ends, plus1024/2048 Q12 HP. These are
partial collection receipts, not a claim of total XP per kill. Paired zero-set
Ballast kills collect0/0. Post-remap death IDs599/604/609 and normalized PCM
matches in the real emulator mix prove the three original voices render. The
reward lab compiles a register-preserving audio observer into the unused private tail
(code+0x8A0,20 counters+0x950), before boot. It never ships. Counters must include
the final60-frame core tail: Arc Eye's death cue may arrive after pickup success.

Red and native-L-switched Black each win the unweakened Conductor with no player
refills, walk out and revisit a cleared room. Final Red earns147, saves at87,
reboots/Continues and walks back to a cleared89; source battery unchanged. All
HP phases0/1/2 are observed. These scripted controls do not establish fun,
difficulty, average fight duration or DeSmuME frame rate.

**Lab implementation.** Keep a stable reference to the original Walker class:
the runner temporarily replaces `midnight_walk.Walker`, so dynamic base reads
can recurse. Custom steps need a second tuple field, even None, for the native
step logger. Reuse the current frame's RAM/state instead of scanning twice.
Combat, earned-save and reward fixtures state their distinct limits. Ignore old
captures left in reused directories; select frames from the current report and
reject transition-black frames when assembling contact sheets.

### Chapter renewal (v0.21.0, 2026-10-17)

Player rejects0.20's shared choreography/native AI and unreliable map/ports.
Sources: `chapter_renewal.py`, `_rooms`, `_motion`, `_combat`, `_lab` companions;
tests `test_chapter_renewal.py`. Publication/qualification state is in TASKS.
Strict parent0.20 SHA4b4e739e; original resources/purchases/32KiB kit protected.

**Real action bindings, not filename ordinals.** `actor_actions.ActorActions`
frames the actor XBD's six-byte action rows. Header+8 is a signed relative
offset in16-byte units, with low nibble at+10; high12 bits at+10 count rows.
Each row repeats that relative-vector encoding, count in high12 bits, flags at
row+4 and exact action byte at+5. Vectors contain the already parsed four-byte
XBD resource bindings. Native0x02001F44 /0x0200211C implement this lookup.
Rows are sorted/unique; all unknown bytes survive read-only round trips.

For **Brute**,55 is GroundAttack1,63 is GroundAttack2,71 is ranged,136 is
RunAttack. **Leaper** adds121/122 for LeapAttack/Prep,68 Combo,69/70 Strong1/2.
64 is absent from these actors. Requesting64 left a misleading action64 field
while the GMB remained Idle, clock0; the NPC stayed in attack state15 indefinitely.
This was caught in an idle-target bait test, fixed before publication, and is
now rejected by a build-time action-binding check. Never infer enemy action IDs
from Spidey's numbering or a filename's suffix. Attack55 is not the Leaper leap.

**Scoped sequencers.** Exact private config pointers select seven ordered
attack/recovery programs (Maw/Ballast/Spore, Skitter/Warden/Eye, Conductor).
Native EnemySM think still runs for navigation/interrupt priorities. Only
ground states0..6 can start a selected action; hurt/death states retain priority.
Native state15/16 entry executes first, then its motion request is replaced and
the native resource-refresh bit set. Private32-slot state stores sequence and
cooldown. Hero coordinates are read, never written: the generic controller
update observer caches only PlayerSM0x021352A4's owner; primary player vtable,
RAM range and motion back-link are checked before proximity reads. Native
damage, player kit/ownership, physics and rewards remain intact. No slow time.

**Motion.**347 private SCA routes cover all seven actors; continuous trajectories
include genuine prone knockdown, airborne tumble, prone land, get-up, hurt and
death rather than treating every Hurt filename as upright recoil. Contact GMBs
and references follow the species rig. Fast Brute slam and Leaper pounce contact
starts move2->6; Brute stop6->11. Native clocks/sample counts otherwise remain.
Private SCA pool compaction removes unreferenced authoring tracks and shares
constant/equal tracks, checking every sampled translation/rotation/scale through
the independent parser. Unknown header bytes stay; nonzero alignment cannot be
discarded. Native SCA files are never compacted. Development cache keys cover
all authoring/format dependencies and verify payload SHA256 before reuse.

**Audio.** Existing617 waves/instruments/sequences remain.35 original voices
plus a tiny silent wave append IDs617..652 (653 total). Direct private actor
state-entry cues cover attack/hurt/death, using native handle construction and
destruction. Old creature vocal requests306..328/457..501/582..616 select652
only in76..107; other rooms and combat foley retain their native behavior.
Five voice categories are authored per species; alert/idle are reserved, not
claimed as all independently heard. Entry counters are not PCM proof by
themselves. Copied-emulator WAV/normalized-correlation evidence is under
`work/dual-rework`; initial Warden death matches0.964 at unity pitch.

**Compact circuit.** Ten active Midnight IDs76/77/78/81/82/83/86/87/88/89:
eight-route loop plus two save branches. Former rooms retain valid saved IDs,
default saves and recovery exits to Observatory, off the new route/map.
147 gates the Crown return and real Conductor victory. Ceilings share collision
bounds; shutters have side and front-facing panels, light bars, thresholds and
X marks. Every Midnight shutter requires X. Crane retains its authored terrain,
locks, machine scripts and IDs, with clear port aisles and visible ceilings.
All same-wall stacked Crane exits now require X, including the ground exit:
otherwise climbing to an upper hatch could enter the lower automatic doorway.

**Traversal lessons.** Never fill Crane's12-unit wall-crawl channel beside high
landings: it seals the climb under the deck, trapping a crawler8 units below
the port. Arrivals stand18 units inward on solid platforms. Turbine's last
84-unit gap was replaced by intermediate landings. Side-branch steps must not
overhang a train/pump by only1 unit; that makes a head trap. Actual input tests
caught these, not a reciprocal graph check. The renewal navigator uses authored
landings, retries missed climbs, jumps off short obstacle walls, and presses X
at stacked ports. Door tests park foes/heal player; combat tests use separate
native-HP crews and explicitly labelled bait/roster fixtures.

**Capacity/loader.** CandidateA/B exceeded64MiB; production moves to128MiB by
padding, increasing capacity byte and recomputing header CRC. Original ROM
remains untouched. Room archives stay below128KiB (largest126976 bytes).

**Save-probe input trap.** `oscorp-reload.json` includes post-boot movement,
opens the sphere's menu and enters Test Upgrades/room70. It is not a neutral
Continue script. A first renewal reload appeared in70 with victory intact,
although its actual saved header correctly contained87. Use only its startup
A presses before1400, then independent native room-return inputs. Preserve the
failed diagnostic; never infer a broken checkpoint from that training route.
Walk clear of the save sphere before pulsing X at the destination shutter;
otherwise the input opens its menu instead of testing that door.

**Visual ordering repair.** A depth QA sheet exposed the compiler's fixed
z=-25 back panels occluding authored machinery at z=-42..-27. Renewal renders
the same opaque/window rectangles at z=-64 instead, leaving native panels open.
An80-unit exterior margin keeps solid roof cut faces visible through high jumps.
Final visual changes affect only20 private Midnight room NSBMDs; ARM9, all
collision/objects/maps, creature assets/bindings and SDAT are byte exact to the
qualified combat/door/save candidate. The automated visual-scope audit records
this; final Midnight doors/visual combat are rerun, Crane controls inherit.

Runtime begins0x0215AE20, reserves0x1800, arena starts0x0215C620.
The old forward SDK autoload copy cannot grow further without overlap. The
bounded0x02000A14..0x02000A68 loop now preloads all three row words and copies
downward, retaining the original BSS/cache loop and registers. The extension
is last, with zero BSS; its table can therefore be overwritten after preloading.
Original ITCM/DTCM rows remain exact. Kit destination/bytes stay fixed.
Boot, live sequencer counters and native-input controls qualify actual relocation.

### Creature Forge

Implemented in v0.22.0, material correction v0.22.1 (2026-10-17).
Shared enemy foundation at that release. The v0.24 contact/lifecycle correction,
v0.25-v0.27 Midnight motion/audio/anatomy changes and v0.28 reliability layer
supersede affected details below; start with the topic map for the current path.

Strict post-pass over immutable0.21.0 SHA60a974f3; `creature_forge.py` composes
it after the accepted maps. Helpers `_design`, `_art`, `_motion`, `_combat`,
`_audio`, `_sound_author`, `_lab`; tests `test_creature_forge`. Room resources,
objects, collision, connections and map descriptors stay exact. Only seven
private model-sheet groups182..188, their existing configs, version strings,
appended creature resources/audio and scoped controller hooks change. The
32KiB player kit is compared byte-for-byte. No player position/HP writes.

**Anatomy correction:** hLpr/hRng arms are shoulder/elbow/wrist7/8/9 and14/15/16.
The preceding6/13 joints are scapulae. Brute is6/7/8 and13/14/15. Treating all
three rigs alike put a leaper's wrist target on its elbow. Limb lengths are now
authored in private SCA translations as well as rotations; extended forelimbs
reach a low predator stance with bent joints rather than clamping straight.
Authored neutral geometry uses the same pose, exact inverse matrices and native
SBC slots. Bone19 is repurposed for a jaw/aperture; terminal toes23/27 carry
independent attack effects. No gameplay data is stored in actor padding.

**Rendering:** UV-painted lofted shells, split blades, beveled armor, jointed
petals and a broken crown replace the former colour-sampled primitives. Every
model binds one shared128x128 RGB555 atlas, so the seven texture variants do not
consume separate VRAM copies. Native material hurt/death tint remains enabled;
there is no inline GPU COLOR. Rebuild each single-entry material Patricia
dictionary when renaming its texture, not only its text. Side eyes/cores face
Y/Z, the actual camera plane. Meshes use240..291 quads,402 for Conductor.
The original generated atlas and generation receipt live in `reference/art`.

**Material-size correction:** published0.22.0 retained the native64x64 original
texture dimensions at material+32 while binding a128px atlas. Nitro derives
magnification from these words, so correct texels/UVs still sampled incorrectly.
Immutable0.22.1 (`creature_texture_fix.py`) changes only the seven private materials
to128x128 plus native version labels. Shape/rig bytes, ARM9, SDAT and all other
resources remain exact. Preserve each resource's previous length modulo4 when
growing labels; the native model loader depends on alignment. Final SHA1613d746,
parent69082fda; exact byte proofs and tests are retained in the build metadata.

**Motion/contacts:**347 privately rebuilt lifecycle routes.22 selected attacks
have independent durations, continuous asymmetrical wrist arcs, overlapping
pelvis/chest/head/digit motion, planted stance/swing gait and distinct prone,
tumble, recoil and rise phases. SCA pools are authored with translation,
rotation and scale tracks; independent sampled round trips check all three.
GMB records are resampled to the same count, keeping opaque channel metadata;
body/reaction volumes follow the authored silhouette and flatten when prone.
Selected attack volumes and GAB on/off pairs are authored together. A native
GAB needs the six-FF terminator and zero/two alignment bytes. Ground pulses
have a2.2-unit height so a jump clears them. Beams/bolts have explicit high/low
lanes; animated toe matrices display corresponding rings, bolts and arcs.

**Runtime:**0x0215C620 reserves0x3000; final used5796 bytes. The parent
descending autoload copy remains. Exact-config records point to32-byte move
descriptors: action, last sample, cooldown updates, drive/jump/cue tables,
counter index and engagement rangeQ12. There are32 private32-byte controller
slots. EnemySM think/entry/update slots0x02133410/418/41C dispatch the authored
program; the generic hero capture retains its native ABI/flags. Native damage,
gravity, collisions, hit/air/web/death priority and rewards remain authoritative.
Native attack entry only initializes the normal damage machinery; selected
private action/GAB/GMB and velocity programs replace its attack behavior.

The engine also runs a secondary state-decision pass at0x02133414, native
0x02095A78. After a real custom jump, it requested fall5 and replaced the attack
before contact. A guarded wrapper returns the native keep-current sentinel
0x7FFFFFFF for navigation decisions0..25 during an owned active program;
hurt/death26..53, dead actors, stale configs and unrelated actors keep the native
result. The impulse first calls native ground detach0x020739B4, preserving its
weak contact lists, then sets Y velocity. K passive Skitter observed real
36.5-unit height and contacts in all three moves with native HP unchanged.
Direct ABI/stale-owner tests cover both think passes and ground steering.

**Clock trap:** motion+0x178 is a whole GAB sample cursor, not Q12 time. Using
Q12 thresholds held state15 forever after animation ended and prevented drive
and impact cues. Cue/impulse thresholds compare previous/current whole samples;
velocities alone are Q12. Motion action+0x254 must match before consuming a
program; same-action re-entry sets motion flags+0x2FC bit1. Hurt cancels the
program immediately. Boss fourth move is eligible below half native HP.

Ground spacing has species speeds/ranges, including ranged retreat and natural
walks off upper catwalks toward a player below. A negative cooldown marks a
committed descent direction; recalculating direction at a fixed X threshold
would oscillate before the edge. Every position change uses native velocity and
physics. Update also compares slot config to actor+0x40: controller AND actor
addresses can both be reused by an unrelated native enemy after a room change.
The stale-pointer regression verifies that its velocity/facing are untouched.

Spore/Eye engage across20 vertical units (others12); recoil blooms jump at2.8
units/update. Freight room97 has narrow recovery gaps that admit the smaller
Spore below the player's accessible floor. A private style2/room97 recovery uses
native velocity and ground detach: first pit x58..90 below y-10 walks toward87,
jumps at3.6 and continues until94; second x304..344 hops at341 and clears348.
Slot cooldown-2 commits recovery across ceiling cancellation/landings and retries
the impulse. Only normal movement or its owned attack can enter this path;
native hurt/death retains priority. Actual trace:87,-20 to93,+6 in60 frames,
followed by a native-HP clear. No actor placement, HP or state fixtures.

**Audio:**57 new mono22050Hz IMA-ADPCM samples:35 lifecycle voices/tells and22
move-specific contact sounds. Layered, pitched CC0 recordings, filtered
transients, short room tails, soft limiting and deterministic quantization
replace oscillator/noise voices. Sources and licenses are preserved under
`reference/audio/creature-forge-sources`; frozen bank/receipts under
`creature-forge-v1`. Normal shipping builds do not need NumPy or FFmpeg. DS ADPCM
is low nibble first; delta=((code&7)*2+1)*step/8 with integer truncation, predictor
clamped to+/-32767. Native bank20/SSAR0/SWAR0 append slots653..709; old rows
survive. Voice filter also silences617..651 only in rooms76..107, chaining the
accepted older filter. Exact actor entry plays new tells/hurt/death; animation
cursor crossings play impacts. Foley for unrelated actions remains native.
Fresh private controller slots also play spawn alerts; hurt entry covers26..50,
including the common37/38 reactions which the older narrow list missed. Idle
voices remain reserved. Diagnostic move words pack selections in low16 bits and
contact crossings in high16, so selecting a move cannot masquerade as executing
it during qualification. Native full-HP clears and passive contact tests differ.

Qualification/publication state and limits are recorded in TASKS. Early failed
timing candidates and navigation probes remain in ignored `work/creature-forge`.
Exact final0.22.1 native-input duels clear all six isolated species with contacts
in all18 moves; full Conductor phase/clear reaches all four. Fresh earned-save
Continue/cleared-boss return passes. These heal the player; the no-refill Red/Black
boss controls use0.22.0 (Red's mechanically identical earlier boss candidate is
explicit in the catalog). Final ARM9 and SDAT are byte exact across the texture
patch. Audio FFT correlation against decoded production tells/contacts/hurts is
0.596..0.987 for the six species. These controls establish engine execution and
preservation, not player fun/difficulty or actual DeSmuME FPS.

#### Chapter composition and engagement audit (v0.22.1, 2026-10-17)

Historical diagnosis of exact v0.22.1. v0.23 subsequently authors room ecology,
coordinates Conductor/lane pressure and revises the hoist; v0.24 and v0.28 change
room envelopes and staging further. The observations below explain those fixes,
not a second current construction queue.

High confidence from final ROM resource parsing, current generator/runtime
source and fresh copied-save engine observations. Receipt:
`reference/chapter_evaluation.json`; raw evidence: `work/chapter-evaluation`.
All128 room NSBMD/NSBTX/BSP/CBMP resources in the0.21 renewal receipt are exact
in0.22.1, including legacy recovery rooms. This excludes similarly prefixed
creature motion resources, which Forge replaces. The existing13f43bd4->0.21
visual-scope receipt changes only Midnight room models; its Crane environment
captures remain valid. Older enemy captures are not current enemy evidence.

**At v0.22.1, room-specific ecology was not yet authored.** Six ordinary active Midnight
rooms76/78/81/83/86/88 each contain one table8 spawner cloned from Pier_Map04,
with the same `spec()` gang recipe and room-scale spawn region. Boss89 is a
separate callback-driven spawner; save77/82/87 have none. The private species
adapter cycles variants rather than selecting a roster authored for each room.
Forge's controller independently increments a per-actor move index and wraps
the descriptor count. It tests the next move's reach before selection; excessive
vertical separation goes to navigation/suppression. These are source contracts,
not proof that all resulting encounters feel identical.

**Terminal elevated-target blind spot.** In an unisolated0.22.1 patrol, native
input reaches the first carriage edge, player `(145.066,16.981)`. From frames
600..1202 Warden stays about `(145.182,4.620)`, state0/action99, full native HP.
The12.361-unit vertical separation exceeds its12-unit engagement band. The
runtime's `vertical` branch suppresses a target above that band; its explicit
recovery steering handles targets below. A second fresh run varied its native
spawn/combat evolution: on nearby ground, Warden repeatedly walks against a
carriage at x216.950 without closing. That supports a separate obstruction/
pursuit concern, not a controlled proof that dropping alone fixes the first
case. Both use healing, but no enemy HP/position or player-position fixtures.
An attempted isolated perch control stopped on the ground instead; its Warden
executes all three moves/contacts. Retain it as a ground control, not a paired
elevated reproduction or evidence that the mixed encounter is fixed.
Fix acceptance must cover ordinary mixed rosters and both sides of the train,
not just enlarge attack volumes or reproduce an isolated flat-floor clear.

**Independent Conductor clocks.** `midnight_rework_boss.stage()` owns the arena
lane warning/live/rest loop, with HP setter observation choosing its half/quarter
phase. Forge owns the creature move sequence, adding Crownfall below half HP.
The two schedules are not explicitly coordinated. Saved death147 shuts down
the arena and gates the return. A coordinated pressure budget is a new change,
not something established by four successful move counters.

**Hoist exposure and scope.** `crane_boss.stage()` alternates slam and sweep;
after warmup their scripted delay budgets are206 and272, of which100 each are
EXPOSED. Nominal vulnerable fraction is200/478 (41.84%); this ratio does not
measure real FPS, actual damage dealt or fun. The three lane centers span64
units near the end of the420-unit Long Arm. Crane power140 opens routes and
poses its lever; the counterweight's motion remains scenery with fixed player
landings. Changing solid geometry or making a rideable load needs its own
native collision/ownership demonstration.

#### Voltage correction: quiet cues and ineffective poise (0.26 research)

**Player0.25 feedback,2026-10-18:** the boss is somewhat better but too slow,
too easy to combo, and lacks effective counters. Midnight enemies seem silent.
This supersedes any implied quality acceptance of0.25's poise or sound mix.

**Confirmed isolated sound finding (exact0.25).** Direct native-handle requests
for custom776 are accepted, like native306; accepted requests alone do not prove
audibility. Against an otherwise identical no-pulse control, native306 renders
at685 RMS difference while custom776 renders at42.5.0.25 Skitter's tell source
is only276 RMS, versus its strike's2829: the new quiet role levels combined with
stock-cue suppression make voices/tells faint. A PCM16 control at unchanged
level remains42.5 RMS, so a format switch alone does not fix it. New normalized
own-row PCM16 plus hostile-cue priority renders477.8 RMS difference, about11x
that old alert, with a waveform match. Actual Skitter/Warden live-versus-muted
runs now have identical gameplay and about0.99 tell/strike waveform matches.
Eye's gameplay diverges, so no whole-mix subtraction is claimed; its live tell
and burst independently match about0.99 while the muted control does not.
Sources: tools/midnight_voltage_audio.py,
work/midnight-voltage/isolated-sound-proof.json; three original controls and
format control are retained. Native/player/music rows remain untouched.

**Counter diagnosis / prototype.**0.25's counter protection depends on native
get-up state51 and selected attack samples. A flinch37 combo need not reach
that state, and a forced state-entry flag can restart an already active clip.
0.26 observes actual owned HP-setter losses and queues physical recoil/return
attacks after three reductions within80 decision updates. It consumes blocked
hurt transitions without restarting a matching running clip. Native HP damage,
death and rewards remain. New faster low/twisting motion and native velocities
are now in-engine qualified: a healed base-string pursuit control observes22
responses; separate Red/Black controls win and save without refills using native
R/B/air-stomp counterplay. Both earned saves pass fresh Continue on final E.
Final E also restores the complete published0.25 lifecycle/GMB/GAB contract:
the draft regenerator would otherwise resample get-up attack94's GMB without
its authored GAB alignment. Only new locomotion/program payloads are overlaid.
Source: reference/midnight_voltage.json and work/midnight-voltage/life-restoration.json.
Counters and clearability still do not establish the player's quality verdict.

#### Combo openings and coherent creature motion (0.27 research)

**Player0.26 feedback,2026-10-19:** mobility/strength are harder and cooler, but
the boss never staggers, preventing combos and making difficulty frustrating.
This supersedes any implied acceptance of0.26 counter fairness. Boss and normal
Midnight creature appearance/motion remain rejected; some rooms need a stronger
lead-up. Counters and knockdown resistance are compatible with the new direction.

**Confirmed source diagnosis,exact0.26:** both decision passes consume hurt
through nearly every sample of every boss attack. Its brief recovery windows
and fast pursuit keep this blanket protection active for most of the fight.
The0.27 prototype protects only earned counter action74; ordinary programs
accept native hurt. Four actual HP reductions queue the escape instead of three.
Disassembly of native enter table0x02132D98 identifies state37's action83 as
brt_HurtHitB, a standing recoil. The scoped prototype maps knockback/floor
reactions38..45/48..50 to37; web46/47 remain native outside the committed counter
and death53 always wins. B's real-input base-Y control observes99 HP losses:
68 enter standing stagger and30 occur during a protected counter.15 escapes
complete, five native player hits deal20920 Q12 damage, and the boss dies through
native damage without player refills. No airborne/floor hurt state appears in
its sampled boss trace. Source: work/midnight-flow/combo-proof-b.json. This is a
deterministic driver observation, not player difficulty acceptance.

**Presentation diagnosis:**0.26 boss locomotion adds a low offset/31-degree
lean over the0.25 stance, but hurt/death clips retain the older body stance.
World-fixed IK tips fight its additional body spins. The0.27 author uses shared
attack-boundary stances, carried hand targets, longer action recovery and
restrained torso turns, with a closed anatomical mesh instead of crown/shards.
The first path A still misses grounded targets too often; B shortens recoil,
starts its return before contact and lowers the leap. C is mechanically byte
exact to B and changes exactly four model resources. Its298/348/320/364-quads
Skitter/Warden/Eye/Conductor meshes replace B's698/788/660/824, preserving large
volumes and the shared painted atlas. Scope: work/midnight-flow/scope-b-to-c.json.
Native-scale visual evidence and player acceptance remain separate gates.

#### Reliability and active-route correction (0.28 research)

**Player0.27 verdict,2026-10-19:** combos are slightly better, but the boss is
too easy, appears idle/misses, and the ramp is not felt. Remove Signal House77
and Pump Refuge82 with incoming doors; unfold the map in actual travel order.
This supersedes any implied acceptance of0.27 difficulty or contact reliability.

**Confirmed live spawn selection:** an ABI-preserving constructor probe on exact
0.27 observes native goal type8, selecting Terminal total/live8/3 and Observatory
12/4. The budgets really are selected; the suspected type14 fallback is not the
explanation in these controls. More budget alone did not establish pressure.
Sources: work/midnight-reliability/goals-terminal/goals-live.json and
goals-observatory/goals-live.json; probe SHA/rows retained with each report.

**Confirmed counter defect, bounded inference about carrier.**0.28 pilot B's
grounded base-Y run executes counter74 in reach with active GMB/GAB windows but
records no boss-to-player dispatcher contacts for74. Its normal55 is a positive
control. Pilot C uses the verified136 route for counters, distinguishing counter
versus normal136 by owned descriptor pointer. Its post-ReceiveHit observer
records result4 at sample12 and repeated actual player HP reductions. The exact
native carrier condition remains unknown; authored GMB/GAB and cursor counters
alone were insufficient. Raw controls: pilot-b-press/native-hits-live.json and
pilot-c-press/native-hits-live.json under work/midnight-reliability.

**Confirmed guard duty:** F's current-owned Red run samples1612 state27 /
action13 BlockImpact and431 state26 / action12 BlockIdle rows, versus704 attack136
rows. Repeated native blocks can therefore look like an inactive boss and do
not feed an HP-loss-only response. I queues a counter after12 guard updates,
retaining the normal response cooldown. Native RUN=0 resets only private owners/
slots before the next arena begin/retry; damage, native flags and save stay native.

**Qualification fixture correction:** the older combat wrapper forces word0
0x180FFFDF and grants temporary purchase XP. Fresh normal Continue from the
latest DSV measures a different word0 and XP. New current-owned controls restore
all three actual ability words, XP and starting HP once in disposable RAM after
that menu prefix, then verify them at combat frame0. No research battery is
copied into the actual save. Source: tools/owned_player_lab.py and
work/midnight-reliability/owned-player-profile.json. Old fixture clears remain
labelled; they are not current-owned difficulty proof.

**Candidate K staging:** the early four-live-cost Terminal control is too
crowded; K uses three live-cost while retaining nine total. The earlier Turbine
sector spans several heights, diluting direct pressure. K joins its y96 exit
landings across x70..192 and activates a native upper-tier wave around132/104.
The qualification driver climbs the real steps before clearing that wave; a
floor-only approach would incorrectly report an empty room before activation.
K's current-owned no-refill Terminal/Turbine controls clear, and all18 active
door directions pass. No actor/player placement or time slowing is used.

**Observed final duty/contact:** current-owned F Red samples2054 guard rows of
3627; I after the bounded guard response samples71 of1609 and791 attack rows.
I Red and J Black earn no-refill wins/saves. A no-R attack-pressure control loses
through native damage with a live boss; it is retained as an expected negative
control, not a passing victory. These single-driver observations do not establish
player fun or a win rate. Final K differs from I combat code only in two Terminal
live-budget words; geometry/UI scope and selective reruns are explicit in
work/midnight-reliability/final-scope-k.json.

**Confirmed impulse ordering:** native EnemySM ReceiveHit writes incoming X/Y
velocities at0x02094D54/5C and scales/overrides them through0x02094E04. Existing
state-only poise leaves those impulses active, displacing a committed attack.
A guarded adapter at0x02094D4C skips just that decoded impulse block through
0x02094E08 during owned commitment. Native HP/reaction dispatch continues.
Source: exact0.27 ARM disassembly, tools/midnight_reliability_combat.py and the
pilot's prevented-impulse telemetry. Subsequent I/J current-owned Red/Black
counterplay and native clearance passed, carried into final K with explicit
byte-scope limits in `reference/midnight_reliability.json`. K directly reran the
changed Terminal/Turbine controls, all 18 doors and earned-save Continues.
Player balance/fun and actual DeSmuME pacing remain open.

#### Scoped movement and chapter finish (v0.29.0)

**Source/agent confidence: high on published v0.29/C, 2026-10-22. Exact
qualification/publication scope is in reference/chapter_finish.json.** This is a strict post-pass
over the exact v0.28 ROM, composed by `chapter_finish.py` after reliability.
The original generators, player source/hex and actor bindings remain immutable.
C is independently reproduced through the normal `mod.py` composition. B/C
scope proves exact ARM9, SDAT and all resources except six hoist models; C fixes
front-facing polygon winding in those models. Controls keep their actual ROM
identity and fixture limits rather than being silently relabelled.

**Player code contract.** `chapter_finish_kit.py` reproduces the complete pinned
parent source before assembling the one velocity transform; normal builds read
its frozen hex. Only the first kit code region is replaced/padded. Fixed entry
offsets, route table, state addresses, second block, purchases/dependencies and
the 32 KiB reserve remain. The old source's load/add/store to player motion+0x7C
is replaced by a store of the same clamped correction to actor+0x18; native
physics/collision perform travel. Literal/native-branch/space checks and actual
open/wall/R controls qualify the correction. The v0.28 wall negative goes beyond
the native boundary; C respects it. This does not publish the old crowd backend.

**Skitter authoring contract.** One private actor receives 57 bound lifecycle
routes and a 276-quad mesh, retaining its native rig, shared Forge128 atlas,
material tint and all other actors' bindings. `chapter_finish_motion.py` authors
a shared low stance, carried wrist trajectories, overlapping thorax/head motion,
linear planted steps and a C1 swing. All knockdown/prone/get-up/death modes use
that body; native get-up attack event/sample clocks are preserved. The three
verified melee carriers stay 55/63/68. GMB real activation and GAB windows are
rebuilt with the authored samples. Current-owned native launch/fall/get-up/kill
collects 10 XP and 1024 Q12 health without refills or enemy HP edits; all three
programs cause actual damage on C. Native-scale captures qualify presentation
execution, not player approval.

**Audio scope.** Only existing Skitter SWAR0 rows 791..795 and 820..822 change.
Every other waveform and SDAT file, including sequence/bank rows and native
player/music sounds, remains exact. Frozen PCM comes from the existing owned
CC0-derived bank with short dry envelopes and deterministic processing; normal
builds verify hashes and do not require NumPy. Live/muted lifecycle runs diverge
and are explicitly excluded from subtraction. Direct native-mix waveform matches
cover all eight roles (0.642..0.941 correlation, bounded band/pitch search), with
zero clipped samples in the lifecycle/contact captures. These are numerical
render/mix controls; auditory preference and final fun remain player gates.

**Freight native navigation.** The new helper runs only for the already-owned
Ballast descriptor in room97, outside attacks/hurt/death. Per-slot private state
stores owner/actor and edge-clear, vertical-lift and return/landing phases. Fresh
slots reset ownership; secondary decisions keep an owned navigation jump while
allowing native reactions. Existing roof extents choose a clear edge before the
native jump/velocity impulse. The phase persists through the apex until real
landing; the first pilot's early release was a demonstrated failure. No actor
position, HP, gravity or player field is written. Native controls cover the
original low overhang and the next roof with current purchases. This is not
proof of every possible upper-platform pursuit sequence. Native hoist damage,
phase timing, collisions, checkpoint and saved victory stay unchanged; only six
already-bound machinery/marker meshes improve their visible states.

**Qualification fixture corrections.** A latest copied save can already own all
added purchases. The old OR-only `kit_lab.set_bits` therefore did not create
unowned extra-skill cases. Explicit `clear2` clears only bits74..82 in disposable
RAM before each case grants its declared bits; native/Black/story/unknown bits
remain. Ordinary current-owned controls still restore the measured player values.
No battery payload is edited. Black fresh Continue legitimately settles at
x49.887 on the hoist's quiet approach, outside the former 12-unit Red-only
sphere-radius assertion. Its actual safe floor segment (x0..64), victory
flag and unchanged earned save pass; native Left then X reaches Save Options
on the fresh earned Continue. Keep both original failed fixture reports.

#### Midnight enemy rejection: contact diagnosis (2026-10-18)

The diagnosis/candidate progression below belongs to the v0.24 correction.
Final publication scope is in `reference/midnight_rebuild.json`; later Midnight
post-passes are indexed above. Pending combined tests on an intermediate pilot
are historical, not the status of the published v0.28 composition.

**Native boss meter adapter research (0.24 ->0.25 prototype,2026-10-18).**
Confirmed in-engine: HUDBossMeter is constructed unconditionally as HUD+0x0C
by0x020E0638; HUD+1 controls its lifecycle/update/render.0x020E0A54 toggles it,
0x020E77B4 updates current/max, and0x020E7920 builds/refreshes the original
two-section purple meter sprites. The normal getter0x02063008 uses intrusive
managed references, so a fabricated NormalEnemy boss-interface pointer is unsafe.
An exact config/room/slot/backlink resolver plus scoped HUD update/meter adapters
feeds actual NormalEnemy HP+44/max+48 into native meter+C/+10/+14. Pilot B
renders the original bar while the boss takes real damage. Source:
tools/midnight_encore_combat.py and work/midnight-epic/pilot-b-boss. Meter
lifecycle, re-entry and original-boss isolation are now qualified: full A shows
native Mega Venom's bar with the custom owner inactive; A/B Conductor victories,
cleanup, return and fresh Continue pass. The final catalog scopes the A controls
to B's identical resolver/renderer templates and exact assets.

Pilot B also confirms that increasing boss HP alone retains ordinary enemy
knockdown loops. **Confirmed in pilot D/full0.25 candidate:** poise covers the
committed middle of an owned attack (sample5 through four samples before
completion), the latter part of an actual native get-up, and36 decision updates
for its counterattack. Anticipation/recovery outside that counter window,
knockdown/get-up, web interactions, actual HP damage and death remain native.
Both decision passes must agree, just as with owned airborne programs. Full
Red/Black traces contain16/13 actual HP losses while attacks stay in state15;
poise does not grant health invulnerability. Both forms earn native victories
and saves without player refills. Source: tools/midnight_encore_combat.py,
work/midnight-epic/poise-native-damage.json and selected catalog controls.
Player presentation/fun acceptance remains open.

**Freight recovery correction (0.25 candidate A -> B,2026-10-18).** A full
native mixed run reaches all three Crane species but exposes a live Maw beneath
the recovery walkway x60..84/y-12. Its centre stays near y-20.8 (native floor
below); native jump/land actions38/119 repeatedly strike the slab's underside.
The player on the walkway cannot reach it. This is an actual escape defect,
not proof that the accepted room needs replacement. The prior recovery path
only owns Spore. Candidate B extends that exact room97 walk-to-clear-edge /
native-impulse vault to Maw, admits native Land state7 before the walk, and
uses its own tell sound. No actor/player position is written. ARM ownership,
native jump/velocity and unchanged hurt/death/HP are unit-tested. Fresh B mixed
play now observes two native Maw escapes onto deck and clears all three
species, including the previously unreachable spawn. Positive-control evidence:
work/midnight-epic/maw-native-recovery.json and full-b-mixed-freight. Raw failed trace:
work/midnight-epic/full-a-mixed-freight/creatures/creature-duel-mixed-red-kit-full-a-freight-039e9646.json.

**Confirmed static defect in published0.22.0..0.23.0.** Forge geometry replaces
attack volume dimensions and GAB pairs but retains resampled native GMB channel3
word5 activation. GAB pairs/cursor contact counters are insufficient: the native
collision test uses GMB word5 too (see player animation rate/contacts). Actual
0.23.0 private GMBs show Skitter Railcut shapes at11..13/19..21 but active bits
at16..18, Switchback shapes19..24 but active25..26, and Warden Toll march,
Ballast Hull charge and Conductor Storm verdict have **zero** active samples.
Many other windows only partially overlap or are entirely disjoint. This
supersedes earlier claims that selected volumes and GAB were authored together
completely. Counters only established cursor crossings. The old pinned
post-passes remain immutable; correction belongs to a new composition.
Source: direct parse of exact0.23.0 XBD-selected private GMBs with Gmb/CompressedBlob;
new work/receipts under `work/midnight-rebuild`. In-engine actual damage and
presentation qualification is still required after correction.

**Confirmed audio ownership path (0.23.0 probe, 2026-10-18).** Many actor
sounds are queued spatially: actor method callsite0x020746AC -> offset thunk0x0205E6A8 -> request
0x0203F348 -> deferred update0x0203F3A4 -> guarded helper0x0203D5B8 ->
player0x0203D5E4. Filtering by final LR sees only the deferred helper and loses
owner context. A compiled read-only request observer shows R7 at0x020746AC is
the actor: enemy vtable0x021301D0 with exact private config at+40, while player
footsteps/hurt vocals have vtable0x0212E3F0. Example native Skitter requests8..12
remain beyond the old306..328/457..501 voice filter; player hurt392..396 must
remain native. Source: `work/midnight-rebuild/motion-a/audio-context-skitter.json`.
New custom sound handling must scope at the actor request and preserve player /
unrelated actor calls, rather than muting whole room-wide ID ranges.

**Confirmed new prototypes (2026-10-18).** The isolated Skitter baseline
completed15 full programs with zero player HP drops; aligning native activation
restored real slash/rush hits. The shorter whole-body pilot lands all three
programs, including a low1.35-Q12-unit/update pounce that reaches a grounded
hero. Original3.2 impulse sailed above him. Source: baseline-skitter,
contactfix-skitter, motion-a and complete-pilot reports under midnight-rebuild.
The observed animation clock advances about one sample per2.2 emulator video
frames; shortening clips fixes cadence without changing the global clock.
Native base strings interrupt into37 recoil,41 knockback,48 HurtFall,49 HurtLand
and51 HurtLandGetUp.48/49 are continuation reactions; repeating hurt vocals on
every fall/landing entry is excessive. New audio suppresses that repetition.
Exact XBD actions158/134/20 are Walk/Run/Crawl;1..3 are not enemy locomotion.

`room_envelope.py` adds sloping empty-room boundaries after the compiler's two
Z-slab nodes, retaining preorder and native solid-leaf face lists. Model cuts,
collision planes and map raster share one convex polygon; nonconvex L/T/stair
shapes remain box unions. The Observatory prototype's sloping sunken floor is
crossed and returned through native input. It supplements the first corner-only
prototype, which passed doors but did not establish sloping floor behavior.
BSP list parity controls total length modulo4. A redundant far-exterior split
preserves the old residue without appending invalid list bytes, keeping all
later native model resource offsets aligned. C lists813 regenerated resources;
that list includes payloads identical to the parent, so it is not a count of
changed bytes. Its32KiB kit matches0.23 exactly. All22 native Midnight
door directions pass on C. Final combined roster/audio/art composition still
requires its own qualification; these facts are agent evidence, not acceptance.

**Confirmed live carrier correction (F, 2026-10-18).** Warden's authored
March still caused no HP loss after fixing GMB active bits and beginning it on
settled ground. The private GroundRangedAttack1 carrier is not equivalent to a
melee carrier; valid XBD flags/GAB alone do not establish a damaging path.
Rebinding the program to the existing private RunAttack136 carrier restores
actual HP loss without changing its intended windows/low pulse geometry. Ballast
charge uses the same verified carrier; Conductor verdict uses DropDownAttack30.
F observes damage in all three Warden/Ballast programs and all four Conductor
programs, followed by native base-string clears. Original/shared XBDs remain
unchanged. This supersedes Forge's broad claim that action slots are universally
interchangeable; the exact additional native carrier condition is not decoded.

A scoped gate in the verified private thinker requires observed actor condition
bit80, a settled0..3 controller state and zero Y velocity before a *new* ground
program. Owned programmed jumps still execute. This prevents ground windups
interrupting a navigation hop/fall; native hurt/death and unrelated actors keep
their original paths. The fixture's Crane approach also needed real R inputs to
pass a blocking actor and enough budget for the subsequent duel; its earlier
walk-only timeout is not a ROM crash. These failed D/E diagnostics are retained.

**Pose correction (G).** FK review found the heavy downstroke's IK clamped its
wrist near y4 while targeting the floor. Whole-body crouch/forward loading now
puts Warden's wrist near2.05 (bell bottom~0.55, planted feet0.65), Ballast near1.8
(fist bottom~0.7), without stretching bones or changing native movement. The
Conductor's Fugue instead conducts with alternating open arms; Crownfall has a
loaded landing. Arm/body motion and impact samples remain continuous. Static
poses alone do not establish the final in-engine presentation verdict.

**Final0.24 composition (J, 2026-10-18, agent evidence).** All813 regenerated
resources parse/round-trip;570 payloads actually differ from0.23 (230 SCA,
234 GMB,55 GAB,17 NSBMD,10 BSP,11 CBMP,10 OBJ,one NSBTX,two strings).
The first two SDK autoload rows,32KiB player kit, original character bindings /
clips and all Crane room resources remain exact. Only three SDAT files change:
SSAR0, bank20 and SWAR0. Independent full production reproduction yields the
same ROM. F/G/I have identical ARM9 and sound-bank bytes to J; explicit private
resource comparisons carry Skitter/Maw/Eye, Warden and Spore contact evidence.
Final J Ballast observes HP damage from55/63/136 and clears natively. Native
mixed Observatory clearance covers all three Midnight species on the sloping
floor/rooted terraces; Freight covers all three Crane species. All22 directed
Midnight doors and the reverse stair/tower and boss-return routes pass.

**Controller qualification correction.** A passive Ballast probe stood above
the Freight overhang without seeing any selected attacks, then cleared the
actor, causing the old route-only `passed` flag to be misleading. A second
probe backed into the crate at x108 (hero stops104.47), keeping the actual gap
below16 and never selecting charge. Both are excluded. The current lab requires
actual HP hits from every programmed action and supports a native approach
destination; the x32 ground approach covers all three. J still shows repeated
Ballast navigation hops when the hero remains directly above a Freight
overhang; ground attack coverage does not establish complete elevated pursuit.
The focused native R control also has HP drops outside the six avoided active
windows, so it is not a no-damage run. Source: J contact/roof/mixed reports in
reference/midnight_rebuild.json; the raw failures remain under work/.

The earned hoist return needs native crate/beam landings `(190,41)`, `(144,61)`,
`(94,23)`, `(50,5)` before its approach sphere. The generic navigator loops under
the low roof at x209..223. This was a controller failure: the explicit native
route succeeds after a real no-refill victory, saves, and fresh Continue retains
victory142 at x36. No post-victory position write or research save reaches the
actual battery. The separate no-refill hoist controls use labelled copied-save
Vitality/kit purchases; the Conductor controls use the native19-unit maximum.

#### Chapter spectacle implementation (v0.23.0, 2026-10-17)

User authorized implementing the chapter evaluation. `chapter_spectacle.py`
is an immutable0.22.1 post-pass; helpers own art, events, combat, audio and labs.
Its runtime uses Forge's verified zero tail plus a1KiB extension of the existing
descending autoload row. The loader/first two SDK rows and32KiB kit remain exact;
the row length/table pointers and arena lower bound grow together. Forge's
default thinker/model generators remain byte exact; opt-in template/sculpt
parameters serve the new composition. Existing native damage/interrupt priority
and exact actor/config ownership checks remain authoritative.

Confirmed on runtime-only48fc9cbb, copied latest DSV/native mixed roster: both
Terminal approaches reach elevated enemies and execute attacks; Warden reaches
36.55 units and246 attack samples in one observation. This uses healing, not a
difficulty control. Physical ground-detach/velocity hops and measured obstruction
steering replace suppression for reachable elevated targets. The initial room
arrival remains a lab fixture; no player-coordinate writes are added to shipping.

Pilot87f27f77 proves open Terminal foreground beneath real25-unit carriage roofs,
native Engine House lever progress and real guarded hoist HP victory/half-health
phase. Initial machinery foreground depth hid the hero during melee; repair moves
the motor/guard behind the play plane and reduces their decorative extents.
Lamp panels must be inside the lever camera frame to prove the power-up visually.
The first gear annulus had clockwise front faces and was culled: reverse the
ring order for outward+Z. New runtime ownership/flags tests cover saved/scalar
model selection, native fallbacks, roster cycles and post-native-HP phase reads.
The ARM probe now decodes rotated immediates and shifted operands used by these
adapters. Native LR is caller-saved; returning through popped PC need not retain
the input LR word. Latest candidate/qualification state belongs in TASKS.

Confirmed map regression in0.21..0.22.1: renewal recompiled all32 descriptors
with `room_minimap.projection(plan)`'s default area5, including Crane96..107.
Actual Engine/Arm captures therefore selected Midnight Line's overview/title.
Crane's original generator correctly uses area6; the new post-pass restores6
for all twelve Crane descriptors and5 for Midnight. The four existing Crane
progress screens gain an Arm save marker without changing room/palette/list
allocation. This supersedes earlier blanket claims that renewal's map metadata
was correct merely because door navigation passed.

Terminal roofs now have an open foreground and solid22..25 roof slabs. A
ground pursuer cannot jump through an overhead slab: it must reach a clear
carriage gap, rise vertically, then steer onto the roof. The new scoped route
commits its exit direction until reaching that gap, avoiding an engagement-range
oscillation at its edge. New contexts also narrow the ranger's elevation band
so it descends rather than firing horizontal lanes above a target below.
Raw before/after probes and failed driver controls remain under
`work/chapter-spectacle`; source/ROM qualification must name its actual candidate.

The native second decision pass can replace navigation with Land7 or Leaper28.
For private Leapers,28 binds action122/LeapAttackPrep, not a hurt reaction;
the earlier blanket26..53 interpretation was conservative and incomplete.
The new primary/secondary guards exclude that prep decision while retaining
37/38 hurt, death53, stale owners/configs and unrelated actors. Owned gap-escape
and rising phases retain their physical movement through navigation decisions.
Do not infer animation freeze from a zero+178 cursor on Land/Prep: those action
rows have no GAB, so that cursor alone cannot describe SCA playback.
Measured3.4-unit pursuit impulses peaked below the new roof's standing height;
the final calibration uses4.0 for pursuit and4.6 for actual obstacle recovery. G/J roof probes confirm actual ascent and attacks.

Captured PCM on G/H exposed a separate event-sound integration failure: the
new room cues710..718 were requested but rejected before the sound adapters.
OBJ opcode22 at `0x0203A894` checks its u16 ID against582 before constructing
a handle; its helper `0x0203D5B8` checks582 again. Forge's direct sound-handle
player bypasses both guards. A trial changing only the second guard (I) still
failed mixed PCM: weak template correlations are incidental, not playback proof.
The revised event adapter calls Forge's complete native handle player only for
710..718 in private rooms76..107; every other request restores the exact native
prologue/continuation. Native bounds/data stay unchanged. ARM ownership/ABI tests
cover both ends and native fallback. Requalify actual mixed PCM before accepting
the new composition.

The Crown full-roster controller can be knocked through its left retreat door;
continuing to chase enemies in the next room cannot qualify Crown's flag146.
The lab now checks its room, returns through the reciprocal Gantry hatch and
uses native jump/evade to reposition near the exit. These are controller inputs,
not shipping collision/HP/actor writes. Native Brute action91 resolves to
`brt_HurtLandGetUp.sca/.gmb` in the clean XBD: observed state51/action91 is a
get-up, not proof of front blocking or frozen animation. The first incomplete
Crown attempt and its last target-room observations are retained.

Final Crown staging correction (K): the old8-cost repeating heavy roster drew
out the second native hunter wave. Observed full native reinforcements include
roughly60-HP Ballast,42-HP Maw and26-HP Spore; config HP is before native scaling.
Use the three-role cycle36/20/21 and4-cost budget for each native wave, retaining
the existing first-clear/reinforcement/final-clear callbacks. K differs from J
by exactly three ARM data bytes; every instruction, room/door/map/script,
animation, model and sound byte is identical. Keep J's directed-door evidence
with this explicit scope proof; qualify K's actual Crown clear, unlocked hoist
door and native approach save before publication. No enemy HP is capped.

K's native Crown clear and unlocked hoist door pass. The first attempted save
after that exit exposes a lab timing trap: the room number changes before the
player initializes, so `travel` accepted a transient0,0 using its previous left
direction. The hero ultimately stood at18, outside the sphere; a RAM flag check
alone incorrectly appeared successful. Fresh Continue correctly returned to65.
Keep that failed control. Wait for settled arrival before walking to36/X and
qualify persistence through fresh Continue. A focused continuation may preset
the separately earned Crown flags, but must label that fixture rather than
claiming an uninterrupted fight/save run. No game/save-format fix is required.

Final published K qualification: native Crown clear/unlocked door pass; the
settled checkpoint continuation and fresh Continue retain Crown146 while
hoist142 remains clear at the safe36-unit default spawn. Separate fresh K
Continue controls retain both boss victories. Strict clean production replay,
version pins, actual battery/checkpoint bytes and rollback metadata all agree.
The catalog names inherited J door/Red boss/PCM controls with the exact
three-byte Crown-only scope. Player fun and actual DeSmuME pacing remain open.

## Campaign branches and Crane Row

The initial 2026-10-13 survey below was research only. Crane Row shipped in
v0.16, with later terrain/creature/navigation/reward changes and shared passes
through v0.24, retained by v0.28. Those dated sections follow the original survey.
The Grid/Skyline and other proposed branches remain deferred. Current shipped
behavior is in CHANGES; design is in [the roadmap](TASM_ROADMAP.md#deferred-work).
`reference/area_roadmap.json` labels current status separately from its historical
capacity baseline and v0.19 implementation receipt.
Original survey builds under `build/area-research/` did not change production.

### Native survey, entrances and materials

`work/area-research/native_probe.py` reads the clean ROM through existing
parsers; `native-survey.json` records all 75 room associations, exits, spawns,
named entity metadata, event variable references and texture names. All 75
OBJ/BSP/texture associations round-trip; entity/event sections round-trip and
BSP trees pass their checks. Unsupported camera/anchor layouts are recorded as
unknown rather than forcing the bounded authoring reader onto them. Entity
labels and variable references alone do not prove accessibility or ability
gates. Native descriptor area words can be zero in the file and populated at
runtime: never infer district order from those raw words.

The observed real DSV was `f9edc1cd...`, room65, mission28, ability word
`0x180FFFDF` (story bits 0..4, no bit5/Sledgehammer Slam). It was read, not
modified, and its bytes were rechecked. The signature occupies 16 bytes before
the checksum: reading stats at +16 mistakes the checksum for the room number.
Do not infer visited rooms or material permission from such a misaligned read.
The survey's visited evidence is native saved flags, not proof of a new route.
Previously player-confirmed Nest material use remains recorded separately.

`native_controls.py` uses the existing kit lab, a copied research battery,
disposable entry warp and the same story bits. Fresh runs in Pier_Save02 (38),
Downtown_Save03 (16) and Residential_Map09 (48) render/update; screenshots
were inspected. These are native-room controls, not new doors or continuous
story-access proofs. Reports: `native-pier-save02.json`,
`native-downtown-save03.json`, `native-residential-roof09.json` in that folder.

- **Pier_Save02:** one existing left exit to Pier_Map04, save sphere, unused
  right wall. Native input-only walking reaches x56.469 at y4.980 and stays
  bounded. Proposed appended touch trigger at x61 with width12 follows the
  existing Sewer_Save02 entrance pattern (inner edge55); a new return spawn2
  near x55 is a candidate. Actual trigger/collision overlap, visible doorway
  and input-only two-way transition still need testing. Pier_Save03 is another
  one-sided save-room candidate; it has not been observed in this session.
- **Downtown_Save03:** both side exits lead to Downtown_Map12 and must remain.
  Native save area is around x30; investigate a separate rear service door with
  a button-press trigger, away from the save prompt. The script can name a room
  transition, but X-operated portal behavior here has not been proven.
- **Residential_Map09:** upper arrival spawn3 is (135.685,242), observed player
  position (135.685,244.981). Retain the original Downtown_Map09 connection,
  sewer grate and ichor wall near (77.708,240.311). Exact new roof-access
  geometry and return path are open. Residential_Save02 is the alternate:
  both side doors are occupied, so do not retarget one as a shortcut.

Concrete material candidates are validated dictionary entries in already-seen
rooms: Pier_Map04/06 (`Pbeam01`, `Pcrate01`, corrugated metal, `skyline01`),
Downtown_Map07 (`officeWall`, `tileFloor`, `officeCLights`, `computer`,
`ElevatorDoors`) and Residential_Map04/09 (`Wbrick`, `metal01`, `vent01`,
`skyline04`). `borrow` preserves their native formats, including format5;
recompression/HD assets are unnecessary for the initial layouts. Room compiler,
far backdrops, collision, cameras and anchors remain the authoring path.
No Hive_Map08..10 or Downtown_Map13/14 material is authorized for early branches.

### Shared room and flag capacity

Reusable audit: `python tools/area_capacity.py --rom
build/Spider-Man-WoS-modded.nds --build-report
build/version-0.15.1-final/Versioned.build.json`. It checks exact ROM/report
identity, reconstructs the published room-table block byte-for-byte, and packs
hypothetical additions in its own process; no ROM/save/source is changed.
Tests cover mismatched release identity, allocation collisions/occupied flags,
the real plan ledger and current table-growth boundary.
All eight new tests and the full 308-test suite pass; consolidated research
checks and source/battery identity are in
`work/area-research/research-verification.json`. Full suite output is
`work/area-research/unit-tests.log`.

At v0.15.0 there are 20 added rooms, 76..95. Tables/map/messages/visited stub
end at **3,584 bytes**, leaving **128 bytes before the Roof adapter** in the
4-KiB block. One placeholder room plus one list record packs with four bytes
left; three rooms do not fit. Nine placeholders with one record each pack at
4,668 bytes in an 8-KiB reservation, leaving 3,140 before the relocated Roof
adapter. This omits extra dialogue, copied parent-area lists and exact final
names/diagram entries; it is a packing result, not a runtime guarantee.

The source pool minus released local/room/visit allocations leaves **21 flags**:
140..149, 152..161 and 245. The current visited function permits rooms96..105
(flags161..152); room106 would collide with Leech's flag151 and is rejected.
The proposed nine-room ledger uses visits161..153, completions140..142 and
Grid power143: 13 flags, eight left. These numbers are unallocated proposals.
Before integration, reserve milestones out of `LOCAL_FLAGS` or the clone
sanitizer can claim them. Any further Midnight growth requires revisiting the
shared ledger. Do not count ability bits, scalar IDs, flag padding or unexamined
276..290 as available storage. Hive needs further flag/allocator research.

`capacity_build.py` made an unpublished **reservation-only** control
`build/area-research/capacity-8k.nds`, SHA `d6040312...`. Its Glob is identical
to v0.15.0; it changes the autoload reservation/arena lower bound by 4 KiB and
relocates the Roof and Signal-core adapters, preserving their scoped hooks.
The native SDK entries and existing room/map/message prefixes stay intact.
The larger block boots and passes `midnight_walk run substation-save` (7
checks), including both bay/Switchyard doors. Native Service Bay Save/Yes ->
fresh Continue also passes all six checks, restoring room95/visited162 with
copied batteries (`capacity-save-test.log`); the three native-room observations
above pass. This is limited qualification: heap high-water, long combat,
Leech/Roof adapter behavior, new rooms/maps and broad regression remain open.
It must not be substituted for a fully qualified release. Reports:
`capacity-build.json`, `capacity-audit.json`, `table-budget.json` and
`work/midnight-line/walk-substation-save-d6040312.json`.

### Crane Row scope check (2026-10-14, pitch only)

The player selected Crane Row and requested a substantially bigger, more
impressive design, pitched before construction. TASM_ROADMAP now owns the
twelve-room Hanging Harbor concept; `reference/area_roadmap.json` replaces
the unbuilt nine-room shared allocation with a Crane-only provisional ledger.
Grid/Skyline keep their concepts but have no reserved IDs now. No new scene,
entrance, animation or ROM was built during this pitch.

`work/area-research/crane_scope_probe.py` reads exact v0.15.1 `160d01cb...` and
its build report. It reproduces the current room table byte-for-byte: **64
bytes free** before the current Roof/core adapters. The v0.15.0 reservation
control `d6040312` remains historical; it does not qualify v0.15.1 adapters.

Planning-only packing trial: ten placeholders use4,784 bytes; twelve use
**5,024 bytes** in an8-KiB reservation, leaving **2,720** before the current
448-byte adapter tail. Neither fits4KiB. Exact final names, dialogue, extra
parent-map records, mapper code and runtime heap headroom are additional
costs/gates. The native Pier list alone adds260 bytes; new room records were
already counted once in the placeholder trial. Report:
`work/area-research/crane-scope-2026-10-14.json`.

The trial temporarily substitutes only a Python visited function, retaining
every released room's assignment. Proposed rooms96..105 use161..152;
106/107 use149/148. Seven milestones/crew/reward reservations140..146 bring
the total to19 of the21 currently audited unused flags, leaving147/245.
All are proposals, not writes to saves or an engine allocation. The normal
`ch.visited(106)` still raises. Building needs an explicit mapper, matching
init/map/save handling and exclusion of all reserved flags from LOCAL_FLAGS.
Further districts require more flag/storage research rather than silently
reusing the old Grid/Skyline ledger or ability bits.

`area_capacity.validate_proposal(..., visit_overrides=...)` validates such
draft mappings and reports `requires_visited_mapper_change`; it cannot alter
released visits or excuse occupied/unaudited storage. New tests verify those
guards and that the live allocator is unchanged afterwards. All11 area-budget
tests pass. This is tooling/planning validation, not new-room qualification.

Large-room targets are360..420 units wide and up to224 tall. The compiler's
511-unit model width includes the full geometry/backdrop/shell bounds, not
only the walkable interior: leave margins and check actual compiled output.
Targets correspond roughly to six/seven camera widths or five view heights;
they do not prove traversal time, performance or good use of the space.
The45–60-minute first-exploration goal is unmeasured. Prototype the hub's
multi-level camera/anchors and the grounded-ship silhouette before filling
all twelve scenes. Individual detailed maps plus a readable district overview
are required; a tiny twelve-node sketch in the old spare strip is not assumed
sufficient. A dedicated local overview would need scoped map research; no
unused seventh area row has been established.

Moving counterweights, a moving grabber and its protected/recovery damage cycle
remain unproved. Keep v0.15.1's lesson: native animated bindings provide hit
geometry; changing a smashable to static-renderable made it invulnerable. A
separate visible machine mesh needs a correctly aligned native hit/damage
target and cleanup, with measured warning/live windows in real captured
frames. A long approach can lead into local camera-sized combat pockets;
never infer that room-wide offscreen attacks are readable because the model
is large. A fixed-geometry route can be validated while those prototypes run.

The interactive planning diagram is copied to
`work/area-research/crane-row-pitch.html`; it is schematic, not game footage
or a map asset. Its selection/links were checked at320 and736 pixel browser
widths; final phone/normal layouts have no horizontal overflow. Full designs,
roles, connections and targets remain in the repository documents/catalog.

### Crane Row construction and qualification (v0.16.0)

Player approved the full Hanging Harbor pitch on2026-10-14. Sources:
`tools/crane_rooms.py` (twelve plans/scripts), `crane_row.py` (post-pass),
`crane_boss.py` (native adapters/machinery) and `crane_walk.py` (copied-save
lab), plus `crane_boss_lab.py` for controlled measurements. Candidate
`39fcf89e` is published as0.16.0 and agent-qualified; no player verdict.
Parent is v0.15.1 `160d01cb`; actual battery `3a4e7c9b` at startup.

**Integration decision:** append an independent8KiB block at0x02158420,
after the existing4KiB Midnight block; preserve that block byte-for-byte.
Copy the96-entry lookup and append descriptors96..107; native sentinel75
stays null. Redirect the room lookup and raise only the two save/reload
guards to108. The new map visited stub retains native flags below92 and
Midnight165..162, then uses161..152/149/148. Milestones140..146 are Crane
private. Kit code/ownership stays intact; its existing room76..115 strength
dial receives only the twelve new rows. All unrelated Glob resources remain
exact; exceptions are appended assets, generated filename table, version/
appended strings and the append-only Pier_Save02 entrance.
The payload uses5008 of8192 reserved bytes. `crane_row.py` owns the full
release generator; `tasm_kit.py` remains the exact0.15.1 parent component.
Future kit changes must rebase the Crane parent guard/profile deliberately,
then qualify the combined game instead of replacing it with a kit-only ROM.

**Map6:** a new owned seven-row area table copies the native five rows and
Midnight's row/list, then adds Crane's overview/list/title. Four native table
base literals redirect to it; the two map bounds6 become7. Prepopulate the
native screen/title fields because static initialization originally fills
them later. Native world overview still draws its five original districts;
Crane has its own local overview and per-room detail maps. Native map-item
ownership bits are untouched; Crane's local map follows the chapter's
unlocked extra-area path. The current diagram uses22 entries for12 rooms
because of palette/cell boundaries. Do not force it into Pier's spare strip.
Old appended message entries are copied exactly into an owned contiguous
extension; native IDs stay native and new message bounds remain below256.

**Native doors/save:** first candidate `5e1ae3d5` entered room96 but its
return spawn55 overlapped the new Pier trigger and bounced back. Spawn44,
facing left, fixes it. `b06cc015`/`221d4b7a` pass native Pier38 -> Quay96 ->
Pier38 by walking, plus Quay->Freight97 across the actual container route.
Office98 Save/Yes -> fresh Continue passes all six native checks, restoring
room98/visited159. Reports under `work/crane-row/walk-pier-entry*.json`,
`walk-cross-AR_CraneQuay2*.json`, `crane-office*.json`. All30 directed Crane
door cases subsequently pass on `3624afd5`, including the Pier connection.
Never overwrite a ROM while its lab run is
active; keep named immutable candidates and hash-qualified reports.

**Movement/runtime:** native world-object get-position is0x02069D54
(out vec, object); set-position is0x02069CE4 (object, vec). A scoped hook
before hazardous-object update0x02069980 moves only the custom flashing-
hazard kind0x12 in rooms102/106, then restores registers/executes the original
prologue. Counterweight snapshots on `221d4b7a` advance y54,60,66,72 at
twelve-captured-frame intervals: one unit per native update/two captured
frames. The mesh is behind the play plane; fixed catwalks provide traversal.
This does not establish a rideable moving platform. Initial kind0x14 did not
produce the observed mover; use an instantiated native kind, not an assumed
spare slot. Final warnings use native electric kind0x11 with private harmless
data only when spawned during MODE1; live-phase0x11 spawns retain native
data. Each actor stores its selected data pointer. The motor marker uses
harmless fire kind0x13; guard uses box0x1F. No model override changes native
objects outside room106 (or the weight's explicit room102 scope).

**Hoist:** one native animated core keeps its complete hit binding, HP36
health units (36*4096). Separate authored motor/guard/grabber meshes avoid
the v0.15.1 static-core hitbox failure. Native world HP subtraction entry
0x0206AFA8 is guarded only for kind0x21 in room106: native code runs while
room scratch0x128==1; protected hits preserve HP. Original callers elsewhere
retain their prologue/path. Script owns one warning -> committed impact/
sweep -> exposed recovery loop, with every delayed hazard action checking
RUN and defeated on execution. Native delay units are two captured frames.
The first flow candidate `a6fc0876` used player healing and did not qualify
difficulty. Later native strikes win without lab refills; qualifications
label purchases explicitly. Type7 player-collide boxes select a lane before
the warning commits; a type5 experiment never changed the zone. Sweep steps
last32 native delay units per32-unit travel, matching one unit per update.
Native table8 support is stopped after45 delay units: an opening crew,
with no later replacements. Living adds can survive spawner deactivation
and victory; the exit opens immediately and room change removes them.
A scoped weak-reference adapter
extends the previously proven Roof zero-HP NormalEnemy cleanup to Crane;
other rooms chain to the original Roof adapter.

**Geometry/lab pitfalls:** upper catwalks touching outer walls blocked the
climb beneath their undersides. Current plans leave12-unit side climbing
channels and arrivals inset18 so native wall crawl reaches high doors and
arrivals land inside ledges. All upper hatches use native button mode0/X,
with an original painted X marker; ground exits retain walk-in mode2.
Otherwise climbing past stacked doors or descending from an arrival can
unintentionally return through another exit. Crown's first catwalk moved24
to32: the former9-unit gap over its crate genuinely trapped Spidey's head.
The navigator separately needed neutral inputs immediately after arrival,
Down to descend a wall, and release frames between B presses. A held-B
controller failure is not evidence that a native jump is impossible.
Scene-view placements are
not traversal evidence. A pose at x88 between alternating shaft platforms
fell to the floor, so use an actual landing (e.g.100,37) for captures.
NormalEnemy scans retain freed actors after room transitions; lab observations
must verify motion back-pointers, live state and bounded room coordinates.
Never change game AI/waves based on such stale observations.

**Scale/horizon control:** `scale-control-e` (`4041a3bb`) changes Quay only
to a wider far backdrop, forcing native model vertex scale128. Foreground
scale/collision remain correct in game. The compiler supports64/128/256/512;
the old511-unit width note was the scale64 case, not a global engine cap.
H (`6705b394`) uses640-unit far scenery throughout the outdoor district.
I (`b2b50dfb`) replaces the skyline's stretched black bottom row with an
authored far water face; its ARM9 is byte-identical to H (`b0b6663d`).
Full normal composition `integrated-h` matches standalone H exactly.

#### Hoist controls and test accuracy

**Combat qualification distinction:** F (`1be9fb7f`) Red wins by real
inputs at frame2517 without refills, ending at81 Q12 HP from24576. Early
tests labelled Black did not assert the suit and cannot qualify it. The
previous Leech qualification used extra
shop purchases (`bits2=0x7fc00`), including Vitality I..III. Crane now labels
the three Vitality purchases explicitly `--purchased-vitality` (`0xe000`).
Vitality reduces incoming damage; the observed Q12 HP maximum stays24576.
`--purchased-kit` reproduces the prior full-kit fixture (`0x7fc00`). These
fixtures never edit a real save. Starting-health driver failures are not
player balance verdicts. Final Black (`39fcf89e`) with Vitality III wins
without lab refills, then passes700-frame hazard cleanup and a real exit/
revisit. Existing native health gains are allowed; a safety window must
reject any observed HP drop rather than reject harmless recovery.
Guard control H preserves147456 HP during protected strikes and loses
2048 during exposed strikes, but the first paired control was inconclusive:
the solid guard also prevented the test driver reaching the core. Final
`3624afd5` paired controls invoke native HP subtraction once from a saved-
register world tick in disposable RAM, masking exposure while the physical
guard is open. Patched protection preserves147456; restoring the original
native HP prologue removes exactly4096. Exposed native calls remove4096
in both runs. The probe uses unused Crane-tail RAM, never the ROM or player
save; physical hit binding is separately proven by actual-input victories.
Reports: `walk-control-{guard,guard-native}-3624afd5.json`; final adapter
relocation is rechecked on `39fcf89e`.

**Placement trap, not a measured damage radius:** early nominal x328
holds actually stood at336.6 after the setup jump retained horizontal
movement. Their12288-Q12 loss therefore did not prove damage in the gap.
Reducing arc count did not change that misplaced control. Correct setup:
settle the native stance, place once more while idle, wait, and assert the
actual coordinate before measuring. Suppress the crew using zero spawn
costs in disposable RAM to isolate environmental damage. On `39fcf89e`,
actual x328 and392 each retain24576 HP for1500 captured frames and remain
at their marked coordinates. Both have green floor marks. At actual312,
110 warning frames cause no damage; the live impact then removes6144 Q12.
One native live arc occupies each warning centre; warnings use the native
electric family with damage flags cleared. Do not infer active hazards
from retained allocations, or collision widths from nominal fixture names.
Reports: `walk-control-{safety,cues}-39fcf89e.json`.

**Driver lessons:** confirm Black form after a six-frame L press; earlier
one-frame, unasserted switches cannot qualify Black. Vitality is three
purchases, not seven. Do not fire Y during the entire approach: native
combos stop ordinary walking. The hoist's native core/guard blocks walking
through it; a normal jump from x332 reaches its right side, where the driver
faces left to hit during recovery and returns to the x392 refuge. Live
combat HP/core reports prevent mistaking that positioning failure for
immunity or an encounter balance problem. Native table8 has finite spawn
cost target0x8000/simultaneous0x4000, not an infinite respawn budget.

**Final regression scope:** `3624afd5` passes all30 Crane/all13 Midnight
real-door cases and12 crash seeds. The same ARM9 on `6705b394` passes68 kit
checks. Final `39fcf89e` changes only three Long Arm resources (model,
textures, OBJ), the owned Crane extension and three adapter branch targets.
All collision, map, door, kit and other resource bytes remain exact. Final
native gate/snare/Black behavior matches that baseline. Data-gateway tests
execute every other room/kind combination against guarded memory, preserving
arguments and native fallback; warning/live selection and null guards are
also exercised. Audit: `work/crane-row/final-{equivalence,native-parity}.json`.
Office native save/Continue remains valid; actual earned flag142 is saved
at Office98 and restored by a fresh emulator load on the final candidate.
Final Red full-kit/Vitality and Black Vitality III victories both pass
post-win hazard windows and real exit/revisit without lab refills. Native
health gains do not constitute damage: `HealthWindow` samples every read,
allows recovery and rejects any intervening decrease. Its separate three
unit cases prevent a heal-then-hit sequence hiding above starting HP.
Native near-death recovery also passes. The copied save's first-death
tutorial needs a touchscreen acknowledgement, and its orb-result popup
needs A before play resumes; an unattended popup is not a frozen level.
Publication is byte-exact with battery `3a4e7c9b` unchanged, wrapper/snapshots
verified and prior/active compositions retained (`publication.json`).
Pacing45–60min remains an unmeasured design target; moving weight is scenery,
not a rideable platform; player feel/performance remain unconfirmed.

#### Crane Row visual polish (v0.16.1)

User requested an ambitious visual/feel sweep before their first Crane test,
2026-10-14. `tools/crane_art.py` owns deterministic original16-colour pixel
materials and scenery: riveted steel, quieter deck plate, hull seams, water
glints, practical lamps, amber girders and small signs. `crane_rooms.geometry`
uses them without changing any solid extents/depths, anchors, camera polygons,
door/input modes or encounter scripts. Lattice crane braces face +z at every
slope; rails/supports and ship fittings stay behind actors, while cargo trim
stays inside the original solid silhouettes. Scenery contributes no collision.

The three visited-Pier skyline pictures now form one broad672-unit panorama
at z-170, rather than eight small cycling tiles. Original mid-distance cranes,
boats, hull windows/superstructure, cargo fittings, power pipes, shaft rails
and a warm office give individual rooms landmarks. Catwalk lips, low rear
rails and underside struts clarify landings; the hoist backdrop keeps the
native warning/motor/refuge positions. Signage and shorter first-visit hints
name the office, power objective, upper loop and final-arm route. No new skills,
enemy balance, hazards, player movement or slow effects are introduced.

Final candidate `5b0d6f55` at `build/version-0.16.1-qualified/Versioned.nds`
has ARM9 **byte-identical** to0.16.0 (`abfbb112`). Resource names/IDs are
identical; exactly24 Crane NSBMD/NSBTX resources and English/American strings
change. All BSP/OBJ/map/machine-model/native/kit assets stay exact. Audit:
`work/crane-row/polish/audit.json`; before/art-A/final emulator surveys are
in the same directory. `tests/test_crane_art.py` checks deterministic lossless
materials, brace winding, landmark depth, non-degenerate scenery and conservative
budgets (<400 quads,128KiB texture pixels/indices,16KiB palettes per room).
First art-A inspection led to softer deck highlights and a warmer office.
Published exactly through playtest: `work/crane-row/polish/publication.json`
verifies save `3a4e7c9b` unchanged, lossless wrapper/checkpoint and retained
prior/active compositions.339 suite +30 post-driver targeted checks pass;
all30 Crane/all13 corrected Midnight routes, Red/Black no-refill victories,
Office save/Continue, lever/cache and warning/live/refuge controls pass.
The corrected Roof driver also passes on the0.16.0 baseline. Original failed
gather runs remain recorded. Player feel/performance/duration are unmeasured;
CHANGES owns the release's explicit validation limits.

**Alignment lesson:** Huffman hint lengths affect the sum of the two string
files before appended resources. Changing its residue modulo4 can insert an
extra alignment resource, shift later resource IDs and change descriptors/
ARM9 despite unchanged instructions. Do not relax release pins to hide this.
The final concise hint copy preserves the original residue and restores exact
IDs/ARM9; intermediate art-C `21af857c` is not the release. Named candidates
remain immutable while emulator surveys run. Visual placements prove art only;
real-door tests separately qualify traversal.

#### Crane Row door and roof repair (v0.16.2)

Player feedback2026-10-14 confirms the art improved but exit shutters and many
ceilings disappear. Two confirmed authoring errors: the shared
`midnight_rooms._shutter` winds a left-wall shutter toward-x (away from the
room), and nine outdoor Crane plans deliberately hide their ceiling shell
despite retaining its solid collision. Native front-face culling makes the
reversed shutters invisible. Crane now uses its own `crane_art.portal` with
inward normals (+x left/-x right), recessed jambs and a lintel lamp. Projection
from either wall remains below1.5 units, within the3.5-unit collision clearance.
The shared helper/other districts are unchanged by this repair.

`crane_art.ceiling` draws full-width downward-facing steel at the existing
y=h boundary of each formerly hidden shell, plus fascia/amber edge and flush
underside strips. Trim stays inside the real ceiling solid. Outdoor roofs use
scenery deliberately: making the plan shell visible would also add ceiling
enemy anchors through `plan_anchors`. This approach retains exact BSP/OBJ,
camera, anchors, maps and ARM9. Twelve room model/texture pairs and the two
version labels are the complete resource-change scope. Every exit gains a
destination sign from LINKS; Freight's wrong "Crown" label is removed (the
high return actually goes to Engine House).

Regression coverage tests actual emitted shutter normals at every port,
downward roof coverage across the full width at z=0, frames/trim extents,
destination labels and conservative GPU budgets (largest335 quads).
Private survey/audit sources and captures: `work/crane-row/repair/`.
Final `reviewed/` survey covers29 exits and36 roof/corner poses; all65 sampled
coordinates match their requested positions, and all rooms remain the intended
IDs. Held poses establish rendering, not the ability to stand in mid-air.
Central scenic captures missed boundary-face errors in0.16.1: future art
reviews must cover every port, ceiling and upper corner before starting the
expensive route/combat qualification. Place/hold fixtures
prove rendering only; validate traversal separately through real doors. A
marked pose can move before the nearest later screenshot: choose the preceding
capture within a sustained pose window, and check the sampled position/room.
`art.face` maps one whole texture onto a quad (correct for signs): using it
for a360-unit steel fascia stretched individual palette pixels into apparent
blank blocks at upper corners. Roof fascia/trim now use `rc.box` world-scale
UVs and reach h+18 to close the whole visible shell. Old floating foreground
hazard bars crossed labels, and Quay's24-unit cargo obscured its ground label;
remove the bars, keep X beside high hatches, and put destination signs above
cargo while clamping their tops below h-2. Final boards are24x6 at z-7,
above ground cargo (floor+27) but below stacked landings (high floor+18).
X uses the same plane in the adjacent column. Projected silhouette checks
cover both playable solids and foreground scenery: merely separating their
world rectangles misses perspective overlap. Compact boards clear Crown's
first landing; moving them forward clears Warren cargo/Engine pipes. Quay's
district sign moves away from its return label; redundant Office lettering
is removed where it overlapped the exit label.
Published as `1bd288f1` on2026-10-15, exact composition and latest battery
`54417ed4` verified by `work/crane-row/repair/publication.json`. CHANGES owns
the qualification counts, reruns and player/performance limits.

#### Crane Row navigation and objectives (v0.16.3)

Player confirms0.16.2 visual improvements, but reports the map's connections
are misleading and X at doors has no clear purpose. `tools/crane_navigation.py`
defines a labelled schematic directly against all29 directed `crane_rooms.LINKS`
ports. Every continuous connector leaves the real door side and avoids other
rooms/wires. Matching letters carry loops that cannot fit the small flat panel:
A Engine/Shaft, B Breakwater/Quay, C Freight/Engine, D Engine/Crown; P is Pier.
Tests assert one-to-one graph coverage, sides, no crossings and panel bounds.
Detail maps retain the native projection and gain destination captions; X marks
button-operated upper hatches. Three-dimensional boards distinguish WALK IN,
X ENTER, X SHORT, X SAVE RM, X OPTIONAL, X HOIST and X RETURN. Their secondary
boards sit above high-door destinations, below ground-door destinations, clear
of the actor's head/stacked landings. Scenery never contributes collision.

**Four progress screens:** power140, Crown146 and boss142 select Restore cargo
power -> Clear the Crown crew -> Defeat the hoist -> Return to the Pier, with
boss taking priority. No new persistent flags or migration. Goal borders amber,
locked endpoints red, unvisited rooms dim but labelled; native current/visited
colours remain distinct. `zz_CraneOverview.cbmp` plus `zz_CraneGuide1..3.cbmp`
share the same20 room-list palette slots and635 tiles each. Reserve palette11
from room allocation: B1..B5 static header/legend, B6..BA current-room source,
BB..BF hidden-room source. Native frame/buttons outside the panel are verified
colour-identical. Office's S/save marker moves away from its text.

Native screen load0x020E136C originally `E7911202` (LDR r1,[r1,r2,LSL#4]).
A B adapter selects the earned screen only for area6/rooms96..107; other
areas/rooms/null stats execute that original LDR. Preserve r0/r2..r14 and CPSR;
branch directly to site+4. A BL here would overwrite the caller's live LR.
Native Objectives constructor's BL0x020E0F28 formerly called0x020D13CC, the
mission-goal getter (native mission table0x0211E4C8,16-byte stride). Only this
call is wrapped. In Crane rooms it returns one of four private8-byte title/body
pairs; constructor reads only +0/+4. Else restore arguments/CPSR and tail-call
the original getter. Native mission table/counter/save bytes stay exact.
The old page incorrectly said "Drain the sewers" while in Crane Row.
Both adapters have ARM instruction tests for flags/registers, null/native
fallback and all12 rooms/four phases; generated pointers/strings are checked.

First-visit groups choose local instructions from those same earned flags,
before the existing visited flag is set; no repeated per-frame message write.
Native say0x15 now receives5 seconds for all Crane hints, including lock/power/
crew/hoist messages. See "Chapter dialogue" for the corrected native timer
units. A real lever press clears the temporary hint back to the updated map
without room change or manual refresh. Other chapters retain their durations.

Pinned candidate `18c90eb8`, ARM9 `2dea0314`, owns5844/8192 Crane bytes; message
bound244 remains below256. Full kit/dial and Midnight4KiB are byte-exact to
0.16.2, as are all collision, doors/spawns/input modes/camera/anchors and native
assets except version/appended strings and filename table. Removing obsolete
First_Visit moves ten entity callback indices; audit resolves them by EG name
and checks every other entity byte and non-message encounter command unchanged.
Only ten native ARM words differ: resource count, message pointer/two bounds,
four relocated Crane gameplay adapter branches, and the two scoped UI sites.
Evidence: `work/crane-row/navigation/audit.json`, `ui-version-0.16.3-nav-d/`,
four door contact sheets and detail/goal/hint sheets. All29 doors/12 detail maps,
four goal maps/Objective pages, native fallback and real lever/hint expiration
have been reviewed. Earning power at the real lever, returning through the
Freight shortcut to Office, saving there and fresh native Continue restores
room98/flag140 and both the phase1 map and Objectives page (`save-goal/`).
**Probe correction:** some transitions leave an old actor/motion pair whose
motion back-link still looks owned. Two Engine exits retain actor0x022AE8F0
alongside the actual player; its controller pointer is4/0x34C, while the live
player has the native controller type0x021352A4 and a matching owner at+0x44.
`player_trace.sample` now uses those validated controller links if motion-owner
filtering leaves multiple candidates. Two fully owned controllers stay
ambiguous; a single original actor can still have no controller. Read-only
tests cover invalid/reused/outside pointers and preserve the input bytes.
The previous probe returned a partial sample without `room_vars`, causing
Crane's machinery logger to raise. Initialize absent variables as an empty tuple
and log machinery only with a sampled actor; never fabricate a pose/variables.
Real-door and post-win revisit checks now await a live arrival instead of
assuming80 frames is sufficient. Earlier exception/ambiguous-probe captures
remain retained. These changes affect lab code only; ROM bytes stay exact.
Published exactly through playtest as0.16.3 (`publication.json`): latest battery
`ac9896ff` is byte-identical and wrapper/checkpoints/prior compositions verify.
All30 Crane cases now confirm live arrivals; all13 Midnight routes and eight
gameplay controls pass. CHANGES owns counts, retries and player-validation limits.

#### Crane Row terrain overhaul (v0.17.0, 2026-10-15)

Player finds the partly explored district boring/bland; hoist feedback is not
available. The repeated flat floor/small-crate geometry is replaced in
`crane_rooms.geometry`: Quay/Freight/Warren/Gantry/Breakwater gain lower solid
maintenance decks at -20/-24/-24/-32/-20. Segmented docks and recovery steps
stand above them. Camera minima, anchor areas and native detail-map projection
follow the new bounds. Doors, arrivals, input modes, locks, IDs, visits and
milestones remain unchanged. The continuous lower deck catches missed jumps;
it is deliberately not water damage or a death pit.

Freight has a complete rising roof route over its fight deck; Warren uses tall
solid stacks with intermediate steps and upper hanging platforms. The Dry Dock
ship is playable hull/deck geometry with open holds, upper rigging platforms and
original rust/navy hull pixels. Shaft shelves become switchbacks around the
existing scenery mover; Gantry uses broken spans over a lower service deck.
Crown gains a broad stage and upper platforms. Native throwable metal barrels
populate combat decks and optional roofs. Hoist warning/live/recovery, HP,
models and win conditions remain unchanged; only its approach terrain changes.
`crane_art` adds support/rigging scenery and reduces repeated small rail posts
to retain the existing <400-quad room budget.

Crew variety uses already-proven native spawner sources: Freight Pier8, Dry
Dock Sewer0x0E, Gantry Residential0x0C. Crown Pier8's real defeat callback
activates Residential0x0C once, guarded by room scratch0x12A; only that second
crew's defeat sets Crown146/upper141. No timer awards a clear. Existing earned
clear flags skip the changed encounters without a save migration. Qualifying
crew controls use 1HP enemies/native strikes and player chase placements:
they establish callbacks, not difficulty or normal traversal.

The final Crown chase control twice stopped at x11.9 after the first crew,
outside the second spawner's activation zone. Aborted RAM has scratch0x12A==1:
the first native callback had worked; it was not a missing victory callback.
`crane_boss_lab.ControlWalker` now returns toward the arena with native D-pad
input while chase is enabled, no enemy remains and Crown is uncleared. That
control passes with121 return frames. Game waves/flags are unchanged. Failed
report/RAM are retained under `work/crane-row/overhaul/k/crews/`.

**Compiler correction:** a valid box layout exposed `compile_boxes` recursing
into a completely solid back child. Its old error misleadingly blamed overlaps.
The native node format only has a front-solid leaf. A redundant x plane at that
child's existing left boundary now encodes a front-solid/back-empty terminal;
the parent makes its empty side unreachable. Existing successful trees are
unchanged. A minimized five-box regression round-trips/checks the tree, checks
2,500 random points plus edge-offset samples against the box union and checks
surface6 versus plain z faces. Crane's revised Warren crosses this generated
collision through real native inputs. No native BSP parser bytes are rewritten.

**Traversal-driver lessons:** do not judge a jump from a teleport pose under
an overhang. Required takeoffs need head clearance; tall ground stacks need
intermediate steps. `crane_walk setpiece` starts at a native room arrival and
uses only controller inputs for Spidey, with enemies explicitly parked. It
checks settled landings and a real exit. State24 is landing, not stable idle:
a buffered B can start another jump after it. The driver releases B after
contact, brakes, waits for twelve settled frames, and uses one initial jump
across descending gaps instead of repeatedly triggering airborne swings. Long
jumps begin moving immediately; only a close higher landing delays steering.
Earlier failed controls
remain in `work/crane-row/overhaul/`; a controller failure alone is not proof
that the terrain is impossible. No traversal RAM placement is used by this
set-piece controller. Combat/visual fixtures remain separately labelled.

Final K `c5fc0512` reproduces through normal composition in
`build/version-0.17.0-final/`. Audit `work/crane-row/overhaul/overhaul-k/audit.json`
checks kit/dial/Midnight bytes, original resources/machine models, all record0
door/trigger/lock bytes, unchanged overview/goal screens and matching boot/Options.
Only native ARM word0x020077F8 (Glob count) differs before the extension; owned
resource descriptors/data change. Crane still owns5844/8192 bytes. All30 real
door cases, seven native-input set pieces and357 tests pass on K. J's final Arm
step gap let a walking player drop before the36-unit block: joining its18-unit
step to that block fixes the generic input route. K differs from J only in the
Arm's OBJ/model/BSP/detail map and filename/alignment framing. Eleven visual
reviews/preview inherit identical bytes; the Arm is recaptured. Collector checks
each source landing's room and bounded live destination after an80-frame wait.
Publication and completed regressions are in TASKS/CHANGES; player
fun/performance are unmeasured.

#### Original Crane creature pipeline (v0.18.0, 2026-10-15)

Player explicitly chose entirely new creatures with new attack animations;
imported enemies/recolours alone do not meet the request. Isolated development
preserved0.17.0 and the real battery; publication is recorded below. Private
probes: `work/crane-row/creatures/`.

`model_sheet.xbd` is a separate resource-group format, numeric kind0xFDB3E9A5.
Its repeated footer/envelope stay intact. Native payload at+8 has s16 high
offset and u16 packed low4 offset/high12 count; table starts8+(high<<4)+low,
then182 groups of three u16 NSBMD/XBD/NSBTX IDs. `actor_resources.ModelSheet`
round-trips and appends without changing old rows/unknown prefix/tail; three
tests include the native file. Runtime wrapper replaces its first8 bytes:
global pointer0x0213E144 identifies the loaded resource. Native model accessor
0x02001EB4 takes a pointer to a group index and loads the group's animation XBD,
model and texture. Do not confuse this with an action-XBD binding.

Character config getter0x020D12A0 returns84-byte records for types2..50 from
0x02136880; types0/1/outside use0x0213682C. Record+8 is populated at runtime
with model-sheet group, +C supplies native HP. Runtime probes: type36->group24
(`brt`), type21->38 (`hLpr`), type20->42 (`hRng`). First word participates in
native spawner cost/live-budget checks at0x0204C5C8; it is not established as
visual scale. Other fields remain unknown unless separately qualified.

Mesh A (`c9e150ac`) replaces only a private training Brute mesh as a control.
Scope A (`c27ac24d`) instead appends group182/model/texture/XBD, clones type36's
config in unused Crane reservation bytes, and overrides the getter only for
room70/type36. The authored mesh renders identically; original models remain
exact. This establishes append/binding feasibility, not new attacks/production
scope. Source `scope_proof.py`; captures under the matching boot-test folders.

Brute/hostless templates have28 bones and one shape. SBC stores bone matrices
in slots0..26, so authored GPU streams can restore individual bone matrices and
draw newly authored rigid geometry in bone-local coordinates. Preserve native
node/SBC/rig bytes; do not infer a new skin editor. Flat-colour original mesh
proof uses opaque white format7 texture plus vertex colours, with an unused
dummy palette for the existing archive writer. Current art/motion modules:
`crane_creature_art.py`, `crane_creature_motion.py`. Attacks are authored from
idle bind lengths/IK/continuous curves, not sampled native attack poses.

Native spawner goal getter0x020D11B0 (24-byte rows at0x02136634) and role chooser
0x020D1200 are distinct from character config. Goal->character variant getter
starts0x020D102C, called at0x0204C5A4; constructor gets goals at0x0204C15C.
Scoped adapters retain native initialization, budget accounting and real defeat
callbacks. `crane_creatures.py` appends three groups, clones configs (nominal
HP10/14/7, native costs1/2/1) and hooks config/variant/goal only in rooms96..107.
Goal row+20 must carry its initialized weight sum: calling native init does not
initialize a separately cloned row. Full A `d34f3cd7` fits6648/8192 bytes.
Original resources/configs remain exact except appended model_sheet rows.
Ten parser/asset/adapter tests pass; native frameworks/rigs are reused, not new AI.

Actual room102/no-dummy duels (`arena_view.py`, isolated native spawns, healing
fixture) prove Ballast and Spore HP loss. Maw initially whiffs at~9 units.
Radius-only control `arena-reach-a.nds` (`3cdf31ea`) changes its GMB kind3 part2
radius3.1->4.6, retaining other words; player HP then drops24576->17904.
Native config+24/+28 range edits were inconclusive training controls and are
**not** used. Training kit gives enemies dummy protection flags, so confirm
incoming damage in story context. Placement below a native body's support
height can fall through the floor: duel driver now uses native positions only.
Kind3 body/attack coordinates are empirically useful, but general cylinder/flag
semantics remain hypotheses; kind0 part9 muzzle placement still needs controls.
All qualified species retain the other GMB words/flags and native movement.

Published D: `f6d09cfc`, ARM9 `805460f9`, version0.18.0;
`build/version-0.18.0-final/Versioned.nds` reproduces it.47 authored SCA routes
(including31 attack routes); one private Ballast GroundAttack2 GAB moves only
contact-start2->6 and end6->11 inside its original17 samples, for visible windup.
Crew budget8 total/4 live admits the1+1+2-cost trio. Patrol3/2 and hoist1/1 retain
small pressure; native budgets/death callbacks handle replenishment.

Mesh-only C->D proof: `mesh-equivalence.json` changes only Maw/Spore NSBMD.
Code, configs, SCA/GMB/GAB, textures and every other resource remain exact.
C's uncapped-health native-position duels clear Maw with Red kit, Spore with
base Red, and Ballast with both Black base and Red kit. Healing is labelled;
these prove combo/damage/real defeat, not difficulty. Early failed drivers
remain: first never entered activation zone; second held Y after its first tap.
Generate a fresh button set each frame so repeated presses have release edges.
The corrected Black Ballast driver needed longer than2400 combat frames.

D uses220/348/218 quads (Maw/Ballast/Spore). All cost<=4 compositions fit6144
vertices with the largest370-quad room, native744-vertex Spidey and384-vertex
prop/FX margin, before clipping/culling. No measured frame-rate claim follows.
The earlier283/234-quad light meshes could exceed this conservative crowd
budget. D's three real crew callbacks, Red-kit/Black no-refill hoist controls
and production mixed fight pass. Mixed fight: all three species together,
max4 live actors, native HP, no placements/caps, healed player, real callback
at3966. It naturally selects Maw leap prep and `hLpr_LeapAttack` (new GMB IDs
traced), in addition to both claw attacks. All30 Crane door cases,13 Midnight
routes and374 tests pass on D; geometry/native-input terrain evidence inherits
from exact0.17.0 room bytes. Normal playtest publication preserves latest DSV
`ac9896ff` exactly (wrapper/checkpoint verified), retaining prior ROM/compositions.
Sources: `crane_creatures.py`, `crane_creature_lab.py`; evidence in
`work/crane-row/creatures/publication.json`; catalog `reference/crane_creatures.json`.
Agent-tested, not player-confirmed; full-chapter duration/frame-rate unmeasured.

#### Crane Row rework and reward correction (v0.19.0, 2026-10-16)

Player rejects0.18.0 (2026-10-15): familiar enemies/sounds, no death tint,
apparently absent XP/HP, sparse encounters, excessive signage/map text and
coarse/repeated art. Prior healed duels did not qualify rewards. Sources and
evidence: `work/crane-row/rework/`; final L is published/agent-tested.
ROM9b2b948f, ARM9 9b04b02a; exact composition and limits in CHANGES.

**Confirmed reward bug:** cloned84-byte configs copied ROM-time zero at+0x50.
Native startup changes it to9 for Brute/type36 and16 for hostless20/21.
Native lethal HP setter0x02049304 sets its once-only dead flag and passes
config+0x50 to0x02049410. Factory RTTI at0x0212BA5C explicitly identifies
`RewardSetSpewer(ERewardSetSpewerType_raw,ERewardSetType,Vector3,Enemy*)`.
Thus+0x50 is **ERewardSetType**, not an animation/sound/model-group index.
Private set31 now copies Brute set9's48-byte row at0x0211E808+9*48, retaining
XP10..12 points (Q12 words at+16/+20) and native LP behavior. Its HP lower/upper
words become1024/2048 (0.25..0.5 native health units). Native OrbHP's smallest
threshold is1024 at0x02138AFC; no fractional-orb assumption is needed. Scoped
getter0x020D1590 returns the private row only for31/in rooms96..107; other IDs/
rooms keep the native prologue. Native tables remain exact. Old0.18.0
controls show actual XP1850->1850 and no health recovery. B `70d9234d` Ballast
gives1850->1862XP and3072 Q12 recovery with healing disabled. Revised idle1HP
targets/real strikes isolate actual collection, not difficulty/AI. H's native
Shaft arrivals/no-placement controls give Maw10XP/2048 HP and Spore12XP/2048 HP;
J Ballast gives12XP/1024 HP, without player healing. Final L gives Maw10XP/1024HP
and Spore10XP/1024HP. The paired native-arrival zero-set Ballast kill observes
real death and awards0XP/0HP. Receipt names reward-*-escape-9b2b948f.json in
work/crane-row/rework; final positive Ballast uses the corrected exit-safe driver.
L Ballast exit-safe gives10XP/2048HP. All three species therefore collect both
native currencies without healing. Positive Ballast receipt is reward-ballast-
native-exit-safe-9b2b948f.json; its zero-set counterpart remains escape. Real
currency is measured throughout.

**Fixture correction:** broad-deck placements could retain the old lower-floor
standing plane even after a jump: Spidey later stood at y-19 inside a rendered
raised dock, while the orbs remained above it. Those zero-collection runs do
not qualify drop behavior. Current reward lab uses native Shaft arrival and
controller movement only, an idle1HP target, and logs player XY/state. Never
attribute a missed pickup to the ROM before checking actual player placement.

**Rejected E/F experiment: never ship these ROMs.**0x02145C54 is the camera;
0x0207E5B0/5CC and distance-scaled0x02049FC0 control camera shake, **not rewards**.
An incorrect inference added a death hook calling them in E/F; it is completely
removed for G. F's observed rewards came from native RewardSetSpewer behavior,
not that hook. Never name a function from adjacent effects: trace its consumer/
RTTI and qualify paired controls before asserting meaning.
**Currency is stats+0x44.** An early rework observation mistakenly called the
changing+0x18 counter XP; corrected before acceptance. Do not repeat it.
Reusable measurement: `tools/crane_reward_lab.py`; no real-save writes.

**Death colour:** authored GPU streams emitted COLOR0x20 for every face,
overwriting the engine's material tint. Face colours now live in a private
RGB555 texture atlas; authored streams emit texcoords, matrices and vertices,
leaving COLOR to the native renderer. A's actual lethal-hit capture visibly
darkens Maw (`death-a-sheet.png`). Native rig/SBC/node bytes remain intact.
All154 SCA routes (Maw57/Ballast39/Spore58) now use authored species poses,
including hit reactions, bindings, air and death. Earlier47-route coverage
left recognizable humanoid reactions/death. Native AI still underlies these
creatures; do not claim a new AI framework. Attack GAB timing stays intact
except the previously qualified fast slam.

**Sound pipeline:** `tools/sdat.py` frames SDAT losslessly and preserves opaque
SYMB/INFO/headers/padding and untouched files. FAT sizes include padding while
SSAR/SBNK/SWAR internal lengths exclude it. Never equate those sizes. Insert
new indexed rows, relocate existing offsets and retain payload bytes exactly;
whole32-byte file growth retains native following-file alignment. Three native
files (SSAR0, SFX bank20, wave archive0) each grow582->597 entries. No native
sound ID/sample/instrument/sequence is replaced.15 deterministic original
11025Hz PCM8 voices cover alert/attack/death/hurt/idle for three species.
SSAR events use instrument VLQ, unity-key60, velocity110, duration0 (native
one-shot convention), endFF. New file growth64608 bytes. `ndspy4.2.0` in ignored
work/runtime independently reads all597 entries; production uses stdlib only.

`crane_audio.adapter` scopes the normal sound-start prologue0x0203D5E4 to
rooms96..107, remapping Brute306..328, Hostless457..479, Leaper480..501 to
private582..596. Input bounds run before this hook, so native582-count guards
stay untouched. Other sounds/rooms execute the original push/continuation with
their original args/registers/CPSR. Five audio integrity/ARM tests pass. F's
post-remap probes observe Maw attack/death593/594 and Ballast583/584 reaching
the sound engine. The ranged chassis supplied no vocal request during its
reward control. G adds an exact private-Spore/controller-type guard at state
entry0x02077844:15/16 attack588,28/29 hurt590,53 death589. It constructs/plays/
destroys a native sound handle like OBJ opcode22. Those cues/native fallback are qualified. PCM capture uses the optional lab audio sink.
Final L counters observe all three private death IDs. Recorded mix waveform
matches Spore0.868/Ballast0.304. Maw's broadband hiss is sensitive to native
pitch and aliasing: naive unfiltered4x mono diagnostic scored0.110 (retained as
a failed diagnostic). Identical2kHz anti-alias filters and a0.65..1.4 pitch scan
match0.234 at0.77 pitch/7.772s, near the actual lethal hit. This independently
proves its authored wave rendered, rather than assuming a call counter proves
sound. Reports audio-render-proof-l.json and maw-pcm-filtered.json; WAVs stay
ignored. Preserve native caller pitch/pan arguments.

**Density:** old Freight/Dry Dock/Crown spawners ran only with clear flags0,
leaving permanently empty saved revisits. Those earned flags still skip the
objective crews; an independent callback-free patrol runs on cleared revisits.
Engine/Shaft/Breakwater also gain patrols. Patrol total/live cost8/4, crews12/4,
hoist opening1/1. Safe office/cache stay clear. Ordinary patrol activation boxes
cover the room vertically/horizontally. Live cost ceiling stays4 for GPU budget;
final native-HP Freight clear and capped Dry Dock/Crown callbacks pass. Floor-anchor height
now reaches h-24 (hoist retains12), so shelves/roofs are eligible. I's copied
earned-clear/native-arrival survey sees3..4 live foes in combat rooms and0 in
Office/Cache. High Quay/Shaft entries initially still saw lower foes; delaying
birth via zero live budget then restoring it did not fix placement.

J splits Quay/Shaft/Gantry into lower and upper patrol zones. The upper spawner
uses native Sewer table14; scoped goal selection supplies4 total/2 live cost
only for14 in96/102/103 (Dry Dock14 remains its main crew). Other goals remain
8/4 patrol,12/4 crew,1/1 hoist. Native global cost ceiling still4. Shaft high
arrival now observes2 foes including y154. Quay's small high hatch landing is
too close to the arriving hero; other legal upper anchors are far across the
room. K adds a58-unit suspended loft x60..118,y64 for visible upper combat.
L uses native spawn mode2 (with real empty completion callback) for those upper
zones. Tracing0x02081D74 from0x02080620 shows mode2 selects central-sector mask0x10;
normal offscreen weights repeatedly selected lower points. Empty upper callback
writes no quest flags; finite4/2 upper wave retains global live cost4. L native
high Quay arrival now sees2 foes y45..47 beside hero69. Keep actual spawn evidence
distinct from anchor eligibility tests.

**Controller lessons:** state9 is wall cling; ignored Up could strand a route
against cargo. State29/GMB `spd_WebHangIdle` can result from repeated B below a
dock; release with Down/B before resuming. These are lab-driver issues, not
proof of broken doors. Native-input pursuit now handles wall routes to higher
foes and moves horizontally when a nearby target is below. Mixed tests may
use explicitly labelled60-unit max/healed player fixtures to avoid a driver
death/minigame interrupt; they do not establish encounter difficulty. Low catwalks
also require moving away before jumping: simply steering to an enemy above
left the lab player directly below its platform. A periodic escape sweep fixes
that driver. Jump before approaching an automatic ground exit when climbing to
a high target; a failed Ballast reward fixture had walked back into Engine,
and a failed Crown callback fixture walked into Gantry. Those original failed
reports/RAM are retained; no production fault is inferred from them. The callback
driver now returns through the actual connecting door if pursuit exits its arena.
Crown then clears at2205 and opens upper return;42 frames use the native return
navigator. Freight uses the stronger natural-HP mixed-clear proof (6019 frames,
XP1850->2028). No actor placements in these controls. All30 final Crane doors,
13 Midnight routes,11 patrol probes,8 progression/boss controls and three actual
reward controls plus zero control pass. Publication preserves latest battery
3d21ee63/634 bytes exactly, including DSV wrapper and checkpoint round trip.

**Art/navigation:** outdoor destination/action boards removed; a4-unit X glyph
marks high hatches. Detail captions and most map labels/legend removed; one
short goal line, landmark icons, true ports and matching loop letters remain.
First-visit/clear speech bubbles are removed: they blocked movement during
encounters (state75); full route details stay on Objectives. A small painted
bolt marks the Engine lever. New64px
steel/deck/cargo/wood use sparse low-contrast wear. Original painted panorama
is `reference/art/crane-harbor-v1.png`, built-in ImageGen prompt/provenance in
the sibling JSON; technical RGB555 encoding is deterministic and build-read
from its sibling binary. Three256x128/256-colour panels cover672x224 world
units at z-170, with no repeated cycling pictures. Inspect at actual DS size.
Git must treat *.rgb555 as binary: a dark palette may have no NUL in Git's
initial probe, causing text/CRLF handling. .gitattributes disables conversion;
staged bytes equal79093a67 SHA256 exactly. Never normalize raw texture words.
All29 exits and36 ceilings/corners reviewed on E (`repair/rework-e/`), inheriting
through exact art bytes. Collision/doors/anchors remain exact.384-test suite E
passes. Final L suite387 passes; expanded ARM/native-input telemetry regressions
also pass9 tests. All13 Midnight native routes and11 arrival/revisit patrol
observations pass on L. Art/UI QA rework/ui-review-l.png shows all four map and
Objectives phases, upper Quay loft and no destination boards. Engine lever is
visually reviewed in walk-control-gates/frame-03300.png; native Pier Objectives
still displays its original goal. Final receipts live in rework/publication.json.

### Native parent-area maps

The actual runtime order was observed from `0x0213B840`, not guessed:

| Area | District / screen | Title string | Native list / entries |
|---|---|---|---|
| 0 | Pier / MMPier | 381 | 0x0211FD34 / 13 |
| 1 | Residential / MMResident | 382 | 0x0211FB7C / 11 |
| 2 | Sewer / MMSewer | 383 | 0x0211FE38 / 18 |
| 3 | Downtown / MMDowntown | 379 | 0x0211FFA0 / 19 |
| 4 | Hive / MMHive | 380 | 0x0211FC58 / 11 |
| 5 | Midnight Line | appended | current chapter list / 25 |

`map_probe.py` checks each proposed parent CBMP round-trip, existing list slots
and all rendered indices; it writes all-visited private previews and
`parent-map-survey.json`. Static blank-cell regions: Pier lower band
(24,120)..(224,152), Downtown upper-left (24,24)..(80,88). Residential is
tighter: only eight-pixel top/bottom bands are wholly blank. All three have
unused five-colour slots, but the unused index scan is not live colour or UI
qualification. Previews were inspected; do not force a tiny unreadable
Residential diagram just because it fits. A redraw requires updating existing
markers/room projections where relevant and validating world/detail views.

Preferred integration: retain parent areas 0/3/1, copy their original 20-byte
list records unchanged (260+380+220 = **860 bytes**) into owned table space,
append new entries, and patch each row's list/count. Extend the corresponding
native overview screen in unused space, preserving the frame, old room art and
source colours. Generate individual detailed maps from each compiled plan.
`room_table` and `room_minimap.Projection.fields` currently hard-code area5;
generalize them with area5 as the default so Midnight remains byte-identical.
Retain native map-item ownership (bits68..72); do not grant maps implicitly.
The existing visited stub is shared by the parent lists and must include every
added room. Direct branch maps are preferable to putting every district into
Midnight's overview or assuming a seventh area slot exists.

### Remaining empirical gates and workflow lessons

**Freight roof reproduction/correction, v0.28 -> v0.29 B, 2026-10-21 (high
confidence, agent evidence):** native walking baits an isolated full-HP Ballast
under the x40..88/y17..20 platform, then native input returns the hero above it.
Both runs reach the same x80.739/y24.981 landing at frame590. On v0.28, Ballast
continues jumping beneath the slab through frame1850, around x80..81/y-7..12,
with no roof contact/damage. B clears the edge, jumps outside the ceiling,
returns and lands, then causes actual native HP loss at frame670 (enemy
x81.291/y24.568). No post-spawn actor/player placement, enemy HP fixture or
player refill is used. A simple arrival with Ballast already on the platform
can pass on the parent and is retained as a separate control. The first A
adapter incorrectly dropped its route at the jump apex; B retains it until a
real landing. Scoped state/guards and other-room control remain required.
Sources: `chapter_finish_crane.py`, `chapter_finish_lab.py`, and
`work/chapter-finish/freight-base-short` / `freight-b-short`. This qualifies the
specific obstruction, not all elevated pursuit or player fun.

The old Pier-door/disposable-chamber, parent-map and Quayside experiments are
completed prerequisites of released Crane Row, not next tasks. Protected native
machine-core damage, hoist death/save persistence, loops and maps subsequently
shipped. Current Crane review should reproduce the Ballast directly-overhead
Freight pursuit edge case and assess full-route presentation, retry flow and
frame pacing. Isolated counters/healed crews do not settle those player gates.

Rideable moving loads/platform collision and cross-room countdown lifetime
remain unproved and deferred. Opcode0x23 starts/resets a native minute timer and
TimerWatcher can run a timeout group; neither establishes survival or clean
retry across rooms. If a future timed branch is requested, first prove an
untimed reversible route, then start -> real door -> timeout/reset and
death/exit/revisit on copied saves. New completion rewards or boss interactions
need their own persistence/kit controls. Preserve story gates, avoid required
paid moves and qualify both suits. Do not allocate deferred branches from an
old capacity sketch or lower enemy quality/count as an unmeasured FPS fix.

Scratch scripts must not shadow Python's standard library: naming a script
`inspect.py` broke `dataclasses` imports in this session; it was renamed
`native_probe.py`. Lab input names are case-sensitive (`Right`, not `RIGHT` or
`right`). Native core output reaches stderr too: redirect all PowerShell
streams when retaining long lab logs. Research sources/captures stay in ignored
work/build; only the reusable audit and its tests belong in tools/tests.

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
  resolve walls/floors. The historical Skyjack velocity/combined candidates
  remained unpublished; the current source/binary recheck confirms the debt
  (see "Shared crowd-hit backend candidates"). A position write ignores
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
- Scratch scripts with backslashes or nested quotes: write them as files. A
  shell heredoc changed `\n` and broke quoting twice on 2026-10-11 (and
  once more on 2026-10-13).
- Keystone (2026-10-13): **a `.byte` run mid-file shifts every later
  absolute branch by its size** (`bl 0x0205F844` assembled to +8 after an
  8-byte table); the branch validator catches it. Tables are `.word`s, and
  a data word must not read as a branch (bits 27..25 = 101) or the same
  validator counts it. Literal loads reach 4 KiB: the second block has a
  second table (`lit3_`) inside the web block. **A conditional call
  (`bleq label`) is encoded as a branch to itself**: the first v0.13.0
  candidates hung as soon as Dragnet dropped its lines without a yank
  (crash hunt seeds 2 and 4, `work/crash/stall_4_3781`: pc = lr inside the
  second block, tick stopped). `assemble_tasm_kit.py` now rejects any
  instruction that branches to itself; write `bne skip` / `bl` instead.
- Strings: no `;` in the text Huffman table. Button glyphs: `` B, ``
  Y, `` A, `` X, `` R, `` L. Keep them as escapes in
  source (editors may write raw private-use characters).
- Kit change loop: edit `tools/tasm_kit.s` / `tasm_kit2.s` → `python
  tools/assemble_tasm_kit.py` (both blocks) → while iterating, `python
  work/shop/dev_build.py NAME` builds `build/dev-kit/NAME` without pins and
  prints the hashes → update `CODE_SHA256`/`CODE2_SHA256`/`ARM9_SHA256` in
  tasm_kit.py, `ARM9_SHA256` in midnight_chapter.py and the profile's
  `arm9_sha256` in release_info.py → bump VERSION/TEXT_EDITS for a new release
  (a published version never changes bytes) → `python tools/tasm_kit.py` →
  `python tools/kit_lab.py qualify build/version-X/Versioned.nds` → tests →
  copy candidate mods + gameplay_profile.json → `python tools/playtest.py build`.
  The kit source pins one code/ARM9 hash, so an older kit release profile is not
  rebuildable from newer source; its rollback is the retained ROM in
  `build/releases/<sha>/`.
