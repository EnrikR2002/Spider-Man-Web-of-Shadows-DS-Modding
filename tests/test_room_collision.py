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

    def test_every_list_names_ancestor_planes_of_its_leaf(self):
        """A solid leaf's list holds planes of nodes above it (its faces), each with a surface value."""
        values = set()
        for e in self.manifest['entries']:
            if not e['name'].endswith('.bsp'): continue
            tree = RoomCollision.parse(self.glob[e['offset']:e['offset'] + e['size']])
            paths, path, stack = {}, [], [(0, None)]
            def walk(node):
                front, back = tree.children(node)
                for kind, value in (front, back):
                    path.append(node)
                    if kind == 'solid': paths[value] = set(path)
                    elif kind == 'node': walk(value)
                    path.pop()
            import sys
            sys.setrecursionlimit(20000)
            walk(0)
            for index, entries in enumerate(tree.lists):
                self.assertTrue({node for node, _ in entries} <= paths[index], e['name'])
                values |= {value for _, value in entries}
        self.assertEqual(values, {0, 1, 2, 4, 5, 6, 7, 9, 10})
        combat = RoomCollision.parse(self.blob('Test_Combat01.bsp'))
        self.assertEqual({value for entries in combat.lists for _, value in entries}, {10})    # plain floor and walls

    def blob(self, name):
        e = next(x for x in self.manifest['entries'] if x['name'] == name)
        return self.glob[e['offset']:e['offset'] + e['size']]

    def test_compiled_boxes_match_native_rooms_point_for_point(self):
        import random
        from tools.room_collision import INF, compile_boxes
        rooms = {
            'Test_Combat01': (20, [(-INF, -INF, 0, INF), (240, -INF, INF, INF), (0, -INF, 240, 0), (0, 60, 240, INF)],
                              (-40, -40, 280, 100)),
            # The save room: a 60 x 25 hall and a 12-unit-high door corridor to x 80.
            'Sewer_Save04': (25, [(-INF, -INF, 0, INF), (0, -INF, INF, 0), (0, 25, 60, INF), (60, 12, 80, INF), (80, 0, INF, INF, 1)],
                             (-30, -30, 110, 60)),
        }
        random.seed(7)
        for name, (slab, boxes, (x0, y0, x1, y1)) in rooms.items():
            native = RoomCollision.parse(self.blob(name + '.bsp'))
            raw = compile_boxes(boxes, slab=slab)
            mine = RoomCollision.parse(raw)
            mine.check_tree()
            self.assertEqual(mine.to_bytes(), raw)
            self.assertLessEqual(len(mine.nodes), len(native.nodes), name)     # z planes are shared, not repeated
            for _ in range(4000):
                x, y, z = random.uniform(x0, x1), random.uniform(y0, y1), random.uniform(-40, 40)
                self.assertEqual(mine.solid_at(x, y, z) is None, native.solid_at(x, y, z) is None, (name, x, y, z))
            for node, entries in zip(mine.nodes, mine.lists): self.assertTrue(entries)
            self.assertEqual({n[2] for n in mine.nodes}, {0})
        self.assertEqual(len(compile_boxes(rooms['Test_Combat01'][1], slab=20)), len(self.blob('Test_Combat01.bsp')))
        # The save room's corridor end keeps its surface value 1; z faces stay plain.
        save = RoomCollision.parse(compile_boxes(rooms['Sewer_Save04'][1]))
        self.assertEqual(sorted({value for entries in save.lists for _, value in entries}), [1, 10])

    def test_compiled_block_is_solid_with_its_own_faces(self):
        from tools.room_collision import INF, compile_boxes
        boxes = [(-INF, -INF, 0, INF), (0, -INF, INF, 0), (0, 25, 60, INF), (60, 12, 80, INF), (80, 0, INF, 12, 1), (24, 0, 36, 8, 6)]
        tree = RoomCollision.parse(compile_boxes(boxes))
        self.assertIsNotNone(tree.solid_at(30, 4))
        self.assertIsNone(tree.solid_at(30, 9))
        self.assertIsNone(tree.solid_at(23.5, 4))
        self.assertIsNone(tree.solid_at(36.5, 4))
        self.assertEqual(tree.floor_below(30, 20), 8.25)
        faces = tree.lists[tree.solid_at(30, 4)]
        planes = set()
        for node, value in faces:
            word0, word1 = tree.nodes[node][:2]
            if word1 & 3 != 2:
                planes.add((word1 & 7, (word0 & ~3) / 4096))
                self.assertEqual(value, 6)                   # the block's own surface value on x and y faces
            else: self.assertEqual(value, 10)
        self.assertTrue({(0, 24.0), (4, -36.0), (5, -8.0)} <= planes)      # x >= 24, x <= 36, y <= 8
        with self.assertRaises(ValueError): compile_boxes([(0, 0, 0, 5)])
        with self.assertRaises(ValueError): compile_boxes([(-INF, -INF, INF, INF)])

    def test_adjacent_solid_children_retain_union_and_surface_faces(self):
        from tools.room_collision import compile_boxes
        import random
        # Minimized from a broken dock with a stack touching its deck. The
        # former writer recursed into an already-solid back child and failed.
        boxes=[(80,-24,300,0,10),(240,0,286,42,6),(142,0,162,44,10),
               (50,-15,74,-12,10),(218,81,250,84,10)]
        raw=compile_boxes(boxes);tree=RoomCollision.parse(raw);tree.check_tree()
        self.assertEqual(tree.to_bytes(),raw)
        rng=random.Random(17)
        points=[(rng.uniform(30,320),rng.uniform(-30,100),rng.uniform(-30,30)) for _ in range(2500)]
        points += [(x+.1,y+.1,0) for x in (50,74,80,142,162,218,240,250,286,300) for y in (-24,-15,-12,0,42,44,81,84)]
        for x,y,z in points:
            expected=abs(z)>=25 or any(a<=x<=c and b<=y<=d for a,b,c,d,_ in boxes)
            self.assertEqual(tree.solid_at(x,y,z) is not None,expected,(x,y,z))
        self.assertIsNotNone(tree.solid_at(250,20))
        self.assertEqual({v for n,v in tree.lists[tree.solid_at(250,20)] if tree.nodes[n][1]&3!=2},{6})


if __name__ == '__main__': unittest.main()
