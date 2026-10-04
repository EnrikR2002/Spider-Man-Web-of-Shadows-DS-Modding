#!/usr/bin/env python3
"""Bounded minimap inspection and one-entry palette experiment, standard library only.

The tiled preview is an empirically coherent interpretation, not a general DAT
parser. Only two hash-identified clean CS5E families are accepted. Unknown DAT
bytes and compressed pixel bytes are never edited by the experiment.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mod
from tools import grip_compression as gc
from tools import wos_tool as w
from tools.nitro_texture import png_rgb

PROFILES = {
    'SpideyMiniMapIcon': (16, 16, (
        '1ea6731d441a4ae29e0e6d3573db1c62a3c10933ba658a73b2ad4f8a5ba547cd',
        'aa6255b67bd0ee9bff6fa8e98ad3a4f2a58d535acb22f714bbbcc64553246a4e',
        'aefeb959fb76176f1047aa7c14d26d48154f04d173d5484fabba1f727f5877ff')),
    'MissionMiniMapIcon': (8, 24, (
        '019a636b7dbc96fbb238999518325d56ea45a10faf826c77bfd8966d6aca0520',
        '37bded68980aad4e98062fe0f38ff544615b51edc28398c5be14d350bc963a06',
        '5072156a663205facf22310c98913e01febb028c74edd1c196e7db26985b5787')),
}
EXTENSIONS = ('.2lz', '.dat', '.pal')
EXPERIMENT = w.PROJECT / 'build/qol-mission-icon'
OVERLAY = EXPERIMENT / 'mods'
ASSET = 'MissionMiniMapIcon.pal'


def tile_positions(width, height):
    if not (8 <= width <= 256 and 8 <= height <= 256 and width % 8 == height % 8 == 0):
        raise ValueError('Tiled dimensions must be multiples of 8 within 8..256')
    return [((y // 8) * (width // 8) + x // 8) * 64 + (y % 8) * 8 + x % 8
            for y in range(height) for x in range(width)]


def decode_tiles(data, width, height):
    positions = tile_positions(width, height)
    if len(data) != width * height // 2: raise ValueError('4bpp tile payload length mismatch')
    return bytes((data[n // 2] >> (4 * (n % 2))) & 15 for n in positions)


def encode_tiles(indices, width, height):
    positions = tile_positions(width, height)
    if len(indices) != width * height or any(i > 15 for i in indices):
        raise ValueError('Expected exactly width*height indices within 0..15')
    out = bytearray(width * height // 2)
    for i, n in zip(indices, positions): out[n // 2] |= i << (4 * (n % 2))
    return bytes(out)


def replace_color(palette, index, color):
    if len(palette) != 32 or not 0 <= index < 16 or not 0 <= color <= 0x7fff:
        raise ValueError('Expected a 16-entry palette, valid index and 15-bit color')
    out = bytearray(palette)
    old = w.u16(palette, index * 2)
    struct.pack_into('<H', out, index * 2, (old & 0x8000) | color)
    return bytes(out)


@dataclass(frozen=True)
class KnownIcon:
    stem: str
    width: int
    height: int
    compressed: gc.CompressedBlob
    metadata: bytes
    palette: bytes
    indices: bytes

    @classmethod
    def parse(cls, stem, compressed, metadata, palette):
        if stem not in PROFILES: raise ValueError('Unsupported minimap family')
        width, height, hashes = PROFILES[stem]
        if tuple(w.sha256(b) for b in (compressed, metadata, palette)) != hashes:
            raise ValueError('Minimap family differs from the verified clean profile')
        if metadata[:2] != bytes((width, height)) or len(palette) != 32:
            raise ValueError('Profile dimensions/palette mismatch')
        blob = gc.CompressedBlob.parse(compressed)
        indices = decode_tiles(blob.decoded, width, height)
        if encode_tiles(indices, width, height) != blob.decoded:
            raise ValueError('Tile interpretation failed exact round trip')
        return cls(stem, width, height, blob, metadata, palette, indices)

    def to_bytes(self):
        return self.compressed.to_bytes(), self.metadata, self.palette

    def preview(self, palette=None, scale=12):
        """Index zero drawn on checkerboard; transparency is a preview hypothesis."""
        palette = self.palette if palette is None else palette
        if len(palette) != 32 or not 1 <= scale <= 16: raise ValueError('Invalid preview palette/scale')
        rgb = bytearray()
        for y in range(self.height):
            row = bytearray()
            for x in range(self.width):
                index = self.indices[y * self.width + x]
                color = w.u16(palette, index * 2)
                shade = 72 + 24 * ((x // 4 + y // 4) % 2)
                pixel = bytes([shade] * 3) if index == 0 else bytes(
                    ((color >> shift) & 31) * 255 // 31 for shift in (0, 5, 10))
                row.extend(pixel * scale)
            rgb.extend(row * scale)
        return png_rgb(self.width * scale, self.height * scale, bytes(rgb))


def load_icons(glob, manifest):
    entries = {e['name']: e for e in manifest['entries']}
    icons = {}
    for stem in PROFILES:
        blobs = []
        for ext in EXTENSIONS:
            e = entries[stem + ext]; blobs.append(glob[e['offset']:e['offset'] + e['size']])
        icons[stem] = KnownIcon.parse(stem, *blobs)
    return icons


def yellow_mission(icon):
    if icon.stem != 'MissionMiniMapIcon': raise ValueError('Expected the mission marker profile')
    if set(icon.indices) != {0, 1, 3} or w.u16(icon.palette, 2) != 0x001f:
        raise ValueError('Mission marker fill differs from the verified baseline')
    # One used fill entry: red -> yellow; no changes to index 0 or black outline 3.
    return replace_color(icon.palette, 1, 0x03ff)


def guarded_overlay(path, original, changed, revert=False):
    """Never overwrite/delete a different edit; exact known experiment only."""
    w.safe_output(path)
    if path.exists() and path.read_bytes() not in (original, changed):
        raise ValueError('Experiment overlay has a different edit; refusing to overwrite/remove it')
    if revert:
        if path.exists(): path.unlink()
    else:
        w.atomic_write(path, changed)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inspect', 'experiment', 'revert'))
    args = parser.parse_args(argv)
    try:
        _, glob, manifest = mod.load_clean()
        icons = load_icons(glob, manifest)
        mission = icons['MissionMiniMapIcon']; changed = yellow_mission(mission)
        if args.action == 'revert':
            guarded_overlay(OVERLAY / ASSET, mission.palette, changed, revert=True)
            print('Removed only the known experiment overlay. Previously built ROMs are unchanged.')
            return 0
        for stem, icon in icons.items():
            w.atomic_write(EXPERIMENT / (stem + '-before.png'), icon.preview())
        w.atomic_write(EXPERIMENT / 'MissionMiniMapIcon-after.png', mission.preview(changed))
        report = {
            'source_rom_sha256': mod.CLEAN_SHA256,
            'interpretation': '4bpp low nibble first; row-major 8x8 tiles; index-zero transparency unconfirmed',
            'families': [{'stem': stem, 'width_candidate': icon.width, 'height_candidate': icon.height,
                          'decoded_size': len(icon.compressed.decoded), 'used_indices': sorted(set(icon.indices)),
                          'source_sha256': dict(zip(EXTENSIONS, PROFILES[stem][2])),
                          'tile_roundtrip_exact': encode_tiles(icon.indices, icon.width, icon.height) == icon.compressed.decoded,
                          'compressed_noop_exact': icon.compressed.replace_decoded(icon.compressed.decoded) == icon.compressed.raw}
                         for stem, icon in icons.items()],
            'experiment': {'asset': ASSET, 'palette_index': 1, 'old_color': '0x001f', 'new_color': '0x03ff',
                           'old_sha256': w.sha256(mission.palette), 'new_sha256': w.sha256(changed),
                           'changed_byte_offsets': [i for i, (a, b) in enumerate(zip(mission.palette, changed)) if a != b],
                           'size_unchanged': len(changed) == len(mission.palette),
                           'runtime_visibility': 'Not established by this tool; inspect in-game mission markers.'}}
        if args.action == 'experiment':
            OVERLAY.mkdir(parents=True, exist_ok=True)
            existing = mod.overlay_files(OVERLAY, [e['name'] for e in manifest['entries']])
            if set(existing) - {ASSET}: raise ValueError('Isolated overlay contains additional assets')
            guarded_overlay(OVERLAY / ASSET, mission.palette, changed)
        w.write_json(EXPERIMENT / 'inspection.json', report)
        print(f'Previews/report: {EXPERIMENT}')
        if args.action == 'experiment': print(f'One-asset overlay: {OVERLAY}')
    except (OSError, ValueError, KeyError) as exc:
        print(f'error: {exc}', file=sys.stderr); return 1
    return 0


if __name__ == '__main__': raise SystemExit(main())