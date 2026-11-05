"""Report the game's four native heaps (free, largest free block, used) from a main-RAM dump.

USA CS5E boot routine 0x02005D60 creates four NitroSystem expanded heaps from OS
arena 0 (main RAM) using the {arena, size} table at 0x0211B93C: 0x82000, 0x30000,
0x81400 bytes, then the rest of the arena. Their handles sit in a table at
0x0213FD60 (0x14-byte entries: handle + NNSFndAllocator); the heap index is also
each block's group ID. Layout follows NitroSystem fnd/expheap: head signature
'EXPH', start +0x18, end +0x1C, free list +0x24, used list +0x2C; 16-byte block
headers 'FR'/'UD', payload size +4, next +0xC. Dump RAM with `tools/kit_lab.py`
(`--ram FRAME`, writes ram-NNNNN.bin). Texture VRAM is a separate pool and is not
reported here. See TECHNICAL "External EUR decompilation".
"""
from __future__ import annotations

import argparse
from pathlib import Path
import struct

BASE = 0x02000000
TABLE, ENTRY, COUNT = 0x0213FD60, 0x14, 4
EXPH, FREE, USED = 0x45585048, 0x4652, 0x5544
HEADER = 16


def blocks(ram: bytes, head: int, signature: int) -> list[int]:
    """Payload sizes along one block list; a broken or cyclic list raises."""
    sizes, seen = [], set()
    while head:
        if head in seen or not BASE <= head <= BASE + len(ram) - HEADER:
            raise ValueError(f'bad block pointer {head:#x}')
        seen.add(head)
        sig, _, size, _, head = struct.unpack_from('<HHIII', ram, head - BASE)
        if sig != signature:
            raise ValueError(f'block signature {sig:#06x}, expected {signature:#06x}')
        sizes.append(size)
    return sizes


def heaps(ram: bytes) -> list[dict]:
    def u32(address): return struct.unpack_from('<I', ram, address - BASE)[0]
    out = []
    for index in range(COUNT):
        handle = u32(TABLE + index * ENTRY)
        if u32(handle) != EXPH:
            raise ValueError(f'heap {index} handle {handle:#x} is not an expanded heap')
        free, used = blocks(ram, u32(handle + 0x24), FREE), blocks(ram, u32(handle + 0x2C), USED)
        out.append({'index': index, 'start': u32(handle + 0x18), 'end': u32(handle + 0x1C),
                    'free': sum(free), 'largest_free': max(free, default=0), 'free_blocks': len(free),
                    'used': sum(used), 'used_blocks': len(used)})
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('ram', type=Path, help='4 MiB main-RAM dump starting at 0x02000000')
    args = parser.parse_args(argv)
    for h in heaps(args.ram.read_bytes()):
        print(f"heap {h['index']} {h['start']:#010x}-{h['end']:#010x} size {h['end'] - h['start']:>8} "
              f"free {h['free']:>8} largest {h['largest_free']:>8} ({h['free_blocks']} blocks) "
              f"used {h['used']:>8} ({h['used_blocks']} blocks)")


if __name__ == '__main__':
    main()
