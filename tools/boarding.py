"""Exact v0.37.0 post-pass: purchased 2099 Boarding and Wing Ripper."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import wos_tool as w, tasm_kit as kit, spider2099 as assets, oscorp_resources
from tools import hunter_kit, web_yank_combo, midnight_voltage as extension, boarding_art as art
from tools.assemble_tasm_kit import literal_errors, native_branch_errors, self_branch_errors
from tools.chapter_renewal_combat import asm
from tools.crane_row import target

PARENT = 'c5ab085a749065a5d180f340086df66de1df67598c3b920c3a21b639928b93c6'
PARENT_PATH = ROOT/'build/version-0.37.0-final/Versioned.nds'
VERSION, DATE = '0.38.0', '2026-10-28'
BIT, EVENT, PRICE = 88, 397, 275


def source(values):
    text = Path(__file__).with_suffix('.s').read_text(encoding='utf-8')
    native = Path(hunter_kit.__file__).with_suffix('.s').read_text(encoding='utf-8')
    owned = native[native.index('owned:\n'):native.index('xy:\n')]
    owned = owned.replace('bl ram_ok', 'bl SHARED_RAM_OK')
    owned = owned.replace('tst r1,#0x80000', 'tst r1,#0x1000000')
    from tools import reel_in
    shared = Path(reel_in.__file__).with_suffix('.s').read_text(encoding='utf-8')
    text += '\n'+shared[shared.index('link:'):shared.index('select_target:')]
    text += '\n'+shared[shared.index('clamp:'):shared.index('cleanup:')]
    line = native[native.index('line_make:'):native.index('unlink_target:')].replace('bl xy', 'bl SHARED_XY')
    text += '\n'+line+'\n'+owned+'\n .ltorg\n'
    for key in sorted(values, key=len, reverse=True):
        text = text.replace(key, f'0x{values[key]:08x}')
    return text


def runtime(at, values):
    text = source(values)
    code = asm(text, at)
    errors = literal_errors(code, text)+native_branch_errors(code, text, at)+self_branch_errors(code)
    if errors:
        raise ValueError('Boarding assembly: '+str(errors))
    return code


def apply_rom(rom):
    if w.sha256(rom) != PARENT:
        raise ValueError('Boarding requires exact published v0.37.0')
    from tools import release_info
    h = w.parse_header(rom)
    arm = rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    if w.sha256(arm) != release_info.PROFILE_INFO['tasm-v0.37.0']['arm9_sha256']:
        raise ValueError('Published parent ARM9 differs')
    meta = json.loads(PARENT_PATH.with_suffix('.build.json').read_text(encoding='utf-8'))
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
            raise ValueError('English/American text counts differ')
        raw = StringSlots(glob[offsets[n]:offsets[n+1]]).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}'},
            appended=('Boarding', 'Boarding',
                'Jump into a heavy foe holding toward it.\n\ue601 rakes; \ue600 rips and kicks off.\n\ue604 releases. Boss attacks shake you off.'))
        blobs[i] = raw+bytes((len(before[i])-len(raw)) % 4)
    if sum(map(len, blobs)) % 4:
        extras['zz_B38_align.bin'] = bytes(-sum(map(len, blobs)) % 4)
    names, blobs = oscorp_resources.append_resources(names, blobs, extras)
    rt = extension.Runtime.__new__(extension.Runtime)
    rt.rom, rt.header, rt.arm, rt.new = rom, h, arm, bytearray(arm)
    rt.end, rt.data = len(arm)-36, bytearray()
    rt.start = kit.TARGET+rt.end-kit.SOURCE
    state = rt.alloc(bytes(256))
    old_shop = w.u32(arm, hunter_kit.BLACK_POINTER)
    if w.u32(arm, hunter_kit.BLACK_COUNT) != 11:
        raise ValueError('Published Black shop count differs')
    off = kit.SOURCE+old_shop-kit.TARGET
    shop = bytearray(arm[off:off+11*32])
    prices = release_info.PROFILE_INFO['tasm-v0.37.0']['black_prices']
    if tuple(w.u32(shop, i*32+28) for i in range(11)) != prices:
        raise ValueError('Published Black prices differ')
    shop.extend(struct.pack('<8I', EVENT, kit.NO_EVENT, kit.NO_EVENT, text_id, text_id+1, text_id+2, 1, PRICE))
    shop_at = rt.alloc(shop)
    struct.pack_into('<I', rt.new, hunter_kit.BLACK_POINTER, shop_at)
    struct.pack_into('<I', rt.new, hunter_kit.BLACK_COUNT, 12)
    sites = (0x020b4888, 0x02070484, 0x02073b60, 0x0209543c)
    old = [w.u32(arm, site-kit.BASE) for site in sites]
    if any(word >> 24 != 0xea for word in old):
        raise ValueError('Published think/animation/update/effect hook differs')
    shared = meta['hunter_kit']['runtime']
    entry = rt.alloc()
    yank = meta['web_yank_combo']['runtime']
    yank_source = web_yank_combo.source()
    for key in sorted(yank['values'], key=len, reverse=True):
        yank_source = yank_source.replace(key, f"0x{yank['values'][key]:08x}")
    exports = asm(yank_source+'\n.word clear_record', yank['entry'])
    if exports[:-4] != web_yank_combo.runtime(yank['entry'], yank['values']):
        raise ValueError('Published Web Yank helper differs')
    values = dict(STATE=state, OLD_THINK=target(sites[0], old[0]),
        OLD_ANIMATION=target(sites[1], old[1]), OLD_UPDATE=target(sites[2], old[2]),
        OLD_EFFECT=target(sites[3], old[3]), YANK_STATE=yank['state'],
        REEL_STATE=meta['reel_in']['runtime']['state'], METEOR_STATE=meta['meteor_catch']['runtime']['state'],
        YANK_RECORDS=yank['records'], YANK_CLEAR=struct.unpack('<I', exports[-4:])[0],
        **{part.upper()+'_'+ext.upper(): names.index('zz_B38_'+part+'.'+ext)
           for part in art.PARTS for ext in ('sca', 'gmb', 'gab')},
        **{part.upper()+'_LEFT_SCA': names.index('zz_B38_'+part+'Left.sca') for part in art.PARTS},
        BOSS_CONFIG=meta['creature_forge']['creatures']['conductor']['config'],
        **{key.upper(): val for key, val in hunter_kit.kit_symbols().items()},
        **web_yank_combo.shared_symbols(shared['entry'], shared['values']))
    code = runtime(entry, values)
    rt.data.extend(code)
    for i, site in enumerate(sites):
        rt.hook(site, entry+4*i)
    if w.u32(arm, oscorp_resources.COUNT_OFFSET) != len(before):
        raise ValueError('Published resource count differs')
    struct.pack_into('<I', rt.new, oscorp_resources.COUNT_OFFSET, len(names))
    result = rt.finish()
    hh = w.parse_header(result)
    new = result[hh['arm9_offset']:hh['arm9_offset']+hh['arm9_size']]
    packed = w.pack_glob(names, blobs)
    ge = next(e for e in w.nitrofs_entries(result) if e['name'] == 'Glob.bin')
    growth = w.align_up(len(packed)-ge['size'])
    if growth <= 0 or hh['used_rom_size']+growth > len(result) or any(x not in (0, 255) for x in result[-growth:]):
        raise ValueError('Insufficient verified cart padding')
    staged = bytearray(result[:ge['end']]+bytes(growth)+result[ge['end']:-growth])
    for e in w.nitrofs_entries(result):
        if e['start'] >= ge['end']:
            struct.pack_into('<2I', staged, hh['fat_offset']+e['id']*8, e['start']+growth, e['end']+growth)
    struct.pack_into('<I', staged, 0x80, hh['used_rom_size']+growth)
    struct.pack_into('<H', staged, 0x15e, w.crc16(staged[:0x15e]))
    result = w.rebuild_rom(bytes(staged), {'Glob.bin': packed})
    w.validate_rom(result, target=True)
    changed = [n for n, a, b in zip(names, before, blobs) if a != b]
    if set(changed) != {'American.strings', 'English.strings', 'GlobFiles.txt'}:
        raise ValueError('Unexpected Boarding resource scope')
    report = dict(version=VERSION, parent_sha256=PARENT, rom_sha256=w.sha256(result), arm9_sha256=w.sha256(new),
        modified_resources=changed, added_resources=list(extras), text_id=text_id,
        runtime=dict(start=rt.start, state=state, shop=shop_at, entry=entry, values=values, bytes=len(code),
            source_offset=rt.end, allocation_bytes=w.align_up(len(rt.data), 0x1000),
            hooks=[dict(site=s, old=o, target=entry+4*i) for i, (s, o) in enumerate(zip(sites, old))]),
        ownership=dict(event=EVENT, bit=BIT, parent_event=None, price=PRICE),
        black_prices=[*prices, PRICE], samples=[c.samples for c in art.CLIPS],
        binding='Hold toward a heavy foe during a jump or heavy zip; Y rakes, A rips, R releases',
        rake_damage_q12=0x1000, rip_damage_q12=0x2000,
        velocity_limits_q12=dict(follow_x=0x4000, follow_y=0x4000, kick_x=0x2800, kick_y=0x4000),
        nitrofs_relocation_bytes=growth, player_kit_32k_unchanged=True,
        native_assets_bindings_rooms_audio_save_format_and_existing_purchases_unchanged=True)
    pin = release_info.PROFILE_INFO.get('tasm-v'+VERSION, {})
    for key in ('rom_sha256', 'arm9_sha256'):
        if pin.get(key) and pin[key] != report[key]:
            raise ValueError('Boarding output differs from immutable release pin')
    return result, report


def generate(output, source_path=PARENT_PATH):
    output, source_path = Path(output), Path(source_path)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):
        raise ValueError('Candidates belong in build/')
    result, report = apply_rom(source_path.read_bytes())
    path = output/'Versioned.nds'
    validation = w.validate_rom(result, target=True)
    meta = json.loads(source_path.with_suffix('.build.json').read_text(encoding='utf-8'))
    ge = next(e for e in validation['nitrofs'] if e['name'] == 'Glob.bin')
    meta.update(boarding=report, release_version=VERSION, release_date=DATE, output_rom_sha256=w.sha256(result),
        output=str(path.resolve()), rom_size=len(result), used_rom_size=validation['header']['used_rom_size'],
        nitrofs=validation['nitrofs'], header_crc16=validation['header']['header_crc16'],
        output_glob_sha256=w.sha256(result[ge['start']:ge['end']]), verified_resource_count=len(assets.resources(result)[0]))
    w.atomic_write(path, result, sources=(source_path,))
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
