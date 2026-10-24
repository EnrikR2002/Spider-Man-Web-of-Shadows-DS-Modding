"""Developer tools that need no ROM: test runner, tool index and link checker."""
import io
from pathlib import Path
import tempfile
import unittest

from tools import doc_links, run_tests, tool_index


class PrivateInputTests(unittest.TestCase):
    def test_missing_private_files_and_modules_are_named(self):
        root = run_tests.ROOT
        self.assertEqual(run_tests.private_reason(
            FileNotFoundError(2, 'missing', str(root / 'original/rom.nds'))), 'original/ file')
        self.assertEqual(run_tests.private_reason(
            FileNotFoundError(2, 'missing', str(root / 'build/v/Versioned.nds'))), 'build/ file')
        self.assertEqual(run_tests.private_reason(ModuleNotFoundError('x', name='keystone')),
                         'keystone module')
        self.assertEqual(run_tests.private_reason(
            ImportError("Failed to import test module\nNo module named 'keystone'")), 'keystone module')
        wrapped = ValueError('wrapped')
        wrapped.__cause__ = FileNotFoundError(2, 'missing', str(root / 'work/glob/spdB.nsbmd'))
        self.assertEqual(run_tests.private_reason(wrapped), 'work/ file')

    def test_real_errors_stay_errors(self):
        self.assertIsNone(run_tests.private_reason(ValueError('bug')))
        self.assertIsNone(run_tests.private_reason(ModuleNotFoundError('x', name='tools.missing')))
        self.assertIsNone(run_tests.private_reason(
            FileNotFoundError(2, 'missing', str(run_tests.ROOT / 'tools/missing.py'))))

    def test_relaxed_run_skips_private_inputs_and_strict_counts_them(self):
        missing = str(run_tests.ROOT / 'original/not-here.nds')

        class Sample(unittest.TestCase):
            def test_private(self):
                open(missing, 'rb')

            def test_real(self):
                raise ValueError('real bug')

        def outcome(relaxed):
            result_class = type('R', (run_tests.PrivateAwareResult,), {'relaxed': relaxed})
            result = result_class(io.StringIO(), True, 0)
            unittest.defaultTestLoader.loadTestsFromTestCase(Sample).run(result)
            return len(result.errors), len(result.skipped), dict(result.private)

        self.assertEqual(outcome(True), (1, 1, {'original/ file': 1}))
        self.assertEqual(outcome(False), (2, 0, {}))


class ToolIndexTests(unittest.TestCase):
    def test_families_group_helpers_under_their_generator(self):
        groups = tool_index.families(['vortex_forge', 'vortex_forge_art', 'vortex_forge_lab',
                                      'midnight_reliability', 'midnight_reliability_lab', 'sca'])
        self.assertEqual(groups['vortex_forge'], ['vortex_forge', 'vortex_forge_art', 'vortex_forge_lab'])
        self.assertEqual(groups['midnight_reliability'], ['midnight_reliability', 'midnight_reliability_lab'])
        self.assertEqual(groups['sca'], ['sca'])

    def test_every_tool_has_a_docstring_summary(self):
        self.assertEqual([name for name, doc in tool_index.summaries().items() if not doc], [])

    def test_filter_matches_purpose(self):
        self.assertIn('doc_archive.py', tool_index.render('archive'))


class DocLinkTests(unittest.TestCase):
    def test_github_style_slugs_and_duplicates(self):
        self.assertEqual(doc_links.slug('SCA / model / textures'), 'sca--model--textures')
        self.assertEqual(doc_links.slug('Hit pipeline (v0.4.0, runtime-probed)'),
                         'hit-pipeline-v040-runtime-probed')
        self.assertEqual(doc_links.anchors('# A\n## A\n```\n# not\n```\n'), {'a', 'a-1'})

    def test_broken_file_and_anchor_are_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'B.md').write_text('# Present\n', encoding='utf-8')
            (root / 'A.md').write_text('[ok](B.md#present) [bad](B.md#absent) [gone](C.md) '
                                       '`[code](C.md)` [web](https://example.com)\n', encoding='utf-8')
            self.assertEqual(doc_links.broken_links(('A.md',), root),
                             ['A.md:1: B.md#absent (missing anchor)', 'A.md:1: C.md (missing file)'])


if __name__ == '__main__':
    unittest.main()
