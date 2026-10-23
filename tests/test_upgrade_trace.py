import struct
import unittest

from tools import player_trace, upgrade_trace


def ram_with_skills(bits=(), currency=39):
    ram = bytearray(4 * 1024 * 1024)
    actor, motion, stats = 0x200000, 0x201000, 0x202000
    for offset, pointer in zip((0, 8, 20), player_trace.VTABLES):
        struct.pack_into('<I', ram, actor + offset, pointer)
    struct.pack_into('<I', ram, actor + 0x30, player_trace.BASE + motion)
    struct.pack_into('<I', ram, motion, player_trace.BASE + actor)
    struct.pack_into('<I', ram, upgrade_trace.STATS_POINTER_ADDRESS - player_trace.BASE,
                     player_trace.BASE + stats)
    struct.pack_into('<I', ram, actor + 0xE8, player_trace.BASE + stats + 12)
    words = [0, 0, 0]
    for bit in bits: words[bit // 32] |= 1 << (bit % 32)
    struct.pack_into('<3I', ram, stats + 12, *words)
    struct.pack_into('<I', ram, stats + 0x44, currency)
    return ram


class UpgradeTraceTests(unittest.TestCase):
    def test_distinguishes_paid_red_slots_and_other_ownership(self):
        ram = ram_with_skills((13, 16, 18, 20, 72), 1000)
        before = bytes(ram)
        result = upgrade_trace.snapshot(ram, arm9_sha256=upgrade_trace.ARM9_SHA256)
        self.assertTrue(result['red_skills']['Web Kick']['owned'])
        self.assertFalse(result['red_skills']['Web Launch']['owned'])
        self.assertTrue(result['red_skills']['Spider Dance']['owned'])
        self.assertEqual(result['red_skills']['Web Kick']['event_id'], 322)
        self.assertEqual(result['currency'], 1000)
        self.assertTrue(result['black_ability_bits']['20'])
        self.assertEqual(result['ability_words'][2], 1 << 8)
        self.assertEqual(bytes(ram), before)

    def test_locked_red_skills_remain_locked(self):
        result = upgrade_trace.snapshot(ram_with_skills((27, 55)),
                                        arm9_sha256=upgrade_trace.ARM9_SHA256)
        self.assertFalse(any(entry['owned'] for entry in result['red_skills'].values()))

    def test_mismatched_engine_or_owner_pointer_is_rejected(self):
        ram = ram_with_skills()
        with self.assertRaisesRegex(ValueError, 'known'):
            upgrade_trace.snapshot(ram, arm9_sha256='0' * 64)
        struct.pack_into('<I', ram, 0x200000 + 0xE8, player_trace.BASE + 0x203000)
        with self.assertRaisesRegex(ValueError, 'disagree'):
            upgrade_trace.snapshot(ram, arm9_sha256=upgrade_trace.ARM9_SHA256)

    def test_invalid_stats_and_player_bounds_are_rejected(self):
        for pointer in (player_trace.BASE - 4, player_trace.BASE + len(ram_with_skills()),
                        player_trace.BASE + 0x202001):
            ram = ram_with_skills()
            struct.pack_into('<I', ram, upgrade_trace.STATS_POINTER_ADDRESS - player_trace.BASE, pointer)
            with self.assertRaisesRegex(ValueError, 'Stats pointer'):
                upgrade_trace.snapshot(ram, arm9_sha256=upgrade_trace.ARM9_SHA256)
        with self.assertRaisesRegex(ValueError, '4 MiB'):
            upgrade_trace.snapshot(b'', arm9_sha256=upgrade_trace.ARM9_SHA256)

    def test_rom_layout_and_hash_guard(self):
        rom = bytearray(0x80)
        with self.assertRaisesRegex(ValueError, 'CS5E'):
            upgrade_trace.verify_rom(rom)
        rom[12:16] = b'CS5E'
        struct.pack_into('<4I', rom, 0x20, 0x100, 0, player_trace.BASE, 8)
        with self.assertRaisesRegex(ValueError, 'location'):
            upgrade_trace.verify_rom(rom)
        struct.pack_into('<4I', rom, 0x20, 0x40, 0, player_trace.BASE, 8)
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            upgrade_trace.verify_rom(rom)


if __name__ == '__main__': unittest.main()
