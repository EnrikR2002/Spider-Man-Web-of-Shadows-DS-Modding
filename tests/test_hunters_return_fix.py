"""Victim-loop isolation, nested/ignored hits and replaced player ownership."""
import json
import unittest

from tests import test_hunters_return as legacy
from tools import hunters_return_fix as fix,wos_tool as w,tasm_kit as kit


class Runtime(unittest.TestCase):
    at=0x021c0000
    sp=0x023f0000
    contact=0x02220000
    cell=0x02220100
    outlist=0x02220200

    @classmethod
    def setUpClass(cls):
        cls.old=legacy.HunterRuntime()
        cls.values=dict(fix.old_symbols(cls.old.at,cls.old.values),STATE=cls.old.state,OLD_CONTACT=cls.old.values['OLD_CONTACT'])
        cls.code=fix.runtime(cls.at,cls.values)

    def fixture(self,phase=1):
        p=self.old.fixture(phase);p.code(self.at,self.code);p.put(self.old.ctl+0x14,43)
        self.hit(p,self.sp,self.contact)
        p.put(self.cell,self.old.hero)
        return p

    def hit(self,p,sp,contact):
        p.put(sp,0x1800);p.put(sp+4,self.outlist)
        p.put(sp+0x80,self.outlist);p.put(sp+0x84,self.old.hero);p.put(sp+0x88,0x02220300)
        for off in range(0,64,4):p.put(sp+0x8c+off,0)
        p.put(sp+0x8c,0x20);p.put(sp+0x90,0xc00);p.put(sp+0x9c,contact)
        for off in range(0,32,4):p.put(contact+off,0)
        p.put(contact+20,0x20)

    def run_entry(self,p,entry,sp=None,regs=None,stop=None,stubs=None):
        r=list(range(100,116)) if regs is None else list(regs)
        r[13]=sp or self.sp;r[14]=self.old.end;r[15]=self.at+entry
        before=list(r);out,c,_=p.run(r,0xa000001f,{stop},stubs)
        self.assertEqual(out[1:15],before[1:15]);self.assertEqual(c,0xa000001f)
        return before,out

    def pre(self,p,victim=None,sp=None):
        sp=sp or self.sp;r=list(range(16))
        r[0]=sp+0x54;r[1]=(victim or self.old.enemy)+8;r[2]=self.cell;r[3]=sp+0x8c
        before,out=self.run_entry(p,0,sp,r,self.values['OLD_CONTACT'],{0x02152c68:self.old.result(1)})
        self.assertEqual(out[0],before[0]);self.assertEqual(p.get(sp),0x1800)

    def end(self,p,sp=None):
        _,out=self.run_entry(p,4,sp,stop=0x02078670)
        self.assertEqual(out[0],self.outlist)

    def test_target_first_and_target_last_do_not_change_the_other_victim(self):
        for order in ((self.old.enemy,self.old.enemy+0x10000),(self.old.enemy+0x10000,self.old.enemy)):
            p=self.fixture();seen=[]
            for victim in order:
                self.pre(p,victim)
                # Native ReceiveHit and credit both see this type before next_victim.
                seen.append((victim,p.get(self.sp+0x8c),p.get(self.contact+20)))
                self.end(p)
                self.assertEqual((p.get(self.sp+0x8c),p.get(self.contact+20)),(0x20,0x20))
                self.assertEqual(p.get(self.sp+0x90),0xc00)
            self.assertEqual(seen,[(v,0x25 if v==self.old.enemy else 0x20,0x25 if v==self.old.enemy else 0x20) for v in order])

    def test_ignored_hit_or_destroyed_move_still_restores_the_call_frame(self):
        for ignored in (False,True):
            p=self.fixture();self.pre(p)
            p.put(self.sp+0x54,1 if ignored else 4)
            p.put(self.old.state,0);p.put(self.old.state+20,0)
            self.end(p)
            self.assertEqual((p.get(self.sp+0x8c),p.get(self.contact+20)),(0x20,0x20))

    def test_nested_dispatch_has_separate_restoration_data(self):
        p=self.fixture();inner=self.sp-0x800;inner_contact=self.contact+0x1000
        self.hit(p,inner,inner_contact)
        self.pre(p);self.pre(p,sp=inner)
        self.end(p,inner)
        self.assertEqual((p.get(inner+0x8c),p.get(inner_contact+20)),(0x20,0x20))
        self.assertEqual((p.get(self.sp+0x8c),p.get(self.contact+20)),(0x25,0x25))
        self.end(p)
        self.assertEqual((p.get(self.sp+0x8c),p.get(self.contact+20)),(0x20,0x20))

    def test_skipped_victim_and_unmapped_contact_are_not_restored_or_dereferenced(self):
        p=self.fixture();self.end(p)  # Native skip before the pre-hit hook.
        self.assertEqual(p.get(self.sp+0x8c),0x20)
        for address in (0,0x100,0x02400000,0x027dfffc,self.contact+1):
            p=self.fixture();p.put(self.sp+0x9c,address);self.pre(p);self.end(p)
            self.assertEqual(p.get(self.sp+0x8c),0x20)

    def test_new_player_clears_both_phases_without_reading_the_old_owner(self):
        new=self.old.hero+0x40000;ctl=self.old.ctl+0x40000;mot=self.old.mot+0x40000
        for phase in (1,2):
            for form in (0,1):
                p=self.fixture(phase);p.put(self.old.state,0x02312340)  # Unmapped departed player.
                for at,value in ((new,0x0212e3f0),(new+0x34,form),(new+0x30,mot),(new+0xe8,self.old.stats+12),
                    (mot+0x1f8,ctl),(ctl+0x44,new),(ctl+0x14,44),(ctl+0x64,0x400),(ctl+0x4c,self.old.enemy+4)):
                    p.put(at,value)
                p.put(self.old.stats,76)
                r=list(range(16));r[4]=new
                self.run_entry(p,8,regs=r,stop=0x02073b64)
                self.assertEqual((p.get(self.old.state),p.get(self.old.state+20)),(0,0))
                if form:
                    r[0]=ctl;r[13]=self.sp;r[14]=self.old.end;r[15]=self.old.at
                    p.run(r,0,{self.old.end},{self.old.native:self.old.result(42),0x02152c68:self.old.result(1)})
                    self.assertEqual((p.get(self.old.state),p.get(self.old.state+20)),(new,1))

    def test_other_actors_do_not_cancel_the_current_player_move(self):
        p=self.fixture();p.put(self.old.enemy,0x021301d0)
        r=list(range(16));r[4]=self.old.enemy
        self.run_entry(p,8,regs=r,stop=0x02073b64)
        self.assertEqual((p.get(self.old.state),p.get(self.old.state+20)),(self.old.hero,1))


class Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=fix.PARENT_PATH.read_bytes();cls.result,cls.report=fix.apply_rom(cls.parent)

    def test_only_three_hooks_zero_tail_and_two_version_resources_change(self):
        an,aa=fix.parent.assets.resources(self.parent);bn,bb=fix.parent.assets.resources(self.result)
        self.assertEqual(an,bn)
        self.assertEqual([n for n,a,b in zip(an,aa,bb) if a!=b],['American.strings','English.strings'])
        h,hh=w.parse_header(self.parent),w.parse_header(self.result)
        a=self.parent[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        b=self.result[hh['arm9_offset']:hh['arm9_offset']+hh['arm9_size']]
        self.assertEqual(len(a),len(b));self.assertEqual(a[kit.SOURCE:kit.SOURCE+kit.RESERVE],b[kit.SOURCE:kit.SOURCE+kit.RESERVE])
        offset=lambda at:kit.SOURCE+at-kit.TARGET if at>=kit.TARGET else at-0x02000000
        rt=self.report['runtime'];allowed={offset(row['site']) for row in rt['hooks']}
        old_meta=json.loads(fix.PARENT_PATH.with_suffix('.build.json').read_text(encoding='utf-8'))
        old_entry=old_meta['hunters_return']['runtime']['entry']
        self.assertEqual([row['site'] for row in rt['hooks']],[0x02078628,0x0207866c,old_entry+12])
        for i,site in enumerate((0x02078628,0x0207866c,old_entry+12)):
            self.assertEqual(w.u32(b,offset(site)),kit.branch(site,rt['entry']+i*4))
        allowed.update(range(offset(rt['entry']),offset(rt['entry'])+rt['bytes'],4))
        self.assertLessEqual({i for i in range(0,len(a),4) if a[i:i+4]!=b[i:i+4]},allowed)
        self.assertEqual(a[0x7862c:0x78630],b[0x7862c:0x78630])
        self.assertEqual(a[0x78650:0x7866c],b[0x78650:0x7866c])
        for e in w.nitrofs_entries(self.result):
            if e['name']=='Glob.bin':continue
            old=next(x for x in w.nitrofs_entries(self.parent) if x['name']==e['name'])
            self.assertEqual(self.result[e['start']:e['end']],self.parent[old['start']:old['end']])

    def test_native_saved_argument_slots_are_dead_before_each_iteration(self):
        from tools import kit_lab
        from capstone.arm import ARM_OP_MEM,ARM_REG_SP
        md=kit_lab._capstone();md.detail=True
        for ins in md.disasm(kit_lab.clean_arm9()[0x784a4:0x78690],0x20784a4):
            for operand in ins.operands:
                self.assertFalse(operand.type==ARM_OP_MEM and operand.mem.base==ARM_REG_SP and 0x80<=operand.mem.disp<0x8c)

    def test_wrong_parent_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'exact published'):fix.apply_rom(b'not a ROM')


if __name__=='__main__':unittest.main()
