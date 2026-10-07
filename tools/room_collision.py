"""Lossless BSP node/list framing. Node meanings require empirical controls."""
from dataclasses import dataclass
import struct

from tools.custom_formats import Bsp


@dataclass(frozen=True)
class RoomCollision:
    envelope: Bsp
    nodes: tuple[tuple[int, int, int, int], ...]
    lists: tuple[tuple[tuple[int, int], ...], ...]

    @classmethod
    def parse(cls, raw):
        envelope = Bsp.parse(bytes(raw))
        if not envelope.region_offsets:
            raise ValueError('BSP has no lists')
        start, end = envelope.table_end, envelope.region_offsets[0]
        if (end - start) % 12:
            raise ValueError('BSP node area is not a 12-byte stream')
        nodes = tuple(struct.iter_unpack('<iIHH', raw[start:end]))
        lists = []
        for a, z in zip(envelope.region_offsets, (*envelope.region_offsets[1:], len(raw))):
            if z - a < 2: raise ValueError('Truncated BSP list')
            count = struct.unpack_from('<H', raw, a)[0]
            if z - a != 2 + count * 4: raise ValueError('BSP list count/size mismatch')
            entries = tuple(struct.iter_unpack('<HH', raw[a + 2:z]))
            if any(index >= len(nodes) for index, _ in entries):
                raise ValueError('BSP list references a nonexistent node')
            lists.append(entries)
        return cls(envelope, nodes, tuple(lists))

    def to_bytes(self):
        e = self.envelope
        prefix = e.raw[:e.table_end]
        return (prefix + b''.join(struct.pack('<iIHH', *n) for n in self.nodes)
                + b''.join(struct.pack('<H', len(entries)) + b''.join(struct.pack('<HH', *entry) for entry in entries)
                           for entries in self.lists))

    def replace_unknown_word0(self, node, value):
        if type(node) is not int or not 0 <= node < len(self.nodes):
            raise ValueError('Node index out of range')
        if type(value) is not int or not -(1 << 31) <= value < (1 << 31):
            raise ValueError('Node word must be signed i32')
        result = bytearray(self.to_bytes())
        struct.pack_into('<i', result, self.envelope.table_end + node * 12, value)
        self.parse(result)
        return bytes(result)
