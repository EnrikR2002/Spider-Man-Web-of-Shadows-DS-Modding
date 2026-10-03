# Moddability matrix

Updated 2026-10-02 for the validated private USA CS5E ROM. Confidence applies to
the described structure; runtime behavior requires separate experiments.

| Format / area | Likely or confirmed control | Parsing status | Editing status | Confidence / next step |
|---|---|---|---|---|
| NDS / NitroFS | Executables and top-level resources | Bounds/FNT/FAT/header CRC/capacity validated | Lossless no-op; changed lengths within 64 MiB supported | High: exact ROM identity and resize tests; no-overlay DS layout only |
| Glob.bin | Ordered named asset container | All 3,733 resources indexed and hashed | Overlay replacement, variable sizes; no adding/renaming/deleting IDs | High: exact archive and ROM round trips |
| NSBTX | 3D texture pixels/palettes; spd red-suit texture confirmed | All 272 parsed losslessly; dictionary/data bounds checked | Same-length palette edits; green-suit experiment available | High: visible gameplay proof in melonDS; general texture encoding deferred |
| NSBMD | Standard Nitro models | Extracted/inventoried; external apicula available | No local mesh import/editor | Standard format known; use viewer then one material/mesh experiment |
| NSBTA | Material/texture animation | Extracted/inventoried; actor XBD tag 1 references confirmed | No animation editor | Medium for bindings; payload not locally decoded |
| XBD actor kind | Direct SCA/GMB/GAB/NSBTA bindings; other state/config fields unknown | Envelope all 248; bindings in 155 actors; opaque tails retained | Existing same-tag reference replacement helper, no runtime rebind test | High for IDs/tags; unknown flags/tail semantics |
| XBD UI/other kinds | UI definitions/configuration, inferred from names | Envelope only: 92 UI-associated + one other kind | Raw replacement only | Medium for envelope; payload unknown |
| GAB | Move/action event metadata, hypothesis | All 227 opaque u16 streams + observed trailer | No semantic event editor | Low for events; compare 13 numbered player attack triplets |
| GMB | Move/animation data, hypothesis | All 769 decompress: 749 PuCrunch + 20 LZ77 | Codec re-encoding tested; decoded gameplay structure unknown | High for codec; shared-count hypothesis has eight exceptions |
| SCA | Skeletal/action data, hypothesis | All 869 surveyed; `4ACS` magic confirmed | No semantic editor | Low for payload; compare against decoded GMB counts first |
| BSP | Room spatial/collision data, hypothesis | All 75 envelopes/region offsets parsed losslessly | No geometry/collision editor | High for envelope; low for node/coordinate semantics |
| OBJ | Room placements/encounters/triggers, hypothesis | Paired 75; word0=2, rest unknown | No object editor | Low: begin with 104-byte difference between Downtown_Save02/03 |
| STRINGS | Localized text, likely | Six language files surveyed; ACII Huffman reference found | No text editor | Low: locate WoS tree/index tables before applying another game's algorithm |
| FONT | Glyphs/metrics, likely | Fourteen files inventoried | No font editor | Low: map one runtime glyph/codepoint |
| 2LZ | UI/sprite image data, likely | 149 PuCrunch decoded; four 00 wrappers unknown | Codec usable; tile/frame editing not established | High for 149 codecs; low for custom image layout |
| DAT / PAL | UI frame/tile metadata / palettes, likely | 153 paired families inventoried | No custom layout/palette editor | Low: pair decoded 2LZ dimensions and palette use |
| CBMP | Custom bitmap data, likely | 142 files inventoried | No editor | Low: determine dimensions/compression experimentally |
| MDAT / MGFX / MPAL | Cutscene visual groups, likely | 65 sets inventoried | No editor | Low; defer until higher-value formats are useful |
| SDAT | Standard DS audio archive | Top-level file preserved and hashed | Low-level whole-file replacement supported, internal editor absent | High for container preservation; audio edits untested |
| ARM9 engine | Loaders, gameplay rules, allocation/room routing | Original executable extracted unchanged | No code patch | Defer full decompilation; target loader callsites when data evidence requires it |

Only one content experiment is currently active: `mods/spd.nsbtx`. It has a
verified inverse workflow and before/after gameplay captures. See `VISIBLE_MOD.md`.
