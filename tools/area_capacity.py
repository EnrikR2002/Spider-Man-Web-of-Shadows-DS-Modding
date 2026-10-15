"""Read-only room-table and flag budget audit for future campaign branches.

Use --rom and --build-report for one exact published build. Hypothetical room
tables are packed in this process only; no ROM, save, source or overlay changes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import mod
from tools import midnight_chapter as ch, tasm_kit as kit, wos_tool as w


def unused_flags(local_flags, room_flags, visited_flags, pool=ch.FREE_FLAGS):
    """Do not infer unused storage outside the previously audited flag pool."""
    used = set(local_flags) | set(room_flags) | set(visited_flags)
    return sorted(set(pool) - used)


def validate_proposal(rooms, milestones, available, *, visit_overrides=None):
    """Check planning allocations; optional new mappings are not engine patches."""
    overrides = {int(index): value for index, value in (visit_overrides or {}).items()}
    if any(index <= max(r.index for r in ch.ROOMS) for index in overrides):
        raise ValueError('A proposed mapping cannot alter an existing room visit')
    indices = [r['room'] for r in rooms]
    flags = [r['visited_flag'] for r in rooms] + list(milestones.values())
    if len(indices) != len(set(indices)):
        raise ValueError('Duplicate proposed room index')
    if len(flags) != len(set(flags)):
        raise ValueError('Proposed persistent flags overlap')
    if set(flags) - set(available):
        raise ValueError('Proposal uses an occupied or unaudited flag')
    for room in rooms:
        if room['room'] <= max(r.index for r in ch.ROOMS):
            raise ValueError('Proposal reuses an existing room')
        expected = overrides.get(room['room'])
        if expected is None:
            expected = ch.visited(room['room'])
        if room['visited_flag'] != expected:
            raise ValueError('Proposal disagrees with the current visited allocator')
    return {'room_count': len(rooms), 'flag_count': len(flags),
            'requires_visited_mapper_change': bool(overrides),
            'remaining_flags': sorted(set(available) - set(flags))}


def audit(rom_path, report_path, room_counts=(1, 3, 6, 9)):
    rom_path, report_path = Path(rom_path), Path(report_path)
    rom = rom_path.read_bytes()
    digest = w.sha256(rom)
    build = json.loads(report_path.read_text(encoding='utf-8'))
    if build['output_rom_sha256'] != digest:
        raise ValueError('Build report does not identify this exact ROM')
    chapter = build['midnight_line']
    from tools import midnight_boss
    adapter_tail = (midnight_boss.ADAPTER_SPACE if chapter['resources']['ML_SignalCore'].get('core_model') is not None else 0x100) + 0x80
    header = w.parse_header(rom)
    live = rom[header['arm9_offset']:header['arm9_offset'] + header['arm9_size']]
    fs = next(e for e in w.validate_rom(rom, target=True)['nitrofs'] if e['name'] == 'Glob.bin')
    _, names, _ = w.parse_glob(rom[fs['start']:fs['end']])
    clean, _, _ = mod.load_clean()
    h = w.parse_header(clean)
    original = clean[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']]
    image_offset = lambda address: kit.SOURCE + address - kit.TARGET
    list_at = struct.unpack_from('<I', live, ch.AREA_ROWS - ch.BASE + ch.MAP_AREA * 16 + 8)[0]
    listing = live[image_offset(list_at):image_offset(list_at) + chapter['map']['entries'] * ch.ENTRY_SIZE]
    first_string = min(v['string'] for v in chapter['messages'].values())
    with patch.object(ch, 'map_entries', return_value=listing):
        table, _, msgs, _ = ch.room_table(original, names, chapter['resources'], first_string)
    published = live[image_offset(ch.ML_BASE):image_offset(ch.ML_BASE) + ch.ML_SPACE]
    if published != table:
        raise ValueError('Current source does not reproduce the published room table')
    stub, _ = ch.visited_stub(msgs + len(ch.LINES) * ch.MESSAGE_SIZE)
    current_bytes = msgs - ch.ML_BASE + len(ch.LINES) * ch.MESSAGE_SIZE + len(stub)
    trials = []
    for count in room_counts:
        if type(count) is not int or count < 1:
            raise ValueError('Hypothetical room count must be positive')
        start = max(r.index for r in ch.ROOMS) + 1
        extra = tuple(ch.Room(start + i, f'AR_Probe{i:02}', 'Test_Surfaces01', 'authored', False) for i in range(count))
        resources = {**chapter['resources'], **{r.name: chapter['resources']['ML_ServiceBay'] for r in extra}}
        for reserve in (ch.ML_SPACE, ch.ML_SPACE + 0x1000):
            with patch.object(ch, 'ROOMS', ch.ROOMS + extra), patch.object(ch, 'ML_SPACE', reserve), \
                    patch.object(ch, 'map_entries', return_value=listing + bytes(count * ch.ENTRY_SIZE)):
                try:
                    _, _, msgs, _ = ch.room_table(original, names, resources, first_string)
                    stub, _ = ch.visited_stub(msgs + len(ch.LINES) * ch.MESSAGE_SIZE)
                    end = msgs - ch.ML_BASE + len(ch.LINES) * ch.MESSAGE_SIZE + len(stub)
                    trials.append({'added_rooms': count, 'reservation': reserve, 'packed': True,
                                   'table_bytes': end, 'free_before_roof_adapter': reserve - adapter_tail - end})
                except ValueError as exc:
                    trials.append({'added_rooms': count, 'reservation': reserve, 'packed': False, 'reason': str(exc)})
    available = unused_flags(chapter['local_flags'].values(), ch.ROOM_FLAGS.values(),
                             (ch.visited(r.index) for r in ch.ROOMS))
    if w.sha256(rom_path.read_bytes()) != digest:
        raise ValueError('Source ROM changed during the read-only audit')
    return {'schema_version': 1, 'source_sha256': digest, 'published_table_exact': True,
            'current_table_bytes': current_bytes,
            'current_free_before_roof_adapter': ch.ML_SPACE - adapter_tail - current_bytes,
            'unused_audited_flags': available, 'trials': trials,
            'limits': 'Hypothetical packing, one map-list entry per room, placeholder resource indices. '
                      'New dialogue, relocated parent-area lists, real maps, adapter/heap runtime behavior, '
                      'native save/reload, combat and real-door traversal require separate qualification.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--build-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'work/area-research/capacity-audit.json')
    args = parser.parse_args(argv)
    report = audit(args.rom, args.build_report)
    w.write_json(args.output, report)
    print(json.dumps({'report': str(args.output), 'table_bytes': report['current_table_bytes'],
                      'free_table_bytes': report['current_free_before_roof_adapter'],
                      'available_flags': len(report['unused_audited_flags'])}))


if __name__ == '__main__':
    main()
