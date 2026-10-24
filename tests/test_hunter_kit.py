"""Hunter input priority, ownership, actual-hit gates, cleanup and exact scope."""
import struct
from types import SimpleNamespace
import unittest

from tests.arm_runtime import ArmProbe
from tools import hunter_kit as h, tasm_kit as kit, wos_tool as w, oscorp_resources


class Runtime(unittest.TestCase):
    at, state = 0x021a1000, 0x021a0000
    hero, mot, ctl, stats = 0x02200000, 0x02201000, 0x02202000, 0x02203000
    enemy, em, config, line = 0x02210000, 0x02211000, 0x02212000, 0x02220000
    stack, end = 0x023f0000, 0x03000000
    values = dict(STATE=state, NATIVE_OBJECT=0x021b0000, OLD_NODE=0x021b0100,
        OLD_ANIMATION=0x021b0200, OLD_UPDATE=0x021b0300, OLD_STRING=0x021b0400, OLD_GENERIC=0x021b0500,
        YANK_SCA=6000, YANK_GMB=6001, SHORT_SCA=6002, SHORT_GMB=6003, YANK_GAB=3352, BOSS_CONFIG=0x02190000,
        WEB_HIT=0x021b0600, WEB_HAND=0x021b0700, WEB_RELEASE=0x021b0800)

    def fixture(self, *, phase=0, form=1, owned=True, x=25, facing=1, clock=4):
        p = ArmProbe()
        p.code(self.at, h.runtime(self.at, self.values))
        for at in range(self.state, self.state+128, 4):
            p.put(at, 0)
        for at in range(kit.KIT_STATE+0x20, kit.KIT_STATE+0xe0, 4):
            p.put(at, 0)
        for at, value in ((self.hero, 0x0212e3f0), (self.hero+0x34, form), (self.hero+0x30, self.mot),
            (self.hero+0xe8, self.stats+12), (self.hero+0xc0, 0), (self.hero+0x18, 0),
            (self.stats, 65), (self.stats+0x14, 1<<19 if owned else 0), (self.stats+0x84, 77824),
            (self.mot, self.hero), (self.mot+0x1f8, self.ctl), (self.mot+0x180, facing),
            (self.mot+0x254, 49 if phase else 99), (self.mot+0x258, 49 if phase else 99),
            (self.mot+0x178, clock), (self.mot+0x2fc, 0), (self.ctl, 0x021352a4),
            (self.ctl+0x44, self.hero), (self.ctl+0x14, 46 if phase else 0),
            (self.enemy, 0x021301d0), (self.enemy+4, 0), (self.enemy+0x30, self.em),
            (self.enemy+0x40, self.config), (self.enemy+0x44, 32768), (self.enemy+0x48, 32768),
            (self.em, self.enemy), (self.line+4, 0), (kit.KIT_STATE+0x20, self.enemy)):
            p.put(at, value)
        for mot, px in ((self.mot, 0), (self.em, x*4096)):
            for off, value in ((0x7c, px), (0x80, 0), (0x160, 0), (0x164, 0)):
                p.put(mot+off, value)
        if phase:
            for off, value in ((0, self.hero), (4, self.ctl), (8, self.enemy+4),
                               (16, self.em), (20, self.config), (24, phase), (32, 65)):
                p.put(self.state+off, value)
            p.put(self.enemy+4, self.state+8)
        return p

    @staticmethod
    def result(value):
        def stub(p, regs, flags):
            regs[0] = value
            return flags
        return stub

    def stubs(self, calls, *, native=0x7fffffff, queued=True, keys=0, live=True, hit=4):
        def peek(p, r, c):
            calls.append(('peek', p.get(r[1])))
            r[0] = int(queued)
            return c
        def consume(p, r, c):
            calls.append(('consume', p.get(r[1])))
            return c
        def fresh(p, r, c):
            r[0] = int(live and r[0] == self.enemy)
            return c
        def hand(p, r, c):
            p.put(r[1], 0)
            p.put(r[1]+4, 2048)
            return c
        def spawn(p, r, c):
            calls.append(('line', p.get(p.get(r[13])), p.get(r[3]), p.get(r[3]+4)))
            p.put(r[0], self.line)
            return c
        def strike(p, r, c):
            calls.append(('hit', *r[:4]))
            r[0] = hit
            return c
        def release(p, r, c):
            calls.append(('release', r[0]))
            for at in range(r[0], r[0]+16, 4):
                p.put(at, 0)
            return c
        return {self.values['NATIVE_OBJECT']: self.result(native), 0x020cff0c: peek, 0x020cfc34: consume,
            0x02152c5c: self.result(keys), 0x02152c68: fresh,
            self.values['WEB_HIT']: strike, self.values['WEB_HAND']: hand, self.values['WEB_RELEASE']: release,
            0x0205f844: spawn, 0x020672d0: self.result(0), 0x0206632c: self.result(0)}

    def run_entry(self, p, index=0, *, regs=None, stops=None, **kw):
        r = list(range(100, 116)) if regs is None else list(regs)
        r[13], r[14], r[15] = self.stack, self.end, self.at+index*4
        before = list(r)
        calls = []
        out, flags, pc = p.run(r, 0xa000001f, stops or {self.end}, self.stubs(calls, **kw))
        return before, out, flags, pc, calls

    def transition(self, p, **kw):
        r = list(range(16))
        r[0] = self.ctl
        before, out, _, _, calls = self.run_entry(p, regs=r, **kw)
        self.assertEqual(out[4:12], before[4:12])
        self.assertEqual(out[13], before[13])
        return out[0], [c for c in calls if c[0] == 'consume']

    def test_native_prompt_wins_before_any_custom_dereference_or_x_consumption(self):
        p = self.fixture()
        p.put(self.ctl+0x44, 0)
        self.assertEqual(self.transition(p, native=82), (82, []))
        self.assertEqual(p.get(self.state+24), 0)

    def test_only_owned_black_ground_x_arms_and_consumes_command_six(self):
        for x, facing in ((25, 1), (-25, 0), (45, 1), (0, 0)):
            p = self.fixture(x=x, facing=facing)
            self.assertEqual(self.transition(p), (46, [('consume', 6)]))
            self.assertEqual(p.get(self.state+8), self.enemy+4)
            self.assertEqual(p.get(self.enemy+4), self.state+8)
        for kw in ({'form': 0}, {'owned': False}, {'x': 46}, {'x': -25}, {'x': 25, 'facing': 0}):
            with self.subTest(kw=kw):
                p = self.fixture(**kw)
                self.assertEqual(self.transition(p), (0x7fffffff, []))
        for kw in ({'live': False}, {'queued': False}, {'keys': 0x100}):
            p = self.fixture()
            self.assertEqual(self.transition(p, **kw), (0x7fffffff, []))
        for field, value in ((self.ctl+0x14, 15), (self.ctl+0x14, 2), (self.ctl+0x14, 3),
            (self.hero+0xc0, self.enemy+4), (self.stats+0x84, 0), (self.enemy+0x44, 0),
            (self.em, self.enemy+4), (self.em+0x80, 9*4096), (self.hero+0xe8, 0x02400000)):
            p = self.fixture()
            p.put(field, value)
            self.assertEqual(self.transition(p), (0x7fffffff, []))

    def test_animation_changes_only_owned_active_resources_and_preserves_flags_registers(self):
        for active in (True, False):
            p = self.fixture(phase=2, owned=active)
            for i in range(6):
                p.put(self.stack+0x2c+4*i, 200+i)
            r = list(range(16))
            r[0], r[4] = 1, self.mot
            before, out, flags, _, _ = self.run_entry(p, 2, regs=r, stops={self.values['OLD_ANIMATION']})
            self.assertEqual(out[:15], before[:15])
            self.assertEqual(flags, 0xa000001f)
            self.assertEqual([p.get(self.stack+0x2c+4*i) for i in range(6)],
                [6000, 201, 202, 6001, 3352, 205] if active else list(range(200, 206)))

    def update(self, p, **kw):
        r = list(range(16))
        r[4] = self.hero
        before, out, flags, _, calls = self.run_entry(p, 3, regs=r, stops={self.values['OLD_UPDATE']}, **kw)
        self.assertEqual(out[:15], before[:15])
        self.assertEqual(flags, 0xa000001f)
        return calls

    def test_distant_target_gets_one_real_scarlet_line_and_one_zero_damage_native_yank(self):
        p = self.fixture(phase=2)
        calls = self.update(p)
        self.assertIn(('line', 0x147f, 25*4096, 0), calls)
        self.assertIn(('hit', self.enemy, 0x21, 0, self.hero), calls)
        self.assertEqual(p.get(self.state+64), 1)
        self.assertFalse(any(c[0] in ('line', 'hit') for c in self.update(p)))

    def test_close_target_skips_pull_and_rake_is_a_single_distance_gated_real_hit(self):
        for up, kind in ((0, 4), (0x40, 0x25)):
            p = self.fixture(phase=2, x=7, clock=18)
            p.put(self.state+36, up)
            calls = self.update(p)
            self.assertFalse(any(c[0] == 'line' for c in calls))
            self.assertIn(('hit', self.enemy, kind, 4096, self.hero), calls)
            self.assertEqual(p.get(self.state+68), 1)
            self.assertFalse(any(c[0] == 'hit' for c in self.update(p)))
        for field in (self.em+0x7c, self.em+0x80):
            p = self.fixture(phase=2, x=7, clock=18)
            p.put(self.state+80, 1)
            p.put(field, 11*4096)
            self.assertFalse(any(c[0] == 'hit' for c in self.update(p)))

    def test_ignored_yank_zips_by_bounded_velocity_and_heavy_up_rake_stays_a_stagger(self):
        p = self.fixture(phase=2)
        self.update(p, hit=1)
        self.assertEqual(p.get(self.state+52), 1)
        self.assertEqual(p.get(self.hero+0x18), 8192)
        self.assertEqual(p.get(self.em+0x7c), 25*4096)
        p.put(self.mot+0x178, 18)
        p.put(self.em+0x7c, 6*4096)
        p.put(self.state+36, 0x40)
        calls = self.update(p)
        self.assertIn(('hit', self.enemy, 4, 4096, self.hero), calls)
        self.assertEqual(p.get(self.hero+0x18), 0)

    def test_close_branch_has_early_contact_and_short_recovery_without_a_yank(self):
        p = self.fixture(phase=2, x=7, clock=5)
        p.put(self.state+88, 1)
        calls = self.update(p)
        self.assertIn(('hit', self.enemy, 4, 4096, self.hero), calls)
        self.assertFalse(any(c[0] == 'line' for c in calls))
        p.put(self.mot+0x178, 11)
        self.update(p)
        self.assertEqual(p.get(self.state+24), 0)

    def test_hurt_death_form_room_replacement_and_stale_targets_unlink_without_damage(self):
        for changes, extra in (({self.ctl+0x14: 63}, {}), ({self.stats+0x84: 0}, {}),
            ({self.hero+0x34: 0}, {}), ({self.stats: 76}, {}), ({self.state: self.hero+4}, {}),
            ({self.state+20: self.config+4}, {}), ({self.enemy+0x44: 0}, {}), ({}, {'live': False})):
            p = self.fixture(phase=2)
            for field, value in changes.items():
                p.put(field, value)
            calls = self.update(p, **extra)
            self.assertFalse(any(c[0] == 'hit' for c in calls))
            self.assertEqual([p.get(self.state+o) for o in (0, 4, 8, 12, 24, 96)], [0]*6)
            self.assertEqual(p.get(self.enemy+4), 0)

    def test_r_falls_through_to_native_evade_without_consuming_a_b_y_or_l(self):
        for index, old in ((4, 'OLD_STRING'), (5, 'OLD_GENERIC')):
            p = self.fixture(phase=2)
            for i, value in enumerate((44, 45, 46, 47, 48, self.end)):
                p.put(self.stack+0x58+4*i, value)
            r = list(range(16))
            r[8] = self.ctl
            _, out, _, pc, calls = self.run_entry(p, index, regs=r,
                stops={self.end, self.values[old]}, queued=True)
            self.assertEqual(pc, self.end)
            self.assertEqual(out[0], 0x7fffffff)
            self.assertEqual(out[13], self.stack+0x70)
            self.assertEqual(calls, [('peek', 3)])


@unittest.skipUnless(h.PARENT_PATH.exists(), 'Private v0.33.1 parent unavailable')
class Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = h.PARENT_PATH.read_bytes()
        cls.result, cls.report = h.apply_rom(cls.parent)
        cls.names, cls.before = h.assets.resources(cls.parent)
        cls.nn, cls.after = h.assets.resources(cls.result)

    def test_only_text_catalog_and_four_private_assets_change(self):
        self.assertEqual(self.nn, self.names+list(h.EXTRAS))
        self.assertEqual({n for n, a, b in zip(self.names, self.before, self.after) if a != b},
                         {'American.strings', 'English.strings', 'GlobFiles.txt'})
        from tools.sca import Sca
        from tools.gmb import Gmb
        from tools.grip_compression import CompressedBlob
        a = Sca.parse(self.after[self.nn.index(h.EXTRAS[0])])
        g = Gmb.parse(CompressedBlob.parse(self.after[self.nn.index(h.EXTRAS[1])]).decoded)
        self.assertEqual((a.frame_count, a.joint_count, g.record_count), (24, 37, 24))
        self.assertEqual(a.to_bytes(), self.after[self.nn.index(h.EXTRAS[0])])
        for e in w.nitrofs_entries(self.result):
            if e['name'] == 'Glob.bin':
                continue
            old = next(x for x in w.nitrofs_entries(self.parent) if x['name'] == e['name'])
            self.assertEqual(self.result[e['start']:e['end']], self.parent[old['start']:old['end']])

    def test_shop_adds_one_independent_bit_and_native_seven_rows_remain_exact(self):
        ah, bh = w.parse_header(self.parent), w.parse_header(self.result)
        a = self.parent[ah['arm9_offset']:ah['arm9_offset']+ah['arm9_size']]
        b = self.result[bh['arm9_offset']:bh['arm9_offset']+bh['arm9_size']]
        rt = self.report['runtime']
        off = kit.SOURCE+rt['shop']-kit.TARGET
        self.assertEqual(b[off:off+7*32], a[h.BLACK_TABLE:h.BLACK_TABLE+7*32])
        self.assertEqual(struct.unpack_from('<3I', b, off+7*32), (392, 382, 382))
        self.assertEqual((w.u32(b, h.BLACK_POINTER), w.u32(b, h.BLACK_COUNT)), (rt['shop'], 8))
        self.assertEqual(a[kit.SOURCE:kit.SOURCE+kit.RESERVE], b[kit.SOURCE:kit.SOURCE+kit.RESERVE])
        self.assertEqual(rt['allocation_bytes'], 4096)

    def test_executable_scope_and_unknown_gap_survive_both_relocations(self):
        ah, bh = w.parse_header(self.parent), w.parse_header(self.result)
        a = self.parent[ah['arm9_offset']:ah['arm9_offset']+ah['arm9_size']]
        b = self.result[bh['arm9_offset']:bh['arm9_offset']+bh['arm9_size']]
        rt = self.report['runtime']
        end, size = len(a)-36, rt['allocation_bytes']
        fields = [(kit.TABLE_POINTERS, 8), (kit.ARENA_LOWER, 4), (h.BLACK_POINTER, 4),
                  (h.BLACK_COUNT, 4), (oscorp_resources.COUNT_OFFSET, 4)]
        fields += [(row['site']-kit.BASE, 4) for row in rt['hooks']]
        allowed = {i for offset, count in fields for i in range(offset, offset+count)}
        self.assertLessEqual({i for i in range(end) if a[i] != b[i]}, allowed)
        self.assertEqual(len(b), len(a)+size)
        self.assertEqual(b[end+size:end+size+24], a[end:end+24])
        old = sorted(w.nitrofs_entries(self.parent), key=lambda e: e['start'])
        new = sorted(w.nitrofs_entries(self.result), key=lambda e: e['start'])
        gap = self.parent[old[0]['end']:old[1]['start']]
        shifted = self.result[new[0]['end']:new[1]['start']]
        self.assertTrue(any(x not in (0, 255) for x in gap))
        self.assertTrue(shifted.endswith(gap))

    def test_motion_returns_to_its_start_and_keeps_feet_planted(self):
        from tools.kit_choreography import Rig
        from tools.sca import Sca
        from tools.animation_rig import AnimationRig
        rig = Rig(Sca.parse(self.before[self.names.index('spd_Idle.sca')]),
                  AnimationRig.parse(self.before[self.names.index('spd.nsbmd')]).parents)
        for clip in (h.art.YANK, h.art.RAKE):
            for channel in clip.CHANNELS:
                self.assertEqual(clip.value(channel, 0), clip.value(channel, clip.samples-1), channel)
            for frame in rig.bake(clip)[2]:
                for joint in (28, 32):
                    self.assertLess(abs(frame[joint][1]-.78), .006)

    def test_only_boot_options_and_three_appended_text_slots_change(self):
        from tools.qol_suits_menu import decode_grown, slot_count
        for name in ('American.strings', 'English.strings'):
            a, b = self.before[self.names.index(name)], self.after[self.nn.index(name)]
            self.assertEqual(slot_count(b), slot_count(a)+3)
            for i in range(slot_count(a)):
                if i not in (50, 74):
                    self.assertEqual(decode_grown(a, i), decode_grown(b, i))
            self.assertEqual(decode_grown(b, slot_count(a)), 'Web Yank')

    def test_wrong_parent_and_unsafe_lab_output_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact published'):
            h.apply_rom(b'not a ROM')
        from tools import hunter_kit_lab
        with self.assertRaisesRegex(ValueError, 'stay in work'):
            hunter_kit_lab.run(SimpleNamespace(out=h.ROOT/'original'))


if __name__ == '__main__':
    unittest.main()
