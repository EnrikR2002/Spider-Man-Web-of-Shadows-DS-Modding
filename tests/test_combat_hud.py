import json
import struct
import unittest
import mod
from tools import combat_hud as h, combat_profile as cp, tasm_sling_strike as s
from tools import combat_readability as q, qol_minimap as qm, wos_tool as w
from tools.qol_suits_menu import StringSlots


class OwnCodeTests(unittest.TestCase):
    def test_code_hashes_and_scratch_bounds(self):
        self.assertEqual(w.sha256(h.code_bytes()), h.CODE_SHA256)
        self.assertEqual(w.sha256(s.code_bytes()), s.CODE_SHA256)
        self.assertEqual(len(h.code_bytes()), 0x3600)
        self.assertFalse(any(h.code_bytes()[0x2800:]))
        self.assertLess(0x1B00 + len(s.code_bytes()), 0x2680)
        self.assertLess(h.STATE + 0x684, h.TARGET + h.RESERVE)
        with self.assertRaises(ValueError): h.sample(b'invalid RAM')


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private original absent')
class LocalReadableCombatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom, cls.glob, cls.manifest = mod.load_clean()
        cls.vault, _ = cp.apply_rom(cls.rom, 'tasm-web-vault')
        cls.hud, _ = cp.apply_rom(cls.rom, 'tasm-readable-combat')
        cls.sling, _ = cp.apply_rom(cls.rom, 'tasm-sling-strike')
        def arm(rom):
            header = w.parse_header(rom)
            return rom[header['arm9_offset']:header['arm9_offset'] + header['arm9_size']]
        cls.old, cls.compact, cls.final = map(arm, (cls.vault, cls.hud, cls.sling))

    def test_hud_extension_edit_revert_is_exact(self):
        table, end, source, lo, hi = struct.unpack_from('<5I', self.compact, 0xB64)
        at = table - h.BASE
        self.assertEqual((source, lo, hi), (0x213E140, 0x213E140, h.TARGET))
        self.assertEqual(struct.unpack_from('<3I', self.compact, at+24), (h.TARGET, 0x3600, 0))
        self.assertEqual(end, table+36)
        self.assertEqual(self.compact[0x1439A0:at], h.code_bytes())
        restored = bytearray(self.compact[:0x1439A0] + self.compact[at:at+24])
        for off, size in ((0xB64,8), (0xFF374,4)):
            restored[off:off+size] = self.old[off:off+size]
        for off in h.IMPULSES: restored[off:off+8] = self.old[off:off+8]
        for off in h.HOOKS: restored[off:off+4] = self.old[off:off+4]
        self.assertEqual(bytes(restored), self.old)

    def test_sling_edit_revert_and_exact_profile(self):
        restored = bytearray(self.final)
        for off, (old, new, _) in s.PATCHES.items():
            self.assertEqual(w.u32(self.final, off), new)
            struct.pack_into('<I', restored, off, old)
        code = s.code_bytes()
        self.assertEqual(self.final[s.SOURCE_OFFSET:s.SOURCE_OFFSET+len(code)], code)
        restored[s.SOURCE_OFFSET:s.SOURCE_OFFSET+len(code)] = bytes(len(code))
        self.assertEqual(bytes(restored), self.compact)
        self.assertEqual(cp.identify_arm9(self.final), s.ARM9_SHA256)
        with self.assertRaises(ValueError): s.apply_rom(self.rom)
        with self.assertRaises(ValueError): s.apply_rom(self.sling)
        with self.assertRaises(ValueError): h.apply_rom(self.hud)

    def test_all_native_purchase_and_shared_input_records_preserved(self):
        catalog = json.loads((mod.ROOT/'docs/ORIGINAL_GAMEPLAY.json').read_text())
        for group in ('red_purchases', 'black_purchases', 'shared_purchases'):
            for item in catalog[group]:
                off = item['record_address'] - h.BASE
                self.assertEqual(self.old[off:off+32], self.final[off:off+32])
        for lo, hi in ((0xB8E40,0xB90AC), (0xB93D0,0xB94BC),
                       (0xC76A0,0xC8180), (0xBF164,0xBF24C),
                       (0x728F4,0x72900), (0x73A6C,0x73AC0)):
            self.assertEqual(self.old[lo:hi], self.final[lo:hi])

    def test_every_nitrofs_byte_preserved_by_executable_extensions(self):
        before = w.validate_rom(self.vault, target=True)['nitrofs']
        after = w.validate_rom(self.sling, target=True)['nitrofs']
        self.assertEqual(len(before),len(after))
        for a,b in zip(before,after):
            self.assertEqual(self.vault[a['start']:a['end']],self.sling[b['start']:b['end']])

    def test_upgrade_text_and_red_marker_preserve_other_assets_and_slots(self):
        entries = {e['name']:e for e in self.manifest['entries']}
        def clean(name):
            e=entries[name];return self.glob[e['offset']:e['offset']+e['size']]
        icon = qm.load_icons(self.glob,self.manifest)['MissionMiniMapIcon']
        overlays = {qm.ASSET:qm.yellow_mission(icon)}
        q.compose(self.glob,self.manifest,overlays,s.TEXT_EDITS)
        self.assertEqual(overlays[qm.ASSET],clean(qm.ASSET))
        self.assertEqual(w.u16(overlays[qm.ASSET],2),0x001F)
        for name in ('American.strings','English.strings'):
            slots=StringSlots(clean(name));changed=overlays[name]
            expected=q.TEXT_EDITS | s.TEXT_EDITS
            for i,old in enumerate(slots.texts):
                self.assertEqual(slots.decode(changed,i),expected.get(i,old))
            self.assertEqual(len(changed),len(clean(name)))


if __name__=='__main__': unittest.main()
