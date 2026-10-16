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

    def test_every_shutter_faces_into_its_room_and_frames_stay_at_the_wall(self):
        for name in cr.NAMES:
            for side,wall,floor,_ in cr.PORTS[name]:
                direction=1 if side=='left' else -1
                quads=art.portal(cr.looks()['door'],wall,floor,side=='left')
                shutter=quads[0]
                normal=rc._normal(shutter.corners)
                self.assertGreater(normal[0]*direction,0,(name,side,floor))
                self.assertEqual(normal[1:],(0,0))
                for q in quads:
                    for x,y,z in q.corners:
                        self.assertTrue(0 < (x-wall)*direction < 1.5)
                        self.assertTrue(floor <= y <= floor+17)

    def test_outdoor_roof_covers_the_full_collision_ceiling_and_faces_down(self):
        for w,h in cr.BOUNDS:
            underside=art.ceiling(w,h,draw_shell=True)[0]
            self.assertEqual(set(underside.corners),{(0,h,-25),(0,h,25),(w,h,-25),(w,h,25)})
            self.assertLess(rc._normal(underside.corners)[1],0)
            quads=art.ceiling(w,h,draw_shell=True)
            # A single stretched16-colour tile looked like huge blank blocks
            # in upper corners. Steel/hazard repeats must keep world scale.
            self.assertEqual(quads[1].repeats[2][0],w/art.STEEL.size[0])
            self.assertEqual(quads[2].repeats[2][0],w/art.EDGE.size[0])
            for q in quads:
                self.assertTrue(all(y>=h for x,y,z in q.corners))


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

    def test_built_rooms_draw_each_exit_and_the_entire_collision_roof(self):
        _,glob,manifest=mod.load_clean()
        entries={e['name']:e for e in manifest['entries']}
        def blob(name):
            e=entries[name];return glob[e['offset']:e['offset']+e['size']]
        for name in cr.NAMES:
            with self.subTest(room=name):
                plan=cr.geometry(name,blob);w,h=cr.BOUNDS[cr.NAMES.index(name)]
                sizes={t.name:(t.width,t.height) for t in plan.textures}
                faces=rc._emit(plan,sizes)
                shutters=faces['gdoor01']
                self.assertEqual(len(shutters),len(cr.PORTS[name]))
                for side,wall,floor,_ in cr.PORTS[name]:
                    candidates=[v for _,v in shutters if abs(v[0][0]-wall)<.2 and min(p[1] for p in v)==floor]
                    self.assertEqual(len(candidates),1)
                    self.assertGreater(rc._normal([p[:3] for p in candidates[0]])[0]*(1 if side=='left' else -1),0)
                # A real underside must cover every horizontal sample at
                # the actual collision roof, at the actor's z=0 plane.
                roofs=[v for group in faces.values() for _,v in group
                       if all(p[1]==h for p in v) and rc._normal([p[:3] for p in v])[1]<0
                       and min(p[2] for p in v)<=0<=max(p[2] for p in v)]
                for x in range(w+1):
                    self.assertTrue(any(min(p[0] for p in v)<=x<=max(p[0] for p in v) for v in roofs),(name,x))
                marks=[q for q in plan.scenery if q.look.texture=='AccessMark']
                high=[port for port in cr.PORTS[name] if port[2]]
                self.assertEqual(len(marks),len(high))
                for mark,(side,wall,floor,_) in zip(marks,high):
                    x0,x1=min(p[0] for p in mark.corners),max(p[0] for p in mark.corners)
                    y0,y1=min(p[1] for p in mark.corners),max(p[1] for p in mark.corners)
                    self.assertEqual((x1-x0,y1-y0),(4,4))
                    self.assertEqual(y0,floor+17)
                    self.assertLessEqual(y1,h)
                    self.assertGreater(rc._normal(mark.corners)[2],0)
                if name!=cr.NAMES[2]:
                    self.assertFalse(any(q.look.texture.startswith('HarborSign') for q in plan.scenery))


if __name__=='__main__':unittest.main()
