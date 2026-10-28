"""Read, verify or append historical project notes without loading the whole documentation archive."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import wos_tool as w

INDEX = ROOT / 'docs/archive/index.json'


def load_index(path=INDEX):
    path = Path(path)
    index = json.loads(path.read_text(encoding='utf-8'))
    archive = path.with_name('legacy-notes.zip')
    if index['schema_version'] != 1:
        raise ValueError('Unsupported documentation archive schema')
    if hashlib.sha256(archive.read_bytes()).hexdigest() != index['archive_sha256']:
        raise ValueError('Documentation archive hash mismatch')
    return index, archive


def resolve_entry(entries, name):
    name = name.replace('\\', '/').casefold()
    matches = [entry for entry in entries if entry['path'].casefold() == name
               or Path(entry['path']).name.casefold() == name]
    if len(matches) != 1:
        raise ValueError(f'Expected one archived note for {name!r}; found {len(matches)}')
    return matches[0]


def read_entry(archive, entry):
    with zipfile.ZipFile(archive) as source:
        raw = source.read(entry['path'])
    if len(raw) != entry['bytes'] or hashlib.sha256(raw).hexdigest() != entry['sha256']:
        raise ValueError(f'Archived note hash mismatch: {entry["path"]}')
    return raw.decode('utf-8')


def select_lines(body, *, section=None, start=None, count=80):
    lines = body.splitlines()
    lower, upper = 1, len(lines) + 1
    if section:
        matches = [(i, line) for i, line in enumerate(lines, 1)
                   if line.startswith('#') and section.casefold() in line.lstrip('# ').casefold()]
        if len(matches) != 1:
            raise ValueError(f'Expected one section for {section!r}; found {len(matches)}; use --toc')
        lower, heading = matches[0]
        level = len(heading) - len(heading.lstrip('#'))
        upper = next((i for i in range(lower + 1, len(lines) + 1)
                      if lines[i - 1].startswith('#')
                      and len(lines[i - 1]) - len(lines[i - 1].lstrip('#')) <= level), upper)
    start = lower if start is None else start
    if count < 1 or not lower <= start < upper:
        raise ValueError('Line range must start within the selected note/section and have positive length')
    end = min(upper, start + count)
    return [(i, lines[i - 1]) for i in range(start, end)], end < upper


def verify_archive(index_path=INDEX):
    index, archive = load_index(index_path)
    paths = [entry['path'] for entry in index['entries']]
    with zipfile.ZipFile(archive) as source:
        if len(paths) != len(set(paths)) or sorted(source.namelist()) != sorted(paths):
            raise ValueError('Documentation archive/index entries differ or contain duplicates')
        if source.testzip() is not None:
            raise ValueError('Documentation archive CRC failed')
    for entry in index['entries']:
        read_entry(archive, entry)
    return len(paths)


def note_sections(body):
    """Markdown headings outside fenced code blocks, as the index records them."""
    sections, fenced = [], False
    for number, line in enumerate(body.splitlines(), 1):
        if line.lstrip().startswith('```'):
            fenced = not fenced
        elif not fenced and line.startswith('#'):
            sections.append({'line': number, 'heading': line.lstrip('#').strip(),
                             'level': len(line) - len(line.lstrip('#'))})
    return sections


def add_entry(name, raw, *, title, snapshot_date, source_revision, index_path=INDEX):
    """Append one retired note byte for byte and re-pin the archive hash."""
    index_path = w.safe_output(Path(index_path))
    index, archive = load_index(index_path)
    w.safe_output(archive)
    name = name.replace('\\', '/')
    if any(entry['path'].casefold() == name.casefold() for entry in index['entries']):
        raise ValueError(f'Archive already holds {name!r}; choose a dated name')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', snapshot_date):
        raise ValueError('Snapshot date must be YYYY-MM-DD')
    body = raw.decode('utf-8')
    info = zipfile.ZipInfo(name, date_time=tuple(map(int, snapshot_date.split('-'))) + (0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o600 << 16
    before = {archive: archive.read_bytes(), index_path: index_path.read_bytes()}
    staged = io.BytesIO(before[archive])
    with zipfile.ZipFile(staged, 'a') as target:
        target.writestr(info, raw)
    index['entries'].append({'path': name, 'title': title, 'snapshot_date': snapshot_date,
                             'source_revision': source_revision, 'bytes': len(raw),
                             'words': len(body.split()), 'sha256': hashlib.sha256(raw).hexdigest(),
                             'sections': note_sections(body)})
    archive_bytes = staged.getvalue()
    index['archive_sha256'] = hashlib.sha256(archive_bytes).hexdigest()
    index_bytes = (json.dumps(index, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    recovery = Path(tempfile.mkdtemp(prefix='.archive-recovery-', dir=archive.parent)).resolve()
    if not recovery.is_relative_to(archive.parent.resolve()):
        raise ValueError('Archive recovery directory escaped its parent')
    keep_recovery = False
    try:
        for path, data in before.items(): w.atomic_write(recovery / path.name, data)
        keep_recovery = True
        try:
            w.atomic_write(archive, archive_bytes)
            w.atomic_write(index_path, index_bytes)
            count = verify_archive(index_path)
            keep_recovery = False
            return count
        except BaseException as error:
            failures = []
            for path, data in reversed(tuple(before.items())):
                try:
                    if (path.read_bytes() if path.exists() else None) != data: w.atomic_write(path, data)
                except (OSError, ValueError) as recovery_error:
                    failures.append(f'{path}: {recovery_error}')
            if failures:
                raise OSError(f'Archive update failed; rollback incomplete: {failures}. Backups: {recovery}') from error
            keep_recovery = False
            raise
    finally:
        if not keep_recovery: shutil.rmtree(recovery)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    listing = commands.add_parser('list', help='List archived note titles, optionally filtered')
    listing.add_argument('query', nargs='?', default='')
    reading = commands.add_parser('read', help='Read one note; defaults to at most 80 lines')
    reading.add_argument('name')
    reading.add_argument('--toc', action='store_true', help='Show section names and line numbers only')
    reading.add_argument('--section', help='Unique substring of a section heading')
    reading.add_argument('--start', type=int, help='Absolute source line number')
    reading.add_argument('--lines', type=int, default=80)
    commands.add_parser('verify', help='Check ZIP, index, lengths and all SHA256s')
    adding = commands.add_parser('add', help='Archive a retired file byte for byte before removing it')
    adding.add_argument('name', help='Unique archive name, e.g. docs/OLD_NOTE-2026-10-24.md')
    adding.add_argument('--from', dest='source', type=Path, required=True, help='File to archive')
    adding.add_argument('--title', required=True)
    adding.add_argument('--date', required=True, help='Snapshot date YYYY-MM-DD')
    adding.add_argument('--revision', help='Git revision the bytes come from (default HEAD)')
    args = parser.parse_args(argv)
    try:
        index, archive = load_index()
        if args.command == 'add':
            revision = args.revision or subprocess.run(
                ['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True, capture_output=True,
                text=True).stdout.strip()
            count = add_entry(args.name, args.source.read_bytes(), title=args.title,
                              snapshot_date=args.date, source_revision=revision)
            print(f'Archived {args.name}; {count} archived notes verified')
        elif args.command == 'verify':
            print(f'{verify_archive()} archived notes verified')
        elif args.command == 'list':
            for entry in index['entries']:
                if args.query.casefold() in (entry['path'] + ' ' + entry['title']).casefold():
                    print(f'{entry["path"]}: {entry["title"]}')
        else:
            entry = resolve_entry(index['entries'], args.name)
            body = read_entry(archive, entry)
            if args.toc:
                for section in entry['sections']:
                    print(f'{section["line"]}: {section["heading"]}')
            else:
                selected, truncated = select_lines(body, section=args.section,
                                                   start=args.start, count=args.lines)
                snapshot_date = entry.get('snapshot_date', index['snapshot_date'])
                print(f'Historical snapshot {snapshot_date}: {entry["path"]}; current status: docs/TASKS.md')
                for number, line in selected:
                    print(f'{number}: {line}')
                if truncated:
                    print(f'More in this section/note; resume with --start {selected[-1][0] + 1}')
    except (KeyError, ValueError, OSError, zipfile.BadZipFile, subprocess.SubprocessError) as exc:
        parser.exit(1, f'{exc}\n')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
