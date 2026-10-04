import struct
import unittest
import mod
from tools import movie_suit as m
from tools.nitro_texture import TextureArchive


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private clean ROM not present')
class MovieSuitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,glob,manifest=mod.load_clean()
        cls.assets={e['name']:glob[e['offset']:e['offset']+e['size']] for e in manifest['entries']
                    if e['name'] in ('spd.nsbtx','spd.nsbmd')}

    def test_texture_noop_and_resize(self):
        raw=self.assets['spd.nsbtx']; pixels=raw[164:4260]; palette=raw[4260:]
        self.assertEqual(m.resize_i8(raw,pixels,palette,64),raw)
        up=bytes(pixels[(y//2)*64+x//2] for y in range(128) for x in range(128))
        result=m.resize_i8(raw,up,palette)
        parsed=TextureArchive.parse(result)
        self.assertEqual((parsed.textures[0]['width'],parsed.textures[0]['height']),(128,128))
        self.assertEqual(parsed.to_bytes(),result)
        self.assertEqual(result[-512:],palette)
        self.assertEqual(result[164:-512],up)
        self.assertEqual(result[0x68:164],raw[0x68:164])
        with self.assertRaises(ValueError): m.resize_i8(raw,up[:-1],palette)
        with self.assertRaises(ValueError): m.resize_i8(raw[:-1],up,palette)

    def test_model_noop_and_exact_uv_inverse(self):
        raw=self.assets['spd.nsbmd']
        self.assertEqual(m.scale_model(raw,1),raw)
        material,offsets=m.uv_offsets(raw)
        self.assertEqual(len(offsets),741)
        result=m.scale_model(raw)
        inverse=bytearray(result)
        allowed=set(range(material+32,material+36))
        for off in offsets:
            allowed.update(range(off,off+4))
            old=struct.unpack_from('<hh',raw,off)
            new=struct.unpack_from('<hh',result,off)
            self.assertEqual(new,tuple(v*2 for v in old))
            struct.pack_into('<hh',inverse,off,*(v//2 for v in new))
        struct.pack_into('<HH',inverse,material+32,64,64)
        self.assertEqual(bytes(inverse),raw)
        self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(raw,result)) if a!=b))
        with self.assertRaises(ValueError): m.scale_model(result)


if __name__=='__main__': unittest.main()