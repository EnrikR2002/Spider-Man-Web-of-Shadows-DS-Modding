import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from tools import playtest as p
from tools import save_backups as saves
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
        with patch.object(p, 'assert_closed'), patch.object(p.w, 'validate_rom'), patch.object(p.subprocess, 'Popen') as launch:
            self.assertEqual(p.launch(self.config, self.store), 0)
        launch.assert_called_once_with([str(exe.resolve()), str(self.rom)], cwd=str(exe.parent))
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
