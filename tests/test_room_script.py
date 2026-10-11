"""Room scripting: AG/EG structure on every native record, native operand layouts, append-only edits."""
import struct
import unittest

import mod
from tools import room_script as s
from tools.room_entities import Entities
from tools.room_events import Command, EventGroup, Events
from tools.room_objects import RoomObjects


class RoomScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, glob, manifest = mod.load_clean()
        cls.rooms = {e['name'][:-8]: glob[e['offset']:e['offset'] + e['size']]
                     for e in manifest['entries'] if e['name'].endswith('_app.obj')}

    def groups(self, raw, record):
        rec = RoomObjects.parse(raw).records[record]
        return Events.parse(rec.sections[1], rec.raw[3]).groups

    def test_batches_are_the_named_action_groups_of_every_native_record(self):
        records = 0
        for name, raw in self.rooms.items():
            for r in range(len(RoomObjects.parse(raw).records)):
                sizes, groups = s.counts(raw, r)          # raises when names/counts disagree
                records += 1
                batches = Entities.parse(RoomObjects.parse(raw).records[r].sections[0]).batches
                for g in self.groups(raw, r):
                    for c in g.commands:
                        if c.opcode == s.ANIMATE and name != 'proto01':     # (AG 0-based, entity 1-based)
                            ag, entity = c.operand[:2]
                            self.assertLess(ag, len(sizes), name)
                            self.assertTrue(1 <= entity <= sizes[ag], name)
                            kind = struct.unpack_from('<I', batches[ag].records[entity - 1], 12)[0]
                            self.assertIn(kind, (2, 14), name)         # characters and objects only
                        if c.opcode in (s.DELAY, s.IF_VAR):              # action AGs are 1-based (0 = none)
                            for at in ((4,) if c.opcode == s.DELAY else (8, 12)):
                                self.assertLessEqual(c.operand[at], len(sizes), name)
                            for at in ((5,) if c.opcode == s.DELAY else (9, 13)):
                                self.assertLessEqual(c.operand[at], groups, name)
        self.assertEqual(records, 156)

    def test_builders_reproduce_native_operands(self):
        init, throw, thrown = (self.groups(self.rooms['Sewer_Map04'], 1)[i].commands for i in (0, 1, 2))
        self.assertEqual(init[1], s.if_var(0x27, '==', 0, then=s.action(entity=(1, 1))))
        self.assertEqual(init[2], s.activate(ag=2))
        self.assertEqual(init[3], s.if_var(0x27, '==', 0, then=s.action(entity=(4, 1), ag=3),
                                           otherwise=s.action(entity=(3, 1), eg=3)))
        self.assertEqual(throw[0], s.animate(3, 1, 0x19))
        self.assertEqual(throw[2], s.set_var(0x123, 0x0B))
        self.assertEqual(thrown[0], s.animate(3, 1, 0x64))
        # Platform: the switch flag gates the electrified boiler; else the boiler AG becomes liftable.
        check = self.groups(self.rooms['Sewer_Map03'], 1)[7].commands[0]
        self.assertEqual(check, s.if_var(0x27, '==', 0, then=s.action(ag=5, eg=7), otherwise=s.action(ag=2)))

    def test_appends_keep_every_existing_index(self):
        raw = self.rooms['Sewer_Map13']
        sizes, groups = s.counts(raw, 1)
        old = RoomObjects.parse(raw)
        entity = Entities.parse(old.records[1].sections[0]).records[-1]
        out, ag = s.append_batch(raw, 1, [(entity, 'A'), (entity, 'B')], 'Extra')
        self.assertEqual(ag, len(sizes))
        out, eg = s.append_groups(out, 1, [(EventGroup((s.set_var(250, 1),)), 'Extra_Run')])
        self.assertEqual(eg, groups + 1)
        out = s.extend_group(out, 1, 0, [s.activate(ag=ag)])
        new = RoomObjects.parse(out)
        self.assertEqual(s.counts(out, 1), (sizes + (2,), groups + 1))
        self.assertEqual(Entities.parse(new.records[1].sections[0]).records[:sum(sizes)],
                         Entities.parse(old.records[1].sections[0]).records)
        old_groups, new_groups = self.groups(raw, 1), self.groups(out, 1)
        self.assertEqual(new_groups[1:groups], old_groups[1:])
        self.assertEqual(new_groups[0].commands, old_groups[0].commands + (s.activate(ag=ag),))
        labels, ends = new.names[1].labels, new.names[1].category_ends
        self.assertEqual(labels[ends[0] - 2:ends[0]], ('A', 'B'))
        self.assertEqual(labels[ends[1] - 1], 'Extra_Run')
        self.assertEqual(labels[ends[2] - 1], 'Extra')
        self.assertEqual(new.records[0].raw, old.records[0].raw)
        self.assertEqual(new.names[0].raw, old.names[0].raw)

    def test_door_deactivate_and_trigger_builders_reproduce_native_bytes(self):
        raw = self.rooms['Hive_Map02']
        entities, groups, batches = s.names(raw, 1)
        self.assertEqual(batches, ('<AG_INIT>', 'Enemy Spawners', 'Smashables', 'Hammer Object', 'Door Locks', 'Ambush Trigger'))
        self.assertEqual(entities[4], ('Ichor Door Block (Untokenized)', 'Object (Gate_Ichor_Floor)'))
        lock, unlock, block_die = (self.groups(raw, 1)[groups.index(n)].commands
                                   for n in ('Door_Lock', 'Door_Unlock', 'Ichor_Block_Die'))
        self.assertEqual(lock[0], s.door((0, 1), True))
        self.assertEqual(block_die[2], s.door((0, 1), False))
        self.assertEqual(lock[5], s.deactivate(entity=(5, 1)))          # the one-shot ambush trigger removes itself
        self.assertEqual(block_die[0], s.deactivate(ag=4))
        self.assertEqual(self.groups(self.rooms['Sewer_Map03'], 1)[9].commands, (s.door((0, 3), True),))   # Lock_Grate
        trigger = Entities.parse(RoomObjects.parse(raw).records[1].sections[0]).batches[5].records[0]
        x, y, z = struct.unpack_from('<3i', trigger)
        self.assertEqual(trigger, s.trigger(x, y, (0x2D, 5), groups.index('Ambush Trigger') + 1, z))
        self.assertEqual(s.actions(lock[5]), (bytes((5, 1, 0, 0)),))
        self.assertEqual(s.targets(bytes((5, 1, 0, 0))), {5})
        self.assertEqual(s.targets(bytes((0, 0, 4, 2))), {3})
        self.assertEqual(s.actions(s.set_var(1, 1)), ())

    def test_drop_commands_removes_whole_commands_and_keeps_every_index(self):
        raw = self.rooms['Hive_Map02']
        _, groups, batches = s.names(raw, 1)
        hammer = batches.index('Hammer Object')
        out, removed = s.drop_commands(raw, 1, lambda g, c: any(hammer in s.targets(a) for a in s.actions(c)))
        self.assertEqual([g for g, _ in removed], [0])
        self.assertEqual(s.counts(out, 1), s.counts(raw, 1))
        self.assertEqual(s.names(out, 1), s.names(raw, 1))
        old, new = self.groups(raw, 1), self.groups(out, 1)
        self.assertEqual(new[1:], old[1:])
        self.assertEqual(new[0].commands, tuple(c for c in old[0].commands if c != removed[0][1]))
        same, nothing = s.drop_commands(raw, 1, lambda g, c: False)
        self.assertEqual((same, nothing), (raw, []))


if __name__ == '__main__':
    unittest.main()
