# Format notes

Evidence date: 2026-10-02. Target: the private USA CS5E dump identified in
`docs/VALIDATION.md`. `docs/ANALYSIS.md` remains the original confirmed inventory.
Reports: `reference/roundtrip_report.json`, `reference/format_survey.json`, and
`reference/visible_mod_report.json`. Generated asset data stays in ignored folders.
Entries below are dated research history; later sections supersede earlier
pending-test statements. Current TASM stage-one evidence is at the end.

## NitroFS / ROM â€” confirmed and tested

The clean 64 MiB image contains two FAT entries, both starting on 0x200 boundaries:

| ID | Name | Start | End, exclusive | Length |
|---|---|---|---|---|
| 0 | Glob.bin | 0x0016F600 | 0x0236C070 | 35,637,872 |
| 1 | sound_data.sdat | 0x0236C200 | 0x03630800 | 19,678,720 |

FNT: 0x0016E800, 34 bytes. FAT: 0x0016EA00, 16 bytes. Banner: 0x0016EC00,
version 1. Used-size field at header 0x80 is 0x03630800. No overlays.
The 400-byte gap between Glob and SDAT and the entire 10,287,104-byte tail are FF.
Every unknown header, executable, banner, gap, and tail byte is preserved on a no-op
rebuild. Unmodified Glob and whole ROM are byte-identical, including padding.

Header CRC16 at 0x15E covers [0,0x15E), initial FFFF, reflected polynomial A001;
the clean value is CF20. The old repacker did not update this when used size changed.
The rebuilt workflow does. FAT start/end words are little-endian u32. Bounds,
overlap with executables/metadata/banner, FNT traversal, CRC, and capacity are checked.

Rebuild policy: copy the complete source image; retain each resource's start when it
still fits; align and move successors only when growth collides with them. Update FAT,
used size when necessary, and header CRC. Shrinking retains the old placement of later
files and preserves vacated bytes. Used size is a conservative, aligned high-water mark.
Growth after the old used region may consume only 00/FF padding and may not exceed the
original capacity. This policy is for the observed DS/no-overlay layout, not arbitrary
DSi/overlay ROMs. Exact no-op identity and grow/shrink/zero-length resources are tested.
Container resizing does not establish that an engine format accepts the changed data.

## Glob.bin â€” confirmed and tested

| Location | Structure |
|---|---|
| 0 | LE u32 offsets, N+1 entries |
| offsets[0] | Table byte size, (N+1)*4 |
| offsets[i]..offsets[i+1] | Resource i, no inserted alignment |
| offsets[N] | Exact archive length |

For CS5E: N=3,733; table size 0x3A58; archive size 0x021FCA70. Offsets are
nondecreasing. The name-table resource is index 805, `GlobFiles.txt`: 3,733 records
of exactly 64 bytes, each ending in LF; names are space-padded. Names map 1:1 to
resource indices. All names are unique even under case folding. Raw filename-table
bytes remain untouched, including unknown/padding bytes.

The parser rejects unsafe Windows paths, duplicate names, malformed offsets and
ambiguous/missing filename tables. Repacking preserves file count/order and supports
arbitrary resource lengths. The overlay workflow protects `GlobFiles.txt`: resource
addition, deletion, renaming, and changed archive IDs are not supported yet.
All 3,733 resource sizes/hashes were checked from extracted files and rebuilt data.
This independently agrees with the offset/list concept in the
[ACII Discovery archive tool](https://gist.github.com/luatsenpai/f1a03c3a1eb9a94df2cc7b6ce7e88298).

## NSBTX / TEX0 â€” structural parsing and palette editing tested

### Bounded player resolution experiment â€” 2026-10-03

tools/movie_suit.py accepts only clean spd model/texture hashes. 64->128 I8 changes
pixel pool from 4,096 to 16,384 bytes, shifts palette and empty compressed-pool
offsets, updates TEX0/envelope lengths, texture width/height bit fields (entry at
file 0x64). Texture dictionary unknown u32 at 0x68 is preserved; no interpretation
of its apparent dimensions is claimed. Names/palette dictionaries unchanged.
The texture 64x64 no-op is exact and resized raw serialization round-trips.

Player MDL0 model begins 0x44, single material at 0x8ac; material u16 width/height
at +32/+34 are 64/64. Single shape at 0x900 has GPU stream beginning 0x910.
741 TEXCOORD commands (0x22), signed 16-bit S/T fixed-point values, were doubled
alongside material dimensions. No positions/normals/bones/animation bytes changed.
GPU packets have four byte opcodes then each command's u32 parameters. Supported
opcodes are strictly bounded; unfamiliar ones fail rather than guessing lengths.
Observed UV values range 23..1009 before scaling. 1x no-op and exact inverse pass.

Apicula export gave 744 vertex records/402 polygons and coherent UV mapping in a
private front-view software preview. Structural leads came from scurest/nsbmd_docs
and apicula source, then checked against this asset. Original-art 128 control and
painted variant reached opening gameplay captures; no full-playthrough/hardware
memory budget proof. See MOVIE_SUIT_EXPERIMENT.md. Complete suite: 42 tests passed.

`tools/nitro_texture.py` parses a single-block, little-endian BTX0 version 1 envelope,
TEX0 data pools, and texture/palette dictionaries. Every one of the 272 supplied
NSBTX files passes parsing and exact raw serialization. Unknown fields remain raw.
The implementation cross-checks the layouts against
[ndspy's texture reader](https://github.com/RoadrunnerWMC/ndspy/blob/master/ndspy/texture.py),
[dictionary reader](https://github.com/RoadrunnerWMC/ndspy/blob/master/ndspy/_common.py),
and [apicula's texture reader](https://github.com/scurest/apicula/blob/master/src/nitro/tex.rs).

TEX0-relative palette byte count is u16@0x30 * 8; its dictionary offset is u32@0x34,
and data offset is u32@0x38. Texture byte count is u16@0x0C * 8, dictionary offset is
u16@0x0E, and ordinary texture pool offset is u32@0x14. Compressed texture pools are
bounds-checked too. Palette data must not overlap a dictionary. This is a limited
palette editor, not a general Nitro model or texture converter.

`spd.nsbtx`, archive index 3281, is 4,772 bytes:

- TEX0 begins at file offset 0x14.
- One I8 texture `Cartoon64`, 64x64, with 4,096 pixel indices at 0xA4.
- One palette `Cartoon64_pl`, 256 LE BGR555 colors, at 0x10A4, length 0x200.
- Palette channel placement: R bits 0..4, G 5..9, B 10..14; preserve bit 15.
- `green-suit` swaps R/G only for red-dominant colors (R>=8, R>G+4, R>B+4).
  It modifies 156 palette entries / 311 ROM bytes; texture indices, dictionaries,
  lengths, other assets, FAT and header are unchanged.

Both cold boots reached Residential gameplay in melonDS DS 1.1.5. At frame 1799,
452 changed pixels are confined to Spider-Man's area [114,66,141,99). This confirms
that this asset controls the visible red-suit player texture. No black-suit or
full-playthrough claim is made. See `docs/VISIBLE_MOD.md` for reproduction/reversal.

## XBD â€” outer envelope and actor resource bindings confirmed

All 248 files pass the lossless envelope parser in `tools/custom_formats.py`:

| Offset | Confirmed representation | Meaning |
|---|---|---|
| 0x00 | LE u32 kind, identical to final u32 | Unknown numeric kind, not assumed to be a hash |
| 0x04 | LE u32, len(file)-12 | Stored size relationship |
| 0x08 | LE u16 | Unknown; magnitude of first negative actor-tail value |
| 0x0A | LE u16 | Unknown; **not** safely interpreted as a file pointer |
| 0x0C, 0x10 | Preserved bytes in actor kind | Unknown flags/data |
| 0x14 onward, actor kind | Repeated LE s16 index / u16 tag | Glob resource references |
| After those references | Opaque tail through final kind | Unknown structure |

Kinds observed: 0x8E3E7B2B (155 actor-associated files), 0x79B59567 (92 mostly UI
files), 0xFDB3E9A5 (one file). Only the first kind gets binding parsing. Across its
155 files, positive indices match the manifest with no exceptions:

| Tag | Referenced extension | Observed references |
|---|---|---|
| 0 | SCA | 1,559 |
| 1 | NSBTA | 37 |
| 3 | GMB | 1,467 |
| 4 | GAB | 423 |

The first negative index marks the boundary of the known reference prefix. Its
magnitude equals u16@0x08 in all 155 cases. Its meaning and the remaining negative
records are unknown. A hypothesis that u16@0x08 counts SCA references fails in 80
of 155 actor files; it must not be labeled an animation count.

`spd.xbd` has 311 references: 126 SCA, 126 GMB, 59 GAB. Its opaque tail begins at
0x4F0 (1264), first signed value -78. For example offsets 0x14/0x18/0x1C reference
`spd_AirAttack1.sca/.gmb/.gab` at archive IDs 3287/3286/3285 with tags 0/3/4.
The corresponding GroundAttack triplets are directly bound as well. `sup.xbd`
references `hf_*` action assets, establishing that definitions can reuse another
actor's resources. Runtime consequences of rebindings remain untested.

`Xbd.replace_binding` can replace an existing reference with another manifest ID
of the same extension/tag while preserving every other byte. Synthetic edit/revert
tests and all-file exact serialization pass. It does not add bindings or decode the
opaque tail. Do not interpret these records as damage values or actor stats.

## GAB / GMB / SCA â€” first differential pass

GAB: all 227 files are multiples of 4 bytes and can be represented as LE u16 words.
They end in three consecutive FFFF words, followed by two zero bytes in 96 files;
131 have no such padding. `Gab` validates this observed trailer and retains all raw
bytes. Event lengths/opcodes/timing/damage semantics remain unknown. The first six
unknown words of all 13 numbered `spd_GroundAttack*.gab` files and paired hashes/sizes
are in the survey for comparison; no arbitrary event editor is exposed.

GMB: **compression is now confirmed**. All 769 decode successfully: 749 use
Griptonite PuCrunch (type 60), 20 use DS LZ77 (type 10). These are compression tags,
not opaque GMB flags. Decoded body semantics remain unknown. Across 767 existing
GMB/SCA pairs, decoded GMB u16@2 equals SCA u32@4 in 759 cases; eight named exceptions
are listed in the survey. A shared sample/frame count is a hypothesis, not a confirmed
semantic field. Decoded GMB u16@0 is 30 in 666 files and 24 in 103; its meaning is unknown.
The tempting formula `24 + count*(u16@0+1)*4` fits only 175/769 files and is rejected
as a general record layout.

SCA: all 869 begin with raw ASCII `4ACS` (LE representation of a possible SCA4 tag).
Header words at 4/8/12/16 are surveyed but retained as unknown. Treating words at
12/16 as bounded physical offsets fails in 2 files at offset 12 and 188 at offset 16; there is no
general offset parser yet. No animation, collision-box, or combat-stat meanings are
claimed. Next: compare decoded GMB data across numbered attacks before changing fields.

## Compression wrappers â€” confirmed codecs, limited re-encoding

`tools/grip_compression.py` implements bounded decoders and deterministic literal
encoders for 10 and 60. PuCrunch structure was cross-checked against the
[NitroPaint implementation](https://github.com/Garhoogin/NitroPaint/blob/main/NitroPaint/compression/PuCrunch.c)
and its [bit-stream reader](https://github.com/Garhoogin/NitroPaint/blob/main/NitroPaint/compression/CxPrivate.c).
The parameter fields describe an RLE table, escape code and distance coding. Bits
are read MSB-first within **little-endian 32-bit words**, not in file byte order.
This detail was required for all supplied 60 streams to decode to their declared sizes.

`CompressedBlob.to_bytes()` and unchanged `replace_decoded()` return the original
stream, preserving wrapper parameters/padding exactly. Changed data uses a canonical
literal encoder; this often expands the file. It preserves the full decoded payload
but is not intended as an optimal compressor. All 918 supported resources (769 GMB +
149 2LZ) passed decode -> literal encode -> decode equality and original raw round trips.
Handcrafted escaped-literal, RLE, short/long LZ, overlap, EOF, word-order and malformed
stream tests also pass. Re-encoded streams have not been boot-tested in the engine.

## BSP + paired OBJ â€” envelope/offsets confirmed, room semantics unknown

All 75 BSP files pass the lossless envelope parser:

| Offset | Confirmed field |
|---|---|
| 0 | `BSP\0` |
| 4 | LE u32 = 7, meaning unknown |
| 8 | LE u32 = 2, meaning unknown |
| 12 | LE u32 = exact file length |
| 16 | LE u32 = end of offset-table region, bounded and multiple of 4 |
| 20..table_end-4 | Monotonic, even, bounded LE u32 region offsets |
| table_end-4 | LE u32 = 01000000, meaning unknown |
| Remaining bytes | Opaque data; no collision/tree/node interpretation yet |

Every BSP has a paired `_app.obj`. All 75 OBJ files start with LE u32 2; remaining
structure is unknown. A trial relationship `OBJ word8 = word4+24` holds for only
4/75 and is rejected as general. Room placement/encounters remain hypotheses.

Useful measured comparisons:

- `Test_Combat01.bsp`: 204 bytes, six offsets; OBJ 2,140 bytes. Its BSP is identical
  to `Upgrade_Test.bsp`, offering a controlled geometry baseline with another setup.
- `Test_Collision01.bsp`: 2,550 bytes, 59 offsets; OBJ 396 bytes.
- `Downtown_Save02/03`: byte-identical 352-byte BSPs; both OBJ files are 1,152 bytes,
  with exactly 104 differing bytes. This is a useful next object-record comparison.
- `Downtown_Save01/02/03` and `Residential_Save02` share an identical BSP. Other
  identical groups: Hive_Save01/02, Pier_Save02/03, Sewer_Save01/04, Sewer_Save02/03.
- `Residential_Save01` differs in geometry (766-byte BSP); use it as a separate family.

These are differential facts, not proof that swapping an OBJ or loading a test room
is safe. No room edit was made in this session.

## STRINGS + FONT â€” compatibility lead only

### Bounded English/American text slots â€” confirmed 2026-10-03

New local evidence supersedes the English/American "no text editor" status below.
Both files have SHA256 19474ce9a50c25538515e585727e4ad5878bc3bb7bb11dd987b72a7c1d556088.
At 0x1064 a u32 0x16c describes the tree region including that word. Following
90 pairs of little-endian u16 form a Huffman tree rooted at pair 0. Values above
256 address pair (value-256); byte leaves are below 256. Value 256 occurs as an
unused special leaf; its semantic meaning is unknown. Bits traverse least-significant
first within each byte. Decoded bytes are UTF-16LE including custom glyph codes.
At 0x11d0 are 1,049 u32 offsets relative to 0x1064; first payload is 0x2234.
Each observed entry terminates with a UTF-16 zero. The 0x1064-byte prefix is unknown
and preserved, not described as an ID lookup schema. Other languages are unsupported.

tools/qol_suits_menu.py accepts only these clean hashes, retains original slot
offsets/lengths/tails, and refuses oversized or unencodable edits. All 1,049 entries
decode/re-encode/decode identically; no-op edits retain exact raw bytes. Four new
tests bring the full suite to 40 passing tests. 35 text IDs rewritten in both
English assets; runtime menu layout still requires user checks. See SUITS_MENU_PASS.md.
Suit prototypes modify only palettes in spd/spdB.nsbtx; black-suit binding at runtime
is still a name/preview-based hypothesis pending suit-switch screenshots.

All six `.strings` and fourteen `.font` files are inventoried by size/hash. The
[ACII Discovery notes](https://github.com/hoothin/AC-II-Discovery-Hans) describe
Huffman text and font investigation, and [its decoder](https://github.com/hoothin/AC-II-Discovery-Hans/blob/main/getText.py)
uses game-specific tree/data offsets. Those offsets are **not** used here. Shared
Griptonite archive behavior does not establish shared string layout. WoS text is
still unparsed; take a runtime text sample/dump or identify tree/table relationships
across all six languages before writing an editor. FONT encoding/glyph mapping is unknown.

## 2LZ / DAT / PAL / CBMP â€” inventory plus compression progress

149/153 `.2lz` files are confirmed type-60 PuCrunch and decode/round-trip through
the codec. Four start with 00: `DeathPalHealth`, `DeathPalPoison`,
`FontPaletteSpriteSpidey`, and `GoalCheck`. The first three are 36 bytes and GoalCheck
is 100; all have first u32 00002000. A simple uncompressed-size wrapper would account
for only 32 bytes, leaving GoalCheck unexplained, so these remain unsupported/unknown.
Do not silently apply a raw-body assumption to them.

General DAT tile/frame layout, PAL ownership, and CBMP dimensions/payload remain
unknown. The 2026-10-02 survey made no custom UI edits. The following bounded
minimap experiment adds evidence without establishing a general sprite schema.

### Minimap investigation â€” 2026-10-03

`tools/qol_minimap.py` accepts only hash-identified clean `SpideyMiniMapIcon` and
`MissionMiniMapIcon` families. It preserves their DAT and compressed bytes verbatim.

| Family | DAT bytes 0..1 | Decoded 2LZ size | PAL size | Used indices under candidate layout |
|---|---|---|---|---|
| SpideyMiniMapIcon | 10 10 | 128 | 32 | 0,2,3,4,5,6,7,11,13,14,15 |
| MissionMiniMapIcon | 08 18 | 96 | 32 | 0,1,3 |

Interpreting those bytes as width/height and pixels as low-nibble-first 4bpp,
row-major 8x8 tiles yields a coherent 16x16 Spider-Man face and 8x24 marker sheet.
Linear pixel order does not yield a coherent face. Both tiled interpretations
round-trip exactly, and an independently constructed four-tile test checks order
and nibble orientation. This supports the layout hypothesis for these two assets;
exact round trips alone are not runtime proof or validation for other families.
All remaining DAT fields stay unknown. Index-zero transparency is a preview
assumption, not yet confirmed in-game. Preview colors interpret PAL words as BGR555.

Experiment: change only MissionMiniMapIcon.pal entry 1, LE u16 at offset 2,
from 001F (red) to 03FF (yellow). Both bytes 2 and 3 change; all other palette
entries, compressed pixels, and DAT bytes remain exact. Index 3 remains black.
The offline preview shows yellow fill and the original black edge. Entry 2 is
also red but unused in this decoded sheet, so it is deliberately not edited.

All 29 automated tests pass, including six new minimap tests: exact family/no-op
serialization, independent tiled order, invalid input rejection, palette confinement
and inverse, guarded overlay/revert, one-asset ROM build, and clean ROM identity on
revert. Build verification checks 3,733 resources; 3,732 remain unchanged.
Modified ROM SHA256: 8932a811aa934bb683d2266e22e6c225f8c8da0380c2a4243712ca220b7a80ca.

Clean and edited 1,800-frame melonDS DS 1.1.5 runs reached Residential gameplay.
All six PNG capture hashes match, including frame 1799. The mission marker is not
visible there, so its runtime color, palette ownership, and readability improvement
remain unverified. The modified emulator process returned 0. PowerShell reported
failure for the baseline stderr-redirection invocation despite completed boot.json
and captures; this is not treated as a gameplay failure or ignored as an absent run.
See `docs/QOL_PLAN.md` for reproduction and the remaining manual acceptance checks.

Follow-up user gameplay evidence: a supplied DeSmuME 0.9.13 screenshot shows a
yellow exclamation-style mission marker with a dark outline in Residential, while
nearby blue S icons appear unchanged. This supports the intended runtime palette
effect for that display. It does not confirm animation, other palette users, or a
paired clean comparison. User reports an in-game save; during local inspection
DeSmuME remained running and the matching mission-icon .dsv was zero bytes.
Later inspection found 634 bytes in that file while DeSmuME remained running.
Nonempty disk output is confirmed, but checkpoint validity/reload is not. No real
save was backed up or modified; close the emulator normally, back up, and test Continue.

## Opaque save snapshots â€” 2026-10-03

`tools/save_backups.py` backs up/restores user-specified absolute `.sav`/`.dsv`
paths without parsing, converting, or modifying their contents. No game save fields,
checksums, slots, or compatibility rules are confirmed by this tool. A snapshot
stores original bytes and source path, suffix, length, and SHA256 in schema-version-1
JSON under ignored `work/save-backups/`. Names are immutable; data and metadata
are verified before restore. Existing different destination bytes are preserved in
a content-addressed format-specific safety snapshot before atomic replacement.
Cross-format transfers, empty/oversize saves, direct symlinks, snapshot-storage
destinations, ROM suffixes, and writes in `original/` are rejected. The emulator
must be closed; no emulator lock or automatic save-path discovery is implemented.
Seven synthetic tests cover round trips and safety failures. The complete 36-test
suite passes, and a subprocess CLI backup/list/restore smoke test reproduced a
synthetic file exactly. This paragraph records the earlier synthetic-only stage;
the current configured gameplay save is preserved as an opaque DSV wrapper and
the workflow still provides no native save parser/editor.

## Test result and immediate next experiments

23 automated tests passed, including all-resource compression re-encoding, all XBD/GAB/BSP
envelope round trips, all NSBTX round trips, and real ROM no-op/resize builds. See
`docs/VALIDATION.md`. Runtime proof is limited to the one palette edit.

1. Inspect actor binding groups plus decoded GroundAttack GMBs; select one same-tag
   existing-action rebind as the next isolated experiment only after documenting its target.
2. Compare matching-count GMB/SCA pairs and the eight exceptions; locate variable sections
   before labeling frame tables or combat metadata.
3. Compare the 104 changed OBJ bytes in Downtown_Save02/03, then adjacent Downtown rooms.
   Use the identical BSP as a control. Resolve room-loader/entrance IDs before test-map routing.
4. Investigate WoS string-tree/table candidates; use ACII as a lead, not a schema.
5. Decode known PuCrunch UI assets and establish DAT/PAL relationships before editing tiles.

## Movie cleanup, stable save association, and suit research â€” 2026-10-04

The user supplied DeSmuME gameplay screenshots of the previous movie suit. Its
black web pattern becomes disconnected dots at gameplay size. `movie_suit.py`
now defaults to a clean body-space paint: mapped red RGB555 (24,3,4), blue
(2,7,19), originally pale head eye islands (1,1,1), with the elongated emblem
retained. Procedural webbing, woven dither and original-texel luminance modulation
are removed; carrying original luminance retained the old texture's noisy detail.
Unmapped texels use the original. This changes artwork, not the binary schema.
128 I8 size and bounded scaled-UV model are unchanged from the earlier experiment.
Explicit legacy art generation reproduced the prior texture byte-for-byte.

The clean combined overlay retains the white alternate texture, both English menu
assets and yellow mission palette exactly. Only spd.nsbtx differs from the earlier
movie combined overlay. The six assets are promoted into private regular mods/.
Stable and isolated builds share SHA256
02e39959f69904e2fd5e2a756ebac3874b8dd3d4b34a9e310e350928361fbd88;
all 3,733 resources verified. Final 1,800-frame melonDS run returned 0; inspected
frame 1799 shows coherent solid red/blue opening gameplay. Offline preview confirms
dark lenses. Full animation, crowded texture budget, alternate suit and DeSmuME
Continue require manual checks. Full suite: 47 passing; seven affected tests rerun
successfully after final color/helper guard changes. No unknown binary fields were
assigned new meanings. See MOVIE_SUIT_EXPERIMENT.md for private evidence paths.

Local DeSmuME inspection with no running emulator found five nonempty 634-byte
Spider-Man DSV files, each associated with a different played ROM basename. All
were preserved and hash-validated in named legacy snapshots. The latest movie-suit
DSV matched recent-ROM entry 0 and was adopted into the stable modded ROM basename;
source bytes retained, previous destination preserved before replacement. SHA256
of adopted save: 548d4d8e6d7044b2299067de92c3d48c66896cd872abcb7f370b88d024938484.
Checkpoint before-suit-cleanup is available. No save payload/footer/slot/checksum
interpretation is introduced. Copy integrity is confirmed; Continue is unverified.

tools/playtest.py remembers the inspected Battery directory in work/playtest.json,
publishes build/Spider-Man-WoS-modded.nds, and uses existing opaque save snapshots
before builds. Windows tasklist CSV inspection blocks save/build mutations while
DeSmuME is running. It is a process preflight, not a lock against emulator relaunch.
Four synthetic tests cover stable association, two-save preservation, checkpoint
restore, repeated filename use, unchanged save bytes, process rejection, invalid
paths/formats and corrupt snapshots. Save-state replay and arbitrary room jumps
are not implemented. Details and PowerShell commands are in TESTING_WORKFLOW.md.

Read-only new-suit research confirms only spd.xbd among player-prefixed actor
definitions; no spdB.xbd appears in the manifest. There are 13 GroundAttack triplets
(1..6, 11..17) and direct references to the existing launcher, dive, dash-slam,
grapple and transform families. Their byte offsets/archive IDs are recorded in
NEW_SUIT_DESIGN.md and private build/suit-research/bindings.json. One actor definition
does not establish identical behavior in both forms or an absolute two-suit limit.
Suit selection, model loading, form-dependent action routing, damage/hitbox/status
fields, resource allocation and unlock persistence remain unknown. No XBD/GAB/GMB/
SCA/ARM9 changes were made. Adding a third suit is a research objective, not a
feature supported by the current replacement-only Glob tool. SUIT_CATALOG.md and
SUIT_IDEAS.json document 66 visual/playstyle concepts and proposed abilities.

## TASM 1 first action and save releases â€” 2026-10-04

User chose TASM 1 first, authorizing either existing-red-form development or a
third slot. The practical first release develops the red form. Selected backlog
is persisted in SUIT_ROADMAP.json; active kit and staged work in NEW_SUIT_DESIGN.md.
This entry supersedes the earlier no-gameplay-edit/Continue-pending statements.

### GAB record boundaries

All 227 GAB files contain whole 6-byte LE `<HHH>` records before the already
observed three-ffff terminator and optional two-byte zero padding. Total: 475
records. The first word is nondecreasing within every file; its interpretation
as an event time/frame is a hypothesis. Second/third words are unknown event/
parameter candidates. In particular `(time,1,5)` is not proven damage or a hit.
`Gab.parse` now exposes these tuples, retaining the original byte stream.
All 227 parse/serialize round trips pass; synthetic tests cover empty, single,
multiple records, alignment padding and malformed partial records.

### Player executable and read-only observations

The unchanged ARM9 SHA256 is
e541bfcd02441db86b43b8649aaa13570be301d302ddfb198804b78528d215dc.
It contains names consistent with C++ RTTI, including `6Spidey` at runtime
0x02129704 and `18SpideyStateMachine`. Inspection links the player type metadata
to vtables 0x0212E3F0, 0x0212E40C and 0x0212E510. A runtime object has these
pointers at +0, +8, +20. In the opening room, object 0x022A2F28 points at +0x30
to motion data 0x022A326C. These heap addresses are observations, not constants
used to locate the player. `player_trace.py` finds a unique matching layout and
bounds the motion pointer inside 4 MiB main RAM; harness use checks ARM9 identity.

Read-only correlations within motion data: +0x230 holds the observed GMB archive
ID, +0x23C its tested action-length candidate, +0x254 current action-ID candidate,
+0x178 increments every two emulator frames during the tested ground attacks.
+0x16C retains the last GAB ID, including after idle; it must not be treated as an
always-current action. Labels remain bounded observations, not a full actor schema.
Optional research disassembly used Capstone 5.0.9 installed only under ignored
work/research-libs. Build, trace and archive tools remain Python standard library.
No executable or RAM bytes are changed.

### Synchronized red opener replacement

Runtime tests show red opener GroundAttack11 (action candidate 56), alternate
opener GroundAttack1 (candidate 55). `tasm_suit.py` changes spd.xbd IDs at 0x164,
0x168, 0x16C from GroundAttack11's SCA/GMB/GAB 3371/3370/3369 to GroundAttack15's
3383/3382/3381. Only these three low bytes differ. Size stays 2,024; other bindings,
opaque tail and footer stay identical. This is one actor-asset experiment.

Paired single-attack traces: both begin at emulator frame 1700 in action 56;
baseline returns to idle at 1744, modified at 1724 (44 -> 24 frames). Captures
show the compact low kick. Repeated Y continues to actions 57/58/59 and idle,
using original successor GMB IDs 3373/3376/3379. L transformation displays the
white alternate form and Y still selects original GMB 3367. Hit/damage/range,
interruptions, bosses, room transitions and long-play behavior remain unmeasured.
Exact evidence, replay commands and private paths: TASM1_IMPLEMENTATION.md.

Rejected isolated experiment: decoded GroundAttack11.gmb u16@0 changed 30 -> 36
and literal-reencoded. Paired frames had unchanged clock/pose/duration. This is
not a proven speed control; field meaning remains unknown. No GMB/GAB/SCA edits
are in the release. Combined seven-asset ROM SHA256:
3c7ec9a5342a80bc20d6b9d058b2b8bfa029ee670d9d42b50a0642122fa9907c.
All 3,733 resources verified. Full suite: 55 tests passed in 75.744 seconds;
published-ROM boot/attack/idle and read-only battery resume test also returned 0.

### DeSmuME wrapper and automatic maintenance

Primary format sources: [DeSmuME dsv.txt](https://raw.githubusercontent.com/TASEmulators/desmume/master/desmume/doc/dsv.txt)
and [mc.cpp](https://raw.githubusercontent.com/TASEmulators/desmume/master/desmume/src/mc.cpp).
The last 40 bytes are six LE u32 followed by the 16-byte cookie
`|-DESMUME SAVE-|`. Source names describe written size, padded size, unused save
type, address size, unused save size, version (observed zero). Payload is the
first padded-size bytes; intervening wrapper text/bytes remain opaque and retained.
All five local 634-byte Spider-Man DSVs have footer words (1,512,1,1,512,0), a
512-byte payload and 82 intervening bytes. Written-size=1 must not be interpreted
as one byte of game progress. Game save checksums/slots/room IDs remain unknown.
`desmume_save.py` validates this bounded v0 wrapper and round-trips every byte.

The isolated melonDS core exposes 512-byte save RAM after load; source-backed
installation through retro_get_memory_data(0) occurs before its first frame.
Current payload copy successfully resumes in the early Residential save room.
Source: [melonDS DS v1.1.5 sram.cpp](https://raw.githubusercontent.com/JesseTG/melonds-ds/v1.1.5/src/libretro/sram.cpp)
and [core.cpp](https://raw.githubusercontent.com/JesseTG/melonds-ds/v1.1.5/src/libretro/core/core.cpp).
The harness never writes its result to the source save.

`Play Spider-Man.cmd` invokes configured DeSmuME with the stable ROM, making a
pre-play snapshot. `playtest.py build` validates/snapshots current progress, builds
a candidate, rechecks process/save state, retains the previous ROM under its hash
in build/releases, then atomically publishes the same stable filename. Synthetic
tests cover changed/invalid saves blocking publication, rollback retention and
launcher paths as well as earlier preservation/process guards. Before-tasm1 and
opening-save-room checkpoints were created. Real stable save SHA256 remains
548d4d8e6d7044b2299067de92c3d48c66896cd872abcb7f370b88d024938484 after release.
Native DeSmuME acceptance remains a player check; process detection is not a lock.

## Purchased Red-tab inventory and approval plan â€” 2026-10-04

User reports Snap Sweep works. They explicitly permit the free base opener, but
require every future move to replace a purchased red-suit skill with a new name
and comparable power. They requested a plan and will approve entries before
implementation. TASM1_UPGRADE_PLAN.md/.json record proposals; no further ROM,
overlay or executable changes are made in this audit.

Clean localized names/descriptions were read with the existing verified decoder.
The unchanged stage-one ROM was replayed with a private current-save copy, opened
through Pause -> Powers & Stats, and its Red tab inspected. Confirmed seven slots:

| Name/list/description text IDs | Original | Observed cost |
|---|---|---:|
| 183/184/185 | Web Kick | 100 |
| 186/187/188 | Web Launch | 200 |
| 189/190/191 | Mid-Air Snare | 600 |
| 192/193/194 | Spider Dance | 400 |
| 195/196/197 | Scissor-Kick Special | 600 |
| 198/199/200 | Amazing Speed Boost | 800 |
| 201/202/203 | Ultimate Speed Boost | 1,000 |

Both Suits has the shared launcher, enemy kick-off, roll kick, stomp, air dodge,
enhanced dodge and quick recovery; these are not red-specific replacement slots.
Reinforced Web is distinct progression functionality: clean text 377 confirms
heavy-object obstacles become grappleable on acquisition. Preserve that function
and acquisition gate along with core Web Grapple/Zip/Pull.

Proposed list/tooltip titles were encoded and decoded in memory: all 14 names
fit their original allocations; all other 1,035 text entries stayed unchanged.
Longer early names Web Rebound/Lizard Vault/Slingshot Strike exceed their native
slots, so the proposed menu labels use Rebound/Web Vault/Sling Strike. No text
overlays were written. Tooltip Rebound (Combo) stays shorter than the list name
Rebound Barrage, as the native Scissor labels also differ.

Purchase flag addresses, prerequisite masks, numeric speed effects, hit damage
and cancel semantics remain unmapped. Runtime prices do not decode their data
layout. Proposed effects/tradeoffs require paired hostile-target tests after
approval; they are not claimed equivalent or implemented yet.

Important alias: Snap Sweep's logical base GroundAttack11 binding now selects
GroundAttack15 payloads. The paid action also binds those payloads. Editing the
shared assets can affect the free opener; preserve them and change paid logical
routes independently. Gate testing must cover both owned and unowned slots.

Private evidence: work/upgrade-research/source.json and input schedules;
build/boot-tests/Spider-Man-WoS-modded-3c7ec9a5/red-skill-inventory and
shared-skill-audit. Research save-copy hash:
3367385a2fa73ee66b0c6b601a3e1d0acab04595762a169f5f1c0795f84ad183.
The real battery changed independently during this read-only audit; preserve the
latest closed-emulator bytes rather than replacing them with the earlier copy.
Stable ROM still hashes to
3c7ec9a5342a80bc20d6b9d058b2b8bfa029ee670d9d42b50a0642122fa9907c.

## Native combat mapping and purchased Rebound â€” 2026-10-04

This section supersedes the earlier claims that GMB/SCA payloads and purchase
flags are unmapped. The user approved the seven-slot plan and incremental releases.
The first purchased replacement is Rebound; the other six retain native behavior.
Detailed sources and limits: ORIGINAL_GAMEPLAY.md/.json, COMBO_ENGINE.md,
UPGRADE_ENGINE.md, ANIMATION_RESEARCH.md and TASM1_REBOUND.md.

### GMB channel boundaries and root motion

Decoded header: four LE u16 values at +0/+2/+4/+6. +2 is per-channel record
count, +4 is channel count; +0/+6 remain unknown. Each channel has a signed
kind and unknown u16 (`<hH>`), then the declared records. Kind/stride switch
0x0202A4FC confirms 0:28, 2:44, 3:32, 4:48, 5:36, 6:44, 12:32 bytes.
Kinds 6/12 do not occur in the clean survey. All 769 decoded assets parse and
reconstruct exactly; all 126 player clips contain three kind-3 arrays and one
kind-0 array, total size `24 + 124 * count`. No padding/tail is guessed.

For the selected player root channel, type-3 record words +0/+4/+8 are transform
translation components. Movement sampler 0x02071BAC uses +8 horizontally with
facing sign and +4 vertically. The normal physics path at 0x02073F60 also adds
root deltas before collision processing. Predicate 0x020B241C selects a root-only
path; its false return does not prohibit root movement. An experimental predicate
instruction patch was rejected. Rebound works with native instructions.

Other GMB record meanings remain unknown except bounded contact-window/geometry
correlations. Event/geometry channels, action duration and unknown bytes are
preserved. `tools/gmb.py` supplies structured lossless reconstruction and a
bounded word editor; compression is handled by the established wrapper.

### SCA pool layout and bounded animation authoring

All 869 resources have `4ACS`, a 28-byte header, u32 frame count at +4, joint
count at +8, static byte count at +0xC and frame stride at +0x10. Counts occupy
bytes 20..25; bytes 26..27 remain unknown. Three descriptor bytes per joint
select translation/rotation/scale pools: low bit 1 means static, high seven bits
are the pool index. Translations are 3*i32 Q12 (12 bytes), scale/inverse-scale
6*i32 Q12 (24 bytes), rotations 9*i16 Q12 matrices (18 bytes).

Total size is `28 + align4(3*joints) + align4(static_bytes) + frames*stride`.
Header, descriptors, pool bytes and alignment survive exact reconstruction.
All 126 player clips contain 37 joints. `tools/sca.py` rejects edits to constant
or shared rotations; independent dynamic matrices can be replaced or composed
with a bounded axis rotation. All 869 original round trips pass. Synthetic tests
preserve unknown/alignment bytes and reject malformed layouts and aliased edits.

Web Kick has 9 samples, 37 joints and stride 704. Its independent Chest_M
joint 3 rotation is at `860 + 704*sample`. Rebound changes only its four matrices
at samples 5..8 with local-X rotations -5/-11/-16/-12 degrees, after contact.
Rig hierarchy, general handedness, clip blending, new tracks and complete animation
export remain unknown/unimplemented; these are fixed-size authored recovery keys.

### Purchase records, ability ownership and native save flow

Native menu records are eight LE u32 values (32 bytes): ownership event,
required event, dependent event, name/list/description string IDs, level count,
cost. Tables: shared 0x02120260, Red 0x02120340, Black 0x02120420. All 21 rows
are verified against the clean ARM9 by a catalog test. Red events 322..328 map
to ability bits 13..19; Black 329..335 to 20..26. Shared events map to the bits
recorded individually in ORIGINAL_GAMEPLAY.json. Required/dependent values are
event IDs, not assumed masks. Dependency pairs include Spider Dance -> Scissor
and Amazing -> Ultimate; parents cannot be refunded while the child is owned.

Shared native costs: Uppercut 50, Kick-Off 200, Drill 400, Jackhammer 600, Air
Dodge 200, Enhanced Dodge 800, Quick Recovery 800. The earlier interpretation
of Enhanced Dodge as 400 from a screenshot was incorrect. Red costs remain
100/200/600/400/600/800/1000. All prices and flags remain native in this release.

Global stats pointer is 0x02145C5C; three ability words start at stats +0x0C,
XP currency is +0x44. The player +0xE8 aliases stats +0x0C. Query/set functions
are 0x020D22AC/0x020D24D8; native buy/refund are 0x020F1AA0/0x020F1B4C.
Web Kick query at 0x020B603C requires bit 13; success can enter controller state
42, animation action 49 then 50. State IDs and animation IDs are distinct.
Unowned/close-target/missed inputs follow native contextual fallback routes.

Actual isolated UI purchase changes 138 -> 38 XP and sets only bit 13. Native
game saving produces a 512-byte payload captured from a disposable emulator run.
Reloading this original-build purchase in Rebound keeps ownership and the paid
route; refund changes 38 -> 138 XP and relocks it. The real DSV is never edited.
Payload checksums/room layout remain unknown; no game save editor was introduced.

### Combo credit and hidden HUD

The lower-right meter increases enemy XP reward; clean instruction 393 confirms
a maximum-meter XP bonus. Exact multipliers remain unknown. No damage buff is
established. HUD vtable 0x0213C848, pointer cell 0x02145C44; model +0 is tier,
+4 Q12 gauge, +0x10 grace, +0x14 decay, +0x18 active, +0x19 credit marker.
Native accumulator 0x02083BF0 initially reveals the HUD when tier >0 or gauge
>30. An already active HUD may persist below this threshold while decaying.

Controlled Snap Sweep contact at frame 2729 raises the hidden gauge to about
12, its second contact at 2745 to about 24; action 57 contact at 2761 reaches
about 36 and reveals it. This explains the user's observation. No artificial
credit boost is needed. Logical red action 56 retains category 0; alternate 55
uses category 7. Repeat-category suppression and tier-dependent coefficients are
described in COMBO_ENGINE.md. Event 8 writes actor +0x28 through 0x02075370;
it is an action marker, not meter credit. Event 7 resets contact collection and
sets motion flag 0x20; event 1 parameters remain unknown.

### Accepted Rebound profile and validation

Rebound replaces Web Kick at 100 XP, native bit 13. Root GMB horizontal samples
become `(0,0,0,0,0,-4096,-10240,-16384,-20480)` Q12, producing a five-unit
backward player step after contact. Paired traces show X120 ->115 persists in
idle; native Web Kick stays X120. The authored SCA recovery changes only four
post-contact Chest rotations. GAB, contact geometry/windows and duration stay exact.

Attack-kind selector 0x020B2498 maps animation action 50 to kind 32. Three
response tables use 36-byte records; the third kind-32 record is zero/immune.
Impulse calculator 0x0207A5F4 reads +0x18 horizontal and +0x1C vertical fields.
Only ARM9 offsets 0x11A2B8/0x11AA98 change from signed -9011 to -4506. Paired
right-facing contact RAM confirms target velocity (9011,6554) -> (4506,6554).
Damage selection/data, vertical impulse, resistance flags and all instructions
stay exact. Raw enemy HP loss is not independently decoded; do not invent it.
The complete measured paid-move meter trace and action timeline match native.

`tools/tasm_rebound.py` generates a deterministic isolated build plus a recipe
pinning five required overlay hashes. `mod.py build/verify` reads the checked-in
`reference/gameplay_profile.json`; `--gameplay-profile original` explicitly keeps
native ARM9 data for controls. A missing/drifted required overlay fails. Probes
accept only the exact clean or accepted combat-data ARM9 hashes.

Accepted ROM SHA256:
`be5fedb66f760dbd0c7e3b7813bf3aba10b326a6514de881b5c542361674d9bf`.
Accepted ARM9 SHA256:
`3298417ae06c47571ea559ebe3e18d33da4ed6f3bfcdcb85025628c440438837`.
Nine assets differ; all 3,733 resources are reread/verified. The full suite passes
76 tests in 87.396 seconds. Runtime checks cover locked/owned, original purchase
carryover, native refund, alternate opener, persistent recoil, enemy reaction,
custom recovery and meter equivalence. Broader boss/wall/interruption/long-play
acceptance remains a player-testing limit. Rebound is released through the stable
save-preserving publisher; source ROM, real save and private test assets are not
distributed to GitHub.

### Accepted Web Vault event hook and root approach

Web Launch is action 51 / controller state 40 / GMB 3359,
`spd_GrapplePullBack`, native purchase bit 14 / 200 XP. Its GAB marker occurs at
time 5. Root-only vertical edits did not produce an airborne transition; native
hop calls on entry interrupted the launch and were rejected. The accepted hook
replaces five ARM instructions at 0x020C9268 in the state-40 launch event case:
`mov r0,r4; bl 020BF164; mov r1,#37; mov r0,#0xC00; b 020C925C`.
This calls the existing physical hop, then rejoins unchanged native response
stores/target dispatch. All other state cases, purchase/input gates, collision,
damage/resistance tables and shared upgrade rows remain exact.

The nine GMB root-X samples become `(0,0,0,8192,24576,40960,40960,40960,40960)`
Q12; vertical/geometry/event channels retain native bytes. Three independent Chest
SCA matrices at frames 3/4/5 are rotated 4/9/14 degrees. Runtime confirms a ten-unit
approach in either facing direction, an 11.632-unit hop, native landing, and normal
aerial attacks when separately requested. Refund relocks the move and returns
200 XP; repurchase and native save/reload preserve it. A missed grapple does not
vault. Rebound's five-unit recoil remains intact.

Paired native/modified enemy positions and animations match at four launch/ascent/
descent snapshots. Gauge/grace/decay/tier/active values match across all 289 traced
frames. The credit-marker byte clears earlier with the fall transition; it is
not claimed identical. Raw enemy HP loss remains undecoded. General ceiling/wall/
boss/interruption and native DeSmuME player acceptance remain pending.

Accepted ARM9 hash `6e563225538658c6c8437ede1886037132adc5ed865693727ef60457072529bf`;
ROM hash `bd94b6f9f8a8a1d8566aca4da284ba4c150ac675cd62ce6afb405a6e9be8c092`.
Eleven assets differ; all 3,733 resources verify. Full suite: 81 passing tests.
`tools/tasm_web_vault.py` composes both paid replacements; exact seven-asset hashes
are pinned by the current recipe. Stable publication preserved the current DSV,
named `before-web-vault` checkpoint and previous Rebound ROM. Detailed replay
paths and reproduction inputs are in TASM1_WEB_VAULT.md. TASKS.md is the durable
session handoff and ordered remaining-work tracker.


## 2026-10-04: bounded combat HUD/code extension

Confirmed by native runtime captures and reversible byte checks; detailed ABI,
file relocation, test results and limits are in COMBAT_FEEDBACK.md.

- ARM9 module parameters B64 identify the 24-byte ITCM/DTCM autoload table at
  1439A0..1439B8, source213E140, and main BSS213E140..214F420. SDK autoload runs
  before clearing main BSS. A third entry copies our own code into214F420; the
  main arena lower-bound literal at FF374 is raised by4000. Original RAM
  addresses, BSS bounds, startup, ARM7 and original autoload entries remain exact.
- ARM9 file growth requires shifting later header/FAT file offsets, not runtime
  addresses. Only verified ROM tail padding is consumed; all NitroFS resources,
  FNT, banner and ARM7 payloads are checked unchanged after relocation.
- Player native subtraction205F3F0 reads actor+E4 stats+84 Q12 HP; enemy subtraction
  20492A8 reads actor+44 Q12 HP and clamps before setter2049304. Different virtual
  layouts must not be confused. Capture effective capped loss, never attack
  request/strength. Training flag restores enemy HP to 40 Q12 after defeat.
- HUDTextBG vtable213C994, constructor20E8F04: +1C is the main BG2 font descriptor;
  +4 is the atlas layer. Native canvas2009328 has a cache at+38 and needs ~238
  bytes; font3 and UTF16 draw200B3A4 work with a full-size canvas. Our bounded
  glyph area begins at tile200; readouts clear only their own map rectangles.
- Native combo is a resource: 75*tier+floor(gauge/4096) crosses the tier rollover
  continuously. It is not a number of landed hits. Snap's initial 12 is confirmed
  onscreen while the native >30 bar threshold still applies.
- Current kind32 Rebound response pairs are (-2253,11469), compared with previous
  (-4506,6554). Immune/boss response record, damage and player recoil stay exact.

Own extension code is checked by hash; normal tools need only stdlib. These are
six known hooks, not a generalized decompiler, arbitrary code loader or camera
projection API. Incidental enemy loss attribution and specialized health paths
remain limits. No save payload or player persistent layout changed.

# Compact HUD, camera projection and Sling Strike (2026-10-04)

Confirmed against the hash-bounded CS5E runtime. Current details/evidence live in
COMBAT_HUD.md and TASM1_SLING_STRIKE.md; older feedback findings remain historical.

- Common enemy actor HP/max are +44/+48; motion pointer+30. The observer accepts
  only updating actors whose vtable+150 points to 02049304. Native motion base
  XYZ+7C/+80/+84 plus local XY+160/+164 form the observed world position;
  motion+8C is the observed half-height. Rendering snapshots does not retain a
  dereferenced actor object and drops stale records after two HUD updates.
- Global02145C54 points to SideScrollCamera(vtable02130684); camera+3C points to
  PerspectiveView(vtable02128A4C). View rotation matrix+C, eye+30/+34/+38,
  aspect+8C and FOV sin/cos+94/+98 reproduce observed training projection.
  Native020F961C transforms the world-minus-eye vector; 020FA840 divides Q12.
  With depth=-viewZ, X=128+128*(viewX/depth*cotFOV/aspect),
  Y=96-96*(viewY/depth*cotFOV). Bar top is projected half-height plus six pixels.
  Other camera classes are unsupported rather than guessed.
- Stock FontPaletteSprite entries3/15/2 are black/red/gray. Native font index0
  produces the small numeral; index3 was the prior large readout. BG2 bitmap
  canvas constructor02009328, XY020093F0, bitmap02009498 and flush02009398 work
  for authored 24x4 4bpp bars. Tile IDs200..2FF are reserved for this canvas.
- Enemy setter02049304 tests actor+88 bit4 and HP<=0, then native02049330
  assigns40. Changing only that conditional instruction to ldrle actor+48
  restores full native max HP in the training replay; ordinary enemies retain
  the branch that bypasses this refill. Other bits remain unknown.
- Mid-Air Snare's paid A route uses states30->31->51 and actions179/29->1/2/3
  in the measured right-facing case. Direct Y is a separate normal aerial route.
  Native gates at020B8EE4/020C76C0/020C7744 still query bit15; all records/prices
  remain unchanged. The common receiver function02094658 receives a source-actor
  reference in R2, retained in R5; its ordinary HP call is0209515C.
- Action queue020728F0 loads the logical action and stores motion+258. The paid
  source guard can replace requested action1 with3 after zip state31, preserving
  all animation assets and native normal-air requests. A qualifying kick's
  requested4096 loss becomes12288, replacing three native4096 follow-ups; the
  light409 zip contact remains. Capped HP loss and requested loss remain distinct.
- Actor+18/+1C are used by the native movement/collision path. Changing these
  during contact alone did not move the player reliably and could amplify target
  response. The accepted post-controller hook at02073B5C supplies three bounded
  horizontal steps and stops on normal air recovery. It leaves vertical velocity
  and coordinates intact; see the paired right/left landing traces. Hard walls,
  ceilings and special targets remain explicit runtime checks, not assumed passes.
- Authored Sling marker lives at extension state+680 (actor/countdown/confirmation).
  HUD ctor clears through+700. The SDK source size remains3600 and the reserved
  heap region4000; no game save bits or unknown purchase fields are repurposed.

Tests: exact HUD-to-Vault and Sling-to-HUD edit/revert; every native purchase row;
all NitroFS byte preservation; unchanged text slots and original red palette;
92-test suite and3733-resource verification. A wall-position fixture put actors
beyond the training floor and fell; it is not valid wall evidence. Normal-room
traversal produced no AI contact, so broader normal-fight coverage stays open.

# Player-feedback combat-flow revision (2026-10-04)

Confirmed native canvas02009498 consumes source columns, each of height argument5;
argument3 is source bits per pixel and argument4 is width. The former row-major
24x4 buffer produced repeated fill chunks. Native tilemap0200931C is row-major
32 cells: base+2*X+64*Y. Canvas+18 is the maximum drawn pixel height used by final
flush02009398/02009A48, and SetXY020093F0 does not reset it. Resetting the next
bar height accumulator after SetXY prevents numeral-height tail tiles escaping
four-row dirty tracking. Moving-camera screenshots confirm no fragments. Other
canvas fields remain known only to the extent described by traced consumers.

Native reaction37 records at ARM9 tables119E20/11A600 have horizontal1434,
vertical14336 Q12. Old accepted helper020BF164 supplied a smaller player hop;
paired old RAM shows player8909 versus target13415 vertical velocity at3206.
New hook after common target dispatch020C9314 accepts state40/bit14/common health
ABI/native result4, calls that native hop helper, copies the target's positive
actual vertical velocity and zeros target horizontal velocity. Native result4
is an observed accepted-contact result; other enum values are unknown. Final
right replay preserves205 Q12 player/target height difference and identical
vertical velocity across3206..3240. Left-facing owned launch also matches.

Sling keeps native queued action3 and12697 Q12 total request budget. Its own
bounded movement marker stores contact targetX/direction/destination; native
facing setter02072860 turns it back only after actual crossing. Controller fall
and landing can precede motion action changes, so recovery handling checks that
transition rather than discarding a still-active movement marker. A rejected
prototype discarded the marker early and caused residual travel/landing roll.
Final right/left replays stop and face the target; no new invulnerability exists.

Own source3600/heap reserve4000 are unchanged. Nine8-byte dirty rectangles at
state+700, count+6A0, render counters+6B0..6BC and cached projection scale+6C0..6C8
are bounded within that reservation. Ctor clearing through+700 resets counts;
rectangle contents are overwritten before use. Cheap observer02151920 filters
nonmatching/full/dead actors before existing full observer02150B20. Rendered bars
still use copied snapshots, never stale actor pointers. Font is warmed at room
entry; rendering halves native HUD cadence and skips idle. Native game timing
and ownership remain unchanged.

96 tests pass; edit/revert restores exact historical Sling;3733 resources verified.
Direct work counters show substantially fewer canvas passes/cell checks. Same-core
wall benchmarks are roughly flat overall (means~4.1ms); they do not establish a
DeSmuME FPS gain or prove the reported hitches are cured. Ordinary AI-density,
bosses, walls/ceilings/interruption and real DeSmuME lag remain player checks.
Current details/proof: COMBAT_FLOW.md, work/combat-flow/final-evidence.json.
