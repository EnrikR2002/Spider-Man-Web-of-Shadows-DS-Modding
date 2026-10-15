"""Boss observation rejects invalid pointers, unrelated classes and dead cores."""
import struct
import unittest
from tools import midnight_boss as b, midnight_boss_lab as lab


class BossLabTests(unittest.TestCase):
    def test_class_specific_hp_and_harmless_flags_without_mutation(self):
        ram = bytearray(4 * 1024 * 1024)
        at, hazard, data = 0x200000, 0x200200, 0x100000
        struct.pack_into('<I', ram, at, 0x0212F7A0)
        struct.pack_into('<2I', ram, at + 0x10C, b.CORE_KIND, b.CORE_HEALTH)
        struct.pack_into('<2i', ram, at + 0x90, 22 * 4096, 8 * 4096)
        struct.pack_into('<I', ram, hazard, 0x0212F2D4)
        struct.pack_into('<I', ram, hazard + 0x108, lab.p.BASE + data)
        struct.pack_into('<I', ram, hazard + 0x10C, b.WARNING_KIND)
        struct.pack_into('<2i', ram, hazard + 0x90, 46 * 4096, 4096)
        before = bytes(ram)
        cores, hazards = lab.world_objects(ram)
        self.assertEqual(cores, [[lab.p.BASE + at, b.CORE_HEALTH, 22, 8]])
        self.assertEqual(hazards, [[b.WARNING_KIND, 0, 46, 1]])
        self.assertEqual(bytes(ram), before)
        ram[at + 0x131] = 1
        struct.pack_into('<I', ram, hazard + 0x108, 0xFFFFFFFF)
        self.assertEqual(lab.world_objects(ram), ([], []))

    def test_truncated_ram_and_vtable_words_near_its_end_are_safe(self):
        with self.assertRaises(ValueError): lab.world_objects(bytes(128))
        ram = bytearray(4 * 1024 * 1024)
        struct.pack_into('<I', ram, len(ram) - 4, 0x0212F7A0)
        self.assertEqual(lab.world_objects(ram), ([], []))

    def test_health_game_pen_targets_orb_centres_and_ignores_the_top_screen(self):
        raw = bytearray(256 * 384 * 4)
        for cx,cy in ((50,250),(160,50)):
            for y in range(cy-9,cy+10):
                for x in range(cx-9,cx+10):
                    if (x-cx)**2+(y-cy)**2<=81:raw[(y*256+x)*4:(y*256+x)*4+4]=bytes((30,100,255,0))
        self.assertEqual(lab.orb_point((raw,256,384,1024),1),[50,250])
        self.assertIsNone(lab.orb_point((bytes(len(raw)),256,384,1024),1))


if __name__ == '__main__': unittest.main()
