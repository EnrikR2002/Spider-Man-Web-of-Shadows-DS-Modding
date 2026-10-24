"""Run the unit tests; on a fresh clone, count missing private inputs as skips.

A fresh clone or cloud workspace has no clean ROM, no local build/ or work/
outputs and no pinned ARM assembler (Keystone under work/research-libs). Tests
that need them error with FileNotFoundError or ImportError. While the clean ROM
is absent this runner reports exactly those errors as "private input missing"
skips and fails only on real errors. With the ROM present (a full local setup),
or with --strict, every error counts.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROM = ROOT / 'original/Spider-Man - Web of Shadows (USA) (En,Fr).nds'
PRIVATE_DIRS = ('original', 'build', 'work', 'mods')
PRIVATE_MODULES = ('keystone', 'numpy', 'PIL')


def private_reason(exc):
    """Name the private input behind an error, or None for a real failure."""
    seen = 0
    while exc is not None and seen < 8:
        if isinstance(exc, FileNotFoundError) and exc.filename:
            path = Path(exc.filename)
            path = (path if path.is_absolute() else Path.cwd() / path).resolve()
            for folder in PRIVATE_DIRS:
                if path.is_relative_to(ROOT / folder):
                    return f'{folder}/ file'
        if isinstance(exc, ModuleNotFoundError) and exc.name in PRIVATE_MODULES:
            return f'{exc.name} module'
        if isinstance(exc, ImportError) and not isinstance(exc, ModuleNotFoundError):
            text = str(exc)
            for name in PRIVATE_MODULES:
                if f"No module named '{name}'" in text:
                    return f'{name} module'
            for folder in PRIVATE_DIRS:
                if f"No such file or directory: '{ROOT / folder}" in text:
                    return f'{folder}/ file'
        exc, seen = exc.__cause__ or exc.__context__, seen + 1
    return None


class PrivateAwareResult(unittest.TextTestResult):
    relaxed = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.private = Counter()

    def addError(self, test, err):
        reason = private_reason(err[1]) if self.relaxed else None
        if reason is None:
            super().addError(test, err)
        else:
            self.private[reason] += 1
            self.addSkip(test, f'private input missing: {reason}')

    def addSubTest(self, test, subtest, err):
        reason = None
        if err is not None and self.relaxed and not issubclass(err[0], test.failureException):
            reason = private_reason(err[1])
        if reason is None:
            super().addSubTest(test, subtest, err)
        else:
            self.private[reason] += 1
            self.addSkip(subtest, f'private input missing: {reason}')


def run(names=(), *, strict=None, verbosity=1, stream=None):
    """Run tests and return the result; strict defaults to 'clean ROM present'."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    loader = unittest.defaultTestLoader
    suite = (loader.loadTestsFromNames(names) if names
             else loader.discover(str(ROOT / 'tests')))
    strict = CLEAN_ROM.exists() if strict is None else strict
    result_class = type('Result', (PrivateAwareResult,), {'relaxed': not strict})
    runner = unittest.TextTestRunner(stream=stream or sys.stderr, verbosity=verbosity,
                                     resultclass=result_class)
    return runner.run(suite)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('names', nargs='*', help='Optional test names, e.g. tests.test_doc_archive')
    parser.add_argument('--strict', action='store_true', help='Count missing private inputs as errors')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args(argv)
    result = run(args.names, strict=True if args.strict else None, verbosity=2 if args.verbose else 1)
    if result.private:
        detail = ', '.join(f'{count} {reason}' for reason, count in sorted(result.private.items()))
        print(f'Private inputs missing (counted as skips): {detail}. '
              'A full local setup or --strict counts them as errors.')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
