"""Behavioral regressions for a comboable boss with earned counter protection."""
import unittest
from tests.arm_runtime import ArmProbe
from tests.test_midnight_voltage import Pressure
from tools import midnight_voltage_combat as voltage,midnight_finale_combat as c,creature_forge_combat as forge


class PressureWindow(Pressure):
    def fixture(self):
        p=super().fixture();p.code(self.at,voltage.damage(self.at,self.old,self.state,self.cfg,hit_threshold=4,window=100));return p
    def test_three_real_losses_queue_but_never_apply_or_remove_damage(self):
        p=self.fixture()
        for i,hp in enumerate((94000,88000,82000,76000)):
            before=p.get(self.actor+0x44);self.call(p,hp)
            self.assertEqual(p.get(self.actor+0x44),before);self.assertEqual(p.get(self.state+16),int(i==3));p.put(self.actor+0x44,hp)
        self.assertEqual(p.get(self.state+12),100)


class Openings(unittest.TestCase):
    at=0x02180000;old=at+0x1000;slots=at+0x2000;cfg=at+0x3000
    ctl=0x02200000;actor=ctl+0x1000;motion=ctl+0x2000;program=ctl+0x3000;end=0x03000000
    def run_case(self,action,clock,decision,hp=1000,valid=True):
        p=ArmProbe();p.code(self.at,c.secondary(self.at,self.old,self.slots,self.cfg));p.put(self.ctl+0x44,self.actor);p.put(self.ctl+0x14,15);p.put(self.ctl+4,1)
        p.put(self.actor+0x40,self.cfg);p.put(self.actor+0x44,hp);p.put(self.actor+0x30,self.motion);p.put(self.motion,self.actor)
        p.put(self.motion+0x178,clock);p.put(self.motion+0x254,action)
        for i in range(32):p.put(self.slots+i*32,0)
        p.put(self.slots,self.ctl);p.put(self.slots+4,self.actor if valid else self.actor+4);p.put(self.slots+8,self.cfg)
        p.put(self.slots+20,self.program);p.put(self.program,action);p.put(self.program+4,37)
        def native(p,r,f):r[0]=decision;return f
        regs=[self.ctl]+list(range(1,13))+[0x023ff000,self.end,self.at]
        out,_,_=p.run(regs,0,{self.end},{self.old:native});self.assertEqual(out[4:14],regs[4:14]);self.assertEqual(p.get(self.actor+0x44),hp)
        return out[0],p
    def test_every_ordinary_attack_can_be_staggered_at_windup_contact_and_recovery(self):
        for action in (55,63,30,136):
            for clock in (0,8,13,21,29,36):
                with self.subTest(action=action,clock=clock):self.assertEqual(self.run_case(action,clock,37)[0],37)
    def test_knockdown_becomes_standing_recoil_but_web_and_death_stay_native(self):
        for decision in range(26,54):
            expected=37 if 38<=decision<=45 or 48<=decision<=50 else decision
            self.assertEqual(self.run_case(55,10,decision)[0],expected)
    def test_only_counter_commitment_is_protected_and_its_recovery_is_open(self):
        for clock,expected in ((0,0x7fffffff),(12,0x7fffffff),(29,0x7fffffff),(30,37),(37,37)):
            value,p=self.run_case(74,clock,37);self.assertEqual(value,expected)
            self.assertEqual(p.memory[self.ctl+4],0 if expected==0x7fffffff else 1)
        self.assertEqual(self.run_case(74,12,53)[0],53)
    def test_stale_slot_and_dead_actor_never_receive_armour_or_reaction_remap(self):
        self.assertEqual(self.run_case(74,12,41,valid=False)[0],41)
        self.assertEqual(self.run_case(74,12,41,hp=0)[0],41)


class PrimaryDecisions(unittest.TestCase):
    def test_normal_hits_interrupt_but_queued_four_hit_escape_can_break_a_flinch(self):
        at=0x02180000;records=at+0x2000;slots=at+0x3000;counts=at+0x4000;hero=at+0x5004
        moves=at+0x6000;play=at+0x7000;nav=at+0x8000;poise=at+0x9000;table=at+0xa000;state=at+0xb000;cfg=at+0xc000
        ctl=0x02200000;actor=ctl+0x1000;motion=ctl+0x2000;stats=ctl+0x3000;program=table;end=0x03000000
        code=forge.think(at,records,slots,counts,hero,hero-4,moves,play,653,rewrite=lambda s:c.decisions(s,nav,poise,state,table,hero))
        for queued,decision,expected in ((False,37,37),(False,41,37),(False,53,53),(True,37,15),(True,53,53)):
            p=ArmProbe();p.code(at,code);p.put(0x02145c5c,stats);p.put(0x02145c34,0);p.put(stats,89);p.put(hero-4,89);p.put(hero,0)
            for i,v in enumerate((cfg,table,6,6)):p.put(records+i*4,v)
            for i,v in enumerate((ctl,actor,cfg,0,10,program,1,0)):p.put(slots+i*4,v)
            for i in range(12):p.put(state+i*4,0)
            p.put(state,actor);p.put(state+4,motion);p.put(state+16,int(queued));p.put(table,55)
            p.put(ctl+0x44,actor);p.put(ctl+0x14,15);p.put(actor,0x021301d0);p.put(actor+0x44,60000);p.put(actor+0x40,cfg)
            p.put(actor+0x30,motion);p.put(motion,actor)
            def native(p,r,f):r[0]=decision;return f
            regs=[ctl]+list(range(1,13))+[0x023ff000,end,at];out,_,_=p.run(regs,0,{end},{0x02095834:native})
            self.assertEqual(out[0],expected);self.assertEqual(p.get(actor+0x44),60000)
            if queued and decision!=53:self.assertEqual(p.get(state+20),72)


if __name__=='__main__':unittest.main()
