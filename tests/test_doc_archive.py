"""Archive integrity and bounded reading; no ROM/emulator required."""
import hashlib
import unittest

from tools import doc_archive as docs


class DocumentationArchiveTests(unittest.TestCase):
    def test_complete_historical_archive_hashes(self):
        index, archive = docs.load_index()
        self.assertEqual(docs.verify_archive(), len(index['entries']))
        entry = docs.resolve_entry(index['entries'], 'FORMAT_NOTES.md')
        self.assertGreater(len(docs.read_entry(archive, entry).splitlines()), 1000)

    def test_section_stops_at_sibling_and_supports_continuation(self):
        body = '# Note\n## First\none\n### Child\ntwo\n## Second\nthree\n'
        selected, more = docs.select_lines(body, section='First', count=2)
        self.assertEqual(selected, [(2, '## First'), (3, 'one')])
        self.assertTrue(more)
        selected, more = docs.select_lines(body, section='First', start=4, count=80)
        self.assertEqual(selected, [(4, '### Child'), (5, 'two')])
        self.assertFalse(more)

    def test_invalid_or_ambiguous_selection_rejected(self):
        for options in ({'section': 'missing'}, {'section': 'Same'}, {'start': 0}, {'count': 0}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                docs.select_lines('# Note\n## Same A\n## Same B\n', **options)
        with self.assertRaises(ValueError):
            docs.resolve_entry([{'path': 'a/NOTE.md'}, {'path': 'b/NOTE.md'}], 'NOTE.md')

    def test_corrupt_entry_metadata_rejected(self):
        index, archive = docs.load_index()
        entry = dict(index['entries'][0], sha256=hashlib.sha256(b'wrong').hexdigest())
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            docs.read_entry(archive, entry)


if __name__ == '__main__':
    unittest.main()
