"""Sound rendering and aggressive-boss controls on copied batteries."""
import argparse,ctypes as ct,json,struct,sys,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import emulator_smoke as e,kit_lab as k,wos_tool as w,playtest


def render_proof(live,muted,style,out):
    """Match actual mixer output, retaining whether gameplay was paired exactly."""
    import numpy as np
    reports=[];tracks=[]
    for folder in (live,muted):
        d=json.loads((folder/('contacts-'+style+'.json')).read_text());reports.append(json.loads(Path(d['raw_report']).read_text()))
        with wave.open(str(next(folder.glob('*.wav')))) as f:
            tracks.append(np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(float).reshape(-1,2).mean(axis=1));rate=f.getframerate()
    exact=reports[0]['forge_trace']==reports[1]['forge_trace'];n=min(map(len,tracks));delta=tracks[0][:n]-tracks[1][:n]
    matches=[]
    def match(signal,template):
        length=len(template);size=1<<(len(signal)+length-1).bit_length()
        corr=np.fft.irfft(np.fft.rfft(signal,size)*np.conj(np.fft.rfft(template,size)),size)[:len(signal)-length+1]
        energy=np.concatenate(([0.],np.cumsum(signal*signal)));window=np.maximum(1,energy[length:]-energy[:-length])
        rho=corr/np.sqrt(np.sum(template*template)*window);rho[window/length<50**2]=0
        i=int(np.argmax(rho));return float(rho[i]),i/rate
    for cue in (style+'-tell',*(style+'-strike-'+str(i) for i in range(3))):
        with wave.open(str(ROOT/'work/midnight-voltage/audio'/(cue+'.wav'))) as f:
            raw=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(float);source_rate=f.getframerate()
        template=np.interp(np.arange(0,len(raw),source_rate/rate*1.0025),np.arange(len(raw)),raw)
        live_rho,time=match(delta if exact else tracks[0],template);muted_rho,other=match(tracks[1],template)
        matches.append(dict(cue=cue,live_correlation=live_rho,muted_correlation=muted_rho,time=time))
    passed=matches[0]['live_correlation']>.9 and any(m['live_correlation']>.9 for m in matches[1:])
    report=dict(passed=passed,style=style,gameplay_trace_exact=exact,live=str(live),muted=str(muted),matches=matches,
        owned_cue_difference_rms=float(np.sqrt(np.mean(delta*delta))) if exact else None,
        limits='Exact paired gameplay permits waveform subtraction; divergent gameplay uses live template matches with a silent-owned-wave control and does not claim a clean whole-mix difference. Role/sequence requests alone are insufficient.')
    out.mkdir(exist_ok=True,parents=True);w.write_json(out/('render-'+style+'.json'),report);print(json.dumps(report));return 0 if passed else 1


def boss_case(a):
    import os
    from tools import midnight_encore_lab as prior,midnight_rework_lab as lab
    from tools import midnight_voltage_motion as motion,crane_creature_lab as driver
    a.out.mkdir(parents=True,exist_ok=True);os.environ['WOS_CHAPTER_LAB_OUT']=str(a.out.resolve())
    meta=json.loads(a.rom.with_suffix('.build.json').read_text());state_address=meta.get('midnight_reliability',meta.get('midnight_finale',meta['midnight_voltage']))['runtime']['state'];rows=[]
    if 'midnight_finale' in meta:
        from tools.midnight_finale_motion import BOSS
        boss_moves=BOSS
    else:boss_moves=motion.MOVES
    native=lab.Walker.tick
    def tick(self,frame,lib):
        result=native(self,frame,lib)
        if frame>=0 and frame%2==0 and self.last_state:
            ram=self.last_ram
            words=struct.unpack_from('<12I',ram,state_address-0x02000000)
            row=dict(frame=frame,state=words,player_hp=self.last_state.hp,player=self.last_state.pos)
            if 'midnight_reliability' in meta:
                row['physics']=struct.unpack_from('<8I',ram,state_address-0x02000000+48)
                address=meta['midnight_reliability']['runtime'].get('hit_log')
                if address and frame%120==0:
                    off=address-0x02000000;n=min(w.u32(ram,off),64)
                    entries=[struct.unpack_from('<8I',ram,off+4+i*32) for i in range(n)]
                    w.write_json(a.out/'native-hits-live.json',dict(frame=frame,rows=entries))
            rows.append(row);self.report.setdefault('voltage_response_trace',[]).append(row)
            if frame%120==0:w.write_json(a.out/'response-live.json',row)
        return result
    lab.Walker.tick=tick
    native_combat=lab.Walker.do_combat
    def combat(self,step,state,ptr,ram):
        if a.case!='press':result=native_combat(self,step,state,ptr,ram)
        else:
            self.buttons.clear()
            if state.flags>>147&1:self.record('pressure_driver_native_victory',True,state,player_refills=self.heal);return True
            if state.hp<=0 or self.t>=step[1]:return self.timeout(step,state,self.t,'continuous base-string pressure')
            result=False
            if state.pos and state.enemies:
                enemy=min(state.enemies,key=lambda e:abs(e['position'][0]/4096-state.pos[0]));dx=enemy['position'][0]/4096-state.pos[0];dy=enemy['position'][1]/4096-state.pos[1]
                if abs(dx)>5.5:self.buttons.add('Right' if dx>0 else 'Left')
                if abs(dx)<13 and abs(dy)<14 and state.frame%8<3:self.buttons.add('Y')
                if dy>9 and state.frame%64<36:self.buttons.add('B')
            elif state.pos:self.buttons.add('Right' if state.pos[0]<90 else 'Left')
        if result:return result
        if a.reactive and state.pos and state.enemies:
            enemy=state.enemies[0]
            if enemy['state']==15:
                move=next((m for m in boss_moves if m.action==enemy['action']),None)
                if move:
                    dx=enemy['position'][0]/4096-state.pos[0]
                    mot=w.u32(ram,enemy['actor']-0x02000000+0x30)-0x02000000;clock=w.u32(ram,mot+0x178)
                    for ci,(start,end) in enumerate(move.contacts):
                        if start-4<=clock<start and self.scratch.get('voltage_dodge')!=(move.action,ci):
                            dx=enemy['position'][0]/4096-state.pos[0];button='B' if move.kind=='fugue' or move.kind in ('crownfall','verdict') and ci==1 else 'R'
                            if a.black and move.kind=='cadenza' and ci==0:button='B'
                            face=w.u32(ram,mot+0x180);behind=bool(dx>0 and face==1 or dx<0 and face==0)
                            if button=='R' and behind and not (a.black and move.kind=='cadenza' and ci==1):continue
                            if move.kind=='verdict' and ci==0 and state.pos[1]<8:continue
                            self.scratch.update(voltage_dodge=(move.action,ci),dodge_start=state.frame,dodge_way='Right' if dx>0 else 'Left',dodge_input=button)
                            self.report.setdefault('voltage_counterplay',[]).append(dict(frame=state.frame,action=move.action,clock=clock,input=button))
                    age=state.frame-self.scratch.get('dodge_start',-100)
                    if 0<=age<16:
                        self.buttons.difference_update(('Left','Right'));self.buttons.add(self.scratch['dodge_way'])
                        button=self.scratch['dodge_input']
                        if age<8:self.buttons.difference_update(('Y','A'))
                        if age<(18 if button=='B' else 6):self.buttons.add(button)
                    if a.black and state.pos[1]>12 and state.pos[1]-enemy['position'][1]/4096>8 and abs(dx)<16 and state.frame%44<5 and age>=8:
                        self.buttons.update(('Down','Y'))
                        if state.frame%44==0:self.report.setdefault('voltage_offense',[]).append(dict(frame=state.frame,input='Down+Y',reason='Native shared air stomp above the target'))
            else:self.scratch.pop('voltage_dodge',None)
        if state.pos:
            if state.pos[0]<22:self.buttons.discard('Left');self.buttons.add('Right')
            if state.pos[0]>202:self.buttons.discard('Right');self.buttons.add('Left')
        return False
    lab.Walker.do_combat=combat
    sys.argv=[sys.argv[0],'conductor','--rom',str(a.rom),'--tag='+a.tag,'--capture-every',str(a.capture_every)]
    for flag,on in (('--no-heal',a.no_heal),('--black',a.black),('--persist',a.persist)):
        if on:sys.argv.append(flag)
    result=prior.main()
    report=dict(rom_sha256=w.sha256(a.rom.read_bytes()),case=a.case,maximum_counters=max((r['state'][7] for r in rows),default=0),
        observed_actual_HP_losses=max((r['state'][9] for r in rows),default=0),rows=rows,
        limits='Underlying copied-save conductor report owns arrival/ability/healing fixtures. Pressure driver uses base Y strings and pursuit without programmed R/A. Production feedback responds to actual native HP loss.')
    w.write_json(a.out/('response'+a.tag+'.json'),report);print(json.dumps({k:v for k,v in report.items() if k not in ('rows','limits')}));return result


def sound(rom,out):
    out.mkdir(parents=True,exist_ok=True);actual=playtest.current_save();before=actual.read_bytes();save=out/'player-copy.dsv';save.write_bytes(before)
    meta=json.loads(rom.with_suffix('.build.json').read_text());probe=meta['voltage_sound_probe'];pcm=[];seen=[];rate=[0]
    def hook(frame,lib):
        if not rate[0]:
            info=(ct.c_byte*40)();lib.retro_get_system_av_info.argtypes=[ct.c_void_p];lib.retro_get_system_av_info(ct.byref(info));rate[0]=round(struct.unpack_from('<d',bytes(info),32)[0])
            lib._wos_audio_sink=lambda f,b:pcm.append(b) if f>=3000 else None
        if frame>=3000 and frame%120==0:
            _,ram=k.ram_of(lib);at=probe['log']-0x02000000;count=w.u32(ram,at)
            seen.append(dict(frame=frame,count=count,rows=[struct.unpack_from('<4I',ram,at+4+(i%128)*16) for i in range(max(0,count-128),count)]))
    script=[r for r in json.loads((ROOT/'reference/combat-inputs/oscorp-reload.json').read_text()) if r['start']<1400]
    caps=e.run(rom,4500,{3100,4400},save_path=save,script=script,label='voltage-sound-'+str(probe['sound']),frame_hook=hook,
        core_options={b'melonds_jit_enable':b'enabled',b'melonds_jit_block_size':b'12'})
    with wave.open(str(out/'mixed.wav'),'wb') as f:f.setparams((2,2,rate[0],0,'NONE','not compressed'));f.writeframes(b''.join(pcm))
    report=dict(rom_sha256=w.sha256(rom.read_bytes()),probe=probe,observations=seen,captures=str(caps),source_battery_unchanged=actual.read_bytes()==before)
    w.write_json(out/'sound.json',report);print(json.dumps(dict(out=str(out),last=seen[-1] if seen else None)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('case',nargs='?',default='sound',choices=('sound','boss','press','analyze'));p.add_argument('--rom',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--live',type=Path);p.add_argument('--muted',type=Path);p.add_argument('--style',default='skitter')
    p.add_argument('--tag',default='');p.add_argument('--capture-every',type=int,default=12);p.add_argument('--reactive',action='store_true');p.add_argument('--no-heal',action='store_true');p.add_argument('--black',action='store_true');p.add_argument('--persist',action='store_true');a=p.parse_args()
    if a.case=='analyze':raise SystemExit(render_proof(a.live,a.muted,a.style,a.out))
    if a.rom is None:p.error('--rom is required for gameplay controls')
    if a.case=='sound':sound(a.rom,a.out)
    else:raise SystemExit(boss_case(a))
