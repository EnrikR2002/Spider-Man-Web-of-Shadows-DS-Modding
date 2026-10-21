"""Contact-activation regression, owner-scoped audio and native sloping BSPs."""
import struct,unittest
from pathlib import Path
from tools import midnight_rebuild as rebuild,midnight_enemy_combat as audio
from tools import midnight_enemy_motion as motion,room_envelope as envelope,room_collision as collision
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob


class ContactRegression(unittest.TestCase):
    def test_the_authored_window_replaces_unrelated_native_active_bits(self):
        n=12;records=[struct.pack('<8i',0,12000,16000,8000,9000,int(i in (2,3)),777,8192) for i in range(n)]
        body=struct.pack('<4H',0,n,1,9)+struct.pack('<hH',3,15)+b''.join(records)
        # Use the established deterministic wrapper writer on one native GMB.
        import mod
        from tools import wos_tool as w
        _,g,_=mod.load_clean();o,names,_=w.parse_glob(g);i=names.index('brt_GroundRangedAttack1.gmb')
        wrap=CompressedBlob.parse(g[o[i]:o[i+1]]);raw=wrap.replace_decoded(body,compact=True)
        updated=Gmb.parse(CompressedBlob.parse(rebuild.align_contacts(raw,((6,9),))).decoded)
        self.assertEqual([i for i in range(n) if updated.channels[0].words(i)[5]],[6,7,8])
        for i in range(n):
            expected=list(struct.unpack('<8i',records[i]));expected[5]=int(6<=i<9)
            self.assertEqual(updated.channels[0].words(i),tuple(expected))

    def test_previously_harmless_native_ranged_slots_become_real_contacts(self):
        import mod
        from tools import wos_tool as w
        from tools.animation_rig import AnimationRig
        from tools.actor_actions import ActorActions
        from tools.sca import Sca
        _,g,_=mod.load_clean();o,names,_=w.parse_glob(g)
        def blob(n):i=names.index(n);return g[o[i]:o[i+1]]
        for style in ('warden','ballast','conductor'):
            move=motion.MOVES[style][2];source='brt_GroundRangedAttack1.gmb'
            idle=Sca.parse(blob('brt_Idle.sca'));parents=AnimationRig.parse(blob('brt.nsbmd')).parents
            poses=[motion.pose(idle,parents,style,'brt','GroundRangedAttack1',f,move.samples,move) for f in range(move.samples)]
            updated=Gmb.parse(CompressedBlob.parse(motion.geometry(blob(source),poses,move,style)).decoded)
            attack=next(c for c in updated.channels if c.kind==3 and c.words(0)[7]==8192)
            self.assertEqual([f for f in range(updated.record_count) if attack.words(f)[5]],[f for a,b in move.contacts for f in range(a,b)])
            self.assertEqual(updated.record_count,move.samples)

    def test_selected_programs_use_native_damaging_carrier_bindings(self):
        import mod
        from tools import wos_tool as w
        from tools.actor_actions import ActorActions
        from tools.creature_forge_design import STYLES,STEMS
        _,g,_=mod.load_clean();o,names,_=w.parse_glob(g)
        def blob(n):i=names.index(n);return g[o[i]:o[i+1]]
        for style,stem in zip(STYLES,STEMS):
            actions=ActorActions.parse(blob(stem+'.xbd'),names)
            for move in motion.MOVES[style]:
                action=actions.lookup(move.action);self.assertIsNotNone(action)
                source=next(b['name'] for b in action.bindings if b['tag']==3)
                geom=Gmb.parse(CompressedBlob.parse(blob(source)).decoded)
                self.assertTrue(any(c.kind==3 and c.words(0)[7]==8192 and any(c.words(f)[5] for f in range(geom.record_count)) for c in geom.channels),(style,move.name,move.action))


class NativeEnvelope(unittest.TestCase):
    def test_sloping_floor_and_ceiling_share_a_single_lossless_tree(self):
        inf=collision.INF
        raw=collision.compile_boxes([(-inf,-inf,0,inf),(100,-inf,inf,inf),(0,-inf,100,-8),(0,80,100,inf)])
        poly=((0,0),(20,-8),(80,-8),(100,0),(100,24),(76,80),(24,80),(0,24))
        modified=envelope.collision_bytes(raw,poly);tree=collision.RoomCollision.parse(modified);tree.check_tree()
        self.assertEqual(tree.to_bytes(),modified)
        for x,y,solid in ((50,10,False),(10,0,False),(10,-6,True),(4,60,True),(96,60,True),(50,70,False),(90,-6,True)):
            self.assertEqual(tree.solid_at(x,y) is not None,solid,(x,y))
        self.assertIsNotNone(tree.solid_at(50,10,26));self.assertIsNone(tree.solid_at(50,10,0))
        self.assertAlmostEqual(tree.floor_below(10,10),-4,delta=.26)

    def test_concave_boundary_is_rejected_instead_of_silently_clipped(self):
        with self.assertRaises(ValueError):envelope.planes(((0,0),(100,0),(100,40),(40,40),(40,80),(0,80)))


class PhysicalMotion(unittest.TestCase):
    def test_heavy_downstrokes_reach_the_floor_with_planted_feet(self):
        import mod
        from tools import wos_tool as w
        from tools.sca import Sca
        from tools.animation_rig import AnimationRig
        _,g,_=mod.load_clean();o,names,_=w.parse_glob(g)
        def blob(n):i=names.index(n);return g[o[i]:o[i+1]]
        idle=Sca.parse(blob('brt_Idle.sca'));parents=AnimationRig.parse(blob('brt.nsbmd')).parents
        for style,half_height in (('warden',1.4),('ballast',1.0)):
            move=motion.MOVES[style][1];p=motion.pose(idle,parents,style,'brt','attack',move.contacts[0][0],move.samples,move);_,points=p.fk()
            feet=(points[22][1]+points[26][1])/2;fist_bottom=points[8][1]-.1-half_height
            self.assertLess(abs(fist_bottom-feet),.35)
            self.assertLess(abs(points[22][1]-points[26][1]),.05)

    def test_whole_actions_return_to_the_neutral_pose_without_a_body_snap(self):
        import mod
        from tools import wos_tool as w
        from tools.sca import Sca
        from tools.animation_rig import AnimationRig
        from tools.creature_forge_design import STYLES,STEMS
        _,g,_=mod.load_clean();o,names,_=w.parse_glob(g)
        def blob(n):i=names.index(n);return g[o[i]:o[i+1]]
        for style,stem in zip(STYLES,STEMS):
            idle=Sca.parse(blob(stem+'_Idle.sca'));parents=AnimationRig.parse(blob(stem+'.nsbmd')).parents;neutral=motion.pose(idle,parents,style,stem,'Idle',0,40)
            for move in motion.MOVES[style]:
                for f in (0,move.samples-1):
                    pose=motion.pose(idle,parents,style,stem,'attack',f,move.samples,move)
                    for j in range(23):
                        self.assertLess(max(abs(a-b) for a,b in zip(pose.t[j],neutral.t[j])),.08,(style,move.name,f,j))
                        self.assertLess(max(abs(a-b) for ra,rb in zip(pose.r[j],neutral.r[j]) for a,b in zip(ra,rb)),.035,(style,move.name,f,j))


class SoundOwnership(unittest.TestCase):
    def test_grounded_attack_gate_waits_for_the_native_landing(self):
        from tests.arm_runtime import ArmProbe
        at=0x2180000;selected=0x2171000;walk=0x2172000;ctl=0x2210000;actor=0x2211000
        for flags,state,vy,allowed in ((0x2c2,0,0,True),(0x242,5,8000,False),(0x2c2,5,0,False),(0x242,1,0,False),(0x2c2,1,-100,False)):
            p=ArmProbe();p.code(at,audio.attack_gate(at,selected,walk));p.put(ctl+0x14,state);p.put(actor+0x10,flags);p.put(actor+0x1c,vy)
            regs=[1,3,2,3,ctl,5,actor,7,8,9,10,11,12,0x23ff000,0x3000000,at]
            out,_,_=p.run(regs,0x8000001f,{selected+4,walk})
            self.assertEqual(out[15],selected+4 if allowed else walk)
            self.assertEqual(out[:3],regs[:3]);self.assertEqual(out[4:15],regs[4:15])

    def test_only_exact_creatures_replace_their_queued_stock_events(self):
        from tests.arm_runtime import ArmProbe
        at=0x2180000;configs=0x2181000;play=0x2182000;stats=0x2200000;actor=0x2210000;mot=0x2211000;end=0x3000000
        for room,owner,config,back,action in ((78,0x21301d0,333,True,55),(78,0x21301d0,333,True,158),
            (78,0x212e3f0,333,True,55),(78,0x21301d0,444,True,55),(75,0x21301d0,333,True,55),(78,0x21301d0,333,False,55)):
            p=ArmProbe();p.code(at,audio.spatial(at,configs,play,719));p.put(0x2145c5c,stats);p.put(stats,room)
            for i in range(7):p.put(configs+i*4,333 if i==3 else 999+i)
            p.put(actor,owner);p.put(actor+0x40,config);p.put(actor+0x30,mot);p.put(mot,actor if back else 1);p.put(mot+0x254,action)
            pointer=0x2220000;p.put(pointer,10);calls=[];voices=[]
            regs=[0x2221000,pointer,1,3,4,5,6,actor,8,9,10,11,12,0x23ff000,end,at]
            def native(p,r,f):calls.append((r[0],p.get(r[1]),r[2]));return f
            def sound(p,r,f):voices.append(r[0]);r[0]=0;r[1]=99;r[2]=100;r[3]=101;return f
            out,flags,_=p.run(regs,0xa000001f,{end},{0x205e6a8:native,play:sound})
            owned=room==78 and owner==0x21301d0 and config==333 and back
            self.assertEqual(calls,[(regs[0],652 if owned else 10,1)])
            self.assertEqual(voices,[738] if owned and action==158 else [])
            self.assertEqual(out[4:12],regs[4:12]);self.assertEqual(out[13],regs[13]);self.assertEqual(p.get(pointer),10)

    def test_bank_remap_preserves_native_outside_the_private_range_and_rooms(self):
        from tests.arm_runtime import ArmProbe
        for room in (75,76,107,108):
            for sound in (129,652,653,709,710,719,775):
                p=ArmProbe();at=0x2180000;old=0x2170000;stats=0x2200000
                p.code(at,audio.voice_bank(at,old,719));p.put(0x2145c5c,stats);p.put(stats,room)
                regs=[0x2220000,sound,20,0,4,5,6,7,8,9,10,11,12,0x23ff000,0x3000000,at]
                out,flags,_=p.run(regs,0xf800001f,{old})
                self.assertEqual(out[1],sound+66 if 76<=room<108 and 653<=sound<710 else sound)
                self.assertEqual(out[0],regs[0]);self.assertEqual(out[2:15],regs[2:15]);self.assertEqual(flags,0xf800001f)

    def test_fall_and_landing_transitions_do_not_repeat_the_impact_vocal(self):
        from tests.arm_runtime import ArmProbe
        for state in (37,41,48,49,50):
            p=ArmProbe();at=0x2180000;old=0x2170000;stats=0x2200000
            p.code(at,audio.voice_bank(at,old,719));p.put(0x2145c5c,stats);p.put(stats,78)
            regs=[0x2220000,671,20,0,4,state,6,7,8,9,10,11,12,0x23ff000,0x3000000,at]
            out,_,_=p.run(regs,0xf800001f,{old})
            self.assertEqual(out[1],652 if state>=48 else 737)


if __name__=='__main__':unittest.main()
