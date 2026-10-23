"""Native ownership/ABI, stale actors, physical pursuit and mesh isolation."""
import struct
import unittest
from types import SimpleNamespace

from tests.arm_runtime import ArmProbe
from tools import hunters_return as h, tasm_kit as kit, spider2099_visual as visual, oscorp_resources
from tools import spider2099_art as art, hunters_return_motion as motion
from tools.animation_rig import AnimationRig
from tools.model_geometry import ModelGeometry


class HunterRuntime(unittest.TestCase):
    at=0x021a0100; state=0x021a0000; native=0x021b0000; end=0x03000000
    hero=0x02200000; ctl=0x02201000; mot=0x02202000; stats=0x02203000
    enemy=0x02210000; em=0x02211000; config=0x02212000
    values=dict(STATE=state,NATIVE_TRANSITION=native,OLD_CONTACT=0x02152c50,
        OLD_EVADE_GENERIC=0x02152c20,OLD_EVADE_STRING=0x02152c24,
        PULL_SCA=6000,RAKE_SCA=6001,RAKE_GMB=6002,RAKE_GAB=3355)

    def fixture(self,phase=0,form=1,owned=True):
        p=ArmProbe();p.code(self.at,h.runtime(self.at,self.values))
        for off in range(0,64,4):p.put(self.state+off,0)
        for at,v in ((self.hero,0x0212e3f0),(self.hero+0x34,form),(self.hero+0x30,self.mot),
            (self.hero+0xe8,self.stats+12),(self.stats,65),(self.stats+12,(1<<20) if owned else 0),
            (self.ctl+0x14,44),(self.ctl+0x44,self.hero),(self.ctl+0x64,0x400),
            (self.ctl+0x4c,self.enemy+4),(self.ctl+0x80,0),(self.mot,self.hero),
            (self.mot+0x1f8,self.ctl),(self.mot+0x178,0),(self.mot+0x254,50),(self.mot+0x258,50),
            (self.enemy+0x30,self.em),(self.enemy+0x40,self.config),(self.enemy+0x44,32768)):
            p.put(at,v)
        for m,x in ((self.mot,0),(self.em,10*4096)):
            for off,v in ((0x7c,x),(0x80,0),(0x160,0),(0x164,0)):p.put(m+off,v)
        if phase:
            for off,v in ((0,self.hero),(4,self.ctl),(8,self.enemy),(12,self.em),(16,self.config),(20,phase),(28,65)):
                p.put(self.state+off,v)
        return p

    def run_entry(self,p,entry=0,stubs=None,stops=None,regs=None,flags=0xa000001f):
        r=list(range(100,116)) if regs is None else list(regs)
        r[13]=0x023f0000;r[14]=self.end;r[15]=self.at+entry
        before=list(r)
        out,c,pc=p.run(r,flags,stops or {self.end},stubs)
        return before,out,c,pc

    @staticmethod
    def result(value):
        def stub(p,r,c):r[0]=value;return c
        return stub

    def transition(self,p,native=42,live=True,queued=True,keys=0):
        consumed=[]
        def consume(p,r,c):consumed.append(p.get(r[1]));return c
        stubs={self.native:self.result(native),0x02152c68:self.result(int(live)),
            0x02152c5c:self.result(keys),0x020cff0c:self.result(int(queued)),0x020cfc34:consume}
        r=list(range(16));r[0]=self.ctl
        before,out,_,_=self.run_entry(p,stubs=stubs,regs=r)
        self.assertEqual(out[4:12],before[4:12]);self.assertEqual(out[13],before[13])
        return out[0],consumed

    def test_native_recall_arms_only_owned_black_after_actual_dash_contact(self):
        p=self.fixture();self.assertEqual(self.transition(p),(42,[]));self.assertEqual(p.get(self.state+20),1)
        for kwargs in ({'form':0},{'owned':False}):
            p=self.fixture(**kwargs);self.transition(p);self.assertEqual(p.get(self.state+20),0)
        for off,v in ((0x14,46),(0x64,0),(0x4c,0)):
            p=self.fixture();p.put(self.ctl+off,v);self.transition(p);self.assertEqual(p.get(self.state+20),0)
        p=self.fixture();self.transition(p,live=False);self.assertEqual(p.get(self.state+20),0)

    def test_resistant_fallback_requires_fresh_target_new_a_and_neutral_traversal(self):
        p=self.fixture();self.assertEqual(self.transition(p,native=0x7fffffff),(46,[5]))
        self.assertEqual(p.get(self.state+20),2)
        for changes in ({'live':False},{'queued':False},{'keys':0x40},{'keys':0x80},{'keys':0x100}):
            p=self.fixture();self.transition(p,native=0x7fffffff,**changes);self.assertEqual(p.get(self.state+20),0)
        for field,value in ((0x7c,25*4096),(0x80,6*4096)):
            p=self.fixture();p.put(self.em+field,value);self.transition(p,native=0x7fffffff)
            self.assertEqual(p.get(self.state+20),0)

    def test_launch_changes_only_the_recalled_target_contact_and_preserves_abi(self):
        for phase,form,live,other,changed in ((1,1,True,False,True),(2,1,True,False,False),
                (1,0,True,False,False),(1,1,False,False,False),(1,1,True,True,False)):
            with self.subTest(phase=phase,form=form,live=live,other=other):
                p=self.fixture(phase,form);p.put(self.ctl+0x14,43)
                info=0x02220000;contact=info+64;cell=info+96
                for off in range(0,96,4):p.put(info+off,0)
                p.put(info,0x20);p.put(info+4,0xc00);p.put(info+16,contact);p.put(contact+20,0x20);p.put(cell,self.hero)
                r=list(range(16));r[1]=self.enemy+8+(4 if other else 0);r[2]=cell;r[3]=info
                before,out,c,_=self.run_entry(p,8,regs=r,stops={self.values['OLD_CONTACT']},
                    stubs={0x02152c68:self.result(int(live))})
                self.assertEqual(out[:15],before[:15]);self.assertEqual(c,0xa000001f)
                self.assertEqual(p.get(info),0x25 if changed else 0x20)
                self.assertEqual(p.get(contact+20),p.get(info));self.assertEqual(p.get(info+4),0xc00)

    def test_pursuit_writes_velocity_only_and_uses_native_collision_position(self):
        for side in (-1,1):
            p=self.fixture(2);p.put(self.ctl+0x14,46);p.put(self.ctl+0x80,5);p.put(self.em+0x7c,side*10*4096)
            r=list(range(16));r[4]=self.hero
            before,out,c,_=self.run_entry(p,12,regs=r,stops={0x02073b64},stubs={0x02152c68:self.result(1),0x02152c60:self.result(0)})
            self.assertEqual(p.get(self.hero+0x18),side*8192&0xffffffff)
            self.assertEqual(p.get(self.mot+0x7c),0);self.assertEqual(p.get(self.em+0x7c),side*40960&0xffffffff)
            self.assertEqual(out[:15],before[:15]);self.assertEqual(c,0xa000001f)

    def test_stale_actor_recycled_motion_form_room_and_native_interrupt_clear_private_state(self):
        for reason in ('stale','motion','config','form','room','hurt','dodge'):
            p=self.fixture(1);p.put(self.ctl+0x14,42);p.put(self.hero+0x18,1234)
            if reason=='stale':p.put(self.state+8,0x02312340)
            if reason=='motion':p.put(self.state+12,self.em+4)
            if reason=='config':p.put(self.state+16,self.config+4)
            if reason=='form':p.put(self.hero+0x34,0)
            if reason=='room':p.put(self.stats,66)
            if reason in ('hurt','dodge'):p.put(self.ctl+0x14,63 if reason=='hurt' else 53)
            r=list(range(16));r[4]=self.hero
            self.run_entry(p,12,regs=r,stops={0x02073b64},stubs={0x02152c68:self.result(0 if reason=='stale' else 1)})
            self.assertEqual(p.get(self.state+20),0);self.assertEqual(p.get(self.hero+0x18),1234)

    def test_r_uses_the_native_evade_transition_and_keeps_caller_stack(self):
        for entry,old in ((16,'OLD_EVADE_GENERIC'),(20,'OLD_EVADE_STRING')):
            for queued in (0,1):
                p=self.fixture(1);r=list(range(16));r[8]=self.ctl
                stack=0x023f0000
                for i,value in enumerate((44,45,46,47,48,self.end)):p.put(stack+0x58+i*4,value)
                before,out,_,pc=self.run_entry(p,entry,regs=r,stops={self.end,self.values[old]},
                    stubs={0x020cff0c:self.result(queued)})
                self.assertEqual(pc,self.end if queued else self.values[old])
                self.assertEqual(out[13],stack+0x70 if queued else stack)
                if queued:self.assertEqual(out[0],0x7fffffff)

    def test_animation_route_is_private_to_owned_black_and_the_active_native_phase(self):
        for phase,form,state,action,take in ((1,1,42,49,6000),(1,1,43,50,6001),
                (2,1,46,55,6001),(1,0,43,50,None),(1,1,53,50,None),(2,1,46,63,None)):
            p=self.fixture(phase,form);p.put(self.ctl+0x14,state);p.put(self.ctl+0x80,5)
            p.put(self.mot+0x258,action)
            record=0x023f0000+0x2c
            for i in range(6):p.put(record+i*4,100+i)
            r=list(range(16));r[0]=1;r[4]=self.mot
            before,out,_,_=self.run_entry(p,4,regs=r,stops={0x02070488})
            self.assertEqual(out[:15],before[:15])
            self.assertEqual(p.get(record),100 if take is None else take)
            if take==6001:self.assertEqual((p.get(record+12),p.get(record+16)),(6002,3355))
            else:self.assertEqual((p.get(record+12),p.get(record+16)),(103,104))


class Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=h.PARENT_PATH.read_bytes();cls.result,cls.report=h.apply_rom(cls.parent)
        cls.names,cls.before=h.assets.resources(cls.parent);cls.nn,cls.after=h.assets.resources(cls.result)

    def test_only_expected_resources_and_six_native_hooks_change(self):
        self.assertEqual(self.names,self.nn[:len(self.names)])
        changed={n for n,a,b in zip(self.names,self.before,self.after) if a!=b}
        self.assertEqual(changed,{'American.strings','English.strings','spd.nsbmd','GlobFiles.txt'})
        a,b=h.w.parse_header(self.parent),h.w.parse_header(self.result)
        aa=self.parent[a['arm9_offset']:a['arm9_offset']+a['arm9_size']]
        bb=self.result[b['arm9_offset']:b['arm9_offset']+b['arm9_size']]
        self.assertEqual(aa[kit.SOURCE:kit.SOURCE+kit.RESERVE],bb[kit.SOURCE:kit.SOURCE+kit.RESERVE])
        self.assertEqual(aa[0x120340:0x120500],bb[0x120340:0x120500])
        changed_words={i for i in range(0,len(aa)-36,4) if aa[i:i+4]!=bb[i:i+4]}
        allowed={x-0x02000000 for x in self.report['runtime']['hooks']}
        allowed.update((kit.TABLE_POINTERS,kit.TABLE_POINTERS+4,kit.ARENA_LOWER,h.w.u32(aa,kit.TABLE_POINTERS)-0x02000000))
        allowed.add(h.w.u32(aa,kit.TABLE_POINTERS)-0x02000000+4)
        allowed.add(h.w.u32(aa,kit.TABLE_POINTERS)-0x02000000+8)
        allowed.add(oscorp_resources.COUNT_OFFSET)
        self.assertLessEqual(changed_words,allowed)
        for e in h.w.nitrofs_entries(self.result):
            if e['name']=='Glob.bin':continue
            old=next(x for x in h.w.nitrofs_entries(self.parent) if x['name']==e['name'])
            self.assertEqual(self.result[e['start']:e['end']],self.parent[old['start']:old['end']])

    def test_rig_uv_counts_red_stream_and_selector_footer_are_exact(self):
        old=self.before[self.names.index('spd.nsbmd')];new=self.after[self.nn.index('spd.nsbmd')]
        a,b=AnimationRig.parse(old),AnimationRig.parse(new)
        self.assertEqual((a.names,a.parents,a.node_records),(b.names,b.parents,b.node_records))
        self.assertEqual(old[-64:],new[-64:])
        a,b=ModelGeometry.parse(old),ModelGeometry.parse(new)
        self.assertEqual(old[a.shapes[0].start:a.shapes[0].start+a.shapes[0].length],new[b.shapes[0].start:b.shapes[0].start+b.shapes[0].length])
        old_faces,new_faces=art.mesh(visual.selected_model(old,1)),art.mesh(visual.selected_model(new,1))
        self.assertEqual(len(new_faces),516)
        self.assertEqual([(v.slot,v.uv) for f in old_faces for v in f],[(v.slot,v.uv) for f in new_faces for v in f])
        self.assertGreater(max(v.position[2] for f in new_faces for v in f if 7<v.position[1]<8),max(v.position[2] for f in old_faces for v in f if 7<v.position[1]<8))

    def test_pull_flows_into_rake_without_a_pose_reset(self):
        for channel in motion.PULL.CHANNELS:
            self.assertEqual(motion.PULL.value(channel,9),motion.RAKE.value(channel,0),channel)

    def test_wrong_parent_is_rejected_before_any_output(self):
        with self.assertRaisesRegex(ValueError,'exact published'):h.apply_rom(b'not a ROM')


class LabOutput(unittest.TestCase):
    def test_research_output_cannot_reach_original_or_the_real_battery(self):
        from tools import hunters_return_lab
        with self.assertRaisesRegex(ValueError,'stay in work'):
            hunters_return_lab.run(SimpleNamespace(out=h.ROOT/'original'))


if __name__=='__main__':unittest.main()
