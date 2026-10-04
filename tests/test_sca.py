import math
from pathlib import Path
import struct
import unittest

from tools.sca import Q12, Sca, multiply_q12, rotation_q12

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = (Q12, 0, 0, 0, Q12, 0, 0, 0, Q12)


def synthetic(shared=False):
    descriptors = bytes((1, 1, 1, 0, 0, 1)) + (bytes((0, 0, 1)) if shared else b'')
    joints = 3 if shared else 2
    header = b'4ACS' + struct.pack('<4I', 2, joints, 54, 32) + bytes((1, 1, 1, 1, 0, 1, 0x5a, 0xa5))
    static = struct.pack('<3i6i9h', 0, 0, 0, *(Q12,) * 6, *IDENTITY) + b'\x91\x92'
    frame = struct.pack('<3i9h', 100, -200, 300, *IDENTITY) + b'\x93\x94'
    return header + descriptors + b'\x95' * ((-len(descriptors)) % 4) + static + frame * 2


class ScaTests(unittest.TestCase):
    def test_structured_roundtrip_preserves_unknowns_and_padding(self):
        raw = synthetic()
        animation = Sca.parse(raw)
        self.assertEqual(animation.to_bytes(), raw)
        self.assertEqual(animation.header[26:28], b'\x5a\xa5')
        self.assertEqual(animation.descriptor_padding, b'\x95\x95')
        self.assertEqual(animation.static_pool.padding, b'\x91\x92')
        self.assertEqual(animation.frames[0].padding, b'\x93\x94')
        self.assertEqual(animation.frames[0].translations, ((100, -200, 300),))

    def test_rotation_edit_is_confined_to_one_dynamic_matrix(self):
        raw = synthetic()
        animation = Sca.parse(raw)
        matrix = rotation_q12('z', 15)
        output = animation.replace_rotation(1, 1, matrix)
        offset = animation.rotation_offset(1, 1)
        self.assertEqual(output[:offset], raw[:offset])
        self.assertEqual(output[offset + 18:], raw[offset + 18:])
        changed = Sca.parse(output)
        self.assertEqual(changed.rotation(1, 1), matrix)
        self.assertEqual(changed.rotation(1, 0), IDENTITY)
        self.assertEqual(changed.to_bytes(), output)

    def test_constant_and_shared_tracks_are_protected(self):
        for raw, joint in ((synthetic(), 0), (synthetic(True), 1)):
            with self.assertRaises(ValueError):
                Sca.parse(raw).replace_rotation(joint, 0, IDENTITY)
        self.assertEqual(Sca.parse(synthetic(True)).track(1)['joints'], (1, 2))

    def test_malformed_counts_bounds_and_descriptors_rejected(self):
        raw = synthetic()
        changes = ((0, b'XXXX'), (4, struct.pack('<I', 0)),
                   (12, struct.pack('<I', 55)), (16, struct.pack('<I', 31)),
                   (28, b'\xff'))
        for offset, data in changes:
            mutated = bytearray(raw)
            mutated[offset:offset + len(data)] = data
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                Sca.parse(bytes(mutated))
        for short in (raw[:-1], raw[:-4], raw + b'\0' * 4):
            with self.assertRaises(ValueError):
                Sca.parse(short)
        animation = Sca.parse(raw)
        for joint, frame in ((-1, 0), (2, 0), (1, -1), (1, 2)):
            with self.assertRaises(ValueError):
                animation.rotation(joint, frame)
        with self.assertRaises(ValueError):
            animation.replace_rotation(1, 0, [32768] * 9)

    def test_q12_rotations_and_zero_edit(self):
        animation = Sca.parse(synthetic())
        self.assertEqual(animation.rotate_joint(1, 0, 'x', 0), synthetic())
        for axis in ('x', 'y', 'z'):
            matrix = rotation_q12(axis, 20)
            inverse = rotation_q12(axis, -20)
            result = multiply_q12(matrix, inverse)
            self.assertTrue(all(abs(a - b) <= 1 for a, b in zip(result, IDENTITY)))
        for axis, angle in (('w', 1), ('x', math.inf), ('x', math.nan)):
            with self.assertRaises(ValueError):
                rotation_q12(axis, angle)

    def test_all_original_assets_structured_roundtrip(self):
        paths = sorted((ROOT / 'work/glob').glob('*.sca'))
        if not paths:
            self.skipTest('Private original resources not extracted')
        self.assertEqual(len(paths), 869)
        player = 0
        for path in paths:
            with self.subTest(name=path.name):
                raw = path.read_bytes()
                animation = Sca.parse(raw)
                self.assertEqual(animation.to_bytes(), raw)
                if path.name.startswith('spd_'):
                    player += 1
                    self.assertEqual(animation.joint_count, 37)
        self.assertEqual(player, 126)


if __name__ == '__main__':
    unittest.main()
