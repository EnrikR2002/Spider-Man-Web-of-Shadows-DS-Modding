import struct
import unittest

import mod
from tools.room_entities import Entities, character_position
from tools.room_objects import RoomObjects


class EntityBoundsTests(unittest.TestCase):
    def test_empty_and_invalid_batches(self):
        self.assertEqual(Entities.parse(b'\x04\x00\x04\x00').to_bytes(), b'\x04\x00\x04\x00')
        for data in (b'\0', b'\x04\0\x08\0', b'\x08\0\x08\x01\x18\0\0\0'):
            with self.assertRaises(ValueError): Entities.parse(data)


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private ROM not present')
class PrivateEntityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.rom, cls.glob, cls.manifest = mod.load_clean()

    def test_all_entity_batches_and_names_roundtrip(self):
        batches = records = objects = 0
        for e in self.manifest['entries']:
            if not e['name'].endswith('_app.obj'): continue
            raw = self.glob[e['offset']:e['offset'] + e['size']]
            room = RoomObjects.parse(raw)
            for record, names in zip(room.records, room.names):
                entities = Entities.parse(record.sections[0])
                with self.subTest(room=e['name'], object=record.offset):
                    self.assertEqual(entities.to_bytes(), record.sections[0])
                    self.assertEqual(len(entities.records), names.category_ends[0])
                batches += len(entities.batches)
                records += len(entities.records)
                objects += 1
        self.assertEqual((objects, batches), (156, 586))
        self.assertGreater(records, 500)

    def test_character_edit_preserves_every_unknown_field(self):
        e = next(e for e in self.manifest['entries'] if e['name'] == 'Test_Combat01_app.obj')
        raw = self.glob[e['offset']:e['offset']+e['size']]
        room = RoomObjects.parse(raw)
        old = Entities.parse(room.records[2].sections[0]).records[0]
        self.assertEqual(character_position(raw, 2, 0, struct.unpack_from('<3i',old)), raw)
        changed = RoomObjects.parse(character_position(raw, 2, 0, (80*4096, 5*4096, 0)))
        new = Entities.parse(changed.records[2].sections[0]).records[0]
        self.assertEqual(new[12:], old[12:])
        self.assertEqual(changed.names, room.names)
        for i in (0,1): self.assertEqual(changed.records[i].raw, room.records[i].raw)
        self.assertEqual(changed.records[2].sections[1:], room.records[2].sections[1:])


if __name__ == '__main__': unittest.main()
