# Confirmed ROM analysis

## ROM
- Title: `SPIDERMANWOS`
- Game code: `CS5E`
- Maker code: `52`
- ROM image: 64 MiB
- Used ROM size: `0x03630800`
- ARM9 size: 1,325,496 bytes
- ARM7 size: 159,192 bytes
- ARM9 overlays: none
- ARM7 overlays: none

## NitroFS
Only two files exist:
- `Glob.bin`: 35,637,872 bytes
- `sound_data.sdat`: 19,678,720 bytes

This is unusually convenient: nearly all game-specific content lives in one archive.

## Glob.bin container
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

## Resource inventory
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

## Standard Nintendo Nitro formats already exposed
- `.nsbmd` has `BMD0` magic: 3D models
- `.nsbtx` has `BTX0` magic: texture archives
- `.nsbta` has `BTA0` magic: material/texture animations
- `sound_data.sdat`: Nintendo SDAT audio archive

These can be investigated with existing DS tooling such as apicula, NitroPaint, and Tinke/TinkeDSi.

## Important custom formats / likely responsibilities
- `.bsp` starts with `BSP\0`; paired with map `_app.obj` files. Strong candidate for room collision/geometry/navigation/region data.
- `.obj` paired with maps; likely placed objects/entities/triggers/encounters.
- `.xbd` associated with character/object model sets; likely definitions/bindings/state metadata.
- `.gab`, `.gmb`, `.sca` appear in animation/attack/state triplets. Player `spd_*` assets expose hundreds of named moves, making these high-value combat targets.
- `.mdat/.mgfx/.mpal` occur in visual scene/cutscene groups.
- `.2lz/.dat/.pal` occur in UI/minimap/tutorial sprite groups.
- `.strings` files are not plaintext; likely compressed/encoded and deserve separate RE work.
- `.cbmp` is a custom bitmap-like format.

## Player assets
The playable Spider-Man set is clearly exposed with prefix `spd`:
- `spd.nsbmd` (15,108 bytes)
- `spd.nsbtx` (4,772 bytes)
- `spd.xbd` (2,024 bytes)
- `spdB.nsbmd` (15,108 bytes), likely the alternate/black-suit model
- hundreds of named action assets, e.g. `spd_GroundAttack1.*`, `spd_Dash.*`, `spd_WebSwing*`, etc.

This is a strong sign that gameplay expansion can eventually be data-driven rather than requiring a full source decompilation.

## Map assets
Named room pairs expose the world structure directly. Confirmed regions include:
- Downtown: Map01..Map14 + save rooms
- Hive: Map01..Map10 + save rooms
- Pier: Map01..Map08 + save rooms
- Residential: Map01..Map09 + save rooms
- Sewer: Map01..Map13 + save rooms
- several test maps (`Test_Combat01`, `Test_Collision01`, `Test_Challenge01`, etc.)

The presence of shipped test maps is especially useful for reverse-engineering room formats and experimentation.

## Repacking
The included `tools/wos_tool.py` can already:
- parse NitroFS
- extract `Glob.bin` / `sound_data.sdat`
- unpack all 3,733 named Glob resources
- repack Glob after arbitrary same-file-count edits, including changed resource sizes
- rebuild the ROM and update NitroFS FAT offsets, keeping the original 64 MiB cart capacity

Next milestone: boot-test an unmodified round trip, then one visible asset modification.

## Validated workflow update — 2026-10-02

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
Gameplay fields, room semantics and WoS text encoding remain unknown.

See `VALIDATION.md`, `VISIBLE_MOD.md`, `FORMAT_NOTES.md`, and
`MODDABILITY_MATRIX.md` for the detailed evidence, tests and remaining priorities.
