import struct
import unittest
from tools.player_trace import BASE, VTABLES, sample


class PlayerTraceTests(unittest.TestCase):
    def test_bounded_layout_and_read_only_samples(self):
        data = bytearray(4*1024*1024)
        for offset, value in zip((0x300, 0x308, 0x314), VTABLES): struct.pack_into('<I', data, offset, value)
        struct.pack_into('<I', data, 0x330, BASE+0x600)
        struct.pack_into('<I', data, 0x830, 3382)
        struct.pack_into('<I', data, 0x854, 56)
        struct.pack_into('<2i', data, 0x67c, -4096, 8192)
        struct.pack_into('<2i', data, 0x760, 1000, -2000)
        struct.pack_into('<3i', data, 0x688, 4000, 5000, 6000)
        struct.pack_into('<I', data, 0x780, 1)
        struct.pack_into('<I', data, 0x7f8, BASE+0x1000)
        struct.pack_into('<I', data, 0x1000, 0x021352a4)
        struct.pack_into('<I', data, 0x1014, 42)
        struct.pack_into('<I', data, 0x1044, BASE+0x300)
        before = bytes(data); result = sample(data)
        self.assertEqual(result['actor_address'], BASE+0x300)
        self.assertEqual(result['motion_address'], BASE+0x600)
        self.assertEqual(result['gmb_id'], 3382)
        self.assertEqual(result['action_id_candidate'], 56)
        self.assertEqual(result['position_q12_candidate'], [-3096, 6192])
        self.assertEqual(result['facing_candidate'], 1)
        self.assertEqual(result['controller']['state_id_candidate'], 42)
        self.assertEqual(bytes(data), before)
        struct.pack_into('<I', data, 0x1044, BASE+0x400)
        with self.assertRaisesRegex(ValueError, 'controller vtable/owner'): sample(data)
        struct.pack_into('<I', data, 0x7f8, BASE+len(data))
        with self.assertRaisesRegex(ValueError, 'controller pointer'): sample(data)
        struct.pack_into('<I', data, 0x7f8, 0)
        self.assertIsNone(sample(data)['controller'])
        struct.pack_into('<I', data, 0x330, BASE+len(data))
        with self.assertRaisesRegex(ValueError, 'outside'): sample(data)
        with self.assertRaises(ValueError): sample(bytes(40))
        with self.assertRaisesRegex(ValueError, 'found 0'): sample(bytes(len(data)))

    def test_stale_actor_copy_is_ignored_when_the_live_motion_points_back(self):
        data = bytearray(4*1024*1024)
        for actor, motion in ((0x300, 0x600), (0x2000, 0x2400)):   # live, then a freed copy
            for offset, value in zip((0, 8, 20), VTABLES): struct.pack_into('<I', data, actor + offset, value)
            struct.pack_into('<I', data, actor + 0x30, BASE + motion)
        struct.pack_into('<I', data, 0x600, BASE + 0x300)          # live motion owner
        self.assertEqual(sample(bytes(data))['actor_address'], BASE + 0x300)
        struct.pack_into('<I', data, 0x2400, BASE + 0x2000)        # both owned: still ambiguous
        with self.assertRaisesRegex(ValueError, 'found 2'): sample(bytes(data))
        struct.pack_into('<I', data, 0x7F8, BASE + 0x1000)
        struct.pack_into('<I', data, 0x1000, 0x021352a4)
        struct.pack_into('<I', data, 0x1044, BASE + 0x300)
        for stale in (4, 0x34C, BASE + len(data), BASE + 0x3000):
            struct.pack_into('<I', data, 0x25F8, stale)
            before=bytes(data)
            self.assertEqual(sample(before)['actor_address'], BASE + 0x300)
            self.assertEqual(bytes(data),before)
        # Two valid controller owners remain ambiguous; never choose by order.
        struct.pack_into('<I', data, 0x3000, 0x021352a4)
        struct.pack_into('<I', data, 0x3044, BASE + 0x2000)
        with self.assertRaisesRegex(ValueError, 'found 2'): sample(bytes(data))
