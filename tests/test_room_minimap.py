"""Real templates round-trip; maps agree with the geometry and keep native UI."""
import unittest
import mod
from tools import midnight_rooms as mr,midnight_chapter as ch,room_minimap as rm
from tools.minimap_cbmp import Cbmp

class RoomMinimapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,glob,manifest=mod.load_clean()
        cls.blobs={e['name']:glob[e['offset']:e['offset']+e['size']] for e in manifest['entries']}

    def test_native_frame_palette_and_unknown_bytes_survive(self):
        raw=self.blobs[ch.MAP_SOURCE];old=Cbmp.parse(raw)
        self.assertEqual(old.to_bytes(),raw)
        for name,spec in mr.AUTHORED.items():
            data,p=rm.build(raw,mr.plan(name,self.blobs.__getitem__),spec.doors,hazards=spec.hazards,save=spec.save)
            new=Cbmp.parse(data)
            self.assertEqual(new.to_bytes(),data)
            self.assertEqual(new.tiles[:len(old.tiles)],old.tiles)
            self.assertEqual((new.unknown,new.trailing),(old.unknown,old.trailing))
            changed=set(range(rm.PALETTE*16,rm.PALETTE*16+len(rm.COLOURS)))
            for i,(a,b) in enumerate(zip(old.screen,new.screen)):
                x,y=i%old.width,i//old.width
                if 3<=x<28 and 3<=y<19:continue
                self.assertEqual(a,b)
                for c in set(old.tile(a&1023)):
                    if c:self.assertNotIn((a>>12)*16+c,changed)
            self.assertTrue({i for i,(a,b) in enumerate(zip(old.palette,new.palette)) if a!=b}<=changed)

    def test_projection_endpoints_and_orientation(self):
        for name in mr.AUTHORED:
            room=mr.plan(name,self.blobs.__getitem__);p=rm.projection(room)
            x0,y0,x1,y1=room.bounds;l,t,r,b=p.rect
            self.assertEqual(p.point(x0,y0),(l,b))
            self.assertEqual(p.point(x1,y1),(r,t))
            self.assertEqual(p.fields[1:5],tuple(v*4096 for v in p.rect))
            self.assertLessEqual(abs((r-l)/(x1-x0)-(b-t)/(y1-y0)),0.025)

    def test_landmark_pixels_follow_world_coordinates(self):
        spec=mr.AUTHORED['ML_ServiceBay'];room=mr.plan(spec.name,self.blobs.__getitem__)
        data,p=rm.build(self.blobs[ch.MAP_SOURCE],room,spec.doors,save=spec.save)
        screen=Cbmp.parse(data)
        self.assertEqual(screen.pixel_index(*p.point(*spec.save)),rm.PALETTE*16+9)
        door=spec.doors[0]
        self.assertEqual(screen.pixel_index(*p.point(door.wall,door.floor+6)),rm.PALETTE*16+5)

if __name__=='__main__':unittest.main()
