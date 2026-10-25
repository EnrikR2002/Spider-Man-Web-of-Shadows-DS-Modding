"""Exact v0.34.2 post-pass: purchased Black Sky Rake and a 1,600-XP Hunter budget."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import wos_tool as w, tasm_kit as kit, spider2099 as assets, oscorp_resources
from tools import sky_rake_art as art, hunter_kit
from tools.crane_row import target
from tools.chapter_renewal_combat import asm
from tools.assemble_tasm_kit import literal_errors, native_branch_errors, self_branch_errors

PARENT = '1068aba45653cbd300925b140320724e37d145433ed18fb3f06d8001e9625098'
PARENT_PATH = ROOT/'build/version-0.34.2-final/Versioned.nds'
DEFAULT_ROM = ROOT/'original/Spider-Man - Web of Shadows (USA) (En,Fr).nds'
VERSION, DATE = '0.35.0', '2026-10-25'
BIT, EVENT, PRICE = 85, 394, 100
PLANNED_PRICES = (50, 75, 100, 100, 125, 150, 75, 75, 100, 100, 125, 150, 175, 200)
PRICES = PLANNED_PRICES[:8]+(PRICE,)


def runtime(at, values):
    source = Path(__file__).with_suffix('.s').read_text(encoding='utf-8')
    for key in sorted(values, key=len, reverse=True):
        source = source.replace(key, f'0x{values[key]:08x}')
    code = asm(source, at)
    errors = literal_errors(code, source)+native_branch_errors(code, source, at)+self_branch_errors(code)
    if errors:
        raise ValueError('Sky Rake assembly: '+str(errors))
    return code


def apply_rom(rom):
    if w.sha256(rom) != PARENT:
        raise ValueError('Sky Rake requires exact published v0.34.2')
    meta = json.loads(PARENT_PATH.with_suffix('.build.json').read_text(encoding='utf-8'))
    h = w.parse_header(rom)
    arm = rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    new = bytearray(arm)
    names, blobs = assets.resources(rom)
    before = tuple(blobs)
    from tools.animation_rig import AnimationRig
    extras = art.resources(names, blobs, AnimationRig.parse(blobs[names.index('spd.nsbmd')]).parents)
    from tools.qol_suits_menu import StringSlots, slot_count
    import mod
    _, glob, _ = mod.load_clean()
    offsets, native_names, _ = w.parse_glob(glob)
    text_id = slot_count(blobs[names.index('American.strings')])
    for name in ('American.strings', 'English.strings'):
        i, n = names.index(name), native_names.index(name)
        if slot_count(blobs[i]) != text_id:
            raise ValueError('Supported English string counts differ')
        raw = StringSlots(glob[offsets[n]:offsets[n+1]]).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}'},
            appended=('Sky Rake', 'Sky Rake',
                'Air \ue601: four talon rakes, then a flip kick.\nKeep tapping to chain; kick pops foes up.\n\ue604 exits. Heavy foes take staggers.'))
        blobs[i] = raw+bytes((len(before[i])-len(raw)) % 4)
    if sum(map(len, blobs)) % 4:
        extras['zz_S35_align.bin'] = bytes(-sum(map(len, blobs)) % 4)
    names, blobs = oscorp_resources.append_resources(names, blobs, extras)
    if w.u32(arm, oscorp_resources.COUNT_OFFSET) != len(before):
        raise ValueError('Parent resource count differs')
    struct.pack_into('<I', new, oscorp_resources.COUNT_OFFSET, len(names))
    off = len(arm)-36-meta['web_yank_combo']['runtime']['remaining_zero_tail']
    if any(arm[off:-36]):
        raise ValueError('Published zero tail is occupied')
    start = kit.TARGET+off-kit.SOURCE
    pointer, count = hunter_kit.BLACK_POINTER, hunter_kit.BLACK_COUNT
    parent_shop = w.u32(arm, pointer)
    if (parent_shop, w.u32(arm, count)) != (meta['hunter_kit']['runtime']['shop'], 8):
        raise ValueError('Published eight-row Black shop differs')
    shop_off = kit.SOURCE+parent_shop-kit.TARGET
    shop = bytearray(arm[shop_off:shop_off+8*32])
    if tuple(w.u32(shop, 32*i+28) for i in range(8)) != (100, 200, 600, 400, 600, 800, 1000, 300):
        raise ValueError('Parent Black prices differ')
    for i, price in enumerate(PRICES[:8]):
        struct.pack_into('<I', shop, 32*i+28, price)
    shop.extend(struct.pack('<8I', EVENT, kit.NO_EVENT, kit.NO_EVENT, text_id, text_id+1, text_id+2, 1, PRICE))
    routes = b''.join(struct.pack('<3I', *(names.index(f'zz_S35_Air{i}.{ext}') for ext in ('sca', 'gmb', 'gab')))
                      for i in range(1, 5))
    entry = start+len(shop)+len(routes)
    sites = (0x02070484, 0x02078628, 0x020b7b18)
    old = [w.u32(arm, site-kit.BASE) for site in sites]
    if any(word >> 24 != 0xea for word in old):
        raise ValueError('Published animation/contact/air-blocker hooks differ')
    values = dict(ROUTES=start+len(shop), BOSS_CONFIG=meta['creature_forge']['creatures']['conductor']['config'],
        **{key: target(site, word) for key, site, word in zip(('OLD_ANIMATION', 'OLD_CONTACT', 'OLD_AIR'), sites, old)})
    code = runtime(entry, values)
    data = bytes(shop)+routes+code
    if off+len(data) > len(arm)-36:
        raise ValueError('Sky Rake exceeds the verified unused tail')
    new[off:off+len(data)] = data
    struct.pack_into('<I', new, pointer, start)
    struct.pack_into('<I', new, count, 9)
    for i, site in enumerate(sites):
        struct.pack_into('<I', new, site-kit.BASE, kit.branch(site, entry+4*i))
    changed = [n for n, a, b in zip(names, before, blobs) if a != b]
    if set(changed) != {'American.strings', 'English.strings', 'GlobFiles.txt'}:
        raise ValueError('Unexpected Sky Rake resource scope')
    packed = w.pack_glob(names, blobs)
    ge = next(e for e in w.nitrofs_entries(rom) if e['name'] == 'Glob.bin')
    growth = w.align_up(len(packed)-ge['size'])
    if growth <= 0 or h['used_rom_size']+growth > len(rom) or any(x not in (0, 255) for x in rom[-growth:]):
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
    report = dict(version=VERSION, parent_sha256=PARENT, rom_sha256=w.sha256(result), arm9_sha256=w.sha256(new),
        modified_resources=changed, added_resources=list(extras), text_id=text_id,
        runtime=dict(entry=entry, source_offset=off, block_start=start, bytes=len(code), block_bytes=len(data),
            values=values, shop=start, routes=start+len(shop), allocation_bytes=0,
            remaining_zero_tail=len(arm)-36-off-len(data),
            hooks=[dict(site=s, old=o, target=entry+4*i) for i, (s, o) in enumerate(zip(sites, old))]),
        ownership=dict(event=EVENT, bit=BIT, price=PRICE, previous_rows_owned_unchanged=True),
        black_prices=dict(previous=[100, 200, 600, 400, 600, 800, 1000, 300], current=list(PRICES),
            planned_fourteen=list(PLANNED_PRICES), planned_total=sum(PLANNED_PRICES)),
        samples=[c.samples for c in art.CLIPS], contact_samples=art.CONTACTS, nitrofs_relocation_bytes=growth,
        frozen_32k_kit_original_assets_bindings_rooms_audio_and_save_format_unchanged=True)
    from tools import release_info
    pin = release_info.PROFILE_INFO.get('tasm-v'+VERSION, {})
    for key in ('rom_sha256', 'arm9_sha256'):
        if pin.get(key) and pin[key] != report[key]:
            raise ValueError('Sky Rake differs from immutable release pin')
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
    meta.update(sky_rake=report, release_version=VERSION, release_date=DATE, output_rom_sha256=w.sha256(result),
        output=str(path.resolve()), rom_size=len(result), used_rom_size=validation['header']['used_rom_size'],
        nitrofs=validation['nitrofs'], header_crc16=validation['header']['header_crc16'],
        output_glob_sha256=w.sha256(result[ge['start']:ge['end']]), verified_resource_count=len(assets.resources(result)[0]))
    w.atomic_write(path, result, sources=(source,))
    w.write_json(path.with_suffix('.build.json'), meta)
    recipe = json.loads((ROOT/'reference/gameplay_profile.json').read_text(encoding='utf-8'))
    recipe.update(profile='tasm-v'+VERSION, release_version=VERSION)
    w.write_json(output/'gameplay_profile.json', recipe)
    w.write_json(output/'changes.json', report)
    print(json.dumps(dict(path=str(path), sha256=report['rom_sha256'], runtime=report['runtime'])), flush=True)
    return path


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--source', type=Path, default=PARENT_PATH)
    a = p.parse_args()
    generate(a.out, a.source)
