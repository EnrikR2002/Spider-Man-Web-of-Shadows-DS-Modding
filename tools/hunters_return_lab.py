"""Copied-current-save Hunter mechanics and native-scale presentation controls."""
import argparse
import ctypes as ct
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import kit_lab as k, wos_tool as w, vortex_forge_lab as v, playtest


def run(a):
    if not a.out.resolve().is_relative_to((ROOT/'work').resolve()):
        raise ValueError('Hunter lab evidence must stay in work/')
    actual,before,copied=v.copy_current(a.out)
    profile=json.loads(a.owned.read_text())
    if w.sha256(before)!=profile['source_sha256']:
        raise ValueError('Actual battery changed; measure current player again')
    boot=(Path(profile['captures'])/'ram-03500.bin').read_bytes()
    hero=k.p.sample(boot)['actor_address']-0x02000000
    initial_form=w.u32(boot,hero+0x34)
    desired_form=0 if a.case=='red' else 1
    inputs=[]
    if initial_form!=desired_form:inputs.append(dict(start=4,end=10,buttons=['L']))
    side='Left' if a.case in ('mirror','wall') else 'Right'
    inputs.extend((dict(start=35,end=40,buttons=[side]),dict(start=60,end=66,buttons=['A'])))
    if a.case=='hold':inputs[-1]['end']=130
    elif a.case!='bare':inputs.append(dict(start=96,end=102,buttons=['A']))
    if a.case=='cancel':inputs.append(dict(start=105,end=111,buttons=['R']))
    if a.case=='swap':inputs.append(dict(start=105,end=111,buttons=['L']))
    if a.case in ('regular','mirror','wall'):
        inputs.extend((dict(start=148,end=154,buttons=['B']),dict(start=162,end=168,buttons=['Y'])))
    meta=json.loads(a.rom.with_suffix('.build.json').read_text())
    state=meta['hunters_return']['runtime']['state']
    native=k.rows_from
    k.rows_from=lambda path:v.current_prefix(path) if str(path).endswith('oscorp-owned.json') else native(path)
    rows=[]
    def hook(frame,lib):
        if frame<0:return
        ptr,ram=k.ram_of(lib)
        current=list(struct.unpack_from('<16I',ram,state-0x02000000))
        if a.case=='stale' and frame==105 and current[5]:
            # Private target corruption only; the native actor is left alive.
            ct.memmove(ptr+state-0x02000000+8,struct.pack('<I',0x02312340),4)
        if a.case=='hurt' and frame==105 and current[5]:
            # One disposable native state interruption; no fabricated damage.
            ct.memmove(ptr+current[1]-0x02000000+0x14,struct.pack('<I',63),4)
        hero=k.p.sample(ram)['actor_address']-0x02000000
        mot=w.u32(ram,hero+0x30)-0x02000000
        wrapper=w.u32(ram,mot+0x58)-0x02000000
        mdl=w.u32(ram,wrapper+0x14)-0x02000000
        appearance=meta['hunters_return']['shared_model']
        material=mdl+appearance['material_offset']
        shape=mdl+appearance['shape_offset']
        rows.append(dict(frame=frame,private=current,form=w.u32(ram,hero+0x34),
            sca=w.u32(ram,mot+0x2f4),shape=list(struct.unpack_from('<2I',ram,shape+8)),
            texture_format=w.u32(ram,material+20)>>26&7,
            dimensions=list(struct.unpack_from('<2H',ram,material+32))))
    start_x=30*4096 if a.case=='wall' else 100*4096
    dx=-70 if a.case=='whiff' else 14
    if a.case in ('mirror','wall'):dx=-dx
    bystanders=(80,85) if a.case=='wall' else (-80,-85)
    clear=1<<20 if a.case=='unowned' else 0
    dest,obs=k._run(a.rom,a.tag,inputs,frames=250,bits=0 if clear else 1<<20,clear=clear,
        enemy_state=(-20,70,0),sparring=True,start_x=start_x,
        place=((dx*4096,246),*( (d*4096,246) for d in bystanders)),save=copied,
        caps=tuple(range(100,197,2)),rams=(105,145,210),extra_hook=hook,
        core_options={b'melonds_jit_enable':b'enabled',b'melonds_jit_block_size':b'12'})
    starts=max(r['private'][8] for r in rows)
    launches=max(r['private'][9] for r in rows)
    pursuits=max(r['private'][10] for r in rows)
    blocked=a.case in ('unowned','red','whiff','hold','bare')
    interrupted=a.case in ('cancel','hurt','stale','swap')
    passed=starts==0 if blocked else starts==1 and (launches==0 if interrupted and a.case!='swap' else launches==1 or pursuits==1)
    if interrupted:passed=passed and rows[-1]['private'][5]==0
    if a.case=='wall':passed=passed and min(r['pos'][0] for r in obs)>=3.4*4096 and max(r['pos'][0] for r in obs)<237*4096
    active=[r for r in rows if r['private'][5]]
    textured=bool(active) and all(r['texture_format']==4 and r['dimensions']==[128,128] for r in active)
    selected=bool(active) and all(r['shape']==meta['hunters_return']['shared_model']['trailer'][6:8] for r in active)
    if not blocked:passed=passed and textured and selected
    source_ok=actual.read_bytes()==before and copied.read_bytes()==before
    passed=passed and source_ok
    report=dict(passed=passed,case=a.case,rom_sha256=w.sha256(a.rom.read_bytes()),route=str(dest),
        starts=starts,launches=launches,pursuits=pursuits,hero_textured=textured,black_draw_list_selected=selected,rows=rows,
        source_battery_sha256=w.sha256(before),source_battery_unchanged=source_ok,
        limits='Latest measured battery copy and ordinary Continue/Test Upgrades; disposable purchase/form, initial positions and idle prefix through70. Training healing/immortality apply. Hurt is a labelled state-only interruption; stale corrupts only private target state. No actual battery writes or campaign-balance claim.')
    w.write_json(a.out/'result.json',report)
    print(json.dumps({key:report[key] for key in ('passed','case','starts','launches','hero_textured','route')}))
    return 0 if passed else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--owned',type=Path,required=True)
    p.add_argument('--case',choices=('regular','mirror','unowned','red','whiff','hold','bare','cancel','hurt','stale','swap','wall'),default='regular')
    p.add_argument('--tag',required=True)
    a=p.parse_args()
    sys.exit(run(a))
