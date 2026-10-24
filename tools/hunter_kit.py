"""Guarded v0.33.1 post-pass: first Hunter revision-3 slice, purchased Web Yank."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import wos_tool as w, tasm_kit as kit, spider2099 as assets, midnight_voltage as extension
from tools import hunter_kit_art as art
from tools.assemble_tasm_kit import literal_errors, native_branch_errors, self_branch_errors
from tools.chapter_renewal_combat import asm
from tools.crane_row import target

PARENT = '7081b1287fab93faf8e4ab44475c0e2d22c1dcd2860c6a15f878992837e510aa'
PARENT_PATH = ROOT/'build/version-0.33.1-final/Versioned.nds'
VERSION = '0.34.0'
DATE = '2026-10-23'
BIT, EVENT, PRICE = 83, 392, 300
BLACK_TABLE, BLACK_POINTER, BLACK_COUNT = 0x120420, 0x120178, 0x120190
EXTRAS = ('zz_H34_Yank.sca', 'zz_H34_Yank.gmb', 'zz_H34_Rake.sca', 'zz_H34_Rake.gmb')
SYMBOLS = ('web_hit', 'web_hand', 'web_release')


def kit_symbols():
    source = (ROOT/'tools/tasm_kit2.s').read_text(encoding='utf-8')
    raw = asm(source, kit.KIT2_BASE)
    if raw != kit.code_bytes(2):
        raise ValueError('Frozen second kit source differs')
    raw = asm(source+'\n.word '+','.join(SYMBOLS), kit.KIT2_BASE)
    return dict(zip(SYMBOLS, struct.unpack_from('<3I', raw, len(raw)-12)))


def runtime(at, values):
    source = Path(__file__).with_suffix('.s').read_text(encoding='utf-8')
    for key, value in values.items():
        source = source.replace(key, f'0x{value:08x}')
    code = asm(source, at)
    errors = literal_errors(code, source)+native_branch_errors(code, source, at)+self_branch_errors(code)
    if errors:
        raise ValueError('Hunter kit adapter assembly: '+str(errors))
    return code


class Runtime(extension.Runtime):
    def __init__(self, rom):
        if w.sha256(rom) != PARENT:
            raise ValueError('Hunter kit requires exact published v0.33.1')
        self.rom, self.header = rom, w.parse_header(rom)
        h = self.header
        self.arm = rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        self.new = bytearray(self.arm)
        self.end = len(self.arm)-36
        self.start = kit.TARGET+self.end-kit.SOURCE
        self.data = bytearray()


def apply_rom(rom):
    rt = Runtime(rom)
    names, blobs = assets.resources(rom)
    before = tuple(blobs)
    from tools.animation_rig import AnimationRig
    from tools.kit_choreography import author
    from tools.gmb import Gmb
    from tools.grip_compression import CompressedBlob, encode_backrefs
    idle = Gmb.parse(CompressedBlob.parse(blobs[names.index('spd_Idle.gmb')]).decoded)
    parents = AnimationRig.parse(blobs[names.index('spd.nsbmd')]).parents
    extra = {}
    for (sca_name, gmb_name), template, clip in (
        (EXTRAS[:2], 'spd_GroundAttack6.sca', art.YANK), (EXTRAS[2:], 'spd_DashSlamAttack.sca', art.RAKE)):
        extra[sca_name], _ = author(blobs[names.index(template)], blobs[names.index('spd_Idle.sca')], parents, clip)
        gmb = struct.pack('<4H', idle.unknown_u16_00, clip.samples, len(idle.channels), idle.unknown_u16_06)
        for c in idle.channels:
            gmb += struct.pack('<hH', c.kind, c.unknown_u16_02)+b''.join(c.records[:clip.samples])
        assert Gmb.parse(gmb).to_bytes() == gmb
        extra[gmb_name] = encode_backrefs(gmb)
    from tools.qol_suits_menu import StringSlots, slot_count
    import mod
    _, glob, _ = mod.load_clean()
    offsets, native_names, _ = w.parse_glob(glob)
    text_id = slot_count(blobs[names.index('American.strings')])
    texts = ('Web Yank', 'Web Yank', 'Ground \ue603: web yank into a talon rake.\nUp + \ue603: launch at the rake.\nHeavy foes: zip to strike. \ue604 exits.')
    for name in ('American.strings', 'English.strings'):
        i, n = names.index(name), native_names.index(name)
        if slot_count(blobs[i]) != text_id:
            raise ValueError('English/American appended string IDs differ')
        raw = StringSlots(glob[offsets[n]:offsets[n+1]]).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}'}, appended=texts)
        blobs[i] = raw+bytes((len(before[i])-len(raw)) % 4)
    from tools import oscorp_resources
    if sum(map(len, blobs)) % 4:
        extra['zz_H34_align.bin'] = bytes(-sum(map(len, blobs)) % 4)
    names, blobs = oscorp_resources.append_resources(names, blobs, extra)
    if (w.u32(rt.arm, BLACK_POINTER), w.u32(rt.arm, BLACK_COUNT)) != (0x02120420, 7):
        raise ValueError('Native Black shop pointer/count changed')
    state = rt.alloc(bytes(128))
    shop = rt.alloc(rt.arm[BLACK_TABLE:BLACK_TABLE+7*32]+struct.pack('<8I',
        EVENT, kit.NO_EVENT, kit.NO_EVENT, text_id, text_id+1, text_id+2, 1, PRICE))
    struct.pack_into('<I', rt.new, BLACK_POINTER, shop)
    struct.pack_into('<I', rt.new, BLACK_COUNT, 8)
    sites = (0x020b721c, 0x020c31e4, 0x02070484, 0x02073b60, 0x020b5334, 0x020b5738)
    old = [w.u32(rt.arm, site-kit.BASE) for site in sites]
    if old[0] != 0xe92d40f0 or any(word >> 24 != 0xea for word in old[1:]):
        raise ValueError('Hunter input/node/animation/update/evade parent hooks differ')
    trampoline = rt.alloc(asm('push {r4-r7,lr}\nb #0x020b7220', rt.start+len(rt.data)))
    # shortcut: native mini-bosses stay outside this registry; add their class adapter before expanding boss coverage.
    parent_meta = json.loads(PARENT_PATH.with_suffix('.build.json').read_text(encoding='utf-8'))
    entry = rt.alloc()
    values = dict(STATE=state, NATIVE_OBJECT=trampoline,
        OLD_NODE=target(sites[1], old[1]), OLD_ANIMATION=target(sites[2], old[2]),
        OLD_UPDATE=target(sites[3], old[3]), OLD_STRING=target(sites[4], old[4]), OLD_GENERIC=target(sites[5], old[5]),
        YANK_SCA=names.index(EXTRAS[0]), YANK_GMB=names.index(EXTRAS[1]),
        SHORT_SCA=names.index(EXTRAS[2]), SHORT_GMB=names.index(EXTRAS[3]),
        YANK_GAB=names.index('spd_GrapplePullAttack.gab'), BOSS_CONFIG=parent_meta['creature_forge']['creatures']['conductor']['config'],
        **{name.upper(): value for name, value in kit_symbols().items()})
    code = runtime(entry, values)
    rt.data.extend(code)
    for index, site in enumerate(sites):
        rt.hook(site, entry+4*index)
    if w.u32(rt.new, oscorp_resources.COUNT_OFFSET) != len(before):
        raise ValueError('Parent resource count changed')
    struct.pack_into('<I', rt.new, oscorp_resources.COUNT_OFFSET, len(names))
    result = rt.finish()
    h = w.parse_header(result)
    packed = w.pack_glob(names, blobs)
    ge = next(e for e in w.nitrofs_entries(result) if e['name'] == 'Glob.bin')
    growth = w.align_up(len(packed)-ge['size'])
    if growth <= 0 or h['used_rom_size']+growth > len(result) or any(x not in (0, 255) for x in result[-growth:]):
        raise ValueError('Insufficient verified ROM padding for Hunter resources')
    staged = bytearray(result[:ge['end']]+bytes(growth)+result[ge['end']:-growth])
    for e in w.nitrofs_entries(result):
        if e['start'] >= ge['end']:
            struct.pack_into('<2I', staged, h['fat_offset']+e['id']*8, e['start']+growth, e['end']+growth)
    struct.pack_into('<I', staged, 0x80, h['used_rom_size']+growth)
    struct.pack_into('<H', staged, 0x15e, w.crc16(staged[:0x15e]))
    result = w.rebuild_rom(bytes(staged), {'Glob.bin': packed})
    changed = [name for name, a, b in zip(names, before, blobs) if a != b]
    if set(changed) != {'American.strings', 'English.strings', 'GlobFiles.txt'}:
        raise ValueError('Unexpected Hunter resource scope')
    hh = w.parse_header(result)
    report = dict(version=VERSION, parent_sha256=PARENT, rom_sha256=w.sha256(result),
        arm9_sha256=w.sha256(result[hh['arm9_offset']:hh['arm9_offset']+hh['arm9_size']]),
        modified_resources=changed, added_resources=list(extra),
        runtime=dict(start=rt.start, state=state, shop=shop, entry=entry, values=values, bytes=len(code),
            allocation_bytes=w.align_up(len(rt.data), 0x1000), hooks=[dict(site=s, old=o, target=entry+4*i) for i, (s, o) in enumerate(zip(sites, old))]),
        ownership=dict(event=EVENT, bit=BIT, price=PRICE, native_black_rows_exact=True, price_provisional=True),
        text_id=text_id, samples=art.YANK.samples, close_samples=art.RAKE.samples, nitrofs_relocation_bytes=growth,
        player_kit_32k_unchanged=True, native_resources_bindings_rooms_audio_save_format_preserved=True)
    from tools import release_info
    pin = release_info.PROFILE_INFO.get('tasm-v'+VERSION, {})
    for key in ('rom_sha256', 'arm9_sha256'):
        if pin.get(key) and pin[key] != report[key]:
            raise ValueError('Hunter kit differs from immutable release pin')
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
    meta.update(hunter_kit=report, release_version=VERSION, release_date=DATE, output_rom_sha256=w.sha256(result),
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
