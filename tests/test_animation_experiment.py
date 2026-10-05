import unittest
import mod
from tools import wos_tool as w
from tools.sca import Sca
from tools.sca_author import sample
from tools import animation_experiment as e


@unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original absent')
class AnimationExperimentTests(unittest.TestCase):
    def source(self):
        # Historical proof template is reproducible even after a new animation
        # replaces this resource in the published overlay.
        from tools.tasm_oscorp_rush import recovery_pose
        _,glob,manifest=mod.load_clean();entry=next(row for row in manifest['entries'] if row['name']==e.ASSET)
        raw=recovery_pose(glob[entry['offset']:entry['offset']+entry['size']])
        self.assertEqual(w.sha256(raw),e.BASE_SHA256);return raw

    def test_rebake_preserves_every_sample_and_authored_recovery_is_bounded(self):
        raw=self.source();a=Sca.parse(raw)
        for variant in ('rebake','guard-recovery'):
            changed=e.author(raw,variant);b=Sca.parse(changed)
            self.assertEqual((b.frame_count,b.joint_count),(20,37))
            self.assertEqual(b.static_pool,a.static_pool)
            for j in range(37):
                self.assertEqual(b.track(j)['joints'],(j,))
                for f in range(20):
                    for channel in ('translation','rotation','scale'):
                        if variant=='guard-recovery' and channel=='rotation' and j in e.DELTAS and 11<=f<=17:continue
                        self.assertEqual(sample(b,j,f,channel),sample(a,j,f,channel))
            self.assertEqual(b.to_bytes(),changed)

    def test_experiment_refuses_unrecognized_templates_or_variants(self):
        raw=self.source()
        with self.assertRaises(ValueError):e.author(raw,'new-move')
        changed=bytearray(raw);changed[26]=1
        with self.assertRaises(ValueError):e.author(bytes(changed),'rebake')

if __name__=='__main__':unittest.main()
