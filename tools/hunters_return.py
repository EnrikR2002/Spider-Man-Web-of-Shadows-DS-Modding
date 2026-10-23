"""Exact v0.31 post-pass: purchased 2099 Hunter's Return and fuller physique."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import wos_tool as w, tasm_kit as kit, spider2099 as assets
from tools import midnight_voltage as extension, hunters_return_art as art, hunters_return_motion as motion
from tools import spider2099_visual as visual, spider2099_movie as movie
from tools.assemble_tasm_kit import literal_errors, native_branch_errors, self_branch_errors
from tools.chapter_renewal_combat import asm

PARENT = 'ce6dd4e6afc8b188447cef5a07b76f58a2b2d0b25e7e829ea83adb70b362cade'
PARENT_PATH = ROOT/'build/version-0.31.0-final/Versioned.nds'
VERSION = '0.32.0'
DATE = '2026-10-23'
EXTRAS = ('zz_H32_Pull.sca', 'zz_H32_Rake.sca', 'zz_H32_Rake.gmb')


def runtime(at, values):
    sys.path.insert(0, str(ROOT/'work/research-libs'))
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
    source = Path(__file__).with_suffix('.s').read_text()
    for key, value in values.items():
        source = source.replace(key, f'0x{value:08x}')
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, at)[0])
    errors = literal_errors(code, source) + native_branch_errors(code, source, at) + self_branch_errors(code)
    if errors:
        raise ValueError('Hunter adapter assembly: ' + str(errors))
    return code


class Runtime(extension.Runtime):
    def __init__(self, rom):
        if w.sha256(rom) != PARENT:
            raise ValueError('Hunter requires exact published v0.31.0')
        self.rom = rom
        self.header = w.parse_header(rom)
        h = self.header
        self.arm = rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        self.new = bytearray(self.arm)
        self.end = len(self.arm) - 36
        self.start = kit.TARGET + self.end - kit.SOURCE
        self.data = bytearray()


def apply_rom(rom):
    rt = Runtime(rom)
    names, blobs = assets.resources(rom)
    before = tuple(blobs)
    import mod
    _, glob, _ = mod.load_clean()
    offsets, native_names, _ = w.parse_glob(glob)

    def native(name):
        i = native_names.index(name)
        return glob[offsets[i]:offsets[i+1]]

    from tools.kit_choreography import author
    from tools.animation_rig import AnimationRig
    parents = AnimationRig.parse(native('spd.nsbmd')).parents
    pull, _ = author(native('spd_GrapplePullAttack.sca'), native('spd_Idle.sca'), parents, motion.PULL)
    rake, _ = author(native('spd_GrapplePullAttackKick.sca'), native('spd_Idle.sca'), parents, motion.RAKE)
    extra = dict(zip(EXTRAS, (pull, rake, native('spd_GrapplePullAttackKick.gmb'))))
    shared = blobs[names.index('spd.nsbmd')]
    black, body = art.model(visual.selected_model(shared, 1))
    red = movie.red_model(shared, native('spd.nsbmd'))
    new_shared, model = visual.shared_model(red, black, blobs[names.index('spd.nsbtx')], blobs[names.index('spdB.nsbtx')])
    if new_shared[-visual.TRAILER_SIZE:] != shared[-visual.TRAILER_SIZE:]:
        raise ValueError('Muscle sculpt must retain existing draw-selector literals')
    blobs[names.index('spd.nsbmd')] = new_shared
    from tools.qol_suits_menu import StringSlots
    for name in ('American.strings', 'English.strings'):
        i = names.index(name)
        raw = StringSlots(native(name)).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}',
            204: "Hunter's Return", 205: "Hunter's Return",
            206: 'After a ground dash hits, tap \ue602 again.\nRecall into a rising talon rake.\nResistant foes: short pursuit. \ue604 exits.'})
        blobs[i] = raw + bytes((len(before[i]) - len(raw)) % 4)
    from tools import oscorp_resources
    if sum(map(len, blobs)) % 4:
        extra['zz_H32_align.bin'] = bytes(-sum(map(len, blobs)) % 4)
    names, blobs = oscorp_resources.append_resources(names, blobs, extra)
    if w.u32(rt.new, oscorp_resources.COUNT_OFFSET) != len(before):
        raise ValueError('Parent resource count changed')
    struct.pack_into('<I', rt.new, oscorp_resources.COUNT_OFFSET, len(names))
    state = rt.alloc(bytes(64))
    trampoline = rt.alloc()
    rt.data.extend(asm('push {r4-r6,lr}\nb #0x020b4da4', trampoline))
    from tools.crane_row import target
    hooks = (0x020b4da0, 0x02070484, 0x02078628, 0x02073b60, 0x020b5738, 0x020b5334)
    expected = (0xe92d4070, 0xe3500000, kit.branch(0x02078628, kit.KIT_BASE+0x30),
                0xe58d2114, kit.branch(0x020b5738, kit.KIT_BASE), kit.branch(0x020b5334, kit.KIT_BASE+4))
    for site, word in zip(hooks, expected):
        if w.u32(rt.arm, site-0x02000000) != word:
            raise ValueError(f'Hunter hook parent differs at {site:#x}')
    entry = rt.alloc()
    values = dict(STATE=state, NATIVE_TRANSITION=trampoline, OLD_CONTACT=target(hooks[2], expected[2]),
        OLD_EVADE_GENERIC=target(hooks[4], expected[4]), OLD_EVADE_STRING=target(hooks[5], expected[5]),
        PULL_SCA=names.index(EXTRAS[0]), RAKE_SCA=names.index(EXTRAS[1]), RAKE_GMB=names.index(EXTRAS[2]),
        RAKE_GAB=names.index('spd_GrapplePullAttackKick.gab'))
    code = runtime(entry, values)
    rt.data.extend(code)
    for i, site in enumerate(hooks):
        rt.hook(site, entry+i*4)
    changed = [n for n, a, b in zip(names, before, blobs) if a != b]
    if set(changed) != {'American.strings', 'English.strings', 'spd.nsbmd', 'GlobFiles.txt'}:
        raise ValueError('Unexpected Hunter resource scope')
    result = rt.finish({'Glob.bin': w.pack_glob(names, blobs)})
    h = w.parse_header(result)
    report = dict(version=VERSION, parent_sha256=PARENT, rom_sha256=w.sha256(result),
        arm9_sha256=w.sha256(result[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]),
        modified_resources=changed, added_resources=list(extra), model=body, shared_model=model,
        runtime=dict(start=rt.start, state=state, entry=entry, bytes=len(code), values=values, hooks=list(hooks)),
        ownership=dict(event=329, bit=20, price=100, record_unchanged=True),
        player_kit_32k_unchanged=True, native_red_and_other_actor_bindings_exact=True,
        rooms_audio_other_skills_save_format_preserved=True)
    from tools import release_info
    pin = release_info.PROFILE_INFO.get('tasm-v'+VERSION, {})
    for key in ('rom_sha256', 'arm9_sha256'):
        if pin.get(key) and pin[key] != report[key]:
            raise ValueError('Hunter differs from immutable release pin')
    return result, report


def generate(output, source=PARENT_PATH):
    source, output = Path(source), Path(output)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):
        raise ValueError('Candidates belong in build/')
    result, report = apply_rom(source.read_bytes())
    path = output/'Versioned.nds'
    v = w.validate_rom(result, target=True)
    meta = json.loads(source.with_suffix('.build.json').read_text())
    ge = next(e for e in v['nitrofs'] if e['name'] == 'Glob.bin')
    meta.update(hunters_return=report, release_version=VERSION, release_date=DATE,
        output_rom_sha256=w.sha256(result), output=str(path.resolve()), rom_size=len(result),
        used_rom_size=v['header']['used_rom_size'], nitrofs=v['nitrofs'], header_crc16=v['header']['header_crc16'],
        output_glob_sha256=w.sha256(result[ge['start']:ge['end']]), verified_resource_count=len(assets.resources(result)[0]))
    w.atomic_write(path, result, sources=(source,))
    w.write_json(path.with_suffix('.build.json'), meta)
    recipe = json.loads((ROOT/'reference/gameplay_profile.json').read_text())
    recipe.update(profile='tasm-v'+VERSION, release_version=VERSION)
    w.write_json(output/'gameplay_profile.json', recipe)
    w.write_json(output/'changes.json', report)
    print(json.dumps(dict(path=str(path), sha256=report['rom_sha256'], runtime=report['runtime'], model=report['model'])), flush=True)
    return path


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--source', type=Path, default=PARENT_PATH)
    a = p.parse_args()
    generate(a.out, a.source)
