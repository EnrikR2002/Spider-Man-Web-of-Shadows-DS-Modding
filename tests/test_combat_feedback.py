import hashlib
import json
import struct
import unittest
import mod
from tools import combat_feedback as f, combat_profile as cp, wos_tool as w


class FeedbackBoundsTests(unittest.TestCase):
    def test_own_code_integrity_and_branch_bounds(self):
        code=f.code_bytes()
        self.assertEqual(len(code),0x3400)
        self.assertEqual(hashlib.sha256(code).hexdigest(),f.CODE_SHA256)
        self.assertTrue(all(x==0 for x in code[0x2800:]))
        self.assertEqual(f.branch(0x2000000,0x2000008),0xEA000000)
        for target in (0x2000009,0x4000008):
            with self.assertRaises(ValueError): f.branch(0x2000000,target)
        with self.assertRaises(ValueError): f.sample(b'not RAM')


@unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private clean ROM absent')
class LocalFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,_,_=mod.load_clean()
        cls.vault,_=cp.apply_rom(cls.rom,'tasm-web-vault')
        cls.changed,cls.log=f.apply_rom(cls.vault)
        cls.before=w.parse_header(cls.vault);cls.after=w.parse_header(cls.changed)
        at=cls.before['arm9_offset']
        cls.old=cls.vault[at:at+cls.before['arm9_size']]
        cls.new=cls.changed[at:at+cls.after['arm9_size']]

    def test_relocation_preserves_arm7_banner_fnt_and_every_nitrofs_file(self):
        a,b=self.before,self.after;delta=b['arm7_offset']-a['arm7_offset']
        self.assertGreater(delta,0)
        self.assertEqual(len(self.changed),len(self.vault))
        self.assertEqual(self.changed[0x34:0x40],self.vault[0x34:0x40])
        for key,size in (('arm7_offset',a['arm7_size']),('fnt_offset',a['fnt_size']),
                         ('banner_offset',0x840)):
            self.assertEqual(self.changed[b[key]:b[key]+size],self.vault[a[key]:a[key]+size])
        old_files=w.validate_rom(self.vault,target=True)['nitrofs']
        new_files=w.validate_rom(self.changed,target=True)['nitrofs']
        for old,new in zip(old_files,new_files):
            self.assertEqual(new['start'],old['start']+delta)
            self.assertEqual(new['end'],old['end']+delta)
            self.assertEqual(self.vault[old['start']:old['end']],self.changed[new['start']:new['end']])
        self.assertEqual(self.changed[0x4000:0x4800],self.vault[0x4000:0x4800])
        self.assertEqual(b['used_rom_size'],a['used_rom_size']+delta)

    def test_autoload_roundtrip_and_reserved_heap_do_not_overlap_bss_or_source(self):
        table,end,source,bss_start,bss_end=struct.unpack_from('<5I',self.new,0xB64)
        self.assertEqual((source,bss_start,bss_end),(0x213E140,0x213E140,f.TARGET))
        at=table-f.BASE
        self.assertEqual(self.new[at:at+24],self.old[0x1439A0:0x1439B8])
        self.assertEqual(struct.unpack_from('<3I',self.new,at+24),(f.TARGET,0x3400,0))
        self.assertEqual(end,table+36)
        self.assertLessEqual(end,f.TARGET)
        self.assertEqual(struct.unpack_from('<I',self.new,0xFF374)[0],f.TARGET+f.RESERVE)
        self.assertEqual(self.new[0x1439A0:at],f.code_bytes())
        # Remove added code/table record and reverse only declared original edits.
        restored=bytearray(self.new[:0x1439A0]+self.new[at:at+24])
        restored[0xB64:0xB6C]=self.old[0xB64:0xB6C]
        restored[0xFF374:0xFF378]=self.old[0xFF374:0xFF378]
        for offset in f.IMPULSES: restored[offset:offset+8]=self.old[offset:offset+8]
        for offset in f.HOOKS: restored[offset:offset+4]=self.old[offset:offset+4]
        self.assertEqual(bytes(restored),self.old)
        self.assertEqual(cp.identify_arm9(self.new),f.ARM9_SHA256)

    def test_purchase_records_and_native_gameplay_abis_are_unchanged(self):
        catalog=json.loads((mod.ROOT/'docs/ORIGINAL_GAMEPLAY.json').read_text(encoding='utf-8'))
        for group in ('red_purchases','black_purchases','shared_purchases'):
            for item in catalog[group]:
                at=item['record_address']-f.BASE
                self.assertEqual(self.old[at:at+32],self.new[at:at+32])
        for lo,hi in ((0xB4888,0xB4AE8),(0xB5E4C,0xB669C),(0xBF164,0xBF24C),
                      (0x5F3F4,0x5F430),(0x492AC,0x49304),(0x83BF0,0x83CC0)):
            self.assertEqual(self.old[lo:hi],self.new[lo:hi])
        for at in f.IMPULSES:
            self.assertEqual(struct.unpack_from('<2i',self.new,at),(-2253,11469))
        for at,(offset,_) in f.HOOKS.items():
            self.assertEqual(struct.unpack_from('<I',self.new,at)[0],f.branch(f.BASE+at,f.TARGET+offset))

    def test_unknown_or_repeated_profile_and_unsafe_loader_are_rejected(self):
        with self.assertRaises(ValueError): f.apply_rom(self.rom)
        with self.assertRaises(ValueError): f.apply_rom(self.changed)
        raw=bytearray(self.old);raw[0xB64]^=1
        with self.assertRaises(ValueError): f.extend_arm9(self.vault,bytes(raw),f.code_bytes())
        with self.assertRaises(ValueError): f.extend_arm9(self.vault,self.old,bytes(f.RESERVE+4))
        bad=bytearray(self.vault);bad[-1]=7
        with self.assertRaises(ValueError): f.extend_arm9(bytes(bad),self.old,f.code_bytes())
        result,_=cp.apply_rom(self.rom,'tasm-combat-feedback')
        self.assertEqual(result,self.changed)


if __name__=='__main__': unittest.main()
