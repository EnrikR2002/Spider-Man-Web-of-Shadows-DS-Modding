"""Bounded 0x10 LZ77 and Griptonite 0x60 PuCrunch codecs, standard library only.

Independent implementation of the documented wire algorithm. Literal encoders
favor simplicity and determinism over compression ratio. Original wrappers are
retained for no-op round trips. References and limitations: FORMAT_NOTES.md.
"""
from dataclasses import dataclass
import struct
from . import wos_tool as w

MAX_DECODED = 16 * 1024 * 1024


class Bits:
    def __init__(self, data, position=0): self.data, self.position = data, position
    def read(self, count):
        if self.position + count > len(self.data) * 8: raise ValueError('Truncated PuCrunch bitstream')
        value = 0
        for _ in range(count):
            # Bits run MSB-first through little-endian 32-bit words.
            byte_index = (self.position // 32) * 4 + 3 - (self.position % 32) // 8
            if byte_index >= len(self.data): raise ValueError('Truncated PuCrunch word')
            value = (value << 1) | ((self.data[byte_index] >> (7 - self.position % 8)) & 1)
            self.position += 1
        return value
    def gamma(self):
        count = 0
        while count < 7 and self.read(1): count += 1
        return (1 << count) | self.read(count)


def decoded_size(data):
    w.check_range(data, 0, 4, 'Compression header')
    size = w.u32(data, 0) >> 8
    if size > MAX_DECODED: raise ValueError('Decoded stream exceeds 16 MiB limit')
    return size


def decode(data: bytes) -> bytes:
    size = decoded_size(data)
    out = bytearray()
    def emit(value, count=1):
        if len(out) + count > size: raise ValueError('Compression token exceeds declared output size')
        out.extend(bytes([value]) * count)
    def copy(distance, count):
        if not 1 <= distance <= len(out): raise ValueError('Compression back-reference before output start')
        if len(out) + count > size: raise ValueError('Compression copy exceeds declared output size')
        for _ in range(count): out.append(out[-distance])
    if data[0] == 0x10:
        pos = 4
        while len(out) < size:
            w.check_range(data, pos, 1, 'LZ77 flags'); flags = data[pos]; pos += 1
            for bit in range(7, -1, -1):
                if len(out) == size: break
                if flags & (1 << bit):
                    w.check_range(data, pos, 2, 'LZ77 copy')
                    a, b = data[pos:pos + 2]; pos += 2
                    copy(((a & 15) << 8) + b + 1, (a >> 4) + 3)
                else:
                    w.check_range(data, pos, 1, 'LZ77 literal'); emit(data[pos]); pos += 1
    elif data[0] == 0x60:
        w.check_range(data, 4, 4, 'PuCrunch parameters')
        table_size, escape, extra, width = data[4:8]
        if not 4 <= table_size <= 32 or table_size % 4 or extra > 24 or width > 8 or escape >= 1 << width:
            raise ValueError('Invalid PuCrunch parameters')
        w.check_range(data, 8, table_size, 'PuCrunch RLE table')
        table = data[8:8 + table_size]
        bits = Bits(data, (8 + table_size) * 8)
        while True:
            prefix = bits.read(width)
            if prefix != escape:
                emit((prefix << (8 - width)) | bits.read(8 - width))
                continue
            length = bits.gamma() + 1
            if length > 2:
                high = bits.gamma() - 1
                if high == 254: break
                distance = (high << (8 + extra)) + bits.read(8 + extra) + 1
                copy(distance, length)
            elif bits.read(1) == 0:
                copy(bits.read(8) + 1, 2)
            elif bits.read(1) == 0:
                new_escape = bits.read(width)
                emit((escape << (8 - width)) | bits.read(8 - width))
                escape = new_escape
            else:
                run = bits.gamma()
                if run >= 128:
                    run = ((run << 1) | bits.read(1)) & 255
                    run |= (bits.gamma() - 1) << 8
                code = bits.gamma()
                if code < 32:
                    if code > table_size: raise ValueError('PuCrunch RLE index outside table')
                    value = table[code - 1]
                else: value = ((code << 3) | bits.read(3)) & 255
                emit(value, run + 1)
    else: raise ValueError(f'Unsupported compression type 0x{data[0]:02x}')
    if len(out) != size: raise ValueError('Compression EOF before declared output size')
    return bytes(out)


class BitWriter:
    def __init__(self): self.data, self.count = bytearray(), 0
    def write(self, value, width):
        for bit in range(width - 1, -1, -1):
            if self.count % 8 == 0: self.data.append(0)
            self.data[-1] |= ((value >> bit) & 1) << (7 - self.count % 8)
            self.count += 1
    def gamma(self, value):
        if not 1 <= value <= 255: raise ValueError('Gamma value must be 1..255')
        count = value.bit_length() - 1
        self.write((1 << count) - 1, count)
        if count < 7: self.write(0, 1)
        self.write(value - (1 << count), count)


def encode_literals(data: bytes, kind=0x60) -> bytes:
    if len(data) >= 1 << 24: raise ValueError('Input exceeds 24-bit compressed header length')
    header = struct.pack('<I', (len(data) << 8) | kind)
    if kind == 0x10:
        result = header + b''.join(b'\0' + data[i:i + 8] for i in range(0, len(data), 8))
    elif kind == 0x60:
        writer = BitWriter()
        for value in data:
            writer.write(value, 8)
            if value == 0:
                # Escape 0, length=2, escaped-literal selector, same new escape.
                writer.gamma(1); writer.write(2, 2); writer.write(0, 8)
        writer.write(0, 8); writer.gamma(2); writer.gamma(255)
        stream = bytes(writer.data) + bytes((-len(writer.data)) % 4)
        stream = b''.join(stream[i:i + 4][::-1] for i in range(0, len(stream), 4))
        result = header + b'\x04\0\0\x08' + bytes(4) + stream
    else: raise ValueError('Only 0x10/0x60 encoders are supported')
    result += bytes((-len(result)) % 4)
    if decode(result) != data: raise ValueError('Encoded stream failed round-trip verification')
    return result


@dataclass(frozen=True)
class CompressedBlob:
    raw: bytes
    decoded: bytes
    @classmethod
    def parse(cls, raw): return cls(raw, decode(raw))
    def to_bytes(self): return self.raw
    def replace_decoded(self, data):
        return self.raw if data == self.decoded else encode_literals(data, self.raw[0])
