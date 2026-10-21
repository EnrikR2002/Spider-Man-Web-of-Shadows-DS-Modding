import struct,unittest
from tools import chapter_renewal_rooms as r,chapter_renewal_combat as c,chapter_renewal_motion as m
from tools import midnight_chapter as ch,room_compiler as rc

class CircuitTests(unittest.TestCase):
    def test_compact_reciprocal_graph_and_arrivals(self):
        self.assertEqual(len(r.ACTIVE),10)
        visited={76};todo=[76]
        while todo:
            i=todo.pop()
            for g,port in enumerate(r.doors(i),1):
                dest,spawn=r.LINKS[r.BY_ID[i],g]
                if dest==ch.ENTRANCE:continue
                j=ch.BY_NAME[dest].index
                reverse=next(g for g,d in enumerate(r.doors(j),1) if d.spawn_id==spawn)
                self.assertEqual(r.LINKS[dest,reverse],(r.BY_ID[i],port.spawn_id))
                if j not in visited:visited.add(j);todo.append(j)
        self.assertEqual(visited,set(r.ACTIVE))

    def test_old_save_rooms_reach_active_circuit(self):
        for i in range(76,96):
            if i not in r.ACTIVE:
                dest,_=r.LINKS[r.BY_ID[i],1]
                self.assertIn(ch.BY_NAME[dest].index,r.ACTIVE)
                self.assertIn(i,ch.BY_INDEX if hasattr(ch,'BY_INDEX') else range(76,96))

    def test_visible_roofs_and_clear_shutter_approaches(self):
        for i in r.ACTIVE:
            room=r.geometry(i);self.assertNotIn('above',room.hidden_shell)
            for d in r.doors(i):
                for distance in (5,10,15):
                    x=d.wall+(distance if d.side=='left' else -distance)
                    self.assertFalse(any(q.x0<x<q.x1 and q.y0<d.floor+6<q.y1 for q in room.solids),(i,d,x))

    def test_architectural_landmarks_are_in_front_of_background_walls(self):
        for index in (81,83):
            room=r.geometry(index)
            self.assertTrue(all(p.look is None for p in room.panels),'Native z=-25 panels hide the machinery')
            background=[q for q in room.scenery if q.look.texture=='MLStone']
            landmark=[q for q in room.scenery if q.look.texture=='MLCyan']
            self.assertTrue(background and landmark)
            self.assertLess(max(v[2] for q in background for v in q.corners),min(v[2] for q in landmark for v in q.corners))

class RuntimeTests(unittest.TestCase):
    def test_player_observer_preserves_arguments_flags_and_native_stack(self):
        from tests.arm_runtime import ArmProbe
        at=0x2160000;controller=0x2210000;hero=0x2163000;owner=0x2220000
        for vtable in (0x21352a4,0x2133368):
            p=ArmProbe();p.code(at,c.capture_hero(at,hero));p.put(controller,vtable);p.put(controller+0x44,owner);p.put(hero,0)
            regs=[controller,1,2,3,4,5,6,7,8,9,10,11,12,0x23ff000,0x3000000,at]
            out,flags,pc=p.run(regs,0xf800001f,{0x20776c0})
            self.assertEqual(out[:13],regs[:13]);self.assertEqual(flags,0xf800001f);self.assertEqual(out[13],regs[13]-8)
            self.assertEqual(p.get(hero),owner if vtable==0x21352a4 else 0)

    def test_voice_filter_is_scoped_and_keeps_all_other_sound_arguments(self):
        from tests.arm_runtime import ArmProbe
        at=0x2160000;old=0x215a000;stats=0x2210000
        for room in (0,75,76,89,96,107,108):
            for sound in (188,306,328,457,501,582,616,617,651):
                p=ArmProbe();p.code(at,c.sound_filter(at,old));p.put(0x2145c5c,stats);p.put(stats,room)
                regs=[0x2200000,sound,20,0,4,5,6,7,8,9,10,11,12,0x23ff000,0x3000000,at]
                out,flags,pc=p.run(regs,0xf800001f,{old})
                mute=76<=room<108 and (306<=sound<=328 or 457<=sound<=501 or 582<=sound<=616)
                self.assertEqual(out[1],652 if mute else sound);self.assertEqual(out[0],regs[0]);self.assertEqual(out[2:15],regs[2:15]);self.assertEqual(flags,0xf800001f)

    def test_private_compaction_preserves_every_sample(self):
        import mod
        from tools import wos_tool as w
        from tools.sca import Sca
        from tools.sca_author import sample
        _,g,_=mod.load_clean();o,n,_=w.parse_glob(g)
        for name in ('brt_HurtKnockDown.sca','hLpr_LeapAttack.sca','hm_HurtLandGetUp.sca','hRng_Idle.sca'):
            i=n.index(name);a=Sca.parse(g[o[i]:o[i+1]]);raw=m.compact_private(a.to_bytes());b=Sca.parse(raw)
            self.assertLessEqual(len(raw),len(a.to_bytes()))
            for j in range(a.joint_count):
                for f in range(a.frame_count):
                    for channel in ('translation','rotation','scale'):self.assertEqual(sample(a,j,f,channel),sample(b,j,f,channel))

    def test_loader_retains_native_cache_tail_and_fits(self):
        code=c.loader();self.assertEqual(len(code),0x58)
        self.assertEqual(struct.unpack_from('<7I',code,60)[:3],(0xEE077F9A,0xEE074F35,0xEE074F3E))

    def test_species_patterns_are_distinct_and_executable(self):
        self.assertEqual(len(set(c.PATTERNS.values())),7)
        for sequence in c.PATTERNS.values():
            for action,state,recovery in sequence:
                self.assertIn(action,(55,63,71,121));self.assertEqual(state,16 if action==71 else 15);self.assertGreater(recovery,0)
        self.assertGreater(len(c.think(0x2160000,0x2161000,0x2161100,0x2162000)),300)
        self.assertGreater(len(c.enter(0x2160000,0x2161000,0x2161100,0x2162000)),250)

    def test_lifecycle_routes_include_prone_rise_and_launch(self):
        expected={'HurtKnockDown':'knockdown','HurtLand':'prone','HurtLandGetUp':'rise','HurtKnockUp':'launch','HurtFall':'tumble','Die':'death'}
        for name,mode in expected.items():self.assertEqual(m.mode('hm_'+name+'.sca'),mode)

    def test_actor_actions_roundtrip_and_no_idle_fallback_attacks(self):
        import mod
        from tools import wos_tool as w
        from tools.actor_actions import ActorActions
        _,g,_=mod.load_clean();o,n,_=w.parse_glob(g)
        for style,stem in zip(m.STYLES,('hLpr','brt','hRng','hLpr','brt','hRng','brt')):
            i=n.index(stem+'.xbd');raw=g[o[i]:o[i+1]];a=ActorActions.parse(raw,n);self.assertEqual(a.to_bytes(),raw)
            self.assertIsNone(a.lookup(64))
            for action,_,_ in c.PATTERNS[style]:
                row=a.lookup(action);self.assertIsNotNone(row)
                self.assertTrue(any('Attack' in b['name'] and b['tag']==0 for b in row.bindings))

    def test_all_voices_differ_and_have_pcm_payload(self):
        waves=[c.voice(i,j) for i in range(7) for j in range(5)]
        self.assertEqual(len(set(waves)),35)
        self.assertTrue(all(len(x)>1000 and struct.unpack_from('<I',x,8)[0]*4==len(x)-12 for x in waves))

if __name__=='__main__':unittest.main()
