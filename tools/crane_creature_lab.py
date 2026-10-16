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
        return {'Up'} if dy>8 else {'B','Right' if dx>0 else 'Left'}
    if dy>28 and 96<=state.room<108:
        width=cr.BOUNDS[state.room-96][0];left=ex<width/2;edge=x if left else width-x
        buttons={'Left' if left else 'Right'}
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


def duel(rom,key,*,black=False,kit=False,observe=360,timeout=3600,tag='',resilient=False):
    runtime=metadata(rom);spec=c.BY_KEY.get(key);configs={v:k for k,v in runtime['configs'].items()}
    cw.install();mw.PLAYER_ABILITIES=0x180FFFDF if kit else 0x1F
    holder={}
    class DuelWalker(cw.Walker):
        def __init__(self,*args,**kw):
            super().__init__(*args,**kw);self.rows=[];self.on['fight']=False;holder['walker']=self
        def tick(self,frame,lib):
            if frame+k.TRAINING_START>=2040:
                ptr,ram=k.ram_of(lib)
                # Before native room initialization: exactly one actor, selected
                # through the shipped native spawner. No position/state writes.
                if spec is not None:
                    ct.memmove(ptr+runtime['state']-p.BASE,struct.pack('<2I',97,{'maw':0,'spore':1,'ballast':2}[key]),8)
                    ct.memmove(ptr+runtime['goals']['crew']-p.BASE,struct.pack('<2I',spec.cost*4096,spec.cost*4096),8)
                state=self.read(frame,ram)
                if state and state.room==97 and state.pos:
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
            if step[0]!='until' or step[1]!='real_hp_duel_clears':return
            _,ram=k.ram_of(lib);s=self.read(frame,ram)
            if not s or not s.pos:return
            if not s.enemies:
                if not mw.flag(flag)(s):
                    self.buttons.clear()
                    if abs(s.pos[0]-200)>10:self.buttons.add('Right' if s.pos[0]<200 else 'Left')
                    if frame%64<36:self.buttons.add('B')
                return
            enemy=min(s.enemies,key=lambda e:abs(e['position'][0]/4096-s.pos[0])+abs(e['position'][1]/4096-s.pos[1]))
            self.buttons.clear();self.buttons.update(pursuit_buttons(frame,s,enemy,kit))
    cw.Walker=DuelWalker
    switch=[mw.until('black_form',lambda s:s.black==1,300,'tapL')] if black else []
    flag=cr.FLAGS['freight']
    steps=[mw.fixtures(fight=False),*switch,('travel',100,600),mw.wait(observe),
           mw.until('real_hp_duel_clears',mw.flag(flag),timeout),mw.wait(60)]
    label=f'creature-duel-{key}-'+('black' if black else 'red')+('-kit' if kit else '-base')+tag
    result=cw.run(rom,label,'AR_FreightExchange',1,steps)
    rows=holder['walker'].rows;summary=summarize(rows)
    passed=result['passed'] and (key in summary['damaged'] if spec else set(summary['damaged'])==set(c.BY_KEY) and summary['max_distinct']==3)
    out=cw.OUT/'creatures'/f'{label}-{result["rom_sha256"][:8]}.json'
    w.write_json(out,{'passed':passed,'summary':summary,'route':result,'observations':rows,
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
