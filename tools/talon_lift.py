"""Exact v0.32.1 post-pass: purchased 2099 Talon Lift on native Power Launch."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import wos_tool as w, tasm_kit as kit, spider2099 as assets, oscorp_resources
from tools.crane_row import target
from tools.assemble_tasm_kit import literal_errors, native_branch_errors, self_branch_errors
from tools.kit_choreography import Clip, author

PARENT = '68800726f92ab0d2c9662892f465610b29447cc0b65866f375f22962a2f7b005'
PARENT_PATH = ROOT/'build/version-0.32.1-final/Versioned.nds'
VERSION = '0.33.0'
DATE = '2026-10-23'
SCA = 'zz_T33_Lift.sca'
TAIL_BYTES = 2040

LIFT = Clip('talon_lift', 14, {
    'root': [(0, (0., 3.92, -.22)), (2, (0., 2.7, -.6)), (3, (0., 2.8, -.3)),
             (5, (0., 4.15, .45)), (7, (0., 4.25, .35)), (10, (0., 3.7, .05)), (13, (0., 3.92, -.22))],
    'yaw': [(0, 0.), (2, -42.), (3, -38.), (5, 30.), (7, 48.), (10, 12.), (13, 0.)],
    'spine_pitch': [(0, 0.), (2, 30.), (3, 26.), (5, -18.), (7, -24.), (10, 9.), (13, 0.)],
    'spine_twist': [(0, 0.), (2, -24.), (4, -10.), (6, 32.), (9, 12.), (13, 0.)],
    'head_pitch': [(0, 0.), (2, -16.), (5, -24.), (8, -12.), (13, 0.)],
    'hand_l': [(0, (1.8, -.6, 1.4)), (2, (1.3, -2.1, -.4)), (3, (.8, -1.9, 1.0)),
               (4, (.7, -.3, 3.9)), (5, (.8, 2.3, 3.2)), (6, (1.5, 3.1, 1.4)),
               (8, (2.9, .8, -1.1)), (11, (2.3, -.6, .7)), (13, (1.8, -.6, 1.4))],
    'hand_r': [(0, (-1.8, -.6, 1.4)), (2, (-1.6, -.4, 2.2)), (4, (-2.1, -.8, 1.0)),
               (6, (-1.1, .2, 3.5)), (7, (-.8, 1.9, 2.6)), (9, (-2.4, 1.0, -.5)),
               (11, (-2.3, -.4, .7)), (13, (-1.8, -.6, 1.4))],
    'elbow_l': [(0, (2.7, -.5, -.5)), (2, (2.8, -1.3, -2.)), (4, (2.2, -.3, 1.6)),
                (6, (2.7, 2.1, -.5)), (9, (3.1, .2, -1.6)), (13, (2.7, -.5, -.5))],
    'elbow_r': [(0, (-2.7, -.5, -.5)), (3, (-3., -.4, .2)), (6, (-2.3, .1, 1.5)),
                (8, (-2.6, 1.2, -1.)), (13, (-2.7, -.5, -.5))],
    'plant_l': [(0, 1.)], 'plant_r': [(0, 1.)],
    'world_l': [(0, (1.1, .78, 1.4))], 'world_r': [(0, (-1.1, .78, -1.1))],
})


def runtime(at, values):
    sys.path.insert(0, str(ROOT/'work/research-libs'))
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
    source = Path(__file__).with_suffix('.s').read_text(encoding='utf-8')
    for key, value in values.items():
        source = source.replace(key, f'0x{value:08x}')
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, at)[0])
    errors = literal_errors(code, source) + native_branch_errors(code, source, at) + self_branch_errors(code)
    if errors:
        raise ValueError('Talon adapter assembly: ' + str(errors))
    return code


def apply_rom(rom):
    if w.sha256(rom) != PARENT:
        raise ValueError('Talon Lift requires exact published v0.32.1')
    header = w.parse_header(rom)
    arm = rom[header['arm9_offset']:header['arm9_offset']+header['arm9_size']]
    new = bytearray(arm)
    names, blobs = assets.resources(rom)
    before = tuple(blobs)
    from tools.animation_rig import AnimationRig
    i = names.index('spd_PowerLauncherAttack.sca')
    authored, _ = author(blobs[i], blobs[names.index('spd_Idle.sca')],
                         AnimationRig.parse(blobs[names.index('spd.nsbmd')]).parents, LIFT)
    from tools.qol_suits_menu import StringSlots
    import mod
    _, glob, _ = mod.load_clean()
    offsets, native_names, _ = w.parse_glob(glob)
    for name in ('American.strings', 'English.strings'):
        i = names.index(name)
        n = native_names.index(name)
        raw = StringSlots(glob[offsets[n]:offsets[n+1]]).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}',
            207: 'Talon Lift', 208: 'Talon Lift',
            209: 'Up + \ue602: coil into a rising talon rake.\nHold \ue600 to follow. \ue601 for air hits.\n\ue604 cancels. Jumping stays manual.'})
        blobs[i] = raw + bytes((len(before[i])-len(raw)) % 4)
    names, blobs = oscorp_resources.append_resources(names, blobs, {SCA: authored})
    if w.u32(arm, oscorp_resources.COUNT_OFFSET) != len(before):
        raise ValueError('Parent resource count changed')
    struct.pack_into('<I', new, oscorp_resources.COUNT_OFFSET, len(names))
    start = len(arm)-36-TAIL_BYTES
    at = kit.TARGET+start-kit.SOURCE
    sites = (0x02070484, 0x020b5738)
    old = [w.u32(arm, site-0x02000000) for site in sites]
    values = dict(OLD_ANIMATION=target(sites[0], old[0]), OLD_EVADE=target(sites[1], old[1]), LIFT_SCA=names.index(SCA))
    code = runtime(at, values)
    if len(code) > TAIL_BYTES or any(arm[start:-36]):
        raise ValueError('Talon Lift tail is occupied or too small')
    new[start:start+len(code)] = code
    for index, site in enumerate(sites):
        struct.pack_into('<I', new, site-0x02000000, kit.branch(site, at+index*4))
    changed = [n for n, a, b in zip(names, before, blobs) if a != b]
    if set(changed) != {'American.strings', 'English.strings', 'GlobFiles.txt'}:
        raise ValueError('Unexpected Talon Lift resource scope')
    packed = w.pack_glob(names, blobs)
    ge = next(e for e in w.nitrofs_entries(rom) if e['name'] == 'Glob.bin')
    growth = w.align_up(len(packed)-ge['size'])
    if growth <= 0 or header['used_rom_size']+growth > len(rom) or any(x not in (0, 255) for x in rom[-growth:]):
        raise ValueError('Insufficient verified padding for Talon resource growth')
    # Keep the parent's occupied gap; insert padding before it as ARM9 growth does.
    staged = bytearray(rom[:ge['end']]+bytes(growth)+rom[ge['end']:-growth])
    for entry in w.nitrofs_entries(rom):
        if entry['start'] >= ge['end']:
            struct.pack_into('<2I', staged, header['fat_offset']+entry['id']*8, entry['start']+growth, entry['end']+growth)
    struct.pack_into('<I', staged, 0x80, header['used_rom_size']+growth)
    struct.pack_into('<H', staged, 0x15e, w.crc16(staged[:0x15e]))
    result = w.rebuild_rom(bytes(staged), {'Glob.bin': packed})
    result, _ = kit.replace_arm9(result, bytes(new))
    w.validate_rom(result, target=True)
    report = dict(version=VERSION, parent_sha256=PARENT, rom_sha256=w.sha256(result), arm9_sha256=w.sha256(new),
        modified_resources=changed, added_resources=[SCA], sca_id=values['LIFT_SCA'], sca_sha256=w.sha256(authored),
        runtime=dict(entry=at, bytes=len(code), values=values, allocation_bytes=0, remaining_zero_tail=TAIL_BYTES-len(code),
                     hooks=[dict(site=s, old=o, target=at+i*4) for i, (s, o) in enumerate(zip(sites, old))]),
        ownership=dict(event=330, bit=21, price=200, record_unchanged=True),
        native_state=45, native_action=128, samples=14, native_contact_samples=[5, 6],
        nitrofs_relocation_bytes=growth, occupied_gap_and_other_file_bytes_preserved=True,
        native_movement_contacts_damage_launch_and_manual_jump_preserved=True,
        player_kit_32k_assets_other_bindings_purchases_rooms_audio_save_format_preserved=True)
    from tools import release_info
    pin = release_info.PROFILE_INFO.get('tasm-v'+VERSION, {})
    for key in ('rom_sha256', 'arm9_sha256'):
        if pin.get(key) and pin[key] != report[key]:
            raise ValueError('Talon Lift differs from immutable release pin')
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
    meta.update(talon_lift=report, release_version=VERSION, release_date=DATE, output_rom_sha256=w.sha256(result),
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
