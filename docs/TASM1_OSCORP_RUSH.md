# Oscorp Rush and training refill

This page records the Rush route, purchase behavior and training refill. Its
original bounded animation edits were superseded by the current three-clip
redesign; see [OSCORP_RUSH_ANIMATION.md](OSCORP_RUSH_ANIMATION.md) for current
choreography, isolated resources, hashes and qualification.

2026-10-04. Implemented and agent-tested; player acceptance remains open.
Current profile: `tasm-oscorp-rush-authored`. Use the stable launcher and Continue.

## Released behavior

**Oscorp Rush replaces Spider Dance at 400 XP.** Press Y, let Snap Sweep end,
then Y, Y, Y for the authored jab-cross-hook, knee/kick and overhand-cross
sequence. Mashing through the opener selects the ordinary ground string. The
purchased pause branch, contact timing, damage, combo credit and duration remain
native. Small forward movement keeps the original ground-pressure role.

Event325 / ownership bit16, availability and the 400-XP native price are unchanged.
Existing Spider Dance ownership carries over; a locked/refunded slot cannot enter
the paid branch. Scissor-Kick Special still needs its own bit17 purchase and the
parent skill. Its prerequisite text now says Oscorp Rush; Rebound Barrage remains
the next approved implementation, not part of this release.

**Training QoL:** hold SELECT and Down to refill the native training target's HP
without leaving Test Upgrades. It preserves position, current reaction, XP and
combo meter. Native refill after defeat remains. The training help panel explains
the chord and the existing Pause -> Return to Save Point route. This is an HP
refill, not a full encounter reset or a new retry menu.

All prior suit, Rebound, matched-rise Vault, passing/turning Sling, compact health
bars, mission marker and instruction overlays are composed into the release.
No research purchase or HP fixture is written into the player's battery save.

## Asset isolation and engine findings

The native pause branch is logical actions61 ->60 ->62, table branches15 ->16 ->17.
Free Snap action56 and paid action60 share GroundAttack15; its SCA/GMB/GAB payloads
and `spd.xbd` stay unchanged relative to the accepted prior release. Purchased
actions61/62 use GroundAttack16/17. See FORMAT_NOTES.md for native gate addresses.

| Asset | Bounded edit | Preserved behavior |
|---|---|---|
| `spd_GroundAttack16.gmb` | Horizontal root channel0 word2: smoothstep from0 to6 Q12 units by sample20; hold through the 39-sample clip | All other channels, contact windows, sample count and unknown decoded bytes |
| `spd_GroundAttack17.gmb` | Root advances2 Q12 units by sample8; hold through20 samples | Same contact/duration/unknown-byte contract |
| `spd_GroundAttack17.sca` | Chest joint3 local-X rotation at samples10..16: -4,-8,-11,-10,-7,-4,-2 degrees | First10 samples, active contact samples6/7 and every other joint/track |
| English/American strings | Slots192/193/194 name/input,197 prerequisite,417 training help | All other accepted text, slot boundaries, tree and unedited bytes |

Root displacement is authored local motion; it is not a promise of that exact
world distance. Native collision and movement composition still apply. In the
right-facing fixture the player moved from135 to139.65 units after the string,
versus136.13 for the prior native string. The mirrored fixture moved148.74 to142.37.
Walls/ceilings were not qualified by these floor fixtures.

The refill code replaces only the accepted observer's own0x180-byte block at
ARM9 source offset0x145EA0 / runtime0x02151920. It retains the common-health vtable
ABI/HUD guards and native continuation. Actor+0x88 bit4 is the guard used by the
native training auto-refill path. The chord checks active-low KEYINPUT bits0x84
and writes positive native max HP(+0x48) to HP(+0x44), then runs the existing
cheap observer. No extra hook, persistent storage or heap reservation is added.
Own code size0x3600 and heap reservation0x4000 remain unchanged.

## Paired agent checks

The pinned melonDS DS1.1.5 harness starts fresh with copied battery bytes. Native
menu inputs buy/refund the slot; fixtures raise XP/HP in disposable core RAM to
avoid a depleted dummy capping measured losses. The left fixture changes player
position on the same floor, then uses native Left input to turn. It is not an
ordinary AI or wall-contact test.

The paid portion produced three3072-Q12 losses on action61, two2048 losses on60,
and one4096 loss on62: **17408 Q12 actual HP loss** in the controlled common target.
The two preceding Snap contacts each lost3072. Contact frames and native combo
credit match the prior release exactly; mirrored losses/credit also match.
These are private actual-HP observations, not inferred attack strength or visible
damage numbers. Other enemy resistances/health paths may differ.

- Locked replay excludes actions60/61/62; ordinary Snap/string remains usable.
- Purchase changes only bit16 and subtracts400 from disposable2000 XP.
- Native save/reload retains bit16 and1600 XP; the paid route remains available.
- Native refund restores2000 XP, clears bit16 and excludes the paid route.
- SELECT+Down restores65536 fixture HP. Clearing native bit4 in RAM leaves41984
  HP unchanged under the same chord, checking the unflagged negative control.
- Final menu capture shows both instruction lines inside the native panel, 400-XP
  price and the player's genuine417-XP progress. Training help was visually checked.
- All102 tests pass, including bounded edit/revert, exact ARM9 confinement, text
  composition and all769 GMB compact-compression decode/re-encode checks.

## Reproduction and evidence

The earlier bounded-motion generator below is historical and intentionally
refuses the current authored profile. Regenerate current choreography with:

```powershell
python tools/oscorp_animation.py --out build/oscorp-dedicated
python mod.py verify --mods build/oscorp-dedicated/mods -o build/oscorp-dedicated/OscorpAuthored.nds --gameplay-profile build/oscorp-dedicated/gameplay_profile.json
```

The original candidate recipe was:

```powershell
python tools/tasm_oscorp_rush.py
python mod.py verify --mods build/oscorp-rush/mods -o build/oscorp-rush/OscorpRush.nds --gameplay-profile build/oscorp-rush/gameplay_profile.json
python -m unittest discover -s tests -v
```

The historical generator accepts only the old guarded combat-flow/Rush
composition and refuses the authored current profile. Existing generators for
historical moves must not overwrite the current default profile. Normal builds use pinned own-code
hex; optional Keystone reassembly is `tools/assemble_training_refill.py`.

Private runtime inputs: `reference/combat-inputs/oscorp-*.json` (no saves/assets).
Fixture details: `work/rush/probe.py`, `scripts.py`, `evidence.py`; assertions and
actual contact rows: `work/rush/evidence.json`. Full gameplay candidates and
refill/save tests: `build/boot-tests/OscorpRush-541f62af/`. That tested ROM was
`541f62af3cc5a5276283364048f3c4874f4e1a6009edd2ca56f7c9291e89cb7e`.
Only the final wrapping of slot194 changed afterward; authored assets/code remain
the same. Exact final ROM also passes owned contact replay against that candidate.
Final owned/refund/reload/menu evidence: `build/boot-tests/OscorpRush-ecb07b9a/`.

Published with `python tools/playtest.py build`; `python mod.py verify` confirms
all3,733 resources and exact isolated/published ROM equality. Latest real DSV
remains `a22cdc22490db27af413520d4a7aa09e7decdec3ab5d41636c575bc6bd19ce46`
(634-byte v0 wrapper/512 payload). Checkpoint `before-oscorp-rush` and the previous
67472ad1 ROM are retained. DeSmuME was closed during checkpoint/publication.

Final ROM SHA256 `ecb07b9a12b3d071f12deaab2d7643276dc52233ca934ee00ea28655415f6f6f`.
ARM9 SHA256 `acab7b96db674e5984de4fb034492f7a898be8641ae4da4bb8054dbad8d4313d`.
Own observer block SHA256 `40d275bfffe23d13b31435dbf7f18e4c343fd5796d1f58ec1e0a484febb353c9`.
Full asset hashes are in `reference/gameplay_profile.json` and private `rush.json`.

Player feel, ordinary/dense AI, specialized enemies/bosses, walls/ceilings,
interruption, and long play remain open. Earlier Sling/Vault/Rebound player checks
stay queued. No newly implemented ability is marked player-confirmed.
