"""Overhaul contracts: original rooms, saved arrivals and chained scoped code."""
import json,struct,unittest
from pathlib import Path
import mod
from tools import midnight_rework as rw,midnight_rework_rooms as rooms,midnight_rework_creatures as c,midnight_rework_boss as b
from tools import midnight_chapter as ch,midnight_rooms as mr,room_compiler as rc,room_collision,nitro_build as nb
from tools import crane_creatures as cc,wos_tool as w
from tools.nitro_texture import TextureArchive
from tests.arm_runtime import ArmProbe

class AdapterTests(unittest.TestCase):
    AT=0x02162000;OUT=0x02210000;STATS=0x02211000;STATE=0x02212000;MANAGER=0x02213000;ACTOR=0x02214000;STOP=0x03004000;OLD=0x02159000
    def setup(self,raw,room,kind):
        p=ArmProbe();p.code(self.AT,raw);p.put(0x02145C5C,self.STATS);p.put(self.STATS,room);p.put(0x02145C34,self.MANAGER)
        p.put(self.OUT,0);p.put(self.STATE,0);p.put(self.STATE+4,0)
        regs=[self.OUT,kind,2,3,4,5,6,7,8,9,10,11,12,0x023FF000,self.STOP,self.AT]
        return p,regs
    def test_config_chain_scope_and_register_flags(self):
        configs=dict(maw=0x2164000,ballast=0x2164100,spore=0x2164200,boss=0x2164300)
        raw=c.config_adapter(self.AT,configs,self.OLD)
        for room in (0,70,75,76,78,89,94,95,96,107,108,0xFFFFFFFF):
            for kind in (0,20,21,36,39):
                p,regs=self.setup(raw,room,kind);before=list(regs)
                got,flags,pc=p.run(regs,0xF800001F,{self.STOP,self.OLD})
                key=next((x.key for x in c.CREATURES if x.kind==kind),None) if 76<=room<96 else None
                if room==89:key='boss' if kind==36 else None
                self.assertEqual(pc,self.STOP if key else self.OLD)
                self.assertEqual(p.get(self.OUT),configs[key] if key else 0)
                self.assertEqual(got[:15],before[:15]);self.assertEqual(flags,0xF800001F)
    def test_single_boss_variant_and_room_reset(self):
        raw=c.variant_adapter(self.AT,self.STATE,self.OLD);p,regs=self.setup(raw,78,8)
        for room,wanted in ((78,(21,36,20,21)),(89,(36,36,36)),(80,(21,36,20))):
            p.put(self.STATS,room)
            for kind in wanted:
                got,flags,pc=p.run(regs,0xA800001F,{self.STOP,self.OLD})
                self.assertEqual(p.get(self.OUT),kind);self.assertEqual(got[:15],regs[:15]);self.assertEqual(flags,0xA800001F)
    def test_boss_phase_follows_actual_health_and_never_heals_or_rewinds(self):
        raw=b.hp_adapter(self.AT)
        for room in (75,76,89,90,96):
            for hp,phase in ((64000,0),(32000,1),(16000,2),(1,2)):
                p,regs=self.setup(raw,room,hp);regs[0]=self.ACTOR;p.put(self.ACTOR,0x021301D0);p.put(self.ACTOR+0x48,64000)
                p.put(self.MANAGER+0x1C0,1);before=list(regs)
                got,flags,pc=p.run(regs,0xF800001F,{b.HP_SITE+4})
                self.assertEqual(p.memory[self.MANAGER+0x1C2],phase if room==89 else 0)
                self.assertEqual(got[:13],before[:13]);self.assertEqual(got[14],before[14]);self.assertEqual(flags,0xF800001F)
                self.assertEqual(got[13],before[13]-16)
                self.assertEqual(p.get(self.ACTOR+0x48),64000)
        p,regs=self.setup(raw,89,60000);regs[0]=self.ACTOR;p.put(self.ACTOR,0x021301D0);p.put(self.ACTOR+0x48,64000)
        p.put(self.MANAGER+0x1C0,0x00020001)
        p.run(regs,0xF800001F,{b.HP_SITE+4})
        self.assertEqual(p.memory[self.MANAGER+0x1C2],2)
    def test_sound_families_are_private_only_inside_midnight(self):
        raw=c.sound_adapter(self.AT,self.OLD)
        for room in (75,76,89,94,95,96,107):
            for value,index in ((306,0),(311,1),(316,2),(457,5),(480,10),(188,None)):
                p,regs=self.setup(raw,room,value);got,flags,pc=p.run(regs,0xF800001F,{cc.CONFIG_SITE,c.audio.SITE+4,self.OLD})
                selected=76<=room<96 and index is not None and (room!=89 or index<5)
                self.assertEqual(pc,c.audio.SITE+4 if selected else self.OLD)
                self.assertEqual(got[1],c.FIRST_SOUND+(15 if room==89 else 0)+index if selected else value)
                self.assertEqual(got[0],regs[0]);self.assertEqual(got[2:13],regs[2:13]);self.assertEqual(flags,0xF800001F)
    def test_rewards_chain_and_native_rooms_are_untouched(self):
        record=0x2164000;raw=c.reward_adapter(self.AT,record,self.OLD)
        for room in (0,75,76,89,95,96,107):
            for reward in (9,16,31,32):
                p,regs=self.setup(raw,room,reward);got,flags,pc=p.run(regs,0xF800001F,{self.STOP,self.OLD})
                yes=76<=room<96 and reward==31
                self.assertEqual(p.get(self.OUT),record if yes else 0);self.assertEqual(pc,self.STOP if yes else self.OLD)
                self.assertEqual(got[:15],regs[:15]);self.assertEqual(flags,0xF800001F)
    def test_objectives_follow_the_new_earned_flag_and_chain_native_crane(self):
        records=0x02165000;raw=rw.objective_adapter(self.AT,records,self.OLD)
        for room in (75,76,89,95,96,107):
            for complete in (0,1):
                p,regs=self.setup(raw,room,0);p.put(self.STATS+0x2C,complete<<19)
                got,flags,pc=p.run(regs,0xF800001F,{self.STOP,self.OLD})
                yes=76<=room<96
                self.assertEqual(pc,self.STOP if yes else self.OLD)
                self.assertEqual(p.get(self.OUT),records+complete*8 if yes else 0)
                self.assertEqual(got[0:2],regs[0:2]);self.assertEqual(got[3:15],regs[3:15]);self.assertEqual(flags,0xF800001F)
    def test_objective_copy_fits_the_native_six_line_panel(self):
        for text in (rw.OBJECTIVES[1],rw.OBJECTIVES[3]):
            self.assertLessEqual(len(text.splitlines()),6)
            self.assertTrue(all(len(line)<=34 for line in text.splitlines()))

@unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private ROM missing')
class RoomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom,g,m=mod.load_clean();entries={e['name']:e for e in m['entries']}
        cls.asset=staticmethod(lambda n:g[entries[n]['offset']:entries[n]['offset']+entries[n]['size']])
    def test_all_fifteen_clones_are_original_compiled_rooms_and_roundtrip(self):
        for name in rooms.NAMES:
            with self.subTest(room=name):
                plan=rooms.geometry(name);built=rc.compile_room(plan)
                self.assertEqual(TextureArchive.parse(built.textures).to_bytes(),built.textures)
                self.assertEqual(nb.room_model(nb.model_parts(built.model)),built.model)
                tree=room_collision.RoomCollision.parse(built.collision)
                self.assertEqual(tree.to_bytes(),built.collision)
                self.assertLess(built.quads,900)
                self.assertNotEqual(built.model,self.asset(ch.BY_NAME[name].source+'.nsbmd'))
                for door in rooms.SPECS[name].doors:
                    x,y,_=door.spawn['xyz'];self.assertIsNone(tree.solid_at(x/4096,y/4096+3))
    def test_saved_ids_and_every_incoming_spawn_are_retained(self):
        self.assertEqual([ch.BY_NAME[n].index for n in rooms.NAMES],list(range(76,91)))
        for (name,group),(dest,spawn) in ch.LINKS.items():
            if dest not in rooms.SPECS:continue
            self.assertIn(spawn,[d.spawn_id for d in rooms.SPECS[dest].doors],(name,group,dest,spawn))
            if name in rooms.SPECS:
                back=next(g for (n,g),(target,_) in ch.LINKS.items() if n==dest and target==name)
                self.assertEqual(rooms.SPECS[dest].doors[back-1].spawn_id,spawn,(name,group,dest,back))
                self.assertNotEqual(rooms.SPECS[name].doors[group-1].side,rooms.SPECS[dest].doors[back-1].side)
        self.assertIn(3,[d.spawn_id for d in rooms.SPECS['ML_Entry'].doors])
    def test_native_texture_bank_and_autoload_source_budgets(self):
        raw=nb.texture_archive(tuple(t for t,p in rooms.materials()),tuple(p for t,p in rooms.materials()))
        self.assertLess(len(raw),128*1024)
        from tools import tasm_kit as kit,crane_row
        self.assertLessEqual(0x02000000+kit.SOURCE+kit.RESERVE+ch.ML_SPACE+crane_row.CR_SPACE+rw.SPACE+36,kit.TARGET)
    def test_conductor_callbacks_are_guarded_and_future_attacks_stop_after_victory(self):
        from tests.test_midnight_boss import Script
        name='ML_Venom';spec=rooms.SPECS[name]
        from tools import room_catalog
        rom,_,manifest=mod.load_clean();h=w.parse_header(rom)
        native=room_catalog.parse(rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']],[e['name'] for e in manifest['entries']])
        source=next(r for r in native if r.name==mr.SOURCE)
        raw,_=ch.build_room(self.asset(mr.SOURCE+'_app.obj'),self.asset(mr.SOURCE+'_app.obj'),ch.Room(89,'MR_Empty',mr.SOURCE,'authored',True),source.index,[r.name for r in native],{})
        spawn,exit=ch.door_templates(self.asset)
        raw=mr.stage(raw,name,self.asset,room_of=lambda n:ch.BY_NAME[n].index,visited=ch.visited(89),spawn_template=spawn,exit_template=exit,
                     links=ch.LINKS,flags=ch.ROOM_FLAGS,authored=spec)
        raw=b.stage(raw,self.asset);sim=Script(raw)
        sim.run('Start');sim.run('Start');sim.advance(350)
        self.assertEqual(sim.vars[b.RUN],1);self.assertFalse(sim.vars.get(b.DEFEATED))
        self.assertEqual(sum(name=='The Conductor' for t,name in sim.events),1)
        sim.run('Victory');sim.run('Victory');sim.advance(5000)
        self.assertEqual(sim.vars[b.DEFEATED],1);self.assertEqual(sim.vars[b.LEGACY_DEFEATED],1)
        self.assertFalse(sim.live('Storm'));self.assertFalse(sim.live('The Conductor'));self.assertEqual(sim.vars[b.RUN],0)
        revisit=Script(raw,flags=(b.DEFEATED,));revisit.advance(5000)
        self.assertFalse(revisit.live('The Conductor'));self.assertFalse(revisit.live('Storm'))
    def test_overview_roundtrips_and_covers_all_twenty_rooms(self):
        from tools.minimap_cbmp import Cbmp
        raw,listing=rw.overview(self.asset(ch.MAP_SOURCE))
        self.assertEqual(Cbmp.parse(raw).to_bytes(),raw)
        self.assertEqual({n for n,_,_,_ in listing},{r.name for r in ch.ROOMS})
        self.assertTrue(all(slot+i not in ch.STATE_COLORS for n,slot,x,y in listing for i in range(5)))

if __name__=='__main__':unittest.main()
