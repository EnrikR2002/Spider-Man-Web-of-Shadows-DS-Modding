"""Authored chapter rooms: plans compile, doors meet walls, scripts start what they should."""
import struct
import unittest

import mod
from tools import midnight_chapter as ch, midnight_rooms as mr, room_author as ra, room_doors as doors, room_script as s
from tools.room_collision import RoomCollision
from tools.room_entities import Entities
from tools.room_events import Events
from tools.room_objects import RoomObjects

SPOILERS = ('Hive_Map08', 'Hive_Map09', 'Hive_Map10', 'Downtown_Map13', 'Downtown_Map14')


class MidnightRoomsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom, glob, manifest = mod.load_clean()
        cls.blobs = {e['name']: glob[e['offset']:e['offset'] + e['size']] for e in manifest['entries']}
        cls.blob = cls.blobs.__getitem__
        names = [e['name'] for e in manifest['entries']]
        at, _, _, size = struct.unpack_from('<4I', rom, 0x20)
        from tools import room_catalog
        native = room_catalog.parse(rom[at:at + size], names)
        room_names = [r.name for r in native]
        template = cls.blobs[ch.STATE_TEMPLATE + '_app.obj']
        source = next(r for r in native if r.name == mr.SOURCE)
        cls.staged = {}
        for name in mr.AUTHORED:
            raw, _ = ch.build_room(cls.blobs[mr.SOURCE + '_app.obj'], template, ch.BY_NAME[name], source.index, room_names, {})
            cls.staged[name] = ch.stage_authored(raw, ch.BY_NAME[name], cls.blob)
        cls.tree = {name: RoomCollision.parse(mr.compiled(name, cls.blob).collision) for name in mr.AUTHORED}

    def record1(self, name):
        record = RoomObjects.parse(self.staged[name]).records[1]
        return s.names(self.staged[name], 1), Events.parse(record.sections[1], record.raw[3]).groups, Entities.parse(record.sections[0])

    def test_every_authored_room_is_a_chapter_room_built_from_seen_districts(self):
        self.assertEqual(set(mr.AUTHORED), {r.name for r in ch.ROOMS if r.source == mr.SOURCE})
        for name, spec in mr.AUTHORED.items():
            self.assertFalse([a for a in spec.archives if a in SPOILERS], name)
            built = mr.compiled(name, self.blob)
            self.assertLess(built.quads, 400, name)
            self.assertLess(len(built.textures), 110_000, name)        # native rooms hold up to about 240 KB
            self.assertTrue(all(len(t) <= 80 for _, t in spec.lines), name)
            self.assertTrue(mr.sources(name) <= set(self.blobs), name)
            bounds = mr.plan(name, self.blob).bounds
            self.assertEqual(tuple(v // 4096 for v in ch.MAP_FIELDS[name][5:]), (bounds[0], bounds[3], bounds[2], bounds[1]), name)
        self.assertEqual(set(mr.lines()), {'ML_Switchyard', 'ML_RelayHall', 'ML_Roof', 'ML_Roof_clear', 'ML_SignalCore', 'ML_SignalCore_clear','ML_ServiceBay'})
        self.assertTrue(set(mr.lines()) <= set(ch.LINES))
        self.assertFalse(mr.LAB)                                       # lab switches are never set in a build

    def test_signal_arena_is_flat_and_the_entry_bulkhead_still_blocks_a_seal_bypass(self):
        tree=self.tree['ML_SignalCore']
        for x in (8,22,34,46,58,70,80):
            self.assertAlmostEqual(tree.floor_below(x,25),0,delta=.3)  # tree probe resolves to quarter-unit bounds
            for y in (5,18,25):self.assertIsNone(tree.solid_at(x,y))
        self.assertIsNone(tree.solid_at(90,5))
        for y in (18,40,65):self.assertIsNotNone(tree.solid_at(90,y))

    def test_doors_stand_at_walls_and_arrivals_stand_on_floors(self):
        for name, spec in mr.AUTHORED.items():
            raw, tree = self.staged[name], self.tree[name]
            exits = {x.group: x for x in doors.exits(raw) if x.record == 0}
            spawns = {sp.spawn_id: sp for sp in doors.spawns(raw)}
            self.assertEqual(len(exits), len(spec.doors), name)
            for group, door in enumerate(spec.doors, 1):
                dest, spawn = ch.LINKS[(name, group)]
                self.assertEqual((exits[group].room, exits[group].selector, exits[group].spawn), (ch.BY_NAME[dest].index, 1, spawn))
                inward = 1 if door.side == 'left' else -1
                y = door.floor + 5
                self.assertIsNotNone(tree.solid_at(door.wall - inward * 0.5, y), (name, door.label))    # a wall behind the doorway
                self.assertIsNone(tree.solid_at(door.wall + inward * 4, y), (name, door.label))         # and room to stand in it
                self.assertIsNotNone(tree.solid_at(door.wall + inward * 4, door.floor - 0.5), (name, door.label))
                # Spidey stopped up to 4.65 from a doorway's wall (half width 3.5): the exit box must reach
                # well past 1.15, and the arrival point must not touch it.
                cx = door.exit['center'][0] / 4096
                edge = cx + inward * mr.EXIT_SIZE[0] / 2
                self.assertGreaterEqual(inward * (edge - door.wall), 2.5, (name, door.label))
                arrival = spawns[door.spawn_id]
                ax, ay = arrival.x / 4096, arrival.y / 4096
                self.assertGreater(inward * (ax - edge), 3.5 + 2, (name, door.label))
                self.assertIsNone(tree.solid_at(ax, ay + 3), (name, door.label))
                self.assertAlmostEqual(tree.floor_below(ax, ay + 3), door.floor, delta=0.3)
                self.assertEqual(arrival.angle, doors.FACING['right' if door.side == 'left' else 'left'])
                self.assertEqual(doors.door_kind(raw, group), door.side)

    def test_camera_and_anchor_points_fit_the_plan(self):
        for name, spec in mr.AUTHORED.items():
            raw, tree = self.staged[name], self.tree[name]
            x0, y0, x1, y1 = mr.plan(name, self.blob).bounds
            (polygon,) = ra.camera(raw)
            self.assertEqual(polygon, spec.camera[0])
            self.assertTrue(all(x0 + 20 <= x <= x1 - 20 and y0 <= y <= y1 for x, y in polygon), name)   # the native inset
            points = ra.anchors(raw)
            self.assertGreater(len([p for p in points if p[2] == ra.FLOOR]), 0 if spec.save else 3, name)
            for x, y, kind in points:
                self.assertIsNone(tree.solid_at(x, y), (name, x, y, kind))
                if kind == ra.FLOOR:
                    self.assertLessEqual(tree.floor_below(x, y), spec.spawn_top + 0.3, (name, x, y))    # nobody appears on a high platform
                    self.assertFalse(any(abs(x - d.wall) < 12 for d in spec.doors if d.floor == round(y - 2)), (name, x))   # nor in a doorway

    def test_spawners_props_and_first_visit(self):
        for name, spec in mr.AUTHORED.items():
            (entity_names, egs, ags), groups, entities = self.record1(name)
            visited = ch.visited(ch.BY_NAME[name].index)
            init = groups[0].commands
            self.assertEqual(init[-1], s.set_var(visited, 1), name)
            self.assertEqual(init[-2], s.if_var(visited, '==', 0, then=s.action(eg=egs.index('First_Visit') + 1)), name)
            self.assertEqual(groups[egs.index('First_Visit')].commands, (ch.say(name),))
            self.assertEqual(ags[0], '<AG_INIT>')
            self.assertEqual(len(entities.batches[0].records), 0)      # batch 0 is live from the start and stays empty
            started = {c.operand[4] - 1 for c in init if c.opcode == s.DELAY and c.operand[4]}
            for gang in spec.gangs:
                ag = ags.index(gang.label)
                self.assertIn(ag, started, (name, gang.label))
                spawner, = entities.batches[ag].records
                self.assertEqual((struct.unpack_from('<I', spawner, 12)[0], spawner[22], bytes(spawner[23:])), (4, gang.table, bytes(5)))
                self.assertEqual(struct.unpack_from('<2H', spawner, 16), gang.box)
            if spec.props:
                self.assertIn(ags.index('Props'), started, name)
                self.assertEqual(len(entities.batches[ags.index('Props')].records), len(spec.props))
            for spawner in (e for b in entities.batches for e in b.records if struct.unpack_from('<I', e, 12)[0] == 4):
                x, y = (v / 4096 for v in struct.unpack_from('<2i', spawner))
                w, h = struct.unpack_from('<2H', spawner, 16)
                inside = [p for p in ra.anchors(self.staged[name]) if p[2] == ra.FLOOR and abs(p[0] - x) < w / 2 and abs(p[1] - y) < h / 2]
                self.assertGreaterEqual(len(inside), 3, name)          # a spawner needs floor points in its zone

    def test_roof_waves_follow_each_other_and_set_the_flag(self):
        spec = mr.AUTHORED['ML_Roof']
        (_, egs, ags), groups, entities = self.record1('ML_Roof')
        waves = [ags.index(g.label) for g in spec.waves]
        init = groups[0].commands
        self.assertIn(s.activate(ag=waves[0], frames=30), init)
        self.assertFalse([c for c in init if c.opcode == s.DELAY and c.operand[4] - 1 in waves[1:]])   # later waves wait
        order = ['Wave_2', 'Wave_3', 'Waves_Clear']
        for n, (ag, gang) in enumerate(zip(waves, spec.waves)):
            spawner, = entities.batches[ag].records
            self.assertEqual((spawner[22], spawner[23], spawner[24]), (gang.table, 2, 1))     # as native ambush spawners
            self.assertEqual(egs[spawner[25] - 1], order[n])                                  # the group run when it is beaten
        # Each step runs once: a guard group tests a scratch byte the go group sets.
        guards = mr.WAVE_GUARDS
        self.assertTrue(set(guards) <= set(ch.ROOM_SCRATCH))
        self.assertEqual([c for c in init if c.opcode == s.SET_VAR][:3], [s.set_var(g, 0) for g in guards])
        for step, name in enumerate(order):
            go = egs.index(name + '_Go')
            self.assertEqual(groups[egs.index(name)].commands, (s.if_var(guards[step], '==', 0, then=s.action(eg=go + 1)),))
            self.assertEqual(groups[go].commands[0], s.set_var(guards[step], 1))
        # A wave also starts 90 s after the one before, in case that one never reports beaten; the clear never does.
        self.assertIn(s.activate(eg=egs.index('Wave_2') + 1, frames=mr.WAVE_TIMEOUT), init)
        self.assertEqual(groups[egs.index('Wave_2_Go')].commands[1:],
                         (s.activate(ag=waves[1], frames=45), s.activate(eg=egs.index('Wave_3') + 1, frames=mr.WAVE_TIMEOUT)))
        self.assertEqual(groups[egs.index('Wave_3_Go')].commands[1:], (s.activate(ag=waves[2], frames=45),))
        self.assertEqual(mr.WAVE_TIMEOUT, 90 * 60)
        clear = groups[egs.index('Waves_Clear_Go')].commands
        self.assertIn(s.set_var(ch.ROOM_FLAGS[spec.cleared], 1), clear)
        self.assertIn(ch.say('ML_Roof_clear'), clear)
        self.assertFalse([c for g in groups for c in g.commands if c.opcode == s.DELAY and c.operand[5] == egs.index('Waves_Clear') + 1])
        # Tables seen spawning in an authored room in the lab; the Sewer 0x0F table spawned nobody there.
        self.assertEqual([g.table for g in spec.waves], [0x08, 0x0E, 0x0C])
        door = spec.doors[0]
        self.assertGreaterEqual(door.wall - (spec.area[2]), 30)        # the passage keeps the fight away from the exit

    def test_service_bay_copies_the_native_sphere_and_has_a_safe_continue_spawn(self):
        raw=self.staged['ML_ServiceBay'];spec=mr.AUTHORED['ML_ServiceBay']
        native=RoomObjects.parse(self.blobs['Sewer_Save04_app.obj']).records[0]
        sphere=next(e for e in Entities.parse(native.sections[0]).records if len(e)==16 and struct.unpack_from('<I',e,12)[0]==10)
        record=RoomObjects.parse(raw).records[0];entities=Entities.parse(record.sections[0])
        ag=next(i for i,batch in enumerate(entities.batches) if any(len(e)==16 and struct.unpack_from('<I',e,12)[0]==10 for e in batch.records))
        actual=entities.batches[ag].records[0]
        self.assertEqual(actual[8:],sphere[8:])
        self.assertEqual(struct.unpack_from('<2i',actual),tuple(round(v*4096) for v in spec.save))
        self.assertIn(s.activate(ag=ag),Events.parse(record.sections[1],record.raw[3]).groups[0].commands)
        spawn=next(p for p in doors.spawns(raw) if p.spawn_id==0)
        self.assertEqual((spawn.x,spawn.y),(40*4096,2*4096))
        self.assertIsNone(self.tree['ML_ServiceBay'].solid_at(40,7))
        self.assertFalse(spec.gangs or spec.waves or spec.hazards)

    def test_relay_arcs_take_turns_with_a_rest_between(self):
        spec = mr.AUTHORED['ML_RelayHall']
        (_, egs, ags), groups, entities = self.record1('ML_RelayHall')
        tree = self.tree['ML_RelayHall']
        phases = [ags.index(f'Arcs {n}') for n in (1, 2)]
        for ag, points in zip(phases, spec.hazards):
            arcs = entities.batches[ag].records
            self.assertEqual([tuple(v / 4096 for v in struct.unpack_from('<2i', e)) for e in arcs], [tuple(map(float, p)) for p in points])
            self.assertTrue(all(struct.unpack_from('<I', e, 12)[0] == 14 and e[22] == 0x11 for e in arcs))   # Hazard_Electric
            for x, y in points:
                self.assertIsNone(tree.solid_at(x, y))
                self.assertAlmostEqual(tree.floor_below(x, y), y - 1, delta=0.3)       # one unit above a catwalk
        self.assertFalse(set(spec.hazards[0]) & set(spec.hazards[1]))
        live = [egs.index(f'Arcs_{n}_Live') for n in (1, 2)]
        rest = [egs.index(f'Arcs_{n}_Rest') for n in (1, 2)]
        for n in (0, 1):
            self.assertEqual(groups[live[n]].commands, (s.activate(ag=phases[n]), s.activate(eg=rest[n] + 1, frames=spec.hazard_period)))
            self.assertEqual(groups[rest[n]].commands, (s.deactivate(ag=phases[n]), s.activate(eg=live[1 - n] + 1, frames=spec.hazard_rest)))
        self.assertIn(s.activate(eg=live[0] + 1, frames=30), groups[0].commands)
        self.assertGreaterEqual(spec.hazard_rest, 40)                  # a jump between catwalks takes about 35 frames
        # The lowest catwalk and the ledge at the upper door are never live; tops are a held jump (27) apart.
        safe = {mr.RELAY_CATWALKS[0][3], mr.RELAY_TOP[3]}
        self.assertFalse({y - 1 for phase in spec.hazards for _, y in phase} & safe)
        tops = [0, *(c[3] for c in mr.RELAY_CATWALKS), mr.RELAY_TOP[3]]
        self.assertTrue(all(10 < b - a <= 20 for a, b in zip(tops, tops[1:])))
        # Outer walls cannot be climbed (surface value 1), the catwalks can be stood on and held (10).
        raw = mr.compiled('ML_RelayHall', self.blob).collision
        values = {value for entries in RoomCollision.parse(raw).lists for _, value in entries}
        self.assertEqual(values, {mr.NO_CLING, 10})


if __name__ == '__main__':
    unittest.main()
