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

    def room(self, name):
        entry = next(e for e in self.manifest['entries'] if e['name'] == name + '.bsp')
        return RoomCollision.parse(self.glob[entry['offset']:entry['offset'] + entry['size']])

    def test_every_node_stream_is_one_preorder_tree_over_all_lists(self):
        for entry in self.manifest['entries']:
            if entry['name'].endswith('.bsp'):
                with self.subTest(room=entry['name']):
                    self.room(entry['name'][:-4]).check_tree()
        broken = self.room('Test_Combat01')
        nodes = list(broken.nodes)
        nodes[0] = (nodes[0][0], nodes[0][1], nodes[0][2], 3)          # node 0 claims another node's list
        with self.assertRaises(ValueError):
            RoomCollision(broken.envelope, tuple(nodes), broken.lists).check_tree()

    def test_training_room_is_a_box_with_measured_walls(self):
        box = self.room('Test_Combat01')            # floor 0, ceiling 60, walls at 0 and 240 (Spidey stops at 3.5/236.5)
        self.assertEqual([box.solid_at(x, 10) is None for x in (-1, 1, 239, 241)], [False, True, True, False])
        self.assertEqual([box.solid_at(120, y) is None for y in (-1, 1, 59, 61)], [False, True, True, False])
        self.assertEqual(box.floor_below(120, 30), 0.25)
        with self.assertRaises(ValueError): box.floor_below(120, -5)
        moved = RoomCollision.parse(box.replace_unknown_word0(1, 180 * 4096 + 1))   # the lab's wall edit
        self.assertIsNotNone(moved.solid_at(200, 10))
        self.assertIsNone(moved.solid_at(170, 10))

    def test_hive_shaft_matches_what_spidey_measured(self):
        gate = self.room('Hive_Map02')              # lab 2026-10-11: walls, landings and falls with real movement
        self.assertIsNone(gate.solid_at(-3.5, 190))            # clung to the right wall at x -3.5 beside the pedestal
        self.assertIsNone(gate.solid_at(-36.5, 190))
        self.assertIsNotNone(gate.solid_at(0.5, 190))
        self.assertIsNotNone(gate.solid_at(-40.5, 190))
        self.assertEqual(gate.floor_below(-20, 190), 180.25)   # stood on the pedestal (position 185 = feet + 5)
        self.assertEqual(gate.floor_below(-15, 80), 60.25)     # landed at position 65 on the slanted wedge
        self.assertIsNotNone(gate.solid_at(-15, 58))           # slanted plane: negated (x, y) normal
        # The only way past the ledge at 96..100 is the 9-unit gap the red floor object closes.
        open_x = [x / 2 for x in range(-80, 1) if gate.solid_at(x / 2, 97) is None]
        self.assertEqual((min(open_x), max(open_x)), (-9.5, -0.5))
        self.assertEqual(gate.floor_below(-5, 110), 60.25)     # so without that object Spidey falls through

    def test_room_map_marks_entities_on_the_slice(self):
        from tools import room_collision
        blobs = {e['name']: self.glob[e['offset']:e['offset'] + e['size']] for e in self.manifest['entries']
                 if e['name'].startswith('Test_Combat01')}
        png, bounds = room_collision.room_map(blobs['Test_Combat01.bsp'], blobs['Test_Combat01_app.obj'], scale=1)
        self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack_from('>2I', png, 16), (bounds[2] - bounds[0], bounds[3] - bounds[1]))
        self.assertTrue(bounds[0] < 120 < bounds[2] and bounds[1] < 5 < bounds[3])   # the room's Spidey is on the map


if __name__ == '__main__': unittest.main()
