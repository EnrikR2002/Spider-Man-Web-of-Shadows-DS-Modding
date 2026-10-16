import unittest
from tools.crane_reward_lab import reward_summary,XP

class RewardTelemetryTests(unittest.TestCase):
    def test_actual_currency_field_and_native_health_gains(self):
        self.assertEqual(XP,0x44)
        rows=[dict(frame=150,xp=1850,hp=12288,dead=False),dict(frame=220,xp=1850,hp=12288,dead=True),
              dict(frame=270,xp=1862,hp=14336,dead=True),dict(frame=300,xp=1862,hp=15360,dead=False)]
        got=reward_summary(rows)
        self.assertTrue(got['passed']);self.assertEqual(got['xp_awarded'],12);self.assertEqual(got['health_recovered_q12'],3072)
        self.assertFalse(reward_summary([{**r,'xp':1850} for r in rows])['passed'])
        self.assertFalse(reward_summary([{**r,'dead':False} for r in rows])['passed'])

if __name__=='__main__':unittest.main()
