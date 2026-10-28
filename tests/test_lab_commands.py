"""Qualification exit codes and fresh copied batteries, without starting an emulator."""
from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import chapter_renewal_lab as renewal, chapter_spectacle_lab as spectacle
from tools import creature_forge_lab as forge, crane_walk as crane, midnight_walk as walk
from tools import midnight_rework_lab as rework, emulator_smoke, wos_tool as w

ROOT = Path(__file__).resolve().parents[1]


class LabCommandTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'work').mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix='lab-command-test-', dir=ROOT/'work')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.rom = self.root/'candidate.nds'; self.rom.write_bytes(b'disposable command fixture')
        self.rom.with_suffix('.build.json').write_text('{}', encoding='utf-8')
        for module in (forge, renewal, crane):
            out = self.root/module.__name__.split('.')[-1]; out.mkdir()
            guard = patch.object(module, 'OUT', out); guard.start(); self.addCleanup(guard.stop)
        guard = patch.object(renewal, 'RUN_TAG', ''); guard.start(); self.addCleanup(guard.stop)

    def test_forge_early_and_regular_commands_return_case_status(self):
        for passed in (False, True):
            report = {'passed': passed}
            with patch.object(forge, 'install'), patch.object(renewal, 'duel', return_value=report), \
                 patch.object(renewal, 'combat', return_value=report), redirect_stdout(io.StringIO()):
                for args in (['duel', '--creature', 'maw'], ['duel', '--creature', 'skitter'], ['boss']):
                    with self.subTest(passed=passed, args=args):
                        self.assertEqual(forge.main([*args, '--rom', str(self.rom)]), 0 if passed else 1)

    def test_forge_duel_batch_returns_failure_when_child_report_fails(self):
        for passed in (False, True):
            for style in forge.d.STYLES[:6]:
                name = ('walk-duel-'+style if style in ('skitter', 'warden', 'eye') else 'duel-'+style+'-proof')
                w.write_json(forge.OUT/(name+'-'+style+'.json'),
                             dict(passed=passed, move_calls=[1]*28, contact_move_calls=[1]*28))
            with patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0)), redirect_stdout(io.StringIO()):
                self.assertEqual(forge.main(['duel-all', '--rom', str(self.rom)]), 0 if passed else 1)

    def test_renewal_duel_batch_keeps_the_report_api_and_failure(self):
        for passed in (False, True):
            for style in forge.d.STYLES[:6]:
                name = 'walk-duel-'+style if style in ('skitter', 'warden', 'eye') else 'duel-'+style+'-proof'
                w.write_json(renewal.OUT/(name+'.json'), dict(passed=passed, attack_sequencer_calls=[3]*7))
            with patch.object(renewal, 'configure_rooms'), \
                 patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0)), redirect_stdout(io.StringIO()):
                report = renewal.main(['duel-all', '--rom', str(self.rom)])
            self.assertEqual(report['passed'], passed)
            self.assertEqual(len(report['creatures']), 6)

    def test_crane_dispatch_returns_the_case_report(self):
        from tools import midnight_line, kit_lab
        cases = (['entry'], ['cross'], ['view'], ['machine'], ['power'], ['map'],
                 ['setpiece', next(iter(crane.SETPIECES))], ['save'])
        for passed in (False, True):
            report = {'passed': passed}
            with patch.object(crane, 'install'), patch.object(crane, 'machine_records', return_value={}), \
                 patch.object(crane, 'run', return_value=report), \
                 patch.object(midnight_line, 'OUT', crane.OUT), \
                 patch.object(midnight_line, 'refuge_save_child', return_value=report), \
                 patch.object(kit_lab, '_run'), redirect_stdout(io.StringIO()):
                for args in cases:
                    with self.subTest(passed=passed, args=args):
                        self.assertIs(crane.main([*args, '--rom', str(self.rom)]), report)

    def test_midnight_dispatch_translates_reports_to_exit_codes(self):
        for passed in (False, True):
            report = dict(passed=passed, route='fixture', finished=passed, checks=[], aborted=None, arrivals=[])
            with patch.object(walk, 'run', return_value=report), patch.object(walk, 'run_child', return_value=report), \
                 patch.object(renewal, 'main', return_value=report), \
                 patch.object(rework, 'main', return_value=report), redirect_stdout(io.StringIO()):
                for command in ('run', '_child'):
                    self.assertEqual(walk.main([command, 'fixture', '--rom', str(self.rom)]), 0 if passed else 1)
                for feature in ('chapter_renewal', 'midnight_rework'):
                    w.write_json(self.rom.with_suffix('.build.json'), {feature: True})
                    self.assertEqual(walk.main(['all', '--rom', str(self.rom)]), 0 if passed else 1)

    def test_real_forge_entry_point_exits_nonzero_for_a_failed_duel(self):
        source = '''import runpy, sys
from unittest.mock import patch
from tools import chapter_renewal_lab
sys.argv = ['tools/creature_forge_lab.py', 'duel', '--rom', 'unused.nds', '--creature', 'maw']
with patch.object(chapter_renewal_lab, 'duel', return_value={'passed': False}):
    runpy.run_path('tools/creature_forge_lab.py', run_name='__main__')
'''
        done = subprocess.run([sys.executable, '-c', source], cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(done.returncode, 1, done.stderr)
        self.assertIn('"passed": false', done.stdout)

    def test_real_renewal_entry_point_returns_manifest_status(self):
        out = self.root/'manifest'; out.mkdir(); (out/'crane').mkdir()
        env = dict(os.environ, WOS_CHAPTER_LAB_OUT=str(out.resolve()))
        for key in ('WOS_CHAPTER_PLAYER_PROFILE', 'WOS_CHAPTER_LAB_SAVE'): env.pop(key, None)
        cmd = [sys.executable, str(Path(renewal.__file__)), 'crane-manifest', '--rom', str(self.rom)]
        failed = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(failed.returncode, 1, failed.stderr)
        digest = w.sha256(self.rom.read_bytes())
        for name, group in [('Pier_Save02', 2), *crane.cr.LINKS]:
            label = 'walk-pier-entry' if name == 'Pier_Save02' else 'walk-cross-'+name+str(group)
            w.write_json(out/'crane'/(label+'-'+digest[:8]+'.json'),
                         dict(passed=True, rom_sha256=digest, rom_unchanged=True, steps=[]))
        passed = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(passed.returncode, 0, passed.stderr)

    def test_spectacle_refreshes_the_copy_after_new_player_progress(self):
        actual, earned = self.root/'actual.dsv', self.root/'earned.sav'
        earned.write_bytes(bytes(512))
        args = ['chapter_spectacle_lab.py', 'arm-continue', '--rom', str(self.rom), '--save', str(earned)]
        with patch.object(spectacle, 'OUT', self.root), \
             patch.object(spectacle.playtest, 'current_save', return_value=actual), \
             patch.object(spectacle.k, 'TRAINING_SAVE'), patch.object(sys, 'argv', args), \
             patch.object(emulator_smoke, 'run', side_effect=RuntimeError('stop before emulator')):
            for progress in (b'first opaque player save', b'new purchases and progress\x00\xff'):
                actual.write_bytes(progress)
                with self.assertRaisesRegex(RuntimeError, 'stop before emulator'): spectacle.main()
                self.assertEqual((self.root/'current-player-copy.dsv').read_bytes(), progress)
                self.assertEqual(actual.read_bytes(), progress)


if __name__ == '__main__':
    unittest.main()
