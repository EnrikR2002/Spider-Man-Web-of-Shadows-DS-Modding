"""Probe Talon Pounce's gated takeoff, receiver ABI and exact resource scope."""
import unittest

import mod
from tests.arm_runtime import ArmProbe
from tools import hunter_kit, spider2099, talon_pounce as t, tasm_kit as kit, wos_tool as w
from tools.qol_suits_menu import decode_grown


class Runtime(unittest.TestCase):
    code, state = 0x021a1000, 0x021a0000
    hero, motion, ctl, bits = 0x02200000, 0x02201000, 0x02202000, 0x0220300c
    stack, end = 0x023f0000, 0x03000000
    pad, trace = 0x02145a48, 0x02029240
    values = dict(STATE=state, BOSS_CONFIG=0x0215a52c, POUNCE_CONTACT=0x021b0000,
                  BOARD_STATE=0x021b0500, BOARD_TARGET=0x021b0600,
                  OLD_THINK=0x021b0100, OLD_ANIMATION=0x021b0200,
                  OLD_UPDATE=0x021b0300, OLD_CONTACT=0x021b0400)
    values.update({f'{part}_{kind}': 6008+3*i+j for i, part in enumerate(('COIL', 'QUICK', 'LOW', 'HIGH'))
                   for j, kind in enumerate(('SCA', 'GMB', 'GAB'))})

    @classmethod
    def setUpClass(cls):
        cls.code_bytes = t.runtime(cls.code, cls.values)

    def fixture(self, quick=False):
        p = ArmProbe()
        p.code(self.code, self.code_bytes)
        p.code(self.state, bytes(36))
        p.code(self.pad, bytes(12))
        words = {self.hero: 0x0212e3f0, self.hero+0x30: self.motion, self.hero+0x34: 1,
                 self.hero+0xe8: self.bits, self.bits: 1 << 25 | int(quick) << 26,
                 self.bits-12: 70, self.motion: self.hero, self.motion+0x1f8: self.ctl,
                 self.motion+0x258: 55, self.motion+0x2fc: 0, self.motion+0x180: 1,
                 self.motion+0x2ac: 4096, self.ctl: 0x021352a4, self.ctl+0x14: 46,
                 self.ctl+0x44: self.hero}
        for addr, value in words.items():
            p.put(addr, value)
        return p

    def regs(self, slot):
        return [*range(13), self.stack, self.end, self.code+4*slot]

    def test_native_charge_thresholds_and_release_aim(self):
        for quick in (False, True):
            for ready in (False, True):
                p = self.fixture(quick)
                regs = self.regs(0)
                regs[8] = self.ctl
                p.run(regs, 0x1f, {0x020c361c})
                self.assertEqual(p.get(self.state+12), 2 if quick else 1)
                p.put(self.state+16, (8 if quick else 16) - int(not ready))
                p.put(self.pad, 0x60 << 16)  # Up+Left on the release update.
                regs = self.regs(1)
                regs[0] = self.ctl

                def empty_queue(_, r, flags):
                    r[0] = 0
                    return flags

                out, _, _ = p.run(regs, 0x1f, {self.end}, {0x020cff0c: empty_queue})
                self.assertEqual(out[0], 15 if ready else 46)
                self.assertEqual(p.get(self.state+12), 4 if ready else 0)
                self.assertEqual(p.get(self.motion+0x258), 1 if ready else 55)
                if ready:
                    self.assertEqual(p.get(self.state+24), 0)

    def test_same_frame_cancel_and_wall_block_do_not_dispatch_private_hits(self):
        for active in (False, True):
            p = self.fixture()
            p.put(self.state, self.motion)
            p.put(self.state+4, self.ctl)
            p.put(self.state+8, 70)
            p.put(self.state+12, 3 if active else 0)
            p.put(self.motion+0x230, self.values['LOW_GMB'])
            p.put(self.ctl+0x14, 51)
            victim, vm, room, bsp = 0x02210000, 0x02211000, 0x02212000, 0x02213000
            result, attacker = self.stack+0x20, self.stack+0x24
            p.put(attacker, self.hero)
            p.put(victim+0x30, vm)
            p.put(0x02145c3c, room)
            p.put(room, bsp)
            for motion, x in ((self.motion, 220), (vm, 244)):
                for off, value in ((0x7c, x*4096), (0x80, 5*4096), (0x160, 0), (0x164, 0)):
                    p.put(motion+off, value)

            def wall(probe, r, flags):
                self.assertEqual(probe.get(r[3]), 24*4096)
                probe.put(r[0]+0x10, 0x900)
                return flags

            regs = self.regs(4)
            regs[:3] = [result, victim+8, attacker]
            out, cpsr, _ = p.run(regs, 0xa000001f, {0x0207862c}, {self.trace: wall})
            self.assertEqual(p.get(result), 1)
            self.assertEqual(out[4:14], regs[4:14])
            self.assertEqual(cpsr, 0xa000001f)


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'private clean ROM missing')
class Build(unittest.TestCase):
    def test_keeps_shop_and_player_kit_and_appends_only_private_animations(self):
        parent = t.PARENT_PATH.read_bytes()
        rom, report = t.apply_rom(parent)
        old_names, old_blobs = spider2099.resources(parent)
        names, blobs = spider2099.resources(rom)
        self.assertEqual(names[:len(old_names)], old_names)
        self.assertEqual(names[len(old_names):], report['added_resources'])
        self.assertEqual({n for n, a, b in zip(names, old_blobs, blobs) if a != b},
                         {'American.strings', 'English.strings', 'GlobFiles.txt'})
        for name in ('American.strings', 'English.strings'):
            for slot, text in t.TEXT.items():
                self.assertEqual(decode_grown(blobs[names.index(name)], slot), text)

        def arm(image):
            header = w.parse_header(image)
            return image[header['arm9_offset']:header['arm9_offset']+header['arm9_size']]

        before, after = arm(parent), arm(rom)
        shop = kit.SOURCE+w.u32(before, hunter_kit.BLACK_POINTER)-kit.TARGET
        count = w.u32(before, hunter_kit.BLACK_COUNT)
        self.assertEqual(w.u32(after, hunter_kit.BLACK_POINTER), w.u32(before, hunter_kit.BLACK_POINTER))
        self.assertEqual(w.u32(after, hunter_kit.BLACK_COUNT), count)
        self.assertEqual(before[shop:shop+32*count], after[shop:shop+32*count])
        self.assertEqual(before[kit.SOURCE:kit.SOURCE+kit.RESERVE], after[kit.SOURCE:kit.SOURCE+kit.RESERVE])
        self.assertEqual(w.u32(before, shop+32*5), 334)
        self.assertEqual(w.u32(before, shop+32*5+28), 225)


if __name__ == '__main__':
    unittest.main()
