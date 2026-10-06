"""Test Upgrades sparring room: Test_Combat01_app.obj with extra Brutes.

Test Upgrades loads room Test_Combat01 (room id 0x51F). Its OBJ holds three
objects; the last places one "Character (Practice Dummy)" (character type 50,
the black-suited Brute). The game keeps that first placement passive, while
further placements in the same characters section spawn with their native AI
and attack. Everything else (header words, event-graph bytes, unknown fields,
the other objects) is preserved; the editor only rewrites the characters
section, the size/offset words that bound it and the matching name records.
See docs/TECHNICAL.md "Training room (Test Upgrades)".
"""
from __future__ import annotations
import struct

NAME = 'Test_Combat01_app.obj'
CLEAN_SHA256 = 'b80b87a7b4be66b02833498181bb5513d54d8d782a93d632597332fa73fb24ff'
DUMMY_OBJECT = 0x47C            # third object record (u16 size 0x4C, 01 01)
NAMES_BLOCK = 0x7E8             # its name block: u32 size, u16 0x14, 7 cumulative u16 counts
RECORD = 24                     # x, y, z, u32 2, u32 angle, u16 0, u16 character type
RIGHT, LEFT = 0x4000, 0xC000    # facing angles of the native placements
# Sparring Brutes (x in Q12 units, facing): one left of Spidey's start (120
# units), two right of the passive dummy (141). Walls are at about 3.5/236.5.
SPARRING = ((60 * 4096, RIGHT), (190 * 4096, LEFT), (215 * 4096, LEFT))


def _sha(data):
    import hashlib
    return hashlib.sha256(data).hexdigest()


def characters(obj: bytes, at=DUMMY_OBJECT):
    """Character placements of one object: (x, y, z, angle, type) per record."""
    size, header, count = struct.unpack_from('<HBB', obj, at + 0x14)
    if header != 8 or size != 8 + RECORD * count:
        raise ValueError('Unexpected characters section')
    out = []
    for i in range(count):
        x, y, z, _, angle, _, kind = struct.unpack_from('<3iIIHH', obj, at + 0x14 + 8 + RECORD * i)
        out.append((x, y, z, angle, kind))
    return out


def with_sparring(clean: bytes, sparring=SPARRING) -> bytes:
    """Clean OBJ plus sparring copies of the dummy placement (at most 3)."""
    if _sha(clean) != CLEAN_SHA256:
        raise ValueError(f'{NAME} differs from the clean CS5E resource')
    d = bytearray(clean)
    at, section = DUMMY_OBJECT, DUMMY_OBJECT + 0x14
    if d[at + 2:at + 4] != b'\x01\x01' or struct.unpack_from('<H', d, at)[0] != 0x4C:
        raise ValueError('Unexpected dummy object record')
    base = bytes(d[section + 8:section + 8 + RECORD])
    records = [base]
    for x, angle in sparring:
        r = bytearray(base)
        struct.pack_into('<i', r, 0, x)
        struct.pack_into('<I', r, 16, angle)
        records.append(bytes(r))
    k = len(records)
    if k > 4:
        raise ValueError('The 8-byte characters header holds at most four record tags')
    new = struct.pack('<HBB', 8 + RECORD * k, 8, k) + bytes([RECORD] * k) + bytes(4 - k) + b''.join(records)
    old_size = 8 + RECORD
    delta = len(new) - old_size
    d[section:section + old_size] = new
    struct.pack_into('<H', d, at, 0x4C + delta)
    ends = struct.unpack_from('<5H', d, at + 8)            # section end offsets, relative to +0x14
    struct.pack_into('<5H', d, at + 8, *(e + delta for e in ends))
    objects_end, names = struct.unpack_from('<2I', d, 4)
    struct.pack_into('<2I', d, 4, objects_end + delta, names + delta)
    block = NAMES_BLOCK + delta
    size = struct.unpack_from('<I', d, block)[0]
    counts = struct.unpack_from('<7H', d, block + 6)
    name = bytes(d[block + 0x14:block + 0x34])
    if block + size != len(d) or counts[0] != 1 or not name.startswith(b'Character (Practice Dummy)\0'):
        raise ValueError('Unexpected dummy name block')
    extra = name * (k - 1)
    struct.pack_into('<I', d, block, size + len(extra))
    struct.pack_into('<7H', d, block + 6, *(c + k - 1 for c in counts))
    d[block + 0x34:block + 0x34] = extra
    return bytes(d)
