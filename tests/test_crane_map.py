"""Crane Row ring map post-pass: room-list rows, exact scope and chaining."""
import struct
import unittest
import mod
from tools import crane_map as m, crane_navigation as nav, crane_rooms as cr, midnight_chapter as ch
from tools import wos_tool as w, spider2099 as assets
from tools.minimap_cbmp import Cbmp


class Entries(unittest.TestCase):
    def test_rows_are_twenty_bytes_and_only_the_office_is_a_save_row(self):
        listing = [(cr.NAMES[0], 11, 46, 123), (cr.NAMES[2], 1, 72, 88), (cr.NAMES[5], 6, 155, 118)]
        raw = m.entries(listing)
        self.assertEqual(len(raw), 3*m.ENTRY)
        for i, (name, slot, x, y) in enumerate(listing):
            row = raw[i*m.ENTRY:(i+1)*m.ENTRY]
            self.assertEqual(struct.unpack_from('<2I', row), (cr.IDS[name], 1))
            self.assertEqual(row[8:11], bytes((int(name == cr.NAMES[2]), slot, slot+4)))
            self.assertEqual((row[11:15], row[15:17]), (ch.STATE_COLORS, bytes((x, y))))

    def test_every_room_has_a_marker_inside_its_own_outline(self):
        for name, slot, x, y in self.listing():
            x, y = x-24, y-24
            self.assertIn((x, y), nav.shape(name), name)

    def listing(self):
        if not mod.DEFAULT_ROM.exists():self.skipTest('Private original missing')
        _, glob, manifest = mod.load_clean()
        e = next(e for e in manifest['entries'] if e['name'] == ch.MAP_SOURCE)
        return m.screens(glob[e['offset']:e['offset']+e['size']])[1]


@unittest.skipUnless(mod.DEFAULT_ROM.exists() and m.ROOT.joinpath('build/version-0.37.0-final/Versioned.nds').exists(),
                     'published v0.37.0 candidate missing')
class Release(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = m.ROOT.joinpath('build/version-0.37.0-final/Versioned.nds').read_bytes()
        cls.result, cls.report = m.apply_rom(cls.parent)

    def test_only_the_four_progress_screens_change_and_the_list_shrinks_in_place(self):
        names, old = assets.resources(self.parent)
        _, new = assets.resources(self.result)
        self.assertEqual([n for n, a, b in zip(names, old, new) if a != b], list(nav.SCREENS))
        self.assertEqual(self.report['entry_count']['old'], 20)
        self.assertLessEqual(self.report['entry_count']['new'], 20)
        h = w.parse_header(self.result)
        arm = self.result[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        row, table, count = m.find_table(arm, names)
        self.assertEqual(count, self.report['entry_count']['new'])
        screen = Cbmp.parse(new[names.index(nav.SCREENS[0])])
        self.assertEqual(screen.to_bytes(), new[names.index(nav.SCREENS[0])][:len(screen.to_bytes())])

    def test_arm_changes_stay_inside_the_room_list_and_its_count(self):
        h = w.parse_header(self.parent);old = self.parent[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        h = w.parse_header(self.result);new = self.result[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
        names, _ = assets.resources(self.parent)
        row, table, count = m.find_table(old, names)
        allowed = set(range(m.offset(table), m.offset(table)+count*m.ENTRY))|set(range(m.offset(row)+16*m.MAP_AREA+12, m.offset(row)+16*m.MAP_AREA+16))
        self.assertEqual(len(old), len(new))
        self.assertTrue({i for i, (a, b) in enumerate(zip(old, new)) if a != b} <= allowed)

    def test_second_application_is_identical_and_other_roms_are_refused(self):
        again, _ = m.apply_rom(self.result)
        self.assertEqual(w.sha256(again), w.sha256(self.result))
        with self.assertRaises(ValueError):m.apply_rom(mod.DEFAULT_ROM.read_bytes())


if __name__ == '__main__':
    unittest.main()
