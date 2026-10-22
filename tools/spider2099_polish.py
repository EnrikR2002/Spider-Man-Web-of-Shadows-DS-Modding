"""Exact v0.30 post-pass: muscular 2099 sculpt, mounted blades and crimson web cape."""
from pathlib import Path
import argparse
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import spider2099 as first,spider2099_sculpt as sculpt,spider2099_visual as visual,wos_tool as w

VERSION='0.30.1'
DATE='2026-10-22'
PARENT='2ebdf894ae723ce6ead2cfbe15a4b11151243f639958bdeea18e9149bdabf088'
PARENT_PATH=ROOT/'build/version-0.30.0-final/Versioned.nds'
CHANGED=('American.strings','English.strings','spd.nsbmd','spdB.nsbtx')


def apply_rom(rom):
    if w.sha256(rom)!=PARENT:raise ValueError('2099 polish requires exact published v0.30.0')
    import mod
    _,glob,manifest=mod.load_clean()
    def native(name):
        e=next(e for e in manifest['entries'] if e['name']==name)
        return glob[e['offset']:e['offset']+e['size']]
    names,blobs=first.resources(rom);before=tuple(blobs)
    model,model_report=sculpt.model(native('spdB.nsbmd'))
    indices,palette,paint_report=sculpt.artwork(native('spdB.nsbmd'))
    black_texture=sculpt.texture(native('spdB.nsbtx'),indices,palette)
    shared,shared_report=visual.shared_model(before[names.index('spd.nsbmd')],model,
        before[names.index('spd.nsbtx')],black_texture)
    blobs[names.index('spd.nsbmd')]=shared
    blobs[names.index('spdB.nsbtx')]=black_texture
    from tools.qol_suits_menu import StringSlots
    for name in ('American.strings','English.strings'):
        i=names.index(name);raw=StringSlots(native(name)).grown(blobs[i],{
            50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}'})
        blobs[i]=raw+bytes(-len(raw)%4)
    changed=[n for n,a,b in zip(names,before,blobs) if a!=b]
    if sorted(changed)!=sorted(CHANGED):raise ValueError('2099 polish changed unexpected resources')
    runtime=visual.Runtime(rom)
    runtime_report=runtime.install(shared_report)
    result=runtime.finish({'Glob.bin':w.pack_glob(names,blobs)})
    old,h=w.parse_header(rom),w.parse_header(result)
    for field in ('arm7',):
        if rom[old[field+'_offset']:old[field+'_offset']+old[field+'_size']]!=result[h[field+'_offset']:h[field+'_offset']+h[field+'_size']]:
            raise ValueError('2099 sculpt changed executable gameplay')
    for e in w.nitrofs_entries(result):
        if e['name']=='Glob.bin':continue
        p=next(p for p in w.nitrofs_entries(rom) if p['name']==e['name'])
        if result[e['start']:e['end']]!=rom[p['start']:p['end']]:raise ValueError('2099 sculpt changed unrelated NitroFS data')
    report={'version':VERSION,'parent_sha256':PARENT,'rom_sha256':w.sha256(result),
        'arm9_sha256':w.sha256(result[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]),
        'modified_resources':changed,'model':model_report,'paint':paint_report,
        'shared_model':shared_report,'cosmetic_draw_selector':runtime_report,
        'resource_hashes':{n:w.sha256(blobs[names.index(n)]) for n in CHANGED},
        'gameplay_kit_unchanged':True,'all_other_resources_unchanged':True,
        'scope':'Appearance only: shared player model retains the exact Red list and selects Black sculpt data just before draw. Skin, blades, crimson web cape and version strings change. Rig, motion clips, native controls/purchases/collisions, 32 KiB kit, rooms, audio and save contract remain exact.'}
    from tools import release_info
    pin=release_info.PROFILE_INFO.get('tasm-v'+VERSION,{})
    for key in ('rom_sha256','arm9_sha256'):
        if pin.get(key) and pin[key]!=report[key]:raise ValueError('2099 sculpt differs from immutable release pin')
    return result,report


def generate(output,source=PARENT_PATH,previews=False):
    output,source=Path(output),Path(source)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Candidates belong in build/')
    result,report=apply_rom(source.read_bytes());path=output/'Versioned.nds'
    meta=json.loads(source.with_suffix('.build.json').read_text());validation=w.validate_rom(result,target=True)
    ge=next(e for e in validation['nitrofs'] if e['name']=='Glob.bin')
    meta.update(spider2099_polish=report,release_version=VERSION,release_date=DATE,
        output_rom_sha256=w.sha256(result),output=str(path.resolve()),rom_size=len(result),
        used_rom_size=validation['header']['used_rom_size'],nitrofs=validation['nitrofs'],
        header_crc16=validation['header']['header_crc16'],output_glob_sha256=w.sha256(result[ge['start']:ge['end']]))
    w.atomic_write(path,result,sources=(source,));w.write_json(path.with_suffix('.build.json'),meta)
    recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text());recipe.update(profile='tasm-v'+VERSION,release_version=VERSION)
    w.write_json(output/'gameplay_profile.json',recipe);w.write_json(output/'appearance.json',report)
    if previews:
        from tools import spider2099_art as art
        names,blobs=first.resources(result)
        display=visual.selected_model(blobs[names.index('spd.nsbmd')],1)
        for yaw in (0,45,90,180):art.render(display,blobs[names.index('spdB.nsbtx')],output/f'model-{yaw}.png',yaw)
    print(json.dumps({'path':str(path),'sha256':report['rom_sha256']}),flush=True)
    return path


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--source',type=Path,default=PARENT_PATH);p.add_argument('--previews',action='store_true')
    args=p.parse_args();generate(args.out,args.source,args.previews)
