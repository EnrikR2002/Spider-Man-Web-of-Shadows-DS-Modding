"""Lossless CS5E room-object envelopes; event/entity payloads remain opaque.

The five section boundaries and name blocks are validated against all 75 clean
rooms. This is NOT an event-graph compiler or a character factory.
"""
from __future__ import annotations

from dataclasses import dataclass
import struct


def _range(raw, at, size, label):
    if at < 0 or size < 0 or at + size > len(raw):
        raise ValueError(f'Truncated {label}')


@dataclass(frozen=True)
class ObjectRecord:
    offset: int
    raw: bytes
    sections: tuple[bytes, ...]

    def replace_section(self, index: int, payload: bytes) -> bytes:
        if type(index) is not int or not 0 <= index < 5:
            raise ValueError('Section index must be 0..4')
        sections = list(self.sections)
        sections[index] = bytes(payload)
        lengths, total = [], 0
        for section in sections:
            total += len(section)
            lengths.append(total)
        if total + 20 > 65535:
            raise ValueError('Object record exceeds u16 size')
        header = bytearray(self.raw[:20])
        struct.pack_into('<H', header, 0, total + 20)
        struct.pack_into('<5H', header, 8, *lengths)
        return bytes(header) + b''.join(sections)


@dataclass(frozen=True)
class NameBlock:
    raw: bytes
    category_ends: tuple[int, ...]
    slots: tuple[bytes, ...]

    @property
    def labels(self):
        # Exact raw slots, including padding and unclassified trailing names,
        # are retained. Labels are advisory editor names, not executable code.
        return tuple(slot.split(b'\0', 1)[0].rstrip(b' ').decode('ascii', 'replace')
                     for slot in self.slots)


@dataclass(frozen=True)
class RoomObjects:
    raw: bytes
    header: bytes
    records: tuple[ObjectRecord, ...]
    between: bytes
    names: tuple[NameBlock, ...]

    @classmethod
    def parse(cls, raw: bytes):
        raw = bytes(raw)
        _range(raw, 0, 16, 'room header')
        if struct.unpack_from('<I', raw)[0] != 2:
            raise ValueError('Unsupported room-object version')
        records_end, names_at = struct.unpack_from('<2I', raw, 4)
        count = raw[12]
        at = 16 + struct.unpack_from('<H', raw, 14)[0]
        if not 16 <= at <= records_end <= names_at <= len(raw):
            raise ValueError('Room-object boundaries out of range')
        if names_at - records_end != count * 8:
            raise ValueError('Unexpected inter-record table size')
        header, records = raw[:at], []
        for _ in range(count):
            _range(raw, at, 20, 'object header')
            size = struct.unpack_from('<H', raw, at)[0]
            ends = struct.unpack_from('<5H', raw, at + 8)
            if size < 20 or ends[-1] != size - 20 or tuple(sorted(ends)) != ends:
                raise ValueError('Invalid object section boundaries')
            if at + size > records_end:
                raise ValueError('Object extends beyond record area')
            starts = (0, *ends[:-1])
            sections = tuple(raw[at + 20 + a:at + 20 + z]
                             for a, z in zip(starts, ends))
            records.append(ObjectRecord(at, raw[at:at + size], sections))
            at += size
        if at != records_end:
            raise ValueError('Record count/end mismatch')
        between, blocks = raw[records_end:names_at], []
        at = names_at
        for _ in range(count):
            _range(raw, at, 20, 'name block header')
            size = struct.unpack_from('<I', raw, at)[0]
            if size < 20 or (size - 20) % 32:
                raise ValueError('Invalid name block size')
            _range(raw, at, size, 'name block')
            ends = struct.unpack_from('<7H', raw, at + 6)
            slots = tuple(raw[i:i + 32] for i in range(at + 20, at + size, 32))
            if tuple(sorted(ends)) != ends or ends[-1] > len(slots):
                raise ValueError('Invalid name category boundaries')
            blocks.append(NameBlock(raw[at:at + size], ends, slots))
            at += size
        if at != len(raw):
            raise ValueError('Unexpected room-object trailing bytes')
        return cls(raw, header, tuple(records), between, tuple(blocks))

    def to_bytes(self):
        return self.header + b''.join(r.raw for r in self.records) + self.between + b''.join(n.raw for n in self.names)

    def replace_section(self, record: int, section: int, payload: bytes):
        """Repack boundaries only. Caller must qualify entity/event semantics.

        Do not add/delete entities here: corresponding name/category and event
        references need a separate, empirically validated editor.
        """
        if type(record) is not int or not 0 <= record < len(self.records):
            raise ValueError('Object record index out of range')
        records = [r.raw for r in self.records]
        records[record] = self.records[record].replace_section(section, payload)
        header = bytearray(self.header)
        end = len(header) + sum(map(len, records))
        struct.pack_into('<2I', header, 4, end, end + len(self.between))
        result = bytes(header) + b''.join(records) + self.between + b''.join(n.raw for n in self.names)
        self.parse(result)
        return result

    def omit_record(self, index=None):
        """Structural experiment only: event references are NOT repaired.

        Native gameplay must be qualified before using this to remove an actor
        group. None is a byte-exact no-op for parser/repacker controls.
        """
        if index is None: return self.to_bytes()
        if type(index) is not int or not 0 <= index < len(self.records):
            raise ValueError('Object record index out of range')
        header = bytearray(self.header)
        records = [r.raw for i,r in enumerate(self.records) if i != index]
        names = [n.raw for i,n in enumerate(self.names) if i != index]
        between = self.between[:index*8] + self.between[(index+1)*8:]
        header[12] = len(records)
        end = len(header) + sum(map(len,records))
        struct.pack_into('<2I',header,4,end,end+len(between))
        result = bytes(header) + b''.join(records) + between + b''.join(names)
        self.parse(result)
        return result
