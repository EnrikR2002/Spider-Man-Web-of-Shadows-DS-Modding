"""Enforce reference/doc_contract.json: the machine-checked documentation rules.

`check` lists every violation (exit 1 when any): the fixed document set, word
limits, required headings/patterns, local links, one current version across
all version sources, CHANGES heading order and frozen published sections,
newest-first feedback log, the 2099 catalog matching the ROADMAP skill table,
and run-together word+number prose. `freeze` records hashes for CHANGES
sections that have none; `--update VERSION` re-freezes a deliberately edited
section (only when the user asked for that edit).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CONTRACT = ROOT / 'reference/doc_contract.json'
VERSION = re.compile(r'v?(\d+\.\d+\.\d+)')


def load(path=CONTRACT):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def read(name, root=ROOT):
    return (root / name).read_text(encoding='utf-8')


def prose(text):
    """Yield (line number, line) outside fenced code, with code spans removed."""
    fenced = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith('```'):
            fenced = not fenced
            continue
        if not fenced:
            yield number, re.sub(r'`[^`]*`', '', line)


def section(text, heading):
    """Lines from `heading` up to the next heading of the same or higher level."""
    lines = text.splitlines()
    level = len(heading) - len(heading.lstrip('#'))
    start = lines.index(heading)
    end = next((i for i in range(start + 1, len(lines))
                if re.match(r'#{1,%d} ' % level, lines[i])), len(lines))
    return lines[start:end]


def changes_sections(text, pattern):
    """Map version -> exact text of each '## vX.Y.Z - date - title' section."""
    lines, result, current = text.splitlines(), {}, None
    for line in lines:
        if line.startswith('## '):
            match = re.match(pattern, line)
            current = '.'.join(match.groups()[:3]) if match else None
            if current:
                result[current] = []
        if current:
            result[current].append(line)
    return {version: '\n'.join(body).rstrip('\n') + '\n' for version, body in result.items()}


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def check_document_set(contract, root=ROOT):
    expected = {doc['path'] for doc in contract['documents']}
    actual = set()
    registered = set()
    common = root / '.git'
    try:
        if common.is_file():
            target = common.read_text(encoding='utf-8').strip()
            if target.startswith('gitdir: '):
                admin = root / target[8:]
                common = (admin / (admin/'commondir').read_text(encoding='utf-8').strip()).resolve()
    except (OSError, ValueError):
        common = root / '.git'
    for pointer in (common / 'worktrees').glob('*/gitdir'):
        try:
            marker = (pointer.parent / pointer.read_text(encoding='utf-8').strip()).resolve()
            target = marker.read_text(encoding='utf-8').strip()
            if target.startswith('gitdir: ') and (marker.parent / target[8:]).resolve() == pointer.parent.resolve():
                registered.add(marker.parent)
        except (OSError, ValueError):
            continue
    for directory, children, files in os.walk(root):
        children[:] = [name for name in children if name not in {'.git', '__pycache__'}
                       and not (Path(directory) == root and name in {'work', 'build', 'original'})
                       and (Path(directory) / name).resolve() not in registered]
        actual.update((Path(directory) / name).relative_to(root).as_posix()
                      for name in files if name.lower().endswith('.md'))
    return ([f'{name}: Markdown file outside the contract' for name in sorted(actual - expected)] +
            [f'{name}: contract document is missing' for name in sorted(expected - actual)])


def check_documents(contract, root=ROOT):
    problems = []
    for doc in contract['documents']:
        text = read(doc['path'], root)
        lines = text.splitlines()
        if 'max_words' in doc and len(text.split()) > doc['max_words']:
            problems.append(f"{doc['path']}: {len(text.split())} words exceeds {doc['max_words']}")
        for heading in doc.get('required_headings', ()):
            if heading not in lines:
                problems.append(f"{doc['path']}: required heading missing: {heading}")
        for pattern in doc.get('required_patterns', ()):
            if not any(re.search(pattern, line) for line in lines):
                problems.append(f"{doc['path']}: required text missing: /{pattern}/")
    return problems


def check_links(contract, root=ROOT):
    from tools import doc_links
    return doc_links.broken_links(tuple(doc['path'] for doc in contract['documents']), root)


def current_versions(contract, root=ROOT):
    """Return {source: version} for every version source the contract names."""
    found = {}
    profile = json.loads(read('reference/gameplay_profile.json', root))
    found['gameplay_profile'] = profile.get('release_version')
    releases = json.loads(read('reference/releases.json', root))['releases']
    found['releases.json'] = releases[-1]['version'] if releases else None
    changes = changes_sections(read('docs/CHANGES.md', root), contract['changes_heading_pattern'])
    found['CHANGES'] = next(iter(changes), None)
    match = re.search(r'Current release: \*\*v(\d+\.\d+\.\d+)\*\*', read('README.md', root))
    found['README'] = match.group(1) if match else None
    tasks = read('docs/TASKS.md', root)
    published = '\n'.join(section(tasks, '## Published build')) if '## Published build' in tasks.splitlines() else ''
    match = re.search(r'\*\*v(\d+\.\d+\.\d+)\*\*', published)
    found['TASKS'] = match.group(1) if match else None
    return found


def check_versions(contract, root=ROOT):
    found = current_versions(contract, root)
    if len(set(found.values())) == 1 and None not in found.values():
        return []
    return ['current version disagrees: ' + ', '.join(f'{k}={v}' for k, v in found.items())]


def check_changes(contract, root=ROOT):
    text = read('docs/CHANGES.md', root)
    pattern = contract['changes_heading_pattern']
    problems, previous = [], None
    for _, line in prose(text):
        if line.startswith('## v') and not re.match(pattern, line):
            problems.append(f'docs/CHANGES.md: malformed version heading: {line}')
        match = re.match(pattern, line)
        if match:
            key = (tuple(int(part) for part in match.groups()[:3]), match.group(4))
            if previous and (key[0] >= previous[0] or key[1] > previous[1]):
                problems.append(f'docs/CHANGES.md: {line} is not below the previous release')
            previous = key
    sections = changes_sections(text, pattern)
    frozen = contract.get('frozen_changes_sections', {})
    for version, body in sections.items():
        if version not in frozen:
            problems.append(f'docs/CHANGES.md: v{version} is not frozen (run tools/doc_contract.py freeze)')
        elif frozen[version] != digest(body):
            problems.append(f'docs/CHANGES.md: frozen v{version} section changed')
    problems += [f'docs/CHANGES.md: frozen v{v} section is missing' for v in frozen if v not in sections]
    return problems


def check_feedback_log(contract, root=ROOT):
    text = read('docs/ROADMAP.md', root)
    heading = contract['feedback_log_heading']
    if heading not in text.splitlines():
        return [f'docs/ROADMAP.md: {heading} missing']
    problems, previous, undated = [], None, False
    for line in section(text, heading):
        if not line.startswith('| ') or line.startswith('| Date') or set(line) <= set('|- '):
            continue
        match = re.match(r'\| (\d{4}-\d{2}-\d{2})', line)
        if not match:
            undated = True
            continue
        if undated or (previous and match.group(1) > previous):
            problems.append(f'docs/ROADMAP.md: feedback log not newest first at {match.group(1)}')
        previous = match.group(1)
    return problems


def check_suit_catalog(contract, root=ROOT):
    spec = contract['suit_catalog']
    catalog = json.loads(read(spec['path'], root))
    suit = next(s for s in catalog['suits'] if s['id'] == spec['suit_id'])
    design = suit['combat_design']
    rows = design['new_rows']
    problems = []
    bits = [row['ability_bit'] for row in rows]
    low, high = spec['free_bits']
    if len(set(bits)) != len(bits):
        problems.append(f"{spec['path']}: duplicate new-row ability bits")
    for row in rows:
        bit = row['ability_bit']
        if not low <= bit <= high or bit in spec['used_bits']:
            problems.append(f"{spec['path']}: {row['move']} bit {bit} is not a free saved bit")
        if row['event_id'] != spec['event_offset'] + bit:
            problems.append(f"{spec['path']}: {row['move']} event {row['event_id']} != {spec['event_offset']}+bit")
    if design.get('skill_count') != spec['native_row_count'] + len(rows):
        problems.append(f"{spec['path']}: skill_count != native rows + new rows")
    text = '\n'.join(section(read('docs/ROADMAP.md', root), spec['roadmap_section']))
    table_new = {int(bit): name.strip() for bit, name in re.findall(r'^\| \d+ \| New \((\d+)\) \| ([^|]+)\|', text, re.M)}
    table_native = {name.strip(): move.strip() for name, move in
                    re.findall(r'^\| \d+ \| ([A-Za-z -]+?) \(\d+\) \| ([^|]+)\|', text, re.M)
                    if name.strip() != 'New'}
    if table_new != {row['ability_bit']: row['move'] for row in rows}:
        problems.append(f"ROADMAP skill table new rows differ from {spec['path']}: {table_new}")
    if table_native != design['native_rows']:
        problems.append(f"ROADMAP skill table native rows differ from {spec['path']}: {table_native}")
    return problems


def check_spacing(contract, root=ROOT):
    pattern = re.compile(contract['spacing_pattern'])
    problems = []
    for doc in contract['documents']:
        for number, line in prose(read(doc['path'], root)):
            problems += [f"{doc['path']}:{number}: run-together '{match.group(0)}'"
                         for match in pattern.finditer(line)]
    return problems


CHECKS = (check_document_set, check_documents, check_links, check_versions, check_changes,
          check_feedback_log, check_suit_catalog, check_spacing)


def check(contract=None, root=ROOT):
    contract = contract or load()
    return [problem for rule in CHECKS for problem in rule(contract, root)]


def freeze(update=(), path=CONTRACT, root=ROOT):
    """Hash unfrozen CHANGES sections; re-hash only the versions named in update."""
    contract = load(path)
    sections = changes_sections(read('docs/CHANGES.md', root), contract['changes_heading_pattern'])
    frozen = contract.setdefault('frozen_changes_sections', {})
    changed = []
    for version, body in sections.items():
        if version not in frozen or version in update:
            if frozen.get(version) != digest(body):
                changed.append(version)
            frozen[version] = digest(body)
    unknown = set(update) - set(sections)
    if unknown:
        raise ValueError(f'No CHANGES section for {sorted(unknown)}')
    contract['frozen_changes_sections'] = dict(sorted(
        frozen.items(), key=lambda item: tuple(int(p) for p in item[0].split('.')), reverse=True))
    Path(path).write_text(json.dumps(contract, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return changed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('check', help='List every documentation-contract violation')
    freezing = commands.add_parser('freeze', help='Freeze new CHANGES sections')
    freezing.add_argument('--update', nargs='*', default=(), metavar='VERSION',
                          help='Re-freeze these deliberately edited versions, e.g. 0.31.0')
    args = parser.parse_args(argv)
    if args.command == 'freeze':
        changed = freeze(tuple(VERSION.fullmatch(v).group(1) for v in args.update))
        print(f'Froze {len(changed)} CHANGES sections' + (f': {", ".join(changed)}' if changed else ''))
        return 0
    problems = check()
    for problem in problems:
        print(problem)
    print(f'{len(problems)} documentation-contract problems' if problems else 'Documentation contract holds')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
