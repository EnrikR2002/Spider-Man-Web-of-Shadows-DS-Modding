"""Talon routing/ABI, native R exit and exact parent-resource isolation."""
import unittest
from types import SimpleNamespace

from tests.arm_runtime import ArmProbe
from tools import talon_lift as t, tasm_kit as kit, wos_tool as w
from tools.animation_rig import AnimationRig
from tools.kit_choreography import Rig
from tools.sca import Sca
from tools.sca_author import sample


class Runtime(unittest.TestCase):
    at = 0x021a0100
    hero, mot, ctl, stats = 0x02200000, 0x02201000, 0x02202000, 0x02203000
    stack, end = 0x023f0000, 0x03000000
    values = dict(OLD_ANIMATION=0x021b0000, OLD_EVADE=0x021b0100, LIFT_SCA=6000)

    def fixture(self):
        p = ArmProbe()
        p.code(self.at, t.runtime(self.at, self.values))
        for at, value in ((self.hero, 0x0212e3f0), (self.hero+0x30, self.mot), (self.hero+0x34, 1),
            (self.hero+0xe8, self.stats), (self.stats, 1<<21), (self.mot, self.hero),
            (self.mot+0x258, 128), (self.mot+0x254, 128), (self.mot+0x178, 5), (self.mot+0x1f8, self.ctl),
            (self.ctl+0x44, self.hero), (self.ctl+0x14, 45), (self.ctl+0x64, 0)):
            p.put(at, value)
        for i in range(6):
            p.put(self.stack+0x2c+i*4, 100+i)
        return p

    def animation(self, p, *, valid=1, mot=None):
        regs = list(range(16))
        regs[0], regs[4], regs[13], regs[14], regs[15] = valid, self.mot if mot is None else mot, self.stack, self.end, self.at
        out, flags, _ = p.run(regs, 0xa000001f, {self.values['OLD_ANIMATION']})
        self.assertEqual(out[:15], regs[:15])
        self.assertEqual(flags, 0xa000001f)
        return [p.get(self.stack+0x2c+i*4) for i in range(6)]

    def test_only_owned_black_power_launch_changes_sca_and_retains_other_action_fields(self):
        p = self.fixture()
        self.assertEqual(self.animation(p), [6000, 101, 102, 103, 104, 105])
        for field, value in ((self.hero, 0x021301d0), (self.hero+0x34, 0), (self.stats, 1<<20),
            (self.hero+0x30, self.mot+4), (self.mot+0x258, 50), (self.ctl+0x14, 51),
            (self.ctl+0x44, self.hero+4), (self.hero+0xe8, 0), (self.hero+0xe8, 0x02400000),
            (self.hero+0xe8, self.stats+1), (self.mot+0x1f8, 0), (self.mot+0x1f8, 0x02400000),
            (self.mot+0x1f8, self.ctl+1), (self.mot, 0), (self.mot, self.hero+1), (self.mot, 0x02400000)):
            with self.subTest(field=hex(field), value=hex(value)):
                p = self.fixture()
                p.put(field, value)
                self.assertEqual(self.animation(p), list(range(100, 106)))
        for mot in (0, self.mot+1, 0x02400000):
            self.assertEqual(self.animation(self.fixture(), mot=mot), list(range(100, 106)))
        self.assertEqual(self.animation(self.fixture(), valid=0), list(range(100, 106)))

    def test_r_uses_native_queue_without_consuming_b_or_changing_caller_stack(self):
        for queued, owned in ((True, True), (False, True), (True, False)):
            p = self.fixture()
            if not owned:
                p.put(self.stats, 0)
            for i, value in enumerate((44, 45, 46, 47, 48, self.end)):
                p.put(self.stack+0x58+i*4, value)
            calls = []
            def peek(probe, regs, flags):
                self.assertEqual(regs[0], self.ctl+0x28)
                calls.append(probe.get(regs[1]))
                regs[0] = int(queued)
                return flags
            regs = list(range(16))
            regs[8], regs[13], regs[14], regs[15] = self.ctl, self.stack, self.end, self.at+4
            out, _, pc = p.run(regs, 0xa000001f, {self.end, self.values['OLD_EVADE']}, {0x020cff0c: peek})
            take = queued and owned
            self.assertEqual(pc, self.end if take else self.values['OLD_EVADE'])
            self.assertEqual(calls, [3] if owned else [])
            self.assertEqual(out[13], self.stack+0x70 if take else self.stack)
            if take:
                self.assertEqual(out[0], 0x7fffffff)
            else:
                self.assertEqual(out[:15], regs[:15])

    def test_even_a_hit_leaves_b_timing_to_the_native_jump(self):
        p = self.fixture()
        p.put(self.ctl+0x64, 0xf00)
        calls = []
        def peek(probe, regs, flags):
            command = probe.get(regs[1])
            calls.append(command)
            regs[0] = int(command == 2)
            return flags
        regs = list(range(16))
        regs[8], regs[13], regs[14], regs[15] = self.ctl, self.stack, self.end, self.at+4
        out, _, pc = p.run(regs, 0xa000001f, {self.values['OLD_EVADE']}, {0x020cff0c: peek})
        self.assertEqual(calls, [3])
        self.assertEqual(pc, self.values['OLD_EVADE'])
        self.assertEqual(out[:15], regs[:15])


class Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = t.PARENT_PATH.read_bytes()
        cls.result, cls.report = t.apply_rom(cls.parent)
        cls.names, cls.before = t.assets.resources(cls.parent)
        cls.nn, cls.after = t.assets.resources(cls.result)

    def test_single_private_clip_retains_all_native_bindings_assets_and_purchases(self):
        self.assertEqual(self.nn, self.names+[t.SCA])
        self.assertEqual({n for n, a, b in zip(self.names, self.before, self.after) if a != b},
                         {'American.strings', 'English.strings', 'GlobFiles.txt'})
        old = self.before[self.names.index('spd_PowerLauncherAttack.sca')]
        new = self.after[self.nn.index(t.SCA)]
        a, b = Sca.parse(old), Sca.parse(new)
        self.assertEqual((b.frame_count, b.joint_count), (14, 37))
        self.assertEqual(b.to_bytes(), new)
        for joint in range(37):
            for frame in range(14):
                self.assertEqual(sample(a, joint, frame, 'scale'), sample(b, joint, frame, 'scale'))
        for e in w.nitrofs_entries(self.result):
            if e['name'] == 'Glob.bin':
                continue
            old = next(x for x in w.nitrofs_entries(self.parent) if x['name'] == e['name'])
            self.assertEqual(self.result[e['start']:e['end']], self.parent[old['start']:old['end']])

    def test_two_hooks_and_resource_count_fit_existing_tail_with_no_growth(self):
        h, hh = w.parse_header(self.parent), w.parse_header(self.result)
        a = self.parent[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        b = self.result[hh['arm9_offset']:hh['arm9_offset']+hh['arm9_size']]
        self.assertEqual(len(a), len(b))
        self.assertEqual(a[kit.SOURCE:kit.SOURCE+kit.RESERVE], b[kit.SOURCE:kit.SOURCE+kit.RESERVE])
        rt = self.report['runtime']
        offset = kit.SOURCE+rt['entry']-kit.TARGET
        allowed = {x['site']-0x02000000 for x in rt['hooks']} | {t.oscorp_resources.COUNT_OFFSET}
        allowed.update(range(offset, offset+rt['bytes'], 4))
        self.assertLessEqual({i for i in range(0, len(a), 4) if a[i:i+4] != b[i:i+4]}, allowed)
        for row in rt['hooks']:
            self.assertEqual(w.u32(b, row['site']-0x02000000), kit.branch(row['site'], row['target']))
        self.assertEqual(a[-36:], b[-36:])

    def test_resource_growth_preserves_the_parent_occupied_gap_and_tail(self):
        old = sorted(w.nitrofs_entries(self.parent), key=lambda e: e['start'])
        new = sorted(w.nitrofs_entries(self.result), key=lambda e: e['start'])
        delta = self.report['nitrofs_relocation_bytes']
        self.assertGreater(delta, 0)
        self.assertTrue(any(x not in (0, 255) for x in self.parent[old[0]['end']:old[1]['start']]))
        self.assertEqual(self.result[old[0]['end']+delta:old[1]['start']+delta],
                         self.parent[old[0]['end']:old[1]['start']])
        self.assertEqual(new[1]['start'], old[1]['start']+delta)
        self.assertEqual(len(self.parent), len(self.result))
        self.assertEqual(self.result[old[1]['start']+delta:], self.parent[old[1]['start']:-delta])

    def test_authored_rake_overlaps_hands_on_native_contact_and_returns_without_pose_reset(self):
        for channel in t.LIFT.CHANNELS:
            self.assertEqual(t.LIFT.value(channel, 0), t.LIFT.value(channel, 13), channel)
        rig = Rig(Sca.parse(self.before[self.names.index('spd_Idle.sca')]),
                  AnimationRig.parse(self.before[self.names.index('spd.nsbmd')]).parents)
        frames = rig.bake(t.LIFT)[2]
        self.assertGreater(frames[5][9][1]-frames[3][9][1], 3.)
        self.assertGreater(frames[7][19][1]-frames[5][19][1], 1.)
        for frame in frames:
            for joint in (28, 32):
                self.assertLess(abs(frame[joint][1]-.78), .006)

    def test_menu_names_instructions_and_version_change_only_intended_slots(self):
        from tools.qol_suits_menu import decode_grown, slot_count
        for name in ('American.strings', 'English.strings'):
            old, new = self.before[self.names.index(name)], self.after[self.nn.index(name)]
            self.assertEqual(decode_grown(new, 207), 'Talon Lift')
            self.assertIn('Hold \ue600', decode_grown(new, 209))
            self.assertEqual(slot_count(old), slot_count(new))
            for i in range(slot_count(new)):
                if i not in (50, 74, 207, 208, 209):
                    self.assertEqual(decode_grown(old, i), decode_grown(new, i))
            self.assertIn(t.VERSION, decode_grown(new, 50))
            self.assertIn(t.VERSION, decode_grown(new, 74))

    def test_wrong_parent_and_unsafe_lab_output_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact published'):
            t.apply_rom(b'not a ROM')
        from tools import talon_lift_lab
        with self.assertRaisesRegex(ValueError, 'stay in work'):
            talon_lift_lab.run(SimpleNamespace(out=t.ROOT/'original'))


if __name__ == '__main__':
    unittest.main()
