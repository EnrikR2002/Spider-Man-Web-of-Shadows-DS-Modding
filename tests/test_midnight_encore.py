"""Real ARM ownership/ABI/lifecycle checks for the new native boss meter."""
import unittest
from tests.arm_runtime import ArmProbe
from tools import midnight_encore_combat as c


class BossOwnership(unittest.TestCase):
    at=0x02180000;slots=0x02182000;cfg=0x02190000
    actor=0x02200000;ctl=0x02201000;mot=0x02202000;stats=0x02203000
    end=0x03000000
    def fixture(self):
        p=ArmProbe();p.code(self.at,c.find_boss(self.at,self.slots,self.cfg))
        p.put(0x02145c5c,self.stats);p.put(self.stats,89)
        for i in range(32):
            for k in range(8):p.put(self.slots+i*32+k*4,0)
        for off,val in ((0,self.ctl),(4,self.actor),(8,self.cfg)):p.put(self.slots+off,val)
        p.put(self.ctl+0x44,self.actor);p.put(self.actor,0x021301d0);p.put(self.actor+0x40,self.cfg)
        p.put(self.actor+0x30,self.mot);p.put(self.mot,self.actor)
        p.put(self.actor+0x44,14000);p.put(self.actor+0x48,20000)
        return p
    def call(self,p):
        regs=[100+i for i in range(16)];regs[13]=0x023ff000;regs[14]=self.end;regs[15]=self.at
        out,flags,stop=p.run(regs,0xa000001f,{self.end})
        self.assertEqual(out[4:15],regs[4:15]);self.assertEqual(stop,self.end)
        return out[0]
    def test_live_boss_is_resolved_without_caching_a_heap_pointer(self):
        p=self.fixture();self.assertEqual(self.call(p),self.actor)
        p.put(self.actor+0x44,0);self.assertEqual(self.call(p),0)
    def test_other_rooms_player_actor_and_wrong_configs_never_feed_the_bar(self):
        for address,value in ((self.stats,78),(self.actor,0x0212e3f0),(self.actor+0x40,self.cfg+0x54),
            (self.slots+8,self.cfg+0x54),(self.actor+0x44,30000)):
            p=self.fixture();p.put(address,value);self.assertEqual(self.call(p),0)
    def test_stale_controller_or_motion_backlinks_and_unaligned_pointers_decline(self):
        for address,value in ((self.ctl+0x44,self.actor+4),(self.mot,self.actor+4),
            (self.actor+0x30,0x40000000),(self.slots,self.ctl+1),(self.slots+4,0x023fff00)):
            p=self.fixture();p.put(address,value);self.assertEqual(self.call(p),0)


class FreightRecovery(unittest.TestCase):
    def test_maw_walks_out_before_a_native_vault_and_other_owners_decline(self):
        from tools import creature_forge_combat as forge
        at=0x02180000;records=0x02182000;slots=0x02183000;counts=0x02184000;hero=0x02185004;room=hero-4
        moves=0x02186000;play=0x02187000;nav=0x02188000;poise=0x02189000;cfg=0x02190000
        ctl=0x02200000;actor=0x02201000;motion=0x02202000;stats=0x02203000;end=0x03000000
        code=forge.think(at,records,slots,counts,hero,room,moves,play,653,rewrite=lambda s:c.decisions(s,nav,poise))
        for style,native_room,state,x,expected in ((0,97,7,78,1),(0,97,7,88,5),(2,97,7,88,5),
            (0,78,7,88,7),(3,97,7,88,7),(0,97,37,88,37)):
            p=ArmProbe();p.code(at,code);p.put(0x02145c5c,stats);p.put(stats,native_room);p.put(room,native_room)
            for i,v in enumerate((cfg,0,3,style)):p.put(records+i*4,v)
            for i,v in enumerate((ctl,actor,cfg,0,10,0,0,0)):p.put(slots+i*4,v)
            p.put(ctl+0x44,actor);p.put(ctl+0x14,state);p.put(actor,0x021301d0);p.put(actor+0x44,20000)
            p.put(actor+0x40,cfg);p.put(actor+0x30,motion);p.put(motion,actor);p.put(motion+0x7c,x*4096)
            p.put(motion+0x80,round(-20.8*4096));p.put(motion+0x160,0);p.put(motion+0x164,0)
            sounds=[];jumps=[]
            def native(p,r,f):r[0]=state;return f
            def jump(p,r,f):jumps.append(r[0]);return f
            def sound(p,r,f):sounds.append(r[0]);return f
            regs=[ctl]+list(range(1,13))+[0x023ff000,end,at]
            out,_,_=p.run(regs,0,{end},{0x02095834:native,0x020739b4:jump,play:sound})
            self.assertEqual(out[0],expected);self.assertEqual(p.get(actor+0x44),20000)
            self.assertEqual(jumps,[actor] if expected==5 else [])
            if expected in (1,5):self.assertEqual(p.get(slots+28),0xc00)
            if expected==5:
                self.assertEqual(p.get(actor+0x1c),14746);self.assertEqual(sounds,[654 if style==0 else 664])


class NativeHud(unittest.TestCase):
    def test_meter_uses_actual_current_and_max_and_preserves_the_native_call_abi(self):
        at=0x02180000;find=0x02181000;obs=0x02182000;actor=0x02200000;meter=0x02201000;end=0x03000000
        for live in (True,False):
            p=ArmProbe();p.code(at,c.meter(at,find,obs));p.put(actor+0x44,8192);p.put(actor+0x48,532480)
            regs=[meter]+list(range(1,13))+[0x023ff000,end,at];calls=[]
            def resolver(p,r,f):r[0]=actor if live else 0;return f
            def render(p,r,f):calls.append(r[0]);r[0]=0;r[1]=999;return f
            stops={end,c.HUD_METER+4};out,_,stop=p.run(regs,0xa000001f,stops,{find:resolver,0x020e7920:render})
            self.assertEqual(out[4:13],regs[4:13])
            if live:
                self.assertEqual(calls,[meter]);self.assertEqual(p.get(meter+0xc),8192)
                self.assertEqual(p.get(meter+0x10),532480);self.assertEqual(p.get(meter+0x14),532480)
                self.assertEqual(out[:14],regs[:14]);self.assertEqual(stop,end)
            else:self.assertEqual(calls,[]);self.assertEqual(stop,c.HUD_METER+4)

    def test_hud_cleans_up_only_a_meter_it_previously_owned(self):
        at=0x02180000;find=0x02181000;owned=0x02182000;obs=owned+4;root=0x02200000
        for live,was_owned,expected in ((True,0,[1]),(False,1,[0]),(False,0,[])):
            p=ArmProbe();p.code(at,c.hud_tick(at,find,owned,obs));p.put(owned,was_owned);calls=[]
            def resolver(p,r,f):r[0]=0x02201000 if live else 0;return f
            def toggle(p,r,f):calls.append(r[1]);self.assertEqual(r[0],root);return f
            regs=[root]+list(range(1,13))+[0x023ff000,0x03000000,at]
            out,_,stop=p.run(regs,0xa000001f,{c.HUD_TICK+4},{find:resolver,0x020e0a54:toggle})
            self.assertEqual(calls,expected);self.assertEqual(out[4:13],regs[4:13])


class CommittedPoise(unittest.TestCase):
    def test_rise_and_counter_poise_do_not_remove_damage_or_guard_death(self):
        at=0x02180000;old=at+0x1000;slots=at+0x2000;cfg=at+0x3000;poise=at+0x4000
        ctl=0x02200000;actor=ctl+0x1000;motion=ctl+0x2000;end=0x03000000
        for state,clock,timer,kind,expected in ((51,3,0,37,37),(51,6,0,41,0x7fffffff),
            (51,8,0,53,53),(1,0,20,37,0x7fffffff),(1,0,0,37,37)):
            p=ArmProbe();p.code(at,c.secondary(at,old,slots,cfg,poise));p.put(poise,actor);p.put(poise+4,timer)
            p.put(ctl+0x44,actor);p.put(ctl+0x14,state);p.put(actor+0x40,cfg);p.put(actor+0x44,1234)
            p.put(actor+0x30,motion);p.put(motion+0x178,clock)
            def native(p,r,f):r[0]=kind;return f
            regs=[ctl]+list(range(1,13))+[0x023ff000,end,at]
            out,_,_=p.run(regs,0,{end},{old:native});self.assertEqual(out[0],expected);self.assertEqual(p.get(actor+0x44),1234)

    def test_secondary_preserves_only_owned_live_committed_attacks_and_never_death(self):
        at=0x02180000;old=at+0x1000;slots=at+0x2000;cfg=at+0x3000
        ctl=0x02200000;actor=ctl+0x1000;motion=ctl+0x2000;program=ctl+0x3000;end=0x03000000
        for clock,hp,kind,expected in ((0,1000,37,37),(5,1000,37,0x7fffffff),(28,1000,41,0x7fffffff),
            (29,1000,41,41),(9,0,37,37),(9,1000,53,53)):
            poise=at+0x4000
            p=ArmProbe();p.code(at,c.secondary(at,old,slots,cfg,poise));p.put(poise,actor);p.put(poise+4,0);p.put(ctl+0x44,actor);p.put(ctl+0x14,15)
            p.put(actor+0x40,cfg);p.put(actor+0x44,hp);p.put(actor+0x30,motion);p.put(motion+0x178,clock)
            p.put(slots,ctl);p.put(slots+4,actor);p.put(slots+20,program);p.put(program+4,33)
            def native(p,r,f):r[0]=kind;return f
            regs=[ctl]+list(range(1,13))+[0x023ff000,end,at]
            out,_,_=p.run(regs,0,{end},{old:native});self.assertEqual(out[0],expected);self.assertEqual(out[4:14],regs[4:14])
