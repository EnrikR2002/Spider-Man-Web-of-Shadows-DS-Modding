"""Cape removal, rig/UV/budget contracts and isolation from native gameplay."""
from pathlib import Path
import struct
import unittest

from tools import spider2099 as base, spider2099_art as old, spider2099_movie as movie
from tools import spider2099_movie_art as art, spider2099_visual as visual, tasm_kit, wos_tool as w
from tools.animation_rig import AnimationRig
from tools.model_geometry import ModelGeometry
from tools.nitro_texture import TextureArchive
from tests.test_spider2099_polish import VisualSelectorABI as ExistingSelectorABI

ROOT = Path(__file__).resolve().parents[1]


class MovieAssets:
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'work/glob/spdB.nsbmd').read_bytes()
        cls.native_tex = (ROOT/'work/glob/spdB.nsbtx').read_bytes()
        cls.parent = movie.PARENT_PATH.read_bytes()
        cls.names, cls.blobs = base.resources(cls.parent)
        cls.previous = cls.blobs[cls.names.index('spd.nsbmd')]
        cls.black, cls.report = art.model(cls.native)
        cls.indices, cls.palette, cls.paint = art.artwork(cls.native)
        cls.black_tex = art.texture(cls.native_tex, cls.indices, cls.palette)
        cls.red = movie.red_model(cls.previous, (ROOT/'work/glob/spd.nsbmd').read_bytes())
        cls.red_tex = cls.blobs[cls.names.index('spd.nsbtx')]
        cls.shared, cls.metadata = visual.shared_model(cls.red, cls.black, cls.red_tex, cls.black_tex)


class MovieContract(MovieAssets, unittest.TestCase):
    def test_native_rig_sbc_and_unknown_node_bytes_are_exact(self):
        a, b = AnimationRig.parse(self.native), AnimationRig.parse(self.black)
        self.assertEqual((a.names, a.parents, a.node_records), (b.names, b.parents, b.node_records))
        self.assertEqual(self.native[a.object_offsets[0]:a.sbc_end], self.black[b.object_offsets[0]:b.sbc_end])

    def test_only_body_blades_and_talons_exist_and_no_cape_stream_survives(self):
        self.assertEqual(self.report['cape'], {'triangles': 0, 'removed': True})
        self.assertEqual(self.report['added_triangles'], 6*4 + 6*2)
        self.assertEqual(len(old.mesh(self.black)), 516)
        self.assertEqual(len(self.shared), ModelGeometry.parse(self.red).shapes[0].start
                         + ModelGeometry.parse(self.red).shapes[0].length
                         + ModelGeometry.parse(self.black).shapes[0].length + visual.TRAILER_SIZE)
        # The old cape extends to Z < -3; body/mounted blades are close to skin.
        self.assertGreater(min(v.position[2] for f in old.mesh(self.black) for v in f), -1.8)

    def test_all_six_blades_are_surface_mounted_and_swept_toward_elbow(self):
        from tools.rush_choreography import sub, unit, dot, length
        a = art.Anatomy(self.native)
        self.assertEqual(len(self.report['forearm_blades']), 6)
        for blade in self.report['forearm_blades']:
            elbow, wrist = (8, 9) if blade['slot'] == 6 else (18, 19)
            direction = unit(sub(a.positions[wrist], a.positions[elbow]))
            self.assertLess(dot(sub(blade['tip_world'], blade['base_world']), direction), 0)
            self.assertGreater(blade['surface_radius'], .25)
            self.assertGreater(length(sub(blade['tip_world'], blade['base_world'])), .43)

    def test_original_red_stream_and_texture_selection_are_retained(self):
        a, b = ModelGeometry.parse(self.previous), ModelGeometry.parse(self.shared)
        self.assertEqual(self.previous[a.shapes[0].start:a.shapes[0].start+a.shapes[0].length],
                         self.shared[b.shapes[0].start:b.shapes[0].start+b.shapes[0].length])
        self.assertEqual(self.metadata['red_dimensions'], [128, 128])
        self.assertEqual(self.metadata['red_magnification'], [2048, 2048])
        self.assertEqual(self.metadata['black_dimensions'], [128, 128])
        self.assertEqual(self.metadata['black_magnification'], [4096, 4096])

    def test_opaque_i8_atlas_and_dimensions_stay_within_the_previous_pixel_pool(self):
        t = TextureArchive.parse(self.black_tex).textures[0]
        self.assertEqual((t['width'], t['height'], t['format'], t['size']), (128, 128, 4, 16384))
        self.assertFalse(t['params'] & 0x2000)
        self.assertEqual(self.black_tex[t['offset']:t['offset']+t['size']], self.indices)
        self.assertEqual(t['unknown_u32'] & 2047, 128)
        self.assertEqual(t['unknown_u32'] >> 11 & 2047, 128)
        self.assertEqual(t['unknown_u32'] & 0xffc00000, w.u32(self.native_tex, 0x68) & 0xffc00000)
        previous = TextureArchive.parse(self.blobs[self.names.index('spdB.nsbtx')]).textures[0]
        self.assertEqual(t['size'], previous['size'])

    def test_movie_mask_has_negative_space_and_spider_has_separate_lower_legs(self):
        a = art.Anatomy(self.native)
        for p in ((.12, 9.02, .1), (.36, 9.61, .1), (.42, 6.4, .4)):
            self.assertTrue(art.red_marking(p, a), p)
        for p in ((.33, 9.31, .1), (0, 9.55, .1), (.52, 6.30, .4)):
            self.assertFalse(art.red_marking(p, a), p)

    def test_bounds_contain_every_drawn_vertex(self):
        g = ModelGeometry.parse(self.black)
        box = struct.unpack_from('<6h', self.black, g.model+44)
        scale = w.u32(self.black, g.model+56) / 4096
        for face in old.mesh(self.black):
            for v in face:
                for k in range(3):
                    self.assertGreaterEqual(v.position[k]+.002, box[k]/4096*scale)
                    self.assertLessEqual(v.position[k]-.002, (box[k]+box[k+3])/4096*scale)


class MovieSelectorABI(MovieAssets, ExistingSelectorABI):
    # Re-run every real ARM ownership/flags/reallocation guard on this model.
    def test_black_then_red_switches_only_shape_material_fields(self):
        p = self.fixture()
        before = dict(p.memory)
        self.call(p)
        allowed = {self.mdl+self.metadata['shape_offset']+i for i in range(8, 16)}
        allowed |= {self.mdl+self.metadata['material_offset']+i for i in range(32, 44)}
        self.assertTrue({at for at, value in before.items() if p.memory[at] != value} <= allowed)
        mat = self.mdl+self.metadata['material_offset']
        self.assertEqual(p.get(mat+32), 128 | 128 << 16)
        self.assertEqual(p.get(mat+36), 4096)
        p.memory[self.stats+0x53] = 0
        self.call(p, 0x6000001f)
        self.assertEqual(p.get(mat+36), 2048)


class MovieComposition(unittest.TestCase):
    def test_scope_is_four_resources_and_existing_selector_literals(self):
        source = movie.PARENT_PATH.read_bytes()
        result, report = movie.apply_rom(source)
        an, aa = base.resources(source)
        bn, bb = base.resources(result)
        self.assertEqual(an, bn)
        self.assertEqual(sorted(n for n, a, b in zip(an, aa, bb) if a != b), sorted(movie.CHANGED))
        ha, hb = w.parse_header(source), w.parse_header(result)
        a = source[ha['arm9_offset']:ha['arm9_offset']+ha['arm9_size']]
        b = result[hb['arm9_offset']:hb['arm9_offset']+hb['arm9_size']]
        self.assertEqual(len(a), len(b))
        self.assertEqual(a[tasm_kit.SOURCE:tasm_kit.SOURCE+tasm_kit.RESERVE], b[tasm_kit.SOURCE:tasm_kit.SOURCE+tasm_kit.RESERVE])
        offset = report['cosmetic_draw_selector']['arm9_source_offset']
        # Only the bounded selector's data literals change; its instructions agree.
        self.assertEqual(a[:offset], b[:offset])
        self.assertEqual(a[offset:offset+436], b[offset:offset+436])
        self.assertEqual(a[offset+488:], b[offset+488:])
        for e in w.nitrofs_entries(result):
            if e['name'] == 'Glob.bin':
                continue
            p = next(p for p in w.nitrofs_entries(source) if p['name'] == e['name'])
            self.assertEqual(source[p['start']:p['end']], result[e['start']:e['end']])
        self.assertEqual(source[ha['arm7_offset']:ha['arm7_offset']+ha['arm7_size']], result[hb['arm7_offset']:hb['arm7_offset']+hb['arm7_size']])

    def test_foreign_parent_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exact published v0.30.1'):
            movie.apply_rom(b'foreign')


if __name__ == '__main__':
    unittest.main()
