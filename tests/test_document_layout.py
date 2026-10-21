"""Keep the approved document roles and bound routine startup reading."""
from pathlib import Path
import os
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DocumentLayoutTests(unittest.TestCase):
    def test_fixed_core_document_set(self):
        expected = {'AGENTS.md', 'README.md', 'mods/README.md', 'docs/TASKS.md',
                    'docs/TECHNICAL.md', 'docs/OG_GAMEPLAY.md', 'docs/CHANGES.md',
                    'docs/TASM_ROADMAP.md', 'docs/DEVELOPMENT.md'}
        actual = set()
        for directory, children, files in os.walk(ROOT):
            children[:] = [name for name in children if name not in {'.git', '__pycache__'}
                           and not (Path(directory) == ROOT and name in {'work', 'build', 'original'})]
            actual.update((Path(directory) / name).relative_to(ROOT).as_posix()
                          for name in files if name.lower().endswith('.md'))
        self.assertEqual(actual, expected)

    def test_startup_documents_remain_small(self):
        for name in ('AGENTS.md', 'docs/TASKS.md'):
            with self.subTest(name=name):
                self.assertLessEqual(len((ROOT / name).read_text(encoding='utf-8').split()), 900)


if __name__ == '__main__':
    unittest.main()
