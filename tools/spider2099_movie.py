"""Exact v0.30.1 appearance post-pass: cape-free Across the Spider-Verse 2099."""
from pathlib import Path
import argparse
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import spider2099 as first, spider2099_movie_art as art
from tools import spider2099_visual as visual, tasm_kit as kit, wos_tool as w
from tools.chapter_renewal_combat import asm
from tools.model_geometry import ModelGeometry

VERSION = '0.30.2'
DATE = '2026-10-22'
PARENT = '7286d0536b6e29d0ebdc355563c6ece8e974058534c9676024ee67928cae530c'
PARENT_PATH = ROOT / 'build/version-0.30.1-final/Versioned.nds'
CHANGED = ('American.strings', 'English.strings', 'spd.nsbmd', 'spdB.nsbtx')


def red_model(shared, native):
    """Remove the old Black stream/footer, restoring the original Red envelope."""
    g, n = ModelGeometry.parse(shared), ModelGeometry.parse(native)
    words = struct.unpack_from('<16I', shared, len(shared)-visual.TRAILER_SIZE)
    if shared[-visual.TRAILER_SIZE:-visual.TRAILER_SIZE+8] != visual.MAGIC:
        raise ValueError('Missing published shared appearance footer')
    end = g.shapes[0].header + words[6]
    if end != g.shapes[0].start + g.shapes[0].length:
        raise ValueError('Unexpected Red/Black list boundary')
    out = bytearray(shared[:end])
    for at, value in ((8, len(out)), (g.block+4, len(out)-g.block), (g.model, len(out)-g.model)):
        struct.pack_into('<I', out, at, value)
    out[g.model+36:g.model+64] = native[n.model+36:n.model+64]
    return bytes(out)


def replace_selector(rom, previous, metadata):
    """Rebind the existing cosmetic extension, preserving its code and heap size."""
    h = w.parse_header(rom)
    arm = rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    # v0.30.1 allocated the last 4 KiB exclusively for this bounded adapter.
    offset = len(arm) - 36 - 4096
    at = kit.TARGET + offset - kit.SOURCE
    g = ModelGeometry.parse(previous)
    old = {'model_size': w.u32(previous, g.model),
           'metadata_offset': len(previous)-visual.TRAILER_SIZE-g.model,
           'shape_offset': g.shapes[0].header-g.model,
           'material_offset': visual.material(previous)-g.model}
    expected = asm(visual.selector_source(at, old), at)
    code = asm(visual.selector_source(at, metadata), at)
    if arm[offset:offset+len(expected)] != expected or len(code) != len(expected):
        raise ValueError('Published cosmetic adapter differs; explicit merge required')
    new = bytearray(arm)
    new[offset:offset+len(code)] = code
    if new[kit.SOURCE:kit.SOURCE+kit.RESERVE] != arm[kit.SOURCE:kit.SOURCE+kit.RESERVE]:
        raise ValueError('Movie appearance changed the 32 KiB player kit')
    result, _ = kit.replace_arm9(rom, bytes(new))
    return result, {'code_address': at, 'arm9_source_offset': offset, 'code_bytes': len(code),
        'code_sha256': w.sha256(code), 'new_allocation_bytes': 0,
        'abi': 'Existing guarded selector with updated model-size/footer literals only; registers/CPSR and gameplay kit preserved.'}


def apply_rom(rom):
    if w.sha256(rom) != PARENT:
        raise ValueError('Movie 2099 requires exact published v0.30.1')
    import mod
    _, glob, manifest = mod.load_clean()
    entries = {e['name']: e for e in manifest['entries']}

    def native(name):
        e = entries[name]
        return glob[e['offset']:e['offset']+e['size']]

    names, blobs = first.resources(rom)
    before = tuple(blobs)
    previous = blobs[names.index('spd.nsbmd')]
    black, model_report = art.model(native('spdB.nsbmd'))
    indices, palette, paint_report = art.artwork(native('spdB.nsbmd'))
    black_tex = art.texture(native('spdB.nsbtx'), indices, palette)
    red = red_model(previous, native('spd.nsbmd'))
    shared, shared_report = visual.shared_model(red, black, blobs[names.index('spd.nsbtx')], black_tex)
    blobs[names.index('spd.nsbmd')] = shared
    blobs[names.index('spdB.nsbtx')] = black_tex
    from tools.qol_suits_menu import StringSlots
    for name in ('American.strings', 'English.strings'):
        i = names.index(name)
        data = StringSlots(native(name)).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}'})
        blobs[i] = data + bytes(-len(data) % 4)
    changed = [n for n, a, b in zip(names, before, blobs) if a != b]
    if sorted(changed) != sorted(CHANGED):
        raise ValueError('Movie appearance changed unexpected resources')
    result, runtime = replace_selector(rom, previous, shared_report)
    result = w.rebuild_rom(result, {'Glob.bin': w.pack_glob(names, blobs)}, legacy_gaps=True)
    h = w.parse_header(result)
    report = {'version': VERSION, 'parent_sha256': PARENT, 'rom_sha256': w.sha256(result),
        'arm9_sha256': w.sha256(result[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]),
        'modified_resources': changed, 'model': model_report, 'paint': paint_report,
        'shared_model': shared_report, 'cosmetic_draw_selector': runtime,
        'resource_hashes': {n: w.sha256(blobs[names.index(n)]) for n in CHANGED},
        'scope': 'Black appearance only: cape geometry/atlas removed, movie-inspired sculpt and markings. Native rig/SBC/animations/physics/controls/purchases, Red list/texture, kit, rooms/audio and battery contract preserved.'}
    from tools import release_info
    pin = release_info.PROFILE_INFO.get('tasm-v'+VERSION, {})
    for key in ('rom_sha256', 'arm9_sha256'):
        if pin.get(key) and pin[key] != report[key]:
            raise ValueError('Movie appearance differs from immutable release pin')
    return result, report


def generate(output, source=PARENT_PATH, previews=False):
    output, source = Path(output), Path(source)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):
        raise ValueError('Candidates belong in build/')
    result, report = apply_rom(source.read_bytes())
    path = output/'Versioned.nds'
    meta = json.loads(source.with_suffix('.build.json').read_text())
    validation = w.validate_rom(result, target=True)
    ge = next(e for e in validation['nitrofs'] if e['name'] == 'Glob.bin')
    meta.update(spider2099_movie=report, release_version=VERSION, release_date=DATE,
        output_rom_sha256=w.sha256(result), output=str(path.resolve()), rom_size=len(result),
        used_rom_size=validation['header']['used_rom_size'], nitrofs=validation['nitrofs'],
        header_crc16=validation['header']['header_crc16'], output_glob_sha256=w.sha256(result[ge['start']:ge['end']]))
    w.atomic_write(path, result, sources=(source,))
    w.write_json(path.with_suffix('.build.json'), meta)
    recipe = json.loads((ROOT/'reference/gameplay_profile.json').read_text())
    recipe.update(profile='tasm-v'+VERSION, release_version=VERSION)
    w.write_json(output/'gameplay_profile.json', recipe)
    w.write_json(output/'appearance.json', report)
    if previews:
        from tools import spider2099_art
        names, blobs = first.resources(result)
        display = visual.selected_model(blobs[names.index('spd.nsbmd')], 1)
        for yaw in (0, 45, 90, 180):
            spider2099_art.render(display, blobs[names.index('spdB.nsbtx')], output/f'model-{yaw}.png', yaw)
    print(json.dumps({'path': str(path), 'sha256': report['rom_sha256']}), flush=True)
    return path


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--source', type=Path, default=PARENT_PATH)
    p.add_argument('--previews', action='store_true')
    args = p.parse_args()
    generate(args.out, args.source, args.previews)
