"""Archive integrity and bounded reading; no ROM/emulator required."""
import hashlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_reader_labels_each_snapshot_with_its_recorded_date(self):
        for entry_date, expected in ((None, '2026-10-05'), ('2026-10-21', '2026-10-21')):
            with self.subTest(entry_date=entry_date):
                entry = {'path': 'NOTE.md'}
                if entry_date is not None:
                    entry['snapshot_date'] = entry_date
                index = {'snapshot_date': '2026-10-05', 'entries': [entry]}
                with patch.object(docs, 'load_index', return_value=(index, None)), \
                     patch.object(docs, 'read_entry', return_value='# Note\n'), \
                     patch('sys.stdout', new_callable=io.StringIO) as output:
                    docs.main(['read', 'NOTE.md', '--lines', '1'])
                self.assertIn(f'Historical snapshot {expected}: NOTE.md', output.getvalue())

    def test_add_appends_one_note_and_repins_the_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            index_path = Path(folder) / 'index.json'
            shutil.copy(docs.INDEX, index_path)
            shutil.copy(docs.INDEX.with_name('legacy-notes.zip'), Path(folder) / 'legacy-notes.zip')
            before = docs.verify_archive(index_path)
            raw = '# Retired\n```text\n# not a heading\n```\n## Kept part\nbody\n'.encode()
            self.assertEqual(docs.add_entry('docs/RETIRED-TEST.md', raw, title='Retired test',
                                            snapshot_date='2026-10-24', source_revision='abc',
                                            index_path=index_path), before + 1)
            index, archive = docs.load_index(index_path)
            entry = docs.resolve_entry(index['entries'], 'RETIRED-TEST.md')
            self.assertEqual(docs.read_entry(archive, entry).encode(), raw)
            self.assertEqual([s['heading'] for s in entry['sections']], ['Retired', 'Kept part'])
            with self.assertRaisesRegex(ValueError, 'already holds'):
                docs.add_entry('docs/retired-test.md', raw, title='Again', snapshot_date='2026-10-24',
                               source_revision='abc', index_path=index_path)
            with self.assertRaisesRegex(ValueError, 'YYYY-MM-DD'):
                docs.add_entry('docs/OTHER.md', raw, title='Bad date', snapshot_date='24/10/2026',
                               source_revision='abc', index_path=index_path)

if __name__ == '__main__':
    unittest.main()
