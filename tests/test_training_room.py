"""Test Upgrades sparring room: lossless OBJ edit and kit training-room contract."""
import re
import struct
import unittest
import mod
from tools import tasm_kit as kit, training_room as room, wos_tool as w


class TrainingRoomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, glob, manifest = mod.load_clean()
        e = next(e for e in manifest['entries'] if e['name'] == room.NAME)
        cls.clean = glob[e['offset']:e['offset'] + e['size']]
        cls.edited = room.with_sparring(cls.clean)

    def test_no_sparring_is_a_lossless_roundtrip(self):
        self.assertEqual(w.sha256(self.clean), room.CLEAN_SHA256)
        self.assertEqual(room.with_sparring(self.clean, ()), self.clean)

    def test_sparring_copies_the_dummy_record_keeping_it_first(self):
        native = room.characters(self.clean)
        self.assertEqual(native, [(577292, 13912, -598, room.LEFT, 50)])
        placed = room.characters(self.edited)
        self.assertEqual(placed[0], native[0])                       # passive dummy stays first
        self.assertEqual([(x, a) for x, _, _, a, _ in placed[1:]], list(room.SPARRING))
        self.assertTrue(all(p[1:3] == native[0][1:3] and p[4] == 50 for p in placed))
        for x, _ in room.SPARRING:
            self.assertTrue(4 * 4096 < x < 236 * 4096)                # inside the room walls

    def test_only_the_characters_section_and_its_bounds_change(self):
        c, e = self.clean, self.edited
        delta = 3 * room.RECORD
        self.assertEqual(len(e), len(c) + delta + 3 * 32)
        self.assertEqual(e[:4], c[:4])
        self.assertEqual(struct.unpack_from('<2I', e, 4), tuple(v + delta for v in struct.unpack_from('<2I', c, 4)))
        self.assertEqual(e[12:room.DUMMY_OBJECT], c[12:room.DUMMY_OBJECT])   # other objects untouched
        tail = room.DUMMY_OBJECT + 0x14 + 0x20
        self.assertEqual(e[tail + delta:room.NAMES_BLOCK + delta], c[tail:room.NAMES_BLOCK])   # event graph, tables, names
        self.assertEqual(e[-(len(c) - room.NAMES_BLOCK - 0x34):], c[room.NAMES_BLOCK + 0x34:])
        self.assertEqual(e.count(b'Character (Practice Dummy)'), 4)

    def test_edited_or_foreign_input_is_rejected(self):
        with self.assertRaises(ValueError):
            room.with_sparring(self.edited)
        with self.assertRaises(ValueError):
            room.with_sparring(self.clean, room.SPARRING + ((100 * 4096, room.LEFT),))

    def test_kit_hooks_the_player_hp_store_and_keeps_training_state_private(self):
        self.assertEqual(kit.HOOKS[0x0205F420], (0x34, 0xE5823084))
        source = (kit.Path(kit.__file__).with_name('tasm_kit.s')).read_text(encoding='utf-8')
        self.assertIn('b 0x0205f424', source)
        # Training state words +0x2F0..+0x2F8 belong to the training section only.
        before, rest = source.split('train_observe:')
        section, after = rest.split('// kit_target(')
        self.assertRegex(section, r'#0x2f[048]\]')
        self.assertNotRegex(before + after, r'#0x2f[048]\]')


if __name__ == '__main__':
    unittest.main()
