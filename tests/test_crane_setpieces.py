"""Safety and progress contracts for Crane Row's playable set pieces."""
import struct
import unittest
import mod
from tools import crane_rooms as cr,crane_walk as cw,room_compiler as rc,room_author
from tools.room_objects import RoomObjects
from tools.room_entities import Entities
from tools.room_events import Events

@unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original missing')
class SetpieceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,glob,manifest=mod.load_clean()
        entries={e['name']:e for e in manifest['entries']}
        cls.blob=staticmethod(lambda name:glob[entries[name]['offset']:entries[name]['offset']+entries[name]['size']])
        cls.plans={n:cr.geometry(n,cls.blob) for n in cr.NAMES}

    def test_all_existing_arrivals_have_clear_body_space_and_a_real_landing(self):
        for name,plan in self.plans.items():
            tree=rc.rc.RoomCollision.parse(rc.collision(plan))
            for door in cr.SPECS[name].doors:
                x=door.wall+(door.inset if door.side=='left' else -door.inset);y=door.floor
                self.assertIsNotNone(tree.solid_at(x,y-.25),(name,door,'missing landing'))
                for dx in (-3,0,3):
                    for dy in (1,6,11):self.assertIsNone(tree.solid_at(x+dx,y+dy),(name,door,'blocked arrival'))

    def test_broken_docks_have_visible_recovery_floors_and_camera_coverage(self):
        for i,bottom in cr.LOWER.items():
            name=cr.NAMES[i];plan=self.plans[name]
            self.assertEqual(plan.bounds[1],bottom)
            self.assertEqual(min(y for p in cr.SPECS[name].camera for x,y in p),bottom)
            self.assertNotIn('below',plan.hidden_shell)
            tree=rc.rc.RoomCollision.parse(rc.collision(plan))
            self.assertTrue(any(tree.solid_at(x,-1) is None for x in range(40,int(plan.bounds[2])-40)))
            self.assertTrue(all(tree.solid_at(x,bottom-.25) is not None for x in range(1,int(plan.bounds[2]))))

    def test_native_input_route_targets_are_real_landings_with_headroom(self):
        for label,(i,spawn,group,points) in cw.SETPIECES.items():
            plan=self.plans[cr.NAMES[i]];tree=rc.rc.RoomCollision.parse(rc.collision(plan))
            for x,y in points:
                self.assertIsNotNone(tree.solid_at(x,y-5.25),(label,x,y,'no platform'))
                for dx in (-3,0,3):
                    for dy in (-4,0,6):self.assertIsNone(tree.solid_at(x+dx,y+dy),(label,x,y,'body collision'))

    def test_encounter_decks_have_floor_anchors_above_the_old_flat_floor(self):
        for i in (1,3,4,9):
            name=cr.NAMES[i];p=self.plans[name];spec=cr.SPECS[name]
            tree=rc.rc.RoomCollision.parse(rc.collision(p))
            anchors=room_author.plan_anchors(rc.surfaces(p),spec.area,floor_top=spec.spawn_top,
                                           solid=lambda x,y:tree.solid_at(x,y) is not None)
            self.assertTrue(any(kind==1 and y>14 for x,y,kind in anchors),name)

    def test_patrol_anchors_reach_upper_routes_without_requiring_ceiling_shells(self):
        for i,minimum in ((0,50),(1,100),(3,90),(6,180),(7,60),(9,120)):
            name=cr.NAMES[i];plan=self.plans[name];spec=cr.SPECS[name]
            tree=rc.rc.RoomCollision.parse(rc.collision(plan))
            points=room_author.plan_anchors(rc.surfaces(plan),spec.area,floor_top=spec.spawn_top,
                                           solid=lambda x,y:tree.solid_at(x,y) is not None)
            self.assertTrue(any(kind==1 and y>=minimum for x,y,kind in points),(name,minimum))

if __name__=='__main__':unittest.main()
