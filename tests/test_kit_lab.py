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

    def test_spin_hits_counts_hp_drops_of_the_first_enemy(self):
        rows = [{'en': [(hp, [0, 0], 0, 99)]} for hp in (100, 100, 90, 90, 80, 85, 70)]
        self.assertEqual(kit_lab.spin_hits(rows), 3)
        self.assertEqual(kit_lab.spin_hits(rows[:1]), 0)


if __name__ == '__main__':
    unittest.main()
