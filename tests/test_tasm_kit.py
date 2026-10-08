"""Red kit ARM9 extension, authored clips and kit release composition (clean ROM)."""
import struct
import unittest
import mod
from tools import combat_profile as cp, release_info, tasm_kit as kit, wos_tool as w
from tools import kit_clips
from tools.kit_choreography import Clip, catmull
from tools.sca import Sca
from tools.qol_suits_menu import StringSlots


class TasmKitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom, cls.glob, cls.manifest = mod.load_clean()
        cls.entries = {e['name']: e for e in cls.manifest['entries']}
        cls.parent, _ = cp.apply_rom(cls.rom, release_info.PROFILE)
        cls.kit, cls.log = kit.apply_rom(cls.parent)

    def clean(self, name):
        e = self.entries[name]
        return self.glob[e['offset']:e['offset'] + e['size']]

    def arm9(self, rom):
        h = w.parse_header(rom)
        return rom[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']]

    def test_code_is_pinned_and_fits_before_route_table(self):
        code = kit.code_bytes()
        self.assertEqual(w.sha256(code), kit.CODE_SHA256)
        self.assertLessEqual(len(code), kit.ROUTE_OFFSET)
        # Every installed hook lands on a branch-table entry.
        for site, (offset, _) in kit.HOOKS.items():
            word = struct.unpack_from('<I', code, offset)[0]
            self.assertEqual(word >> 24, 0xEA, hex(site))

    def test_kit_arm9_is_pinned_and_release_profile_matches(self):
        self.assertEqual(w.sha256(self.arm9(self.kit)), kit.ARM9_SHA256)
        released, _ = cp.apply_rom(self.rom, kit.RELEASE_PROFILE)
        self.assertEqual(released, self.kit)
        self.assertTrue(kit.uses_kit(kit.RELEASE_PROFILE))
        self.assertFalse(kit.uses_kit(release_info.PROFILE))

    def test_arm9_changes_are_confined_to_hooks_and_tables(self):
        old, new = self.arm9(self.parent), self.arm9(self.kit)
        allowed = set()
        for site in (*kit.HOOKS, *kit.RESTORE):
            allowed |= set(range(site - kit.BASE, site - kit.BASE + 4))
        for at in kit.IMPULSES:
            allowed |= set(range(at, at + 8))
        allowed |= set(range(kit.COUNT_OFFSET, kit.COUNT_OFFSET + 4))
        allowed |= set(range(kit.TABLE_POINTERS, kit.TABLE_POINTERS + 8))
        allowed |= set(range(kit.ARENA_LOWER, kit.ARENA_LOWER + 4))
        changed = {i for i in range(kit.SOURCE) if old[i] != new[i]}
        self.assertTrue(changed <= allowed, sorted(changed - allowed)[:8])
        for site, (_, original) in kit.HOOKS.items():
            self.assertEqual(w.u32(old, site - kit.BASE), original)
            self.assertEqual(w.u32(new, site - kit.BASE), kit.branch(site, kit.KIT_BASE + kit.HOOKS[site][0]))
        # The prior HUD/flow image is carried byte-for-byte; the kit follows it.
        self.assertEqual(new[kit.SOURCE:kit.SOURCE + kit.OLD_CODE], old[kit.SOURCE:kit.SOURCE + kit.OLD_CODE])
        start = kit.SOURCE + kit.OLD_STATE_END
        self.assertEqual(new[start:start + len(kit.code_bytes())], kit.code_bytes())
        self.assertEqual(w.u32(new, kit.ARENA_LOWER), kit.TARGET + kit.RESERVE)
        self.assertEqual(w.u32(new, kit.COUNT_OFFSET), kit.PARENT_COUNT + len(kit.EXTRA_NAMES))

    def test_route_rows_name_appended_resources(self):
        from tools import oscorp_resources as rush
        names = [e['name'] for e in self.manifest['entries']] + [*rush.EXTRA_NAMES, *kit.EXTRA_NAMES]
        self.assertEqual(len(self.manifest['entries']) + len(rush.EXTRA_NAMES), kit.PARENT_COUNT)
        rows = kit.route_table()
        for i, (action, route, name) in enumerate(kit.ROUTES):
            self.assertEqual(struct.unpack_from('<3I', rows, i * 12), (action, route, names.index(name)))
        self.assertEqual(rows[-12:], bytes(12))

    def test_kit_never_writes_the_false_actor_position_copies(self):
        # Spidey's actor allocation is 0xF4 bytes; +0x148/+0x180/+0x210/+0x2CC
        # are past its end. v0.4.0 Spider-Sense stored x there and corrupted
        # the heap (crash/freeze). Motion +0x180 is facing (read only).
        import re
        source = (kit.Path(kit.__file__).with_name('tasm_kit.s')).read_text(encoding='utf-8')
        stores = re.findall(r'^\s*str\w*\s+\w+,\s*\[\w+,\s*#(0x148|0x180|0x210|0x2cc)\]', source, re.M | re.I)
        self.assertEqual(stores, [])

    def test_unknown_parent_and_double_apply_rejected(self):
        with self.assertRaises(ValueError):
            kit.apply_rom(self.kit)
        with self.assertRaises(ValueError):
            kit.apply_rom(self.rom)

    def test_clips_match_native_sample_counts_and_bake_deterministically(self):
        for target, (source, name) in kit.CLIP_SOURCES.items():
            clip = kit_clips.CLIPS[name]
            self.assertEqual(Sca.parse(self.clean(source)).frame_count, clip.samples, name)
        first = kit.author_overlays(self.glob, self.entries)
        again = kit.author_overlays(self.glob, self.entries)
        self.assertEqual(first, again)
        for target, data in first.items():
            sca = Sca.parse(data)
            self.assertEqual(sca.to_bytes(), data)
            self.assertEqual(sca.joint_count, 37)

    def test_spin_legs_are_straight_blades_not_a_breakdance_v(self):
        # v0.2.1 player feedback: legs locked out in a wide, near-horizontal split.
        import math
        from tools.animation_rig import AnimationRig
        from tools.kit_choreography import Rig
        rig = Rig(Sca.parse(self.clean('spd_Idle.sca')), AnimationRig.parse(self.clean('spd.nsbmd')).parents)
        full = math.dist(rig.bind_p[26], rig.bind_p[27]) + math.dist(rig.bind_p[27], rig.bind_p[28])
        for s, pos in enumerate(rig.bake(kit_clips.SPIN)[2]):
            for hip, ankle in ((26, 28), (30, 32)):
                leg = [pos[ankle][i] - pos[hip][i] for i in range(3)]
                self.assertGreater(math.dist(pos[hip], pos[ankle]) / full, .94, s)
                self.assertLess(math.degrees(math.atan2(leg[1], math.hypot(leg[0], leg[2]))), 35., s)
            self.assertGreater(math.dist(pos[28], pos[32]), 9., s)

    def test_curves_hit_their_keys_and_reject_unknown_channels(self):
        keys = [(0, 0.), (3, 90.), (7, 10.)]
        for t, v in keys:
            self.assertAlmostEqual(catmull(keys, t), v)
        with self.assertRaises(ValueError):
            Clip('bad', 4, {'not_a_channel': [(0, 0.)]})

    def test_release_text_is_encodable_and_roundtrips(self):
        from tools.qol_suits_menu import COUNT, decode_grown
        slots = StringSlots(self.clean('English.strings'))
        changed = slots.repack(self.clean('English.strings'), kit.TEXT_EDITS)
        for index in range(COUNT):      # a grown tree (e.g. digit 7) re-encodes every slot
            self.assertEqual(decode_grown(changed, index), kit.TEXT_EDITS.get(index, slots.texts[index]))
        self.assertEqual(slots.repack(changed, kit.TEXT_EDITS), changed)

    def test_appended_slots_follow_the_native_ones(self):
        from tools.qol_suits_menu import COUNT, decode_grown, slot_count
        clean = self.clean('English.strings')
        slots = StringSlots(clean)
        grown = slots.grown(clean, {}, appended=['Midnight Line: the power is out.', 'Second line'])
        self.assertEqual(slot_count(grown), COUNT + 2)
        self.assertEqual([decode_grown(grown, i) for i in (COUNT, COUNT + 1)], ['Midnight Line: the power is out.', 'Second line'])
        self.assertEqual(decode_grown(grown, 50), slots.texts[50])
        slots.check_grown(grown)

    def test_grown_tree_adds_only_missing_bytes(self):
        from tools.qol_suits_menu import BASE, decode_grown
        clean = self.clean('English.strings')
        slots = StringSlots(clean)
        self.assertEqual(slots.missing_bytes({1: 'v0.7.0'}), [0x37])
        grown = slots.repack(clean, {1: 'v0.7.0'})
        self.assertEqual(grown[:BASE], clean[:BASE])
        self.assertEqual(w.u32(grown, BASE), w.u32(clean, BASE) + 4)        # one extra tree node
        self.assertEqual(decode_grown(grown, 1), 'v0.7.0')
        self.assertEqual(decode_grown(grown, 2), slots.texts[2])


if __name__ == '__main__':
    unittest.main()
