import struct
import unittest

import mod
from tools import room_catalog as c


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private ROM not present')
class RoomCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom, _, manifest = mod.load_clean()
        at, _, _, size = struct.unpack_from('<4I', rom, 0x20)
        cls.arm9 = rom[at:at + size]
        cls.names = [e['name'] for e in manifest['entries']]

    def test_all_native_rooms_and_known_training_mapping(self):
        entries = c.parse(self.arm9, self.names)
        self.assertEqual(len(entries), 75)
        training = next(e for e in entries if e.name == 'Test_Combat01')
        self.assertEqual(training.index, 70)
        self.assertEqual(training.address, 0x02130DA4)
        self.assertEqual(self.names[training.minimap], 'MMPlaceholder.cbmp')
        self.assertEqual(next(e.index for e in entries if e.name == 'Sewer_Map07'), 57)
        self.assertEqual(len({e.name for e in entries}), 75)

    def test_out_of_bounds_pointer_and_duplicate_rejected(self):
        for value in (0, 0x04000000, 0x02130D05):
            raw = bytearray(self.arm9)
            struct.pack_into('<I', raw, c.LOOKUP - 0x02000000, value)
            with self.assertRaises(ValueError): c.parse(raw, self.names)
        raw = bytearray(self.arm9)
        raw[c.LOOKUP - 0x02000000:c.LOOKUP - 0x02000000 + 4] = raw[c.LOOKUP - 0x02000000 + 4:c.LOOKUP - 0x02000000 + 8]
        with self.assertRaises(ValueError): c.parse(raw, self.names)


if __name__ == '__main__': unittest.main()
