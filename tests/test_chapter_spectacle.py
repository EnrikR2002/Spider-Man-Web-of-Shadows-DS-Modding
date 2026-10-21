import json,struct,unittest
from pathlib import Path
from tools import chapter_spectacle_combat as c,chapter_spectacle_rooms as r,chapter_spectacle_events as e
from tests.arm_runtime import ArmProbe

class RuntimeOwnership(unittest.TestCase):
    def regs(self,at,end):return [0x2200000,0x13,2,3,4,5,6,7,8,9,10,11,12,0x23ff000,end,at]

    def test_event_sounds_route_only_the_declared_chapter_range_and_keep_abi(self):
        at=0x2160000;stats=0x2210000;operand=0x2214000;resume=c.SOUND_EVENT_SITE+4;end=0x3000000;play=0x215f000
        for room in (65,76,89,96,107,108):
            for cue in (188,581,582,709,710,718,719,65535):
                p=ArmProbe();p.code(at,c.sound_event(at,710,9,play));p.put(0x2145c5c,stats);p.put(stats,room)
                regs=self.regs(at,end);p.put(regs[0]+12,operand);p.put(operand,cue);called=[]
                def native(probe,rr,flags):called.append(rr[0]);rr[0:4]=[90,91,92,93];return 0x6800001f
                out,flags,pc=p.run(regs,0x9800001f,{resume,end},{play:native})
                private=76<=room<108 and 710<=cue<719
                self.assertEqual(called,[cue] if private else []);self.assertEqual(pc,end if private else resume)
                self.assertEqual(out[:13],regs[:13]);self.assertEqual(out[13],regs[13]-(0 if private else 12));self.assertEqual(flags,0x9800001f)

    def test_secondary_keeps_owned_navigation_without_eating_hurt_or_stale_actors(self):
        at=0x2160000;slots=0x2170000;ctl=0x2200000;actor=0x2210000;end=0x3000000;cfg=0x215b114
        cases=((5,-4,cfg,0x7fffffff),(7,-5,cfg,0x7fffffff),(5,18,cfg,5),(28,18,cfg,0x7fffffff),(37,-4,cfg,37),(38,-5,cfg,38),(53,-4,cfg,53),(5,-4,0x2136880,5))
        for native,cooldown,actual,wanted in cases:
            p=ArmProbe();p.code(at,c.secondary(at,slots,(cfg,0x215b050)))
            for i,v in enumerate((ctl,actor,cfg,0,cooldown,0,1,0)):p.put(slots+i*4,v)
            p.put(ctl+0x44,actor);p.put(actor+0x40,actual);p.put(actor+0x44,100)
            regs=self.regs(at,end);regs[0]=ctl
            def think(probe,rr,flags):rr[0]=native;return flags
            out,_,_=p.run(regs,0x9800001f,{end},{0x2095a78:think})
            self.assertEqual(out[0],wanted);self.assertEqual(out[4:14],regs[4:14])

    def test_world_models_select_saved_or_scalar_state_and_keep_abi(self):
        at=0x2160000;table=0x2170000;old=0x2158000;end=0x3000000;stats=0x2210000;manager=0x2220000
        for room,kind,flag,on in ((81,0x13,245,0),(81,0x13,245,1),(106,0x13,0x12f,0),(106,0x13,0x12f,1),(75,0x13,245,1),(81,0x11,245,1)):
            p=ArmProbe();p.code(at,c.world_data(at,table,old));p.put(0x2145c5c,stats);p.put(stats,room);p.put(0x2145c34,manager)
            row_room=81 if flag==245 else 106
            p.code(table,struct.pack('<10I',row_room,0x13,flag,0x2171000,0x2171040,0,0,0,0,0))
            if flag<0x123:p.memory[stats+0x1c+flag//8]=on<<(flag%8)
            else:p.memory[manager+flag+0x99]=on
            regs=self.regs(at,end);regs[1]=kind
            stops={end,old};out,flags,pc=p.run(regs,0x9800001f,stops)
            if room==row_room and kind==0x13:self.assertEqual(p.get(regs[0]),0x2171040 if on else 0x2171000);self.assertEqual(pc,end)
            else:self.assertEqual(pc,old)
            self.assertEqual(out[:15],regs[:15]);self.assertEqual(flags,0x9800001f)

    def test_contextual_roster_keeps_native_fallback_and_resets_between_rooms(self):
        at=0x2160000;table=0x2170000;pattern=0x2170100;state=0x2170200;old=0x2158000;end=0x3000000;stats=0x2210000
        p=ArmProbe();p.code(at,c.variant(at,table,state,old));p.code(table,struct.pack('<6I',78,pattern,3,0,0,0));p.code(pattern,bytes((21,36,20)))
        p.put(state,0xffffffff);p.put(state+4,0);p.put(0x2145c5c,stats);p.put(stats,78);regs=self.regs(at,end)
        for wanted in (21,36,20,21):
            out,flags,pc=p.run(regs,0x6800001f,{end,old});self.assertEqual(p.get(regs[0]),wanted);self.assertEqual(out[:15],regs[:15]);self.assertEqual(flags,0x6800001f)
        p.put(stats,75);out,_,pc=p.run(regs,0x6800001f,{end,old});self.assertEqual(pc,old)

    def test_core_phase_comes_from_real_post_damage_hp_and_retains_return(self):
        at=0x2160000;old=0x2158000;end=0x3000000;actor=0x2200000;stats=0x2210000;manager=0x2220000
        for room,kind,hp,changed in ((106,0x21,18*4096,True),(106,0x21,19*4096,False),(106,0x21,0,False),(105,0x21,4*4096,False),(106,0x13,4*4096,False)):
            p=ArmProbe();p.code(at,c.core_phase(at,old));p.put(actor,0x212f7a0);p.put(actor+0x10c,kind);p.put(actor+0x110,36*4096)
            p.put(0x2145c5c,stats);p.put(stats,room);p.put(0x2145c34,manager);p.memory[manager+0x1c8]=0
            regs=self.regs(at,end)
            def native(probe,rr,ff):probe.put(actor+0x110,hp);rr[0]=0x1234;return 0xf800001f
            out,flags,_=p.run(regs,0x8000001f,{end},{old:native})
            self.assertEqual(p.memory[manager+0x1c8],int(changed));self.assertEqual(out[0],0x1234);self.assertEqual(flags,0xf800001f)
            self.assertEqual(out[4:14],regs[4:14])

class ChapterContracts(unittest.TestCase):
    def test_contextual_heavy_commit_has_a_reachable_engagement_window(self):
        from tools import creature_forge_design as design
        for style in ('ballast','warden'):
            self.assertGreater(design.MOVES[style][2].reach,c.HEAVY_APPROACH)
    def test_no_roster_uses_unowned_species_or_infinite_budgets(self):
        self.assertEqual(set(r.ROSTERS),set(r.BUDGETS))
        for i,seq in r.ROSTERS.items():
            self.assertTrue(set(seq)<={20,21,36});total,live=r.BUDGETS[i];self.assertLessEqual(live,total);self.assertLessEqual(live,4)
        self.assertEqual(r.BUDGETS[89],(2,2));self.assertEqual(r.BUDGETS[106],(1,1))

    def test_terminal_has_open_ground_and_real_visible_roof_geometry(self):
        import mod
        from tools import wos_tool as w,room_collision
        _,g,_=mod.load_clean();off,names,_=w.parse_glob(g)
        def native(n):i=names.index(n);return g[off[i]:off[i+1]]
        plan=r.geometry(78,native);tree=room_collision.RoomCollision.parse(__import__('tools.room_compiler',fromlist=['compile_room']).compile_room(plan).collision)
        for x in (90,180,260):self.assertIsNone(tree.solid_at(x,8));self.assertIsNotNone(tree.solid_at(x,23));self.assertIsNone(tree.solid_at(x,30))

if __name__=='__main__':unittest.main()
