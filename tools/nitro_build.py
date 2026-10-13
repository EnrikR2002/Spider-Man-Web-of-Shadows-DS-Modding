"""Writers for the Nitro files a room needs: name dictionaries, texture archives and one-node room models.

Every writer is checked against the game's own files: parsing a native file
into the parts below and building it again gives the same bytes (tests; all
room texture archives and room models). Layouts follow
https://github.com/scurest/nsbmd_docs and the native rooms; fields this
module does not interpret are carried as given (material records, node data).
See TECHNICAL "Room compiler".
"""
from __future__ import annotations
from dataclasses import dataclass, field
import struct

from tools import wos_tool as w
from tools.nitro_texture import dictionary

NAME = 16
BPP = {1: 8, 2: 2, 3: 4, 4: 8, 5: 2, 6: 8, 7: 16}          # bits per texel by texture format


def _name(text):
    raw = text.encode('ascii')
    if not raw or len(raw) > NAME: raise ValueError(f'Nitro name must be 1..16 ASCII bytes: {text!r}')
    return raw.ljust(NAME, b'\0')


def _bit(name, bit): return name[bit >> 3] >> (bit & 7) & 1


def patricia(names):
    """Search-tree nodes of a Nitro dictionary: (ref bit, left, right, entry) for the root and each name."""
    keys = [_name(n) for n in names]
    if len(set(keys)) != len(keys): raise ValueError('Duplicate Nitro dictionary names')
    nodes = [{'ref': 127, 'left': 0, 'right': 0, 'idx': 0, 'key': bytes(NAME)}]
    for index, key in enumerate(keys):
        current, below = nodes[0], nodes[nodes[0]['left']]
        while current['ref'] > below['ref']:
            current, below = below, nodes[below['right'] if _bit(key, below['ref']) else below['left']]
        bit = 127
        while _bit(below['key'], bit) == _bit(key, bit): bit -= 1
        current, at = nodes[0], nodes[0]['left']
        below = nodes[at]
        while current['ref'] > below['ref'] > bit:
            current = below
            at = below['right'] if _bit(key, below['ref']) else below['left']
            below = nodes[at]
        new = len(nodes)
        node = {'ref': bit, 'left': at if _bit(key, bit) else new, 'right': new if _bit(key, bit) else at,
                'idx': index, 'key': key}
        if current is nodes[0] or not _bit(key, current['ref']): current['left'] = new
        else: current['right'] = new
        nodes.append(node)
    # Native files number the nodes in preorder (left child first), not in insertion order.
    order, stack = [0], [nodes[0]['left']] if nodes[0]['left'] else []
    parent_ref = {nodes[0]['left']: 127}
    while stack:
        at = stack.pop()
        order.append(at)
        for child in (nodes[at]['right'], nodes[at]['left']):
            if nodes[child]['ref'] < nodes[at]['ref']: stack.append(child)
    if len(order) != len(nodes): raise ValueError('Dictionary tree is not connected')
    number = {old: new for new, old in enumerate(order)}
    return [(nodes[o]['ref'], number[nodes[o]['left']], number[nodes[o]['right']], nodes[o]['idx']) for o in order]


def dictionary_bytes(rows):
    """Nitro dictionary of (name, entry bytes) rows; every entry has the same size."""
    rows = list(rows)
    if not rows or len(rows) > 255: raise ValueError('Nitro dictionary needs 1..255 entries')
    unit = len(rows[0][1])
    if any(len(entry) != unit for _, entry in rows): raise ValueError('Dictionary entries differ in size')
    count = len(rows)
    nodes = b''.join(bytes(n) for n in patricia([name for name, _ in rows]))
    body = (nodes + struct.pack('<2H', unit, 4 + count * unit) + b''.join(entry for _, entry in rows)
            + b''.join(_name(name) for name, _ in rows))
    return struct.pack('<2B3H', 0, count, 8 + len(body), 8, 12 + count * 4) + body


# --- texture archives ----------------------------------------------------------
@dataclass(frozen=True)
class Texture:
    name: str
    width: int
    height: int
    format: int
    data: bytes
    index: bytes = b''              # format 5 only: one u16 per 4x4 block
    flags: int = 0                  # texture parameter bits outside size and format (bit 13: colour 0 transparent)
    extra: int = 0x80000000         # high bits of the second dictionary word (native: bit 31 set)


@dataclass(frozen=True)
class Palette:
    name: str
    data: bytes
    flag: int = 0                   # native: 1 on some four-colour palettes


def _size_bits(value):
    bits = value.bit_length() - 4
    if value < 8 or value > 1024 or value != 8 << bits: raise ValueError('Texture sides are powers of two from 8 to 1024')
    return bits


def texture_archive(textures, palettes):
    """NSBTX holding the textures and palettes in the given order (pools laid out as in native files)."""
    plain, packed, indices, rows = bytearray(), bytearray(), bytearray(), []
    for t in textures:
        size = t.width * t.height * BPP[t.format] // 8
        if len(t.data) != size: raise ValueError(f'{t.name}: texture data is {len(t.data)} bytes, expected {size}')
        if t.flags & 0x1FF0: raise ValueError(f'{t.name}: flags overlap size or format')
        pool = packed if t.format == 5 else plain
        if len(pool) % 8: raise ValueError('Texture pool lost its 8-byte grid')
        if t.format == 5:
            if len(t.index) != size // 2: raise ValueError(f'{t.name}: index data is {len(t.index)} bytes')
            indices += t.index
        elif t.index: raise ValueError(f'{t.name}: only format 5 has index data')
        params = t.flags | _size_bits(t.width) << 4 | _size_bits(t.height) << 7 | t.format << 10
        rows.append((t.name, struct.pack('<2HI', len(pool) // 8, params, t.extra | t.width | t.height << 11)))
        pool += t.data
        pool += bytes(-len(pool) % 8)
    colours, pal_rows = bytearray(), []
    for p in palettes:
        if not p.data or len(p.data) % 2: raise ValueError(f'{p.name}: palette needs whole colours')
        pal_rows.append((p.name, struct.pack('<2H', len(colours) // 8, p.flag)))
        colours += p.data
        colours += bytes(-len(colours) % 8)
    tex_dict, pal_dict = dictionary_bytes(rows), dictionary_bytes(pal_rows)
    tex_at = 0x3C
    pal_at = tex_at + len(tex_dict)
    plain_at = pal_at + len(pal_dict)
    packed_at = plain_at + len(plain)
    index_at = packed_at + len(packed)
    colours_at = index_at + len(indices)
    size = colours_at + len(colours)
    if max(len(plain), len(packed), len(colours)) >> 3 > 0xFFFF: raise ValueError('Texture pool too large')
    block = (b'TEX0' + struct.pack('<2I2H2I', size, 0, len(plain) >> 3, tex_at, 0, plain_at)
             + struct.pack('<I2H3I', 0, len(packed) >> 3, tex_at, 0, packed_at, index_at)
             + struct.pack('<4I', 0, len(colours) >> 3, pal_at, colours_at)
             + tex_dict + pal_dict + plain + packed + indices + colours)
    if len(block) != size: raise ValueError('TEX0 size mismatch')
    return b'BTX0' + struct.pack('<2HI2HI', 0xFEFF, 1, 20 + size, 16, 1, 20) + block


def archive_parts(raw):
    """(textures, palettes) of a native NSBTX, for texture_archive and for borrowing single textures."""
    from tools.nitro_texture import TextureArchive
    archive = TextureArchive.parse(raw)
    block = raw[archive.tex0_start:]
    index_at = archive.tex0_start + w.u32(block, 0x28)
    packed_at = archive.tex0_start + w.u32(block, 0x24)
    textures = []
    for t in archive.textures:
        data = raw[t['offset']:t['offset'] + t['size']]
        index = b''
        if t['format'] == 5:
            at = index_at + (t['offset'] - packed_at) // 2
            index = raw[at:at + t['size'] // 2]
        textures.append(Texture(t['name'], t['width'], t['height'], t['format'], data, index,
                                t['params'] & ~0x1FF0 & 0xFFFF, t['unknown_u32'] & ~0x3FFFFF))
    palettes = [Palette(p['name'], raw[p['offset']:p['offset'] + p['size']], p['unknown_u16']) for p in archive.palettes]
    return textures, palettes


# --- room models ---------------------------------------------------------------
@dataclass(frozen=True)
class Material:
    name: str
    texture: str | None             # texture and palette names the engine binds at load
    palette: str | None
    record: bytes                   # the 44-byte material record (see material_record)


@dataclass(frozen=True)
class RoomModel:
    name: str
    node: str
    node_data: bytes
    materials: tuple
    streams: tuple                  # GPU command stream of each shape
    draw: tuple                     # (material, shape) pairs in drawing order
    scale: int                      # vertex scale, Q12
    counts: tuple                   # vertices, polygons, triangles, quads
    box: tuple                      # x, y, z, width, height, depth (s16, in box-scale units)
    box_scale: int
    shape_flags: tuple = ()
    shape_names: tuple = ()
    info: bytes = bytes((0, 0, 0, 1))   # SBC type, scaling rule, texture matrix mode, node count
    tail: bytes = bytes((1, 0))         # first unused matrix stack id, padding


def material_record(width, height, *, polygon=0x001F0080, diffuse_ambient=0x0000E739, texture_param=0x00030000):
    """44-byte material as in native rooms: vertex colours, both repeats on, front faces only."""
    return struct.pack('<2H6I4H2I', 0, 44, diffuse_ambient, 0, polygon, 0x3F1FF8FF, texture_param, 0xFFFFFFFF,
                       0, 0x1FCE, width, height, 0x1000, 0x1000)


def _pairs(materials, key):
    """Dictionary rows and index bytes binding each texture (or palette) name to the materials using it."""
    names = sorted({getattr(m, key) for m in materials if getattr(m, key)})
    lists = [bytes(i for i, m in enumerate(materials) if getattr(m, key) == name) for name in names]
    return names, lists


def room_model(model):
    """NSBMD with one model and one node whose shapes are drawn with the given materials."""
    m = model
    count = len(m.streams)
    flags = m.shape_flags or (6,) * count
    shape_names = m.shape_names or tuple(f'polygon{i}' for i in range(count))
    if not m.materials or not count or len(flags) != count or len(shape_names) != count:
        raise ValueError('Room model needs materials and shapes')
    if any(not 0 <= a < len(m.materials) or not 0 <= b < count for a, b in m.draw):
        raise ValueError('Draw list names a missing material or shape')
    if len(m.materials) > 255 or count > 255: raise ValueError('Too many materials or shapes')
    node_dict = dictionary_bytes([(m.node, struct.pack('<I', 0))])
    node_dict = dictionary_bytes([(m.node, struct.pack('<I', len(node_dict)))])
    nodes = node_dict + m.node_data
    sbc = bytes((0x26, 0, 0, 0, 0, 0x02, 0, 1, 0x0B)) + b''.join(bytes((0x04, a, 0x05, b)) for a, b in m.draw) + bytes((0x2B, 0x01))
    sbc += bytes(-len(sbc) % 4)
    # Materials: pair dictionaries, material dictionary, index lists, records.
    tex_names, tex_lists = _pairs(m.materials, 'texture')
    pal_names, pal_lists = _pairs(m.materials, 'palette')
    mat_dict_size = len(dictionary_bytes([(x.name, bytes(4)) for x in m.materials]))
    tex_at = 4 + mat_dict_size
    tex_size = len(dictionary_bytes([(n, bytes(4)) for n in tex_names])) if tex_names else 0
    pal_at = tex_at + tex_size
    pal_size = len(dictionary_bytes([(n, bytes(4)) for n in pal_names])) if pal_names else 0
    lists_at = pal_at + pal_size
    at, tex_rows, pal_rows, lists = lists_at, [], [], b''
    for names, groups, rows in ((tex_names, tex_lists, tex_rows), (pal_names, pal_lists, pal_rows)):
        for name, group in zip(names, groups):
            rows.append((name, struct.pack('<H2B', at, len(group), 0)))
            at += len(group)
            lists += group
    lists += bytes(-len(lists) % 4)
    records_at = lists_at + len(lists)
    offsets, records = [], b''
    for x in m.materials:
        if len(x.record) != w.u16(x.record, 2) or len(x.record) % 4: raise ValueError(f'{x.name}: material record size')
        offsets.append(records_at + len(records))
        records += x.record
    materials = (struct.pack('<2H', tex_at if tex_names else 0, pal_at if pal_names else 0)
                 + dictionary_bytes([(x.name, struct.pack('<I', o)) for x, o in zip(m.materials, offsets)])
                 + (dictionary_bytes(tex_rows) if tex_rows else b'') + (dictionary_bytes(pal_rows) if pal_rows else b'')
                 + lists + records)
    # Shapes: dictionary, 16-byte headers, command streams.
    shape_dict_size = len(dictionary_bytes([(n, bytes(4)) for n in shape_names]))
    headers_at = shape_dict_size
    streams_at = headers_at + 16 * count
    headers, body = b'', b''
    for i, (stream, flag) in enumerate(zip(m.streams, flags)):
        if not stream or len(stream) % 4: raise ValueError('GPU stream must be whole words')
        header_at = headers_at + 16 * i
        headers += struct.pack('<2H3I', 0, 16, flag, streams_at + len(body) - header_at, len(stream))
        body += stream
    shapes = dictionary_bytes([(n, struct.pack('<I', headers_at + 16 * i)) for i, n in enumerate(shape_names)]) + headers + body
    sbc_at = 64 + len(nodes)
    materials_at = sbc_at + len(sbc)
    shapes_at = materials_at + len(materials)
    size = shapes_at + len(shapes)
    inverse = 1 if m.scale == 4096 else round(4096 * 4096 / m.scale)
    box_inverse = 1 if m.box_scale == 4096 else round(4096 * 4096 / m.box_scale)
    header = (struct.pack('<5I', size, sbc_at, materials_at, shapes_at, size) + m.info
              + bytes((len(m.materials), count)) + m.tail + struct.pack('<2i4H6h2i', m.scale, inverse, *m.counts, *m.box,
                                                                        m.box_scale, box_inverse))
    body = header + nodes + sbc + materials + shapes
    if len(header) != 64 or len(body) != size: raise ValueError('Model layout mismatch')
    model_dict = dictionary_bytes([(m.name, struct.pack('<I', 0))])
    model_dict = dictionary_bytes([(m.name, struct.pack('<I', 8 + len(model_dict)))])
    block = b'MDL0' + struct.pack('<I', 8 + len(model_dict) + size) + model_dict + body
    return b'BMD0' + struct.pack('<2HI2HI', 0xFEFF, 2, 20 + len(block), 16, 1, 20) + block


def model_parts(raw):
    """RoomModel of a native one-node room model (for room_model and as a pattern for authored rooms)."""
    from tools.model_geometry import ModelGeometry
    g = ModelGeometry.parse(raw)
    block, m = g.block, g.model
    name = dictionary(raw, block + 8, 4)[0][0]
    if raw[m + 23] != 1: raise ValueError('Expected a one-node model')
    node_name, node_entry = dictionary(raw, m + 64, 4)[0]
    sbc_at, mat_at, shp_at = m + w.u32(raw, m + 4), m + w.u32(raw, m + 8), m + w.u32(raw, m + 12)
    node_at = m + 64 + w.u32(node_entry, 0)
    node_data = raw[node_at:sbc_at]
    sbc = raw[sbc_at:mat_at]
    if sbc[:9] != bytes((0x26, 0, 0, 0, 0, 0x02, 0, 1, 0x0B)): raise ValueError('Unexpected SBC prologue')
    draw, at = [], 9
    while sbc[at] == 0x04:
        if sbc[at + 2] != 0x05: raise ValueError('Unexpected SBC command')
        draw.append((sbc[at + 1], sbc[at + 3])); at += 4
    if sbc[at:at + 2] != bytes((0x2B, 0x01)) or any(sbc[at + 2:]): raise ValueError('Unexpected SBC epilogue')
    rows = dictionary(raw, mat_at + 4, 4)
    bound = {}
    for key, off in (('texture', w.u16(raw, mat_at)), ('palette', w.u16(raw, mat_at + 2))):
        if not off: continue
        for pair_name, entry in dictionary(raw, mat_at + off, 4):
            o, n, flag = struct.unpack('<H2B', entry)
            if flag: raise ValueError('Bound flag set in a stored model')
            for index in raw[mat_at + o:mat_at + o + n]: bound[(key, index)] = pair_name
    materials = []
    for i, (mat_name, entry) in enumerate(rows):
        at = mat_at + w.u32(entry, 0)
        materials.append(Material(mat_name, bound.get(('texture', i)), bound.get(('palette', i)), raw[at:at + w.u16(raw, at + 2)]))
    streams = tuple(raw[s.start:s.start + s.length] for s in g.shapes)
    flags = tuple(w.u32(raw, s.header + 4) for s in g.shapes)
    return RoomModel(name, node_name, node_data, tuple(materials), streams, tuple(draw), struct.unpack_from('<i', raw, m + 28)[0],
                     struct.unpack_from('<4H', raw, m + 36), struct.unpack_from('<6h', raw, m + 44),
                     struct.unpack_from('<i', raw, m + 56)[0], flags, tuple(s.name for s in g.shapes),
                     raw[m + 20:m + 24], raw[m + 26:m + 28])
