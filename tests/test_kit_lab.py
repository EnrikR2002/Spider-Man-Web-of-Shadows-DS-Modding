"""Kit research lab: tracked input scripts stay valid; parity comparison tolerates only a phase."""
import unittest
from tools import emulator_smoke, kit_lab


class KitLabTests(unittest.TestCase):
    def test_every_tracked_input_script_is_a_valid_schedule(self):
        files = sorted(kit_lab.INPUTS.glob('*.json'))
        self.assertGreater(len(files), 10)
        for path in files:
            with self.subTest(path=path.name):
                emulator_smoke.input_schedule(kit_lab.rows_from(path))

    def test_parity_allows_one_constant_phase_only(self):
        base = [(-20, 0, 99, 1, 10), (21, 46, 56, 1, 10), (41, 53, 139, 1, 10)]
        shifted = [(-20, 0, 99, 1, 10), (20, 46, 56, 1, 10), (40, 53, 139, 1, 10)]
        self.assertTrue(kit_lab.same_behavior(shifted, base))
        uneven = [(-20, 0, 99, 1, 10), (20, 46, 56, 1, 10), (41, 53, 139, 1, 10)]
        self.assertFalse(kit_lab.same_behavior(uneven, base))
        moved = [(-20, 0, 99, 1, 10), (21, 46, 56, 1, 10), (41, 53, 139, 0, 10)]
        self.assertFalse(kit_lab.same_behavior(moved, base))


if __name__ == '__main__':
    unittest.main()
