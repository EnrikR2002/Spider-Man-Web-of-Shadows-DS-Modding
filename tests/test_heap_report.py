"""Native expanded-heap walker reads free/used block lists from a RAM image."""
import struct
import unittest

from tools import heap_report as h


def put(ram, address, fmt, *values):
    struct.pack_into(fmt, ram, address - h.BASE, *values)


class HeapReportTests(unittest.TestCase):
    def ram(self):
        ram = bytearray(0x200000)
        for i in range(h.COUNT):
            handle = 0x02100000 + i * 0x1000
            put(ram, h.TABLE + i * h.ENTRY, '<I', handle)
            put(ram, handle, '<I', h.EXPH)
            put(ram, handle + 0x18, '<II', handle + 0x40, handle + 0x1000)
            put(ram, handle + 0x24, '<I', handle + 0x100)       # free: 0x100 -> 0x300
            put(ram, handle + 0x2C, '<I', handle + 0x200)       # used: 0x200
            put(ram, handle + 0x100, '<HHIII', h.FREE, 0, 0x80, 0, handle + 0x300)
            put(ram, handle + 0x300, '<HHIII', h.FREE, 0, 0x400, handle + 0x100, 0)
            put(ram, handle + 0x200, '<HHIII', h.USED, i, 0x60, 0, 0)
        return ram

    def test_totals(self):
        report = h.heaps(bytes(self.ram()))
        self.assertEqual(len(report), 4)
        self.assertEqual({k: report[2][k] for k in ('free', 'largest_free', 'free_blocks', 'used', 'used_blocks')},
                         {'free': 0x480, 'largest_free': 0x400, 'free_blocks': 2, 'used': 0x60, 'used_blocks': 1})
        self.assertEqual(report[0]['end'] - report[0]['start'], 0x1000 - 0x40)

    def test_rejects_cycles_and_bad_signatures(self):
        ram = self.ram()
        put(ram, 0x02100300 + 0xC, '<I', 0x02100100)            # free list loops back
        with self.assertRaisesRegex(ValueError, 'bad block'):
            h.heaps(bytes(ram))
        ram = self.ram()
        put(ram, 0x02100200, '<H', h.FREE)                      # used block with a free tag
        with self.assertRaisesRegex(ValueError, 'signature'):
            h.heaps(bytes(ram))


if __name__ == '__main__':
    unittest.main()
