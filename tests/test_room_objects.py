"""Independent malformed fixtures and full private-room lossless coverage."""
import struct
import unittest

import mod
from tools.room_objects import RoomObjects


def fixture():
    sections = (b'aaaa', b'', b'bb', b'opaque events', b'cc')
    ends, total = [], 0
    for s in sections:
        total += len(s)
        ends.append(total)
    record = struct.pack('<H2sI5HH', total + 20, b'\x01\x01', 0x1234, *ends, 0x5678) + b''.join(sections)
    end = 16 + len(record)
    names = struct.pack('<IH7H', 84, 20, 1, 1, 1, 1, 1, 1, 1) + b'Entity'.ljust(32, b'\0') + b'Unclassified group'.ljust(32, b' ')
    return struct.pack('<3IBBH', 2, end, end + 8, 1, 0, 0) + record + b'opaque!!' + names


class RoomObjectTests(unittest.TestCase):
    def test_lossless_opaque_and_unclassified_names(self):
        raw = fixture()
        room = RoomObjects.parse(raw)
        self.assertEqual(room.to_bytes(), raw)
        self.assertEqual(room.names[0].labels, ('Entity', 'Unclassified group'))
        self.assertEqual(room.replace_section(0, 3, room.records[0].sections[3]), raw)
        self.assertEqual(room.omit_record(), raw)
        empty = RoomObjects.parse(room.omit_record(0))
        self.assertEqual((empty.records,empty.names,empty.between), ((),(),b''))

    def test_section_growth_preserves_all_other_payloads(self):
        room = RoomObjects.parse(fixture())
        changed = RoomObjects.parse(room.replace_section(0, 1, b'new payload'))
        self.assertEqual(changed.between, room.between)
        self.assertEqual(changed.names, room.names)
        self.assertEqual(changed.records[0].raw[2:8], room.records[0].raw[2:8])
        self.assertEqual(changed.records[0].raw[18:20], room.records[0].raw[18:20])
        for i in (0, 2, 3, 4):
            self.assertEqual(changed.records[0].sections[i], room.records[0].sections[i])
        self.assertEqual(changed.replace_section(0, 1, b''), fixture())

    def test_invalid_boundaries_rejected(self):
        raw = fixture()
        for offset, fmt, value in [(0, '<I', 3), (4, '<I', 5000), (8, '<I', 0),
                                   (12, '<B', 2), (16, '<H', 19), (24, '<H', 60000)]:
            bad = bytearray(raw)
            struct.pack_into(fmt, bad, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                RoomObjects.parse(bad)
        for n in (0, 15, len(raw) - 1):
            with self.assertRaises(ValueError):
                RoomObjects.parse(raw[:n])
        with self.assertRaises(ValueError):
            RoomObjects.parse(raw + b'extra')

    def test_edit_bounds(self):
        room = RoomObjects.parse(fixture())
        for record, section in [(-1, 0), (1, 0), (0, -1), (0, 5)]:
            with self.assertRaises(ValueError): room.replace_section(record, section, b'')
        with self.assertRaises(ValueError): room.replace_section(0, 0, bytes(65536))


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private clean ROM not present')
class PrivateRoomTests(unittest.TestCase):
    def test_all_75_rooms_and_every_noop_section_edit(self):
        _, glob, manifest = mod.load_clean()
        count = 0
        for entry in manifest['entries']:
            if not entry['name'].endswith('_app.obj'): continue
            raw = glob[entry['offset']:entry['offset'] + entry['size']]
            room = RoomObjects.parse(raw)
            with self.subTest(room=entry['name']):
                self.assertEqual(room.to_bytes(), raw)
                self.assertEqual(room.omit_record(),raw)
                for i, record in enumerate(room.records):
                    for j, section in enumerate(record.sections):
                        self.assertEqual(room.replace_section(i, j, section), raw)
            count += 1
        self.assertEqual(count, 75)


if __name__ == '__main__': unittest.main()
