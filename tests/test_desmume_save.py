import struct
import unittest
from tools.desmume_save import Dsv, COOKIE
from tools.emulator_smoke import input_schedule


def dsv(payload=bytes(512), middle=b'unknown wrapper text'):
    return payload + middle + struct.pack('<6I', 1, len(payload), 1, 1, len(payload), 0) + COOKIE


class DsvTests(unittest.TestCase):
    def test_lossless_opaque_payload_and_middle(self):
        raw = dsv(bytes(range(256)) * 2, b'opaque\0\xff')
        parsed = Dsv.parse(raw)
        self.assertEqual(parsed.to_bytes(), raw)
        self.assertEqual(parsed.payload, bytes(range(256)) * 2)
        self.assertEqual(parsed.middle, b'opaque\0\xff')
        self.assertEqual(parsed.footer_words, (1, 512, 1, 1, 512, 0))

    def test_reject_invalid_footer(self):
        raw = dsv()
        variants = [raw[:-1], raw[:-16] + bytes(16), bytes(40)]
        for field, value in ((0, 513), (1, 0), (1, 100000), (3, 4), (5, 1)):
            changed = bytearray(raw)
            struct.pack_into('<I', changed, len(raw) - 40 + field * 4, value)
            variants.append(bytes(changed))
        for changed in variants:
            with self.subTest(data=changed[-40:]), self.assertRaises(ValueError): Dsv.parse(changed)

    def test_explicit_input_ranges(self):
        self.assertEqual(input_schedule([{'start': 7, 'end': 9, 'buttons': ['Y', 'Right']}]),
                         [(7, 9, frozenset((1, 7)))])
        for rows in ({}, [{'start': -1, 'end': 9, 'buttons': ['Y']}],
                     [{'start': 7, 'end': 7, 'buttons': ['Y']}],
                     [{'start': 7, 'end': 9, 'buttons': ['unknown']}]):
            with self.assertRaises(ValueError): input_schedule(rows)
