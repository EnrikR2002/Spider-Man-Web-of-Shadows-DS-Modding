"""Native exits/spawns across all clean rooms and appended doorways (real data)."""
import struct
import unittest

import mod
from tools import room_doors as doors
from tools.room_entities import Entities
from tools.room_events import Events
from tools.room_objects import RoomObjects


class RoomDoorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, glob, manifest = mod.load_clean()
        cls.objects = {e['name'][:-8]: glob[e['offset']:e['offset'] + e['size']]
                       for e in manifest['entries'] if e['name'].endswith('_app.obj')}

    def test_spawn_table_matches_extra_name_slots_in_every_room(self):
        self.assertEqual(len(self.objects), 75)
        for name, raw in self.objects.items():
            parsed = RoomObjects.parse(raw)
            names = parsed.names[0]
            extra = (len(names.raw) - 20) // 32 - names.category_ends[-1]
            spawns = doors.spawns(raw)
            self.assertEqual(len(spawns), extra, name)
            self.assertEqual(len({s.spawn_id for s in spawns}), len(spawns), name)

    def test_known_sewer_exits_and_save_room_spawns(self):
        self.assertEqual([(x.group, x.room, x.selector, x.spawn) for x in doors.exits(self.objects['Sewer_Map07'])],
                         [(1, 55, 1, 2), (2, 58, 1, 1), (3, 65, 1, 1), (4, 55, 1, 3)])
        save = doors.spawns(self.objects['Sewer_Save02'])
        self.assertEqual([(s.spawn_id, s.x, s.angle) for s in save], [(1, 17625, 0x4000), (0, 126976, 0)])

    def test_every_native_exit_names_an_existing_room_spawn(self):
        by_index = {}
        import struct as st
        rom, _, manifest = mod.load_clean()
        from tools import room_catalog
        at, _, _, size = st.unpack_from('<4I', rom, 0x20)
        rooms = room_catalog.parse(rom[at:at + size], [e['name'] for e in manifest['entries']])
        for room in rooms: by_index[room.index] = room.name
        missing, defaults = [], 0
        for name, raw in self.objects.items():
            for x in doors.exits(raw):
                target = self.objects[by_index[x.room]]
                if x.spawn in {s.spawn_id for s in doors.spawns(target)}: continue
                if x.spawn == 0: defaults += 1      # no spawn 0 entry: default Spidey placement
                else: missing.append((name, x))
        self.assertEqual(missing, [])
        self.assertEqual(defaults, 5)

    def test_door_kinds_agree_with_native_pairs(self):
        rom, _, manifest = mod.load_clean()
        from tools import room_catalog
        at, _, _, size = struct.unpack_from('<4I', rom, 0x20)
        names = {r.index: r.name for r in room_catalog.parse(rom[at:at + size], [e['name'] for e in manifest['entries']])}
        agree = total = 0
        for name, raw in self.objects.items():
            for x in doors.exits(raw):
                if x.record: continue
                dest = self.objects[names[x.room]]
                back = [b for b in doors.exits(dest) if b.record == 0 and names[b.room] == name]
                try:
                    kinds = {doors.door_kind(dest, b.group) for b in back}
                    kind = doors.door_kind(raw, x.group)
                except ValueError:          # exit fired by a non-trigger entity/event
                    continue
                if not kinds: continue
                total += 1
                agree += doors.OPPOSITE[kind] in kinds
        self.assertGreaterEqual(total, 170)
        self.assertGreaterEqual(agree / total, 0.95)
        self.assertEqual(doors.door_kind(self.objects['Sewer_Map03'], 4), 'up')
        self.assertEqual(doors.door_kind(self.objects['Sewer_Map03'], 2), 'down')
        self.assertEqual(doors.door_kind(self.objects['Sewer_Save02'], 1), 'left')

    def test_noop_retarget_is_byte_exact_and_retarget_changes_one_operand(self):
        raw = self.objects['Sewer_Map07']
        self.assertEqual(doors.retarget(raw, {}), raw)
        changed = doors.retarget(raw, {(0, 3): (76, 1, 5)})
        self.assertEqual(len(changed), len(raw))
        self.assertEqual(sum(a != b for a, b in zip(raw, changed)), 2)   # room and spawn bytes
        self.assertIn((3, 76, 1, 5), [(x.group, x.room, x.selector, x.spawn) for x in doors.exits(changed)])
        with self.assertRaises(ValueError): doors.retarget(raw, {(0, 0): (1, 1, 1)})   # init group

    def test_add_spawn_appends_and_keeps_records_and_names(self):
        raw = self.objects['Sewer_Save02']
        changed = doors.add_spawn(raw, 2, (44 * 4096, 2 * 4096, 0), 'left')
        old, new = RoomObjects.parse(raw), RoomObjects.parse(changed)
        self.assertEqual(doors.spawns(changed)[:2], doors.spawns(raw))
        last = doors.spawns(changed)[-1]
        self.assertEqual((last.spawn_id, last.x, last.y, last.angle), (2, 44 * 4096, 2 * 4096, 0xC000))
        self.assertEqual([r.raw for r in new.records], [r.raw for r in old.records])
        self.assertEqual([n.raw for n in new.names], [n.raw for n in old.names])
        with self.assertRaises(ValueError): doors.add_spawn(raw, 1, (0, 0, 0), 'left')

    def test_add_exit_appends_trigger_group_and_names_without_moving_others(self):
        raw = self.objects['Sewer_Save02']
        changed = doors.add_exit(raw, center=(61 * 4096, 4 * 4096, 0), size=(12, 24), room=76, selector=1, spawn=1,
                                 trigger_name='Trigger (Main|Exit_Midnight)', group_name='Exit_Midnight_Line')
        old, new = RoomObjects.parse(raw), RoomObjects.parse(changed)
        old_e, new_e = (Entities.parse(x.records[0].sections[0]).records for x in (old, new))
        old_g, new_g = (Events.parse(x.records[0].sections[1], x.records[0].raw[3]).groups for x in (old, new))
        self.assertEqual(new_e[:-1], old_e)
        self.assertEqual(new_g[:-1], old_g)
        trigger = new_e[-1]
        self.assertEqual(struct.unpack_from('<3iI', trigger), (61 * 4096, 4 * 4096, 0, 7))
        self.assertEqual(struct.unpack_from('<2H', trigger, 20), (12, 24))
        self.assertEqual(trigger[27], len(new_g))           # 1-based reference to the new group
        self.assertEqual(old.records[1].raw, new.records[1].raw)
        self.assertEqual(old.names[1].raw, new.names[1].raw)
        labels = new.names[0].labels
        self.assertEqual(labels[len(new_e) - 1], 'Trigger (Main|Exit_Midnight)')
        self.assertEqual(labels[new.names[0].category_ends[1] - 1], 'Exit_Midnight_Line')
        self.assertEqual(new.names[0].category_ends, (4, 7, 8, 8, 8, 9, 9))
        self.assertEqual([(x.group, x.room, x.spawn) for x in doors.exits(changed)], [(1, 57, 4), (2, 76, 1)])
        self.assertEqual(doors.spawns(changed), doors.spawns(raw))

    def test_room_without_exit_trigger_is_rejected(self):
        with self.assertRaises(ValueError):
            doors.add_exit(self.objects['Test_Combat01'], center=(0, 0, 0), size=(8, 8), room=76, selector=1,
                           spawn=0, trigger_name='Trigger', group_name='Exit')


if __name__ == '__main__':
    unittest.main()
