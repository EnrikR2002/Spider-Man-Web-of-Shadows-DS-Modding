#!/usr/bin/env python3
"""Stable DeSmuME ROM, validated battery wrapper, and exact testing checkpoints.

Save in-game and close DeSmuME before build, adopt, checkpoint, or restore.
Local configuration and snapshots stay in ignored work/. No save-state support.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mod
from tools import save_backups as saves
from tools import wos_tool as w
from tools.desmume_save import Dsv

CONFIG = mod.ROOT / 'work/playtest.json'
ROM = mod.ROOT / 'build/Spider-Man-WoS-modded.nds'
CANDIDATE = mod.ROOT / 'build/playtest-candidate/Spider-Man-WoS-modded.nds'
RELEASES = mod.ROOT / 'build/releases'
# Optional DeSmuME0.9.13 command-line experiments. The ordinary launcher uses
# saved settings. This tool does not edit the INI or load save states, but the
# emulator persists its selected 3D renderer even for a command-line override.
# Sources: release_0_9_13/src/commandline.cpp and frontend/windows/main.cpp.
# Performance/visual acceptance remains open; presets are not activated by default.
LAUNCH_PRESETS = {
    'current': (),
    'performance-preview': ('--preload-rom', '--jit-enable', '--jit-size', '12'),
    'hd-preview': ('--preload-rom', '--jit-enable', '--jit-size', '12',
                   '--3d-render', 'autogl', '--gpu-resolution-multiplier', '2'),
}


def assert_closed():
    """Fail before mutations if a DeSmuME process is running on Windows."""
    if os.name != 'nt':
        return
    result = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], check=True,
                            capture_output=True, text=True, timeout=15)
    if any(row and 'desmume' in row[0].casefold()
           for row in csv.reader(io.StringIO(result.stdout))):
        raise ValueError('Save in-game and close DeSmuME first; no files changed')


def validate_battery_dir(value):
    if not isinstance(value, (str, os.PathLike)):
        raise ValueError('Battery directory must be a path')
    directory = Path(value)
    if not directory.is_absolute() or not directory.is_dir():
        raise ValueError('Use the actual absolute DeSmuME Battery directory')
    if directory.is_symlink():
        raise ValueError('Battery directory symlinks are unsupported')
    directory = w.safe_output(directory)
    if directory.is_relative_to(saves.STORE.resolve()):
        raise ValueError('Battery directory must be outside snapshot storage')
    return directory


def configure(battery_dir, config=CONFIG, emulator=None):
    directory = validate_battery_dir(battery_dir)
    data = {'schema_version': 1, 'battery_directory': str(directory)}
    if Path(config).exists():
        old = json.loads(Path(config).read_text(encoding='utf-8'))
        if old.get('schema_version') == 1 and old.get('emulator'): data['emulator'] = old['emulator']
    if emulator is not None:
        data['emulator'] = str(emulator_path(emulator))
    w.write_json(config, data)
    return directory / (ROM.stem + '.dsv')


def emulator_path(value):
    path = Path(value)
    if not path.is_absolute() or not path.is_file() or path.suffix.lower() != '.exe' or path.is_symlink():
        raise ValueError('Use the actual absolute DeSmuME executable path')
    return path.resolve()


def inspect_save(path):
    return Dsv.parse(saves.read_save(path))


def current_save(config=CONFIG):
    data = json.loads(Path(config).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('Invalid playtest configuration')
    directory = validate_battery_dir(data.get('battery_directory', ''))
    return saves.save_path(directory / (ROM.stem + '.dsv'))


def preserve(path, prefix, store=saves.STORE):
    """Idempotent content-addressed backup, with integrity checks on reuse."""
    path = saves.save_path(path)
    data = saves.read_save(path)
    name = prefix + '-' + path.suffix.lower()[1:] + '-' + w.sha256(data)
    directory = saves.snapshot_path(store, name)
    if directory.exists():
        metadata, old = saves.load_snapshot(name, store)
        if old != data or metadata['suffix'] != path.suffix.lower():
            raise ValueError('Existing safety snapshot differs')
    else:
        saves.backup(path, name, store)
    return name


def adopt(source, destination, store=saves.STORE):
    """Copy progress to the stable ROM association; retain both original saves."""
    source = saves.save_path(source)
    if source.suffix.lower() != '.dsv':
        raise ValueError('DeSmuME playtests require .dsv; no format conversion')
    inspect_save(source)
    name = preserve(source, 'adopt', store)
    safety = saves.restore(name, destination, store)
    return name, safety


def build(mods='mods', config=CONFIG, store=saves.STORE):
    assert_closed()
    path = current_save(config)
    if path.exists(): inspect_save(path)
    snapshot = preserve(path, 'before-build', store) if path.exists() else None
    # The build never writes a battery save. mod.main validates the clean ROM,
    # entire overlay, and every rebuilt resource before atomic ROM publication.
    result = mod.main(['build', '--mods', str(mods), '-o', str(CANDIDATE)])
    if result:
        return result
    assert_closed()
    if snapshot and saves.read_save(path) != saves.load_snapshot(snapshot, store)[1]:
        raise ValueError('Battery save changed during build; keep DeSmuME closed')
    candidate = CANDIDATE.read_bytes()
    previous = ROM.read_bytes() if ROM.exists() else None
    log_path = CANDIDATE.with_suffix('.build.json')
    release_log = json.loads(log_path.read_text(encoding='utf-8')) if log_path.exists() else {}
    version = release_log.get('release_version')
    if version:
        from tools import release_info
        release_info.check_version_reuse(version, w.sha256(candidate))
    if previous is not None:
        rollback = RELEASES / w.sha256(previous) / ROM.name
        if rollback.exists() and rollback.read_bytes() != previous:
            raise ValueError('Existing ROM rollback copy differs; refusing publication')
        if not rollback.exists(): w.atomic_write(rollback, previous, (mod.DEFAULT_ROM,))
    w.atomic_write(ROM, candidate, (mod.DEFAULT_ROM,))
    if ROM.read_bytes() != candidate: raise ValueError('Published ROM differs from validated candidate')
    if log_path.exists(): w.atomic_write(ROM.with_suffix('.build.json'), log_path.read_bytes())
    w.write_json(RELEASES / w.sha256(candidate) / 'release.json', {
        'schema_version': 1, 'rom_sha256': w.sha256(candidate),
        'version': version,
        'previous_rom_sha256': w.sha256(previous) if previous is not None else None,
        'battery_checkpoint': snapshot, 'stable_rom': str(ROM),
        'battery_sha256': w.sha256(saves.read_save(path)) if path.exists() else None})
    if version:
        release_info.register_release(version, w.sha256(candidate), date=release_log.get('release_date'),
                                      previous=w.sha256(previous) if previous is not None else None)
    print(f'Always open: {ROM}')
    print(f'Continue uses: {path}')
    if snapshot:
        print(f'Pre-build checkpoint: {snapshot}')
    else:
        print('No stable battery save yet. Adopt an existing .dsv or save in-game once.')
    return 0


def launch(config=CONFIG, store=saves.STORE, preset='current'):
    assert_closed()
    if preset not in LAUNCH_PRESETS: raise ValueError('Unknown DeSmuME launch preset')
    data = json.loads(Path(config).read_text(encoding='utf-8'))
    exe = emulator_path(data.get('emulator', ''))
    path = current_save(config)
    if not ROM.is_file(): raise ValueError('Stable ROM has not been built')
    w.validate_rom(ROM.read_bytes(), target=True)
    if path.exists():
        inspect_save(path)
        print(f'Progress backed up: {preserve(path, "before-play", store)}')
    subprocess.Popen([str(exe), *LAUNCH_PRESETS[preset], str(ROM)], cwd=str(exe.parent))
    print('Opened the stable ROM in DeSmuME. Choose Continue, then save in-game before closing.')
    if preset != 'current': print(f'Preview preset: {preset}; performance and visuals still need player checks.')
    return 0


def list_snapshots(store=saves.STORE):
    if not Path(store).exists():
        print('No checkpoints yet.')
        return
    for directory in sorted(Path(store).iterdir(), key=lambda p: p.name):
        if directory.is_dir():
            metadata, _ = saves.load_snapshot(directory.name, store)
            print(f'{directory.name}: {metadata["size"]} bytes; {metadata["sha256"]}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('configure', help='Remember the actual Battery folder')
    p.add_argument('--battery-dir', required=True)
    p.add_argument('--emulator', help='Actual absolute DeSmuME .exe path for the launcher')
    p = commands.add_parser('adopt', help='Copy existing .dsv progress to the stable ROM')
    p.add_argument('save')
    p = commands.add_parser('build', help='Back up progress and rebuild the same ROM')
    p.add_argument('--mods', default='mods')
    for command in ('checkpoint', 'restore'):
        p = commands.add_parser(command)
        p.add_argument('name')
    commands.add_parser('list')
    commands.add_parser('status')
    p = commands.add_parser('launch')
    p.add_argument('--preset', choices=LAUNCH_PRESETS, default='current')
    args = parser.parse_args(argv)
    try:
        if args.command in ('adopt', 'checkpoint', 'restore', 'configure'):
            assert_closed()
        if args.command == 'configure':
            print(f'Stable battery save: {configure(args.battery_dir, emulator=args.emulator)}')
        elif args.command == 'build':
            return build(args.mods)
        elif args.command == 'list':
            list_snapshots()
        elif args.command == 'launch':
            return launch(preset=args.preset)
        else:
            path = current_save()
            if args.command == 'adopt':
                name, safety = adopt(args.save, path)
                print(f'Copied/verified progress to {path}; source retained as {name}')
                if safety:
                    print(f'Previous stable save retained as {safety}')
            elif args.command == 'checkpoint':
                inspect_save(path)
                metadata = saves.backup(path, args.name)
                print(f'Checkpoint {args.name}: {metadata["size"]} bytes; {metadata["sha256"]}')
            elif args.command == 'restore':
                Dsv.parse(saves.load_snapshot(args.name)[1])
                safety = saves.restore(args.name, path)
                print(f'Restored/verified {args.name}. Open {ROM} and choose Continue.')
                if safety:
                    print(f'Previous progress retained as {safety}')
            else:
                print(f'ROM: {ROM}\nSave: {path}')
                if path.exists():
                    parsed = inspect_save(path)
                    print(f'{len(parsed.raw)} bytes; SHA256 {w.sha256(parsed.raw)}; DSV v0 payload {len(parsed.payload)} bytes')
                else:
                    print('No battery save at the stable filename yet.')
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
