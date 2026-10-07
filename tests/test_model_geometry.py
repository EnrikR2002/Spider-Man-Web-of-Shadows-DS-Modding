import unittest

import mod
from tools import model_geometry as m


class GPUStreamTests(unittest.TestCase):
    def test_quad_packet_and_bounded_vertices(self):
        stream = m.quads_stream([(0x7FFF, [(0,0,0),(1,0,0),(1,1,0),(0,1,0)])])
        self.assertEqual(stream[:4], bytes([0x40,0x20,0x22,0x23]))
        self.assertEqual(len(stream) % 4, 0)
        with self.assertRaises(ValueError): m.quads_stream([(0, [(600,0,0)] * 4)])
        with self.assertRaises(ValueError): m.box(0,0,0,0,1,1,0)


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private ROM not present')
class PrivateModelTests(unittest.TestCase):
    def test_mesh_noop_roundtrip_and_authored_stream_preservation(self):
        _, glob, manifest = mod.load_clean()
        e = next(e for e in manifest['entries'] if e['name'] == 'Test_Combat01.nsbmd')
        raw = glob[e['offset']:e['offset'] + e['size']]
        model = m.ModelGeometry.parse(raw)
        self.assertEqual(model.to_bytes(), raw)
        self.assertEqual(model.replace_streams([raw[s.start:s.start+s.length] for s in model.shapes], vertices=52, quads=13), raw)
        changed = m.platform_model(raw)
        parsed = m.ModelGeometry.parse(changed)
        # Existing material/SBC/node section survives exactly; only model size
        # and geometry counters before it, plus shape pointers, are edited.
        start, end = model.model + 64, model.shapes[0].header
        self.assertEqual(changed[start:end], raw[start:end])
        self.assertTrue(all(s.start >= len(raw) for s in parsed.shapes))
        self.assertEqual(changed[len(raw):], b''.join(changed[s.start:s.start+s.length] for s in parsed.shapes))


if __name__ == '__main__': unittest.main()
