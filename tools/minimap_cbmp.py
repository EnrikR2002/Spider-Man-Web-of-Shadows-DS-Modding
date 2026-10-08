"""CBMP minimap screens: parse, render and rebuild (standard library only).

Layout of the 4bpp screens (98 of 142 CBMP files, every minimap among them;
tests check each round-trips; the *_8/HUD/BlackBG UI screens differ):
u16 unknown (121 in every file), u16 tile count, 256 BGR555 colours (16
palettes), u16 width/height in 8x8 tiles, width*height u16 screen entries (NDS
text BG: tile 0..9, h/v flip 10/11, palette 12..15), u32 compressed length, a
Griptonite 0x60 PuCrunch body without its 4-byte type/size word (parameters,
RLE table, bitstream) that decodes to tile count * 32 bytes of 4bpp tiles,
then trailing bytes kept verbatim.

Area maps (MMSewer.cbmp etc.) give each room a 5-colour slot inside one
palette (first colour is the background); the game copies hidden/visited/
current colours into the slot named by the area room list. See TECHNICAL
"Minimap screens and area room lists".
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import grip_compression as gc
from tools.nitro_texture import png_rgb

TILE = 32


@dataclass(frozen=True)
class Cbmp:
    unknown: int
    palette: tuple
    width: int
    height: int
    screen: tuple
    tiles: bytes
    body: bytes            # original compressed body, reused while tiles are unchanged
    trailing: bytes

    @classmethod
    def parse(cls, raw):
        unknown, count = struct.unpack_from('<2H', raw)
        palette = struct.unpack_from('<256H', raw, 4)
        width, height = struct.unpack_from('<2H', raw, 516)
        at = 520 + 2 * width * height
        screen = struct.unpack_from(f'<{width * height}H', raw, 520)
        length = struct.unpack_from('<I', raw, at)[0]
        body = raw[at + 4:at + 4 + length]
        if len(body) != length: raise ValueError('Truncated CBMP body')
        tiles = gc.decode(struct.pack('<I', 0x60 | count * TILE << 8) + body)
        return cls(unknown, palette, width, height, screen, tiles, body, raw[at + 4 + length:])

    @property
    def count(self): return len(self.tiles) // TILE

    def to_bytes(self):
        body = self.body
        try: same = gc.decode(struct.pack('<I', 0x60 | self.count * TILE << 8) + body) == self.tiles
        except ValueError: same = False
        if not same: body = gc.encode_backrefs(self.tiles)[4:]
        return (struct.pack('<2H', self.unknown, self.count) + struct.pack('<256H', *self.palette)
                + struct.pack('<2H', self.width, self.height) + struct.pack(f'<{len(self.screen)}H', *self.screen)
                + struct.pack('<I', len(body)) + body + self.trailing)

    def tile(self, index):
        """64 colour indices (0..15), row-major."""
        raw = self.tiles[index * TILE:(index + 1) * TILE]
        return tuple((raw[i // 2] >> 4 * (i & 1)) & 15 for i in range(64))

    def with_tiles(self, pixels_list):
        """Append tiles (each 64 indices); returns (cbmp, first new index)."""
        out = bytearray(self.tiles)
        for pixels in pixels_list:
            if len(pixels) != 64 or any(not 0 <= p < 16 for p in pixels): raise ValueError('Tile needs 64 indices 0..15')
            out += bytes(pixels[i] | pixels[i + 1] << 4 for i in range(0, 64, 2))
        if len(out) // TILE > 1024: raise ValueError('Tile index exceeds 10 bits')
        return replace(self, tiles=bytes(out)), self.count

    def with_screen(self, cells):
        """cells: {(x, y): entry}."""
        screen = list(self.screen)
        for (x, y), entry in cells.items():
            if not (0 <= x < self.width and 0 <= y < self.height): raise ValueError('Cell outside the screen')
            if (entry & 0x3FF) >= self.count: raise ValueError('Screen entry names a missing tile')
            screen[y * self.width + x] = entry
        return replace(self, screen=tuple(screen))

    def with_colors(self, colors):
        """colors: {palette index 0..255: BGR555}."""
        palette = list(self.palette)
        for index, value in colors.items(): palette[index] = value
        return replace(self, palette=tuple(palette))

    def pixel_index(self, x, y):
        """Palette index (0..255) at screen pixel, or None for colour 0."""
        entry = self.screen[(y // 8) * self.width + x // 8]
        tx, ty = x % 8, y % 8
        if entry >> 10 & 1: tx = 7 - tx
        if entry >> 11 & 1: ty = 7 - ty
        c = self.tile(entry & 0x3FF)[ty * 8 + tx]
        return None if c == 0 else (entry >> 12) * 16 + c

    def render(self, colors=None, scale=1):
        """RGB PNG; colors overrides palette entries (e.g. visited room slots)."""
        palette = list(self.palette)
        for index, value in (colors or {}).items(): palette[index] = value
        def rgb(c): return bytes(((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31))
        rows = []
        for y in range(self.height * 8):
            row = b''.join(rgb(palette[i]) if (i := self.pixel_index(x, y)) is not None else b'\x10\x10\x18'
                           for x in range(self.width * 8))
            row = b''.join(row[i:i + 3] * scale for i in range(0, len(row), 3))
            rows.extend([row] * scale)
        return png_rgb(self.width * 8 * scale, self.height * 8 * scale, b''.join(rows))
