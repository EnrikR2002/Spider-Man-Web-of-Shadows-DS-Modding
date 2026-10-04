"""Lossless structural parser for decoded CS5E GMB channel arrays.

The clean ARM9's 0x0202A58C / 0x0202A4FC establish channel counts,
record counts and type-specific strides. Coordinate, flag and tag meanings
remain separately documented hypotheses; this module assigns none of them.
Compression wrappers are handled by grip_compression.CompressedBlob.
"""
from dataclasses import dataclass
import struct

# ARM9 handles 6/12 with the same strides as 2/3; neither occurs in the
# 769 clean files surveyed. Unsupported kinds are rejected, not inferred.
RECORD_STRIDES = {0: 28, 2: 44, 3: 32, 4: 48, 5: 36, 6: 44, 12: 32}


@dataclass(frozen=True)
class GmbChannel:
    offset: int
    kind: int
    unknown_u16_02: int
    stride: int
    records: tuple[bytes, ...]

    def words(self, frame: int) -> tuple[int, ...]:
        if not 0 <= frame < len(self.records):
            raise ValueError('GMB record index out of range')
        return struct.unpack(f'<{self.stride // 4}i', self.records[frame])


@dataclass(frozen=True)
class Gmb:
    raw: bytes
    unknown_u16_00: int
    record_count: int
    unknown_u16_06: int
    channels: tuple[GmbChannel, ...]

    @classmethod
    def parse(cls, decoded: bytes):
        raw = bytes(decoded)
        if len(raw) < 8:
            raise ValueError('Truncated GMB header')
        value00, count, channel_count, value06 = struct.unpack_from('<4H', raw)
        channels, pos = [], 8
        # Each declared channel must contain a header even with no records.
        if channel_count > (len(raw) - 8) // 4:
            raise ValueError('GMB channel count exceeds available headers')
        for _ in range(channel_count):
            if pos + 4 > len(raw):
                raise ValueError('Truncated GMB channel header')
            kind, value02 = struct.unpack_from('<hH', raw, pos)
            if kind not in RECORD_STRIDES:
                raise ValueError(f'Unsupported GMB channel kind {kind}')
            stride = RECORD_STRIDES[kind]
            end = pos + 4 + count * stride
            if end > len(raw):
                raise ValueError('GMB channel records exceed decoded data')
            records = tuple(raw[p:p+stride] for p in range(pos+4, end, stride))
            channels.append(GmbChannel(pos, kind, value02, stride, records))
            pos = end
        if pos != len(raw):
            raise ValueError('GMB declared channels do not consume decoded data')
        return cls(raw, value00, count, value06, tuple(channels))

    def to_bytes(self) -> bytes:
        """Repack all channels, retaining every unknown header/record byte."""
        parts = [struct.pack('<4H', self.unknown_u16_00, self.record_count,
                             len(self.channels), self.unknown_u16_06)]
        for channel in self.channels:
            parts.append(struct.pack('<hH', channel.kind, channel.unknown_u16_02))
            parts.extend(channel.records)
        return b''.join(parts)

    def replace_word(self, channel: int, frame: int, word: int, value: int) -> bytes:
        """Change one bounded signed LE i32 without assigning it semantics."""
        if not 0 <= channel < len(self.channels):
            raise ValueError('GMB channel index out of range')
        item = self.channels[channel]
        if not 0 <= frame < self.record_count or not 0 <= word < item.stride // 4:
            raise ValueError('GMB record/word index out of range')
        if not isinstance(value, int) or not -(1 << 31) <= value < (1 << 31):
            raise ValueError('GMB word must be a signed 32-bit integer')
        changed = bytearray(self.raw)
        struct.pack_into('<i', changed, item.offset + 4 + frame * item.stride + word * 4, value)
        Gmb.parse(changed)
        return bytes(changed)
