import math,struct,unittest,json
from pathlib import Path
from tools import creature_forge_design as d,creature_forge_audio as a,creature_forge_motion as m,creature_forge_combat as c

class Programs(unittest.TestCase):
    def test_contact_windows_have_tells_recovery_and_unique_mechanics(self):
        self.assertEqual(sum(map(len,d.MOVES.values())),22)
        names=set()
        for style,moves in d.MOVES.items():
            for move in moves:
                self.assertNotIn(move.name,names);names.add(move.name)
                self.assertGreaterEqual(move.contacts[0][0],11)
                self.assertGreaterEqual(move.samples-move.contacts[-1][1],10)
                for start,end in move.contacts:self.assertLess(start,end);self.assertLess(end,move.samples)
                for f in range(move.samples):
                    self.assertTrue(all(math.isfinite(v) for v in d.hit_shape(move,f)))
                    if not any(x<=f<y for x,y in move.contacts):self.assertLess(d.hit_shape(move,f)[3],.2)
        self.assertEqual(d.arms('hLpr'),((7,8,9),(14,15,16)))
        self.assertEqual(d.arms('hRng'),((7,8,9),(14,15,16)))
        self.assertEqual(d.arms('brt'),((6,7,8),(13,14,15)))

    def test_ground_pulses_are_jumpable_and_show_matching_expansion(self):
        for style in d.STYLES:
            for move in d.MOVES[style]:
                if move.kind not in ('quake','fugue','march'):continue
                for start,end in move.contacts:
                    for f in range(start,end):
                        y,z,h,r=d.hit_shape(move,f);effect=d.fx(move,f)[0]
                        self.assertLessEqual(y+h/2,2.3)
                        self.assertAlmostEqual(effect[3][0]*2,r)

class Audio(unittest.TestCase):
    def test_nds_adpcm_known_predictor_and_low_nibble_first(self):
        raw=struct.pack('<hH',0,0)+bytes((0x71,))
        self.assertEqual(a.decode(raw),[0,2,15])
        values=[int(12000*math.sin(i*.08)) for i in range(6000)]
        encoded=a.encode(values);self.assertEqual(encoded[0],2)
        self.assertEqual(struct.unpack_from('<I',encoded,8)[0]*4,len(encoded)-12)
        decoded=a.decode(encoded[12:])[:len(values)]
        power=sum(v*v for v in values);noise=sum((x-y)**2 for x,y in zip(values,decoded))
        self.assertGreater(10*math.log10(power/noise),25)

    def test_pinned_recorded_layers_are_unique_and_not_clipped(self):
        from tools import wos_tool as w
        manifest=json.loads((a.DIR/'manifest.json').read_text());self.assertEqual(len(manifest['samples']),57)
        self.assertEqual(len({e['sha256'] for e in manifest['samples']}),57)
        for e in manifest['samples']:
            raw=(a.DIR/e['file']).read_bytes();self.assertEqual(w.sha256(raw),e['sha256'])
            self.assertGreater(e['snr_db'],20);self.assertLess(e['peak'],30000)

class NativeAssets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import mod
        from tools import wos_tool as w
        _,g,_=mod.load_clean();o,n,_=w.parse_glob(g);cls.blobs=dict(zip(n,(g[x:y] for x,y in zip(o,o[1:]))))

    def test_articulated_wrist_targets_and_scale_pools_roundtrip(self):
        from tools.sca import Sca
        from tools.sca_author import sample
        from tools.animation_rig import AnimationRig
        for style,stem in (('maw','hLpr'),('eye','hRng'),('warden','brt')):
            idle=Sca.parse(self.blobs[stem+'_Idle.sca']);parents=AnimationRig.parse(self.blobs[stem+'.nsbmd']).parents;move=d.MOVES[style][0]
            poses=[m.pose(idle,parents,style,stem,'GroundAttack1',f,move.samples,move) for f in range(move.samples)]
            raw=m.encode(self.blobs[stem+'_Idle.sca'],poses);parsed=Sca.parse(raw)
            self.assertEqual(parsed.frame_count,move.samples)
            for f,p in enumerate(poses):
                for j in range(28):
                    self.assertEqual(sample(parsed,j,f,'translation'),tuple(round(v*4096) for v in p.t[j]))
                    self.assertEqual(sample(parsed,j,f,'rotation'),m.stored(p.r[j]))
                for j in (23,27):self.assertEqual(sample(parsed,j,f,'scale'),p.forge_scale[j])
            _,positions=m.pose(idle,parents,style,stem).fk()
            for i,chain in enumerate(d.arms(stem)):
                error=math.dist(positions[chain[-1]],m.REST[style][2][i]);self.assertLess(error,.2)

    def test_sound_filter_scope_keeps_native_abi_and_flags(self):
        from tests.arm_runtime import ArmProbe
        at=0x2160000;old=0x215a000;stats=0x2210000
        for room in (75,76,89,107,108):
            for sound in (188,616,617,651,652,653,709):
                probe=ArmProbe();probe.code(at,c.sound_filter(at,old,652));probe.put(0x2145c5c,stats);probe.put(stats,room)
                regs=[0x2200000,sound,20,0,4,5,6,7,8,9,10,11,12,0x23ff000,0x3000000,at]
                out,flags,_=probe.run(regs,0xf800001f,{old})
                self.assertEqual(out[1],652 if 76<=room<108 and 617<=sound<=651 else sound)
                self.assertEqual(out[0],regs[0]);self.assertEqual(out[2:15],regs[2:15]);self.assertEqual(flags,0xf800001f)

    def test_ground_steering_rejects_a_reused_native_controller(self):
        from tests.arm_runtime import ArmProbe
        at=0x2160000;slots=0x2170000;ctl=0x2210000;actor=0x2220000;motion=0x2221000;end=0x3000000
        for actual in (0x215b114,0x2136880):
            probe=ArmProbe();probe.code(at,c.update(at,slots,0x2168000,0x2171000))
            for i,v in enumerate((ctl,actor,0x215b114,0,0,0,1,2560)):probe.put(slots+i*4,v)
            probe.put(ctl+0x14,1);probe.put(ctl+0x44,actor);probe.put(actor+0x40,actual);probe.put(actor+0x30,motion)
            probe.put(actor+0x18,123);probe.put(motion+0x180,0)
            regs=[ctl,ctl+0x14,2,3,4,5,6,7,8,9,10,11,12,0x23ff000,end,at]
            out,_,_=probe.run(regs,0x8000001f,{end},{0x2097e74:lambda p,r,f:f})
            self.assertEqual(probe.get(actor+0x18),2560 if actual==0x215b114 else 123)
            self.assertEqual(probe.get(motion+0x180),1 if actual==0x215b114 else 0)
            self.assertEqual(out[4:12],regs[4:12]);self.assertEqual(out[13],regs[13])

    def test_secondary_air_pass_keeps_authored_clip_and_native_interruptions(self):
        from tests.arm_runtime import ArmProbe
        at=0x2160000;slots=0x2170000;ctl=0x2210000;actor=0x2220000;end=0x3000000;cfg=0x215b114
        for native,active,hp,actual in ((5,1,100,cfg),(6,1,100,cfg),(28,1,100,cfg),(53,1,0,cfg),(5,0,100,cfg),(5,1,100,0x2136880)):
            probe=ArmProbe();probe.code(at,c.secondary(at,slots))
            for i,v in enumerate((ctl,actor,cfg,0,0,active,1,0)):probe.put(slots+i*4,v)
            probe.put(ctl+0x14,15);probe.put(ctl+0x44,actor);probe.put(actor+0x40,actual);probe.put(actor+0x44,hp)
            regs=[ctl,1,2,3,4,5,6,7,8,9,10,11,12,0x23ff000,end,at]
            def native_think(p,r,f):r[0]=native;return f
            out,_,_=probe.run(regs,0x8000001f,{end},{0x2095a78:native_think})
            self.assertEqual(out[0],0x7fffffff if native<=25 and active and hp>0 and actual==cfg else native)
            self.assertEqual(out[4:12],regs[4:12]);self.assertEqual(out[13],regs[13])

if __name__=='__main__':unittest.main()
