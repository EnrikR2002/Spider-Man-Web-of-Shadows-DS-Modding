"""Read one historical project note without loading the entire documentation archive."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
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
    args = parser.parse_args(argv)
    try:
        index, archive = load_index()
        if args.command == 'verify':
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
                print(f'Historical snapshot 2026-10-05: {entry["path"]}; current status: docs/TASKS.md')
                for number, line in selected:
                    print(f'{number}: {line}')
                if truncated:
                    print(f'More in this section/note; resume with --start {selected[-1][0] + 1}')
    except (KeyError, ValueError, OSError, zipfile.BadZipFile) as exc:
        parser.exit(1, f'{exc}\n')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
