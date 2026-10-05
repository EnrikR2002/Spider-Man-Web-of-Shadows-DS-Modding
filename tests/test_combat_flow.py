import json
import struct
import unittest
from unittest.mock import patch
import mod
from tools import combat_flow as f, combat_profile as cp, tasm_sling_strike as s, combat_hud as h, wos_tool as w
from tools import combat_readability as q
from tools.qol_suits_menu import StringSlots

class AuthoredFlowTests(unittest.TestCase):
    def test_authored_code_and_reserved_state_bounds(self):
        code=f.code_bytes()
        self.assertEqual(w.sha256(code),f.CODE_SHA256)
        self.assertEqual(len(code),0x3600)
        self.assertEqual(code[0x2680:0x2800],h.code_bytes()[0x2680:0x2800])
        self.assertFalse(any(code[0x2800:]))
        self.assertLessEqual(h.STATE+0x700+9*8,h.TARGET+h.RESERVE)
        self.assertEqual(w.u32(code,0x1020),0xE3A02F6E)

@unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original absent')
class LocalCombatFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.glob,cls.manifest=mod.load_clean()
        cls.before,_=cp.apply_rom(cls.rom,'tasm-sling-strike')
        cls.after,_=cp.apply_rom(cls.rom,'tasm-combat-flow')
        cls.header=w.parse_header(cls.after)
        at=cls.header['arm9_offset'];size=cls.header['arm9_size']
        cls.old=cls.before[at:at+size];cls.new=cls.after[at:at+size]

    def test_guarded_complete_edit_revert(self):
        self.assertEqual(cp.identify_arm9(self.new),f.ARM9_SHA256)
        at=self.header['arm9_offset'];restored=bytearray(self.after)
        for offset,size in ((f.SOURCE_OFFSET,0x3600),(f.VAULT_OFFSET,20),(0xC9314,4),(0x73A68,4)):
            restored[at+offset:at+offset+size]=self.before[at+offset:at+offset+size]
        self.assertEqual(bytes(restored),self.before)
        self.assertEqual(self.after[at+f.SOURCE_OFFSET:at+f.SOURCE_OFFSET+0x3600],f.code_bytes())
        with self.assertRaises(ValueError):f.apply_rom(self.rom)
        with self.assertRaises(ValueError):f.apply_rom(self.after)

    def test_native_purchase_input_damage_and_sdk_records_preserved(self):
        catalog=json.loads((mod.ROOT/'docs/ORIGINAL_GAMEPLAY.json').read_text())
        for group in ('red_purchases','black_purchases','shared_purchases'):
            for item in catalog[group]:
                offset=item['record_address']-h.BASE
                self.assertEqual(self.old[offset:offset+32],self.new[offset:offset+32])
        for lo,hi in ((0xB8E40,0xB90AC),(0xB93D0,0xB94BC),(0xC76A0,0xC8180),
                       (0xBF164,0xBF24C),(0x95160,0x95200),(0xB64,0xB78)):
            self.assertEqual(self.old[lo:hi],self.new[lo:hi])
        table=w.u32(self.old,0xB64)-h.BASE
        self.assertEqual(self.old[table:table+36],self.new[table:table+36])
        self.assertEqual(self.old[0x728F0:0x728F4],self.new[0x728F0:0x728F4])
        self.assertEqual(self.old[0x73B5C:0x73B60],self.new[0x73B5C:0x73B60])

    def test_instruction_text_preserves_every_other_composed_slot(self):
        entries={e['name']:e for e in self.manifest['entries']}
        from tools.oscorp_resources import EXTRA_NAMES
        overlays=mod.overlay_files(mod.ROOT/'mods',list(entries),added_names=EXTRA_NAMES)
        # This historical composition starts from its own prerequisite recipe,
        # not the newer Rush strings now installed in the local default overlay.
        for name in ('English.strings','American.strings'):
            e=entries[name];clean=self.glob[e['offset']:e['offset']+e['size']]
            overlays[name]=q.text_overlay(clean,clean)
        before=dict(overlays)
        q.compose(self.glob,self.manifest,overlays,f.TEXT_EDITS)
        for name in ('English.strings','American.strings'):
            entry=entries[name]
            clean=self.glob[entry['offset']:entry['offset']+entry['size']]
            slots=StringSlots(clean)
            for index in range(len(slots.texts)):
                self.assertEqual(slots.decode(overlays[name],index),
                    f.TEXT_EDITS.get(index,slots.decode(before[name],index)))
            self.assertEqual(len(overlays[name]),len(before[name]))
        for name in set(overlays)-{'English.strings','American.strings'}:
            self.assertEqual(overlays[name],before[name])
        with patch.object(cp,'load_recipe',return_value='tasm-oscorp-rush'):
            with self.assertRaises(ValueError):f.generate(output='build/rejected-historical-flow')

if __name__=='__main__':unittest.main()
