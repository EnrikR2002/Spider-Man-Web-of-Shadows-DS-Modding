import struct,unittest
from tools import creature_texture_fix as f,wos_tool as w
from tools.animation_rig import AnimationRig
from tools.model_geometry import ModelGeometry

class TextureMaterialTests(unittest.TestCase):
    def test_only_original_texture_dimensions_change(self):
        import mod
        _,g,_=mod.load_clean();o,n,_=w.parse_glob(g)
        for stem in ('hLpr','brt','hRng'):
            i=n.index(stem+'.nsbmd');raw=g[o[i]:o[i+1]];fixed,changes=f.fix_model(raw)
            self.assertEqual(len(fixed),len(raw));self.assertEqual(len(changes),1)
            at=changes[0]['offset'];expected=bytearray(raw);struct.pack_into('<2H',expected,at,128,128)
            self.assertEqual(fixed,bytes(expected));self.assertEqual(AnimationRig.parse(fixed).parents,AnimationRig.parse(raw).parents)
            self.assertEqual([fixed[s.start:s.start+s.length] for s in ModelGeometry.parse(fixed).shapes],
                             [raw[s.start:s.start+s.length] for s in ModelGeometry.parse(raw).shapes])

    def test_requires_frozen_parent_material_dimensions(self):
        import mod
        _,g,_=mod.load_clean();o,n,_=w.parse_glob(g);i=n.index('brt.nsbmd');fixed,_=f.fix_model(g[o[i]:o[i+1]])
        with self.assertRaises(ValueError):f.fix_model(fixed)

if __name__=='__main__':unittest.main()
