# Full Oscorp Rush animation redesign

2026-10-05. Anime exaggeration revision published through
`python tools/playtest.py build`. The player confirmed the choreography was new,
rejected the initial dance-like sway, then rejected the compact refinement because
the limbs looked stubby. This revision uses much larger windups and screen-plane
extensions, a rising uppercut, a fully unfolded high kick and a lunging overhand.
Player acceptance of this revision and ordinary-encounter qualification remain open.

## Authored sequence

All three paid clips now have newly posed body choreography across their entire
native duration. The authoring starts with idle bone lengths and hand/foot
orientation; it does not apply a recovery delta to a stock attack sequence.

| Paid action | Samples | New choreography | Native contacts observed |
|---|---:|---|---|
| 61 | 39 | Loaded straight, high cross and rising uppercut; sharp extensions and brief impact holds | clocks5/12/18 |
| 60 | 12 | High knee, recoil, then fully extended high kick; return to guard | clocks4/9 |
| 62 | 20 | Oversized shoulder load into a lunging overhand; recover to native idle | clock6 |

The same Y -> let Snap Sweep finish -> Y,Y,Y branch,400 XP/event325/bit16,
dependencies, native speed tiers and ownership are retained. Punches now load
well behind the torso and snap into larger extensions in the camera-visible Y/Z
plane. The third entry contact rises from a low windup; the finish loads the right
arm high before driving down and forward. Existing ownership
carries over. No new contact, increased damage or free ability is introduced.
The prior accepted root advance, feedback, suit, other paid moves and training
refill remain composed. The upgrade instructions now read “Punches, high kick,
heavy finish.” Both lines fit the native panel in the revision's menu capture.

Scissor-Kick Special remains the600-XP/bit17 child, not a separately redesigned
Rebound Barrage. In a paired rapid-input/bit17 training fixture it repeats action60
four times, producing eight bridge contacts versus Rush's normal two. Its late
contacts cross a native meter tier and have correspondingly different actual HP
loss; both old and new builds agree. That is observed behavior for this fixture,
not a universal repeat cap. The repeated section now uses Rush's new knee/kick.
Rebound Barrage's distinct future mechanics/animation remain queued.

## Isolation and archive extension

The initial private trial reused GroundAttack11 because Snap had displaced its
player binding. A complete XBD scan found `m6.xbd` still binds G11,16 and17.
That trial was rejected for publication. The final build appends three dedicated
SCA resources instead:

| New index | Resource | Player XBD binding offset |
|---:|---|---:|
| 3733 | `zz_tasm_RushBridge.sca` | 404 |
| 3734 | `zz_tasm_RushEntry.sca` | 416 |
| 3735 | `zz_tasm_RushFinish.sca` | 428 |

All original3733 IDs and every existing filename record are retained exactly.
The name-table resource remains805; three64-byte records are appended to its
original bytes. Offset-table size grows by12 bytes; payload offsets are repacked.
Only three SCA indices in `spd.xbd` change. All GMB/GAB bindings, Snap's
356/360/364 triple and every other actor's bindings stay exact against the parent.
Every original animation payload also stays exact against the parent, including
the prior accepted bounded pose edits. New choreography cannot leak through the
original attack resources to another actor.

The loader at0x02007758 has a confirmed resource-count literal at ARM9 source
0x77F8 / runtime0x020077F8. It adds one for the EOF offset, resizes the offset
buffer and reads count+1 words. That literal changes3733 ->3736; the rest of the
accepted ARM9 is exact. Index-to-offset getter0x020079F0 and filename805/64-byte
lookup0x02007A04 continue to work. No old resource is renumbered.

The ordinary overlay workflow still rejects arbitrary new names and manual
GlobFiles edits. Only `tasm-oscorp-rush-authored` permits the three fixed names,
checks their37-joint/12,39,20-sample SCA layouts and requires pinned hashes.
Every build re-reads and verifies all3736 resources, including generated names.

## Authoring implementation

`tools/rush_choreography.py` poses the canonical37-bone rig with deterministic
forward kinematics, two-bone limb IK, smooth control curves and quaternion
blending. The stored SCA matrix transposes to column-vector FK: Y is up and Z
is forward for this player rig. Native leg endpoints and in-game grounded poses/
forward knee motion calibrate this convention. It is not a general model-axis
guarantee or an implemented Blender conversion.

The higher pelvis and wider stance stop the legs bunching under an upright torso.
Entry and finisher foot IK retains the ground height with small forward foot
adjustments. The bridge deliberately lifts the right knee, recoils, then unfolds
the leg. Shoulder rotation, torso lean and visual root drive are larger, while
the head counter-rotates to keep its gaze toward the opponent. Hands return to
guard between contacts; wrists now point along the forearm rather than retaining
the idle world's hand direction, which could point into screen depth.
The finisher's return-to-idle interpolation keeps the known post-blend IK fix:
post-blend IK corrects an ankle dip seen during initial development. The
finisher's sample19 rotations/translations exactly match native
Idle sample0. Native finger poses and all scale/inverse-scale values are retained.
For the anime impact, lower-arm/end translations temporarily lengthen the entry
arms by at most12%, finishing arm16%, and the kicking leg8%. They return to native
lengths outside their keyed gain windows; no permanent model or unknown scale
field is edited. This is original attack choreography on the existing rig.
Bone count, clip lengths, native contact/events and gameplay root channels stay
separate. Old unused SCA pools/unknown bytes are retained by the sampled repacker.

In the chosen straight-root basis, local X maps to world Y (up), local Y to
world Z (forward), and local Z to world X (right). The revision twists BackA
around local X. Using local Y tipped the chest sideways; local Z now supplies
small chest/neck counter-pitch so the head stays upright during forward strikes.
This describes the explicit authoring basis, not an assumed axis for every model.

Quantized, re-read FK confirms the previous kick sample9 had only0.353 hip-to-ankle
reach relative to its two-bone chain; the new kick reaches0.990 and its ankle rises
from Y2.26/Z1.13 to Y4.80/Z5.79. Entry contact wrists move from forward Z2.38/2.51
to3.76/4.02; the uppercut wrist reaches Y8.41 rather than6.10. This is pose-space
evidence, not collision reach or measured screen pixels.

New SCA sizes: bridge12376 bytes/stride956; entry53848/1364; finish31768/1560.
Only these three clips grow. Extra cache/static metadata and heap high-water
headroom are not measured; unused-track compaction remains future work. This
release makes no FPS claim.

## Reproduction and qualification

```powershell
python tools/oscorp_animation.py --out build/oscorp-anime
python mod.py verify --mods build/oscorp-anime/mods -o build/oscorp-anime/OscorpAuthored.nds --gameplay-profile build/oscorp-anime/gameplay_profile.json
python -m unittest discover -s tests -p test_rush_choreography.py -v
```

The generator accepts the exact old Rush parent or the three pinned authored compositions
and is deterministic. Historical move generators must not overwrite this profile.
Research uses copied battery bytes and disposable emulator RAM, never a stale
save state. Scissor's bit17 fixture is confined to research RAM.

The original full-animation release qualified paired controlled floor replays in
both facing directions: the same six
paid HP contacts/credit, native sample clocks and relative timing, final position
and return to idle. Locked/refunded cases exclude the paid route. Native purchase
subtracts400 and changes only bit16; native save/reload retains ownership.
Its then-current real progress also booted through Continue in a read-only
battery replay. That historical evidence is kept under the old hash below.

The expanded archive shifts all contacts, including unchanged Snap, two emulator
frames earlier than the old replay. A count-only control retains the original
player bindings and text while adding the same unused resources/count literal;
it has exactly the same contact frames as the final build. Thus this phase shift
is present without the authored choreography. Relative timing and all native
contact clocks/loss/credit remain equal. This is not a measured FPS/speed change.
Control: `build/oscorp-count-control/CountControl.nds` and
`build/boot-tests/CountControl-409c6d41/count-only-owned/`.

Current ROM SHA256 `4d36970e7e06fae190ad27971ba6f85a5cfa74f0cad664f36c61c74455e0f65e`.
ARM9 SHA256 `72ab438e0998ec2b021bd79a4f36adf5e88a456ccbe51afff100c81461390b12`.
The stable `build/Spider-Man-WoS-modded.nds` is byte-identical to the qualified
candidate and a fresh regeneration from the published composition. The revision
source passes all8 choreography tests, including two new checks on re-read baked
screen-plane reach/unfolding and bounded translation stretch. The prior revision
passed125 source tests; the full suite was not rerun for this pose revision.
Build validation verifies all3736 resources.
Relative to the prior compact f0382e98 ROM, only three dedicated SCAs and the two
localized instruction resources change. IDs, all actor bindings, original SCAs,
GMB/GAB event and root data, and the entire ARM9 are exact. In fresh copied-battery
floor replays, both facing directions retain all eight contacts including Snap,
HP losses, native credit, exact contact frames and final position against that
prior release. Dense actual-game captures every two emulator frames were reviewed
as enlarged contact sheets in both directions, alongside matching parent frames.
The kick extension is visibly distinct from the previous folded leg. Quality acceptance still
belongs to the player. No broader encounter acceptance is claimed.

Latest real battery `5a03c116b31de0f35e57a81f8fa77cbbf0615850fb665391c52943b1079e237e`
is preserved exactly:634-byte DSVv0/512 payload. Content-addressed
`before-rush-anime-dsv-<sha>` and `before-build-dsv-<sha>` checkpoints preserve it.
The prior f0382e98 ROM remains under `build/releases/<old-sha>/`, with its active
recipe/overlays in `anime-parent/`. Earlier checkpoints/releases remain.
DeSmuME was closed
for publication. No fixture or old save was restored to the player's battery.
Current proof: `work/animation-research/anime-evidence.json`,
`anime-tests.log`, `check-anime.py`, `anime-publication.log`;
replays `build/boot-tests/OscorpAuthored-4d36970e/{anime-right,anime-left}/`, with
`entry-review.png`, `bridge-review.png`, `finish-review.png`, `before-after.png`
and `left-review.png`. Candidate `build/oscorp-anime/`, regenerated from published
overlays in `build/oscorp-anime-regenerated/`; authored poses and hashes are in
`build/oscorp-anime/choreography.json`. Historical compact proof remains in
`visual-refinement-evidence.json` and `build/boot-tests/OscorpAuthored-f0382e98/`.
Initial dedicated-resource proof:
`work/animation-research/dedicated-evidence.json`,
`check-dedicated.py`, `qualify-dedicated.py`,
`build/boot-tests/OscorpAuthored-8bc72be4/`; poses and hashes:
`build/oscorp-dedicated/choreography.json`.

Ordinary AI, walls/ceilings, specialized enemies/bosses, interruption, long play
and player feel remain open. Training contact parity is not coverage of those
encounters. Blender import/export and coordinated variable-duration authoring
remain separate work. This is a full authored three-clip animation on the existing
paid branch, not a new purchased action slot or a new gameplay repeat mechanic.
