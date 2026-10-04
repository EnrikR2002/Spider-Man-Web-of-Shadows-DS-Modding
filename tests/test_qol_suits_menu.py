import unittest
import mod
from tools import qol_suits_menu as q
from tools import nitro_texture as nt


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private clean ROM not present')
class SuitMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, glob, manifest = mod.load_clean()
        cls.assets = {e['name']: glob[e['offset']:e['offset'] + e['size']]
                      for e in manifest['entries'] if e['name'] in
                      ('American.strings', 'English.strings', 'spd.nsbtx', 'spdB.nsbtx')}
        cls.slots = q.StringSlots(cls.assets['American.strings'])

    def test_all_text_roundtrips_and_noop_identity(self):
        s = self.slots
        self.assertEqual(len(s.texts), 1049)
        self.assertEqual(s.texts[164], 'Launch enemies into the air by pressing up on ¿ and \ue601 together.')
        self.assertEqual(s.replace(dict(enumerate(s.texts))), s.raw)
        for i, text in enumerate(s.texts):
            data = s.encode(text)
            start = s.offsets[i]
            end = s.offsets[i + 1] if i + 1 < q.COUNT else len(s.raw)
            self.assertLessEqual(len(data), end - start)
            candidate = s.raw[:start] + data + s.raw[start + len(data):]
            self.assertEqual(s.decode(candidate, i), text)
        self.assertEqual(self.assets['American.strings'], self.assets['English.strings'])

    def test_text_edit_confinement(self):
        s = self.slots
        result = s.replace({161: 'Raises maximum health.'})
        start, end = s.offsets[161:163]
        self.assertEqual(result[:start], s.raw[:start])
        self.assertEqual(result[end:], s.raw[end:])
        self.assertEqual(len(result), len(s.raw))
        for i, text in enumerate(s.texts):
            self.assertEqual(s.decode(result, i), 'Raises maximum health.' if i == 161 else text)

    def test_refuse_bad_text_and_profile(self):
        with self.assertRaises(ValueError): self.slots.replace({161: 'health ' * 100})
        with self.assertRaises(ValueError): self.slots.encode('+')
        with self.assertRaises(ValueError): self.slots.replace({-1: 'test'})
        with self.assertRaises(ValueError): q.StringSlots(self.slots.raw[:-1])

    def test_palette_only_and_determinism(self):
        for name in ('spd.nsbtx', 'spdB.nsbtx'):
            original = self.assets[name]
            a = nt.TextureArchive.parse(original)
            changed = q.suit_palette(original, name == 'spdB.nsbtx')
            self.assertNotEqual(original, changed)
            self.assertEqual(changed[:a.palette_start], original[:a.palette_start])
            self.assertEqual(changed[a.palette_start + a.palette_size:], original[a.palette_start + a.palette_size:])
            self.assertEqual(len(original), len(changed))
            self.assertEqual(q.suit_palette(original, name == 'spdB.nsbtx'), changed)
            nt.TextureArchive.parse(changed)


if __name__ == '__main__':
    unittest.main()