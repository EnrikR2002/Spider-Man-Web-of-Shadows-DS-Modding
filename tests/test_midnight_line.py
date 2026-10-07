"""Guarded namespace staging, capture checks, and occupied-resource rejection."""
from pathlib import Path
import struct
import unittest
from unittest import mock

import mod
from tools import midnight_line as ml, nitro_texture, room_extension as r, room_objects, room_entities, room_events, training_room


class CaptureTests(unittest.TestCase):
    def test_blank_capture_is_not_a_rendering_success(self):
        for rgb, expected in ((bytes(12),False), (b'\xff\0\0'*4,True)):
            data = nitro_texture.png_rgb(2,2,rgb)
            with mock.patch.object(Path,'read_bytes',return_value=data):
                self.assertEqual(ml.capture_not_black(Path('capture.png')),expected)

    def test_falling_and_ongoing_updates_are_not_proof_of_input(self):
        falling=[{'f':f,'pos':[10000,f*1000],'st':19} for f in range(150)]
        self.assertEqual(ml.input_motion_checks(falling),{'movement_responds':False,'jump_responds':False})
        rows=[{'f':0,'pos':[10000,0],'st':0},{'f':55,'pos':[22000,0],'st':1},
              {'f':95,'pos':[10000,0],'st':1},{'f':105,'pos':[10000,5000],'st':15}]
        self.assertTrue(all(ml.input_motion_checks(rows).values()))


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private ROM not present')
class NamespaceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom, glob, manifest = mod.load_clean()
        at,_,_,size=struct.unpack_from('<4I',rom,0x20)
        cls.arm9=rom[at:at+size]
        cls.names=[e['name'] for e in manifest['entries']]
        e=next(e for e in manifest['entries'] if e['name']==training_room.NAME)
        cls.training=glob[e['offset']:e['offset']+e['size']]

    def test_resource_override_uses_distinct_model_list_and_keeps_original_lookup(self):
        names=self.names+['zz_ml_model.nsbmd','zz_ml_tex.nsbtx','zz_ml_collision.bsp','zz_ml_entities.obj']
        count=len(self.names)
        resources={'model':count,'texture':count+1,'bsp':count+2,'objects':count+3}
        patches=r.probe_image(self.arm9,names,resources)
        image=bytes.fromhex(patches[0]['hex'])
        offset=81*4
        self.assertEqual(struct.unpack_from('<3I',image,offset+4),(count+1,count+2,count+3))
        model_pointer=struct.unpack_from('<I',image,offset+32)[0]
        self.assertEqual(model_pointer%4,0)
        self.assertEqual(struct.unpack_from('<I',image,model_pointer-r.BASE)[0],count)
        with self.assertRaises(ValueError): r.probe_image(self.arm9,names,{'model':count})
        with self.assertRaises(ValueError): r.probe_image(self.arm9,names,{**resources,'model':count+1})
        self.assertEqual(len(r.probe_image(self.arm9,names,resources,mode=0)),4)
        patches=r.probe_image(self.arm9,names,resources,mode=1)
        self.assertEqual(patches[-1]['addr'],r.TEST_MODE)
        self.assertEqual(struct.unpack('<I',bytes.fromhex(patches[-1]['hex']))[0],0xE3A02001)
        with self.assertRaises(ValueError): r.probe_image(self.arm9,names,resources,mode=True)
        with self.assertRaises(ValueError): r.probe_image(self.arm9,names,resources,mode=3)
        patches=r.probe_image(self.arm9,names,resources,mode=1,test_context=False)
        self.assertEqual(patches[-1]['addr'],r.TEST_CONTEXT)
        self.assertEqual(bytes.fromhex(patches[-1]['hex']),struct.pack('<I',0xE3A01000))

    def test_empty_training_group_repairs_both_self_references_and_preserves_base(self):
        for raw in (self.training,training_room.with_sparring(self.training)):
            old=room_objects.RoomObjects.parse(raw)
            result=room_objects.RoomObjects.parse(ml.empty_training_group(raw,repair_init=True))
            self.assertEqual(tuple(r.raw for r in result.records[:2]),tuple(r.raw for r in old.records[:2]))
            self.assertEqual(tuple(n.raw for n in result.names[:2]),tuple(n.raw for n in old.names[:2]))
            self.assertEqual(result.between,old.between)
            self.assertEqual(len(room_entities.Entities.parse(result.records[2].sections[0]).records),0)
            self.assertEqual(result.names[2].category_ends,(0,1,2,2,2,2,2))
            self.assertEqual(result.names[2].labels,('<EG_INIT>','<AG_INIT>'))
            events=room_events.Events.parse(result.records[2].sections[1],1)
            self.assertEqual(tuple(c.opcode for c in events.groups[0].commands),(0x15,))
            original=room_events.Events.parse(old.records[2].sections[1],1)
            self.assertEqual(events.groups[0].commands[0],original.groups[0].commands[0])
        with self.assertRaises(ValueError):ml.empty_training_group(result.to_bytes(),repair_init=True)
