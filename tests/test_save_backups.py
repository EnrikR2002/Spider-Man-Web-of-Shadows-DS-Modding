import json
import io
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools import save_backups as saves
from tools import wos_tool as w


class SaveBackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = self.root / 'snapshots'
        self.save = self.root / 'progress.dsv'
        self.original = bytes(range(256)) + b'opaque footer\x00\xff'
        self.save.write_bytes(self.original)

    def test_roundtrip_preserves_current_save_before_restore(self):
        saves.backup(self.save, 'before-boss', self.store)
        current = b'new progress including unknown bytes\xff'
        self.save.write_bytes(current)
        safety = saves.restore('before-boss', self.save, self.store)
        self.assertEqual(self.save.read_bytes(), self.original)
        self.assertEqual(saves.load_snapshot(safety, self.store)[1], current)
        self.assertEqual(saves.restore('before-boss', self.save, self.store), None)
        saves.restore(safety, self.save, self.store)
        self.assertEqual(self.save.read_bytes(), current)

    def test_missing_destination_same_format_different_name(self):
        saves.backup(self.save, 'marker-test', self.store)
        dest = self.root / 'another-rom' / 'experiment.dsv'
        self.assertIsNone(saves.restore('marker-test', dest, self.store))
        self.assertEqual(dest.read_bytes(), self.original)
        self.assertEqual(self.save.read_bytes(), self.original)

    def test_duplicate_and_tamper_fail_without_touching_save(self):
        saves.backup(self.save, 'checkpoint', self.store)
        with self.assertRaises(FileExistsError): saves.backup(self.save, 'checkpoint', self.store)
        (self.store / 'checkpoint/save.dsv').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'mismatch'): saves.restore('checkpoint', self.save, self.store)
        self.assertEqual(self.save.read_bytes(), self.original)

    def test_failed_backup_leaves_no_partial_snapshot_and_can_retry(self):
        write = w.atomic_write
        for filename in ('save.dsv', 'snapshot.json'):
            with self.subTest(filename=filename):
                def fail_after_write(path, data, sources=()):
                    write(path, data, sources)
                    if Path(path).name == filename: raise OSError('injected checkpoint failure')
                with patch.object(w, 'atomic_write', side_effect=fail_after_write):
                    with self.assertRaisesRegex(OSError, 'injected checkpoint failure'):
                        saves.backup(self.save, 'checkpoint', self.store)
                self.assertEqual(list(self.store.iterdir()), [])
                self.assertEqual(self.save.read_bytes(), self.original)
        with patch.object(saves, 'load_snapshot', side_effect=ValueError('verification failed')):
            with self.assertRaisesRegex(ValueError, 'verification failed'):
                saves.backup(self.save, 'checkpoint', self.store)
        with patch.object(Path, 'rename', side_effect=OSError('rename failed')):
            with self.assertRaisesRegex(OSError, 'rename failed'):
                saves.backup(self.save, 'checkpoint', self.store)
        self.assertEqual(list(self.store.iterdir()), [])
        saves.backup(self.save, 'checkpoint', self.store)
        self.assertEqual(saves.load_snapshot('checkpoint', self.store)[1], self.original)

    def test_corrupt_metadata_and_format_conversion_rejected(self):
        saves.backup(self.save, 'checkpoint', self.store)
        with self.assertRaisesRegex(ValueError, 'convert'):
            saves.restore('checkpoint', self.root / 'wrong.sav', self.store)
        meta = self.store / 'checkpoint/snapshot.json'
        meta.write_text(json.dumps({'schema_version': 1, 'suffix': '../escape'}))
        with self.assertRaises(ValueError): saves.restore('checkpoint', self.save, self.store)
        self.assertEqual(self.save.read_bytes(), self.original)

    def test_invalid_names_paths_and_empty_save(self):
        for name in ('../escape', 'a/b', 'CON', '', 'x' * 97):
            with self.assertRaises(ValueError): saves.backup(self.save, name, self.store)
        for path in (Path('relative.dsv'), self.root / 'rom.nds', w.PROJECT / 'original/test.sav'):
            with self.assertRaises(ValueError): saves.save_path(path)
        self.save.write_bytes(b'')
        with self.assertRaises(ValueError): saves.backup(self.save, 'empty', self.store)
        self.assertFalse(self.store.exists())

    def test_storage_cannot_be_restore_target_or_backup_source(self):
        saves.backup(self.save, 'checkpoint', self.store)
        path = self.store / 'checkpoint/save.dsv'
        with self.assertRaises(ValueError): saves.restore('checkpoint', path, self.store)
        with self.assertRaises(ValueError): saves.backup(path, 'copy', self.store)

    def test_checkpoint_lists_ignore_incomplete_internal_staging(self):
        from tools import playtest
        saves.backup(self.save, 'checkpoint', self.store)
        (self.store/(saves.STAGING_PREFIX+'interrupted')).mkdir()
        output = io.StringIO()
        with redirect_stdout(output): playtest.list_snapshots(self.store)
        self.assertIn('checkpoint:', output.getvalue())
        self.assertNotIn('interrupted', output.getvalue())
        load = saves.load_snapshot
        output = io.StringIO()
        with patch.object(saves, 'STORE', self.store), \
             patch.object(saves, 'load_snapshot', side_effect=lambda name: load(name, self.store)), \
             redirect_stdout(output):
            self.assertEqual(saves.main(['list']), 0)
        self.assertIn('checkpoint ', output.getvalue())
        self.assertNotIn('interrupted', output.getvalue())

    def test_existing_bad_safety_snapshot_blocks_restore(self):
        saves.backup(self.save, 'checkpoint', self.store)
        current = b'current save'
        self.save.write_bytes(current)
        safety = 'before-restore-dsv-' + w.sha256(current)
        saves.backup(self.save, safety, self.store)
        (self.store / safety / 'save.dsv').write_bytes(b'corrupt')
        with self.assertRaises(ValueError): saves.restore('checkpoint', self.save, self.store)
        self.assertEqual(self.save.read_bytes(), current)
