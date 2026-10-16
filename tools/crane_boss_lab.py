"""Copied-save Crane controls: protection, warnings, callbacks and persistence.

Placements and parked/capped crews are isolated measurement fixtures. They
never qualify traversal or encounter difficulty. Real Y inputs damage props.
"""
import argparse
import ctypes as c
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import crane_walk as cw,crane_rooms as cr,crane_boss as b
from tools import midnight_walk as mw,kit_lab as k,player_trace as p


class HealthWindow:
    """Detect any sampled damage, including damage hidden by earlier healing."""
    def __init__(self,hp):self.before=self.last=self.minimum=hp;self.dropped=False
    def sample(self,hp):
        self.dropped|=hp<self.last;self.minimum=min(self.minimum,hp);self.last=hp
    def passed(self,regeneration=False):
        return not self.dropped and (regeneration or self.last==self.before)


def core_hp(state):
    return next((o[1] for o in state.machines if o[0]==b.CORE),None)


class ControlWalker(cw.Walker):
    pen=None
    native_crew=False
    native_crew_room=None
    def read(self,frame,ram):
        state=super().read(frame,ram)
        if state:
            for window in self.scratch.get('health_windows',{}).values():window.sample(state.hp)
        return state
    def tick(self,frame,lib):
        self.native_lib=lib
        if self.native_crew:
            ptr,ram=k.ram_of(lib);state=self.read(frame,ram)
            if state and state.room in (97,100,105) and state.pos:
                stats=struct.unpack_from('<I',ram,k.STATS_POINTER-p.BASE)[0]-p.BASE
                c.memmove(ptr+stats+0x84,struct.pack('<2I',245760,245760),8)
        if self.pen is not None and frame>self.scratch.get('death_frame',10**9):
            from tools.midnight_boss_lab import orb_point
            if frame%8==0 and hasattr(lib,'_wos_video'):
                raw,fmt=lib._wos_video;point=orb_point(raw,fmt)
                # The copied research save can still show the native first-
                # death tutorial before it exposes the actual health orbs.
                if not point and frame-self.scratch['death_frame']<900 and frame%120==0:point=[128,320]
                self.pen[:]=point or []
            elif frame%8==3:self.pen.clear()
        if self.scratch.get('mask_exposure'):
            ptr,ram=k.ram_of(lib)
            manager=struct.unpack_from('<I',ram,0x02145C34-p.BASE)[0]-p.BASE
            if 0<manager<len(ram)-0x1CA:c.memmove(ptr+manager+0x1C1,b'\0',1)
        result=super().tick(frame,lib)
        if self.native_crew and self.on['fight'] and self.i<len(self.steps) and self.steps[self.i][0]=='until':
            from tools.crane_creature_lab import pursuit_buttons
            _,ram=k.ram_of(lib);state=self.read(frame,ram)
            if state and state.pos:
                self.buttons.clear()
                if state.room!=self.native_crew_room and 96<=state.room<108:
                    current=cr.NAMES[state.room-96]
                    group=next((g for (source,g),(target,_) in cr.LINKS.items()
                                if source==current and cr.IDS.get(target)==self.native_crew_room),None)
                    if group is not None:
                        self.report.setdefault('native_crew_returns',[]).append([frame,state.room,group])
                        self.do_navigate(('navigate',current,group,12000),state,*k.ram_of(lib))
                elif state.enemies:
                    enemy=min(state.enemies,key=lambda e:abs(e['position'][0]/4096-state.pos[0])+abs(e['position'][1]/4096-state.pos[1]))
                    self.buttons.update(pursuit_buttons(frame,state,enemy))
                else:
                    centre=cr.BOUNDS[state.room-96][0]/2
                    if abs(state.pos[0]-centre)>8:self.buttons.add('Right' if state.pos[0]<centre else 'Left')
                    if frame%64<30:self.buttons.add('B')
        if frame>=0 and self.on['chase']:
            _,ram=k.ram_of(lib);state=self.read(frame,ram)
            if state and state.room==cr.IDS[cr.NAMES[9]] and state.pos and not state.enemies and not(state.flags>>cr.FLAGS['crown']&1):
                # A chase fixture can finish the first wave at x12, outside
                # the reinforcement's activation zone. Resume native movement
                # into the arena instead of waiting motionless for a callback.
                self.buttons.add('Right' if state.pos[0]<168 else 'Left')
                self.report.setdefault('crew_zone_return_frames',[]).append(frame)
        return result

    def do_mask_exposure(self,step,state,ptr,ram):
        self.scratch['mask_exposure']=step[1]
        return True

    def do_kill(self,step,state,ptr,ram):
        stats=struct.unpack_from('<I',ram,k.STATS_POINTER-p.BASE)[0]-p.BASE
        c.memmove(ptr+stats+0x84,bytes(4),4)
        self.scratch['death_frame']=state.frame;self.on['alive']=False
        self.record('native_near_death_fixture',True,state)
        return True

    def do_suppress_crew(self,step,state,ptr,ram):
        # Native table8's first two words are documented spawn costs. Zero
        # them only in this disposable environment control, before activation.
        address=0x02136634+8*24
        before=struct.unpack_from('<2I',ram,address-p.BASE)
        if before!=(0x8000,0x4000):raise ValueError('Native table8 costs changed')
        c.memmove(ptr+address-p.BASE,bytes(8),8)
        self.record('crew_free_hazard_fixture',True,state)
        return True

    def do_measure(self,step,state,ptr,ram):
        key,source=step[1:]
        self.scratch[key]=state.hp if source=='player' else core_hp(state)
        if source=='player':self.scratch.setdefault('health_windows',{})[key]=HealthWindow(state.hp)
        return True

    def do_compare(self,step,state,ptr,ram):
        key,source,op=step[1:]
        before=self.scratch[key];after=state.hp if source=='player' else core_hp(state)
        window=self.scratch.get('health_windows',{}).pop(key,None)
        ok=False if before is None or after is None else (window.passed(op=='no_damage') if window and op in ('equal','no_damage') else after==before if op=='equal' else after<before)
        self.record(key,before is not None and after is not None and ok,state,before=before,after=after,
                    minimum=window.minimum if window else None,dropped=window.dropped if window else None)
        return True

    def do_unhook(self,step,state,ptr,ram):
        # Paired disposable-RAM control: identical script/input, native damage.
        c.memmove(ptr+b.HP_SITE-p.BASE,struct.pack('<I',0xE92D000F),4)
        self.record('native_hp_prologue_restored_in_lab_only',True,state)
        return True

    def do_probe(self,step,state,ptr,ram):
        # Invoke native HP subtraction exactly once from a saved-register
        # world tick. This isolates the HP hook from the guard's physical box.
        # All code/patches are disposable lab RAM in unused Crane reservation.
        core=next(o for o in state.machines if o[0]==b.CORE)
        at=0x0215A300;counter=0x0215A3F0
        word=struct.unpack_from('<I',ram,b.TICK_SITE-p.BASE)[0]
        target=cw.crane_row.target(b.TICK_SITE,word)
        a=b.Arm(at);a.emit(0xE92D500F);a.lit(2,'counter',counter)
        a.emit(0xE5923000,0xE3530000);a.b('done',1)
        a.emit(0xE3A03001,0xE5823000);a.lit(0,'core',int(core[6],16));a.lit(1,'damage',4096)
        a.b(b.HP_SITE,link=True);a.label('done');a.emit(0xE8BD500F);a.b(target)
        code=a.finish()
        if at+len(code)>=counter:raise ValueError('Probe exceeded unused lab tail')
        c.memmove(ptr+at-p.BASE,code,len(code));c.memmove(ptr+counter-p.BASE,bytes(4),4)
        c.memmove(ptr+b.TICK_SITE-p.BASE,struct.pack('<I',b._branch(b.TICK_SITE,at)),4)
        self.scratch['probe_original']=word
        return True

    def do_restore_probe(self,step,state,ptr,ram):
        c.memmove(ptr+b.TICK_SITE-p.BASE,struct.pack('<I',self.scratch['probe_original']),4)
        return True

    def do_snapshot(self,step,state,ptr,ram):
        lib=self.native_lib
        if lib.retro_get_memory_size(0)!=512:raise ValueError('Expected native SRAM')
        data=c.string_at(lib.retro_get_memory_data(0),512)
        (cw.OUT/'crane-win.sav').write_bytes(data)
        self.record('office_saved_earned_hoist_victory',state.room==98 and bool(state.flags>>142&1),state)
        return True


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',choices=('guard','guard-native','cues','safety','clear','persist','crew','cache','gates','reset','leave'))
    ap.add_argument('--room',default='AR_CraneCrown')
    ap.add_argument('--rom',type=Path,required=True)
    args=ap.parse_args(argv)
    cw.install();cw.MACHINE_DATA.update(cw.machine_records(args.rom));cw.Walker=ControlWalker
    mode=args.mode;room=cr.NAMES[10];preset=()
    v=lambda i,x:lambda state:len(state.room_vars)>i and state.room_vars[i]==x
    start=[mw.wait(60),mw.fixtures(fight=False,park=(100,80)),*mw.put(282,5),
           mw.walk('enter_hoist',310,300),mw.until('machine_running',v(0,1),200)]
    if mode in ('safety','cues','reset'):start.insert(1,('suppress_crew','environment_only'))
    if mode.startswith('guard'):
        steps=start+[*mw.put(348,5),mw.until('motor_exposed_first',v(1,1),800),
                     ('mask_exposure',True),mw.wait(2)]
        if mode=='guard-native':steps += [('unhook','native-control')]
        steps += [('measure','guarded_motor','core'),('probe','guarded'),mw.wait(4),('restore_probe','guarded'),
            ('compare','guarded_motor','core','less' if mode=='guard-native' else 'equal'),('mask_exposure',False),
            mw.until('exposure_returns',v(1,1),800),('measure','exposed_motor','core'),('probe','exposed'),
            mw.wait(4),('restore_probe','exposed'),('compare','exposed_motor','core','less')]
    elif mode=='cues':
        steps=start+[*mw.put(312,5),mw.until('first_recovery',v(1,1),800),
            mw.until('sweep_warning_begins',v(4,1),800),mw.place(312,5),mw.wait(4),
            mw.check('warning_control_at_measured_centre',lambda s:abs(s.pos[0]-312)<.25),mw.fixtures(alive=False),
            ('measure','warning_no_damage','player'),mw.wait(110),('compare','warning_no_damage','player','equal'),
            mw.until('impact_is_live',v(4,4),300),mw.wait(24),('compare','live_impact_hurts','player','less')]
        # Reuse the original health mark for a positively damaging control.
        steps.insert(-3,('measure','live_impact_hurts','player'))
    elif mode=='safety':
        steps=start
        for x in (328,392):
            key='safe_floor_'+str(x)
            steps += [mw.fixtures(alive=True),*mw.put(x,5),mw.place(x,5),mw.wait(30),
                mw.check(key+'_actual_coordinate',lambda s,x=x:abs(s.pos[0]-x)<.25),mw.fixtures(alive=False),
                ('measure',key,'player'),mw.wait(1500),('compare',key,'player','equal'),
                mw.check(key+'_stays_on_floor',lambda s,x=x:4.5<s.pos[1]<5.5 and abs(s.pos[0]-x)<.25)]
    elif mode=='reset':
        pen=[];ControlWalker.pen=pen
        native=k.emu.run
        def emulator(*pos,**kw):kw['live_touch']=pen;return native(*pos,**kw)
        k.emu.run=emulator
        steps=start+[*mw.put(392,5),mw.place(392,5),mw.wait(10),mw.until('attempt_active',v(0,1),200),mw.fixtures(park=None),
            ('kill','health_zero'),mw.wait(1000),mw.hold('A',6),mw.hold('Right+B',48),mw.wait(100),
            mw.check('native_recovery_without_victory',lambda s:s.hp>0 and s.state not in (74,75,79) and not(s.flags>>142&1))]
    elif mode=='leave':
        preset=(cr.FLAGS['crown'],cr.FLAGS['upper'])
        steps=start+[mw.until('warning_pending',v(4,1),200),mw.fixtures(park=None),cw.nav(room,1),mw.wait(400),
            mw.check('leaving_does_not_award_victory',lambda s:s.room==105 and not(s.flags>>142&1)),
            cw.nav(cr.NAMES[9],3),mw.wait(100),mw.check('reentered_attempt_is_idle',lambda s:s.room==106 and s.room_vars[0]==0),
            *mw.put(282,5),mw.walk('reenter_hoist',310,300),mw.wait(30),
            mw.check('fresh_attempt_full_native_core',lambda s:s.room_vars[0]==1 and any(o[0]==b.CORE and o[1]==b.HEALTH for o in s.machines))]
    elif mode in ('clear','persist'):
        if mode=='persist':preset=(cr.FLAGS['freight'],)
        steps=start+[mw.fixtures(park=None),mw.walk('approach_motor',332,200),mw.hold('Right+B',50),mw.wait(30),('machine_attack',5000),mw.wait(90),
            mw.fixtures(alive=False,park=(100,80)),('measure','victory_cleanup_safe','player'),mw.wait(700),
            ('compare','victory_cleanup_safe','player','equal'),mw.fixtures(alive=True,park=None),cw.nav(room,2),mw.wait(80),
            mw.check('earned_return_to_breakwater',lambda s:s.room==107),cw.nav(cr.NAMES[11],1),mw.wait(80),
            mw.check('cleared_revisit_idle',lambda s:s.room==106 and s.room_vars[0]==0 and bool(s.flags>>142&1)),
            *mw.put(344,5),('measure','revisit_cleanup_safe','player'),mw.wait(400),
            ('compare','revisit_cleanup_safe','player','equal')]
        if mode=='persist':
            steps += [cw.nav(room,2),mw.wait(80),cw.nav(cr.NAMES[11],2),mw.wait(80),
                cw.nav(cr.NAMES[0],2),mw.wait(80),cw.nav(cr.NAMES[1],3),mw.wait(80),
                mw.walk('office_sphere',48,600),mw.hold('X',6),mw.wait(70),mw.hold('A',6),
                mw.wait(90),mw.hold('A',6),mw.wait(220),('snapshot','native-save')]
    elif mode=='crew':
        room=args.room;key={cr.NAMES[1]:'freight',cr.NAMES[4]:'drydock',cr.NAMES[9]:'crown'}[room]
        ControlWalker.native_crew=True;ControlWalker.native_crew_room=cr.IDS[room]
        steps=[mw.fixtures(fight=False),mw.wait(60),
            mw.until('native_crew_appears',lambda s:bool(s.enemies),600),
            mw.check('no_automatic_clear',lambda s:not(s.flags>>cr.FLAGS[key]&1)),
            mw.fixtures(fight=True,chase=False),mw.until('crew_death_callback',mw.flag(cr.FLAGS[key]),6000),
            mw.fixtures(fight=False,chase=False),mw.check('crown_opens_upper_return',
                lambda s:key!='crown' or bool(s.flags>>cr.FLAGS['upper']&1))]
    elif mode=='cache':
        room=cr.NAMES[8]
        steps=[mw.wait(60),mw.fixtures(fight=False),*mw.put(100,45),mw.wait(30),mw.hold('Right',2),
            mw.check('stash_unclaimed',lambda s:not(s.flags>>143&1))]
        for _ in range(20):steps += [mw.hold('Y',3),mw.wait(7)]
        steps += [mw.hold('Left',2),mw.until('native_stash_destruction_claims_cache',mw.flag(143),600,'mash'),cw.nav(room,1),mw.wait(80),
            cw.nav(cr.NAMES[5],4),mw.wait(80),mw.check('cache_claim_survives_revisit',lambda s:s.room==104 and bool(s.flags>>143&1))]
    else:
        room=cr.NAMES[5]
        steps=[mw.wait(60),mw.fixtures(fight=False),*mw.put(264,5),mw.hold('Right',80),
            mw.check('counterweight_closed_before_power',lambda s:s.room==101 and not(s.flags>>140&1)),
            *mw.put(146,5),mw.wait(20),mw.hold('X',6),mw.wait(40),
            mw.check('native_lever_earns_power',mw.flag(140)),cw.nav(room,2),mw.wait(80),
            mw.check('counterweight_open_after_power',lambda s:s.room==102)]
    report=cw.run(args.rom,'control-'+mode+('-'+args.room if mode=='crew' else ''),room,1,steps,preset)
    if mode=='crew':
        report['limit']='Copied save;60-unit healed player and1HP enemy fixtures. Native arrival/inputs/positions; no actor placements. Callback qualification only.'
        from tools import wos_tool as w
        w.write_json(cw.OUT/('walk-control-crew-'+args.room+'-'+report['rom_sha256'][:8]+'.json'),report)
    if mode=='persist' and report['passed']:
        native=k._run
        def reload(*pos,**kw):kw['save']=cw.OUT/'crane-win.sav';return native(*pos,**kw)
        k._run=reload
        report=cw.run(args.rom,'control-persist-reload',cr.NAMES[10],1,[mw.wait(120),
            mw.check('earned_victory_restored_from_native_save',mw.flag(142)),
            mw.check('no_restart_after_reload',v(0,0)),*mw.put(344,5),mw.fixtures(alive=False),
            ('measure','reload_safe','player'),mw.wait(400),('compare','reload_safe','player','equal')])
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
