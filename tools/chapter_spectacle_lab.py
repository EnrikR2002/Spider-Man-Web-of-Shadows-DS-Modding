"""Copied-save, native-input chapter presentation and pursuit observations."""
import argparse,json,sys,ctypes as ct,struct,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import creature_forge_lab as forge,chapter_renewal_lab as q,midnight_walk as mw,kit_lab as k,wos_tool as w
OUT=ROOT/'work/chapter-spectacle'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('case',choices=('terminal','terminal-reverse','terminal-upper','terminal-roof','station-air','quay-air','duel','freight','crown','crown-checkpoint','phase','conductor','conductor-continue','hoist','hoist-save','arm-continue','arm-retry-continue','engine','pump'))
    p.add_argument('--rom',type=Path,required=True);p.add_argument('--tag',default='');p.add_argument('--capture-every',type=int,default=12)
    p.add_argument('--black',action='store_true');p.add_argument('--no-heal',action='store_true');p.add_argument('--save',type=Path);p.add_argument('--persist',action='store_true')
    p.add_argument('--creature',choices=('skitter','warden','eye'),default='warden');a=p.parse_args()
    if a.no_heal and a.case in ('duel','freight','crown','phase'):raise ValueError('This control deliberately heals the player; use the no-heal boss controls for a separate survival check')
    OUT.mkdir(parents=True,exist_ok=True)
    config=json.loads((ROOT/'work/playtest.json').read_text());actual=Path(config['battery_directory'])/'Spider-Man-WoS-modded.dsv'
    copied=OUT/'current-player-copy.dsv'
    if not copied.exists():copied.write_bytes(actual.read_bytes())
    k.TRAINING_SAVE=copied
    if a.case in ('arm-continue','arm-retry-continue'):
        from tools import emulator_smoke as emu,player_trace as pt
        if not a.save:raise ValueError('Continue requires the exact earned --save')
        before=w.sha256(a.save.read_bytes());script=[r for r in json.loads((ROOT/'reference/combat-inputs/oscorp-reload.json').read_text()) if r['start']<1400]
        cap=emu.run(a.rom,3100,{1800,3000},save_path=a.save,script=script,label=a.case+a.tag,ram_captures={1800,3000},core_options={b'melonds_jit_enable':b'enabled',b'melonds_jit_block_size':b'12'})
        rows=[]
        for frame in (1800,3000):
            ram=(cap/f'ram-{frame:05d}.bin').read_bytes();stats=w.u32(ram,k.STATS_POINTER-pt.BASE)-pt.BASE
            flags=int.from_bytes(ram[stats+0x1c:stats+0x44],'little');hero=pt.sample(ram)
            rows.append(dict(frame=frame,room=w.u32(ram,stats),victory=bool(flags>>142&1),crown_complete=bool(flags>>146&1),position=[v/4096 for v in hero['position_q12_candidate']]))
        checks=dict(continue_in_arm=all(row['room']==106 for row in rows),expected_victory_state=all(row['victory']==(a.case=='arm-continue') for row in rows),safe_checkpoint_position=abs(rows[-1]['position'][0]-36)<12,source_save_unchanged=w.sha256(a.save.read_bytes())==before)
        if a.case=='arm-retry-continue':checks['earned_crown_retained']=all(row['crown_complete'] for row in rows)
        report=dict(rom_sha256=w.sha256(a.rom.read_bytes()),passed=all(checks.values()),checks=checks,observations=rows,captures=str(cap),save=str(a.save),limits='Fresh unmodified candidate boot/Continue from the in-game earned private hoist save; no warp, flag, player or enemy placement fixture.')
        w.write_json(OUT/(a.case+a.tag+'.json'),report);print(json.dumps(report));return 0 if report['passed'] else 1
    # Fresh encounter state exists only in disposable RAM. Never edit the DSV.
    clear_flags={'engine':(140,),'hoist':(142,),'hoist-save':(142,),'conductor':(147,),'phase':(147,),'freight':(144,),'crown':(141,142,146),'crown-checkpoint':(142,),'pump':(245,)}.get(a.case,())
    if clear_flags:
        native=k._run
        def fresh(*args,**kw):
            original=kw['extra_hook'];done=False
            def hook(frame,lib):
                nonlocal done
                if not done and frame==-990:
                    ptr,ram=k.ram_of(lib);stats=w.u32(ram,k.STATS_POINTER-0x02000000)-0x02000000
                    flags=int.from_bytes(ram[stats+0x1c:stats+0x44],'little')
                    for bit in clear_flags:flags&=~(1<<bit)
                    ct.memmove(ptr+stats+0x1c,flags.to_bytes(40,'little'),40);done=True
                return original(frame,lib)
            kw['extra_hook']=hook;return native(*args,**kw)
        k._run=fresh
    if a.case in ('hoist','hoist-save','engine','freight','crown','crown-checkpoint','quay-air'):
        from tools import crane_walk as cw,midnight_rework_lab as lab
        pcm=[];rate=[0];runner=k._run
        def recorded(*args,**kw):
            original=kw['extra_hook']
            def hook(frame,lib):
                if frame>=0 and not rate[0]:
                    info=(ct.c_byte*40)();lib.retro_get_system_av_info.argtypes=[ct.c_void_p];lib.retro_get_system_av_info(ct.byref(info));rate[0]=round(struct.unpack_from('<d',bytes(info),32)[0])
                    lib._wos_audio_sink=lambda f,b:pcm.append(b) if f>=k.TRAINING_START else None
                return original(frame,lib)
            kw['extra_hook']=hook;return runner(*args,**kw)
        cw.OUT=OUT;lab.JIT=True;k._run=lab.static_warp_runner(recorded);k._run._midnight_static=True
        if a.case=='crown-checkpoint':
            class CheckpointWalker(cw.Walker):
                def tick(self,frame,lib):self.native_lib=lib;return super().tick(frame,lib)
                def do_checkpoint_snapshot(self,step,state,ptr,ram):
                    lib=self.native_lib
                    if lib.retro_get_memory_size(0)!=512:raise ValueError('Expected512-byte native SRAM')
                    path=OUT/('crown-checkpoint'+a.tag+'.sav');path.write_bytes(ct.string_at(lib.retro_get_memory_data(0),512));self.report['earned_save']=str(path)
                    self.record('native_pre_boss_save_requested',state.room==106 and bool(state.flags>>146&1) and not bool(state.flags>>142&1),state);return True
            cw.Walker=CheckpointWalker;cw.install()
            result=cw.run(a.rom,'crown-checkpoint'+a.tag,'AR_CraneCrown',1,[mw.wait(90),cw.nav('AR_CraneCrown',3,3000),mw.wait(120),
                mw.check('settled_arm_arrival',lambda state:state.room==106 and state.pos and state.pos[0]<60 and state.pos[1]<20),('travel',36,600),mw.wait(60),
                mw.hold('X',6),mw.wait(70),mw.hold('A',6),mw.wait(90),mw.hold('A',6),mw.wait(220),('checkpoint_snapshot',None)],preset=(140,141,146))
            result['checkpoint_fixture']='Focused continuation after separately qualified native Crown clear: initial arrival and earlier power/earned crew flags preset; native reciprocal route and settled sphere interaction. Fresh Continue is required to establish persistence.'
            w.write_json(OUT/('walk-crown-checkpoint'+a.tag+'.json'),result);return 0 if result['passed'] else 1
        if a.case=='quay-air':
            cw.install();result=cw.run(a.rom,'quay-air'+a.tag,'AR_CraneQuay',1,[mw.wait(1500)])
            if pcm:
                with wave.open(str(OUT/('quay-air'+a.tag+'.wav')),'wb') as stream:stream.setparams((2,2,rate[0],0,'NONE','not compressed'));stream.writeframes(b''.join(pcm))
            return 0 if result['passed'] else 1
        if a.case in ('freight','crown'):
            from tools import crane_creature_lab as creatures
            counterplay=[]
            if a.case=='crown':
                pursuit=creatures.pursuit_buttons;escape={}
                def take_back(frame,state,enemy,kit=False):
                    dx=enemy['position'][0]/4096-state.pos[0];dy=enemy['position'][1]/4096-state.pos[1]
                    near=abs(dx)<22 and abs(dy)<16
                    if 'start' not in escape and near and frame>=escape.get('next',0) and (enemy.get('state')==51 or state.pos[0]<30 or state.pos[0]>306):
                        escape.update(start=frame,way='Right' if dx>0 else 'Left')
                        counterplay.append(dict(frame=frame,position=state.pos,enemy_state=enemy.get('state'),direction=escape['way'],input='Native jump/evade around a close foe or away from an exit'))
                    if 'start' in escape:
                        age=frame-escape['start']
                        if age<65:
                            buttons={escape['way']}
                            if age<6:buttons.add('R')
                            if 6<=age<38:buttons.add('B')
                            if 30<=age<60 and frame%8<3:buttons.add('Y')
                            return buttons
                        escape.pop('start');escape['next']=frame+180
                    return pursuit(frame,state,enemy,kit)
                creatures.pursuit_buttons=take_back
            # Live budget3 is in native cost units: Ballast costs2, so this
            # composition deliberately supports two simultaneous species.
            kwargs=dict(room='AR_CraneCrown',progress_flag=146,minimum_distinct=3,preset=(140,),approach_save=OUT/('crown-earned'+a.tag+'.sav')) if a.case=='crown' else dict(minimum_distinct=2)
            passed=creatures.duel(a.rom,'mixed',black=a.black,kit=True,observe=300,timeout=14000,tag=a.tag,resilient=True,**kwargs)
            if a.case=='crown':
                report=OUT/'creatures'/('creature-duel-mixed-crown-'+('black' if a.black else 'red')+'-kit'+a.tag+'-'+w.sha256(a.rom.read_bytes())[:8]+'.json')
                data=json.loads(report.read_text());data['native_counterplay_inputs']=counterplay
                data['limits']+=' Crown arrival presets earlier power140; crew/hoist flags start clear. Driver uses native jump/evade to reposition and reciprocal inputs after an accidental retreat; enemy HP/positions/states remain native. Optional ending earns the approach save through the real unlocked hoist door.'
                w.write_json(report,data)
            if pcm:
                with wave.open(str(OUT/(a.case+a.tag+'.wav')),'wb') as stream:stream.setparams((2,2,rate[0],0,'NONE','not compressed'));stream.writeframes(b''.join(pcm))
            return 0 if passed else 1
        if a.case.startswith('hoist'):
            if a.case=='hoist-save':
                class SaveWalker(cw.Walker):
                    def tick(self,frame,lib):self.native_lib=lib;return super().tick(frame,lib)
                    def do_navigate(self,step,state,ptr,ram):
                        if step[1:3]==('AR_LongArm',1) and state.room==106 and state.pos and state.pos[0]<40 and state.pos[1]<12:
                            self.record('native_return_to_approach_save',True,state);return True
                        result=super().do_navigate(step,state,ptr,ram)
                        if not result and state.pos and any(abs(enemy['position'][0]/4096-state.pos[0])<14 and abs(enemy['position'][1]/4096-state.pos[1])<12 for enemy in state.enemies):self.buttons.add('Y')
                        return result
                    def do_save_snapshot(self,step,state,ptr,ram):
                        lib=self.native_lib
                        if lib.retro_get_memory_size(0)!=512:raise ValueError('Expected512-byte native SRAM')
                        path=OUT/('arm-earned'+a.tag+'.sav');path.write_bytes(ct.string_at(lib.retro_get_memory_data(0),512))
                        self.report['earned_save']=str(path);self.record('earned_hoist_save',state.room==106 and bool(state.flags>>142&1),state);return True
                cw.Walker=SaveWalker;run=cw.run
                def save_run(rom,label,start,spawn,steps,preset=()):
                    steps=[*steps,cw.nav('AR_LongArm',1,3000),mw.wait(90),mw.hold('X',6),mw.wait(70),mw.hold('A',6),mw.wait(90),mw.hold('A',6),mw.wait(220),('save_snapshot',None)]
                    return run(rom,label+'-save',start,spawn,steps,preset)
                cw.run=save_run
            args=['machine','--rom',str(a.rom),'--tag='+a.tag,'--combat-frames','10000','--purchased-kit']
            if a.no_heal:args.append('--no-heal')
            if a.black:args.append('--black')
            cw.main(args)
            if pcm:
                with wave.open(str(OUT/('hoist'+a.tag+'.wav')),'wb') as stream:stream.setparams((2,2,rate[0],0,'NONE','not compressed'));stream.writeframes(b''.join(pcm))
            label=('hoist-'+('black' if a.black else 'red') if a.no_heal else 'hoist-flow')+'-kit'+a.tag+('-save' if a.case=='hoist-save' else '')
            report=json.loads((OUT/('walk-'+label+'.json')).read_text());return 0 if report['passed'] else 1
        cw.install();cw.MACHINE_DATA.update(cw.machine_records(a.rom))
        result=cw.run(a.rom,'engine'+a.tag,'AR_EngineHouse',1,[mw.wait(120),mw.check('power_initially_off',lambda state:not (state.flags>>140&1)),('travel',142,1600),mw.wait(45),mw.hold('X',6),mw.wait(240),mw.mark('powered'),mw.check('power_earned',mw.flag(140))])
        if pcm:
            with wave.open(str(OUT/('engine'+a.tag+'.wav')),'wb') as stream:stream.setparams((2,2,rate[0],0,'NONE','not compressed'));stream.writeframes(b''.join(pcm))
        print(json.dumps(dict(case=a.case,passed=result['passed'],captures=result['captures'])));return 0 if result['passed'] else 1
    forge.OUT=OUT;q.OUT=OUT;forge.install(a.rom,a.capture_every);q.RUN_TAG=a.tag
    if a.case=='conductor-continue':result=q.continue_earned(a.rom)
    elif a.case=='conductor':result=q.combat(a.rom,black=a.black,persist=a.persist,heal=not a.no_heal)
    elif a.case=='phase':result=q.run(a.rom,'conductor-phase','ML_Venom',2,[mw.wait(120),('phase_bait',9000),mw.wait(180),('combat',14000)],combat=True,heal=True)
    elif a.case=='station-air':result=q.run(a.rom,'station-air','ML_Entry',1,[mw.wait(1500)],combat=True)
    elif a.case=='duel':
        # The new post-pass owns per-room pattern/goal tables. Older duel
        # fixtures target the previous tables and no longer isolate a roster.
        metadata=json.loads(a.rom.with_suffix('.build.json').read_text())['chapter_spectacle']['scripted_runtime']
        from tools import player_trace as pt,midnight_rework_lab as lab
        pattern=metadata['patterns']['78'];goals=metadata['goal_table'];kind={'skitter':21,'warden':36,'eye':20}[a.creature]
        native=k._run
        def isolated(*args,**kw):
            original=kw['extra_hook']
            def hook(frame,lib):
                if frame+k.TRAINING_START>=2040:
                    ptr,ram=k.ram_of(lib);ct.memmove(ptr+pattern-pt.BASE,bytes((kind,)*4),4)
                    for row in range(19):
                        at=goals-pt.BASE+row*20;room=w.u32(ram,at)
                        if not room:break
                        if room==78:
                            cost=2 if kind==36 else 1
                            for column in (4,8,12):ct.memmove(ptr+w.u32(ram,at+column)-pt.BASE,struct.pack('<2I',cost*4096,cost*4096),8)
                            break
                return original(frame,lib)
            kw['extra_hook']=hook;return native(*args,**kw)
        isolated._midnight_static=True;k._run=isolated
        original_bait=lab.Walker.do_bait
        def contextual_bait(self,step,state,ptr,ram):
            contact=self.report.get('contact_move_calls',[])
            # Toll march has a deliberate16..18-unit engagement window. Bait
            # with controller movement at that distance; never force an action.
            if step[1]=='warden' and len(contact)==28 and not contact[18] and state.enemies and state.pos:
                if self.t>=step[2]:return self.timeout(step,state,step[2],'contextual Toll march bait')
                enemy=state.enemies[0];dx=enemy['position'][0]/4096-state.pos[0];dy=enemy['position'][1]/4096-state.pos[1]
                if abs(dy)<10:
                    self.buttons.clear()
                    if abs(dx)<16.7:self.buttons.add('Left' if dx>0 else 'Right')
                    elif abs(dx)>17.7:self.buttons.add('Right' if dx>0 else 'Left')
                    return False
            return original_bait(self,step,state,ptr,ram)
        lab.Walker.do_bait=contextual_bait
        result=q.duel(a.rom,a.creature)
        result['isolation_fixture']='Disposable new room78 pattern/goal tables only; native actor HP/AI/position. Player healing/purchases. Warden bait uses native inputs at17 units.'
        w.write_json(OUT/('walk-duel-'+a.creature+a.tag+'.json'),result)
    elif a.case=='pump':
        result=q.run(a.rom,'pump','ML_NestShaft',2,[mw.wait(90),mw.check('pump_initially_unstable',lambda state:not (state.flags>>245&1)),('travel',110,1800),mw.wait(45),mw.hold('X',6),mw.wait(240),mw.mark('pumps_stable'),mw.check('pump_stabilized',mw.flag(245))],combat=True,heal=not a.no_heal)
    else:
        spawn,target={'terminal':(1,140),'terminal-reverse':(2,200),'terminal-upper':(3,140),'terminal-roof':(1,180)}[a.case]
        steps=[mw.wait(90),('travel',target,1800),mw.wait(1200)]
        if a.case=='terminal-roof':
            spawn=3;steps=[mw.wait(90),('land',54,37,1400),('land',104,30,1400),('land',180,30,1400),mw.wait(900)]
        if a.black:steps=[mw.hold('L',6),mw.wait(90),mw.check('black_form_confirmed',lambda state:state.black==1),*steps]
        result=q.run(a.rom,a.case,'ML_Station',spawn,steps,combat=True,black=a.black,heal=not a.no_heal)
        trace=result.get('forge_trace',[]);styles={}
        for style in ('skitter','warden','eye'):
            rows=[(r,e) for r in trace for e in r['enemies'] if e['style']==style and r.get('player')]
            if not rows:continue
            styles[style]=dict(observations=len(rows),maximum_height=max(e['position'][1]/4096 for r,e in rows),
                attack_samples=sum(e['state']==15 for r,e in rows),
                closest=sum(1 for r,e in rows if abs(r['player'][0]-e['position'][0]/4096)<14 and abs(r['player'][1]-e['position'][1]/4096)<12),
                min_distance=min(abs(r['player'][0]-e['position'][0]/4096) for r,e in rows))
        result['pursuit_observation']=styles
        w.write_json(OUT/('pursuit-'+a.case+a.tag+'.json'),dict(rom_sha256=result['rom_sha256'],passed=result['passed'],styles=styles,
            report=str((OUT/('walk-'+a.case+a.tag+'.json')).relative_to(ROOT)),
            limits='Fresh copied-save arrival; native mixed full-HP roster and controller movement; player healing/purchases as labelled. Observation, not difficulty or a player verdict.'))
    print(json.dumps(dict(case=a.case,passed=result['passed'],pursuit=result.get('pursuit_observation'),captures=result.get('captures'))))
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
