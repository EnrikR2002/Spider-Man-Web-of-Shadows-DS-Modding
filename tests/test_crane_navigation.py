"""Map connections must match real door pairs and remain legible in every phase."""
import struct
import unittest
import mod
from tools import crane_navigation as n,crane_rooms as cr,midnight_chapter as ch
from tools.minimap_cbmp import Cbmp

class NavigationGraphTests(unittest.TestCase):
    def test_every_door_has_one_exact_map_connection(self):
        seen=[]
        for link in n.LINKS:
            seen.append(link.source)
            if link.destination is None:
                self.assertEqual(cr.LINKS[link.source],('Pier_Save02',2))
            else:
                seen.append(link.destination)
                a,g=link.source;b,h=link.destination
                self.assertEqual(cr.LINKS[a,g],(b,cr.PORTS[b][h-1][3]))
                self.assertEqual(cr.LINKS[b,h],(a,cr.PORTS[a][g-1][3]))
        self.assertCountEqual(seen,cr.LINKS)

    def test_necks_join_touching_rooms_without_overlap_and_make_one_connected_map(self):
        shapes={name:n.shape(name) for name in cr.NAMES}
        owner={}
        for name,pixels in shapes.items():
            for xy in pixels:
                self.assertNotIn(xy,owner,(name,owner.get(xy)));owner[xy]=name
        def touching(pixels,other):
            return any((x+dx,y+dy) in other for x,y in pixels for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))
        neck_owner={};graph={name:set() for name in cr.NAMES}
        for link in n.LINKS:
            if link.neck is None:continue
            x0,y0,x1,y1=link.neck
            pixels={(x,y) for x in range(x0,x1) for y in range(y0,y1)}
            self.assertFalse(pixels&owner.keys(),link)
            self.assertFalse(pixels&neck_owner.keys(),link)
            neck_owner.update({xy:link for xy in pixels})
            a,b=link.source[0],link.destination[0]
            self.assertTrue(touching(pixels,shapes[a]) and touching(pixels,shapes[b]),link)
            graph[a].add(b);graph[b].add(a)
        seen={cr.NAMES[0]};stack=[cr.NAMES[0]]
        while stack:
            for other in graph[stack.pop()]-seen:seen.add(other);stack.append(other)
        self.assertEqual(seen,set(cr.NAMES))

    def test_only_the_pier_exit_is_an_arrow_and_it_leaves_the_quays_left_wall(self):
        arrows=[link for link in n.LINKS if link.neck is None]
        self.assertEqual([link.source for link in arrows],[(cr.NAMES[0],1)])
        x,y,dx=arrows[0].arrow;x0,y0,x1,y1=n.RECTS[cr.NAMES[0]]
        self.assertEqual((x,dx,cr.PORTS[cr.NAMES[0]][0][0]),(x0,-1,'left'))
        self.assertTrue(y0<=y<y1)
        self.assertFalse(set(n.arrow_pixels(arrows[0]))&set().union(*(n.shape(name) for name in cr.NAMES)))

    def test_all_pixels_fit_panel_and_lock_target_state_tracks_progress(self):
        for stage in range(4):
            p=n.map_pixels(stage)
            self.assertTrue(all(0<=x<200 and 16<=y<120 for x,y in p))
            self.assertEqual(n.phase(n.phase_flags(stage)),stage)
            self.assertTrue(any(name==n.TARGETS[stage] and role==n.GOAL for name,role in p.values()))
        # Each locked door reddens only its own half of its neck until its flag is earned.
        unlock={'power':1,'upper':2,'crown':2,'boss':3}
        for key,(flag,_) in cr.LOCKS.items():
            link=next(link for link in n.LINKS if key in (link.source,link.destination))
            for stage in range(4):
                roles={role for name,role in n.neck_pixels(link,n.phase_flags(stage)).values() if name==key[0]}
                self.assertEqual(roles,{n.LOCK if stage<unlock[flag] else ch.EDGE},(key,stage))

    def test_hints_and_detail_captions_refer_to_real_destinations(self):
        for name in cr.NAMES:
            self.assertTrue(set(n.entry_keys(name))<=set(cr.LINES))
            self.assertEqual(n.detail_labels(name),())
        self.assertTrue(all(len(header[0])<=13 and header[1]=='' for header in n.HEADERS))


class NavigationAdapterTests(unittest.TestCase):
    def execute(self,area,room,flags,stats=True,cpsr=0xA800001F,objective=False):
        at,stop=0x02159A00,0x03004000 if objective else n.SCREEN_SITE+4;table,stats_at=0x02200000,0x02201000
        output,records=0x02202000,0x02203000
        raw=n.objective_adapter(at,records) if objective else n.screen_adapter(at,(4100,4101,4102,4103))
        memory={at+i:v for i,v in enumerate(raw)}
        def put(addr,value):memory.update({addr+i:v for i,v in enumerate(struct.pack('<I',value))})
        def get(addr):return int.from_bytes(bytes(memory[addr+i] for i in range(4)),'little')
        put(0x02145C5C,stats_at if stats else 0);put(stats_at,room)
        memory[stats_at+0x2D]=(flags>>136)&255;memory[stats_at+0x2E]=(flags>>144)&255
        put(table+area*16,1000+area)
        regs=[output if objective else 0xABC,9 if objective else table,area,0x123,4,5,6,7,8,9,10,11,0xCDEF,0x023FF000,0x03004000,at]
        before=list(regs);initial=cpsr;fallback=False
        original_stats=[memory.get(stats_at+i) for i in range(0x98)]
        for _ in range(100):
            pc=regs[15]
            if objective and pc==n.OBJECTIVE_NATIVE:
                self.assertEqual(regs[0],before[0]);self.assertEqual(regs[1],before[1]);self.assertEqual(cpsr,initial)
                fallback=True;regs[2]=0x0211E4C8;regs[1]=regs[2]+regs[1]*16;put(regs[0],regs[1]);regs[15]=regs[14];continue
            if pc==stop:
                excluded=(1,2) if objective else (1,)
                self.assertEqual([v for i,v in enumerate(regs[:15]) if i not in excluded],[v for i,v in enumerate(before[:15]) if i not in excluded])
                self.assertEqual(cpsr,initial)
                self.assertEqual([memory.get(stats_at+i) for i in range(0x98)],original_stats)
                return (get(output),fallback) if objective else regs[1]
            word=get(pc);regs[15]=pc+4;cond=word>>28;z=bool(cpsr&0x40000000);carry=bool(cpsr&0x20000000)
            if not {0:z,1:not z,2:carry,3:not carry,14:True}[cond]:continue
            if word==0xE10FC000:regs[12]=cpsr
            elif word==0xE128F00C:cpsr=(cpsr&0x00FFFFFF)|(regs[12]&0xFF000000)
            elif word==n.SCREEN_ORIGINAL:regs[1]=get(regs[1]+regs[2]*16)
            elif word==0xE12FFF1E:regs[15]=regs[14]
            elif word&0x0E000000==0x0A000000:
                offset=word&0xFFFFFF
                if offset&0x800000:offset-=1<<24
                regs[15]=pc+8+offset*4
            elif word&0xFFFF0000 in (0xE92D0000,0xE8BD0000):
                indexes=[i for i in range(16) if word>>i&1]
                if word>>16==0xE92D:
                    regs[13]-=4*len(indexes)
                    for i,index in enumerate(indexes):put(regs[13]+i*4,regs[index])
                else:
                    values=[get(regs[13]+i*4) for i in range(len(indexes))];regs[13]+=4*len(indexes)
                    for index,value in zip(indexes,values):regs[index]=value
            elif word&0x0FF00000==0x03500000:
                a,b=regs[word>>16&15],word&255;value=(a-b)&0xFFFFFFFF
                cpsr=(cpsr&0x0FFFFFFF)|(value&0x80000000)|(0x40000000 if value==0 else 0)|(0x20000000 if a>=b else 0)
            elif word&0x0FF00000==0x03100000:
                value=regs[word>>16&15]&(word&255)
                cpsr=(cpsr&0x3FFFFFFF)|(0x40000000 if value==0 else 0)|(value&0x80000000)
            elif word&0x0FF00000 in (0x05900000,0x05D00000):
                base=word>>16&15;addr=(pc+8 if base==15 else regs[base])+(word&0xFFF)
                regs[word>>12&15]=memory[addr] if word&0x00400000 else get(addr)
            elif word&0x0FF00000==0x05800000:put(regs[word>>16&15]+(word&0xFFF),regs[word>>12&15])
            else:self.fail(hex(word))
        self.fail('Map selector did not return')

    def test_native_areas_rooms_null_stats_and_processor_flags_are_preserved(self):
        for area in range(8):
            for room in (0,75,95,108,0xFFFFFFFF):self.assertEqual(self.execute(area,room,0),1000+area)
        self.assertEqual(self.execute(6,100,0,stats=False),1006)

    def test_private_area_chooses_each_earned_goal_without_writing_stats(self):
        for room in range(96,108):
            for stage in range(4):
                for cpsr in (0x0000001F,0xF800001F):
                    self.assertEqual(self.execute(6,room,n.phase_flags(stage),cpsr=cpsr),4100+stage)

    def test_objectives_page_uses_private_titles_bodies_and_native_fallback(self):
        for room in (0,38,75,95,108,0xFFFFFFFF):
            self.assertEqual(self.execute(0,room,0,objective=True),(0x0211E4C8+9*16,True))
        self.assertEqual(self.execute(0,100,0,stats=False,objective=True),(0x0211E4C8+9*16,True))
        for room in range(96,108):
            for stage in range(4):
                self.assertEqual(self.execute(0,room,n.phase_flags(stage),objective=True),(0x02203000+stage*8,False))


@unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original missing')
class NavigationScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,glob,manifest=mod.load_clean();e=next(e for e in manifest['entries'] if e['name']==ch.MAP_SOURCE)
        cls.raw=glob[e['offset']:e['offset']+e['size']]

    def test_variants_roundtrip_share_slots_keep_frame_and_stay_in_tile_budget(self):
        listing=None
        for stage in range(4):
            raw,rows=n.overview(self.raw,stage);s=Cbmp.parse(raw);old=Cbmp.parse(self.raw)
            self.assertEqual(s.to_bytes(),raw);self.assertLessEqual(s.count,1024)
            self.assertEqual(s.tiles[:len(old.tiles)],old.tiles)
            self.assertEqual((s.unknown,s.trailing),(old.unknown,old.trailing))
            if listing is not None:self.assertEqual(rows,listing)
            listing=rows
            # A private source palette may change, but it cannot recolour
            # the native frame/buttons outside the map's replaced border.
            for y in range(192):
                for x in range(256):
                    if 16<=x<240 and 16<=y<160:continue
                    a,b=old.pixel_index(x,y),s.pixel_index(x,y)
                    self.assertEqual(None if a is None else old.palette[a],None if b is None else s.palette[b],(x,y))

if __name__=='__main__':unittest.main()
