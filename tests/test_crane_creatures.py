"""Original creature asset integrity and strict room-scoped adapter behavior."""
import struct,unittest
import mod
from tools import crane_creatures as c,crane_creature_motion as motion,wos_tool as w
from tools.custom_formats import Xbd
from tools.animation_rig import AnimationRig
from tools.model_geometry import ModelGeometry
from tools.nitro_texture import TextureArchive
from tools.sca import Sca,rotation_q12
from tools.sca_author import repack_samples,sample
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob
from tests.arm_runtime import ArmProbe

class CreatureAdapterTests(unittest.TestCase):
    AT=0x0215A000;STOP=0x03004000;OUT=0x02210000;STATS=0x02211000;STATE=0x02212000
    CONFIGS={'maw':0x0215AA00,'ballast':0x0215AA54,'spore':0x0215AAA8}
    GOALS={'opening':0x0215AC00,'patrol':0x0215AC18,'crew':0x0215AC30,'upper':0x0215AC48}
    def probe(self,raw,room,value,stats=True):
        p=ArmProbe();p.code(self.AT,raw);p.put(0x02145C5C,self.STATS if stats else 0);p.put(self.STATS,room)
        p.put(self.OUT,0);p.put(self.STATE,0);p.put(self.STATE+4,0)
        p.put(self.STATS+0x2C,0)
        for spec in c.CREATURES:p.put(c.CONFIG_TABLE+(spec.kind-2)*84+0x50,0x70+spec.kind)
        regs=[self.OUT,value,2,3,4,5,6,7,8,9,10,11,12,0x023FF000,self.STOP,self.AT]
        return p,regs

    def test_config_overrides_only_three_types_in_the_twelve_rooms_and_preserves_flags_registers(self):
        raw=c.config_adapter(self.AT,self.CONFIGS)
        for room in (0,38,70,95,96,100,107,108,255,0xFFFFFFFF):
            for kind in (0,1,2,20,21,36,39,40,50,74,255):
                p,regs=self.probe(raw,room,kind);before=list(regs);initial=0xF800001F
                got,flags,pc=p.run(regs,initial,{self.STOP,c.CONFIG_SITE+4})
                selected=next((s.key for s in c.CREATURES if s.kind==kind),None) if 96<=room<108 else None
                self.assertEqual(pc,self.STOP if selected else c.CONFIG_SITE+4)
                self.assertEqual(p.get(self.OUT),self.CONFIGS[selected] if selected else 0)
                self.assertEqual(got[:13],before[:13]);self.assertEqual(got[14],before[14]);self.assertEqual(flags,initial)
                self.assertEqual(got[13],before[13] if selected else before[13]-16)
        p,regs=self.probe(raw,100,21,stats=False)
        self.assertEqual(p.run(regs,0xA800001F,{self.STOP,c.CONFIG_SITE+4})[2],c.CONFIG_SITE+4)

    def test_variant_cycle_resets_by_room_and_hoist_opens_with_one_maw(self):
        raw=c.variant_adapter(self.AT,self.STATE);p,regs=self.probe(raw,96,8)
        for room,wanted in ((96,[21,20,36,21,20,36]),(100,[21,20,36]),(106,[21,21,21]),(105,[21,20,36])):
            p.put(self.STATS,room)
            for kind in wanted:
                before=list(regs);got,flags,pc=p.run(regs,0xA800001F,{self.STOP,c.VARIANT_NATIVE})
                self.assertEqual(pc,self.STOP);self.assertEqual(p.get(self.OUT),kind)
                self.assertEqual(got[:15],before[:15]);self.assertEqual(flags,0xA800001F)
        for room in (0,70,95,108,0xFFFFFFFF):
            p,regs=self.probe(raw,room,8);before=dict(p.memory)
            got,flags,pc=p.run(regs,0xF800001F,{self.STOP,c.VARIANT_NATIVE})
            self.assertEqual(pc,c.VARIANT_NATIVE);self.assertEqual(got[:15],regs[:15]);self.assertEqual(flags,0xF800001F)
            self.assertEqual(p.get(self.STATE),0);self.assertEqual(p.get(self.STATE+4),0);self.assertEqual(p.get(self.OUT),0)

    def test_goal_wrapper_keeps_native_initialization_and_result_registers_for_every_room(self):
        raw=c.goal_adapter(self.AT,self.GOALS)
        for room,table in ((r,t) for r in (0,70,95,96,97,99,100,102,103,105,106,107,108) for t in (8,14)):
            p,regs=self.probe(raw,room,table);initial=list(regs);called=[]
            def native(p,r,flags):
                called.append((r[0],r[1]));p.put(r[0],0x021366F4)
                r[0]=0x021366F4;r[1]=0xABCD;r[2]=0x1234;r[3]=0x5678;r[12]=0x9ABC
                return 0x7800001F
            got,flags,pc=p.run(regs,0xA800001F,{self.STOP},{c.GOAL_NATIVE:native})
            wanted=self.GOALS['opening' if room==106 else 'upper' if table==14 and room in (96,102,103) else 'crew' if room in (97,100,105) else 'patrol'] if 96<=room<108 else 0x021366F4
            self.assertEqual(called,[(self.OUT,table)]);self.assertEqual(p.get(self.OUT),wanted)
            self.assertEqual(got[:4],[0x021366F4,0xABCD,0x1234,0x5678]);self.assertEqual(got[12],0x9ABC)
            self.assertEqual(got[4:12],initial[4:12]);self.assertEqual(got[13:15],initial[13:15]);self.assertEqual(flags,0x7800001F)

    def test_saved_crew_clears_select_patrol_budgets(self):
        raw=c.goal_adapter(self.AT,self.GOALS)
        for room,mask in ((97,1),(100,2),(105,4)):
            p,regs=self.probe(raw,room,8);p.put(self.STATS+0x2C,mask<<16)
            def native(p,r,flags):p.put(r[0],0x021366F4);return flags
            p.run(regs,0xF800001F,{self.STOP},{c.GOAL_NATIVE:native})
            self.assertEqual(p.get(self.OUT),self.GOALS['patrol'])

    def test_private_reward_set_has_a_scoped_getter_with_native_fallback(self):
        record=0x0215AD00;raw=c.reward_adapter(self.AT,record)
        for room in (0,70,95,96,101,107,108):
            for kind in (0,9,16,c.REWARD_SET,32):
                p,regs=self.probe(raw,room,kind);got,flags,pc=p.run(regs,0xF800001F,{self.STOP,c.REWARD_SITE+4})
                selected=96<=room<108 and kind==c.REWARD_SET
                self.assertEqual(pc,self.STOP if selected else c.REWARD_SITE+4)
                self.assertEqual(p.get(self.OUT),record if selected else 0)
                self.assertEqual(got[:13],regs[:13]);self.assertEqual(got[14],regs[14]);self.assertEqual(flags,0xF800001F)


@unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original missing')
class CreatureAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom,g,m=mod.load_clean();es={e['name']:e for e in m['entries']}
        cls.blob=staticmethod(lambda n:g[es[n]['offset']:es[n]['offset']+es[n]['size']])
        cls.names=list(es);h=w.parse_header(rom);cls.arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        cls.extra,cls.links,cls.report=c.prepare(cls.blob,cls.names)

    def test_models_are_original_gpu_streams_with_native_rig_and_safe_per_creature_budgets(self):
        for spec in c.CREATURES:
            raw=self.extra['zz_CR_'+spec.key+'.nsbmd'];source=self.blob(spec.stem+'.nsbmd')
            a,b=ModelGeometry.parse(source),ModelGeometry.parse(raw)
            self.assertEqual(AnimationRig.parse(raw).names,AnimationRig.parse(source).names)
            self.assertEqual(AnimationRig.parse(raw).parents,AnimationRig.parse(source).parents)
            end=a.model+w.u32(source,a.model+8)
            self.assertEqual(raw[a.model+64:end],source[a.model+64:end])
            self.assertTrue(all(s.start>=len(source) for s in b.shapes))
            self.assertLess(self.report[spec.key]['quads'],400)
            t=self.extra['zz_CR_'+spec.key+'.nsbtx'];self.assertEqual(TextureArchive.parse(t).to_bytes(),t)

    def test_authored_attack_pose_does_not_depend_on_native_attack_rotations(self):
        for spec in c.CREATURES:
            clip=next(x for x in self.report[spec.key]['clips'] if x['mode']=='attack')
            source=self.blob(clip['source']);a=Sca.parse(source)
            changed=repack_samples(source,rotations={3:[rotation_q12('x',65)]*a.frame_count})
            idle=self.blob(spec.stem+'_Idle.sca');parents=AnimationRig.parse(self.blob(spec.stem+'.nsbmd')).parents
            raw,_=motion.author(changed,idle,parents,spec.key,clip['mode'],clip['contact_start'],clip['contact_end'])
            mine=Sca.parse(self.extra[clip['authored']]);other=Sca.parse(raw)
            self.assertEqual((mine.frame_count,mine.joint_count),(a.frame_count,a.joint_count))
            count=0
            for j in range(28):
                for f in range(a.frame_count):
                    self.assertEqual(mine.rotation(j,f),other.rotation(j,f))
                    self.assertEqual(sample(mine,j,f,'scale'),sample(a,j,f,'scale'))
                    count+=mine.rotation(j,f)!=a.rotation(j,f)
            self.assertGreater(count,a.frame_count*6)

    def test_every_animation_binding_has_a_species_route_including_reactions_and_death(self):
        for spec in c.CREATURES:
            xbd=Xbd.parse(self.blob(spec.stem+'.xbd'),self.names)
            routes=[b for b in xbd.bindings if b['tag']==0]
            mapping=self.links['zz_CR_'+spec.key+'.xbd']
            self.assertTrue(all(b['offset'] in mapping for b in routes))
            self.assertTrue({'die','hurt','bound','air'}<={clip['mode'] for clip in self.report[spec.key]['clips']})

    def test_authored_display_lists_allow_native_colour_tints(self):
        sizes={0:0,0x14:1,0x40:1,0x22:1,0x23:2,0x41:0}
        for spec in c.CREATURES:
            raw=self.extra['zz_CR_'+spec.key+'.nsbmd'];model=ModelGeometry.parse(raw)
            for shape in model.shapes:
                at=shape.start;end=at+shape.length;vertices=0
                while at<end:
                    commands=raw[at:at+4];at+=4
                    for op in commands:
                        self.assertIn(op,sizes,'A baked COLOR command would mask native hurt/death feedback')
                        at+=sizes[op]*4;vertices+=op==0x23
                self.assertEqual(at,end);self.assertGreater(vertices,100)

    def test_all_xbd_changes_are_explicit_appended_bindings_with_opaque_tail_retained(self):
        names=self.names+list(self.extra);blobs=[self.blob(n) for n in self.names]+list(self.extra.values())
        out=c.bind_xbds(names,blobs,self.links)
        for spec in c.CREATURES:
            target='zz_CR_'+spec.key+'.xbd';source=self.blob(spec.stem+'.xbd');a=Xbd.parse(source,names)
            raw=out[names.index(target)];b=Xbd.parse(raw,names)
            self.assertEqual(raw[:20],source[:20]);self.assertEqual(raw[a.opaque_tail_start:],source[a.opaque_tail_start:])
            for before,after in zip(a.bindings,b.bindings):
                wanted=self.links[target].get(before['offset'],before['name'])
                self.assertEqual(after['name'],wanted)

    def test_configs_preserve_unknown_bytes_and_actor_costs_without_touching_original_table(self):
        original=bytes(self.arm)
        for i,spec in enumerate(c.CREATURES):
            before=self.arm[c.CONFIG_TABLE-0x2000000+(spec.kind-2)*84:c.CONFIG_TABLE-0x2000000+(spec.kind-1)*84]
            after=c.character_config(self.arm,spec,182+i)
            self.assertEqual(w.u32(after,0),w.u32(before,0));self.assertEqual(w.u32(after,8),182+i)
            self.assertEqual(w.u32(after,12),spec.hp*4096)
            self.assertEqual(w.u32(after,0x50),c.REWARD_SET)
            self.assertEqual(after[:8]+after[16:0x50],before[:8]+before[16:0x50])
        self.assertEqual(self.arm,original)

    def test_private_drop_set_preserves_native_xp_and_lp_with_a_positive_small_health_roll(self):
        raw=c.reward_config(self.arm);start=c.REWARD_TABLE-0x02000000+9*48
        native=self.arm[start:start+48]
        self.assertEqual(raw[8:],native[8:]);self.assertEqual(struct.unpack_from('<2i',raw),(1024,2048))
        self.assertEqual(struct.unpack_from('<2i',raw,16),(10*4096,12*4096))

    def test_motion_geometry_retains_native_movement_flags_unknown_words_and_framing(self):
        for spec in c.CREATURES:
            source=Xbd.parse(self.blob(spec.stem+'.xbd'),self.names)
            mapping=self.links['zz_CR_'+spec.key+'.xbd']
            for binding in source.bindings:
                target=mapping.get(binding['offset'])
                if not target or not target.endswith('.gmb'):continue
                before=Gmb.parse(CompressedBlob.parse(self.blob(binding['name'])).decoded)
                after=Gmb.parse(CompressedBlob.parse(self.extra[target]).decoded)
                self.assertEqual((before.record_count,len(before.channels)),(after.record_count,len(after.channels)))
                allowed=set()
                for a,b in zip(before.channels,after.channels):
                    self.assertEqual((a.kind,a.stride,a.offset),(b.kind,b.stride,b.offset))
                    for f in range(before.record_count):
                        words=a.words(f)
                        changed=range(1,5) if a.kind==3 and words[7] in (0,4096,8192) else range(3) if a.kind==0 and words[6]==36864 else ()
                        for word in changed:
                            allowed.update(range(a.offset+4+f*a.stride+word*4,a.offset+4+f*a.stride+word*4+4))
                differences={i for i,(a,b) in enumerate(zip(before.raw,after.raw)) if a!=b}
                self.assertTrue(differences<=allowed,target)
                self.assertEqual(len(before.raw),len(after.raw))

    def test_goal_budgets_allow_the_trio_keep_native_costs_and_initialize_weights(self):
        configs=c.goal_configs(self.arm)
        for key,expected in (('patrol',(8,4)),('crew',(12,4)),('opening',(1,1)),('upper',(4,2))):
            raw=configs[key];self.assertEqual(struct.unpack_from('<2I',raw),tuple(x*4096 for x in expected))
            native=self.arm[c.GOAL_TABLE-0x2000000+8*24:c.GOAL_TABLE-0x2000000+9*24]
            self.assertEqual(raw[8:20]+raw[21:],native[8:20]+native[21:])
            self.assertGreater(raw[20],0)
        self.assertLessEqual(sum(s.cost for s in c.CREATURES),w.u32(configs['crew'],4)//4096)

    def test_full_four_unit_roster_fits_ds_vertex_buffer_with_room_player_and_prop_margin(self):
        import itertools
        player=self.blob('spd.nsbmd');player_vertices=w.u16(player,ModelGeometry.parse(player).model+36)
        for counts in itertools.product(range(5),repeat=3):
            if sum(n*s.cost for n,s in zip(counts,c.CREATURES))>4:continue
            creature_vertices=sum(n*self.report[s.key]['quads']*4 for n,s in zip(counts,c.CREATURES))
            # Largest shipped Crane room:370 quads. Reserve384 vertices for
            # existing props/FX, before any camera clipping or face culling.
            self.assertLessEqual(creature_vertices+370*4+player_vertices+384,6144,counts)


class CreatureTelemetryTests(unittest.TestCase):
    def test_duel_controller_releases_y_between_presses_and_pursues_with_native_inputs(self):
        from tools.crane_creature_lab import fight_buttons
        sequence=[fight_buttons(f,4,0) for f in range(16)]
        self.assertEqual([f for f,b in enumerate(sequence) if 'Y' in b],[0,1,2,8,9,10])
        self.assertIn('Left',fight_buttons(30,-20,0));self.assertNotIn('Y',fight_buttons(30,-20,0))
        self.assertIn('B',fight_buttons(30,20,16))
        from tools.crane_creature_lab import pursuit_buttons
        from types import SimpleNamespace
        # Jump before approaching a wall beside an automatic ground exit.
        state=SimpleNamespace(pos=(12,5),state=0,room=105)
        buttons=pursuit_buttons(40,state,{'position':(20*4096,80*4096)})
        self.assertIn('B',buttons);self.assertNotIn('Left',buttons)

    def test_fast_slam_only_changes_two_contact_frames_and_keeps_opaque_event_tail(self):
        raw=struct.pack('<6H',2,1,1,6,1,5)+b'\xff'*6+b'\0\0'
        result=c.attack_events(c.BY_KEY['ballast'],'brt_GroundAttack2.sca',raw)
        self.assertEqual({i for i,(a,b) in enumerate(zip(raw,result)) if a!=b},{0,6})
        self.assertEqual(result[12:],raw[12:])
        self.assertEqual(c.attack_events(c.BY_KEY['maw'],'brt_GroundAttack2.sca',raw),raw)

    def test_health_drops_survive_healing_and_gauge_is_reported_without_a_hit_count(self):
        from tools.crane_creature_lab import summarize
        def row(hp,enemy_hp,gauge):
            return {'hp':hp,'gauge':gauge,'player_state':15,'enemies':[
                {'actor':0x02230000,'key':'maw','hp':enemy_hp,'action':55}]}
        out=summarize([row(24576,90000,0),row(20000,88000,4096),row(24576,86000,8192)])
        self.assertTrue(out['incoming_damage_observed']);self.assertEqual(out['damaged'],['maw'])
        self.assertEqual(out['peak_combo_gauge_q12'],8192)
        self.assertNotIn('hits',out)

if __name__=='__main__':unittest.main()
