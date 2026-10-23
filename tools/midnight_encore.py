"""Immutable0.24 post-pass: dynamic creatures, clean audio and boss pressure."""
import argparse,json,struct,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import mod
from tools import wos_tool as w,tasm_kit as kit,creature_forge as forge,crane_row as crane
from tools import midnight_encore_motion as motion,midnight_encore_combat as combat
VERSION='0.25.0';DATE='2026-10-18'
PARENT='c31bae4c60869133f9cf4dd3e8b0b2895123d1a2e99d91599231cc8d983b1393'
OUT=ROOT/'build/version-0.25.0-final'
offset=forge.offset


def authored(native,names,style,stem):
    deps=('midnight_encore_motion.py','midnight_enemy_motion.py','creature_forge_motion.py','creature_forge_design.py')
    key=w.sha256(b''.join((ROOT/'tools'/n).read_bytes() for n in deps)+style.encode()+native(stem+'.xbd'))
    path=ROOT/'work/midnight-epic/motion-cache'/(key+'.zip')
    if path.exists():
        with zipfile.ZipFile(path) as z:
            meta=json.loads(z.read('manifest.json'));extras={n:z.read(n) for n in z.namelist() if n!='manifest.json'}
        if meta['hashes']!={n:w.sha256(v) for n,v in extras.items()}:raise ValueError('Encore cache integrity')
        return extras,meta['clips']
    extras,clips=motion.prepare(native,names,style,stem,'zz_F22_'+style)
    path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,v in extras.items():z.writestr(n,v)
        z.writestr('manifest.json',json.dumps(dict(clips=clips,hashes={n:w.sha256(v) for n,v in extras.items()})))
    return extras,clips


def apply_rom(rom,*,pilot=False,voices=True):
    if w.sha256(rom)!=PARENT:raise ValueError('Encore requires exact published0.24.0')
    meta=json.loads((ROOT/'build/version-0.24.0-final/Versioned.build.json').read_text())
    fs=next(e for e in w.nitrofs_entries(rom) if e['name']=='Glob.bin');g=rom[fs['start']:fs['end']]
    o,names,_=w.parse_glob(g);blobs=[g[a:b] for a,b in zip(o,o[1:])];before=tuple(blobs)
    _,ng,_=mod.load_clean();no,nn,_=w.parse_glob(ng)
    def native(n):i=nn.index(n);return ng[no[i]:no[i+1]]
    h=w.parse_header(rom);arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']];new=bytearray(arm)
    end=len(arm)-36;start=kit.TARGET+end-kit.SOURCE;data=bytearray();changed=[];creatures={};rt=meta['creature_forge']['runtime']
    def alloc(raw=b''):
        data.extend(bytes(-len(data)%4));at=start+len(data);data.extend(raw);return at
    impact=0
    for index,(style,stem,group,cfg) in enumerate(forge.parent.PRIVATE_STYLES):
        if pilot and style not in ('skitter','conductor'):impact+=len(motion.MOVES[style]);continue
        print('ANIMATE '+style,flush=True);extras,clips=authored(native,nn,style,stem)
        for name,payload in extras.items():
            if name not in names:raise ValueError('Unbound private payload '+name)
            i=names.index(name);blobs[i]=payload+bytes((len(blobs[i])-len(payload))%4);changed.append(name)
        table=w.u32(arm,offset(rt['records'])+index*16+4)
        for j,m in enumerate(motion.MOVES[style]):
            drive=alloc(b''.join(struct.pack('<3i',a,b,round(v*4096)) for a,b,v in m.drives)+struct.pack('<3i',0x7fffffff,0,0))
            jump=alloc(b''.join(struct.pack('<2i',a,round(v*4096)) for a,v in m.jumps)+struct.pack('<2i',0x7fffffff,0))
            cue=alloc(b''.join(struct.pack('<2i',a,653+35+impact) for a,b in m.contacts)+struct.pack('<2i',0x7fffffff,0))
            struct.pack_into('<8I',new,offset(table)+j*32,m.action,m.samples-1,m.cooldown,drive,jump,cue,index*4+j,round(m.reach*4096));impact+=1
        creatures[style]=dict(clips=clips,programs=[vars(m) for m in motion.MOVES[style]])
    from tools import midnight_encore_art as art,creature_forge_art,creature_texture_fix
    from tools.animation_rig import AnimationRig
    from tools.sca import Sca
    neutral=motion.pose(Sca.parse(native('brt_Idle.sca')),AnimationRig.parse(native('brt.nsbmd')).parents,'conductor','brt')
    neutral.rebuild_style='conductor'
    model,art_report=creature_forge_art.model('conductor','brt',native('brt.nsbmd'),neutral,sculpt_type=art.Conductor)
    model,_=creature_texture_fix.fix_model(model);i=names.index('zz_F22_conductor.nsbmd')
    blobs[i]=model+bytes((len(blobs[i])-len(model))%4);changed.append(names[i]);creatures['conductor']['model']=art_report
    cfg=meta['creature_forge']['creatures']['conductor']['config']
    struct.pack_into('<I',new,offset(cfg)+12,132*4096)
    capture=forge.parent.combat.capture_hero(rt['capture'],rt['hero']);play=rt['capture']+len(capture)
    poise=alloc(bytes(8));thinker=alloc();data.extend(forge.combat.think(thinker,rt['records'],rt['slots'],rt['attack_counters'],rt['hero'],rt['hero']-4,rt['move_counters'],play,653,
        rewrite=lambda source:combat.decisions(source,meta['chapter_spectacle']['runtime']['navigation'],poise)))
    struct.pack_into('<I',new,forge.combat.THINK_SLOT-0x02000000,thinker)
    second=alloc();data.extend(combat.secondary(second,w.u32(arm,forge.combat.SECOND_SLOT-0x02000000),rt['slots'],cfg,poise))
    struct.pack_into('<I',new,forge.combat.SECOND_SLOT-0x02000000,second)
    resolver=alloc();data.extend(combat.find_boss(resolver,rt['slots'],cfg));owned=alloc(bytes(4));observed=alloc(bytes(16))
    hud=alloc();data.extend(combat.hud_tick(hud,resolver,owned,observed));meter=alloc();data.extend(combat.meter(meter,resolver,observed))
    for site,at,word in ((combat.HUD_TICK,hud,0xe92d4038),(combat.HUD_METER,meter,0xe92d4018)):
        if w.u32(arm,site-0x02000000)!=word:raise ValueError('Native HUD prologue differs')
        struct.pack_into('<I',new,site-0x02000000,crane.branch(site,at))
    sound=None
    if voices:
        from tools import midnight_encore_audio as audio,midnight_enemy_audio as old_audio,midnight_enemy_combat as old_combat
        prior=meta['midnight_rebuild']['sound']
        old=crane.target(old_combat.SOUND_SITE,w.u32(arm,old_combat.SOUND_SITE-0x02000000))
        old_code=old_combat.voice_bank(old,crane.target(old_combat.SOUND_SITE,w.u32((ROOT/'build/version-0.23.0-final/Versioned.nds').read_bytes(),h['arm9_offset']+old_combat.SOUND_SITE-0x02000000)),old_audio.FIRST)
        # Replace only known literals in the exact owned adapters. No native
        # player vocal/footstep or other actor bank is edited.
        for at,size in ((prior['bank_adapter'],len(old_code)),(prior['spatial_adapter'],len(old_combat.spatial(prior['spatial_adapter'],prior['configs'],play,old_audio.FIRST)))):
            code=bytes(new[offset(at):offset(at)+size]);needle=struct.pack('<I',old_audio.FIRST)
            if code.count(needle)!=1:raise ValueError('Expected one owned bank literal')
            new[offset(at):offset(at)+size]=code.replace(needle,struct.pack('<I',audio.FIRST))
        sound=dict(first=audio.FIRST,count=57,manifest=str(audio.DIR.relative_to(ROOT)/'manifest.json'))
    from tools.qol_suits_menu import StringSlots,decode_grown
    for name in forge.chapter.STRING_FILES:
        i=names.index(name);payload=StringSlots(native(name)).grown(blobs[i],{50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}'})
        blobs[i]=payload+bytes((len(blobs[i])-len(payload))%4);changed.append(name)
        if decode_grown(blobs[i],74)!=f'Options v{VERSION}':raise ValueError('Version label')
    space=(len(data)+0xfff)//0x1000*0x1000
    if w.u32(arm,kit.TABLE_POINTERS)!=0x02000000+end or struct.unpack_from('<3I',arm,end+24)!=(kit.TARGET,end-kit.SOURCE,0):raise ValueError('Parent autoload contract')
    new=new[:end]+bytes(space)+new[end:end+24]+struct.pack('<3I',kit.TARGET,end-kit.SOURCE+space,0)
    struct.pack_into('<2I',new,kit.TABLE_POINTERS,0x02000000+end+space,0x02000000+end+space+36)
    struct.pack_into('<I',new,kit.ARENA_LOWER,start+space);new[offset(start):offset(start)+len(data)]=data
    replacements={'Glob.bin':w.pack_glob(names,blobs)}
    if voices:
        sf=next(e for e in w.nitrofs_entries(rom) if e['name']=='sound_data.sdat');replacements['sound_data.sdat']=audio.sound_data(rom[sf['start']:sf['end']])
    result=w.rebuild_rom(rom,replacements,legacy_gaps=True);result,_=kit.replace_arm9(result,bytes(new));w.validate_rom(result,target=True)
    if new[kit.SOURCE:kit.SOURCE+kit.RESERVE]!=arm[kit.SOURCE:kit.SOURCE+kit.RESERVE]:raise ValueError('Player kit changed')
    if any(blobs[i]!=raw for i,raw in enumerate(before) if names[i] not in changed):raise ValueError('Unrelated asset changed')
    report=dict(version=VERSION,parent_sha256=PARENT,rom_sha256=w.sha256(result),arm9_sha256=w.sha256(new),pilot=pilot,creatures=creatures,sound=sound,
        runtime=dict(start=start,used=len(data),reservation=space,think=thinker,secondary=second,poise=poise,resolver=resolver,hud=hud,meter=meter,owned=owned,observed=observed),
        boss_hp=132,player_kit_preserved=True,room_resources_unchanged=True,modified_resources=changed)
    if not pilot:
        from tools import release_info
        pin=release_info.PROFILE_INFO.get('tasm-v'+VERSION,{})
        for key in ('rom_sha256','arm9_sha256'):
            if pin.get(key) and pin[key]!=report[key]:raise ValueError('Encore differs from its release pin')
    return result,report


def generate(output=OUT,source=None,**options):
    source=Path(source) if source else ROOT/'build/version-0.24.0-final/Versioned.nds';output=Path(output)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Candidate must stay in build/')
    result,report=apply_rom(source.read_bytes(),**options);path=output/'Versioned.nds'
    meta=json.loads(source.with_suffix('.build.json').read_text());meta['midnight_encore']=report
    meta.update(release_version=VERSION,release_date=DATE,output=str(path.resolve()),output_rom_sha256=w.sha256(result))
    v=w.validate_rom(result,target=True);meta.update(rom_size=len(result),used_rom_size=v['header']['used_rom_size'],nitrofs=v['nitrofs'],header_crc16=v['header']['header_crc16'])
    w.atomic_write(path,result,sources=(source,mod.DEFAULT_ROM));w.write_json(path.with_suffix('.build.json'),meta)
    recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text());recipe.update(profile='tasm-v'+VERSION,release_version=VERSION);w.write_json(output/'gameplay_profile.json',recipe)
    print(json.dumps(dict(candidate=str(path),sha256=report['rom_sha256'],runtime=report['runtime'])));return path


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path);p.add_argument('--release-dir',type=Path,default=OUT);p.add_argument('--pilot',action='store_true');p.add_argument('--no-voices',action='store_true');a=p.parse_args()
    generate(a.release_dir,a.source,pilot=a.pilot,voices=not a.no_voices)
