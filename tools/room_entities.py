"""Lossless framing of room OBJ entity batches; kind words stay unknown.

Section 0 contains consecutive batches, not just the first character array.
Native entity names correspond to the concatenated batch order. Records retain
all unknown bytes; the bounded character edit changes only observed XYZ fields.
"""
from dataclasses import dataclass
import struct

from tools.room_objects import RoomObjects


@dataclass(frozen=True)
class Batch:
    header: bytes
    records: tuple[bytes, ...]


@dataclass(frozen=True)
class Entities:
    batches: tuple[Batch, ...]

    @classmethod
    def parse(cls, raw):
        raw = bytes(raw)
        at, batches = 0, []
        while at < len(raw):
            if at + 4 > len(raw): raise ValueError('Truncated entity batch header')
            size, header_size, count = struct.unpack_from('<HBB', raw, at)
            if size < 4 or at + size > len(raw) or header_size != (4 + count + 3) // 4 * 4:
                raise ValueError('Invalid entity batch bounds')
            if header_size > size: raise ValueError('Entity header exceeds batch')
            pos, records = at + header_size, []
            for length in raw[at + 4:at + 4 + count]:
                if not length or pos + length > at + size:
                    raise ValueError('Entity record exceeds batch')
                records.append(raw[pos:pos + length])
                pos += length
            if pos != at + size: raise ValueError('Entity batch has unexpected trailing data')
            batches.append(Batch(raw[at:at + header_size], tuple(records)))
            at += size
        return cls(tuple(batches))

    def to_bytes(self):
        return b''.join(batch.header + b''.join(batch.records) for batch in self.batches)

    @property
    def records(self): return tuple(record for batch in self.batches for record in batch.records)

    def replace_record(self, index, payload):
        if type(index) is not int or not 0 <= index < len(self.records):
            raise ValueError('Entity index out of range')
        if len(payload) != len(self.records[index]): raise ValueError('Entity replacement must retain size')
        flat, chunks = 0, []
        for batch in self.batches:
            chunks.append(batch.header)
            for record in batch.records:
                chunks.append(bytes(payload) if flat == index else record)
                flat += 1
        result = b''.join(chunks)
        self.parse(result)
        return result


def character_position(raw, object_index, entity_index, xyz):
    room = RoomObjects.parse(raw)
    if type(object_index) is not int or not 0 <= object_index < len(room.records):
        raise ValueError('Object index out of range')
    record, names = room.records[object_index], room.names[object_index]
    entities = Entities.parse(record.sections[0])
    if names.category_ends[0] != len(entities.records): raise ValueError('Entity name/count mismatch')
    if type(entity_index) is not int or not 0 <= entity_index < len(entities.records):
        raise ValueError('Entity index out of range')
    source = entities.records[entity_index]
    if len(source) != 24 or not names.labels[entity_index].startswith('Character ('):
        raise ValueError('Expected named 24-byte character placement')
    if len(xyz) != 3 or any(type(v) is not int or not -(1<<31) <= v < (1<<31) for v in xyz):
        raise ValueError('Expected three signed Q12 coordinates')
    changed = bytearray(source)
    struct.pack_into('<3i', changed, 0, *xyz)
    return room.replace_section(object_index, 0, entities.replace_record(entity_index, changed))
