"""Copied-save gameplay controls with native boss-meter and PCM observations."""
import argparse,ctypes as ct,json,os,struct,sys,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import midnight_rebuild_lab as prior,midnight_rework_lab as lab
from tools import kit_lab as k,wos_tool as w,playtest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('case');p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--tag',default='');p.add_argument('--black',action='store_true');p.add_argument('--no-heal',action='store_true')
    p.add_argument('--persist',action='store_true');p.add_argument('--capture-every',type=int,default=12)
    p.add_argument('--save',type=Path,help='Explicit earned research save for a fresh Continue')
    p.add_argument('--reactive',action='store_true',help='Use native R inputs in response to authored boss tells');a=p.parse_args()
    out=Path(os.environ.get('WOS_CHAPTER_LAB_OUT',ROOT/'work/midnight-epic/qualification')).resolve()
    if not out.is_relative_to((ROOT/'work').resolve()):raise ValueError('Private evidence must stay in work/')
    out.mkdir(parents=True,exist_ok=True);os.environ['WOS_CHAPTER_LAB_OUT']=str(out)
    if a.save:
        earned=a.save.resolve()
        if not earned.is_relative_to((ROOT/'work').resolve()) or not earned.is_file():raise ValueError('Earned save must be an existing private file under work/')
        (out/'conductor-earned.sav').write_bytes(earned.read_bytes())
    actual=playtest.current_save();before=actual.read_bytes()
    meta=json.loads(a.rom.with_suffix('.build.json').read_text());rt=meta['midnight_encore']['runtime']
    native_tick=lab.Walker.tick;rows=[];pcm=[];rate=[0];reports=[]
    def tick(self,frame,lib):
        result=native_tick(self,frame,lib)
        if frame>=0 and frame%6==0 and self.last_state:
            _,ram=k.ram_of(lib);observed=struct.unpack_from('<4I',ram,rt['observed']-0x02000000)
            state=self.last_state;rows.append(dict(frame=frame,room=state.room,hp=state.hp,player=state.pos,actor=observed[0],meter=observed[1],
                displayed_hp=observed[2],displayed_max=observed[3],owned=w.u32(ram,rt['owned']-0x02000000),
                enemies=[dict(actor=e['actor'],hp=e['hp'],max=e['max'],action=e['action'],state=e['state']) for e in state.enemies]))
            if not reports:reports.append(self.report)
        return result
    lab.Walker.tick=tick
    if a.reactive:
        from tools import midnight_encore_motion as motion
        native_combat=lab.Walker.do_combat
        def reactive(self,step,state,ptr,ram):
            result=native_combat(self,step,state,ptr,ram)
            if result:return result
            if state.pos and state.enemies:
                e=state.enemies[0]
                if e['state']==15:
                    move=next((m for m in motion.MOVES['conductor'] if m.action==e['action']),None)
                    if move:
                        mot=w.u32(ram,e['actor']-0x02000000+0x30)-0x02000000;clock=w.u32(ram,mot+0x178)
                        for ci,(start,end) in enumerate(move.contacts):
                            if start-4<=clock<start and self.scratch.get('reactive_window')!=(e['action'],ci):
                                dx=e['position'][0]/4096-state.pos[0];way='Right' if dx>0 else 'Left'
                                button='B' if move.kind=='fugue' or move.kind in ('crownfall','verdict') and ci==1 else 'R'
                                self.scratch.update(reactive_window=(e['action'],ci),reactive_start=state.frame,reactive_way=way,reactive_button=button)
                                self.report.setdefault('reactive_inputs',[]).append(dict(frame=state.frame,action=e['action'],clock=clock,input=button,direction=way))
                        age=state.frame-self.scratch.get('reactive_start',-100)
                        if 0<=age<27:
                            self.buttons.difference_update(('Left','Right','A','Y'));self.buttons.add(self.scratch['reactive_way'])
                            button=self.scratch['reactive_button']
                            if age<(18 if button=='B' else 6):self.buttons.add(button)
                else:self.scratch.pop('reactive_window',None)
            return False
        lab.Walker.do_combat=reactive
    native_run=k._run
    def recorded(*args,**kw):
        hook=kw['extra_hook']
        def audio(frame,lib):
            if frame>=0 and not rate[0]:
                info=(ct.c_byte*40)();lib.retro_get_system_av_info.argtypes=[ct.c_void_p];lib.retro_get_system_av_info(ct.byref(info))
                rate[0]=round(struct.unpack_from('<d',bytes(info),32)[0]);lib._wos_audio_sink=lambda f,b:pcm.append(b) if f>=k.TRAINING_START else None
            return hook(frame,lib)
        kw['extra_hook']=audio;return native_run(*args,**kw)
    k._run=recorded
    sys.argv=[sys.argv[0],a.case,'--rom',str(a.rom),'--tag='+a.tag,'--capture-every',str(a.capture_every)]
    for flag,on in (('--black',a.black),('--no-heal',a.no_heal),('--persist',a.persist)):
        if on:sys.argv.append(flag)
    if a.case=='native-boss':
        from types import SimpleNamespace
        from tools import midnight_walk as mw,midnight_chapter as chapter
        copied=out/'current-player-copy.dsv';copied.write_bytes(before);k.TRAINING_SAVE=copied
        raw=a.rom.read_bytes();fs=next(e for e in w.nitrofs_entries(raw) if e['name']=='Glob.bin');glob=raw[fs['start']:fs['end']]
        offsets,names,_=w.parse_glob(glob);i=names.index('Hive_Map09_app.obj');native_obj=glob[offsets[i]:offsets[i+1]]
        chapter.BY_NAME={**chapter.BY_NAME,'NativeVenom':SimpleNamespace(index=25)};old_objects=mw.rom_objects
        mw.rom_objects=lambda rom:{**old_objects(rom),25:native_obj};mw.OUT=out
        k._run=lab.static_warp_runner(k._run);k._run._midnight_static=True
        native_rows=[]
        class NativeWalker(lab.Walker):
            combat=True;heal=True
            def tick(self,frame,lib):
                if frame==-990:
                    ptr,ram=k.ram_of(lib);stats=w.u32(ram,k.STATS_POINTER-0x02000000)-0x02000000
                    flags=int.from_bytes(ram[stats+0x1c:stats+0x44],'little')&~(1<<175)
                    ct.memmove(ptr+stats+0x1c,flags.to_bytes(40,'little'),40);ct.memmove(ptr+stats+0x48,b'\x29',1)
                result=super().tick(frame,lib)
                if frame>=0 and frame%30==0:
                    _,ram=k.ram_of(lib);bars=[];pos=0
                    while (at:=ram.find(struct.pack('<I',0x0213c81c),pos))>=0:
                        pos=at+4
                        if at%4 or at+0x24>len(ram):continue
                        words=struct.unpack_from('<9I',ram,at)
                        if 0<words[3]<=words[4]<0x1000000 and 0x02000000<=words[1]<0x02400000:bars.append(dict(address=at+0x02000000,hp=words[3],maximum=words[4]))
                    native_rows.append(dict(frame=frame,room=self.last_state.room if self.last_state else None,bars=bars,custom_owned=w.u32(ram,rt['owned']-0x02000000)))
                return result
        mw.Walker=NativeWalker
        mw.run_child(a.rom,'native-boss'+a.tag,('NativeVenom',0,(),[mw.wait(180),mw.hold('Right',100),mw.wait(1200)]))
        report=json.loads((out/('walk-native-boss'+a.tag+'.json')).read_text())
        visible=[r for r in native_rows if r['bars']]
        report.update(native_hud_observations=native_rows,native_hud_visible=bool(visible),custom_hud_stayed_inactive=all(not r['custom_owned'] for r in native_rows),
            fixture='Native Hive_Map09 arrival, copied-save mission41 and native Venom-dead flag cleared before entry. Player healing. Native Mega Venom actor/script/HUD, no enemy-state or HP writes.')
        report['passed']=bool(report['passed'] and visible and report['custom_hud_stayed_inactive'])
        w.write_json(out/('native-boss'+a.tag+'.json'),report);result=0 if report['passed'] else 1
    elif a.case in ('pressure','counterplay'):
        from tools import chapter_renewal_lab as q,creature_forge_lab as forge,midnight_walk as mw
        copied=out/'current-player-copy.dsv';copied.write_bytes(before);k.TRAINING_SAVE=copied
        q.OUT=out;forge.OUT=out;q.RUN_TAG=a.tag;forge.install(a.rom,a.capture_every)
        runner=k._run
        def fresh(*args,**kw):
            hook=kw['extra_hook'];done=False
            def clear(frame,lib):
                nonlocal done
                if frame==-990 and not done:
                    ptr,ram=k.ram_of(lib);stats=w.u32(ram,k.STATS_POINTER-0x02000000)-0x02000000
                    flags=int.from_bytes(ram[stats+0x1c:stats+0x44],'little')&~(1<<147)
                    ct.memmove(ptr+stats+0x1c,flags.to_bytes(40,'little'),40);done=True
                return hook(frame,lib)
            kw['extra_hook']=clear;return runner(*args,**kw)
        fresh._midnight_static=True;k._run=fresh
        def watch(self,step,state,ptr,ram):
            self.on['alive']=False;self.buttons.clear()
            if self.t>=step[1]:self.on['alive']=True;return True
            if state.hp<=0:return self.timeout(step,state,self.t,'passive boss study defeat')
            if state.pos and state.enemies:
                e=state.enemies[0];dx=e['position'][0]/4096-state.pos[0]
                mot=w.u32(ram,e['actor']-0x02000000+0x30)-0x02000000;clock=w.u32(ram,mot+0x178)
                previous=self.scratch.get('last_hp',state.hp);self.scratch['last_hp']=state.hp
                if state.hp<previous:
                    self.report.setdefault('pressure_damage',[]).append(dict(frame=state.frame,action=e['action'],clock=clock,amount=previous-state.hp))
                if e['state']!=15:
                    self.scratch.pop('dodge',None)
                    stats=w.u32(ram,k.STATS_POINTER-0x02000000)-0x02000000;top=w.u32(ram,stats+0x88)
                    if 0<state.hp<top:
                        ct.memmove(ptr+stats+0x84,struct.pack('<I',top),4)
                        self.report.setdefault('pressure_between_program_refills',[]).append(state.frame)
                    hits={r['action'] for r in self.report.get('pressure_damage',[])}
                    wanted=35 if 30 not in hits else 11
                    if abs(dx)>wanted+1:self.buttons.add('Right' if dx>0 else 'Left')
                    if abs(dx)<wanted-1:self.buttons.add('Left' if dx>0 else 'Right')
                    if state.pos[0]<20:self.buttons.discard('Left');self.buttons.add('Right')
                    if state.pos[0]>204:self.buttons.discard('Right');self.buttons.add('Left')
                elif a.case=='counterplay':
                    from tools import midnight_encore_motion as motion
                    move=next((m for m in motion.MOVES['conductor'] if m.action==e['action']),None)
                    if move and move.contacts[0][0]-5<=clock<move.contacts[0][0] and 'dodge' not in self.scratch:
                        self.scratch['dodge']=(state.frame,'Right' if dx>0 else 'Left')
                        self.report.setdefault('native_counterplay',[]).append(dict(frame=state.frame,action=e['action'],clock=clock,input='R',direction=self.scratch['dodge'][1]))
                    if 'dodge' in self.scratch:
                        started,way=self.scratch['dodge'];age=state.frame-started
                        if age<30:self.buttons.add(way)
                        if age<6:self.buttons.add('R')
            return False
        lab.Walker.do_watch_boss=watch
        phase=lab.Walker.do_phase_bait
        def healed_phase(self,*args):self.on['alive']=True;return phase(self,*args)
        lab.Walker.do_phase_bait=healed_phase
        switched=[mw.hold('L',6),mw.wait(90)] if a.black else []
        data=q.run(a.rom,a.case,'ML_Venom',2,[mw.wait(120),*switched,('travel',90,1800),('watch_boss',2100),('phase_bait',9000),('watch_boss',1800),('combat',14000)],combat=True,heal=True)
        data['limits']='Copied actual save, arrival and earned-flag reset fixtures; full native enemy HP. Between-program player refills during passive observations; per-frame player healing only for actual damage progression/clear. No forced boss action or HP. R is native input.'
        w.write_json(out/('boss-pressure'+a.tag+'.json'),data);result=0 if data['passed'] else 1
    else:result=prior.main()
    own=[r for r in rows if r['owned'] and r['actor'] and r['meter']]
    matches=[r for r in own if any(e['actor']==r['actor'] and abs(e['hp']-r['displayed_hp'])<=8192 and e['max']==r['displayed_max'] for e in r['enemies'])]
    if pcm:
        with wave.open(str(out/('mixed-'+a.case+a.tag+'.wav')),'wb') as f:f.setparams((2,2,rate[0],0,'NONE','not compressed'));f.writeframes(b''.join(pcm))
    report=dict(rom_sha256=w.sha256(a.rom.read_bytes()),case=a.case,tag=a.tag,rows=rows,native_meter_samples=len(own),matching_health_samples=len(matches),
        distinct_displayed_hp=sorted({r['displayed_hp'] for r in own}),source_battery_unchanged=actual.read_bytes()==before,
        limits='Read-only meter observation around copied-save chapter lab. Underlying report owns initial arrival/progression/purchase and healing fixtures; PCM captured from emulator mixer. HP can advance within the observed native frame.')
    w.write_json(out/('hud-'+a.case+a.tag+'.json'),report)
    print(json.dumps({key:val for key,val in report.items() if key not in ('rows','distinct_displayed_hp','limits')}))
    return result


if __name__=='__main__':raise SystemExit(main())
