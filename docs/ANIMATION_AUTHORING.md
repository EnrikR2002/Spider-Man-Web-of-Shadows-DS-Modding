# Authoring distinct Spider-Man animations

The initial compiler/recovery investigation below is historical. A full authored
three-clip Rush sequence is now published through a procedural FK/IK workflow;
see [OSCORP_RUSH_ANIMATION.md](OSCORP_RUSH_ANIMATION.md). Blender conversion remains
unimplemented. Dedicated appended SCAs isolate the new choreography from Snap
and other actors without replacing original animation payloads.

2026-10-04. User direction: future attacks should gain distinct authored
choreography; reusing stock clips with new names/movement is not the long-term
animation goal. This investigation adds a working sampled-animation compiler
and an isolated runtime proof. It does **not** replace the released Rush build
or claim a finished full attack or a Blender round trip.

## What was in the game at the initial investigation

Released Oscorp Rush uses native GroundAttack16/15/17 clips. GroundAttack16/17
gain new forward root motion;17 has seven small Chest recovery keys. Rebound and
Vault also have bounded authored pose deltas. Those are modifications of stock
clips, not complete newly choreographed attacks. Sling's current kick/turn uses
native animation/controller resources. See the individual release documents.

We can author new animation content on the existing 37-bone model. A new mesh,
new bones or a third suit slot is not required. A purchased clip can retain its
resource ID while replacing its poses completely. New archive IDs/action slots
are a separate routing/progression problem, not a prerequisite for the first
distinct replacement animation.

## New working authoring tools

`tools/sca_author.py` exports all sampled joint translation/rotation/scale values
to private JSON and imports changed rotations/translations into a native SCA.
The source hash, joint count and sample count must match the template. New
independent dynamic tracks are appended and only the selected joint descriptors
point to them. A previously constant or shared track can now animate independently
without changing another bone. It can rewrite every bone over the whole native
duration; it is no longer restricted to the old independent rotation keys.

No-change export/import returns the exact original file. Original static pools,
unused dynamic values, untouched channels, descriptors and unknown header bytes
are retained. Native scale/inverse-scale authoring is disabled pending further
calibration. Nonzero alignment bytes that structural growth would discard cause
rejection; zero alignment can be resized. New indices cannot exceed the 7-bit
descriptor range. Animation length, skeleton and gameplay events are not guessed.

```powershell
python tools/sca_author.py export mods/spd_GroundAttack17.sca --model work/glob/spd.nsbmd --out build/animation-authoring/rush-template.json
# Author sampled local rotations/translations in a separate private JSON file.
python tools/sca_author.py import mods/spd_GroundAttack17.sca build/animation-authoring/authored.json --out build/animation-authoring/authored.sca
```

The export includes raw Q12 matrices, not Blender world matrices or Euler angles.
Each `tracks` record uses the canonical `joint` index and per-sample
`translation_q12`, `rotation_q12`, `scale_q12` arrays. Scale includes its native
inverse values and must remain exact. An optional `--independent-rotations` import
bakes all 37 rotations, including unchanged constant/helper tracks. Outputs are
confined to private `build/` or `work/`; inputs cannot be overwritten.

`tools/animation_rig.py` reads the original model's 37 object names and ancestry.
It checks every NODE parent against the SBC matrix-stack ancestry and preserves
the complete model bytes. Unknown flags are reported as unknown. This is a
read-only rig map, not a model/skin editor.

## Rig mapping and Blender conversion

Fresh apicula export contains 34 skinned/ancestor joints, omitting canonical
helpers34/35/36 and reordering the remaining bones. Map by verified names and
rest transforms; never use its `jointN` ordinal as an SCA index.

| Bone | Canonical SCA/model index | Fresh DAE node ID |
|---|---:|---|
| Chest | 3 | joint3 |
| Shoulder L | 7 | joint9 |
| Shoulder R | 17 | joint7 |
| Hip L | 26 | joint13 |
| Hip R | 30 | joint12 |

The 37-parent tree is established by original player SBC nodes, with roots/spine,
left/right arms, fingers, legs and the three unused export helpers retained.
The NSBMD model and apicula render-command reader provide the model-side context;
the custom SCA loader/evaluator remains the source for animation layout.
[apicula model reader](https://github.com/scurest/apicula/blob/master/src/nitro/model.rs),
[render command interpreter](https://github.com/scurest/apicula/blob/master/src/nitro/render_cmds.rs),
[COLLADA joint generation](https://github.com/scurest/apicula/blob/master/src/convert/collada/mod.rs#L585).

A proper DCC bridge is the next unimplemented step. Blender's final PoseBone
matrix is in armature object space; its `matrix_basis` is relative to parent and
rest bone. Neither can simply be written into an SCA rotation pool. Export the
evaluated pose after constraints/IK, account for imported bone-axis/rest changes,
then convert to the game's parent-local TRS and Q12 matrix order.
[Blender PoseBone API](https://docs.blender.org/api/4.5/bpy.types.PoseBone.html).

Proposed conversion, to be calibrated rather than treated as an already tested
importer: with column-vector notation, `C` maps Blender coordinates to game
coordinates, `B` is bind-world and `P` is evaluated pose-world. Per joint,

```text
P_game = C * P_blender * inverse(B_blender) * inverse(C) * B_game
L_game = inverse(P_game_parent) * P_game
```

This includes bind-axis differences; at the DCC rest pose it yields the game bind
pose. Establish `C`, the imported bind matrices and stored rotation transpose
using a neutral pose and isolated positive X/Y/Z rotations. Do not guess axes
from bone names, copy compact ordinals or import a generic humanoid animation
without retargeting. Preserve the omitted helpers from the source clip.

The practical pipeline is: faithful model/rig import -> native clip preview ->
custom key poses/IK -> evaluated sampled pose export -> SCA compiler -> isolated
in-game captures -> gameplay qualification. It supports newly authored anticipation,
body twist, kick extension, recoil and landing poses once conversion is calibrated.
No Blender installation/export round trip was used to validate the present proof.

## Isolated game proof

`tools/animation_experiment.py` builds two one-asset experiments from the guarded
Rush composition. Only `spd_GroundAttack17.sca` changes; ARM9, GMB, GAB, XBD,
strings, costs and ownership remain exact. It never publishes the stable ROM.

```powershell
python tools/animation_experiment.py rebake --out build/animation-authoring/rebake
python tools/animation_experiment.py guard-recovery --out build/animation-authoring/guard
```

First experiment appends independent rotations for all37 bones while preserving
every sampled pose. Rotation pool count31 ->68, stride884 ->1548, file18248 ->31528
bytes. The game loads and plays it. Finisher and subsequent captures match the
released baseline exactly; an earlier frame3140 differs before this finisher
plays, so whole-run pixel determinism is not claimed.

Second experiment authors a new six-joint recovery sequence: Chest, Head, both
shoulders and elbows. It ramps through samples11..17 and returns to the original
pose by18; the first11 samples/impact and all translations/scales remain original.
At native clock14, the changed upper-body pose is visible in frame3290. This is
an authoring proof, not a polished guard move or a complete new attack. The native
cartwheel/leg choreography remains, so the full silhouette is still mostly stock.

Both candidates and baseline have identical training contact frames, actual HP
loss and native combo credit, ownership, final actor position and return to idle.
Guard/rebake screenshots differ only at captured recovery frames3286/3290.
Source batteries are copied into disposable emulator RAM; fixtures raise only
research XP/HP. The real save is never restored or edited. It advanced independently
while the player tested; the source checkpoint remains exact.

Hit pause matters: in this fixture the sample clock stays6 at emulator frames
3264..3274, reaches9 at3280 and14 at3290. Do not hardcode custom SCA timing as
60 samples/second from apicula's standard NSBCA exporter. Use actual game-clock
observations. Fractional SCA playback interpolates matrix components, not quaternion
SLERP; large adjacent rotations can distort intermediate poses. Author smooth
quaternion curves in the DCC, bake sufficiently close sample poses and inspect
the game's interpolation and final-frame transition.

The append-only proof intentionally retains old unused pools. It grows storage
by13280 bytes and two cached frame buffers by1328 bytes in aggregate. That is
derived from the verified two-buffer/stride layout, not a measured heap high-water
mark or speed result. Before many large clips, add separately tested removal of
unused tracks/deduplication and trace room heap headroom. Do not enlarge all clips
without measuring residency.

Private evidence: `work/animation-research/author-runtime-evidence.json` and
`check-author-runtime.py`; templates/candidates under `build/animation-authoring/`;
runtime folders in that report; frame3290 compares the visible recovery. Whole
clip hashes: rebake `e69edd67b3b9f8dcbd3262efe95a3817f90c589fff7bd3a5f59c85386f42363f`,
guard `821b7da77b080c67e1aea7b24a63fe718d45501d849a0ab32cc18e205e65f899`.
Published ROM remains `ecb07b9a12b3d071f12deaab2d7643276dc52233ca934ee00ea28655415f6f6f`.

## Initial milestones and subsequent progress

The full paid choreography and route-isolation milestones below are now achieved
with procedural FK/IK rather than a Blender bridge. A complete Blender round trip
and broader encounter qualification remain open; current release evidence and
concrete follow-up are in OSCORP_RUSH_ANIMATION.md and TASKS.md.

1. Calibrate Blender bind/axis conversion using canonical37 names and a neutral
   pose plus one-bone rotations. Import an unchanged native clip and demand matching
   sampled matrices/poses before exporting newly animated content.
2. Author one full paid finisher on GroundAttack17: deliberate windup, twisting
   strike and balanced recovery, replacing the stock cartwheel silhouette. Keep
   its20 samples, native contact6/7 and current purchase gate for the first trial.
   Root/collision GMB and events remain separate; adjust them only through their
   own measured experiment if new choreography requires it.
3. Verify beginning/end blending, planted feet, hands, facing and collision, then
   measured contact/HP/credit, locked/owned/refund/save and interruption/ordinary
   encounters. GMB/GAB byte equality alone does not prove limb-based contact paths
   stay equivalent when impact poses change.
4. Extend to the next paid branch with an original full-body sequence. Shared
   GroundAttack15 cannot be changed globally because free Snap also uses it;
   isolate its paid route first. Variable clip lengths require coordinated
   SCA/GMB/GAB/controller work; additional persistent purchases remain separate.

Corpus validation now covers all869 exact sample export/imports and all126 player
clips baked into independent rotations. New tests cover aliases/constants,
translation authoring, unknown/padding preservation, schema/range/descriptor
guards, canonical rig ancestry and isolated experiment confinement. Native
scale authoring, general retargeting, new rigs and a complete DCC round trip remain
open. The working compiler makes original animation choreography practical;
the current research prototype is not counted as a finished attack release.

Final validation: `python -m unittest discover -s tests -v` passes all115 tests;
`python mod.py verify` verifies all3,733 resources against the unchanged published
ROM. The historical combat-flow generator now rejects the newer Rush profile
instead of silently downgrading it. Its instruction-composition test uses its
own historical prerequisite baseline; the Rush tests still verify the current
release's complete text composition.
