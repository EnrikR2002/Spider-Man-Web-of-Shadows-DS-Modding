"""Blender bridge: export a native character model to glTF, import an edited glTF onto it.

Scope, checked and refused otherwise: a one-model NSBMD with one shape, one
material, unscaled bind nodes, no weighted SBC skin (op 0x09) and an SBC matrix
restore before its shape. That is the player and most characters/enemies. Each
vertex follows one bone through a native stored matrix (GPU MTX_RESTORE 0x14);
glTF weights collapse to the largest joint, and a joint without a stored matrix
falls back to its nearest ancestor that has one. The import keeps the template's
rig, SBC, material and all other bytes. It appends one triangle list, points the
shape at it (`model_geometry.replace_streams`), sets the header counts and only
grows the model box. Textures in format 3 (I4), 4 (I8) or 7 (direct) keep the
template's names, format and flags; a new image size changes the material size.
Joint names must match the template. New bones, rigs, weights and animation are
out of scope.

  export MODEL TEXTURE OUT.glb        clean-ROM names, e.g. spd.nsbmd spd.nsbtx
  import IN.glb MODEL TEXTURE OUTDIR  writes OUTDIR/MODEL, OUTDIR/TEXTURE, report.json
  rom OUTDIR OUT.nds                  research ROM: clean ROM plus OUTDIR's resources

Outputs are private copyrighted derivatives: write them under build/ or work/.
In Blender use File > Import/Export > glTF 2.0 (.glb). Keep the armature at the
origin and keep bone names. See DEVELOPMENT "Blender model bridge".
"""
from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import nitro_build as nb  # noqa: E402
from tools import wos_tool as w  # noqa: E402
from tools.animation_rig import AnimationRig  # noqa: E402
from tools.crane_creature_art import packets  # noqa: E402
from tools.model_geometry import ModelGeometry  # noqa: E402
from tools.nitro_texture import dictionary  # noqa: E402
from tools.spider2099_art import bind_transforms, gpu_commands  # noqa: E402

COLOURS = {3: 16, 4: 256}           # palette formats the bridge writes; 7 is direct RGB555
UNSUPPORTED_GPU = {0x1B, 0x20, 0x21}  # scale, colour and normal never occur in bridged models


def _signed(value, bits):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value >> (bits - 1) else value


def _inverse(m):
    (a, b, c), (d, e, f), (g, h, i) = m
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-9: raise ValueError('Singular bind rotation')
    return ((( e * i - f * h) / det, -(b * i - c * h) / det, ( b * f - c * e) / det),
            (-(d * i - f * g) / det, ( a * i - c * g) / det, -(a * f - c * d) / det),
            (( d * h - e * g) / det, -(a * h - b * g) / det, ( a * e - b * d) / det))


def _mv(m, v): return tuple(sum(m[r][k] * v[k] for k in range(3)) for r in range(3))


# --- native model ---------------------------------------------------------------
def material(raw):
    """(record offset, width, height) of the single material; width/height define UV space."""
    g = ModelGeometry.parse(raw)
    mats = g.model + w.u32(raw, g.model + 8)
    rows = dictionary(raw, mats + 4, 4)
    if len(rows) != 1: raise ValueError('The bridge needs a model with one material')
    at = mats + w.u32(rows[0][1], 0)
    return (at, *struct.unpack_from('<2H', raw, at + 32))


def bound_names(raw):
    """(texture names, palette names) the model binds by name at load."""
    g = ModelGeometry.parse(raw)
    mats = g.model + w.u32(raw, g.model + 8)
    return ([n for n, _ in dictionary(raw, mats + w.u16(raw, mats), 4)],
            [n for n, _ in dictionary(raw, mats + w.u16(raw, mats + 2), 4)])


def template(raw):
    """Checked native bind data: (geometry, rig, rotations, positions, {slot: joint}, start slot)."""
    g = ModelGeometry.parse(raw)
    if len(g.shapes) != 1: raise ValueError('The bridge needs a model with one shape')
    material(raw)
    rig, rotations, positions, slots = bind_transforms(raw)   # raises on scaled bind nodes
    start = None
    for _, op, args in rig.node_records:
        if op == 9: raise ValueError('Weighted SBC skins are outside the bridge')
        if op == 5: break
        if op == 3: start = args[0]
    if start not in slots: raise ValueError('Expected a stored-matrix restore before the shape')
    return g, rig, rotations, positions, slots, start


def triangles(raw):
    """Native faces: triangles of (slot, (x, y, z) Q12 bone-local, (s, t) 1/16 texel); CCW outward."""
    *_, slots, start = template(raw)
    slot, st, xyz, mode, pending, faces = start, (0, 0), [0, 0, 0], None, [], []
    for op, args in gpu_commands(raw):
        if op in UNSUPPORTED_GPU: raise ValueError(f'GPU command {op:#x} is outside the bridge')
        if op == 0x14: slot = args[0]
        elif op == 0x22: st = (_signed(args[0], 16), _signed(args[0] >> 16, 16))
        elif op == 0x40: mode, pending = args[0], []
        elif op == 0x41: mode, pending = None, []
        elif 0x23 <= op <= 0x28:
            a = args[0]
            if op == 0x23: xyz = [_signed(a, 16), _signed(a >> 16, 16), _signed(args[1], 16)]
            elif op == 0x24: xyz = [_signed(a >> 10 * i, 10) * 64 for i in range(3)]
            elif op == 0x28: xyz = [xyz[i] + _signed(a >> 10 * i, 10) for i in range(3)]
            else:
                for i, axis in enumerate({0x25: (0, 1), 0x26: (0, 2), 0x27: (1, 2)}[op]):
                    xyz[axis] = _signed(a >> 16 * i, 16)
            if slot not in slots or mode not in (0, 1, 2, 3):
                raise ValueError('Vertex outside a stored matrix or primitive')
            pending.append((slot, tuple(xyz), st))
            n = len(pending)
            if mode == 0 and n % 3 == 0: faces.append(tuple(pending[-3:]))
            elif mode == 1 and n % 4 == 0:
                a_, b, c, d = pending[-4:]
                faces += [(a_, b, c), (a_, c, d)]
            elif mode == 2 and n >= 3:
                a_, b, c = pending[-3:]
                faces.append((a_, b, c) if n % 2 else (b, a_, c))
            elif mode == 3 and n >= 4 and n % 2 == 0:
                a_, b, c, d = pending[-4:]
                faces += [(a_, b, d), (a_, d, c)]
    return faces


def stream(faces, start):
    """One triangle list; matrix restores and texcoords only when they change."""
    commands, slot, last = [(0x40, (0,))], start, None
    for face in faces:
        for s, (x, y, z), st in face:
            if any(not -32768 <= v <= 32767 for v in (x, y, z, *st)):
                raise ValueError('Vertex or texcoord outside the native 16-bit range')
            if s != slot: commands.append((0x14, (s,))); slot = s
            if st != last: commands.append((0x22, ((st[0] & 0xFFFF) | (st[1] & 0xFFFF) << 16,))); last = st
            commands.append((0x23, ((x & 0xFFFF) | (y & 0xFFFF) << 16, z & 0xFFFF)))
    return packets(commands + [(0x41, ())])


def world(rotations, positions, slots, vertex):
    slot, xyz, _ = vertex
    j = slots[slot]
    p = _mv(rotations[j], tuple(v / 4096 for v in xyz))
    return tuple(positions[j][k] + p[k] for k in range(3))


def write_model(raw, faces, size=None):
    """Template bytes with `faces` as its only drawn list; returns (model, report)."""
    g, rig, rotations, positions, slots, start = template(raw)
    if not faces or len(faces) * 3 > 65535: raise ValueError('Triangle count outside the header range')
    out = bytearray(g.replace_streams([stream(faces, start)], vertices=0, quads=0))
    struct.pack_into('<4H', out, g.model + 36, len(faces) * 3, len(faces), len(faces), 0)
    scale = w.u32(raw, g.model + 56) / 4096
    low = list(struct.unpack_from('<3h', raw, g.model + 44))
    high = [low[k] + w.u16(raw, g.model + 50 + 2 * k) for k in range(3)]
    points = [world(rotations, positions, slots, v) for face in faces for v in face]
    low = [min(low[k], math.floor(min(p[k] for p in points) / scale * 4096) - 2) for k in range(3)]
    high = [max(high[k], math.ceil(max(p[k] for p in points) / scale * 4096) + 2) for k in range(3)]
    if any(not -32768 <= v <= 32767 for v in low) or any(not 0 <= high[k] - low[k] <= 65535 for k in range(3)):
        raise ValueError('Model box outside its native field range')
    struct.pack_into('<3h3H', out, g.model + 44, *low, *(high[k] - low[k] for k in range(3)))
    if size: struct.pack_into('<2H', out, material(raw)[0] + 32, *size)
    out = bytes(out)
    check = AnimationRig.parse(out)
    if (check.parents, check.node_records) != (rig.parents, rig.node_records): raise ValueError('Bridge changed the rig/SBC')
    if triangles(out) != list(faces): raise ValueError('Written stream does not decode to the imported faces')
    return out, {'triangles': len(faces), 'native_header_counts': list(struct.unpack_from('<4H', raw, g.model + 36)),
                 'stream_bytes': len(out) - len(raw), 'model_bytes': [len(raw), len(out)]}


# --- textures -------------------------------------------------------------------
def _rgb(c): return tuple((c >> s & 31) * 255 // 31 for s in (0, 5, 10))


def _parts(tex_raw, model_raw):
    names, palettes = bound_names(model_raw)
    textures, pals = nb.archive_parts(tex_raw)
    match = [t for t in textures if t.name in names]
    if len(match) != 1: raise ValueError(f'Expected one bound texture in the archive, found {len(match)}')
    t = match[0]
    if t.format not in (3, 4, 7): raise ValueError(f'Texture format {t.format} is outside the bridge (I4, I8, direct)')
    pal = None
    if t.format != 7:
        pal = next((p for p in pals if p.name in palettes), None)
        if pal is None: raise ValueError('Palette bound by the model is missing')
    return textures, pals, t, pal


def decode_texture(tex_raw, model_raw):
    """(width, height, RGBA bytes) of the model's bound texture."""
    _, _, t, pal = _parts(tex_raw, model_raw)
    n = t.width * t.height
    if t.format == 7:
        colours = struct.unpack_from(f'<{n}H', t.data)
        return t.width, t.height, b''.join(bytes(_rgb(c)) + (b'\xff' if c & 0x8000 else b'\0') for c in colours)
    table = struct.unpack_from(f'<{len(pal.data) // 2}H', pal.data)
    index = list(t.data) if t.format == 4 else [b >> s & 15 for b in t.data for s in (0, 4)]
    clear = t.flags & 0x2000
    return t.width, t.height, b''.join(bytes(_rgb(table[i])) + (b'\0' if clear and i == 0 else b'\xff') for i in index)


def encode_texture(tex_raw, model_raw, width, height, rgba):
    """Template archive with the bound texture redrawn from RGBA; unchanged pixels keep the bytes."""
    if decode_texture(tex_raw, model_raw) == (width, height, rgba): return tex_raw
    from PIL import Image
    textures, pals, t, pal = _parts(tex_raw, model_raw)
    nb._size_bits(width); nb._size_bits(height)
    pixels = [rgba[i:i + 4] for i in range(0, len(rgba), 4)]
    if t.format == 7:
        data = b''.join(struct.pack('<H', (p[0] >> 3) | (p[1] >> 3) << 5 | (p[2] >> 3) << 10 | (0x8000 if p[3] >= 128 else 0))
                        for p in pixels)
        new_pal = pal
    else:
        clear = bool(t.flags & 0x2000)
        rgb = Image.frombytes('RGB', (width, height), b''.join(p[:3] for p in pixels))
        q = rgb.quantize(COLOURS[t.format] - clear, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        index = [i + clear for i in q.tobytes()]
        if clear: index = [0 if p[3] < 128 else i for p, i in zip(pixels, index)]
        colours = q.getpalette()[:3 * (max(index) + 1 - clear)]
        table = [0] * clear + [(colours[k] >> 3) | (colours[k + 1] >> 3) << 5 | (colours[k + 2] >> 3) << 10
                               for k in range(0, len(colours), 3)]
        table += [0] * (COLOURS[t.format] - len(table))
        data = bytes(index) if t.format == 4 else bytes(index[k] | index[k + 1] << 4 for k in range(0, len(index), 2))
        new_pal = nb.Palette(pal.name, struct.pack(f'<{len(table)}H', *table), pal.flag)
    new = nb.Texture(t.name, width, height, t.format, data, b'', t.flags, t.extra)
    return nb.texture_archive([new if x is t else x for x in textures], [new_pal if x is pal else x for x in pals])


# --- glTF -----------------------------------------------------------------------
def _glb(document, binary):
    body = json.dumps(document, separators=(',', ':')).encode()
    body += b' ' * (-len(body) % 4)
    binary += bytes(-len(binary) % 4)
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(body) + len(binary)) + struct.pack('<I4s', len(body), b'JSON')
            + body + struct.pack('<I4s', len(binary), b'BIN\0') + binary)


def export_glb(model_raw, tex_raw, name):
    """glTF 2.0 binary: bind-pose mesh skinned rigidly to the native joints, plus the texture as PNG."""
    from PIL import Image
    _, rig, rotations, positions, slots, _ = template(model_raw)
    _, mw, mh = material(model_raw)
    faces = [f for f in triangles(model_raw) if len(set(f)) == 3]    # index-degenerate strip joins draw nothing
    keys, index = {}, []
    for face in faces:
        for v in face: index.append(keys.setdefault(v, len(keys)))
    verts = list(keys)
    pos = [world(rotations, positions, slots, v) for v in verts]
    uv = [(st[0] / 16 / mw, st[1] / 16 / mh) for _, _, st in verts]
    joints = [slots[s] for s, _, _ in verts]
    tw, th, rgba = decode_texture(tex_raw, model_raw)
    if (tw, th) != (mw, mh): raise ValueError(f'Material declares {mw}x{mh} but the texture is {tw}x{th}')
    png = io.BytesIO()
    Image.frombytes('RGBA', (tw, th), rgba).save(png, 'PNG')
    n = len(rig.names)
    blobs = [b''.join(struct.pack('<3f', *p) for p in pos), b''.join(struct.pack('<2f', *t) for t in uv),
             b''.join(struct.pack('<4B', j, 0, 0, 0) for j in joints), struct.pack('<4f', 1, 0, 0, 0) * len(verts),
             struct.pack(f'<{len(index)}{"H" if len(verts) < 65536 else "I"}', *index),
             b''.join(struct.pack('<16f', 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -p[0], -p[1], -p[2], 1) for p in positions),
             png.getvalue()]
    binary, views = b'', []
    for blob in blobs:
        binary += bytes(-len(binary) % 4)
        views.append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(blob)})
        binary += blob
    lo = [min(p[k] for p in pos) for k in range(3)]
    hi = [max(p[k] for p in pos) for k in range(3)]
    accessors = [
        {'bufferView': 0, 'componentType': 5126, 'count': len(verts), 'type': 'VEC3', 'min': lo, 'max': hi},
        {'bufferView': 1, 'componentType': 5126, 'count': len(verts), 'type': 'VEC2'},
        {'bufferView': 2, 'componentType': 5121, 'count': len(verts), 'type': 'VEC4'},
        {'bufferView': 3, 'componentType': 5126, 'count': len(verts), 'type': 'VEC4'},
        {'bufferView': 4, 'componentType': 5123 if len(verts) < 65536 else 5125, 'count': len(index), 'type': 'SCALAR'},
        {'bufferView': 5, 'componentType': 5126, 'count': n, 'type': 'MAT4'}]
    if n > 255: raise ValueError('More than 255 joints')
    # shortcut: joints carry bind translation only (native Q12 rotations are not exactly
    # orthonormal); enough for rigid mesh editing, extend for an SCA animation bridge.
    nodes = [{'name': rig.names[j], 'translation': list(positions[j]) if rig.parents[j] is None
              else [positions[j][k] - positions[rig.parents[j]][k] for k in range(3)]} for j in range(n)]
    for j, parent in enumerate(rig.parents):
        if parent is not None: nodes[parent].setdefault('children', []).append(j)
    nodes.append({'name': Path(name).stem, 'mesh': 0, 'skin': 0})
    clear = any(rgba[k] < 128 for k in range(3, len(rgba), 4))
    document = {
        'asset': {'version': '2.0', 'generator': 'tools/model_bridge.py', 'extras': {'template': name}},
        'scene': 0, 'scenes': [{'nodes': [n] + [j for j, p in enumerate(rig.parents) if p is None]}],
        'nodes': nodes, 'skins': [{'joints': list(range(n)), 'inverseBindMatrices': 5}],
        'meshes': [{'name': Path(name).stem, 'primitives': [{
            'attributes': {'POSITION': 0, 'TEXCOORD_0': 1, 'JOINTS_0': 2, 'WEIGHTS_0': 3},
            'indices': 4, 'material': 0, 'mode': 4}]}],
        'materials': [{'name': Path(name).stem, 'alphaMode': 'MASK' if clear else 'OPAQUE',
                       'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}, 'metallicFactor': 0}}],
        'textures': [{'sampler': 0, 'source': 0}], 'samplers': [{'magFilter': 9728, 'minFilter': 9728}],
        'images': [{'bufferView': 6, 'mimeType': 'image/png'}],
        'accessors': accessors, 'bufferViews': views, 'buffers': [{'byteLength': len(binary) + (-len(binary) % 4)}]}
    return _glb(document, binary)


def read_glb(data):
    """(document, binary chunk) of a .glb file."""
    magic, version, length = struct.unpack_from('<4sII', data)
    if magic != b'glTF' or version != 2 or length != len(data): raise ValueError('Expected a glTF 2.0 .glb file')
    size, kind = struct.unpack_from('<I4s', data, 12)
    if kind != b'JSON': raise ValueError('glb lacks its JSON chunk')
    document = json.loads(data[20:20 + size])
    at = 20 + size
    binary = b''
    if at < len(data):
        size2, kind2 = struct.unpack_from('<I4s', data, at)
        if kind2 == b'BIN\0': binary = data[at + 8:at + 8 + size2]
    return document, binary


def accessor(document, binary, i):
    a = document['accessors'][i]
    if 'sparse' in a or 'bufferView' not in a: raise ValueError('Sparse or empty glTF accessors are unsupported')
    view = document['bufferViews'][a['bufferView']]
    if view.get('buffer', 0) != 0: raise ValueError('Only the glb binary buffer is supported')
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    code = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}[a['componentType']]
    size = struct.calcsize(code) * width
    stride, base = view.get('byteStride') or size, view.get('byteOffset', 0) + a.get('byteOffset', 0)
    if base + stride * (a['count'] - 1) + size > len(binary): raise ValueError('glTF accessor outside the buffer')
    rows = [struct.unpack_from('<' + code * width, binary, base + k * stride) for k in range(a['count'])]
    if a.get('normalized'):
        top = {'b': 127, 'B': 255, 'h': 32767, 'H': 65535}[code]
        rows = [tuple(max(v / top, -1.) for v in r) for r in rows]
    return rows


def _local(node):
    if 'matrix' in node:
        m = node['matrix']
        return [[m[c * 4 + r] for c in range(4)] for r in range(4)]
    x, y, z, q = *node.get('translation', (0, 0, 0)), node.get('rotation', (0, 0, 0, 1))
    sx, sy, sz = node.get('scale', (1, 1, 1))
    qx, qy, qz, qw = q
    r = [[1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
         [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
         [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]]
    return [[r[i][0] * sx, r[i][1] * sy, r[i][2] * sz, (x, y, z)[i]] for i in range(3)] + [[0, 0, 0, 1]]


def _mm(a, b): return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def globals_of(document):
    """Scene-space 4x4 matrix of every node reached from the default scene."""
    out, nodes = {}, document['nodes']

    def visit(i, parent):
        out[i] = _mm(parent, _local(nodes[i]))
        for child in nodes[i].get('children', ()): visit(child, out[i])
    identity = [[float(i == j) for j in range(4)] for i in range(4)]
    for root in document['scenes'][document.get('scene', 0)]['nodes']: visit(root, identity)
    return out


def import_glb(data, model_raw, tex_raw):
    """Edited glb -> (model bytes, texture bytes, report) on the native template."""
    from PIL import Image
    document, binary = read_glb(data)
    _, rig, rotations, positions, slots, start = template(model_raw)
    meshes = [(i, n) for i, n in enumerate(document['nodes']) if 'mesh' in n]
    if len(meshes) != 1: raise ValueError(f'Expected one mesh object, found {len(meshes)}')
    node = meshes[0][1]
    prims = document['meshes'][node['mesh']]['primitives']
    if len(prims) != 1 or prims[0].get('mode', 4) != 4: raise ValueError('Expected one triangle primitive (one material)')
    prim = prims[0]
    attrs = prim['attributes']
    for key in ('POSITION', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0'):
        if key not in attrs: raise ValueError(f'glTF mesh lacks {key}: keep the UVs and the armature modifier')
    if 'skin' not in node: raise ValueError('Mesh is not skinned to the template armature')
    skin = document['skins'][node['skin']]
    names = [document['nodes'][j].get('name') for j in skin['joints']]
    unknown = sorted({n for n in names if n not in rig.names}, key=str)
    if unknown: raise ValueError(f'Joints not in the template rig: {unknown}')
    world_of = globals_of(document)
    ibm = accessor(document, binary, skin['inverseBindMatrices']) if 'inverseBindMatrices' in skin else [None] * len(names)
    skinning = []
    for j, node_index in enumerate(skin['joints']):
        inv = [[1. if r == c else 0. for c in range(4)] for r in range(4)] if ibm[j] is None else \
            [[ibm[j][c * 4 + r] for c in range(4)] for r in range(4)]
        skinning.append(_mm(world_of[node_index], inv))
    stored = {j: s for s, j in sorted(slots.items(), reverse=True)}

    def slot_of(name):                       # nearest ancestor with a stored matrix
        k = rig.names.index(name)
        while k is not None and k not in stored: k = rig.parents[k]
        if k is None: raise ValueError(f'Vertices bound to {name}, which has no stored-matrix ancestor')
        return stored[k]
    pos, uv = accessor(document, binary, attrs['POSITION']), accessor(document, binary, attrs['TEXCOORD_0'])
    jnt, wgt = accessor(document, binary, attrs['JOINTS_0']), accessor(document, binary, attrs['WEIGHTS_0'])
    idx = [r[0] for r in accessor(document, binary, prim['indices'])] if 'indices' in prim else list(range(len(pos)))
    if len(idx) % 3: raise ValueError('Triangle index count is not a multiple of three')
    # Texture: the glb's base-colour image, else the template's.
    tw, th = material(model_raw)[1:]
    texture, size = tex_raw, None
    material_index = prim.get('material')
    image = None
    if material_index is not None:
        info = document['materials'][material_index].get('pbrMetallicRoughness', {}).get('baseColorTexture')
        if info is not None: image = document['images'][document['textures'][info['index']]['source']]
    if image is not None:
        view = document['bufferViews'][image['bufferView']]
        start_at = view.get('byteOffset', 0)
        picture = Image.open(io.BytesIO(binary[start_at:start_at + view['byteLength']])).convert('RGBA')
        texture = encode_texture(tex_raw, model_raw, *picture.size, picture.tobytes())
        if picture.size != (tw, th): size = picture.size
        tw, th = picture.size
    inverse = [_inverse(r) for r in rotations]
    collapsed = remapped = 0
    vertices = []
    for k in range(len(pos)):
        order = sorted(range(4), key=lambda c: -wgt[k][c])
        if wgt[k][order[1]] > 1e-3: collapsed += 1
        name = names[jnt[k][order[0]]]
        slot = slot_of(name)
        if slots[slot] != rig.names.index(name): remapped += 1
        m = skinning[jnt[k][order[0]]]
        p = [sum(m[r][c] * (list(pos[k]) + [1])[c] for c in range(4)) for r in range(3)]
        joint = slots[slot]
        local = _mv(inverse[joint], tuple(p[c] - positions[joint][c] for c in range(3)))
        vertices.append((slot, tuple(round(v * 4096) for v in local),
                         (round(uv[k][0] * tw * 16), round(uv[k][1] * th * 16))))
    faces = [tuple(vertices[i] for i in idx[k:k + 3]) for k in range(0, len(idx), 3)]
    model, report = write_model(model_raw, faces, size)
    report.update({'vertices': len(pos), 'collapsed_weight_vertices': collapsed, 'ancestor_remapped_vertices': remapped,
                   'texture': {'size': [tw, th], 'changed': texture != tex_raw, 'bytes': [len(tex_raw), len(texture)]}})
    warnings = []
    native_polygons = report['native_header_counts'][1]
    if report['triangles'] > native_polygons:
        warnings.append(f"{report['triangles']} polygons vs {native_polygons} native; the DS draws at most "
                        '2048 polygons / 6144 vertices per frame for the whole scene.')
    if len(texture) > len(tex_raw):
        warnings.append('Texture grew: texture VRAM headroom is unmeasured; a crowded scene may leave other materials unbound.')
    report['warnings'] = warnings
    return model, texture, report


# --- research ROM ----------------------------------------------------------------
def research_rom(files):
    """Clean ROM with existing Glob resources replaced; for disposable emulator checks only."""
    import mod
    rom, glob, _ = mod.load_clean()
    offsets, names, _ = w.parse_glob(glob)
    blobs = [glob[a:b] for a, b in zip(offsets, offsets[1:])]
    for name, raw in files.items():
        if name not in names: raise ValueError(f'{name} is not a clean Glob resource (additions are not supported)')
        if len(raw) % 4: raise ValueError(f'{name} length is not a multiple of four')
        blobs[names.index(name)] = raw
    out = w.rebuild_rom(rom, {'Glob.bin': w.pack_glob(names, blobs)}, legacy_gaps=True)
    w.validate_rom(out, target=True)
    return out


def _private(path):
    path = Path(path).resolve()
    if not any(path.is_relative_to((ROOT / d).resolve()) for d in ('build', 'work')):
        raise ValueError('Bridge outputs are private game derivatives: write them under build/ or work/')
    return path


def _clean(name):
    import mod
    _, glob, _ = mod.load_clean()
    offsets, names, _ = w.parse_glob(glob)
    if name not in names: raise ValueError(f'{name} is not a clean Glob resource')
    i = names.index(name)
    return glob[offsets[i]:offsets[i + 1]]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)
    e = sub.add_parser('export'); e.add_argument('model'); e.add_argument('texture'); e.add_argument('out')
    i = sub.add_parser('import'); i.add_argument('glb'); i.add_argument('model'); i.add_argument('texture'); i.add_argument('outdir')
    r = sub.add_parser('rom'); r.add_argument('outdir'); r.add_argument('out')
    args = parser.parse_args(argv)
    if args.command == 'export':
        w.atomic_write(_private(args.out), export_glb(_clean(args.model), _clean(args.texture), args.model))
    elif args.command == 'import':
        out = _private(args.outdir)
        model, texture, report = import_glb(Path(args.glb).read_bytes(), _clean(args.model), _clean(args.texture))
        w.atomic_write(out / args.model, model)
        w.atomic_write(out / args.texture, texture)
        w.write_json(out / 'report.json', report)
        print(json.dumps(report, indent=2))
    else:
        folder = Path(args.outdir)
        files = {p.name: p.read_bytes() for p in folder.iterdir() if p.suffix in ('.nsbmd', '.nsbtx')}
        w.atomic_write(_private(args.out), research_rom(files))
        print(f'{args.out}: {", ".join(sorted(files))}')


if __name__ == '__main__':
    main()
