import struct
import unittest

import mod
from tools import room_catalog, room_extension as r


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private ROM not present')
class RoomExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom, _, manifest = mod.load_clean()
        at, _, _, size = struct.unpack_from('<4I', rom, 0x20)
        cls.arm9 = rom[at:at + size]
        cls.names = [e['name'] for e in manifest['entries']]

    def test_probe_keeps_native_indices_and_invalid_sentinel(self):
        patches = r.probe_image(self.arm9, self.names)
        image = bytes.fromhex(patches[0]['hex'])
        native = room_catalog.parse(self.arm9, self.names)
        self.assertEqual(struct.unpack_from('<75I', image), tuple(e.address for e in native))
        self.assertEqual(struct.unpack_from('<I', image, 75 * 4)[0], 0)
        self.assertLessEqual(r.BASE + len(image), r.LIMIT)
        for name in r.ROOM_NAMES: self.assertIn(name.encode() + b'\0', image)
        # Each clone retains its complete native descriptor except its name.
        source = next(e for e in native if e.name == 'Test_Combat01')
        for i in range(5):
            at = 81 * 4 + i * 80
            self.assertEqual(image[at + 4:at + 80], source.raw[4:])

    def test_foreign_lookup_rejected(self):
        raw = bytearray(self.arm9)
        struct.pack_into('<I', raw, r.LOOKUP_LITERAL - 0x02000000, 0)
        with self.assertRaises(ValueError): r.probe_image(raw, self.names)


if __name__ == '__main__': unittest.main()
