"""Exact v0.30.2 post-pass: bind Midnight creatures with a compact shared I4 atlas."""
from pathlib import Path
import argparse
import json
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
PARENT='214282a5ddf6ac71bbbddd8b5aa3854a13754313a3c66ac29d27ceb55b4f3808'
VERSION='0.30.3'
DATE='2026-10-22'
TEXTURE='zz_F22_Atlas.nsbtx'
ATLAS=ROOT/'reference/art/creature-forge-materials-v1.png'


def compact_texture(source):
    """Repack the exact shared 128px artwork from direct color to indexed I4."""
    from PIL import Image
    from tools import nitro_build
    from tools.nitro_texture import TextureArchive
    from tools import wos_tool as w

    native=TextureArchive.parse(source)
    if (len(native.textures)!=1 or native.textures[0]['name']!='Forge128'
            or native.textures[0]['width']!=128 or native.textures[0]['height']!=128
            or native.textures[0]['format']!=7 or native.textures[0]['size']!=32768
            or len(native.palettes)!=1 or native.palettes[0]['name']!='ForgePal'):
        raise ValueError('Expected the exact v0.30.2 shared 128px direct-color atlas')
    image=Image.open(ATLAS).convert('RGB').resize((128,128),Image.Resampling.LANCZOS)
    quantized=image.quantize(colors=16,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
    indices=quantized.tobytes();rgb=quantized.getpalette()[:48]
    if len(indices)!=128*128 or len(rgb)!=48 or max(indices)>15:
        raise ValueError('Unexpected 16-color shared atlas')
    palette=b''.join(struct.pack('<H',(rgb[i]>>3)|((rgb[i+1]>>3)<<5)|((rgb[i+2]>>3)<<10))
                                 for i in range(0,48,3))
    packed=bytes(indices[i]|(indices[i+1]<<4) for i in range(0,len(indices),2))
    result=nitro_build.texture_archive(
        (nitro_build.Texture('Forge128',128,128,3,packed),),
        (nitro_build.Palette('ForgePal',palette),))
    parsed=TextureArchive.parse(result);texture=parsed.textures[0]
    if (texture['format'],texture['size'],texture['width'],texture['height'])!=(3,8192,128,128):
        raise ValueError('Compact atlas is not 128x128 I4')
    if parsed.palettes[0]['name']!='ForgePal' or texture['params']&0x2000:
        raise ValueError('Compact atlas changed material names or palette-zero opacity')
    unpacked=bytes(v for byte in result[texture['offset']:texture['offset']+texture['size']]
                   for v in (byte&15,byte>>4))
    if unpacked!=indices:
        raise ValueError('Compact atlas I4 pixels do not round-trip')
    return result,{'parent_format':'direct-color','parent_pixel_bytes':32768,
        'format':'I4','pixel_bytes':8192,'palette_colors':16,'dimensions':[128,128],
        'shared_material_names':['Forge128','ForgePal'],'palette_zero_transparent':False,
        'compression_ratio':0.25,'quantizer':'Pillow FASTOCTREE, no dithering; RGB555 palette'}


def apply_rom(rom):
    from tools import wos_tool as w,spider2099 as assets,release_info
    if w.sha256(rom)!=PARENT:
        raise ValueError('Enemy texture fix requires exact published v0.30.2')
    names,blobs=assets.resources(rom);before=tuple(blobs);idx=names.index(TEXTURE)
    atlas,report=compact_texture(blobs[idx]);blobs[idx]=atlas
    from tools.qol_suits_menu import StringSlots
    import mod
    _,glob,manifest=mod.load_clean();entries={e['name']:e for e in manifest['entries']}
    for name in ('American.strings','English.strings'):
        i=names.index(name);entry=entries[name];native=glob[entry['offset']:entry['offset']+entry['size']]
        blobs[i]=StringSlots(native).grown(blobs[i],{
            50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}'})
        blobs[i]+=bytes(-len(blobs[i])%4)
    changed=[name for name,a,b in zip(names,before,blobs) if a!=b]
    if sorted(changed)!=sorted((TEXTURE,'American.strings','English.strings')):
        raise ValueError('Enemy atlas post-pass changed unexpected Glob resources')
    result=w.rebuild_rom(rom,{'Glob.bin':w.pack_glob(names,blobs)})
    validation=w.validate_rom(result,target=True);h=w.parse_header(result)
    parent_h=w.parse_header(rom)
    for field in ('arm7','arm9'):
        if rom[parent_h[field+'_offset']:parent_h[field+'_offset']+parent_h[field+'_size']]!=result[h[field+'_offset']:h[field+'_offset']+h[field+'_size']]:
            raise ValueError('Enemy atlas changed executable gameplay')
    for e in w.nitrofs_entries(result):
        if e['name']=='Glob.bin':continue
        old=next(p for p in w.nitrofs_entries(rom) if p['name']==e['name'])
        if result[e['start']:e['end']]!=rom[old['start']:old['end']]:
            raise ValueError('Enemy atlas changed unrelated NitroFS data')
    log={'version':VERSION,'parent_sha256':PARENT,'rom_sha256':w.sha256(result),
        'arm9_sha256':w.sha256(result[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]),
        'atlas':report,'modified_resources':changed,'all_enemy_model_xbd_and_motion_resources_exact':True,
        'all_other_resources_exact':True,'gameplay_arm9_arm7_exact':True}
    pin=release_info.PROFILE_INFO.get('tasm-v'+VERSION,{})
    for key in ('rom_sha256','arm9_sha256'):
        if pin.get(key) and pin[key]!=log[key]:raise ValueError('Enemy atlas composition differs from release pin')
    return result,log


def generate(output,source=ROOT/'build/version-0.30.2-final/Versioned.nds'):
    import mod
    from tools import wos_tool as w
    output,source=Path(output),Path(source)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):
        raise ValueError('Candidates belong in build/')
    result,log=apply_rom(source.read_bytes());path=output/'Versioned.nds'
    validation=w.validate_rom(result,target=True);meta=json.loads(source.with_suffix('.build.json').read_text(encoding='utf-8'))
    ge=next(e for e in validation['nitrofs'] if e['name']=='Glob.bin')
    meta.update(spider2099_enemy_texture=log,release_version=VERSION,release_date=DATE,
        output_rom_sha256=w.sha256(result),output=str(path.resolve()),rom_size=len(result),
        used_rom_size=validation['header']['used_rom_size'],nitrofs=validation['nitrofs'],
        header_crc16=validation['header']['header_crc16'],output_glob_sha256=w.sha256(result[ge['start']:ge['end']]))
    w.atomic_write(path,result,sources=(source,));w.write_json(path.with_suffix('.build.json'),meta)
    recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text(encoding='utf-8'))
    recipe.update(profile='tasm-v'+VERSION,release_version=VERSION)
    w.write_json(output/'gameplay_profile.json',recipe);w.write_json(output/'appearance.json',log)
    print(json.dumps({'path':str(path),'sha256':log['rom_sha256']}),flush=True)
    return path


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--source',type=Path,default=ROOT/'build/version-0.30.2-final/Versioned.nds')
    args=p.parse_args();generate(args.out,args.source)
