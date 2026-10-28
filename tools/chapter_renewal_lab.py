"""Copied-save, native-input qualification of the compact chapter revision."""
import argparse,json,sys,subprocess,struct,ctypes as ct,wave,os
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import chapter_renewal_rooms as rooms,midnight_chapter as ch,midnight_rooms as mr
from tools import midnight_rework_lab as lab,midnight_walk as mw,crane_walk as cw,wos_tool as w
from tools import kit_lab as k,player_trace as p,midnight_rework_boss as boss
OUT=Path(os.environ.get('WOS_CHAPTER_LAB_OUT',ROOT/'work/dual-rework')).resolve()
if not OUT.is_relative_to((ROOT/'work').resolve()):raise ValueError('Chapter lab output must remain under work/')
CRANE_OUT=OUT/'crane' if os.environ.get('WOS_CHAPTER_LAB_OUT') else ROOT/'work/crane-row'
ISOLATE=None
RUN_TAG=''
NATIVE_ROSTER=lab.Walker.do_roster
NATIVE_LAND=lab.Walker.do_land_if_below
NATIVE_NAV=lab.Walker.do_navigate

def configure_rooms(rom):
    """Use the candidate's actual envelopes/ports, retaining old lab defaults."""
    global rooms
    from tools import owned_player_lab
    owned_player_lab.install()
    copied_save=os.environ.get('WOS_CHAPTER_LAB_SAVE')
    if copied_save:
        path=Path(copied_save).resolve()
        if not path.is_relative_to((ROOT/'work').resolve()) or not path.is_file():raise ValueError('Chapter lab save must be an existing private copy under work/')
        k.TRAINING_SAVE=path
    metadata=json.loads(Path(rom).with_suffix('.build.json').read_text(encoding='utf-8'))
    if metadata.get('midnight_reliability',{}).get('rooms'):
        from tools import midnight_reliability_rooms
        rooms=midnight_reliability_rooms
    elif metadata.get('midnight_rebuild',{}).get('rooms'):
        from tools import midnight_rebuild_rooms
        rooms=midnight_rebuild_rooms
    else:
        from tools import chapter_renewal_rooms
        rooms=chapter_renewal_rooms

def land_with_retry(self,step,state,ptr,ram):
    if state.room!=92 and state.pos and state.pos[1]<step[2]-32:
        earlier=[i for i,s in enumerate(self.steps[:self.i]) if s[0]=='land_if_below' and state.pos[1]+5<s[2]<=state.pos[1]+27]
        if earlier:
            self.report.setdefault('native_climb_retries',[]).append([state.frame,self.i,earlier[-1]])
            if len(self.report['native_climb_retries'])>12:return self.timeout(step,state,self.t,'climb retry limit')
            self.i=earlier[-1]-1;return True
    return NATIVE_LAND(self,step,state,ptr,ram)

def navigate_with_jump(self,step,state,ptr,ram):
    result=NATIVE_NAV(self,step,state,ptr,ram)
    if not result and state.state==9 and self.t%32<12:self.buttons.add('B')
    return result
lab.Walker.do_land_if_below=land_with_retry
lab.Walker.do_navigate=navigate_with_jump

def roster_with_escape(self,step,state,ptr,ram):
    """Use a real retreat/jump when close pursuit stalls on another actor."""
    last=self.scratch.get('roster_position')
    self.scratch['roster_position']=state.pos
    stalled=last is not None and state.pos is not None and max(abs(a-b) for a,b in zip(last,state.pos))<.05
    self.scratch['roster_still']=self.scratch.get('roster_still',0)+1 if stalled else 0
    if self.scratch['roster_still']>90 and 'roster_escape' not in self.scratch:
        way='Left' if state.pos[0]>80 else 'Right'
        self.scratch['roster_escape']=(state.frame,way)
        self.report.setdefault('native_escape_inputs',[]).append([state.frame,state.pos,state.state,way])
    if 'roster_escape' in self.scratch:
        start,way=self.scratch['roster_escape'];age=state.frame-start
        if age<90:
            self.buttons.clear();self.buttons.add(way)
            if age<45:self.buttons.add('B')
            if age<12:self.buttons.add('R')
            return False
        self.scratch.pop('roster_escape');self.scratch['roster_still']=0
    return NATIVE_ROSTER(self,step,state,ptr,ram)
lab.Walker.do_roster=roster_with_escape

def bait(self,step,state,ptr,ram):
    style,timeout=step[1:]
    index=('maw','ballast','spore','skitter','warden','eye','conductor').index(style)
    counts=self.report.get('attack_sequencer_calls',[0]*7)
    contact=self.report.get('contact_move_calls')
    contact_ready=contact is None or all(contact[index*4:index*4+3])
    if counts[index]>=3 and contact_ready:
        self.record('three_authored_attack_selections',True,state,style=style,selections=counts[index]);return True
    if self.t>=timeout:return self.timeout(step,state,timeout,'bait authored pattern '+style)
    self.buttons.clear()
    if state.enemies and state.pos:
        enemy=min(state.enemies,key=lambda e:abs(e['position'][0]/4096-state.pos[0])+abs(e['position'][1]/4096-state.pos[1]))
        ex,ey=(v/4096 for v in enemy['position']);dx,dy=ex-state.pos[0],ey-state.pos[1]
        if abs(dx)>7 or abs(dy)>10:
            from tools.crane_creature_lab import pursuit_buttons
            self.buttons.update(pursuit_buttons(state.frame,state,enemy,kit=False));self.buttons.difference_update(('Y','A','R'))
    return False
lab.Walker.do_bait=bait

def install():
    names=tuple(rooms.BY_ID[i] for i in range(76,96))
    lab.rooms=SimpleNamespace(NAMES=names,SPECS=rooms.SPECS,SIZES=tuple(rooms.SIZES.get(i,(112,72)) for i in range(76,96)),
        TURBINE_STEPS=rooms.STEPS[83],CROWN_STEPS=(),LANDINGS={rooms.BY_ID[i]:v for i,v in rooms.STEPS.items()},manual=lambda n,g:True)
    lab.OUT=OUT;lab.JIT=True;lab.SUBSTATION_LANDINGS={};ch.LINKS=rooms.LINKS
    lab.install()

def report_runtime(rom,result):
    metadata=json.loads(Path(rom).with_suffix('.build.json').read_text())
    meta=metadata.get('creature_forge') or metadata['chapter_renewal']
    # Reads at the final frame, copied to the report by the observer below.
    return meta

def run(rom,label,start,spawn,steps,*,combat=False,black=False,heal=True):
    label+=RUN_TAG
    configure_rooms(rom);install();meta=report_runtime(rom,None)
    original=lab.Walker.tick;pcm=[];rate=[0]
    oldmeta=json.loads(Path(rom).with_suffix('.build.json').read_text())['midnight_rework']['creatures']
    def observed(self,frame,lib):
        if ISOLATE is not None and frame+k.TRAINING_START>=2040:
            ptr,_=k.ram_of(lib);idx=('skitter','warden','eye').index(ISOLATE);cost=2 if idx==1 else 1
            ct.memmove(ptr+oldmeta['state']-p.BASE,struct.pack('<2I',78,idx),8)
            ct.memmove(ptr+oldmeta['goals']['patrol']-p.BASE,struct.pack('<2I',cost*4096,cost*4096),8)
            ct.memmove(ptr+oldmeta['goals']['upper']-p.BASE,bytes(8),8)
        if combat and frame>=0 and not rate[0]:
            info=(ct.c_byte*40)();lib.retro_get_system_av_info.argtypes=[ct.c_void_p];lib.retro_get_system_av_info(ct.byref(info))
            rate[0]=round(struct.unpack_from('<d',bytes(info),32)[0]);lib._wos_audio_sink=lambda f,b:pcm.append(b) if f>=k.TRAINING_START else None
        original(self,frame,lib)
        if frame>=0 and frame%12==0:
            _,ram=k.ram_of(lib);rt=meta['runtime']
            self.report['attack_sequencer_calls']=list(struct.unpack_from('<7I',ram,rt['attack_counters']-p.BASE))
            self.report['voice_event_calls']=list(struct.unpack_from('<7I',ram,rt['voice_counters']-p.BASE))
            self.report['attack_slots']=list(struct.iter_unpack('<8I',ram[rt['slots']-p.BASE:rt['slots']-p.BASE+1024]))
            if frame==600:
                (OUT/('observed-'+label+'.ram')).write_bytes(ram)
            if frame%300==0 and combat:
                state=self.last_state
                w.write_json(OUT/('live-'+label+'.json'),dict(frame=frame,player=state.pos if state else None,
                    state=state.state if state else None,attacks=self.report['attack_sequencer_calls'],
                    enemies=state.enemies if state else []))
    lab.Walker.tick=observed
    try:result=lab.run(rom,label,start,spawn,steps,preset=(boss.DEFEATED,) if not combat else (),combat=combat,heal=heal)
    finally:lab.Walker.tick=original
    if pcm:
        with wave.open(str(OUT/(label+'.wav')),'wb') as stream:
            stream.setnchannels(2);stream.setsampwidth(2);stream.setframerate(rate[0]);stream.writeframes(b''.join(pcm))
    return result

def duel(rom,style):
    if style in ('skitter','warden','eye'):
        global ISOLATE
        ISOLATE=style
        return run(rom,'duel-'+style,'ML_Station',1,[mw.wait(90),('travel',100,1400),('bait',style,6000),('roster',14000),mw.wait(180)],combat=True)
    from tools import crane_creature_lab as creatures
    meta=report_runtime(rom,None);proof={};pcm=[];rate=[0];native=k._run
    def observed_runner(*args,**kw):
        old=kw['extra_hook']
        def observed(frame,lib):
            result=old(frame,lib)
            if frame>=0:
                if not rate[0]:
                    info=(ct.c_byte*40)();lib.retro_get_system_av_info.argtypes=[ct.c_void_p];lib.retro_get_system_av_info(ct.byref(info))
                    rate[0]=round(struct.unpack_from('<d',bytes(info),32)[0]);lib._wos_audio_sink=lambda f,b:pcm.append(b) if f>=k.TRAINING_START else None
                if frame%12==0:
                    _,ram=k.ram_of(lib);rt=meta['runtime']
                    proof['attack_sequencer_calls']=list(struct.unpack_from('<7I',ram,rt['attack_counters']-p.BASE))
                    proof['voice_event_calls']=list(struct.unpack_from('<7I',ram,rt['voice_counters']-p.BASE))
                    if 'move_counters' in rt:
                        packed=struct.unpack_from('<28I',ram,rt['move_counters']-p.BASE)
                        proof['move_calls']=[v&65535 for v in packed]
                        proof['contact_move_calls']=[v>>16 for v in packed]
                        proof['contact_cue_calls']=w.u32(ram,rt['contact_cues']-p.BASE)
                    proof.setdefault('slots',[]).append([frame,list(struct.iter_unpack('<8I',ram[rt['slots']-p.BASE:rt['slots']-p.BASE+1024]))])
            return result
        kw['extra_hook']=observed;return native(*args,**kw)
    lab.JIT=True;k._run=lab.static_warp_runner(observed_runner)
    passed=creatures.duel(rom,style,kit=True,observe=900,timeout=12000,tag='-renewal'+RUN_TAG,bait_runtime=meta['runtime'],bait_index=('maw','ballast','spore').index(style))
    proof.update(passed=passed,rom_sha256=w.sha256(Path(rom).read_bytes()))
    w.write_json(OUT/('duel-'+style+'-proof'+RUN_TAG+'.json'),proof)
    if pcm:
        with wave.open(str(OUT/('duel-'+style+RUN_TAG+'.wav')),'wb') as stream:
            stream.setnchannels(2);stream.setsampwidth(2);stream.setframerate(rate[0]);stream.writeframes(b''.join(pcm))
    return proof

def pair(rom,name,g):
    configure_rooms(rom);install();return lab.pair(rom,name,g)

def combat(rom,roster=False,black=False,persist=False,heal=True):
    steps=[mw.wait(120)]
    if black:steps.extend((mw.hold('L',6),mw.wait(90)))
    if roster:
        steps.extend((('roster',14000),mw.wait(120)))
        return run(rom,'terminal-roster','ML_Station',1,steps,combat=True)
    steps.extend((('combat',14000),mw.wait(180),cw.nav('ML_Venom',1,1400),mw.wait(90),mw.check('earned_exit_to_save',lambda s:s.room==87)))
    if persist:steps.extend((mw.walk('sanctuary_save',56,600),mw.hold('X',6),mw.wait(70),mw.hold('A',6),mw.wait(90),mw.hold('A',6),mw.wait(220),('snapshot','save')))
    else:steps.extend((cw.nav('ML_NestShrine',2,1400),mw.wait(90),mw.check('boss_cleared_on_return',lambda s:s.room==89 and bool(s.flags>>147&1) and not s.enemies)))
    return run(rom,'conductor-'+('black' if black else 'red')+('-save' if persist else '' if heal else '-no-refill'),'ML_Venom',2,steps,combat=True,heal=heal)

def continue_earned(rom):
    from tools import emulator_smoke as emu
    save=OUT/'conductor-earned.sav';before=w.sha256(save.read_bytes());sha=w.sha256(Path(rom).read_bytes())
    script=[r for r in json.loads((ROOT/'reference/combat-inputs/oscorp-reload.json').read_text()) if r['start']<1400]
    # A Continue can use the native record's entry spawn rather than the save
    # sphere's current X. The fixed160-frame walk stopped in the new128-wide
    # chapel. Drive the actual room/door with inputs, then release on arrival.
    buttons=set()
    def return_to_boss(frame,lib):
        if frame<3000:return
        buttons.clear();_,ram=k.ram_of(lib);stats=w.u32(ram,k.STATS_POINTER-p.BASE)-p.BASE
        if not 0<=stats<len(ram)-0x98:return
        if w.u32(ram,stats)==87:
            sample=p.sample(ram);x=sample['position_q12_candidate'][0]/4096
            buttons.add('Right')
            if x>100 and frame%16<6:buttons.add('X')
    captures=emu.run(Path(rom),4160,{3000,4100},save_path=save,script=script,label='renewal-continue-'+sha[:8]+'-'+before[:8],ram_captures={3000,4100},
        frame_hook=return_to_boss,live_buttons=buttons,core_options={b'melonds_jit_enable':b'enabled',b'melonds_jit_block_size':b'12'})
    rows=[]
    for frame in (3000,4100):
        ram=(captures/f'ram-{frame:05d}.bin').read_bytes();stats=w.u32(ram,k.STATS_POINTER-p.BASE)-p.BASE
        flags=int.from_bytes(ram[stats+0x1c:stats+0x44],'little');sample=p.sample(ram)
        enemies=[e for e in k.enemies(ram) if e['hp']>0]
        rows.append(dict(frame=frame,room=w.u32(ram,stats),earned=bool(flags>>147&1),position=sample['position_q12_candidate'],enemies=len(enemies)))
    checks=dict(continue_at_sanctuary=rows[0]['room']==87,earned_flag=all(r['earned'] for r in rows),
        native_return_to_cleared_boss=rows[1]['room']==89 and rows[1]['enemies']==0,source_save_unchanged=w.sha256(save.read_bytes())==before)
    report=dict(rom_sha256=sha,passed=all(checks.values()),checks=checks,observations=rows,captures=str(captures),
        limits='Actual earned copied battery, fresh boot and Continue, native inputs to boss; no warp, flag or actor fixtures.')
    w.write_json(OUT/'earned-continue.json',report);print(json.dumps(report));return report

def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('command',choices=('all','pair','combat','roster','view','crane-all','crane-manifest','_crane','idle','duel','duel-all','continue'))
    a.add_argument('--rom',required=True);a.add_argument('--name',default='ML_Entry');a.add_argument('--group',type=int,default=1)
    a.add_argument('--black',action='store_true');a.add_argument('--persist',action='store_true');a.add_argument('--jobs',type=int,default=3)
    a.add_argument('--no-heal',action='store_true')
    a.add_argument('--capture-every',type=int,default=30);a.add_argument('--tag',default='')
    a.add_argument('--creature',choices=('maw','ballast','spore','skitter','warden','eye'),default='maw')
    args=a.parse_args(argv)
    configure_rooms(args.rom)
    global RUN_TAG
    RUN_TAG=args.tag
    if args.capture_every!=30:
        native=k._run
        def dense(*a,**kw):
            kw['caps']=tuple(range(0,kw['frames'],args.capture_every));return native(*a,**kw)
        k._run=dense
    if args.command=='duel-all':
        from concurrent.futures import ThreadPoolExecutor,as_completed
        def one(style):
            log=OUT/('duel-'+style+'.log')
            with log.open('w') as f:proc=subprocess.run([sys.executable,str(Path(__file__)),'duel','--rom',args.rom,'--creature',style],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
            path=OUT/('walk-duel-'+style+'.json') if style in ('skitter','warden','eye') else OUT/('duel-'+style+'-proof.json')
            report=json.loads(path.read_text()) if path.exists() else {};counts=report.get('attack_sequencer_calls',[0]*7)
            index=('maw','ballast','spore','skitter','warden','eye').index(style)
            return style,bool(proc.returncode==0 and report.get('passed') and counts[index]>=3)
        results={}
        with ThreadPoolExecutor(args.jobs) as pool:
            for future in as_completed([pool.submit(one,s) for s in ('maw','ballast','spore','skitter','warden','eye')]):
                s,passed=future.result();results[s]=passed;print(json.dumps([s,passed]),flush=True)
        report=dict(rom_sha256=w.sha256(Path(args.rom).read_bytes()),passed=all(results.values()),creatures=results)
        w.write_json(OUT/'duel-all.json',report);return report
    if args.command=='_crane':
        cw.OUT=CRANE_OUT
        lab.JIT=True;k._run=lab.static_warp_runner(k._run)
        old_init=cw.Walker.__init__
        def parked(self,*a,**kw):
            old_init(self,*a,**kw);self.on.update(fight=False,park=(500,400))
            self.report['door_fixture']=dict(parked_enemies=True,healed_player=True,player_placements=False)
        cw.Walker.__init__=parked
        old_nav=cw.Walker.do_navigate
        def manual_stacked(self,step,state,ptr,ram):
            result=old_nav(self,step,state,ptr,ram)
            from tools import crane_rooms as cr
            name,g=step[1:3]
            if not result and name in cr.SPECS and state.pos:
                d=cr.SPECS[name].doors[g-1]
                if sum(v.side==d.side for v in cr.SPECS[name].doors)>1 and abs(state.pos[0]-d.wall)<18 and d.floor-3<state.pos[1]<d.floor+15 and self.t%12<5:self.buttons.add('X')
                if not d.floor and state.state==9 and self.t%32<12:self.buttons.add('B')
            return result
        cw.Walker.do_navigate=manual_stacked
        if args.name=='AR_ContainerWarren' and args.group==2:
            native_run=cw.run
            def cargo_route(rom,label,start,spawn,steps,preset=()):
                steps=list(steps);at=next(i for i,s in enumerate(steps) if s[0]=='navigate')
                # Jump before leaving the quay, then use the actual cargo
                # roofs. Walking into the recovery pit first made the broad
                # wall navigator hang below the first crate's ledge.
                guided=[item for x,y in cw.SETPIECES['cargo-canyon'][3] for item in (('land',x,y,900),mw.wait(12))]
                return native_run(rom,label,start,spawn,steps[:at]+guided+steps[at:],preset)
            cw.run=cargo_route
        sys.argv=[str(Path(cw.__file__)),'cross',args.name,'--rom',args.rom,'--group',str(args.group),
                  '--preset','power,upper,crown,boss,freight,drydock']
        if args.name=='Pier_Save02':sys.argv=[str(Path(cw.__file__)),'entry','--rom',args.rom]
        return cw.main()
    if args.command=='crane-manifest':
        from tools import crane_rooms
        sha=w.sha256(Path(args.rom).read_bytes());reports={};checks={}
        for name,g in [('Pier_Save02',2),*crane_rooms.LINKS]:
            label=name+str(g);base='walk-pier-entry' if name=='Pier_Save02' else 'walk-cross-'+label
            path=CRANE_OUT/(base+'-'+sha[:8]+'.json');r=json.loads(path.read_text()) if path.exists() else {}
            checks[label]=bool(r.get('passed') and r.get('rom_sha256')==sha and r.get('rom_unchanged'))
            if any(s['kind']=='place' for s in r.get('steps',[])):checks[label]=False
            reports[label]=str(path.relative_to(ROOT))
        result=dict(rom_sha256=sha,passed=all(checks.values()),doors=checks,directed_doors=len(checks),case_reports=reports,
            limits='Copied-save arrivals, parked enemies, healed player. Native controller movement only; Cargo Canyon uses its authored roof landings. No player-position traversal fixtures.')
        w.write_json(OUT/'crane-doors.json',result);print(json.dumps(result));return result
    if args.command=='crane-all':
        from tools import crane_rooms
        from concurrent.futures import ThreadPoolExecutor,as_completed
        def one(item):
            name,g=item;label=name+str(g);log=OUT/('crane-'+label+'.log');log.parent.mkdir(parents=True,exist_ok=True)
            with log.open('w') as f:proc=subprocess.run([sys.executable,str(Path(__file__)),'_crane','--rom',args.rom,'--name',name,'--group',str(g)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
            sha=w.sha256(Path(args.rom).read_bytes());base='walk-pier-entry' if name=='Pier_Save02' else 'walk-cross-'+label
            path=CRANE_OUT/(base+'-'+sha[:8]+'.json');report=json.loads(path.read_text()) if path.exists() else {}
            return label,proc.returncode==0 and report.get('passed',False) and report.get('rom_sha256')==sha
        result={}
        with ThreadPoolExecutor(args.jobs) as pool:
            for future in as_completed([pool.submit(one,item) for item in [('Pier_Save02',2),*crane_rooms.LINKS]]):
                label,passed=future.result();result[label]=passed;print(json.dumps([label,passed]),flush=True)
        summary=dict(rom_sha256=w.sha256(Path(args.rom).read_bytes()),passed=all(result.values()),doors=result)
        w.write_json(OUT/'crane-doors.json',summary);return summary
    if args.command=='pair':return pair(args.rom,args.name,args.group)
    if args.command=='continue':return continue_earned(args.rom)
    if args.command=='duel':return duel(args.rom,args.creature)
    if args.command in ('combat','roster'):return combat(args.rom,args.command=='roster',args.black,args.persist,not args.no_heal)
    if args.command=='idle':return run(args.rom,'idle-'+args.name,args.name,args.group,[mw.wait(1000)],combat=True)
    if args.command=='view':return run(args.rom,'view-'+args.name,args.name,args.group,[mw.wait(180),mw.mark('arrival'),('travel',90,800),mw.wait(180),mw.mark('room')])
    tasks=[];seen=set()
    for (n,g),(d,s) in rooms.LINKS.items():
        if ch.BY_NAME[n].index not in rooms.ACTIVE:continue
        edge=frozenset((n,d))
        if edge not in seen:tasks.append((n,g));seen.add(edge)
    def work(item):
        n,g=item;label=str(ch.BY_NAME[n].index)+'-'+str(g)
        out=OUT/('pair-'+label+'.log');out.parent.mkdir(exist_ok=True,parents=True)
        with out.open('w') as f:
            proc=subprocess.run([sys.executable,str(Path(__file__)),'pair','--rom',args.rom,'--name',n,'--group',str(g)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
        sha=w.sha256(Path(args.rom).read_bytes());path=OUT/('walk-pair-'+label+'-'+sha[:8]+'.json');r=json.loads(path.read_text()) if path.exists() else {}
        return label,proc.returncode==0 and r.get('passed',False) and r.get('rom_sha256')==sha
    from concurrent.futures import ThreadPoolExecutor,as_completed
    results={}
    with ThreadPoolExecutor(args.jobs) as pool:
        futures=[pool.submit(work,item) for item in tasks]
        for future in as_completed(futures):
            label,passed=future.result();results[label]=passed;print(json.dumps([label,passed]),flush=True)
    result=dict(rom_sha256=w.sha256(Path(args.rom).read_bytes()),passed=all(results.values()),pairs=results,directed_doors=len(tasks)*2,
        limits='Native arrivals and controller movement. Enemies parked and player healed. Initial warp compiled into disposable ROM before JIT. No traversal placement fixtures.')
    w.write_json(OUT/'midnight-doors.json',result);print(json.dumps(result));return result

if __name__=='__main__':raise SystemExit(0 if main()['passed'] else 1)
