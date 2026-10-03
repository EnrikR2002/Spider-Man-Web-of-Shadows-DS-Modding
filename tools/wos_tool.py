#!/usr/bin/env python3
"""Lossless CS5E NitroFS/Glob tooling. Python standard library only."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import struct
import sys
import tempfile
from pathlib import Path

ALIGN = 0x200
PROJECT = Path(__file__).resolve().parents[1]


def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def p32(v): return struct.pack('<I', v)
def align_up(v, a=ALIGN): return (v + a - 1) & ~(a - 1)
def sha256(data): return hashlib.sha256(data).hexdigest()


def crc16(data: bytes) -> int:
    """NDS CRC16: initial 0xffff, reflected polynomial 0xa001."""
    crc = 0xffff
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ (0xa001 if crc & 1 else 0)
    return crc


def check_range(data, start, size, label):
    if start < 0 or size < 0 or start + size > len(data):
        raise ValueError(f'{label} out of bounds: 0x{start:X}+0x{size:X} (file 0x{len(data):X})')


def safe_name(name: str) -> str:
    """Reject path traversal and Windows aliases/devices, rather than sanitizing."""
    reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {f'{p}{i}' for p in ('COM', 'LPT') for i in range(1, 10)}
    if not name or '\\' in name:
        raise ValueError(f'Unsafe filename: {name!r}')
    for part in name.split('/'):
        if (not part or part in ('.', '..') or part[-1] in '. '
                or any(ord(c) < 32 or ord(c) > 126 or c in '<>:"|?*' for c in part)
                or part.split('.')[0].upper() in reserved):
            raise ValueError(f'Unsafe filename: {name!r}')
    return name


def safe_output(path: Path, sources=()) -> Path:
    resolved = path.resolve()
    if resolved.is_relative_to((PROJECT / 'original').resolve()):
        raise ValueError(f'Refusing to write inside original/: {path}')
    clean_rom = PROJECT / 'original/Spider-Man - Web of Shadows (USA) (En,Fr).nds'
    protected = tuple(sources) + ((clean_rom,) if clean_rom.exists() else ())
    for source in protected:
        if resolved == source.resolve() or (path.exists() and os.path.samefile(path, source)):
            raise ValueError(f'Refusing to overwrite input: {path}')
    return resolved


def atomic_write(path: Path, data: bytes, sources=()) -> None:
    dest = safe_output(path, sources)
    if dest.is_file() and dest.read_bytes() == data:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=dest.name + '.', suffix='.tmp', dir=dest.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.replace(temporary, dest)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def write_json(path, obj):
    atomic_write(path, (json.dumps(obj, indent=2, sort_keys=True) + '\n').encode('utf-8'))


def parse_header(rom: bytes) -> dict:
    check_range(rom, 0, 0x160, 'NDS header')
    h = {'title': rom[:12].rstrip(b'\0').decode('ascii', 'replace'),
         'gamecode': rom[12:16].decode('ascii', 'replace'),
         'maker': rom[16:18].decode('ascii', 'replace'),
         'device_capacity': rom[0x14], 'file_size': len(rom),
         'banner_offset': u32(rom, 0x68), 'used_rom_size': u32(rom, 0x80),
         'header_size': u32(rom, 0x84), 'header_crc16': u16(rom, 0x15e),
         'computed_header_crc16': crc16(rom[:0x15e])}
    for label, off, size in [('arm9', 0x20, 0x2c), ('arm7', 0x30, 0x3c),
                            ('fnt', 0x40, 0x44), ('fat', 0x48, 0x4c),
                            ('arm9_overlay', 0x50, 0x54), ('arm7_overlay', 0x58, 0x5c)]:
        h[label + '_offset'] = u32(rom, off)
        h[label + '_size'] = u32(rom, size)
        check_range(rom, h[label + '_offset'], h[label + '_size'], label)
    if h['fat_size'] % 8 or not h['fat_size']: raise ValueError('FAT must contain complete 8-byte entries')
    if h['fnt_size'] < 8: raise ValueError('FNT missing root directory')
    if not 0x160 <= h['header_size'] <= len(rom): raise ValueError('Invalid NDS header size')
    if not h['header_size'] <= h['used_rom_size'] <= len(rom): raise ValueError('Invalid used ROM size')
    return h


def nitrofs_paths(rom: bytes) -> dict[int, str]:
    h = parse_header(rom)
    fnt = rom[h['fnt_offset']:h['fnt_offset'] + h['fnt_size']]
    count = u16(fnt, 6)
    if not 1 <= count <= 4096: raise ValueError('Invalid FNT directory count')
    check_range(fnt, 0, count * 8, 'FNT directories')
    dirs = {0xf000 + i: struct.unpack_from('<IHH', fnt, i * 8) for i in range(count)}
    paths, visited = {}, set()
    def walk(did, prefix='', depth=0):
        if did not in dirs or did in visited or depth > 128:
            raise ValueError('Invalid, cyclic, repeated or too deep FNT directory')
        visited.add(did)
        pos, fid, _ = dirs[did]
        if pos < count * 8: raise ValueError('FNT subtable overlaps directory table')
        while True:
            check_range(fnt, pos, 1, 'FNT entry')
            length = fnt[pos]; pos += 1
            if length == 0: break
            n = length & 0x7f
            if not n: raise ValueError('Empty FNT name')
            check_range(fnt, pos, n, 'FNT name')
            name = fnt[pos:pos + n].decode('ascii'); pos += n
            if '/' in name: raise ValueError('FNT component contains slash')
            path = safe_name(prefix + name)
            if length & 0x80:
                check_range(fnt, pos, 2, 'FNT child directory')
                child = u16(fnt, pos); pos += 2
                if child not in dirs or dirs[child][2] != did: raise ValueError('FNT parent/child mismatch')
                walk(child, path + '/', depth + 1)
            else:
                if fid in paths or fid >= h['fat_size'] // 8: raise ValueError('Duplicate/out-of-range FNT file ID')
                paths[fid] = path; fid += 1
    walk(0xf000)
    if len(visited) != count or len({v.casefold() for v in paths.values()}) != len(paths):
        raise ValueError('Unreachable FNT directory or duplicate filename')
    return paths


def nitrofs_entries(rom: bytes) -> list[dict]:
    h, paths = parse_header(rom), nitrofs_paths(rom)
    out, protected = [], [(0, h['header_size'], 'header')]
    for part in ('arm9', 'arm7', 'fnt', 'fat', 'arm9_overlay', 'arm7_overlay'):
        if h[part + '_size']:
            protected.append((h[part + '_offset'], h[part + '_offset'] + h[part + '_size'], part))
    if h['banner_offset']:
        check_range(rom, h['banner_offset'], 2, 'banner version')
        sizes = {1: 0x840, 2: 0x940, 3: 0x1240, 0x103: 0x23c0}
        version = u16(rom, h['banner_offset'])
        if version not in sizes: raise ValueError(f'Unknown banner version: {version}')
        check_range(rom, h['banner_offset'], sizes[version], 'banner')
        protected.append((h['banner_offset'], h['banner_offset'] + sizes[version], 'banner'))
    for fid in range(h['fat_size'] // 8):
        start, end = struct.unpack_from('<II', rom, h['fat_offset'] + fid * 8)
        check_range(rom, start, end - start, f'FAT file {fid}')
        if end > h['used_rom_size']: raise ValueError(f'FAT file {fid} exceeds used ROM size')
        for pstart, pend, label in protected:
            if start < pend and end > pstart: raise ValueError(f'FAT file {fid} overlaps {label}')
        out.append({'id': fid, 'name': paths.get(fid, f'file_{fid:04d}.bin'),
                    'start': start, 'end': end, 'size': end - start})
    ordered = sorted(out, key=lambda e: e['start'])
    if any(a['end'] > b['start'] for a, b in zip(ordered, ordered[1:])): raise ValueError('Overlapping FAT resources')
    return out


def validate_rom(rom: bytes, *, target=False) -> dict:
    h, entries = parse_header(rom), nitrofs_entries(rom)
    if h['header_crc16'] != h['computed_header_crc16']: raise ValueError('NDS header CRC16 mismatch')
    if h['device_capacity'] > 15 or len(rom) != (128 * 1024 << h['device_capacity']):
        raise ValueError('ROM image does not match declared cartridge capacity')
    if target and (h['gamecode'] != 'CS5E' or h['title'] != 'SPIDERMANWOS'
                   or [e['name'] for e in entries] != ['Glob.bin', 'sound_data.sdat']):
        raise ValueError('Expected Spider-Man Web of Shadows USA CS5E layout')
    return {'header': h, 'nitrofs': entries, 'sha256': sha256(rom)}


def parse_glob(glob: bytes) -> tuple[list[int], list[str], int]:
    if len(glob) < 8: raise ValueError('Glob.bin is too small')
    table_size = u32(glob, 0)
    if table_size < 8 or table_size % 4 or table_size > len(glob): raise ValueError(f'Invalid Glob table size: {table_size}')
    offsets = list(struct.unpack_from(f'<{table_size // 4}I', glob, 0))
    if offsets[-1] != len(glob): raise ValueError('Last Glob offset != file size')
    if any(b < a for a, b in zip(offsets, offsets[1:])): raise ValueError('Glob offsets are not monotonic')
    n, candidates = len(offsets) - 1, []
    for i in range(n):
        if offsets[i + 1] - offsets[i] != n * 64: continue
        blob = glob[offsets[i]:offsets[i + 1]]
        try:
            names = []
            for j in range(n):
                record = blob[j * 64:(j + 1) * 64]
                if record[-1:] != b'\n' or record.count(b'\n') != 1: raise ValueError('Invalid filename record')
                names.append(safe_name(record.rstrip(b' \r\n\0').decode('ascii')))
            if names[i] != 'GlobFiles.txt' or len({x.casefold() for x in names}) != n: raise ValueError('Invalid filename mapping')
            candidates.append((names, i))
        except (UnicodeDecodeError, ValueError): continue
    if len(candidates) != 1: raise ValueError('Expected one valid embedded GlobFiles.txt filename table')
    names, index = candidates[0]
    return offsets, names, index


def pack_glob(names: list[str], blobs: list[bytes]) -> bytes:
    if len(names) != len(blobs) or not names: raise ValueError('Glob names/resource count mismatch')
    offsets = [(len(blobs) + 1) * 4]
    for blob in blobs: offsets.append(offsets[-1] + len(blob))
    if offsets[-1] > 0xffffffff: raise ValueError('Glob exceeds 32-bit offsets')
    result = struct.pack(f'<{len(offsets)}I', *offsets) + b''.join(blobs)
    if parse_glob(result)[1] != names: raise ValueError('Repacked Glob filename mapping differs from manifest')
    return result


def rebuild_rom(original: bytes, replacements: dict[str, bytes]) -> bytes:
    """Preserve placements; relocate successors only on collision, within capacity.

    Unknown gaps/prefix/tail stay from the source; growth consumes only 00/ff
    padding after used size. Shrinking leaves vacated bytes untouched.
    """
    report = validate_rom(original)
    h, entries = report['header'], report['nitrofs']
    if h['arm9_overlay_size'] or h['arm7_overlay_size'] or original[0x12] != 0:
        raise ValueError('Rebuilder supports DS images without overlays only')
    unknown = set(replacements) - {e['name'] for e in entries}
    if unknown: raise ValueError(f'Unknown NitroFS replacements: {sorted(unknown)}')
    if all(replacements.get(e['name'], original[e['start']:e['end']]) == original[e['start']:e['end']] for e in entries):
        return original
    ordered = sorted(entries, key=lambda e: e['start'])
    if any(e['start'] % ALIGN for e in ordered): raise ValueError('NitroFS starts are not 0x200 aligned')
    first = ordered[0]['start']
    for part in ('arm9', 'arm7', 'fnt', 'fat'):
        if h[part + '_offset'] + h[part + '_size'] > first: raise ValueError('Unsupported layout: metadata after first NitroFS file')
    if h['banner_offset'] >= first: raise ValueError('Unsupported layout: banner after first NitroFS file')
    plan, cursor = [], first
    for entry in ordered:
        blob = replacements.get(entry['name'], original[entry['start']:entry['end']])
        start = max(entry['start'], align_up(cursor)); end = start + len(blob)
        plan.append((entry, start, end, blob)); cursor = end
    used = max(h['used_rom_size'], align_up(cursor))
    if used > len(original): raise ValueError(f'Rebuilt used size 0x{used:X} exceeds cart capacity 0x{len(original):X}')
    if any(value not in (0, 255) for value in original[h['used_rom_size']:used]):
        raise ValueError('Growth would overwrite unknown non-padding bytes after used ROM size')
    out = bytearray(original)
    for entry, start, end, blob in plan:
        out[start:end] = blob
        struct.pack_into('<II', out, h['fat_offset'] + entry['id'] * 8, start, end)
    struct.pack_into('<I', out, 0x80, used)
    struct.pack_into('<H', out, 0x15e, crc16(out[:0x15e]))
    result = bytes(out)
    validate_rom(result)
    for entry in nitrofs_entries(result):
        old = next(e for e in entries if e['id'] == entry['id'])
        expected = replacements.get(entry['name'], original[old['start']:old['end']])
        if result[entry['start']:entry['end']] != expected: raise ValueError(f'Rebuilt resource mismatch: {entry["name"]}')
    return result


def glob_manifest(glob: bytes) -> dict:
    offsets, names, index = parse_glob(glob)
    entries = []
    for i, name in enumerate(names):
        blob = glob[offsets[i]:offsets[i + 1]]
        entries.append({'index': i, 'name': name, 'offset': offsets[i], 'size': len(blob),
                        'sha256': sha256(blob), 'magic_hex': blob[:8].hex()})
    return {'name_table_index': index, 'sha256': sha256(glob), 'entries': entries}


def extract_rom(rom: bytes, out: Path) -> None:
    report = validate_rom(rom); h = report['header']; safe_output(out)
    write_json(out / 'header.json', h)
    for part in ('arm9', 'arm7'):
        atomic_write(out / (part + '.bin'), rom[h[part + '_offset']:h[part + '_offset'] + h[part + '_size']])
    manifest = []
    for e in report['nitrofs']:
        blob = rom[e['start']:e['end']]
        atomic_write(out / 'nitrofs' / e['name'], blob)
        manifest.append(dict(e, sha256=sha256(blob)))
    write_json(out / 'nitrofs_manifest.json', manifest)


def unpack_glob(glob: bytes, out: Path) -> None:
    manifest = glob_manifest(glob); safe_output(out)
    for e in manifest['entries']:
        atomic_write(out / e['name'], glob[e['offset']:e['offset'] + e['size']])
    write_json(out / '_glob_manifest.json', manifest)


def repack_directory(src: Path) -> bytes:
    entries = json.loads((src / '_glob_manifest.json').read_text(encoding='utf-8'))['entries']
    if [e['index'] for e in entries] != list(range(len(entries))): raise ValueError('Manifest indices must be contiguous in original order')
    names = [safe_name(e['name']) for e in entries]; blobs = []
    for name in names:
        p = src / name
        if not p.resolve().is_relative_to(src.resolve()): raise ValueError(f'Resource path escapes extraction directory: {name}')
        blobs.append(p.read_bytes())
    return pack_glob(names, blobs)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__); sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('inspect-rom'); p.add_argument('rom')
    p = sp.add_parser('extract-rom'); p.add_argument('rom'); p.add_argument('-o', '--out', default='work/rom')
    p = sp.add_parser('unpack-glob'); p.add_argument('glob'); p.add_argument('-o', '--out', default='work/glob')
    p = sp.add_parser('repack-glob'); p.add_argument('dir'); p.add_argument('-o', '--out', default='build/Glob.bin')
    p = sp.add_parser('repack-rom'); p.add_argument('rom'); p.add_argument('--glob'); p.add_argument('--sdat'); p.add_argument('-o', '--out', default='build/Spider-Man-WoS-modded.nds')
    p = sp.add_parser('manifest'); p.add_argument('glob'); p.add_argument('-o', '--out', default='glob_manifest.csv')
    args = ap.parse_args(argv)
    try:
        if args.cmd == 'inspect-rom': print(json.dumps(validate_rom(Path(args.rom).read_bytes()), indent=2))
        elif args.cmd == 'extract-rom': extract_rom(Path(args.rom).read_bytes(), Path(args.out))
        elif args.cmd == 'unpack-glob': unpack_glob(Path(args.glob).read_bytes(), Path(args.out))
        elif args.cmd == 'repack-glob': atomic_write(Path(args.out), repack_directory(Path(args.dir)))
        elif args.cmd == 'repack-rom':
            replacements = {}
            if args.glob: replacements['Glob.bin'] = Path(args.glob).read_bytes()
            if args.sdat: replacements['sound_data.sdat'] = Path(args.sdat).read_bytes()
            if not replacements: raise ValueError('Provide --glob and/or --sdat')
            rom = Path(args.rom)
            atomic_write(Path(args.out), rebuild_rom(rom.read_bytes(), replacements), (rom,))
        elif args.cmd == 'manifest':
            manifest = glob_manifest(Path(args.glob).read_bytes())
            dest = safe_output(Path(args.out), (Path(args.glob),)); dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('w', newline='', encoding='utf-8') as stream:
                writer = csv.writer(stream); writer.writerow(['index', 'name', 'size', 'offset', 'magic_hex'])
                for e in manifest['entries']: writer.writerow([e['index'], e['name'], e['size'], hex(e['offset']), e['magic_hex']])
        if args.cmd != 'inspect-rom': print(f'{args.cmd} complete -> {args.out}')
    except (OSError, ValueError, KeyError, struct.error) as exc:
        print(f'error: {exc}', file=sys.stderr); return 1
    return 0


if __name__ == '__main__': raise SystemExit(main())
