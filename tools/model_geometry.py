"""Lossless single-model NSBMD mesh framing and bounded authored GPU streams.

Nitro layout reference: https://github.com/scurest/nsbmd_docs
Opaque material, bone, SBC and original mesh data remain intact. New streams
are appended and referenced by existing shape headers; no new rig is implied.
"""
from dataclasses import dataclass
import struct

from tools.nitro_texture import dictionary
from tools import wos_tool as w


@dataclass(frozen=True)
class Shape:
    name: str
    header: int
    start: int
    length: int


@dataclass(frozen=True)
class ModelGeometry:
    raw: bytes
    block: int
    model: int
    shapes: tuple[Shape, ...]

    @classmethod
    def parse(cls, raw):
        raw = bytes(raw)
        w.check_range(raw, 0, 20, 'NSBMD header')
        if raw[:4] != b'BMD0' or w.u32(raw, 8) != len(raw) or w.u16(raw, 14) != 1:
            raise ValueError('Expected single-block NSBMD')
        block = w.u32(raw, 16)
        w.check_range(raw, block, 8, 'MDL0 header')
        if raw[block:block + 4] != b'MDL0' or block + w.u32(raw, block + 4) != len(raw):
            raise ValueError('Invalid MDL0 bounds')
        models = dictionary(raw, block + 8, 4)
        if len(models) != 1: raise ValueError('Expected one model')
        model = block + w.u32(models[0][1], 0)
        w.check_range(raw, model, 64, 'model header')
        if model + w.u32(raw, model) != len(raw): raise ValueError('Unsupported model placement')
        shape_base = model + w.u32(raw, model + 12)
        rows = dictionary(raw, shape_base, 4)
        if len(rows) != raw[model + 25]: raise ValueError('Shape count mismatch')
        shapes = []
        for name, entry in rows:
            header = shape_base + w.u32(entry, 0)
            w.check_range(raw, header, 16, 'shape header')
            if w.u16(raw, header + 2) != 16: raise ValueError('Unexpected shape header size')
            start, length = header + w.u32(raw, header + 8), w.u32(raw, header + 12)
            w.check_range(raw, start, length, 'shape commands')
            if start % 4 or length % 4: raise ValueError('Unaligned shape commands')
            shapes.append(Shape(name, header, start, length))
        return cls(raw, block, model, tuple(shapes))

    def to_bytes(self): return self.raw

    def replace_streams(self, streams, *, vertices, quads):
        if len(streams) != len(self.shapes): raise ValueError('Shape stream count mismatch')
        if not 0 <= vertices <= 65535 or not 0 <= quads <= 65535:
            raise ValueError('Geometry count overflow')
        if all(bytes(s) == self.raw[sh.start:sh.start + sh.length] for s, sh in zip(streams, self.shapes)):
            return self.raw
        out = bytearray(self.raw)
        for stream, shape in zip(streams, self.shapes):
            if not stream or len(stream) % 4: raise ValueError('Invalid GPU stream alignment')
            at = len(out)
            out.extend(stream)
            struct.pack_into('<2I', out, shape.header + 8, at - shape.header, len(stream))
        struct.pack_into('<I', out, 8, len(out))
        struct.pack_into('<I', out, self.block + 4, len(out) - self.block)
        struct.pack_into('<I', out, self.model, len(out) - self.model)
        struct.pack_into('<4H', out, self.model + 36, vertices, quads, 0, quads)
        self.parse(out)
        return bytes(out)


def quads_stream(faces):
    """Author flat-colour quads in game units for the test model's 64x scale.

    Each face is (RGB555, four XYZ vertices). This does not author collision.
    """
    commands = [(0x40, (1,))]  # quads
    for colour, vertices in faces:
        if type(colour) is not int or not 0 <= colour < 32768 or len(vertices) != 4:
            raise ValueError('Invalid coloured quad')
        commands.extend([(0x20, (colour,)), (0x22, (0,))])
        for vertex in vertices:
            if len(vertex) != 3: raise ValueError('Expected XYZ vertex')
            values = [round(x * 64) for x in vertex]
            if any(not -32768 <= x < 32768 for x in values): raise ValueError('Vertex exceeds fixed-point range')
            x, y, z = values
            commands.append((0x23, ((x & 65535) | (y & 65535) << 16, z & 65535)))
    commands.append((0x41, ()))
    commands += [(0, ())] * (-len(commands) % 4)
    stream = bytearray()
    for at in range(0, len(commands), 4):
        group = commands[at:at + 4]
        stream.extend(bytes(op for op, _ in group))
        for _, params in group:
            stream.extend(struct.pack(f'<{len(params)}I', *params))
    return bytes(stream)


def box(x0, y0, z0, x1, y1, z1, colour):
    if not x0 < x1 or not y0 < y1 or not z0 < z1: raise ValueError('Invalid box bounds')
    a, b, c, d = (x0,y0,z0), (x1,y0,z0), (x1,y1,z0), (x0,y1,z0)
    e, f, g, h = (x0,y0,z1), (x1,y0,z1), (x1,y1,z1), (x0,y1,z1)
    return [(colour, vertices) for vertices in ((a,d,c,b), (e,f,g,h), (a,e,h,d), (b,c,g,f), (d,h,g,c), (a,b,f,e))]


def platform_model(template):
    """Authored geometry proof: flat 180-unit platform and decorative back wall.

    Back-plane columns/benches stay away from the player collision plane. This
    is a development shell, not the finished station's visual art.
    """
    model = ModelGeometry.parse(template)
    if len(model.shapes) != 2 or w.u32(template, model.model + 28) != 64 * 4096:
        raise ValueError('Expected two-shape 64x test-room template')
    background = box(0,-3,-10,180,0,10,0x4210)
    background += box(0,0,-12,180,60,-10,0x18A5)
    decorations = []
    for x in (16,52,88,124,160):
        decorations += box(x,0,-10,x+3,48,-7,0x318C)
        decorations += box(x-1,46,-10,x+4,49,-7,0x03DF)
    decorations += box(38,10,-10,70,12,-7,0x14B6)  # bench
    decorations += box(104,32,-10,145,40,-8,0x03DF)  # sign placeholder
    decorations += box(4,0,-1,6,1,1,0x03DF)
    faces = (background, decorations)
    count = sum(map(len, faces))
    return model.replace_streams([quads_stream(f) for f in faces], vertices=count * 4, quads=count)
