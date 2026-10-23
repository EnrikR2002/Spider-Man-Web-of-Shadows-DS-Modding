"""0.23.0: authored chapter encounters, machinery and presentation over0.22.1."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import mod
from tools import wos_tool as w,tasm_kit as kit,midnight_chapter as ch,crane_row as crane
from tools import creature_forge as forge,chapter_spectacle_combat as combat
from tools.qol_suits_menu import StringSlots,decode_grown

VERSION='0.23.0'
PARENT='1613d74662c7dfa9d5166da0b8c8ed08ec048c605a7e9167edf3e320ac4d2a75'
START=forge.START+0x16A4
EXTENSION=0x400
OLD_SPACE=forge.SPACE-0x16A4
SPACE=OLD_SPACE+EXTENSION
OUT=ROOT/'build/version-0.23.0-final'
offset=forge.offset


def apply_rom(rom,*,runtime_only=False,pilot=False):
    if w.sha256(rom)!=PARENT:raise ValueError('Spectacle requires exact published0.22.1')
    fs=next(e for e in w.nitrofs_entries(rom) if e['name']=='Glob.bin');glob=rom[fs['start']:fs['end']]
    offsets,names,_=w.parse_glob(glob);blobs=[glob[a:b] for a,b in zip(offsets,offsets[1:])];originals=tuple(blobs)
    clean,cg,_=mod.load_clean();co,cn,_=w.parse_glob(cg)
    def native(n):i=cn.index(n);return cg[co[i]:co[i+1]]
    h=w.parse_header(rom);arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']];new=bytearray(arm)
    parent=json.loads((ROOT/'reference/creature_forge.json').read_text(encoding='utf-8'))
    if parent['rom_sha256']!=PARENT:raise ValueError('Parent Forge receipt mismatch')
    rt=parent['authored']['runtime'];data=bytearray();modified=set()
    def alloc(raw=b'',size=None):
        data.extend(bytes(-len(data)%4));at=START+len(data);data.extend(raw if size is None else bytes(size));return at
    if any(arm[offset(START):offset(START)+OLD_SPACE]):raise ValueError('Parent reserved tail is occupied')
    capture=forge.parent.combat.capture_hero(rt['capture'],rt['hero']);play=rt['capture']+len(capture)
    room=rt['hero']-4
    expected=forge.combat.think(rt['think'],rt['records'],rt['slots'],rt['attack_counters'],rt['hero'],room,rt['move_counters'],play)
    if arm[offset(rt['think']):offset(rt['think'])+len(expected)]!=expected:raise ValueError('Frozen Forge thinker differs')
    navigation=alloc(size=32*8);think=alloc();data.extend(combat.think(think,rt,navigation,room,play))
    secondary=alloc();data.extend(combat.secondary(secondary,rt['slots'],(forge.parent.PRIVATE_STYLES[0][3],forge.parent.PRIVATE_STYLES[3][3])))
    if w.u32(arm,forge.combat.THINK_SLOT-0x02000000)!=rt['think']:raise ValueError('Parent EnemySM slot mismatch')
    struct.pack_into('<I',new,forge.combat.THINK_SLOT-0x02000000,think)
    if w.u32(arm,forge.combat.SECOND_SLOT-0x02000000)!=rt['secondary']:raise ValueError('Parent secondary slot mismatch')
    struct.pack_into('<I',new,forge.combat.SECOND_SLOT-0x02000000,secondary)
    report=dict(version=VERSION,parent_sha256=PARENT,runtime=dict(start=START,reservation=SPACE,think=think,secondary=secondary,navigation=navigation),
                player_kit_preserved=True,runtime_only=runtime_only,pilot=pilot)
    if not runtime_only:
        from tools import chapter_spectacle_rooms as rooms
        names,blobs,new,room_report=rooms.apply(names,blobs,new,native,alloc,data,rt,pilot=pilot)
        modified.update(room_report.pop('modified_indices'));report.update(room_report)
        from tools import chapter_spectacle_audio as audio
        site=combat.SOUND_EVENT_SITE
        if w.u32(arm,site-0x02000000)!=0xE92D4018:raise ValueError('Native OBJ sound-event prologue changed')
        event=alloc();data.extend(combat.sound_event(event,audio.FIRST,len(audio.NAMES),play))
        struct.pack_into('<I',new,site-0x02000000,crane.branch(site,event))
        report['sound_event']=dict(site=site,adapter=event,native_count=582,first=audio.FIRST,count=len(audio.NAMES),rooms=[76,107],play=play)
    for n in ch.STRING_FILES:
        i=names.index(n);raw=StringSlots(native(n)).grown(blobs[i],{50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}'})
        raw+=bytes((len(blobs[i])-len(raw))%4);blobs[i]=raw;modified.add(i)
        if decode_grown(raw,74)!=f'Options v{VERSION}':raise ValueError('Version label failure')
    used=len(data)
    if used>SPACE:raise ValueError(f'Spectacle reservation exceeded: {used}/{SPACE}')
    end=len(arm)-36
    if w.u32(arm,kit.TABLE_POINTERS)!=0x02000000+end or struct.unpack_from('<3I',arm,end+24)!=(kit.TARGET,end-kit.SOURCE,0):raise ValueError('Parent autoload rows changed')
    new=new[:end]+bytes(EXTENSION)+new[end:end+24]+struct.pack('<3I',kit.TARGET,end-kit.SOURCE+EXTENSION,0)
    struct.pack_into('<2I',new,kit.TABLE_POINTERS,0x02000000+end+EXTENSION,0x02000000+end+EXTENSION+36)
    struct.pack_into('<I',new,kit.ARENA_LOWER,forge.START+forge.SPACE+EXTENSION)
    new[offset(START):offset(START)+used]=data
    if new[kit.SOURCE:kit.SOURCE+kit.RESERVE]!=arm[kit.SOURCE:kit.SOURCE+kit.RESERVE]:raise ValueError('Player kit changed')
    for i,raw in enumerate(blobs[:len(originals)]):
        if i not in modified and raw!=originals[i]:raise ValueError('Unrelated asset changed: '+names[i])
    replacements={'Glob.bin':w.pack_glob(names,blobs)}
    if not runtime_only:
        from tools import chapter_spectacle_audio as audio
        sf=next(e for e in w.nitrofs_entries(rom) if e['name']=='sound_data.sdat')
        replacements['sound_data.sdat']=audio.sound_data(rom[sf['start']:sf['end']])
    result=w.rebuild_rom(rom,replacements,legacy_gaps=True);result,_=kit.replace_arm9(result,bytes(new));w.validate_rom(result,target=True)
    report['runtime'].update(used=used);report.update(rom_sha256=w.sha256(result),arm9_sha256=w.sha256(new),
        modified_resources=[names[i] for i in sorted(modified) if blobs[i]!=originals[i]],sound_data_preserved=runtime_only)
    from tools import release_info
    pin=release_info.PROFILE_INFO.get('tasm-v'+VERSION,{})
    if not runtime_only and not pilot:
        for k,raw in (('rom_sha256',result),('arm9_sha256',new)):
            if pin.get(k) and pin[k]!=w.sha256(raw):raise ValueError('Spectacle differs from immutable release pin')
    return result,report


def generate(output=OUT,source=None,*,runtime_only=False,pilot=False):
    output=Path(output);source=Path(source) if source else ROOT/'build/version-0.22.1-final/Versioned.nds'
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Private candidates belong in build/')
    result,report=apply_rom(source.read_bytes(),runtime_only=runtime_only,pilot=pilot)
    meta=json.loads(source.with_suffix('.build.json').read_text(encoding='utf-8'));meta['chapter_spectacle']=report
    meta.update(release_version=VERSION,release_date='2026-10-17',output_rom_sha256=w.sha256(result))
    v=w.validate_rom(result,target=True);meta.update(rom_size=len(result),used_rom_size=v['header']['used_rom_size'],nitrofs=v['nitrofs'],header_crc16=v['header']['header_crc16'])
    path=output/'Versioned.nds';w.atomic_write(path,result,sources=(source,mod.DEFAULT_ROM));w.write_json(path.with_suffix('.build.json'),meta)
    recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text(encoding='utf-8'));recipe.update(profile='tasm-v'+VERSION,release_version=VERSION)
    w.write_json(output/'gameplay_profile.json',recipe);print(json.dumps(dict(candidate=str(path),rom_sha256=w.sha256(result),runtime=report['runtime'])));return path

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path);p.add_argument('--release-dir',type=Path,default=OUT)
    p.add_argument('--runtime-only',action='store_true');p.add_argument('--pilot',action='store_true')
    a=p.parse_args();generate(a.release_dir,a.source,runtime_only=a.runtime_only,pilot=a.pilot)
