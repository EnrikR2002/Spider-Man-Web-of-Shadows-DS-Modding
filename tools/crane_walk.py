"""Crane Row lab: copied-save views and actual-input door/traversal checks."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
import struct
import subprocess
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import crane_rooms as cr, crane_row, midnight_chapter as ch, midnight_walk as mw
from tools import room_collision, wos_tool as w
from tools import crane_boss as cb

OUT=ROOT/'work/crane-row'
MACHINE_DATA={}

def machine_records(path):
    from tools import tasm_kit as kit
    raw=Path(path).read_bytes();h=w.parse_header(raw);arm=raw[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    fs=next(e for e in w.validate_rom(raw,target=True)['nitrofs'] if e['name']=='Glob.bin')
    _,names,_=w.parse_glob(raw[fs['start']:fs['end']])
    result={}
    for key,kind in (('warning',cb.WARN),('motor',cb.MOTOR),('hook',cb.HOOK),('shield',cb.SHIELD),('weight',cb.HOOK)):
        model=names.index(f'zz_CR_{key}.nsbmd')
        at=arm.find(struct.pack('<3I',0,0xB6,model),kit.SOURCE+kit.RESERVE+ch.ML_SPACE)
        if at>=0:result[kit.TARGET+at-kit.SOURCE]=kind
    return result

def install():
    # Lab registry only; the production Midnight registry never owns these IDs.
    ch.BY_NAME={**ch.BY_NAME,**{n:SimpleNamespace(index=i) for n,i in cr.IDS.items()},'Pier_Save02':SimpleNamespace(index=38)}
    native_visit=ch.visited
    ch.visited=lambda i:cr.VISITS[i] if i in cr.VISITS else native_visit(i)
    mw.OUT=OUT
    original=mw.rom_objects
    def objects(path):
        result=original(path);raw=Path(path).read_bytes()
        fs=next(e for e in w.validate_rom(raw,target=True)['nitrofs'] if e['name']=='Glob.bin')
        glob=raw[fs['start']:fs['end']];offsets,names,_=w.parse_glob(glob)
        for n,i in {**cr.IDS,'Pier_Save02':38}.items():
            index=names.index('Pier_Save02_app.obj' if i==38 else f'zz_{n}_app.obj')
            result[i]=glob[offsets[index]:offsets[index+1]]
        return result
    mw.rom_objects=objects

class Walker(mw.Walker):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.on['fight']=False

    def tick(self,frame,lib):
        super().tick(frame,lib)
        if self.on['fight'] and self.buttons and 'Y' in self.buttons:
            from tools import kit_lab as k
            state=self.read(frame,k.ram_of(lib)[1])
            if state and state.state==9 and self.i<len(self.steps) and self.steps[self.i][0] in ('navigate','travel','land'):
                self.buttons.discard('Y')
            if state and state.pos and not any(abs(e['position'][0]/4096-state.pos[0])<15 and
                abs(e['position'][1]/4096-state.pos[1])<12 for e in state.enemies):self.buttons.discard('Y')

    def do_travel(self,step,state,ptr,ram):
        _,x,timeout=step
        if state.pos is None:return self.timeout(step,state,timeout,'travel pose')
        if self.t==0:self.scratch.update(travel_dir='Right' if x>state.pos[0] else 'Left',travel_x=state.pos[0],travel_stall=0,travel_jump=0)
        way=self.scratch['travel_dir']
        if (state.pos[0]>=x if way=='Right' else state.pos[0]<=x):
            self.record('travel_to_'+str(x),True,state);return True
        if self.t>=timeout:return self.timeout(step,state,timeout,'travel to '+str(x))
        self.buttons.clear();self.buttons.add(way)
        stalled=abs(state.pos[0]-self.scratch['travel_x'])<.1
        self.scratch['travel_stall']=self.scratch['travel_stall']+1 if stalled else 0
        self.scratch['travel_x']=state.pos[0]
        jump=self.scratch['travel_jump']
        if self.scratch['travel_stall']>8 and jump<=0 and state.state in (0,1,4,5,6,7,16):jump=28
        if jump>0:self.buttons.add('B')
        self.scratch['travel_jump']=jump-1
        if state.state in (7,9,16):self.buttons.add('Up')
        return False

    def do_land(self,step,state,ptr,ram):
        """Reach a platform with native inputs; no position or velocity writes.

        Enemies may be parked by an explicitly labelled traversal fixture.
        The destination is the standing player position, five above the deck.
        """
        _,x,y,timeout=step
        if state.pos is None:return self.timeout(step,state,timeout,'landing pose')
        px,py=state.pos
        if self.t==0:self.scratch.update(landing_x=px,landing_ground=False,landing_settled=0,
                                        landing_descent=py>y+3,landing_pause=8 if abs(x-px)<28 else 0)
        vx=px-self.scratch['landing_x'];self.scratch['landing_x']=px
        ground=state.state in (0,1,4,5,6,24)
        if abs(px-x)<12 and abs(py-y)<2 and ground:self.scratch['landing_ground']=True
        if py<y-4:self.scratch.update(landing_ground=False,landing_descent=False)
        settled=abs(px-x)<2 and abs(py-y)<2 and state.state in (0,1,4,5,6) and abs(vx)<.12
        self.scratch['landing_settled']=self.scratch['landing_settled']+1 if settled else 0
        if self.scratch['landing_settled']>=12:
            self.record('land_'+str(x)+'_'+str(y),True,state);return True
        if self.t>=timeout:return self.timeout(step,state,timeout,'native landing '+str((x,y)))
        self.buttons.clear()
        if self.t%6==0:self.report.setdefault('landing_control',[]).append([state.frame,x,y,px,py,state.state])
        if self.scratch['landing_ground']:
            # Release B after a real contact and brake before the destination.
            # Repeating jumps while trying to hit one coordinate made a valid
            # landing look impossible and could walk the driver off its edge.
            if abs(px-x)>max(1,abs(vx)*8):self.buttons.add('Right' if x>px else 'Left')
            return False
        # Gain clearance before moving under a higher platform's leading edge.
        if abs(px-x)>1 and not (py<y-3 and self.t%64<self.scratch['landing_pause']):self.buttons.add('Right' if x>px else 'Left')
        # Held jump -> release -> retry. A second airborne B is the native
        # web swing. Controller state never substitutes for a RAM placement.
        if self.t<40 or not self.scratch['landing_descent'] and self.t%64<40:self.buttons.add('B')
        if state.state in (7,9,16) and py<y:self.buttons.add('Up')
        return False

    def read(self,frame,ram):
        state=super().read(frame,ram)
        if state is None:return state
        if state.room in cr.IDS.values():
            from tools import player_trace as p
            w,h=cr.BOUNDS[state.room-96]
            real=[]
            for enemy in state.enemies:
                motion=struct.unpack_from('<I',ram,enemy['actor']-p.BASE+0x30)[0]-p.BASE
                if not 0<motion<len(ram)-0x300 or struct.unpack_from('<I',ram,motion)[0]!=enemy['actor']:continue
                x,y=(v/4096 for v in enemy['position'])
                if enemy['state'] is None or not (-80<x<w+80 and -50<y<h+100):continue
                real.append(enemy)
            state.enemies=real
        state.machines=[]
        if state.room in (102,106):
            found=set()
            for vtable in (0x0212F7A0,0x0212F2D4):
                at=0
                while (at:=ram.find(struct.pack('<I',vtable),at+4))>=0:
                    if at<0x150000 or at+0x174>len(ram) or at%4:continue
                    kind,hp=struct.unpack_from('<2I',ram,at+0x10C)
                    if kind not in (cb.CORE,cb.HOOK,cb.MOTOR,cb.SHIELD,cb.WARN):continue
                    x,y=struct.unpack_from('<2i',ram,at+0x90)
                    if abs(x)>4096*1024 or abs(y)>4096*1024:continue
                    state.machines.append([kind,hp,x/4096,y/4096,ram[at+0x131],ram[at+0x168],hex(at+0x02000000)])
                    found.add(at)
            for data,kind in MACHINE_DATA.items():
                pos=0
                while (pos:=ram.find(struct.pack('<I',data),pos+4))>=0:
                    at=pos-0x108
                    if at in found or at<0x150000 or at+0x174>len(ram) or at%4:continue
                    vt=struct.unpack_from('<I',ram,at)[0]
                    if not 0x0212F000<=vt<0x02130000 or struct.unpack_from('<I',ram,at+0x10C)[0]!=kind:continue
                    hp=struct.unpack_from('<I',ram,at+0x110)[0];x,y=struct.unpack_from('<2i',ram,at+0x90)
                    if abs(x)>4096*1024 or abs(y)>4096*1024:continue
                    state.machines.append([kind,hp,x/4096,y/4096,ram[at+0x131],ram[at+0x168],hex(at+0x02000000),hex(vt)])
                    found.add(at)
            if frame>=0 and frame%12==0 and state.sample is not None:
                self.report.setdefault('machinery',[]).append([frame,state.room,list(state.room_vars),state.machines,state.hp])
        return state

    def do_machine_attack(self,step,state,ptr,ram):
        if self.t%240==0:
            w.write_json(OUT/('live-combat-'+('black' if state.black else 'red')+'.json'),
                {'rom_sha256':self.report.get('candidate_sha256'),'frame':state.frame,'hp':state.hp,'position':state.pos,'vars':state.room_vars,'machines':state.machines})
        if state.flags>>cr.FLAGS['boss']&1:
            self.record('hoist_defeated',True,state,frames=self.t);return True
        if self.t>=step[1]:return self.timeout(step,state,step[1],'hoist defeat')
        if state.hp<=0:return self.timeout(step,state,self.t,'player defeated before hoist')
        if state.pos is None:return False
        self.buttons.clear()
        exposed=len(state.room_vars)>1 and state.room_vars[1]==1
        x=state.pos[0];target=cb.MOTOR_X+7 if exposed else 392
        mode=state.room_vars[4] if len(state.room_vars)>4 else 0
        near=min(state.enemies,key=lambda e:abs(e['position'][0]/4096-x),default=None)
        if abs(x-target)>1.5:self.buttons.add('Right' if target>x else 'Left')
        elif exposed and self.t%16<2:self.buttons.add('Left' if x>cb.MOTOR_X else 'Right')
        elif near and self.t%16<2:self.buttons.add('Right' if near['position'][0]/4096>x else 'Left')
        in_reach=(abs(x-(cb.MOTOR_X+7))<5 and state.pos[1]<11) if exposed else x>386 and near and abs(near['position'][0]/4096-x)<9
        if in_reach and self.t%12<5:self.buttons.add('Y')
        if (x<cb.MOTOR_X+4 or mode in (2,4) and x<390) and state.pos[1]<14 and self.t%36<24:self.buttons.add('B')
        if near and near['state'] in (15,16) and abs(near['position'][0]/4096-x)<14 and self.t%24<6:
            self.buttons.add('R')
        return False

    def do_navigate(self,step,state,ptr,ram):
        _,name,group,timeout=step
        if state.room!=cr.IDS.get(name,38):return True
        if state.pos is None:return self.timeout(step,state,timeout,'live pose for '+name)
        if self.t>=timeout:return self.timeout(step,state,timeout,'reach '+name+' door '+str(group))
        self.buttons.clear()
        if state.state==29:
            # Native WebHangIdle: repeated traversal jumps can attach a web
            # below a raised dock. Release it before resuming the route.
            if self.t%24<6:self.buttons.add('B')
            else:self.buttons.add('Down')
            return False
        if name=='Pier_Save02':
            self.buttons.add('Right' if group==2 else 'Left');return False
        side,wall,floor,_=cr.PORTS[name][group-1]
        x,y=state.pos
        if self.t==0:
            self.scratch.update(nav_pos=(x,y),nav_jump=-8,nav_stall=0)
            self.scratch.pop('climb_start',None)
        way='Left' if side=='left' else 'Right'
        self.buttons.add(way)
        near=x<18 if side=='left' else x>wall-18
        if not floor and near and y>20:
            self.buttons.add('Down')
            return False
        if floor:
            edge=12 if side=='left' else wall-12
            near=x<18 if side=='left' else x>wall-18
            if near:
                if floor-5<=y<=floor+14:
                    if self.t%12<5:self.buttons.add('X')
                    return False
                if y>floor+14:
                    self.buttons.add('Down')
                    return False
                self.scratch.setdefault('climb_start',state.frame)
                age=state.frame-self.scratch['climb_start']
                if age<32 or name==cr.NAMES[0] and group==3 and age%48<28:self.buttons.add('B')
                if age<8:self.buttons.discard(way)
                else:self.buttons.add('Up')
                if floor+1<=y<=floor+13 and age%12<5:self.buttons.add('X')
                return False
        last=self.scratch.get('nav_pos',(x,y))
        stalled=self.t>0 and abs(x-last[0])<.1
        self.scratch['nav_stall']=self.scratch.get('nav_stall',0)+1 if stalled else 0
        self.scratch['nav_pos']=(x,y)
        jump=self.scratch.get('nav_jump',0)
        if self.scratch['nav_stall']>=8 and state.state in (0,1,4,5,6,7,16) and jump<=-8:jump=28
        if jump>0:
            self.buttons.add('B');self.scratch['nav_jump']=jump-1
        else:self.scratch['nav_jump']=max(-20,jump-1)
        if state.state in (7,9,16):self.buttons.add('Up')
        return False

def nav(name,group,timeout=2200):return ('navigate',name,group,timeout)

# Native entrance -> set-piece landings -> real exit. Separate from the broad
# door controller, these require the authored platforms instead of bypassing
# an entire room along its outer walls. y is standing position, not feet.
SETPIECES={
    'quay':(0,1,2,((60,5),(100,21),(112,21),(156,23),(168,23),(204,41),(222,41),(264,59),(290,59),(318,5))),
    'freight-roofs':(1,1,4,((64,25),(98,47),(118,47),(152,69),(184,69),(232,89),(264,89),(312,109),(372,117))),
    'cargo-canyon':(3,1,2,((42,5),(72,23),(112,43),(150,49),(188,69),(210,69),(230,89),(264,109),(320,87),(356,5))),
    'ship-deck':(4,1,2,((40,69),(104,73),(130,73),(180,95),(190,95),(250,113),(310,93),(374,69))),
    'shaft':(6,1,2,((48,23),(72,23),(102,45),(82,67),(102,89),(72,111),(102,133),(82,155),(102,177),(144,197))),
    'broken-gantry':(7,1,2,((48,5),(98,5),(118,5),(166,21),(202,21),(254,5),(284,5),(332,25),(354,25),(394,5))),
    'crown':(9,1,3,((102,21),(92,21),(58,43),(78,43),(132,63),(156,63),(210,83),(234,83),(296,101))),
}

def run(rom,label,start,spawn,steps,preset=()):
    original=mw.Walker;mw.Walker=Walker
    # Navigator timeouts contribute to the run budget via the standard until
    # representation used by the base harness. A generous final wait is safe:
    # the frame hook stops immediately when the actual steps finish.
    steps=list(steps)
    budget=sum(step[3] if step[0] in ('navigate','land') else step[1] if step[0]=='machine_attack' else step[2] if step[0]=='travel' else 0 for step in steps)
    steps.append(mw.wait(1))
    base_run=mw.run_child
    # run_child's step budget doesn't know this extra step type. Reserve
    # sufficient budget in one inert final wait; the navigator ends normally.
    steps[-1]=mw.wait(budget)
    finish=steps[:-1]
    # Stop once the meaningful steps have completed, rather than waiting the
    # budget padding. This leaves the padding available to the native driver.
    class TimedWalker(Walker):
        def __init__(self,*pos,**kw):
            super().__init__(*pos,**kw)
            self.report['candidate_sha256']=w.sha256(Path(rom).read_bytes())
        def tick(self,frame,lib):
            if self.i>=len(finish):self.i=len(self.steps);return
            return super().tick(frame,lib)
    mw.Walker=TimedWalker
    try:base_run(rom,label,(start,spawn,preset,steps))
    finally:mw.Walker=original
    report=json.loads((OUT/f'walk-{label}.json').read_text())
    report['preset_flags']=list(preset)
    w.write_json(OUT/f'walk-{label}.json',report)
    w.write_json(OUT/f"walk-{label}-{report['rom_sha256'][:8]}.json",report)
    print(json.dumps(mw.summary(report)))
    return report

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('entry','cross','view','save','machine','power','all','map','setpiece'))
    p.add_argument('name',nargs='?',default=cr.NAMES[0]);p.add_argument('points',nargs='*')
    p.add_argument('--rom',type=Path,default=ROOT/'build/crane-row/dev.nds')
    p.add_argument('--spawn',type=int,default=1);p.add_argument('--group',type=int,default=2)
    p.add_argument('--preset',default='',help='Copied-save fixture: comma-separated Crane flags')
    p.add_argument('--no-heal',action='store_true');p.add_argument('--black',action='store_true')
    p.add_argument('--purchased-vitality',action='store_true',help='Copied-save combat fixture: existing Vitality I..III purchases; no refills')
    p.add_argument('--purchased-kit',action='store_true',help='Copied-save combat fixture: existing extra kit and Vitality purchases (word2 0x7fc00)')
    p.add_argument('--tag',default='',help='Distinct evidence label for another controller trial')
    p.add_argument('--combat-frames',type=int,default=5000,help='Native combat deadline, excluding setup')
    p.add_argument('--verify-clear',action='store_true',help='After a real victory, park leftover crew and measure hazard cleanup/revisit')
    p.add_argument('--fight',action='store_true',help='Traversal fixture: 1HP crew, native strikes; not a difficulty test')
    p.add_argument('--jobs',type=int,default=2)
    args=p.parse_args(argv);install();MACHINE_DATA.update(machine_records(args.rom))
    if args.command=='setpiece':
        i,spawn,group,points=SETPIECES[args.name];name=cr.NAMES[i]
        steps=[mw.wait(90),mw.fixtures(fight=False,park=(-60,-60)),mw.wait(20)]
        for x,y in points:steps += [('land',x,y,900),mw.wait(12)]
        wanted=cr.IDS[cr.LINKS[name,group][0]]
        dest=cr.LINKS[name,group][0];dw,dh=cr.BOUNDS[cr.NAMES.index(dest)]
        bottom=cr.LOWER.get(cr.NAMES.index(dest),0)
        steps += [nav(name,group),mw.wait(80),mw.until('setpiece_real_exit',
            lambda s:s.room==wanted and s.pos is not None and 0<s.pos[0]<dw and bottom<s.pos[1]<dh,600)]
        return run(args.rom,'setpiece-'+args.name+args.tag,name,spawn,steps,tuple(cr.FLAGS.values()))
    elif args.command=='entry':
        return run(args.rom,'pier-entry','Pier_Save02',1,[mw.wait(60),mw.fixtures(fight=False),nav('Pier_Save02',2),
            mw.wait(60),mw.check('native_pier_to_crane',lambda s:s.room==96),nav(cr.NAMES[0],1),mw.wait(60),
            mw.check('crane_to_native_pier',lambda s:s.room==38)])
    elif args.command=='cross':
        destination=cr.LINKS[args.name,args.group][0]
        wanted=cr.IDS.get(destination,38)
        return run(args.rom,'cross-'+args.name+str(args.group),args.name,args.spawn,[mw.fixtures(fight=args.fight),mw.wait(60),
            mw.check('starts_in_room',lambda s:s.room==cr.IDS[args.name] and s.pos is not None),
            nav(args.name,args.group),mw.fixtures(fight=False),mw.wait(80),
            mw.until('real_exit',lambda s:s.room==wanted and s.pos is not None,600)],
            tuple(cr.FLAGS[n] for n in args.preset.split(',') if n))
    elif args.command=='view':
        steps=[mw.wait(90),mw.fixtures(fight=False)]
        for i,point in enumerate(args.points):
            x,y=map(float,point.split(','));steps += [*mw.put(x,y),mw.wait(50),mw.mark('view'+str(i))]
        if not args.points:steps.append(mw.wait(60))
        return run(args.rom,'view-'+args.name,args.name,args.spawn,steps,
            tuple(cr.VISITS.values())+tuple(cr.FLAGS[n] for n in args.preset.split(',') if n))
    elif args.command=='save':
        from tools import midnight_line
        midnight_line.OUT=OUT
        return midnight_line.refuge_save_child(args.rom,'crane-office',cr.NAMES[2])
    elif args.command=='machine':
        # Explicit combat setup placement; movement into the start trigger and
        # every strike are native inputs. This is not a traversal qualification.
        label='hoist-'+('black' if args.black else 'red') if args.no_heal else 'hoist-flow'
        if args.purchased_vitality or args.purchased_kit:
            label+='-kit' if args.purchased_kit else '-vitality'
            from tools import kit_lab as k
            native_run=k._run
            def vital_run(*pos,**kw):
                kw['bits2']=0x7fc00 if args.purchased_kit else 0xe000
                return native_run(*pos,**kw)
            k._run=vital_run
        label+=args.tag
        switch=[mw.hold('L',6),mw.wait(60),mw.until('black_form_confirmed',mw.black,90)] if args.black else [mw.check('red_form_confirmed',mw.red)]
        steps=[mw.wait(60),mw.fixtures(fight=False,alive=not args.no_heal),*switch,
            *mw.put(282,5),mw.walk('enter_hoist',310,300),mw.walk('approach_motor',332,200),
            mw.hold('Right+B',50),mw.wait(30),('machine_attack',args.combat_frames),
            mw.wait(90),mw.check('victory_saved_in_ram',mw.flag(cr.FLAGS['boss']))]
        if args.verify_clear:
            # ControlWalker adds HP measurement steps; no health refill.
            from tools.crane_boss_lab import ControlWalker
            globals()['Walker']=ControlWalker
            steps += [mw.fixtures(park=(100,80),alive=False),('measure','victory_hazards_clear','player'),
                mw.wait(700),('compare','victory_hazards_clear','player','no_damage'),nav(cr.NAMES[10],2),mw.wait(80),
                nav(cr.NAMES[11],1),mw.wait(80),mw.until('earned_cleared_revisit',
                    lambda s:s.room==106 and s.pos is not None and bool(s.flags>>142&1)
                    and bool(s.room_vars) and s.room_vars[0]==0,600)]
        return run(args.rom,label,cr.NAMES[10],1,steps)
    elif args.command=='map':
        from tools import kit_lab as k
        native_run=k._run
        def touched(*pos,**kw):
            pos=list(pos);pos[2]=[{'start':f,'end':f+5,'buttons':[],'touch':[244,367]} for f in (160,320,480)]
            return native_run(*pos,**kw)
        k._run=touched
        try:
            return run(args.rom,'map-'+args.name,args.name,args.spawn,[mw.wait(120),mw.mark('overview'),
                mw.wait(140),mw.mark('world'),mw.wait(160),mw.mark('detail'),mw.wait(160),mw.mark('overview_return')],
                tuple(cr.VISITS.values()))
        finally:k._run=native_run
    elif args.command=='power':
        return run(args.rom,'cargo-power',cr.NAMES[5],1,[mw.wait(60),mw.fixtures(fight=False),
            ('travel',146,1200),mw.wait(45),mw.hold('X',6),mw.wait(45),
            mw.check('lever_restores_cargo_power',mw.flag(cr.FLAGS['power'])),nav(cr.NAMES[5],2),
            mw.wait(60),mw.check('powered_door_to_counterweight',lambda s:s.room==102)])
    elif args.command=='all':
        cases=[('entry',[])]+[(n+str(g),['cross',n,'--group',str(g),'--preset','power,upper,crown,boss,freight,drydock','--fight'])
                              for n,g in cr.LINKS]
        def work(case):
            label,cmd=case
            if label=='entry':cmd=['entry']
            log=OUT/('batch-'+label+'.log');log.parent.mkdir(parents=True,exist_ok=True)
            with log.open('w') as f:done=subprocess.run([sys.executable,str(Path(__file__)),*cmd,'--rom',str(args.rom)],stdout=f,stderr=subprocess.STDOUT,cwd=ROOT)
            path=OUT/('walk-pier-entry.json' if label=='entry' else 'walk-cross-'+label+'.json')
            report=json.loads(path.read_text()) if path.exists() else {}
            return label,done.returncode==0 and report.get('passed',False),report.get('aborted')
        results=[]
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            pending=[pool.submit(work,case) for case in cases]
            for future in as_completed(pending):
                result=future.result();results.append(result);print(json.dumps(result),flush=True)
                w.write_json(OUT/'all-progress.json',{'rom':str(args.rom),'results':results,'passed':all(r[1] for r in results)})
        return dict(rom=str(args.rom),results=results,passed=all(r[1] for r in results))

if __name__=='__main__':raise SystemExit(0 if main()['passed'] else 1)
