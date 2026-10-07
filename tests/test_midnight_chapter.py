"""Midnight Line chapter: link geometry, sanitized clones, flag allocation and tables."""
import struct
import unittest

import mod
from tools import midnight_chapter as ch, room_catalog, room_doors as doors
from tools.nitro_texture import TextureArchive
from tools.room_entities import Entities
from tools.room_events import Events
from tools.room_objects import RoomObjects


class MidnightChapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom, glob, manifest = mod.load_clean()
        cls.names = [e['name'] for e in manifest['entries']]
        cls.blobs = {e['name']: glob[e['offset']:e['offset'] + e['size']] for e in manifest['entries']}
        at, _, _, size = struct.unpack_from('<4I', rom, 0x20)
        cls.arm9 = rom[at:at + size]
        cls.native = room_catalog.parse(cls.arm9, cls.names)
        cls.room_names = [r.name for r in cls.native]
        cls.local = {}
        cls.built = {}
        template = cls.blobs[ch.STATE_TEMPLATE + '_app.obj']
        for room in ch.ROOMS:
            src = next(r for r in cls.native if r.name == room.source)
            cls.built[room.name] = ch.build_room(cls.blobs[room.source + '_app.obj'], template, room,
                                                 src.index, cls.room_names, cls.local)
        cls.entrance = ch.entrance_obj(cls.blobs[ch.ENTRANCE + '_app.obj'], cls.room_names)

    def obj(self, name):
        return self.entrance if name == ch.ENTRANCE else self.built[name][0]

    def index(self, name):
        return ch.BY_NAME[name].index if name in ch.BY_NAME else self.room_names.index(name)

    def name_of(self, index):
        return next((r.name for r in ch.ROOMS if r.index == index), None) or self.room_names[index]

    def triggers(self, raw):
        """{group: (x, y)} for record-0 exit triggers."""
        record = RoomObjects.parse(raw).records[0]
        return {e[27] - 1: struct.unpack_from('<2i', e) for e in Entities.parse(record.sections[0]).records
                if len(e) == 28 and struct.unpack_from('<I', e, 12)[0] == doors.TRIGGER_TYPE}

    def test_every_chapter_exit_is_linked_and_lands_beside_the_door_back(self):
        exits = {(name, x.group): x for name in (*ch.BY_NAME, ch.ENTRANCE) for x in doors.exits(self.obj(name))
                 if x.record == 0 and (name != ch.ENTRANCE or x.room >= ch.FIRST)}
        self.assertEqual(len(exits), len(ch.LINKS) + 1)
        for (name, group), x in exits.items():
            dest = self.name_of(x.room)
            if (name, group) in ch.LINKS: self.assertEqual(ch.LINKS[(name, group)], (dest, x.spawn))
            self.assertEqual(x.selector, 1)
            spawn = next(s for s in doors.spawns(self.obj(dest)) if s.spawn_id == x.spawn)
            # The nearest exit trigger to the arrival point must lead back.
            nearest = min(self.triggers(self.obj(dest)).items(),
                          key=lambda t: (t[1][0] - spawn.x) ** 2 + (t[1][1] - spawn.y) ** 2)[0]
            back = next(b for b in doors.exits(self.obj(dest)) if b.record == 0 and b.group == nearest)
            self.assertEqual(self.name_of(back.room), name, (name, group, dest))

    def test_tour_rides_every_directed_link_once_as_one_walk(self):
        self.assertEqual(sorted(ch.TOUR[1:]), sorted(ch.LINKS))
        self.assertEqual(ch.TOUR[0][0], ch.ENTRANCE)
        rooms = [ch.ENTRANCE] + [None] * len(ch.TOUR)
        for i, (room, group) in enumerate(ch.TOUR):
            self.assertEqual(room, rooms[i])
            dest = ch.LINKS[(room, group)][0] if room != ch.ENTRANCE else 'ML_Platform'
            rooms[i + 1] = dest
        self.assertEqual(rooms[-1], ch.ENTRANCE)

    def test_flag_allocation_stays_inside_the_unreferenced_range(self):
        visited = {ch.VISITED_BASE + r.index for r in ch.ROOMS}
        milestones = set(ch.MILESTONE_FLAGS.values())
        local = set(ch.LOCAL_FLAGS)
        free = set(ch.FREE_FLAGS)
        self.assertTrue(visited | milestones | local <= free)
        self.assertFalse(visited & milestones or visited & local or milestones & local)
        self.assertTrue(all(f < ch.FLAG_LIMIT for f in free))
        self.assertTrue(set(self.local.values()) <= local)

    def test_clones_write_only_chapter_flags_and_keep_no_native_exit(self):
        allowed = set(ch.FREE_FLAGS)
        for room in ch.ROOMS:
            parsed = RoomObjects.parse(self.obj(room.name))
            self.assertEqual(len(parsed.records), 2)
            for r, record in enumerate(parsed.records):
                for group in Events.parse(record.sections[1], record.raw[3]).groups:
                    for c in group.commands:
                        self.assertNotEqual(c.opcode, ch.MESSAGE, room.name)
                        if c.opcode in (ch.SET_VAR, ch.INC_VAR, ch.DEC_VAR):
                            self.assertIn(struct.unpack_from('<H', c.operand)[0], allowed, room.name)
                        if c.opcode == ch.IF_VAR:
                            var = struct.unpack_from('<H', c.operand)[0]
                            self.assertTrue(var in allowed or var >= ch.FLAG_LIMIT, (room.name, hex(var)))
                        if c.opcode == doors.GO_TO_ROOM:
                            self.assertEqual(r, 0)
                            self.assertTrue(c.operand[0] >= ch.FIRST or c.operand[0] == self.index(ch.ENTRANCE))
                for e in Entities.parse(record.sections[0]).records:
                    if struct.unpack_from('<I', e, 12)[0] == ch.PICKUP_TYPE:
                        self.assertEqual(struct.unpack_from('<i', e, 4)[0], ch.REMOVED_PICKUP_Y)
            init = Events.parse(parsed.records[1].sections[1], parsed.records[1].raw[3]).groups[0]
            sets = [struct.unpack_from('<H', c.operand)[0] for c in init.commands if c.opcode == ch.SET_VAR]
            self.assertIn(ch.VISITED_BASE + room.index, sets, room.name)
            if not room.encounters:
                self.assertEqual(Entities.parse(parsed.records[1].sections[0]).records, ())
        self.assertEqual(self.local, {('ML_Service', 0x42): 268})

    def test_entrance_keeps_the_native_exit_and_adds_return_spawn(self):
        exits = [(x.group, x.room, x.selector, x.spawn) for x in doors.exits(self.entrance)]
        self.assertEqual(exits, [(1, 57, 2, 4), (2, ch.FIRST, 1, ch.ENTRANCE_DOOR['spawn'])])
        self.assertEqual([s.spawn_id for s in doors.spawns(self.entrance)], [1, 0, 2])
        native = RoomObjects.parse(self.blobs[ch.ENTRANCE + '_app.obj'])
        self.assertEqual(RoomObjects.parse(self.entrance).records[1].raw, native.records[1].raw)

    def test_room_table_keeps_native_lookup_and_points_at_appended_rooms(self):
        resources = {r.name: {'objects': 4000 + 2 * i, 'texture': 4001 + 2 * i} for i, r in enumerate(ch.ROOMS)}
        names = self.names + [f'x{i}' for i in range(4000 - len(self.names))]
        names += [n for r in ch.ROOMS for n in (f'zz_{r.name}_app.obj', f'zz_{r.name}Textures.nsbtx')]
        table = ch.room_table(self.arm9, names, resources)
        self.assertEqual(len(table), ch.ML_SPACE)
        lookup = struct.unpack_from(f'<{ch.FIRST + len(ch.ROOMS)}I', table)
        self.assertEqual(lookup[:75], tuple(r.address for r in self.native))
        self.assertEqual(lookup[75], 0)
        for room, address in zip(ch.ROOMS, lookup[ch.FIRST:]):
            raw = table[address - ch.ML_BASE:address - ch.ML_BASE + room_catalog.SIZE]
            src = next(r for r in self.native if r.name == room.source)
            name_at, tex, bsp, obj = struct.unpack_from('<4I', raw)
            self.assertEqual((tex, bsp, obj), (resources[room.name]['texture'], src.bsp, resources[room.name]['objects']))
            label = table[name_at - ch.ML_BASE:].split(b'\0', 1)[0].decode()
            self.assertEqual(label, room.name)
            model = struct.unpack_from('<I', table, struct.unpack_from('<I', raw, 0x20)[0] - ch.ML_BASE)[0]
            self.assertEqual(self.names[model], room.source + '.nsbmd')
            self.assertEqual(raw[0x24:], src.raw[0x24:])     # animation, minimap and unknown fields

    def test_grade_keeps_texture_bytes_and_alpha_bit(self):
        source = self.blobs['Sewer_Map03Textures.nsbtx']
        graded = ch.graded_textures(source, 'midnight')
        archive = TextureArchive.parse(source)
        a, z = archive.palette_start, archive.palette_start + archive.palette_size
        self.assertEqual((graded[:a], graded[z:]), (source[:a], source[z:]))
        self.assertNotEqual(graded[a:z], source[a:z])
        for i in range(a, z, 2):
            self.assertEqual(struct.unpack_from('<H', graded, i)[0] & 0x8000, struct.unpack_from('<H', source, i)[0] & 0x8000)
        self.assertEqual(ch.graded_textures(source, 'midnight'), graded)


if __name__ == '__main__':
    unittest.main()
