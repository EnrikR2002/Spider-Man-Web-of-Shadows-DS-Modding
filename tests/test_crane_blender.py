"""Ballast Blender study: native topology, texture and isolated ROM boundaries."""
import json
import struct
import tempfile
import unittest
from pathlib import Path
from tools import crane_blender as c, model_bridge as b, spider2099 as assets, wos_tool as w


class BoundaryTests(unittest.TestCase):
    def test_rejects_output_outside_research_directory(self):
        with self.assertRaisesRegex(ValueError, 'build/crane-models'):
            c.candidate('missing.nds', c.ROOT / 'build/Spider-Man-WoS-modded.nds')


class BallastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths = (c.ROOT / 'build/version-0.40.0-final/Versioned.nds',
                 c.ROOT / 'build/Spider-Man-WoS-modded.nds')
        parent = next((p for p in paths if p.exists() and w.sha256(p.read_bytes()) == c.PARENT), None)
        if parent is None:
            raise unittest.SkipTest('private published v0.40.0 ROM missing')
        cls.parent = parent
        names, blobs = assets.resources(parent.read_bytes())
        cls.raw, cls.texture = (blobs[names.index(n)] for n in (c.MODEL, c.TEXTURE))

    def test_unchanged_bridge_and_uv_guard(self):
        glb = b.export_glb(self.raw, self.texture, c.MODEL)
        result, report = c.rewrite(self.raw, self.texture, glb)
        self.assertEqual(report, {'changed_vertices': 0, 'added_quads': 0})
        self.assertEqual(b.triangles(result), b.triangles(self.raw))
        doc, binary = b.read_glb(glb)
        uv = doc['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0']
        accessor = doc['accessors'][uv]
        view = doc['bufferViews'][accessor['bufferView']]
        at = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        binary = bytearray(binary)
        struct.pack_into('<f', binary, at, struct.unpack_from('<f', binary, at)[0] + .25)
        with self.assertRaisesRegex(ValueError, 'UV or bone changed'):
            c.rewrite(self.raw, self.texture, b._glb(doc, bytes(binary)))

    def test_replacement_selects_exactly_twenty_old_quads(self):
        cut = c.replace_old_armor(self.raw)
        old, new = b.ModelGeometry.parse(self.raw), b.ModelGeometry.parse(cut)
        self.assertEqual(struct.unpack_from('<4H', self.raw, old.model + 36), (1064, 266, 0, 266))
        self.assertEqual(struct.unpack_from('<4H', cut, new.model + 36), (984, 246, 0, 246))
        self.assertEqual(b.template(cut)[1].node_records, b.template(self.raw)[1].node_records)

    @unittest.skipUnless(c.BLENDER.exists(), 'local Blender 4.5 missing')
    def test_candidate_keeps_budget_rig_effect_bones_and_metadata(self):
        folder = c.ROOT / 'build/crane-models'
        self.assertTrue(folder.resolve().is_relative_to(c.ROOT.resolve()))
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='test-', dir=folder) as temporary:
            output = Path(temporary).resolve() / 'Versioned.nds'
            self.assertTrue(output.is_relative_to(folder.resolve()))
            report = c.candidate(self.parent, output)
            meta = json.loads(output.with_suffix('.build.json').read_text(encoding='utf-8'))
            candidate_names, candidate_blobs = assets.resources(output.read_bytes())
            model = candidate_blobs[candidate_names.index(c.MODEL)]
            self.assertEqual(meta['crane_blender_study'], report)
            self.assertEqual(meta['output_rom_sha256'], report['rom_sha256'])
            self.assertEqual(w.sha256(output.read_bytes()), report['rom_sha256'])
            self.assertEqual(report['rom_sha256'], '5f011cbe2e0aa5125aed335c28e044e9a9d3cb24194090e78d768165e9f90652')
            self.assertEqual(report['modified_resources'], [c.MODEL])
        old, new = b.ModelGeometry.parse(self.raw), b.ModelGeometry.parse(model)
        self.assertEqual(model[new.model + 36:new.model + 44], self.raw[old.model + 36:old.model + 44])
        self.assertEqual(b.template(model)[1].node_records, b.template(self.raw)[1].node_records)
        slots = b.template(self.raw)[4]
        rig = b.template(self.raw)[1]
        effects = {slot for slot, joint in slots.items() if 'MidToe1_' in rig.names[joint]}
        self.assertEqual([f for f in b.triangles(model) if f[0][0] in effects],
                         [f for f in b.triangles(self.raw) if f[0][0] in effects])
        self.assertEqual((report['added_quads'], report['removed_quads']), (20, 20))
        self.assertTrue(report['blender_version'].startswith('Blender '))
        self.assertEqual(w.sha256(model), '186c60dd24d9bc0c966220622be54dd98f58ef07bdac880af71cb4aeda3ee896')


if __name__ == '__main__':
    unittest.main()
