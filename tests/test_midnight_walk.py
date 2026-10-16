"""Midnight Line walk routes: every room-to-room step is a chapter link and every lab placement is in open space."""
import struct
import unittest

import mod
from tools import midnight_chapter as ch, midnight_rooms, midnight_walk as walk, room_catalog
from tools.room_collision import RoomCollision


class MidnightWalkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom, glob, manifest = mod.load_clean()
        cls.blobs = {e['name']: glob[e['offset']:e['offset'] + e['size']] for e in manifest['entries']}
        at, _, _, size = struct.unpack_from('<4I', rom, 0x20)
        names = [e['name'] for e in manifest['entries']]
        cls.native = room_catalog.parse(rom[at:at + size], names)
        cls.room_names = [r.name for r in cls.native]
        cls.routes = walk.routes()
        cls.collision = {r.name: RoomCollision.parse(midnight_rooms.compiled(r.name, cls.blobs.__getitem__).collision
                                                     if r.name in midnight_rooms.AUTHORED else cls.blobs[r.source + '.bsp'])
                         for r in ch.ROOMS}

    def test_routes_cover_the_whole_loop_through_chapter_links(self):
        linked = {(room, dest) for (room, _), (dest, _) in ch.LINKS.items()}
        seen = set()
        for name, (start, spawn, preset, steps) in self.routes.items():
            self.assertIn(start, ch.BY_NAME, name)
            self.assertTrue(all(f in ch.FREE_FLAGS for f in preset), name)
            previous = start
            for room, step in walk.rooms_of(start, steps):
                if room != previous:
                    self.assertIn((previous, room), linked, (name, previous, room))     # only real doors between rooms
                    seen.add((previous, room))
                    previous = room
        loop = ['ML_Stairs', 'ML_Platform', 'ML_NestShaft', 'ML_NestRest', 'ML_NestThroat', 'ML_NestSpan', 'ML_NestHollow',
                'ML_NestGallery', 'ML_NestShrine', 'ML_Venom', 'ML_NestGate', 'ML_Stairs']
        self.assertTrue(set(zip(loop, loop[1:])) <= seen)
        self.assertIn(('ML_Stairs', 'ML_NestGate'), seen)                 # the grate as a shortcut after the loop
        substation = ['ML_Yard', 'ML_Switchyard', 'ML_RelayHall', 'ML_Roof', 'ML_SignalCore']    # every authored door, both ways
        self.assertTrue({*zip(substation, substation[1:]), *zip(substation[1:], substation)} <= seen)
        self.assertTrue({('ML_Switchyard','ML_ServiceBay'),('ML_ServiceBay','ML_Switchyard')}<=seen)
        # The native Span neck is12 high: a masher can stand against it
        # forever. The walk gate must use a real duck-roll, with the crew
        # kept in the same traversal fixture as the preceding wall checks.
        steps=self.routes['span-hollow'][3]
        i=next(i for i,s in enumerate(steps) if s[0]=='until' and s[1]=='span_to_hollow')
        self.assertEqual(steps[i][4],('Right','Down','tapR'))
        self.assertEqual(steps[i-1],walk.fixtures(fight=False,park=(-330,-30)))

    def test_lab_placements_are_in_open_space_of_their_room(self):
        placed = 0
        for name, (start, spawn, preset, steps) in self.routes.items():
            for room, step in walk.rooms_of(start, steps):
                if step[0] != 'place': continue
                x, y = step[1], step[2]
                bsp = self.collision[room]
                # Position is ~5 above the feet: body between y - 5 and y, half width RADIUS.
                for dx in (-walk.RADIUS + 0.5, 0, walk.RADIUS - 0.5):
                    self.assertIsNone(bsp.solid_at(x + dx, y), (name, room, x, y))
                placed += 1
        self.assertGreaterEqual(placed, 15)

    def test_shaft_template_of_the_descents_matches_collision(self):
        for room, centre, gap in (('ML_NestShaft', 20, -1), ('ML_NestThroat', -20, +1), ('ML_NestGate', -20, +1),
                                  ('ML_NestHollow', 0, -1)):
            bsp = self.collision[room]
            edge = centre + gap * 14
            self.assertIsNone(bsp.solid_at(edge, 97), room)                # the ledge gap beside the wall
            self.assertIsNotNone(bsp.solid_at(centre - gap * 5, 97), room)  # the ledge itself
            self.assertIsNotNone(bsp.solid_at(edge, 58), room)             # the wedge under the gap
            self.assertIsNone(bsp.solid_at(centre - gap * 14, 58), room)   # and the way past it
            self.assertIsNotNone(bsp.solid_at(centre, 128), room)          # platforms in the middle
            self.assertIsNotNone(bsp.solid_at(centre, 30), room)
        steps = walk.descend('x', 20, -1)
        self.assertEqual([s[2] for s in steps if s[0] == 'walk'], [6, 25, 34])

    def test_exit_trigger_lookup_reads_the_built_room(self):
        template = self.blobs[ch.STATE_TEMPLATE + '_app.obj']
        room = ch.BY_NAME['ML_NestGate']
        source = next(r for r in self.native if r.name == room.source)
        raw, _ = ch.build_room(self.blobs[room.source + '_app.obj'], template, room, source.index, self.room_names,
                               dict(ch.SHARED_FLAGS))
        self.assertEqual(walk.trigger_of(raw, 2), (-20 * 4096, 218 * 4096))     # the ceiling exit to the Stairs
        self.assertEqual(walk.trigger_of(raw, 1), (18 * 4096, 8 * 4096))
        with self.assertRaises(ValueError): walk.trigger_of(raw, 7)

    def test_step_builders(self):
        self.assertEqual(walk.hold('Up+A', 3), ('hold', ('Up', 'A'), 3))
        self.assertEqual(walk.until('x', None, 5, 'Right+tapA')[4], ('Right', 'tapA'))
        self.assertEqual([s[0] for s in walk.put(1, 2)], ['place', 'hold', 'wait', 'settle'])
        self.assertEqual([s[0] for s in walk.grate('g', 'ML_NestShaft', 285)][-2:], ['until', 'until'])
        self.assertEqual(walk.in_room('ML_Venom').room, 'ML_Venom')
        self.assertEqual(walk.PLAYER_ABILITIES >> 5 & 1, 0)                # no Sledgehammer Slam (story ability 314)
        self.assertEqual(walk.PLAYER_ABILITIES & 0x1F, 0x1F)               # Ichor Crawl/Web, Tarantula, Reinforced Web, Bulldozer

    def test_loading_frame_has_no_fabricated_player_or_room_variables(self):
        from unittest.mock import patch
        from tools import kit_lab,player_trace,crane_walk
        ram=bytearray(0x400000)
        struct.pack_into('<I',ram,kit_lab.STATS_POINTER-player_trace.BASE,player_trace.BASE+0x1000)
        struct.pack_into('<I',ram,0x1000,102)
        driver=crane_walk.Walker((),{})
        with patch.object(player_trace,'sample',side_effect=ValueError('Actor still loading')):
            state=driver.read(12,ram)
        self.assertEqual(state.room,102)
        self.assertIsNone(state.pos)
        self.assertEqual(state.room_vars,())
        self.assertNotIn('machinery',driver.report)

    def test_roof_chase_fixture_cannot_enter_the_boss_or_relay_door(self):
        self.assertEqual(walk.chase_point(93,3.5,5),(24,6))
        self.assertEqual(walk.chase_point(93,210,5),(176,6))
        self.assertEqual(walk.chase_point(93,100,20),(96,21))
        self.assertEqual(walk.chase_point(92,15,20),(11,21))


if __name__ == '__main__':
    unittest.main()
