"""Copied-save Midnight overhaul walks, original creature combat and captures.

Every door is approached with controller inputs from a real arrival spawn.
Door tests park enemies and heal the player. Combat never caps enemy HP;
healed and no-refill runs are separate evidence.
"""
import argparse,ctypes as ct,json,struct,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import midnight_walk as mw,crane_walk as cw,midnight_chapter as ch,midnight_rooms as mr
from tools import midnight_rework_rooms as rooms,midnight_rework_boss as boss,kit_lab as k,player_trace as p,wos_tool as w
from tools.crane_creature_lab import pursuit_buttons
OUT=ROOT/'work/midnight-rework'
BASE_WALKER=mw.Walker
JIT=False
AUDIO_PROBE=None
SUBSTATION_LANDINGS={
    ('ML_Switchyard',3):((29,15),(8,38)),
    ('ML_Roof',2):((137,17),(120,5),(39,17),(24,5)),
}

def static_warp_runner(native):
    """Compile only the four lab-entry words before boot, permitting safe JIT.

    The normal lab writes those same words in RAM with JIT disabled. This
    fixture changes no physics, rooms, enemies or saves and never loads states.
    """
    def run(rom,label,inputs,**kw):
        if not JIT:return native(rom,label,inputs,**kw)
        patch=Path(kw.pop('patch'));rows=json.loads(patch.read_text());source=Path(rom);raw=source.read_bytes();fixture=bytearray(raw)
        h=w.parse_header(raw)
        for row in rows:
            address=row['addr'];at=h['arm9_offset']+address-p.BASE
            expected=bytes.fromhex(row['expect']);value=bytes.fromhex(row['hex'])
            if fixture[at:at+len(value)]!=expected:raise ValueError('Static entry fixture expectation changed')
            fixture[at:at+len(value)]=value
        if Walker.reward_key:
            # Read-only post-remap observer, compiled before boot as well.
            # It writes counters only in the verified unused private tail.
            from tools import midnight_rework as rw,tasm_kit as kit,crane_audio as audio
            from tools.crane_boss import Arm
            from tools.crane_row import branch
            code_at=rw.START+0x8A0;table_at=rw.START+0x950;site=audio.SITE+4
            offset=lambda address:kit.SOURCE+address-kit.TARGET if address>=kit.TARGET else address-p.BASE
            if any(fixture[h['arm9_offset']+offset(code_at):h['arm9_offset']+offset(table_at)+84]):raise ValueError('Audio observer tail is occupied')
            a=Arm(code_at);a.emit(0xE92D100F,0xE10FC000);a.lit(0,'first',597)
            a.lit(2,'table',table_at);a.emit(0xE5821050,0xE1510000);a.b('done',3)
            a.emit(0xE0411000,0xE3510014);a.b('done',2)
            a.lit(2,'table');a.emit(0xE0822101,0xE5923000,0xE2833001,0xE5823000)
            a.label('done');a.emit(0xE128F00C,0xE8BD100F,0xE24DD00C);a.b(site+4)
            code=a.finish()
            if code_at+len(code)>table_at or w.u32(fixture,h['arm9_offset']+site-p.BASE)!=0xE24DD00C:raise ValueError('Audio probe continuation contract')
            at=h['arm9_offset']+offset(code_at);fixture[at:at+len(code)]=code
            struct.pack_into('<I',fixture,h['arm9_offset']+site-p.BASE,branch(site,code_at))
            global AUDIO_PROBE
            AUDIO_PROBE=table_at
        path=ROOT/'build/midnight-rework/entry-fixtures'/f'{w.sha256(raw)[:8]}-{label}.nds'
        w.atomic_write(path,bytes(fixture),sources=(source,))
        kw['core_options']={**kw.get('core_options',{}),b'melonds_jit_enable':b'enabled',b'melonds_jit_block_size':b'12'}
        if Walker.reward_key and AUDIO_PROBE:
            old_hook=kw['extra_hook']
            def observed(frame,lib):
                result=old_hook(frame,lib)
                if frame>=0 and Walker.current.i>=len(Walker.current.steps):
                    _,ram=k.ram_of(lib)
                    Walker.current.report['private_audio_calls']=list(struct.unpack_from('<20I',ram,AUDIO_PROBE-p.BASE))
                return result
            kw['extra_hook']=observed
        return native(path,label,inputs,**kw)
    return run

def install():
    if not getattr(k._run,'_midnight_static',False):
        k._run=static_warp_runner(k._run);k._run._midnight_static=True
    ids={r.name:r.index for r in ch.ROOMS}
    ports={name:tuple((d.side,d.wall,d.floor,d.spawn_id) for d in spec.doors) for name,spec in {**mr.AUTHORED,**rooms.SPECS}.items()}
    bounds={name:(rooms.SIZES[rooms.NAMES.index(name)] if name in rooms.NAMES else
                tuple(mr.AUTHORED[name].camera[0][2])) for name in ids}
    # Navigator consumes the actual authored doors, not the old clone bounds.
    cw.cr=SimpleNamespace(IDS=ids,PORTS=ports,NAMES=tuple(ids),BOUNDS=[bounds[n] for n in ids],LINKS=ch.LINKS)
    cw.OUT=OUT;mw.OUT=OUT
    return ids,ports

class Walker(cw.Walker):
    combat=False
    heal=True
    reward_key=None
    runtime=None
    zero_reward=False
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw);self.on['alive']=self.heal
        self.on.update(fight=False,park=None if self.combat else (500,400))
        self.seen={};self.min_hp=None
        Walker.current=self;self.pcm=[];self.audio_installed=False
    def read(self,frame,ram):
        state=BASE_WALKER.read(self,frame,ram)
        if state and state.pos:
            real=[]
            for e in state.enemies:
                mo=struct.unpack_from('<I',ram,e['actor']-p.BASE+0x30)[0]-p.BASE
                if e['state'] is not None and 0<mo<len(ram)-0x300 and w.u32(ram,mo)==e['actor'] and -30<e['position'][0]/4096<500 and -50<e['position'][1]/4096<260:real.append(e)
            state.enemies=real
        self.last_state=state;self.last_ram=ram
        return state
    def do_navigate(self,step,state,ptr,ram):
        result=super().do_navigate(step,state,ptr,ram)
        _,name,group,timeout=step
        if not result and name in rooms.SPECS and rooms.manual(name,group) and state.pos:
            side,wall,floor,spawn=cw.cr.PORTS[name][group-1]
            if abs(state.pos[0]-wall)<18 and floor+1<=state.pos[1]<=floor+13 and self.t%12<5:self.buttons.add('X')
        return result
    def do_land_if_below(self,step,state,ptr,ram):
        if state.state==29:
            self.buttons.clear();self.buttons.add('B' if self.t%24<6 else 'Down');return False
        if state.pos and state.pos[1]>=step[2]-1 and abs(state.pos[0]-step[1])<28 and state.state in (0,1,4,5,6):return True
        if state.room==92 and state.pos and state.pos[1]<step[2]-32:
            options=[i for i,s in enumerate(self.steps[:self.i]) if s[0]=='land_if_below' and state.pos[1]+5<s[2]<=state.pos[1]+27]
            if options:
                self.report.setdefault('climb_retries',[]).append([state.frame,self.i,options[-1]])
                if len(self.report['climb_retries'])>8:return self.timeout(step,state,self.t,'relay climb retries')
                self.i=options[-1]-1;return True
        if self.t==0:self.scratch.pop('edge_jump',None)
        if state.pos:
            x,y=state.pos;target_x,target_y=step[1:3]
            if self.t>80 and 'edge_jump' not in self.scratch and abs(x-target_x)<20 and y<target_y-8:
                self.scratch['edge_jump']=(self.t,'Left' if target_x>cw.cr.BOUNDS[state.room-76][0]/2 else 'Right')
            if 'edge_jump' in self.scratch:
                started,away=self.scratch['edge_jump'];age=self.t-started
                self.buttons.clear()
                if age<50:self.buttons.add(away)
                elif age<70:self.buttons.add('B')
                elif age<125:self.buttons.update(('B','Right' if away=='Left' else 'Left'))
                else:self.scratch.pop('edge_jump',None)
                if age<125:return False
        return super().do_land(('land',*step[1:]),state,ptr,ram)
    def tick(self,frame,lib):
        self.native_lib=lib
        if self.reward_key and not self.audio_installed:
            info=(ct.c_byte*40)();lib.retro_get_system_av_info.argtypes=[ct.c_void_p];lib.retro_get_system_av_info(ct.byref(info))
            self.audio_rate=round(struct.unpack_from('<d',bytes(info),32)[0])
            lib._wos_audio_sink=lambda f,data:self.pcm.append(data) if f>=k.TRAINING_START else None
            self.audio_installed=True
        if self.reward_key and frame+k.TRAINING_START>=2040:
            from tools import midnight_rework_creatures as creatures
            ptr,ram=k.ram_of(lib);spec=next(c for c in creatures.CREATURES if c.key==self.reward_key)
            ct.memmove(ptr+self.runtime['state']-p.BASE,struct.pack('<2I',84,('maw','ballast','spore').index(self.reward_key)),8)
            for key,address in self.runtime['goals'].items():
                cost=spec.cost*4096 if key=='patrol' else 0
                ct.memmove(ptr+address-p.BASE,struct.pack('<2I',cost,cost),8)
            if self.zero_reward:ct.memmove(ptr+self.runtime['configs'][self.reward_key]-p.BASE+0x50,bytes(4),4)
        super().tick(frame,lib)
        if frame<0 or not self.combat:return
        ram=self.last_ram;state=self.last_state
        if AUDIO_PROBE and self.reward_key and frame>=0:self.report['private_audio_calls']=list(struct.unpack_from('<20I',ram,AUDIO_PROBE-p.BASE))
        if state and state.pos and self.combat:
            self.min_hp=state.hp if self.min_hp is None else min(self.min_hp,state.hp)
            if frame%12==0:
                stats=w.u32(ram,k.STATS_POINTER-p.BASE)-p.BASE
                self.report.setdefault('combat',[]).append(dict(frame=frame,hp=state.hp,vars=state.room_vars,pos=state.pos,
                    xp=w.u32(ram,stats+0x44),enemies=[dict(e,config=hex(w.u32(ram,e['actor']-p.BASE+0x40))) for e in state.enemies]))
    def do_combat(self,step,state,ptr,ram):
        if self.t>=step[1]:return self.timeout(step,state,step[1],'Conductor combat deadline')
        self.buttons.clear()
        if state.flags>>boss.DEFEATED&1:
            self.record('Conductor_defeated_by_native_damage',True,state,minimum_hp=self.min_hp,player_refills=self.heal);return True
        if state.hp<=0:return self.timeout(step,state,self.t,'player defeat during Conductor combat')
        if state.pos:
            if state.enemies:
                e=min(state.enemies,key=lambda e:abs(e['position'][0]/4096-state.pos[0]))
                self.buttons.update(pursuit_buttons(state.frame,state,e,kit=True))
                if state.pos[0]<25:self.buttons.discard('Left');self.buttons.add('Right')
                if state.pos[0]>200:self.buttons.discard('Right');self.buttons.add('Left')
            elif not state.room_vars or not state.room_vars[0]:self.buttons.add('Right' if state.pos[0]<55 else 'Left')
        return False
    def do_end(self,step,state,ptr,ram):
        self.i=len(self.steps)-1;return True
    def do_roster(self,step,state,ptr,ram):
        if self.t>=step[1]:return self.timeout(step,state,step[1],'native roster clearance')
        self.buttons.clear()
        if state.pos:
            if state.enemies:
                self.scratch['roster_seen']=True;self.scratch['roster_empty']=0
                e=min(state.enemies,key=lambda e:abs(e['position'][0]/4096-state.pos[0]))
                self.buttons.update(pursuit_buttons(state.frame,state,e,kit=True))
                if state.pos[0]<20:self.buttons.discard('Left');self.buttons.add('Right')
                if state.pos[0]>332:self.buttons.discard('Right');self.buttons.add('Left')
            else:
                self.scratch['roster_empty']=self.scratch.get('roster_empty',0)+1
                if self.scratch.get('roster_seen') and self.scratch['roster_empty']>=120:
                    self.record('full_HP_roster_cleared',True,state,player_refills=self.heal);return True
                if state.pos[0]<160:self.buttons.add('Right')
                elif state.pos[0]>190:self.buttons.add('Left')
                if self.t%64<32:self.buttons.add('B')
                if state.state in (7,9,16):self.buttons.add('Up')
        return False
    def do_snapshot(self,step,state,ptr,ram):
        lib=self.native_lib
        if lib.retro_get_memory_size(0)!=512:raise ValueError('Expected copied native512-byte SRAM')
        path=OUT/'conductor-earned.sav';path.write_bytes(ct.string_at(lib.retro_get_memory_data(0),512))
        self.record('earned_Conductor_flag_saved',state.room==87 and bool(state.flags>>boss.DEFEATED&1),state)
        return True
    def do_reward(self,step,state,ptr,ram):
        if self.t>=4000:return self.timeout(step,state,4000,'physical reward collection')
        stats=w.u32(ram,k.STATS_POINTER-p.BASE)-p.BASE;config=self.runtime['configs'][self.reward_key]
        owned=[e for e in k.enemies(ram) if w.u32(ram,e['actor']-p.BASE+0x40)==config]
        self.buttons.clear()
        if 'reward_start' not in self.scratch:
            if not state.enemies:
                if state.pos and state.pos[0]<170:self.buttons.add('Right')
                return False
            target=next((e for e in owned if e['hp']>0),None)
            if target is None:return False
            ct.memmove(ptr+stats+0x84,struct.pack('<I',12288),4)
            ct.memmove(ptr+target['actor']-p.BASE+0x44,struct.pack('<I',1),4)
            self.scratch.update(reward_start=self.t,reward_xp=w.u32(ram,stats+0x44),reward_actor=target['actor'])
        target=next((e for e in owned if e['actor']==self.scratch['reward_actor']),None)
        if target and target['hp']>0:
            if target['controller']:ct.memmove(ptr+target['controller']-p.BASE+0x14,bytes(4),4)
            if state.pos:self.buttons.update(pursuit_buttons(state.frame,state,target))
        if target and target['hp']<=0 and w.u32(ram,target['actor']-p.BASE+0x88)&0x10:self.scratch.setdefault('reward_dead',self.t)
        if 'reward_dead' in self.scratch:
            xp=w.u32(ram,stats+0x44)-self.scratch['reward_xp'];health=state.hp-12288
            if (xp>0 and health>0) or self.t-self.scratch['reward_dead']>500:
                passed=(xp==0 and health==0) if self.zero_reward else xp>0 and health>0
                self.record('native_physical_XP_and_HP' if not self.zero_reward else 'zero_reward_control',passed,state,
                    xp_awarded=xp,health_recovered_q12=health,player_refills=False,target_fixture='one idle1HP actor; native arrival/pursuit/strike; no position writes')
                return True
        return False

def run(rom,label,start,spawn,steps,preset=(),*,combat=False,heal=True):
    install();cw.Walker=Walker;Walker.combat=combat;Walker.heal=heal
    expanded=[]
    for step in steps:
        if step[0]=='navigate' and step[1:3]==('ML_RelayHall',2):
            # Unchanged legacy Relay: retain its established upper-landing
            # isolation fixture, then use the actual door with native input.
            # This qualifies the doorway, not the full active-arc ascent.
            expanded += [mw.place(20,115),mw.hold('B',6),mw.wait(90)]
        if step[0]=='navigate' and step[1] in rooms.SPECS:
            name,g=step[1:3];side,wall,floor,spawn_id=cw.cr.PORTS[name][g-1]
            if floor:
                width=rooms.SIZES[rooms.NAMES.index(name)][0]
                points=getattr(rooms,'LANDINGS',{}).get(name,
                    rooms.TURBINE_STEPS if name=='ML_NestThroat' else rooms.CROWN_STEPS if name=='ML_NestGate' else tuple((30+(n%2)*24 if side=='left' else width-30-(n%2)*24,y) for n,y in enumerate(range(16,int(floor),16))))
                for x,y in points:
                    expanded.append(('land_if_below',x,y+5,1500))
                expanded.append(('land_if_below',17 if side=='left' else width-17,floor+5,1500))
        elif step[0]=='navigate' and (step[1],step[2]) in SUBSTATION_LANDINGS:
            for x,y in SUBSTATION_LANDINGS[step[1],step[2]]:
                # The two Roof gaps require an actual ground landing before
                # entering the low tunnel, rather than running onto its roof.
                kind='land' if step[1]=='ML_Roof' and y==5 else 'land_if_below'
                expanded.append((kind,x,y,1500))
        expanded.append(step)
    steps=expanded
    if combat:
        mw.PLAYER_ABILITIES=0x180FFFDF
    # Explicit terminal step skips the padding budget after the meaningful
    # native-input route completes, including custom conditional landings.
    extra=sum(s[3] for s in steps if s[0]=='land_if_below')+(16000 if combat else 0)
    if extra:
        steps=[*steps,('end',None),mw.hold('',extra)]
    result=cw.run(rom,label,start,spawn,steps,preset)
    if Walker.current.pcm:
        import wave
        with wave.open(str(OUT/(label+'.wav')),'wb') as stream:
            stream.setnchannels(2);stream.setsampwidth(2);stream.setframerate(Walker.current.audio_rate);stream.writeframes(b''.join(Walker.current.pcm))
    return result

def one_door(rom,name,group):
    spec=rooms.SPECS[name] if name in rooms.SPECS else mr.AUTHORED[name]
    # Spawn opposite the exit, so tests cross the room instead of standing
    # next to the trigger. All movement after entry is real controller input.
    target=spec.doors[group-1];arrival=next((d for d in spec.doors if d.side!=target.side),spec.doors[0])
    destination=ch.LINKS[name,group][0]
    expected=ch.BY_NAME[destination].index if destination in ch.BY_NAME else 52 # resolved below for native
    if destination==ch.ENTRANCE:
        import mod
        from tools import room_catalog
        raw,_,_=mod.load_clean();h=w.parse_header(raw)
        expected=next(r.index for r in room_catalog.parse(raw[h['arm9_offset']:h['arm9_offset']+h['arm9_size']],
            [e['name'] for e in mod.load_clean()[2]['entries']]) if r.name==destination)
    steps=[mw.wait(120),cw.nav(name,group,4200),mw.wait(120),
           mw.check('real_door_destination',lambda s:s.room==expected)]
    return run(rom,f'door-{ch.BY_NAME[name].index}-{group}',name,arrival.spawn_id,steps,
               preset=(boss.DEFEATED,ch.ROOM_FLAGS['signal_leech_defeated'],ch.ROOM_FLAGS['substation_cleared']))

def combat(rom,heal=True,black=False,persist=False):
    steps=[mw.wait(120)]
    if black:steps += [mw.hold('L',6),mw.wait(90),mw.check('native_Black_form',lambda s:s.black==1)]
    steps += [('combat',14000),mw.wait(240),cw.nav('ML_Venom',1,1200),mw.wait(90),mw.check('boss_exit_after_real_victory',lambda s:s.room==87)]
    if persist:
        steps += [mw.walk('sanctuary_save',56,600),mw.hold('X',6),mw.wait(70),mw.hold('A',6),mw.wait(90),mw.hold('A',6),mw.wait(220),('snapshot','save')]
    else:
        steps += [cw.nav('ML_NestShrine',1,1200),mw.wait(120),mw.check('boss_stays_cleared_on_revisit',lambda s:s.room==89 and bool(s.flags>>boss.DEFEATED&1) and s.room_vars[0]==0 and not s.enemies)]
    return run(rom,'conductor-'+('black' if black else 'red')+('-save' if persist else '-healed' if heal else '-no-refill'),
        'ML_Venom',2,steps,combat=True,heal=heal)

def pair(rom,name,group):
    spec=rooms.SPECS[name] if name in rooms.SPECS else mr.AUTHORED[name]
    target=spec.doors[group-1];arrival=next((d for d in spec.doors if d.side!=target.side),spec.doors[0])
    destination,spawn=ch.LINKS[name,group]
    if destination==ch.ENTRANCE:
        # The original entrance remains a real door in native Save02.
        expected=65
        steps=[mw.wait(120),cw.nav(name,group,4200),mw.wait(90),mw.check('native_return',lambda s:s.room==65),
               mw.until('native_entrance',mw.in_room(name),600,'Right'),mw.wait(90),
               mw.check('chapter_entry',lambda s:s.room==ch.BY_NAME[name].index)]
    else:
        destspec=rooms.SPECS[destination] if destination in rooms.SPECS else mr.AUTHORED[destination]
        back=next(g for g,d in enumerate(destspec.doors,1) if d.spawn_id==spawn)
        steps=[mw.wait(120),cw.nav(name,group,4200),mw.wait(90),
               mw.check('outward_door',lambda s:s.room==ch.BY_NAME[destination].index),
               cw.nav(destination,back,4200),mw.wait(90),mw.check('return_door',lambda s:s.room==ch.BY_NAME[name].index)]
    return run(rom,f'pair-{ch.BY_NAME[name].index}-{group}',name,arrival.spawn_id,steps,
        preset=(boss.DEFEATED,ch.ROOM_FLAGS['signal_leech_defeated'],ch.ROOM_FLAGS['substation_cleared']))

def manifest(rom):
    """Audit already completed cases for this exact immutable source ROM."""
    sha=w.sha256(Path(rom).read_bytes());seen=set();reports={};limits={}
    for (name,g),(dest,spawn) in ch.LINKS.items():
        edge=frozenset((name,dest))
        if edge in seen:continue
        seen.add(edge);label=f'pair-{ch.BY_NAME[name].index}-{g}'
        path=OUT/f'walk-{label}-{sha[:8]}.json';data=json.loads(path.read_text())
        if data['rom_sha256']!=sha or not data['passed'] or not data['rom_unchanged']:raise ValueError('Door case failed: '+label)
        if any(s['kind']=='place' for s in data['steps']):
            if label!='pair-92-2':raise ValueError('Unexpected placement in replacement-room traversal')
            limits[label]='Unchanged Relay upper landing isolated in disposable RAM; actual doorway walked. Full active-arc ascent not qualified.'
        reports[label]=str(path.relative_to(ROOT))
    report=dict(rom_sha256=sha,passed=True,door_pairs={k:True for k in reports},directed_doors=len(ch.LINKS)+1,
        case_reports=reports,limited_cases=limits,
        limit='Four initial warp words compiled in disposable ROMs; JIT enabled. Enemies parked, player healed, defeated flags preset. No position fixtures in the fifteen replacement rooms. See limited_cases for unchanged Relay.')
    w.write_json(OUT/'real-doors.json',report);print(json.dumps(report));return report

def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('command',choices=('door','pair','all','manifest','combat','roster','reward','_door','_pair'))
    a.add_argument('--rom',required=True);a.add_argument('--name',default='ML_Entry');a.add_argument('--group',type=int,default=1)
    a.add_argument('--heal',action='store_true');a.add_argument('--black',action='store_true');a.add_argument('--persist',action='store_true')
    a.add_argument('--creature',choices=('maw','ballast','spore'),default='maw');a.add_argument('--zero-reward',action='store_true')
    a.add_argument('--jobs',type=int,default=4);a.add_argument('--jit',action='store_true');args=a.parse_args(argv)
    global JIT
    JIT=args.jit
    if args.command in ('door','_door'):return one_door(args.rom,args.name,args.group)
    if args.command in ('pair','_pair'):return pair(args.rom,args.name,args.group)
    if args.command=='manifest':return manifest(args.rom)
    if args.command=='combat':return combat(args.rom,args.heal,args.black,args.persist)
    if args.command=='roster':return run(args.rom,'native-roster','ML_Station',1,[mw.wait(120),('roster',12000)],combat=True,heal=args.heal)
    if args.command=='reward':
        Walker.reward_key=args.creature;Walker.zero_reward=args.zero_reward
        Walker.runtime=json.loads(Path(args.rom).with_suffix('.build.json').read_text())['midnight_rework']['creatures']
        return run(args.rom,'reward-'+args.creature+('-zero' if args.zero_reward else ''),'ML_NestSpan',2,[mw.wait(120),('reward',None)],combat=True,heal=False)
    import subprocess
    from concurrent.futures import ThreadPoolExecutor
    def one(item):
        name,g=item
        done=subprocess.run([sys.executable,str(Path(__file__)),'_pair','--rom',str(args.rom),'--name',name,'--group',str(g),'--jit'],capture_output=True,text=True,cwd=ROOT)
        label=f'pair-{ch.BY_NAME[name].index}-{g}'
        if done.returncode:
            w.atomic_write(OUT/(label+'-error.log'),done.stdout.encode()+done.stderr.encode());return label,False
        report=json.loads((OUT/('walk-'+label+'.json')).read_text());return label,report['passed']
    tasks=[];seen=set()
    for (name,g),(dest,spawn) in ch.LINKS.items():
        key=frozenset((name,dest))
        if key not in seen:tasks.append((name,g));seen.add(key)
    with ThreadPoolExecutor(args.jobs) as pool:results=dict(pool.map(one,tasks))
    report=dict(rom_sha256=w.sha256(Path(args.rom).read_bytes()),passed=all(results.values()),door_pairs=results,
                directed_doors=len(ch.LINKS)+1,
                limit='Native arrivals and controller traversal through every replacement room. Four entry words compiled before boot; JIT enabled. The unchanged Relay upper doorway uses its established landing-placement fixture; this does not qualify its full active-arc ascent. Enemies parked; player healed; defeated flags preset.')
    w.write_json(OUT/'real-doors.json',report);print(json.dumps(report));return report

if __name__=='__main__':main()
