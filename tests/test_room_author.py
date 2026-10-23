"""Camera polygons and anchor points of room object files."""
import unittest
import struct

import mod
from tools import room_author as ra
from tools.room_objects import RoomObjects


class RoomAuthorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, glob, manifest = mod.load_clean()
        cls.blobs = {e['name']: glob[e['offset']:e['offset'] + e['size']] for e in manifest['entries']}
        cls.rooms = [n for n in cls.blobs if n.endswith('_app.obj')]

    def test_native_camera_sections_round_trip(self):
        seen, polygons = 0, 0
        for name in self.rooms:
            section = RoomObjects.parse(self.blobs[name]).records[0].sections[4]
            if name.startswith('Residential_Map04'):                   # one point there carries an extra word
                with self.assertRaises(ValueError): ra.camera(self.blobs[name])
                continue
            found = ra.camera(self.blobs[name])
            self.assertEqual(ra.camera_section(found), section, name)
            seen += bool(found); polygons += len(found)
        self.assertEqual((seen, polygons), (67, 83))                   # the debug rooms have none: a free camera
        self.assertEqual(ra.camera(self.blobs['Sewer_Save04_app.obj']), (((20, 25), (20, 0), (40, 0), (40, 25)),))
        self.assertEqual(len(ra.camera(self.blobs['Residential_Map01_app.obj'])), 3)
        self.assertEqual(ra.camera(self.blobs['Test_Surfaces01_app.obj']), ())

    def test_camera_can_be_authored(self):
        raw = self.blobs['Test_Surfaces01_app.obj']
        polygon = ra.room_camera((0, 0, 60, 25))
        self.assertEqual(polygon, ((20, 25), (20, 0), (40, 0), (40, 25)))      # the native rule, as in the Refuge
        built = ra.set_camera(raw, [polygon])
        self.assertEqual(RoomObjects.parse(built).records[0].sections[4],
                         RoomObjects.parse(self.blobs['Sewer_Save04_app.obj']).records[0].sections[4])
        self.assertEqual(RoomObjects.parse(built).records[0].sections[:4], RoomObjects.parse(raw).records[0].sections[:4])
        self.assertEqual(ra.room_camera((0, 0, 30, 200)), ((14.5, 200), (14.5, 0), (15.5, 0), (15.5, 200)))   # a narrow shaft
        two = ra.set_camera(raw, [polygon, ((0, 0), (10, 0))])
        self.assertEqual(ra.camera(two), (polygon, ((0, 0), (10, 0))))
        self.assertEqual(ra.camera(ra.set_camera(two, [])), ())

    def test_anchor_points(self):
        native = ra.anchors(self.blobs['Test_Combat01_app.obj'])
        self.assertEqual(len(native), 36)
        self.assertEqual(sorted({kind for _, _, kind in native}), [1, 2, 3, 4, 5])
        floor = [(x, y) for x, y, kind in native if kind == ra.FLOOR]
        self.assertTrue(all(abs(y - 2) < 0.1 for _, y in floor) and len(floor) == 12)       # 2 above the floor, every 20 units
        self.assertEqual(ra.anchors(self.blobs['Sewer_Save04_app.obj']), [])                # a room nobody spawns in
        raw = self.blobs['Test_Surfaces01_app.obj']
        points = [(10, 2, ra.FLOOR), (3.5, 20, ra.LEFT_WALL), (50, 30, ra.AIR)]
        built = ra.set_anchors(raw, points)
        self.assertEqual(ra.anchors(built), points)
        section = RoomObjects.parse(built).records[0].sections[3]
        self.assertEqual((len(section), section[2], section[3], section[4:7]), (8 + 60, 8, 3, bytes((20, 20, 20))))
        with self.assertRaises(ValueError): ra.anchor_section([(0, 0, 9)])
        self.assertEqual(ra.anchor_section([]), b'')

    def test_every_supported_camera_count_round_trips_and_corruption_is_rejected(self):
        raw = self.blobs['Test_Surfaces01_app.obj']
        for count in range(1, 16):
            with self.subTest(count=count):
                polygons = [((i, 0), (i + 1, 0), (i + 1, 5), (i, 5)) for i in range(count)]
                built = ra.set_camera(raw, polygons)
                self.assertEqual(ra.camera(built), tuple(polygons))
        section = ra.camera_section(polygons[:4])
        bad_offset = bytearray(section); struct.pack_into('<H', bad_offset, 2, 0)
        bad_padding = bytearray(ra.camera_section(polygons[:3])); bad_padding[9] = 1
        for corrupt in (section[:-1], section + b'\0', bytes(bad_offset), bytes(bad_padding)):
            with self.assertRaises(ValueError):
                ra.camera(RoomObjects.parse(raw).replace_section(0, 4, corrupt))


if __name__ == '__main__':
    unittest.main()
