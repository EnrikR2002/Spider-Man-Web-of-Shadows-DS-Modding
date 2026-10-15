"""Copied-save Signal Leech lab: real attacks, flow, cues, native death and persistence.

Run MODE --rom R in a quiet child. The kit lab supplies a copied research
save and disposable RAM. Flow/persist refill only Spidey. Combat/basic/black
use unweakened enemies and cores. No real battery is read or written.
"""
import argparse
import ctypes as c
import json
from pathlib import Path
import struct
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import midnight_walk as mw, midnight_boss as b, kit_lab as k, player_trace as p
from tools.midnight_walk import wait, fixtures, hold, walk, check, flag, until, in_room, mark, put, SETTLE


def world_objects(ram):
    """Bounded class-specific observation; hazard entries can include retained allocations.

    Core death byte and HP are checked. Hazard flags describe damage capability,
    not whether a retained object currently renders: frame/HP captures qualify
    activation. This observer never writes memory or assumes NormalEnemy layout.
    """
    if len(ram) != 4 * 1024 * 1024: raise ValueError('Expected 4 MiB main RAM')
    cores, hazards = [], []
    for vtable in (0x0212F7A0, 0x0212F2D4):
        at = 0
        while (at := ram.find(struct.pack('<I', vtable), at + 4)) >= 0:
            if at < 0x150000 or at % 4 or at > len(ram) - 0x174: continue
            kind, hp = struct.unpack_from('<2I', ram, at + 0x10C)
            x, y = struct.unpack_from('<2i', ram, at + 0x90)
            if abs(x) > 4096 * 1024 or abs(y) > 4096 * 1024: continue
            if vtable == 0x0212F7A0:
                if kind == b.CORE_KIND and 0 < hp <= b.CORE_HEALTH and not ram[at + 0x131]:
                    cores.append([at + p.BASE, hp, x / 4096, y / 4096])
            else:
                data = struct.unpack_from('<I', ram, at + 0x108)[0] - p.BASE
                if kind in (0x11, 0x12, b.MARKER_KIND) and 0 <= data <= len(ram) - 64 and not ram[at + 0x168]:
                    hazards.append([kind, struct.unpack_from('<I', ram, data)[0], x / 4096, y / 4096])
    return cores, hazards


def orb_point(frame, pixel_format):
    """Find a bright poison/health orb on the native lower screen for a real pen tap."""
    data, width, height, pitch = frame
    if (width, height) != (256,384): return None
    def rgb(x,y):
        if pixel_format == 1:
            blue,green,red,_ = data[y*pitch+x*4:y*pitch+x*4+4]
            return red,green,blue
        value=struct.unpack_from('<H',data,y*pitch+x*2)[0]
        if pixel_format == 2:return (value>>11)*255//31,((value>>5)&63)*255//63,(value&31)*255//31
        return ((value>>10)&31)*255//31,((value>>5)&31)*255//31,(value&31)*255//31
    for blue in (False,True):
        pixels=set()
        for y in range(212,380,2):
            for x in range(2,254,2):
                r,g,bv=rgb(x,y)
                if (bv>210 and r<160 and g<190) if blue else (r>220 and 40<g<190 and bv<160):pixels.add((x,y))
        clusters=[]
        while pixels:
            stack=[pixels.pop()];points=[]
            while stack:
                x,y=stack.pop();points.append((x,y))
                for n in ((x-2,y),(x+2,y),(x,y-2),(x,y+2)):
                    if n in pixels:pixels.remove(n);stack.append(n)
            if len(points)<15:continue
            xs,ys=zip(*points);w,h=max(xs)-min(xs),max(ys)-min(ys)
            if 6<=w<=28 and 6<=h<=28 and 0.6<w/max(h,1)<1.6:clusters.append(points)
        if clusters:
            points=max(clusters,key=len)
            return [round(sum(x for x,y in points)/len(points)),round(sum(y for x,y in points)/len(points))]
    return None


def child(rom, mode):
    rows=[]
    death={'frame':None}
    old=mw.Walker.read
    def read(self,frame,ram):
        s=old(self,frame,ram)
        if s is None: return None
        manager=struct.unpack_from('<I',ram,0x2145c34-p.BASE)[0]-p.BASE
        s.vars=list(ram[manager+0x1c0:manager+0x1ca]) if 0<manager<len(ram)-0x1ca else []
        s.cores,s.hazards=world_objects(ram)
        if mode == 'reset' and death['frame'] is not None and frame > death['frame'] and s.hp > 0 and s.state not in (74,75,79):
            self.scratch['recovered_after_death'] = True
        if frame>=0 and frame%12==0:rows.append([frame,s.room,s.pos,s.state,s.hp,s.vars,s.cores,len(s.enemies),s.hazards])
        if frame>=0 and frame%120==0:json.dump(rows,open('work/midnight-line/leech-'+mode+'-live.json','w'))
        return s
    mw.Walker.read=read
    base_run=k._run
    reload_save=False
    def long_run(*args,**kw):
        kw['frames']=10000
        kw['caps']=tuple(range(0,10000,120))
        if mode in ('combat','black'):kw['bits2']=0x7fc00
        if reload_save:kw['save']=__import__('pathlib').Path('work/midnight-line/leech-win.sav')
        if mode=='reset':
            touches=[{'start':720,'end':726,'buttons':[],'touch':[128,320]}]
            for n in range(360):
                touches.append({'start':840+n*6,'end':842+n*6,'buttons':[],
                                'touch':[(16,64,112,160,208,240)[n%6],(212,252,292,332,372)[n//6%5]]})
            touches += [{'start':f,'end':f+6,'buttons':['A']} for f in (1800,2100,2400,2700,3000,3200)]
            args=(args[0],args[1],touches,*args[3:])
        return base_run(*args,**kw)
    k._run=long_run
    def attack_core(self,step,s,ptr,ram):
        index,timeout=step[1:]
        if len(s.vars)>index+2 and s.vars[index+2]:
            self.record('core'+str(index),True,s,frames=self.t);return True
        if self.t>=timeout:
            self.record('core'+str(index),False,s,frames=self.t);return True
        if not s.pos:return False
        x=b.CORE_X[index];dx=x-s.pos[0]
        self.buttons.clear()
        way='Right' if dx>0 else 'Left'
        # A core is on the ground beneath its shelf. If a crew knocks the
        # driver onto that shelf, walk off its edge before swinging again.
        if s.pos[1]>16 and abs(dx)<12:
            self.buttons.add('Left' if s.pos[0]<x else 'Right')
            return False
        if abs(dx)>7.0:self.buttons.add(way)
        else:
            if self.t%16<2:self.buttons.add(way)
            if self.t%8<3:self.buttons.add('Y')
        if mode in ('basic','combat','black'):
            dangerous=any(e['state'] in (15,16) and abs(e['position'][0]/4096-s.pos[0])<12 for e in s.enemies)
            if dangerous and self.t%24<3:self.buttons.update(('R',way))
            live=any(h[0]==0x11 and h[1]&0x6000 and abs(h[2]-s.pos[0])<10 for h in s.hazards)
            if live and s.pos[1]<12:self.buttons.add('B')
        return False
    mw.Walker.do_core=attack_core
    oldtick=mw.Walker.tick
    pen=[]
    if mode=='reset':
        native_emulator=k.emu.run
        def emulator(*args,**kw):
            kw['live_touch']=pen
            return native_emulator(*args,**kw)
        k.emu.run=emulator
    def tick(self,frame,lib):
        self.native_lib=lib
        result=oldtick(self,frame,lib)
        if mode=='reset' and frame>800:
            if frame%8==0 and hasattr(lib,'_wos_video'):
                raw,fmt=lib._wos_video
                point=orb_point(raw,fmt)
                pen[:]=point or []
            elif frame%8==3:pen.clear()
        return result
    mw.Walker.tick=tick
    def snapshot(self,step,s,ptr,ram):
        from pathlib import Path
        lib=self.native_lib
        size=lib.retro_get_memory_size(0)
        if size!=512:raise ValueError('Expected native 512-byte SRAM')
        data=c.string_at(lib.retro_get_memory_data(0),size)
        Path('work/midnight-line/leech-win.sav').write_bytes(data)
        self.record('saved_victory_flag_in_refuge',s.room==77 and bool(s.flags>>151&1),s)
        return True
    mw.Walker.do_snapshot=snapshot
    def kill(self,step,s,ptr,ram):
        stats=struct.unpack_from('<I',ram,k.STATS_POINTER-p.BASE)[0]-p.BASE
        c.memmove(ptr+stats+0x84,bytes(4),4)
        self.on['alive']=False
        death['frame']=s.frame
        self.record('death_fixture',True,s)
        return True
    mw.Walker.do_kill=kill
    def health_mark(self,step,s,ptr,ram):
        self.scratch['clarity_hp'] = s.hp
        return True
    def health_check(self,step,s,ptr,ram):
        previous=self.scratch['clarity_hp']
        ok=s.hp==previous if step[2]=='equal' else s.hp<previous
        self.record(step[1],ok,s,before_hp=previous,after_hp=s.hp)
        return True
    mw.Walker.do_health_mark=health_mark
    mw.Walker.do_health_check=health_check
    def v(index,value): return lambda s: len(s.vars)>index and s.vars[index]==value
    steps=[fixtures(fight=False,alive=mode in ('flow','persist')),wait(60),hold('A',3),wait(30),walk('inside',63,300),wait(100),
           check('running',v(0,1)),check('all_cores_full_health',lambda s:len(s.cores)==3 and all(a[1]==b.CORE_HEALTH for a in s.cores)),
           hold('Right',180),check('sealed',lambda s:s.pos[0]<80 and s.room==94),
           hold('X',3),wait(30),mark('breaker'),wait(350)]
    for i,x in reversed(list(enumerate(b.CORE_X))):
        steps += [('core',i,2000),wait(50)]
        if i == 2 and mode == 'flow':
            steps += [hold('Right+B',28),hold('Right',90),
                      check('seal_holds_after_nearest_core_is_gone',lambda s:s.room==94 and s.pos[0]<=84-3.5+.25)]
    steps += [check('won',flag(151)),wait(250),until('back_to_roof',in_room('ML_Roof'),500,'Right'),wait(60),
              until('revisit',in_room(b.ROOM),500,'Left'),wait(100),check('still_cleared',flag(151)),
              check('idle_after_win',v(0,0)),check('no_cores',lambda s:not s.cores),mark('end')]
    if mode=='basic':mw.PLAYER_ABILITIES=0x1f
    if mode=='black':steps.insert(4,hold('L',3))
    if mode in ('basic','combat','black'):
        steps=[fixtures(fight=False,alive=False),wait(60),walk('inside',63,300),wait(10)]
        if mode=='black':steps += [hold('L',3),wait(20)]
        for i in (2,1,0):steps += [('core',i,2400),wait(10)]
        steps += [check('won_without_refills',flag(151)),until('exit',in_room('ML_Roof'),500,'Right')]
    if mode=='cue':
        steps=[fixtures(fight=False,alive=False),wait(60),walk('inside',63,300),fixtures(park=(92,5)),
               *put(11,5)]
        for i in range(30):steps += [hold('Right',6),hold('Left',6)]
        steps += [mark('cue_end')]
    if mode=='clarity':
        steps=[fixtures(fight=False,alive=True,park=(8,60)),wait(60),walk('inside',63,300),wait(100),
               check('three_core_beacons',lambda s:sum(h[0]==b.MARKER_KIND for h in s.hazards)==3)]
        for x in (34,58,8):
            steps += [fixtures(alive=True),*put(x,5),wait(30),fixtures(alive=False),('health_mark','safe'),
                      wait(1440),('health_check','green_'+str(x)+'_no_damage','equal')]
        # Stand beside the core rather than on its native collision mound.
        steps += [fixtures(alive=True),*put(14.5,5),wait(30),
                  check('beside_core_on_floor',lambda s:4.5<s.pos[1]<5.5),
                  # Static allocations can outlive their visible activation.
                  # Use the scheduler's STEP transitions, then HP/captures.
                  # Native OBJ delay units are two captured DS frames here.
                  until('last_lane_rest',lambda s:s.vars[7]==2,1500),
                  until('first_lane_rest',lambda s:s.vars[7]==0,600),
                  wait(2*b.REST[0]+8), fixtures(alive=False),('health_mark','warning'),
                  wait(2*b.WARNING[0]-16),('health_check','warning_is_harmless','equal'),
                  until('live_damage',lambda state:state.hp<6*4096,2*b.LIVE[0]+60)]
        steps += [('health_check','live_lane_damages','less'),fixtures(alive=True),mark('clarity_end')]
    if mode=='persist':
        steps += [until('return_roof',in_room('ML_Roof'),500,'Right'),wait(SETTLE),
                  *put(200,5),until('return_relay',in_room('ML_RelayHall'),500,'Right'),wait(SETTLE),
                  *put(100,5),until('return_switchyard',in_room('ML_Switchyard'),500,'Right'),wait(SETTLE),
                  *put(225,5),until('return_yard',in_room('ML_Yard'),500,'Right'),wait(SETTLE),
                  *put(150,45),until('return_refuge',in_room('ML_Refuge'),500,'Right'),wait(SETTLE),
                  *put(30,5),hold('X',6),wait(70),hold('A',6),wait(90),hold('A',6),wait(220),('snapshot','save')]
    if mode=='reset':
        steps=[fixtures(fight=False,alive=True),wait(60),walk('inside',63,300),wait(10),('core',2,800),
               wait(100),('kill','death'),wait(2800),mark('after_death'),
               check('native_death_recovers',lambda s:any(death['frame'] is not None and r[0]>death['frame'] and r[4]>0 and r[3] not in (74,75,79) for r in rows)),
               check('no_victory_on_death',lambda s:not(s.flags>>151&1))]
    mw.run_child(rom,'leech-'+mode,(b.ROOM,1,(),steps))
    json.dump(rows,open('work/midnight-line/leech-'+mode+'.json','w'),indent=1)
    print('LEECH',mode,rows[-1])
    if mode=='persist':
        rows=[];reload_save=True;mode='persist-reload'
        mw.run_child(rom,'leech-persist-reload',(b.ROOM,1,(),[fixtures(fight=False,alive=False),wait(120),
            check('saved_victory_restored',flag(151)),check('no_cores_after_reload',lambda s:not s.cores),
            walk('cleared_arena',20,500),wait(250),check('no_new_attempt',v(0,0))]))
        json.dump(rows,open('work/midnight-line/leech-persist-reload.json','w'),indent=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('run', '_child'))
    parser.add_argument('mode', choices=('flow','combat','basic','black','cue','clarity','persist','reset'))
    parser.add_argument('--rom', default=str(ROOT / 'build/Spider-Man-WoS-modded.nds'))
    a = parser.parse_args()
    if a.command == '_child':
        child(a.rom, a.mode)
        return 0
    log = ROOT / 'work/midnight-line' / ('boss-lab-' + a.mode + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('w', encoding='utf-8') as stream:
        result = subprocess.run([sys.executable, str(Path(__file__)), '_child', a.mode, '--rom', a.rom],
                                cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        print('Boss lab failed; inspect ' + str(log))
        return result.returncode
    report = json.loads((ROOT / 'work/midnight-line' / ('walk-leech-' + a.mode + '.json')).read_text())
    print(json.dumps({'mode':a.mode,'passed':report['passed'],'rom_sha256':report['rom_sha256'],
                      'checks':report['checks'],'log':str(log)}))
    return 0 if report['passed'] else 1


if __name__ == '__main__': raise SystemExit(main())
