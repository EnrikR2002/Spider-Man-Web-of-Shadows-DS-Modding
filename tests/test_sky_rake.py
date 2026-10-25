"""Owned Black air routing, isolated native pop hits, affordable rows and byte scope."""
import struct
import unittest
from tests.arm_runtime import ArmProbe
from tools import sky_rake as s, tasm_kit as kit, wos_tool as w


class Runtime(unittest.TestCase):
    at, routes, hero, motion = 0x021a1000, 0x021a0000, 0x02200000, 0x02201000
    ctl, stats, stack, end = 0x02202000, 0x02203000, 0x023f0000, 0x03000000
    values = dict(ROUTES=routes, BOSS_CONFIG=0x02190000, OLD_ANIMATION=0x021b0000,
                  OLD_CONTACT=0x021b0100, OLD_AIR=0x021b0200)

    def fixture(self, action=1, form=1, owned=True, state=51):
        p = ArmProbe()
        p.code(self.at, s.runtime(self.at, self.values))
        for at, value in ((self.hero, 0x0212e3f0), (self.hero+0x30, self.motion),
            (self.hero+0x34, form), (self.hero+0xe8, self.stats+12),
            (self.stats+12,1<<10), (self.stats+20, (1<<21) if owned else 0), (self.motion, self.hero),
            (self.motion+0x258, action), (self.motion+0x1f8, self.ctl),
            (self.ctl+0x44, self.hero), (self.ctl+0x14, state)):
            p.put(at, value)
        for i in range(12):
            p.put(self.routes+i*4, 6000+i)
        p.put(self.hero+4,0)
        return p

    def run_entry(self, p, index, regs, *, stops=None, stubs=None):
        regs[13:16] = [self.stack, self.end, self.at+index*4]
        return p.run(regs, 0xa000001f, stops or {self.end}, stubs)

    def test_only_owned_black_current_air_actions_change_all_three_resources(self):
        for action in range(1, 5):
            p = self.fixture(action=action)
            for off in (0x2c, 0x38, 0x3c): p.put(self.stack+off, 12)
            regs = list(range(100, 116)); regs[0], regs[4] = 1, self.motion
            out, flags, _ = self.run_entry(p, 0, regs, stops={self.values['OLD_ANIMATION']})
            self.assertEqual(out[:13], regs[:13])
            self.assertEqual(flags, 0xa000001f)
            self.assertEqual(out[13], self.stack)
            self.assertEqual([p.get(self.stack+i) for i in (0x2c,0x38,0x3c)], list(range(6000+(action-1)*3, 6003+(action-1)*3)))
        for kwargs in ({'form':0}, {'owned':False}, {'state':46}, {'state':63}, {'action':0}, {'action':5}):
            p = self.fixture(**kwargs)
            p.put(self.stack+0x2c, 12)
            regs = list(range(16)); regs[0],regs[4] = 1,self.motion
            self.run_entry(p,0,regs,stops={self.values['OLD_ANIMATION']})
            self.assertEqual(p.get(self.stack+0x2c),12)
        for at,value in ((self.motion,self.hero+4),(self.hero+0x30,self.motion+4),
                         (self.hero+0xe8,0x023ffffc),(self.ctl+0x44,self.hero+4)):
            p=self.fixture();p.put(at,value);p.put(self.stack+0x2c,12)
            regs=list(range(16));regs[0],regs[4]=1,self.motion
            self.run_entry(p,0,regs,stops={self.values['OLD_ANIMATION']})
            self.assertEqual(p.get(self.stack+0x2c),12)

    def contact(self,p,kind=0x16,attacker=0x02211000):
        info = 0x02210000
        p.put(info,kind);p.put(attacker,self.hero)
        regs=list(range(16));regs[2],regs[3],regs[4]=attacker,info,0x021b1000
        out,flags,_=self.run_entry(p,1,regs,stops={self.values['OLD_CONTACT']})
        self.assertEqual(out[:4],regs[:4]);self.assertEqual(flags,0xa000001f)
        return out[4]

    def test_finisher_receiver_is_scoped_without_changing_the_shared_info(self):
        p=self.fixture(action=4);wrapper=self.contact(p)
        self.assertNotEqual(wrapper,0x021b1000)
        self.assertEqual(self.contact(self.fixture(action=4),attacker=0x027ef000),wrapper)
        self.assertEqual(self.contact(self.fixture(action=3),kind=0x14),wrapper)
        for kwargs,kind in (({'action':3},0x16),({'form':0},0x16),({'owned':False},0x16),({'action':4},0x04)):
            self.assertEqual(self.contact(self.fixture(**kwargs),kind),0x021b1000)

    def test_pop_is_native_launch_or_heavy_stagger_with_original_info_and_damage_preserved(self):
        for kind,heavy,ignored in ((0x16,False,False),(0x16,True,False),(0x16,False,True),
                                   (0x14,False,False),(0x14,True,False),(0x14,False,True)):
            p=self.fixture(action=4);wrapper=self.contact(p)
            result,victim,info,contact,attacker,receive=0x02220000,0x02221000,0x02222000,0x02223000,0x02224000,0x021b1000
            for at in range(info,info+64,4): p.put(at,42)
            for at in range(contact,contact+32,4): p.put(at,43)
            p.put(info,kind);p.put(info+16,contact);p.put(contact+20,kind)
            p.put(victim,0x021301d0);p.put(victim+8,0x021c0000);p.put(0x021c0040,receive)
            p.put(victim+0x40,self.values['BOSS_CONFIG'] if heavy else 0x02230000)
            p.put(attacker,self.hero);p.put(self.stack,0x1000)
            seen=[]
            def native(q,r,c):
                seen.append((q.get(r[3]),q.get(q.get(r[3]+16)+20),q.get(r[13])))
                self.assertEqual(r[:3],[result,victim+8,attacker])
                q.put(r[0],1 if ignored and len(seen)==1 else 4)
                return c
            regs=list(range(100,116));regs[:4]=[result,victim+8,attacker,info]
            regs[13:]=[self.stack,self.end,wrapper]
            out,_,_=p.run(regs,0x1f,{self.end},{receive:native})
            reaction=0x25 if kind==0x16 else 0x14
            wanted=[4] if heavy else [reaction,4] if ignored else [reaction]
            self.assertEqual(seen,[(kind,kind,0x1000) for kind in wanted])
            self.assertEqual((p.get(info),p.get(info+16),p.get(contact+20)),(kind,contact,kind))
            self.assertEqual(out[4:12],regs[4:12]);self.assertEqual(out[13],self.stack)

    def test_air_r_exits_and_other_native_commands_remain_untouched(self):
        for queued in (3,4,None):
            p=self.fixture();p.put(self.stack,19);p.put(self.stack+4,self.end)
            seen=[]
            def peek(q,r,c):
                seen.append(q.get(r[1]));r[0]=int(q.get(r[1])==queued);return c
            regs=list(range(16));regs[0],regs[4]=self.hero,self.ctl
            out,_,pc=self.run_entry(p,2,regs,stops={self.end,self.values['OLD_AIR']},stubs={0x020cff0c:peek})
            self.assertEqual(pc,self.end if queued==3 else self.values['OLD_AIR'])
            self.assertEqual(seen,[3])
            if queued==3:self.assertEqual((out[0],out[13]),(0x7fffffff,self.stack+8))

    def test_fourteen_row_budget_is_affordable_and_new_row_uses_its_reserved_bit(self):
        self.assertEqual((len(s.PLANNED_PRICES),sum(s.PLANNED_PRICES),min(s.PLANNED_PRICES),max(s.PLANNED_PRICES)),(14,1600,50,200))
        self.assertEqual(s.EVENT-309,s.BIT)
        self.assertEqual(s.PRICES,s.PLANNED_PRICES[:8]+(s.PLANNED_PRICES[9],))

    def test_r_without_paid_air_dodge_consumes_only_r_and_enters_native_fall(self):
        p=self.fixture();p.put(self.stats+12,0);p.put(self.stack,19);p.put(self.stack+4,self.end)
        calls=[]
        def peek(q,r,c):r[0]=int(q.get(r[1])==3);return c
        def consume(q,r,c):calls.append(q.get(r[1]));return c
        regs=list(range(16));regs[0],regs[4]=self.hero,self.ctl
        out,_,pc=self.run_entry(p,2,regs,stubs={0x020cff0c:peek,0x020cfc34:consume})
        self.assertEqual((pc,out[0],out[13],calls),(self.end,19,self.stack+8,[3]))
        self.assertEqual(p.get(self.stats+12),0)


@unittest.skipUnless(s.PARENT_PATH.exists(),'private published parent missing')
class Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=s.PARENT_PATH.read_bytes();cls.after,cls.report=s.apply_rom(cls.before)

    def test_only_appended_art_strings_shop_pointer_and_guarded_code_change(self):
        an,ab=s.assets.resources(self.before);bn,bb=s.assets.resources(self.after)
        self.assertEqual([n for n,a,b in zip(an,ab,bb) if a!=b],['American.strings','English.strings','GlobFiles.txt'])
        from tools.gmb import Gmb
        from tools.custom_formats import Gab
        from tools.grip_compression import CompressedBlob
        from tools.sca import Sca
        for i,(clip,contacts) in enumerate(zip(s.art.CLIPS,s.art.CONTACTS),1):
            self.assertEqual(Sca.parse(bb[bn.index(f'zz_S35_Air{i}.sca')]).frame_count,clip.samples)
            g=Gmb.parse(CompressedBlob.parse(bb[bn.index(f'zz_S35_Air{i}.gmb')]).decoded)
            attack=g.channels[2]
            self.assertEqual(tuple(f for f in range(g.record_count) if attack.words(f)[5]),contacts)
            Gab.parse(bb[bn.index(f'zz_S35_Air{i}.gab')])
        def arm(rom):
            h=w.parse_header(rom);return rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        a,b=arm(self.before),arm(self.after);rt=self.report['runtime']
        allowed=set(range(rt['source_offset'],rt['source_offset']+rt['block_bytes']))
        for off in (s.hunter_kit.BLACK_POINTER,s.hunter_kit.BLACK_COUNT,s.oscorp_resources.COUNT_OFFSET,
                    *(r['site']-kit.BASE for r in rt['hooks'])): allowed.update(range(off,off+4))
        self.assertTrue(all(i in allowed for i,(x,y) in enumerate(zip(a,b)) if x!=y))
        self.assertEqual(a[kit.SOURCE:kit.SOURCE+kit.RESERVE],b[kit.SOURCE:kit.SOURCE+kit.RESERVE])
        parent=w.u32(a,s.hunter_kit.BLACK_POINTER)-kit.TARGET+kit.SOURCE
        current=rt['shop']-kit.TARGET+kit.SOURCE
        from tools.hunter_kit_lab import shop_price
        self.assertEqual(shop_price(self.before,7,83),300)
        self.assertEqual(shop_price(self.after,7,83),75)
        self.assertEqual(shop_price(self.after,8,85),100)
        with self.assertRaises(ValueError):shop_price(self.after,8,84)
        for i,price in enumerate(s.PRICES[:8]):
            self.assertEqual(a[parent+i*32:parent+i*32+28],b[current+i*32:current+i*32+28])
            self.assertEqual(w.u32(b,current+i*32+28),price)
        self.assertEqual(w.u32(b,current+8*32),s.EVENT)
        for e in w.nitrofs_entries(self.before):
            if e['name']=='Glob.bin':continue
            n=next(x for x in w.nitrofs_entries(self.after) if x['name']==e['name'])
            self.assertEqual(self.before[e['start']:e['end']],self.after[n['start']:n['end']])


if __name__=='__main__':unittest.main()
