"""Small CS5E instruction improvements on the guarded current combat composition.

Only English/American text slots change. Keep current slot tails, ownership,
gameplay code, other overlays and player saves intact. Outputs remain private.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mod
from tools import combat_profile as cp, wos_tool as w
from tools.qol_suits_menu import StringSlots

TEXT_EDITS = {
    164: 'Up and \ue601 together.\nLaunch an enemy.',
    167: 'While rolling, press \ue601.\nMulti-hit kick.',
    170: 'In mid-air: Down and \ue601.\nA four-hit stomp.',
    173: 'Hold \ue604 to keep dodging.\nSteer with Left or Right.',
    179: 'After a hit or knockdown:\n\ue604 to recover and counterattack.',
    182: 'In mid-air: \ue600 near an enemy.\nKick off backward.',
    194: '\ue601, wait briefly, \ue601, \ue601, \ue601.\nThe gap is between attacks.',
    230: 'In mid-air, hold \ue600 to web swing.\nUse non-ichor surfaces.\nRelease \ue600 to let go.',
    233: 'On a ceiling, press \ue600 to hang.\nUp/Down adjusts web length.',
    239: 'Hold Up while running into a wall,\nor Dash into it.',
    242: 'Press \ue603 to lift an object.\nPress \ue601 or \ue603 to throw it.',
    403: 'SELECT switches between your\nmap and mission objective.',
    404: 'Tap Zoom to change map views:\nCurrent Map, District or World.',
    407: 'Save Point: choose Save.',
    417: 'Defeat the target to refill it.\nPause: Return to Save Point.',
    421: 'At a Save Point, choose Test Upgrades\nto practice combat.',
}


def edit_slots(clean: bytes, current: bytes) -> bytes:
    slots = StringSlots(clean)
    if len(current) != len(clean) or current[:slots.offsets[0]] != clean[:slots.offsets[0]]:
        raise ValueError('Current text bounds/tree differ from the verified profile')
    changed = bytearray(current)
    for index, text in TEXT_EDITS.items():
        data = slots.encode(text)
        start = slots.offsets[index]
        end = slots.offsets[index + 1] if index + 1 < len(slots.offsets) else len(clean)
        if len(data) > end - start:
            raise ValueError(f'Instruction exceeds original slot {index}')
        changed[start:start + len(data)] = data
    result = bytes(changed)
    for index in range(len(slots.texts)):
        before = slots.decode(current, index)
        after = slots.decode(result, index)
        if after != TEXT_EDITS.get(index, before):
            raise ValueError(f'Instruction round-trip/preservation failed: {index}')
        if index not in TEXT_EDITS:
            start = slots.offsets[index]
            end = slots.offsets[index + 1] if index + 1 < len(slots.offsets) else len(clean)
            if result[start:end] != current[start:end]:
                raise ValueError(f'Unrelated slot bytes changed: {index}')
    return result


def generate(base_mods='mods', output='build/qol-clarity'):
    root = w.safe_output(mod.project_path(output))
    if not root.is_relative_to((mod.ROOT / 'build').resolve()):
        raise ValueError('Candidates belong in build/')
    rom, glob, manifest = mod.load_clean()
    entries = {e['name']: e for e in manifest['entries']}
    overlays = mod.overlay_files(mod.project_path(base_mods), list(entries))
    profile = cp.load_recipe(mod.ROOT / 'reference/gameplay_profile.json', overlays)
    if profile != 'tasm-combat-flow':
        raise ValueError('Clarity pass requires the guarded current combat-flow composition')
    before = dict(overlays)
    for name in ('English.strings', 'American.strings'):
        entry = entries[name]
        clean = glob[entry['offset']:entry['offset'] + entry['size']]
        overlays[name] = edit_slots(clean, overlays[name])
    for name, data in overlays.items():
        w.atomic_write(root / 'mods' / name, data, (mod.DEFAULT_ROM,))
    w.write_json(root / 'gameplay_profile.json', {
        'schema_version': 1, 'profile': profile,
        'required_overlays': {name: w.sha256(data) for name, data in overlays.items()}})
    result, _, log = mod.create_build(rom, glob, manifest, overlays, gameplay_profile=profile)
    original, _, _ = mod.create_build(rom, glob, manifest, before, gameplay_profile=profile)
    header = w.parse_header(result)
    at, size = header['arm9_offset'], header['arm9_size']
    if result[at:at + size] != original[at:at + size]:
        raise ValueError('Text-only candidate changed gameplay code')
    path = root / 'Clarity.nds'
    w.atomic_write(path, result, (mod.DEFAULT_ROM,))
    w.write_json(path.with_suffix('.build.json'), log)
    w.write_json(root / 'clarity.json', {
        'schema_version': 1, 'text_slot_ids': sorted(TEXT_EDITS),
        'rom_sha256': w.sha256(result),
        'arm9_unchanged_sha256': w.sha256(result[at:at + size]),
        'unchanged_overlays': [name for name in overlays if overlays[name] == before[name]],
        'decoded_slots_checked_per_language': 1049,
        'assessment': 'Round-trip and byte preservation verified; menu layout awaits capture.'})
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mods', default='mods')
    parser.add_argument('--out', default='build/qol-clarity')
    args = parser.parse_args()
    try:
        print(generate(args.mods, args.out))
    except (ValueError, OSError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
