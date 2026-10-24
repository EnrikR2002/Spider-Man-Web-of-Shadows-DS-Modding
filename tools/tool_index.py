"""List every tools/ module with its one-line purpose, grouped by feature family.

A family is the longest other module name that prefixes this one (for example
midnight_reliability_lab belongs to midnight_reliability). Pass a word to filter
by module name or purpose. Read a tool's --help before running it.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parent


def summaries(folder=TOOLS):
    """Map module stem -> first docstring line (empty when absent)."""
    result = {}
    for path in sorted(folder.glob('*.py')):
        try:
            doc = ast.get_docstring(ast.parse(path.read_text(encoding='utf-8'))) or ''
        except SyntaxError:
            doc = ''
        result[path.stem] = doc.strip().splitlines()[0] if doc.strip() else ''
    return result


def families(stems):
    """Group stems under the longest other stem that prefixes them with '_'."""
    groups = {}
    for stem in sorted(stems):
        parents = [other for other in stems if other != stem and stem.startswith(other + '_')]
        groups.setdefault(max(parents, key=len) if parents else stem, []).append(stem)
    merged = {}
    for root in sorted(groups):
        top = root
        while True:
            parents = [other for other in groups if other != top and top.startswith(other + '_')]
            if not parents:
                break
            top = max(parents, key=len)
        merged.setdefault(top, []).extend(groups[root])
    return {root: sorted(set(members)) for root, members in merged.items()}


def render(query='', folder=TOOLS):
    docs = summaries(folder)
    lines = []
    for root, members in families(list(docs)).items():
        shown = [m for m in members if not query or query.casefold() in (m + ' ' + docs[m]).casefold()]
        if not shown:
            continue
        lines.append(f'{root}:' if len(members) > 1 else '')
        for member in shown:
            indent = '  ' if len(members) > 1 else ''
            lines.append(f'{indent}{member}.py - {docs[member] or "(no docstring)"}')
    return '\n'.join(line for line in lines if line)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('query', nargs='?', default='', help='Filter by name or purpose')
    args = parser.parse_args(argv)
    print(render(args.query))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
