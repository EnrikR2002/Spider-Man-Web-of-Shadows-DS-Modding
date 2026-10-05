import unittest
import random
import mod
from tools.grip_compression import encode_backrefs,encode_literals,decode,CompressedBlob

class CompactCompressionTests(unittest.TestCase):
    def test_copy_overlap_distance_boundaries_and_determinism(self):
        rng=random.Random(325)
        cases=[b'',b'\0',b'abc',bytes(70000),b'ab'*1024,bytes(range(256))*4]
        for size in (255,256,257,512,2048):cases.append(rng.randbytes(size))
        distant=rng.randbytes(70000);cases.append(distant+distant[:256])
        for raw in cases:
            compressed=encode_backrefs(raw)
            self.assertEqual(decode(compressed),raw)
            self.assertEqual(encode_backrefs(raw),compressed)
            self.assertLessEqual(len(compressed),len(encode_literals(raw)))
        self.assertLess(len(encode_backrefs(bytes(70000))),70000//50)

    @unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original absent')
    def test_every_original_gmb_reencodes_and_preserves_noop_wrapper(self):
        _,glob,manifest=mod.load_clean();count=0
        for e in manifest['entries']:
            if not e['name'].endswith('.gmb'):continue
            raw=glob[e['offset']:e['offset']+e['size']];blob=CompressedBlob.parse(raw)
            self.assertEqual(blob.replace_decoded(blob.decoded,compact=True),raw)
            compact=encode_backrefs(blob.decoded)
            self.assertEqual(decode(compact),blob.decoded)
            count+=1
        self.assertEqual(count,769)

if __name__=='__main__':unittest.main()
