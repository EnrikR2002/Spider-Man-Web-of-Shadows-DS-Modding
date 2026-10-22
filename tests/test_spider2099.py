"""Native skin/rig preservation, atlas isolation and exact 2099 ROM scope."""
from pathlib import Path
import struct
import unittest

from tools import spider2099 as suit, spider2099_art as art, wos_tool as w
from tools.animation_rig import AnimationRig
from tools.model_geometry import ModelGeometry
from tools.nitro_texture import TextureArchive, dictionary

ROOT=Path(__file__).resolve().parents[1]


class NativePlayerArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import mod
        _,glob,manifest=mod.load_clean()
        cls.assets={e['name']:glob[e['offset']:e['offset']+e['size']]
                    for e in manifest['entries'] if e['name'] in ('spdB.nsbmd','spdB.nsbtx')}
        cls.raw=cls.assets['spdB.nsbmd']
        cls.model,cls.report=art.model(cls.raw)
        cls.indices,cls.palette,cls.points=art.artwork(cls.raw)
        cls.texture=art.texture(cls.assets['spdB.nsbtx'],cls.indices,cls.palette)

    def test_native_strip_decoder_matches_independent_dcc_bounds(self):
        faces=art.mesh(self.raw)
        self.assertEqual(len(faces),480)
        expected=((-4.8636584,4.847648),(.017010015,10.039697),(-1.0801071,.8970285))
        for axis,(lo,hi) in enumerate(expected):
            self.assertAlmostEqual(min(v.position[axis] for f in faces for v in f),lo,places=5)
            self.assertAlmostEqual(max(v.position[axis] for f in faces for v in f),hi,places=5)

    def test_original_skin_opaque_bytes_rig_sbc_and_material_tint_are_exact(self):
        g=ModelGeometry.parse(self.raw)
        b=bytearray(self.model[:len(self.raw)])
        ranges=[(8,4),(g.block+4,4),(g.model,4),(g.model+36,8),(g.shapes[0].header+8,8)]
        mats=g.model+w.u32(self.raw,g.model+8)
        mat=mats+w.u32(dictionary(self.raw,mats+4,4)[0][1],0)
        ranges.append((mat+32,4))
        for at,size in ranges:b[at:at+size]=self.raw[at:at+size]
        self.assertEqual(bytes(b),self.raw)
        a,c=AnimationRig.parse(self.raw),AnimationRig.parse(self.model)
        self.assertEqual((a.names,a.parents,a.node_records,a.object_offsets),
                         (c.names,c.parents,c.node_records,c.object_offsets))
        self.assertEqual(len(art.mesh(self.model)),480+self.report['added_triangles'])

    def test_original_gpu_commands_only_double_uvs_and_added_vertices_use_valid_matrices(self):
        original=list(art.gpu_commands(self.raw));new=list(art.gpu_commands(self.model))
        g=ModelGeometry.parse(self.raw)
        self.assertEqual(art.packets(original),self.raw[g.shapes[0].start:g.shapes[0].start+g.shapes[0].length])
        for (op,args),(new_op,new_args) in zip(original,new):
            self.assertEqual(op,new_op)
            if op==0x22:
                uv=struct.unpack('<2h',struct.pack('<I',args[0]))
                self.assertEqual(struct.unpack('<2h',struct.pack('<I',new_args[0])),tuple(v*2 for v in uv))
            else:self.assertEqual(args,new_args)
        for op,args in new[len(original):]:
            if op==0x14:self.assertIn(args[0],art.bind_matrices(self.raw)[3])

    def test_reserved_swatches_do_not_paint_native_islands(self):
        self.assertTrue(all(self.points[y*128+x] is None for y in range(124,128) for x in range(16)))
        self.assertEqual(len(self.indices),16384)
        self.assertEqual(len(self.palette),512)
        atlas=TextureArchive.parse(self.texture)
        self.assertEqual((atlas.textures[0]['width'],atlas.textures[0]['height'],atlas.textures[0]['format']),(128,128,4))
        self.assertEqual(TextureArchive.parse(atlas.to_bytes()).to_bytes(),self.texture)
        # Opaque high dictionary bits and palette flags survive resizing.
        before=TextureArchive.parse(self.assets['spdB.nsbtx'])
        self.assertEqual(atlas.textures[0]['unknown_u32'],before.textures[0]['unknown_u32'])
        self.assertEqual(atlas.palettes[0]['unknown_u16'],before.palettes[0]['unknown_u16'])
        prefix=bytearray(self.texture[:164]);source=self.assets['spdB.nsbtx']
        for at,size in ((8,4),(24,4),(32,2),(20+0x24,4),(20+0x28,4),(20+0x38,4),(0x64,4)):
            prefix[at:at+size]=source[at:at+size]
        self.assertEqual(bytes(prefix),source[:164])

    def test_changed_native_parent_is_rejected(self):
        changed=bytearray(self.raw);changed[100]^=1
        with self.assertRaisesRegex(ValueError,'exact native Black model'):art.model(changed)
        changed=bytearray(self.assets['spdB.nsbtx']);changed[-1]^=1
        with self.assertRaisesRegex(ValueError,'exact native Black atlas'):
            art.texture(changed,self.indices,self.palette)


class AppearanceComposition(unittest.TestCase):
    def test_exact_resource_scope_and_executables_survive(self):
        source=suit.PARENT_PATH.read_bytes()
        candidate,report=suit.apply_rom(source)
        an,aa=suit.resources(source);bn,bb=suit.resources(candidate)
        self.assertEqual(an,bn)
        self.assertEqual(sorted(n for n,a,b in zip(an,aa,bb) if a!=b),sorted(suit.CHANGED))
        for field in ('arm9','arm7'):
            a,b=w.parse_header(source),w.parse_header(candidate)
            self.assertEqual(source[a[field+'_offset']:a[field+'_offset']+a[field+'_size']],
                candidate[b[field+'_offset']:b[field+'_offset']+b[field+'_size']])
        from tools.qol_suits_menu import decode_grown
        for name in ('English.strings','American.strings'):
            self.assertIn('v'+suit.VERSION,decode_grown(bb[bn.index(name)],50))
            self.assertEqual(decode_grown(bb[bn.index(name)],74),'Options v'+suit.VERSION)
        self.assertTrue(report['executable_unchanged'])
        self.assertTrue(report['all_other_resources_unchanged'])

    def test_foreign_rom_is_rejected_before_authoring(self):
        with self.assertRaisesRegex(ValueError,'exact published v0.29.0'):suit.apply_rom(b'foreign')


if __name__=='__main__':unittest.main()
