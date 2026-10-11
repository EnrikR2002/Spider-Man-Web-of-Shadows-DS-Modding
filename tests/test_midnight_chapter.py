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
        exits = {(name, x.group): x for name in (*ch.BY_NAME, ch.ENTRANCE) for x in doors.exits(self.final(name))
                 if x.record == 0 and (name != ch.ENTRANCE or x.room >= ch.FIRST) and (name, x.group) not in ch.SEALED}
        self.assertEqual(len(exits), len(ch.LINKS) + 1)
        for (name, group), x in exits.items():
            dest = self.name_of(x.room)
            if (name, group) in ch.LINKS: self.assertEqual(ch.LINKS[(name, group)], (dest, x.spawn))
            self.assertEqual(x.selector, 1)
            spawn = next(s for s in doors.spawns(self.final(dest)) if s.spawn_id == x.spawn)
            # The nearest exit trigger to the arrival point must lead back.
            nearest = min(self.triggers(self.final(dest)).items(),
                          key=lambda t: (t[1][0] - spawn.x) ** 2 + (t[1][1] - spawn.y) ** 2)[0]
            back = next(b for b in doors.exits(self.final(dest)) if b.record == 0 and b.group == nearest)
            self.assertEqual(self.name_of(back.room), name, (name, group, dest))

    def test_every_link_joins_opposite_door_kinds(self):
        for (name, group), (dest, spawn) in ch.LINKS.items():
            arrival = next(s for s in doors.spawns(self.final(dest)) if s.spawn_id == spawn)
            back = min(self.triggers(self.final(dest)).items(),     # the door beside the arrival
                       key=lambda t: (t[1][0] - arrival.x) ** 2 + (t[1][1] - arrival.y) ** 2)[0]
            self.assertEqual(doors.door_kind(self.final(name), group), doors.OPPOSITE[doors.door_kind(self.final(dest), back)],
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
            shipped = RoomObjects.parse(self.final(room.name)).records[1]    # proto01 marks nothing natively
            init = Events.parse(shipped.sections[1], shipped.raw[3]).groups[0]
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

    def record1(self, raw):
        from tools import room_script as s
        record = RoomObjects.parse(raw).records[1]
        return s.names(raw, 1), Events.parse(record.sections[1], record.raw[3]).groups

    def finished(self, name):
        """The room as apply_rom ships it, without its breaker/hint/objective appends."""
        raw = self.obj(name)
        if ch.BY_NAME[name].encounters and name != ch.YARD['room']: raw = ch.open_hammer_floors(raw)[0]
        if name in ch.UNSEALED: raw = ch.unseal(raw)
        if name == ch.BOSS['room']: raw = ch.stage_boss(raw)
        if name == ch.GRATE['room']: raw = ch.seal_grate(raw, ch.VISITED_BASE + ch.BY_NAME[ch.GRATE['opened_by']].index)
        if name == ch.YARD['room']:
            raw = ch.stage_yard(raw, self.blobs[ch.BY_NAME[ch.YARD['hub']].source + '_app.obj'],
                                self.blobs[ch.YARD['gang']['source'] + '_app.obj'], ch.VISITED_BASE + ch.BY_NAME[name].index)
        if name == ch.YARD['hub']: raw = ch.add_yard_door(raw, self.blobs[ch.YARD['hub_door']['source'] + '_app.obj'])
        return raw

    def final(self, name):
        return self.entrance if name == ch.ENTRANCE else self.finished(name)

    def test_no_clone_needs_sledgehammer_slam(self):
        """The player's softlock (2026-10-11): red ichor floors only the boss's withheld reward breaks."""
        from tools import room_script as s
        floors = {}
        for room in ch.ROOMS:
            if not room.encounters or room.name == ch.YARD['room']: continue     # the Yard: test_yard_...
            raw, count = ch.open_hammer_floors(self.obj(room.name))
            if count: floors[room.name] = count
            batches = Entities.parse(RoomObjects.parse(raw).records[1].sections[0]).batches
            red = {b for b, batch in enumerate(batches) for e in batch.records
                   if len(e) >= 24 and struct.unpack_from('<I', e, 12)[0] == ch.OBJECT_TYPE and e[22] == ch.SLEDGEHAMMER_FLOOR}
            _, groups = self.record1(raw)
            for group in groups:
                for c in group.commands:
                    if c.opcode != s.DEACTIVATE:
                        self.assertFalse(any(s.targets(a) & red for a in s.actions(c)), room.name)
            self.assertEqual(s.counts(raw, 1), s.counts(self.obj(room.name), 1))       # nothing is renumbered
        self.assertEqual(floors, {'ML_NestGate': 1, 'ML_NestHollow': 1, 'ML_Venom': 2})
        # Natively those floors are raised by the room init until smashed.
        native = self.blobs['Hive_Map02_app.obj']
        (names, _, batches), groups = self.record1(native)
        hammer = batches.index('Hammer Object')
        self.assertIn(s.if_var(0x71, '==', 0, then=s.action(ag=hammer)), groups[0].commands)

    def test_nest_rooms_never_run_their_door_seal(self):
        from tools import room_script as s
        self.assertEqual(set(ch.UNSEALED), {r.name for r in ch.ROOMS if r.source.startswith('Hive_Map') and r.encounters})
        for name in ch.UNSEALED:
            raw = self.finished(name)
            (_, egs, _), groups = self.record1(raw)
            seal = egs.index(ch.SEAL_GROUP) + 1
            calls = [c for g in groups for c in g.commands if c.opcode != s.DEACTIVATE and any(a[3] == seal for a in s.actions(c))]
            self.assertEqual(calls, [], name)
            (_, _, _), before = self.record1(self.obj(name))
            self.assertEqual(sum(len(g.commands) for g in before) - sum(len(g.commands) for g in groups),
                             1 + (name in ('ML_NestGate', 'ML_NestHollow')), name)   # the seal call (+ the red floor)
            self.assertTrue(groups[egs.index(ch.SEAL_GROUP)].commands)                # the group itself is kept, unused
            spawners = [c for c in groups[0].commands if c == s.activate(ag=1)]
            self.assertEqual(len(spawners), 1, name)                                  # the fight still starts

    def test_boss_arena_starts_and_seals_only_with_spidey_inside(self):
        from tools import room_script as s
        raw, built = self.finished('ML_Venom'), self.obj('ML_Venom')
        (entities, egs, ags), groups = self.record1(raw)
        (_, old_egs, old_ags), old = self.record1(built)
        self.assertEqual((egs, ags[:-1]), (old_egs, old_ags))
        walls, arena = ags.index(ch.BOSS['walls']), len(ags) - 1
        self.assertEqual(ags[arena], 'Arena Trigger')
        route, start, fight, reward = (groups[egs.index(ch.BOSS[k])].commands for k in ('route', 'start', 'fight', 'reward'))
        self.assertNotIn(s.activate(ag=walls), route)                       # natively raised at room load
        self.assertIn(s.activate(ag=walls), old[egs.index(ch.BOSS['route'])].commands)
        timers = [c for c in start if c.opcode == ch.IF_VAR and struct.unpack_from('<H', c.operand, 2)[0]]
        self.assertEqual(timers, [])                                        # no 450-frame start outside the arena
        self.assertEqual(start[-1], s.activate(ag=arena))
        self.assertEqual(fight[-4:], (s.deactivate(ag=arena), s.activate(ag=walls),
                                      s.animate(walls, 1, ch.GATE_GROW), s.animate(walls, 2, ch.GATE_GROW)))
        self.assertEqual(reward[-1], ch.say('way_up'))
        trigger = Entities.parse(RoomObjects.parse(raw).records[1].sections[0]).batches[arena].records[0]
        x, y = (v / 4096 for v in struct.unpack_from('<2i', trigger))
        w, h = struct.unpack_from('<2H', trigger, 20)
        self.assertEqual(trigger[27], egs.index(ch.BOSS['fight']) + 1)
        # The box lies inside the arena, clear of both wall openings (x 24.5..30.5 and 149.5..155.5) by 10 units.
        self.assertTrue(30.5 + 10 <= x - w / 2 and x + w / 2 <= 149.5 - 10)
        from tools.room_collision import RoomCollision
        arena_bsp = RoomCollision.parse(self.blobs['Downtown_Map14.bsp'])
        self.assertTrue(all(arena_bsp.solid_at(px, 50) is None for px in (27.5, 152.5)))     # the wall openings
        self.assertTrue(all(arena_bsp.solid_at(px, 40) is None for px in (20, 160)))         # where the red floors sat
        self.assertIsNone(arena_bsp.solid_at(x - w / 2 + 1, 20))

    def test_stairs_grate_opens_only_after_the_gate(self):
        from tools import room_script as s
        raw, built = self.finished('ML_Stairs'), self.obj('ML_Stairs')
        opened = ch.VISITED_BASE + ch.BY_NAME['ML_NestGate'].index
        (entities, egs, ags), groups = self.record1(raw)
        sizes, count = s.counts(built, 1)
        self.assertEqual(s.counts(raw, 1), (sizes + (1,), count + 2))
        door = (0, entities[0].index(ch.GRATE['door']) + 1)
        self.assertEqual(groups[0].commands[-1], s.if_var(opened, '==', 0, then=s.action(eg=count + 1)))
        self.assertEqual(groups[count].commands, (s.door(door, True), s.activate(ag=len(sizes))))
        self.assertEqual(groups[count + 1].commands, (ch.say('sealed_grate'), s.deactivate(entity=(len(sizes), 1))))
        # The Gate's ceiling exit arrives through this grate, and visiting the Gate sets the flag first.
        self.assertEqual(ch.LINKS[('ML_NestGate', 2)], ('ML_Stairs', 1))
        gate_init = self.record1(self.finished('ML_NestGate'))[1][0].commands
        self.assertIn(s.set_var(opened, 1), gate_init)
        # The breaker is appended after it, as apply_rom does.
        with_breaker = ch.add_breaker(raw, self.blobs[ch.BREAKER_SOURCE + '_app.obj'])
        self.assertEqual(s.counts(with_breaker, 1), (sizes + (1, 2), count + 4))

    def test_platform_says_how_the_grate_works_when_the_boiler_breaks(self):
        raw = ch.add_grate_hint(ch.add_power_hint(self.obj(ch.HINT_ROOM)))
        (_, egs, _), groups = self.record1(raw)
        self.assertEqual(groups[egs.index(ch.BOILER_GROUP)].commands[-1], ch.say('grate_clear'))
        self.assertEqual(ch.message_id('grate_clear'), ch.MESSAGE_FIRST + list(ch.LINES).index('grate_clear'))

    def test_yard_is_a_clean_reachable_side_room(self):
        from tools import room_script as s
        from tools.room_collision import RoomCollision
        yard, hub = ch.BY_NAME[ch.YARD['room']], ch.BY_NAME[ch.YARD['hub']]
        raw, native = self.finished(yard.name), RoomObjects.parse(self.blobs['proto01_app.obj'])
        self.assertEqual((doors.spawns(self.blobs['proto01_app.obj']), doors.exits(self.blobs['proto01_app.obj'])), ((), ()))
        self.assertEqual([(x.group, x.room, x.selector, x.spawn) for x in doors.exits(raw)], [(1, hub.index, 1, 2)])
        spawn, = doors.spawns(raw)
        self.assertEqual((spawn.spawn_id, spawn.angle), (1, doors.FACING['left']))
        bsp = RoomCollision.parse(self.blobs['proto01.bsp'])
        x, y = spawn.x / 4096, spawn.y / 4096
        self.assertIsNone(bsp.solid_at(x, y + 3))
        self.assertAlmostEqual(bsp.floor_below(x, y + 3), 40, delta=0.5)       # stands on the tunnel floor
        # The tunnel wall is at 175 and Spidey (half width 3.5) reaches 171.5: the exit box must start before that.
        (tx, ty), = [xy for g, xy in self.triggers(raw).items() if g == 1]
        wall = next(v / 2 for v in range(int(2 * x), 400) if bsp.solid_at(v / 2, y + 3) is not None)
        self.assertLess(tx / 4096 - ch.YARD['exit']['size'][0] / 2, wall - 1)        # overlap = x + 3.5 > box edge
        self.assertGreater(tx / 4096 - ch.YARD['exit']['size'][0] / 2 - 3.5, x + 4)   # arriving does not leave again
        # Test content is out of reach: orbs, red floor/wall, ichor gates and their prompts, hazards.
        entities = Entities.parse(RoomObjects.parse(raw).records[1].sections[0])
        old = Entities.parse(native.records[1].sections[0]).records
        moved = [i for i, (a, b) in enumerate(zip(old, entities.records)) if a != b]
        self.assertEqual(len(moved), 5 + len(ch.YARD['removed_kinds']) + 2)
        for i in moved:
            self.assertEqual(struct.unpack_from('<i', entities.records[i], 4)[0], ch.REMOVED_PICKUP_Y)
            self.assertEqual(entities.records[i][:4] + entities.records[i][8:], old[i][:4] + old[i][8:])
        kinds = {e[22] for i, e in enumerate(entities.records[:len(old)])
                 if i not in moved and len(e) >= 24 and struct.unpack_from('<I', e, 12)[0] == ch.OBJECT_TYPE}
        self.assertFalse(kinds & set(ch.YARD['removed_kinds']))
        (names, egs, ags), groups = self.record1(raw)
        self.assertEqual(ags[-1], 'Yard Gang')
        gang = entities.batches[-1].records[0]
        self.assertEqual((struct.unpack_from('<I', gang, 12)[0], gang[22], bytes(gang[23:])), (ch.SPAWNER_TYPE, 0x08, bytes(5)))
        self.assertEqual(struct.unpack_from('<2H', gang, 16), ch.YARD['gang']['box'])
        visited = ch.VISITED_BASE + yard.index
        self.assertEqual(visited, 266)
        self.assertNotIn(visited, self.local.values())                        # freed by the 138/139 substitution
        self.assertEqual(groups[0].commands[-3:], (s.activate(ag=len(ags) - 1),
                                                   s.if_var(visited, '==', 0, then=s.action(eg=len(egs))),
                                                   s.set_var(visited, 1)))
        self.assertEqual(groups[-1].commands, (ch.say('yard'),))
        chain = {g + 1 for g, n in enumerate(egs) if n.startswith(ch.YARD['pickup_chain'])}
        self.assertFalse([c for c in groups[0].commands if any(a[3] in chain for a in s.actions(c))])
        # Allocations published in v0.8.1 keep their numbers.
        self.assertEqual({k: self.local[k] for k in (('ML_Station', 0x42), ('ML_Platform', 0x27), ('ML_Platform', 0x62), ch.COMPLETED)},
                         {('ML_Station', 0x42): 268, ('ML_Platform', 0x27): 269, ('ML_Platform', 0x62): 270, ch.COMPLETED: 246})

    def test_refuge_gains_the_yard_door_without_losing_anything(self):
        from tools import room_script as s
        from tools.room_collision import RoomCollision
        built, raw = self.obj(ch.YARD['hub']), self.finished(ch.YARD['hub'])
        self.assertEqual(doors.exits(raw)[:-1], doors.exits(built))
        self.assertEqual(doors.spawns(raw)[:-1], doors.spawns(built))
        new = doors.exits(raw)[-1]
        self.assertEqual((new.record, new.group, new.room, new.spawn), (0, 2, ch.BY_NAME[ch.YARD['room']].index, 1))
        self.assertEqual(doors.spawns(raw)[-1].spawn_id, 2)
        bsp = RoomCollision.parse(self.blobs['Sewer_Save04.bsp'])
        (tx, ty), = [xy for g, xy in self.triggers(raw).items() if g == 2]
        wall = next(v / 2 for v in range(20, -40, -1) if bsp.solid_at(v / 2, 5) is not None)
        self.assertGreater(tx / 4096 + ch.YARD['hub_exit']['size'][0] / 2, wall + 1)      # overlap = x - 3.5 < box edge
        arrival = doors.spawns(raw)[-1]
        self.assertGreater(arrival.x / 4096 - 3.5, tx / 4096 + ch.YARD['hub_exit']['size'][0] / 2 + 3)   # arriving stays
        sizes, groups = s.counts(built, 1)
        self.assertEqual(s.counts(raw, 1), (sizes + (1,), groups))
        door = Entities.parse(RoomObjects.parse(raw).records[1].sections[0]).batches[-1].records[0]
        self.assertEqual(struct.unpack_from('<I', door, 12)[0], 3)             # a door entity
        self.assertEqual(self.record1(raw)[1][0].commands[-1], s.activate(ag=len(sizes)))

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
