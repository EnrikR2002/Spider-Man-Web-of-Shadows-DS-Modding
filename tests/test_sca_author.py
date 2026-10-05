import copy
from dataclasses import replace
from pathlib import Path
import struct
import unittest
import mod
from tools import wos_tool as w
from tools.sca import Sca,Pool,rotation_q12
from tools.sca_author import export_samples,import_samples,repack_samples,sample
from tests.test_sca import synthetic,IDENTITY


class ScaAuthorTests(unittest.TestCase):
    def test_sample_export_import_is_exact_and_scale_edit_is_rejected(self):
        raw=synthetic(True);data=export_samples(raw)
        self.assertEqual(import_samples(raw,data),raw)
        data['tracks'][1]['scale_q12'][0][0]+=1
        with self.assertRaises(ValueError):import_samples(raw,data)

    def test_shared_track_becomes_independent_without_changing_other_joint(self):
        raw=bytearray(synthetic(True));parsed=Sca.parse(raw)
        # Native zero alignment may be shortened when adding one18-byte track.
        # Keep the nonzero header/descriptor/static padding preservation checks.
        for f in range(parsed.frame_count):
            raw[parsed.frames_start+(f+1)*parsed.frame_stride-2:parsed.frames_start+(f+1)*parsed.frame_stride]=bytes(2)
        raw=bytes(raw);a=Sca.parse(raw)
        changed=repack_samples(raw,rotations={1:[IDENTITY,rotation_q12('z',30)]})
        b=Sca.parse(changed)
        self.assertEqual(b.rotation(1,1),rotation_q12('z',30))
        self.assertEqual(b.rotation(2,1),a.rotation(2,1))
        self.assertEqual(b.track(1)['joints'],(1,))
        self.assertEqual(b.static_pool,a.static_pool)
        self.assertEqual(b.header[26:28],a.header[26:28])
        self.assertEqual(b.descriptor_padding,a.descriptor_padding)
        self.assertEqual(b.frames[0].padding,b'')
        self.assertEqual(b.frames[0].rotations[:-1],a.frames[0].rotations)
        self.assertEqual(b.to_bytes(),changed)

    def test_static_and_aliased_translations_can_be_authored_independently(self):
        raw=synthetic(True);a=Sca.parse(raw)
        changed=repack_samples(raw,translations={0:[(0,0,0),(100,200,300)]})
        b=Sca.parse(changed)
        self.assertFalse(b.track(0,'translation')['static'])
        self.assertEqual(sample(b,0,1,'translation'),(100,200,300))
        self.assertEqual(sample(b,1,1,'translation'),sample(a,1,1,'translation'))
        self.assertEqual(b.static_pool,a.static_pool)
        self.assertEqual(b.frame_stride,a.frame_stride+12)

    def test_padding_is_preserved_or_nonzero_loss_is_rejected(self):
        raw=synthetic()
        with self.assertRaises(ValueError):
            repack_samples(raw,rotations={0:[IDENTITY,rotation_q12('x',15)]})
        # Appending two 18-byte entries leaves original alignment intact.
        changed=repack_samples(raw,rotations={0:[IDENTITY,rotation_q12('x',15)],1:[IDENTITY,rotation_q12('z',20)]})
        self.assertEqual(Sca.parse(changed).frames[0].padding,b'\x93\x94')

    def test_document_identity_duplicate_counts_and_ranges_are_checked(self):
        raw=synthetic(True);original=export_samples(raw)
        for field,value in (('base_sha256','bad'),('frame_count',3),('joint_count',4)):
            data=copy.deepcopy(original);data[field]=value
            with self.assertRaises(ValueError):import_samples(raw,data)
        data=copy.deepcopy(original);data['tracks'][2]['joint']=1
        with self.assertRaises(ValueError):import_samples(raw,data)
        for values in ([IDENTITY],[(32768,)*9]*2,[(True,)*9]*2):
            with self.assertRaises(ValueError):repack_samples(raw,rotations={1:values})

    def test_descriptor_index_limit_prevents_wrapping_into_other_tracks(self):
        a=Sca.parse(synthetic());header=bytearray(a.header)
        header[25]=128;struct.pack_into('<I',header,16,2316)
        frames=tuple(Pool(p.translations,p.scales,(IDENTITY,)*128,b'') for p in a.frames)
        raw=replace(a,header=bytes(header),frames=frames).to_bytes()
        self.assertEqual(Sca.parse(raw).counts[5],128)
        with self.assertRaises(ValueError):repack_samples(raw,rotations={1:[IDENTITY,rotation_q12('x',20)]})

    @unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original absent')
    def test_all_869_original_sample_documents_roundtrip_exactly(self):
        _,glob,manifest=mod.load_clean();count=0
        for e in manifest['entries']:
            if not e['name'].endswith('.sca'):continue
            raw=glob[e['offset']:e['offset']+e['size']]
            self.assertEqual(import_samples(raw,export_samples(raw)),raw,e['name']);count+=1
        self.assertEqual(count,869)

    @unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original absent')
    def test_all_126_player_clips_can_bake_independent_rotation_tracks(self):
        _,glob,manifest=mod.load_clean();count=0
        for e in manifest['entries']:
            if not(e['name'].startswith('spd_') and e['name'].endswith('.sca')):continue
            raw=glob[e['offset']:e['offset']+e['size']];a=Sca.parse(raw)
            changed=repack_samples(raw,independent_rotations=True);b=Sca.parse(changed)
            self.assertEqual((b.frame_count,b.joint_count),(a.frame_count,37))
            self.assertEqual(b.static_pool,a.static_pool)
            for j in range(37):
                self.assertFalse(b.track(j)['static']);self.assertEqual(b.track(j)['joints'],(j,))
                for f in range(a.frame_count):self.assertEqual(b.rotation(j,f),a.rotation(j,f))
            count+=1
        self.assertEqual(count,126)

if __name__=='__main__':unittest.main()
