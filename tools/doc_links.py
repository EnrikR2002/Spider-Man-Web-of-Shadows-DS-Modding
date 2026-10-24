"""Check relative Markdown links and #anchors in the project documents.

Anchors follow GitHub's heading slugs: lower case, punctuation other than
hyphens/underscores dropped, spaces become hyphens, repeats get -1, -2 ...
External http(s)/mailto links are not fetched. Code spans and fenced code are
ignored. Exit status 1 lists every broken link.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ('AGENTS.md', 'README.md', 'mods/README.md', 'docs/TASKS.md', 'docs/DEVELOPMENT.md',
             'docs/TECHNICAL.md', 'docs/OG_GAMEPLAY.md', 'docs/CHANGES.md', 'docs/ROADMAP.md')
LINK = re.compile(r'(?<!!)\[[^\]]*\]\(([^)\s]+)\)')


def prose_lines(text):
    """Yield (line number, line) outside fenced code, with code spans removed."""
    fenced = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith('```'):
            fenced = not fenced
            continue
        if not fenced:
            yield number, re.sub(r'`[^`]*`', '', line)


def slug(heading):
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', heading.strip())
    return re.sub(r'[^\w\- ]', '', text.lower()).replace(' ', '-')


def anchors(text):
    seen, result = {}, set()
    for _, line in prose_lines(text):
        match = re.match(r'#{1,6}\s+(.*?)\s*#*\s*$', line)
        if match:
            base = slug(match.group(1))
            count = seen.get(base, 0)
            seen[base] = count + 1
            result.add(base if count == 0 else f'{base}-{count}')
    return result


def broken_links(documents=DOCUMENTS, root=ROOT):
    """Return 'file:line: target (reason)' for each unresolved local link."""
    problems, cache = [], {}
    for name in documents:
        source = root / name
        text = source.read_text(encoding='utf-8')
        for number, line in prose_lines(text):
            for target in LINK.findall(line):
                if re.match(r'[a-z][a-z0-9+.-]*:', target):
                    continue
                path_part, _, anchor = target.partition('#')
                path = (source.parent / path_part).resolve() if path_part else source
                if not path.exists():
                    problems.append(f'{name}:{number}: {target} (missing file)')
                    continue
                if anchor and path.suffix == '.md':
                    if path not in cache:
                        cache[path] = anchors(path.read_text(encoding='utf-8'))
                    if anchor not in cache[path]:
                        problems.append(f'{name}:{number}: {target} (missing anchor)')
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args(argv)
    problems = broken_links()
    for problem in problems:
        print(problem)
    print(f'{len(problems)} broken local links' if problems else 'All local links and anchors resolve')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
