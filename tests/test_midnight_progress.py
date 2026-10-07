import unittest

from tools import midnight_progress as m


class MidnightProgressTests(unittest.TestCase):
    def test_all_valid_milestones_preserve_unrelated_bits(self):
        for other in (0, 7, 0xAB000007, 0xFF000000):
            word = other
            for progress in (m.Progress(True), m.Progress(True, True), m.Progress(True, True, True), m.Progress()):
                word = m.encode(word, progress)
                self.assertEqual(word & ~m.MASK, other)
                self.assertEqual(m.decode(word), progress)

    def test_unknown_allocation_and_version_are_never_overwritten(self):
        for word in (8, 0x00112240, m.MAGIC | 0x80, m.MAGIC | 0x40 | 32):
            with self.assertRaises(ValueError): m.encode(word, m.Progress(True))

    def test_invalid_prerequisites_and_word_bounds(self):
        for flags in ((False, True, False), (True, False, True), (1, False, False)):
            with self.assertRaises(ValueError): m.Progress(*flags)
        for word in (-1, 1 << 32, True):
            with self.assertRaises(ValueError): m.decode(word)


if __name__ == '__main__': unittest.main()
