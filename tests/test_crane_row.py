"""Crane extension contracts and lossless authored resources; private ROM only."""
import json
import struct
import unittest
import mod
from tools import crane_rooms as c,crane_row as r,crane_boss as b,midnight_chapter as ch,room_doors as d
from tools import nitro_build as nb,room_collision as collision,room_script as s,tasm_kit as kit,wos_tool as w
from tools.nitro_texture import TextureArchive
from tools.room_objects import RoomObjects
from tools.room_events import Events


class CraneDefinitionTests(unittest.TestCase):
    def test_twelve_rooms_and_unique_safe_allocations(self):
        self.assertEqual(set(c.IDS.values()),set(range(96,108)))
        flags=list(c.VISITS.values())+list(c.FLAGS.values())
        self.assertEqual(len(flags),len(set(flags)))
        self.assertFalse(set(flags)&{ch.visited(x.index) for x in ch.ROOMS})
        self.assertFalse(set(flags)&set(ch.ROOM_FLAGS.values()))
        self.assertTrue(set(flags)<=set(ch.FREE_FLAGS))

    def test_all_connections_have_a_reciprocal_opposite_side(self):
        for (a,g),(b,spawn) in c.LINKS.items():
            if b=='Pier_Save02':continue
            other=next(i for i,p in enumerate(c.PORTS[b],1) if p[3]==spawn)
            self.assertEqual(c.LINKS[b,other],(a,c.PORTS[a][g-1][3]))
            self.assertNotEqual(c.PORTS[a][g-1][0],c.PORTS[b][other-1][0])

    def test_full_graph_reachable_and_office_has_no_enemy_spawner(self):
        seen={c.NAMES[0]}
        while True:
            more={b for (a,_),(b,_) in c.LINKS.items() if a in seen and b in c.IDS}-seen
            if not more:break
            seen|=more
        self.assertEqual(seen,set(c.NAMES))
        self.assertFalse(c.SPECS[c.NAMES[2]].gangs)
        self.assertEqual(c.SPECS[c.NAMES[2]].save,(48,7))

    def test_machine_meshes_roundtrip_with_native_vertex_range(self):
        for name,raw in b.models().items():
            with self.subTest(model=name):
                model=nb.model_parts(raw)
                self.assertEqual(nb.room_model(model),raw)
                self.assertEqual(len(model.streams),1)

    def test_arm_builder_resolves_forward_labels_and_blob_literals(self):
        a=b.Arm(0x02159000);a.b('end');a.lit(3,'record');a.label('end');a.emit(0xE12FFF1E);a.blob('record',b'abcd')
        raw=a.finish();words=struct.unpack('<5I',raw)
        self.assertEqual(r.target(a.at,words[0]),a.at+8)
        pointer=a.at+4+8+(words[1]&0xFFF)
        self.assertEqual(struct.unpack_from('<I',raw,pointer-a.at)[0],a.at+16)
        self.assertEqual(raw[16:],b'abcd')

    def test_arm_builder_rejects_out_of_range_branches_and_literals(self):
        with self.assertRaises(ValueError):b._branch(0,0x4000000)
        with self.assertRaises(ValueError):b._branch(0,3)
        a=b.Arm(0x02159000);a.lit(0,'far',1);a.emit(*([0xE1A00000]*1025))
        with self.assertRaises(ValueError):a.finish()


@unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original missing')
class CraneDataGatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw=mod.DEFAULT_ROM.read_bytes();h=w.parse_header(raw)
        cls.arm=raw[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]

    def execute(self,room,kind,mode=1,stats=True,manager=True):
        at=0x02159000;fallback=0x02157800;stop=0x03004000
        resources=dict(zip(('warning','motor','hook','shield','weight'),range(4100,4105)))
        code=b.data_adapter(self.arm,at,fallback,resources)
        memory={at+i:v for i,v in enumerate(code)}
        def put(address,value):
            memory.update({address+i:v for i,v in enumerate(struct.pack('<I',value))})
        def get(address):return int.from_bytes(bytes(memory[address+i] for i in range(4)),'little')
        output=0x02200000;stats_at=0x02200100;manager_at=0x02200400
        put(output,0);put(0x02145C5C,stats_at if stats else 0);put(stats_at,room)
        put(0x02145C34,manager_at if manager else 0);memory[manager_at+0x1C4]=mode
        regs=[output,kind,0x1234,0x5678]+[0]*8+[0x9ABC,0x03007F00,stop,at]
        original=list(regs);equal=False
        for _ in range(150):
            pc=regs[15]
            if pc in (fallback,stop):
                self.assertEqual(regs[:15],original[:15])
                pointer=get(output)
                return pc,bytes(memory[pointer+i] for i in range(64)) if pointer else None,resources
            word=get(pc);cond=word>>28;regs[15]=pc+4
            if not {0:equal,1:not equal,14:True}[cond]:continue
            if word>>25&7==5:
                offset=word&0xFFFFFF
                if offset&0x800000:offset-=1<<24
                regs[15]=pc+8+offset*4
            elif word&0xFFFF0000 in (0xE92D0000,0xE8BD0000):
                indexes=[i for i in range(16) if word>>i&1]
                if word&0xFFFF0000==0xE92D0000:
                    regs[13]-=4*len(indexes)
                    for i,index in enumerate(indexes):put(regs[13]+4*i,regs[index])
                else:
                    values=[get(regs[13]+4*i) for i in range(len(indexes))]
                    regs[13]+=4*len(indexes)
                    for index,value in zip(indexes,values):regs[index]=value
            elif word&0x0FF00000==0x03500000:
                equal=regs[word>>16&15]==word&255
            elif word&0x0FF00000 in (0x05900000,0x05D00000):
                base=word>>16&15;address=(pc+8 if base==15 else regs[base])+(word&0xFFF)
                regs[word>>12&15]=memory[address] if word&0x00400000 else get(address)
            elif word&0x0FF00000==0x05800000:put(regs[word>>16&15]+(word&0xFFF),regs[word>>12&15])
            else:self.fail(f'Unmodelled gateway instruction {word:08x}')
        self.fail('Gateway did not return')

    def test_every_other_room_and_kind_retains_native_handling_and_arguments(self):
        for room in (*range(102),103,104,105,107):
            for kind in range(64):
                path,data,_=self.execute(room,kind)
                self.assertEqual(path,0x02157800,(room,kind));self.assertIsNone(data)

    def test_warning_is_harmless_only_at_warning_spawn_and_live_keeps_native_data(self):
        _,data,resources=self.execute(106,0x11,1)
        self.assertEqual(w.u32(data,0),0);self.assertEqual(w.u32(data,8),resources['warning'])
        for mode in (0,2,3,4):
            path,data,_=self.execute(106,0x11,mode)
            self.assertEqual(path,0x02157800);self.assertIsNone(data)
        self.assertIsNone(self.execute(106,0x11,1,manager=False)[1])
        self.assertIsNone(self.execute(106,0x11,1,stats=False)[1])

    def test_machine_and_counterweight_records_keep_their_scopes(self):
        _,core,_=self.execute(106,b.CORE)
        original=bytearray(self.arm[0x138FD8+b.CORE*64:0x138FD8+(b.CORE+1)*64])
        struct.pack_into('<I',original,20,b.HEALTH)
        self.assertEqual(core,original)
        _,weight,resources=self.execute(102,b.HOOK)
        self.assertEqual(w.u32(weight,8),resources['weight'])
        self.assertIsNone(self.execute(102,b.MOTOR)[1])


@unittest.skipUnless(mod.DEFAULT_ROM.exists() and (mod.ROOT/'build/version-0.15.1-final/Versioned.nds').exists(),'Private baseline missing')
class CraneBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=(mod.ROOT/'build/version-0.15.1-final/Versioned.nds').read_bytes()
        cls.rom,cls.report=r.apply_rom(cls.parent)
        def parts(raw):
            h=w.parse_header(raw);arm=raw[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
            fs=next(e for e in w.validate_rom(raw,target=True)['nitrofs'] if e['name']=='Glob.bin')
            g=raw[fs['start']:fs['end']];offsets,names,_=w.parse_glob(g)
            return arm,{n:g[a:z] for n,a,z in zip(names,offsets,offsets[1:])}
        cls.arm,cls.assets=parts(cls.rom);cls.old_arm,cls.old_assets=parts(cls.parent)

    def test_original_chapter_and_every_unrelated_asset_are_exact(self):
        allowed={'Pier_Save02_app.obj','English.strings','American.strings','GlobFiles.txt','model_sheet.xbd'}
        for n,b in self.old_assets.items():
            if n not in allowed:self.assertEqual(self.assets[n],b,n)
        start=kit.SOURCE+kit.RESERVE;end=start+ch.ML_SPACE
        self.assertEqual(self.arm[start:end],self.old_arm[start:end])

    def test_lookup_preserves_all_old_entries_and_grows_save_bounds(self):
        at=kit.SOURCE+r.CR_BASE-kit.TARGET
        old=kit.SOURCE+ch.ML_BASE-kit.TARGET
        self.assertEqual(self.arm[at:at+96*4],self.old_arm[old:old+96*4])
        for site in (ch.SAVE_ROOM_CHECK,ch.RELOAD_ROOM_CHECK):
            self.assertEqual(w.u32(self.arm,site-r.BASE),ch.CMP_R1|108)
        for i in range(96,108):
            pointer=w.u32(self.arm,at+i*4)
            descriptor=kit.SOURCE+pointer-kit.TARGET
            self.assertEqual(w.u32(self.arm,descriptor+0x28),6)

    def test_appended_creature_groups_and_private_records_preserve_native_groups(self):
        from tools.actor_resources import ModelSheet
        from tools import crane_creatures as creatures
        old=ModelSheet.parse(self.old_assets['model_sheet.xbd']);new=ModelSheet.parse(self.assets['model_sheet.xbd'])
        self.assertEqual(new.groups[:len(old.groups)],old.groups)
        self.assertEqual(len(new.groups),len(old.groups)+3)
        runtime=self.report['creatures']['runtime']
        self.assertEqual(runtime['scope'],list(range(96,108)))
        for spec in creatures.CREATURES:
            at=kit.SOURCE+runtime['configs'][spec.key]-kit.TARGET
            self.assertEqual(w.u32(self.arm,at+8),runtime['groups'][spec.key])
            self.assertEqual(w.u32(self.arm,at),spec.cost*4096)
        for site in (creatures.CONFIG_SITE,creatures.VARIANT_CALL,creatures.GOAL_CALL):
            address=r.target(site,w.u32(self.arm,site-r.BASE))
            self.assertTrue(r.CR_BASE<=address<r.CR_BASE+self.report['table_bytes'])

    def test_navigation_hooks_reference_owned_goal_strings_and_fit_reservation(self):
        from tools import crane_navigation as nav
        for site in (nav.SCREEN_SITE,nav.OBJECTIVE_SITE):
            word=w.u32(self.arm,site-r.BASE)
            self.assertEqual(bool(word&0x01000000),site==nav.OBJECTIVE_SITE)
            pointer=r.target(site,word)
            self.assertTrue(r.CR_BASE<=pointer<r.CR_BASE+self.report['table_bytes'])
        pointer=r.target(nav.OBJECTIVE_SITE,w.u32(self.arm,nav.OBJECTIVE_SITE-r.BASE))
        at=kit.SOURCE+pointer-kit.TARGET
        code=nav.objective_adapter(pointer,0)
        # All four literal pointers must resolve to private title/body pairs.
        found=[]
        for i in range(0,len(code),4):
            word=w.u32(code,i)
            if word&0xFFFFF000!=0xE59F2000:continue
            address=w.u32(self.arm,at+i+8+(word&0xFFF))
            if address==0x02145C5C:continue
            self.assertTrue(r.CR_BASE<=address<r.CR_BASE+self.report['table_bytes']-7)
            pair=kit.SOURCE+address-kit.TARGET
            title,body=struct.unpack_from('<2I',self.arm,pair)
            from tools.qol_suits_menu import decode_grown
            titles=nav.GOAL_TITLES
            decoded=decode_grown(self.assets['English.strings'],title)
            self.assertIn(decoded,titles)
            found.append(decoded)
            self.assertEqual(decode_grown(self.assets['English.strings'],body),c.LINES[nav.GOAL_BODIES[titles.index(decoded)]])
        self.assertCountEqual(found,nav.GOAL_TITLES)
        self.assertLessEqual(self.report['table_bytes'],r.CR_SPACE)
        self.assertLess(max(m['id'] for m in self.report['messages'].values()),256)

    def test_all_models_textures_bsp_and_objects_roundtrip(self):
        for n in c.NAMES:
            with self.subTest(room=n):
                raw=self.assets[f'zz_{n}.nsbmd'];self.assertEqual(nb.room_model(nb.model_parts(raw)),raw)
                raw=self.assets[f'zz_{n}Textures.nsbtx'];self.assertEqual(TextureArchive.parse(raw).to_bytes(),raw)
                raw=self.assets[f'zz_{n}.bsp'];tree=collision.RoomCollision.parse(raw);tree.check_tree();self.assertEqual(tree.to_bytes(),raw)
                raw=self.assets[f'zz_{n}_app.obj'];parsed=RoomObjects.parse(raw);self.assertEqual(parsed.to_bytes(),raw)
                for rec in parsed.records:
                    self.assertEqual(Events.parse(rec.sections[1],rec.raw[3]).to_bytes(),rec.sections[1])

    def test_no_story_reward_grant_or_native_progress_write(self):
        for n in c.NAMES:
            parsed=RoomObjects.parse(self.assets[f'zz_{n}_app.obj'])
            for rec in parsed.records:
                for group in Events.parse(rec.sections[1],rec.raw[3]).groups:
                    for cmd in group.commands:
                        self.assertNotEqual(cmd.opcode,0x1F,n)
                        if cmd.opcode in (0x24,0x25,0x26):
                            flag=struct.unpack_from('<H',cmd.operand)[0]
                            self.assertIn(flag,(*c.VISITS.values(),*c.FLAGS.values(),*ch.ROOM_SCRATCH),n)

    def test_native_save_room_keeps_its_exit_and_gets_a_non_bouncing_return(self):
        raw=self.assets['Pier_Save02_app.obj'];old=self.old_assets['Pier_Save02_app.obj']
        self.assertEqual(d.exits(raw)[:len(d.exits(old))],d.exits(old))
        self.assertEqual(d.spawns(raw)[:len(d.spawns(old))],d.spawns(old))
        arrival=next(p for p in d.spawns(raw) if p.spawn_id==2)
        self.assertLess(arrival.x/4096,48)

    def test_area_and_message_tables_are_bounded_and_not_overlapping_adapters(self):
        self.assertLess(self.report['table_bytes'],r.CR_SPACE)
        self.assertGreaterEqual(len(self.report['area_references']),4)
        self.assertLess(ch.MESSAGE_FIRST+len(ch.LINES)+len(c.LINES),256)

    def test_high_hatches_require_button_and_ground_doors_walk_in(self):
        from tools.room_entities import Entities
        for name in c.NAMES:
            rec=RoomObjects.parse(self.assets[f'zz_{name}_app.obj']).records[0]
            entities=Entities.parse(rec.sections[0]).records
            for group,port in enumerate(c.PORTS[name],1):
                trigger=next(e for e in entities if len(e)==28 and w.u32(e,12)==7 and e[27]==group+1)
                self.assertEqual(trigger[26],0 if port[2] else 2,(name,group))

    def test_scoped_hp_hook_preserves_native_fallback(self):
        site=b.HP_SITE-r.BASE;word=w.u32(self.arm,site)
        self.assertEqual(word>>24,0xEA)
        at=kit.SOURCE+r.target(b.HP_SITE,word)-kit.TARGET
        adapter=b.hp_adapter(r.target(b.HP_SITE,word))
        self.assertEqual(self.arm[at:at+len(adapter)],adapter)
        words=struct.unpack(f'<{len(adapter)//4}I',adapter)
        self.assertIn(0xE352006A,words)  # room 106
        self.assertIn(0xE3520021,words)  # native animated core kind
        self.assertIn(0xE5D221C1,words)  # current exposure, not cached actor state
        self.assertIn(0xE92D000F,words)  # displaced native prologue

    def test_live_lane_objects_fit_the_warning_centres(self):
        from tools.room_entities import Entities
        parsed=RoomObjects.parse(self.assets['zz_AR_LongArm_app.obj']);rec=parsed.records[1]
        arcs=[e for e,label in zip(Entities.parse(rec.sections[0]).records,parsed.names[1].labels) if label=='Object (Cargo Impact)']
        self.assertEqual(len(arcs),3)
        self.assertTrue(all(len(e)==28 and w.u32(e,12)==14 and e[22]==0x11 for e in arcs))
        self.assertEqual(sorted(struct.unpack_from('<i',e)[0]//4096 for e in arcs),list(b.LANES))


if __name__=='__main__':unittest.main()
