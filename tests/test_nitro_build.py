"""Nitro writers: native dictionaries, texture archives and room models rebuild byte for byte."""
import unittest

import mod
from tools import nitro_build as nb
from tools.model_geometry import ModelGeometry
from tools.nitro_texture import TextureArchive, dictionary


class NitroBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, glob, manifest = mod.load_clean()
        cls.blobs = {e['name']: glob[e['offset']:e['offset'] + e['size']] for e in manifest['entries']}

    def test_dictionary_search_tree_matches_native_files(self):
        raw = self.blobs['Test_Surfaces01.nsbmd']
        model = ModelGeometry.parse(raw).model
        at = model + int.from_bytes(raw[model + 8:model + 12], 'little') + 4          # the material dictionary, ten names
        rows = dictionary(raw, at, 4)
        self.assertEqual(len(rows), 10)
        built = nb.dictionary_bytes(rows)
        self.assertEqual(built, raw[at:at + len(built)])
        nodes = nb.patricia([name for name, _ in rows])
        self.assertEqual(nodes[0][:3], (127, 1, 0))                    # root: bit 127, left child first
        self.assertEqual(sorted(n[3] for n in nodes[1:]), list(range(10)))
        self.assertEqual(nb.patricia(['Test_Surfaces01']), [(127, 1, 0, 0), (117, 0, 1, 0)])
        with self.assertRaises(ValueError): nb.patricia(['a', 'a'])
        with self.assertRaises(ValueError): nb.dictionary_bytes([('x' * 17, b'\0\0\0\0')])

    def test_room_texture_archives_rebuild_from_their_parts(self):
        rebuilt = 0
        for name in ('Test_Combat01Textures.nsbtx', 'proto01Textures.nsbtx', 'Pier_Map06Textures.nsbtx',
                     'Downtown_Map06Textures.nsbtx', 'Residential_Map01Textures.nsbtx', 'Sewer_Map03Textures.nsbtx'):
            raw = self.blobs[name]
            textures, palettes = nb.archive_parts(raw)
            self.assertEqual(nb.texture_archive(textures, palettes), raw, name)
            rebuilt += len(textures)
        self.assertGreater(rebuilt, 100)
        # A subset in another order is still a valid archive holding the same pixels.
        textures, palettes = nb.archive_parts(self.blobs['proto01Textures.nsbtx'])
        pick = [t for t in textures if t.name in ('wbrick01', 'cityscape01')][::-1]
        raw = nb.texture_archive(pick, [p for t in pick for p in palettes if p.name == t.name + '_pl'])
        archive = TextureArchive.parse(raw)
        self.assertEqual([t['name'] for t in archive.textures], ['wbrick01', 'cityscape01'])
        again, _ = nb.archive_parts(raw)
        self.assertEqual([(t.data, t.index) for t in again], [(t.data, t.index) for t in pick])
        with self.assertRaises(ValueError): nb.texture_archive([nb.Texture('x', 8, 8, 3, b'\0' * 5)], [nb.Palette('x_pl', b'\0' * 32)])

    def test_one_node_room_models_rebuild_from_their_parts(self):
        for name in ('Test_Surfaces01.nsbmd', 'Test_Combat01.nsbmd', 'proto01.nsbmd', 'Downtown_Map14.nsbmd', 'Hive_Map02.nsbmd'):
            raw = self.blobs[name]
            self.assertEqual(nb.room_model(nb.model_parts(raw)), raw, name)
        parts = nb.model_parts(self.blobs['Test_Surfaces01.nsbmd'])
        self.assertEqual((len(parts.materials), len(parts.streams), parts.scale), (10, 10, 128 * 4096))
        self.assertEqual(parts.materials[8].texture, 'tx_default')
        self.assertEqual(parts.materials[0].record, nb.material_record(128, 128, polygon=0x001F0081))   # native record layout


if __name__ == '__main__':
    unittest.main()
