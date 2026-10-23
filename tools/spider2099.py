"""Exact v0.29 post-pass: classic 2099 Black-slot appearance, native gameplay."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import wos_tool as w, spider2099_art as art

VERSION = '0.30.0'
DATE = '2026-10-22'
PARENT = '3c9aeacca6bbc446e2f61815b341e5c5106d0f30a4c9510bcbf9384fbea16db2'
PARENT_PATH = ROOT / 'build/version-0.29.0-final/Versioned.nds'
CHANGED = ('American.strings', 'English.strings', 'spdB.nsbmd', 'spdB.nsbtx')


def resources(rom):
    entry = next(e for e in w.nitrofs_entries(rom) if e['name'] == 'Glob.bin')
    glob = rom[entry['start']:entry['end']]
    offsets, names, _ = w.parse_glob(glob)
    return names, [glob[a:b] for a,b in zip(offsets,offsets[1:])]


def apply_rom(rom):
    if w.sha256(rom) != PARENT:
        raise ValueError('2099 appearance requires exact published v0.29.0')
    names, blobs = resources(rom)
    before = tuple(blobs)
    model = blobs[names.index('spdB.nsbmd')]
    # Black currently has the player's white experimental repaint. Author from
    # verified native geometry/atlas, without reading or reusing old suit marks.
    import mod
    _, glob, manifest = mod.load_clean()
    def native(name):
        e = next(e for e in manifest['entries'] if e['name'] == name)
        return glob[e['offset']:e['offset']+e['size']]
    indices, palette, _ = art.artwork(model)
    blobs[names.index('spdB.nsbmd')], model_report = art.model(model)
    blobs[names.index('spdB.nsbtx')] = art.texture(native('spdB.nsbtx'),indices,palette)
    from tools.qol_suits_menu import StringSlots
    for name in ('American.strings','English.strings'):
        i = names.index(name)
        raw = StringSlots(native(name)).grown(blobs[i],{
            50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}'})
        blobs[i] = raw + bytes(-len(raw)%4)
    changes = [n for n,a,b in zip(names,before,blobs) if a != b]
    if sorted(changes) != sorted(CHANGED):
        raise ValueError('2099 changed unexpected resources')
    result = w.rebuild_rom(rom,{'Glob.bin':w.pack_glob(names,blobs)},legacy_gaps=True)
    h, old = w.parse_header(result), w.parse_header(rom)
    arm = result[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    if arm != rom[old['arm9_offset']:old['arm9_offset']+old['arm9_size']]:
        raise ValueError('Appearance pass changed executable gameplay')
    for name in ('arm7','arm9'):
        if result[h[name+'_offset']:h[name+'_offset']+h[name+'_size']] != rom[old[name+'_offset']:old[name+'_offset']+old[name+'_size']]:
            raise ValueError('Appearance pass changed executable')
    for e in w.nitrofs_entries(result):
        if e['name'] != 'Glob.bin':
            prior = next(p for p in w.nitrofs_entries(rom) if p['name']==e['name'])
            if result[e['start']:e['end']] != rom[prior['start']:prior['end']]:
                raise ValueError('Appearance pass changed unrelated NitroFS file')
    report = {'version':VERSION,'parent_sha256':PARENT,'rom_sha256':w.sha256(result),
              'arm9_sha256':w.sha256(arm),'modified_resources':changes,'model':model_report,
              'resource_hashes':{n:w.sha256(blobs[names.index(n)]) for n in CHANGED},
              'executable_unchanged':True,'all_other_resources_unchanged':True,
              'scope':'Classic 2099 Black-slot appearance only. Native Black moves, ownership, shared upgrades, Red kit, rooms, audio and saves unchanged.'}
    from tools import release_info
    pin = release_info.PROFILE_INFO.get('tasm-v'+VERSION,{})
    for key in ('rom_sha256','arm9_sha256'):
        if pin.get(key) and pin[key] != report[key]:
            raise ValueError('2099 differs from immutable release pin')
    return result,report


def generate(output,source=PARENT_PATH,previews=False):
    output,source=Path(output),Path(source)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):
        raise ValueError('Candidates belong inside build/')
    result,report=apply_rom(source.read_bytes())
    path=output/'Versioned.nds'
    meta=json.loads(source.with_suffix('.build.json').read_text())
    validation=w.validate_rom(result,target=True)
    ge=next(e for e in validation['nitrofs'] if e['name']=='Glob.bin')
    meta.update(spider2099=report,release_version=VERSION,release_date=DATE,
                output_rom_sha256=w.sha256(result),output=str(path.resolve()),rom_size=len(result),
                used_rom_size=validation['header']['used_rom_size'],nitrofs=validation['nitrofs'],
                header_crc16=validation['header']['header_crc16'],output_glob_sha256=w.sha256(result[ge['start']:ge['end']]))
    w.atomic_write(path,result,sources=(source,))
    w.write_json(path.with_suffix('.build.json'),meta)
    recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text())
    recipe.update(profile='tasm-v'+VERSION,release_version=VERSION)
    w.write_json(output/'gameplay_profile.json',recipe)
    w.write_json(output/'appearance.json',report)
    if previews:
        names,blobs=resources(result)
        model,texture=(blobs[names.index(n)] for n in ('spdB.nsbmd','spdB.nsbtx'))
        for yaw in (0,45,90,180):
            art.render(model,texture,output/f'model-{yaw}.png',yaw)
    print(json.dumps({'path':str(path),'sha256':report['rom_sha256']}),flush=True)
    return path


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--source',type=Path,default=PARENT_PATH)
    parser.add_argument('--previews',action='store_true')
    args=parser.parse_args()
    generate(args.out,args.source,args.previews)
