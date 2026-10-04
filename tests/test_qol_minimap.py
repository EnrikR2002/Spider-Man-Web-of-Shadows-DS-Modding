import struct
import tempfile
import unittest
from pathlib import Path
import mod
from tools import qol_minimap as ui


class TileTests(unittest.TestCase):
    def test_independent_tile_order_and_nibbles(self):
        # Four constant tiles in a 16x16 image, independently constructed.
        raw = b'\x21' * 32 + b'\x43' * 32 + b'\x65' * 32 + b'\x87' * 32
        expected = bytes([1, 2] * 4 + [3, 4] * 4) * 8 + bytes([5, 6] * 4 + [7, 8] * 4) * 8
        self.assertEqual(ui.decode_tiles(raw, 16, 16), expected)
        self.assertEqual(ui.encode_tiles(expected, 16, 16), raw)

    def test_roundtrip_and_invalid_inputs(self):
        for width, height in ((8, 24), (16, 16), (24, 32)):
            raw = bytes(i % 256 for i in range(width * height // 2))
            self.assertEqual(ui.encode_tiles(ui.decode_tiles(raw, width, height), width, height), raw)
        for width, height in ((0, 8), (7, 8), (8, 9), (264, 8)):
            with self.assertRaises(ValueError): ui.decode_tiles(b'', width, height)
        with self.assertRaises(ValueError): ui.decode_tiles(bytes(31), 8, 8)
        with self.assertRaises(ValueError): ui.encode_tiles(bytes([16]) * 64, 8, 8)
        with self.assertRaises(ValueError): ui.encode_tiles(bytes(63), 8, 8)

    def test_palette_confinement_and_inverse(self):
        original = struct.pack('<16H', *[0x8000 + i for i in range(16)])
        changed = ui.replace_color(original, 1, 0x03ff)
        self.assertEqual(changed[:2], original[:2]); self.assertEqual(changed[4:], original[4:])
        self.assertEqual(struct.unpack_from('<H', changed, 2)[0], 0x83ff)
        self.assertEqual(ui.replace_color(changed, 1, 1), original)
        for palette, index, color in ((bytes(30), 1, 0), (original, 16, 0), (original, 0, 0x8000)):
            with self.assertRaises(ValueError): ui.replace_color(palette, index, color)

    def test_overlay_guard_and_revert(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.pal'
            ui.guarded_overlay(path, b'old', b'new')
            ui.guarded_overlay(path, b'old', b'new')
            self.assertEqual(path.read_bytes(), b'new')
            ui.guarded_overlay(path, b'old', b'new', revert=True)
            self.assertFalse(path.exists())
            path.write_bytes(b'another edit')
            for revert in (False, True):
                with self.assertRaises(ValueError): ui.guarded_overlay(path, b'old', b'new', revert)
            self.assertEqual(path.read_bytes(), b'another edit')


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private clean ROM not present')
class LocalIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom, cls.glob, cls.manifest = mod.load_clean()
        cls.icons = ui.load_icons(cls.glob, cls.manifest)

    def test_known_families_lossless_and_strict(self):
        for stem, icon in self.icons.items():
            blobs = icon.to_bytes()
            self.assertEqual(ui.KnownIcon.parse(stem, *blobs).to_bytes(), blobs)
            self.assertEqual(icon.compressed.replace_decoded(ui.encode_tiles(icon.indices, icon.width, icon.height)), blobs[0])
            self.assertTrue(icon.preview().startswith(b'\x89PNG\r\n\x1a\n'))
            altered = bytes([blobs[1][0] ^ 1]) + blobs[1][1:]
            with self.assertRaises(ValueError): ui.KnownIcon.parse(stem, blobs[0], altered, blobs[2])
        with self.assertRaises(ValueError): ui.KnownIcon.parse('Unknown', b'', b'', b'')

    def test_one_asset_build_and_exact_revert(self):
        icon = self.icons['MissionMiniMapIcon']; changed = ui.yellow_mission(icon)
        self.assertEqual([i for i, (a, b) in enumerate(zip(icon.palette, changed)) if a != b], [2, 3])
        self.assertEqual(ui.replace_color(changed, 1, 0x001f), icon.palette)
        result, _, report = mod.create_build(self.rom, self.glob, self.manifest, {ui.ASSET: changed})
        self.assertNotEqual(result, self.rom)
        self.assertEqual([e['name'] for e in report['replaced_assets']], [ui.ASSET])
        self.assertEqual(report['unchanged_resource_count'], 3732)
        # Same-size palette changes must leave every other ROM byte intact.
        e = next(e for e in self.manifest['entries'] if e['name'] == ui.ASSET)
        base = report['nitrofs'][0]['start'] + e['offset']
        self.assertEqual(result[:base], self.rom[:base])
        self.assertEqual(result[base + 32:], self.rom[base + 32:])
        reverted, _, _ = mod.create_build(self.rom, self.glob, self.manifest, {})
        self.assertEqual(reverted, self.rom)