"""Bounded Ballast material and Freight staging contracts."""
import struct
import unittest

from tests.arm_runtime import ArmProbe
from tests import test_crane_drop
from tools import crane_drop as d, crane_visibility as c, room_script as s, spider2099 as assets, wos_tool as w
from tools.actor_resources import ModelSheet
from tools.model_geometry import ModelGeometry
from tools.nitro_texture import TextureArchive
from tools.qol_suits_menu import decode_grown
from tools.room_entities import Entities
from tools.room_events import Events
from tools.room_objects import RoomObjects


@unittest.skipUnless((c.ROOT / 'work/research-libs/keystone').exists(), 'private Keystone missing')
class HeightAdapter(unittest.TestCase):
    def test_only_the_upper_freight_container_gets_the_higher_target(self):
        at, row, stack, ret = 0x021A1000, 0x02203000, 0x023F0000, 0x021F0000
        for room, x, increment in ((97, c.UPPER_X, 40), (97, c.LOWER_X, 0), (100, c.UPPER_X, 0), (105, c.UPPER_X, 0)):
            with self.subTest(room=room, x=x):
                p = ArmProbe()
                p.code(at, c.height_adapter(at))
                p.put(row, room)
                p.put(stack, x * d.U)
                p.put(stack + 4, 12345)
                regs = [0] * 16
                regs[5], regs[7], regs[13], regs[14], regs[15] = row, 20 * d.U, stack, ret, at
                result, _, _ = p.run(regs, 0, {ret})
                self.assertEqual((result[0], result[7], result[13]), (12345, (20 + increment) * d.U, stack))
                self.assertEqual(p.get(stack), x * d.U)

    def test_full_drop_motion_uses_the_selected_deck_and_preserves_other_rooms(self):
        base = test_crane_drop.Motion()
        rows = bytearray(d.table())
        struct.pack_into('<2i', rows, 4, 20 * d.U, 0)
        helper = 0x021A2000
        code = bytearray(d.drop_motion(base.at, base.old, base.rows))
        site = code.index(struct.pack('<I', 0xE59D0004))
        struct.pack_into('<I', code, site, c.crane_row.branch(base.at + site, helper, link=True))
        for room, x, start, target in ((97, c.UPPER_X, 60, 40), (97, c.LOWER_X, 20, 0), (100, c.UPPER_X, 142, 68)):
            with self.subTest(room=room, x=x):
                p = base.fixture(room=room, state=1, y=start * d.U, rows=rows)
                p.pos[0] = x * d.U
                p.code(base.at, bytes(code))
                p.code(helper, c.height_adapter(helper))
                for _ in range(100):
                    y, touched = base.tick(p)
                self.assertEqual((y, touched), (target * d.U, ['get', 'set', 'old'] * 100))


@unittest.skipUnless((c.ROOT / 'work/research-libs/keystone').exists(), 'private Keystone missing')
class SpawnAnchor(unittest.TestCase):
    at, ret, stack = 0x021A3000, 0x021F0000, 0x023E0000
    spawner, stats, manager, ref, anchor, dest = (0x02240000, 0x02241000, 0x02242000,
                                                  0x02243000, 0x02244000, 0x02245000)

    def invoke(self, *, room=97, mode=1, kind=1, owner=True, caller=True, burst=True,
               stats_ptr=None, manager_ptr=None, spawner_ptr=None, anchor_z=0, anchor_extra=0, alternate=False):
        p = ArmProbe()
        p.code(self.at, c.spawn_anchor_adapter(self.at))
        anchor = self.anchor + (4 if alternate else 0)
        for addr, value in ((self.stack + 0x1fc, 0x0204C64C if caller else 0x0204C650),
                            (self.stack + 0x1e4, self.spawner if spawner_ptr is None else spawner_ptr),
                            (self.spawner, 0x0212BDA4 if owner else 0x0212BDA0),
                            (self.spawner + 0x28, (244 if burst else 208) * d.U),
                            (self.spawner + 0x2c, (22 if burst else 88) * d.U),
                            (self.spawner + 0x30, (44 if burst else 212) * d.U),
                            (self.spawner + 0x34, (36 if burst else 112) * d.U),
                            (0x02145C5C, self.stats if stats_ptr is None else stats_ptr), (self.stats, room),
                            (0x02145C34, self.manager if manager_ptr is None else manager_ptr),
                            (self.ref, anchor), (anchor, 100 * d.U), (anchor + 4, 60 * d.U),
                            (anchor + 8, anchor_z), (anchor + 12, anchor_extra)):
            p.put(addr, value)
        p.memory[anchor + 0x10] = kind
        p.memory[self.manager + 0x1c5] = mode

        def native(probe, regs, flags):
            point = probe.get(regs[1])
            for j in range(3):
                probe.put(regs[0] + 4 * j, probe.get(point + 4 * j))
            regs[2], regs[1] = point, probe.get(point + 8)
            return flags

        regs = list(range(16))
        regs[0], regs[1], regs[13], regs[14], regs[15] = self.dest, self.ref, self.stack, self.ret, self.at
        out, flags, _ = p.run(regs, 0xA0000000, {self.ret}, {c.ANCHOR_NATIVE: native})
        self.assertEqual(out[0:4], [self.dest, anchor_z, anchor, 3])
        self.assertEqual(out[4:8], regs[4:8])
        self.assertEqual((out[12], out[13], flags), (regs[12], self.stack, 0xA0000000))
        return p.get(self.dest) // d.U, p.get(self.dest + 4) // d.U

    def test_only_the_active_freight_burst_uses_the_native_floor_points(self):
        self.assertEqual(self.invoke(mode=1), (228, 42))
        self.assertEqual(self.invoke(mode=2), (260, 2))
        self.assertEqual(self.invoke(mode=1, alternate=True), (208, 42))
        self.assertEqual(self.invoke(mode=2, alternate=True), (236, 2))
        for case in ({'room': 100}, {'mode': 0}, {'mode': 3}, {'kind': 5}, {'owner': False},
                     {'caller': False}, {'burst': False}, {'stats_ptr': 0}, {'stats_ptr': self.stats + 1},
                     {'manager_ptr': 0}, {'spawner_ptr': 0}, {'anchor_z': d.U}, {'anchor_extra': 1}):
            with self.subTest(case=case):
                self.assertEqual(self.invoke(**case), (100, 60))


@unittest.skipUnless(c.PARENT_PATH.exists(), 'published v0.39.0 build missing')
class Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = c.PARENT_PATH.read_bytes()
        cls.names, cls.original = assets.resources(cls.parent)
        cls.rom, cls.report = c.apply_rom(cls.parent)
        cls.new_names, cls.blobs = assets.resources(cls.rom)

    def raw(self, name, *, original=False):
        names, blobs = (self.names, self.original) if original else (self.new_names, self.blobs)
        return blobs[names.index(name)]

    def groups(self, raw):
        rec = RoomObjects.parse(raw).records[1]
        return Events.parse(rec.sections[1], rec.raw[3]).groups, s.names(raw, 1)

    def test_trigger_branches_are_exclusive_and_keep_the_original_crew(self):
        raw = self.raw(c.OBJ)
        groups, (_, labels, batches) = self.groups(raw)
        old, (_, old_labels, _) = self.groups(self.raw(c.OBJ, original=True))
        gate, lower = (batches.index(n) for n in ('Cargo Drop Gate', 'Lower Cargo Gate'))
        upper = groups[labels.index('Drop_Begin')].commands
        right = groups[labels.index('Right_Drop_Begin')].commands
        for commands in (upper, right):
            self.assertIn(s.deactivate(ag=gate), commands)
            self.assertIn(s.deactivate(ag=lower), commands)
        self.assertIn(s.activate(ag=lower), groups[labels.index('Drop_Arm')].commands)
        self.assertIn(s.activate(ag=batches.index('Dock Crew')), groups[labels.index('Right_Drop_Land')].commands)
        self.assertEqual(groups[labels.index('Right_Drop_Land')].commands.count(s.activate(ag=batches.index('Cargo Burst'))), 1)
        self.assertEqual(groups[labels.index('Drop_Land')].commands,
                         (s.set_var(c.MODE, 1), *old[old_labels.index('Drop_Land')].commands))
        self.assertEqual(groups[labels.index('Drop_Burst_Stop')].commands,
                         (s.set_var(c.MODE, 0), *old[old_labels.index('Drop_Burst_Stop')].commands))
        self.assertEqual(groups[labels.index('Right_Drop_Land')].commands[0], s.set_var(c.MODE, 2))
        self.assertEqual(groups[labels.index('Right_Drop_Burst_Stop')].commands[0], s.set_var(c.MODE, 0))
        for name in ('Drop_Rise', 'Drop_Clear'):
            self.assertEqual(groups[labels.index(name)], old[old_labels.index(name)])
        self.assertEqual(groups[0].commands, (s.set_var(c.MODE, 0), *old[0].commands))

    def test_lower_gate_and_placements_stay_in_freight(self):
        raw = self.raw(c.OBJ)
        names = s.names(raw, 1)[2]
        entities = Entities.parse(RoomObjects.parse(raw).records[1].sections[0])
        for name, xy in (('Cargo Drop', (c.UPPER_X, 60)), ('Cargo Drop Open', (c.UPPER_X, 40)),
                         ('Right Cargo Drop', (c.LOWER_X, 20)), ('Right Cargo Drop Open', (c.LOWER_X, 0)),
                         ('Lower Cargo Gate', (244, 18))):
            record = entities.batches[names.index(name)].records[0]
            self.assertEqual(struct.unpack_from('<2i', record), tuple(v * d.U for v in xy))
        old_raw = self.raw(c.OBJ, original=True)
        old_names = s.names(old_raw, 1)[2]
        old_entities = Entities.parse(RoomObjects.parse(old_raw).records[1].sections[0])
        self.assertEqual(entities.batches[names.index('Dock Crew')], old_entities.batches[old_names.index('Dock Crew')])
        old_burst = old_entities.batches[old_names.index('Cargo Burst')].records[0]
        new_burst = entities.batches[names.index('Cargo Burst')].records[0]
        self.assertEqual(old_burst[:16] + old_burst[20:], new_burst[:16] + new_burst[20:])
        self.assertEqual(struct.unpack_from('<2H', new_burst, 16), (88, 72))
        matching = [e for record in RoomObjects.parse(raw).records for e in Entities.parse(record.sections[0]).records
                    if len(e) == 28 and struct.unpack_from('<3iI2H', e) == (244 * d.U, 22 * d.U, 0, 4, 88, 72)]
        self.assertEqual(matching, [new_burst])
        self.assertNotIn('Right Cargo Burst', names)
        with self.assertRaises(ValueError):
            c.freight_script(raw)

    def test_rejects_an_occupied_route_variable_or_ambiguous_burst_signature(self):
        old = self.raw(c.OBJ, original=True)
        changed = s.extend_group(old, 1, 0, [s.set_var(c.MODE, 1)], prepend=True)
        with self.assertRaisesRegex(ValueError, 'route variable'):
            c.freight_script(changed)
        names = s.names(old, 1)[2]
        batches = Entities.parse(RoomObjects.parse(old).records[1].sections[0]).batches
        duplicate = bytearray(batches[names.index('Cargo Burst')].records[0])
        struct.pack_into('<2H', duplicate, 16, 88, 72)
        changed, _ = s.append_batch(old, 1, [(bytes(duplicate), 'EnemySpawner (Duplicate)')], 'Duplicate Burst')
        with self.assertRaisesRegex(ValueError, 'not unique'):
            c.freight_script(changed)
        obj = RoomObjects.parse(old)
        section = bytearray(obj.records[0].sections[3])
        _, head, count = struct.unpack_from('<HBB', section)
        index = next(i for i in range(count) if struct.unpack_from('<i', section, head + 20 * i + 16)[0] == 1)
        struct.pack_into('<i', section, head + 20 * index + 8, d.U)
        with self.assertRaisesRegex(ValueError, 'floor-anchor metadata'):
            c.freight_script(obj.replace_section(0, 3, section))

    def test_only_ballast_uses_the_private_direct_texture(self):
        sheet = ModelSheet.parse(self.raw('model_sheet.xbd'))
        old = ModelSheet.parse(self.raw('model_sheet.xbd', original=True))
        self.assertEqual(sheet.groups[c.GROUP][2], self.new_names.index(c.BALLAST_TEXTURE))
        self.assertEqual(sheet.groups[:c.GROUP], old.groups[:c.GROUP])
        self.assertEqual(sheet.groups[c.GROUP + 1:], old.groups[c.GROUP + 1:])
        t = TextureArchive.parse(self.raw(c.BALLAST_TEXTURE)).textures[0]
        self.assertEqual((t['format'], t['width'], t['height'], t['size']), (7, 64, 64, 8192))
        self.assertEqual(self.raw('zz_F22_Atlas.nsbtx'), self.raw('zz_F22_Atlas.nsbtx', original=True))

    def test_spawn_hooks_are_limited_to_the_three_verified_constructor_reads(self):
        old_h, new_h = w.parse_header(self.parent), w.parse_header(self.rom)
        old = self.parent[old_h['arm9_offset']:old_h['arm9_offset'] + old_h['arm9_size']]
        new = self.rom[new_h['arm9_offset']:new_h['arm9_offset'] + new_h['arm9_size']]
        base = 0x02000000
        self.assertEqual(w.u32(new, c.SPAWN_CALL - base), w.u32(old, c.SPAWN_CALL - base))
        for site in c.ANCHOR_SITES:
            self.assertEqual(w.u32(old, site - base), c.crane_row.branch(site, c.ANCHOR_NATIVE, link=True))
            self.assertEqual(w.u32(new, site - base), c.crane_row.branch(site, self.report['anchor_hook'], link=True))
        for cfg in c.CONFIGS:
            self.assertEqual(w.u32(old, c.kit.SOURCE + cfg - c.kit.TARGET + 4) & 0x33, 0)

    def test_freight_alone_receives_the_smaller_cargo_models(self):
        for name in d.MODELS:
            self.assertEqual(self.raw(name), self.raw(name, original=True))
        old, new = self.raw(d.MODELS[1], original=True), self.raw(c.CARGO_MODELS[1])
        old_model, new_model = ModelGeometry.parse(old), ModelGeometry.parse(new)
        self.assertEqual(w.u16(new, new_model.model + 36), w.u16(old, old_model.model + 36) + 16)
        self.assertEqual(w.u16(new, new_model.model + 38), w.u16(old, old_model.model + 38) + 4)
        colors = [args[0] for op, args in c.gpu_commands(new) if op == 0x20]
        self.assertIn(6 | 9 << 5 | 13 << 10, colors)
        self.assertEqual(colors.count(11 | 14 << 5 | 17 << 10), 4)
        h = w.parse_header(self.rom)
        arm = self.rom[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']]
        old_h = w.parse_header(self.parent)
        old_arm = self.parent[old_h['arm9_offset']:old_h['arm9_offset'] + old_h['arm9_size']]
        off = lambda a: c.kit.SOURCE + a - c.kit.TARGET
        rows = []
        at = off(c.WORLD)
        while w.u32(arm, at):
            room, kind, var, record, _ = struct.unpack_from('<5I', arm, at)
            if room in (97, 100, 105) and kind in (d.CLOSED, d.OPEN):
                rows.append((room, kind, self.new_names[w.u32(arm, off(record) + 8)]))
                if room == 97:
                    old_record = w.u32(old_arm, at + 12)
                    before, after = old_arm[off(old_record):off(old_record) + 64], arm[off(record):off(record) + 64]
                    self.assertEqual(before[:8] + before[12:], after[:8] + after[12:])
            at += 20
        for room, kind, model in rows:
            expected = c.CARGO_MODELS[kind == d.OPEN] if room == 97 else d.MODELS[kind == d.OPEN]
            self.assertEqual(model, expected)
        self.assertEqual(len(rows), 6)

    def test_other_rooms_and_unrelated_resources_remain_exact(self):
        changed = set(self.report['modified_resources'])
        self.assertEqual(changed, {c.BALLAST_MODEL, c.OBJ, 'American.strings', 'English.strings', 'GlobFiles.txt', 'model_sheet.xbd'})
        for name in ('zz_AR_DryDock_app.obj', 'zz_AR_CraneCrown_app.obj', 'zz_F22_maw.nsbmd', 'zz_F22_spore.nsbmd'):
            self.assertEqual(self.raw(name), self.raw(name, original=True))
        old, new = (RoomObjects.parse(self.raw(c.OBJ, original=previous)) for previous in (True, False))
        self.assertEqual(old.records[0].raw, new.records[0].raw)
        self.assertEqual(old.records[1].sections[2:], new.records[1].sections[2:])
        old_fs = {e['name']: self.parent[e['start']:e['end']] for e in w.nitrofs_entries(self.parent)}
        new_fs = {e['name']: self.rom[e['start']:e['end']] for e in w.nitrofs_entries(self.rom)}
        self.assertEqual(old_fs.keys(), new_fs.keys())
        for name in old_fs.keys() - {'Glob.bin'}:
            self.assertEqual(old_fs[name], new_fs[name], name)
        old_h, new_h = w.parse_header(self.parent), w.parse_header(self.rom)
        old_arm7 = self.parent[old_h['arm7_offset']:old_h['arm7_offset'] + old_h['arm7_size']]
        new_arm7 = self.rom[new_h['arm7_offset']:new_h['arm7_offset'] + new_h['arm7_size']]
        self.assertEqual(old_arm7, new_arm7)
        a, b = old_h['arm9_offset'], new_h['arm9_offset']
        start, end = c.kit.SOURCE, c.kit.SOURCE + c.kit.RESERVE
        self.assertEqual(self.parent[a + start:a + end], self.rom[b + start:b + end])

    def test_both_language_version_labels_match_the_candidate(self):
        for name in ('American.strings', 'English.strings'):
            raw = self.raw(name)
            self.assertEqual(decode_grown(raw, 50), f'TASM v{c.VERSION}\nPress a button to start')
            self.assertEqual(decode_grown(raw, 74), f'Options v{c.VERSION}')

    def test_rejects_any_nonparent_rom(self):
        with self.assertRaises(ValueError):
            c.apply_rom(self.rom)


if __name__ == '__main__':
    unittest.main()
