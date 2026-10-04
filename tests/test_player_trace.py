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
        before = bytes(data); result = sample(data)
        self.assertEqual(result['actor_address'], BASE+0x300)
        self.assertEqual(result['motion_address'], BASE+0x600)
        self.assertEqual(result['gmb_id'], 3382)
        self.assertEqual(result['action_id_candidate'], 56)
        self.assertEqual(bytes(data), before)
        struct.pack_into('<I', data, 0x330, BASE+len(data))
        with self.assertRaisesRegex(ValueError, 'outside'): sample(data)
        with self.assertRaises(ValueError): sample(bytes(40))
        with self.assertRaisesRegex(ValueError, 'found 0'): sample(bytes(len(data)))
