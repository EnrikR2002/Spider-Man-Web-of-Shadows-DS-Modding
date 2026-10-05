"""Isolated full Rush choreography, retaining native purchase gates and budgets."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import mod
from tools import wos_tool as w,combat_profile as cp,combat_readability as q,combat_flow,tasm_oscorp_rush
from tools.animation_rig import AnimationRig
from tools.custom_formats import Xbd
from tools.rush_choreography import author
from tools import oscorp_resources as resources

PARENT='tasm-oscorp-rush'
PROFILE='tasm-oscorp-rush-authored'
PARENT_RECIPE_SHA='a2b63f8def8c0e2ee7e0751b7b27ddf0655a27ab9d76522cea4f85a988af7ac0'
AUTHORED_RECIPE_SHA='3606b6015a95a50e473fdff4a6e1c9f23a3bbcefa5cf9757c58008bcaa69219b'
REFINED_RECIPE_SHA='293dc1dc8b630276e87617da5b3b4199d8f59bba8952b3924d849aae995946f8'
TEXT_EDITS={194:'\ue601, let the sweep end, \ue601, \ue601, \ue601.\nPunch combo, knee and overhand.'}

def isolate_rush(raw,names):
    x=Xbd.parse(raw,names);out=raw;changes=[]
    # Dedicated appended SCAs: no original attack resource changes. In
    # particular m6 also uses G11/16/17; none is a globally unused spare.
    for offset,source,target in ((404,'spd_GroundAttack15.sca',resources.EXTRA_NAMES[0]),
                                  (416,'spd_GroundAttack16.sca',resources.EXTRA_NAMES[1]),
                                  (428,'spd_GroundAttack17.sca',resources.EXTRA_NAMES[2])):
        b=next((b for b in x.bindings if b['offset']==offset),None)
        if b is None or b['name']!=source:raise ValueError('Paid Rush binding differs')
        index=names.index(target)
        out=Xbd.parse(out,names).replace_binding(offset,index,names);changes.append({'offset':offset,'old':b['index'],'new':index})
    return out,changes

def generate(output='build/oscorp-dedicated'):
    dest=w.safe_output(mod.project_path(output))
    if not dest.is_relative_to((mod.ROOT/'build').resolve()):raise ValueError('Candidates belong in build/')
    rom,glob,manifest=mod.load_clean();entries={e['name']:e for e in manifest['entries']};names=list(entries)
    recipe=mod.ROOT/'reference/gameplay_profile.json'
    extra=resources.EXTRA_NAMES if json.loads(recipe.read_text())['profile']==PROFILE else ()
    overlays=mod.overlay_files(mod.ROOT/'mods',names,added_names=extra)
    current=cp.load_recipe(recipe,overlays)
    accepted={PARENT:{PARENT_RECIPE_SHA},PROFILE:{AUTHORED_RECIPE_SHA,REFINED_RECIPE_SHA}}
    if w.sha256(recipe.read_bytes()) not in accepted.get(current,set()):
        raise ValueError('Full authoring requires an exact accepted Rush composition')
    if set(overlays)!=set(json.loads(recipe.read_text())['required_overlays']):
        raise ValueError('Explicit merge required for additional overlays')
    def clean(name):
        e=entries[name];return glob[e['offset']:e['offset']+e['size']]
    rig=AnimationRig.parse(clean('spd.nsbmd'));idle=clean('spd_Idle.sca');proof={}
    for variant,source,target in (('entry','spd_GroundAttack16',resources.EXTRA_NAMES[1]),
                                  ('bridge','spd_GroundAttack15',resources.EXTRA_NAMES[0]),
                                  ('finish','spd_GroundAttack17',resources.EXTRA_NAMES[2])):
        base=clean(source+'.sca')
        if variant=='finish':base=tasm_oscorp_rush.recovery_pose(base)
        changed,poses=author(base,idle,rig.parents,variant);overlays[target]=changed
        proof[variant]={'source':source,'target':target,'base_sha256':w.sha256(base),
                        'authored_sha256':w.sha256(changed),'old_size':len(base),'new_size':len(changed),'poses':poses}
    xbd=overlays['spd.xbd']
    if current==PROFILE:
        for offset,source in ((404,'spd_GroundAttack15.sca'),(416,'spd_GroundAttack16.sca'),(428,'spd_GroundAttack17.sca')):
            xbd=Xbd.parse(xbd,[*names,*resources.EXTRA_NAMES]).replace_binding(offset,names.index(source),[*names,*resources.EXTRA_NAMES])
    overlays['spd.xbd'],bindings=isolate_rush(xbd,[*names,*resources.EXTRA_NAMES])
    q.compose(glob,manifest,overlays,combat_flow.TEXT_EDITS | tasm_oscorp_rush.TEXT_EDITS | TEXT_EDITS)
    if (dest/'mods').exists() and set(mod.overlay_files(dest/'mods',names,added_names=resources.EXTRA_NAMES))-set(overlays):
        raise ValueError('Candidate directory contains older overlays; use a separate output directory')
    for name,data in overlays.items():w.atomic_write(dest/'mods'/name,data,(mod.DEFAULT_ROM,))
    recipe={'schema_version':1,'profile':PROFILE,'required_overlays':{n:w.sha256(d) for n,d in overlays.items()}}
    w.write_json(dest/'gameplay_profile.json',recipe)
    result,_,log=mod.create_build(rom,glob,manifest,overlays,gameplay_profile=PROFILE)
    path=dest/'OscorpAuthored.nds';w.atomic_write(path,result,(mod.DEFAULT_ROM,));w.write_json(path.with_suffix('.build.json'),log)
    w.write_json(dest/'choreography.json',{'rom_sha256':w.sha256(result),'clips':proof,'bindings':bindings,
                 'limitations':['Procedural FK/IK authoring; no Blender import/export.',
                                'New impact poses need measured contact and visual qualification before promotion.']})
    return path

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',default='build/oscorp-dedicated');args=parser.parse_args()
    try:print(generate(args.out));return 0
    except (ValueError,OSError) as exc:print(f'error: {exc}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
