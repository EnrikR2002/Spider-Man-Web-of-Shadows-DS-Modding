import json
from pathlib import Path
import tempfile
import unittest
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

    def test_existing_bad_safety_snapshot_blocks_restore(self):
        saves.backup(self.save, 'checkpoint', self.store)
        current = b'current save'
        self.save.write_bytes(current)
        safety = 'before-restore-dsv-' + w.sha256(current)
        saves.backup(self.save, safety, self.store)
        (self.store / safety / 'save.dsv').write_bytes(b'corrupt')
        with self.assertRaises(ValueError): saves.restore('checkpoint', self.save, self.store)
        self.assertEqual(self.save.read_bytes(), current)