import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from tools import playtest as p
from tools import save_backups as saves
from tools import release_info
from tests.test_desmume_save import dsv


class PlaytestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.battery = self.root / 'Battery'
        self.battery.mkdir()
        self.config = self.root / 'playtest.json'
        self.store = self.root / 'snapshots'
        self.source = self.battery / 'old-experiment.dsv'
        self.source.write_bytes(dsv(b'opaque current progress\x00\xff'))
        self.destination = p.configure(self.battery, self.config)
        self.rom = self.root / p.ROM.name
        self.candidate = self.root / 'candidate.nds'
        for name, value in (('ROM', self.rom), ('CANDIDATE', self.candidate), ('RELEASES', self.root/'releases')):
            patcher = patch.object(p, name, value); patcher.start(); self.addCleanup(patcher.stop)
        self.history = self.root / 'history.json'
        patcher = patch.object(release_info, 'HISTORY', self.history)
        patcher.start(); self.addCleanup(patcher.stop)
        self.candidate.write_bytes(b'new rom')
        p.w.write_json(self.candidate.with_suffix('.build.json'), {
            'output_rom_sha256': p.w.sha256(b'new rom'), 'release_version': '9.9.9', 'release_date': '2026-10-23'})

    def test_config_and_adopt_restore_roundtrip_preserve_both_saves(self):
        self.assertEqual(p.current_save(self.config), self.destination)
        earlier = b'earlier stable save'
        self.destination.write_bytes(earlier)
        name, safety = p.adopt(self.source, self.destination, self.store)
        self.assertEqual(self.destination.read_bytes(), self.source.read_bytes())
        self.assertEqual(saves.load_snapshot(safety, self.store)[1], earlier)
        self.assertEqual(p.adopt(self.source, self.destination, self.store), (name, None))
        saves.backup(self.destination, 'early-room', self.store)
        self.destination.write_bytes(b'later room')
        safety = saves.restore('early-room', self.destination, self.store)
        self.assertEqual(self.destination.read_bytes(), self.source.read_bytes())
        self.assertEqual(saves.load_snapshot(safety, self.store)[1], b'later room')

    def test_repeated_build_keeps_rom_name_and_save_bytes(self):
        p.adopt(self.source, self.destination, self.store)
        self.rom.write_bytes(b'earlier rom'); self.candidate.write_bytes(b'new rom')
        with patch.object(p, 'assert_closed'), patch.object(p.mod, 'main', return_value=0) as build:
            self.assertEqual(p.build('mods/one', self.config, self.store), 0)
            self.assertEqual(p.build('mods/two', self.config, self.store), 0)
        self.assertEqual([call.args[0][-1] for call in build.call_args_list], [str(self.candidate)]*2)
        self.assertEqual(self.rom.read_bytes(), b'new rom')
        archived = [path.read_bytes() for path in (self.root/'releases').rglob('*.nds')]
        self.assertIn(b'earlier rom', archived)
        self.assertEqual(self.destination.read_bytes(), self.source.read_bytes())
        self.assertEqual(len(list(self.store.glob('before-build-*'))), 1)

    def test_republish_keeps_the_original_receipt_and_history_after_more_play(self):
        p.adopt(self.source, self.destination, self.store)
        self.rom.write_bytes(b'earlier rom')
        with patch.object(p, 'assert_closed'), patch.object(p.mod, 'main', return_value=0):
            self.assertEqual(p.build(config=self.config, store=self.store), 0)
            receipt = p.RELEASES / p.w.sha256(self.candidate.read_bytes()) / 'release.json'
            original = receipt.read_bytes(); history = self.history.read_bytes()
            self.destination.write_bytes(dsv(b'newer progress'))
            self.assertEqual(p.build(config=self.config, store=self.store), 0)
        self.assertEqual(receipt.read_bytes(), original)
        self.assertEqual(self.history.read_bytes(), history)
        saved = json.loads(original)
        self.assertEqual(saved['previous_rom_sha256'], p.w.sha256(b'earlier rom'))
        self.assertEqual(saves.load_snapshot(saved['battery_checkpoint'], self.store)[1], self.source.read_bytes())
        self.assertEqual(self.destination.read_bytes(), dsv(b'newer progress'))

    def test_failure_after_each_publication_write_restores_all_previous_files(self):
        p.adopt(self.source, self.destination, self.store)
        old_rom = b'earlier rom'
        old_log = json.dumps({'output_rom_sha256': p.w.sha256(old_rom)}).encode()
        old_history = json.dumps({'schema_version': 1, 'releases': []}).encode()
        stable_log = self.rom.with_suffix('.build.json')
        receipt = p.RELEASES / p.w.sha256(self.candidate.read_bytes()) / 'release.json'
        expected = {self.rom: old_rom, stable_log: old_log, receipt: None, self.history: old_history}
        write = p.w.atomic_write
        for failed_target in expected:
            with self.subTest(failed_target=failed_target.name):
                self.rom.write_bytes(old_rom); stable_log.write_bytes(old_log); self.history.write_bytes(old_history)
                failed = False
                def fail_after_write(target, data, sources=()):
                    nonlocal failed
                    write(target, data, sources)
                    if Path(target) == failed_target and not failed:
                        failed = True
                        raise OSError('injected publication failure')
                with patch.object(p, 'assert_closed'), patch.object(p.mod, 'main', return_value=0):
                    with patch.object(p.w, 'atomic_write', side_effect=fail_after_write):
                        with self.assertRaisesRegex(OSError, 'injected publication failure'):
                            p.build(config=self.config, store=self.store)
                self.assertTrue(failed)
                for target, data in expected.items():
                    self.assertEqual(target.read_bytes() if target.exists() else None, data)
                backup = p.RELEASES / p.w.sha256(old_rom) / self.rom.name
                self.assertEqual(backup.read_bytes(), old_rom)
                self.assertEqual(backup.with_suffix('.build.json').read_bytes(), old_log)
                self.assertEqual(self.destination.read_bytes(), self.source.read_bytes())

    def test_failed_first_publication_removes_partial_installation(self):
        receipt = p.RELEASES / p.w.sha256(self.candidate.read_bytes()) / 'release.json'
        write = p.w.atomic_write
        def fail_after_history(target, data, sources=()):
            write(target, data, sources)
            if Path(target) == self.history: raise OSError('history write failed')
        with patch.object(p, 'assert_closed'), patch.object(p.mod, 'main', return_value=0):
            with patch.object(p.w, 'atomic_write', side_effect=fail_after_history):
                with self.assertRaisesRegex(OSError, 'history write failed'):
                    p.build(config=self.config, store=self.store)
        for target in (self.rom, self.rom.with_suffix('.build.json'), receipt, self.history):
            self.assertFalse(target.exists())

    def test_rollback_continues_if_one_recovery_write_fails(self):
        self.rom.write_bytes(b'earlier rom')
        stable_log = self.rom.with_suffix('.build.json'); stable_log.write_bytes(b'old metadata')
        write = p.w.atomic_write
        def fail_metadata(target, data, sources=()):
            if Path(target) == stable_log:
                if data != b'old metadata': write(target, data, sources)
                raise OSError('metadata locked')
            write(target, data, sources)
        with patch.object(p, 'assert_closed'), patch.object(p.mod, 'main', return_value=0):
            with patch.object(p.w, 'atomic_write', side_effect=fail_metadata):
                with self.assertRaisesRegex(OSError, 'rollback incomplete.*Backups:'):
                    p.build(config=self.config, store=self.store)
        self.assertEqual(self.rom.read_bytes(), b'earlier rom')
        backup = p.RELEASES / p.w.sha256(b'earlier rom') / stable_log.name
        self.assertEqual(backup.read_bytes(), b'old metadata')

    def test_bad_candidate_metadata_or_receipt_blocks_installation(self):
        self.rom.write_bytes(b'earlier rom')
        log = self.candidate.with_suffix('.build.json'); metadata = log.read_bytes()
        receipt = p.RELEASES / p.w.sha256(self.candidate.read_bytes()) / 'release.json'
        with patch.object(p, 'assert_closed'), patch.object(p.mod, 'main', return_value=0):
            log.unlink()
            with self.assertRaises(FileNotFoundError): p.build(config=self.config, store=self.store)
            log.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'metadata'): p.build(config=self.config, store=self.store)
            log.write_bytes(metadata)
            p.w.write_json(receipt, {'schema_version': 1, 'rom_sha256': 'wrong', 'version': '9.9.9'})
            with self.assertRaisesRegex(ValueError, 'receipt'): p.build(config=self.config, store=self.store)
        self.assertEqual(self.rom.read_bytes(), b'earlier rom')

    def test_live_emulator_blocks_build_before_backup_or_rom_write(self):
        self.destination.write_bytes(b'progress')
        result = subprocess.CompletedProcess([], 0, '"DeSmuME_0.9.13_x64.exe","42"\n', '')
        with patch.object(p.os, 'name', 'nt'), patch.object(p.subprocess, 'run', return_value=result):
            with self.assertRaisesRegex(ValueError, 'close DeSmuME'):
                p.assert_closed()
        with patch.object(p, 'assert_closed', side_effect=ValueError('close DeSmuME')):
            with patch.object(p.mod, 'main') as build:
                with self.assertRaises(ValueError): p.build('mods', self.config, self.store)
                build.assert_not_called()
        self.assertFalse(self.store.exists())
        self.assertEqual(self.destination.read_bytes(), b'progress')

    def test_invalid_save_or_changed_save_blocks_publication(self):
        self.rom.write_bytes(b'earlier rom'); self.candidate.write_bytes(b'candidate rom')
        self.destination.write_bytes(b'invalid wrapper')
        with patch.object(p, 'assert_closed'), patch.object(p.mod, 'main') as build:
            with self.assertRaisesRegex(ValueError, 'footer'): p.build('mods', self.config, self.store)
            build.assert_not_called()
        p.adopt(self.source, self.destination, self.store)
        def changed_during_build(argv):
            self.destination.write_bytes(dsv(b'changed progress')); return 0
        with patch.object(p, 'assert_closed'), patch.object(p.mod, 'main', side_effect=changed_during_build):
            with self.assertRaisesRegex(ValueError, 'changed during build'): p.build('mods', self.config, self.store)
        self.assertEqual(self.rom.read_bytes(), b'earlier rom')

    def test_launcher_uses_same_rom_and_backs_up_progress(self):
        exe = self.root/'DeSmuME.exe'; exe.write_bytes(b'placeholder')
        p.configure(self.battery, self.config, exe)
        p.adopt(self.source, self.destination, self.store); self.rom.write_bytes(b'placeholder')
        for preset in ('current', 'jit-preview', 'renderer-preview'):
            with self.subTest(preset=preset):
                with patch.object(p, 'assert_closed'), patch.object(p.w, 'validate_rom'), patch.object(p.subprocess, 'Popen') as launch:
                    self.assertEqual(p.launch(self.config, self.store, preset), 0)
                launch.assert_called_once_with([str(exe.resolve()), *p.LAUNCH_PRESETS[preset], str(self.rom)],
                                              cwd=str(exe.parent))
        self.assertEqual(self.destination.read_bytes(), self.source.read_bytes())
        self.assertEqual(len(list(self.store.glob('before-play-*'))), 1)

    def test_bad_paths_configuration_and_corrupt_backup_fail_closed(self):
        for directory in ('relative', self.root/'missing'):
            with self.assertRaises(ValueError): p.configure(directory, self.config)
        other = self.root / 'raw.sav'; other.write_bytes(b'raw')
        with self.assertRaisesRegex(ValueError, 'no format conversion'):
            p.adopt(other, self.destination, self.store)
        name = p.preserve(self.source, 'adopt', self.store)
        (self.store/name/'save.dsv').write_bytes(b'corrupt')
        with self.assertRaises(ValueError): p.adopt(self.source, self.destination, self.store)
        self.assertFalse(self.destination.exists())
        self.config.write_text(json.dumps({'schema_version':99}))
        with self.assertRaises(ValueError): p.current_save(self.config)
        self.config.write_text(json.dumps({'schema_version':1,'battery_directory':None}))
        with self.assertRaises(ValueError): p.current_save(self.config)


if __name__ == '__main__':
    unittest.main()
