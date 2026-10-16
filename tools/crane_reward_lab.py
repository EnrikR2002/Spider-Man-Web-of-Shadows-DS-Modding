"""Copied-save reward controls: one native strike kills an isolated1HP creature.

Player healing is disabled. A labelled chase placement isolates pickup behavior;
this control does not qualify traversal, enemy difficulty or normal combat HP.
"""
import argparse,ctypes as ct,json,struct,sys,wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import crane_creatures as creatures,crane_creature_lab as duels
from tools import crane_walk as cw,midnight_walk as mw,kit_lab as k,player_trace as p,wos_tool as w

XP=0x44

def audio_trace(ptr,ram):
    """Disposable post-remap call counter in unused Crane-tail RAM; no ROM edit."""
    from tools import crane_audio,crane_row
    from tools.crane_boss import Arm
    at=crane_row.CR_BASE+0x1F00;table=crane_row.CR_BASE+0x1FC0;site=crane_audio.SITE+4
    if w.u32(ram,site-p.BASE)!=0xE24DD00C:raise ValueError('Native sound continuation changed')
    if any(ram[at-p.BASE:table-p.BASE]):raise ValueError('Audio probe tail is occupied')
    a=Arm(at);a.emit(0xE92D100F,0xE10FC000);a.lit(0,'first',crane_audio.FIRST)
    a.lit(2,'table',table);a.emit(0xE582103C)
    a.emit(0xE1510000);a.b('done',3);a.emit(0xE0411000,0xE351000F);a.b('done',2)
    a.lit(2,'table');a.emit(0xE0822101,0xE5923000,0xE2833001,0xE5823000)
    a.label('done');a.emit(0xE128F00C,0xE8BD100F,0xE24DD00C);a.b(site+4)
    raw=a.finish()
    if at+len(raw)>table:raise ValueError('Audio probe exceeds private scratch')
    ct.memmove(ptr+at-p.BASE,raw,len(raw));ct.memmove(ptr+site-p.BASE,struct.pack('<I',crane_row.branch(site,at)),4)
    return table

def reward_summary(rows):
    setup=[r for r in rows if r['frame']>=150]
    dead=[r for r in setup if r['dead']]
    if not setup or not dead:return {'passed':False,'reason':'No sampled real lethal hit'}
    start=setup[0];end=setup[-1]
    gains=sum(max(0,b['hp']-a['hp']) for a,b in zip(setup,setup[1:]))
    return {'passed':end['xp']>start['xp'] and gains>0,'xp_before':start['xp'],'xp_after':end['xp'],
            'xp_awarded':end['xp']-start['xp'],'health_recovered_q12':gains,'first_death':dead[0]['frame']}

def run(rom,key,*,zero_reward=False,audio=False,tag=''):
    rom=Path(rom);runtime=duels.metadata(rom);spec=creatures.BY_KEY[key];cw.install();holder={}
    class RewardWalker(cw.Walker):
        def __init__(self,*args,**kw):
            super().__init__(*args,**kw);self.rows=[];self.started=False;self.pcm=[];self.audio_installed=False;self.audio_rate=None;self.sound_counts=[0]*15;self.sound_ids=set();holder['walker']=self
        def do_reward_setup(self,step,state,ptr,ram):
            if not state.pos or state.state not in (0,1,4,5,6):
                return self.timeout(step,state,400,'native reward-fixture stance')
            stats=w.u32(ram,k.STATS_POINTER-p.BASE)-p.BASE
            ct.memmove(ptr+stats+0x84,struct.pack('<I',12288),4);self.started=True
            self.rows.append({'frame':state.frame,'xp':w.u32(ram,stats+XP),'hp':12288,'dead':False,'enemies':state.enemies,
                              'player':state.pos,'player_state':state.state,
                              'reward_word':w.u32(ram,runtime['configs'][key]-p.BASE+0x50)})
            return True
        def tick(self,frame,lib):
            ptr,ram=k.ram_of(lib)
            if frame+k.TRAINING_START>=2040:
                ct.memmove(ptr+runtime['state']-p.BASE,struct.pack('<2I',102,{'maw':0,'spore':1,'ballast':2}[key]),8)

                for name,goal in runtime['goals'].items():
                    cost=0 if name=='upper' else spec.cost*4096
                    ct.memmove(ptr+goal-p.BASE,struct.pack('<2I',cost,cost),8)
                if zero_reward:
                    for address in (runtime['configs'][key]+0x50,creatures.CONFIG_TABLE+(spec.kind-2)*84+0x50):
                        ct.memmove(ptr+address-p.BASE,bytes(4),4)
            s=self.read(frame,ram)
            if audio and not self.audio_installed and frame>=0:
                self.audio_table=audio_trace(ptr,ram)
                info=(ct.c_byte*40)();lib.retro_get_system_av_info.argtypes=[ct.c_void_p]
                lib.retro_get_system_av_info(ct.byref(info));self.audio_rate=round(struct.unpack_from('<d',bytes(info),32)[0])
                lib._wos_audio_sink=lambda f,data:self.pcm.append(data) if f>=k.TRAINING_START+150 else None
                self.audio_installed=True
            if audio and self.audio_installed:
                self.sound_counts=list(struct.unpack_from('<15I',ram,self.audio_table-p.BASE))
                self.sound_ids.add(w.u32(ram,self.audio_table-p.BASE+60))
            if s and s.room==102 and s.pos:
                stats=w.u32(ram,k.STATS_POINTER-p.BASE)-p.BASE
                if self.started and frame%2==0:
                    owned=[]
                    for e in k.enemies(ram):
                        actor=e['actor']-p.BASE;motion=w.u32(ram,actor+0x30)-p.BASE
                        if not 0<motion<len(ram)-0x300 or w.u32(ram,motion)!=e['actor']:continue
                        if w.u32(ram,actor+0x40)!=runtime['configs'][key]:continue
                        e={**e,'flags':w.u32(ram,actor+0x88),'controller_type':w.u32(ram,e['controller']-p.BASE) if e['controller'] else None}
                        owned.append(e)
                    self.rows.append({'frame':frame,'xp':w.u32(ram,stats+XP),'hp':s.hp,
                        'player':s.pos,'player_state':s.state,
                        'dead':any(e['hp']<=0 for e in owned),'enemies':owned,
                        'reward_word':w.u32(ram,runtime['configs'][key]-p.BASE+0x50)})
                    if any(e['hp']<=0 for e in owned) and not self.scratch.get('reward_ram_saved'):
                        self.scratch['reward_ram_saved']=True;self.scratch['native_dead']=True
                        w.atomic_write(cw.OUT/'rework'/('reward-'+key+tag+'-'+w.sha256(rom.read_bytes())[:8]+'-death-ram.bin'),ram)
                if self.started and s.enemies and self.i<len(self.steps) and self.steps[self.i][0]=='until':
                    e=s.enemies[0]
                    # An idle1HP target is a reward fixture, not an AI duel.
                    if e['controller']:ct.memmove(ptr+e['controller']-p.BASE+0x14,bytes(4),4)
            super().tick(frame,lib)
            if self.i<len(self.steps) and self.steps[self.i][0]=='until' and s and s.pos and s.enemies:
                e=s.enemies[0];self.buttons.clear();self.buttons.update(duels.pursuit_buttons(frame,s,e))
    cw.Walker=RewardWalker
    label='reward-'+key+('-zero' if zero_reward else '-native')+tag
    result=cw.run(rom,label,'AR_Counterweight',1,[mw.fixtures(fight=False,alive=False),
        mw.wait(180),('reward_setup','baseline'),mw.fixtures(fight=True),
        mw.until('native_lethal_hit',lambda state:bool(holder['walker'].scratch.get('native_dead')),2500),mw.wait(400)])
    walker=holder['walker'];summary=reward_summary(walker.rows)
    passed=result['passed'] and (summary.get('xp_awarded')==0 and summary.get('health_recovered_q12')==0 if zero_reward else summary['passed'])
    out=cw.OUT/'rework'/f'{label}-{result["rom_sha256"][:8]}.json'
    w.write_json(out,{'passed':passed,'summary':summary,'route':result,'rows':walker.rows,'private_audio_calls':walker.sound_counts,
        'observed_sound_ids':sorted(walker.sound_ids),
        'limits':'Copied save; isolated idle1HP creature, native room arrival/movement/Y strikes. No actor placements or player healing. Does not establish difficulty/AI.'})
    if walker.pcm:
        with wave.open(str(out.with_suffix('.wav')),'wb') as stream:
            stream.setnchannels(2);stream.setsampwidth(2);stream.setframerate(walker.audio_rate);stream.writeframes(b''.join(walker.pcm))
    print(json.dumps({**summary,'report':str(out),'passed':passed}));return passed

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--rom',type=Path,required=True)
    ap.add_argument('--creature',choices=tuple(creatures.BY_KEY),required=True);ap.add_argument('--zero-reward',action='store_true')
    ap.add_argument('--audio',action='store_true');ap.add_argument('--tag',default='');args=ap.parse_args()
    raise SystemExit(0 if run(args.rom,args.creature,zero_reward=args.zero_reward,audio=args.audio,tag=args.tag) else 1)
