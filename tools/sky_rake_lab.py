"""Copied-latest-save Sky Rake: native air chains, contacts, exits and shop persistence."""
import argparse
import ctypes as ct
import json
from pathlib import Path
import struct
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import kit_lab as k, vortex_forge_lab as v, wos_tool as w, sky_rake as s


def run(a):
    if not a.out.resolve().is_relative_to((ROOT/'work').resolve()):
        raise ValueError('Sky Rake evidence belongs in work/')
    actual, before, copied = v.copy_current(a.out)
    profile = json.loads(a.owned.read_text(encoding='utf-8'))
    if w.sha256(before) != profile['source_sha256']:
        raise ValueError('Actual battery changed; remeasure current player')
    boot = (Path(profile['captures'])/'ram-03500.bin').read_bytes()
    form = 0 if a.case == 'red' else 1
    actor = k.p.sample(boot)['actor_address']-k.p.BASE
    inputs = [] if w.u32(boot,actor+0x34)==form else [dict(start=4,end=10,buttons=['L'])]
    mirror = a.case in ('mirror','wall')
    inputs += [dict(start=30,end=36,buttons=['Left' if mirror else 'Right']),
               dict(start=60,end=66,buttons=['Up','A'])]
    if a.case != 'ground':
        inputs.append(dict(start=96,end=128,buttons=['B']))
    presses = (120,136,152,168,184,200) if a.case=='approach' else (112,128,144,160,176,192)
    inputs += [dict(start=t,end=t+6,buttons=['Y']) for t in presses]
    if a.case=='approach':inputs.append(dict(start=108,end=112,buttons=['Right']))
    if a.case in ('air-a','air-down-a'):
        inputs = [r for r in inputs if r['start'] != 60 and r['buttons'] != ['Y']]
        inputs.append(dict(start=112,end=118,buttons=['A'] if a.case=='air-a' else ['Down','A']))
    if a.case in ('cancel','cancel-no-air-dodge','swap','hurt'):
        if a.case!='hurt':
            inputs.append(dict(start=118,end=124,buttons=['L' if a.case=='swap' else 'R']))
        inputs = [r for r in inputs if r['buttons'] != ['Y'] or r['start']==112]
    if a.case=='swap':inputs.append(dict(start=212,end=218,buttons=['L']))
    rows, pcm, rate, selected = [], [], [0], []
    def hook(frame,lib):
        ptr,ram = k.ram_of(lib)
        if -20<=frame<70:
            for e in k.enemies(ram):
                if e['controller'] and e['state'] in (0,1,2,15):
                    ct.memmove(ptr+e['controller']-k.p.BASE+0x14,bytes(4),4)
                    ct.memmove(ptr+e['controller']-k.p.BASE+4,b'\x01',1)
        if frame==58:
            # One initial HP fixture lets one training foe survive the entire five-contact chain.
            px,py=k.p.sample(ram)['position_q12_candidate']
            enemies=sorted(k.enemies(ram),key=lambda e:abs(e['position'][0]-px))
            side=-1 if mirror else 1
            for i,e in enumerate(enemies):
                mot=w.u32(ram,e['actor']-k.p.BASE+0x30)-k.p.BASE
                gap=(75 if a.case=='whiff' else 7)*side if i==0 else (-75-10*i)*side
                k.teleport(ptr,ram,mot,px+gap*4096,py+246)
                if i==0:
                    selected.append(e['actor'])
                    hp=196608
                    ct.memmove(ptr+e['actor']-k.p.BASE+0x44,struct.pack('<2i',hp,hp),8)
        if frame<0:return
        if frame==90:
            info=(ct.c_byte*40)();lib.retro_get_system_av_info.argtypes=[ct.c_void_p]
            lib.retro_get_system_av_info(ct.byref(info));rate[0]=round(struct.unpack_from('<d',bytes(info),32)[0])
            lib._wos_audio_sink=lambda f,data:pcm.append(data) if k.TRAINING_START+90<=f<k.TRAINING_START+240 else None
        sample=k.p.sample(ram);hero=sample['actor_address']-k.p.BASE;mot=sample['motion_address']-k.p.BASE
        ctl=w.u32(ram,mot+0x1f8)-k.p.BASE;wrapper=w.u32(ram,mot+0x58)-k.p.BASE
        slot=w.u32(ram,wrapper+0x29c)
        if slot not in (0,1):raise ValueError('Invalid native blend slot')
        if frame==119 and a.case=='hurt':
            ct.memmove(ptr+ctl+0x14,struct.pack('<I',63),4)
            ct.memmove(ptr+ctl+4,b'\x01',1)
        rows.append(dict(frame=frame,form=w.u32(ram,hero+0x34),state=w.u32(ram,ctl+0x14),
            action=w.u32(ram,mot+0x258),clock=w.u32(ram,mot+0x178),
            sca=w.u32(ram,wrapper+0x1c4+0x78*slot),enemies=k.enemies(ram)))
    native=k.rows_from
    k.rows_from=lambda path:v.current_prefix(path) if str(path).endswith('oscorp-owned.json') else native(path)
    try:
        route,obs=k._run(a.rom,a.tag,inputs,frames=280,bits=1<<21,
            clear=1<<10 if a.case=='cancel-no-air-dodge' else 0,clear2=1<<21,
            bits2=0 if a.case=='unowned' else 1<<21,sparring=True,start_x=(14 if a.case=='wall' else 100)*4096,
            save=copied,caps=tuple(range(108,236,2)),rams=(119,140,182,230),extra_hook=hook,
            core_options={b'melonds_jit_enable':b'enabled',b'melonds_jit_block_size':b'12'})
    finally:k.rows_from=native
    if rate[0] and pcm:
        with wave.open(str(a.out/'mixed.wav'),'wb') as audio:
            audio.setparams((2,2,rate[0],0,'NONE','not compressed'));audio.writeframes(b''.join(pcm))
    target=selected[0]
    foes=[next((e for e in r['enemies'] if e['actor']==target),None) for r in rows]
    losses=[dict(frame=i,action=rows[i]['action'],clock=rows[i]['clock'],hp=e['hp'],state=e['state'])
            for i,e in enumerate(foes) if i>=60 and e and foes[i-1] and e['hp']<foes[i-1]['hp']]
    air=[r for r in rows if r['state']==51 and 1<=r['action']<=4]
    names,_=s.assets.resources(a.rom.read_bytes())
    scas={names.index(f'zz_S35_Air{i}.sca') for i in range(1,5) if f'zz_S35_Air{i}.sca' in names}
    routed=[r for r in air if r['sca'] in scas]
    checks=dict(actual_battery_unchanged=actual.read_bytes()==before and copied.read_bytes()==before,
        collision_bounds=all(3.4*4096<=r['pos'][0]<=237*4096 for r in obs))
    if a.case in ('unowned','red','ground','air-a','air-down-a'):
        checks['no_private_air_route']=not routed
    else:
        checks['private_black_air_route']=bool(routed) and len(routed)==len(air)
        if a.case in ('cancel','cancel-no-air-dodge','hurt'):
            checks['interruption_exits']=any(118<=r['frame']<=126 and r['state']!=51 for r in rows)
            checks['no_later_contacts']=not any(d['frame']>124 for d in losses)
        elif a.case=='swap':
            changed=[r['frame'] for r in rows if r['frame']>=212 and r['form']==0]
            checks['native_ground_form_switch']=bool(changed) and rows[-1]['form']==0
            checks['no_private_route_after_switch']=bool(changed) and not any(r['frame']>=changed[0] for r in routed)
        elif a.case=='whiff':checks['no_air_contact_on_whiff']=not any(1<=d['action']<=4 for d in losses)
        else:
            checks['all_four_actions']=set(r['action'] for r in air)=={1,2,3,4}
            checks['five_air_contacts']=len([d for d in losses if 1<=d['action']<=4])>=5
            kicks=[d for d in losses if d['action']==4]
            checks['kick_pops_up']=any(any(e and e['state']==39 for e in foes[d['frame']:d['frame']+12]) for d in kicks)
    report=dict(passed=all(checks.values()),case=a.case,checks=checks,rom_sha256=w.sha256(a.rom.read_bytes()),
        route=str(route),source_battery_sha256=w.sha256(before),target_actor=target,damage=losses,
        sequence=k.seq(obs),rows=rows,
        limits='Copied latest actual battery; ordinary Continue/Test Upgrades. Disposable initial form/ownership, '
        'one initial target layout/HP fixture and idle enemy prefix through70; native movement/contact/AI afterward. '
        'Hurt case injects one controller interruption. Training healing/immortality apply. No actual save writes, '
        'campaign-balance, perceptual audio or hardware-pacing claim.')
    w.write_json(a.out/'result.json',report)
    print(json.dumps({key:report[key] for key in ('passed','case','checks','damage','route')}),flush=True)
    return 0 if report['passed'] else 1


def boss(a):
    """Native-input attacks on live chapter enemies; no enemy state/position writes."""
    import os
    from tools import chapter_renewal_lab as q, creature_forge_lab as forge, midnight_rework_lab as lab
    from tools import midnight_walk as mw, owned_player_lab
    if not a.out.resolve().is_relative_to((ROOT/'work').resolve()):
        raise ValueError('Sky Rake evidence belongs in work/')
    actual,before,copied=v.copy_current(a.out)
    os.environ['WOS_CHAPTER_LAB_SAVE']=str(copied);owned_player_lab.install(a.owned)
    q.configure_rooms(a.rom);forge.OUT=a.out;q.OUT=a.out;q.RUN_TAG='-'+a.tag;forge.install(a.rom,6)
    meta=json.loads(a.rom.with_suffix('.build.json').read_text())
    config=meta['creature_forge']['creatures']['conductor']['config']
    heavy=a.case.startswith('boss')
    native,rows,started,seen,fixtures,fixture_jumps=lab.Walker.tick,[],[-1000],set(),[],set()
    def tick(self,frame,lib):
        if frame==-990 and heavy:
            ptr,ram=k.ram_of(lib);stats=w.u32(ram,k.STATS_POINTER-k.p.BASE)-k.p.BASE
            flags=int.from_bytes(ram[stats+0x1c:stats+0x44],'little')&~(1<<147)
            ct.memmove(ptr+stats+0x1c,flags.to_bytes(40,'little'),40)
        native(self,frame,lib)
        if frame<0:return
        ptr,ram=k.ram_of(lib)
        if frame==0:
            stats=w.u32(ram,k.STATS_POINTER-k.p.BASE)-k.p.BASE
            ct.memmove(ptr+stats+0x14,struct.pack('<I',w.u32(ram,stats+0x14)|(1<<21)),4)
        current=self.last_state
        if not current or not current.pos:return
        self.buttons.clear()
        if not current.black:
            if frame%60<6:self.buttons.add('L')
        foes=[e for e in current.enemies if not heavy or w.u32(ram,e['actor']-k.p.BASE+0x40)==config]
        seen.update(e['actor'] for e in foes)
        living=sorted(foes,key=lambda e:abs(e['position'][0]/4096-current.pos[0]))
        if current.black and living:
            dx=living[0]['position'][0]/4096-current.pos[0]
            face=k.p.sample(ram)['facing_candidate'];toward='Right' if dx>=0 else 'Left'
            age=frame-started[0]
            if age<100:
                if not heavy:
                    if age<6:self.buttons.add('B')
                    if current.state in (15,19,51) and 4<=age<90 and (age-4)%16<6:self.buttons.add('Y')
                else:
                    if age<6:self.buttons.add('B')
                    if 4<=age<90 and (age-4)%16<6:self.buttons.add('Y')
            elif abs(dx)>8 or face!=int(dx>=0):self.buttons.add(toward)
            elif current.state==0 and age>=130:
                if not heavy and not fixtures:
                    ct.memmove(ptr+living[0]['actor']-k.p.BASE+0x44,struct.pack('<I',4096),4)
                    fixtures.append(dict(frame=frame,actor=living[0]['actor'],initial_hp=4096))
                self.buttons.add('B');started[0]=frame
        elif current.black and current.pos[0]<100:self.buttons.add('Right')
        sample=k.p.sample(ram);mot=sample['motion_address']-k.p.BASE
        if a.case=='boss-finisher' and started[0] not in fixture_jumps and current.state==51 and w.u32(ram,mot+0x258)==1 and w.u32(ram,mot+0x178)==0:
            ctl=w.u32(ram,mot+0x1f8)-k.p.BASE
            ct.memmove(ptr+ctl+0x80,struct.pack('<I',2),4)
            for off in (0x254,0x258):ct.memmove(ptr+mot+off,struct.pack('<I',4),4)
            ct.memmove(ptr+mot+0x2fc,struct.pack('<I',w.u32(ram,mot+0x2fc)|2),4)
            fixtures.append(frame)
            fixture_jumps.add(started[0])
        if not heavy:foes += [e for e in k.enemies(ram) if e['actor'] in seen and e['hp']==0]
        rows.append(dict(frame=frame,state=current.state,action=w.u32(ram,mot+0x258),
            clock=w.u32(ram,mot+0x178),hero_pos=current.pos,enemies=foes,last_hit_kind=w.u32(ram,k.KIT_STATE-k.p.BASE+0x380)))
    lab.Walker.tick=tick
    try:route=q.run(a.rom,a.tag,'ML_Venom' if heavy else 'ML_Station',2 if heavy else 1,[mw.wait(1300)],combat=True,heal=True)
    finally:lab.Walker.tick=native
    live=[r for r in rows if r['enemies']]
    previous,drops={},[]
    for r in live:
        for e in r['enemies']:
            if e['actor'] in previous and e['hp']<previous[e['actor']]:
                drops.append(dict(frame=r['frame'],action=r['action'],state=r['state'],enemy_state=e['state'],hp=e['hp'],actor=e['actor'],native_kind=r['last_hit_kind']))
            previous[e['actor']]=e['hp']
    checks=dict(actual_air_hp_loss=any(d['state']==51 and 1<=d['action']<=4 for d in drops),
        source_battery_unchanged=actual.read_bytes()==before and copied.read_bytes()==before)
    if heavy:
        checks['heavy_never_launched']=all(e['state'] not in (39,42,44,45,46,48,49) for r in live for e in r['enemies'])
        if a.case=='boss-finisher':checks['kick_contact']=any(d['state']==51 and d['action']==4 and d['native_kind']==0x16 for d in drops)
    else:checks['native_air_kill']=any(d['state']==51 and 1<=d['action']<=4 and d['hp']==0 for d in drops)
    report=dict(passed=all(checks.values()),case=a.case,checks=checks,route=route,damage=drops,rows=rows,fixtures=fixtures,
        rom_sha256=w.sha256(a.rom.read_bytes()),source_battery_sha256=w.sha256(before),
        limits='Copied latest actual battery and measured current purchases/XP. Disposable initial room arrival, '
        'cleared already-earned boss flag147 for boss cases, Sky Rake ownership and player healing. Enemy HP/state/position, AI '
        'and subsequent player L/B/Y/directional movement stay native. Encounter alone gives the first close '
        'enemy one initial 4096-HP lifecycle fixture. Boss-finisher alone presets air node2, action4 and '
        'native resource refresh once per initial air action to isolate the kick; it does not prove a full natural '
        'five-hit combo on a standing heavy. No victory, balance or player-verdict claim.')
    w.write_json(a.out/'result.json',report)
    print(json.dumps({key:report[key] for key in ('passed','checks','damage')}),flush=True)
    return 0 if report['passed'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--owned',type=Path,required=True);p.add_argument('--tag',required=True)
    p.add_argument('--case',choices=('chain','approach','mirror','wall','unowned','red','whiff','cancel','cancel-no-air-dodge','swap','hurt','ground','air-a','air-down-a','shop','boss','boss-finisher','encounter'),default='chain')
    a=p.parse_args()
    if a.case=='shop':
        from tools.hunter_kit_lab import shop
        sys.exit(shop(a,row=8,bit=s.BIT,price=s.PRICE))
    sys.exit(boss(a) if a.case.startswith('boss') or a.case=='encounter' else run(a))
