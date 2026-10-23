"""Exact v0.33.0 appearance post-pass: taller 2099 and neon scarlet webs."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import wos_tool as w, tasm_kit as kit, spider2099 as assets, spider2099_visual as visual
from tools.chapter_renewal_combat import asm
from tools.model_geometry import ModelGeometry

VERSION = '0.33.1'
DATE = '2026-10-23'
PARENT = '8c7d4c59fb8c75229fdbea8453028065d702ba89ee5725d687cfa06fd798543a'
PARENT_PATH = ROOT/'build/version-0.33.0-final/Versioned.nds'
SELECTOR_OFFSET = 1441696
ZERO_TAIL = 1624
WEB_COLOR = 0x147F  # RGB555 (31, 3, 5): bright scarlet.


def selector_source(at, metadata):
    source = visual.selector_source(at, metadata)
    return source.replace('    done:', '''
        cmp r7,#1
        bne done
        mov r0,#0x1b
        adr r1,height_scale
        mov r2,#3
        bl #0x01ffc004
    done:''').replace('    ram_low:',
        '    height_scale: .word 0x1000,0x1200,0x1000\n    ram_low:')


def colors_source():
    return f'''
        b line_color
        b effect_color
    line_color:
        push {{r1,r2,r12}}
        mrs r12,cpsr
        mov r2,r0
        ldr r0,white
        b select_color
    effect_color:
        push {{r1,r2,r12}}
        mrs r12,cpsr
        mov r2,r0
        ldr r0,native_effect
    select_color:
        ldr r1,[r2,#0x34]
        cmp r1,#1
        ldreq r0,scarlet
        msr cpsr_f,r12
        pop {{r1,r2,r12}}
        bx lr
    white: .word 0x7fff
    native_effect: .word 0x5967
    scarlet: .word {WEB_COLOR}
    '''


def apply_rom(rom):
    if w.sha256(rom) != PARENT:
        raise ValueError('2099 presence requires exact published v0.33.0')
    header = w.parse_header(rom)
    arm = rom[header['arm9_offset']:header['arm9_offset']+header['arm9_size']]
    new = bytearray(arm)
    names, blobs = assets.resources(rom)
    shared = blobs[names.index('spd.nsbmd')]
    g = ModelGeometry.parse(shared)
    metadata = dict(model_size=w.u32(shared, g.model),
        metadata_offset=len(shared)-visual.TRAILER_SIZE-g.model,
        shape_offset=g.shapes[0].header-g.model, material_offset=visual.material(shared)-g.model)
    at = kit.TARGET+SELECTOR_OFFSET-kit.SOURCE
    expected = asm(visual.selector_source(at, metadata), at)
    code = asm(selector_source(at, metadata), at)
    if arm[SELECTOR_OFFSET:SELECTOR_OFFSET+len(expected)] != expected or any(
            arm[SELECTOR_OFFSET+len(expected):SELECTOR_OFFSET+len(code)]):
        raise ValueError('Published visual adapter or its unused tail differs')
    new[SELECTOR_OFFSET:SELECTOR_OFFSET+len(code)] = code
    color_offset = len(arm)-36-ZERO_TAIL
    color_at = kit.TARGET+color_offset-kit.SOURCE
    colors = asm(colors_source(), color_at)
    if len(colors) > ZERO_TAIL or any(arm[color_offset:color_offset+len(colors)]):
        raise ValueError('2099 color adapter tail is occupied')
    new[color_offset:color_offset+len(colors)] = colors
    getters = (0x0205F838, 0x0205F37C)
    for index, site in enumerate(getters):
        if struct.unpack_from('<3I', arm, site-kit.BASE) != (0xE59F0000, 0xE12FFF1E, (0x7FFF, 0x5967)[index]):
            raise ValueError('Native player web color getter differs')
        struct.pack_into('<I', new, site-kit.BASE, kit.branch(site, color_at+4*index))
    from tools.qol_suits_menu import StringSlots
    import mod
    _, glob, _ = mod.load_clean()
    offsets, native_names, _ = w.parse_glob(glob)
    for name in ('American.strings', 'English.strings'):
        i = names.index(name)
        n = native_names.index(name)
        raw = StringSlots(glob[offsets[n]:offsets[n+1]]).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}'})
        if len(raw) > len(blobs[i]):
            raise ValueError('Appearance version labels must fit the parent text resource')
        blobs[i] = raw + blobs[i][len(raw):]
    result = w.rebuild_rom(rom, {'Glob.bin': w.pack_glob(names, blobs)})
    result, _ = kit.replace_arm9(result, bytes(new))
    report = dict(version=VERSION, parent_sha256=PARENT, rom_sha256=w.sha256(result), arm9_sha256=w.sha256(new),
        height_scale_q12=[4096, 4608, 4096], height_increase_percent=12.5, web_color_rgb555=WEB_COLOR,
        selector=dict(address=at, source_offset=SELECTOR_OFFSET, bytes=len(code), metadata=metadata),
        colors=dict(address=color_at, source_offset=color_offset, bytes=len(colors), getters=list(getters)),
        modified_resources=['American.strings', 'English.strings'], allocation_bytes=0,
        scope='2099 render height and native line/web-effect tint only; native collisions, movement, rig, motion, mesh, textures, purchases, skills, rooms, audio and save format preserved. Red keeps native height and both original web colors.')
    from tools import release_info
    pin = release_info.PROFILE_INFO.get('tasm-v'+VERSION, {})
    for key in ('rom_sha256', 'arm9_sha256'):
        if pin.get(key) and pin[key] != report[key]:
            raise ValueError('2099 presence differs from immutable release pin')
    return result, report


def generate(output, source=PARENT_PATH):
    source, output = Path(source), Path(output)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):
        raise ValueError('Candidates belong in build/')
    result, report = apply_rom(source.read_bytes())
    path = output/'Versioned.nds'
    validation = w.validate_rom(result, target=True)
    meta = json.loads(source.with_suffix('.build.json').read_text(encoding='utf-8'))
    ge = next(e for e in validation['nitrofs'] if e['name'] == 'Glob.bin')
    meta.update(spider2099_presence=report, release_version=VERSION, release_date=DATE,
        output_rom_sha256=w.sha256(result), output=str(path.resolve()), rom_size=len(result),
        used_rom_size=validation['header']['used_rom_size'], nitrofs=validation['nitrofs'],
        header_crc16=validation['header']['header_crc16'], output_glob_sha256=w.sha256(result[ge['start']:ge['end']]))
    w.atomic_write(path, result, sources=(source,))
    w.write_json(path.with_suffix('.build.json'), meta)
    w.write_json(output/'changes.json', report)
    print(json.dumps(dict(path=str(path), sha256=report['rom_sha256'])), flush=True)
    return path


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--source', type=Path, default=PARENT_PATH)
    a = p.parse_args()
    generate(a.out, a.source)
