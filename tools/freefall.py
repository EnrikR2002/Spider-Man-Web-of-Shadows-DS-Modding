"""Exact v0.40.0 post-pass for Miguel's purchased, height-scaled Freefall."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import freefall_art as art, midnight_voltage, oscorp_resources, release_info
from tools import spider2099, tasm_kit as kit, wos_tool as w
from tools.animation_rig import AnimationRig
from tools.crane_row import target
from tools.qol_suits_menu import StringSlots


VERSION, DATE = '0.41.0', '2026-11-06'
PARENT = release_info.PROFILE_INFO['tasm-v0.40.0']
PARENT_PATH = ROOT / 'build/version-0.40.0-final/Versioned.nds'
HOOKS = (
    (0x02070484, 0xea040e06, False),
    (0x020c28d8, 0xebfeef3b, True),
    (0x0207112c, 0xe58dc0a8, False),
    (0x02078628, 0xea03e160, False),
    (0x020b4888, 0xea02fd04, False),
)
TEXT = {
    50: f'TASM v{VERSION}\nPress a button to start',
    74: f'Options v{VERSION}',
    210: 'Freefall',
    211: 'Freefall',
    212: 'Air Down + \ue600: dive talons-first.\nHigh falls hit wider and harder.\nGrounded foes bounce. \ue604 lets go.',
}


def runtime(at, values):
    from tools.crane_arm import assembled

    source = Path(__file__).with_suffix('.s').read_text(encoding='utf-8')
    for key, value in values.items():
        source = source.replace(key, f'0x{value:08x}')
    return assembled(source, at)


def apply_rom(rom):
    if w.sha256(rom) != PARENT['rom_sha256']:
        raise ValueError('Freefall requires exact published v0.40.0')
    header = w.parse_header(rom)
    arm = rom[header['arm9_offset']:header['arm9_offset'] + header['arm9_size']]
    if w.sha256(arm) != PARENT['arm9_sha256']:
        raise ValueError('Unexpected v0.40.0 ARM9')
    names, blobs = spider2099.resources(rom)
    before = tuple(blobs)
    parents = AnimationRig.parse(blobs[names.index('spd.nsbmd')]).parents
    extras = art.resources(names, blobs, parents)

    import mod
    _, clean, manifest = mod.load_clean()
    for name in ('American.strings', 'English.strings'):
        index = names.index(name)
        entry = next(e for e in manifest['entries'] if e['name'] == name)
        slots = StringSlots(clean[entry['offset']:entry['offset'] + entry['size']])
        raw = slots.grown(blobs[index], TEXT)
        blobs[index] = raw + bytes((len(before[index]) - len(raw)) % 4)
    names, blobs = oscorp_resources.append_resources(names, blobs, extras)
    changed = [name for name, old, new in zip(names, before, blobs) if old != new]
    if set(changed) != {'American.strings', 'English.strings', 'GlobFiles.txt'}:
        raise ValueError('Unexpected Freefall resource scope')

    rt = midnight_voltage.Runtime.__new__(midnight_voltage.Runtime)
    rt.rom, rt.header, rt.arm, rt.new = rom, header, arm, bytearray(arm)
    rt.end, rt.data = len(arm) - 36, bytearray()
    rt.start = kit.TARGET + rt.end - kit.SOURCE
    state = rt.alloc(bytes(16))
    start = rt.alloc()
    values = dict(STATE=state, BOSS_CONFIG=0x0215a52c,
                  NATIVE_DIVE=names.index(art.TEMPLATES[0]), NATIVE_LAND=names.index(art.TEMPLATES[1]),
                  DIVE_SCA=names.index(art.NAMES[0]), LAND_SCA=names.index(art.NAMES[1]),
                  OLD_ANIMATION=target(*HOOKS[0][:2]), OLD_CONTACT=target(*HOOKS[3][:2]),
                  OLD_THINK=target(*HOOKS[4][:2]))
    code = runtime(start, values)
    rt.data.extend(code)
    hooks = []
    for index, (site, expected, link) in enumerate(HOOKS):
        if w.u32(arm, site - kit.BASE) != expected:
            raise ValueError(f'Freefall hook preimage differs at {site:#x}')
        entry = start + 4 * index
        rt.hook(site, entry, link=link)
        hooks.append(dict(site=site, old=expected, target=entry, link=link))
    if w.u32(arm, oscorp_resources.COUNT_OFFSET) != len(before):
        raise ValueError('Unexpected native resource count')
    struct.pack_into('<I', rt.new, oscorp_resources.COUNT_OFFSET, len(names))
    result = rt.finish()
    header = w.parse_header(result)
    arm = result[header['arm9_offset']:header['arm9_offset'] + header['arm9_size']]

    # Slide the occupied Glob gap and its successors before filling the new space.
    packed = w.pack_glob(names, blobs)
    entries = w.nitrofs_entries(result)
    glob = next(e for e in entries if e['name'] == 'Glob.bin')
    growth = w.align_up(len(packed) - glob['size'])
    if (growth <= 0 or header['used_rom_size'] + growth > len(result)
            or any(value not in (0, 255) for value in result[-growth:])):
        raise ValueError('Insufficient verified cart padding for Freefall')
    staged = bytearray(result[:glob['end']] + bytes(growth) + result[glob['end']:-growth])
    for entry in entries:
        if entry['start'] >= glob['end']:
            struct.pack_into('<2I', staged, header['fat_offset'] + entry['id'] * 8,
                             entry['start'] + growth, entry['end'] + growth)
    struct.pack_into('<I', staged, 0x80, header['used_rom_size'] + growth)
    struct.pack_into('<H', staged, 0x15e, w.crc16(staged[:0x15e]))
    result = w.rebuild_rom(bytes(staged), {'Glob.bin': packed})
    w.validate_rom(result, target=True)
    report = dict(version=VERSION, parent_sha256=PARENT['rom_sha256'],
                  rom_sha256=w.sha256(result), arm9_sha256=w.sha256(arm),
                  modified_resources=changed, added_resources=list(extras),
                  runtime=dict(state=state, entry=start, hooks=hooks, values=values, bytes=len(code),
                               allocation_bytes=w.align_up(len(rt.data), 0x1000)),
                  ownership=dict(event=331, bit=22, price=150), samples=[c.samples for c in art.CLIPS],
                  nitrofs_relocation_bytes=growth)
    pin = release_info.PROFILE_INFO.get('tasm-v' + VERSION, {})
    for key in ('rom_sha256', 'arm9_sha256'):
        if pin.get(key) and pin[key] != report[key]:
            raise ValueError('Freefall differs from immutable release pin')
    return result, report


def generate(output, source=PARENT_PATH):
    output, source = Path(output), Path(source)
    if not output.resolve().is_relative_to((ROOT / 'build').resolve()):
        raise ValueError('Candidates belong in build/')
    result, report = apply_rom(source.read_bytes())
    path = output / 'Versioned.nds'
    validation = w.validate_rom(result, target=True)
    glob = next(e for e in validation['nitrofs'] if e['name'] == 'Glob.bin')
    meta = json.loads(source.with_suffix('.build.json').read_text(encoding='utf-8'))
    meta.update(freefall=report, release_version=VERSION, release_date=DATE, output=str(path.resolve()),
                output_rom_sha256=report['rom_sha256'], output_glob_sha256=w.sha256(result[glob['start']:glob['end']]),
                rom_size=len(result), used_rom_size=validation['header']['used_rom_size'],
                nitrofs=validation['nitrofs'], header_crc16=validation['header']['header_crc16'],
                verified_resource_count=w.u32(result, validation['header']['arm9_offset'] + oscorp_resources.COUNT_OFFSET))
    w.atomic_write(path, result, sources=(source,))
    w.write_json(path.with_suffix('.build.json'), meta)
    recipe = json.loads((ROOT / 'reference/gameplay_profile.json').read_text(encoding='utf-8'))
    recipe.update(profile='tasm-v' + VERSION, release_version=VERSION)
    w.write_json(output / 'gameplay_profile.json', recipe)
    w.write_json(output / 'changes.json', report)
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--source', default=PARENT_PATH, type=Path)
    args = parser.parse_args()
    print(generate(args.out, args.source))
