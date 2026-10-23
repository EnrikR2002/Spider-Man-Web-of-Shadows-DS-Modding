"""Copied-current-save Vortex gates, native boss damage, rendering and byte scope."""
import argparse
import ctypes as ct
import json
import os
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import kit_lab as k,wos_tool as w,playtest,vortex_forge as vf


def copy_current(out):
    out.mkdir(parents=True,exist_ok=True);actual=playtest.current_save();before=actual.read_bytes()
    copied=out/'current-player-copy.dsv';copied.write_bytes(before)
    return actual,before,copied


def current_prefix(path):
    """Ordinary Continue, then the actual save sphere's Test Upgrades menu."""
    return [dict(start=t,end=t+6,buttons=[button]) for t,button in (
        (720,'A'),(840,'A'),(960,'A'),(1080,'Down'),(1140,'A'),(1500,'B'),(1620,'A'),
        (1800,'X'),(1860,'Down'),(1920,'Down'),(1980,'A'))]


def vortex(a):
    actual,before,copied=copy_current(a.out)
    meta=json.loads(a.rom.with_suffix('.build.json').read_text());state=meta['vortex_forge']['runtime']['state'];rows=[]
    native=k.rows_from
    def prefix(path):return current_prefix(path) if str(path).endswith('oscorp-owned.json') else native(path)
    k.rows_from=prefix
    def hook(frame,lib):
        if frame>=0:
            ptr,ram=k.ram_of(lib)
            if a.case=='bystander' and frame<=100:
                # Isolate body contacts from an unrelated enemy interrupting
                # the grapple windup; never overwrite cocoons or launched foes.
                for enemy in k.enemies(ram):
                    if enemy['controller'] and enemy['state'] not in (39,41,46,48,49):
                        ct.memmove(ptr+enemy['controller']-0x02000000+0x14,bytes(4),4)
            rows.append(dict(frame=frame,private=list(struct.unpack_from('<16I',ram,state-0x02000000))))
    mirror=a.case=='mirror';side='Left' if mirror else 'Right'
    inputs=[dict(start=15,end=20,buttons=[side]),dict(start=50,end=90,buttons=['A']),dict(start=112,end=118,buttons=['Down','Y'])]
    if a.case=='bare':inputs=[dict(start=45,end=52,buttons=['Down','Y'])]
    if a.case=='bystander':
        inputs=[dict(start=15,end=20,buttons=[side]),dict(start=50,end=80,buttons=['A']),dict(start=86,end=92,buttons=['Down','Y'])]
    if a.case=='cancel':inputs.append(dict(start=128,end=134,buttons=['R']))
    if a.case=='black':inputs.insert(0,dict(start=4,end=10,buttons=['L']))
    bits=0 if a.case=='unowned' else 0x60000 if a.case in ('dragnet','cancel') else 0x40000
    positions=(-8,12,18,30) if a.case=='bystander' else (21,24,27,30)
    route,obs=k._run(a.rom,a.tag,inputs,frames=220,bits2=bits,clear2=0x7fc00,sparring=True,start_x=100*4096,
        place=tuple((d*4096*(-1 if mirror else 1),246) for d in positions),enemy_state=(-20,48,0),save=copied,
        caps=tuple(range(100,173,3)),rams=(145,),extra_hook=hook,
        core_options={b'melonds_jit_enable':b'enabled',b'melonds_jit_block_size':b'12'})
    starts=max(r['private'][10] for r in rows);slams=max(r['private'][11] for r in rows);bystanders=max(r['private'][13] for r in rows)
    if a.case in ('bare','unowned','black'):passed=starts==0
    elif a.case=='cancel':passed=starts==1 and slams==0 and rows[-1]['private'][4]==0
    else:passed=starts==1 and slams>0
    if a.case=='bystander':passed=passed and bystanders>0
    webbed=max((sum(e[2]==46 for e in r['en']) for r in obs),default=0)
    passed=passed and actual.read_bytes()==before and copied.read_bytes()==before
    report=dict(case=a.case,rom_sha256=w.sha256(a.rom.read_bytes()),route=str(route),passed=passed,starts=starts,
        slams=slams,bystander_hits=bystanders,maximum_actual_webbed=webbed,rows=rows,
        source_battery_sha256=w.sha256(before),source_battery_unchanged=actual.read_bytes()==before,copy_unchanged=copied.read_bytes()==before,
        limits='Latest actual DSV copy and ordinary Continue/Test Upgrades. Disposable initial purchases, positions and idle enemy prefix through frame48. The bystander case alone additionally parks unwebbed standing bystanders through frame100, leaving cocoons, launched/hurt actors and contacts native. Training immortality/healing applies; this is mechanics/presentation, not campaign balance.')
    w.write_json(a.out/'result.json',report)
    print(json.dumps({key:report[key] for key in ('case','passed','starts','slams','bystander_hits','maximum_actual_webbed','route')}))
    return 0 if passed else 1


def boss(a):
    from tools import chapter_renewal_lab as q,creature_forge_lab as forge,midnight_rework_lab as lab,midnight_walk as mw,owned_player_lab,combat_hud
    from tools.spider2099 import resources
    from tools.model_geometry import ModelGeometry
    from tools.nitro_texture import dictionary
    actual,before,copied=copy_current(a.out)
    if not a.owned:raise ValueError('Boss controls require --owned from a freshly measured actual-save profile')
    os.environ['WOS_CHAPTER_LAB_SAVE']=str(copied);owned_player_lab.install(a.owned)
    q.configure_rooms(a.rom);forge.OUT=a.out;q.OUT=a.out;q.RUN_TAG='-'+a.tag;forge.install(a.rom,18)
    native=lab.Walker.tick;rows=[];names,blobs=resources(a.rom.read_bytes());raw=blobs[names.index('zz_F22_conductor.nsbmd')]
    g=ModelGeometry.parse(raw);mb=g.model+w.u32(raw,g.model+8);matoff=mb+w.u32(dictionary(raw,mb+4,4)[0][1],0)-g.model
    def tick(self,frame,lib):
        result=native(self,frame,lib)
        if frame<0:return result
        ptr,ram=k.ram_of(lib);stats=w.u32(ram,k.STATS_POINTER-0x02000000)-0x02000000
        if frame==0 and a.low_hp:ct.memmove(ptr+stats+0x84,struct.pack('<I',1536),4)
        if self.last_state:
            row=dict(frame=frame,hp=w.u32(ram,stats+0x84),state=self.last_state.state,enemy_bars=combat_hud.sample(ram)['enemy_bars'])
            for enemy in self.last_state.enemies:
                mot=w.u32(ram,enemy['actor']-0x02000000+0x30)-0x02000000;wr=w.u32(ram,mot+0x58)-0x02000000
                mdl=w.u32(ram,wr+0x14)-0x02000000;mat=mdl+matoff
                row.update(boss_actor=enemy['actor'],material=ram[mat:mat+44].hex(),texture_format=w.u32(ram,mat+20)>>26&7,
                           dimensions=list(struct.unpack_from('<2H',ram,mat+32)))
            rows.append(row)
        return result
    lab.Walker.tick=tick
    route=q.run(a.rom,'boss-view-'+a.tag,'ML_Venom',2,[mw.wait(120),mw.walk('arena',80,600),mw.wait(900)],combat=True,heal=False)
    drops=[dict(frame=r['frame'],hp=r['hp']) for i,r in enumerate(rows) if i>1 and r['hp']<rows[i-1]['hp']]
    bindings=[r for r in rows if 'texture_format' in r]
    hp_pass=bool(drops and (drops[0]['hp']==0 if not a.parent else len(drops)>1)) if a.low_hp else bool(bindings)
    hud_pass=all(not any(b['actor']==r['boss_actor'] for b in r['enemy_bars']) for r in bindings) if not a.parent else True
    texture_pass=all(r['texture_format']==7 and r['dimensions']==[64,64] for r in bindings) if not a.parent else True
    passed=hp_pass and hud_pass and texture_pass and actual.read_bytes()==before and copied.read_bytes()==before
    report=dict(passed=passed,rom_sha256=w.sha256(a.rom.read_bytes()),route=route,rows=rows,hp_drops=drops,
        boss_bar_only=hud_pass,boss_texture_bound=texture_pass,source_battery_sha256=w.sha256(before),
        source_battery_unchanged=actual.read_bytes()==before,copy_unchanged=copied.read_bytes()==before,
        limits='Latest actual DSV copy; compiled initial arena arrival, measured current ownership/XP/initial HP. Optional 1536-Q12 initial low-HP fixture; native walk/contact thereafter, no healing. Standstill damage/render control, not a victory or player acceptance.')
    w.write_json(a.out/'result.json',report)
    print(json.dumps(dict(passed=passed,hp_drops=drops,boss_bar_only=hud_pass,boss_texture_bound=texture_pass)))
    return 0 if passed else 1


def scope(a):
    from tools.spider2099 import resources
    from tools.sca import Sca
    from tools.sca_author import sample
    old=vf.PARENT_PATH.read_bytes();new=a.rom.read_bytes();names,before=resources(old);nn,after=resources(new)
    log=json.loads(a.rom.with_suffix('.build.json').read_text())['vortex_forge'];allowed=set(log['modified_resources'])
    assert names==nn[:len(names)]
    assert {n for n,x,y in zip(names,before,after) if x!=y}==allowed
    clips=[]
    for name in allowed:
        if not name.startswith('zz_F22_conductor_') or not name.endswith('.sca'):continue
        x,y=Sca.parse(before[names.index(name)]),Sca.parse(after[nn.index(name)])
        assert (x.frame_count,x.joint_count)==(y.frame_count,y.joint_count)
        for j in range(x.joint_count):
            for f in range(x.frame_count):
                for channel in ('rotation','scale'):assert sample(x,j,f,channel)==sample(y,j,f,channel)
        clips.append(name)
    assert len(clips)==39
    for name in ('arm7',):
        h,hh=w.parse_header(old),w.parse_header(new)
        assert old[h[name+'_offset']:h[name+'_offset']+h[name+'_size']]==new[hh[name+'_offset']:hh[name+'_offset']+hh[name+'_size']]
    for e in w.nitrofs_entries(old):
        if e['name']=='Glob.bin':continue
        other=next(x for x in w.nitrofs_entries(new) if x['name']==e['name'])
        assert old[e['start']:e['end']]==new[other['start']:other['end']]
    report=dict(passed=True,rom_sha256=w.sha256(new),private_boss_clips=len(clips),boss_timings_rotations_scales_exact=True,
        unrelated_resources_exact=True,rooms_gmb_gab_audio_arm7_exact=True,scope=log)
    a.out.mkdir(parents=True,exist_ok=True);w.write_json(a.out/'scope.json',report);print(json.dumps(dict(passed=True,private_boss_clips=len(clips))))
    return 0


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('vortex','boss','scope'));p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--tag',default='v31');p.add_argument('--case',choices=('regular','dragnet','bare','unowned','black','cancel','mirror','bystander'),default='regular')
    p.add_argument('--owned',type=Path);p.add_argument('--low-hp',action='store_true');p.add_argument('--parent',action='store_true');a=p.parse_args()
    a.rom=a.rom.resolve();a.out=a.out.resolve()
    if not a.out.is_relative_to((ROOT/'work').resolve()):raise ValueError('Private evidence belongs in work/')
    raise SystemExit(dict(vortex=vortex,boss=boss,scope=scope)[a.command](a))
