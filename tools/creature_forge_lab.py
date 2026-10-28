"""Copied-save, native-input visual/combat probes for the enemy replacement."""
import argparse,json,struct,ctypes as ct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import chapter_renewal_lab as q,midnight_rework_lab as lab,midnight_walk as mw,kit_lab as k,player_trace as p,wos_tool as w
from tools import creature_forge_design as d
OUT=ROOT/'work/creature-forge'

def install(rom,capture=0):
    q.OUT=OUT;meta=q.report_runtime(rom,None);rt=meta['runtime'];q.install()
    original=lab.Walker.tick
    def tick(self,frame,lib):
        original(self,frame,lib)
        if frame>=0 and frame%2==0:
            _,ram=k.ram_of(lib);state=self.last_state
            if state:
                entries=[]
                for enemy in state.enemies:
                    a=enemy['actor']-p.BASE;cfg=w.u32(ram,a+0x40);style=next((s for s,e in meta['creatures'].items() if e['config']==cfg),None)
                    if not style:continue
                    m=w.u32(ram,a+0x30)-p.BASE
                    if w.u32(ram,m)!=enemy['actor']:continue
                    entries.append(dict(**enemy,style=style,velocity=struct.unpack_from('<2i',ram,a+0x18),clock=w.u32(ram,m+0x178),gmb=w.u32(ram,m+0x230),face=w.u32(ram,m+0x180)))
                self.report.setdefault('forge_trace',[]).append(dict(frame=frame,player=state.pos,hp=state.hp,black=state.black,player_state=state.state,enemies=entries))
                packed=struct.unpack_from('<28I',ram,rt['move_counters']-p.BASE)
                self.report['move_calls']=[v&65535 for v in packed];self.report['contact_move_calls']=[v>>16 for v in packed]
                self.report['contact_cue_calls']=w.u32(ram,rt['contact_cues']-p.BASE)
                if frame%120==0:
                    try:w.write_json(OUT/('probe-live-'+q.RUN_TAG.strip('-')+'.json'),dict(last=self.report['forge_trace'][-1],moves=self.report['move_calls'],cues=self.report['contact_cue_calls'],slots=list(struct.iter_unpack('<8I',ram[rt['slots']-p.BASE:rt['slots']-p.BASE+1024]))))
                    except PermissionError:pass  # Optional live probe may be open in a Windows reader.
    lab.Walker.tick=tick
    combat_step=lab.Walker.do_combat
    def phase_bait(self,step,state,ptr,ram):
        enemies=[e for e in state.enemies if w.u32(ram,e['actor']-p.BASE+0x40)==meta['creatures']['conductor']['config']]
        if not enemies:return combat_step(self,('combat',step[1]),state,ptr,ram)
        enemy=enemies[0]
        if enemy['hp']>enemy['max']//2:return combat_step(self,('combat',step[1]),state,ptr,ram)
        if self.t>=step[1]:return self.timeout(step,state,step[1],'native half-HP Crownfall qualification')
        if w.u32(ram,rt['move_counters']-p.BASE+27*4):
            self.record('Crownfall_selected_after_actual_half_HP',True,state,native_enemy_hp=enemy['hp'],native_enemy_max=enemy['max'],player_healing=True);return True
        self.buttons.clear()
        if state.pos:
            dx=enemy['position'][0]/4096-state.pos[0]
            if abs(dx)>10:self.buttons.add('Right' if dx>0 else 'Left')
        return False
    lab.Walker.do_phase_bait=phase_bait
    if capture:
        native=k._run
        def dense(*a,**kw):kw['caps']=tuple(range(0,kw['frames'],capture));return native(*a,**kw)
        dense._midnight_static=True
        k._run=dense
    return meta

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=('view','passive','duel','duel-all','boss','phase','roster','idle','pair','continue'))
    ap.add_argument('--rom',type=Path,required=True);ap.add_argument('--creature',choices=d.STYLES,default='warden');ap.add_argument('--capture-every',type=int,default=0)
    ap.add_argument('--tag',default='');ap.add_argument('--black',action='store_true');ap.add_argument('--no-heal',action='store_true');ap.add_argument('--persist',action='store_true')
    args=ap.parse_args(argv)
    if args.command=='duel-all':
        from concurrent.futures import ThreadPoolExecutor,as_completed
        import subprocess
        def run(style):
            label=args.tag+'-'+style;log=OUT/('duel'+label+'.log')
            with log.open('w') as stream:
                result=subprocess.run([sys.executable,str(Path(__file__)),'duel','--rom',str(args.rom),'--creature',style,'--tag='+label,
                    '--capture-every',str(args.capture_every)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
            name=('walk-duel-'+style if style in ('skitter','warden','eye') else 'duel-'+style+'-proof')+label+'.json'
            path=OUT/name;report=json.loads(path.read_text()) if path.exists() else {}
            calls=report.get('move_calls',[]);contacts=report.get('contact_move_calls',[]);index=d.STYLES.index(style)
            return style,dict(passed=bool(result.returncode==0 and report.get('passed') and len(calls)==28 and all(calls[index*4:index*4+3]) and len(contacts)==28 and all(contacts[index*4:index*4+3])),
                report=str(path.relative_to(ROOT)),moves=calls[index*4:index*4+3],contacts=contacts[index*4:index*4+3],cues=report.get('contact_cue_calls'))
        cases={}
        with ThreadPoolExecutor(3) as pool:
            for future in as_completed([pool.submit(run,style) for style in d.STYLES[:6]]):
                style,value=future.result();cases[style]=value;print(json.dumps([style,value]),flush=True)
        report=dict(rom_sha256=w.sha256(args.rom.read_bytes()),passed=all(v['passed'] for v in cases.values()),cases=cases)
        w.write_json(OUT/('duel-all'+args.tag+'.json'),report);return 0 if report['passed'] else 1
    q.RUN_TAG=args.tag
    if args.command=='duel' and args.creature in ('maw','ballast','spore'):
        q.OUT=OUT
        if args.capture_every:
            native=k._run
            def dense(*a,**kw):kw['caps']=tuple(range(0,kw['frames'],args.capture_every));return native(*a,**kw)
            k._run=dense
        result=q.duel(args.rom,args.creature);print(json.dumps(dict(passed=result.get('passed'))));return 0 if result['passed'] else 1
    install(args.rom,args.capture_every)
    if args.command=='view':
        if args.creature in ('skitter','warden','eye'):q.ISOLATE=args.creature
        result=q.run(args.rom,'forge-view-'+args.creature,'ML_Station',1,[mw.wait(90),('travel',100,1000),mw.wait(1500)],combat=True)
    elif args.command=='passive':
        q.ISOLATE=args.creature
        result=q.run(args.rom,'passive-'+args.creature,'ML_Station',1,[mw.wait(90),('travel',200,1400),mw.wait(1600)],combat=True)
    elif args.command=='duel':result=q.duel(args.rom,args.creature)
    elif args.command=='boss':result=q.combat(args.rom,black=args.black,persist=args.persist,heal=not args.no_heal)
    elif args.command=='roster':result=q.combat(args.rom,roster=True)
    elif args.command=='phase':result=q.run(args.rom,'conductor-phase','ML_Venom',2,[mw.wait(120),('phase_bait',9000),mw.wait(180),('combat',14000)],combat=True,heal=True)
    elif args.command=='continue':result=q.continue_earned(args.rom)
    elif args.command=='pair':result=q.pair(args.rom,'ML_Station',2)
    else:result=q.run(args.rom,'forge-idle','ML_Station',1,[mw.wait(1500)],combat=True)
    print(json.dumps(dict(passed=result.get('passed') if isinstance(result,dict) else result)))
    return 0 if (result['passed'] if isinstance(result,dict) else result) else 1
if __name__=='__main__':raise SystemExit(main())
