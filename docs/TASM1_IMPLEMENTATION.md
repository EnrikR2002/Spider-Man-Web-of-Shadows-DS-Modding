# TASM 1 stage one: Snap Sweep

2026-10-04. One red-form opening action is replaced by an existing compact low
kick, retaining the native combo controller. No new slot, inputs, combo tree,
damage constants, unlock flags or save fields are introduced.

User follow-up: Snap Sweep was playtested and confirmed working. It is explicitly
allowed to remain free. Future purchased skill replacements await the approval
plan in `TASM1_UPGRADE_PLAN.md`; no additional moves are implemented by that audit.

## Exact edit

`tools/tasm_suit.py` starts from the validated original and merges accepted mods.
In the 2,024-byte `spd.xbd`, three u16 archive IDs change:

| Offset | Type | Before | After |
|---|---|---|---|
| 0x164 | SCA | 3371 / spd_GroundAttack11.sca | 3383 / spd_GroundAttack15.sca |
| 0x168 | GMB | 3370 / spd_GroundAttack11.gmb | 3382 / spd_GroundAttack15.gmb |
| 0x16C | GAB | 3369 / spd_GroundAttack11.gab | 3381 / spd_GroundAttack15.gab |

Only bytes 0x164, 0x168, 0x16C actually differ (IDs retain their high bytes).
Every other binding, opaque field, tail and footer is identical. No resource is
added/recompressed. Clean XBD SHA256:
`9626adf3151f91093b542757ad5756a3e837eb77105315eb66994b07f63f4975`.
Edited: `22bd8c3771aa9e09f66d1869f260fc4e49e394c7ff1a33877d0b92190d7c0d4d`.
Seven-asset combined ROM:
`3c7ec9a5342a80bc20d6b9d058b2b8bfa029ee670d9d42b50a0642122fa9907c`.

## Runtime evidence

Pinned melonDS DS 1.1.5, software renderer, built-in BIOS/direct boot. An isolated
copy of the current DSV's 512-byte payload loads before frame zero. The original
634-byte file is untouched (SHA256
`548d4d8e6d7044b2299067de92c3d48c66896cd872abcb7f370b88d024938484`).
Both ROMs resume in the early Residential save room. Y starts the test at 1700.

| Observation | Baseline | TASM candidate |
|---|---|---|
| First action at 1700 | Action candidate 56 / GMB 3370 | Same action 56 / GMB 3382 |
| First return to idle | Frame 1744 / GMB 3461 / action 99 | Frame 1724 / GMB 3461 / action 99 |
| Observed duration | 44 emulator frames | 24 emulator frames |
| Repeated Y | Native route reference | 56 -> 57 -> 58 -> 59 -> idle; GMB 3382 -> 3373 -> 3376 -> 3379 |
| L switch, then Y | Alternate form's GroundAttack1 | White form visible; original GMB 3367 / action 55 retained |

Images show the low kick replacing the higher opener. Clock candidate at
motion+0x178 increments every two emulator frames during these attacks. The
builder re-reads and verifies every one of 3,733 resources. Player telemetry
checks the known ARM9 hash and bounds all RAM pointers; it never writes RAM.

Private evidence in `build/boot-tests/`:

- `Spider-Man-WoS-modded-02e39959/precise-original/player-trace.json`
- `TASM1-stage1-3c7ec9a5/precise-tasm/player-trace.json`
- `rebound-3c7ec9a5/jab-rebound/`, `combo-chain/`, `alternate-form/`.
- Edit report: `build/tasm1-stage1/tasm1.json`.

No hostile combat target was verified in these runs. Damage, contact count, range,
boss behavior, interruption, room transitions and long-play stability remain
unmeasured. Two similar GAB records do not prove two damage hits.

## Reproduce privately

Agent commands, after saving in-game and closing DeSmuME:

```powershell
python tools/tasm_suit.py
python -m unittest tests.test_tasm_suit tests.test_player_trace -v
python tools/emulator_smoke.py build/tasm1-stage1/TASM1-stage1.nds --save 'FULL_PATH_TO_STABLE_DSV' --script reference/combat-inputs/single-opener.json --label precise-tasm --frames 1760 --capture 1723,1724,1759 --player-trace 1699:1755
```

`reference/combat-inputs/` also holds combo-chain and alternate-form scripts.
They replay the early room, not arbitrary progress. Saves/assets remain ignored.
After checks, publish accepted overlays through `playtest.py build`.

## Rejected experiment

Changing decoded GroundAttack11.gmb u16 at 0 from 30 to 36 and re-encoding it
produced unchanged poses/clocks/duration in paired captures. It is absent from
the release. This word remains unknown and is not an established attack-speed
control. Next: enemy contact/cancel tests, then one custom Web Rebound transition.
