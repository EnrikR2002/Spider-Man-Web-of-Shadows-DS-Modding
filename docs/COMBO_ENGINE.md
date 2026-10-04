# Combo meter and GMB channel research

Research target: clean USA CS5E ARM9 SHA256
`e541bfcd02441db86b43b8649aaa13570be301d302ddfb198804b78528d215dc`.
Addresses below are runtime ARM9 addresses, not ROM file offsets. Subtract
`0x02000000` to address `work/rom/arm9.bin`. Analysis is read-only; no executable
patch or real save modification is required for these findings.

## What the original meter rewards

The native Combo Meter tutorial (localized text ID 393) explains that combining
attacks raises the meter, increases enemy Experience Point drops, and earns a
large bonus at maximum. It is an experience reward system. Exact XP multipliers
and the maximum bonus amount remain unverified; the tutorial does not establish
a damage multiplier.

The original engine also rewards variety. Each attack category has a base meter
gain, a repetition penalty and an expiry time. Repeating one category can stop
earning meter until its repetition history expires. Multiple contacts within
one action have distinct treatment through the credit marker; this should be
retained when modifying moves instead of applying an arbitrary meter boost.

## Why the first Snap Sweep hits can appear not to count

Starting from an inactive meter, the HUD deliberately stays hidden at tier zero
while gauge is **30 or below**. It becomes active when gauge exceeds 30, or when
the meter reaches a higher tier. Once active, it can remain visible during decay
below 30 until the model clears. The underlying gauge can increase while no
meter is visible.

An isolated native Test Upgrades replay with a battery copy records:

| Emulator frame | Logical action / action clock | Gauge | Active flag |
|---:|---|---:|---:|
| 2729 | 56 / 4, Snap Sweep first contact | 12.0007 | 0 |
| 2745 | 56 / 9, Snap Sweep second contact | 24.0015 | 0 |
| 2761 | 57 / 2, native second combo action | 36.0022 | 1 |
| 2837 | 59 / 4, native later combo action | 81.9050 | 1 |

This proves the tested Snap Sweep contacts receive credit. It also explains why
the user could see the meter appear only during the following combo actions.
It does not prove that every distance, enemy, block state or interrupt behaves
identically. The clean opener comparison and damage balance require separate
paired tests; Snap Sweep's borrowed motion contains two active contact windows,
where the original opener contains one.

Private evidence:
`build/boot-tests/Spider-Man-WoS-modded-3c7ec9a5/training-contact/player-trace.json`.
The first training-single attempt misses and shows zero credit in both builds;
misses must not be used to diagnose a meter defect.

## Static engine map

The `HUDComboMeter` RTTI name at `0x0213C850` identifies its vtable
`0x0213C848`. Its constructor/update at `0x020E7C4C` / `0x020E7D48` read the
combo model through the global pointer at `0x02145C44`. Heap addresses vary by
room and are not constants. The bounded read-only probe follows this pointer.

| Combo model offset | Static behavior / bounded interpretation |
|---:|---|
| `+0x00` | Tier, advanced while below 5 |
| `+0x04` | Gauge in signed Q12 fixed point, clamped to 0..100 |
| `+0x08..0x0C` | Repetition-history list; nodes contain category, expiry and count |
| `+0x10` | Grace countdown before decay |
| `+0x14` | Gauge decay amount, initially `0x800` = 0.5 |
| `+0x18` | Active flag read by HUD; initial activation requires tier >0 or gauge >30 |
| `+0x19` | Credit marker used to group related contacts; complete lifecycle pending |

Relevant functions:

- `0x020836E4`: initializes model to zero, decay to 0.5.
- `0x02083718`: per-update decay/history expiry. Decreases grace; when expired,
  subtracts decay from gauge. On crossing zero, loses a tier and resets gauge
  to 75; doubles decay. At decay >=8, clears remaining tier/gauge.
- `0x020837D8`: registers a credited category, applies repetition, contact and
  tier scaling, then calls the accumulator when the amount is positive.
- `0x02083BF0`: adds credit, resets decay to 0.5, gives at least 15 updates of
  grace. At gauge >=100 and tier <5, advances tier and subtracts 75 from gauge;
  gives at least 30 updates of grace. Sets active when tier >0 or gauge >30.
- `0x02083A9C`: penalty path subtracts two tiers, sets gauge to 75 if tiers
  remain, otherwise zero. Its observed combat caller is `0x020B3BB8`; exact
  trigger classification still needs runtime confirmation.
- `0x02083A90`: clears the credit marker; do not assume this runs every frame.
- `0x02083AE4`: raises grace to at least the requested value.

These are game update counts, not established seconds. Emulator frames and game
updates can differ; the tested action clock advances every two emulator frames.

Credit table `0x0211BCB0` consists of four-byte records `<BBH>`: base amount,
repetition percentage and history expiry. This is indexed by **credit category**,
not directly by animation or archive ID. Tier scaling at `0x0211B894` has Q12
values `3277,2662,2048,1638,1229,819`, approximately
`0.8,0.65,0.5,0.4,0.3,0.2`. Base amount 15 at tier zero produces 49155 Q12,
matching the measured 12.0007 gain. A separate contact argument can halve gain.

`SpideyStateMachine` vtable `0x021352A4` slots `+0xE4`, `+0xE8`, `+0xEC`
route target/contact categories through `0x020CC014`, `0x020CC760`,
`0x020CCCA8`. These are called by contact processing at
`0x020B3330..0x020B3378`; eligibility is checked through slot `+0xD8` first.
Slot `+0xE0` / `0x020CBFF0` ultimately registers the category.

For the ordinary category path:

- Logical red opener action 56 maps to credit category 0.
- Logical black opener action 55 maps to credit category 7.
- Both table records are `(15,100,180)`.
- Snap Sweep keeps logical action 56, therefore retains the red opener's credit
  category despite selecting different SCA/GMB/GAB resources.

The mappings do not establish damage equivalence or all target categories.

## GAB events are not arbitrary damage/meter fields

At `0x02002FE0` the engine advances through six-byte `<HHH>` records, dispatching
the second/third words when the first is reached by the supplied action clock.
Dispatcher `0x0208418C` maps the event type to the actor's event vtable.

For the Spidey actor:

- Event 8 calls third vtable `+0x18`, thunk `0x0204C0C8`, then
  `0x02075370`, which sets actor byte `+0x28` to 1. Several state transitions
  test this byte. It is an action marker, not a direct meter increment.
- Event 9 calls third vtable `+0x1C`, thunk `0x0204C0B8`, then
  `0x0207537C`, which writes the low-byte parameter to actor `+0x28`.
- Event 7 calls third vtable `+0x14`, thunk `0x0204C0D8`, then
  `0x02075308`, which resets the motion contact collection and sets motion flag
  `0x20`. Precise gameplay reset effects need isolated tests.
- Event 1's parameter semantics remain unassigned. `(time,1,5)` is not a proven
  damage amount. Do not create a meter fix by rewriting this value.

Original opener GAB11 contains `(2,1,5),(9,8,0)`; borrowed GAB15 contains
`(2,1,5),(7,1,5)`. Missing event 8 by itself does not remove meter credit.

## Decoded GMB structure

`tools/gmb.py` implements only confirmed boundaries, retaining unknown bytes.
Compression is handled separately by the established compression wrapper.

| Header offset | Field |
|---:|---|
| `0x00` | u16 unknown; commonly 30/24, not proven speed |
| `0x02` | u16 per-channel record count, correlated with action duration |
| `0x04` | u16 channel count |
| `0x06` | u16 unknown, retained |
| `0x08` | First channel header |

Each channel starts with `<hH>`: signed kind plus unknown u16. It is followed
by exactly `record_count` fixed-stride records. There is no inferred padding.
Static kind/stride switch at `0x0202A4FC`:

| Kind | Record stride | Clean survey |
|---:|---:|---:|
| 0 | 28 | 228 channels |
| 2 | 44 | 88 |
| 3 | 32 | 1,777 |
| 4 | 48 | 76 |
| 5 | 36 | 108 |
| 6 | 44 | Absent, supported by switch |
| 12 | 32 | Absent, supported by switch |

All **769** decoded GMBs end exactly at the declared final channel boundary.
All 126 player GMBs have three kind-3 arrays and one kind-0 array, giving size
`24 + 124 * record_count`. A parser/repacker no-op round-trip and bounded
single-word edit tests verify these boundaries and preservation. Unrecognized
kinds, truncation, impossible counts and trailing bytes are rejected.

`0x0202A6C4` selects channels by comparing the last record word to
`requested_index << 12`. Player callers select indices 0,1,2. Word meanings
within records still require targeted tests before friendly labels/editors.

Original GMB11: count 22, kind-3 channel offsets `0x8,0x2CC,0x590`, kind-0
offset `0x854`; decoded end 2,752. Borrowed GMB15: count 12, corresponding
offsets `0x8,0x18C,0x310,0x494`; end 1,512.

Within channel 2, record word 5 (offset `+20`) equals 1 at indices 4/5 in GMB11,
and 4/5/9/10 in GMB15. The Snap replay's meter contacts match those two windows.
First five words are `(0,22810,23623,42489,13032)` for GMB11 and
`(0,18506,17122,34369,12338)` for GMB15. Geometry/position interpretation is
plausible but not a completed collision schema. No global edit to GMB15 should
be published: it is shared with a purchased move as well as Snap Sweep.

Private scratch survey: `work/combo-engine/gmb-layout-survey.json`; decoded
channel comparisons: `gmb11-channels.json` / `gmb15-channels.json` in that folder.
No private assets are committed or distributed.
