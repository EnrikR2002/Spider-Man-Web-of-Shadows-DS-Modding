"""Current copied-save chapter controls, including the new reverse stair route."""
import argparse,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import chapter_spectacle_lab as prior,chapter_renewal_lab as q
from tools import creature_forge_lab as forge,midnight_rework_lab as lab,midnight_walk as mw,crane_walk as cw,kit_lab as k,wos_tool as w

HOIST_RETURN=(('land',190,41,1400),('land',144,61,1400),('land',94,23,1400),('land',50,5,1400))


def main():
    out=Path(os.environ.get('WOS_CHAPTER_LAB_OUT',ROOT/'work/midnight-rebuild/qualification')).resolve()
    if not out.is_relative_to((ROOT/'work').resolve()):raise ValueError('Private research output must remain in work/')
    out.mkdir(parents=True,exist_ok=True);prior.OUT=out
    from tools import playtest
    actual=playtest.current_save();before=actual.read_bytes();copy=out/'current-player-copy.dsv';copy.write_bytes(before);k.TRAINING_SAVE=copy
    if len(sys.argv)>1 and sys.argv[1]=='hoist-save':
        native_run=cw.run
        def return_over_beams(rom,label,start,spawn,steps,preset=()):
            route=[]
            for step in steps:
                if step[:3]==('navigate','AR_LongArm',1):route.extend(HOIST_RETURN)
                route.append(step)
            return native_run(rom,label,start,spawn,route,preset)
        cw.run=return_over_beams
    if len(sys.argv)<2 or sys.argv[1] not in ('tower-loop','crown-reverse','return-loop','hoist-return','observatory','terminal-wave','floodworks-wave','turbine-wave','conductor-study'):return prior.main()
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('case');p.add_argument('--rom',type=Path,required=True);p.add_argument('--tag',default='');p.add_argument('--black',action='store_true');a=p.parse_args()
    if a.case=='hoist-return':
        cw.OUT=out;lab.JIT=True;k._run=lab.static_warp_runner(k._run);k._run._midnight_static=True;cw.install()
        result=cw.run(a.rom,'hoist-return'+a.tag,'AR_LongArm',1,[mw.wait(90),mw.fixtures(fight=False,park=(-60,-60)),
            *mw.put(282,5),*HOIST_RETURN],preset=(142,))
        result['limits']='Focused return traversal: initial arrival/position and cleared hoist preset, crew parked; all movement after initial setup uses native input/physics. Not an earned victory/save test.'
        result['source_battery_unchanged']=actual.read_bytes()==before;w.write_json(out/('result-hoist-return'+a.tag+'.json'),result)
        return 0 if result['passed'] and result['source_battery_unchanged'] else 1
    forge.OUT=out;q.OUT=out;q.RUN_TAG=a.tag;forge.install(a.rom,12)
    switch=[mw.hold('L',6),mw.wait(90),mw.check('native_black_form',lambda s:s.black==1)] if a.black else []
    if a.case in ('observatory','terminal-wave','floodworks-wave','turbine-wave'):
        index,spawn,approach,width={
            'observatory':(86,2,142,288),'terminal-wave':(78,1,140,336),
            'floodworks-wave':(81,2,144,288),'turbine-wave':(83,2,96,192)}[a.case]
        native_roster=lab.Walker.do_roster
        def contained_roster(self,step,state,ptr,ram):
            done=native_roster(self,step,state,ptr,ram)
            if not done and state.pos:
                if state.pos[0]<20:self.buttons.discard('Left');self.buttons.add('Right')
                if state.pos[0]>width-20:self.buttons.discard('Right');self.buttons.add('Left')
            return done
        lab.Walker.do_roster=contained_roster
        from tools.chapter_renewal_rooms import BY_ID
        ending=[mw.wait(90),mw.check('native_bowl_roster_clear_in_same_room',lambda s:s.room==index and not s.enemies)] if a.case=='observatory' else [
            mw.wait(240),('roster',6000),mw.wait(90),mw.check('native_ramp_roster_clear_in_same_room',lambda s:s.room==index and not s.enemies)]
        candidate_meta=json.loads(a.rom.with_suffix('.build.json').read_text())
        upper=index==83 and candidate_meta.get('midnight_reliability',{}).get('rooms',{}).get('rooms',{}).get(BY_ID[index],{}).get('upper_balcony_encounter')
        approach_steps=[('land',x,y+5,1600) for x,y in ((48,16),(88,32),(128,48),(88,64),(48,80),(88,96))] if upper else [('travel',approach,1800)]
        result=q.run(a.rom,a.case,BY_ID[index],spawn,[mw.wait(90),*approach_steps,('roster',14000),*ending],combat=True,heal=True)
    elif a.case=='conductor-study':
        native=k._run;done=False
        def fresh(*args,**kw):
            original=kw['extra_hook']
            def hook(frame,lib):
                nonlocal done
                if frame==-990 and not done:
                    import ctypes as ct
                    ptr,ram=k.ram_of(lib);stats=w.u32(ram,k.STATS_POINTER-0x2000000)-0x2000000
                    flags=int.from_bytes(ram[stats+0x1c:stats+0x44],'little')&~(1<<147);ct.memmove(ptr+stats+0x1c,flags.to_bytes(40,'little'),40);done=True
                return original(frame,lib)
            kw['extra_hook']=hook;return native(*args,**kw)
        fresh._midnight_static=True;k._run=fresh
        def study(self,step,state,ptr,ram):
            self.buttons.clear()
            if self.t>=step[1]:return True
            if state.pos and state.enemies:
                e=state.enemies[0];dx=e['position'][0]/4096-state.pos[0]
                if e['state']!=15:
                    if abs(dx)>12:self.buttons.add('Right' if dx>0 else 'Left')
                    elif abs(dx)<9:self.buttons.add('Left' if dx>0 else 'Right')
            return False
        lab.Walker.do_study_boss=study
        result=q.run(a.rom,'conductor-study','ML_Venom',2,[mw.wait(120),*switch,('travel',90,1800),('study_boss',1800),('phase_bait',9000),('study_boss',1800),('combat',14000)],combat=True,heal=True)
    elif a.case=='return-loop':
        result=q.run(a.rom,'return-loop'+('-black' if a.black else '-red'),'ML_Venom',2,[mw.wait(90),*switch,
            cw.nav('ML_Venom',2,4200),mw.wait(90),cw.nav('ML_NestGate',2,4200),mw.wait(90),
            mw.check('crown_descent_reaches_gate_balcony',lambda s:s.room==76),('land',54,37,1500),('land',70,5,1500),
            cw.nav('ML_Entry',2,4200),mw.wait(90),mw.check('native_return_to_sewer',lambda s:s.room==65)])
    else:
        start='ML_Entry' if a.case=='tower-loop' else 'ML_NestGate';spawn=3 if a.case=='tower-loop' else 1
        steps=[mw.wait(90),*switch]
        if a.case=='tower-loop':steps.extend((cw.nav('ML_Entry',3,4200),mw.wait(90),mw.check('tower_enters_crown_return',lambda s:s.room==88)))
        steps.extend((cw.nav('ML_NestGate',1,5000),mw.wait(90),mw.check('reverse_stairs_reach_conductor',lambda s:s.room==89)))
        result=q.run(a.rom,a.case+('-black' if a.black else '-red'),start,spawn,steps)
    result['source_battery_unchanged']=actual.read_bytes()==before
    w.write_json(out/('result-'+a.case+a.tag+'.json'),result)
    return 0 if result['passed'] and result['source_battery_unchanged'] else 1


if __name__=='__main__':raise SystemExit(main())
