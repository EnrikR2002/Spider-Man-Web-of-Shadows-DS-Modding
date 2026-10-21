"""Immutable0.23.0 post-pass for the player's Midnight enemy/room rejection."""
import argparse,json,struct,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import mod
from tools import wos_tool as w,tasm_kit as kit,chapter_spectacle as parent
from tools import creature_forge as forge,crane_row as crane
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob
from tools.chapter_renewal_combat import asm

VERSION='0.24.0'
DATE='2026-10-18'
PARENT='534c9df52d91f6dbb4102f4deb9143fbaea6b8324f9e7525db4a3880d226e18c'
OUT=ROOT/'build/version-0.24.0-final'
offset=forge.offset


def align_contacts(raw,windows):
    wrap=CompressedBlob.parse(raw);g=Gmb.parse(wrap.decoded);changed=bytearray(wrap.decoded);found=0
    for ch in g.channels:
        if ch.kind!=3 or ch.words(0)[7]!=8192:continue
        found+=1
        for f in range(g.record_count):
            struct.pack_into('<i',changed,ch.offset+4+f*ch.stride+20,int(any(a<=f<b for a,b in windows)))
    if not found:raise ValueError('Authored contact clip has no native attack volume')
    if Gmb.parse(changed).to_bytes()!=changed:raise ValueError('Contact round trip failed')
    return wrap.replace_decoded(bytes(changed),compact=True)


def audio_observer(at,table,old,request=False):
    """Diagnostic only: log unmodified requests and the native caller context."""
    return asm(f'''
        push {{r0-r12,lr}}
        mrs r12,cpsr
        {'ldr r1,[r1]' if request else ''}
        ldr r0,table
        ldr r2,[r0]
        add r3,r2,#1
        str r3,[r0]
        and r2,r2,#255
        add r0,r0,#4
        add r0,r0,r2,lsl #5
        str r1,[r0]
        str lr,[r0,#4]
        str r4,[r0,#8]
        str r5,[r0,#12]
        str r6,[r0,#16]
        str r7,[r0,#20]
        str r8,[r0,#24]
        ldr r3,[sp,#60]
        str r3,[r0,#28]
        msr cpsr_f,r12
        pop {{r0-r12,lr}}
        {'push {r4-r6,lr}' if request else ''}
        b #0x{old:x}
    table: .word 0x{table:x}
    ''',at)


def authored_motion(native,names,style,stem,prefix):
    from tools import midnight_enemy_motion as motion
    deps=('midnight_enemy_motion.py','creature_forge_motion.py','creature_forge_design.py')
    key=w.sha256(b''.join((ROOT/'tools'/f).read_bytes() for f in deps)+style.encode()+native(stem+'.xbd'))
    path=ROOT/'work/midnight-rebuild/motion-cache'/(key+'.zip')
    if path.exists():
        with zipfile.ZipFile(path) as z:
            meta=json.loads(z.read('manifest.json'));extras={n:z.read(n) for n in z.namelist() if n!='manifest.json'}
        if meta['hashes']!={n:w.sha256(v) for n,v in extras.items()}:raise ValueError('Motion cache mismatch')
        return extras,meta['clips']
    extras,links,clips=motion.prepare(native,names,style,stem,prefix);path.parent.mkdir(exist_ok=True,parents=True)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,v in extras.items():z.writestr(n,v)
        z.writestr('manifest.json',json.dumps(dict(clips=clips,hashes={n:w.sha256(v) for n,v in extras.items()})))
    return extras,clips


def apply_rom(rom,*,contact_pilot=False,observe_audio=False,observe_requests=False,motion_pilot=False,full_motion=False,voices=False,rooms_pilot=False,rooms=False):
    if w.sha256(rom)!=PARENT:raise ValueError('Rebuild requires exact published0.23.0')
    fs=next(e for e in w.nitrofs_entries(rom) if e['name']=='Glob.bin');glob=rom[fs['start']:fs['end']]
    o,names,_=w.parse_glob(glob);blobs=[glob[a:b] for a,b in zip(o,o[1:])]
    before=tuple(blobs);meta=json.loads((ROOT/'build/version-0.23.0-final/Versioned.build.json').read_text(encoding='utf-8'))
    h=w.parse_header(rom);arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']];new=bytearray(arm)
    end=len(arm)-36;start=kit.TARGET+end-kit.SOURCE;data=bytearray();changed=[];rebuilt={}
    def alloc(raw):
        data.extend(bytes(-len(data)%4));address=start+len(data);data.extend(raw);return address
    if motion_pilot or full_motion or rooms_pilot or rooms:
        _,native_glob,_=mod.load_clean();no,nn,_=w.parse_glob(native_glob)
        def native(n):i=nn.index(n);return native_glob[no[i]:no[i+1]]
    if motion_pilot or full_motion:
        from tools import midnight_enemy_motion as motion,midnight_enemy_art as art,creature_forge_art,creature_texture_fix
        from tools.animation_rig import AnimationRig
        from tools.sca import Sca
        impact=0;rt=meta['creature_forge']['runtime']
        for index,(style,stem,group,cfg) in enumerate(forge.parent.PRIVATE_STYLES):
            if motion_pilot and style!='skitter':impact+=len(motion.MOVES[style]);continue
            print('AUTHOR '+style,flush=True)
            extras,clips=authored_motion(native,nn,style,stem,'zz_F22_'+style)
            # Keep the already-private XBD and all binding IDs exact. Only its
            # owned animation/contact payloads are regenerated in place.
            extras.pop('zz_F22_'+style+'.xbd')
            for name,payload in extras.items():
                if name not in names:raise ValueError('Private binding absent: '+name)
                idx=names.index(name);blobs[idx]=payload+bytes((len(blobs[idx])-len(payload))%4);changed.append(name)
            rig=AnimationRig.parse(native(stem+'.nsbmd'));neutral=motion.pose(Sca.parse(native(stem+'_Idle.sca')),rig.parents,style,stem)
            neutral.rebuild_style=style
            model,art_report=creature_forge_art.model(style,stem,native(stem+'.nsbmd'),neutral,sculpt_type=art.Sculpt)
            model,_=creature_texture_fix.fix_model(model);name='zz_F22_'+style+'.nsbmd';idx=names.index(name)
            blobs[idx]=model+bytes((len(blobs[idx])-len(model))%4);changed.append(name)
            table=w.u32(arm,offset(rt['records'])+index*16+4)
            for j,m in enumerate(motion.MOVES[style]):
                drive=alloc(b''.join(struct.pack('<3i',a,b,round(v*4096)) for a,b,v in m.drives)+struct.pack('<3i',0x7fffffff,0,0))
                jump=alloc(b''.join(struct.pack('<2i',a,round(v*4096)) for a,v in m.jumps)+struct.pack('<2i',0x7fffffff,0))
                cue=alloc(b''.join(struct.pack('<2i',a,653+35+impact) for a,b in m.contacts)+struct.pack('<2i',0x7fffffff,0))
                struct.pack_into('<8I',new,offset(table)+j*32,m.action,m.samples-1,m.cooldown,drive,jump,cue,index*4+j,round(m.reach*4096));impact+=1
            rebuilt[style]=dict(clips=clips,programs=[vars(m) for m in motion.MOVES[style]],model=art_report)
    for style,info in meta['creature_forge']['creatures'].items():
        if style in rebuilt:continue
        if contact_pilot and style!='skitter':continue
        if motion_pilot:continue
        for clip in info['clips']:
            if not clip['contacts']:continue
            n=clip['resource'][:-4]+'.gmb'
            if n not in names:continue
            idx=names.index(n);wrap=Gmb.parse(CompressedBlob.parse(blobs[idx]).decoded)
            if not any(c.kind==3 and c.words(0)[7]==8192 for c in wrap.channels):continue
            value=align_contacts(blobs[idx],clip['contacts']);blobs[idx]=value+bytes((len(blobs[idx])-len(value))%4);changed.append(n)
    room_report=None
    if rooms_pilot or rooms:
        from tools import midnight_rebuild_rooms as room_builder
        room_report,room_changes=room_builder.apply(names,blobs,new,native,offset,alloc,pilot=rooms_pilot)
        changed.extend(room_changes)
    sound_report=None
    if voices:
        from tools import midnight_enemy_audio as audio,midnight_enemy_combat as combat
        rt=meta['creature_forge']['runtime'];capture=forge.parent.combat.capture_hero(rt['capture'],rt['hero']);play=rt['capture']+len(capture)
        configs=alloc(b''.join(struct.pack('<I',cfg if not motion_pilot or style=='skitter' else 0) for style,stem,group,cfg in forge.parent.PRIVATE_STYLES))
        if w.u32(arm,combat.SPATIAL_SITE-0x02000000)!=crane.branch(combat.SPATIAL_SITE,0x0205e6a8,link=True):raise ValueError('Actor spatial request callsite changed')
        at=alloc(b'');data.extend(combat.spatial(at,configs,play,audio.FIRST))
        struct.pack_into('<I',new,combat.SPATIAL_SITE-0x02000000,crane.branch(combat.SPATIAL_SITE,at,link=True))
        old=crane.target(combat.SOUND_SITE,w.u32(arm,combat.SOUND_SITE-0x02000000));bank=alloc(b'');data.extend(combat.voice_bank(bank,old,audio.FIRST))
        struct.pack_into('<I',new,combat.SOUND_SITE-0x02000000,crane.branch(combat.SOUND_SITE,bank))
        sound_report=dict(first=audio.FIRST,count=57,spatial_adapter=at,bank_adapter=bank,configs=configs,play=play,manifest=str(audio.DIR.relative_to(ROOT)/'manifest.json'))
    ground_gate=None
    if motion_pilot or full_motion:
        from tools import midnight_enemy_combat as combat,chapter_spectacle_combat as prior_combat
        rt=meta['creature_forge']['runtime'];prior_rt=meta['chapter_spectacle']['runtime']
        capture=forge.parent.combat.capture_hero(rt['capture'],rt['hero']);play=rt['capture']+len(capture)
        tagged=forge.combat.think(prior_rt['think'],rt['records'],rt['slots'],rt['attack_counters'],rt['hero'],rt['hero']-4,rt['move_counters'],play,653,
            rewrite=lambda source:prior_combat.enhance(source,prior_rt['navigation'])+'\n .word select_ready\n .word walking\n')
        frozen=tagged[:-8];selected,walking=struct.unpack_from('<2I',tagged,len(tagged)-8)
        if arm[offset(prior_rt['think']):offset(prior_rt['think'])+len(frozen)]!=frozen:raise ValueError('Frozen primary thinker differs')
        if w.u32(arm,offset(selected))!=0xe1500001:raise ValueError('Expected native move-index compare')
        gate=alloc(b'');data.extend(combat.attack_gate(gate,selected,walking))
        struct.pack_into('<I',new,offset(selected),crane.branch(selected,gate))
        ground_gate=dict(adapter=gate,site=selected,walking=walking,grounded_bit=128)
    shipping=full_motion and voices and rooms and not (motion_pilot or contact_pilot or observe_audio or observe_requests or rooms_pilot)
    if shipping:
        from tools.qol_suits_menu import StringSlots,decode_grown
        for name in forge.chapter.STRING_FILES:
            i=names.index(name);payload=StringSlots(native(name)).grown(blobs[i],{50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}'})
            blobs[i]=payload+bytes((len(blobs[i])-len(payload))%4);changed.append(name)
            if decode_grown(blobs[i],74)!=f'Options v{VERSION}':raise ValueError('Version label mismatch')
    observer=None
    if observe_audio or observe_requests:
        table=alloc(bytes(4+256*32));at=alloc(b'')
        from tools import crane_audio
        site=0x0203f348 if observe_requests else crane_audio.SITE
        if observe_requests:
            if w.u32(arm,site-0x02000000)!=0xe92d4070:raise ValueError('Native spatial sound request prologue')
            old=site+4
        else:old=crane.target(site,w.u32(arm,site-0x02000000))
        code=audio_observer(at,table,old,observe_requests)
        data.extend(code);observer=dict(table=table,adapter=at,entries=256,bytes_per_entry=32)
        struct.pack_into('<I',new,site-0x02000000,crane.branch(site,at))
    if data:
        space=(len(data)+0xfff)//0x1000*0x1000
        if w.u32(arm,kit.TABLE_POINTERS)!=0x02000000+end or struct.unpack_from('<3I',arm,end+24)!=(kit.TARGET,end-kit.SOURCE,0):raise ValueError('Parent autoload rows changed')
        new=new[:end]+bytes(space)+new[end:end+24]+struct.pack('<3I',kit.TARGET,end-kit.SOURCE+space,0)
        struct.pack_into('<2I',new,kit.TABLE_POINTERS,0x02000000+end+space,0x02000000+end+space+36)
        struct.pack_into('<I',new,kit.ARENA_LOWER,start+space)
        new[offset(start):offset(start)+len(data)]=data
    replacements={'Glob.bin':w.pack_glob(names,blobs)}
    if voices:
        sf=next(e for e in w.nitrofs_entries(rom) if e['name']=='sound_data.sdat');replacements['sound_data.sdat']=audio.sound_data(rom[sf['start']:sf['end']])
    result=w.rebuild_rom(rom,replacements)
    if data:result,_=kit.replace_arm9(result,bytes(new))
    w.validate_rom(result,target=True)
    report=dict(version=VERSION,parent_sha256=PARENT,contact_pilot=contact_pilot,audio_observer=observer,modified_resources=changed,creatures=rebuilt,sound=sound_report,rooms=room_report,shipping=shipping,ground_gate=ground_gate,
        player_kit_preserved=new[kit.SOURCE:kit.SOURCE+kit.RESERVE]==arm[kit.SOURCE:kit.SOURCE+kit.RESERVE],rom_sha256=w.sha256(result))
    report.update(arm9_sha256=w.sha256(new),runtime=dict(start=start,used=len(data),reservation=space if data else 0))
    if shipping:
        from tools import release_info
        pin=release_info.PROFILE_INFO.get('tasm-v'+VERSION,{})
        for key,value in (('rom_sha256',w.sha256(result)),('arm9_sha256',w.sha256(new))):
            if pin.get(key) and pin[key]!=value:raise ValueError('New composition differs from immutable release pin')
    return result,report


def generate(output=OUT,source=None,**options):
    source=Path(source) if source else ROOT/'build/version-0.23.0-final/Versioned.nds';output=Path(output)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Private candidate must stay in build/')
    result,report=apply_rom(source.read_bytes(),**options)
    meta=json.loads(source.with_suffix('.build.json').read_text(encoding='utf-8'));meta['midnight_rebuild']=report
    meta['output_rom_sha256']=w.sha256(result);path=output/'Versioned.nds'
    meta['output']=str(path.resolve())
    if report['shipping']:meta.update(release_version=VERSION,release_date=DATE)
    validation=w.validate_rom(result,target=True);meta.update(rom_size=len(result),used_rom_size=validation['header']['used_rom_size'],nitrofs=validation['nitrofs'],header_crc16=validation['header']['header_crc16'])
    w.atomic_write(path,result,sources=(source,mod.DEFAULT_ROM));w.write_json(path.with_suffix('.build.json'),meta)
    recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text(encoding='utf-8'))
    if report['shipping']:recipe.update(profile='tasm-v'+VERSION,release_version=VERSION)
    w.write_json(output/'gameplay_profile.json',recipe)
    print(json.dumps(dict(candidate=str(path),rom_sha256=report['rom_sha256'],creatures=list(report['creatures']),rooms=list(report['rooms'] or {}),sound=report['sound'])));return path


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--release-dir',type=Path,default=OUT);p.add_argument('--source',type=Path)
    p.add_argument('--contact-pilot',action='store_true');p.add_argument('--observe-audio',action='store_true')
    p.add_argument('--motion-pilot',action='store_true');p.add_argument('--full-motion',action='store_true');p.add_argument('--observe-requests',action='store_true');p.add_argument('--voices',action='store_true')
    p.add_argument('--rooms-pilot',action='store_true');p.add_argument('--rooms',action='store_true');a=p.parse_args()
    generate(a.release_dir,a.source,contact_pilot=a.contact_pilot,observe_audio=a.observe_audio,observe_requests=a.observe_requests,motion_pilot=a.motion_pilot,full_motion=a.full_motion,voices=a.voices,rooms_pilot=a.rooms_pilot,rooms=a.rooms)
