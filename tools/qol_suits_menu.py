#!/usr/bin/env python3
"""Bounded CS5E text-slot edits and reversible suit palette prototypes."""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mod
from tools import wos_tool as w
from tools.nitro_texture import TextureArchive, preview
from tools.qol_minimap import load_icons, yellow_mission

BASE = 0x1064
COUNT = 1049
TEXT_HASH = '19474ce9a50c25538515e585727e4ad5878bc3bb7bb11dd987b72a7c1d556088'
DEST = mod.ROOT / 'build/qol-suits-menu'


class StringSlots:
    """Verified English/American profile only; unknown prefix and slot tails retained."""
    def __init__(self, raw):
        if w.sha256(raw) != TEXT_HASH:
            raise ValueError('Expected hash-identified clean CS5E English strings')
        self.raw = raw
        size = w.u32(raw, BASE)
        self.tree = tuple(struct.unpack_from('<HH', raw, i)
                          for i in range(BASE + 4, BASE + size, 4))
        self.offsets = tuple(BASE + v for v in struct.unpack_from(f'<{COUNT}I', raw, BASE + size))
        if self.offsets[0] != BASE + size + COUNT * 4 or any(
                not a < b <= len(raw) for a, b in zip(self.offsets, self.offsets[1:] + (len(raw),))):
            raise ValueError('Invalid string slot bounds')
        self.codes = {}
        def visit(node, bits, ancestors):
            if node in ancestors or node >= len(self.tree):
                raise ValueError('Invalid Huffman tree')
            for bit, value in enumerate(self.tree[node]):
                path = bits + (bit,)
                if value > 256:
                    visit(value - 256, path, ancestors + (node,))
                elif value in self.codes:
                    raise ValueError('Duplicate Huffman leaf')
                else:
                    self.codes[value] = path
        visit(0, (), ())
        self.texts = tuple(self.decode(raw, i) for i in range(COUNT))

    def decode(self, raw, index):
        start = self.offsets[index]
        end = self.offsets[index + 1] if index + 1 < COUNT else len(raw)
        output = bytearray()
        node = 0
        for byte in raw[start:end]:
            for k in range(8):
                value = self.tree[node][(byte >> k) & 1]
                if value > 256:
                    node = value - 256
                else:
                    output.append(value)
                    node = 0
                    if len(output) % 2 == 0 and output[-2:] == b'\0\0':
                        return output[:-2].decode('utf-16le')
        raise ValueError(f'Unterminated string slot {index}')

    def encode(self, text):
        bits = []
        for byte in text.encode('utf-16le') + b'\0\0':
            if byte not in self.codes:
                raise ValueError(f'Unsupported text byte {byte}')
            bits.extend(self.codes[byte])
        out = bytearray((len(bits) + 7) // 8)
        for i, bit in enumerate(bits):
            out[i // 8] |= bit << (i % 8)
        return bytes(out)

    def replace(self, edits):
        output = bytearray(self.raw)
        for index, text in edits.items():
            if not 0 <= index < COUNT:
                raise ValueError('String index out of range')
            if text == self.texts[index]:
                continue
            data = self.encode(text)
            start = self.offsets[index]
            end = self.offsets[index + 1] if index + 1 < COUNT else len(output)
            if len(data) > end - start:
                raise ValueError(f'Text exceeds original slot {index}')
            output[start:start + len(data)] = data
            if self.decode(output, index) != text:
                raise ValueError('Edited text failed round trip')
        return bytes(output)


def suit_palette(raw, invert=False):
    archive = TextureArchive.parse(raw)
    if (len(archive.textures), len(archive.palettes), archive.palette_size) != (1, 1, 512) or (
            archive.textures[0]['format'], archive.textures[0]['width'], archive.textures[0]['height']) != (4, 64, 64):
        raise ValueError('Expected one 64x64 I8 suit texture')
    palette = bytearray(raw[archive.palette_start:archive.palette_start + archive.palette_size])
    for i in range(256):
        old = w.u16(palette, i * 2)
        r, g, b = (old >> s & 31 for s in (0, 5, 10))
        if invert:
            # Negative luminance: light body, dark emblem/eyes, no blue/yellow cast.
            v = 31 - (r * 3 + g * 6 + b) // 10
            r = g = b = v
        elif r >= 8 and r > g + 4 and r > b + 4:
            r, g, b = min(31, r + 2), g // 2, b // 2
        elif b > r + 2:
            r, g, b = r // 2, g * 3 // 4, min(31, b + 3)
        elif min(r, g, b) >= 22:
            r, g, b = 29, 24, 12
        struct.pack_into('<H', palette, i * 2, (old & 0x8000) | r | g << 5 | b << 10)
    return archive.replace_palette(bytes(palette))


def main():
    _, glob, manifest = mod.load_clean()
    assets = {e['name']: glob[e['offset']:e['offset'] + e['size']] for e in manifest['entries']
              if e['name'] in ('American.strings', 'English.strings', 'spd.nsbtx', 'spdB.nsbtx')}
    strings = StringSlots(assets['American.strings'])
    DEST.mkdir(parents=True, exist_ok=True)
    w.atomic_write(DEST / 'text-inventory.txt', '\n'.join(f'{i}: {text!r}' for i, text in enumerate(strings.texts)).encode('utf-8'))
    if '--inspect' in sys.argv:
        print(f'Decoded {COUNT} strings: {DEST / "text-inventory.txt"}')
        return
    # IDs verified against decoded clean text; retain the game's button glyphs.
    edits = {
        121: 'Core',
        131: 'Press \ue605 to switch suits.',
        143: 'Red suit: Press \ue602 to grapple and break large objects.',
        146: 'Black suit: Press \ue602 to dash through red ichor walls.',
        149: 'Black suit: In mid-air, press \ue602 and Down on ¿ to break red ichor floors.',
        152: 'Raises maximum Life Orbs.',
        155: 'Raises attack damage.',
        158: 'Lowers damage taken.',
        161: 'Raises maximum health.',
        164: 'Press Up on ¿ and \ue601 together to launch an enemy.',
        167: 'While rolling, press \ue601 for a multi-hit kick.',
        170: 'In mid-air, press Down on ¿ and \ue601 for a 4-hit stomp.',
        173: 'Hold \ue604 to dodge repeatedly. Use Left or Right on ¿ to steer.',
        176: 'In mid-air, press \ue604 to dodge.',
        179: 'After a hit or knockdown, press \ue604 to recover and counter-attack.',
        182: 'In mid-air, press \ue600 to kick off an enemy backwards.',
        185: 'With an enemy grappled, press \ue601 to pull them in and knock them back.',
        188: 'With an enemy grappled, press Up on ¿ to launch them.',
        191: 'Red suit: In mid-air, press \ue602 to zip to an enemy and attack.',
        194: 'Red suit combo: \ue601, pause, \ue601, \ue601, \ue601.',
        197: 'Red suit combo: \ue601, pause, \ue601, then tap \ue601 repeatedly for rapid kicks.',
        200: 'Red suit: Raises attack speed.',
        203: 'Red suit: Maximum attack speed.',
        206: 'Black suit: After a Power Dash hit, press \ue602 to pull the enemy back and hit again.',
        209: 'Black suit: Press Up on ¿ and \ue602 together to launch an enemy without jumping.',
        215: 'Black suit combo: \ue601, \ue601, \ue601, pause, \ue601, \ue601.',
        218: 'Black suit combo: \ue601, \ue601, \ue601, pause, then tap \ue601 repeatedly for extra hits.',
        221: 'Black suit: Hold \ue601 during each strike to charge it.',
        224: 'Charge attacks reach full power in half the time.',
        227: 'On a wall or ceiling without ichor, use ¿ to crawl.',
        230: 'In mid-air, press \ue600 to swing from non-ichor surfaces. Hold \ue600 to keep swinging. Release to let go.',
        233: 'While still on a ceiling, press \ue600 to hang. Use Up or Down on ¿ to adjust web length.',
        236: 'Next to a wall, press \ue600 to jump off.',
        239: 'Hold Up on ¿ while running into a wall, or Dash into it.',
        242: 'Press \ue603 to lift an object. Press \ue601 or \ue603 to throw it.',
    }
    changed_text = strings.replace(edits)
    overlay = {name: changed_text for name in ('American.strings', 'English.strings')}
    overlay.update({name: suit_palette(assets[name], name == 'spdB.nsbtx') for name in ('spd.nsbtx', 'spdB.nsbtx')})
    mission = load_icons(glob, manifest)['MissionMiniMapIcon']
    assets['MissionMiniMapIcon.pal'] = mission.palette
    overlay['MissionMiniMapIcon.pal'] = yellow_mission(mission)
    folder = DEST / 'mods'
    folder.mkdir(exist_ok=True)
    # Refuse unknown existing files/edits, never alter the regular mods directory.
    for path in folder.iterdir():
        if not path.is_file() or path.name not in overlay or path.read_bytes() != overlay[path.name]:
            raise ValueError(f'Existing overlay differs: {path}')
    for name, data in overlay.items():
        w.atomic_write(folder / name, data)
    for name in ('spd.nsbtx', 'spdB.nsbtx'):
        preview(assets[name], DEST / f'{name}-before.png', 8)
        preview(overlay[name], DEST / f'{name}-after.png', 8)
    w.write_json(DEST / 'recipe.json', {'text_edits': [{'id': i, 'before': strings.texts[i], 'after': t} for i, t in edits.items()],
                 'assets': {n: {'before': w.sha256(assets[n]), 'after': w.sha256(d)} for n, d in overlay.items()},
                 'status': 'Palette prototypes; menu fit and black-suit runtime unverified'})
    print(f'Generated {len(overlay)} overlays; {len(edits)} text edits in {folder}')


if __name__ == '__main__':
    main()