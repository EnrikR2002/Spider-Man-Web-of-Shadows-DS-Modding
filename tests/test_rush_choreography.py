import json
from pathlib import Path
import unittest
import mod
from tools import wos_tool as w,combat_profile as cp,oscorp_animation as release
from tools.sca import Sca
from tools.sca_author import sample
from tools.animation_rig import AnimationRig
from tools.custom_formats import Xbd
from tools import rush_choreography as c
from tools import oscorp_resources as resources
import struct
from tools.qol_suits_menu import StringSlots
from tools import combat_readability as q,combat_flow,tasm_oscorp_rush

class MathTests(unittest.TestCase):
    def test_shortest_arc_and_stored_matrix_convention(self):
        for a,b in (((1,0,0),(0,1,0)),((1,0,0),(-1,0,0)),((0,0,1),(0,0,1))):
            r=c.align(a,b)
            for got,want in zip(c.mv(r,a),b):self.assertAlmostEqual(got,want,places=6)
            self.assertEqual(c.stored(c.decoded(c.stored(r))),c.stored(r))
            for i,row in enumerate(c.mm(r,c.transpose(r))):
                for j,value in enumerate(row):self.assertAlmostEqual(value,1 if i==j else 0,places=6)
    def test_quaternion_blending_is_rigid_through_a_half_turn(self):
        end=c.axis('y',180)
        for gain in (0.,.25,.5,.75,1.):
            r=c.tween_rotation(c.IDENTITY,end,gain)
            for i,row in enumerate(c.mm(r,c.transpose(r))):
                for j,value in enumerate(row):self.assertAlmostEqual(value,1 if i==j else 0,places=4)
        middle=c.tween_rotation(c.IDENTITY,end,.5)
        self.assertAlmostEqual(c.length(c.mv(middle,(1,0,0))),1,places=5)

@unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original absent')
class LocalChoreographyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.glob,cls.manifest=mod.load_clean();cls.entries={e['name']:e for e in cls.manifest['entries']}
        cls.names=list(cls.entries);cls.rig=AnimationRig.parse(cls.clean('spd.nsbmd'));cls.idle=cls.clean('spd_Idle.sca')
    @classmethod
    def clean(cls,name):
        e=cls.entries[name];return cls.glob[e['offset']:e['offset']+e['size']]
    def test_whole_clips_new_major_pose_sequences_and_native_scales(self):
        for variant,asset in (('entry','spd_GroundAttack16'),('bridge','spd_GroundAttack15'),('finish','spd_GroundAttack17')):
            raw=self.clean(asset+'.sca');before=Sca.parse(raw)
            changed,proof=c.author(raw,self.idle,self.rig.parents,variant);after=Sca.parse(changed)
            self.assertEqual(after.to_bytes(),changed)
            self.assertEqual((after.frame_count,after.joint_count),(before.frame_count,37))
            self.assertEqual(after.header[26:28],before.header[26:28]);self.assertEqual(after.static_pool,before.static_pool)
            self.assertEqual(after.descriptor_padding,before.descriptor_padding)
            for f in range(before.frame_count):
                for j in range(37):self.assertEqual(sample(after,j,f,'scale'),sample(before,j,f,'scale'))
                # Major chains are new throughout, rather than post-hit deltas.
                self.assertGreater(sum(after.rotation(j,f)!=before.rotation(j,f) for j in (1,2,3,7,8,17,18,26,27,30,31)),8)
                self.assertGreater(proof[f]['left_ankle'][1],.7)
                if variant!='bridge':self.assertAlmostEqual(proof[f]['right_ankle'][1],.78,delta=.12 if variant=='finish' and f>=14 else .04)
                self.assertAlmostEqual(proof[f]['left_ankle'][1],.78,delta=.12 if variant=='finish' and f>=14 else .04)
            if variant=='finish':
                idle=Sca.parse(self.idle)
                for j in range(37):
                    self.assertEqual(after.rotation(j,19),idle.rotation(j,0))
                    self.assertEqual(sample(after,j,19,'translation'),sample(idle,j,0,'translation'))
            self.assertEqual(c.author(raw,self.idle,self.rig.parents,variant)[0],changed)
        with self.assertRaises(ValueError):c.author(raw,self.idle,self.rig.parents,'entry')
    def test_paid_binding_isolation_no_snap_or_other_action_edits(self):
        # Recreate the accepted Snap route from the original XBD for a durable
        # fixture independent of which later gameplay recipe is published.
        raw=self.clean('spd.xbd');x=Xbd.parse(raw,self.names)
        for offset,extension in ((356,'.sca'),(360,'.gmb'),(364,'.gab')):
            raw=Xbd.parse(raw,self.names).replace_binding(offset,self.names.index('spd_GroundAttack15'+extension),self.names)
        names=[*self.names,*resources.EXTRA_NAMES]
        changed,proof=release.isolate_rush(raw,names);before=Xbd.parse(raw,names);after=Xbd.parse(changed,names)
        self.assertEqual(after.to_bytes(),changed);self.assertEqual(after.raw[after.opaque_tail_start:],before.raw[before.opaque_tail_start:])
        allowed={at for row in proof for at in (row['offset'],row['offset']+1)}
        self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(raw,changed)) if a!=b))
        self.assertEqual(changed[356:368],raw[356:368])
        self.assertEqual([row['offset'] for row in proof],[404,416,428])
        # Existing GMB/GAB and all non-Rush actors remain on their native IDs.
        for offset in (408,412,420,424,432,436):self.assertEqual(changed[offset:offset+4],raw[offset:offset+4])
        with self.assertRaises(ValueError):release.isolate_rush(changed,names)
    def test_native_engine_and_purchase_table_exactly_preserved(self):
        before,_=cp.apply_rom(self.rom,'tasm-oscorp-rush');after,_=cp.apply_rom(self.rom,release.PROFILE)
        h=w.parse_header(after);restored=bytearray(after)
        struct.pack_into('<I',restored,h['arm9_offset']+resources.COUNT_OFFSET,3733)
        self.assertEqual(before,restored)
    def test_new_input_text_preserves_every_other_current_slot(self):
        overlays=mod.overlay_files(mod.ROOT/'mods',self.names,added_names=resources.EXTRA_NAMES);before=dict(overlays)
        q.compose(self.glob,self.manifest,overlays,combat_flow.TEXT_EDITS | tasm_oscorp_rush.TEXT_EDITS | release.TEXT_EDITS)
        for name in ('English.strings','American.strings'):
            slots=StringSlots(self.clean(name))
            for index in range(len(slots.texts)):
                self.assertEqual(slots.decode(overlays[name],index),release.TEXT_EDITS.get(index,slots.decode(before[name],index)))
        for name in set(overlays)-{'English.strings','American.strings'}:self.assertEqual(overlays[name],before[name])

if __name__=='__main__':unittest.main()
