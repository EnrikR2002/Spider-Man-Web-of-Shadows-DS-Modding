"""EUR decomp tables map to USA code addresses and verify against ARM9 bytes."""
import struct
import tempfile
import unittest
from pathlib import Path

from tools import decomp_xref as x


def bl(at, target):
    return struct.pack('<I', 0xEB000000 | ((target - at - 8) >> 2) & 0xFFFFFF)


class DecompXrefTests(unittest.TestCase):
    def fixture(self):
        folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (folder / 'itcm').mkdir()
        (folder / 'symbols.txt').write_text(
            'func_02000100 kind:function(arm,size=0x10) addr:0x02000100\n'
            'func_020a0004 kind:function(arm,size=0x8) addr:0x020a0004\n'
            'data_02120000 kind:data(any) addr:0x02120000\n')
        (folder / 'relocs.txt').write_text(
            'from:0x02000104 kind:arm_call to:0x020a0004 module:main\n'
            'from:0x02120000 kind:load to:0x02000100 module:main\n')
        (folder / 'itcm/symbols.txt').write_text('func_01ff8000 kind:function(arm,size=0x8) addr:0x01ff8000\n')
        (folder / 'itcm/relocs.txt').write_text('from:0x01ff8000 kind:arm_call to:0x020a0004 module:main\n')
        arm9 = bytearray(x.ITCM_SOURCE + 8)
        arm9[0x104:0x108] = bl(0x02000104, 0x020A0000)  # EUR target 0x020A0004 is USA 0x020A0000
        arm9[x.ITCM_SOURCE:x.ITCM_SOURCE + 4] = bl(0x01FF8000, 0x020A0000)
        return folder, arm9

    def test_shift_rule_and_data_refusal(self):
        self.assertEqual(x.usa(0x02084AA0), 0x02084AA0)
        self.assertEqual(x.usa(0x02084AA4), 0x02084AA0)
        self.assertEqual(x.eur(0x02084AA0), 0x02084AA4)
        with self.assertRaises(ValueError): x.usa(0x02127920)

    def test_verify_callers_and_callees(self):
        folder, arm9 = self.fixture()
        funcs, relocs = x.load(folder)
        self.assertEqual(x.verify(bytes(arm9), relocs), {'ok': 2, 'bad': 0})
        self.assertEqual(x.callers(funcs, relocs, 0x020A0000),
                         [(0x01FF8000, 'func_01ff8000', 'arm_call'), (0x02000100, 'func_02000100', 'arm_call')])
        self.assertEqual(x.callers(funcs, relocs, 0x02000100), [(0x02120000, 'eur-data', 'load')])
        self.assertEqual(x.callees(funcs, relocs, 0x02000108)[1], [(0x02000104, 'arm_call', 0x020A0000, 'usa')])
        arm9[0x104:0x108] = bl(0x02000104, 0x020A0004)
        self.assertEqual(x.verify(bytes(arm9), relocs), {'ok': 1, 'bad': 1})


if __name__ == '__main__':
    unittest.main()
