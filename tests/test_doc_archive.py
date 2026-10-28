"""Archive integrity and bounded reading; no ROM/emulator required."""
import hashlib
import io
from contextlib import ExitStack
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import doc_archive as docs


class DocumentationArchiveTests(unittest.TestCase):
    def copied_archive(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        index_path = Path(temporary.name) / 'index.json'
        shutil.copy(docs.INDEX, index_path)
        shutil.copy(docs.INDEX.with_name('legacy-notes.zip'), index_path.with_name('legacy-notes.zip'))
        return index_path

    def test_failed_archive_update_restores_both_files_and_allows_retry(self):
        write = docs.w.atomic_write
        for failure in ('legacy-notes.zip', 'index.json', 'verification'):
            with self.subTest(failure=failure):
                index_path = self.copied_archive()
                before = {p: p.read_bytes() for p in (index_path, index_path.with_name('legacy-notes.zip'))}
                count = docs.verify_archive(index_path)
                failed = False
                def fail_after_write(path, data, sources=()):
                    nonlocal failed
                    write(path, data, sources)
                    if Path(path) == index_path.with_name(failure) and not failed:
                        failed = True
                        raise OSError('injected archive failure')
                with ExitStack() as stack:
                    stack.enter_context(patch.object(docs.w, 'atomic_write', side_effect=fail_after_write))
                    if failure == 'verification':
                        stack.enter_context(patch.object(docs, 'verify_archive', side_effect=ValueError('verification failed')))
                    with self.assertRaises((OSError, ValueError)):
                        docs.add_entry('RETRY.md', b'# Retry\n', title='Retry', snapshot_date='2026-10-28',
                                       source_revision='fixture', index_path=index_path)
                for path, raw in before.items(): self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(docs.verify_archive(index_path), count)
                self.assertEqual(list(index_path.parent.glob('.archive-recovery-*')), [])
                self.assertEqual(docs.add_entry('RETRY.md', b'# Retry\n', title='Retry', snapshot_date='2026-10-28',
                                               source_revision='fixture', index_path=index_path), count+1)

    def test_incomplete_archive_rollback_retains_exact_recovery_copies(self):
        for recovery_error in (OSError, KeyboardInterrupt):
            with self.subTest(recovery_error=recovery_error):
                index_path = self.copied_archive(); archive = index_path.with_name('legacy-notes.zip')
                before = {p: p.read_bytes() for p in (index_path, archive)}
                write = docs.w.atomic_write
                failed = False
                def fail_update_and_archive_recovery(path, data, sources=()):
                    nonlocal failed
                    path = Path(path)
                    if path == archive and failed: raise recovery_error('archive recovery locked')
                    write(path, data, sources)
                    if path == index_path and not failed:
                        failed = True
                        raise OSError('index write failed')
                message = 'rollback incomplete.*Backups:' if recovery_error is OSError else 'recovery locked'
                with patch.object(docs.w, 'atomic_write', side_effect=fail_update_and_archive_recovery):
                    with self.assertRaisesRegex(recovery_error, message):
                        docs.add_entry('FAILED.md', b'# Failed\n', title='Failed', snapshot_date='2026-10-28',
                                       source_revision='fixture', index_path=index_path)
                recovery, = index_path.parent.glob('.archive-recovery-*')
                for path, raw in before.items(): self.assertEqual((recovery/path.name).read_bytes(), raw)
                self.assertEqual(index_path.read_bytes(), before[index_path])

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
