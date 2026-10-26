"""Exact v0.35.1 post-pass: keep the Sky Rake finisher's launch in front."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import wos_tool as w, tasm_kit as kit, spider2099 as assets, sky_rake
from tools.assemble_tasm_kit import literal_errors, native_branch_errors, self_branch_errors
from tools.chapter_renewal_combat import asm

PARENT = '76e6049eab8e511da388854c76c33a739649e6ea77ca08a99bc763fefaceae3f'
PARENT_PATH = ROOT/'build/version-0.35.1-final/Versioned.nds'
VERSION, DATE = '0.35.2', '2026-10-25'
BLX_R12, POST_BLX_LOAD = 0xe12fff3c, 0xe5940000


def direction(at, continuation):
    source = Path(__file__).with_suffix('.s').read_text(encoding='utf-8')
    source = source.replace('CONTINUATION', f'0x{continuation:08x}')
    code = asm(source, at)
    errors = literal_errors(code, source)+native_branch_errors(code, source, at)+self_branch_errors(code)
    if errors:
        raise ValueError('Sky Rake forward launch assembly: '+str(errors))
    return code


def apply_rom(rom):
    if w.sha256(rom) != PARENT:
        raise ValueError('Sky Rake front landing requires exact published v0.35.1')
    from tools import release_info
    parent = release_info.PROFILE_INFO['tasm-v0.35.1']
    h = w.parse_header(rom)
    arm = rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    if w.sha256(arm) != parent['arm9_sha256']:
        raise ValueError('Published v0.35.1 ARM9 differs')
    meta = json.loads(PARENT_PATH.with_suffix('.build.json').read_text(encoding='utf-8'))
    rt = meta['sky_rake']['runtime']
    base = sky_rake.runtime(rt['entry'], rt['values'])
    runtime_off = kit.SOURCE+rt['entry']-kit.TARGET
    block_end = rt['source_offset']+rt['block_bytes']
    if (runtime_off+len(base) != block_end or len(base) != rt['bytes']
            or arm[runtime_off:runtime_off+len(base)] != base
            or any(arm[block_end:-36])):
        raise ValueError('Published Sky Rake code or its guarded zero tail differs')
    hits = [i for i in range(0, len(base), 4)
            if w.u32(base, i) == BLX_R12 and i+8 <= len(base)
            and w.u32(base, i+4) == POST_BLX_LOAD]
    if len(hits) != 1 or rt['remaining_zero_tail'] < 64:
        raise ValueError('Expected the single guarded native hit callback and free tail')
    site_off = runtime_off+hits[0]+4
    helper_off = block_end
    site = kit.TARGET+site_off-kit.SOURCE
    helper = kit.TARGET+helper_off-kit.SOURCE
    code = direction(helper, site+4)
    if helper_off+len(code) > len(arm)-36 or any(arm[helper_off:helper_off+len(code)]):
        raise ValueError('Forward launch helper exceeds its verified zero tail')
    new_arm = bytearray(arm)
    struct.pack_into('<I', new_arm, site_off, kit.branch(site, helper))
    new_arm[helper_off:helper_off+len(code)] = code
    names, blobs = assets.resources(rom)
    before = tuple(blobs)
    from tools.qol_suits_menu import StringSlots, slot_count
    import mod
    _, glob, _ = mod.load_clean()
    offsets, native_names, _ = w.parse_glob(glob)
    counts = []
    for name in ('American.strings', 'English.strings'):
        i, n = names.index(name), native_names.index(name)
        counts.append(slot_count(blobs[i]))
        raw = StringSlots(glob[offsets[n]:offsets[n+1]]).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}'})
        blobs[i] = raw+bytes((len(before[i])-len(raw)) % 4)
    if counts[0] != counts[1]:
        raise ValueError('Supported English string counts differ')
    changed = [n for n, a, b in zip(names, before, blobs) if a != b]
    if set(changed) != {'American.strings', 'English.strings'}:
        raise ValueError('Unexpected Sky Rake forward-launch resource scope')
    result = w.rebuild_rom(rom, {'Glob.bin': w.pack_glob(names, blobs)})
    result, _ = kit.replace_arm9(result, bytes(new_arm))
    w.validate_rom(result, target=True)
    report = dict(version=VERSION, parent_sha256=PARENT, rom_sha256=w.sha256(result),
        arm9_sha256=w.sha256(new_arm), modified_resources=changed,
        launch=dict(native_kind=0x25, target_landing_offset_goal_q12=3*4096,
            initial_velocity='one-thirty-second of the difference from a three-unit forward landing goal',
            velocity_limit_q12=0x600, vertical_launch_unchanged=True,
            light_targets_only=True), helper=dict(site=site, site_offset=site_off,
            address=helper, source_offset=helper_off, bytes=len(code), allocation_bytes=0,
            remaining_zero_tail=len(arm)-36-block_end-len(code)),
        black_prices_ownership_contact_clock_original_binds_and_save_format_unchanged=True)
    pin = release_info.PROFILE_INFO.get('tasm-v'+VERSION, {})
    for key in ('rom_sha256', 'arm9_sha256'):
        if pin.get(key) and pin[key] != report[key]:
            raise ValueError('Sky Rake forward-launch output differs from release pin')
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
    meta.update(sky_rake_front=report, release_version=VERSION, release_date=DATE,
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
