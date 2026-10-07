import struct
import unittest

import mod
from tools.room_collision import RoomCollision


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private clean ROM not present')
class RoomCollisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.rom, cls.glob, cls.manifest = mod.load_clean()

    def test_all_75_node_list_roundtrips(self):
        count = nodes = lists = 0
        for entry in self.manifest['entries']:
            if not entry['name'].endswith('.bsp'): continue
            raw = self.glob[entry['offset']:entry['offset'] + entry['size']]
            with self.subTest(room=entry['name']):
                parsed = RoomCollision.parse(raw)
                self.assertEqual(parsed.to_bytes(), raw)
                self.assertEqual(parsed.replace_unknown_word0(0, parsed.nodes[0][0]), raw)
                nodes += len(parsed.nodes)
                lists += len(parsed.lists)
            count += 1
        self.assertEqual((count, nodes, lists), (75, 8789, 5503))

    def test_controlled_edit_changes_only_one_word_and_rejects_bad_refs(self):
        entry = next(e for e in self.manifest['entries'] if e['name'] == 'Test_Combat01.bsp')
        raw = self.glob[entry['offset']:entry['offset'] + entry['size']]
        parsed = RoomCollision.parse(raw)
        changed = parsed.replace_unknown_word0(1, 180 * 4096 + 1)
        at = parsed.envelope.table_end + 12
        self.assertEqual(changed[:at], raw[:at])
        self.assertEqual(changed[at + 4:], raw[at + 4:])
        bad = bytearray(raw)
        struct.pack_into('<H', bad, parsed.envelope.region_offsets[0] + 2, len(parsed.nodes))
        with self.assertRaises(ValueError): RoomCollision.parse(bad)
        with self.assertRaises(ValueError): parsed.replace_unknown_word0(-1, 0)
        with self.assertRaises(ValueError): parsed.replace_unknown_word0(0, 1 << 31)


if __name__ == '__main__': unittest.main()
