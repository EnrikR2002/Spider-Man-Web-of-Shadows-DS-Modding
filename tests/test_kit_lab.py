"""Kit research lab: tracked input scripts stay valid; parity comparison tolerates only a phase."""
import unittest
import tempfile
import struct
from pathlib import Path
from unittest import mock
from tools import emulator_smoke, kit_lab


class KitLabTests(unittest.TestCase):
    def test_enemy_scan_rejects_reused_motion_but_keeps_owned_death_actors(self):
        base, actor, motion, controller = 0x02000000, 0x1000, 0x2000, 0x3000
        for hp in (0, 4096):
            for owner in (0, base+actor, base+actor+0x100):
                with self.subTest(hp=hp, owner=owner):
                    ram = bytearray(4*1024*1024)
                    for at, value in ((actor, kit_lab.ENEMY_VTABLE), (actor+0x30, base+motion),
                                      (actor+0x44, hp), (actor+0x48, 4096), (motion, owner),
                                      (motion+0x1f8, base+controller), (controller+0x14, 6 if not hp else 0)):
                        struct.pack_into('<I', ram, at, value)
                    enemies = kit_lab.enemies(ram)
                    self.assertEqual([e['actor'] for e in enemies], [base+actor] if owner == base+actor else [])
                    if enemies: self.assertEqual(enemies[0]['hp'], hp)

    def test_runtime_patch_cannot_replace_published_qualification_evidence(self):
        published = kit_lab.ROOT / 'work/kit/evidence.json'
        for options in ({}, {'out': published, 'label_prefix': 'candidate-'},
                        {'out': published.with_name('candidate.json')}):
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, 'separate output'):
                kit_lab.qualify('unused.nds', patch='unused.json', **options)

    def test_jit_rejected_before_applying_runtime_code_patches(self):
        with tempfile.TemporaryDirectory() as directory:
            save = Path(directory) / 'copy.dsv'
            save.write_bytes(b'fixture')
            patches = Path(directory) / 'patches.json'
            patches.write_text('[{"addr": 33554432, "hex": "00000000"}]')
            with mock.patch.object(emulator_smoke, 'run', side_effect=AssertionError('must not run')):
                with self.assertRaisesRegex(ValueError, 'JIT disabled'):
                    kit_lab._run('unused.nds', 'test', [], save=save, patch=patches,
                                 core_options={b'melonds_jit_enable': b'enabled'})

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

    def test_added_purchase_fixture_clears_only_requested_ram_word_bits(self):
        import ctypes, struct
        buf = ctypes.create_string_buffer(4*1024*1024)
        stats = 0x200000
        struct.pack_into('<I', buf, kit_lab.STATS_POINTER-kit_lab.p.BASE, kit_lab.p.BASE+stats)
        struct.pack_into('<3I', buf, stats+0xC, 0x12345678, 0xabcdef01, 0xa507fddf)
        with mock.patch.object(kit_lab, 'ram_of', return_value=(ctypes.addressof(buf), buf.raw)):
            kit_lab.clear_word2(None, kit_lab.ADDED_WORD2_MASK)
        self.assertEqual(struct.unpack_from('<3I', buf, stats+0xC),
                         (0x12345678, 0xabcdef01, 0xa507fddf & ~kit_lab.ADDED_WORD2_MASK))

    def test_teleport_moves_base_and_probes_keeping_probe_offsets(self):
        import ctypes, struct
        buf = ctypes.create_string_buffer(0x300)
        struct.pack_into('<2i', buf, 0x7C, 100, 200)       # base
        struct.pack_into('<2i', buf, 0x160, 10, 20)        # local: absolute (110, 220)
        for off, dy in zip(kit_lab.PROBES, (-5, 7, -5)):
            struct.pack_into('<2i', buf, off, 110, 220 + dy)
        kit_lab.teleport(ctypes.addressof(buf), buf.raw, 0, 1000, 2000)
        self.assertEqual(struct.unpack_from('<2i', buf, 0x7C), (990, 1980))
        for off, dy in zip(kit_lab.PROBES, (-5, 7, -5)):
            self.assertEqual(struct.unpack_from('<2i', buf, off), (1000, 2000 + dy))
        # Never the old false "actor copies" (past the 0xF4-byte actor: heap corruption).
        self.assertTrue(set(kit_lab.PROBES).isdisjoint({0x148, 0x180, 0x210, 0x2CC}))


if __name__ == '__main__':
    unittest.main()
