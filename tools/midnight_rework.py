"""Compose the storm-terminal Midnight overhaul over the exact accepted0.19.0.

Sources stay private. Original/native and Crane resources remain byte exact;
chapter replacements and original appended assets have an explicit audit.
"""
import argparse,json,struct,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import mod
from tools import midnight_chapter as ch, midnight_rooms as mr, midnight_rework_rooms as rooms
from tools import midnight_rework_creatures as creatures, midnight_rework_boss as boss
from tools import room_catalog,room_compiler as rc,room_minimap,oscorp_resources,tasm_kit as kit,wos_tool as w
from tools import crane_row as crane, crane_creatures as cc, crane_navigation as nav, crane_audio
from tools.crane_boss import Arm
from tools.actor_resources import ModelSheet
from tools.qol_suits_menu import StringSlots,slot_count

VERSION='0.20.0'
BASE=0x02000000
PARENT='9b2b948f6030a60246a0ca9ae477ae51c22f4aa349645fb2c6cef367c4557582'
START=crane.CR_BASE+crane.CR_SPACE
# ARM9 autoload source/table must end below the pinned kit destination.
# Beyond0xA5C extra bytes the source table is overwritten during relocation.
SPACE=0xA00
OUT=ROOT/'build/version-0.20.0-final'
OBJECTIVES=('Stop the Conductor',
    'Terminal / Viaduct: keep right.\nFloodworks > Turbine Rise.\nBridge > Capacitors > Observatory.\nConductor: beyond Sanctuary.\nX at marked hatches.\nSave: Pump Refuge / Sanctuary.',
    'Midnight Line restored',
    'Conductor defeated.\nCrown Approach returns to Tower.\nTower left: Signal House save,\nTrain Sheds and Substation.\nStorm Gate left: back to Sewer.\nSave before closing.')

def overview(template):
    # Preserve colour-changing native slots. Small schematic pieces carry
    # topology; detail maps depict the actual compiled walkable geometry.
    names=[r.name for r in ch.ROOMS]
    xy=((6,4),(154,28),(42,4),(154,4),(92,4),(94,54),(124,54),(154,54),
        (154,80),(124,80),(94,80),(64,80),(94,106),(64,106),(114,28),
        (74,28),(34,28),(6,54),(6,80),(46,54))
    rects={n:[(x,y,x+22,y+12)] for n,(x,y) in zip(names,xy)}
    def pixels():
        result={}
        for name,((x0,y0,x1,y1),) in rects.items():
            for y in range(y0,y1):
                for x in range(x0,x1):result[x,y]=(name,ch.EDGE if x in (x0,x1-1) or y in (y0,y1-1) else ch.FILL)
        for n in names:
            x,y,x1,y1=rects[n][0]
            if n in ch.SAVE_ROOMS:
                for a in range(4):result[x+9+a,y+4]=(n,ch.EDGE);result[x+10,y+3+a]=(n,ch.EDGE)
        return result
    with patch.object(ch,'MAP_ROOMS',rects),patch.object(ch,'_map_pixels',pixels):
        raw,listing=ch.map_layout(template)
    # Draw static connecting wires after allocating room slots. Allocating a
    # room again in every crossed cell exhausts the finite palette-pair budget.
    # A mixed room cell uses its existing edge pen; empty cells use reserved
    # source0xB6 verbatim. Source colours and room slots stay byte exact.
    from tools.minimap_cbmp import Cbmp
    screen=Cbmp.parse(raw);wires=set();seen=set();body=pixels()
    for (name,group),(dest,_) in ch.LINKS.items():
        pair=frozenset((name,dest))
        if dest not in rects or pair in seen:continue
        seen.add(pair)
        x,y,x1,y1=rects[name][0];xx,yy,xx1,yy1=rects[dest][0]
        a=((x+x1)//2,(y+y1)//2);z=((xx+xx1)//2,(yy+yy1)//2);mid=(a[0],z[1])
        for start,end in ((a,mid),(mid,z)):
            steps=max(abs(start[0]-end[0]),abs(start[1]-end[1]),1)
            for i in range(steps+1):
                point=(round(start[0]+(end[0]-start[0])*i/steps),round(start[1]+(end[1]-start[1])*i/steps))
                if point not in body:wires.add(point)
    cells={}
    for x,y in sorted(wires):cells.setdefault((3+x//8,3+y//8),[]).append((x%8,y%8))
    tiles=[];changed={}
    for (cx,cy),points in cells.items():
        entry=screen.screen[cy*screen.width+cx];palette=entry>>12;tile=list(screen.tile(entry&0x3FF))
        pens=[slot%16+ch.EDGE for n,slot,x,y in listing if slot//16==palette and slot%16+ch.EDGE in tile]
        if pens:pen=pens[0]
        else:palette=11;pen=6;tile=[0]*64
        for x,y in points:tile[y*8+x]=pen
        changed[cx,cy]=(palette<<12)|(screen.count+len(tiles));tiles.append(tile)
    screen,_=screen.with_tiles(tiles)
    return screen.with_screen(changed).to_bytes(),listing

def objective_adapter(at,records,old):
    a=Arm(at);a.emit(0xE92D500B,0xE10FC000)
    creatures.scope(a,'fallback')
    a.lit(2,'stats',0x02145C5C);a.emit(0xE5922000,0xE5D2302E,0xE3130008);a.b('done',1) # flag147
    a.lit(2,'active',records);a.b('store');a.label('done');a.lit(2,'complete',records+8)
    a.label('store');a.emit(0xE5802000,0xE128F00C,0xE8BD500B,0xE12FFF1E)
    a.label('fallback');a.emit(0xE128F00C,0xE8BD500B);a.b(old)
    return a.finish()

def warning_adapter(arm,at,model,old):
    from tools import midnight_boss as mb
    raw=bytearray(arm[mb.DATA_BASE-BASE+mb.WARNING_KIND*64:mb.DATA_BASE-BASE+(mb.WARNING_KIND+1)*64])
    struct.pack_into('<3I',raw,0,0,0xB6,model)
    a=Arm(at);a.emit(0xE92D500F,0xE10FC000)
    a.lit(2,'stats',0x02145C5C);a.emit(0xE5922000,0xE3520000);a.b('fallback',0)
    a.emit(0xE5922000,0xE3520059);a.b('fallback',1);a.emit(0xE3510012);a.b('fallback',1)
    a.lit(2,'data');a.emit(0xE5802000,0xE128F00C,0xE8BD900F)
    a.label('fallback');a.emit(0xE128F00C,0xE8BD500F);a.b(old);a.blob('data',raw)
    return a.finish()

def wave_adapter(at,old):
    a=Arm(at);a.lit(2,'stats',0x02145C5C);a.emit(0xE5922000,0xE3520000);a.b(old,0)
    a.emit(0xE5923000,0xE353004C);a.b(old,3);a.emit(0xE3530060);a.b(old,2)
    a.emit(0xE5913000);a.lit(2,'enemy',0x021301D0);a.emit(0xE1530002);a.b(old,1)
    a.emit(0xE5913044,0xE3530000);a.b(0x0204C2CC,13);a.b(0x0204C340)
    return a.finish()

def apply_rom(rom):
    if w.sha256(rom)!=PARENT:raise ValueError('Midnight overhaul needs exact accepted0.19.0 composition')
    fs=next(e for e in w.validate_rom(rom,target=True)['nitrofs'] if e['name']=='Glob.bin')
    old_glob=rom[fs['start']:fs['end']];offsets,names,table_index=w.parse_glob(old_glob)
    blobs=[old_glob[a:z] for a,z in zip(offsets,offsets[1:])];originals=tuple(blobs)
    clean,clean_glob,manifest=mod.load_clean();entries={e['name']:e for e in manifest['entries']}
    def asset(name):
        e=entries[name];return clean_glob[e['offset']:e['offset']+e['size']]
    h=w.parse_header(rom);arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    hc=w.parse_header(clean);clean_arm=clean[hc['arm9_offset']:hc['arm9_offset']+hc['arm9_size']]
    natives=room_catalog.parse(clean_arm,names);source=next(r for r in natives if r.name==mr.SOURCE)
    spawn,exit=ch.door_templates(asset)
    from tools import nitro_build
    extras={'zz_MLR_MidnightTextures.nsbtx':nitro_build.texture_archive(
        tuple(t for t,p in rooms.materials()),tuple(p for t,p in rooms.materials()))}
    if len(extras['zz_MLR_MidnightTextures.nsbtx'])>=128*1024:raise ValueError('Midnight room textures exceed native128KiB allocation')
    modified=set();compiled={};objects={};plans={}
    for name in rooms.NAMES:
        index=ch.BY_NAME[name].index;spec=rooms.SPECS[name];plan=spec.plan(asset);built=rc.compile_room(plan)
        raw,_=ch.build_room(asset(mr.SOURCE+'_app.obj'),asset(mr.SOURCE+'_app.obj'),ch.Room(index,'MR_Empty',mr.SOURCE,'authored',True),
            source.index,[r.name for r in natives],{},visited_flag=ch.visited(index))
        raw=mr.stage(raw,name,asset,room_of=lambda n:ch.BY_NAME[n].index if n in ch.BY_NAME else next(r.index for r in natives if r.name==n),
            visited=ch.visited(index),spawn_template=spawn,exit_template=exit,links=ch.LINKS,flags=ch.ROOM_FLAGS,authored=spec,compiled_room=built)
        from tools.room_objects import RoomObjects
        from tools.room_entities import Entities
        parsed=RoomObjects.parse(raw);entities=Entities.parse(parsed.records[0].sections[0])
        for n,entity in enumerate(entities.records):
            if len(entity)==28 and w.u32(entity,12)==7 and entity[27]>1 and rooms.manual(name,entity[27]-1):
                changed=bytearray(entity);changed[26]=0
                section=entities.replace_record(n,bytes(changed))
                raw=parsed.replace_section(0,0,section);parsed=RoomObjects.parse(raw);entities=Entities.parse(section)
        if name=='ML_Venom':raw=boss.stage(raw,asset)
        key=f'zz_{name}_app.obj';blobs[names.index(key)]=raw;modified.add(names.index(key))
        # One original material/panorama archive is shared by all new rooms.
        # Keep the superseded private grades inert rather than multiplying a
        # large texture bank fifteen times on a64MiB cartridge.
        extras[f'zz_MLR_{name}.nsbmd']=built.model;extras[f'zz_MLR_{name}.bsp']=built.collision
        labels=[rooms.TITLES[rooms.NAMES.index(ch.LINKS[name,g][0])][:10].upper() if ch.LINKS[name,g][0] in rooms.NAMES
                else 'SUBSTATION' if ch.LINKS[name,g][0]=='ML_Switchyard' else 'SEWER' for g in range(1,len(spec.doors)+1)]
        extras[f'zz_MLR_{name}.cbmp'],_=room_minimap.build(asset(ch.MAP_SOURCE),plan,spec.doors,save=spec.save,door_labels=labels,glyphs=rooms.ca.FONT)
        compiled[name]=built;objects[name]=raw;plans[name]=plan
    overview_blob,listing=overview(asset(ch.MAP_SOURCE))
    blobs[names.index(ch.MAP_SCREEN)]=overview_blob;modified.add(names.index(ch.MAP_SCREEN))
    more,links,creature_report=creatures.prepare(asset,names)
    # Full-lifecycle authored clips already present in the accepted Crane
    # composition are immutable shared choreography on the same rig. XBDs
    # stay private; original creature meshes/voices remain distinct.
    by_hash={w.sha256(raw):name for name,raw in zip(names,originals)};aliases={}
    for name,raw in more.items():
        if name.endswith('.xbd'):extras[name]=raw;continue
        digest=w.sha256(raw)
        if digest in by_hash:aliases[name]=by_hash[digest]
        else:extras[name]=raw;by_hash[digest]=name
    links={name:{offset:aliases.get(target,target) for offset,target in mappings.items()} for name,mappings in links.items()}
    goal_text=OBJECTIVES
    counts=set()
    for name in ch.STRING_FILES:
        i=names.index(name);counts.add(slot_count(blobs[i]));blobs[i]=StringSlots(asset(name)).grown(blobs[i],
            {50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}'},appended=goal_text)
        modified.add(i)
    if len(counts)!=1:raise ValueError('String count mismatch')
    first=counts.pop()
    aligned={};size=sum(map(len,blobs))
    for name,raw in extras.items():
        if name.endswith(('.nsbmd','.nsbtx')) and size%4:
            pad=bytes(-size%4);aligned[f'zz_mlr_align{len(aligned)}.bin']=pad;size+=len(pad)
        aligned[name]=raw;size+=len(raw)
    out_names,out_blobs=oscorp_resources.append_resources(names,blobs,aligned)
    out_blobs=cc.bind_xbds(out_names,out_blobs,links)
    si=out_names.index('model_sheet.xbd');modified.add(si);sheet=ModelSheet.parse(out_blobs[si]);groups={}
    models=[]
    for key in ('maw','ballast','spore','boss'):
        prefix='zz_MLR_Boss_ballast' if key=='boss' else 'zz_MLR_'+key
        groups[key]=len(sheet.groups)+len(models)
        models.append(tuple(out_names.index(aliases.get(prefix+ext,prefix+ext)) for ext in ('.nsbmd','.xbd','.nsbtx')))
    out_blobs[si]=sheet.append(tuple(models))
    data=bytearray()
    def alloc(payload=b'',size=None):
        data.extend(bytes(-len(data)%4));at=START+len(data);data.extend(payload if size is None else bytes(size));return at
    offset=lambda addr:kit.SOURCE+addr-kit.TARGET if addr>=kit.TARGET else addr-BASE
    new=bytearray(arm)
    lookup=w.u32(arm,ch.LOOKUP_LITERAL-BASE)
    resource_map={}
    for name in rooms.NAMES:
        index=ch.BY_NAME[name].index;desc=w.u32(arm,offset(lookup)+4*index);at=offset(desc)
        original=arm[at:at+80];raw=bytearray(source.raw)
        texture=out_names.index('zz_MLR_MidnightTextures.nsbtx');obj=out_names.index(f'zz_{name}_app.obj')
        model=out_names.index(f'zz_MLR_{name}.nsbmd');bsp=out_names.index(f'zz_MLR_{name}.bsp');detail=out_names.index(f'zz_MLR_{name}.cbmp')
        struct.pack_into('<4I',raw,0,w.u32(original,0),texture,bsp,obj)
        model_pointer=w.u32(original,0x20)
        if not ch.ML_BASE<=model_pointer<ch.ML_BASE+ch.ML_SPACE:raise ValueError('Owned chapter model pointer missing')
        struct.pack_into('<I',raw,0x20,model_pointer)
        struct.pack_into('<I',new,offset(model_pointer),model)
        struct.pack_into('<9i',raw,0x28,*room_minimap.projection(plans[name]).fields)
        struct.pack_into('<I',raw,0x4C,detail);new[at:at+80]=raw
        resource_map[name]=dict(index=index,model=model,texture=texture,objects=obj,bsp=bsp,detail_map=detail,
            title=rooms.TITLES[rooms.NAMES.index(name)],quads=compiled[name].quads,bounds=plans[name].bounds)
    # Area5 table was relocated by Crane; find it through native literal refs.
    areas=None
    for p in range(0,kit.SOURCE,4):
        candidate=w.u32(arm,p)
        if START-crane.CR_SPACE<=candidate<START:
            at=offset(candidate)
            if arm[at:at+4]==struct.pack('<I',out_names.index('MMPier.cbmp')):
                if at+7*16<=len(arm) and w.u32(arm,at+6*16)==out_names.index(crane.MAP_SCREEN):areas=candidate;break
    if areas is None:raise ValueError('Accepted area table missing')
    map_at,map_count=struct.unpack_from('<2I',arm,offset(areas)+5*16+8)
    map_bytes=ch.map_entries(listing)
    if not ch.ML_BASE<=map_at<ch.ML_BASE+ch.ML_SPACE or len(map_bytes)>map_count*20:raise ValueError('Owned Midnight map list capacity')
    new[offset(map_at):offset(map_at)+len(map_bytes)]=map_bytes
    struct.pack_into('<2I',new,offset(areas)+5*16+8,map_at,len(listing))
    goal_at=alloc(struct.pack('<4I',first,first+1,first+2,first+3))
    configs={c.key:alloc(cc.character_config(clean_arm,c,groups[c.key])) for c in creatures.CREATURES}
    configs['boss']=alloc(cc.character_config(clean_arm,creatures.BOSS,groups['boss']))
    goals=cc.goal_configs(clean_arm)
    single=bytearray(goals['opening']);struct.pack_into('<2I',single,0,2*4096,2*4096)
    goals={'patrol':goals['patrol'],'upper':goals['upper'],'boss':bytes(single)}
    goals={key:alloc(raw) for key,raw in goals.items()};reward=alloc(cc.reward_config(clean_arm));state=alloc(bytes(8))
    hooks={}
    def hook(site,make,link=False,condition=14):
        old=crane.target(site,w.u32(arm,site-BASE));at=alloc();data.extend(make(at,old));hooks[site]=crane.branch(site,at,condition,link)
    hook(cc.CONFIG_SITE,lambda at,old:creatures.config_adapter(at,configs,old))
    hook(cc.VARIANT_CALL,lambda at,old:creatures.variant_adapter(at,state,old),link=True)
    hook(cc.GOAL_CALL,lambda at,old:creatures.goal_adapter(at,goals,old),link=True)
    hook(cc.REWARD_SITE,lambda at,old:creatures.reward_adapter(at,reward,old))
    hook(crane_audio.SITE,creatures.sound_adapter)
    hook(crane_audio.STATE_SITE,lambda at,old:creatures.spore_adapter(at,configs['spore'],old))
    hook(nav.OBJECTIVE_SITE,lambda at,old:objective_adapter(at,goal_at,old),link=True)
    hook(0x020D1610,lambda at,old:warning_adapter(clean_arm,at,out_names.index('zz_SignalWarning.nsbmd'),old))
    hook(0x0204C2C8,wave_adapter,condition=1)
    if w.u32(arm,boss.HP_SITE-BASE)!=0xE92D000F:raise ValueError('Native enemy HP setter changed')
    hp_at=alloc();data.extend(boss.hp_adapter(hp_at));hooks[boss.HP_SITE]=crane.branch(boss.HP_SITE,hp_at)
    if len(data)>SPACE:raise ValueError('Midnight overhaul reservation exceeded')
    used=len(data);data.extend(bytes(SPACE-len(data)))
    end=kit.SOURCE+kit.RESERVE+ch.ML_SPACE+crane.CR_SPACE
    if BASE+end+SPACE+36>kit.TARGET:raise ValueError('Autoload source/table overlaps kit destination')
    if len(arm)!=end+36 or struct.unpack_from('<3I',arm,end+24)!=(kit.TARGET,end-kit.SOURCE,0):raise ValueError('Parent autoload contract')
    new=new[:end]+data+new[end:end+24]+struct.pack('<3I',kit.TARGET,end-kit.SOURCE+SPACE,0)
    struct.pack_into('<2I',new,kit.TABLE_POINTERS,BASE+end+SPACE,BASE+end+SPACE+36)
    struct.pack_into('<I',new,kit.ARENA_LOWER,kit.TARGET+end-kit.SOURCE+SPACE)
    struct.pack_into('<I',new,ch.GLOB_COUNT,len(out_names))
    for site,word in hooks.items():struct.pack_into('<I',new,site-BASE,word)
    if new[kit.SOURCE:kit.SOURCE+kit.RESERVE]!=arm[kit.SOURCE:kit.SOURCE+kit.RESERVE]:raise ValueError('Kit bytes changed')
    sound_fs=next(e for e in w.validate_rom(rom,target=True)['nitrofs'] if e['name']=='sound_data.sdat')
    result=w.rebuild_rom(rom,{'Glob.bin':w.pack_glob(out_names,out_blobs),'sound_data.sdat':creatures.sound_data(rom[sound_fs['start']:sound_fs['end']])},legacy_gaps=True)
    result,_=kit.replace_arm9(result,bytes(new));w.validate_rom(result,target=True)
    from tools import release_info
    expected=release_info.PROFILE_INFO['tasm-v'+VERSION]['arm9_sha256']
    if expected and w.sha256(new)!=expected:raise ValueError('Midnight release ARM9 differs from its pin')
    expected_rom=release_info.PROFILE_INFO['tasm-v'+VERSION].get('rom_sha256')
    if expected_rom and w.sha256(result)!=expected_rom:raise ValueError('Midnight release ROM differs from its qualified pin')
    for i,raw in enumerate(out_blobs[:len(originals)]):
        if i not in (*modified,table_index) and raw!=originals[i]:raise ValueError('Unrelated resource changed: '+names[i])
    return result,dict(version=VERSION,parent_sha256=PARENT,rom_sha256=w.sha256(result),arm9_sha256=w.sha256(new),
        rooms=resource_map,table_bytes=used,reservation=SPACE,kit_bytes_preserved=True,native_and_crane_resources_preserved=True,
        modified_resources=[names[i] for i in sorted(modified)],creatures=dict(assets=creature_report,configs=configs,goals=goals,groups=groups,state=state),
        boss=dict(room=89,defeated=boss.DEFEATED,hp=creatures.BOSS.hp,phases='native HP half/quarter',hp_adapter=hp_at),
        hooks={hex(k):hex(v) for k,v in hooks.items()},map_entries=len(listing),shared_choreography_resources=aliases)

def generate(output=OUT,source=None):
    output=Path(output)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Candidates belong in build/')
    if source is not None:
        result,report=apply_rom(Path(source).read_bytes());path=output/'Versioned.nds'
        w.atomic_write(path,result,sources=(mod.DEFAULT_ROM,Path(source)))
        w.write_json(path.with_suffix('.build.json'),dict(midnight_rework=report))
        print(json.dumps(dict(candidate=str(path),sha256=w.sha256(result),arm9=report['arm9_sha256'])))
        return path
    rom,glob,manifest=mod.load_clean()
    overlays=mod.overlay_files(ROOT/'mods',[e['name'] for e in manifest['entries']],added_names=(*oscorp_resources.EXTRA_NAMES,*kit.EXTRA_NAMES))
    result,_,log=mod.create_build(rom,glob,manifest,overlays,gameplay_profile='tasm-v'+VERSION)
    for name,raw in overlays.items():w.atomic_write(output/'mods'/name,raw,sources=(mod.DEFAULT_ROM,))
    w.write_json(output/'gameplay_profile.json',dict(schema_version=1,profile='tasm-v'+VERSION,release_version=VERSION,
        required_overlays={n:w.sha256(raw) for n,raw in sorted(overlays.items())}))
    path=output/'Versioned.nds';w.atomic_write(path,result,sources=(mod.DEFAULT_ROM,));w.write_json(path.with_suffix('.build.json'),log)
    print(json.dumps(dict(candidate=str(path),sha256=w.sha256(result),arm9=log['midnight_rework']['arm9_sha256'])))
    return path

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--release-dir',type=Path,default=OUT);p.add_argument('--source',type=Path);args=p.parse_args();generate(args.release_dir,args.source)
