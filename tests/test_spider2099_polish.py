"""Real shared draw ownership, blade/cape attachment and native appearance ABI."""
from pathlib import Path
import struct
import unittest

from tests.arm_runtime import ArmProbe
from tools import spider2099 as base,spider2099_sculpt as sculpt,spider2099_visual as visual,wos_tool as w,tasm_kit
from tools.animation_rig import AnimationRig
from tools.model_geometry import ModelGeometry
from tools.nitro_texture import TextureArchive
from tools.chapter_renewal_combat import asm

ROOT=Path(__file__).resolve().parents[1]


class SculptAssets:
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'work/glob/spdB.nsbmd').read_bytes()
        cls.native_tex=(ROOT/'work/glob/spdB.nsbtx').read_bytes()
        cls.black,cls.report=sculpt.model(cls.native)
        cls.indices,cls.palette,cls.paint=sculpt.artwork(cls.native)
        cls.black_tex=sculpt.texture(cls.native_tex,cls.indices,cls.palette)
        names,blobs=base.resources((ROOT/'build/version-0.30.0-final/Versioned.nds').read_bytes())
        cls.red=blobs[names.index('spd.nsbmd')];cls.red_tex=blobs[names.index('spd.nsbtx')]
        cls.parent_black_tex=blobs[names.index('spdB.nsbtx')]
        cls.shared,cls.metadata=visual.shared_model(cls.red,cls.black,cls.red_tex,cls.black_tex)


class SculptContract(SculptAssets,unittest.TestCase):

    def test_radial_sculpt_increases_volume_with_identical_rig_and_sbc(self):
        a,b=AnimationRig.parse(self.native),AnimationRig.parse(self.black)
        self.assertEqual((a.names,a.parents,a.node_records,a.object_offsets),(b.names,b.parents,b.node_records,b.object_offsets))
        self.assertEqual(self.native[a.object_offsets[0]:a.sbc_end],self.black[b.object_offsets[0]:b.sbc_end])
        anatomy=sculpt.Anatomy(self.native)
        self.assertGreater(anatomy.morph((.9,7.5,.4))[0],1.05)
        self.assertGreater(anatomy.morph((.9,7.5,.4))[2],.5)
        for old,new in zip((.1,5.4,.1),anatomy.morph((.1,5.4,.1))):
            self.assertAlmostEqual(old,new,places=6)

    def test_blades_are_on_the_surface_and_sweep_toward_each_elbow(self):
        self.assertEqual(len(self.report['forearm_blades']),6)
        self.assertEqual({r['slot'] for r in self.report['forearm_blades']},{6,15})
        a=sculpt.Anatomy(self.native)
        from tools.rush_choreography import sub,mul,unit,dot,length
        for r in self.report['forearm_blades']:
            elbow,wrist=(8,9) if r['slot']==6 else (18,19)
            direction=unit(sub(a.positions[wrist],a.positions[elbow]))
            self.assertTrue(r['sweep_toward_elbow'])
            self.assertLess(dot(sub(r['tip_world'],r['base_world']),direction),0)
            self.assertGreater(length(sub(r['tip_world'],r['base_world'])),.43)
            self.assertGreater(r['surface_radius'],.25)
        for r in self.report['cape']['collar_anchors']:
            self.assertAlmostEqual(r['skin'][2]-r['point'][2],.07)
            self.assertLess(r['point'][2],r['skin'][2])

    def test_cape_holes_are_real_and_the_entire_body_half_is_opaque(self):
        self.assertTrue(all(self.indices[y*256+x]!=0 for y in range(128) for x in range(128)))
        holes=sum(self.indices[y*256+x]==0 for y in range(128) for x in range(128,256))
        self.assertGreater(holes,10000);self.assertLess(holes,15000)
        t=TextureArchive.parse(self.black_tex).textures[0]
        self.assertEqual((t['width'],t['height'],t['format']),(256,128,3))
        self.assertEqual(t['size'],16384)
        self.assertLessEqual(t['size'],TextureArchive.parse(self.parent_black_tex).textures[0]['size'])
        raw=self.black_tex[t['offset']:t['offset']+t['size']]
        self.assertEqual(bytes(v for b in raw for v in (b&15,b>>4)),self.indices)
        self.assertTrue(t['params']&0x2000)
        self.assertEqual(t['unknown_u32']&2047,256)
        self.assertEqual(t['unknown_u32']>>11&2047,128)
        self.assertEqual(t['unknown_u32']&0xffc00000,TextureArchive.parse(self.native_tex).textures[0]['unknown_u32']&0xffc00000)

    def test_shared_model_default_red_packet_is_byte_exact_and_black_is_distinct(self):
        r=ModelGeometry.parse(self.red);shared=ModelGeometry.parse(self.shared)
        self.assertEqual(self.shared[shared.shapes[0].start:shared.shapes[0].start+shared.shapes[0].length],self.red[r.shapes[0].start:r.shapes[0].start+r.shapes[0].length])
        chosen=visual.selected_model(self.shared,1);b=ModelGeometry.parse(chosen)
        original_black=ModelGeometry.parse(self.black)
        self.assertEqual(chosen[b.shapes[0].start:b.shapes[0].start+b.shapes[0].length],self.black[original_black.shapes[0].start:original_black.shapes[0].start+original_black.shapes[0].length])
        self.assertEqual(self.metadata['black_magnification'],[4096,4096])
        self.assertEqual(self.metadata['red_magnification'],[2048,2048])

    def test_box_contains_all_body_cape_and_blade_vertices(self):
        from tools import spider2099_art as art
        g=ModelGeometry.parse(self.black);box=struct.unpack_from('<6h',self.black,g.model+44)
        scale=w.u32(self.black,g.model+56)/4096
        for face in art.mesh(self.black):
            for v in face:
                for k in range(3):
                    self.assertGreaterEqual(v.position[k]+.002,box[k]/4096*scale)
                    self.assertLessEqual(v.position[k]-.002,(box[k]+box[k+3])/4096*scale)


class VisualSelectorABI(SculptAssets,unittest.TestCase):
    code_at=0x02180000
    owner=0x02200000
    mdl=0x02201000
    stats=0x02220000

    def fixture(self,form=1):
        p=ArmProbe();g=ModelGeometry.parse(self.shared)
        p.code(self.code_at,asm(visual.selector_source(self.code_at,self.metadata),self.code_at))
        p.put(self.owner,visual.MODEL_VTABLE);p.put(self.owner+0x14,self.mdl)
        p.code(self.mdl,self.shared[g.model:]);p.put(visual.STATS_POINTER,self.stats)
        p.code(self.stats,bytes(256));p.memory[self.stats+0x53]=form
        return p

    def call(self,p,flags=0xb000001f,owner=None):
        regs=list(range(13))+[0x023f0000,0x02010000,self.code_at];regs[5]=self.owner if owner is None else owner
        out,cpsr,stop=p.run(regs,flags,{visual.HOOK_EXEC+4})
        self.assertEqual(out[0],regs[5]);self.assertEqual(out[1:15],regs[1:15]);self.assertEqual(cpsr,flags)
        return out

    def test_black_then_red_switches_only_shape_material_fields(self):
        p=self.fixture();before=dict(p.memory);self.call(p)
        allowed={self.mdl+self.metadata['shape_offset']+i for i in range(8,16)}
        allowed|={self.mdl+self.metadata['material_offset']+i for i in range(32,44)}
        changed={at for at,value in before.items() if p.memory[at]!=value}
        self.assertTrue(changed<=allowed)
        shape=self.mdl+self.metadata['shape_offset'];mat=self.mdl+self.metadata['material_offset']
        self.assertEqual(p.get(shape+8),self.metadata['trailer'][6])
        self.assertEqual(p.get(mat+32),256|(128<<16))
        p.memory[self.stats+0x53]=0;self.call(p,0x6000001f)
        self.assertEqual(p.get(shape+8),self.metadata['trailer'][4])
        self.assertEqual(p.get(shape+12),self.metadata['trailer'][5])
        self.assertEqual(p.get(mat+32),128|(128<<16))
        self.assertEqual(p.get(mat+36),2048)

    def test_invalid_owners_models_tags_forms_and_streams_write_nothing(self):
        cases=('owner-type','mdl-null','mdl-high','mdl-size','tag','form','stats-null','stats-high','stream-length','stream-bounds')
        for case in cases:
            with self.subTest(case=case):
                p=self.fixture();meta=self.mdl+self.metadata['metadata_offset']
                if case=='owner-type':p.put(self.owner,0x021301d0)
                elif case=='mdl-null':p.put(self.owner+0x14,0)
                elif case=='mdl-high':p.put(self.owner+0x14,0x023fff00)
                elif case=='mdl-size':p.put(self.mdl,self.metadata['model_size']+4)
                elif case=='tag':p.put(meta,0)
                elif case=='form':p.memory[self.stats+0x53]=2
                elif case=='stats-null':p.put(visual.STATS_POINTER,0)
                elif case=='stats-high':p.put(visual.STATS_POINTER,0x023ffff0)
                elif case=='stream-length':p.put(meta+28,0)
                elif case=='stream-bounds':p.put(meta+24,0x100000)
                before={k:v for k,v in p.memory.items() if self.owner<=k<self.stats+256}
                self.call(p)
                self.assertEqual(before,{k:p.memory[k] for k in before})

    def test_all_condition_flag_combinations_survive_the_pre_draw_hook(self):
        for flags in range(16):
            self.call(self.fixture(),(flags<<28)|0x0800001f)

    def test_reloaded_model_pointer_is_resolved_again_each_draw(self):
        p=self.fixture();self.call(p);old=bytes(p.memory[self.mdl+i] for i in range(self.metadata['model_size']))
        new=self.mdl+0x30000;g=ModelGeometry.parse(self.shared);p.code(new,self.shared[g.model:]);p.put(self.owner+0x14,new)
        self.call(p)
        self.assertEqual(p.get(new+self.metadata['shape_offset']+8),self.metadata['trailer'][6])
        self.assertEqual(bytes(p.memory[self.mdl+i] for i in range(self.metadata['model_size'])),old)


class CompositionContract(unittest.TestCase):
    def test_only_visual_resources_hook_and_autoload_metadata_change(self):
        from tools import spider2099_polish as polish
        source=polish.PARENT_PATH.read_bytes();result,report=polish.apply_rom(source)
        an,aa=base.resources(source);bn,bb=base.resources(result)
        self.assertEqual(an,bn)
        self.assertEqual(sorted(n for n,a,b in zip(an,aa,bb) if a!=b),sorted(polish.CHANGED))
        ha,hb=w.parse_header(source),w.parse_header(result)
        a=source[ha['arm9_offset']:ha['arm9_offset']+ha['arm9_size']]
        b=result[hb['arm9_offset']:hb['arm9_offset']+hb['arm9_size']]
        self.assertEqual(a[tasm_kit.SOURCE:tasm_kit.SOURCE+tasm_kit.RESERVE],b[tasm_kit.SOURCE:tasm_kit.SOURCE+tasm_kit.RESERVE])
        allowed={i for at,size in ((tasm_kit.TABLE_POINTERS,8),(tasm_kit.ARENA_LOWER,4),(report['cosmetic_draw_selector']['arm9_hook_source_offset'],4)) for i in range(at,at+size)}
        self.assertTrue({i for i,(x,y) in enumerate(zip(a[:-36],b)) if x!=y}<=allowed)
        self.assertEqual(source[ha['arm7_offset']:ha['arm7_offset']+ha['arm7_size']],result[hb['arm7_offset']:hb['arm7_offset']+hb['arm7_size']])
        self.assertEqual(len(b)-len(a),4096)

    def test_foreign_parent_is_rejected_before_any_asset_write(self):
        from tools import spider2099_polish as polish
        with self.assertRaisesRegex(ValueError,'exact published v0.30.0'):polish.apply_rom(b'foreign')


if __name__=='__main__':unittest.main()
