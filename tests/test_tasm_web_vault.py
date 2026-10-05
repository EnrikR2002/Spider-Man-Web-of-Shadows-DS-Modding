import json
import struct
import unittest
import mod
from tools import combat_profile as cp
from tools import tasm_rebound as tr
from tools import tasm_web_vault as tv
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob
from tools.qol_suits_menu import StringSlots
from tools.sca import Sca


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private clean ROM absent')
class LocalWebVaultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom, cls.glob, cls.manifest = mod.load_clean()
        cls.assets = {e['name']:cls.glob[e['offset']:e['offset']+e['size']]
                      for e in cls.manifest['entries'] if e['name'] in
                      (tv.ASSET,tv.POSE_ASSET,'American.strings')}

    def test_forward_root_preserves_every_contact_event_and_vertical_word(self):
        raw = self.assets[tv.ASSET]
        before = Gmb.parse(CompressedBlob.parse(raw).decoded)
        changed = tv.advance(raw)
        after = Gmb.parse(CompressedBlob.parse(changed).decoded)
        self.assertEqual(before.record_count,after.record_count)
        self.assertEqual(before.channels[1:],after.channels[1:])
        for frame,value in enumerate(tv.ADVANCE_Q12):
            old,new = before.channels[0].words(frame),after.channels[0].words(frame)
            self.assertEqual(old[:2]+old[3:],new[:2]+new[3:])
            self.assertEqual(new[2],value)
        with self.assertRaises(ValueError): tv.advance(changed)

    def test_pose_changes_only_three_independent_chest_rotations(self):
        raw = self.assets[tv.POSE_ASSET]; before = Sca.parse(raw)
        changed = tv.pose(raw); after = Sca.parse(changed)
        allowed = {byte for frame,_ in tv.POSE_KEYS
                   for byte in range(before.rotation_offset(3,frame),before.rotation_offset(3,frame)+18)}
        differences = {i for i,(a,b) in enumerate(zip(raw,changed)) if a!=b}
        self.assertTrue(differences); self.assertTrue(differences<=allowed)
        self.assertEqual(len(raw),len(changed))
        self.assertEqual(after.to_bytes(),changed)
        self.assertEqual(after.header,before.header)
        self.assertEqual(after.frames[:3],before.frames[:3])
        self.assertEqual(after.frames[6:],before.frames[6:])

    def test_text_composes_both_moves_and_keeps_every_other_slot(self):
        raw = self.assets['American.strings']; slots = StringSlots(raw)
        current = tr.text_overlay(raw,slots.replace({131:'Press \ue605 to switch suits.'}))
        changed = tv.text_overlay(raw,current)
        edits = tr.TEXT_EDITS | tv.TEXT_EDITS
        for i in range(1049):
            self.assertEqual(slots.decode(changed,i),edits.get(i,slots.decode(current,i)))
        self.assertIn('\xbf',slots.decode(changed,188))
        self.assertEqual(tv.text_overlay(raw,changed),changed)

    def test_arm9_is_exact_bounded_patch_with_native_response_preserved(self):
        changed,log = cp.apply_rom(self.rom,'tasm-web-vault')
        start,_,_,size = struct.unpack_from('<4I',self.rom,0x20)
        expected = bytearray(cp.apply_rom(self.rom,True)[0])
        struct.pack_into('<5I',expected,start+cp.VAULT_OFFSET,*cp.VAULT_WORDS)
        self.assertEqual(changed,bytes(expected)); self.assertEqual(len(log),3)
        self.assertEqual(cp.identify_arm9(changed[start:start+size]),cp.WEB_VAULT_ARM9_SHA256)
        # Decode the two ARM branches: native hop, then original response stores.
        for word,address,target in ((cp.VAULT_WORDS[1],0x020C926C,0x020BF164),
                                    (cp.VAULT_WORDS[4],0x020C9278,0x020C925C)):
            displacement = word & 0xFFFFFF
            if displacement & 0x800000: displacement -= 0x1000000
            self.assertEqual(address+8+displacement*4,target)
        self.assertEqual(changed[start+0xC9258:start+0xC9268],self.rom[start+0xC9258:start+0xC9268])
        self.assertEqual(changed[start+0xC92D0:start+0xC95E8],self.rom[start+0xC92D0:start+0xC95E8])
        with self.assertRaises(ValueError): cp.apply_rom(changed,'tasm-web-vault')
        with self.assertRaises(ValueError): cp.apply_rom(self.rom,'unknown')

    def test_all_purchase_costs_flags_dependencies_and_shared_routes_stay_exact(self):
        changed,_ = cp.apply_rom(self.rom,'tasm-web-vault')
        start = struct.unpack_from('<I',self.rom,0x20)[0]
        catalog = json.loads((mod.ROOT/'reference/original_gameplay.json').read_text())
        for group in ('red_purchases','black_purchases','shared_purchases'):
            for item in catalog[group]:
                at = start+item['record_address']-0x02000000
                self.assertEqual(changed[at:at+32],self.rom[at:at+32])
        # Entire native input selector, grapple purchase gate and physical helper.
        for lo,hi in ((0xB4888,0xB4AE8),(0xB5E4C,0xB669C),(0xBF164,0xBF24C)):
            self.assertEqual(changed[start+lo:start+hi],self.rom[start+lo:start+hi])


if __name__=='__main__': unittest.main()
