"""Minimal lossless NSBTX palette editing; no model/texture re-encoding.

TEX0/dictionary layout cross-checked against ndspy and apicula (see notes).
Unknown header/dictionary bytes stay in the raw source. Preview supports I8 only.
"""
from __future__ import annotations
from dataclasses import dataclass
import struct
import zlib
from pathlib import Path
from . import wos_tool as w


def dictionary(data: bytes, start: int, entry_size: int) -> list[tuple[str, bytes]]:
    w.check_range(data, start, 12, 'Nitro dictionary')
    count, size = data[start + 1], w.u16(data, start + 2)
    w.check_range(data, start, size, 'Nitro dictionary size')
    nodes_size = w.u16(data, start + 6)
    if w.u16(data, start + 4) != 8 or nodes_size != 12 + count * 4:
        raise ValueError('Unsupported Nitro dictionary node layout')
    pos = start + nodes_size
    w.check_range(data, pos, 4, 'Nitro dictionary entry header')
    if w.u16(data, pos) != entry_size or w.u16(data, pos + 2) != 4 + count * entry_size:
        raise ValueError('Invalid Nitro dictionary entry sizes')
    pos += 4
    names_start = pos + count * entry_size
    if names_start + count * 16 != start + size: raise ValueError('Invalid Nitro dictionary name bounds')
    rows = []
    for i in range(count):
        name = data[names_start + i * 16:names_start + (i + 1) * 16].rstrip(b'\0').decode('ascii')
        rows.append((name, data[pos + i * entry_size:pos + (i + 1) * entry_size]))
    if len({name for name, _ in rows}) != count: raise ValueError('Duplicate Nitro dictionary names')
    return rows


@dataclass(frozen=True)
class TextureArchive:
    raw: bytes
    tex0_start: int
    palette_start: int
    palette_size: int
    textures: tuple[dict, ...]
    palettes: tuple[dict, ...]

    @classmethod
    def parse(cls, raw: bytes):
        w.check_range(raw, 0, 20, 'NSBTX header')
        if raw[:4] != b'BTX0' or w.u16(raw, 4) != 0xfeff or w.u16(raw, 6) != 1:
            raise ValueError('Expected little-endian NSBTX version 1')
        if w.u32(raw, 8) != len(raw) or w.u16(raw, 12) != 16 or w.u16(raw, 14) != 1:
            raise ValueError('Unsupported NSBTX size/header/block count')
        start = w.u32(raw, 16)
        w.check_range(raw, start, 0x3c, 'TEX0 header')
        if start < 20 or raw[start:start + 4] != b'TEX0' or start + w.u32(raw, start + 4) != len(raw):
            raise ValueError('Invalid TEX0 block bounds')
        block = raw[start:]
        tex_offset, tex_size = w.u32(block, 0x14), w.u16(block, 0x0c) * 8
        compressed_offset, compressed_size = w.u32(block, 0x24), w.u16(block, 0x1c) * 8
        compressed_indices = w.u32(block, 0x28)
        palette_offset, palette_size = w.u32(block, 0x38), w.u16(block, 0x30) * 8
        pools = [(tex_offset, tex_size, 'texture data'), (compressed_offset, compressed_size, 'compressed texture data'),
                 (compressed_indices, compressed_size // 2, 'compressed indices'), (palette_offset, palette_size, 'palette')]
        for off, size, label in pools:
            w.check_range(block, off, size, label)
            if size and off < 0x3c: raise ValueError(f'{label} overlaps TEX0 header')
        spans = sorted((off, off + size, label) for off, size, label in pools if size)
        if any(a[1] > b[0] for a, b in zip(spans, spans[1:])):
            raise ValueError('Overlapping TEX0 data pools')
        tex_dict, pal_dict = w.u16(block, 0x0e), w.u32(block, 0x34)
        textures = []
        for name, entry in dictionary(block, tex_dict, 8):
            off, params, unknown = struct.unpack('<HHI', entry)
            width, height, fmt = 8 << ((params >> 4) & 7), 8 << ((params >> 7) & 7), (params >> 10) & 7
            bpp = {1: 8, 2: 2, 3: 4, 4: 8, 5: 2, 6: 8, 7: 16}.get(fmt)
            if bpp is None: raise ValueError('Unknown Nitro texture pixel format 0')
            size = width * height * bpp // 8
            pool_offset, pool_size = (compressed_offset, compressed_size) if fmt == 5 else (tex_offset, tex_size)
            if off * 8 + size > pool_size: raise ValueError('Texture exceeds data pool')
            if fmt == 5 and off * 4 + size // 2 > compressed_size // 2: raise ValueError('Texture indices exceed pool')
            textures.append({'name': name, 'width': width, 'height': height, 'format': fmt, 'params': params,
                             'offset': start + pool_offset + off * 8, 'size': size, 'unknown_u32': unknown})
        palettes = []
        rows = dictionary(block, pal_dict, 4)
        starts = sorted({w.u16(entry, 0) * 8 for _, entry in rows} | {palette_size})
        for name, entry in rows:
            off = w.u16(entry, 0) * 8
            if off >= palette_size: raise ValueError('Palette offset outside pool')
            end = next(value for value in starts if value > off)
            palettes.append({'name': name, 'offset': start + palette_offset + off, 'size': end - off,
                             'unknown_u16': w.u16(entry, 2)})
        # Editing is confined to a data pool that cannot overlap either dictionary.
        for off in (tex_dict, pal_dict):
            end = off + w.u16(block, off + 2)
            if palette_size and off < palette_offset + palette_size and end > palette_offset:
                raise ValueError('Palette pool overlaps Nitro dictionary')
        return cls(raw, start, start + palette_offset, palette_size, tuple(textures), tuple(palettes))

    def to_bytes(self) -> bytes:
        return self.raw

    def replace_palette(self, colors: bytes) -> bytes:
        if len(colors) != self.palette_size: raise ValueError('Palette edits must retain byte length')
        output = self.raw[:self.palette_start] + colors + self.raw[self.palette_start + self.palette_size:]
        TextureArchive.parse(output)
        return output


def green_suit(data: bytes) -> tuple[bytes, dict]:
    archive = TextureArchive.parse(data)
    if (len(archive.textures) != 1 or len(archive.palettes) != 1
            or archive.textures[0]['name'] != 'Cartoon64' or archive.palettes[0]['name'] != 'Cartoon64_pl'
            or (archive.textures[0]['format'], archive.textures[0]['width'], archive.textures[0]['height']) != (4, 64, 64)
            or archive.palette_size != 512):
        raise ValueError('Green-suit experiment expects the verified spd.nsbtx layout')
    palette = bytearray(data[archive.palette_start:archive.palette_start + archive.palette_size])
    edits = []
    for i in range(len(palette) // 2):
        old = w.u16(palette, i * 2)
        red, green, blue = old & 31, (old >> 5) & 31, (old >> 10) & 31
        if red >= 8 and red > green + 4 and red > blue + 4:
            new = (old & 0x8000) | green | (red << 5) | (blue << 10)
            struct.pack_into('<H', palette, i * 2, new)
            edits.append({'index': i, 'offset': archive.palette_start + i * 2, 'old_bgr555': old, 'new_bgr555': new})
    if not edits: raise ValueError('No red palette colors found')
    changed = archive.replace_palette(bytes(palette))
    return changed, {'asset': 'spd.nsbtx', 'old_sha256': w.sha256(data), 'new_sha256': w.sha256(changed),
                     'old_size': len(data), 'new_size': len(changed), 'palette_start': archive.palette_start,
                     'palette_size': archive.palette_size, 'color_edits': edits,
                     'boot_evidence': 'See archived VISIBLE_MOD.md and reference/visible_mod_report.json',
                     'rule': 'swap red/green for r>=8, r>g+4, r>b+4; preserve bit15'}


def png_rgb(width: int, height: int, rgb: bytes) -> bytes:
    if len(rgb) != width * height * 3: raise ValueError('PNG RGB dimensions mismatch')
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    scanlines = b''.join(b'\0' + rgb[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(scanlines, 9)) + chunk(b'IEND', b''))


def preview(data: bytes, path: Path, scale=4) -> None:
    archive = TextureArchive.parse(data)
    if len(archive.textures) != 1 or len(archive.palettes) != 1 or archive.textures[0]['format'] != 4:
        raise ValueError('Preview supports one I8 texture and one palette only')
    texture, palette = archive.textures[0], archive.palettes[0]
    indices = data[texture['offset']:texture['offset'] + texture['size']]
    rgb = bytearray()
    for y in range(texture['height']):
        row = bytearray()
        for x in range(texture['width']):
            i = indices[y * texture['width'] + x]
            if i * 2 + 2 > palette['size']: raise ValueError('Pixel index outside palette')
            color = w.u16(data, palette['offset'] + i * 2)
            components = [(color >> shift) & 31 for shift in (0, 5, 10)]
            pixel = bytes((v << 3) | (v >> 2) for v in components)
            row.extend(pixel * scale)
        rgb.extend(row * scale)
    w.atomic_write(path, png_rgb(texture['width'] * scale, texture['height'] * scale, bytes(rgb)))
