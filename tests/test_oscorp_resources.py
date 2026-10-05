import struct
import unittest
import mod
from tests.test_toolchain import make_glob
from tools import oscorp_resources as r,wos_tool as w,combat_profile as cp

class AppendTests(unittest.TestCase):
    def test_noop_and_append_preserve_ids_names_and_unknown_payloads(self):
        original=make_glob();offsets,names,index=w.parse_glob(original)
        blobs=[original[a:b] for a,b in zip(offsets,offsets[1:])]
        nn,bb=r.append_resources(names,blobs,{})
        self.assertEqual(w.pack_glob(nn,bb),original)
        extra={'zz_NewA.sca':b'new opaque A','zz_NewB.gab':b'new opaque B'}
        nn,bb=r.append_resources(names,blobs,extra);changed=w.pack_glob(nn,bb)
        oo,parsed,ii=w.parse_glob(changed);self.assertEqual(parsed,nn);self.assertEqual(ii,index)
        self.assertEqual(parsed[:len(names)],names)
        for i in range(len(names)):
            got=changed[oo[i]:oo[i+1]]
            if i==index:self.assertEqual(got[:len(blobs[i])],blobs[i])
            else:self.assertEqual(got,blobs[i])
        self.assertEqual(w.pack_glob(parsed,[changed[a:b] for a,b in zip(oo,oo[1:])]),changed)
        # Removing only our added records/resources restores the exact archive.
        bb[index]=bb[index][:len(blobs[index])]
        self.assertEqual(w.pack_glob(nn[:len(names)],bb[:len(names)]),original)
    def test_reject_collisions_invalid_names_and_bad_base_mapping(self):
        raw=make_glob();o,n,i=w.parse_glob(raw);b=[raw[a:z] for a,z in zip(o,o[1:])]
        for extra in ({'ASSET.BIN':b'x'},{'../bad.sca':b'x'},{'x'*64:b'x'},{'a.sca':b'x','A.sca':b'y'}):
            with self.assertRaises(ValueError):r.append_resources(n,b,extra)
        with self.assertRaises(ValueError):r.append_resources(n,b[:-1],{'new.sca':b'x'})

@unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original absent')
class LocalResourceTests(unittest.TestCase):
    def test_only_authored_profile_accepts_fixed_extra_names(self):
        rom,glob,manifest=mod.load_clean();entries={e['name']:e for e in manifest['entries']}
        overlay={}
        for name,source in zip(r.EXTRA_NAMES,('spd_GroundAttack15.sca','spd_GroundAttack16.sca','spd_GroundAttack17.sca')):
            e=entries[source];overlay[name]=glob[e['offset']:e['offset']+e['size']]
        with self.assertRaisesRegex(ValueError,'Invalid overlay'):mod.create_build(rom,glob,manifest,overlay)
        incomplete=dict(overlay);del incomplete[r.EXTRA_NAMES[0]]
        with self.assertRaisesRegex(ValueError,'requires'):mod.create_build(rom,glob,manifest,incomplete,gameplay_profile=r.PROFILE)
        overlay['GlobFiles.txt']=b'bad'
        with self.assertRaisesRegex(ValueError,'Invalid overlay'):mod.create_build(rom,glob,manifest,overlay,gameplay_profile=r.PROFILE)
    def test_native_resource_count_patch_exact_and_reversible(self):
        rom,glob,manifest=mod.load_clean();parent,_=cp.apply_rom(rom,'tasm-oscorp-rush')
        changed,_=r.apply_rom(parent);h=w.parse_header(changed);offset=h['arm9_offset']+r.COUNT_OFFSET
        self.assertEqual(w.u32(changed,offset),3736)
        restored=bytearray(changed);restored[offset:offset+4]=parent[offset:offset+4];self.assertEqual(restored,parent)
        self.assertEqual(cp.identify_arm9(changed[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]),r.ARM9_SHA256)
        with self.assertRaises(ValueError):r.apply_rom(changed)
        with self.assertRaises(ValueError):r.apply_rom(rom)

if __name__=='__main__':unittest.main()
