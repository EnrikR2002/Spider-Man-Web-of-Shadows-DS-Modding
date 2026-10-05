"""Purchased advancing red string; native timing, damage and ownership retained."""
from pathlib import Path
import argparse
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mod
from tools import wos_tool as w, combat_profile as cp, combat_readability as q, combat_flow as flow
from tools.grip_compression import CompressedBlob
from tools.gmb import Gmb
from tools.sca import Sca

PROFILE = 'tasm-oscorp-rush'
# Native logical actions 61 and 62; action60 and free action56 share G15.
ROOTS = {'spd_GroundAttack16.gmb': (39, 20, 6*4096),
         'spd_GroundAttack17.gmb': (20, 8, 2*4096)}
POSE_ASSET = 'spd_GroundAttack17.sca'
POSE_KEYS = ((10,-4), (11,-8), (12,-11), (13,-10), (14,-7), (15,-4), (16,-2))
TEXT_EDITS = {192:'Oscorp Rush', 193:'Oscorp Rush',
    194:'\ue601, let the sweep end, \ue601, \ue601, \ue601.\nAdvancing kicks, then a strike.',
    197:'Requires Oscorp Rush.\n\ue601, pause, \ue601, then rapid \ue601.',
    417:'SELECT and Down: refill.\nPause: Return to Save Point.'}

def advance(raw, asset):
    if asset not in ROOTS: raise ValueError('Unsupported paid Rush asset')
    count, end, distance = ROOTS[asset]
    wrapper = CompressedBlob.parse(raw)
    g = Gmb.parse(wrapper.decoded)
    if (g.record_count != count or
        [(c.kind,c.unknown_u16_02) for c in g.channels] != [(3,0),(3,1),(3,0),(0,0)]):
        raise ValueError('Unexpected native Rush movement layout')
    original = [g.channels[0].words(i)[2] for i in range(count)]
    if asset.endswith('16.gmb'):
        if original[0] != 0 or original[-1] != 4870 or any(a>b for a,b in zip(original,original[1:])):
            raise ValueError('Native triple-kick root differs')
    elif any(original): raise ValueError('Native finisher root differs')
    result = g.raw
    # Smooth bounded displacement, fixed native length/events/contact arrays.
    # Integer smoothstep has exact endpoints and deterministic rounding.
    for i in range(count):
        t = min(i,end)
        value = distance * t*t * (3*end-2*t) // (end**3)
        result = Gmb.parse(result).replace_word(0,i,2,value)
    if result[g.channels[1].offset:] != g.raw[g.channels[1].offset:]:
        raise ValueError('Rush touched non-root data')
    return wrapper.replace_decoded(result,compact=True)

def recovery_pose(raw):
    s = Sca.parse(raw)
    if (s.frame_count,s.joint_count) != (20,37):
        raise ValueError('Unexpected native finisher skeleton')
    result = raw
    for frame,angle in POSE_KEYS:
        result = Sca.parse(result).rotate_joint(3,frame,'x',angle)
    return result

def generate(base_mods='mods', output='build/oscorp-rush'):
    root=w.safe_output(mod.project_path(output))
    if not root.is_relative_to((mod.ROOT/'build').resolve()): raise ValueError('Candidates belong in build/')
    rom,glob,manifest=mod.load_clean();entries={e['name']:e for e in manifest['entries']}
    overlays=mod.overlay_files(mod.project_path(base_mods),list(entries))
    current=cp.load_recipe(mod.ROOT/'reference/gameplay_profile.json',overlays)
    if current not in ('tasm-combat-flow',PROFILE): raise ValueError('Rush requires the accepted combat-flow composition')
    edits=[]
    for name in (*ROOTS,POSE_ASSET):
        e=entries[name];clean=glob[e['offset']:e['offset']+e['size']]
        changed=advance(clean,name) if name in ROOTS else recovery_pose(clean)
        if overlays.get(name,clean) not in (clean,changed): raise ValueError(f'Explicit merge required: {name}')
        overlays[name]=changed
        edits.append({'asset':name,'clean_sha256':w.sha256(clean),'sha256':w.sha256(changed)})
    q.compose(glob,manifest,overlays,flow.TEXT_EDITS | TEXT_EDITS)
    for name,data in overlays.items(): w.atomic_write(root/'mods'/name,data,(mod.DEFAULT_ROM,))
    recipe={'schema_version':1,'profile':PROFILE,'required_overlays':{n:w.sha256(d) for n,d in overlays.items()}}
    w.write_json(root/'gameplay_profile.json',recipe)
    result,_,log=mod.create_build(rom,glob,manifest,overlays,gameplay_profile=PROFILE)
    path=root/'OscorpRush.nds';w.atomic_write(path,result,(mod.DEFAULT_ROM,));w.write_json(path.with_suffix('.build.json'),log)
    w.write_json(root/'rush.json',{'assets':edits,'rom_sha256':w.sha256(result),'ownership_bit':16,'event':325,'price':400,
        'limitations':['Native clips retained; authored advance and post-contact chest recovery.',
                       'No new hit, damage, launcher, speed tier or Scissor extension is granted.']})
    return path

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mods',default='mods');parser.add_argument('--out',default='build/oscorp-rush');args=parser.parse_args()
    try: print(generate(args.mods,args.out))
    except (ValueError,OSError) as exc: print(f'error: {exc}',file=sys.stderr);return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
