"""Census of every native ARM9 word the mod has changed, release by release.

Reads the clean ROM and each retained release ROM (build/version-<v>-final,
build/version-<v> or build/releases/<sha>), compares the native image word by
word and records, for every changed site, its clean word, its word in each
release that changed it and where a patched branch now lands. It also maps the
appended extension image (file offset 0x1439A0, loaded at 0x0214F420) to the
release that last wrote each range. Run it after publishing to rewrite
reference/engine_hooks.json; query it with tools/engine_map.py. A new post-pass
reads its hook preimages here. See TECHNICAL "Engine map".
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASE = 0x02000000
MODULE_PARAMS = 0xB64      # autoload list start, list end, autoload data start (file addresses)
CATALOG = ROOT / 'reference/engine_hooks.json'
STABLE = ROOT / 'build/Spider-Man-WoS-modded.nds'
REGIONS = ((0x02000000, 'tcm'), (0x021193BC, 'code'), (0x02127920, 'rodata'), (0x0213E140, 'data'))  # USA section ends


def arm9_of(path: Path) -> bytes:
    """The ARM9 image of a ROM, read without loading the whole cartridge."""
    with open(path, 'rb') as handle:
        header = handle.read(0x40)
        offset, size = struct.unpack_from('<I', header, 0x20)[0], struct.unpack_from('<I', header, 0x2C)[0]
        handle.seek(offset)
        return handle.read(size)


def clean_arm9() -> bytes:
    """The clean CS5E ARM9, read from the ROM in original/ (FileNotFoundError in a fresh clone)."""
    import mod
    return arm9_of(mod.DEFAULT_ROM)


def layout(arm9: bytes) -> list[tuple[int, int, int]]:
    """(load address, file offset, size) of the static image and each autoload section."""
    start, end, source = (value - BASE for value in struct.unpack_from('<3I', arm9, MODULE_PARAMS))
    rows = [(BASE, 0, source)]
    for at in range(start, end, 12):
        address, size, _ = struct.unpack_from('<3I', arm9, at)
        rows.append((address, source, size))
        source += size
    return rows


def offset_of(arm9: bytes, address: int) -> int:
    """File offset of a load address in this image; raises for BSS or unmapped RAM."""
    for start, offset, size in reversed(layout(arm9)):
        if start <= address < start + size: return offset + address - start
    raise ValueError(f'{address:#010x} is not stored in this ARM9 image')


def branch_target(address: int, word: int):
    """Destination of an ARM B/BL word at address, else None."""
    if (word >> 25) & 7 != 5 or word >> 28 == 0xF: return None
    return (address + 8 + (((word & 0xFFFFFF) ^ 0x800000) - 0x800000) * 4) & 0xFFFFFFFF


def region(address: int) -> str:
    return next((name for end, name in REGIONS if address < end), 'tcm')


def address_of(arm9: bytes, offset: int) -> int:
    """Load address of a file offset in this image."""
    return next(start + offset - at for start, at, size in layout(arm9) if at <= offset < at + size)


def census(clean: bytes, releases: list[tuple[str, str, bytes]]) -> dict:
    """releases: [(version, label, arm9)] oldest first. Returns the hook catalog."""
    native_end = layout(clean)[-1][1] + layout(clean)[-1][2]      # the clean autoload list follows the data
    sites: dict[int, dict] = {}
    owner: list[int] = []
    previous, old_extension, target = clean, b'', None
    for index, (version, label, arm9) in enumerate(releases):
        for off in range(0, native_end, 4):
            if arm9[off:off + 4] != previous[off:off + 4]:
                site = sites.setdefault(off, dict(clean=clean[off:off + 4], history=[]))
                site['history'].append((version, struct.unpack_from('<I', arm9, off)[0]))
        sections = layout(arm9)
        extension = b''
        if len(sections) > len(layout(clean)):
            target, offset, size = sections[-1]
            extension = arm9[offset:offset + size]
        owner.extend([index] * (len(extension) - len(owner)))
        for at in range(0, min(len(extension), len(old_extension)), 16):
            if extension[at:at + 16] != old_extension[at:at + 16]:
                for i in range(at, min(at + 16, len(extension), len(old_extension))):
                    if extension[i] != old_extension[i]: owner[i] = index
        previous, old_extension = arm9, extension
    blocks, start = [], 0
    for i in range(1, len(owner) + 1):
        if i == len(owner) or owner[i] != owner[start]:
            blocks.append([target + start, target + i, releases[owner[start]][0]])
            start = i
    merged = []                                 # a few rewritten bytes inside a block stay with that block
    for block in blocks:
        if merged and (block[2] == merged[-1][2] or block[1] - block[0] < 64): merged[-1][1] = block[1]
        else: merged.append(block)
    labels = {version: label for version, label, _ in releases}
    current = releases[-1][2]
    rows = []
    for off in sorted(sites):
        site = sites[off]
        if current[off:off + 4] == site['clean']: continue      # changed once, restored since
        address = address_of(clean, off)
        word = struct.unpack_from('<I', current, off)[0]
        row = dict(address=f'0x{address:08x}', region=region(address), clean=site['clean'][::-1].hex(),
                   current=f'{word:08x}')
        # A patched branch, or a pointer word, that now lands in our extension image.
        goes = branch_target(address, word) if row['region'] in ('code', 'tcm') else None
        goes = next((g for g in (goes, word) if g is not None and target is not None
                     and target <= g < target + len(old_extension)), None)
        if MODULE_PARAMS <= off < MODULE_PARAMS + 12: goes = None      # autoload list bounds are file addresses
        if goes is not None:
            row['target'] = f'0x{goes:08x}'
            row['owner'] = next((v for a, b, v in merged if a <= goes < b), None)
        row['history'] = [[version, f'{value:08x}'] for version, value in site['history']]
        rows.append(row)
    return dict(
        schema_version=1,
        purpose='Native ARM9 words changed by the published mod and the extension-image layout. '
                'Generated by tools/arm9_hooks.py: never edit by hand. "current" is the preimage a new hook must expect.',
        clean_arm9_sha256=hashlib.sha256(clean).hexdigest(),
        release=releases[-1][0], arm9_sha256=hashlib.sha256(current).hexdigest(),
        releases=[[version, labels[version]] for version in labels],
        extension=dict(target=f'0x{target:08x}', end=f'0x{target + len(old_extension):08x}',
                       file_offset=f'0x{layout(current)[-1][1]:x}',
                       blocks=[[f'0x{a:08x}', f'0x{b:08x}', v] for a, b, v in merged]) if target else None,
        sites=rows)


def release_roms() -> list[tuple[str, str, Path]]:
    """(version, CHANGES title, ROM path) for every profile whose ROM is retained, oldest first."""
    from tools import release_info
    titles = dict(re.findall(r'^## v(\d+\.\d+\.\d+) - \S+ - (.+)$', (ROOT / 'docs/CHANGES.md').read_text(encoding='utf-8'), re.M))
    rows = []
    for info in release_info.PROFILE_INFO.values():
        version = info['version']
        paths = [ROOT / f'build/version-{version}-final/Versioned.nds', ROOT / f'build/version-{version}/Versioned.nds',
                 ROOT / f'build/releases/{info.get("rom_sha256")}/Spider-Man-WoS-modded.nds']
        path = next((p for p in paths if p.is_file()), None)
        if path: rows.append((version, titles.get(version, ''), path))
    return rows


def dumps(data: dict) -> str:
    """Stable JSON with one site per line: reviewable diffs."""
    sites = ',\n'.join('  ' + json.dumps(s, separators=(',', ':')) for s in data['sites'])
    head = json.dumps({k: v for k, v in data.items() if k != 'sites'}, indent=1)
    return head[:-2] + ',\n "sites": [\n' + sites + '\n ]\n}\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', type=Path, default=CATALOG)
    args = parser.parse_args(argv)
    roms = release_roms()
    releases = [(version, label, arm9_of(path)) for version, label, path in roms]
    if hashlib.sha256(releases[-1][2]).digest() != hashlib.sha256(arm9_of(STABLE)).digest():
        raise SystemExit(f'{roms[-1][2]} is not the stable ROM: build or retain the published release first')
    data = census(clean_arm9(), releases)
    args.out.write_text(dumps(data), encoding='utf-8', newline='\n')
    print(f'{len(data["sites"])} changed native sites over {len(releases)} releases -> {args.out}')


if __name__ == '__main__':
    main()
