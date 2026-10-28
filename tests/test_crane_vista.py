"""Long Arm harbour vista: scenery-only, collision-identical and chainable."""
import unittest
import mod
from tools import crane_vista as v, crane_map as m, room_compiler as rc, wos_tool as w, spider2099 as assets

PARENT = v.ROOT/'build/version-0.37.0-final/Versioned.nds'


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private original missing')
class Scenery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = v.native_plan()
        cls.new = v.vista(cls.plan)

    def test_only_the_published_slab_and_pillars_leave_and_only_scenery_changes(self):
        slab, pillars = v.published_occluders()
        gone = [q for q in self.plan.scenery if q not in self.new.scenery]
        self.assertEqual(len(gone), len(slab)+len(pillars))
        self.assertTrue(all(q in (*slab, *pillars) for q in gone))
        self.assertEqual((self.new.solids, self.new.panels, self.new.bounds), (self.plan.solids, self.plan.panels, self.plan.bounds))

    def test_everything_added_stays_behind_the_actor_plane_and_inside_the_room(self):
        added = [q for q in self.new.scenery if q not in self.plan.scenery]
        self.assertGreater(len(added), 100)
        for q in added:
            xs, ys, zs = zip(*q.corners)
            self.assertLessEqual(max(zs), -19.9, q)
            self.assertGreaterEqual(min(xs), -6, q)
            self.assertLessEqual(max(xs), 428, q)
            self.assertGreaterEqual(min(ys), -4.01, q)

    def test_compiled_collision_is_byte_identical_and_quads_stay_under_the_published_peak(self):
        old, new = rc.compile_room(self.plan), rc.compile_room(self.new)
        self.assertEqual(new.collision, old.collision)
        self.assertLessEqual(new.quads, v.MAX_QUADS)
        self.assertLess(v.MAX_QUADS, 531)    # Dry Dock, the busiest published room

    def test_a_changed_parent_scenery_is_refused(self):
        slab, _ = v.published_occluders()
        from dataclasses import replace
        missing = replace(self.plan, scenery=tuple(q for q in self.plan.scenery if q != slab[0]))
        with self.assertRaises(ValueError):v.vista(missing)


@unittest.skipUnless(mod.DEFAULT_ROM.exists() and PARENT.exists(), 'published v0.37.0 candidate missing')
class Release(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = PARENT.read_bytes()
        cls.result, cls.report = v.apply_rom(cls.parent)

    def test_only_the_room_model_and_textures_change(self):
        names, old = assets.resources(self.parent)
        _, new = assets.resources(self.result)
        self.assertEqual([n for n, a, b in zip(names, old, new) if a != b], [v.MODEL, v.TEXTURE])
        self.assertTrue(self.report['collision_identical'])
        self.assertEqual(new[names.index(v.COLLISION)], old[names.index(v.COLLISION)])

    def test_repeat_and_either_order_with_the_map_pass_give_the_same_rom(self):
        again, _ = v.apply_rom(self.result)
        self.assertEqual(again, self.result)
        mapped, _ = m.apply_rom(self.parent)
        a, _ = v.apply_rom(mapped)
        b, _ = m.apply_rom(self.result)
        self.assertEqual(w.sha256(a), w.sha256(b))

    def test_other_roms_are_refused(self):
        with self.assertRaises(ValueError):v.apply_rom(mod.DEFAULT_ROM.read_bytes())


if __name__ == '__main__':
    unittest.main()
