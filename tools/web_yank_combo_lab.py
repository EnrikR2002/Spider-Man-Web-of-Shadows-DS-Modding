"""Copied-latest-save Down+A utility, native control parity and chosen follow-ups."""
import argparse
import ctypes as ct
import json
from pathlib import Path
import struct
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import kit_lab as k, vortex_forge_lab as v, wos_tool as w


def six_enemy_fixture(rom):
    """Lab-only six-Brute OBJ; production executable and every other asset stay exact."""
    from tools import hunter_kit, training_room, room_script
    from tools.room_objects import RoomObjects
    from tools.room_entities import Entities, Batch
    source=rom.read_bytes()
    names,blobs=hunter_kit.assets.resources(source)
    index=names.index(training_room.NAME)
    parsed=RoomObjects.parse(blobs[index])
    batches=Entities.parse(parsed.records[2].sections[0]).batches
    assert len(batches)==1 and len(batches[0].records)==4
    records=list(batches[0].records)
    for x in (160,185):
        rec=bytearray(records[-1]);struct.pack_into('<i',rec,0,x*4096);records.append(bytes(rec))
    header=struct.pack('<HBB',12+24*6,12,6)+bytes([24]*6)+bytes(2)
    section=Entities((Batch(header,tuple(records)),)).to_bytes()
    labels=room_script._name_block(parsed.names[2],{0:['Character (Practice Dummy)']*2})
    blobs[index]=room_script._replace(parsed,2,{0:section},{},labels)
    assert len(Entities.parse(RoomObjects.parse(blobs[index]).records[2].sections[0]).records)==6
    result=w.rebuild_rom(source,{'Glob.bin':w.pack_glob(names,blobs)},legacy_gaps=True)
    ah,bh=w.parse_header(source),w.parse_header(result)
    assert source[ah['arm9_offset']:ah['arm9_offset']+ah['arm9_size']]==result[bh['arm9_offset']:bh['arm9_offset']+bh['arm9_size']]
    nn,bb=hunter_kit.assets.resources(result)
    assert names==nn and [n for n,a,b in zip(names,hunter_kit.assets.resources(source)[1],bb) if a!=b]==[training_room.NAME]
    out=ROOT/'build'/('yank-six-fixture-'+w.sha256(source)[:8])/'Lab.nds'
    w.atomic_write(out,result,sources=(rom,))
    meta=json.loads(rom.with_suffix('.build.json').read_text())
    meta.update(output_rom_sha256=w.sha256(result),yank_six_fixture=dict(source_rom_sha256=w.sha256(source),
        modified_resource=training_room.NAME,enemy_count=6,executable_and_other_assets_exact=True))
    w.write_json(out.with_suffix('.build.json'),meta)
    return out


def run(a):
    if not a.out.resolve().is_relative_to((ROOT/'work').resolve()):
        raise ValueError('Pure-pull lab evidence must stay in work/')
    actual, before, copied = v.copy_current(a.out)
    profile = json.loads(a.owned.read_text(encoding='utf-8'))
    if w.sha256(before) != profile['source_sha256']:
        raise ValueError('Actual battery changed; measure current player again')
    boot = (Path(profile['captures'])/'ram-03500.bin').read_bytes()
    desired = 0 if a.case == 'red' else 1
    hero = k.p.sample(boot)['actor_address']-k.p.BASE
    inputs = [] if w.u32(boot,hero+0x34)==desired else [dict(start=4,end=10,buttons=['L'])]
    mirror = a.case == 'mirror'
    inputs.append(dict(start=30,end=36,buttons=['Left' if mirror else 'Right']))
    cast = 84 if a.case == 'combo' else 60
    buttons = {'x':['X'], 'up-x':['Up','X'], 'plain-a':['A'], 'up-a':['Up','A']}.get(a.case,['Down','A'])
    inputs.append(dict(start=cast,end=145 if a.case=='hold' else cast+6,buttons=buttons))
    if a.case == 'combo':
        inputs += [dict(start=t,end=t+6,buttons=['Y']) for t in (40,68,124)]
    if a.case in ('followup','lift'):
        inputs.append(dict(start=98,end=104,buttons=['Up','A'] if a.case=='lift' else ['Y']))
    if a.case in ('cancel','swap'):
        inputs.append(dict(start=70,end=76,buttons=['R' if a.case=='cancel' else 'L']))
    if a.case == 'air': inputs.append(dict(start=46,end=52,buttons=['B']))
    if a.case == 'repeat':
        inputs += [dict(start=t,end=t+6,buttons=['Down','A']) for t in (110,160,210)]
    if a.case == 'moving': inputs.append(dict(start=30,end=75,buttons=['Right']))
    meta = json.loads(a.rom.with_suffix('.build.json').read_text())
    rt = meta['hunter_kit']['runtime']
    state = rt['state']-k.p.BASE
    crowd=meta.get('web_yank_combo',{}).get('runtime',{}).get('records')
    dx = 6 if a.case=='close' else 80 if a.case=='whiff' else a.distance
    side = -1 if mirror else 1
    dx *= side
    rows, pcm, rate, injected = [], [], [0], [False]
    def hook(frame,lib):
        ptr,ram = k.ram_of(lib)
        if -20 <= frame < cast+10 or a.case=='repeat' and any(t-20<=frame<t+10 for t in (110,160,210)):
            for e in k.enemies(ram):
                if e['controller'] and e['state'] in (0,1,2,15):
                    ct.memmove(ptr+e['controller']-k.p.BASE+0x14,bytes(4),4)
                    ct.memmove(ptr+e['controller']-k.p.BASE+4,b'\x01',1)
        if frame == cast-2 or a.case=='repeat' and frame in (108,158,208):
            px,py = k.p.sample(ram)['position_q12_candidate']
            foes = sorted(k.enemies(ram),key=lambda e:abs(e['position'][0]-(px+dx*4096)))
            gaps=(16,20,24,28,32,36) if a.case=='crowd' else (dx,-75*side,-85*side,-95*side)
            for e,gap in zip(foes,gaps):
                motion = w.u32(ram,e['actor']-k.p.BASE+0x30)-k.p.BASE
                k.teleport(ptr,ram,motion,px+round(gap*4096),py+246)
            ptr,ram = k.ram_of(lib)
        if frame < 0: return
        if frame == 50:
            info = (ct.c_byte*40)()
            lib.retro_get_system_av_info.argtypes=[ct.c_void_p]
            lib.retro_get_system_av_info(ct.byref(info))
            rate[0]=round(struct.unpack_from('<d',bytes(info),32)[0])
            lib._wos_audio_sink=lambda f,data:pcm.append(data) if k.TRAINING_START+50<=f<k.TRAINING_START+160 else None
        if 50<=frame<160 and frame%2==0:
            video,pixel=lib._wos_video
            w.atomic_write(a.out/'motion'/f'frame-{(frame-50)//2:03d}.png',k.emu.frame_png(video,pixel))
        private=list(struct.unpack_from('<32I',ram,state))
        if frame==73 and private[6] and a.case in ('hurt','stale'):
            if a.case=='hurt':
                ct.memmove(ptr+private[1]-k.p.BASE+0x14,struct.pack('<I',63),4)
                ct.memmove(ptr+private[1]-k.p.BASE+4,b'\x01',1)
            else: ct.memmove(ptr+state+20,bytes(4),4)
            injected[0]=True
        sample=k.p.sample(ram)
        controller=sample['controller']['address']-k.p.BASE
        motion=sample['motion_address']-k.p.BASE
        wrapper=w.u32(ram,motion+0x58)-k.p.BASE
        slot=w.u32(ram,wrapper+0x29c)
        rows.append(dict(frame=frame,private=private,hero_pos=sample['position_q12_candidate'],
            records=[private]+[list(struct.unpack_from('<32I',ram,crowd-k.p.BASE+128*i)) for i in range(4)] if crowd else [private],
            hero_state=sample['controller']['state_id_candidate'],node=w.u32(ram,controller+0x80),
            weak_head=w.u32(ram,sample['actor_address']-k.p.BASE+4),
            sca=w.u32(ram,wrapper+0x1c4+0x78*slot),enemies=k.enemies(ram)))
    native=k.rows_from
    k.rows_from=lambda p:v.current_prefix(p) if str(p).endswith('oscorp-owned.json') else native(p)
    try:
        route,obs=k._run(a.rom,a.tag,inputs,frames=280 if a.case=='repeat' else 180,
            bits=0,bits2=0 if a.case=='unowned' else 1<<19,clear2=1<<19,sparring=True,
            start_x=100*4096,place=tuple((round(d*4096),246) for d in (dx,-75*side,-85*side,-95*side)),
            save=copied,caps=tuple(range(60,132,4)),rams=(62,74,98),extra_hook=hook,
            core_options={b'melonds_jit_enable':b'enabled',b'melonds_jit_block_size':b'12'})
    finally: k.rows_from=native
    starts=max(r['private'][15] for r in rows)
    active=[r for r in rows if r['private'][6]]
    checks=dict(actual_battery_unchanged=actual.read_bytes()==before and copied.read_bytes()==before,
        cleanup_complete=all(rows[-1]['private'][i]==0 for i in (0,1,2,6,24,28)),
        hero_weak_head_unlinked=all(r['weak_head'] not in ([rt['state']+112]+[crowd+128*i+112 for i in range(4)] if crowd else [rt['state']+112]) for r in rows if not r['private'][6]),
        all_target_records_clean=all(rec[i]==0 for rec in rows[-1]['records'] for i in (2,24,28)))
    native_cases=('x','up-x','plain-a','up-a','air','unowned','red','close','whiff')
    target=next((r['private'][2]-4 for r in active if r['private'][2]),None)
    foe=lambda r:next((e for e in r['enemies'] if e['actor']==target),None)
    damage=[dict(frame=r['frame'],hp=foe(r)['hp']) for prev,r in zip(rows,rows[1:])
            if foe(prev) and foe(r) and foe(r)['hp']<foe(prev)['hp']]
    if a.case in native_cases:
        checks['no_custom_activation']=starts==0
    else:
        checks['owned_down_a_cast']=starts>=1
        checks['private_cast_clip']=any(r['sca']==rt['values']['YANK_SCA'] for r in active)
        checks['no_utility_damage']=not any(cast<=d['frame']<=cast+30 for d in damage)
        if a.case in ('cancel','swap','hurt','stale'):
            if a.case=='cancel': checks['native_r_exit']=any(70<=r['f']<=78 and r['st'] in (52,53,54,55,57) for r in obs)
            if a.case in ('hurt','stale'):checks['fixture_applied']=injected[0]
        else:
            pulls=[r for r in rows if r['private'][16]]
            checks['upright_reel']=bool(pulls) and any(rec[23] for r in pulls for rec in r['records'])
            checks['zero_hp_catch_flash_suppressed']=max(r['private'][17] for r in rows)>=1
            release=next((r for p,r in zip(rows,rows[1:]) if p['private'][6] and not r['private'][6]),None)
            e=foe(release) if release else None
            gap=(e['position'][0]-release['hero_pos'][0])/4096*side if e else None
            checks['arrival_in_melee_and_native_idle']=release is not None and release['hero_state']==0 and gap is not None and 3<=gap<=12
            if a.case in ('followup','combo','lift'):
                checks['chosen_followup_damages']=bool(damage)
                checks['chosen_talon_lift' if a.case=='lift' else 'chosen_native_y']=any(r['f']>=98 and r['st']==(45 if a.case=='lift' else 46) and r['act']!=49 for r in obs)
            else: checks['pure_pull_no_damage']=not damage
            if a.case=='repeat': checks['four_distinct_casts']=starts==4
    report=dict(case=a.case,passed=all(checks.values()),checks=checks,starts=starts,
        rom_sha256=w.sha256(a.rom.read_bytes()),source_battery_sha256=w.sha256(before),route=str(route),
        target=target,damage=damage,sequence=k.seq(obs),rows=rows,
        limits='Fresh latest actual DSV copy; disposable bit83, training XP/healing, initial positions and '
        'pre-input layout/idle re-entry until ten frames after input (before each of four casts for repeat). '
        'Native AI/collision/reactions afterward. '
        'Hurt/stale controls inject one labelled private-RAM interruption. No real save writes or balance/feel claim.')
    if a.case=='crowd':
        caught={rec[2]-4 for r in rows for rec in r['records'] if rec[2] and rec[11]==4}
        bound=max(sum(rec[2]!=0 for rec in r['records']) for r in rows)
        checks['independent_crowd_targets']=len(caught)>=min(5,max(len(r['enemies']) for r in rows))
        checks['never_binds_more_than_five']=bound<=5
        checks['all_target_and_line_refs_clean']=all(rec[i]==0 for rec in rows[-1]['records'] for i in (2,24,28))
        report.update(caught=sorted(caught),peak_bound=bound,passed=all(checks.values()),fixture=meta.get('yank_six_fixture'))
    w.write_json(a.out/'result.json',report)
    if pcm:
        with wave.open(str(a.out/'motion.wav'),'wb') as s:
            s.setnchannels(2);s.setsampwidth(2);s.setframerate(rate[0]);s.writeframes(b''.join(pcm))
    print(json.dumps({key:report[key] for key in ('case','passed','checks','starts','damage')}),flush=True)
    return 0 if report['passed'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--owned',type=Path,required=True);p.add_argument('--tag',required=True)
    p.add_argument('--distance',type=float,default=28)
    p.add_argument('--six-enemies',action='store_true',help='Lab-only six-Brute room, with exact production executable/assets')
    p.add_argument('--case',choices=('regular','mirror','close','x','up-x','plain-a','up-a','air','unowned','red',
        'whiff','followup','lift','combo','crowd','hold','repeat','cancel','swap','hurt','stale','moving','boss'),default='regular')
    a=p.parse_args()
    if a.six_enemies: a.rom=six_enemy_fixture(a.rom)
    if a.case=='boss':
        from tools import hunter_kit_lab
        raise SystemExit(hunter_kit_lab.boss(a))
    raise SystemExit(run(a))
