"""Private one-asset SCA authoring experiments; never publishes the stable ROM.

rebake: new independent rotation tracks, original sampled poses.
guard-recovery: authored multi-joint recovery after contact, same action timing.
This is pipeline research, not an accepted new attack or Blender importer.
"""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import mod
from tools import wos_tool as w,combat_profile as cp
from tools.sca import Sca,multiply_q12,rotation_q12
from tools.sca_author import repack_samples,export_samples
from tools.animation_rig import AnimationRig

ASSET='spd_GroundAttack17.sca'
BASE_SHA256='782da8b35e252251b5759afbf00adb8a48a62ca0db397fb3b1d4cadfb41cc2e8'
# First proof: fixed native hit poses; new upper-body follow-through / guard.
# These explicit stored-axis deltas require visual calibration, not DCC claims.
DELTAS={3:('x',-24),5:('x',12),7:('z',-45),8:('z',35),17:('z',45),18:('z',-35)}
ENVELOPE={10:0,11:0.25,12:0.65,13:0.9,14:1,15:0.9,16:0.65,17:0.25,18:0}


def author(raw,variant):
    a=Sca.parse(raw)
    if w.sha256(raw)!=BASE_SHA256 or (a.frame_count,a.joint_count)!=(20,37):
        raise ValueError('Experiment requires the exact accepted Rush finisher')
    if variant not in ('rebake','guard-recovery'):raise ValueError('Unknown animation experiment')
    rotations={}
    if variant=='guard-recovery':
        for joint,(axis,peak) in DELTAS.items():
            keys=[a.rotation(joint,f) for f in range(a.frame_count)]
            for frame,gain in ENVELOPE.items():
                keys[frame]=multiply_q12(keys[frame],rotation_q12(axis,peak*gain))
            rotations[joint]=keys
    return repack_samples(raw,rotations=rotations,independent_rotations=True)


def generate(variant,output):
    dest=w.safe_output(mod.project_path(output))
    if not dest.is_relative_to((mod.ROOT/'build').resolve()):raise ValueError('Research candidates belong in build/')
    rom,glob,manifest=mod.load_clean();names=[e['name'] for e in manifest['entries']]
    overlays=mod.overlay_files(mod.ROOT/'mods',names)
    if cp.load_recipe(mod.ROOT/'reference/gameplay_profile.json',overlays)!='tasm-oscorp-rush':
        raise ValueError('Experiment requires the accepted Rush composition')
    base=overlays[ASSET];changed=author(base,variant);overlays[ASSET]=changed
    rig_entry=next(e for e in manifest['entries'] if e['name']=='spd.nsbmd')
    rig=AnimationRig.parse(glob[rig_entry['offset']:rig_entry['offset']+rig_entry['size']])
    for name,data in overlays.items():w.atomic_write(dest/'mods'/name,data,(mod.DEFAULT_ROM,))
    recipe={'schema_version':1,'profile':'tasm-oscorp-rush','required_overlays':{n:w.sha256(d) for n,d in overlays.items()}}
    w.write_json(dest/'gameplay_profile.json',recipe)
    result,_,log=mod.create_build(rom,glob,manifest,overlays,gameplay_profile='tasm-oscorp-rush')
    path=dest/'AnimationTest.nds';w.atomic_write(path,result,(mod.DEFAULT_ROM,));w.write_json(path.with_suffix('.build.json'),log)
    w.write_json(dest/'samples.json',export_samples(changed,rig))
    a,b=Sca.parse(base),Sca.parse(changed)
    w.write_json(dest/'experiment.json',{'variant':variant,'asset':ASSET,'base_sha256':w.sha256(base),
        'sca_sha256':w.sha256(changed),'rom_sha256':w.sha256(result),'old_size':len(base),'new_size':len(changed),
        'old_stride':a.frame_stride,'new_stride':b.frame_stride,'old_counts':list(a.counts),'new_counts':list(b.counts),
        'authored_joints':list(DELTAS) if variant=='guard-recovery' else [],'first_changed_sample':11 if variant=='guard-recovery' else None,
        'limitations':['Same timing and resource ID; no new action or archive entry.',
                       'Only recovery poses authored; full new anticipation/impact choreography remains future work.',
                       'No Blender round trip, dense AI, wall or player acceptance implied.']})
    return path


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('variant',choices=('rebake','guard-recovery'));parser.add_argument('--out',required=True)
    args=parser.parse_args()
    try:print(generate(args.variant,args.out));return 0
    except (ValueError,OSError) as exc:print(f'error: {exc}',file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
