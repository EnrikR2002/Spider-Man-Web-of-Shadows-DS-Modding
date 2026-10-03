# Format notes

Evidence date: 2026-10-02. Target: the private USA CS5E dump identified in
`docs/VALIDATION.md`. `docs/ANALYSIS.md` remains the original confirmed inventory.
Reports: `reference/roundtrip_report.json`, `reference/format_survey.json`, and
`reference/visible_mod_report.json`. Generated asset data stays in ignored folders.

## NitroFS / ROM — confirmed and tested

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

## Glob.bin — confirmed and tested

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

## NSBTX / TEX0 — structural parsing and palette editing tested

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

## XBD — outer envelope and actor resource bindings confirmed

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

## GAB / GMB / SCA — first differential pass

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

## Compression wrappers — confirmed codecs, limited re-encoding

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

## BSP + paired OBJ — envelope/offsets confirmed, room semantics unknown

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

## STRINGS + FONT — compatibility lead only

All six `.strings` and fourteen `.font` files are inventoried by size/hash. The
[ACII Discovery notes](https://github.com/hoothin/AC-II-Discovery-Hans) describe
Huffman text and font investigation, and [its decoder](https://github.com/hoothin/AC-II-Discovery-Hans/blob/main/getText.py)
uses game-specific tree/data offsets. Those offsets are **not** used here. Shared
Griptonite archive behavior does not establish shared string layout. WoS text is
still unparsed; take a runtime text sample/dump or identify tree/table relationships
across all six languages before writing an editor. FONT encoding/glyph mapping is unknown.

## 2LZ / DAT / PAL / CBMP — inventory plus compression progress

149/153 `.2lz` files are confirmed type-60 PuCrunch and decode/round-trip through
the codec. Four start with 00: `DeathPalHealth`, `DeathPalPoison`,
`FontPaletteSpriteSpidey`, and `GoalCheck`. The first three are 36 bytes and GoalCheck
is 100; all have first u32 00002000. A simple uncompressed-size wrapper would account
for only 32 bytes, leaving GoalCheck unexplained, so these remain unsupported/unknown.
Do not silently apply a raw-body assumption to them.

DAT tile/frame layout, PAL indexing/ownership, and CBMP dimensions/payload remain
unknown. Corresponding names and hashes are surveyed. No custom UI asset was changed;
the visible test used the standard Nitro texture instead.

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
