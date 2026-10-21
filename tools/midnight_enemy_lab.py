"""Observe real enemy contacts, cadence and audio on a disposable copied save.

Initial arrival and one-species spawn budget are fixtures. All movement, attack
selection, enemy HP and player damage after arrival use the native engine.
"""
import argparse, ctypes as ct, json, struct, sys,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import chapter_renewal_lab as q, creature_forge_lab as forge
from tools import midnight_rework_lab as lab, midnight_walk as mw, kit_lab as k
from tools import player_trace as pt, wos_tool as w


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--style',choices=('maw','ballast','spore','skitter','warden','eye'),default='skitter')
    p.add_argument('--tag',default='baseline');p.add_argument('--frames',type=int,default=2200)
    p.add_argument('--distance',type=float,default=7);p.add_argument('--capture-every',type=int,default=4)
    p.add_argument('--approach-x',type=float,help='Native-input approach destination before observing attacks')
    p.add_argument('--black',action='store_true')
    p.add_argument('--finish',action='store_true',help='After damage observation, clear through native attacks with player refills')
    p.add_argument('--reset-between',action='store_true',help='Reset native player HP only between complete attack programs; never during a strike')
    p.add_argument('--counterplay',action='store_true',help='Respond to the windup with native jump or R through a melee foe')
    a=p.parse_args();out=ROOT/'work/midnight-rebuild'/a.tag;out.mkdir(parents=True,exist_ok=True)
    config=json.loads((ROOT/'work/playtest.json').read_text(encoding='utf-8'))
    actual=Path(config['battery_directory'])/'Spider-Man-WoS-modded.dsv'
    before=actual.read_bytes();copied=out/'player-copy.dsv';copied.write_bytes(before);k.TRAINING_SAVE=copied
    forge.OUT=out;q.OUT=out;q.RUN_TAG='-'+a.tag+'-'+a.style;forge.install(a.rom,a.capture_every)
    meta=json.loads(a.rom.with_suffix('.build.json').read_text(encoding='utf-8'))
    rt=meta['creature_forge']['runtime'];st=meta['chapter_spectacle']['scripted_runtime']
    crane=a.style in ('maw','ballast','spore');room_index=97 if crane else 78
    pattern=st['patterns'][str(room_index)];goals=st['goal_table'];kind={'skitter':21,'warden':36,'eye':20,'maw':21,'ballast':36,'spore':20}[a.style]
    # Later post-passes replace the pattern pointer in this stable table. Read
    # that pointer from the candidate rather than mutating obsolete RAM data.
    if 'midnight_finale' in meta:
        raw=a.rom.read_bytes();h=w.parse_header(raw);arm=raw[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        from tools.creature_forge import offset
        for row in range(40):
            at=offset(st['roster_table'])+row*12;rid=w.u32(arm,at)
            if rid==room_index:pattern=w.u32(arm,at+4);break
            if not rid:raise ValueError('Candidate lacks requested roster room')
    index=('maw','ballast','spore','skitter','warden','eye').index(a.style)
    runner=k._run;audio_rows=[];audio_seen=0;pcm=[];rate=[0];resets=[];counterplay=[];actual_hits=set()
    authored_programs=meta.get('midnight_encore',meta.get('midnight_rebuild',{})).get('creatures',{}).get(a.style,{}).get('programs',[])
    def isolate(*args,**kw):
        original=kw['extra_hook']
        def hook(frame,lib):
            nonlocal audio_seen
            if frame+k.TRAINING_START>=2040:
                ptr,ram=k.ram_of(lib);ct.memmove(ptr+pattern-pt.BASE,bytes((kind,)*4),4)
                for row in range(19):
                    at=goals-pt.BASE+row*20;room=w.u32(ram,at)
                    if room==room_index:
                        cost=2 if kind==36 else 1
                        for col in (4,8,12):ct.memmove(ptr+w.u32(ram,at+col)-pt.BASE,struct.pack('<2I',cost*4096,cost*4096),8)
                        break
                    if not room:break
            result=original(frame,lib)
            if crane and frame>=0 and not rate[0]:
                info=(ct.c_byte*40)();lib.retro_get_system_av_info.argtypes=[ct.c_void_p];lib.retro_get_system_av_info(ct.byref(info));rate[0]=round(struct.unpack_from('<d',bytes(info),32)[0])
                lib._wos_audio_sink=lambda f,b:pcm.append(b) if f>=k.TRAINING_START else None
            observer=meta.get('midnight_rebuild',{}).get('audio_observer')
            if observer and frame>=0:
                _,ram=k.ram_of(lib);base=observer['table']-pt.BASE;count=w.u32(ram,base)
                for i in range(max(audio_seen,count-256),count):
                    words=struct.unpack_from('<8I',ram,base+4+(i%256)*32);contexts=[]
                    for value in words[2:]:
                        at=value-pt.BASE
                        contexts.append(list(struct.unpack_from('<20I',ram,at)) if 0<=at<len(ram)-80 and at%4==0 else None)
                    audio_rows.append(dict(frame=frame,words=words,contexts=contexts))
                audio_seen=count
            return result
        kw['extra_hook']=hook;return runner(*args,**kw)
    isolate._midnight_static=True;k._run=isolate
    def watch(self,step,state,ptr,ram):
        self.buttons.clear()
        if self.t>=step[1] or state.hp<=0:return True
        if state.enemies and state.pos:
            enemy=state.enemies[0];dx=enemy['position'][0]/4096-state.pos[0];dy=enemy['position'][1]/4096-state.pos[1]
            previous=self.scratch.get('study_hp',state.hp);self.scratch['study_hp']=state.hp
            if state.hp<previous and enemy['state']==15:
                mot=w.u32(ram,enemy['actor']-pt.BASE+0x30)-pt.BASE;clock=w.u32(ram,mot+0x178)
                program=next((m for m in authored_programs if m['action']==enemy['action']),None)
                if program and any(x<=clock<=y for x,y in program['contacts']):actual_hits.add(enemy['action'])
            # Approach through normal input, then stand for a complete attack.
            # Correct distance only between programs; never chase a windup.
            slot=next((s for s in self.report.get('attack_slots',[]) if s[0]==enemy['controller']),None)
            if enemy['state']!=15:
                self.scratch.pop('study_dodge',None)
                if a.reset_between:
                    stats=w.u32(ram,k.STATS_POINTER-pt.BASE)-pt.BASE;top=w.u32(ram,stats+0x88)
                    if 0<state.hp<top:ct.memmove(ptr+stats+0x84,struct.pack('<I',top),4);resets.append(state.frame)
                wanted=a.distance
                if len(authored_programs)==3:
                    if a.style in ('warden','ballast') and authored_programs[2]['action'] not in actual_hits:wanted=17.2
                    if a.style in ('eye','spore'):wanted=24 if any(authored_programs[i]['action'] not in actual_hits for i in (0,2)) else 7
                if abs(dy)>5:
                    if dy < -8 and abs(dx)<32:
                        # Leave an overhanging deck before trying to approach
                        # an actor underneath it. Matching X alone can keep a
                        # passive damage probe directly above the target.
                        self.buttons.add('Left' if state.pos[0]<88 else 'Right')
                        return False
                    from tools.crane_creature_lab import pursuit_buttons
                    self.buttons.update(pursuit_buttons(state.frame,state,enemy,False));self.buttons.difference_update(('Y','A','R'));return False
                if abs(dx)>wanted+1:self.buttons.add('Right' if dx>0 else 'Left')
                elif abs(dx)<wanted-1:self.buttons.add('Left' if dx>0 else 'Right')
            elif a.counterplay:
                if meta.get('midnight_encore'):
                    from tools import midnight_encore_motion as authored
                else:
                    from tools import midnight_enemy_motion as authored
                move=next((m for m in authored.MOVES[a.style] if m.action==enemy['action']),None)
                if move:
                    mot=w.u32(ram,enemy['actor']-pt.BASE+0x30)-pt.BASE;clock=w.u32(ram,mot+0x178)
                    jump=move.kind in ('march','peal','quake','seeds','twins','beam','lance','burst')
                    if max(0,move.contacts[0][0]-(7 if jump else 4))<=clock<move.contacts[0][0] and 'study_dodge' not in self.scratch:
                        entry=dict(frame=state.frame,action=enemy['action'],clock=clock,input='B' if jump else 'R',direction='Right' if dx>0 else 'Left')
                        counterplay.append(entry);self.scratch['study_dodge']=entry
                    entry=self.scratch.get('study_dodge')
                    if entry:
                        age=state.frame-entry['frame']
                        if entry['input']=='B' and age<20:self.buttons.add('B')
                        elif entry['input']=='R' and age<24:
                            self.buttons.add(entry['direction'])
                            if age<7:self.buttons.add('R')
        return False
    lab.Walker.do_watch_enemy=watch
    def finish(self,step,state,ptr,ram):
        from tools.crane_creature_lab import pursuit_buttons
        self.on['alive']=True;self.buttons.clear()
        if self.t>=step[1]:return self.timeout(step,state,step[1],'native base-kit creature clearance')
        live=[e for e in state.enemies if e['hp']>0]
        if live and state.pos:
            self.scratch['finish_seen']=True;self.scratch['finish_empty']=0
            enemy=min(live,key=lambda e:abs(e['position'][0]/4096-state.pos[0]))
            self.buttons.update(pursuit_buttons(state.frame,state,enemy,False))
        else:
            self.scratch['finish_empty']=self.scratch.get('finish_empty',0)+1
            if self.scratch.get('finish_seen') and self.scratch['finish_empty']>=150:
                self.record('native_base_string_clear',True,state,enemy_hp_fixture=False,player_healing_during_clear_only=True);return True
        return False
    lab.Walker.do_finish_enemy=finish
    original_travel=lab.Walker.do_travel
    def approach(self,step,state,ptr,ram):
        # Real encounters can block a walk-only approach. Use native evade to
        # pass the actor without damaging it before the contact observation.
        if crane and self.t>0 and 'travel_dir' in self.scratch and state.pos and any(abs(e['position'][0]/4096-state.pos[0])<18 and abs(e['position'][1]/4096-state.pos[1])<16 for e in state.enemies) and self.t%90<8:
            self.buttons.clear();self.buttons.update(('Right' if step[1]>state.pos[0] else 'Left','R'));return False
        return original_travel(self,step,state,ptr,ram)
    lab.Walker.do_travel=approach
    approach_x=a.approach_x if a.approach_x is not None else 100 if crane else 122
    steps=[mw.wait(90),('travel',approach_x,2400 if crane else 1400)]
    if a.black:steps.extend((mw.hold('L',6),mw.wait(90),mw.check('native_black_form',lambda s:s.black==1)))
    steps.append(('watch_enemy',a.frames))
    if a.finish:steps.append(('finish_enemy',8000))
    steps.append(mw.wait(30))
    if crane:
        from tools import crane_walk as cw,crane_rooms
        cw.cr=crane_rooms;cw.install();cw.OUT=out;lab.OUT=out;mw.OUT=out
        cw.Walker=lab.Walker;lab.Walker.combat=True;lab.Walker.heal=False
        steps.extend((('end',None),mw.wait(a.frames+(8000 if a.finish else 0))))
        result=cw.run(a.rom,'contact-watch'+q.RUN_TAG,'AR_FreightExchange',1,steps)
        if pcm:
            with wave.open(str(out/('contact-watch'+q.RUN_TAG+'.wav')),'wb') as stream:stream.setparams((2,2,rate[0],0,'NONE','not compressed'));stream.writeframes(b''.join(pcm))
    else:result=q.run(a.rom,'contact-watch','ML_Station',1,steps,combat=True,heal=False)
    trace=result.get('forge_trace',[]);drops=[];programs=[];current=None
    for row in trace:
        if row.get('enemies'):
            e=row['enemies'][0]
            key=(e['actor'],e.get('action')) if e['state']==15 else None
            if key and (current is None or current['key']!=key or e['clock']<current['last_clock']):
                current=dict(key=key,start=row['frame'],end=row['frame'],first_clock=e['clock'],last_clock=e['clock'],start_hp=row['hp'],end_hp=row['hp'],enemy_start=e['position'],enemy_end=e['position']);programs.append(current)
            if key and current:
                current.update(end=row['frame'],last_clock=e['clock'],end_hp=row['hp'],enemy_end=e['position'])
            if not key:current=None
    for prev,row in zip(trace,trace[1:]):
        if row['hp']<prev['hp']:drops.append(dict(frame=row['frame'],damage_q12=prev['hp']-row['hp'],player=row['player'],enemies=row['enemies']))
    required={m['action'] for m in authored_programs}
    coverage=bool(programs and counterplay) if a.counterplay else required<=actual_hits if required else bool(programs and drops)
    report=dict(rom_sha256=w.sha256(a.rom.read_bytes()),passed=result['passed'] and coverage,native_route_passed=result['passed'],required_hit_actions=sorted(required),contact_coverage_passed=coverage,programs=programs,damage=drops,
        captures=result.get('captures'),raw_report=str(out/('walk-contact-watch'+q.RUN_TAG+'.json')),
        source_battery_unchanged=actual.read_bytes()==before,
        resets_between_programs=resets,
        counterplay_inputs=counterplay,
        actual_watch_hit_actions=sorted(actual_hits),
        limits='Copied battery; initial room arrival and isolated one-species budget. Native inputs/HP/AI; no attack forcing or position edits. Optional HP resets occur only between complete programs; clearance has separate player refills. Enemy HP stays native.')
    w.write_json(out/('contacts-'+a.style+'.json'),report)
    if audio_rows:w.write_json(out/('audio-context-'+a.style+'.json'),audio_rows)
    print(json.dumps(dict(captures=report['captures'],programs=programs,damage_events=len(drops),battery_unchanged=report['source_battery_unchanged'])))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
