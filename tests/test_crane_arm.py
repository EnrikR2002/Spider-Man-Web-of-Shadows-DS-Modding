"""Long Arm three-act fight: ARM health/meter contracts and the published script edits."""
import struct
import unittest
from tests.arm_runtime import ArmProbe
from tools import crane_arm as a, crane_boss as cb, chapter_spectacle_events as ev
from tools import wos_tool as w, spider2099 as assets
from tools.room_events import Events
from tools.room_objects import RoomObjects


class Arm(unittest.TestCase):
    at, old, cells, stats, manager = 0x021a1000, 0x021b0000, 0x021a0000, 0x02203000, 0x02204000
    core, ret, stack = 0x02210000, 0x021f0000, 0x023f0000
    FULL = 36*4096

    def fixture(self, code, *, room=106, kind=0x21, hp=FULL, run=1):
        p = ArmProbe()
        p.code(self.at, code)
        for at in range(self.cells, self.cells+0x4C, 4):p.put(at, 0)
        p.put(self.cells+0x44, 1234);p.put(self.cells+0x48, self.FULL)
        for at in range(self.manager+0x1b8, self.manager+0x1d0, 4):p.put(at, 0)
        p.memory[self.manager+0x1c0] = run
        for at, value in ((0x02145c5c, self.stats), (0x02145c34, self.manager), (self.stats, room),
                          (self.core, 0x02130000), (self.core+0x10c, kind), (self.core+0x110, hp)):
            p.put(at, value)
        return p

    def phase(self, p, hp_after=None, grow=None):
        def old(probe, regs, flags):
            if grow is not None:probe.put(self.core, grow)
            return flags
        regs = [0]*16;regs[0], regs[13], regs[14], regs[15] = self.core, self.stack, self.ret, self.at
        p.run(regs, 0, {self.ret}, {self.old: old})
        return p.memory[self.manager+0x1c8], p.get(self.cells+0x44)

    def test_phase_marker_follows_real_core_health_and_mirrors_it_for_the_meter(self):
        code = a.fury_phase(self.at, self.old, self.cells)
        for hp, marker in ((self.FULL, 0), (a.FURY_HP+1, 0), (a.FURY_HP, 2), (4096, 2)):
            with self.subTest(hp=hp):
                self.assertEqual(self.phase(self.fixture(code, hp=hp)), (marker, hp))

    def test_dead_or_negative_core_shows_an_empty_meter_and_never_a_phase(self):
        code = a.fury_phase(self.at, self.old, self.cells)
        for hp in (0, -4096):
            with self.subTest(hp=hp):
                self.assertEqual(self.phase(self.fixture(code, hp=hp)), (0, 0))

    def test_other_rooms_other_actors_and_replaced_cores_are_untouched(self):
        code = a.fury_phase(self.at, self.old, self.cells)
        self.assertEqual(self.phase(self.fixture(code, room=105, hp=4096)), (0, 1234))
        self.assertEqual(self.phase(self.fixture(code, kind=0x20, hp=4096)), (0, 1234))
        self.assertEqual(self.phase(self.fixture(code, hp=4096), grow=0x02131111), (0, 1234))

    def finder(self, p, found=0x5150):
        def old(probe, regs, flags):
            regs[0] = found
            return flags
        regs = [0]*16;regs[13], regs[14], regs[15] = self.stack, self.ret, self.at
        regs, _, _ = p.run(regs, 0, {self.ret}, {self.old: old})
        return regs[0], p.get(self.cells+0x44)

    def test_boss_finder_answers_for_the_running_hoist_only(self):
        code = a.hoist_resolver(self.at, self.old, self.cells)
        self.assertEqual(self.finder(self.fixture(code, run=1)), (self.cells, 1234))
        # An idle hoist refills the displayed bar for the next attempt and defers to the published finder.
        self.assertEqual(self.finder(self.fixture(code, run=0)), (0x5150, self.FULL))
        # Any other room is exactly the published Conductor finder.
        self.assertEqual(self.finder(self.fixture(code, room=89, run=1)), (0x5150, 1234))

    def test_hoist_health_matches_the_boss_the_cells_describe(self):
        self.assertEqual(cb.HEALTH, self.FULL)
        self.assertEqual((a.HALF_HP, a.FURY_HP), (cb.HEALTH*2//3, cb.HEALTH//3))


@unittest.skipUnless(a.PARENT_PATH.exists(), 'published v0.38.0 build missing')
class Script(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import mod
        rom = a.PARENT_PATH.read_bytes()
        names, blobs = assets.resources(rom)
        cls.parent = blobs[names.index(a.OBJ)]
        _, glob, _ = mod.load_clean()
        offsets, native, _ = w.parse_glob(glob)
        cls.native = lambda self_, name: glob[offsets[native.index(name)]:offsets[native.index(name)+1]]
        cls.raw = a.script(cls.parent, lambda name: cls.native(None, name))

    def groups(self, raw):
        rec = RoomObjects.parse(raw).records[1]
        return Events.parse(rec.sections[1], rec.raw[3]).groups, ev.s.names(raw, 1)[1]

    def test_the_three_acts_use_published_entry_points_and_fit_the_byte_ids(self):
        groups, names = self.groups(self.raw)
        old, _ = self.groups(self.parent)
        self.assertLessEqual(len(groups), 255)
        self.assertEqual(groups[:len(old)] != old, True)
        for name in ('Slam_Aftermath', 'Fury_Gate', 'Fury_Again', 'Backup_Call', 'Reserve_Call',
                     'Warn0_Go_Fury', 'Warn1_Go_Fury', 'Warn2_Go_Fury', 'Sweep_Warn_Go_Fury'):
            self.assertEqual(names.count(name), 1, name)

    def test_fury_tell_is_shorter_than_every_published_tell(self):
        groups, names = self.groups(self.raw)
        delays = [struct.unpack_from('<H', c.operand)[0] for c in groups[names.index('Warn0_Go_Fury')].commands
                  if c.opcode == 0x1C and struct.unpack_from('<H', c.operand)[0]]
        self.assertEqual(delays, [a.FURY_TELL])
        self.assertLess(a.FURY_TELL, 0x24)

    def test_start_no_longer_calls_the_opening_crew_and_init_resets_the_new_variables(self):
        groups, names = self.groups(self.raw)
        old, _ = self.groups(self.parent)
        start = names.index('Start')
        gone = [c for c in old[start].commands if c not in groups[start].commands]
        self.assertEqual([(c.opcode, c.operand[4]) for c in gone], [(0x1C, a.CREW_AG+1)])
        reset = {struct.unpack_from('<H', c.operand)[0] for c in groups[0].commands[:3]}
        self.assertEqual(reset, {a.WAVE_A, a.WAVE_B, a.CHAIN})

    def test_every_slam_hands_over_to_the_aftermath_gate_after_the_published_delay(self):
        groups, names = self.groups(self.raw)
        after = names.index('Slam_Aftermath')+1
        for i in range(3):
            last = groups[names.index(f'Hit{i}_Go')].commands[-1]
            self.assertEqual((last.opcode, struct.unpack_from('<H', last.operand)[0], last.operand[5]), (0x1C, 18, after))

    def test_script_edit_is_exact_to_its_parent_only(self):
        with self.assertRaises(ValueError):a.script(self.raw, lambda name: self.native(None, name))


class Release(unittest.TestCase):
    def test_only_the_exact_published_parent_is_accepted(self):
        with self.assertRaises(ValueError):a.apply_rom(bytes(64))


if __name__ == '__main__':
    unittest.main()
