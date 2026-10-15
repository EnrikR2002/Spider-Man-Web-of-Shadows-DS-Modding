"""Environmental safety measurements must distinguish recovery from damage."""
import unittest
from tools.crane_boss_lab import HealthWindow


class HealthWindowTests(unittest.TestCase):
    def test_flat_health_is_safe(self):
        window=HealthWindow(100)
        for hp in (100,100,100):window.sample(hp)
        self.assertTrue(window.passed());self.assertEqual(window.minimum,100)

    def test_native_recovery_is_not_damage(self):
        window=HealthWindow(100)
        for hp in (100,105,110):window.sample(hp)
        self.assertTrue(window.passed(regeneration=True));self.assertFalse(window.passed())

    def test_damage_after_recovery_cannot_hide_above_starting_health(self):
        window=HealthWindow(100)
        for hp in (110,105,115):window.sample(hp)
        self.assertFalse(window.passed(regeneration=True));self.assertTrue(window.dropped)
