"""Pressure ownership, non-restarting retaliation and sound isolation."""
import struct,unittest
from pathlib import Path
from tests.arm_runtime import ArmProbe
from tools import midnight_voltage_combat as c,creature_forge_combat as forge


class Pressure(unittest.TestCase):
    at=0x02180000;old=0x02181000;state=0x02182000;cfg=0x02190000
    actor=0x02200000;motion=0x02201000;stats=0x02202000;end=0x03000000
    def fixture(self):
        p=ArmProbe();p.code(self.at,c.damage(self.at,self.old,self.state,self.cfg))
        for i in range(12):p.put(self.state+4*i,0)
        p.put(self.actor,0x021301d0);p.put(self.actor+0x40,self.cfg);p.put(self.actor+0x30,self.motion);p.put(self.actor+0x44,100000)
        p.put(0x02145c5c,self.stats);p.put(self.stats,89);return p
    def call(self,p,hp,actor=None):
        regs=[self.actor if actor is None else actor,hp]+list(range(2,13))+[0x023ff000,self.end,self.at]
        out,flags,stop=p.run(regs,0xa000001f,{self.old});self.assertEqual(out[:15],regs[:15]);self.assertEqual(flags,0xa000001f)
        return out
    def test_three_real_losses_queue_but_never_apply_or_remove_damage(self):
        p=self.fixture()
        for i,hp in enumerate((94000,88000,82000)):
            before=p.get(self.actor+0x44);self.call(p,hp);self.assertEqual(p.get(self.actor+0x44),before)
            self.assertEqual(p.get(self.state+16),int(i==2));p.put(self.actor+0x44,hp)
        self.assertEqual(p.get(self.state+36),3);self.assertEqual(p.get(self.state+12),80)
    def test_heals_equal_hp_other_owners_and_dead_actors_do_not_queue(self):
        for where,value in ((self.stats,78),(self.actor+0x40,self.cfg+4),(self.actor,0x0212e3f0)):
            p=self.fixture();p.put(where,value)
            for _ in range(4):self.call(p,90000)
            self.assertEqual(p.get(self.state+16),0);self.assertEqual(p.get(self.state+36),0)
        p=self.fixture()
        for hp in (100000,110000):self.call(p,hp)
        self.assertEqual(p.get(self.state+36),0);p.put(self.state+16,1);p.put(self.state+24,64);self.call(p,0)
        self.assertEqual(p.get(self.state+16),0);self.assertEqual(p.get(self.state+24),0)
    def test_bad_actor_addresses_decline_before_dereferencing(self):
        for actor in (0,0x40000000,self.actor+1):
            p=self.fixture();self.call(p,90000,actor);self.assertEqual(p.get(self.state+36),0)


class CounterTransition(unittest.TestCase):
    def test_queued_pressure_uses_native_state_entry_without_HP_or_position_writes(self):
        at=0x02180000;records=0x02182000;slots=0x02183000;counts=0x02184000;hero=0x02185004;room=hero-4
        moves=0x02186000;play=0x02187000;nav=0x02188000;poise=0x02189000;table=0x0218a000;state=0x0218b000;cfg=0x02190000
        ctl=0x02200000;actor=0x02201000;motion=0x02202000;stats=0x02203000;end=0x03000000
        code=forge.think(at,records,slots,counts,hero,room,moves,play,653,rewrite=lambda s:c.decisions(s,nav,poise,state,table,hero))
        for native_state,expected in ((37,15),(53,53)):
            p=ArmProbe();p.code(at,code);p.put(0x02145c5c,stats);p.put(0x02145c34,0);p.put(stats,89);p.put(room,89);p.put(hero,0)
            for i,v in enumerate((cfg,table,6,6)):p.put(records+i*4,v)
            for i,v in enumerate((ctl,actor,cfg,0,10,0,1,0)):p.put(slots+i*4,v)
            for i in range(12):p.put(state+i*4,0)
            p.put(state,actor);p.put(state+4,motion);p.put(state+16,1)
            p.put(ctl+0x44,actor);p.put(ctl+0x14,37);p.put(actor,0x021301d0);p.put(actor+0x44,60000);p.put(actor+0x40,cfg)
            p.put(actor+0x30,motion);p.put(motion,actor)
            def native(p,r,f):r[0]=native_state;return f
            regs=[ctl]+list(range(1,13))+[0x023ff000,end,at];out,_,_=p.run(regs,0,{end},{0x02095834:native})
            self.assertEqual(out[0],expected);self.assertEqual(p.get(actor+0x44),60000)
            if expected==15:
                self.assertEqual(p.get(slots+20),table+4*32);self.assertEqual(p.get(state+16),0);self.assertEqual(p.get(state+28),1)
                self.assertEqual(p.get(state+24),64);self.assertEqual(p.memory[ctl+4],1)
    def test_running_attack_consumes_hurt_force_flag_but_recovery_and_death_remain(self):
        at=0x02180000;old=at+0x1000;slots=at+0x2000;cfg=at+0x3000;ctl=0x02200000;actor=ctl+0x1000;motion=ctl+0x2000;program=ctl+0x3000;end=0x03000000
        for clock,hp,next_state,expected in ((0,1000,37,0x7fffffff),(23,1000,41,0x7fffffff),(24,1000,37,37),(4,0,37,37),(4,1000,53,53)):
            p=ArmProbe();p.code(at,c.secondary(at,old,slots,cfg));p.put(ctl+0x44,actor);p.put(ctl+0x14,15);p.put(ctl+4,1)
            p.put(actor+0x40,cfg);p.put(actor+0x44,hp);p.put(actor+0x30,motion);p.put(motion+0x178,clock);p.put(motion+0x254,74)
            p.put(slots,ctl);p.put(slots+4,actor);p.put(slots+20,program);p.put(program,74);p.put(program+4,27)
            def native(p,r,f):r[0]=next_state;return f
            regs=[ctl]+list(range(1,13))+[0x023ff000,end,at];out,_,_=p.run(regs,0,{end},{old:native})
            self.assertEqual(out[0],expected);self.assertEqual(p.memory[ctl+4],0 if expected==0x7fffffff else 1)


class GapTurns(unittest.TestCase):
    def test_turns_only_at_crossed_gaps_with_owned_live_actor_and_player_backlinks(self):
        at=0x02180000;old=at+0x1000;slots=at+0x2000;cfg=at+0x3000;hero_ptr=at+0x4000;state=at+0x5000
        ctl=0x02200000;actor=ctl+0x1000;motion=ctl+0x2000;program=ctl+0x3000;hero=ctl+0x4000;hm=ctl+0x5000
        for action,clock,last,valid,expected in ((74,14,13,True,0),(74,14,14,True,1),(55,17,15,True,0),(74,3,2,True,1),(74,14,13,False,1)):
            p=ArmProbe();p.code(at,c.update(at,old,slots,cfg,hero_ptr,state));p.put(ctl+0x14,15);p.put(ctl+0x44,actor)
            p.put(actor+0x40,cfg);p.put(actor+0x44,1000);p.put(actor+0x30,motion);p.put(motion,actor)
            p.put(motion+0x254,action);p.put(motion+0x178,clock);p.put(motion+0x7c,112*4096);p.put(motion+0x160,0)
            p.put(slots,ctl);p.put(slots+4,actor);p.put(slots+20,program);p.put(slots+24,1);p.put(slots+28,last);p.put(program,action)
            p.put(hero_ptr,hero);p.put(hero,0x0212e3f0);p.put(hero+0x30,hm);p.put(hm,hero if valid else 0)
            p.put(hm+0x7c,40*4096);p.put(hm+0x160,0);p.put(state+44,0)
            regs=[ctl]+list(range(1,13))+[0x023ff000,0x03000000,at];out,_,_=p.run(regs,0,{old})
            self.assertEqual(out[:15],regs[:15]);self.assertEqual(p.get(slots+24),expected)


class SoundIsolation(unittest.TestCase):
    def test_native_sound_rows_and_samples_stay_exact_and_muted_control_has_same_layout(self):
        from tools import wos_tool as w,sdat,midnight_voltage_audio as a
        rom=(Path(__file__).resolve().parents[1]/'build/version-0.25.0-final/Versioned.nds').read_bytes()
        e=next(e for e in w.nitrofs_entries(rom) if e['name']=='sound_data.sdat');raw=rom[e['start']:e['end']]
        old=sdat.Sdat.parse(raw);live=sdat.Sdat.parse(a.sound_data(raw));muted=sdat.Sdat.parse(a.sound_data(raw,muted=True))
        changed=[i for i in range(len(old.entries)) if old.blob(i)!=live.blob(i)]
        self.assertEqual(changed,sorted((old.file_id(1,0),old.file_id(3,0))))
        seq=old.file_id(1,0);self.assertEqual(old.blob(seq)[:0x20+a.FIRST*12],live.blob(seq)[:0x20+a.FIRST*12])
        self.assertEqual(live.blob(seq),muted.blob(seq));wid=old.file_id(3,0);oo=old.blob(wid);ll=live.blob(wid);mm=muted.blob(wid)
        self.assertEqual(len(ll),len(mm));self.assertEqual(ll[:0x3c+(a.FIRST+a.COUNT)*4],mm[:0x3c+(a.FIRST+a.COUNT)*4])
        for i in range(a.FIRST):
            start=w.u32(oo,0x3c+i*4);end=w.u32(oo,0x3c+(i+1)*4)
            self.assertEqual(oo[start:end],ll[start:end])
        for i in range(a.FIRST,a.FIRST+a.COUNT):
            start=w.u32(ll,0x3c+i*4);end=w.u32(ll,0x3c+(i+1)*4) if i+1<a.FIRST+a.COUNT else w.u32(ll,8)
            self.assertEqual(ll[start],1);self.assertEqual(ll[start:start+12],mm[start:start+12]);self.assertEqual(set(mm[start+12:end]),{0})
