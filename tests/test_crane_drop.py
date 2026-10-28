"""Cargo drops: the container's motion contract and the rooms' published-script edits."""
import struct
import unittest
from tests.arm_runtime import ArmProbe
from tools import crane_arm as a, crane_drop as d, spider2099 as assets, chapter_spectacle_events as ev
from tools import wos_tool as w
from tools.room_events import Events
from tools.room_objects import RoomObjects


class Motion(unittest.TestCase):
    at, old, rows, stats, manager = 0x021a1000, 0x021b0000, 0x021a0800, 0x02203000, 0x02204000
    obj, ret, stack = 0x02210000, 0x021f0000, 0x023f0000

    def fixture(self, *, room=97, kind=d.CLOSED, state=0, y=0, dead=0, rows=None):
        p = ArmProbe()
        p.code(self.at, d.drop_motion(self.at, self.old, self.rows))
        p.code(self.rows, rows if rows is not None else d.table())
        for at, value in ((0x02145c5c, self.stats), (0x02145c34, self.manager), (self.stats, room),
                          (self.obj+0x10c, kind)):
            p.put(at, value)
        p.memory[self.obj+0x168] = dead
        p.memory[self.manager+0x99+d.DROP] = state
        p.pos = [0, y, 0]
        p.touched = []
        return p

    def tick(self, p):
        def get(probe, regs, flags):
            for i, v in enumerate(p.pos):probe.put(regs[0]+4*i, v)
            p.touched.append('get')
            return flags
        def put(probe, regs, flags):
            p.pos = [struct.unpack('<i', struct.pack('<I', probe.get(regs[1]+4*i)))[0] for i in range(3)]
            p.touched.append('set')
            return flags
        def old(probe, regs, flags):
            p.touched.append('old')
            return flags
        regs = [0]*16
        regs[0], regs[13], regs[14], regs[15] = self.obj, self.stack, self.ret, self.at
        out, _, _ = p.run(regs, 0, {self.ret}, {d.GET_POSITION: get, d.SET_POSITION: put, self.old: old})
        self.assertEqual((out[0], out[13]), (self.obj, self.stack), 'registers and stack are restored')
        return p.pos[1], p.touched

    def test_closed_container_lowers_to_the_deck_then_stops_there(self):
        deck = 68*d.U
        p = self.fixture(room=100, state=1, y=deck+d.HANG*d.U)
        y, touched = self.tick(p)
        self.assertEqual((y, touched), (deck+d.HANG*d.U-d.RISE, ['get', 'set', 'old']))
        for _ in range(60):y, _ = self.tick(p)
        self.assertEqual(y, deck)

    def test_hanging_container_stays_up_and_is_lifted_back_when_it_is_not_lowering(self):
        high = (0+d.HANG)*d.U
        self.assertEqual(self.tick(self.fixture(state=0, y=high))[0], high)
        self.assertEqual(self.tick(self.fixture(state=0, y=high-5*d.U))[0], high-5*d.U+d.RISE)

    def test_open_container_waits_on_the_deck_and_rises_only_when_lifted(self):
        deck = 16*d.U
        self.assertEqual(self.tick(self.fixture(room=105, kind=d.OPEN, state=1, y=deck))[0], deck)
        p = self.fixture(room=105, kind=d.OPEN, state=2, y=deck)
        self.assertEqual(self.tick(p)[0], deck+d.RISE)
        for _ in range(100):y, _ = self.tick(p)
        self.assertEqual(y, (16+d.HANG)*d.U)

    def test_other_rooms_kinds_and_dead_objects_are_only_the_published_tick(self):
        for case in (dict(room=106), dict(room=96), dict(kind=0x13), dict(dead=1)):
            with self.subTest(case=case):
                p = self.fixture(state=1, y=1234, **case)
                self.assertEqual(self.tick(p), (1234, ['old']))

    def test_table_covers_exactly_the_three_drop_rooms(self):
        rooms = [struct.unpack_from('<i', d.table(), 16*i)[0] for i in range(4)]
        self.assertEqual(rooms, [97, 100, 105, 0])
        self.assertEqual(d.LAND_FRAMES, 51)


class Meshes(unittest.TestCase):
    def test_both_container_states_are_distinct_valid_models(self):
        models = d.models()
        self.assertEqual(tuple(models), d.MODELS)
        closed, opened = models.values()
        self.assertNotEqual(closed, opened)
        for raw in models.values():
            self.assertGreater(len(raw), 500)
            self.assertEqual(len(raw) % 4, 0)

    def test_world_rows_describe_each_kind_in_each_room(self):
        rows = d.world_rows((97, 100, 105), 0x100, 0x140)
        self.assertEqual(len(rows), 6*20)
        self.assertEqual(struct.unpack_from('<5I', rows, 0), (97, d.CLOSED, d.DROP, 0x100, 0x100))
        self.assertEqual(struct.unpack_from('<5I', rows, 20), (97, d.OPEN, d.DROP, 0x140, 0x140))


@unittest.skipUnless(a.PARENT_PATH.exists(), 'published v0.38.0 build missing')
class Script(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import mod
        rom = a.PARENT_PATH.read_bytes()
        cls.names, cls.blobs = assets.resources(rom)
        _, glob, _ = mod.load_clean()
        offsets, native, _ = w.parse_glob(glob)
        cls.native = staticmethod(lambda name: glob[offsets[native.index(name)]:offsets[native.index(name)+1]])

    def room(self, room):
        raw = self.blobs[self.names.index(f'zz_{d.ROOMS[room][0]}_app.obj')]
        return raw, d.script(raw, room, self.native)

    def groups(self, raw):
        rec = RoomObjects.parse(raw).records[1]
        return Events.parse(rec.sections[1], rec.raw[3]).groups, ev.s.names(raw, 1)

    def test_every_drop_room_gets_its_sequence_and_stays_inside_the_byte_ids(self):
        for room in d.ROOMS:
            with self.subTest(room=room):
                raw, new = self.room(room)
                groups, names = self.groups(new)
                self.assertLessEqual(len(groups), 255)
                self.assertLessEqual(len(names[2]), 255)
                for n in ('Drop_Arm', 'Drop_Begin', 'Drop_Land', 'Drop_Rise', 'Drop_Clear'):
                    self.assertEqual(names[1].count(n), 1, n)
                self.assertIn('Cargo Drop', names[2])
                self.assertIn('Cargo Drop Open', names[2])

    def test_the_crew_waits_for_the_container_instead_of_starting_with_the_room(self):
        for room in (97, 100):
            with self.subTest(room=room):
                raw, new = self.room(room)
                old, _ = self.groups(raw)
                fresh, _ = self.groups(new)
                crew = d.ROOMS[room][4]
                crew_ag = ev.s.names(raw, 1)[2].index(crew)
                hit = [c for c in old[0].commands if c.opcode == 0x1D and c.operand[6:10] == ev.s.action(ag=crew_ag)]
                self.assertEqual(len(hit), 1)
                self.assertFalse([c for c in fresh[0].commands if c.opcode == 0x1D and c.operand[6:10] == ev.s.action(ag=crew_ag)])
                # The only other change to the init group is the reset in front of it.
                self.assertEqual(len(fresh[0].commands), len(old[0].commands)+1)

    def test_crown_hunters_arrive_by_cargo_and_the_first_crew_is_untouched(self):
        raw, new = self.room(105)
        old, names = self.groups(raw)
        fresh, fresh_names = self.groups(new)
        index = names[1].index('Crown_Reinforcements')
        self.assertFalse([c for c in fresh[index].commands if c.opcode == 0x1C and c.operand[2:6] == ev.s.action(ag=names[2].index('Crown Hunters'))])
        land = fresh_names[1].index('Drop_Land')+1
        self.assertEqual(len([c for c in fresh[index].commands if c.opcode == 0x1C and c.operand[2:6] == ev.s.action(eg=land)]), 1)
        self.assertEqual(fresh[0].commands[1:], old[0].commands)

    def test_script_edit_is_exact_to_its_parent_only(self):
        raw, new = self.room(97)
        with self.assertRaises(ValueError):d.script(new, 97, self.native)


@unittest.skipUnless(a.PARENT_PATH.exists(), 'published v0.38.0 build missing')
class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom, cls.report = a.apply_rom(a.PARENT_PATH.read_bytes())

    def test_resource_scope_is_the_three_rooms_the_text_two_appended_models_and_the_chained_passes(self):
        from tools import crane_map, crane_vista
        r = self.report
        mine = {a.OBJ, 'American.strings', 'English.strings', 'GlobFiles.txt', *(f'zz_{cfg[0]}_app.obj' for cfg in d.ROOMS.values())}
        self.assertEqual(set(r['modified_resources']), mine | {crane_vista.MODEL, crane_vista.TEXTURE, *crane_map.nav.SCREENS})
        self.assertEqual(r['composed']['crane_arm_rom_sha256'] == r['rom_sha256'], False)
        self.assertEqual(set(r['composed']['map']['modified_resources']) <= set(crane_map.nav.SCREENS), True)
        self.assertEqual(r['composed']['vista']['collision_identical'], True)
        self.assertEqual([n for n in r['cargo_drop']['appended_resources'] if n.endswith('.nsbmd')], list(d.MODELS))
        names = assets.resources(self.rom)[0]
        self.assertEqual(names[-2:], list(d.MODELS))

    def test_bare_build_stops_before_the_chained_passes(self):
        rom, report = a.apply_rom(a.PARENT_PATH.read_bytes(), compose=False)
        self.assertNotIn('composed', report)
        self.assertNotEqual(w.sha256(rom), w.sha256(self.rom))
        self.assertEqual(report['rom_sha256'], self.report['composed']['crane_arm_rom_sha256'])

    def test_world_table_gains_exactly_the_six_container_rows_and_the_tick_hook_is_chained(self):
        h = w.parse_header(self.rom)
        arm = self.rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        from tools import tasm_kit as kit
        off = lambda address: kit.SOURCE+address-kit.TARGET if address >= kit.TARGET else address-0x02000000
        table = self.report['cargo_drop']['world_table']
        rows, at = [], off(table)
        while w.u32(arm, at):
            rows.append(struct.unpack_from('<5I', arm, at));at += 20
        self.assertEqual([(r[0], r[1]) for r in rows[-6:]], [(97, d.CLOSED), (97, d.OPEN), (100, d.CLOSED),
                         (100, d.OPEN), (105, d.CLOSED), (105, d.OPEN)])
        self.assertEqual(len(rows), 15+6)
        from tools.crane_row import target
        tick = d.cb.TICK_SITE
        self.assertEqual(target(tick, w.u32(arm, tick-0x02000000)), self.report['cargo_drop']['motion_hook'])
        self.assertEqual(w.u32(arm, 0x77F8), len(assets.resources(self.rom)[0]))

    def test_only_the_published_parent_is_accepted(self):
        with self.assertRaises(ValueError):a.apply_rom(self.rom)


if __name__ == '__main__':
    unittest.main()
