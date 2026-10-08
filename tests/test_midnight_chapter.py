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
        cls.local = dict(ch.SHARED_FLAGS)
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
                 if x.record == 0 and (name != ch.ENTRANCE or x.room >= ch.FIRST) and (name, x.group) not in ch.SEALED}
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

    def test_every_link_joins_opposite_door_kinds(self):
        for (name, group), (dest, spawn) in ch.LINKS.items():
            arrival = next(s for s in doors.spawns(self.obj(dest)) if s.spawn_id == spawn)
            back = min(self.triggers(self.obj(dest)).items(),     # the door beside the arrival
                       key=lambda t: (t[1][0] - arrival.x) ** 2 + (t[1][1] - arrival.y) ** 2)[0]
            self.assertEqual(doors.door_kind(self.obj(name), group), doors.OPPOSITE[doors.door_kind(self.obj(dest), back)],
                             (name, group, dest))
        entry = ch.ENTRANCE_DOOR['room']
        self.assertEqual(doors.door_kind(self.entrance, 2), 'right')
        self.assertEqual(doors.door_kind(self.obj(entry), next(g for (r, g), v in ch.LINKS.items() if r == entry and v[0] == ch.ENTRANCE)), 'left')

    def test_sealed_exits_are_out_of_reach(self):
        for name, group in ch.SEALED:
            (x, y), = [xy for g, xy in self.triggers(self.obj(name)).items() if g == group]
            self.assertEqual(y, ch.REMOVED_PICKUP_Y, (name, group))
            self.assertNotIn((name, group), ch.LINKS)
            back = [k for k, (dest, _) in ch.LINKS.items() if dest == name]
            self.assertTrue(back, name)                       # the room is still reachable

    def test_tour_rides_every_directed_link_once_as_one_walk(self):
        self.assertEqual(sorted(ch.TOUR[1:]), sorted(ch.LINKS))
        self.assertEqual(ch.TOUR[0][0], ch.ENTRANCE)
        rooms = [ch.ENTRANCE] + [None] * len(ch.TOUR)
        for i, (room, group) in enumerate(ch.TOUR):
            self.assertEqual(room, rooms[i])
            dest = ch.LINKS[(room, group)][0] if room != ch.ENTRANCE else ch.ENTRANCE_DOOR['room']
            rooms[i + 1] = dest
        self.assertEqual(rooms[-1], ch.ENTRANCE)

    def test_flag_allocation_stays_inside_the_unreferenced_range(self):
        visited = {ch.VISITED_BASE + r.index for r in ch.ROOMS}
        local = set(ch.LOCAL_FLAGS)
        free = set(ch.FREE_FLAGS)
        self.assertTrue(visited | local <= free)
        self.assertFalse(visited & local)
        self.assertEqual(len(local), len(ch.LOCAL_FLAGS))
        self.assertTrue(all(f < ch.FLAG_LIMIT for f in free))
        self.assertTrue(set(self.local.values()) <= local)

    def test_clones_write_only_chapter_flags_and_keep_no_native_exit(self):
        allowed = set(ch.FREE_FLAGS) | set(ch.ROOM_SCRATCH)
        for room in ch.ROOMS:
            parsed = RoomObjects.parse(self.obj(room.name))
            self.assertEqual(len(parsed.records), 2)
            for r, record in enumerate(parsed.records):
                for group in Events.parse(record.sections[1], record.raw[3]).groups:
                    for c in group.commands:
                        self.assertNotIn(c.opcode, (ch.MESSAGE, ch.GRANT, ch.SPAWN_PICKUP), room.name)
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
        self.assertEqual(self.local[('ML_Station', 0x42)], 268)
        # Venom's reward: no ability grant or collectible orb; its pickup group runs directly.
        groups = Events.parse(*(lambda r: (r.sections[1], r.raw[3]))(RoomObjects.parse(self.obj('ML_Venom')).records[1])).groups
        self.assertEqual([c.operand[5] for c in groups[4].commands if c.opcode == ch.DELAY], [9])
        self.assertIn(ch.INC_VAR, [c.opcode for c in groups[8].commands])

    def test_entrance_keeps_the_native_exit_and_adds_return_spawn(self):
        exits = [(x.group, x.room, x.selector, x.spawn) for x in doors.exits(self.entrance)]
        self.assertEqual(exits, [(1, 57, 2, 4), (2, ch.FIRST, 1, ch.ENTRANCE_DOOR['spawn'])])
        self.assertEqual([s.spawn_id for s in doors.spawns(self.entrance)], [1, 0, 2])
        native = RoomObjects.parse(self.blobs[ch.ENTRANCE + '_app.obj'])
        built = RoomObjects.parse(self.entrance)
        old_e, new_e = (Entities.parse(x.records[1].sections[0]).records for x in (native, built))
        self.assertEqual(new_e[:-1], old_e)                    # native record-1 entities kept in order
        self.assertEqual(new_e[-1][4:], old_e[0][4:])          # doorway copy, moved along x only
        self.assertEqual(struct.unpack_from('<i', new_e[-1])[0], ch.DOORWAY['x'])
        self.assertEqual(built.records[1].sections[1:], native.records[1].sections[1:])
        self.assertEqual(built.names[1].labels[len(new_e) - 1], ch.DOORWAY['name'])

    def test_room_table_keeps_native_lookup_and_points_at_appended_rooms(self):
        resources = {r.name: {'objects': 4000 + 2 * i, 'texture': 4001 + 2 * i} for i, r in enumerate(ch.ROOMS)}
        names = self.names + [f'x{i}' for i in range(4000 - len(self.names))]
        names += [n for r in ch.ROOMS for n in (f'zz_{r.name}_app.obj', f'zz_{r.name}Textures.nsbtx')]
        table, list_at, messages_at = ch.room_table(self.arm9, names, resources, 1049)
        self.assertEqual(len(table), ch.ML_SPACE)
        entries = table[messages_at - ch.ML_BASE:messages_at - ch.ML_BASE + ch.MESSAGE_SIZE * len(ch.LINES)]
        self.assertEqual(entries, ch.message_entries(1049))
        entries = table[list_at - ch.ML_BASE:list_at - ch.ML_BASE + ch.ENTRY_SIZE * (ch.SEWER_COUNT + len(ch.ROOMS))]
        native = self.arm9[ch.SEWER_LIST - ch.BASE:ch.SEWER_LIST - ch.BASE + ch.ENTRY_SIZE * ch.SEWER_COUNT]
        self.assertEqual(entries[:len(native)], native)                   # native Sewer rooms kept in order
        added = [entries[i:i + ch.ENTRY_SIZE] for i in range(len(native), len(entries), ch.ENTRY_SIZE)]
        self.assertEqual([struct.unpack_from('<2I', e) for e in added], [(ch.BY_NAME[r].index, 1) for r in ch.DIAGRAM])
        slots = [e[9] for e in added]
        self.assertEqual(len(set(slots)), len(ch.ROOMS))
        self.assertTrue(all(e[10] == e[9] + 4 and e[11:15] == native[11:15] for e in added))
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
            self.assertEqual(raw[0x24:0x28], src.raw[0x24:0x28])   # texture animation
            self.assertEqual(raw[0x4C:], src.raw[0x4C:])           # map piece and later fields
            self.assertEqual(struct.unpack_from('<8i', raw, 0x2C), ch.MAP_FIELDS[room.source][1:])
            self.assertEqual(struct.unpack_from('<i', raw, 0x28)[0], ch.SEWER_AREA)   # drawn on the Sewer screen

    def test_map_screen_draws_each_room_in_its_own_free_slot(self):
        from tools.minimap_cbmp import Cbmp
        raw = self.blobs[ch.MAP_SCREEN]
        old, new = Cbmp.parse(raw), Cbmp.parse(ch.map_screen(raw))
        self.assertEqual(new.tiles[:len(old.tiles)], old.tiles)
        cells = {c: r for r, cs in ch.DIAGRAM.items() for c in cs}
        for i, (a, b) in enumerate(zip(old.screen, new.screen)):
            xy = (i % old.width, i // old.width)
            if xy not in cells: self.assertEqual(a, b)
            else:
                slot = dict(zip(ch.DIAGRAM, ch.MAP_SLOTS))[cells[xy]]
                self.assertEqual(b >> 12, slot >> 4)
                self.assertTrue(set(new.tile(b & 0x3FF)) <= {0} | set(range(slot & 15, (slot & 15) + 5)))
        changed = {i for i, (a, b) in enumerate(zip(old.palette, new.palette)) if a != b}
        self.assertTrue(changed <= {s + k for s in ch.MAP_SLOTS for k in range(5)})
        self.assertEqual(set(ch.DIAGRAM), set(ch.BY_NAME))

    def test_breaker_cuts_the_platform_flag_and_appends_only(self):
        from tools import room_script as s
        self.assertEqual(self.local[('ML_Platform', 0x27)], ch.TRACK_POWER)
        self.assertIn(ch.TRACK_POWER, ch.FREE_FLAGS)
        built = self.obj(ch.BREAKER['room'])
        raw = ch.add_breaker(built, self.blobs[ch.BREAKER_SOURCE + '_app.obj'])
        old, new = RoomObjects.parse(built), RoomObjects.parse(raw)
        sizes, groups = s.counts(built, 1)
        self.assertEqual(s.counts(raw, 1), (sizes + (2,), groups + 2))
        self.assertEqual(new.records[0].raw, old.records[0].raw)
        old_e, new_e = (Entities.parse(x.records[1].sections[0]).records for x in (old, new))
        self.assertEqual(new_e[:-2], old_e)
        native = RoomObjects.parse(self.blobs[ch.BREAKER_SOURCE + '_app.obj'])
        labels = native.names[1].labels
        source = {labels[i]: e for i, e in enumerate(Entities.parse(native.records[1].sections[0]).records)}
        switch, trigger = new_e[-2:]
        self.assertEqual(switch[12:], source['Object (Switch)'][12:])
        self.assertEqual((trigger[12:20], trigger[24:27]), (source['Trigger (Button Press)'][12:20],
                                                            source['Trigger (Button Press)'][24:27]))
        self.assertEqual(trigger[27], groups + 1)                    # pressing runs Breaker_Throw
        self.assertEqual(struct.unpack_from('<3i', switch), ch.BREAKER['switch'])
        events = Events.parse(new.records[1].sections[1], new.records[1].raw[3]).groups
        old_events = Events.parse(old.records[1].sections[1], old.records[1].raw[3]).groups
        self.assertEqual(events[1:groups], old_events[1:])
        throw, thrown = events[groups].commands, events[groups + 1].commands
        self.assertIn(s.set_var(ch.TRACK_POWER, 1), throw)
        self.assertIn(ch.say('breaker'), throw)
        self.assertEqual(thrown, (s.animate(len(sizes), 1, ch.SWITCH_THROWN),))
        self.assertEqual(events[0].commands[:-2], old_events[0].commands)
        self.assertEqual(events[0].commands[-2:], (
            s.activate(entity=(len(sizes), 1)),
            s.if_var(ch.TRACK_POWER, '==', 0, then=s.action(entity=(len(sizes), 2)), otherwise=s.action(eg=groups + 2))))

    def test_power_hint_runs_only_while_the_tracks_are_live(self):
        from tools import room_script as s
        built = self.obj(ch.HINT_ROOM)
        raw = ch.add_power_hint(built)
        _, groups = s.counts(built, 1)
        events = Events.parse(*(lambda r: (r.sections[1], r.raw[3]))(RoomObjects.parse(raw).records[1])).groups
        self.assertEqual(events[groups].commands, (ch.say('live_tracks'),))
        self.assertEqual(events[0].commands[-1], s.if_var(ch.TRACK_POWER, '==', 0, then=s.action(eg=groups + 1)))
        # The Platform's own boiler logic reads the same shared flag.
        reads = {struct.unpack_from('<H', c.operand)[0] for g in events for c in g.commands if c.opcode == ch.IF_VAR}
        self.assertIn(ch.TRACK_POWER, reads)

    def test_objective_board_picks_one_line_by_progress(self):
        from tools import room_script as s
        built = self.obj(ch.OBJECTIVE_ROOM)
        completed = self.local[ch.COMPLETED]
        self.assertIn(completed, ch.FREE_FLAGS)
        raw = ch.add_objectives(built, completed)
        _, groups = s.counts(built, 1)
        events = Events.parse(*(lambda r: (r.sections[1], r.raw[3]))(RoomObjects.parse(raw).records[1])).groups
        power, nest, done, check = range(groups + 1, groups + 5)
        self.assertEqual([events[g - 1].commands for g in (power, nest, done)],
                         [(ch.say('goal_power'),), (ch.say('goal_nest'),), (ch.say('goal_done'),)])
        self.assertEqual(events[check - 1].commands, (s.if_var(ch.TRACK_POWER, '==', 0, then=s.action(eg=power),
                                                               otherwise=s.action(eg=nest)),))
        self.assertEqual(events[0].commands[-1], s.if_var(completed, '==', 0, then=s.action(eg=check),
                                                          otherwise=s.action(eg=done)))   # completion first
        self.assertTrue(all(len(text) <= 80 for text in ch.LINES.values()))

    def test_message_accessor_keeps_native_ids_and_adds_chapter_ids(self):
        at = ch.MESSAGE_ACCESSOR - ch.BASE
        self.assertEqual(struct.unpack_from('<9I', self.arm9, at), ch.ACCESSOR_NATIVE)
        for address in ch.MESSAGE_BOUNDS:
            self.assertEqual(struct.unpack_from('<I', self.arm9, address - ch.BASE)[0], ch.CMP_R1 | ch.MESSAGE_FIRST)
        words = ch.message_accessor(0x02155800)
        self.assertEqual(len(words), len(ch.ACCESSOR_NATIVE))
        self.assertEqual(words[7], ch.MESSAGE_TABLE)
        self.assertEqual(words[8] + ch.MESSAGE_FIRST * ch.MESSAGE_SIZE, 0x02155800)
        # Both ldr literals are pc + 8 + 0x10 away from their instruction.
        self.assertEqual([(w & 0x0FFFFFFF, i) for i, w in enumerate(words[1:3], 1)], [(0x059F3010, 1), (0x059F3010, 2)])
        self.assertEqual(ch.MESSAGE_ACCESSOR + 4 * 1 + 8 + 0x10, ch.MESSAGE_ACCESSOR + 4 * 7)
        self.assertEqual(ch.MESSAGE_ACCESSOR + 4 * 2 + 8 + 0x10, ch.MESSAGE_ACCESSOR + 4 * 8)
        entry = ch.message_entries(1049)[:ch.MESSAGE_SIZE]
        native = self.arm9[ch.MESSAGE_TABLE - ch.BASE:ch.MESSAGE_TABLE - ch.BASE + ch.MESSAGE_SIZE * ch.MESSAGE_FIRST]
        for native_id in (0x0E, 0x29):          # voiceless one-page natives (district text, tutorial)
            self.assertEqual(native[native_id * 44 + 4:native_id * 44 + 44], entry[4:])
        self.assertEqual(struct.unpack_from('<I', entry)[0], 1049)
        self.assertEqual(ch.say('breaker').operand, bytes((0, 0, ch.MESSAGE_FIRST + 1, 0, 0, 0, 0, 0)))
        self.assertLessEqual(ch.MESSAGE_FIRST + len(ch.LINES), 0xFF)

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
