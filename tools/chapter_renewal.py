"""0.21.0: compact, connected chapters with private motion/combat/audio.

Strict post-pass over accepted0.20.0. Original assets, purchases and saved IDs
are preserved; all new content and runtime tables have an explicit manifest.
"""
import argparse,json,struct,sys,zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import mod
from tools import wos_tool as w,tasm_kit as kit,midnight_chapter as ch,midnight_rooms as mr
from tools import midnight_rework as parent,midnight_rework_boss as boss,crane_row as crane,crane_rooms as cr
from tools import chapter_renewal_rooms as rooms,chapter_renewal_motion as motion,chapter_renewal_combat as combat
from tools import room_catalog,room_compiler as rc,room_minimap,room_author,oscorp_resources,crane_creatures as cc,crane_audio
from tools.actor_resources import ModelSheet
from tools.actor_actions import ActorActions
from tools.room_objects import RoomObjects
from tools.room_entities import Entities
from tools.room_events import Events,EventGroup
from tools import room_script
from tools.qol_suits_menu import StringSlots,slot_count

VERSION='0.21.0'
PARENT='4b4e739eb9e85699942afe29cb0f9e809d7f9302dcee9154e338717516139888'
BASE=0x02000000
START=parent.START+parent.SPACE
SPACE=0x1800
OUT=ROOT/'build/version-0.21.0-final'
OBJECTIVES=('Stop the Conductor',
    'Terminal > Floodworks > Turbine.\nObservatory > Sanctuary > Conductor.\nX opens the lit shutters.\nSave: Signal House / Pump Refuge.\nCrown Return loops to Storm Gate.',
    'Midnight Line restored',
    'Conductor defeated.\nCrown Return leads to Storm Gate.\nIts left ground shutter: Sewer.\nX at a sphere to save.')

PRIVATE_STYLES=(('maw','hLpr',182,34970356),('ballast','brt',183,34970440),('spore','hRng',184,34970524),
    ('skitter','hLpr',185,34972720),('warden','brt',186,34972804),('eye','hRng',187,34972888),('conductor','brt',188,34972972))

def authored_motion(native,names,style,stem,prefix):
    dependencies=('chapter_renewal_motion.py','crane_creatures.py','crane_creature_motion.py','sca_author.py',
        'crane_creature_art.py','rush_choreography.py','kit_choreography.py','animation_rig.py','sca.py',
        'gmb.py','custom_formats.py','grip_compression.py','nitro_texture.py')
    key=w.sha256(b''.join((ROOT/'tools'/n).read_bytes() for n in dependencies)+style.encode()+native(stem+'.xbd'))
    cache=ROOT/'work/dual-rework/motion-cache'/f'{key}.zip'
    if cache.exists():
        with zipfile.ZipFile(cache) as z:
            meta=json.loads(z.read('manifest.json'));extras={n:z.read(n) for n in z.namelist() if n!='manifest.json'}
        if {n:w.sha256(raw) for n,raw in extras.items()}!=meta['payload_hashes']:raise ValueError('Motion cache integrity failure')
        return extras,{n:{int(k):v for k,v in d.items()} for n,d in meta['links'].items()},meta['clips']
    extras,links,clips=motion.prepare(native,names,style,stem,prefix)
    cache.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(cache,'w',zipfile.ZIP_DEFLATED) as z:
        for n,raw in extras.items():z.writestr(n,raw)
        z.writestr('manifest.json',json.dumps(dict(links=links,clips=clips,payload_hashes={n:w.sha256(raw) for n,raw in extras.items()})))
    return extras,links,clips

def offset(addr):return kit.SOURCE+addr-kit.TARGET if addr>=kit.TARGET else addr-BASE

def overview(template):
    xy={76:(8,70),78:(48,70),81:(88,70),83:(128,70),86:(168,70),
        87:(168,32),89:(128,32),88:(48,32),77:(48,108),82:(88,108)}
    rects={rooms.BY_ID[i]:[(x,y,x+28,y+14)] for i,(x,y) in xy.items()}
    def pixels():
        out={}
        for n,((x,y,xx,yy),) in rects.items():
            for b in range(y,yy):
                for a in range(x,xx):out[a,b]=(n,ch.EDGE if a in (x,xx-1) or b in (y,yy-1) else ch.FILL)
            if ch.BY_NAME[n].index in rooms.SAVE:
                for d in range(6):out[x+11+d,y+6]=(n,ch.EDGE);out[x+13,y+4+d]=(n,ch.EDGE)
        return out
    with patch.object(ch,'MAP_ROOMS',rects),patch.object(ch,'_map_pixels',pixels):raw,listing=ch.map_layout(template)
    from tools.minimap_cbmp import Cbmp
    screen=Cbmp.parse(raw);body=pixels();wires=set();seen=set()
    for (n,g),(dest,_) in rooms.LINKS.items():
        edge=frozenset((n,dest))
        if n not in rects or dest not in rects or edge in seen:continue
        seen.add(edge);a=rects[n][0];b=rects[dest][0];x,y=(a[0]+a[2])//2,(a[1]+a[3])//2;xx,yy=(b[0]+b[2])//2,(b[1]+b[3])//2
        for i in range(min(x,xx),max(x,xx)+1):
            if (i,y) not in body:wires.add((i,y))
        for i in range(min(y,yy),max(y,yy)+1):
            if (xx,i) not in body:wires.add((xx,i))
    cells={}
    for x,y in wires:cells.setdefault((3+x//8,3+y//8),[]).append((x%8,y%8))
    tiles=[];changed={}
    for (cx,cy),points in sorted(cells.items()):
        entry=screen.screen[cy*screen.width+cx];palette=entry>>12;tile=list(screen.tile(entry&1023))
        pens=[slot%16+ch.EDGE for n,slot,x,y in listing if slot//16==palette and slot%16+ch.EDGE in tile]
        if pens:pen=pens[0]
        else:palette=11;pen=6;tile=[0]*64
        for x,y in points:tile[y*8+x]=pen
        changed[cx,cy]=palette<<12|screen.count+len(tiles);tiles.append(tile)
    screen,_=screen.with_tiles(tiles)
    return screen.with_screen(changed).to_bytes(),listing

def apply_rom(rom):
    if w.sha256(rom)!=PARENT:raise ValueError('Renewal requires exact accepted0.20.0')
    fs=next(e for e in w.nitrofs_entries(rom) if e['name']=='Glob.bin');glob=rom[fs['start']:fs['end']]
    offsets,names,table=w.parse_glob(glob);blobs=[glob[a:b] for a,b in zip(offsets,offsets[1:])];originals=tuple(blobs)
    def asset(n):return originals[names.index(n)]
    clean,cg,cm=mod.load_clean();co,cn,_=w.parse_glob(cg)
    def native(n):i=cn.index(n);return cg[co[i]:co[i+1]]
    h=w.parse_header(rom);arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']];new=bytearray(arm)
    hc=w.parse_header(clean);ca=clean[hc['arm9_offset']:hc['arm9_offset']+hc['arm9_size']]
    catalog=room_catalog.parse(ca,cn);source=next(r for r in catalog if r.name==mr.SOURCE)
    spawn,exit=ch.door_templates(native);lookup=w.u32(arm,ch.LOOKUP_LITERAL-BASE)
    extras={};modified=set();plans={};compiled={};objects={};descs={};reports={}
    for index in range(76,108):
        name=rooms.BY_ID[index] if index<96 else cr.NAMES[index-96]
        print('ROOM '+str(index)+' '+name,flush=True)
        if index<96:
            spec=rooms.SPECS[name];plan=spec.plan(native);built=rc.compile_room(plan)
            raw,_=ch.build_room(native(mr.SOURCE+'_app.obj'),native(mr.SOURCE+'_app.obj'),ch.Room(index,'RenewalEmpty',mr.SOURCE,'authored',True),
                source.index,[r.name for r in catalog],{},visited_flag=ch.visited(index))
            raw=mr.stage(raw,name,native,room_of=lambda n:ch.BY_NAME[n].index if n in ch.BY_NAME else next(r.index for r in catalog if r.name==n),
                visited=ch.visited(index),spawn_template=spawn,exit_template=exit,links=rooms.LINKS,flags=ch.ROOM_FLAGS,authored=spec,compiled_room=built)
            # Every Midnight shutter has one explicit interaction. Crossing an
            # upper landing can no longer accidentally trigger the lower exit.
            obj=RoomObjects.parse(raw);entities=Entities.parse(obj.records[0].sections[0]);section=entities.to_bytes() if hasattr(entities,'to_bytes') else obj.records[0].sections[0]
            for i,e in enumerate(entities.records):
                if len(e)==28 and w.u32(e,12)==7 and e[27]>1:
                    ed=bytearray(e);ed[26]=0;section=Entities.parse(section).replace_record(i,bytes(ed))
            raw=obj.replace_section(0,0,section)
            if index==89:raw=boss.stage(raw,native)
            if index in (76,88):
                group=3 if index==76 else 2;obj=RoomObjects.parse(raw)
                commands=Events.parse(obj.records[0].sections[1],obj.records[0].raw[3]).groups[group].commands
                raw,opened=room_script.append_groups(raw,0,[(EventGroup(commands),'Earned Crown return')])
                raw,_=room_script.drop_commands(raw,0,lambda g,c:g==group)
                raw=room_script.extend_group(raw,0,group,[room_script.if_var(boss.DEFEATED,'==',1,then=room_script.action(eg=opened))])
        else:
            spec=cr.SPECS[name];plan=rooms.crane_geometry(name,native);built=rc.compile_room(plan);raw=asset('zz_'+name+'_app.obj')
            tree=rc.rc.RoomCollision.parse(built.collision)
            anchors=room_author.plan_anchors(rc.surfaces(plan),spec.area or plan.bounds,floor_top=spec.spawn_top,solid=lambda x,y:tree.solid_at(x,y) is not None)
            raw=room_author.set_anchors(raw,anchors)
            obj=RoomObjects.parse(raw);section=obj.records[0].sections[0];entities=Entities.parse(section)
            for g,d in enumerate(spec.doors,1):
                if sum(v.side==d.side for v in spec.doors)<2:continue
                for j,e in enumerate(entities.records):
                    if len(e)==28 and w.u32(e,12)==7 and e[27]==g+1:
                        changed=bytearray(e);changed[26]=0;section=Entities.parse(section).replace_record(j,bytes(changed))
            raw=obj.replace_section(0,0,section)
        plans[name]=plan;compiled[name]=built;objects[name]=raw
        objindex=names.index('zz_'+name+'_app.obj');blobs[objindex]=raw;modified.add(objindex)
        prefix='zz_R21_'+name
        extras[prefix+'.nsbmd']=built.model;extras[prefix+'.bsp']=built.collision
        extras[prefix+'.nsbtx']=built.textures
        extras[prefix+'.cbmp'],_=room_minimap.build(native(ch.MAP_SOURCE),plan,spec.doors,save=spec.save,glyphs=__import__('tools.crane_art',fromlist=['FONT']).FONT)
        descs[index]=w.u32(arm,offset(lookup)+4*index)
        reports[name]=dict(index=index,title=rooms.TITLES.get(index,cr.DESTINATIONS.get(name,'Recovery passage')),bounds=plan.bounds,quads=built.quads,
            active=index>=96 or index in rooms.ACTIVE,ports=[dict(side=d.side,floor=d.floor,spawn=d.spawn_id) for d in spec.doors])
    raw,listing=overview(native(ch.MAP_SOURCE));i=names.index(ch.MAP_SCREEN);blobs[i]=raw;modified.add(i)
    # Each of seven species gets its own full lifecycle set. Existing models
    # retain their exact neutral bind pose and original native rigs.
    sheetindex=names.index('model_sheet.xbd');sheet=ModelSheet.parse(asset('model_sheet.xbd'));links={};clipreport={}
    styles=PRIVATE_STYLES
    group_xbds={}
    for style,stem,group,cfg in styles:
        print('MOTION '+style,flush=True);prefix='zz_R21_'+style
        if w.u32(arm,offset(cfg)+8)!=group:raise ValueError('Pinned private configuration changed')
        actions=ActorActions.parse(native(stem+'.xbd'),cn)
        for action,state,recovery in combat.PATTERNS[style]:
            if actions.lookup(action) is None:raise ValueError(f'{style} attack{action} has no actor animation')
        more,ll,clips=authored_motion(native,cn,style,stem,prefix);extras.update(more);links.update(ll);group_xbds[group]=prefix+'.xbd';clipreport[style]=clips
    # Shorten Objectives and show a new immutable version in both native menus.
    for n in ch.STRING_FILES:
        i=names.index(n);first=slot_count(blobs[i]);blobs[i]=StringSlots(native(n)).grown(blobs[i],{50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}'},appended=OBJECTIVES);modified.add(i)
    aligned={};size=sum(map(len,blobs))
    for n,raw in extras.items():
        if n.endswith(('.nsbmd','.nsbtx')) and size%4:
            pad=bytes(-size%4);aligned[f'zz_r21_align{len(aligned)}.bin']=pad;size+=len(pad)
        aligned[n]=raw;size+=len(raw)
    outnames,outblobs=oscorp_resources.append_resources(names,blobs,aligned)
    # Native XBD resource IDs are unchanged by append; remap only selected parts.
    outblobs=cc.bind_xbds(outnames,outblobs,links)
    edited=bytearray(outblobs[sheetindex])
    for group,xbd in group_xbds.items():struct.pack_into('<H',edited,sheet.start+group*6+2,outnames.index(xbd))
    ModelSheet.parse(edited);outblobs[sheetindex]=bytes(edited);modified.add(sheetindex)
    for index,desc in descs.items():
        n=rooms.BY_ID[index] if index<96 else cr.NAMES[index-96];prefix='zz_R21_'+n;at=offset(desc)
        struct.pack_into('<I',new,at+4,outnames.index(prefix+'.nsbtx'));struct.pack_into('<I',new,at+8,outnames.index(prefix+'.bsp'))
        modelptr=w.u32(arm,at+0x20);struct.pack_into('<I',new,offset(modelptr),outnames.index(prefix+'.nsbmd'))
        struct.pack_into('<9i',new,at+0x28,*room_minimap.projection(plans[n]).fields);struct.pack_into('<I',new,at+0x4c,outnames.index(prefix+'.cbmp'))
    # Locate the existing area table through exact native literal references.
    areas=None
    for at in range(0,kit.SOURCE,4):
        value=w.u32(arm,at)
        if crane.CR_BASE<=value<parent.START and w.u32(arm,offset(value))==names.index('MMPier.cbmp'):
            if w.u32(arm,offset(value)+6*16)==names.index(crane.MAP_SCREEN):areas=value;break
    if areas is None:raise ValueError('Area table missing')
    mapat,count=struct.unpack_from('<2I',arm,offset(areas)+5*16+8);mapped=ch.map_entries(listing)
    if len(mapped)>count*20:raise ValueError('Map list exceeds owned storage')
    new[offset(mapat):offset(mapat)+len(mapped)]=mapped;struct.pack_into('<I',new,offset(areas)+5*16+12,len(listing))
    data=bytearray()
    def alloc(raw=b'',size=None):
        data.extend(bytes(-len(data)%4));at=START+len(data);data.extend(raw if size is None else bytes(size));return at
    sequences={s:alloc(b''.join(struct.pack('<3I',*v) for v in combat.PATTERNS[s])) for s,_,_,_ in styles}
    records=alloc(b''.join(struct.pack('<4I',cfg,sequences[s],len(combat.PATTERNS[s]),i) for i,(s,_,_,cfg) in enumerate(styles))+bytes(16))
    slots=alloc(size=32*32);counts=alloc(size=28);voices=alloc(size=28);hero=alloc(size=4)
    capture=alloc();data.extend(combat.capture_hero(capture,hero))
    think=alloc();data.extend(combat.think(think,records,slots,counts,hero));enter=alloc();data.extend(combat.enter(enter,records,slots,voices))
    sound=alloc();data.extend(combat.sound_filter(sound,crane.target(crane_audio.SITE,w.u32(arm,crane_audio.SITE-BASE))))
    goal=alloc(struct.pack('<4I',first,first+1,first+2,first+3));obj=alloc();data.extend(parent.objective_adapter(obj,goal,crane.target(__import__('tools.crane_navigation',fromlist=['OBJECTIVE_SITE']).OBJECTIVE_SITE,w.u32(arm,0xE0F28))))
    if len(data)>SPACE:raise ValueError('Runtime reservation exceeded')
    used=len(data);data.extend(bytes(SPACE-used));end=len(arm)-36
    if w.u32(arm,kit.TABLE_POINTERS)!=BASE+end or struct.unpack_from('<3I',arm,end+24)!=(kit.TARGET,end-kit.SOURCE,0):raise ValueError('Parent autoload contract')
    loader=combat.loader()
    if len(loader)!=0x58:raise ValueError('Descending loader must fit exact SDK loop')
    new[0xa14:0xa6c]=loader
    new=new[:end]+data+new[end:end+24]+struct.pack('<3I',kit.TARGET,end-kit.SOURCE+SPACE,0)
    struct.pack_into('<2I',new,kit.TABLE_POINTERS,BASE+end+SPACE,BASE+end+SPACE+36)
    struct.pack_into('<I',new,kit.ARENA_LOWER,START+SPACE)
    if w.u32(arm,0x776bc)!=0xe92d4010:raise ValueError('Controller update prologue changed')
    for at,value in ((0x020776bc,crane.branch(0x020776bc,capture)),(combat.THINK_SLOT,think),(combat.ENTER_SLOT,enter),(crane_audio.SITE,crane.branch(crane_audio.SITE,sound)),
                     (0x020E0F28,crane.branch(0x020E0F28,obj,link=True)),(BASE+ch.GLOB_COUNT,len(outnames))):struct.pack_into('<I',new,at-BASE,value)
    sf=next(e for e in w.nitrofs_entries(rom) if e['name']=='sound_data.sdat')
    print('PACK',flush=True)
    expanded=bytearray(rom)+b'\xff'*len(rom);expanded[0x14]+=1
    struct.pack_into('<H',expanded,0x15e,w.crc16(expanded[:0x15e]))
    w.validate_rom(expanded,target=True)
    result=w.rebuild_rom(bytes(expanded),{'Glob.bin':w.pack_glob(outnames,outblobs),'sound_data.sdat':combat.sound_data(rom[sf['start']:sf['end']])})
    result,_=kit.replace_arm9(result,bytes(new));w.validate_rom(result,target=True)
    if new[kit.SOURCE:kit.SOURCE+kit.RESERVE]!=arm[kit.SOURCE:kit.SOURCE+kit.RESERVE]:raise ValueError('Player kit changed')
    for i,raw in enumerate(outblobs[:len(originals)]):
        if i not in modified and i!=table and raw!=originals[i]:raise ValueError('Unrelated asset changed: '+names[i])
    from tools import release_info
    pin=release_info.PROFILE_INFO['tasm-v'+VERSION]
    if pin.get('rom_sha256') and w.sha256(result)!=pin['rom_sha256']:raise ValueError('Renewal ROM differs from release pin')
    if pin.get('arm9_sha256') and w.sha256(new)!=pin['arm9_sha256']:raise ValueError('Renewal ARM9 differs from release pin')
    report=dict(version=VERSION,parent_sha256=PARENT,rom_sha256=w.sha256(result),arm9_sha256=w.sha256(new),rooms=reports,
        active_midnight_rooms=list(rooms.ACTIVE),midnight_links={n+':'+str(g):[d,s] for (n,g),(d,s) in rooms.LINKS.items()},
        lifecycle=clipreport,patterns=combat.PATTERNS,configs={s:cfg for s,_,_,cfg in styles},runtime=dict(start=START,reservation=SPACE,used=used,
        slots=slots,attack_counters=counts,voice_counters=voices,hero=hero,capture=capture,think=think,enter=enter,records=records),
        sound=dict(first=combat.FIRST,count=35,old_voice_requests_muted=True),map_entries=len(listing),kit_preserved=True,
        cartridge_mib=len(result)//(1024*1024),loader='preloaded rows, descending word copies, native BSS/cache handling',modified_resources=[names[i] for i in sorted(modified)],
        appended_resources={n:dict(size=len(raw),sha256=w.sha256(raw)) for n,raw in aligned.items()})
    return result,report

def generate(output=OUT,source=None):
    output=Path(output);source=Path(source) if source is not None else None
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Candidates belong in build')
    if source is None:
        clean,g,manifest=mod.load_clean()
        overlays=mod.overlay_files(ROOT/'mods',[e['name'] for e in manifest['entries']],added_names=(*oscorp_resources.EXTRA_NAMES,*kit.EXTRA_NAMES))
        result,_,metadata=mod.create_build(clean,g,manifest,overlays,gameplay_profile='tasm-v'+VERSION);report=metadata['chapter_renewal']
        recipe=dict(schema_version=1,profile='tasm-v'+VERSION,release_version=VERSION,required_overlays={n:w.sha256(raw) for n,raw in sorted(overlays.items())})
        for n,raw in overlays.items():w.atomic_write(output/'mods'/n,raw,sources=(mod.DEFAULT_ROM,))
    else:
        result,report=apply_rom(source.read_bytes());metadata=json.loads(source.with_suffix('.build.json').read_text());metadata['chapter_renewal']=report
        recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text());recipe.update(profile='tasm-v'+VERSION,release_version=VERSION)
    path=output/'Versioned.nds';w.atomic_write(path,result,sources=(mod.DEFAULT_ROM,*((source,) if source else ())))
    metadata.update(release_version=VERSION,release_date='2026-10-17',output_rom_sha256=w.sha256(result))
    checked=w.validate_rom(result,target=True);metadata.update(rom_size=len(result),used_rom_size=checked['header']['used_rom_size'],nitrofs=checked['nitrofs'],header_crc16=checked['header']['header_crc16'])
    w.write_json(output/'gameplay_profile.json',recipe)
    w.write_json(path.with_suffix('.build.json'),metadata);print(json.dumps(dict(candidate=str(path),sha=w.sha256(result),runtime=report['runtime'])))
    return path

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--release-dir',type=Path,default=OUT);p.add_argument('--source',type=Path);a=p.parse_args();generate(a.release_dir,a.source)
