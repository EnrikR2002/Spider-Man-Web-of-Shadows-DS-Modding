# Rebound: first purchased TASM replacement (historical move evidence)

2026-10-04. Replaces **Web Kick**, costs the native **100 XP**, and retains native
ownership bit 13/event 322. Snap Sweep remains the free opener; the other six
approved replacements are pending and keep their original behavior and names.

## Player behavior

Grapple an enemy with DS A, then press Y while grappled. The paid pull brings a
distant target in, kicks it, and adds a short backward step with an authored chest
recovery pose. The original candidate's enemy horizontal impulse is approximately
halved. The published revision makes the launch closer and higher for a possible
juggle; current values and player checks are in `COMBAT_FEEDBACK.md`.
In that historical candidate, damage calculation, hit count, purchase price,
recovery timing, meter category, invulnerability and boss resistance were retained.
The published revision changes only the enemy trajectory. The recoil is
ordinary collision-resolved movement; no dodge immunity or extra attack is added.

The original contextual rules still apply. A grappled target already very close
can select a normal attack rather than the paid pull/kick. A missed grapple does
not award meter or invoke Rebound. Keyboard defaults here are W for A and Q for Y.
The save-point X prompt uses T; buy Rebound through **Buy Upgrades -> Red**.

## Deterministic recipe

`tools/tasm_rebound.py` composes the existing accepted cosmetics/QoL/Snap Sweep
with two original-resource edits and three localized text slots:

- `spd_GrapplePullAttackKick.gmb`: first channel's horizontal root coordinate at
  samples0..8 becomes `(0,0,0,0,0,-4096,-10240,-16384,-20480)` in Q12. All other
  words, channels, hit geometry, active windows and duration remain exact.
- `spd_GrapplePullAttackKick.sca`: Chest joint3 receives local-X rotations
  -5,-11,-16,-12 degrees at samples5,6,7,8. Only four independent 18-byte matrices
  change. Samples0..4, all other tracks, scale, timing and aliases remain exact.
- American/English slots183/184/185 become the Rebound name/list/instruction. All
  other existing QoL text is retained. In-game wrapping is visually verified.

The native `0x020B2498` attack-kind selector maps animation action50 to kind32
through `0x020B2868`. Its response tables have 36-byte records. The impulse
calculator at `0x0207A5F4` reads signed +0x18 horizontal and +0x1C vertical values;
damage has a separate path. `tools/combat_profile.py` changes only kind32's
horizontal values at ARM9 offsets **0x11A2B8/0x11AA98**, -9011 -> -4506.
The zero/immune third response table is untouched. No executable instruction,
purchase check, other attack record or vertical impulse changes. The changed
ARM9 is accepted by probes only under its exact known SHA256.

An earlier proposed state42 movement-predicate patch was rejected: the normal
physics path already applies the GMB root delta. Native-engine and GMB-only
controls both confirm persistent recoil. That unnecessary instruction patch is
archived privately and does not ship.

Generate an isolated complete candidate with:

```powershell
python tools/tasm_rebound.py --out build/tasm1-rebound
```

The generated gameplay recipe pins the five required overlay hashes. The
regular build reads `reference/gameplay_profile.json` and fails if an expected
asset drifts or is missing. Use `--gameplay-profile original` for an explicit
engine-data control. Publish with `python tools/playtest.py build`, preserving
the stable ROM name and live progress.

## Runtime evidence

The native Save Point **Test Upgrades** arena provides an enemy without granting
unowned skills. Every purchase/replay uses a private copy, never the real battery.

| Check | Observed result |
|---|---|
| Unowned input | Bit13 false; normal action56/GMB3382, no paid49/50 chain or recoil |
| Actual purchase | Native UI138 ->38 XP; only bit13 set; other six Red purchases stay false |
| Paid route | Action49/GMB3353 at3192 -> action50/GMB3356 at3206 -> idle at3234 |
| Damage/contact budget | Native action timeline, hit geometry, active windows and complete meter trace match; damage handler/multiplier/data are unchanged |
| Player movement | Native X120 stays120; Rebound X120 becomes115 and stays115 in idle |
| Left-facing recoil | Facing 0, action49 at3342 ->50 at3356 ->idle at3384; X162.901 ->167.901, the same backward five-unit step |
| Enemy reaction at3208 | Native velocity `(9011,6554)` becomes `(4506,6554)`; position at contact is identical |
| Meter | Both paid versions reach gauge180235 Q12 at3208; the entire measured meter trace matches |
| Save/reload carryover | Buy and save in the original build; reload battery copy in the candidate: bit13 true,38 XP, paid49/50 route works |
| Refund |38 ->138 XP, bit13 cleared, paid route relocked |
| Alternate suit | Native action55/GMB3367 retained; returns to idle normally |

Exact raw enemy HP loss is not independently decoded by this pass. Damage
equivalence is established through preserved damage selection/data and unchanged
contact windows/credits, rather than an invented HP reading. Arena checks do not
establish every boss, ceiling, wall, interruption or long-play case. Broader
player testing remains useful; the vulnerable recoil is deliberately small.

Private evidence lives in `build/boot-tests/Rebound-be5fedb6/` under
`rebound-owned`, `rebound-locked`, `rebound-existing-purchase`,
`rebound-reloaded-hit`, `rebound-refund`, `rebound-alternate` and
`rebound-left-close`. Native comparison:
`build/boot-tests/Spider-Man-WoS-modded-3c7ec9a5/native-webkick-position/`.
Public replay inputs contain only button/frame schedules, with no asset or save.

Candidate/stable ROM SHA256:
`be5fedb66f760dbd0c7e3b7813bf3aba10b326a6514de881b5c542361674d9bf`.
Combat-data ARM9 SHA256:
`3298417ae06c47571ea559ebe3e18d33da4ed6f3bfcdcb85025628c440438837`.
The full suite passed **76 tests in 87.396 seconds** before publication.
Every rebuild rereads all 3,733 resources; nine assets differ from the original.
Real progress is backed up immediately before publication and left byte-identical.

Published through `tools/playtest.py build` at the stable daily filename. The
closed-emulator live DSV SHA256 was
`5130df3f7405b5939faa307cdf71087b8aff8f700a7714f1f404de8e8eab6719` before
and after publication and the read-only 1,800-frame release resume. Named
checkpoint `before-rebound` retains it; the previous stage-one ROM is preserved
under `build/releases/3c7ec9a5.../`. The release capture resumes the existing
Residential save point. These are private evidence, not game data committed to Git.
