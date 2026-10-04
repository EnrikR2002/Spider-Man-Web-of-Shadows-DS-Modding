# Moddability matrix

Updated 2026-10-04 for the validated private USA CS5E ROM. Confidence applies to
the described structure; runtime behavior requires separate experiments.

| Format / area | Likely or confirmed control | Parsing status | Editing status | Confidence / next step |
|---|---|---|---|---|
| NDS / NitroFS | Executables and top-level resources | Bounds/FNT/FAT/header CRC/capacity validated | Lossless no-op; changed lengths within 64 MiB supported | High: exact ROM identity and resize tests; no-overlay DS layout only |
| Glob.bin | Ordered named asset container | All 3,733 resources indexed and hashed | Overlay replacement, variable sizes; no adding/renaming/deleting IDs | High: exact archive and ROM round trips |
| NSBTX | 3D texture pixels/palettes; spd red-suit texture confirmed | All 272 parsed losslessly; dictionary/data bounds checked | Palette edits and hash-bounded 64→128 player I8 repaint; clean panels/black lenses promoted | High for bounded profile: texture/model round trips and gameplay boot; general encoder deferred |
| NSBMD | Standard Nitro models | Player exported with coherent UVs; bounded material/shape GPU stream inspection | Player UV scaling and material dimensions only; no topology/skeleton editor | 1x identity/exact inverse tests; 128 texture control reaches gameplay; see MOVIE_SUIT_EXPERIMENT.md |
| NSBTA | Material/texture animation | Extracted/inventoried; actor XBD tag 1 references confirmed | No animation editor | Medium for bindings; payload not locally decoded |
| XBD actor kind | Direct SCA/GMB/GAB/NSBTA bindings; other state/config fields unknown | Envelope all 248; bindings in 155 actors; opaque tails retained | TASM red opener rebinds one synchronized action triplet; only three bytes differ | Runtime pose/duration/chaining and alternate-form control established; hit/damage tests pending |
| XBD UI/other kinds | UI definitions/configuration, inferred from names | Envelope only: 92 UI-associated + one other kind | Raw replacement only | Medium for envelope; payload unknown |
| GAB | Move/action event metadata, hypothesis | All 227 parsed as 6-byte three-u16 records plus terminator/padding; exact round trips | Reuse existing action with synchronized binding; no semantic event editor | High for record boundaries; timing/event/parameter meanings unknown |
| GMB | Move/animation data, hypothesis | All 769 decompress: 749 PuCrunch + 20 LZ77 | Codec re-encoding tested; decoded gameplay structure unknown | High for codec; shared-count hypothesis has eight exceptions |
| SCA | Skeletal/action data, hypothesis | All 869 surveyed; `4ACS` magic confirmed | No semantic editor | Low for payload; compare against decoded GMB counts first |
| BSP | Room spatial/collision data, hypothesis | All 75 envelopes/region offsets parsed losslessly | No geometry/collision editor | High for envelope; low for node/coordinate semantics |
| OBJ | Room placements/encounters/triggers, hypothesis | Paired 75; word0=2, rest unknown | No object editor | Low: begin with 104-byte difference between Downtown_Save02/03 |
| STRINGS | Localized text; English/American menu instructions decoded | Hash-bounded Huffman tree and 1,049 UTF-16LE slots round-tripped; prefix unknown | Same-slot text edits, 35 readability replacements; other languages unsupported | High for bounded codec; menu wrapping/runtime pending; see SUITS_MENU_PASS.md |
| FONT | Glyphs/metrics, likely | Fourteen files inventoried | No font editor | Low: map one runtime glyph/codepoint |
| 2LZ | UI/sprite image data, likely | 149 PuCrunch decoded; four 00 wrappers unknown; two hash-identified minimap sheets have coherent 4bpp tiled previews and exact round trips | Codec usable; bounded tiled conversion tested, no pixel runtime edit | High for codecs; medium for two preview layouts, not a general schema |
| DAT / PAL | UI frame/tile metadata / palettes, likely | 153 families inventoried; first two DAT bytes fit two minimap dimension candidates; other DAT fields unknown | One-entry mission PAL experiment with strict clean profiles and guarded revert | User DeSmuME screenshot shows intended yellow marker/dark edge; animation and broader palette ownership unverified |
| CBMP | Custom bitmap data, likely | 142 files inventoried | No editor | Low: determine dimensions/compression experimentally |
| MDAT / MGFX / MPAL | Cutscene visual groups, likely | 65 sets inventoried | No editor | Low; defer until higher-value formats are useful |
| SDAT | Standard DS audio archive | Top-level file preserved and hashed | Low-level whole-file replacement supported, internal editor absent | High for container preservation; audio edits untested |
| ARM9 engine | Loaders, gameplay rules, allocation/room routing | Spidey/state-machine RTTI found; bounded read-only player RAM probes tied to known ARM9 hash | No executable/RAM writes | Red/alternate opener resource routing observed; selector/conditional ability handlers remain unknown |
| Battery saves (.sav/.dsv) | Progress stored by emulator; game payload opaque | Lossless DeSmuME v0 footer/payload separation; source-backed dimensions and snapshot integrity checks | Stable launcher, pre-play/pre-release backups, named restore, prior-ROM rollback; no game save editor | Current DSV copy resumes in melonDS; real file remains identical; native DeSmuME Continue pending |
| Third playable suit / action routing | Independent selectable appearance and ability kit | Red opener GroundAttack11, alternate GroundAttack1 runtime-confirmed; selector unknown | TASM red-form stage one shipped; selected shortlist persisted; third slot not implemented | One changed action proven; custom transitions/counters and independent slot remain research; see NEW_SUIT_DESIGN.md |
| Purchased red skills / progression | Seven paid skills and their gating | Native names/text IDs and in-game prices inventoried; actual purchase flags/prerequisites/speed values unmapped | Proposed one-for-one replacements in TASM1_UPGRADE_PLAN; waiting for user approval | Costs/name fit verified; no gate or gameplay patch; preserve shared skills, core traversal and free Snap Sweep |

The green-suit example has verified gameplay proof and an inverse workflow; see
`VISIBLE_MOD.md`. The current isolated QoL experiment lives under
`build/qol-mission-icon/mods/`, not the normal `mods/` directory. It changes only
MissionMiniMapIcon.pal, boots to gameplay, and preserves baseline opening captures.
A user DeSmuME screenshot now shows the intended yellow mission marker; animation,
paired comparison, and checkpoint reload remain pending. See `QOL_PLAN.md`.
