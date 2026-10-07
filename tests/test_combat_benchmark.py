import unittest
from tools import combat_benchmark as b


class CombatBenchmarkTests(unittest.TestCase):
    def test_native_half_rate_and_wrap(self):
        result = b.cadence([0xFFFFFFFF, 0xFFFFFFFF, 0, 0, 1])
        self.assertEqual(result['updates_per_60_frames'], 30)
        self.assertEqual(result['longest_no_update_frames'], 1)

    def test_stall_and_short_or_reset_samples(self):
        self.assertEqual(b.cadence([5] * 61)['longest_no_update_frames'], 60)
        for samples in ([0], [100, 0]):
            with self.subTest(samples=samples), self.assertRaises(ValueError):
                b.cadence(samples)


if __name__ == '__main__':
    unittest.main()
