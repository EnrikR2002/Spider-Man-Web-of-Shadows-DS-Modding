#!/usr/bin/env python3
"""Deterministic differential survey of confirmed envelopes and unknown fields.

The report contains metadata, hashes and associations, never decoded asset data.
Use --decoded work/decoded to write supported decompressed assets privately.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mod
from tools import custom_formats as cf
from tools import grip_compression as gc
from tools import wos_tool as w


def survey(glob, manifest, decoded_dir=None):
    names = [e['name'] for e in manifest['entries']]
    by_name = {e['name']: glob[e['offset']:e['offset'] + e['size']] for e in manifest['entries']}
    report = {'source_rom_sha256': mod.CLEAN_SHA256, 'source_glob_sha256': manifest['sha256'],
              'xbd': [], 'gab': [], 'gmb': [], 'sca': [], 'rooms': [], 'graphics_2lz': [],
              'other_formats': {}, 'move_triplets': []}
    kinds, tag_exts, codecs, gab_padding = Counter(), Counter(), Counter(), Counter()
    paired, matches, exceptions = 0, 0, []
    for name, data in by_name.items():
        ext = Path(name).suffix
        if ext == '.xbd':
            parsed = cf.Xbd.parse(data, names); kinds[f'0x{parsed.kind:08x}'] += 1
            row = {'name': name, 'size': len(data), 'kind': f'0x{parsed.kind:08x}',
                   'unknown_u16_08': parsed.unknown_u16_08, 'unknown_u16_0a': parsed.unknown_u16_0a,
                   'opaque_tail_start': parsed.opaque_tail_start, 'bindings': parsed.bindings}
            report['xbd'].append(row)
            for b in parsed.bindings: tag_exts[f'{b["tag"]}:{Path(b["name"]).suffix}'] += 1
        elif ext == '.gab':
            parsed = cf.Gab.parse(data); gab_padding[str(parsed.padding_size)] += 1
            report['gab'].append({'name': name, 'size': len(data), 'terminator_offset': parsed.terminator_offset,
                                  'padding_size': parsed.padding_size, 'sha256': w.sha256(data)})
        elif ext in ('.gmb', '.2lz'):
            row = {'name': name, 'stored_size': len(data), 'type_byte': data[0]}
            if data[0] in (0x10, 0x60):
                decoded = gc.decode(data); codecs[f'{ext}:0x{data[0]:02x}'] += 1
                row.update(decoded_size=len(decoded), decoded_sha256=w.sha256(decoded))
                if decoded_dir is not None: w.atomic_write(decoded_dir / name, decoded)
                if ext == '.gmb':
                    row.update(unknown_u16_00=w.u16(decoded, 0), unknown_u16_02=w.u16(decoded, 2))
                    if name[:-4] + '.sca' in by_name:
                        sca = by_name[name[:-4] + '.sca']; paired += 1
                        match = w.u16(decoded, 2) == w.u32(sca, 4); matches += match
                        if not match: exceptions.append(name)
            else: row['status'] = 'unknown wrapper; no automatic decoding'; codecs[f'{ext}:unknown_0x{data[0]:02x}'] += 1
            report['gmb' if ext == '.gmb' else 'graphics_2lz'].append(row)
        elif ext == '.sca':
            report['sca'].append({'name': name, 'size': len(data), 'magic': data[:4].decode('ascii'),
                                  'unknown_u32_04': w.u32(data, 4), 'unknown_u32_08': w.u32(data, 8),
                                  'unknown_u32_0c': w.u32(data, 12), 'unknown_u32_10': w.u32(data, 16)})
        elif ext == '.bsp':
            parsed = cf.Bsp.parse(data); obj_name = name[:-4] + '_app.obj'
            obj = by_name.get(obj_name)
            report['rooms'].append({'name': name, 'size': len(data), 'table_end': parsed.table_end,
                                    'region_offsets': parsed.region_offsets,
                                    'obj_name': obj_name, 'obj_size': len(obj) if obj else None,
                                    'obj_unknown_u32_00': w.u32(obj, 0) if obj else None,
                                    'obj_unknown_u32_04': w.u32(obj, 4) if obj else None,
                                    'obj_unknown_u32_08': w.u32(obj, 8) if obj else None,
                                    'bsp_sha256': w.sha256(data), 'obj_sha256': w.sha256(obj) if obj else None})
        elif ext in ('.strings', '.font', '.dat', '.pal', '.cbmp', '.obj'):
            report['other_formats'].setdefault(ext, []).append({'name': name, 'size': len(data), 'sha256': w.sha256(data)})
    for name, data in by_name.items():
        if name.startswith('spd_GroundAttack') and name.endswith('.gab'):
            stem = name[:-4]; row = {'stem': stem, 'gab_unknown_first_words': list(cf.Gab.parse(data).words[:6])}
            for ext in ('.gab', '.gmb', '.sca'):
                b = by_name.get(stem + ext)
                row[ext[1:]] = {'present': b is not None, 'size': len(b), 'sha256': w.sha256(b)} if b is not None else {'present': False}
            report['move_triplets'].append(row)
    report['summary'] = {'xbd_kind_counts': dict(kinds), 'actor_binding_tag_extensions': dict(tag_exts),
                         'compression_counts': dict(codecs), 'gab_padding_counts': dict(gab_padding),
                         'gmb_sca_paired_count': paired, 'gmb_u16_02_matches_sca_u32_04': matches,
                         'gmb_sca_counter_exceptions': exceptions}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--out', default='reference/format_survey.json')
    parser.add_argument('--decoded', help='Optional private decompression output directory')
    args = parser.parse_args()
    try:
        _, glob, manifest = mod.load_clean()
        report = survey(glob, manifest, mod.project_path(args.decoded) if args.decoded else None)
        w.write_json(mod.project_path(args.out), report)
        print(json.dumps(report['summary'], indent=2)); print(f'Survey -> {args.out}')
    except (OSError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr); return 1
    return 0


if __name__ == '__main__': raise SystemExit(main())
