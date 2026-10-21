"""0.22.1: match material original dimensions to the shared128px atlas.

Nitro texture binding derives magnification from these dimensions. Retaining
the native64px material cropped/scaled the new UV atlas despite correct texels.
Only the seven private materials and native version labels change.
"""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import mod
from tools import wos_tool as w,midnight_chapter as ch,release_info
from tools.model_geometry import ModelGeometry
from tools.animation_rig import AnimationRig
from tools.nitro_texture import dictionary
from tools.qol_suits_menu import StringSlots,decode_grown
VERSION='0.22.1'
PARENT='69082fda16d7c0491f9bc945e6ebef11c526f7c7622a98a89959ea294b4f2eb2'
OUT=ROOT/'build/version-0.22.1-final'
STYLES=('maw','ballast','spore','skitter','warden','eye','conductor')

def fix_model(raw):
    m=ModelGeometry.parse(raw);mat=m.model+w.u32(raw,m.model+8);out=bytearray(raw);changes=[]
    for name,entry in dictionary(raw,mat+4,4):
        at=mat+w.u32(entry,0);before=struct.unpack_from('<2H',raw,at+32)
        if before!=(64,64):raise ValueError('Expected frozen0.22 material dimensions')
        struct.pack_into('<2H',out,at+32,128,128);changes.append(dict(material=name,offset=at+32,before=before,after=(128,128)))
    if AnimationRig.parse(out).parents!=AnimationRig.parse(raw).parents:raise ValueError('Texture fix changed rig')
    ModelGeometry.parse(out)
    return bytes(out),changes

def apply_rom(rom):
    if w.sha256(rom)!=PARENT:raise ValueError('Texture patch requires exact published0.22.0')
    ge=next(e for e in w.nitrofs_entries(rom) if e['name']=='Glob.bin');g=rom[ge['start']:ge['end']];o,names,_=w.parse_glob(g)
    blobs=[g[a:b] for a,b in zip(o,o[1:])];before=tuple(blobs);report={};changed=set()
    for style in STYLES:
        name='zz_F22_'+style+'.nsbmd';i=names.index(name);blobs[i],report[style]=fix_model(blobs[i]);changed.add(i)
    clean,cg,_=mod.load_clean();co,cn,_=w.parse_glob(cg)
    for name in ch.STRING_FILES:
        i=names.index(name);j=cn.index(name);native=cg[co[j]:co[j+1]]
        raw=StringSlots(native).grown(blobs[i],{50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}'})
        raw+=bytes((len(blobs[i])-len(raw))%4)
        if decode_grown(raw,74)!=f'Options v{VERSION}':raise ValueError('Texture patch version label failed')
        blobs[i]=raw;changed.add(i)
    for i,raw in enumerate(blobs):
        if i not in changed and raw!=before[i]:raise ValueError('Unrelated texture-patch resource changed')
    result=w.rebuild_rom(rom,{'Glob.bin':w.pack_glob(names,blobs)});w.validate_rom(result,target=True)
    h=w.parse_header(rom);arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']];hh=w.parse_header(result)
    if result[hh['arm9_offset']:hh['arm9_offset']+hh['arm9_size']]!=arm:raise ValueError('Texture patch changed executable')
    sf=lambda r:next(r[e['start']:e['end']] for e in w.nitrofs_entries(r) if e['name']=='sound_data.sdat')
    if sf(result)!=sf(rom):raise ValueError('Texture patch changed sound bank')
    pin=release_info.PROFILE_INFO['tasm-v'+VERSION]
    if pin.get('rom_sha256') and w.sha256(result)!=pin['rom_sha256']:raise ValueError('Texture patch differs from release pin')
    meta=dict(version=VERSION,parent_sha256=PARENT,rom_sha256=w.sha256(result),arm9_sha256=w.sha256(arm),materials=report,
        modified_resources=[names[i] for i in sorted(changed)],all_other_resources_exact=True,executable_exact=True,sound_exact=True)
    return result,meta

def generate(output=OUT,source=None):
    output=Path(output);source=Path(source) if source else ROOT/'build/version-0.22.0-final/Versioned.nds'
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Private candidates belong in build/')
    result,report=apply_rom(source.read_bytes());meta=json.loads(source.with_suffix('.build.json').read_text());meta['creature_texture_fix']=report
    meta.update(release_version=VERSION,release_date='2026-10-17',output_rom_sha256=w.sha256(result))
    v=w.validate_rom(result,target=True);meta.update(rom_size=len(result),used_rom_size=v['header']['used_rom_size'],nitrofs=v['nitrofs'],header_crc16=v['header']['header_crc16'])
    path=output/'Versioned.nds';w.atomic_write(path,result,sources=(source,mod.DEFAULT_ROM));w.write_json(path.with_suffix('.build.json'),meta)
    recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text());recipe.update(profile='tasm-v'+VERSION,release_version=VERSION);w.write_json(output/'gameplay_profile.json',recipe)
    print(json.dumps(dict(candidate=str(path),sha256=w.sha256(result),report=report)));return path
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path);p.add_argument('--release-dir',type=Path,default=OUT);a=p.parse_args();generate(a.release_dir,a.source)
