#!/usr/bin/env python3
"""Opaque .sav/.dsv snapshots. Close your emulator before backup or restore.

No save parsing, conversion, editing, or emulator-path guessing. Snapshots are
private, immutable named directories with size/SHA256 verification. Every restore
of an existing file first snapshots its current bytes.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import wos_tool as w

STORE = w.PROJECT / 'work/save-backups'
SUFFIXES = {'.sav', '.dsv'}
MAX_SIZE = 16 * 1024 * 1024
STAGING_PREFIX = '.snapshot-'


def snapshot_path(store, name):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,95}', name):
        raise ValueError('Snapshot name must be 1..96 letters/digits/hyphens/underscores')
    w.safe_name(name)
    path = Path(store) / name
    if path.is_symlink(): raise ValueError('Snapshot symlinks are unsupported')
    if not path.resolve().is_relative_to(Path(store).resolve()):
        raise ValueError('Snapshot path escapes storage')
    w.safe_output(path)
    return path


def save_path(path):
    path = Path(path)
    if not path.is_absolute(): raise ValueError('Use an absolute save-file path')
    if path.suffix.lower() not in SUFFIXES: raise ValueError('Only .sav and .dsv files are supported')
    if path.is_symlink(): raise ValueError('Save symlinks are unsupported')
    w.safe_output(path)
    return path


def read_save(path):
    if not path.is_file(): raise ValueError(f'Save file does not exist: {path}')
    if not 1 <= path.stat().st_size <= MAX_SIZE: raise ValueError('Save size must be 1 byte..16 MiB')
    data = path.read_bytes()
    if not 1 <= len(data) <= MAX_SIZE: raise ValueError('Save changed size while reading')
    return data


def backup(source, name, store=STORE):
    source = save_path(source)
    directory = snapshot_path(store, name)
    if source.resolve().is_relative_to(Path(store).resolve()):
        raise ValueError('Source must be outside snapshot storage')
    data = read_save(source)
    metadata = {'schema_version': 1, 'source_path': str(source.resolve()),
                'suffix': source.suffix.lower(), 'size': len(data), 'sha256': w.sha256(data)}
    directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=STAGING_PREFIX, dir=directory.parent) as temporary:
        staged = Path(temporary) / name
        w.atomic_write(staged / ('save' + metadata['suffix']), data, (source,))
        w.write_json(staged / 'snapshot.json', metadata)
        load_snapshot(name, temporary)
        if directory.exists(): raise FileExistsError(f'Snapshot already exists: {directory}')
        staged.rename(directory)
    return metadata


def load_snapshot(name, store=STORE):
    directory = snapshot_path(store, name)
    meta_path = directory / 'snapshot.json'
    if meta_path.is_symlink(): raise ValueError('Snapshot metadata symlink unsupported')
    metadata = json.loads(meta_path.read_text(encoding='utf-8'))
    if not isinstance(metadata, dict) or metadata.get('schema_version') != 1:
        raise ValueError('Unsupported snapshot metadata')
    suffix = metadata.get('suffix')
    if suffix not in SUFFIXES: raise ValueError('Invalid snapshot suffix')
    data_path = directory / ('save' + suffix)
    if data_path.is_symlink(): raise ValueError('Snapshot data symlink unsupported')
    data = read_save(data_path)
    if len(data) != metadata.get('size') or w.sha256(data) != metadata.get('sha256'):
        raise ValueError('Snapshot size/SHA256 mismatch; refusing restore')
    return metadata, data


def restore(name, destination, store=STORE):
    destination = save_path(destination)
    if destination.resolve().is_relative_to(Path(store).resolve()):
        raise ValueError('Restore destination must be outside snapshot storage')
    metadata, data = load_snapshot(name, store)
    if destination.suffix.lower() != metadata['suffix']:
        raise ValueError('Save suffix differs: this tool does not convert .sav/.dsv formats')
    if destination.exists():
        current = read_save(destination)
        if current == data: return None  # Exact no-op; no extra safety snapshot.
        # Content-addressed names make repeated restores deterministic.
        safety = 'before-restore-' + destination.suffix.lower()[1:] + '-' + w.sha256(current)
        directory = snapshot_path(store, safety)
        if directory.exists():
            old_meta, old_data = load_snapshot(safety, store)
            if old_data != current or old_meta['suffix'] != destination.suffix.lower():
                raise ValueError('Existing safety snapshot differs; refusing restore')
        else:
            backup(destination, safety, store)
        # Do not overwrite if another process changed the save during backup.
        if read_save(destination) != current: raise ValueError('Save changed during backup; close the emulator')
    else:
        safety = None
    w.atomic_write(destination, data)
    if destination.read_bytes() != data: raise ValueError('Restored save verification failed')
    return safety


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('backup'); p.add_argument('save'); p.add_argument('name')
    p = commands.add_parser('restore'); p.add_argument('name'); p.add_argument('save')
    commands.add_parser('list')
    args = parser.parse_args(argv)
    try:
        if args.command == 'backup':
            metadata = backup(args.save, args.name)
            print(f'Backed up {args.name}: {metadata["size"]} bytes; SHA256 {metadata["sha256"]}')
        elif args.command == 'restore':
            safety = restore(args.name, args.save)
            print(f'Restored/verified {args.save}')
            if safety: print(f'Previous save preserved as {safety}')
        elif STORE.exists():
            for directory in sorted(STORE.iterdir(), key=lambda p: p.name):
                if directory.is_dir() and not directory.name.startswith(STAGING_PREFIX):
                    metadata, _ = load_snapshot(directory.name)
                    print(f'{directory.name} {metadata["suffix"]} {metadata["size"]} bytes {metadata["sha256"]}')
        else:
            print('No snapshots yet.')
    except (OSError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr); return 1
    return 0


if __name__ == '__main__': raise SystemExit(main())
