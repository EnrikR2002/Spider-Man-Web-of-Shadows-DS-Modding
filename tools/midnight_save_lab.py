"""Native-save persistence experiment using copied batteries and disposable RAM.

Candidate upper flag bits are research only, NOT approved storage. Native code
copies 40 flag bytes and bounds flag queries to 291; test round trips before
designating any spare bits. No command here edits a real save or ROM.
"""
from __future__ import annotations
import argparse
import ctypes as c
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import mod
from tools import emulator_smoke as emu, kit_lab as k, midnight_progress as progress, wos_tool as w

OUT = ROOT / 'work/midnight-line'
PATTERN = progress.encode(0, progress.Progress(True, True, True))


def stats(lib):
    ptr, ram = k.ram_of(lib)
    address = struct.unpack_from('<I', ram, k.STATS_POINTER - 0x02000000)[0]
    offset = address - 0x02000000
    if address % 4 or not 0 <= offset < len(ram) - 0x98:
        raise ValueError('Stats outside aligned RAM')
    return ptr, offset, ram[offset:offset + 0x98]


def run_child(mode):
    injected = []
    reload = mode == 'reload'
    save = OUT / 'native-save-fixture.sav' if reload else k.TRAINING_SAVE
    save_hash = w.sha256(save.read_bytes())
    script_path = 'oscorp-reload.json' if reload else 'oscorp-save.json'
    script = json.loads((ROOT / 'reference/combat-inputs' / script_path).read_text())
    def hook(frame, lib):
        if frame == 2250 and mode == 'fixture':
            ptr, offset, data = stats(lib)
            original = struct.unpack_from('<I', data, 0x40)[0]
            if original & ~7:
                raise ValueError('Candidate unused flag bits already occupied')
            encoded = progress.encode(original, progress.Progress(True, True, True))
            c.memmove(ptr + offset + 0x40, struct.pack('<I', encoded), 4)
            injected.append({'frame': frame, 'old_word': original, 'new_word': encoded})
    dest = emu.run(mod.DEFAULT_ROM, 3000, {2250, 2420, 2900}, save_path=save,
                   script=script, label='ml-save-' + mode, frame_hook=hook,
                   ram_captures={2900}, battery_captures={2900}, core_options=k.NO_JIT)
    if w.sha256(save.read_bytes()) != save_hash: raise ValueError('Source battery changed')
    ram = (dest / 'ram-02900.bin').read_bytes()
    address = struct.unpack_from('<I', ram, k.STATS_POINTER - 0x02000000)[0]
    offset = address - 0x02000000
    if not 0 <= offset <= len(ram) - 0x98: raise ValueError('Stats missing at completion')
    data = ram[offset:offset + 0x98]
    battery = next(dest.glob('battery-02900.*'))
    report = {'mode': mode, 'source_sha256': save_hash, 'source_unchanged': True,
              'injected': injected, 'flag_word': struct.unpack_from('<I', data, 0x40)[0],
              'stats_hex': data[:0x58].hex(), 'battery': str(battery),
              'captures': [str(x) for x in sorted(dest.glob('frame-*.png'))],
              'confidence': 'Round-trip probe only; allocation and all native accesses not yet qualified'}
    word = report['flag_word']
    state = progress.decode(word)
    report['decoded_progress'] = {'discovered':state.discovered, 'main_power':state.main_power, 'completed':state.completed}
    if mode == 'fixture':
        w.atomic_write(OUT / 'native-save-fixture.sav', battery.read_bytes(), sources=(save,))
    w.write_json(OUT / ('save-' + mode + '.json'), report)
    print('ML_SAVE_REPORT ' + str(OUT / ('save-' + mode + '.json')), flush=True)


def verify():
    records = [json.loads((OUT / ('save-' + mode + '.json')).read_text()) for mode in ('control','fixture','reload')]
    control, fixture, reload = records
    a,b = Path(control['battery']).read_bytes(), Path(fixture['battery']).read_bytes()
    differences = [i for i,(x,y) in enumerate(zip(a,b)) if x != y]
    checks = {'sources_unchanged':all(r['source_unchanged'] for r in records),
              'versioned_milestones_survive_boot':fixture['flag_word'] == reload['flag_word'] == PATTERN,
              'only_marker_and_checksum_changed':set(differences) <= set(range(16,20)) | set(range(84,88)),
              'native_flags_unchanged_after_boot':bytes.fromhex(fixture['stats_hex'])[28:64] == bytes.fromhex(reload['stats_hex'])[28:64]}
    report = {'schema_version':1, 'passed':all(checks.values()), 'checks':checks,
              'marker':hex(PATTERN), 'battery_changed_offsets':differences,
              'publication_gate':'Native allocation audit and integrated checkpoint handling remain open'}
    w.write_json(OUT / 'save-verification.json',report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('control', 'fixture', 'reload', 'verify'))
    parser.add_argument('--child', action='store_true')
    args = parser.parse_args()
    if args.mode == 'verify':
        report = verify()
        print(json.dumps(report,indent=2))
        return 0 if report['passed'] else 1
    if args.child: return run_child(args.mode)
    done = subprocess.run([sys.executable, str(Path(__file__)), args.mode, '--child'],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
    lines = [s[s.index('ML_SAVE_REPORT '):] for s in done.stdout.splitlines() if 'ML_SAVE_REPORT ' in s]
    if done.returncode or not lines:
        log = OUT / ('save-' + args.mode + '-error.log')
        w.atomic_write(log, done.stdout.encode('utf-8'))
        raise ValueError(f'Native save probe failed; inspect {log}')
    report = json.loads(Path(lines[-1][15:]).read_text())
    print(json.dumps({k: v for k, v in report.items() if k != 'stats_hex'}, indent=2))


if __name__ == '__main__': sys.exit(main())
