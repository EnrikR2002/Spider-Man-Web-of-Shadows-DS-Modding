"""Confirmed outer structures only. Opaque sections are retained byte-for-byte."""
from dataclasses import dataclass
from pathlib import Path
import struct
from . import wos_tool as w

ACTOR_KIND = 0x8e3e7b2b
BINDING_EXTENSIONS = {0: '.sca', 1: '.nsbta', 3: '.gmb', 4: '.gab'}


@dataclass(frozen=True)
class Xbd:
    raw: bytes
    kind: int
    unknown_u16_08: int
    unknown_u16_0a: int
    bindings: tuple[dict, ...]
    opaque_tail_start: int

    @classmethod
    def parse(cls, raw: bytes, names: list[str]):
        w.check_range(raw, 0, 12, 'XBD envelope')
        if len(raw) % 4 or w.u32(raw, 4) != len(raw) - 12 or raw[:4] != raw[-4:]:
            raise ValueError('XBD envelope size/type footer mismatch')
        kind, value08, value0a = w.u32(raw, 0), w.u16(raw, 8), w.u16(raw, 10)
        bindings, pos = [], 8
        if kind == ACTOR_KIND:
            w.check_range(raw, 0, 24, 'Actor XBD prefix')
            pos = 20
            while pos + 4 <= len(raw) - 4:
                index, tag = struct.unpack_from('<hH', raw, pos)
                if index < 0: break
                if index >= len(names) or tag not in BINDING_EXTENSIONS:
                    raise ValueError('Unknown actor binding index/tag')
                name = names[index]
                if Path(name).suffix != BINDING_EXTENSIONS[tag]:
                    raise ValueError(f'XBD binding tag/file extension mismatch: {name}')
                bindings.append({'offset': pos, 'index': index, 'tag': tag, 'name': name})
                pos += 4
            if pos + 4 > len(raw) - 4 or struct.unpack_from('<h', raw, pos)[0] != -value08:
                raise ValueError('Actor XBD opaque-tail boundary mismatch')
        return cls(raw, kind, value08, value0a, tuple(bindings), pos)

    def to_bytes(self): return self.raw

    def replace_binding(self, offset: int, new_index: int, names: list[str]) -> bytes:
        record = next((b for b in self.bindings if b['offset'] == offset), None)
        if record is None: raise ValueError('Offset is not a parsed actor binding')
        if not 0 <= new_index < min(len(names), 32768): raise ValueError('Binding index out of range')
        if Path(names[new_index]).suffix != BINDING_EXTENSIONS[record['tag']]:
            raise ValueError('Replacement must match the binding extension/tag')
        result = bytearray(self.raw); struct.pack_into('<H', result, offset, new_index)
        Xbd.parse(bytes(result), names)
        return bytes(result)


@dataclass(frozen=True)
class Gab:
    raw: bytes
    words: tuple[int, ...]
    terminator_offset: int
    padding_size: int
    records: tuple[tuple[int, int, int], ...]

    @classmethod
    def parse(cls, raw: bytes):
        if len(raw) < 8 or len(raw) % 4: raise ValueError('GAB must be a nonempty aligned u16 stream')
        if raw.endswith(b'\xff' * 6): padding = 0
        elif raw.endswith(b'\xff' * 6 + b'\0\0'): padding = 2
        else: raise ValueError('GAB missing observed three-ffff terminator')
        end = len(raw) - 6 - padding
        if end % 6: raise ValueError('GAB payload must contain whole three-u16 records')
        records = tuple(struct.iter_unpack('<HHH', raw[:end]))
        return cls(raw, struct.unpack(f'<{len(raw) // 2}H', raw), end, padding, records)

    def to_bytes(self): return self.raw


@dataclass(frozen=True)
class Bsp:
    raw: bytes
    table_end: int
    region_offsets: tuple[int, ...]

    @classmethod
    def parse(cls, raw: bytes):
        w.check_range(raw, 0, 24, 'BSP prefix')
        if raw[:4] != b'BSP\0' or w.u32(raw, 4) != 7 or w.u32(raw, 8) != 2 or w.u32(raw, 12) != len(raw):
            raise ValueError('Unsupported BSP envelope')
        end = w.u32(raw, 16)
        if not 24 <= end <= len(raw) or end % 4: raise ValueError('BSP offset-table boundary invalid')
        if w.u32(raw, end - 4) != 0x01000000: raise ValueError('BSP unknown table trailer differs from observed constant')
        offsets = struct.unpack(f'<{(end - 24) // 4}I', raw[20:end - 4])
        if any(not end <= v <= len(raw) or v % 2 for v in offsets) or any(a > b for a, b in zip(offsets, offsets[1:])):
            raise ValueError('BSP region offsets out of bounds/nonmonotonic')
        return cls(raw, end, offsets)

    def to_bytes(self): return self.raw
