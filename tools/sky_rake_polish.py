"""Exact v0.35.0 post-pass: connected Sky Rake motion and moderate Black prices."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import wos_tool as w, tasm_kit as kit, spider2099 as assets
from tools import sky_rake as parent, sky_rake_polish_art as art

PARENT = '65dc457f346e071cd9755e3d67db69c9be09cc99392725eee52c5b1512c0aab5'
PARENT_PATH = ROOT/'build/version-0.35.0-final/Versioned.nds'
VERSION, DATE = '0.35.1', '2026-10-25'
PLANNED_PRICES = (75, 125, 150, 150, 200, 225, 125, 100, 150, 150, 200, 225, 275, 300)
PRICES = PLANNED_PRICES[:8]+(PLANNED_PRICES[9],)


def apply_rom(rom):
    if w.sha256(rom) != PARENT:
        raise ValueError('Sky Rake polish requires exact published v0.35.0')
    h = w.parse_header(rom)
    arm = rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    new = bytearray(arm)
    pointer = w.u32(arm, parent.hunter_kit.BLACK_POINTER)
    off = kit.SOURCE+pointer-kit.TARGET
    if w.u32(arm, parent.hunter_kit.BLACK_COUNT) != 9 or tuple(
            w.u32(arm, off+i*32+28) for i in range(9)) != parent.PRICES:
        raise ValueError('Published nine-row Black shop differs')
    for i, price in enumerate(PRICES):
        struct.pack_into('<I', new, off+i*32+28, price)
    names, blobs = assets.resources(rom)
    before = tuple(blobs)
    from tools.animation_rig import AnimationRig
    for name, blob in art.resources(names, blobs,
            AnimationRig.parse(blobs[names.index('spd.nsbmd')]).parents).items():
        blobs[names.index(name)] = blob
    from tools.qol_suits_menu import StringSlots
    import mod
    _, glob, _ = mod.load_clean()
    offsets, native_names, _ = w.parse_glob(glob)
    for name in ('American.strings', 'English.strings'):
        i, n = names.index(name), native_names.index(name)
        raw = StringSlots(glob[offsets[n]:offsets[n+1]]).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}'})
        blobs[i] = raw+bytes((len(before[i])-len(raw)) % 4)
    changed = [n for n, a, b in zip(names, before, blobs) if a != b]
    if set(changed) != {'American.strings', 'English.strings',
                       *(f'zz_S35_Air{i}.sca' for i in range(1, 5))}:
        raise ValueError('Unexpected Sky Rake polish resource scope')
    packed = w.pack_glob(names, blobs)
    ge = next(e for e in w.nitrofs_entries(rom) if e['name'] == 'Glob.bin')
    growth = max(0, w.align_up(len(packed)-ge['size']))
    staged = rom
    if growth:
        if h['used_rom_size']+growth > len(rom) or any(x not in (0, 255) for x in rom[-growth:]):
            raise ValueError('Insufficient verified cart padding')
        staged = bytearray(rom[:ge['end']]+bytes(growth)+rom[ge['end']:-growth])
        for e in w.nitrofs_entries(rom):
            if e['start'] >= ge['end']:
                struct.pack_into('<2I', staged, h['fat_offset']+e['id']*8, e['start']+growth, e['end']+growth)
        struct.pack_into('<I', staged, 0x80, h['used_rom_size']+growth)
        struct.pack_into('<H', staged, 0x15e, w.crc16(staged[:0x15e]))
    result = w.rebuild_rom(bytes(staged), {'Glob.bin': packed})
    result, _ = kit.replace_arm9(result, bytes(new))
    w.validate_rom(result, target=True)
    report = dict(version=VERSION, parent_sha256=PARENT, rom_sha256=w.sha256(result),
        arm9_sha256=w.sha256(new), modified_resources=changed, samples=[c.samples for c in art.CLIPS],
        black_prices=dict(previous=list(parent.PRICES), current=list(PRICES),
            current_total=sum(PRICES), planned_fourteen=list(PLANNED_PRICES), planned_total=sum(PLANNED_PRICES)),
        shop_source_offset=off, nitrofs_relocation_bytes=growth,
        runtime_contacts_events_32k_kit_original_bindings_rooms_audio_save_unchanged=True)
    from tools import release_info
    for key in ('rom_sha256', 'arm9_sha256'):
        pin = release_info.PROFILE_INFO.get('tasm-v'+VERSION, {}).get(key)
        if pin and pin != report[key]:
            raise ValueError('Sky Rake polish differs from immutable release pin')
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
    meta.update(sky_rake_polish=report, release_version=VERSION, release_date=DATE,
        output_rom_sha256=w.sha256(result), output=str(path.resolve()),
        rom_size=len(result), used_rom_size=validation['header']['used_rom_size'],
        nitrofs=validation['nitrofs'], header_crc16=validation['header']['header_crc16'],
        output_glob_sha256=w.sha256(result[ge['start']:ge['end']]))
    w.atomic_write(path, result, sources=(source,))
    w.write_json(path.with_suffix('.build.json'), meta)
    recipe = json.loads((ROOT/'reference/gameplay_profile.json').read_text(encoding='utf-8'))
    recipe.update(profile='tasm-v'+VERSION, release_version=VERSION)
    w.write_json(output/'gameplay_profile.json', recipe)
    w.write_json(output/'changes.json', report)
    print(json.dumps(dict(path=str(path), sha256=report['rom_sha256'])), flush=True)
    return path


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--source', type=Path, default=PARENT_PATH)
    a = p.parse_args()
    generate(a.out, a.source)
