"""Real native data: growth preservation, price confinement and version guards."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
import mod
from tools import combat_profile as cp, oscorp_resources as extra, release_info as release, wos_tool as w
from tools.qol_suits_menu import StringSlots, COUNT, BASE


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom, cls.glob, cls.manifest = mod.load_clean()
        entry = next(e for e in cls.manifest['entries'] if e['name'] == 'English.strings')
        cls.clean_text = cls.glob[entry['offset']:entry['offset'] + entry['size']]
        cls.slots = StringSlots(cls.clean_text)

    def test_noop_and_grown_variant_roundtrip_preserve_every_unedited_slot(self):
        slots = self.slots
        self.assertEqual(slots.repack(self.clean_text, {}), self.clean_text)
        changed = slots.repack(self.clean_text, release.TEXT_EDITS)
        self.assertEqual(slots.repack(changed, {}), changed)
        self.assertEqual(slots.repack(changed, release.TEXT_EDITS), changed)
        offsets = slots.variant_offsets(changed)
        table = BASE + w.u32(self.clean_text, BASE)
        self.assertEqual(changed[:table], self.clean_text[:table])
        for i in range(COUNT):
            self.assertEqual(slots.decode(changed, i), release.TEXT_EDITS.get(i, slots.texts[i]))
            old = self.clean_text[slots.offsets[i]:slots.offsets[i + 1] if i + 1 < COUNT else len(self.clean_text)]
            new = changed[offsets[i]:offsets[i + 1] if i + 1 < COUNT else len(changed)]
            if i not in release.TEXT_EDITS:
                self.assertEqual(old, new)
            elif len(slots.encode(release.TEXT_EDITS[i])) > len(old):
                self.assertTrue(new.endswith(old))

    def test_corrupt_prefix_offsets_and_out_of_range_edits_rejected(self):
        for at in (0, BASE + w.u32(self.clean_text, BASE)):
            changed = bytearray(self.clean_text)
            changed[at] ^= 255
            with self.assertRaises(ValueError):
                self.slots.repack(bytes(changed), {})
        with self.assertRaises(ValueError):
            self.slots.repack(self.clean_text, {COUNT: 'invalid'})

    def test_later_text_composition_preserves_boot_and_options_version(self):
        from tools import combat_readability as text
        versioned = self.slots.repack(self.clean_text, release.TEXT_EDITS)
        composed = text.text_overlay(self.clean_text, versioned, {194: 'New paid move instructions.'})
        for index, value in release.TEXT_EDITS.items():
            self.assertEqual(self.slots.decode(composed, index), value)
        self.assertEqual(self.slots.decode(composed, 194), 'New paid move instructions.')
        self.assertEqual(self.slots.repack(composed, {}), composed)

    def test_only_red_and_shared_price_words_change_and_inverse_is_exact(self):
        parent, _ = cp.apply_rom(self.rom, extra.PROFILE)
        changed, edits = release.apply_rom(parent)
        h = w.parse_header(parent)
        start = h['arm9_offset']
        allowed = {start + table + row * 32 + 28 + byte
                   for table in (release.PRICE_TABLE, release.SHARED_PRICE_TABLE)
                   for row in range(7) for byte in range(4)}
        self.assertTrue({i for i, (a, b) in enumerate(zip(parent, changed)) if a != b} <= allowed)
        self.assertEqual(len(edits), 14)
        restored = bytearray(changed)
        for table, prices in ((release.PRICE_TABLE, release.OLD_PRICES),
                              (release.SHARED_PRICE_TABLE, release.OLD_SHARED_PRICES)):
            for row, price in enumerate(prices):
                struct.pack_into('<I', restored, start + table + row * 32 + 28, price)
        self.assertEqual(restored, parent)
        with self.assertRaises(ValueError):
            release.apply_rom(changed)

    def test_shared_discount_preserves_red_prices_every_other_byte_and_inverse(self):
        old, _ = cp.apply_rom(self.rom, release.PARENT_PROFILE)
        changed, _ = cp.apply_rom(self.rom, release.PROFILE)
        h = w.parse_header(old)
        start = h['arm9_offset']
        allowed = {start + release.SHARED_PRICE_TABLE + row * 32 + 28 + byte
                   for row in range(7) for byte in range(4)}
        self.assertTrue({i for i, (a, b) in enumerate(zip(old, changed)) if a != b} <= allowed)
        restored = bytearray(changed)
        for row, price in enumerate(release.OLD_SHARED_PRICES):
            struct.pack_into('<I', restored, start + release.SHARED_PRICE_TABLE + row * 32 + 28, price)
        self.assertEqual(restored, old)
        catalog = json.loads((mod.ROOT / 'reference/original_gameplay.json').read_text(encoding='utf-8'))
        for row, record in enumerate(catalog['shared_purchases']):
            at = start + record['record_address'] - 0x02000000
            self.assertEqual(record['name'], release.SHARED_NAMES[row])
            self.assertEqual(record['ability_bit'], release.SHARED_BITS[row])
            self.assertEqual(struct.unpack_from('<I', changed, at + 28)[0], release.SHARED_PRICES[row])
            self.assertEqual(changed[at:at + 28], old[at:at + 28])

    def test_previous_numbered_release_still_rebuilds_exactly(self):
        folder = mod.ROOT / 'build/releases' / release.PARENT_ROM_SHA / 'composition'
        if not folder.exists():
            self.skipTest('Private v0.1.0 composition unavailable')
        names = [e['name'] for e in self.manifest['entries']]
        overlays = mod.overlay_files(folder / 'mods', names, added_names=extra.EXTRA_NAMES)
        profile = cp.load_recipe(folder / 'gameplay_profile.json', overlays)
        self.assertEqual(profile, release.PARENT_PROFILE)
        built, _, log = mod.create_build(self.rom, self.glob, self.manifest, overlays, gameplay_profile=profile)
        self.assertEqual(w.sha256(built), release.PARENT_ROM_SHA)
        self.assertEqual(log['release_version'], release.PROFILE_INFO[release.PARENT_PROFILE]['version'])

    def test_recipe_version_and_overlay_hashes_must_match(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'recipe.json'
            recipe = {'schema_version': 1, 'profile': release.PROFILE,
                      'release_version': release.VERSION, 'required_overlays': {'test': w.sha256(b'known')}}
            path.write_text(json.dumps(recipe), encoding='utf-8')
            self.assertEqual(cp.load_recipe(path, {'test': b'known'}), release.PROFILE)
            recipe['release_version'] = '9.9.9'
            path.write_text(json.dumps(recipe), encoding='utf-8')
            with self.assertRaises(ValueError):
                cp.load_recipe(path, {'test': b'known'})

    def test_published_version_reuse_is_idempotent_and_different_rom_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            history = Path(folder) / 'history.json'
            release.register_release('0.1.0', 'first', date='2026-10-05', previous='old', history=history)
            before = history.read_bytes()
            release.register_release('0.1.0', 'first', date='2026-10-05', previous='old', history=history)
            self.assertEqual(history.read_bytes(), before)
            with self.assertRaisesRegex(ValueError, 'different published ROM'):
                release.check_version_reuse('0.1.0', 'changed', history)
            for invalid in ('v0.1.0', '0.1', '00.1.0', '0.1.-1'):
                with self.assertRaises(ValueError):
                    release.check_version_reuse(invalid, 'first', history)


if __name__ == '__main__':
    unittest.main()
