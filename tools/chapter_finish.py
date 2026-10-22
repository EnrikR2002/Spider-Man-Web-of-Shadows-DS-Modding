"""Guarded v0.28 post-pass: native Skyjack drift, Skitter and Crane finish work."""
from pathlib import Path
import argparse
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import midnight_voltage, wos_tool as w, tasm_kit as kit, creature_forge as forge

PARENT = '6819cb91e824961552b86690c3fdd112930bbd1cbb70d5c3c76978b5ce932a20'
VERSION = '0.29.0'
DATE = '2026-10-22'
PARENT_PATH = ROOT / 'build/version-0.28.0-final/Versioned.nds'


class Runtime(midnight_voltage.Runtime):
    def __init__(self, rom):
        if w.sha256(rom) != PARENT:
            raise ValueError('Chapter finish requires exact published v0.28')
        self.rom = rom
        self.header = w.parse_header(rom)
        h = self.header
        self.arm = rom[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']]
        self.new = bytearray(self.arm)
        self.end = len(self.arm) - 36
        self.start = kit.TARGET + self.end - kit.SOURCE
        self.data = bytearray()


def apply_rom(rom, *, stage='full'):
    if stage not in ('kit', 'skitter', 'full'):
        raise ValueError('Unknown finish stage')
    runtime = Runtime(rom)
    meta = json.loads(PARENT_PATH.with_suffix('.build.json').read_text())
    entry = next(e for e in w.nitrofs_entries(rom) if e['name'] == 'Glob.bin')
    glob = rom[entry['start']:entry['end']]
    offsets, names, _ = w.parse_glob(glob)
    blobs = [glob[a:b] for a, b in zip(offsets, offsets[1:])]
    before = tuple(blobs)
    import mod
    _, clean, _ = mod.load_clean()
    co, cn, _ = w.parse_glob(clean)
    native = lambda name: clean[co[cn.index(name)]:co[cn.index(name) + 1]]
    parent = lambda name: before[names.index(name)]
    changed = []
    report = {'version': VERSION, 'parent_sha256': PARENT, 'stage': stage}
    if stage != 'kit':
        from tools import chapter_finish_skitter
        report['skitter'] = chapter_finish_skitter.apply(runtime, meta, names, blobs, native, parent)
        changed.extend(report['skitter']['modified_resources'])
    if stage == 'full':
        from tools import chapter_finish_crane
        report['crane'] = chapter_finish_crane.apply(runtime, meta, names, blobs, native)
        changed.extend(report['crane']['modified_resources'])
    from tools.qol_suits_menu import StringSlots
    for name in forge.chapter.STRING_FILES:
        i = names.index(name)
        raw = StringSlots(native(name)).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}'})
        blobs[i] = raw + bytes((len(blobs[i]) - len(raw)) % 4)
        changed.append(name)
    if any(a != b for name, a, b in zip(names, before, blobs) if name not in changed):
        raise ValueError('Unlisted resource changed')
    replacements = {'Glob.bin': w.pack_glob(names, blobs)}
    if stage != 'kit':
        from tools import chapter_finish_audio
        sound = next(e for e in w.nitrofs_entries(rom) if e['name'] == 'sound_data.sdat')
        replacements['sound_data.sdat'], report['skitter_audio'] = chapter_finish_audio.sound_data(rom[sound['start']:sound['end']])
    result = runtime.finish(replacements)
    from tools import chapter_finish_kit
    result, report['kit'] = chapter_finish_kit.apply(result)
    h = w.parse_header(result)
    report.update(modified_resources=sorted(set(changed)), rom_sha256=w.sha256(result),
                  arm9_sha256=w.sha256(result[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']]))
    if stage == 'full':
        from tools import release_info
        pin = release_info.PROFILE_INFO.get('tasm-v' + VERSION, {})
        for key in ('rom_sha256', 'arm9_sha256'):
            if pin.get(key) and pin[key] != report[key]:
                raise ValueError('Finish composition differs from its immutable release pin')
    return result, report


def generate(output, source=PARENT_PATH, stage='full'):
    source, output = Path(source), Path(output)
    if not output.resolve().is_relative_to((ROOT / 'build').resolve()):
        raise ValueError('Candidate output must stay inside build/')
    raw, report = apply_rom(source.read_bytes(), stage=stage)
    path = output / 'Versioned.nds'
    meta = json.loads(source.with_suffix('.build.json').read_text())
    meta['chapter_finish'] = report
    meta.update(release_version=VERSION, release_date=DATE, output_rom_sha256=w.sha256(raw),
                output=str(path.resolve()))
    validation = w.validate_rom(raw, target=True)
    ge = next(e for e in validation['nitrofs'] if e['name'] == 'Glob.bin')
    meta.update(rom_size=len(raw), used_rom_size=validation['header']['used_rom_size'],
                nitrofs=validation['nitrofs'], header_crc16=validation['header']['header_crc16'],
                output_glob_sha256=w.sha256(raw[ge['start']:ge['end']]))
    w.atomic_write(path, raw, sources=(source,))
    w.write_json(path.with_suffix('.build.json'), meta)
    recipe = json.loads((ROOT / 'reference/gameplay_profile.json').read_text())
    recipe.update(profile='tasm-v' + VERSION, release_version=VERSION)
    w.write_json(output / 'gameplay_profile.json', recipe)
    print(json.dumps({'path': str(path), 'stage': stage, 'sha256': report['rom_sha256']}), flush=True)
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=PARENT_PATH)
    parser.add_argument('--stage', choices=('kit', 'skitter', 'full'), default='full')
    args = parser.parse_args()
    generate(args.out, args.source, args.stage)
