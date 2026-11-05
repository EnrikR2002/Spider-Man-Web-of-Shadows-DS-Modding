"""Blender model bridge: glb framing, GPU stream encoding and exact native round trips."""
import json
import struct
import unittest

from tools import model_bridge as b


def canon(face):
    k = min(range(3), key=lambda i: face[i])
    return face[k:] + face[:k]


class SyntheticTests(unittest.TestCase):
    def test_glb_accessors_read_strided_and_normalized_data(self):
        binary = struct.pack('<4B', 255, 0, 128, 7) + struct.pack('<3f', 1, 2, 3) + bytes(4) + struct.pack('<3f', 4, 5, 6)
        doc = {'asset': {'version': '2.0'},
               'bufferViews': [{'buffer': 0, 'byteOffset': 0, 'byteLength': 4},
                               {'buffer': 0, 'byteOffset': 4, 'byteLength': 28, 'byteStride': 16}],
               'accessors': [{'bufferView': 0, 'componentType': 5121, 'count': 2, 'type': 'VEC2', 'normalized': True},
                             {'bufferView': 1, 'componentType': 5126, 'count': 2, 'type': 'VEC3'}]}
        got, chunk = b.read_glb(b._glb(doc, binary))
        self.assertEqual(got['accessors'], doc['accessors'])
        self.assertEqual(b.accessor(got, chunk, 0), [(1.0, 0.0), (128 / 255, 7 / 255)])
        self.assertEqual(b.accessor(got, chunk, 1), [(1.0, 2.0, 3.0), (4.0, 5.0, 6.0)])
        with self.assertRaisesRegex(ValueError, 'glTF 2.0'):
            b.read_glb(b'glTF' + struct.pack('<II', 1, 12))

    def test_node_matrices_and_inverse(self):
        half = 2 ** -0.5     # 90 degrees about Z, then translate
        doc = {'scene': 0, 'scenes': [{'nodes': [0]}],
               'nodes': [{'translation': [1, 2, 3], 'rotation': [0, 0, half, half], 'children': [1]},
                         {'translation': [1, 0, 0]}]}
        child = b.globals_of(doc)[1]
        self.assertEqual([round(child[r][3], 9) for r in range(3)], [1, 3, 3])
        m = ((2, 0, 1), (0, 1, 0), (1, 0, 1))
        inv = b._inverse(m)
        self.assertEqual([[round(sum(m[r][k] * inv[k][c] for k in range(3)), 9) for c in range(3)] for r in range(3)],
                         [[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    def test_stream_restores_matrix_and_texcoord_only_on_change(self):
        face = ((4, (4096, -1, 0), (16, 32)), (4, (0, 0, 0), (16, 32)), (5, (1, 2, 3), (0, 0)))
        raw = b.stream([face], 4)
        ops = []
        at = 0
        while at < len(raw):
            group = raw[at:at + 4]
            at += 4
            for op in group:
                ops.append(op)
                at += 4 * {0x40: 1, 0x22: 1, 0x23: 2, 0x14: 1}.get(op, 0)
        self.assertEqual([op for op in ops if op], [0x40, 0x22, 0x23, 0x23, 0x14, 0x22, 0x23, 0x41])
        with self.assertRaisesRegex(ValueError, '16-bit'):
            b.stream([((4, (40000, 0, 0), (0, 0)),) * 3], 4)


class NativeRoundTripTests(unittest.TestCase):
    """Private clean-ROM checks; a fresh clone reports them as missing private input."""

    def test_unchanged_export_import_reproduces_native_faces(self):
        for model, texture in (('spd.nsbmd', 'spd.nsbtx'), ('brt.nsbmd', 'brt.nsbtx')):
            mr, tr = b._clean(model), b._clean(texture)
            new, tex, report = b.import_glb(b.export_glb(mr, tr, model), mr, tr)
            native = sorted(canon(f) for f in b.triangles(mr) if len(set(f)) == 3)
            self.assertEqual(sorted(canon(f) for f in b.triangles(new)), native, model)
            self.assertEqual(tex, tr)
            self.assertEqual(report['collapsed_weight_vertices'], 0)

    def test_added_part_follows_its_bone_and_grows_the_box(self):
        mr, tr = b._clean('spd.nsbmd'), b._clean('spd.nsbtx')
        doc, binary = b.read_glb(b.export_glb(mr, tr, 'spd.nsbmd'))
        head = next(i for i, n in enumerate(doc['nodes']) if n.get('name') == 'spd:Head_M')
        pos = b.accessor(doc, binary, 0)
        tip = (0.0, 14.0, 0.0)                     # far above the native box
        rows = [pos[0], pos[1], tip]
        verts = len(pos)
        # Append three vertices bound to the head and one triangle using them.
        extra = (b''.join(struct.pack('<3f', *p) for p in rows), struct.pack('<2f', .1, .7) * 3,
                 struct.pack('<4B', head, 0, 0, 0) * 3, struct.pack('<4f', 1, 0, 0, 0) * 3)
        views = doc['bufferViews']
        out = bytearray(binary)
        for slot, data in zip((0, 1, 2, 3), extra):
            old = views[slot]
            moved = bytes(out[old['byteOffset']:old['byteOffset'] + old['byteLength']]) + data
            out += bytes(-len(out) % 4)
            views[slot] = {'buffer': 0, 'byteOffset': len(out), 'byteLength': len(moved)}
            out += moved
            doc['accessors'][slot]['count'] = verts + 3
        doc['accessors'][0]['max'] = [max(a, c) for a, c in zip(doc['accessors'][0]['max'], tip)]
        index = b.accessor(doc, bytes(out), 4)
        data = struct.pack(f'<{len(index) + 3}H', *[r[0] for r in index], verts, verts + 1, verts + 2)
        out += bytes(-len(out) % 4)
        views[4] = {'buffer': 0, 'byteOffset': len(out), 'byteLength': len(data)}
        out += data
        doc['accessors'][4]['count'] += 3
        doc['buffers'] = [{'byteLength': len(out) + (-len(out) % 4)}]
        model, _, report = b.import_glb(b._glb(doc, bytes(out)), mr, tr)
        added = b.triangles(model)[-1]
        g, _, rotations, positions, slots, _ = b.template(model)
        self.assertEqual({slots[v[0]] for v in added}, {5})
        self.assertAlmostEqual(b.world(rotations, positions, slots, added[2])[1], 14.0, places=3)
        box_y_top = (struct.unpack_from('<h', model, g.model + 46)[0] + struct.unpack_from('<H', model, g.model + 52)[0])
        self.assertGreater(box_y_top * struct.unpack_from('<I', model, g.model + 56)[0] / 4096 / 4096, 14.0)
        self.assertEqual(report['triangles'], 481)

        doc['nodes'][head]['name'] = 'spd:NewBone'
        with self.assertRaisesRegex(ValueError, 'not in the template rig'):
            b.import_glb(b._glb(doc, bytes(out)), mr, tr)

    def test_texture_redraw_keeps_names_and_resizes_material(self):
        mr, tr = b._clean('spd.nsbmd'), b._clean('spd.nsbtx')
        w, h, rgba = b.decode_texture(tr, mr)
        bigger = b''.join(rgba[(y // 2 * w + x // 2) * 4:(y // 2 * w + x // 2) * 4 + 4] for y in range(2 * h) for x in range(2 * w))
        archive = b.encode_texture(tr, mr, 2 * w, 2 * h, bigger)
        self.assertEqual(b.decode_texture(archive, mr)[:2], (2 * w, 2 * h))
        self.assertEqual(b.bound_names(mr)[0], [t.name for t in b.nb.archive_parts(archive)[0]])
        model, _ = b.write_model(mr, b.triangles(mr), (2 * w, 2 * h))
        self.assertEqual(b.material(model)[1:], (2 * w, 2 * h))
        self.assertIs(b.encode_texture(tr, mr, w, h, rgba), tr)
        self.assertTrue(json.dumps(b.write_model(mr, b.triangles(mr))[1]))


if __name__ == '__main__':
    unittest.main()
