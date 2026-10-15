"""Crane Row post-pass: independent room/map/message storage after Midnight.

Candidates go to build/. Existing room IDs, descriptors, visited flags, chapter
resources and the native five-area map remain intact. No player save is edited.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import mod
from tools import crane_rooms as cr, midnight_chapter as ch, midnight_rooms as mr
from tools import oscorp_resources, room_catalog, room_compiler, room_doors, room_minimap
from tools import room_script as s, tasm_kit as kit, wos_tool as w
from tools.room_objects import RoomObjects
from tools.room_entities import Entities
from tools.room_events import Command
from tools.qol_suits_menu import StringSlots,slot_count

VERSION='0.16.1'
BASE=0x02000000
CR_BASE=ch.ML_BASE+0x1000
CR_SPACE=0x2000
MAP_AREA=6
MAP_SCREEN='zz_CraneOverview.cbmp'
PARENT_ARM9='117c9f7c21c6b2212e95aaf021b3537128de7d6b831cc328e7620021635d6da6'
_ROLES={n:SimpleNamespace(index=cr.IDS[n]) for n in cr.NAMES}
RECTS=dict(zip(cr.NAMES,((80,110,126,122),(70,80,122,98),(148,82,170,96),
    (6,80,44,98),(6,110,56,122),(62,40,104,60),(6,32,34,68),(6,8,56,20),
    (132,44,154,56),(76,8,126,20),(148,8,196,20),(148,110,196,122))))

def _map_pixels():
    pixels={}
    def line(name,x0,y0,x1,y1):
        count=max(abs(x1-x0),abs(y1-y0),1)
        for i in range(count+1):pixels[round(x0+(x1-x0)*i/count),round(y0+(y1-y0)*i/count)]=(name,ch.EDGE)
    for i,points in ((0,((104,110),(104,98))),(1,((70,88),(44,88))),
                     (3,((26,98),(26,110))),(4,((52,110),(52,76),(60,76),(60,50),(62,50))),
                     (5,((62,48),(34,48))),(6,((20,32),(20,20))),(7,((56,14),(76,14))),
                     (9,((126,14),(148,14))),(10,((196,14),(199,14),(199,116),(196,116))),
                     (11,((148,116),(126,116))),(1,((122,89),(148,89))),
                     (5,((104,50),(132,50))),(5,((88,60),(88,80))),(9,((88,20),(88,40)))):
        for a,b in zip(points,points[1:]):line(cr.NAMES[i],*a,*b)
    for name,(x0,y0,x1,y1) in RECTS.items():
        for x in range(x0,x1):
            for y in range(y0,y1):
                pixels[x,y]=(name,ch.EDGE if x in (x0,x1-1) or y in (y0,y1-1) else ch.FILL)
    for k in range(-3,4):pixels[172+k,14+k]=(cr.NAMES[10],ch.EDGE)
    return pixels

def overview(raw):
    with patch.multiple(ch,MAP_ROOMS={n:[r] for n,r in RECTS.items()},SAVE_ROOMS={cr.NAMES[2]},
                         BOSS_ROOMS={cr.NAMES[10]},_map_pixels=_map_pixels):
        return ch.map_layout(raw)

def branch(site,target,condition=14,link=False):
    displacement=target-site-8
    if displacement%4 or not -(1<<25)<=displacement<(1<<25):raise ValueError('ARM branch range')
    return condition<<28|(0x0B000000 if link else 0x0A000000)|((displacement>>2)&0xFFFFFF)

def target(site,word):
    d=word&0xFFFFFF
    if d&0x800000:d-=0x1000000
    return site+8+4*d

def visited_stub(at):
    flags=bytes([ch.visited(i) for i in range(92,96)]+[cr.VISITS[i] for i in range(96,108)])
    words=(0xE357005C,0x328750B0,0x312FFF1E,0xE28F5008,0xE0855007,0xE555505C,0xE12FFF1E)
    return struct.pack('<7I',*words)+flags

def entrance(raw):
    raw=room_doors.add_spawn(raw,2,(44*4096,2*4096,0),'left')
    raw=room_doors.add_exit(raw,room=96,selector=1,spawn=1,center=(61*4096,6*4096,0),size=(12,24),
                            trigger_name='Trigger (Crane Row)',group_name='Crane Row')
    native=RoomObjects.parse(raw)
    e=next(e for e in Entities.parse(native.records[1].sections[0]).records
           if len(e)==24 and struct.unpack_from('<I',e,12)[0]==3)
    e=bytearray(e);struct.pack_into('<i',e,0,int(59.5*4096))
    return room_doors.append_entity(raw,1,bytes(e),'Door (Crane Row)')

def apply_rom(rom, *, version=VERSION):
    h=w.parse_header(rom);arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    if w.sha256(arm)!=PARENT_ARM9:raise ValueError('Crane Row needs the exact v0.15.1 chapter ARM9')
    source_hash=w.sha256(rom)
    fs=next(e for e in w.validate_rom(rom,target=True)['nitrofs'] if e['name']=='Glob.bin')
    glob=rom[fs['start']:fs['end']];offsets,names,table_index=w.parse_glob(glob)
    blobs=[glob[a:z] for a,z in zip(offsets,offsets[1:])]
    originals=tuple(blobs)
    clean,clean_glob,manifest=mod.load_clean()
    clean_h=w.parse_header(clean);clean_arm=clean[clean_h['arm9_offset']:clean_h['arm9_offset']+clean_h['arm9_size']]
    entries={e['name']:e for e in manifest['entries']}
    def asset(name):
        e=entries[name];return clean_glob[e['offset']:e['offset']+e['size']]
    native=room_catalog.parse(clean_arm,names)
    source=next(r for r in native if r.name==mr.SOURCE)
    native_names=[r.name for r in native]
    spawn_template,exit_template=ch.door_templates(asset)
    old_message_first=ch.MESSAGE_FIRST+len(ch.LINES)
    def say(key):
        if key not in cr.LINES:return None
        return Command(0x15,struct.pack('<HBBBBBB',0,old_message_first+list(cr.LINES).index(key),0,0,0,0,0))
    extras={};plans={};objects={};built_rooms={}
    for name in cr.NAMES:
        index=cr.IDS[name]
        raw,_=ch.build_room(asset(mr.SOURCE+'_app.obj'),asset(mr.SOURCE+'_app.obj'),
                            ch.Room(index,name,mr.SOURCE,'authored',True),source.index,native_names,{})
        plan=cr.geometry(name,asset)
        try:built=room_compiler.compile_room(plan)
        except ValueError as exc:raise ValueError(f'{name}: {exc}') from exc
        obj=cr.stage(raw,name,asset,built,spawn_template,exit_template,say)
        extras[f'zz_{name}_app.obj']=obj
        extras[f'zz_{name}Textures.nsbtx']=built.textures
        extras[f'zz_{name}.nsbmd']=built.model
        extras[f'zz_{name}.bsp']=built.collision
        extras[f'zz_{name}_detail.cbmp'],_=room_minimap.build(asset(ch.MAP_SOURCE),plan,cr.SPECS[name].doors,save=cr.SPECS[name].save)
        plans[name]=plan;objects[name]=obj;built_rooms[name]=built
    extras[MAP_SCREEN],listing=overview(asset(ch.MAP_SOURCE))
    from tools import crane_boss
    for key,model in crane_boss.models().items():extras[f'zz_CR_{key}.nsbmd']=model
    modified={names.index('Pier_Save02_app.obj')}
    blobs[names.index('Pier_Save02_app.obj')]=entrance(blobs[names.index('Pier_Save02_app.obj')])
    firsts=set()
    for name in ch.STRING_FILES:
        i=names.index(name);modified.add(i);firsts.add(slot_count(blobs[i]))
        blobs[i]=StringSlots(asset(name)).grown(blobs[i],{50:f'TASM v{version}\nPress a button to start',74:f'Options v{version}'},
                              appended=[*cr.LINES.values(),cr.TITLE])
    if len(firsts)!=1:raise ValueError('String count mismatch')
    first_string=firsts.pop()
    aligned={};size=sum(map(len,blobs))
    for name,data in extras.items():
        if name.endswith(('.nsbmd','.nsbtx')) and size%4:
            pad=bytes(-size%4);aligned[f'zz_cr_alignment{len(aligned)}.bin']=pad;size+=len(pad)
        aligned[name]=data;size+=len(data)
    out_names,out_blobs=oscorp_resources.append_resources(names,blobs,aligned)
    # Owned table allocator. The Midnight autoload prefix is copied unchanged.
    data=bytearray()
    def alloc(payload=b'',size=None):
        data.extend(bytes(-len(data)%4));at=CR_BASE+len(data)
        data.extend(payload if size is None else bytes(size));return at
    lookup_at=alloc(size=108*4)
    descriptor_at=alloc(size=12*80)
    model_at=alloc(size=12*4)
    labels_at=alloc(b''.join(n.encode()+b'\0' for n in cr.NAMES))
    old_offset=lambda addr: kit.SOURCE+addr-kit.TARGET if addr>=kit.TARGET else addr-BASE
    old_lookup=w.u32(arm,ch.LOOKUP_LITERAL-BASE)
    lookup=list(struct.unpack_from('<96I',arm,old_offset(old_lookup)))
    cursor=labels_at
    resource_map={}
    for i,name in enumerate(cr.NAMES):
        indices={key:out_names.index(file) for key,file in {
            'objects':f'zz_{name}_app.obj','texture':f'zz_{name}Textures.nsbtx','model':f'zz_{name}.nsbmd',
            'bsp':f'zz_{name}.bsp','detail_map':f'zz_{name}_detail.cbmp'}.items()}
        resource_map[name]=indices
        raw=bytearray(source.raw)
        struct.pack_into('<4I',raw,0,cursor,indices['texture'],indices['bsp'],indices['objects'])
        struct.pack_into('<I',raw,0x20,model_at+i*4)
        struct.pack_into('<9i',raw,0x28,*room_minimap.projection(plans[name],MAP_AREA).fields)
        struct.pack_into('<I',raw,0x4C,indices['detail_map'])
        data[descriptor_at-CR_BASE+i*80:descriptor_at-CR_BASE+(i+1)*80]=raw
        struct.pack_into('<I',data,model_at-CR_BASE+i*4,indices['model'])
        lookup.append(descriptor_at+i*80);cursor+=len(name)+1
    struct.pack_into('<108I',data,lookup_at-CR_BASE,*lookup)
    stub_at=alloc();data.extend(visited_stub(stub_at))
    areas_at=alloc(size=7*16)
    for i,(screen,title) in enumerate(zip(('MMPier.cbmp','MMResident.cbmp','MMSewer.cbmp','MMDowntown.cbmp','MMHive.cbmp',ch.MAP_SCREEN),
                                        (381,382,383,379,380,w.u32(arm,ch.AREA_LITERALS[1]-BASE)))):
        row=bytearray(arm[ch.AREA_ROWS-BASE+i*16:ch.AREA_ROWS-BASE+(i+1)*16])
        struct.pack_into('<2I',row,0,out_names.index(screen),title)
        data[areas_at-CR_BASE+i*16:areas_at-CR_BASE+(i+1)*16]=row
    map_at=alloc(b''.join(struct.pack('<2I',cr.IDS[n],1)+bytes((1 if n==cr.NAMES[2] else 0,slot,slot+4))+ch.STATE_COLORS+bytes((x,y,0,0,0))
                          for n,slot,x,y in listing))
    struct.pack_into('<4I',data,areas_at-CR_BASE+MAP_AREA*16,out_names.index(MAP_SCREEN),first_string+len(cr.LINES),map_at,len(listing))
    # Current accessor has a literal at +0x20: biased new-message table.
    words=struct.unpack_from('<9I',arm,ch.MESSAGE_ACCESSOR-BASE)
    old_messages=words[-1]+ch.MESSAGE_FIRST*44
    existing_messages=arm[old_offset(old_messages):old_offset(old_messages)+44*len(ch.LINES)]
    if len(existing_messages)!=44*len(ch.LINES):raise ValueError('Parent message table bounds')
    message_bytes=existing_messages+b''.join(struct.pack('<IHH9I',first_string+i,0xFFFF,0xFFFF,*([0x7FFFFFFF]*9)) for i in range(len(cr.LINES)))
    messages_at=alloc(message_bytes)
    state_at=alloc(size=32)
    hooks=[]
    data_at=alloc();data.extend(crane_boss.data_adapter(clean_arm,data_at,
        target(0x020D1610,w.u32(arm,0x020D1610-BASE)),
        {key:out_names.index(f'zz_CR_{key}.nsbmd') for key in crane_boss.models()}))
    hooks.append((0x020D1610,branch(0x020D1610,data_at)))
    for site,expected,make in ((crane_boss.HP_SITE,0xE92D000F,crane_boss.hp_adapter),
                              (crane_boss.TICK_SITE,0xE92D4FF0,lambda at:crane_boss.motion_adapter(at,state_at))):
        if w.u32(arm,site-BASE)!=expected:raise ValueError('Native crane hook changed')
        at=alloc();data.extend(make(at));hooks.append((site,branch(site,at)))
    wave_site=0x0204C2C8;at=alloc();data.extend(crane_boss.wave_adapter(at,target(wave_site,w.u32(arm,wave_site-BASE))))
    hooks.append((wave_site,branch(wave_site,at,condition=1)))
    if len(data)>CR_SPACE:raise ValueError('Crane tables exceed reservation')
    used=len(data);data.extend(bytes(CR_SPACE-len(data)))
    old_end=kit.SOURCE+kit.RESERVE+ch.ML_SPACE
    if len(arm)!=old_end+36 or struct.unpack_from('<3I',arm,old_end+24)!=(kit.TARGET,kit.RESERVE+ch.ML_SPACE,0):
        raise ValueError('Parent autoload contract')
    image=bytearray(arm[kit.SOURCE:old_end])+data
    # Existing kit dial has forty rows, including all twelve new room IDs.
    for index in range(96,108):
        scale=(0,0) if index in (98,104,107) else (min(192,144+4*(index-96)),96)
        at=kit.KIT2_OFFSET+kit.DIAL_OFFSET+(index-76)*2
        if any(image[at:at+2]):raise ValueError('New room strength slot already occupied')
        image[at:at+2]=bytes(scale)
    new=bytearray(arm[:kit.SOURCE]+image+arm[old_end:old_end+24]+struct.pack('<3I',kit.TARGET,len(image),0))
    end=kit.SOURCE+len(image)
    struct.pack_into('<2I',new,kit.TABLE_POINTERS,BASE+end,BASE+end+36)
    struct.pack_into('<I',new,kit.ARENA_LOWER,kit.TARGET+len(image))
    patches=[]
    def put(address,value):
        before=w.u32(new,address-BASE);struct.pack_into('<I',new,address-BASE,value);patches.append((address,before,value))
    put(ch.LOOKUP_LITERAL,lookup_at)
    put(ch.SAVE_ROOM_CHECK,ch.CMP_R1|108);put(ch.RELOAD_ROOM_CHECK,ch.CMP_R1|108)
    put(BASE+ch.GLOB_COUNT,len(out_names))
    put(ch.MAP_VISITED_SITE[0],branch(ch.MAP_VISITED_SITE[0],stub_at,link=True))
    area_refs=[]
    for at in range(0,len(arm)-4,4):
        value=w.u32(arm,at)
        if ch.AREA_ROWS<=value<ch.AREA_ROWS+6*16:
            put(BASE+at,areas_at+value-ch.AREA_ROWS);area_refs.append(hex(BASE+at))
    if len(area_refs)<4:raise ValueError('Native area table references changed')
    for address,_,old in ch.MAP_AREA_BOUNDS:
        if w.u32(arm,address-BASE)!=old:raise ValueError('Parent map bound changed')
        put(address,0xE3500007)
    for i,value in enumerate(ch.message_accessor(messages_at)):put(ch.MESSAGE_ACCESSOR+4*i,value)
    for address in ch.MESSAGE_BOUNDS:put(address,ch.CMP_R1|(old_message_first+len(cr.LINES)))
    for address,value in hooks:put(address,value)
    # Retain the exact existing chapter block, including both native adapters.
    if new[kit.SOURCE+kit.RESERVE:old_end]!=arm[kit.SOURCE+kit.RESERVE:old_end]:raise ValueError('Midnight block changed')
    staged=w.rebuild_rom(rom,{'Glob.bin':w.pack_glob(out_names,out_blobs)})
    result,_=kit.replace_arm9(staged,bytes(new))
    checked=w.validate_rom(result,target=True)
    final_h=w.parse_header(result)
    arm_digest=w.sha256(result[final_h['arm9_offset']:final_h['arm9_offset']+final_h['arm9_size']])
    from tools import release_info
    expected=release_info.PROFILE_INFO.get('tasm-v'+version,{}).get('arm9_sha256')
    if expected and arm_digest!=expected:raise ValueError('Crane release ARM9 differs from its pin')
    for i,blob in enumerate(out_blobs):
        if i<len(originals) and i not in (*modified,table_index) and blob!=originals[i]:raise ValueError('Unrelated resource changed: '+names[i])
    return result,{'schema_version':1,'version':version,'parent_sha256':source_hash,'rom_sha256':w.sha256(result),'arm9_sha256':arm_digest,
        'rooms':{n:{'index':cr.IDS[n],'visited':cr.VISITS[cr.IDS[n]],'quads':built_rooms[n].quads,'bounds':list(plans[n].bounds),**resource_map[n]} for n in cr.NAMES},
        'area':MAP_AREA,'map_entries':len(listing),'area_references':area_refs,'table_bytes':used,'reservation':CR_SPACE,
        'midnight_block_preserved':True,'patches':[{'address':hex(a),'old':hex(b),'new':hex(c)} for a,b,c in patches],
        'messages':{k:{'id':old_message_first+i,'string':first_string+i} for i,k in enumerate(cr.LINES)},
        'status':'Structural candidate; traversal, map, save and encounter qualification required.'}

def build(source=ROOT/'build/version-0.15.1-final/Versioned.nds',output=ROOT/'build/crane-row/dev.nds'):
    source,output=Path(source),Path(output)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Candidates belong in build/')
    raw=source.read_bytes();result,report=apply_rom(raw)
    w.atomic_write(output,result,sources=(source,mod.DEFAULT_ROM))
    w.write_json(output.with_suffix('.build.json'),report)
    if source.read_bytes()!=raw:raise ValueError('Source changed')
    print(json.dumps({'candidate':str(output),'sha256':report['rom_sha256'],'rooms':len(report['rooms']),'table_bytes':report['table_bytes']}))
    return output

def generate(output):
    """Compose a reviewable full release candidate through the normal pipeline."""
    output=Path(output)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Candidates belong in build/')
    from tools import tasm_kit,oscorp_resources
    rom,glob,manifest=mod.load_clean()
    overlays=mod.overlay_files(ROOT/'mods',[e['name'] for e in manifest['entries']],
        added_names=(*oscorp_resources.EXTRA_NAMES,*tasm_kit.EXTRA_NAMES))
    result,_,log=mod.create_build(rom,glob,manifest,overlays,gameplay_profile='tasm-v'+VERSION)
    for name,blob in overlays.items():w.atomic_write(output/'mods'/name,blob,sources=(mod.DEFAULT_ROM,))
    recipe={'schema_version':1,'profile':'tasm-v'+VERSION,'release_version':VERSION,
            'required_overlays':{name:w.sha256(blob) for name,blob in sorted(overlays.items())}}
    w.write_json(output/'gameplay_profile.json',recipe)
    path=output/'Versioned.nds';w.atomic_write(path,result,sources=(mod.DEFAULT_ROM,))
    w.write_json(path.with_suffix('.build.json'),log)
    w.write_json(output/'release.json',{'version':VERSION,'rom_sha256':w.sha256(result),
        'arm9_sha256':log['crane_row']['arm9_sha256'],'qualification':'Candidate; not published'})
    print(json.dumps({'candidate':str(path),'sha256':w.sha256(result),'arm9':log['crane_row']['arm9_sha256']}))
    return path

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=ROOT/'build/version-0.15.1-final/Versioned.nds');p.add_argument('--output',type=Path,default=ROOT/'build/crane-row/dev.nds');p.add_argument('--release-dir',type=Path)
    args=p.parse_args();generate(args.release_dir) if args.release_dir else build(args.source,args.output)
