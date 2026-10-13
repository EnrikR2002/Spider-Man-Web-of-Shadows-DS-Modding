"""Room compiler: one box list gives matching collision and visible faces; faces are wound for their viewer."""
import struct
import unittest

import mod
from tools import nitro_build as nb, room_author as ra, room_compiler as rcm
from tools.model_geometry import ModelGeometry
from tools.nitro_texture import TextureArchive
from tools.room_collision import RoomCollision
from tools.room_compiler import Look, Panel, Room, Solid


class RoomCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, glob, manifest = mod.load_clean()
        cls.blobs = {e['name']: glob[e['offset']:e['offset'] + e['size']] for e in manifest['entries']}
        pairs = [rcm.borrow(cls.blobs['proto01Textures.nsbtx'], n) for n in ('Fconcrete01', 'wbrick01', 'wcutaway01', 'Pcrate01')]
        cls.textures, cls.palettes = tuple(t for t, _ in pairs), tuple(p for _, p in pairs)
        floor, brick, cut, crate = (Look('Fconcrete01'), Look('wbrick01', (16, 16)), Look('wcutaway01', (8, 8)), Look('Pcrate01', (12, 12)))
        cls.theme = {'top': floor, 'side': brick, 'under': brick, 'front': cut, 'back': brick}
        cls.crate = crate

    def room(self, **extra):
        solids = (Solid(60, 12, 80, 30), Solid(24, 0, 36, 8, top=self.crate, side=self.crate, depth=10))
        return Room('Test', (0, 0, 80, 30), self.theme, solids, textures=self.textures, palettes=self.palettes, **extra)

    def faces(self, room):
        sizes = {t.name: (t.width, t.height) for t in room.textures}
        return rcm._emit(room, sizes)

    def test_collision_and_model_come_from_the_same_boxes(self):
        room = self.room()
        built = rcm.compile_room(room)
        tree = RoomCollision.parse(built.collision)
        tree.check_tree()
        for x, y, solid in ((10, 5, False), (30, 4, True), (30, 9, False), (70, 20, True), (70, 5, False), (-1, 5, True),
                            (81, 5, True), (40, -1, True), (40, 31, True)):
            self.assertEqual(tree.solid_at(x, y) is not None, solid, (x, y))
        self.assertAlmostEqual(tree.floor_below(30, 12), 8, delta=0.3)
        model = ModelGeometry.parse(built.model)
        self.assertEqual(len(model.shapes), len(built.by_texture))
        self.assertEqual(sum(built.by_texture.values()), built.quads)
        self.assertEqual(struct.unpack_from('<4H', built.model, model.model + 36), (built.quads * 4, built.quads, 0, built.quads))
        archive = TextureArchive.parse(built.textures)
        self.assertEqual({t['name'] for t in archive.textures}, set(built.by_texture))
        parts = nb.model_parts(built.model)
        self.assertEqual({m.texture for m in parts.materials}, set(built.by_texture))
        self.assertEqual(parts.scale, 64 * 4096)                       # the smallest scale that holds the room

    def test_every_plan_face_faces_its_viewer(self):
        # _emit raises on a face wound the wrong way; check a few by hand as well.
        faces = self.faces(self.room())
        def normal(vertices):
            a, b, c = (v[:3] for v in vertices[:3])
            e1, e2 = [q - p for p, q in zip(a, b)], [q - p for p, q in zip(b, c)]
            return (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
        floor = [v for _, v in faces['Fconcrete01'] if all(p[1] == 0 for p in v)]
        self.assertTrue(floor and all(normal(v)[1] > 0 for v in floor))                 # floors face up
        left_wall = [v for _, v in faces['wbrick01'] if all(p[0] == 0 for p in v)]
        self.assertTrue(left_wall and all(normal(v)[0] > 0 for v in left_wall))         # the left wall faces right
        back = [v for _, v in faces['wbrick01'] if all(p[2] == -rcm.DEPTH for p in v)]
        self.assertTrue(back and all(normal(v)[2] > 0 for v in back))                   # the back wall faces the camera
        for group in faces.values():
            for _, vertices in group:
                self.assertTrue(all(-2048 < p[3] < 2048 and -2048 < p[4] < 2048 for p in vertices))   # texel range

    def test_free_standing_solid_stops_short_and_keeps_its_floor_in_front(self):
        faces = self.faces(self.room())
        crate = [v for _, v in faces['Pcrate01']]
        self.assertTrue(crate)
        self.assertEqual(max(p[2] for v in crate for p in v), 10)                       # its body ends at depth 10
        apron = [v for _, v in faces['Fconcrete01'] if all(p[1] == 0 for p in v) and min(p[2] for p in v) == 10]
        self.assertEqual([(min(p[0] for p in v), max(p[0] for p in v), max(p[2] for p in v)) for v in apron], [(24, 36, rcm.DEPTH)])
        full = self.faces(Room('Test', (0, 0, 80, 30), self.theme, (Solid(24, 0, 36, 8, top=self.crate, side=self.crate),),
                               textures=self.textures, palettes=self.palettes))
        self.assertEqual(max(p[2] for _, v in full['Pcrate01'] for p in v), rcm.DEPTH)
        self.assertFalse('Pcrate01' in full and any(min(p[2] for p in v) == 10 for _, v in full['Fconcrete01']))

    def test_hidden_solids_and_panels(self):
        room = self.room(panels=(Panel(8, 6, 22, 20, self.crate, 1.0, anchor=(8, 20)),))
        faces = self.faces(room)
        panel = [v for _, v in faces['Pcrate01'] if all(p[2] == -rcm.DEPTH for p in v)]
        boxes = [(min(p[0] for p in v), min(p[1] for p in v), max(p[0] for p in v), max(p[1] for p in v)) for v in panel]
        self.assertEqual((min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)),
                         (8, 6, 22, 20))                                   # the panel, cut into rows by the plan's grid
        self.assertEqual(sum((b[2] - b[0]) * (b[3] - b[1]) for b in boxes), 14 * 14)
        hidden = Room('Test', (0, 0, 80, 30), self.theme, (Solid(30, 20, 50, 30, hidden=True),), textures=self.textures,
                      palettes=self.palettes, hidden_shell=('above',))
        self.assertIsNotNone(RoomCollision.parse(rcm.collision(hidden)).solid_at(40, 25))     # still solid
        self.assertFalse([v for group in self.faces(hidden).values() for _, v in group
                          if all(p[1] == 20 for p in v) or all(p[1] == 30 for p in v)])            # but never drawn
        mirrored = self.faces(self.room(panels=(Panel(8, 6, 22, 20, self.crate, 1.0, anchor=(8, 20), mirror=True),)))
        plain = [v for _, v in faces['Pcrate01'] if all(p[2] == -rcm.DEPTH for p in v)][0]
        flipped = [v for _, v in mirrored['Pcrate01'] if all(p[2] == -rcm.DEPTH for p in v)][0]
        self.assertGreater(plain[2][3] - plain[1][3], 0)               # texture runs left to right
        self.assertLess(flipped[2][3] - flipped[1][3], 0)              # and right to left when mirrored

    def test_fills_close_the_gap_beside_a_free_standing_solid(self):
        # A catwalk that stops at z 14 between a full-depth wall (left) and the room's own wall (right):
        # both walls go on in front of it, and so does a deeper block's underside above a shallow one.
        solids = (Solid(0, 0, 10, 30), Solid(10, 12, 80, 16, top=self.crate, side=self.crate, depth=14),
                  Solid(30, 16, 50, 30), Solid(30, 8, 50, 12, depth=5))
        room = Room('Test', (0, 0, 80, 30), self.theme, solids, textures=self.textures, palettes=self.palettes)
        kinds = {}
        for face in rcm._plan_faces(room): kinds.setdefault(face[1], []).append(face)
        right = [f for f in kinds['right_fill'] if f[2] == 10]
        self.assertEqual([(f[3], f[4], f[5]) for f in right], [((12, 16), 14, rcm.DEPTH)])
        left = [f for f in kinds['left_fill'] if f[2] == 80]
        self.assertEqual([(f[3], f[4], f[5]) for f in left], [((12, 16), 14, rcm.DEPTH)])
        under = kinds['under_fill']
        self.assertIn(((30, 50), 16, 14, rcm.DEPTH), [(f[2], f[3], f[4], f[5]) for f in under])
        self.assertEqual({f[1] for f in rcm._plan_faces(self.room()) if f[1].endswith('_fill')}, set())   # nothing to fill
        self.assertFalse(any(kind.endswith('fill') for kind, *_ in rcm.surfaces(room)))             # not walls for anchors
        rcm.compile_room(room)                                           # windings are checked while emitting

    def test_open_panels_and_backdrops(self):
        # A panel without a look leaves the back wall open; a backdrop is a row of far quads, every second
        # one mirrored, with the picture's sky folded on above and its bottom row stretched below.
        room = self.room(panels=(Panel(10, 10, 50, 100, None),))
        back = [f for f in rcm._plan_faces(room) if f[1] == 'back']
        self.assertFalse(any(f[2][0] < 30 < f[2][2] and f[2][1] < 20 < f[2][3] for f in back))
        self.assertTrue(any(f[2][0] < 5 < f[2][2] and f[2][1] < 20 < f[2][3] for f in back))
        quads = rcm.backdrop(self.crate, -40, 120, 0, 100, tile=80, sky=40, ground=30)
        tiles = [q for q in quads if q.corners[0][1] == 100 and q.corners[1][1] == 0]
        self.assertEqual([q.corners[0][0] for q in tiles], [-40, 40])
        self.assertEqual({q.corners[0][2] for q in quads}, {-170.0})
        self.assertEqual([q.repeats[0][0] for q in tiles], [0.0, 1.0])              # the second tile is mirrored
        sky = sorted((q.corners[1][1], q.corners[0][1], q.repeats[1][1], q.repeats[0][1]) for q in quads if q.corners[1][1] >= 100 and q.corners[0][0] == -40)
        self.assertEqual(sky, [(100, 120, 0.0, 0.2), (120, 140, 0.2, 0.0)])         # bottom v, top v: folded, no seam
        ground = [q for q in quads if q.corners[0][1] == 0 and q.corners[1][1] == -30]
        self.assertEqual(len(ground), 2)
        for q in quads: self.assertGreater(rcm._normal(q.corners)[2], 0)            # they face the camera
        rcm.compile_room(self.room(scenery=tuple(quads), panels=(Panel(10, 10, 50, 100, None),)))

    def test_surfaces_and_anchor_points(self):
        room = self.room()
        surfaces = rcm.surfaces(room)
        self.assertIn(('top', 0, 24, 0), surfaces)
        self.assertIn(('top', 24, 36, 8), surfaces)
        self.assertIn(('wall_left', 0, 0, 30), surfaces)
        self.assertIn(('wall_right', 60, 12, 30), surfaces)
        tree = RoomCollision.parse(rcm.collision(room))
        points = ra.plan_anchors(surfaces, room.bounds, floor_top=4, solid=lambda x, y: tree.solid_at(x, y) is not None)
        floor = [p for p in points if p[2] == ra.FLOOR]
        self.assertTrue(floor and all(y == 2 for _, y, _ in floor))                     # only the ground: the crate top is above 4
        for x, y, kind in points:
            self.assertIsNone(tree.solid_at(x, y), (x, y, kind))                        # every point is in open space
        self.assertEqual({k for _, _, k in points}, {ra.FLOOR, ra.LEFT_WALL, ra.RIGHT_WALL, ra.CEILING, ra.AIR})

    def test_painted_textures(self):
        pixels = [(x % 32, y % 32, (x + y) % 32) for y in range(16) for x in range(16)]
        texture, palette = rcm.paint('paint', 16, 16, pixels, 16)
        self.assertEqual((texture.format, len(texture.data), len(palette.data)), (3, 128, 32))
        texture, palette = rcm.paint('paint', 16, 16, pixels, 256)
        self.assertEqual((texture.format, len(texture.data), len(palette.data)), (4, 256, 512))
        colours = [struct.unpack_from('<H', palette.data, 2 * i)[0] for i in texture.data]
        self.assertEqual([(c & 31, c >> 5 & 31, c >> 10 & 31) for c in colours], pixels)   # 256 colours hold all of them exactly
        TextureArchive.parse(nb.texture_archive([texture], [palette]))
        with self.assertRaises(ValueError): rcm.compile_room(Room('Bad', (0, 0, 10, 10), {**self.theme, 'top': Look('missing')},
                                                                  textures=self.textures, palettes=self.palettes))


if __name__ == '__main__':
    unittest.main()
