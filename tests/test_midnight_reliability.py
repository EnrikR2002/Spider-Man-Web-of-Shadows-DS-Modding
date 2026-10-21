"""Native contact, bounded poise, spawn stats and removed-route contracts."""
import struct,unittest
from pathlib import Path
from tests.arm_runtime import ArmProbe
from tools import midnight_reliability_combat as c,midnight_reliability_rooms as rooms,wos_tool as w


class Armour(unittest.TestCase):
    at=0x02180000;slots=at+0x3000;boss=at+0x4000;warden=at+0x4100;table=at+0x5000;cfgs=at+0x6000
    ctl=0x02200000;actor=ctl+0x1000;motion=ctl+0x2000;stats=ctl+0x3000;end=0x03000000
    def fixture(self,action=136,clock=0,counter=False,warden=False,room=89):
        p=ArmProbe();guard=self.at+0x1000;ward=self.at+0x1200;bt=self.at+0x2000;wt=bt+0x100
        p.code(self.at,c.armour(self.at,self.slots,self.boss,self.warden,guard,ward,self.table))
        p.code(guard,c.interval(guard,bt));p.code(ward,c.interval(ward,wt))
        for base,rows in ((bt,((136,12,15),(55,8,11))),(wt,((55,6,13),))):
            for i,row in enumerate((*rows,(0xffffffff,0,0))):
                for j,v in enumerate(row):p.put(base+i*12+j*4,v)
        cfg=self.warden if warden else self.boss;program=self.table+128 if counter else self.table
        p.put(self.ctl+0x14,15);p.put(self.ctl+0x44,self.actor);p.put(self.actor,0x021301d0);p.put(self.actor+0x40,cfg);p.put(self.actor+0x44,10000)
        p.put(self.actor+0x30,self.motion);p.put(self.motion,self.actor);p.put(self.motion+0x178,clock);p.put(self.motion+0x254,action)
        p.put(0x02145c5c,self.stats);p.put(self.stats,room)
        for i in range(32):p.put(self.slots+i*32,0)
        p.put(self.slots,self.ctl);p.put(self.slots+4,self.actor);p.put(self.slots+8,cfg);p.put(self.slots+20,program);p.put(program,action)
        return p
    def call(self,p):
        r=[self.ctl]+list(range(1,13))+[0x023ff000,self.end,self.at];out,_,_=p.run(r,0,{self.end});self.assertEqual(out[1:14],r[1:14]);return out[0]
    def test_same_native_carrier_has_different_normal_and_counter_commitment(self):
        for clock in (0,5,11,12,14,15,25,33,34,39):
            self.assertEqual(self.call(self.fixture(clock=clock,counter=False)),int(12<=clock<15))
            self.assertEqual(self.call(self.fixture(clock=clock,counter=True)),int(clock<34))
    def test_late_warden_gets_commitment_but_early_warden_remains_fully_interruptible(self):
        for room in (76,78,81,83,86,97):
            self.assertEqual(self.call(self.fixture(action=55,clock=8,warden=True,room=room)),int(room in (81,83,86)))
    def test_death_stale_slots_wrong_class_and_backlinks_never_get_poise(self):
        for where,value in ((self.actor+0x44,0),(self.actor,0x0212e3f0),(self.slots+4,self.actor+4),(self.motion,self.actor+4),(self.actor+0x40,self.boss+4)):
            p=self.fixture(clock=12,counter=True);p.put(where,value);self.assertEqual(self.call(p),0)


class ImpulseABI(unittest.TestCase):
    def test_guard_skips_only_impulse_writes_and_preserves_native_flags_and_registers(self):
        at=0x02180000;check=at+0x1000;debug=at+0x2000;ctl=0x02200000;actor=ctl+0x1000
        for protected in (False,True):
            p=ArmProbe();p.code(at,c.impulse(at,check,debug));p.put(ctl+0x44,actor);p.put(actor+0x44,10000);p.put(actor+0x18,3500);p.put(actor+0x1c,200);p.put(debug,0)
            def test(p,r,f):self.assertEqual(r[0],ctl);r[0]=int(protected);return f
            r=list(range(13))+[0x023ff000,0x023fff00,at];r[6]=ctl;out,flags,stop=p.run(r,0xa000001f,{0x02094d50,0x02094e08},{check:test})
            expected=r[:15];expected[1]=r[1] if protected else actor
            self.assertEqual(out[:15],expected);self.assertEqual(flags,0xa000001f);self.assertEqual(stop,0x02094e08 if protected else 0x02094d50)
            self.assertEqual(p.get(actor+0x44),10000);self.assertEqual(p.get(actor+0x18),3500);self.assertEqual(p.get(actor+0x1c),200);self.assertEqual(p.get(debug),int(protected))


class ActualContact(unittest.TestCase):
    def test_result_probe_reads_actual_attacker_victim_result_and_HP_without_mutation(self):
        at=0x02180000;cfg=at+0x1000;log=at+0x2000;actor=0x02200000;hero=actor+0x1000;motion=actor+0x2000;hm=actor+0x3000;stats=actor+0x4000;sp=0x023ff000
        for valid in (True,False):
            p=ArmProbe();p.code(at,c.hit_observer(at,cfg,log));p.put(log,0);p.put(actor,0x021301d0);p.put(actor+0x40,cfg if valid else cfg+4);p.put(actor+0x30,motion)
            p.put(hero,0x0212e3f0);p.put(hero+0x30,hm);p.put(sp+8,actor);p.put(sp+0x58,hero);p.put(sp+0x54,4);p.put(sp+0x8c,32)
            p.put(motion+0x254,136);p.put(motion+0x178,12);p.put(0x02145c5c,stats);p.put(stats+0x84,30000)
            for base,x,y in ((motion,80*4096,6*4096),(hm,86*4096,5*4096)):
                p.put(base+0x7c,x);p.put(base+0x80,y);p.put(base+0x160,0);p.put(base+0x164,0)
            r=list(range(13))+[sp,0x023fff00,at];out,flags,_=p.run(r,0xa000001f,{0x02078630});self.assertEqual(out[0],4);self.assertEqual(out[1:15],r[1:15]);self.assertEqual(flags,0xa000001f);self.assertEqual(p.get(stats+0x84),30000)
            self.assertEqual(p.get(log),int(valid))
            if valid:self.assertEqual([p.get(log+4+i*4) for i in range(8)], [136,12,32,4,30000,6*4096,5*4096,(-6*4096)&0xffffffff])


class LifecycleAndSpawn(unittest.TestCase):
    def test_native_arena_idle_resets_owners_without_touching_native_run_or_player_data(self):
        at=0x02180000;old=at+0x1000;state=at+0x2000;slots=at+0x3000;stats=0x02200000;manager=stats+0x1000
        for room,run,clear in ((89,0,True),(89,1,False),(86,0,False)):
            p=ArmProbe();p.code(at,c.lifecycle(at,old,state,slots));p.put(0x02145c5c,stats);p.put(stats,room);p.put(0x02145c34,manager);p.put(manager+0x1c0,run)
            for i in range(20):p.put(state+4*i,123)
            for i in range(32):p.put(slots+32*i,0x02210000+i*64)
            r=list(range(13))+[0x023ff000,0x023fff00,at];out,flags,_=p.run(r,0xa000001f,{old});self.assertEqual(out[:15],r[:15]);self.assertEqual(flags,0xa000001f)
            self.assertEqual(p.get(state),0 if clear else 123);self.assertEqual(p.get(slots),0 if clear else 0x02210000);self.assertEqual(p.get(manager+0x1c0),run)
    def test_spawn_scales_native_configs_and_caps_live_count_with_no_actor_HP_writes(self):
        at=0x02180000;old=at+0x1000;table=at+0x2000;cfglist=at+0x3000;slots=at+0x4000;marker=at+0x5000;stats=0x02200000;outptr=stats+0x1000
        configs=[at+0x6000+i*0x100 for i in range(3)]
        for live,previous in ((0,86),(4,86),(4,78)):
            p=ArmProbe();p.code(at,c.staged_spawn(at,old,table,cfglist,slots,marker));p.put(0x02145c5c,stats);p.put(stats,86);p.put(marker,previous)
            for i,v in enumerate((86,18*4096,26*4096,15*4096,0)):p.put(table+i*4,v)
            for i,cfg in enumerate(configs):p.put(cfglist+i*4,cfg);p.put(cfg+12,4096);p.put(cfg+16,0x12345678)
            for i in range(32):
                p.put(slots+i*32,0)
                if i<live:
                    actor=0x02210000+i*0x100;p.put(slots+i*32,actor+0x80);p.put(slots+i*32+4,actor);p.put(slots+i*32+8,configs[i%3]);p.put(actor,0x021301d0);p.put(actor+0x40,configs[i%3]);p.put(actor+0x44,7777)
            def native(p,r,f):p.put(outptr,20);return f
            r=[outptr]+list(range(1,13))+[0x023ff000,0x03000000,at];out,flags,_=p.run(r,0xa000001f,{0x03000000},{old:native});self.assertEqual(out[4:14],r[4:14]);self.assertEqual(flags,0xa000001f)
            self.assertEqual(p.get(outptr),36 if live==4 and previous==86 else 20);self.assertEqual(p.get(marker),86)
            for cfg,hp in zip(configs,(18,26,15)):self.assertEqual(p.get(cfg+12),hp*4096);self.assertEqual(p.get(cfg+16),0x12345678)
            if live:self.assertEqual(p.get(0x02210044),7777)


class GuardPressure(unittest.TestCase):
    def test_repeated_native_blocks_queue_counter_without_requiring_damage_and_death_wins(self):
        from tools import creature_forge_combat as forge
        at=0x02180000;records=at+0x3000;slots=at+0x4000;counts=at+0x5000;hero=at+0x6004;table=at+0x7000;state=at+0x8000;cfg=at+0x9000;check=at+0xa000
        ctl=0x02200000;actor=ctl+0x1000;motion=ctl+0x2000;stats=ctl+0x3000;end=0x03000000
        code=forge.think(at,records,slots,counts,hero,hero-4,at+0xb000,at+0xc000,653,rewrite=lambda s:c.decisions(s,at+0xd000,at+0xe000,state,table,hero,check))
        p=ArmProbe();p.code(at,code);p.put(0x02145c5c,stats);p.put(0x02145c34,0);p.put(stats,89);p.put(hero-4,89);p.put(hero,0)
        for i,v in enumerate((cfg,table,6,6)):p.put(records+i*4,v)
        for i,v in enumerate((ctl,actor,cfg,0,10,0,1,0)):p.put(slots+i*4,v)
        for i in range(20):p.put(state+i*4,0)
        p.put(ctl+0x44,actor);p.put(ctl+0x14,27);p.put(actor,0x021301d0);p.put(actor+0x40,cfg);p.put(actor+0x44,60000);p.put(actor+0x30,motion);p.put(motion,actor)
        kind=[27]
        def native(p,r,f):r[0]=kind[0];return f
        def poise(p,r,f):r[0]=0;return f
        r=[ctl]+list(range(1,13))+[0x023ff000,end,at]
        for n in range(12):
            out,_,_=p.run(r,0,{end},{0x02095834:native,check:poise});self.assertEqual(out[0],15 if n==11 else 27);self.assertEqual(p.get(actor+0x44),60000)
        self.assertEqual(p.get(slots+20),table+128);self.assertEqual(p.get(state+28),1)
        kind[0]=53;p.put(state+16,1);p.put(state+20,0);out,_,_=p.run(r,0,{end},{0x02095834:native,check:poise});self.assertEqual(out[0],53)


class Routes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r=(Path(__file__).resolve().parents[1]/'build/version-0.27.0-final/Versioned.nds').read_bytes();e=next(e for e in w.nitrofs_entries(r) if e['name']=='Glob.bin');g=r[e['start']:e['end']];o,n,_=w.parse_glob(g);cls.assets=dict(zip(n,(g[a:b] for a,b in zip(o,o[1:]))))
    def test_removed_branch_has_neither_trigger_nor_transition_and_preserves_other_records(self):
        from tools.room_objects import RoomObjects
        from tools.room_entities import Entities
        from tools import room_doors,room_script
        for name,target in (('ML_Station',77),('ML_NestShaft',82)):
            old=self.assets['zz_'+name+'_app.obj'];raw=rooms.remove_branch(old);p=RoomObjects.parse(raw);before=RoomObjects.parse(old)
            self.assertEqual(p.records[1].raw,before.records[1].raw);self.assertEqual(p.header[16:],before.header[16:]);room_script.counts(raw,0)
            self.assertFalse(any(e.room==target for e in room_doors.exits(raw)))
            self.assertFalse(any(len(e)==28 and w.u32(e,12)==7 and e[27]==4 for e in Entities.parse(p.records[0].sections[0]).records))
    def test_active_graph_is_eight_rooms_with_no_incoming_retired_edge(self):
        self.assertEqual(len(rooms.ACTIVE),8);self.assertEqual(len(rooms.LINKS),17)
        for (n,g),(d,sp) in rooms.LINKS.items():self.assertNotIn(n,('ML_Refuge','ML_NestRest'));self.assertNotIn(d,('ML_Refuge','ML_NestRest'))
        self.assertLess(rooms.CENTRES[87][0],rooms.CENTRES[89][0]);self.assertLess(rooms.CENTRES[89][0],rooms.CENTRES[88][0])
    def test_turbine_wave_is_authored_on_the_upper_tier_without_changing_main_exits(self):
        from tools.room_objects import RoomObjects
        from tools.room_entities import Entities
        from tools import room_doors
        old=self.assets['zz_ML_NestThroat_app.obj'];raw=rooms.upper_wave(old);p=RoomObjects.parse(raw)
        self.assertEqual(p.records[0].raw,RoomObjects.parse(old).records[0].raw);self.assertEqual(room_doors.exits(raw),room_doors.exits(old))
        found=[]
        for e,label in zip(Entities.parse(p.records[1].sections[0]).records,p.names[1].labels):
            if len(e)==28 and (w.u32(e,12)==4 or label=='Trigger (Encounter Approach)'):found.append(struct.unpack_from('<2i',e))
        self.assertEqual(found,[(132*4096,104*4096)]*2)


if __name__=='__main__':unittest.main()
