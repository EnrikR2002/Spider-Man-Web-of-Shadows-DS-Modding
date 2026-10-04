# Native upgrade ownership and purchase routing

2026-10-04. Read-only research for the USA CS5E engine. This document records
original behavior, not implemented TASM replacements. Runtime addresses below
are valid only for ARM9 SHA256
`e541bfcd02441db86b43b8649aaa13570be301d302ddfb198804b78528d215dc`.
Heap locations vary; use pointers and cross-checks rather than fixed heap addresses.

## Native Red menu records

The original ARM9 has seven 32-byte records beginning at runtime `0x02120340`
(ARM9 file offset `0x120340`). Each contains eight LE u32 words. Disassembly of
the menu confirms the following meanings:

| Offset | Meaning | Evidence |
|---|---|---|
| +0x00 | Ownership event ID for the first level | Menu query and purchase/refund handlers pass it to the event service. |
| +0x04 | Required ownership event ID, or sentinel 382 | Disabled predicate rejects a non-sentinel requirement when its query is false. |
| +0x08 | Dependent ownership event ID, or sentinel 382 | Disabled predicate rejects the row when a non-sentinel dependent is owned. This prevents selecting/refunding a parent while its child remains owned. |
| +0x0C | Name string ID | Matches the decoded native names. |
| +0x10 | Second name string ID | Matches native list/tooltip text; exact UI assignment is documented in the approval plan. |
| +0x14 | Description string ID | Matches the decoded native instructions. |
| +0x18 | Number of consecutive ownership events/levels | `0x020F123C` counts owned events from the first ID over this many levels. Each Red row has one. |
| +0x1C | Price per level | Buy subtracts this value from currency; refund adds it. |

The record table pointer list is at `0x02120170`; entry 1 points to Red,
entry 2 to Black. Corresponding entry counts are at `0x02120188`; both have
seven rows. Other categories are outside this bounded mapping.

| Native skill | Record address | Ownership event | Ability bit | Required event | Dependent event | Cost |
|---|---:|---:|---:|---:|---:|---:|
| Web Kick | 0x02120340 | 322 | 13 | 382 | 382 | 100 |
| Web Launch | 0x02120360 | 323 | 14 | 382 | 382 | 200 |
| Mid-Air Snare | 0x02120380 | 324 | 15 | 382 | 382 | 600 |
| Spider Dance | 0x021203A0 | 325 | 16 | 382 | 326 | 400 |
| Scissor-Kick Special | 0x021203C0 | 326 | 17 | 325 | 382 | 600 |
| Amazing Speed Boost | 0x021203E0 | 327 | 18 | 382 | 328 | 800 |
| Ultimate Speed Boost | 0x02120400 | 328 | 19 | 327 | 382 | 1,000 |

382 is the observed no-event sentinel; it is not a purchase bit. The dependent
column is not a second skill granted by purchasing the row. Spider Dance and
Scissor form one dependency pair; Amazing and Ultimate Speed form another.

## Purchase, refund and gameplay ownership share one bitset

The event query at `0x020D22AC` handles IDs 309..381 by subtracting 309 and
reading the resulting ability bit through `0x0203B98C`. The event setter at
`0x020D24D8` maps the same range and changes the corresponding bit through
`0x0205721C`. Consequently, Red ownership events 322..328 map to bits 13..19;
the seven Black rows map to bits 20..26.

The global pointer cell `0x02145C5C` points to the stats object. Its three ability
words begin at +0x0C; currency is u32 at +0x44. These are runtime fields.
The game's on-disk checksum, slot layout and save offsets are not decoded here.
No save bytes were edited to establish this mapping.

The menu disabled predicate at `0x020F1150` combines currency, current ownership,
the prerequisite event and dependent event. Having insufficient currency blocks
an unowned row. An owned row remains selectable for refund unless its dependent
is owned. The buy handler `0x020F1AA0` subtracts the native row price, chooses the
first unowned level and sets its event. The refund handler `0x020F1B4C` adds the
price back and clears the last owned level. Native menu availability may have
additional surrounding conditions; this does not establish all story gates.

Gameplay queries use the player getter at `0x02060240`. It reads an ability-word
pointer from player +0xE8, then calls the same bit test `0x0203B98C`. A runtime
dump from the earlier Red-menu audit confirmed player +0xE8 equals stats +0x0C.
That dump had currency 39 and all seven Red skill bits clear. The free Snap Sweep
base opener does not require these purchased bits.

`tools/upgrade_trace.py` exposes this ownership/currency view. It requires the
clean ARM9 or exact known Rebound combat-data variant identity, identifies the player by the existing three-vtable
layout, bounds all memory pointers, and checks the player/stats alias. It reads
RAM only. Five synthetic tests cover ownership separation, unchanged input,
locked skills, mismatched pointers, invalid bounds and ROM identity guards.

For movement comparisons, `player_trace.sample` now follows the native position
getter `0x02074CD0`: position components are signed motion +0x7C plus +0x160,
and +0x80 plus +0x164. The vector getter at `0x02074D10` instead reads geometry
dimensions at +0x88/+0x8C/+0x90; those must not be mistaken for player position.
Facing is returned by `0x02074D3C` from motion +0x180. Positional replays now
confirm the Q12 scale for the bounded recoil experiment; signed values are retained.

## Web Kick and Web Launch transitions

The native command path at `0x020B603C` requests ability bit 13 through the player
interface. Its failed query branches at `0x020B6054` past the paid Web Kick path.
When owned, additional target and positional checks must pass; the successful
return at `0x020B61F8` is state ID 42 (`0x2A`). A live paid grapple test subsequently
selected animation action 49/GMB3353, followed by action 50/GMB3356. During the
kick, controller +0x14 is **43**, as checked from paired RAM at emulator frame
3208. Controller states and animation action IDs must be traced separately.

The nearby Web Launch query at `0x020B6264` requests bit 14. A successful query
returns state ID 40 (`0x28`) at `0x020B6280`. Failing this query follows other
native routing rather than granting Web Launch. State IDs are distinct from
the GMB resource IDs and animation/action IDs observed in player telemetry.

Preserve these native gate checks for Rebound/Web Vault. Renaming text or editing
an animation does not constitute a new purchase mechanism. An existing purchased
bit should simply select the replacement behavior after release.

## Rebound movement research

The motion object's first selected GMB channel is stored at +0x23C/+0x240.
`0x02071BAC` obtains a difference between two channel samples through
`0x02077D94`, `0x0207793C` and the generic transform sampler `0x0202968C`.
For type-3 records, record words +0,+4,+8 become transform translation +0x14,
+0x18,+0x1C. The two-dimensional movement result uses the +8 component for
horizontal motion, flipping its sign with facing, and +4 for vertical motion.
The first-channel horizontal values are zero in both native grapple-attack GMBs.

Actor update `0x02073D50` checks motion +0x2FC bit 10, or a state-machine
predicate. `0x020B241C` returns true for states 11,12,13,14,17,59,60,61,62,81.
This selects a **root-only movement path**, not permission to move. When false,
execution continues at `0x02073DEC` into the normal physics path. At
`0x02073F60..0x02073F90`, it still adds the sampled root delta to actor +0x18/+0x1C,
then adds the physics delta before collision processing. Both paths apply root
movement. The earlier hypothesis that state 42 required enabling was incorrect.

A GMB-only control confirmed the original engine applies the authored recoil
through normal physics: player X120 becomes X115 after the kick and stays there
in idle. An unnecessary experimental predicate patch was rejected and archived
under work/upgrade-gates/experimental-engine-patch/. No instruction edit is
required or shipped for this movement.

The SCA codec has since been decoded, with all 869 clips round-tripping.
ANIMATION_RESEARCH.md records the loader, evaluator and safe joint-matrix editor.
TASM1_REBOUND.md records the authored recoil/pose and the separate, narrowly
bounded horizontal-impulse data edit.

Private scratch and code traces are retained in `work/upgrade-gates/`. Research
uses disposable builds and battery copies. The accepted release changes two ARM9
data words and bounded assets; it changes no instructions or real save bytes.

## Purchase and catalog validation

The original Both Suits table at 0x02120260 confirms Uppercut50, Enemy
Kick-Off200, Drill400, Jackhammer600, Air Dodge200, Enhanced Dodge800 and
Quick Recovery800. The Black table at 0x02120420 has the same seven price
tiers as Red, with Widowmaker -> Poison Pummel and Super Charge -> Quick
Charge dependency pairs. ORIGINAL_GAMEPLAY.json records every row address,
event, purchase bit, cost and parent/dependent; a test cross-checks all21
rows against the original ROM. A screenshot interpretation of Enhanced400
was incorrect and is superseded by its native record.

An isolated actual UI purchase changed currency138 ->38 and set only bit13
for Web Kick. The final candidate uses that same purchase path under the
Rebound name. Unowned input selects the ordinary action instead of the paid
pull49/kick50 chain. All real save bytes are left to the normal native saver.
