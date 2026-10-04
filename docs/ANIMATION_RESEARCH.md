# CS5E SCA joint animation: confirmed layout and bounded custom poses

2026-10-04. **Custom skeletal poses are now feasible.** The original SCA loader
and evaluator establish its section layout and channel encodings. A lossless
standard-library parser reconstructs all **869 original files**, including all
**126 player clips**, byte for byte. A bounded editor can change one independent
dynamic rotation key while preserving timing, other tracks and unknown bytes.

The format investigation itself used read-only originals. The first accepted
authored recovery pose now ships in Rebound; TASM1_REBOUND.md records its separate
contact, collision, purchase and save checks. Animation structure alone does not
establish those behaviors; they also belong to the logical action/controller.

## Evidence and original code paths

All runtime addresses below apply only to original CS5E ARM9 SHA256
`e541bfcd02441db86b43b8649aaa13570be301d302ddfb198804b78528d215dc`.

| Address | Confirmed role / observation |
|---|---|
| `0x02128530` | RTTI name for `gfx3d::JointAnimation`; associated vtable `0x02128570` |
| `0x02013884` → `0x0201CB9C` | Joint-animation resource load path |
| `0x0201C958` | Seeks to resource zero and reads exactly **28 header bytes** |
| `0x0201C9A4` | Computes `align4(3 * joint_count)` |
| `0x0201C9F0` | Reads descriptor region plus aligned static pool after header |
| `0x0201CAA0` | Reads a frame block from `frame_start + frame * stride` |
| `0x0201CD5C` | Caches current/next frame blocks; next index wraps to zero after the last frame |
| `0x0213D8E8` | Joint-animation handler registration (`J`, subtype `SC`), initializer `0x0201D19C` |
| `0x0201D19C` | Installs the custom evaluator at `0x01FF8BC0` |
| `0x01FF8BC0` | Evaluates a joint's translation, rotation and scale from three descriptor bytes, interpolating current/next samples |

The evaluator lives in ITCM. The source mapping is confirmed by original startup
copy code at `0x020009FC` and module parameters at `0x02000B64`. The autoload table
at `0x021439A0` has `(target=0x01FF8000, copy=0x5740, zero=0x40)` followed by the
DTCM entry. Copied source begins at `0x0213E140`; therefore `0x01FF8BC0` corresponds
to **ARM9 file offset `0x13ED00`**. Do not subtract the ordinary `0x02000000` load
base when inspecting ITCM instructions.

Independent private survey: `work/animation-research/survey_sca.py` / `survey.json`.
Private disassembler maps the verified autoload range. Optional Capstone 5.0.9
was used only for research; `tools/sca.py` and its tests have no external dependency.

## SCA4 header

All integers below are little-endian. `align4(x) = (x + 3) & ~3`.

| File offset | Stored type | Established meaning |
|---:|---|---|
| `0x00` | 4 bytes | ASCII `4ACS`, representing the SCA4 tag |
| `0x04` | u32 | Frame/sample count; loader stores it in a u16 runtime field |
| `0x08` | u32 | Joint/object-matrix count; loader stores it in a u16 runtime field |
| `0x0C` | u32 | **Static-pool payload byte length**, before alignment |
| `0x10` | u32 | **Per-frame block stride**, including alignment |
| `0x14` | u8 | Number of static translation vectors |
| `0x15` | u8 | Number of static scale-and-inverse-scale entries |
| `0x16` | u8 | Number of static rotation matrices |
| `0x17` | u8 | Number of dynamic translation vectors per frame |
| `0x18` | u8 | Number of dynamic scale-and-inverse-scale entries per frame |
| `0x19` | u8 | Number of dynamic rotation matrices per frame |
| `0x1A–0x1B` | 2 bytes | **Unknown**, zero in every original file; preserved |

Earlier surveys treated `0x0C` and `0x10` as possible offsets and found exceptions.
That interpretation is rejected: they are pool size and frame stride. The loader
and the complete corpus agree on the formulas below.

```text
descriptors_start = 28
descriptors_bytes = 3 * joint_count
static_start      = 28 + align4(descriptors_bytes)
static_bytes      = 12*static_T + 24*static_S + 18*static_R
frames_start      = static_start + align4(static_bytes)
frame_stride      = align4(12*dynamic_T + 24*dynamic_S + 18*dynamic_R)
file_size         = frames_start + frame_count * frame_stride
```

**869/869** satisfy every formula and exact file-size accounting. Counts span
1–460 frames and 1–89 joints. All player clips have **37 joints**. A zero stride
is valid: some clips hold constant poses for several logical frames.

## Joint descriptors and channel pools

There are three bytes per joint, in **T / R / S** order. For each byte:

```text
pool_index = descriptor >> 1
is_static  = (descriptor & 1) != 0
```

A static descriptor selects the static pool. A dynamic descriptor selects the
same indexed entry from each frame block. Descriptor indices are bounded by the
appropriate header count in **869/869** files. Different joints can deliberately
share an entry, and a static entry spans the entire clip. Editing an aliased or
constant entry without changing its descriptors affects every consumer.

Both the static pool and each dynamic frame block store these arrays in **T / S /
R** order, which differs from the descriptor order:

| Channel | Entry bytes | Encoding / evaluator behavior |
|---|---:|---|
| Translation | 12 | Three signed 32-bit Q12 values, XYZ |
| Scale | 24 | Six signed 32-bit Q12 values: XYZ scale, followed by XYZ inverse scale |
| Rotation | 18 | Nine signed 16-bit Q12 matrix coefficients in stored 3×3 order |

Q12 uses **4096 as 1.0**. Static identity entries include zero translation, six
4096 scale/inverse-scale values and rotation diagonal 4096 with off-diagonal zero.
The evaluator checks those identity values, sign-extends rotation coefficients,
and feeds them to the rendering result. Rotation is a **matrix**, not Euler angles
or a quaternion. Translation/scale interpolation uses Q12 fractions; rotation
interpolates the nine matrix components. When an interpolated scale changes, the
evaluator recomputes inverse scale rather than blindly interpolating its stored
inverse. Matrix storage orientation, local-axis sign and model-facing conventions
must still be visually calibrated for authored deltas.

Unknown/alignment bytes remain unchanged. The bounded editor does not deduplicate
tracks, introduce channels, change frame count, enlarge pools or re-time the clip.
Those are possible future repacker features, not part of this confirmed edit API.

## Player rig and Rebound target

The clean `spd.nsbmd` has 37 object matrices, matching the player SCA descriptors.
Its model dictionary retains useful names. The 34 skinned joints in the existing
COLLADA export omit some helpers, so use the **original 37-entry model dictionary**
for animation indices; do not use the export's compact joint ordinal.

The original model reader context agrees with apicula's direct model parser:
objects carry the rest TRS matrices and animation changes those matrices.
[Primary apicula model reader](https://github.com/scurest/apicula/blob/master/src/nitro/model.rs)
supports the NSBMD interpretation; the custom SCA layout above comes from the
game's own loader/evaluator. Standard NSBCA uses a different sampled-curve format,
as shown by [apicula's NSBCA reader](https://github.com/scurest/apicula/blob/master/src/nitro/animation.rs);
do not rename SCA to NSBCA or feed it to that decoder.

Target **`spd_GrapplePullAttackKick.sca`**:

- Size **6,980 bytes**, 9 samples, 37 joints.
- Counts `(static T/S/R, dynamic T/S/R) = (31/1/6, 5/5/29)`.
- Static pool starts **140**, frame blocks start **644**, stride **704**.
- Companion `spd_GrapplePullAttack.sca` is a distinct 10-sample, 8,020-byte clip:
  counts `(27/1/5, 9/4/30)`, static pool 438 bytes rounded to 440, stride 744.
  Keep the pull/setup phase and the kick phase distinct.

| Joint index / model name | Kick clip rotation track | Aliases | Matrix offset for sample `f` |
|---|---|---|---|
| 0 `spd:ScaleGroup` | Static 0 | Joints 0 and 34 | Constant/shared; editor rejects it |
| 1 `spd:Root_M` | Dynamic 0 | None | `824 + 704*f` |
| 2 `spd:BackA_M` | Dynamic 1 | None | `842 + 704*f` |
| 3 `spd:Chest_M` | Dynamic 2 | None | `860 + 704*f` |
| 7 `spd:Shoulder_L` | Dynamic 6 | None | `932 + 704*f` |
| 8 `spd:Elbow_L` | Dynamic 7 | None | `950 + 704*f` |
| 17 `spd:Shoulder_R` | Dynamic 14 | None | `1076 + 704*f` |
| 18 `spd:Elbow_R` | Dynamic 15 | None | `1094 + 704*f` |
| 26 `spd:Hip_L` | Dynamic 21 | None | `1202 + 704*f` |
| 27 `spd:Knee_L` | Dynamic 22 | None | `1220 + 704*f` |
| 30 `spd:Hip_R` | Dynamic 25 | None | `1274 + 704*f` |
| 31 `spd:Knee_R` | Dynamic 26 | None | `1292 + 704*f` |

Track identities apply to this clip only; resolve descriptors again for another
clip. Indices/names come from the clean original model dictionary, and aliases
from the parsed clip. None of the rows with independent dynamic rotations share
their matrix with another joint in this target.

## Recommended first custom pose

Give Rebound a readable **kick → recoil → balanced landing** silhouette by making
small changes to Root_M or Chest_M and the shoulders in zero-based samples **5–8**.
Begin with Chest_M alone and a modest Q12 matrix delta; then add restrained arm
counterbalance if the visual evidence supports it. Preserve samples 0–4, frame
count, descriptors, translation/scale channels, GMB, GAB and action timing. Use a
smooth amplitude envelope instead of inserting a sudden pose at sample 5.

This is an authored pose proposal. The exact positive/negative local axis that
leans the torso backward must be calibrated with before/after game captures.
Do not claim the model lean itself causes gameplay recoil: **visual root motion
does not establish collision-resolved actor displacement**. Keep the code-level
player recoil and enemy reaction as separate measured behaviors. Likewise, keeping
GMB/GAB unchanged is necessary but does not prove hitboxes are unaffected if their
world positions follow joints; make the first pose change after verified contact
and re-check damage, meter credit and enemy separation.

`tools/sca.py` exposes `Sca.track`, `rotation`, `rotation_offset`,
`replace_rotation` and `rotate_joint`. Replacements reject static tracks and any
dynamic track shared by another joint. `rotate_joint` composes a small Q12 axis
rotation on the specified left/right side; orientation is explicit rather than
being guessed as a world-space recoil direction. Zero-angle composition on an
independent track preserves exact bytes. There is no animation CLI that writes a
ROM or regular overlay automatically.

## Validation and acceptance

Six tests in `tests/test_sca.py` passed on 2026-10-04:

1. Every one of 869 original resources parses and reconstructs byte-identically;
   all 126 player clips retain 37 joints.
2. Synthetic unknown header and nonzero alignment bytes survive reconstruction.
3. One dynamic matrix edit is confined to its exact 18-byte key; other frames and
   channels remain identical and edited output reparses/reconstructs identically.
4. Static and shared rotation edits are rejected.
5. Malformed sizes, strides, descriptors, frame/joint indices and int16 values
   are rejected.
6. Q12 rotation/inverse composition stays within one quantization unit of identity;
   a zero-angle edit is byte-identical.

Agent verification command:

```powershell
python -m unittest tests.test_sca -v
```

Before a candidate is accepted, report changed joints/samples/matrix offsets and
hashes. Check no other SCA bytes, GMB/GAB data or action routes changed; retain
each paid route's existing gate. Boot the isolated candidate, compare impact and
post-contact poses, confirm no foot/hand/room clipping or unnatural scale change,
and measure same-enemy hit count, damage, recovery, displacement and combo meter.
Verify locked/purchased cases, alternate form, base Snap Sweep, and pause/return to
idle. Publish only after those gameplay checks through the established save-safe
release workflow.

The accepted Rebound recovery now uses Chest_M local-X rotations of -5, -11,
-16 and -12 degrees at samples 5–8. Bounded captures verify the post-contact pose;
GMB root deltas independently produce persistent, collision-resolved player recoil.
See TASM1_REBOUND.md for hashes, contact/credit comparisons and remaining playtest limits.

Remaining research: rig parent relationships/handedness in a reusable authoring
tool, general root-motion/physics interactions, scale compensation conventions, clip blending
and last-frame transition, adding new dynamic tracks, optimal data deduplication,
and full Blender/NSBCA-to-SCA authoring. A complete new clip pipeline is beyond
the tested fixed-size matrix editor; it is now an engineering task with a concrete
format foundation rather than an opaque-file experiment.
