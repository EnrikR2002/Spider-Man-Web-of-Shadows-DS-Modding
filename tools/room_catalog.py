"""Read the clean CS5E room lookup table without inventing room IDs.

Native lookup 0x02084AB4 indexes a table of pointers to 80-byte descriptors.
Descriptors start at their name pointer. The preceding word is NOT their ID.
"""
from dataclasses import dataclass
import struct

from tools import player_trace as p

LOOKUP = 0x021321F4
COUNT = 75
SIZE = 80


@dataclass(frozen=True)
class RoomEntry:
    index: int
    address: int
    name: str
    texture: int
    bsp: int
    objects: int
    minimap: int
    raw: bytes


def parse(arm9: bytes, names: list[str]):
    entries, addresses = [], set()
    for index in range(COUNT):
        at = LOOKUP - p.BASE + 4 * index
        if at + 4 > len(arm9): raise ValueError('Truncated room lookup')
        address = struct.unpack_from('<I', arm9, at)[0]
        offset = address - p.BASE
        if address % 4 or not 0 <= offset <= len(arm9) - SIZE:
            raise ValueError('Room descriptor outside ARM9')
        if address in addresses: raise ValueError('Duplicate room descriptor')
        addresses.add(address)
        raw = arm9[offset:offset + SIZE]
        name_at, texture, bsp, objects = struct.unpack_from('<4I', raw)
        name_offset = name_at - p.BASE
        if not 0 <= name_offset < len(arm9): raise ValueError('Room name outside ARM9')
        end = arm9.find(b'\0', name_offset, name_offset + 64)
        if end < 0: raise ValueError('Unterminated room name')
        try: name = arm9[name_offset:end].decode('ascii')
        except UnicodeDecodeError as exc: raise ValueError('Non-ASCII room name') from exc
        minimap = struct.unpack_from('<I', raw, 76)[0]
        for resource in (texture, bsp, objects, minimap):
            if not 0 <= resource < len(names): raise ValueError('Room resource out of range')
        if names[bsp] != name + '.bsp' or names[objects] != name + '_app.obj':
            raise ValueError('Room name/resource mismatch')
        if not names[texture].endswith('.nsbtx') or not names[minimap].endswith('.cbmp'):
            raise ValueError('Unexpected room texture/minimap format')
        entries.append(RoomEntry(index, address, name, texture, bsp, objects, minimap, raw))
    return tuple(entries)
