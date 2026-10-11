"""Lossless BSP node/list framing, plus the solid/empty tree walk (TECHNICAL "Room collision tree").

Node (12 bytes): i32 word0 = plane distance (Q12) with two flag bits in bits
0..1, u32 word1 = plane normal, u16 unknown, u16 link. Normal: 0x4000000N is
axis N & 3 (x, y, z), negated when N & 4; any other word is two s16 (Q12)
holding the *negated* (x, y) normal of a slanted wall. A point is in front of
a node when normal . p >= distance.
The stream is a tree in preorder: flag 1 = the front child is a solid leaf
(link = index of its list), flag 2 = the back child is empty space; a child
that is neither is the next node, and when both children are nodes the front
one follows and the back one is node `link`. Every list is the solid leaf of
exactly one node (all 75 rooms; tests). The list entries (node, value) and the
u16 at +8 are still unknown. Confirmed in game on Hive_Map02 (walls, ledges
and landing heights measured with Spidey). Objects (doors, ichor gates,
smashable floors, liftables) add collision that is not in this file.
"""
from dataclasses import dataclass
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.custom_formats import Bsp

FRONT_SOLID, BACK_EMPTY = 1, 2


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

    def side(self, node, x, y, z=0.0):
        """Signed distance (units) of a point from node's plane; >= 0 is the front."""
        word0, word1 = self.nodes[node][:2]
        distance = (word0 & ~3) / 4096
        if word1 >> 28 == 4:
            value = (x, y, z)[word1 & 3]
            return (-value if word1 & 4 else value) - distance
        nx, ny = struct.unpack('<2h', struct.pack('<I', word1))
        return -(nx * x + ny * y) / 4096 - distance

    def children(self, node):
        """(front, back): ('solid', list index), ('empty', None) or ('node', index)."""
        flags, link = self.nodes[node][0] & 3, self.nodes[node][3]
        front = ('solid', link) if flags & FRONT_SOLID else ('node', node + 1)
        if flags & BACK_EMPTY: back = ('empty', None)
        else: back = ('node', link if not flags & FRONT_SOLID else node + 1)
        return front, back

    def solid_at(self, x, y, z=0.0):
        """Index of the solid leaf holding the point (world units), or None in empty space."""
        node = 0
        for _ in range(len(self.nodes) + 1):
            kind, value = self.children(node)[0 if self.side(node, x, y, z) >= 0 else 1]
            if kind == 'solid': return value
            if kind == 'empty': return None
            node = value
        raise ValueError('BSP walk did not end')

    def check_tree(self):
        """Raise unless the node stream is one preorder tree using every list exactly once."""
        seen, leaves = [0] * len(self.nodes), []
        stack, node = [], 0
        while True:
            if node >= len(self.nodes): raise ValueError('BSP tree runs past its nodes')
            seen[node] += 1
            front, back = self.children(node)
            if front[0] == 'solid': leaves.append(front[1])
            nexts = [value for kind, value in (front, back) if kind == 'node']
            if len(nexts) == 2:
                stack.append(nexts[1]); node = nexts[0]
            elif nexts: node = nexts[0]
            elif stack:
                if stack[-1] != node + 1: raise ValueError('BSP back child is not in preorder')
                node = stack.pop()
            else: break
        if node != len(self.nodes) - 1 or any(n != 1 for n in seen): raise ValueError('BSP nodes are not one tree')
        if sorted(leaves) != list(range(len(self.lists))): raise ValueError('BSP lists are not the solid leaves')

    def floor_below(self, x, y, limit=400.0, step=0.25):
        """Height of the first solid found straight below an empty point, or None within `limit` units."""
        if self.solid_at(x, y) is not None: raise ValueError('Point is inside collision')
        for n in range(1, int(limit / step) + 1):
            if self.solid_at(x, y - n * step) is not None: return y - (n - 1) * step
        return None

    def map_png(self, bounds, scale=2, marks=()):
        """PNG of the z=0 slice: solid dark, empty light; marks = (x, y, (r, g, b)[, radius]) dots."""
        from tools.nitro_texture import png_rgb
        x0, y0, x1, y1 = bounds
        width, height = int((x1 - x0) * scale), int((y1 - y0) * scale)
        image = bytearray(bytes((226, 226, 216)) * (width * height))
        for py in range(height):
            y = y1 - (py + 0.5) / scale
            for px in range(width):
                leaf = self.solid_at(x0 + (px + 0.5) / scale, y)
                if leaf is not None:
                    image[(py * width + px) * 3:(py * width + px) * 3 + 3] = bytes(
                        (40 + leaf * 37 % 60, 40 + leaf * 53 % 60, 60 + leaf * 29 % 80))
        for gx in range(int(x0 // 50 + 1) * 50, int(x1), 50):          # tick every 50 units along both axes
            for k in range(4): marks = (*marks, (gx, y0 + (k + 0.5) / scale, (0, 0, 0), 0))
        for gy in range(int(y0 // 50 + 1) * 50, int(y1), 50):
            for k in range(4): marks = (*marks, (x0 + (k + 0.5) / scale, gy, (0, 0, 0), 0))
        for x, y, colour, *radius in marks:
            r = radius[0] if radius else 2
            cx, cy = int((x - x0) * scale), int((y1 - y) * scale)
            for yy in range(max(0, cy - r), min(height, cy + r + 1)):
                for xx in range(max(0, cx - r), min(width, cx + r + 1)):
                    image[(yy * width + xx) * 3:(yy * width + xx) * 3 + 3] = bytes(colour)
        return png_rgb(width, height, bytes(image))

    def replace_unknown_word0(self, node, value):
        if type(node) is not int or not 0 <= node < len(self.nodes):
            raise ValueError('Node index out of range')
        if type(value) is not int or not -(1 << 31) <= value < (1 << 31):
            raise ValueError('Node word must be signed i32')
        result = bytearray(self.to_bytes())
        struct.pack_into('<i', result, self.envelope.table_end + node * 12, value)
        self.parse(result)
        return bytes(result)


MARK_COLOURS = {7: (0, 150, 0), 14: (210, 0, 0), 3: (0, 0, 220), 4: (200, 0, 200), 2: (255, 140, 0), 10: (0, 200, 200)}


def room_map(collision_raw, objects_raw, scale=2, margin=30):
    """Collision PNG of a room with its entities (triggers green, objects red, doors blue,
    spawners magenta, characters orange, save point cyan) and door spawns (yellow)."""
    from tools import room_doors
    from tools.room_entities import Entities
    from tools.room_objects import RoomObjects
    marks = [(spawn.x / 4096, spawn.y / 4096, (255, 215, 0), 1) for spawn in room_doors.spawns(objects_raw)]
    for record in RoomObjects.parse(objects_raw).records:
        for entity in Entities.parse(record.sections[0]).records:
            if len(entity) >= 16:
                x, y = (v / 4096 for v in struct.unpack_from('<2i', entity))
                kind = struct.unpack_from('<I', entity, 12)[0]
                if abs(y) < 2000: marks.append((x, y, MARK_COLOURS.get(kind, (120, 120, 120))))
    xs, ys = [m[0] for m in marks], [m[1] for m in marks]
    bounds = (int(min(xs)) - margin, int(min(ys)) - margin, int(max(xs)) + margin, int(max(ys)) + margin)
    return RoomCollision.parse(collision_raw).map_png(bounds, scale, tuple(marks)), bounds


def main(argv=None):
    import argparse
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import mod
    parser = argparse.ArgumentParser(description='Collision map of a native room (z=0 slice with entities).')
    parser.add_argument('room', help='native room name, e.g. Hive_Map02')
    parser.add_argument('--out', default=None, help='PNG path (default work/maps/<room>.png)')
    parser.add_argument('--scale', type=int, default=3, help='pixels per world unit')
    parser.add_argument('--objects', default=None, help='OBJ file to mark instead of the native one')
    args = parser.parse_args(argv)
    _, glob, manifest = mod.load_clean()
    blobs = {e['name']: glob[e['offset']:e['offset'] + e['size']] for e in manifest['entries']}
    objects = Path(args.objects).read_bytes() if args.objects else blobs[args.room + '_app.obj']
    png, bounds = room_map(blobs[args.room + '.bsp'], objects, args.scale)
    out = Path(args.out or mod.ROOT / 'work/maps' / (args.room + '.png'))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(png)
    print(f'{out}: x {bounds[0]}..{bounds[2]}, y {bounds[1]}..{bounds[3]}, {args.scale} px per unit')


if __name__ == '__main__':
    main()
