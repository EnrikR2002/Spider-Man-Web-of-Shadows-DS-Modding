#!/usr/bin/env python3
"""TASM 1 stage one: red-form opening low kick, retaining the game's combo routing.

Rebind one synchronized player action triplet; do not edit damage, save data,
executable code, GAB events, or the alternate form's GroundAttack1 resources.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mod
from tools.custom_formats import Xbd
from tools import wos_tool as w

SOURCE = 'spd_GroundAttack11'
TARGET = 'spd_GroundAttack15'


def opening_kick(raw: bytes, names: list[str]):
    actor = Xbd.parse(raw, names)
    if len(actor.bindings) != 311 or actor.opaque_tail_start != 0x4f0:
        raise ValueError('Unexpected CS5E player binding layout')
    result = raw
    changes = []
    for ext in ('sca', 'gmb', 'gab'):
        source, target = f'{SOURCE}.{ext}', f'{TARGET}.{ext}'
        records = [b for b in actor.bindings if b['name'] == source]
        if len(records) != 1: raise ValueError(f'Expected one clean player binding for {source}')
        old = records[0]
        target_index = names.index(target)
        result = Xbd.parse(result, names).replace_binding(old['offset'], target_index, names)
        changes.append({'offset': old['offset'], 'old_index': old['index'],
                        'new_index': target_index, 'old_name': source, 'new_name': target})
    return result, changes


def generate(base_mods='mods', output='build/tasm1-stage1'):
    root = w.safe_output(mod.project_path(output))
    if not root.is_relative_to((mod.ROOT / 'build').resolve()):
        raise ValueError('TASM experiment output must be inside build/')
    rom, glob, manifest = mod.load_clean()
    names = [e['name'] for e in manifest['entries']]
    entry = next(e for e in manifest['entries'] if e['name'] == 'spd.xbd')
    clean = glob[entry['offset']:entry['offset'] + entry['size']]
    changed, bindings = opening_kick(clean, names)
    overlays = mod.overlay_files(mod.project_path(base_mods), names)
    if 'spd.xbd' in overlays and overlays['spd.xbd'] not in (clean, changed):
        raise ValueError('Existing player definition has other edits; merge them explicitly')
    overlays['spd.xbd'] = changed
    for name, data in overlays.items(): w.atomic_write(root/'mods'/name, data, (mod.DEFAULT_ROM,))
    build, _, log = mod.create_build(rom, glob, manifest, overlays)
    path = root/'TASM1-stage1.nds'
    w.atomic_write(path, build, (mod.DEFAULT_ROM,)); w.write_json(path.with_suffix('.build.json'), log)
    w.write_json(root/'tasm1.json', {'stage': 1, 'feature': 'Snap Sweep opening kick',
        'source_xbd_sha256': w.sha256(clean), 'output_xbd_sha256': w.sha256(changed),
        'changed_byte_offsets': [i for i, (a, b) in enumerate(zip(clean, changed)) if a != b],
        'bindings': bindings, 'rom_sha256': w.sha256(build),
        'limitations': ['Existing red-form first action replaced; no third slot.',
                        'Existing combo controller and successor actions retained.',
                        'Damage values, unlock flags, and save payload are unedited.']})
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mods', default='mods')
    parser.add_argument('--out', default='build/tasm1-stage1')
    args = parser.parse_args(argv)
    try:
        print(f'TASM 1 candidate: {generate(args.mods, args.out)}')
    except (OSError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr); return 1
    return 0


if __name__ == '__main__': raise SystemExit(main())
