"""Art must remain deterministic, GPU-bounded, and outside movement contracts."""
import unittest
from tools import crane_art as art, crane_rooms as cr, room_compiler as rc
from tools import nitro_build as nb
from tools.nitro_texture import TextureArchive
import mod


class CraneArtTests(unittest.TestCase):
    def test_original_materials_are_lossless_and_have_unique_nitro_names(self):
        pairs=art.materials();textures,palettes=zip(*pairs)
        self.assertEqual(len({t.name for t in textures}),len(textures))
        self.assertTrue(all(len(t.name)<=16 and p.name==t.name+'_pl' for t,p in pairs))
        raw=nb.texture_archive(textures,palettes)
        self.assertEqual(TextureArchive.parse(raw).to_bytes(),raw)
        art.materials.cache_clear()
        self.assertEqual(art.materials(),pairs)

    def test_all_lattice_braces_face_the_camera_at_every_slope(self):
        for x0,y0,x1,y1 in ((0,0,10,30),(10,30,0,0),(0,30,10,0),(5,0,5,30),(0,5,30,5)):
            q=art.bar(x0,y0,x1,y1,-100)
            self.assertGreater(rc._normal(q.corners)[2],0)
        with self.assertRaises(ValueError):art.bar(0,0,0,0,-20)

    def test_all_room_landmarks_are_behind_the_actor_plane(self):
        for i,(w,h) in enumerate(cr.BOUNDS):
            # With no solids only landmarks are emitted; fittings on existing
            # solids are separately bounded by their collision silhouettes.
            for q in art.setwork(i,w,h,()):
                self.assertLess(max(p[2] for p in q.corners),-7,(i,q))
                if all(p[2]==q.corners[0][2] for p in q.corners):
                    self.assertGreater(rc._normal(q.corners)[2],-0.001)


@unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original missing')
class CraneArtBudgetTests(unittest.TestCase):
    def test_all_room_models_fit_conservative_texture_and_polygon_budgets(self):
        _,glob,manifest=mod.load_clean()
        entries={e['name']:e for e in manifest['entries']}
        def blob(name):
            e=entries[name];return glob[e['offset']:e['offset']+e['size']]
        for name in cr.NAMES:
            with self.subTest(room=name):
                plan=cr.geometry(name,blob);built=rc.compile_room(plan)
                self.assertLess(built.quads,400)
                tex,pal=nb.archive_parts(built.textures)
                self.assertLess(sum(len(t.data)+len(t.index) for t in tex),128*1024)
                self.assertLess(sum(len(p.data) for p in pal),16*1024)
                # Every scenery face must have area; inverted diagonal braces
                # used to silently disappear with native front-face culling.
                for q in plan.scenery:
                    self.assertGreater(sum(v*v for v in rc._normal(q.corners)),0)


if __name__=='__main__':unittest.main()
