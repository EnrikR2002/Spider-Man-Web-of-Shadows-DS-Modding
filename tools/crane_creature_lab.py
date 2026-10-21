"""Copied-save creature duels with native spawns, movement, HP and callbacks.

An isolated roster/budget is a disposable RAM fixture. The player may be healed;
enemy HP is never capped. This qualifies contact/counterplay, not difficulty.
"""
import argparse,ctypes as ct,json,struct,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import crane_walk as cw,midnight_walk as mw,kit_lab as k,player_trace as p
from tools import crane_creatures as c,crane_rooms as cr,wos_tool as w


def metadata(rom):
    report=json.loads(Path(rom).with_suffix('.build.json').read_text())
    return report.get('crane_row',report)['creatures']['runtime']


def summarize(rows):
    """Observed health changes only; the combo meter is not a hit count."""
    damaged=set();seen=set();last={};incoming=False;hp=None;peak=0;actions=set();states=set();max_live=0;max_distinct=0
    for row in rows:
        max_live=max(max_live,len(row['enemies']));max_distinct=max(max_distinct,len({e['key'] for e in row['enemies']}))
        if hp is not None and row['hp']<hp:incoming=True
        hp=row['hp'];peak=max(peak,row.get('gauge',0));states.add(row['player_state'])
        for enemy in row['enemies']:
            key=enemy['key'];seen.add(key);actions.add((key,enemy['action']))
            identity=(enemy['actor'],key)
            if identity in last and enemy['hp']<last[identity]:damaged.add(key)
            last[identity]=enemy['hp']
    return {'seen':sorted(seen),'damaged':sorted(damaged),'incoming_damage_observed':incoming,
            'peak_combo_gauge_q12':peak,'player_states':sorted(x for x in states if x is not None),
            'enemy_actions':sorted(actions),'samples':len(rows),'max_live':max_live,'max_distinct':max_distinct}


def fight_buttons(frame,dx,dy,kit=False):
    buttons=set()
    if abs(dx)>5.5 or abs(dy)>8 or frame%45<2:buttons.add('Right' if dx>0 else 'Left')
    if dy>8 and frame%64<38:buttons.add('B')
    if abs(dx)<12 and abs(dy)<13 and frame%8<3:buttons.add('Y')
    if frame%180<5:buttons.add('R')
    if kit and frame%300 in range(180,205):buttons.update(('Down','A'))
    return buttons

def pursuit_buttons(frame,state,enemy,kit=False):
    """Native-input lab pursuit, including wall crawl and web-hang release."""
    x,y=state.pos;ex,ey=(v/4096 for v in enemy['position']);dx,dy=ex-x,ey-y
    if state.state==29:return {'B'} if frame%24<6 else {'Down'}
    if state.state==9:
        # A foe below a freight overhang needs a real crawl down. Repeated
        # wall jumps lifted the driver onto the same roof forever, even when
        # the target was reachable from the sunken deck underneath it.
        if dy < -8:return {'Down'}
        return {'Up'} if dy>8 else {'B','Right' if dx>0 else 'Left'}
    if dy>28 and 96<=state.room<108:
        width=cr.BOUNDS[state.room-96][0];left=ex<width/2;edge=x if left else width-x
        # Cargo walls inside the room are climbable too. Walking toward the
        # outer wall without Up left the old driver stuck below an internal
        # crate while the new recoil hop put its target on the roof.
        buttons={'Left' if left else 'Right','Up'}
        if frame%64<38:buttons.add('B')
        if edge<24 and y<18:
            return {'B','Up'}
        if edge<18:buttons.add('Up')
        if edge<34 and (y<18 or edge<18) and frame%24<12:buttons.add('B')
        return buttons
    # A short catwalk can trap a naive chase directly underneath its target.
    # Sweep out from below it with real inputs before jumping back to attack.
    if 8<dy<28 and abs(dx)<24 and frame%360<110:
        way='Left' if frame//360%2==0 else 'Right'
        if x<24:way='Right'
        elif 96<=state.room<108 and x>cr.BOUNDS[state.room-96][0]-24:way='Left'
        return {way,'B'} if frame%36<22 else {way}
    buttons=fight_buttons(frame,dx,dy,kit)
    if abs(dx)<15 and -18<dy<24 and frame%8<3:buttons.add('Y')
    # Keep a lab chase away from automatic ground exits.
    if 96<=state.room<108:
        width=cr.BOUNDS[state.room-96][0]
        if x<14:buttons.discard('Left');buttons.add('Right')
        elif x>width-14:buttons.discard('Right');buttons.add('Left')
    return buttons


def duel(rom,key,*,black=False,kit=False,observe=360,timeout=3600,tag='',resilient=False,bait_runtime=None,bait_index=None,minimum_distinct=3,room='AR_FreightExchange',progress_flag=None,preset=(),approach_save=None):
    runtime=metadata(rom);spec=c.BY_KEY.get(key);configs={v:k for k,v in runtime['configs'].items()}
    if spec is not None and room!='AR_FreightExchange':raise ValueError('Single-species isolation owns Freight only')
    room_id=cr.IDS[room]
    cw.install();mw.PLAYER_ABILITIES=0x180FFFDF if kit else 0x1F
    holder={}
    class DuelWalker(cw.Walker):
        def __init__(self,*args,**kw):
            super().__init__(*args,**kw);self.rows=[];self.on['fight']=False;holder['walker']=self
        def tick(self,frame,lib):
            self.native_lib=lib
            if frame+k.TRAINING_START>=2040:
                ptr,ram=k.ram_of(lib)
                # Before native room initialization: exactly one actor, selected
                # through the shipped native spawner. No position/state writes.
                if spec is not None:
                    ct.memmove(ptr+runtime['state']-p.BASE,struct.pack('<2I',97,{'maw':0,'spore':1,'ballast':2}[key]),8)
                    ct.memmove(ptr+runtime['goals']['crew']-p.BASE,struct.pack('<2I',spec.cost*4096,spec.cost*4096),8)
                state=self.read(frame,ram)
                if state and state.room==room_id and state.pos:
                    stats=struct.unpack_from('<I',ram,k.STATS_POINTER-p.BASE)[0]-p.BASE
                    if resilient:
                        # Explicit crowd-driver fixture: prevent an inter-heal
                        # lethal burst interrupting a callback/animation test.
                        ct.memmove(ptr+stats+0x84,struct.pack('<2I',245760,245760),8)
                    if kit and state.sample:
                        old=w.u32(ram,stats+0x14);ct.memmove(ptr+stats+0x14,struct.pack('<I',old|0x71400),4)
                    if frame%2==0:
                        enemies=[]
                        for enemy in state.enemies:
                            actor=enemy['actor']-p.BASE;cfg=w.u32(ram,actor+0x40)
                            if cfg not in configs:continue
                            motion=w.u32(ram,actor+0x30)-p.BASE
                            enemies.append({**enemy,'key':configs[cfg],'gmb':w.u32(ram,motion+0x230),
                                            'clock':w.u32(ram,motion+0x178),'flags':w.u32(ram,actor+0x88)})
                        combo=state.sample['combo'] if state.sample else None
                        self.rows.append({'frame':frame,'hp':state.hp,'player_state':state.state,'player':state.pos,
                                          'xp':w.u32(ram,stats+0x44),
                                          'gauge':combo['gauge_fixed_candidate'] if combo else 0,'enemies':enemies})
            super().tick(frame,lib)
            if frame<0 or self.i>=len(self.steps):return
            step=self.steps[self.i]
            if bait_runtime is not None and bait_index is not None and frame<5500 and step[0] not in ('fixtures','travel'):
                _,ram=k.ram_of(lib)
                selected=w.u32(ram,bait_runtime['attack_counters']-p.BASE+bait_index*4)
                contact_ready=True
                if bait_runtime.get('move_counter_encoding'):
                    words=struct.unpack_from('<3I',ram,bait_runtime['move_counters']-p.BASE+bait_index*16)
                    contact_ready=all(v>>16 for v in words)
                if selected<3 or not contact_ready:
                    state=self.read(frame,ram);self.buttons.clear()
                    if state and state.pos and state.enemies:
                        e=min(state.enemies,key=lambda e:abs(e['position'][0]/4096-state.pos[0])+abs(e['position'][1]/4096-state.pos[1]))
                        dx=e['position'][0]/4096-state.pos[0];dy=e['position'][1]/4096-state.pos[1]
                        if abs(dx)>7 or abs(dy)>10:
                            self.buttons.update(pursuit_buttons(frame,state,e,False));self.buttons.difference_update(('Y','A','R'))
                    return
            step=self.steps[self.i]
            if step[0]!='until' or step[1]!='real_hp_duel_clears':return
            _,ram=k.ram_of(lib);s=self.read(frame,ram)
            if not s or not s.pos:return
            if s.room!=room_id:
                # A real knockback can carry the player through an automatic
                # retreat door. Return by its native reciprocal route instead
                # of fighting in the wrong room until the deadline expires.
                if room=='AR_CraneCrown' and s.room==cr.IDS['AR_GantrySpine']:
                    if self.scratch.get('duel_return_room')!=s.room:
                        self.scratch.update(duel_return_room=s.room,duel_return_start=frame)
                        self.record('native_retreat_during_duel',True,s)
                    age=self.t;self.t=frame-self.scratch['duel_return_start']
                    try:self.do_navigate(('navigate','AR_GantrySpine',2,1800),s,ptr,ram)
                    finally:self.t=age
                    return
                self.buttons.clear();return
            self.scratch.pop('duel_return_room',None)
            if not s.enemies:
                if not mw.flag(flag)(s):
                    self.buttons.clear()
                    if abs(s.pos[0]-200)>10:self.buttons.add('Right' if s.pos[0]<200 else 'Left')
                    if frame%64<36:self.buttons.add('B')
                return
            enemy=min(s.enemies,key=lambda e:abs(e['position'][0]/4096-s.pos[0])+abs(e['position'][1]/4096-s.pos[1]))
            self.buttons.clear();self.buttons.update(pursuit_buttons(frame,s,enemy,kit))
        def do_approach_snapshot(self,step,state,ptr,ram):
            path=Path(step[1]).resolve()
            if not path.is_relative_to((ROOT/'work').resolve()):raise ValueError('Research checkpoints belong under work/')
            lib=self.native_lib
            if lib.retro_get_memory_size(0)!=512:raise ValueError('Expected512-byte native SRAM')
            path.write_bytes(ct.string_at(lib.retro_get_memory_data(0),512))
            self.report['earned_save']=str(path)
            self.record('earned_Crown_and_pre_hoist_checkpoint',state.room==106 and bool(state.flags>>146&1) and not bool(state.flags>>142&1),state)
            return True
    cw.Walker=DuelWalker
    switch=[mw.until('black_form',lambda s:s.black==1,300,'tapL')] if black else []
    flag=cr.FLAGS['freight'] if progress_flag is None else progress_flag
    steps=[mw.fixtures(fight=False),*switch,('travel',100,600),mw.wait(observe),
           mw.until('real_hp_duel_clears',mw.flag(flag),timeout),mw.wait(60)]
    if approach_save:
        if room!='AR_CraneCrown':raise ValueError('The earned approach checkpoint follows Crown')
        steps.extend((cw.nav(room,3,3000),mw.check('earned_hoist_door',lambda s:s.room==106),mw.wait(120),('travel',36,600),mw.wait(60),
                      mw.hold('X',6),mw.wait(70),mw.hold('A',6),mw.wait(90),mw.hold('A',6),mw.wait(220),('approach_snapshot',str(approach_save))))
    label=f'creature-duel-{key}'+('-crown' if room=='AR_CraneCrown' else '')+'-'+('black' if black else 'red')+('-kit' if kit else '-base')+tag
    result=cw.run(rom,label,room,1,steps,preset)
    rows=holder['walker'].rows;summary=summarize(rows)
    passed=result['passed'] and (key in summary['damaged'] if spec else set(summary['damaged'])==set(c.BY_KEY) and summary['max_distinct']>=minimum_distinct)
    out=cw.OUT/'creatures'/f'{label}-{result["rom_sha256"][:8]}.json'
    w.write_json(out,{'passed':passed,'summary':summary,'route':result,'observations':rows,'minimum_simultaneous_species':minimum_distinct if not spec else 1,
                     'limits':('Isolated roster/budget; ' if spec else 'Production mixed roster/budget; ')+
                              ('60-unit max/healed player; ' if resilient else 'healed player; ')+
                              'copied save. Native enemy HP/spawns/AI; real inputs, no actor placement/state fixture. Not a difficulty test.'})
    print(json.dumps({'report':str(out),'passed':passed,**summary}))
    return passed


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--rom',type=Path,required=True)
    ap.add_argument('--creature',choices=(*c.BY_KEY,'mixed'),required=True);ap.add_argument('--black',action='store_true')
    ap.add_argument('--kit',action='store_true');ap.add_argument('--observe',type=int,default=360)
    ap.add_argument('--tag',default='')
    ap.add_argument('--resilient',action='store_true',help='Explicit60-unit player-health fixture for a natural-HP crowd/callback test')
    ap.add_argument('--timeout',type=int,default=3600);a=ap.parse_args()
    raise SystemExit(0 if duel(a.rom,a.creature,black=a.black,kit=a.kit,observe=a.observe,timeout=a.timeout,tag=a.tag,resilient=a.resilient) else 1)
