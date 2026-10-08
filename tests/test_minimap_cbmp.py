"""4bpp CBMP screens: lossless parse/rebuild of every minimap and bounded edits."""
import unittest

import mod
from tools.minimap_cbmp import Cbmp


class MinimapCbmpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, glob, manifest = mod.load_clean()
        cls.screens = {e['name']: glob[e['offset']:e['offset'] + e['size']]
                       for e in manifest['entries'] if e['name'].startswith('MM') and e['name'].endswith('.cbmp')}

    def test_every_minimap_screen_round_trips(self):
        self.assertGreaterEqual(len(self.screens), 40)
        for name, raw in self.screens.items():
            screen = Cbmp.parse(raw)
            self.assertEqual(screen.to_bytes(), raw, name)
            self.assertEqual(screen.unknown, 121, name)          # area screens 32x24; room maps can be taller
            self.assertEqual(len(screen.screen), screen.width * screen.height, name)
            self.assertEqual(len(screen.tiles), 32 * screen.count, name)

    def test_appended_tile_and_cell_survive_a_reencode(self):
        screen = Cbmp.parse(self.screens['MMSewer.cbmp'])
        pixels = [i % 16 for i in range(64)]
        grown, index = screen.with_tiles([pixels])
        grown = grown.with_screen({(3, 15): 0x1000 | index}).with_colors({0x11: 0x7FFF})
        again = Cbmp.parse(grown.to_bytes())
        self.assertEqual(again.tile(index), tuple(pixels))
        self.assertEqual(again.screen[15 * 32 + 3], 0x1000 | index)
        self.assertEqual(again.palette[0x11], 0x7FFF)
        self.assertEqual(again.tiles[:len(screen.tiles)], screen.tiles)
        self.assertEqual(again.pixel_index(3 * 8 + 1, 15 * 8), 0x11)
        with self.assertRaises(ValueError): screen.with_screen({(0, 0): screen.count})
        with self.assertRaises(ValueError): screen.with_tiles([[16] * 64])


if __name__ == '__main__':
    unittest.main()
