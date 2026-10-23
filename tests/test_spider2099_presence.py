"""2099-only draw scale/tints, native ABI and exact appearance release scope."""
import struct
import unittest

from tests import test_spider2099_polish as legacy
from tests.arm_runtime import ArmProbe
from tools import spider2099_presence as p, spider2099 as assets, wos_tool as w, tasm_kit as kit
from tools import spider2099_visual as visual
from tools.chapter_renewal_combat import asm
from tools.model_geometry import ModelGeometry


class PresenceSelectorABI(legacy.VisualSelectorABI):
    @classmethod
    def setUpClass(cls):
        names, blobs = assets.resources(p.PARENT_PATH.read_bytes())
        cls.shared = blobs[names.index('spd.nsbmd')]
        g = ModelGeometry.parse(cls.shared)
        cls.metadata = dict(model_size=w.u32(cls.shared, g.model),
            metadata_offset=len(cls.shared)-visual.TRAILER_SIZE-g.model,
            shape_offset=g.shapes[0].header-g.model, material_offset=visual.material(cls.shared)-g.model,
            trailer=list(struct.unpack_from('<16I', cls.shared, len(cls.shared)-64)))

    def fixture(self, form=1):
        probe = super().fixture(form)
        probe.code(self.code_at, asm(p.selector_source(self.code_at, self.metadata), self.code_at))
        self.commands = []
        return probe

    def call(self, probe, flags=0xb000001f, owner=None):
        def fifo(mem, regs, cpsr):
            self.assertEqual((regs[0], regs[2]), (0x1b, 3))
            self.commands.append([mem.get(regs[1]+i*4) for i in range(3)])
            for i in (0, 1, 2, 3, 12):
                regs[i] = 0xdeadbeef
            return 0x0800001f
        regs = list(range(13))+[0x023f0000, 0x02010000, self.code_at]
        regs[5] = self.owner if owner is None else owner
        out, cpsr, _ = probe.run(regs, flags, {visual.HOOK_EXEC+4}, {0x01ffc004: fifo})
        self.assertEqual(out[0], regs[5])
        self.assertEqual(out[1:15], regs[1:15])
        self.assertEqual(cpsr, flags)
        return out

    def test_black_then_red_switches_only_shape_material_fields(self):
        probe = self.fixture()
        before = dict(probe.memory)
        self.call(probe)
        self.assertEqual(self.commands, [[4096, 4608, 4096]])
        allowed = {self.mdl+self.metadata['shape_offset']+i for i in range(8, 16)}
        allowed |= {self.mdl+self.metadata['material_offset']+i for i in range(32, 44)}
        self.assertTrue({at for at in before if before[at] != probe.memory[at]} <= allowed)
        probe.memory[self.stats+0x53] = 0
        self.call(probe)
        self.assertEqual(self.commands, [[4096, 4608, 4096]])
        self.assertEqual(probe.get(self.mdl+self.metadata['shape_offset']+8), self.metadata['trailer'][4])

    def test_both_color_getters_preserve_registers_flags_and_native_red_colors(self):
        for entry, original in ((0, 0x7fff), (4, 0x5967)):
            for form in (0, 1, 2):
                for flags in range(16):
                    probe = ArmProbe()
                    probe.code(self.code_at, asm(p.colors_source(), self.code_at))
                    probe.put(self.owner+0x34, form)
                    regs = list(range(16))
                    regs[0], regs[13], regs[14], regs[15] = self.owner, 0x023f0000, 0x02010000, self.code_at+entry
                    cpsr = flags<<28 | 0x0800001f
                    out, after, _ = probe.run(regs, cpsr, {regs[14]})
                    self.assertEqual(out[0], p.WEB_COLOR if form == 1 else original)
                    self.assertEqual(out[1:15], regs[1:15])
                    self.assertEqual(after, cpsr)


class Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = p.PARENT_PATH.read_bytes()
        cls.result, cls.report = p.apply_rom(cls.parent)

    def test_only_version_text_and_bounded_cosmetic_code_change(self):
        an, aa = assets.resources(self.parent)
        bn, bb = assets.resources(self.result)
        self.assertEqual(an, bn)
        self.assertEqual([n for n, a, b in zip(an, aa, bb) if a != b], ['American.strings', 'English.strings'])
        h = w.parse_header(self.parent)
        old = self.parent[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        new = self.result[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        allowed = {i for block in ('selector', 'colors') for i in range(
            self.report[block]['source_offset'], self.report[block]['source_offset']+self.report[block]['bytes'])}
        allowed |= {i for site in self.report['colors']['getters'] for i in range(site-kit.BASE, site-kit.BASE+4)}
        self.assertTrue({i for i, (a, b) in enumerate(zip(old, new)) if a != b} <= allowed)
        self.assertEqual(old[kit.SOURCE:kit.SOURCE+kit.RESERVE], new[kit.SOURCE:kit.SOURCE+kit.RESERVE])
        a, b = bytearray(self.parent), bytearray(self.result)
        ge = next(e for e in w.nitrofs_entries(self.parent) if e['name'] == 'Glob.bin')
        for start, size in ((h['arm9_offset'], h['arm9_size']), (ge['start'], ge['size'])):
            a[start:start+size] = b[start:start+size] = bytes(size)
        self.assertEqual(a, b)

    def test_exact_parent_and_build_output_guards(self):
        with self.assertRaisesRegex(ValueError, 'exact published v0.33.0'):
            p.apply_rom(b'foreign')
        with self.assertRaisesRegex(ValueError, 'Candidates belong in build'):
            p.generate(p.ROOT/'original')

    def test_only_boot_and_options_text_slots_change(self):
        from tools.qol_suits_menu import decode_grown, slot_count
        names, before = assets.resources(self.parent)
        _, after = assets.resources(self.result)
        for name in ('American.strings', 'English.strings'):
            a, b = before[names.index(name)], after[names.index(name)]
            self.assertEqual(slot_count(a), slot_count(b))
            self.assertEqual([i for i in range(slot_count(a)) if decode_grown(a, i) != decode_grown(b, i)], [50, 74])
            for i in (50, 74):
                self.assertIn(p.VERSION, decode_grown(b, i))


if __name__ == '__main__':
    unittest.main()
