"""Connected rake motion, unchanged native contact/runtime and purchase-safe prices."""
import unittest
from tools import sky_rake_polish as s, wos_tool as w, tasm_kit as kit


class Motion(unittest.TestCase):
    def test_phrase_has_matching_seams_and_a_full_heel_flip(self):
        for a, b in zip(s.art.CLIPS, s.art.CLIPS[1:]):
            for channel in a.keys:
                self.assertEqual(a.value(channel, a.samples-1), b.value(channel, 0))
        phrase = s.art.PHRASE
        self.assertLess(phrase.value('pitch', 40)-phrase.value('pitch', 23), -350)
        self.assertLess(phrase.value('foot_r', 28)[1], -4.)
        for contact in (3, 8, 13, 20):
            leg_lengths = [-phrase.value('foot_'+side, contact)[1] for side in ('l', 'r')]
            self.assertGreater(max(leg_lengths), 3.8)
        self.assertEqual((len(s.PRICES), sum(s.PRICES), sum(s.PLANNED_PRICES)), (9, 1300, 2450))
        self.assertTrue(all(a < b for a, b in zip(s.parent.PRICES, s.PRICES)))


@unittest.skipUnless(s.PARENT_PATH.exists(), 'private published parent missing')
class Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = s.PARENT_PATH.read_bytes()
        cls.after, cls.report = s.apply_rom(cls.before)

    def test_only_private_motion_version_and_black_price_words_change(self):
        an, ab = s.assets.resources(self.before)
        bn, bb = s.assets.resources(self.after)
        self.assertEqual(an, bn)
        changed = [n for n, a, b in zip(an, ab, bb) if a != b]
        self.assertEqual(set(changed), {'American.strings', 'English.strings',
                         *(f'zz_S35_Air{i}.sca' for i in range(1, 5))})
        self.assertEqual(changed, self.report['modified_resources'])
        from tools.sca import Sca
        from tools.sca_author import sample
        for i, clip in enumerate(s.art.CLIPS, 1):
            original = Sca.parse(ab[an.index(f'zz_S35_Air{i}.sca')])
            current = Sca.parse(bb[bn.index(f'zz_S35_Air{i}.sca')])
            self.assertEqual((current.frame_count, current.joint_count), (clip.samples, 37))
            self.assertEqual(current.to_bytes(), bb[bn.index(f'zz_S35_Air{i}.sca')])
            for j in range(37):
                for f in range(clip.samples):
                    self.assertEqual(sample(original, j, f, 'scale'), sample(current, j, f, 'scale'))
        def arm(rom):
            h = w.parse_header(rom)
            return rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        a, b = arm(self.before), arm(self.after)
        off = self.report['shop_source_offset']
        allowed = {off+i*32+28+j for i in range(9) for j in range(4)}
        self.assertTrue(all(i in allowed for i, (x, y) in enumerate(zip(a, b)) if x != y))
        self.assertEqual(a[kit.SOURCE:kit.SOURCE+kit.RESERVE], b[kit.SOURCE:kit.SOURCE+kit.RESERVE])
        for i, price in enumerate(s.PRICES):
            self.assertEqual(a[off+i*32:off+i*32+28], b[off+i*32:off+i*32+28])
            self.assertEqual(w.u32(b, off+i*32+28), price)
        for e in w.nitrofs_entries(self.before):
            if e['name'] == 'Glob.bin':
                continue
            n = next(x for x in w.nitrofs_entries(self.after) if x['name'] == e['name'])
            self.assertEqual(self.before[e['start']:e['end']], self.after[n['start']:n['end']])
        from tools.qol_suits_menu import decode_grown
        for name in ('American.strings', 'English.strings'):
            self.assertIn(s.VERSION, decode_grown(bb[bn.index(name)], 50))
            self.assertIn(s.VERSION, decode_grown(bb[bn.index(name)], 74))

    def test_wrong_parent_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact published'):
            s.apply_rom(bytes(512))


if __name__ == '__main__':
    unittest.main()
