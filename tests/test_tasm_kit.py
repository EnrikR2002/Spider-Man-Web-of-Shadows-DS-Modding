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
        # v0.10.0: the second block is pinned too and its hooks land on its table.
        code2 = kit.code_bytes(2)
        self.assertEqual(w.sha256(code2), kit.CODE2_SHA256)
        self.assertLessEqual(len(code2), kit.KIT2_CODE)
        for site, (offset, _) in kit.HOOKS2.items():
            self.assertEqual(struct.unpack_from('<I', code2, offset)[0] >> 24, 0xEA, hex(site))

    def test_kit_arm9_is_pinned_and_release_profile_matches(self):
        self.assertEqual(w.sha256(self.arm9(self.kit)), kit.ARM9_SHA256)
        released, _ = cp.apply_rom(self.rom, kit.RELEASE_PROFILE)
        self.assertEqual(released, self.kit)
        self.assertTrue(kit.uses_kit(kit.RELEASE_PROFILE))
        self.assertFalse(kit.uses_kit(release_info.PROFILE))

    def test_arm9_changes_are_confined_to_hooks_and_tables(self):
        old, new = self.arm9(self.parent), self.arm9(self.kit)
        allowed = set()
        for site in (*kit.HOOKS, *kit.HOOKS2, *kit.RESTORE, *kit.EVENT_BOUNDS):
            allowed |= set(range(site - kit.BASE, site - kit.BASE + 4))
        for at in (kit.RED_POINTER, kit.RED_COUNT, kit.BOTH_POINTER, kit.BOTH_COUNT):
            allowed |= set(range(at, at + 4))
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
        for site, (_, original) in kit.HOOKS2.items():
            self.assertEqual(w.u32(old, site - kit.BASE), original)
            self.assertEqual(w.u32(new, site - kit.BASE), kit.branch(site, kit.KIT2_BASE + kit.HOOKS2[site][0]))
        # Second block: code, then zeros up to the shop rows; state stays zero.
        block = new[kit.SOURCE + kit.KIT2_OFFSET:kit.SOURCE + kit.KIT2_OFFSET + kit.KIT2_SPACE]
        code2 = kit.code_bytes(2)
        self.assertEqual(block[:len(code2)], code2)
        self.assertEqual(block[len(code2):kit.SHOP_OFFSET], bytes(kit.SHOP_OFFSET - len(code2)))
        # v0.13.0: 13 Red rows end before the dial; the ten Both Suits rows sit in the tail of the state
        # area, past everything the code keeps there. All the rest is zero.
        red_end = kit.SHOP_OFFSET + (7 + len(kit.SHOP_ROWS)) * 32
        state = kit.KIT2_STATE - kit.KIT2_BASE
        self.assertLessEqual(red_end, kit.DIAL_OFFSET)
        self.assertEqual(block[red_end:kit.BOTH_OFFSET], bytes(kit.BOTH_OFFSET - red_end))   # dial, used state: zero in a kit ROM
        self.assertGreaterEqual(kit.BOTH_OFFSET, state + kit.KIT2_STATE_USED)
        self.assertEqual(block[kit.BOTH_OFFSET + 10 * 32:], bytes(kit.KIT2_SPACE - kit.BOTH_OFFSET - 10 * 32))
        self.assertLessEqual(kit.BOTH_OFFSET + 10 * 32, kit.KIT2_SPACE)
        # The chapter's strength dial is empty in a kit ROM (tools/midnight_chapter.py fills it).
        self.assertLessEqual(kit.DIAL_OFFSET + 2 * kit.DIAL_ROOMS, state)
        self.assertEqual(state, 0x1C00)
        # Every state offset the second block's source names stays below KIT2_STATE_USED.
        import re
        source = (kit.Path(kit.__file__).with_name('tasm_kit2.s')).read_text(encoding='utf-8')
        used = [int(x, 16) for x in re.findall(r'\[r(?:4|5|6|10),#0x([0-9a-f]+)\]', source)]
        self.assertLess(max(x for x in used if x < 0x400), kit.KIT2_STATE_USED)
        self.assertIn('add r0,r0,#0x1c0', source)                          # the built hit: 0x1BC..0x23F
        self.assertIn('add r1,r10,#0x240', source)                         # Overclock cooldowns: 0x240..0x26F
        self.assertEqual(kit.IMAGE, kit.RESERVE)

    def test_red_shop_gains_rows_on_free_ability_bits(self):
        old, new = self.arm9(self.parent), self.arm9(self.kit)
        self.assertEqual(w.u32(new, kit.RED_POINTER), kit.KIT2_BASE + kit.SHOP_OFFSET)
        self.assertEqual(w.u32(new, kit.RED_COUNT), 13)
        self.assertEqual([row[0] for row in kit.SHOP_ROWS], ['web_rush', 'ricochet', 'momentum', 'overclock', 'dragnet', 'vortex'])
        table = kit.SOURCE + kit.KIT2_OFFSET + kit.SHOP_OFFSET
        self.assertEqual(new[table:table + 7 * 32], old[kit.RED_TABLE:kit.RED_TABLE + 7 * 32])
        self.assertEqual(new[kit.RED_TABLE:kit.RED_TABLE + 7 * 32], old[kit.RED_TABLE:kit.RED_TABLE + 7 * 32])
        native = {struct.unpack_from('<I', old, base + 32 * row)[0] + level
                  for base, count in ((0x120260, 7), (0x120340, 7), (0x120420, 7), (0x120680, 12), (0x1201A0, 6), (0x120500, 12))
                  for row in range(count) for level in range(struct.unpack_from('<I', old, base + 32 * row + 24)[0])}
        for index, (key, event, price, *texts) in enumerate(kit.SHOP_ROWS):
            row = struct.unpack_from('<8I', new, table + (7 + index) * 32)
            first = kit.STRING_COUNT + 3 * index
            self.assertEqual(row, (event, kit.NO_EVENT, kit.NO_EVENT, first, first + 1, first + 2, 1, price))
            # Above the native 73 ability bits (and the sentinel), inside the third word.
            self.assertTrue(kit.NO_EVENT < event <= 404 and event not in native, key)
            self.assertEqual(kit.SHOP_BITS[key], event - 309)
            self.assertEqual(kit.SHOP_TEXTS[3 * index:3 * index + 3], tuple(texts))
        self.assertEqual(sorted(kit.SHOP_BITS.values()), [74, 75, 76, 77, 78, 79, 80, 81, 82])
        # The masks the second block tests in ability word 2 (bit - 64).
        source = (kit.Path(kit.__file__).with_name('tasm_kit2.s')).read_text(encoding='utf-8')
        for key, needle in (('overclock', 'mov r1,#0x10000\n  bl k2_owned'), ('dragnet', 'mov r1,#0x20000\n  bl k2_owned'),
                            ('vortex', 'ldr r1,lit3_00040000\n  bl k2_owned')):
            self.assertIn(f'{1 << (kit.SHOP_BITS[key] - 64):#x}'[2:], needle)
            self.assertIn(needle, source, key)
        # v0.11.0: the Both Suits list moves too and gains the Vitality chain.
        self.assertEqual(w.u32(new, kit.BOTH_POINTER), kit.KIT2_BASE + kit.BOTH_OFFSET)
        self.assertEqual(w.u32(new, kit.BOTH_COUNT), 10)
        table = kit.SOURCE + kit.KIT2_OFFSET + kit.BOTH_OFFSET
        self.assertEqual(new[table:table + 7 * 32], old[kit.BOTH_TABLE:kit.BOTH_TABLE + 7 * 32])
        self.assertEqual(new[kit.BOTH_TABLE:kit.BOTH_TABLE + 7 * 32], old[kit.BOTH_TABLE:kit.BOTH_TABLE + 7 * 32])
        events = [row[1] for row in kit.BOTH_ROWS]
        for index, (key, event, price, *texts) in enumerate(kit.BOTH_ROWS):
            row = struct.unpack_from('<8I', new, table + (7 + index) * 32)
            first = kit.STRING_COUNT + 3 * (len(kit.SHOP_ROWS) + index)
            required = events[index - 1] if index else kit.NO_EVENT              # each level needs the one before
            dependent = events[index + 1] if index + 1 < len(events) else kit.NO_EVENT   # and cannot be refunded under the next
            self.assertEqual(row, (event, required, dependent, first, first + 1, first + 2, 1, price))
            self.assertTrue(kit.NO_EVENT < event <= 404 and event not in native, key)
            self.assertEqual(kit.SHOP_BITS[key], event - 309)
        self.assertEqual(events, sorted(events))
        self.assertEqual([row[2] for row in kit.BOTH_ROWS], sorted(row[2] for row in kit.BOTH_ROWS))
        # Bounds: events below 405 reach bits below 96; the fourth word (a counter) is never addressed.
        for site, (original, word) in kit.EVENT_BOUNDS.items():
            self.assertEqual((w.u32(old, site - kit.BASE), w.u32(new, site - kit.BASE)), (original, word))
        self.assertEqual({word & 0xFF for _, word in kit.EVENT_BOUNDS.values()}, {0x72, 0x60})
        self.assertEqual(0x123 + 0x72 - 309, 96)

    def test_shop_texts_are_appended_once(self):
        from tools.qol_suits_menu import decode_grown, slot_count
        clean = self.clean('English.strings')
        slots = StringSlots(clean)
        first = kit.shop_strings(slots, slots.repack(clean, kit.TEXT_EDITS))
        self.assertEqual(slot_count(first), kit.STRING_COUNT + len(kit.SHOP_TEXTS))
        self.assertEqual([decode_grown(first, kit.STRING_COUNT + i) for i in range(len(kit.SHOP_TEXTS))], list(kit.SHOP_TEXTS))
        self.assertEqual(decode_grown(first, 74), kit.TEXT_EDITS[74])
        self.assertEqual(kit.shop_strings(slots, first), first)      # a previous kit overlay is rewritten, not grown
        # A v0.10.0 overlay holds nine texts and a v0.11.0/v0.12.0 one eighteen: they are rewritten and the rest appended.
        for held in kit.PREVIOUS_TEXTS:
            older = slots.grown(slots.repack(clean, kit.TEXT_EDITS), {}, appended=['old'] * held)
            self.assertEqual(kit.shop_strings(slots, older), first)
        # The next release repacks this overlay first: appended slots must survive an edit.
        again = slots.repack(first, {74: 'Options v9.9.9'})
        self.assertEqual(slot_count(again), kit.STRING_COUNT + len(kit.SHOP_TEXTS))
        self.assertEqual(decode_grown(again, kit.STRING_COUNT), kit.SHOP_TEXTS[0])
        self.assertEqual(decode_grown(again, 74), 'Options v9.9.9')
        with self.assertRaises(ValueError):
            kit.shop_strings(slots, slots.grown(first, {}, appended=['extra']))

    def test_blocks_only_call_each_other_through_their_entry_tables(self):
        import re
        folder = kit.Path(kit.__file__).parent
        one, two = ((folder / name).read_text(encoding='utf-8') for name in ('tasm_kit.s', 'tasm_kit2.s'))

        def calls(text, low, high):
            found = {int(x, 16) for x in re.findall(r'^\s*b\w*\s+0x([0-9a-fA-F]{8})', text, re.M)}
            return {x for x in found if low <= x < high}
        self.assertEqual(calls(one, kit.KIT2_BASE, kit.KIT2_BASE + kit.KIT2_SPACE),
                         {kit.KIT2_BASE + offset for offset in (0x00, 0x04, 0x08, 0x0C, 0x14, 0x18)})
        code2 = kit.code_bytes(2)
        for offset in (0x00, 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C):
            self.assertEqual(struct.unpack_from('<I', code2, offset)[0] >> 24, 0xEA)
        exports = calls(two, kit.KIT_BASE, kit.KIT_BASE + kit.CODE_SPACE)
        self.assertTrue(exports and exports <= {kit.KIT_BASE + offset for offset in range(0x38, 0x50, 4)})
        code = kit.code_bytes()
        for address in exports:
            self.assertEqual(struct.unpack_from('<I', code, address - kit.KIT_BASE)[0] >> 24, 0xEA)

    def test_momentum_only_skips_samples_without_an_active_attack_box(self):
        # Doubling a step at clock c skips a point in samples c+1..c+2 (rates up to 1.3).
        import re
        from pathlib import Path
        from tools import grip_compression, gmb
        source = (kit.Path(kit.__file__).with_name('tasm_kit2.s')).read_text(encoding='utf-8')
        words = re.search(r'^momentum_blocked:\s*\.word\s+(.+)$', source, re.M).group(1)
        table = [int(x, 0) for x in words.split(',')]
        # Action 56 (Snap Sweep) plays GroundAttack15's payload; 57..62 their own.
        clips = (15, 12, 13, 14, 15, 16, 17)
        self.assertEqual(len(table), len(clips))
        lasts = []
        for mask, number in zip(table, clips):
            name = f'spd_GroundAttack{number}.gmb'
            overlay = Path(mod.ROOT) / 'mods' / name
            data = gmb.Gmb.parse(grip_compression.decode(overlay.read_bytes() if overlay.exists() else self.clean(name)))
            active = set()
            for channel in data.channels:
                flags = [channel.words(f)[5] == 1 for f in range(data.record_count)] if channel.kind == 3 else []
                if any(flags) and not all(flags):       # the attack box; body boxes are always on
                    active |= {f for f, on in enumerate(flags) if on}
            self.assertTrue(active, name)
            wanted = sum(1 << c for c in range(32) if {c + 1, c + 2} & active)
            self.assertEqual(mask, wanted, name)
            lasts.append(data.record_count - 1)
        # v0.11.0: the last sample is never skipped either (the string blocker decides repeat/end on it).
        last = re.search(r'^momentum_last:\s*\.word\s+(0x[0-9A-Fa-f]+),\s*(0x[0-9A-Fa-f]+)', source, re.M).groups()
        self.assertEqual(list(b''.join(struct.pack('<I', int(x, 16)) for x in last))[:len(clips)], lasts)
        self.assertIn('sub r0,r0,#2', source)

    def test_no_instruction_branches_to_itself(self):
        # Keystone encodes 'bleq label' as a branch to its own address (found by the v0.13.0 crash hunt).
        import re
        for block, name in ((1, 'tasm_kit.s'), (2, 'tasm_kit2.s')):
            code = kit.code_bytes(block)
            for at in range(0, len(code), 4):
                word = struct.unpack_from('<I', code, at)[0]
                self.assertFalse((word & 0x0EFFFFFF) == 0x0AFFFFFE and word >> 28 != 0xF, f'{name} {at:#x}')
            source = re.sub(r'//.*', '', (kit.Path(kit.__file__).with_name(name)).read_text(encoding='utf-8'))
            self.assertEqual(re.findall(r'^\s*bl(?:eq|ne|hs|cs|cc|mi|pl|vs|vc|hi|ge|gt)\s', source, re.M), [], name)

    def test_vortex_steps_follow_their_actions_attack_windows(self):
        # Each step's contacts are the first active sample of its native action's attack windows; the
        # area hit follows one update later. Tables are words: a .byte run shifts later absolute branches.
        import re
        from pathlib import Path
        from tools import grip_compression, gmb
        source = (kit.Path(kit.__file__).with_name('tasm_kit2.s')).read_text(encoding='utf-8')
        self.assertNotIn('.byte', re.sub(r'//.*', '', source))
        self.assertNotIn('.byte', re.sub(r'//.*', '', (kit.Path(kit.__file__).with_name('tasm_kit.s')).read_text(encoding='utf-8')))
        actions = [int(x) for x in re.search(r'^web_actions:\s*\.word\s+([0-9, ]+)', source, re.M).group(1).replace(' ', '').split(',') if x]
        self.assertEqual(actions, [0, 57, 56, 59, 49])
        words = [int(x, 16) for x in re.findall(r'0x([0-9A-Fa-f]{8})', re.search(r'^web_contacts:.*\n((?:\s+\.word .*\n){5})', source, re.M).group(1))]
        self.assertEqual(len(words), 10)
        self.assertTrue(all((word >> 25) & 7 != 5 for word in words))
        payload = {57: 12, 56: 15, 59: 14}                              # action -> GroundAttack payload (Snap plays G15)
        for step in (1, 2, 3):
            name = f'spd_GroundAttack{payload[actions[step]]}.gmb'
            overlay = Path(mod.ROOT) / 'mods' / name
            data = gmb.Gmb.parse(grip_compression.decode(overlay.read_bytes() if overlay.exists() else self.clean(name)))
            active = set()
            for channel in data.channels:
                flags = [channel.words(f)[5] == 1 for f in range(data.record_count)] if channel.kind == 3 else []
                if any(flags) and not all(flags): active |= {f for f, on in enumerate(flags) if on}
            starts = sorted(f for f in active if f - 1 not in active)
            contacts = [words[2 * step + k] for k in range(2)]
            wanted = starts + ([8] if step == 1 else [])   # authored return lash; native GMB stays intact
            self.assertEqual([c & 0xFF for c in contacts if c & 0xFF != 255], wanted, name)
            for c in contacts:
                if c & 0xFF != 255:
                    self.assertIn(c >> 8 & 0xFF, (0x04, 0x1F))
                    self.assertTrue(0x800 <= (c >> 16 & 0xFF) << 8 <= 0x1000)
        self.assertEqual(words[:2] + words[8:], [0xFF] * 4)             # no step 0; the heave has no contact
        # Routes: the heave and the three steps each have their own clip on their action.
        routes = {(action, kind): name for action, kind, name in kit.ROUTES}
        for step, kind in ((4, 10), (1, 11), (2, 12), (3, 13)):
            self.assertIn((actions[step], kind), routes)
        self.assertIn('and r1,r0,#3', source)                           # route kind = 10 + (step & 3)

    def test_v0_11_tuning_lives_in_the_second_block(self):
        # Reflex/Sense attack speed 1.10/1.20 (native 1.15/1.3), Vitality damage 1/1.25, 1/1.5, 1/1.75,
        # bar tint in BG palette colours 25..28, dial table at its fixed address.
        import re
        source = (kit.Path(kit.__file__).with_name('tasm_kit2.s')).read_text(encoding='utf-8')
        literals = {name: int(value, 16) for name, value in re.findall(r'^(lit2_\w+):\s*\.word\s+0x([0-9A-Fa-f]+)', source, re.M)}
        self.assertEqual(literals['lit2_0000119a'] / 4096, 4506 / 4096)
        self.assertAlmostEqual(literals['lit2_0000119a'] / 4096, 1.10, 3)
        self.assertAlmostEqual(literals['lit2_00001333'] / 4096, 1.20, 3)
        # With Momentum owned, combo tier 3 and up restores the native 1.15 / 1.3 (the tuning block's own values).
        self.assertEqual((literals['lit2_00001266'], literals['lit2_000014cc']), (0x1266, 0x14CC))
        self.assertIn('cmp r3,#3\n  ldrge r1,lit2_00001266\n  ldrge r2,lit2_000014cc', source)
        self.assertEqual(literals['lit2_02156fc0'], kit.KIT2_BASE + kit.DIAL_OFFSET)
        self.assertEqual(literals['lit2_05000032'], 0x05000000 + 2 * 25)
        for level, scale in zip((1.25, 1.5, 1.75), (205, 171, 146)):
            self.assertAlmostEqual(256 / scale, level, 1)
            self.assertIn(f'movne r2,#{scale}', source)
        colors = [int(x, 16) for x in re.search(r'^vit_colors:.*\n((?:\s+\.word .*\n){4})', source, re.M).group(1).replace('.word', '').replace(',', ' ').split()]
        self.assertEqual(len(colors), 8)
        self.assertEqual((colors[0] & 0x7FFF, colors[0] >> 16, colors[1] & 0xFFFF, colors[1] >> 16),
                         (0x000D, 0x0C77, 0x18DA, 0x253D))                   # level 0: HUDTop_8's own reds
        self.assertTrue(all((word >> 25) & 7 != 5 for word in colors))       # no word reads as a branch (assembler check)
        self.assertEqual(kit.DIAL_ROOMS, 40)
        self.assertIn('cmp r1,#40', source)

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
