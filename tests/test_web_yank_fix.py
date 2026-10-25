"""Firm reel movement, cancellation, hook ABI and immutable-parent byte scope."""
import unittest

from tests import test_hunter_kit as original
from tools import web_yank_fix as f, hunter_kit as h, tasm_kit as kit, wos_tool as w


class Runtime(original.Runtime):
    enemy_ctl = 0x02213000

    def fixture(self, **kw):
        p = super().fixture(**kw)
        p.code(self.at, f.runtime(self.at, self.values))
        p.put(self.hero+4, self.state+112 if kw.get('phase') else 0)
        p.put(self.state+112, self.hero+4 if kw.get('phase') else 0)
        p.put(self.state+124, kw.get('facing', 1))
        p.put(self.em+0x1f8, self.enemy_ctl)
        p.put(self.enemy_ctl+0x14, 37)
        p.put(self.enemy+0x18, 0)
        p.put(self.enemy+0x1c, 1234)
        return p

    def test_distant_target_gets_one_real_scarlet_line_and_one_zero_damage_native_yank(self):
        p = self.fixture(phase=2, clock=2)
        calls = self.update(p)
        self.assertIn(('hit', self.enemy, 0x16, 0, self.hero), calls)
        self.assertEqual(sum(c[0] == 'line' for c in calls), 1)
        self.assertFalse(any(c[0] == 'hit' for c in self.update(p)))

    def test_ignored_yank_zips_by_bounded_velocity_and_heavy_up_rake_stays_a_stagger(self):
        p = self.fixture(phase=2)
        self.update(p, hit=1)
        self.assertEqual(p.get(self.state+52), 1)
        self.assertEqual(p.get(self.hero+0x18), 5*4096)
        p.put(self.mot+0x178, 10)
        p.put(self.em+0x7c, 6*4096)
        p.put(self.state+36, 0x40)
        self.update(p)
        self.assertEqual(p.get(self.state+120), 1)
        p.put(self.mot+0x178, 3)
        self.assertIn(('hit', self.enemy, 4, 4096, self.hero), self.update(p))
        self.assertEqual(p.get(self.hero+0x18), 0)

    def test_close_target_skips_pull_and_rake_is_a_single_distance_gated_real_hit(self):
        for up, kind in ((0, 4), (0x40, 0x25)):
            p = self.fixture(phase=2, x=7, clock=3)
            p.put(self.state+120, 1)
            p.put(self.state+36, up)
            calls = self.update(p)
            self.assertFalse(any(c[0] == 'line' for c in calls))
            self.assertIn(('hit', self.enemy, kind, 4096, self.hero), calls)
            self.assertEqual(p.get(self.state+68), 1)
            self.assertFalse(any(c[0] == 'hit' for c in self.update(p)))

    def test_hurt_death_form_room_replacement_and_stale_targets_unlink_without_damage(self):
        super().test_hurt_death_form_room_replacement_and_stale_targets_unlink_without_damage()
        p = self.fixture(phase=2)
        p.put(self.ctl+0x14, 63)
        self.update(p)
        self.assertEqual(p.get(self.hero+4), 0)
        self.assertEqual(p.get(self.state+112), 0)

    def reel(self, p, **kw):
        r = list(range(16))
        r[0] = self.enemy
        return self.run_entry(p, 6, regs=r, **kw)

    def test_reel_stops_six_units_ahead_in_both_facings_without_changing_coordinates_or_gravity(self):
        for facing, positions in ((1, (40, 12, 6)), (0, (-40, -12, -6))):
            for x in positions:
                with self.subTest(facing=facing, x=x):
                    p = self.fixture(phase=2, x=x, facing=facing)
                    p.put(self.state+44, 4)
                    before, out, _, _, _ = self.reel(p)
                    desired = max(-6, min(6, (6 if facing else -6)-x))*4096
                    self.assertEqual(p.get(self.enemy+0x18), desired & 0xffffffff)
                    self.assertEqual(p.get(self.enemy+0x1c), 1234)
                    self.assertEqual(p.get(self.em+0x7c), (x*4096) & 0xffffffff)
                    self.assertEqual(p.get(self.em+0x80), 0)
                    self.assertEqual(out[4:12], before[4:12])
                    self.assertEqual(out[13], before[13])

    def test_interruption_heavy_dead_or_reused_actors_cannot_be_reeled(self):
        for at, value in ((self.state+112, 0), (self.state+52, 1), (self.state+84, 1), (self.state+120, 1),
                          (self.state+20, 0), (self.state+16, 0), (self.enemy+0x44, 0),
                          (self.hero+0x34, 0), (self.ctl+0x14, 63), (self.enemy_ctl+0x14, 49),
                          (self.stats, 76), (self.state, self.hero+4)):
            p = self.fixture(phase=2)
            p.put(self.state+44, 4)
            p.put(at, value)
            self.reel(p)
            self.assertEqual(p.get(self.enemy+0x18), 0, f'guard {at:#x}={value}')

    def test_impact_and_cancellation_stop_owned_reel_velocity_and_release_web(self):
        for cancel in (False, True):
            p = self.fixture(phase=2, x=6, clock=3)
            p.put(self.state+44, 4)
            self.reel(p)
            p.put(self.enemy+0x18, 9000)
            p.put(self.state+120, 1)
            if cancel:
                p.put(self.ctl+0x14, 63)
            calls = self.update(p)
            self.assertEqual(p.get(self.enemy+0x18), 0)
            self.assertEqual(p.get(self.state+92), 0)
            self.assertTrue(any(c[0] == 'release' for c in calls))
            if not cancel:
                self.assertIn(('hit', self.enemy, 4, 4096, self.hero), calls)
                self.assertEqual(p.get(self.state+112), self.hero+4)
                self.assertEqual(p.get(self.hero+4), self.state+112)
                p.put(self.ctl+0x14, 0)
                self.update(p)
            self.assertEqual(p.get(self.hero+4), 0)
            self.assertEqual(p.get(self.state+112), 0)

    def test_long_clip_releases_after_seventeen_samples(self):
        p = self.fixture(phase=2, clock=17)
        self.update(p)
        self.assertEqual(p.get(self.state+24), 0)

    def test_actual_arrival_reenters_native_action_without_writing_clocks_or_hitting_early(self):
        p = self.fixture(phase=2, x=6, clock=8)
        p.put(self.state+80, 1)
        p.put(self.state+44, 4)
        self.reel(p)
        calls = self.update(p)
        self.assertEqual(p.get(self.state+120), 1)
        self.assertEqual(p.get(self.mot+0x2fc) & 2, 2)
        self.assertEqual(p.get(self.mot+0x178), 8)
        self.assertEqual(p.get(self.enemy+0x18), 0)
        self.assertFalse(any(c[0] == 'hit' for c in calls))


@unittest.skipUnless(f.PARENT_PATH.exists(), 'Private v0.34.0 parent unavailable')
class Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = f.PARENT_PATH.read_bytes()
        cls.result, cls.report = f.apply_rom(cls.parent)

    def test_only_private_cast_and_version_strings_change(self):
        an, ab = h.assets.resources(self.parent)
        bn, bb = h.assets.resources(self.result)
        self.assertEqual(an, bn)
        self.assertEqual({n for n, a, b in zip(an, ab, bb) if a != b},
                         {'American.strings', 'English.strings', *h.EXTRAS})
        from tools.qol_suits_menu import decode_grown, slot_count
        for name in ('American.strings', 'English.strings'):
            a, b = ab[an.index(name)], bb[bn.index(name)]
            self.assertEqual(slot_count(a), slot_count(b))
            for slot in range(slot_count(a)):
                if slot not in (50, 74):
                    self.assertEqual(decode_grown(a, slot), decode_grown(b, slot))
            self.assertEqual(decode_grown(b, 50), 'TASM v'+f.VERSION+'\nPress a button to start')
            self.assertEqual(decode_grown(b, 74), 'Options v'+f.VERSION)
        for channel in f.art.YANK.CHANNELS:
            self.assertEqual(f.art.YANK.value(channel, 17), f.art.RAKE.value(channel, 0))
            self.assertEqual(f.art.RAKE.value(channel, 7), h.art.RAKE.value(channel, 11))
        from tools.sca import Sca
        from tools.gmb import Gmb
        from tools.grip_compression import CompressedBlob
        for sca, gmb, samples in ((h.EXTRAS[0], h.EXTRAS[1], 18), (h.EXTRAS[2], h.EXTRAS[3], 8)):
            self.assertEqual(Sca.parse(bb[bn.index(sca)]).frame_count, samples)
            self.assertEqual(Gmb.parse(CompressedBlob.parse(bb[bn.index(gmb)]).decoded).record_count, samples)
        self.assertEqual(self.report['allocation_bytes'], 0)
        for e in w.nitrofs_entries(self.result):
            if e['name'] == 'Glob.bin':
                continue
            old = next(o for o in w.nitrofs_entries(self.parent) if o['name'] == e['name'])
            self.assertEqual(self.result[e['start']:e['end']], self.parent[old['start']:old['end']])

    def test_entire_executable_outside_existing_private_code_tail_is_exact(self):
        ah, bh = w.parse_header(self.parent), w.parse_header(self.result)
        a = self.parent[ah['arm9_offset']:ah['arm9_offset']+ah['arm9_size']]
        b = self.result[bh['arm9_offset']:bh['arm9_offset']+bh['arm9_size']]
        off = self.report['runtime']['source_offset']
        self.assertEqual(len(a), len(b))
        self.assertEqual(a[:off], b[:off])
        self.assertEqual(a[-36:], b[-36:])
        self.assertEqual(a[kit.SOURCE:kit.SOURCE+kit.RESERVE], b[kit.SOURCE:kit.SOURCE+kit.RESERVE])

    def test_wrong_parent_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact published'):
            f.apply_rom(self.parent[:-1]+bytes([self.parent[-1] ^ 1]))


if __name__ == '__main__':
    unittest.main()
