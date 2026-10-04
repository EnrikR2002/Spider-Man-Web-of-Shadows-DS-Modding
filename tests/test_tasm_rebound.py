import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import mod
from tools import combat_profile as cp
from tools import tasm_rebound as tr
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob
from tools.qol_suits_menu import StringSlots
from tools.sca import Sca


class RecipeTests(unittest.TestCase):
    def test_recipe_rejects_missing_changed_or_unknown_profile(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'recipe.json'
            data = {'schema_version': 1, 'profile': 'tasm-rebound',
                    'required_overlays': {'move.gmb': hashlib.sha256(b'move').hexdigest()}}
            path.write_text(json.dumps(data))
            self.assertTrue(cp.load_recipe(path, {'move.gmb': b'move'}))
            for overlay in ({}, {'move.gmb': b'other'}):
                with self.assertRaises(ValueError): cp.load_recipe(path, overlay)
            for data in ({'profile': 'other', 'schema_version': 1},
                         {'profile': 'tasm-rebound', 'schema_version': 1},
                         {'profile': 'original', 'schema_version': 2}):
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError): cp.load_recipe(path, {})
        self.assertEqual(cp.apply_rom(b'unidentified synthetic data'), (b'unidentified synthetic data', []))
        with self.assertRaises(ValueError): cp.apply_rom(b'unidentified synthetic data', True)


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private clean ROM absent')
class LocalReboundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom, cls.glob, cls.manifest = mod.load_clean()
        cls.assets = {e['name']: cls.glob[e['offset']:e['offset']+e['size']]
                      for e in cls.manifest['entries'] if e['name'] in
                      (tr.ASSET, tr.POSE_ASSET, 'American.strings')}

    def test_recoil_preserves_contact_geometry_events_and_duration(self):
        raw = self.assets[tr.ASSET]
        original = Gmb.parse(CompressedBlob.parse(raw).decoded)
        modified = Gmb.parse(CompressedBlob.parse(tr.recoil(raw)).decoded)
        self.assertEqual(modified.record_count, original.record_count)
        self.assertEqual(modified.channels[1:], original.channels[1:])
        for frame, value in enumerate(tr.RECOIL_Q12):
            before, after = original.channels[0].words(frame), modified.channels[0].words(frame)
            self.assertEqual(after[:2]+after[3:], before[:2]+before[3:])
            self.assertEqual(after[2], value)
        self.assertEqual(modified.to_bytes(), modified.raw)
        with self.assertRaises(ValueError): tr.recoil(tr.recoil(raw))

    def test_authored_pose_is_limited_to_post_contact_chest_matrices(self):
        raw = self.assets[tr.POSE_ASSET]; before = Sca.parse(raw)
        changed = tr.pose(raw); after = Sca.parse(changed)
        allowed = {byte for frame, _ in tr.POSE_KEYS
                   for byte in range(before.rotation_offset(3, frame), before.rotation_offset(3, frame)+18)}
        differences = {i for i, (a,b) in enumerate(zip(raw,changed)) if a != b}
        self.assertTrue(differences); self.assertTrue(differences <= allowed)
        self.assertEqual(len(raw), len(changed))
        self.assertEqual(after.to_bytes(), changed)
        self.assertEqual(after.header, before.header)
        self.assertEqual(after.frames[:5], before.frames[:5])

    def test_names_change_only_the_three_paid_text_slots(self):
        raw = self.assets['American.strings']; slots = StringSlots(raw)
        # Retain an unrelated existing QoL edit when composing the upgrade.
        current = slots.replace({131: 'Press \ue605 to switch suits.'})
        changed = tr.text_overlay(raw, current)
        for i in range(1049):
            expected = tr.TEXT_EDITS.get(i, slots.decode(current, i))
            self.assertEqual(slots.decode(changed, i), expected)
        self.assertEqual(tr.text_overlay(raw, current), changed)

    def test_response_edit_changes_two_impulses_and_no_other_rom_bytes(self):
        changed, log = cp.apply_rom(self.rom, True)
        start, _, _, size = struct.unpack_from('<4I', self.rom, 0x20)
        expected = bytearray(self.rom)
        for offset in cp.IMPULSE_OFFSETS:
            struct.pack_into('<i', expected, start+offset, cp.REBOUND_IMPULSE)
        self.assertEqual(changed, bytes(expected)); self.assertEqual(len(log), 2)
        self.assertEqual(cp.identify_arm9(changed[start:start+size]), cp.REBOUND_ARM9_SHA256)
        restored = bytearray(changed)
        for offset in cp.IMPULSE_OFFSETS:
            struct.pack_into('<i', restored, start+offset, cp.NATIVE_IMPULSE)
        self.assertEqual(bytes(restored), self.rom)
        corrupt = bytearray(changed); corrupt[start+0x90000] ^= 1
        with self.assertRaises(ValueError): cp.identify_arm9(corrupt[start:start+size])
        with self.assertRaises(ValueError): cp.apply_rom(changed, True)

    def test_original_catalog_matches_all_21_native_purchase_records(self):
        catalog = json.loads((mod.ROOT/'docs/ORIGINAL_GAMEPLAY.json').read_text())
        start = struct.unpack_from('<I', self.rom, 0x20)[0]
        for group in ('red_purchases', 'black_purchases', 'shared_purchases'):
            self.assertEqual(len(catalog[group]), 7)
            for item in catalog[group]:
                at = start + item['record_address'] - 0x02000000
                row = struct.unpack_from('<8I', self.rom, at)
                self.assertEqual(row[0], item['event_id'])
                self.assertEqual(row[3:6], tuple(item['slots']))
                self.assertEqual(row[7], item['cost'])
                self.assertEqual(item['ability_bit'], row[0]-309)
                self.assertEqual(item['required_event'], None if row[1]==382 else row[1])
                self.assertEqual(item['dependent_event'], None if row[2]==382 else row[2])


if __name__ == '__main__': unittest.main()
