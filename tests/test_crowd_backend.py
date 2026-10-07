"""Own-code staging must reproduce the published kit and protect native branches."""
from pathlib import Path
import tempfile
import unittest
import json
from tools import crowd_backend as b, crowd_area_lab as a, tasm_kit as kit


class CrowdBackendTests(unittest.TestCase):
    def test_unknown_or_changed_source_fails_closed(self):
        for variant in b.VARIANTS:
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                b.candidate_source('', variant)
        with self.assertRaises(ValueError):
            b.candidate_source('', 'unreviewed')

    def test_isolated_candidates_validate_without_changing_published_files(self):
        source_path = b.ROOT / 'tools/tasm_kit.s'
        hex_path = source_path.with_suffix('.hex')
        before = (source_path.read_bytes(), hex_path.read_bytes())
        try:
            for variant in b.VARIANTS:
                with self.subTest(variant=variant), tempfile.TemporaryDirectory() as directory:
                    out, report = b.stage(variant, Path(directory))
                    self.assertEqual(report['published_code_sha256'], kit.CODE_SHA256)
                    self.assertLessEqual(report['candidate_bytes'], kit.ROUTE_OFFSET)
                    self.assertTrue((out / 'patch.json').is_file())
                    if variant == 'area':
                        patch = json.loads(a.invocation_patch(out).read_text())
                        harness = next(p for p in patch if p['addr'] == a.HARNESS)
                        self.assertLessEqual(a.HARNESS + len(bytes.fromhex(harness['hex'])), a.CONFIG)
                        hook = next(p for p in patch if p['addr'] == kit.KIT_BASE + 0x14)
                        candidate = bytes.fromhex((out / 'candidate.hex').read_text())
                        self.assertEqual(bytes.fromhex(hook['expect']), candidate[0x14:0x18])
        except ModuleNotFoundError as exc:
            if exc.name == 'keystone':
                self.skipTest('Optional assembler research dependency unavailable')
            raise
        self.assertEqual((source_path.read_bytes(), hex_path.read_bytes()), before)

    def test_invocation_rejects_missing_or_ambiguous_helper(self):
        for code in (b'', bytes.fromhex('01000000') * 2):
            with self.subTest(code=code), self.assertRaises(ValueError):
                a.unique_signature(code, (1,))

    def test_sky_coverage_requires_a_connecting_control_and_preserves_cancel_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            cases = {}
            for name in ('open', 'wall', 'cancel'):
                cases[name] = {}
                for mode in ('control', 'candidate'):
                    evidence = out / (name + '-' + mode)
                    evidence.mkdir()
                    rows = [{'f': f, 'st': state, 'pos': [950000, 20000], 'vel': [velocity, 0],
                             'probe': [latch, 0, 0, 0], 'en': [[65536 - loss, [960000, 20000], 0, 99]]}
                            for f, state, velocity, latch, loss in
                            ((0, 19, 0, 1, 0), (93, 52, -1000, 1, 6 * 4096), (219, 0, 0, 0, 6 * 4096))]
                    (evidence / 'observations.json').write_text(json.dumps(rows))
                    cases[name][mode] = {'evidence': str(evidence), 'armed': name == 'wall'}
            (out / 'sky-coverage.json').write_text(json.dumps({'cases': cases}))
            self.assertTrue(b.summarize_sky(out)['passed'])
            control = Path(cases['open']['control']['evidence']) / 'observations.json'
            rows = json.loads(control.read_text())
            for row in rows: row['en'][0][0] = 65536 - 3072
            control.write_text(json.dumps(rows))
            self.assertFalse(b.summarize_sky(out)['checks']['open_control_hits_connect'])


if __name__ == '__main__':
    unittest.main()
