import unittest
import json
import mod
from tools import tasm_oscorp_rush as r, combat_profile as cp, combat_flow as f,training_refill as t,wos_tool as w
from tools import combat_readability as q
from tools.grip_compression import CompressedBlob
from tools.gmb import Gmb
from tools.sca import Sca
from tools.qol_suits_menu import StringSlots

@unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original absent')
class LocalRushTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.glob,cls.manifest=mod.load_clean()
        cls.entries={e['name']:e for e in cls.manifest['entries']}

    def clean(self,name):
        e=self.entries[name];return self.glob[e['offset']:e['offset']+e['size']]

    def test_root_round_trip_confinement_and_exact_revert(self):
        for name,(count,end,distance) in r.ROOTS.items():
            source=CompressedBlob.parse(self.clean(name));before=Gmb.parse(source.decoded)
            after=Gmb.parse(CompressedBlob.parse(r.advance(self.clean(name),name)).decoded)
            self.assertEqual(after.to_bytes(),after.raw)
            allowed=set()
            restored=after.raw
            for i in range(count):
                at=before.channels[0].offset+4+32*i+8;allowed.update(range(at,at+4))
                restored=Gmb.parse(restored).replace_word(0,i,2,before.channels[0].words(i)[2])
            self.assertEqual(restored,before.raw)
            self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(before.raw,after.raw)) if a!=b))
            roots=[after.channels[0].words(i)[2] for i in range(count)]
            self.assertEqual(roots[0],0);self.assertEqual(roots[end:], [distance]*(count-end))
            self.assertTrue(all(a<=b for a,b in zip(roots,roots[1:])))
            self.assertEqual(len(after.raw),len(before.raw))
            with self.assertRaises(ValueError):r.advance(r.advance(self.clean(name),name),name)

    def test_post_contact_pose_round_trip_and_revert(self):
        raw=self.clean(r.POSE_ASSET);before=Sca.parse(raw);changed=r.recovery_pose(raw);after=Sca.parse(changed)
        self.assertEqual(after.to_bytes(),changed)
        allowed=set();restored=bytearray(changed)
        for frame,_ in r.POSE_KEYS:
            at=before.rotation_offset(3,frame);allowed.update(range(at,at+18));restored[at:at+18]=raw[at:at+18]
        self.assertEqual(restored,raw)
        self.assertTrue(all(i in allowed for i,(a,b) in enumerate(zip(raw,changed)) if a!=b))
        self.assertEqual(after.frames[:10],before.frames[:10])

    def test_native_engine_gate_budget_purchase_and_snap_unchanged(self):
        a,_=cp.apply_rom(self.rom,r.PROFILE);b,_=cp.apply_rom(self.rom,'tasm-combat-flow')
        h=w.parse_header(a);at=h['arm9_offset'];restored=bytearray(a)
        restored[at+t.OFFSET:at+t.OFFSET+0x180]=b[at+t.OFFSET:at+t.OFFSET+0x180]
        self.assertEqual(restored,b)
        self.assertEqual(w.sha256(a[at:at+h['arm9_size']]),t.ARM9_SHA256)
        with self.assertRaises(ValueError):t.apply_rom(self.rom)
        with self.assertRaises(ValueError):t.apply_rom(a)
        # Asset ownership is separate from logical action: only paid red 61/62.
        catalog=json.loads((mod.ROOT/'docs/ORIGINAL_GAMEPLAY.json').read_text())
        row=next(x for x in catalog['red_purchases'] if x['ability_bit']==16)
        self.assertEqual(row['cost'],400)
        self.assertNotIn('spd_GroundAttack15.gmb',r.ROOTS)
        self.assertNotEqual(r.POSE_ASSET,'spd_GroundAttack15.sca')
        self.assertNotIn('spd.xbd',r.ROOTS)

    def test_text_preserves_other_composed_slots_and_is_idempotent(self):
        from tools.oscorp_resources import EXTRA_NAMES
        overlays=mod.overlay_files(mod.ROOT/'mods',list(self.entries),added_names=EXTRA_NAMES)
        # Test this release's historical prerequisite text, not a later full
        # choreography release's revised instructions.
        q.compose(self.glob,self.manifest,overlays,f.TEXT_EDITS | r.TEXT_EDITS)
        before=dict(overlays)
        q.compose(self.glob,self.manifest,overlays,f.TEXT_EDITS | r.TEXT_EDITS)
        once=dict(overlays);q.compose(self.glob,self.manifest,overlays,f.TEXT_EDITS | r.TEXT_EDITS);self.assertEqual(once,overlays)
        for name in ('English.strings','American.strings'):
            slots=StringSlots(self.clean(name))
            for i in range(len(slots.texts)):
                self.assertEqual(slots.decode(overlays[name],i),r.TEXT_EDITS.get(i,slots.decode(before[name],i)))
        for name in set(overlays)-{'English.strings','American.strings'}:
            self.assertEqual(overlays[name],before[name])

if __name__=='__main__':unittest.main()
