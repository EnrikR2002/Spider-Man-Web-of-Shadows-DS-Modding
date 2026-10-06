"""Crash hunt: deterministic fight scripts and melonDS ARM9/DTCM state decoding."""
import struct
import unittest
from tools import crash_hunt, emulator_smoke


def fake_state(halted, regs, cpsr, abt=(0, 0, 0), dtcm=b''):
    arm9 = struct.pack('<4I', 0xBC, 0, 0, 3) + struct.pack('<I', halted) + struct.pack('<16I', *regs)
    arm9 += struct.pack('<I', cpsr) + bytes(8 * 4) + bytes(3 * 4) + struct.pack('<3I', *abt) + bytes(3 * 4)
    body = bytes(16) + bytes(0x8000) + dtcm.ljust(0x4000, b'\0')
    cp15 = b'CP15' + struct.pack('<I', len(body) + 8) + body
    return b'MELN' + bytes(12) + b'ARM9' + arm9 + bytes(32) + cp15


class CrashHuntTests(unittest.TestCase):
    def test_fight_script_is_deterministic_and_valid(self):
        rows = crash_hunt.fight_script(7, 4000)
        self.assertEqual(rows, crash_hunt.fight_script(7, 4000))
        self.assertNotEqual(rows, crash_hunt.fight_script(8, 4000))
        emulator_smoke.input_schedule(rows)
        pressed = {b for r in rows for b in r['buttons']}
        self.assertTrue({'Y', 'R'} <= pressed)
        self.assertTrue(any('R' in r['buttons'] and r['end'] - r['start'] >= 20 for r in rows))   # held R chains

    def test_registers_and_banked_abort_frame_decode(self):
        regs = list(range(16)); regs[13], regs[14], regs[15] = 0, 0x0201DC14, 0xFFFF0108
        stack = bytes(0x31BC) + struct.pack('<4I', 0, 0x0201D87C, 0x12345678, 0x02153E5C)
        state = fake_state(0, regs, 0x20000097, abt=(0x027E31BC, 0x0201DC08, 0x2000001F), dtcm=stack)
        r = crash_hunt.arm9_registers(state)
        self.assertEqual((r['halted'], r['r'][15], r['cpsr'] & 0x1F), (0, 0xFFFF0108, 0x17))
        self.assertEqual(r['abt'][:2], [0x027E31BC, 0x0201DC08])
        text = '\n'.join(crash_hunt.describe(state))
        self.assertIn('DATA ABORT at 0x0201dc0c', text)
        self.assertIn('0x0201d87c', text)
        self.assertIn('0x02153e5c', text)
        self.assertNotIn('0x12345678', text)

    def test_halted_idle_wait_is_not_reported_as_abort(self):
        regs = [0] * 16; regs[15] = 0x020FFA30
        text = '\n'.join(crash_hunt.describe(fake_state(1, regs, 0x1F)))
        self.assertIn('halted 1', text)
        self.assertNotIn('ABORT', text)


if __name__ == '__main__':
    unittest.main()
