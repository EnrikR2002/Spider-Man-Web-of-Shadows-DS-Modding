"""Crane Row overview map post-pass: the ring layout of tools/crane_navigation.py.

Replaces the four progress screens and rewrites the area-6 room list in place;
nothing else moves. The map table is found by structure (the area row whose
screen is zz_CraneOverview.cbmp), so the pass chains after any Crane Row build
that kept the published map allocation, and can be the last step of a release.
"""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import wos_tool as w, tasm_kit as kit, spider2099 as assets, midnight_voltage as extension
from tools import crane_navigation as nav, crane_rooms as cr, midnight_chapter as ch

BASE = 0x02000000
ENTRY = 20
MAP_AREA = 6
SAVE_ROOM = cr.NAMES[2]
CHECKPOINT = cr.NAMES[10]


def offset(address):
    return kit.SOURCE+address-kit.TARGET if address >= kit.TARGET else address-BASE


def entries(listing):
    """Area-list rows exactly as crane_row writes them: room, selector 1, save type, slot, colour sources, marker."""
    return b''.join(struct.pack('<2I', cr.IDS[n], 1)+bytes((1 if n == SAVE_ROOM else 0, slot, slot+4))
                    +ch.STATE_COLORS+bytes((x, y, 0, 0, 0)) for n, slot, x, y in listing)


def screens(native):
    """The four progress screens and the one room list they share."""
    out, listing = {}, None
    for stage, name in enumerate(nav.SCREENS):
        raw, rows = nav.overview(native, stage, extra_saves=(CHECKPOINT,))
        if listing is not None and rows != listing:raise ValueError('Progress map slots must stay identical')
        out[name], listing = raw, rows
    return out, listing


def find_table(arm, names):
    """(area row address, entries address, count) of the published Crane map; exactly one must validate."""
    screen = names.index(nav.SCREENS[0])
    end = kit.TARGET+len(arm)-kit.SOURCE
    found = {}
    for at in range(0, len(arm)-3, 4):
        value = w.u32(arm, at)
        if not kit.TARGET <= value < end:continue
        for i in range(6):
            row = value-16*i
            o = offset(row)+16*MAP_AREA
            if row >= kit.TARGET and o+16 <= len(arm) and w.u32(arm, o) == screen:
                table, count = w.u32(arm, o+8), w.u32(arm, o+12)
                if kit.TARGET <= table < end and 0 < count <= 64:found[row] = (table, count)
    if len(found) != 1:raise ValueError('Crane Row map table not found exactly once')
    row, (table, count) = next(iter(found.items()))
    return row, table, count


def apply_rom(rom):
    h = w.parse_header(rom)
    arm = rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    names, blobs = assets.resources(rom)
    before = tuple(blobs)
    import mod
    _, glob, _ = mod.load_clean()
    offsets, native_names, _ = w.parse_glob(glob)
    native = glob[offsets[native_names.index(ch.MAP_SOURCE)]:offsets[native_names.index(ch.MAP_SOURCE)+1]]
    new_screens, listing = screens(native)
    row, table, count = find_table(arm, names)
    payload = entries(listing)
    if len(payload)//ENTRY > count:raise ValueError('New map needs more room-list rows than the published table holds')
    for name, raw in new_screens.items():
        i = names.index(name)
        blobs[i] = raw+bytes((len(before[i])-len(raw)) % 4)
    rt = extension.Runtime.__new__(extension.Runtime)
    rt.rom, rt.header, rt.arm, rt.new = rom, h, arm, bytearray(arm)
    rt.end, rt.data = len(arm)-36, bytearray()
    rt.start = kit.TARGET+rt.end-kit.SOURCE
    rt.new[offset(table):offset(table)+count*ENTRY] = payload+bytes(count*ENTRY-len(payload))
    struct.pack_into('<I', rt.new, offset(row)+16*MAP_AREA+12, len(payload)//ENTRY)
    result = rt.finish()
    packed = w.pack_glob(names, blobs)
    ge = next(e for e in w.nitrofs_entries(result) if e['name'] == 'Glob.bin')
    growth = w.align_up(len(packed)-ge['size'])
    hh = w.parse_header(result)
    if growth > 0:
        if hh['used_rom_size']+growth > len(result) or any(x not in (0, 255) for x in result[-growth:]):
            raise ValueError('Insufficient verified cart padding')
        staged = bytearray(result[:ge['end']]+bytes(growth)+result[ge['end']:-growth])
        for e in w.nitrofs_entries(result):
            if e['start'] >= ge['end']:
                struct.pack_into('<2I', staged, hh['fat_offset']+e['id']*8, e['start']+growth, e['end']+growth)
        struct.pack_into('<I', staged, 0x80, hh['used_rom_size']+growth)
        struct.pack_into('<H', staged, 0x15e, w.crc16(staged[:0x15e]))
        result = bytes(staged)
    result = w.rebuild_rom(result, {'Glob.bin': packed})
    w.validate_rom(result, target=True)
    hh = w.parse_header(result)
    new_arm = result[hh['arm9_offset']:hh['arm9_offset']+hh['arm9_size']]
    changed = [n for n, a, b in zip(names, before, blobs) if a != b]
    if not set(changed) <= set(nav.SCREENS):raise ValueError('Unexpected map resource scope')
    return result, dict(parent_sha256=w.sha256(rom), rom_sha256=w.sha256(result), arm9_sha256=w.sha256(new_arm),
        modified_resources=changed, nitrofs_relocation_bytes=max(growth, 0), area_row=row, entries=table,
        entry_count=dict(old=count, new=len(payload)//ENTRY), rooms=len(nav.RECTS),
        arm9_bytes_changed=sum(a != b for a, b in zip(arm, new_arm)))


def generate(output, source):
    output, source = Path(output), Path(source)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):
        raise ValueError('Candidates belong in build/')
    result, report = apply_rom(source.read_bytes())
    path = output/'Versioned.nds'
    w.atomic_write(path, result, sources=(source,))
    w.write_json(output/'changes.json', report)
    print(json.dumps(dict(path=str(path), sha256=report['rom_sha256'], entries=report['entry_count'])), flush=True)
    return path


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True, help='Any Crane Row ROM with the published map table')
    a = p.parse_args()
    generate(a.out, a.source)
