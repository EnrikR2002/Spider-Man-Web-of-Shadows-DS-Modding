"""Exercise Freefall's native hook ABI and exact-ROM resource scope."""
import unittest

import mod
from tests.arm_runtime import ArmProbe
from tools import freefall as f, hunter_kit, spider2099, tasm_kit as kit, wos_tool as w
from tools.qol_suits_menu import decode_grown
from tools.sca import Sca


class Runtime(unittest.TestCase):
    code, state = 0x021a1000, 0x021a0000
    hero, motion, ctl, bits = 0x02200000, 0x02201000, 0x02202000, 0x02203000
    stack, end = 0x023f0000, 0x03000000
    values = dict(STATE=state, BOSS_CONFIG=0x0215a52c, NATIVE_DIVE=3407, NATIVE_LAND=3410,
                  DIVE_SCA=6006, LAND_SCA=6007, OLD_ANIMATION=0x021b0000, OLD_CONTACT=0x021b0100,
                  OLD_THINK=0x021b0200)

    @classmethod
    def setUpClass(cls):
        cls.assembled = f.runtime(cls.code, cls.values)

    def fixture(self, *, form=1, owned=True):
        p = ArmProbe()
        p.code(self.code, self.assembled)
        p.code(self.state, bytes(16))
        for address, value in ((self.hero, 0x0212e3f0), (self.hero+0x30, self.motion), (self.hero+0x34, form),
                               (self.hero+0xe8, self.bits), (self.bits, (1 << 22) if owned else 0),
                               (self.motion, self.hero), (self.motion+0x1f8, self.ctl),
                               (self.motion+0x254, 111), (self.motion+0x258, 73),
                               (self.motion+0x80, 120*4096), (self.motion+0x164, 4096),
                               (self.ctl, 0x021352a4), (self.ctl+0x44, self.hero), (self.ctl+0x14, 35)):
            p.put(address, value)
        p.put(self.stack+0x2c, self.values['NATIVE_DIVE'])
        return p

    def run_hook(self, p, slot, stop):
        regs = list(range(100, 116))
        regs[0] = self.ctl if slot == 4 else 1
        regs[2] = 0xc00
        regs[4] = self.ctl if slot == 1 else self.motion
        if slot == 2:
            regs[5] = regs[12] = 0x47c3
        regs[13:] = [self.stack, self.end, self.code + 4*slot]
        out, cpsr, _ = p.run(regs, 0xa000001f, {stop})
        if slot != 2:
            self.assertEqual(out[4:12], regs[4:12])
        self.assertEqual(out[13], self.stack)
        return out, cpsr

    def test_only_owned_black_dive_changes_the_action_record_and_keeps_flags(self):
        for form, owned in ((0, True), (1, False), (1, True)):
            p = self.fixture(form=form, owned=owned)
            _, flags = self.run_hook(p, 0, self.values['OLD_ANIMATION'])
            self.assertEqual(flags, 0xa000001f)
            self.assertEqual(p.get(self.stack+0x2c), self.values['DIVE_SCA' if form and owned else 'NATIVE_DIVE'])
            self.assertEqual(p.get(self.state), self.motion if form and owned else 0)

    def test_actual_drop_drives_the_two_horizontal_extents_and_caps_the_shake(self):
        for drop, power in ((27, 0), (54, 2052), (81, 4096), (190, 4096)):
            p = self.fixture()
            self.run_hook(p, 0, self.values['OLD_ANIMATION'])
            p.put(self.motion+0x80, (120-drop)*4096)
            p.put(self.motion+0x2ac, 4096)
            p.put(self.ctl+0x18, 35)
            p.put(self.ctl+0x14, 36)
            p.put(self.motion+0x254, 74)
            out, _ = self.run_hook(p, 1, 0x0207e5cc)
            self.assertEqual(p.get(self.state+8), power)
            self.assertEqual(out[2], 0xc00 + power//2)
            out, _ = self.run_hook(p, 2, 0x02071130)
            expected = 0x47c3 + (0x47c3 * power >> 11)
            self.assertEqual(p.get(self.stack+0xa8), expected)
            self.assertEqual(out[5], expected)
            self.assertEqual(out[3], 103)

    def test_receiver_gets_scaled_strength_and_native_hp_with_boss_stagger(self):
        for vtable, config, kind in ((0x021301d0, 0, 0x12), (0x021301d0, self.values['BOSS_CONFIG'], 4),
                                     (0x0212ce38, 0, 4), (0x02130100, 0, 0x12)):
            p = self.fixture()
            p.put(self.state, self.motion)
            p.put(self.state+8, 4096)
            p.put(self.ctl+0x14, 36)
            p.put(self.motion+0x254, 74)
            victim, interface, receive = 0x02210000, 0x021ff000, 0x021ff100
            result, attacker, info = self.stack+0x20, self.stack+0x24, self.stack+0x40
            p.code(info, bytes(0x40))
            for addr, value in ((victim, vtable), (victim+8, interface), (victim+0x40, config),
                                (interface+0x40, receive), (attacker, self.hero), (info, 0x12),
                                (info+4, 0x1800), (self.stack, 0x2400)):
                p.put(addr, value)
            regs = [result, victim+8, attacker, info, receive, *range(5, 13), self.stack, self.end, self.code+12]
            regs, _, _ = p.run(regs, 0xa000001f, {self.values['OLD_CONTACT']})
            regs[15] = regs[4]
            seen = []

            def native(p, r, flags):
                seen.append((p.get(r[3]), p.get(r[3]+4), p.get(r[13])))
                p.put(r[0], 4)
                return flags

            p.run(regs, 0xa000001f, {self.end}, {receive: native})
            self.assertEqual(seen, [(kind, 0x1800 if vtable == 0x02130100 else 0x2400, 0x2400)])
            self.assertEqual((p.get(info), p.get(info+4)), (0x12, 0x1800))

    def test_interrupted_owner_clears_the_landing_token(self):
        for addr, value in ((self.ctl+0x14, 63), (self.ctl+0x14, 74), (self.hero+0x34, 0),
                            (self.bits, 0), (self.hero+0x30, self.motion+4)):
            p = self.fixture()
            self.run_hook(p, 0, self.values['OLD_ANIMATION'])
            p.put(addr, value)
            self.run_hook(p, 4, self.values['OLD_THINK'])
            self.assertEqual(p.get(self.state), 0)

    def test_ground_release_rejects_only_the_pending_native_slam_sample(self):
        p = self.fixture()
        p.put(self.state+12, self.motion)
        result, attacker, info = self.stack+0x20, self.stack+0x24, self.stack+0x40
        p.put(attacker, self.hero)
        p.put(info, 0x12)
        regs = [result, 0, attacker, info, *range(4, 13), self.stack, self.end, self.code+12]
        p.run(regs, 0xa000001f, {0x0207862c})
        self.assertEqual(p.get(result), 1)
        p.put(info, 0x04)
        p.run(regs, 0xa000001f, {self.values['OLD_CONTACT']})
        self.run_hook(p, 4, self.values['OLD_THINK'])
        self.assertEqual(p.get(self.state+12), 0)


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'private clean ROM missing')
class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = f.PARENT_PATH.read_bytes()
        cls.rom, cls.report = f.apply_rom(cls.parent)

    def test_only_private_scas_and_english_slots_change(self):
        names, blobs = spider2099.resources(self.rom)
        old_names, old = spider2099.resources(self.parent)
        self.assertEqual(names[:len(old_names)], old_names)
        self.assertEqual(tuple(names[len(old_names):]), f.art.NAMES)
        self.assertEqual({n for n, a, b in zip(names, old, blobs) if a != b},
                         {'American.strings', 'English.strings', 'GlobFiles.txt'})
        for name, original, count in zip(f.art.NAMES, f.art.TEMPLATES, (24, 19)):
            authored = blobs[names.index(name)]
            self.assertNotEqual(authored, blobs[names.index(original)])
            self.assertEqual(Sca.parse(authored).frame_count, count)
        for name in ('American.strings', 'English.strings'):
            for index, text in f.TEXT.items():
                self.assertEqual(decode_grown(blobs[names.index(name)], index), text)

    def test_native_shop_and_32_kib_player_kit_keep_their_bytes(self):
        def arm(rom):
            header = w.parse_header(rom)
            return rom[header['arm9_offset']:header['arm9_offset']+header['arm9_size']]
        before, after = arm(self.parent), arm(self.rom)
        count = w.u32(before, hunter_kit.BLACK_COUNT)
        shop = kit.SOURCE + w.u32(before, hunter_kit.BLACK_POINTER) - kit.TARGET
        self.assertEqual(w.u32(after, hunter_kit.BLACK_COUNT), count)
        self.assertEqual(w.u32(after, hunter_kit.BLACK_POINTER), w.u32(before, hunter_kit.BLACK_POINTER))
        self.assertEqual(before[shop:shop+32*count], after[shop:shop+32*count])
        self.assertEqual(before[kit.SOURCE:kit.SOURCE+kit.RESERVE], after[kit.SOURCE:kit.SOURCE+kit.RESERVE])


if __name__ == '__main__':
    unittest.main()
