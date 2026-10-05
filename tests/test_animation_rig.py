import unittest
import mod
from tools.animation_rig import AnimationRig,node_ancestry


class RigTests(unittest.TestCase):
    def test_node_parent_and_stack_lineage_agree(self):
        stream=bytes((0x26,0,0,0,0,0x26,1,0,2,1,0x66,2,0,3,2,0,1))
        parents,records,used=node_ancestry(stream,3)
        self.assertEqual(parents,(None,0,0));self.assertEqual(used,len(stream))

    def test_unknown_commands_bad_stacks_and_disagreeing_parents_are_rejected(self):
        for stream,count in ((b'\xff',1),(bytes((3,8,1)),1),(bytes((0x26,0,1,0,0,1)),2),
                             (bytes((0x26,0,0,0,0)),1),(bytes((0x26,0,0,0,0,1)),2)):
            with self.assertRaises(ValueError):node_ancestry(stream,count)

    @unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original absent')
    def test_clean_player_rig_roundtrip_and_canonical_parent_indices(self):
        _,glob,manifest=mod.load_clean();e=next(e for e in manifest['entries'] if e['name']=='spd.nsbmd')
        raw=glob[e['offset']:e['offset']+e['size']];rig=AnimationRig.parse(raw)
        self.assertEqual(rig.to_bytes(),raw);self.assertEqual(len(rig.names),37)
        for joint,name,parent in ((3,'spd:Chest_M',2),(7,'spd:Shoulder_L',6),(17,'spd:Shoulder_R',16),
                                  (26,'spd:Hip_L',1),(30,'spd:Hip_R',1),(34,'spd:joint3',0),(35,'spd:joint1',34)):
            self.assertEqual((rig.names[joint],rig.parents[joint]),(name,parent))
        self.assertEqual(rig.sbc_start,0x764);self.assertEqual(rig.sbc_end,0x82b)

if __name__=='__main__':unittest.main()
