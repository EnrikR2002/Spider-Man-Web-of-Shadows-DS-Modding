# Toolchain validation — 2026-10-02

## Tested input and exact round trip

The supplied private ROM matches the original project analysis. Its SHA256 is:

`61a6ed6e67fcce5cc63843fafeb0c0e6072bb750f552d5ff5d690cda02ea9203`

It is 67,108,864 bytes (64 MiB), USA CS5E, with 3,733 Glob resources. Every index,
filename, offset, length and first-eight-byte signature agrees with the existing
`reference/glob_manifest.csv` (SHA256
`1580beea32cf021711ba6e5e71b695a614854c3bf053188a59faf4153b6ac88d`).

The original tools were run before modification: ROM inspection, NitroFS extraction,
Glob unpacking, unmodified Glob repacking, and unmodified ROM repacking. Both outputs
were byte-identical. The result was reproduced using the hardened tools and `mod.py`.
There are **zero differing bytes/ranges**, so no padding/rebuild discrepancy needs explaining.

Glob SHA256 before and after:

`37f91388c4872627063f82670e33a915fdff2097c21ae21727e516a6157c0c8f`

The full ROM SHA256 after the round trip and after removing the test overlay equals
the clean SHA256 above. Complete per-resource SHA256s, ROM/FAT/header metadata, and
identity results are saved in `reference/roundtrip_report.json`. The extraction
manifests in `work/` include SHA256s as well. No binary game assets are in the report.

The baseline hash is intentionally pinned. A mismatch is not silently accepted as
another clean revision; inspect and separately establish its integrity before changing
the pin. A trimmed ROM is outside this validated 64 MiB workflow.

## Structural checks

- Header, FNT, FAT, ARM sections and banner fit in the image.
- FAT entries have nonnegative lengths, fit within used size, do not overlap each other
  or executable/metadata/banner regions, and correspond to the two known filenames.
- Declared cartridge capacity matches the image size; rebuilt data cannot exceed it.
- Header CRC16 is correct (clean CF20); size changes update it.
- Glob table starts at zero, its first offset is its size, its final offset is EOF,
  offsets are monotonic, and exactly one valid embedded filename table is present.
- Every extracted resource's length/SHA256 matches clean source data.
- Every rebuilt Glob resource is read back from the ROM and compared to its expected bytes.
- SDAT remains exactly identical when only Glob resources change.

Unmodified builds preserve every original byte. Modified builds preserve unknown
source bytes wherever the known replaced/moved regions permit. Shrinking preserves
vacated bytes; growth consumes only validated padding beyond used size. FNT, ARM9,
ARM7, banner and cartridge capacity are not re-encoded.

## Automated tests

Run:

```powershell
python -m unittest discover -s tests -v
```

Result: **23 tests passed** with the supplied ROM, including:

- Synthetic Glob no-op/grow/shrink/empty resource and extracted-directory round trips.
- Invalid offsets, missing/duplicate/unsafe names and reordered extraction manifest rejection.
- Synthetic FAT/FNT/header corruption, capacity overflow and unknown-tail overwrite rejection.
- Original/input output protection, including hard-link identity checks in the writer.
- Exact filename validation, protected name table, deterministic overlay builds and logs.
- Real-ROM byte-identical no-op and arbitrary resource length changes, preserving 3,732 other resources.
- Lossless parsing of all 272 NSBTX files; reversible palette edits confined to their data pool.
- Rejection of a palette pool that overlaps texture data, preventing edits to pixel indices.
- Lossless XBD/GAB/BSP envelope parsing for all 248/227/75 files and a byte-confined XBD binding edit.
- Handcrafted PuCrunch word order, escaped literal, RLE, short/long LZ, EOF and malformed cases;
  handcrafted standard LZ77 overlapping copy.
- Decode -> literal encode -> decode equality for all 918 supported GMB/2LZ streams,
  and exact original-wrapper preservation for unchanged data.

The full suite took about 69 seconds here; compression re-encoding dominates.
Private-ROM tests skip when the ROM is absent, so synthetic tests need no copyrighted fixtures.
Resized XBD test payloads are container-level corruption regressions **not gameplay mods**;
they are constructed in memory and never used for the visible experiment.

## Reproduction

```powershell
python tools/wos_tool.py inspect-rom 'original/Spider-Man - Web of Shadows (USA) (En,Fr).nds'
python mod.py extract
python mod.py verify --round-trip
python -m unittest discover -s tests -v
```

The round-trip command writes `build/roundtrip/Glob.bin` and
`build/roundtrip/Spider-Man-WoS-unmodified.nds`; both are private/ignored artifacts.
Then `python mod.py build` builds whichever overlay is currently active, and
`python mod.py verify` checks that build against the current clean-source + overlay inputs.

## Runtime verification and limits

Both the unmodified round-trip ROM and green-suit build ran for 1,800 frames in
the pinned official Windows x64 melonDS DS 1.1.5 core with built-in BIOS and software
rendering. Both reached Residential gameplay. The same scripted Start/A sequence
produced the same pose; all 452 changed screenshot pixels lie in the player's sprite
area. Captures, settings, source hashes and core identity are recorded separately;
see `docs/VISIBLE_MOD.md` and `reference/visible_mod_report.json`.

This establishes one visible texture modification and a successful baseline boot.
It does not establish a full playthrough, hardware compatibility, new archive resource
creation, arbitrary engine data edits, or runtime acceptance of re-encoded compression streams.
Those need their own one-change experiments.
