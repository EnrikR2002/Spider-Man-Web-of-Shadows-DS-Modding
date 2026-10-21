"""0.22.0 enemy replacement over the immutable accepted0.21 map composition."""
import argparse,json,struct,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import mod
from tools import wos_tool as w,tasm_kit as kit,chapter_renewal as parent,midnight_chapter as chapter
from tools import creature_forge_design as design,creature_forge_motion as motion,creature_forge_art as art,creature_forge_combat as combat,creature_forge_audio as audio
from tools import crane_creatures as cc,crane_row as crane,crane_audio,oscorp_resources
from tools.actor_resources import ModelSheet
from tools.sca import Sca
from tools.animation_rig import AnimationRig
from tools.qol_suits_menu import StringSlots
VERSION='0.22.0'
PARENT='60a974f33a3ca2f57dbe2cf11a7a12b585c172be8565cc0968301544b3a11340'
BASE=0x02000000;START=parent.START+parent.SPACE;SPACE=0x3000
OUT=ROOT/'build/version-0.22.0-final'
offset=parent.offset

def authored(blob,names,style,stem,prefix):
    deps=('creature_forge_motion.py','creature_forge_design.py','crane_creature_art.py','kit_choreography.py','rush_choreography.py','chapter_renewal_motion.py','sca.py','gmb.py','grip_compression.py')
    key=w.sha256(b''.join((ROOT/'tools'/n).read_bytes() for n in deps)+style.encode()+blob(stem+'.xbd'))
    cache=ROOT/'work/creature-forge/motion-cache'/f'{key}.zip'
    if cache.exists():
        with zipfile.ZipFile(cache) as z:
            meta=json.loads(z.read('manifest.json'));extras={n:z.read(n) for n in z.namelist() if n!='manifest.json'}
        if meta['hashes']!={n:w.sha256(v) for n,v in extras.items()}:raise ValueError('Forge motion cache integrity')
        return extras,{n:{int(k):v for k,v in rows.items()} for n,rows in meta['links'].items()},meta['clips']
    extras,links,clips=motion.prepare(blob,names,style,stem,prefix);cache.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(cache,'w',zipfile.ZIP_DEFLATED) as z:
        for n,v in extras.items():z.writestr(n,v)
        z.writestr('manifest.json',json.dumps(dict(links=links,clips=clips,hashes={n:w.sha256(v) for n,v in extras.items()})))
    return extras,links,clips

def apply_rom(rom):
    if w.sha256(rom)!=PARENT:raise ValueError('Forge requires immutable0.21.0 parent')
    ge=next(e for e in w.nitrofs_entries(rom) if e['name']=='Glob.bin');glob=rom[ge['start']:ge['end']]
    o,names,_=w.parse_glob(glob);blobs=[glob[a:b] for a,b in zip(o,o[1:])];before=tuple(blobs)
    clean,cg,_=mod.load_clean();co,cn,_=w.parse_glob(cg)
    def native(n):i=cn.index(n);return cg[co[i]:co[i+1]]
    h=w.parse_header(rom);arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']];new=bytearray(arm)
    extras={'zz_F22_Atlas.nsbtx':art.texture()};links={};reports={};modified={names.index('GlobFiles.txt')}
    sheetindex=names.index('model_sheet.xbd');sheet=ModelSheet.parse(before[sheetindex]);groups={}
    for i,(style,stem,group,cfg) in enumerate(parent.PRIVATE_STYLES):
        print('SCULPT '+style,flush=True);prefix='zz_F22_'+style
        rig=AnimationRig.parse(native(stem+'.nsbmd'));idle=Sca.parse(native(stem+'_Idle.sca'))
        model,meta=art.model(style,stem,native(stem+'.nsbmd'),motion.pose(idle,rig.parents,style,stem))
        extras[prefix+'.nsbmd']=model
        print('CHOREOGRAPH '+style,flush=True)
        more,ll,clips=authored(native,cn,style,stem,prefix);extras.update(more);links.update(ll)
        groups[group]=(prefix+'.nsbmd',prefix+'.xbd','zz_F22_Atlas.nsbtx')
        reports[style]=dict(stem=stem,group=group,config=cfg,hp=design.HP[i],model=prefix+'.nsbmd',clips=clips,**meta)
        struct.pack_into('<I',new,offset(cfg)+12,design.HP[i]*4096)
    for name in chapter.STRING_FILES:
        idx=names.index(name);blobs[idx]=StringSlots(native(name)).grown(blobs[idx],{50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}'});modified.add(idx)
    aligned={};size=sum(map(len,blobs))
    for n,raw in extras.items():
        if n.endswith(('.nsbmd','.nsbtx')) and size%4:
            pad=bytes(-size%4);aligned[f'zz_f22_align{len(aligned)}.bin']=pad;size+=len(pad)
        aligned[n]=raw;size+=len(raw)
    outnames,outblobs=oscorp_resources.append_resources(names,blobs,aligned);outblobs=cc.bind_xbds(outnames,outblobs,links)
    edited=bytearray(outblobs[sheetindex])
    for group,rows in groups.items():struct.pack_into('<3H',edited,sheet.start+group*6,*(outnames.index(n) for n in rows))
    ModelSheet.parse(edited);outblobs[sheetindex]=bytes(edited);modified.add(sheetindex)
    data=bytearray()
    def alloc(raw=b'',size=None):
        data.extend(bytes(-len(data)%4));at=START+len(data);data.extend(raw if size is None else bytes(size));return at
    move_tables={};impact_index=0
    for i,style in enumerate(design.STYLES):
        rows=[]
        for j,move in enumerate(design.MOVES[style]):
            # Motion+178 is the whole GAB sample cursor, not Q12 time.
            drive=alloc(b''.join(struct.pack('<3i',a,b,round(v*4096)) for a,b,v in move.drives)+struct.pack('<3i',0x7fffffff,0,0))
            jump=alloc(b''.join(struct.pack('<2i',a,round(v*4096)) for a,v in move.jumps)+struct.pack('<2i',0x7fffffff,0))
            cue=alloc(b''.join(struct.pack('<2i',a,audio.FIRST+35+impact_index) for a,b in move.contacts)+struct.pack('<2i',0x7fffffff,0))
            rows.append(struct.pack('<8I',move.action,move.samples-1,move.cooldown,drive,jump,cue,i*4+j,round(move.reach*4096)))
            impact_index+=1
        move_tables[style]=alloc(b''.join(rows))
    records=alloc(b''.join(struct.pack('<4I',cfg,move_tables[s],len(design.MOVES[s]),i) for i,(s,_,_,cfg) in enumerate(parent.PRIVATE_STYLES))+bytes(16))
    slots=alloc(size=32*32);counts=alloc(size=28);voices=alloc(size=28);moves=alloc(size=28*4);cues=alloc(size=4);room=alloc(struct.pack('<I',0xffffffff))
    hero=alloc(size=4);capture=alloc();data.extend(parent.combat.capture_hero(capture,hero))
    play=alloc();data.extend(combat.play(play));think=alloc();data.extend(combat.think(think,records,slots,counts,hero,room,moves,play,audio.FIRST))
    secondary=alloc();data.extend(combat.secondary(secondary,slots))
    enter=alloc();data.extend(combat.enter(enter,records,slots,voices,audio.FIRST,play));update=alloc();data.extend(combat.update(update,slots,play,cues,moves))
    sound=alloc();data.extend(combat.sound_filter(sound,crane.target(crane_audio.SITE,w.u32(arm,crane_audio.SITE-BASE)),652))
    used=len(data)
    if used>SPACE:raise ValueError('Forge runtime reservation exceeded')
    data.extend(bytes(SPACE-used));end=len(arm)-36
    if w.u32(arm,kit.TABLE_POINTERS)!=BASE+end or struct.unpack_from('<3I',arm,end+24)!=(kit.TARGET,end-kit.SOURCE,0):raise ValueError('Parent autoload contract changed')
    new=new[:end]+data+new[end:end+24]+struct.pack('<3I',kit.TARGET,end-kit.SOURCE+SPACE,0)
    struct.pack_into('<2I',new,kit.TABLE_POINTERS,BASE+end+SPACE,BASE+end+SPACE+36);struct.pack_into('<I',new,kit.ARENA_LOWER,START+SPACE)
    for at,value in ((0x020776bc,crane.branch(0x020776bc,capture)),(combat.THINK_SLOT,think),(combat.SECOND_SLOT,secondary),(combat.ENTER_SLOT,enter),(combat.UPDATE_SLOT,update),
                      (crane_audio.SITE,crane.branch(crane_audio.SITE,sound)),(BASE+chapter.GLOB_COUNT,len(outnames))):struct.pack_into('<I',new,at-BASE,value)
    sf=next(e for e in w.nitrofs_entries(rom) if e['name']=='sound_data.sdat');print('PACK',flush=True)
    result=w.rebuild_rom(rom,{'Glob.bin':w.pack_glob(outnames,outblobs),'sound_data.sdat':audio.sound_data(rom[sf['start']:sf['end']])})
    result,_=kit.replace_arm9(result,bytes(new));w.validate_rom(result,target=True)
    if new[kit.SOURCE:kit.SOURCE+kit.RESERVE]!=arm[kit.SOURCE:kit.SOURCE+kit.RESERVE]:raise ValueError('Player kit changed')
    for i,raw in enumerate(outblobs[:len(before)]):
        if i not in modified and raw!=before[i]:raise ValueError('Unrelated asset changed: '+names[i])
    from tools import release_info
    pin=release_info.PROFILE_INFO['tasm-v'+VERSION]
    for key,raw in (('rom_sha256',result),('arm9_sha256',new)):
        if pin.get(key) and pin[key]!=w.sha256(raw):raise ValueError('Forge differs from immutable release pin')
    report=dict(version=VERSION,parent_sha256=PARENT,rom_sha256=w.sha256(result),arm9_sha256=w.sha256(new),creatures=reports,
        runtime=dict(start=START,reservation=SPACE,used=used,slots=slots,slot_bytes=32,records=records,hero=hero,capture=capture,think=think,secondary=secondary,enter=enter,update=update,
                     attack_counters=counts,voice_counters=voices,move_counters=moves,contact_cues=cues,move_counter_encoding='low16 selections / high16 contacts'),
        sound=dict(first=audio.FIRST,count=57,manifest='reference/audio/creature-forge-v1/manifest.json',format='22050Hz DS IMA-ADPCM'),
        programs={s:[vars(m) for m in design.MOVES[s]] for s in design.STYLES},maps_byte_identical=True,player_kit_preserved=True,
        modified_resources=[names[i] for i in sorted(modified)],appended_resources={n:dict(size=len(raw),sha256=w.sha256(raw)) for n,raw in aligned.items()})
    return result,report

def generate(output=OUT,source=None):
    output=Path(output);source=Path(source) if source else None
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Candidate must be private under build/')
    if source:
        result,report=apply_rom(source.read_bytes());metadata=json.loads(source.with_suffix('.build.json').read_text());metadata['creature_forge']=report
        recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text());recipe.update(profile='tasm-v'+VERSION,release_version=VERSION)
    else:
        clean,g,manifest=mod.load_clean();overlays=mod.overlay_files(ROOT/'mods',[e['name'] for e in manifest['entries']],added_names=(*oscorp_resources.EXTRA_NAMES,*kit.EXTRA_NAMES))
        result,_,metadata=mod.create_build(clean,g,manifest,overlays,gameplay_profile='tasm-v'+VERSION);report=metadata['creature_forge']
        recipe=dict(schema_version=1,profile='tasm-v'+VERSION,release_version=VERSION,required_overlays={n:w.sha256(raw) for n,raw in sorted(overlays.items())})
        for n,raw in overlays.items():w.atomic_write(output/'mods'/n,raw,sources=(mod.DEFAULT_ROM,))
    path=output/'Versioned.nds';w.atomic_write(path,result,sources=(mod.DEFAULT_ROM,*((source,) if source else ())))
    metadata.update(release_version=VERSION,release_date='2026-10-17',output_rom_sha256=w.sha256(result));v=w.validate_rom(result,target=True)
    metadata.update(rom_size=len(result),used_rom_size=v['header']['used_rom_size'],nitrofs=v['nitrofs'],header_crc16=v['header']['header_crc16'])
    w.write_json(output/'gameplay_profile.json',recipe);w.write_json(path.with_suffix('.build.json'),metadata)
    print(json.dumps(dict(candidate=str(path),sha=w.sha256(result),runtime=report['runtime'])))
    return path

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path);p.add_argument('--release-dir',type=Path,default=OUT);args=p.parse_args();generate(args.release_dir,args.source)
