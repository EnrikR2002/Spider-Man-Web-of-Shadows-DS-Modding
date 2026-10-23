"""Raw lethal damage, exact cocoon eligibility, native exits and boss HUD scope."""
import struct
import unittest
from tests.arm_runtime import ArmProbe
from tools import vortex_forge as vf,tasm_kit as kit


class Damage(unittest.TestCase):
    def run_damage(self,hp,damage,bits=0,room=65,dial=0,fixed=True):
        p=ArmProbe();raw=bytearray(kit.code_bytes(2));entry=vf.kit_symbols()['k2_damage']
        if fixed:struct.pack_into('<I',raw,entry-kit.KIT2_BASE+4,0xe0514000)
        p.code(kit.KIT2_BASE,raw);stats=0x02210000
        p.put(0x02145c5c,stats);p.put(stats,room);p.put(stats+0x14,bits)
        if 76<=room<116:p.memory[0x02156fc0+(room-76)*2+1]=dial
        regs=[0x50000+i for i in range(16)];regs[0]=(hp-damage)&0xffffffff;regs[1]=hp;regs[2]=stats;regs[3]=max(0,hp-damage)
        regs[13]=0x023f0000;regs[14]=0x03000000;regs[15]=entry
        after,_,_=p.run(regs,0,{0x03000000})
        for i in (0,1,2,4,5,13):self.assertEqual(after[i],regs[i])
        return after[3]

    def test_full_incoming_damage_not_remaining_hp_is_scaled(self):
        self.assertGreater(self.run_damage(1500,4096,0x8000,fixed=False),0)
        self.assertEqual(self.run_damage(1500,4096,0x8000),0)

    def test_vitality_and_room_scaling_at_full_and_low_hp(self):
        for bits,vit in ((0,256),(0x2000,205),(0x6000,171),(0xe000,146)):
            for room,dial in ((65,0),(89,64),(89,96),(89,32)):
                factor=((dial*4 if dial else 256)*vit)>>8
                for damage in (1,1024,4096,16384):
                    for hp in (128,1500,8192,77824):
                        with self.subTest(bits=bits,room=room,dial=dial,damage=damage,hp=hp):
                            loss=damage if factor==256 else max(1,damage*factor>>8)
                            self.assertEqual(self.run_damage(hp,damage,bits,room,dial),max(0,hp-loss))


class Gates(unittest.TestCase):
    at=0x021a1000;state=0x021a0000;boss=0x02270000;end=0x03000000
    ctl=0x02200000;hero=0x02201000;mot=0x02202000
    symbols=vf.kit_symbols()

    def fixture(self,webbed=True,owned=True,held=0x80,state=0,live=True):
        p=ArmProbe();p.code(self.at,vf.runtime(self.at,self.state,self.boss,self.symbols))
        for at in range(self.state,self.state+256,4):p.put(at,0)
        for at in range(0x02154c40,0x02154d00,4):p.put(at,0)
        p.put(0x02154c20,100)
        p.put(self.ctl+0x14,state);p.put(self.ctl+0x44,self.hero);p.put(self.hero+0x30,self.mot)
        for field in (0x7c,0x80,0x160,0x164):p.put(self.mot+field,0)
        p.put(self.mot+0x180,1)
        enemy=0x02210000;motion=0x02211000;controller=0x02212000
        p.put(0x02154c40,enemy);p.put(0x02154c44,8*4096);p.put(0x02154c48,0)
        p.put(enemy+0x30,motion);p.put(enemy+0x40,0x02213000);p.put(enemy+0x48,20*4096)
        p.put(motion+0x1f8,controller);p.put(controller+0x14,46 if webbed else 0)
        consumed=[]
        def result(value):
            def stub(p,r,c):r[0]=value;return c
            return stub
        def consume(p,r,c):consumed.append(1);return c
        stubs={self.symbols['k2_owned']:result(int(owned)),0x02152c5c:result(held),
               0x020cff0c:result(1),0x020cfc34:consume,0x02152c68:result(int(live))}
        regs=[100+i for i in range(16)];regs[0]=self.ctl;regs[13]=0x023f0000;regs[14]=self.end;regs[15]=self.at
        out,_,_=p.run(regs,0,{self.end},stubs)
        for i in range(4,12):self.assertEqual(out[i],regs[i])
        self.assertEqual(out[13],regs[13])
        return out[0],consumed,p

    def test_only_actual_webbed_targets_start_owned_red_finisher(self):
        result,consumed,p=self.fixture()
        self.assertEqual((result,len(consumed),p.get(self.state+8)),(1,1,1))
        for kw in ({'webbed':False},{'owned':False},{'held':0},{'held':0x180},{'held':0xc0},{'state':39},{'state':53},{'live':False}):
            with self.subTest(kw=kw):
                result,consumed,_=self.fixture(**kw);self.assertEqual((result,len(consumed)),(0,0))

    def test_boss_hud_filter_preserves_flags_and_other_actor_snapshots(self):
        for vtable,config,stop in ((0x021301d0,self.boss,0x02073a6c),(0x021301d0,self.boss+4,0x02151924),(0x0212e3f0,self.boss,0x02151924)):
            p=ArmProbe();p.code(self.at,vf.runtime(self.at,self.state,self.boss,self.symbols));actor=0x02220000
            p.put(actor,vtable);p.put(actor+0x40,config)
            regs=list(range(16));regs[0]=actor;regs[13]=0x023f0000;regs[14]=self.end;regs[15]=self.at+12
            out,flags,pc=p.run(regs,0xa000001f,{stop})
            self.assertEqual((flags,pc),(0xa000001f,stop))
            self.assertEqual(out[:13],regs[:13])

    def test_native_interrupt_releases_every_private_target(self):
        for native_state in (37,53,57,67):
            p=ArmProbe();p.code(self.at,vf.runtime(self.at,self.state,self.boss,self.symbols))
            for at in range(self.state,self.state+256,4):p.put(at,1)
            p.put(self.state,self.hero);p.put(self.state+4,self.ctl)
            p.put(self.hero+0x30,self.mot);p.put(self.mot+0x1f8,self.ctl);p.put(self.ctl+0x14,native_state)
            regs=list(range(16));regs[0]=self.hero;regs[13]=0x023f0000;regs[14]=self.end;regs[15]=self.at+8
            out,_,_=p.run(regs,0,{self.end})
            self.assertEqual([p.get(self.state+o) for o in (8,12,16)],[0,0,0])
            self.assertEqual([p.get(self.state+64+i*16+12) for i in range(4)],[0]*4)
            self.assertEqual(out[4:12],regs[4:12]);self.assertEqual(out[13],regs[13])

    def test_stale_registry_target_is_not_dereferenced_or_moved(self):
        p=ArmProbe();p.code(self.at,vf.runtime(self.at,self.state,self.boss,self.symbols))
        for at in range(self.state,self.state+256,4):p.put(at,0)
        p.put(self.state,self.hero);p.put(self.state+4,self.ctl);p.put(self.state+8,1);p.put(self.state+16,1)
        p.put(self.state+64,0x02312340)  # deliberately unmapped actor memory
        p.put(self.hero+0x30,self.mot);p.put(self.mot+0x1f8,self.ctl);p.put(self.ctl+0x14,46)
        for off in (0x7c,0x80,0x160,0x164):p.put(self.mot+off,0)
        p.put(self.mot+0x254,59);p.put(self.mot+0x178,13)
        def stale(probe,regs,flags):regs[0]=0;return flags
        regs=list(range(16));regs[0]=self.hero;regs[13]=0x023f0000;regs[14]=self.end;regs[15]=self.at+8
        p.run(regs,0,{self.end},{0x02152c68:stale})
        self.assertEqual(p.get(self.state+44),0)


if __name__=='__main__':unittest.main()
