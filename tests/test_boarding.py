"""Execute Boarding ARM ownership, weak references, hit clocks and release paths."""
import struct
import unittest
from pathlib import Path
from tests import test_hunter_kit as foundation
from tools import boarding as b, hunter_kit as h, tasm_kit as kit, wos_tool as w


def ct_signed(value):
    return value-(1 << 32) if value & 0x80000000 else value


class Runtime(unittest.TestCase):
    at, state = 0x021a1000, 0x021a0000
    hero, mot, ctl, stats = foundation.Runtime.hero, foundation.Runtime.mot, foundation.Runtime.ctl, foundation.Runtime.stats
    enemy, em, ec = foundation.Runtime.enemy, foundation.Runtime.em, 0x02213000
    stack, end = foundation.Runtime.stack, foundation.Runtime.end
    values = dict(STATE=state, YANK_STATE=state+0x4000, YANK_RECORDS=state+0x5000,
        REEL_STATE=state+0x6000, METEOR_STATE=state+0x7000, YANK_CLEAR=0x021c0400,
        OLD_THINK=0x021c0000, OLD_ANIMATION=0x021c0100, OLD_UPDATE=0x021c0200,
        OLD_EFFECT=0x021c0300, WEB_HIT=0x021c0600, WEB_HAND=0x021c0700, WEB_RELEASE=0x021c0800,
        BOSS_CONFIG=foundation.Runtime.config)
    for i, part in enumerate(b.art.PARTS):
        values[part.upper()+'_LEFT_SCA'] = 6250+i
        for j, ext in enumerate(('SCA', 'GMB', 'GAB')):
            values[part.upper()+'_'+ext] = 6200+3*i+j

    @classmethod
    def setUpClass(cls):
        source = Path(h.__file__).with_suffix('.s').read_text()
        for key, value in foundation.Runtime.values.items():
            source = source.replace(key, f'0x{value:08x}')
        cls.helpers = b.asm(source+'\n.word ram_ok,xy,unlink_target', 0x021b1000)
        cls.values.update(zip(('SHARED_RAM_OK', 'SHARED_XY', 'SHARED_UNLINK_TARGET'), struct.unpack('<3I', cls.helpers[-12:])))
        labels = ('mini_ok', 'target_ok', 'select_target', 'cleanup', 'update', 'observe_mini', 'release_yank', 'shoulder_height')
        code = b.asm(b.source(cls.values)+'\n.word '+','.join(labels), cls.at)
        cls.labels = dict(zip(labels, struct.unpack('<8I', code[-32:])))
        cls.code = b.runtime(cls.at, cls.values)
        assert code[:-32] == cls.code

    def fixture(self, *, phase=0, owned=True, form=1, x=6, facing=1, mini=False):
        p = foundation.Runtime().fixture(form=form, x=x, facing=facing)
        p.code(self.at, self.code)
        p.code(0x021b1000, self.helpers)
        p.code(self.state, bytes(256))
        for key in ('YANK_STATE', 'YANK_RECORDS', 'REEL_STATE', 'METEOR_STATE'):
            p.code(self.values[key], bytes(512))
        for at, val in ((self.stats+0x14, (1<<24) if owned else 0), (self.hero+4, 0),
            (self.hero+0x1c, 0), (self.mot+0x2ac, 0), (self.mot+0x16c, self.values['HOLD_GAB']),
            (self.mot+0x258, 1), (self.ctl+0x14, 51 if phase else 15),
            (self.ctl+0x24, 0), (self.em+0x1f8, self.ec), (self.em+0x180, facing),
            (self.ec+0x44, self.enemy), (self.ec+0x14, 0)):
            p.put(at, val)
        p.code(0x02145a48, struct.pack('<5H', 0, 0x10 if facing else 0x20, 0, 0, 0))
        p.put(kit.KIT_STATE, 100)
        p.put(0x02145c5c, self.stats)
        if mini:
            for at, val in ((self.enemy, 0x0212ce38), (self.enemy+8, 0x0212ce54),
                (self.em+0x10, 4915),
                (self.enemy+0xfc, 327680), (self.enemy+0x100, 327680), (self.enemy+0xf4, 0),
                (self.enemy+0xf8, 0x0213754c), (self.ec, 0x02133c18),
                (self.state+192, self.enemy+4), (self.state+212, 100), (self.state+216, 65)):
                p.put(at, val)
            p.put(kit.KIT_STATE+0x20, 0)
        if phase:
            p.put(self.mot+0x80, 10*4096)
            for off, val in ((0, self.hero), (4, self.ctl), (8, self.enemy+4),
                (16, self.em), (20, 0x0213754c if mini else self.values['BOSS_CONFIG']),
                (24, phase), (32, 65), (56, 1), (88, facing), (112, self.hero+4),
                (136, self.ec), (140, 0x0212ce38 if mini else 0x021301d0)):
                p.put(self.state+off, val)
            p.put(self.enemy+4, self.state+8)
            p.put(self.hero+4, self.state+112)
        return p

    def stubs(self, calls, queued=(), live=True, hit=4):
        def peek(p, r, flags):
            r[0] = int(p.get(r[1]) in queued)
            return flags
        def consume(p, r, flags):
            calls.append(('consume', p.get(r[1])))
            return flags
        def fresh(p, r, flags):
            r[0] = int(live and r[0] == self.enemy)
            return flags
        def strike(p, r, flags):
            calls.append(('hit', *r[:4]))
            r[0] = hit
            return flags
        def transition(p, r, flags):
            p.put(r[0]+0x14, r[1])
            return flags
        def clear(p, r, flags):
            calls.append(('yank-clear', r[0]))
            return flags
        def hand(p, r, flags):
            for i in range(3):
                p.put(r[1]+4*i, 0)
            return flags
        return {0x020cff0c: peek, 0x020cfc34: consume, 0x02152c68: fresh,
            self.values['WEB_HIT']: strike, 0x02077844: transition,
            self.values['WEB_RELEASE']: foundation.Runtime.result(0),
            self.values['YANK_CLEAR']: clear, self.values['WEB_HAND']: hand,
            0x0206632c: foundation.Runtime.result(0), 0x020739b4: foundation.Runtime.result(0)}

    def call(self, p, entry=0, *, actor=None, stubs=None, argument=None):
        regs = list(range(100, 116))
        regs[0] = self.ctl if entry == 0 else actor or self.hero
        if argument is not None:
            regs[1] = argument
        regs[4] = actor or self.hero
        regs[5] = self.state
        regs[6] = self.hero
        regs[7] = self.mot
        regs[13:] = [self.stack, self.end, self.labels[entry] if isinstance(entry, str) else self.at+4*entry]
        before = list(regs)
        result = p.run(regs, 0xa000001f, {self.end, self.values['OLD_THINK'], self.values['OLD_UPDATE']}, stubs)
        self.assertEqual(result[0][4:12], before[4:12])
        self.assertEqual(result[0][13], self.stack)
        return result

    def test_owned_air_approach_both_facings_begins_without_a_built_hit(self):
        for face in (0, 1):
            p, calls = self.fixture(facing=face, x=6 if face else -6), []
            regs, _, pc = self.call(p, stubs=self.stubs(calls))
            self.assertEqual((regs[0], pc, calls), (51, self.end, []))
            self.assertEqual([p.get(self.state+i) for i in (0, 4, 8, 24, 112)],
                [self.hero, self.ctl, self.enemy+4, 1, self.hero+4])

    def test_native_fallback_for_ownership_form_direction_range_and_priority(self):
        for options in ({'owned': False}, {'form': 0}, {'x': 10}, {'x': -6}):
            p, calls = self.fixture(**options), []
            _, _, pc = self.call(p, stubs=self.stubs(calls))
            self.assertEqual((pc, calls, p.get(self.state+24)), (self.values['OLD_THINK'], [], 0), options)
        for at, value in ((0x02145a4a, 0), (self.ctl+0x14, 0), (self.mot+0x2ac, 4096),
                          (self.em, self.hero), (self.ec+0x14, 15), (self.ec+0x14, 16)):
            p, calls = self.fixture(), []
            p.put(at, value)
            _, _, pc = self.call(p, stubs=self.stubs(calls))
            self.assertEqual((pc, calls), (self.values['OLD_THINK'], []), (hex(at), value))
        for queue in ((3,), (4,)):
            p, calls = self.fixture(), []
            _, _, pc = self.call(p, stubs=self.stubs(calls, queued=queue))
            self.assertEqual((pc, calls), (self.values['OLD_THINK'], []))

    def test_native_mini_layout_and_all_subtype_parameters_are_guarded(self):
        for kind, param in enumerate((0x0213754c, 0x021375a0, 0x02137648, 0x0213769c)):
            p = self.fixture(mini=True)
            p.put(self.enemy+0xf4, kind); p.put(self.enemy+0xf8, param)
            out, _, _ = self.call(p, 'mini_ok', actor=self.enemy)
            self.assertEqual(out[0], self.enemy)
        for at, val in ((self.enemy+8, 0), (self.enemy+0xfc, 0), (self.enemy+0xfc, 327681),
                        (self.enemy+0xf4, 4), (self.enemy+0xf8, 0x021375a0),
                        (self.em, self.hero), (self.ec, 0), (self.ec+0x44, self.hero)):
            p = self.fixture(mini=True); p.put(at, val)
            out, _, _ = self.call(p, 'mini_ok', actor=self.enemy)
            self.assertEqual(out[0], 0, (hex(at), val))

    def test_native_mini_fresh_observer_and_weak_reference_do_not_duplicate_links(self):
        p = self.fixture(mini=True)
        p.put(self.state+192, 0); p.put(self.enemy+4, 0)
        for _ in range(2):
            self.call(p, 'observe_mini', actor=self.enemy)
        self.assertEqual([p.get(self.state+i) for i in (192, 196, 212)], [self.enemy+4, 0, 100])
        self.assertEqual(p.get(self.enemy+4), self.state+192)
        self.assertEqual(p.get(self.enemy+0xfc), 327680)
        p.put(self.state+212, 97)
        out, _, pc = self.call(p, stubs=self.stubs([]))
        self.assertEqual(pc, self.values['OLD_THINK'])

    def test_animation_routes_both_facings_and_all_phases_without_changing_other_caller_slots(self):
        for facing in (0, 1):
            for phase in range(1, 7):
                p = self.fixture(phase=phase, facing=facing)
                for i in range(6):
                    p.put(self.stack+0x2c+4*i, 200+i)
                r = list(range(100, 116))
                r[0], r[4] = 1, self.mot
                r[13:] = [self.stack, self.end, self.at+4]
                out, _, pc = p.run(r, 0xa000001f, {0x02070488, self.values['OLD_ANIMATION']})
                part = b.art.PARTS[0 if phase == 6 else phase-1].upper()
                sca = self.values[part+('_SCA' if facing else '_LEFT_SCA')]
                self.assertEqual(pc, 0x02070488)
                self.assertEqual(out[:15], r[:15])
                self.assertEqual([p.get(self.stack+0x2c+4*i) for i in range(6)],
                    [sca, 201, 202, self.values[part+'_GMB'], self.values[part+'_GAB'], 205])

    def test_mini_zip_arrival_requires_held_toward_and_releases_its_line(self):
        for x, held, expected in ((6, 0x10, 1), (6, 0, 0), (6, 0x20, 0), (0, 0x20, 1), (0, 0x10, 1)):
            p, calls = self.fixture(phase=6, mini=True, x=x), []
            p.put(0x02145a4a, held)
            p.put(self.state+96, foundation.Runtime.line+4)
            p.put(foundation.Runtime.line+4, self.state+96)
            p.put(self.state+100, 0)
            self.call(p, 'update', stubs=self.stubs(calls))
            self.assertEqual((p.get(self.state+24), p.get(self.state+96), calls), (expected, 0, []))

    def test_yank_handoff_clears_the_master_then_the_actual_four_extra_records(self):
        p, calls = self.fixture(), []
        p.put(self.values['YANK_STATE']+120, 5)
        self.call(p, 'release_yank', stubs=self.stubs(calls))
        self.assertEqual(calls, [('yank-clear', self.values['YANK_STATE'])]+
            [('yank-clear', self.values['YANK_RECORDS']+128*i) for i in range(4)])

    def test_hold_has_no_ride_timeout_or_built_hits(self):
        p, calls = self.fixture(phase=2), []
        p.put(self.state+84, 1000000)
        p.put(self.mot+0x178, 23)
        self.call(p, 'update', stubs=self.stubs(calls))
        self.assertEqual((p.get(self.state+24), calls), (2, []))
        self.assertLessEqual(abs(ct_signed(p.get(self.hero+0x18))), 0x4000)
        self.assertLessEqual(abs(ct_signed(p.get(self.hero+0x1c))), 0x4000)

    def test_y_and_a_choose_one_authored_attack_without_automatic_damage(self):
        for command, phase in ((1, 3), (5, 4)):
            p, calls = self.fixture(phase=2), []
            out, _, _ = self.call(p, stubs=self.stubs(calls, queued=(command,)))
            self.assertEqual((out[0], p.get(self.state+24), calls), (51, phase, [('consume', command)]))

    def test_rake_deals_one_native_hit_only_on_its_authored_contact(self):
        p, calls = self.fixture(phase=3), []
        p.put(self.mot+0x16c, self.values['RAKE_GAB'])
        for clock in (5, 6, 6, 9):
            p.put(self.mot+0x178, clock)
            self.call(p, 'update', stubs=self.stubs(calls))
        self.assertEqual(calls, [('hit', self.enemy, 4, 4096, self.hero)])
        self.assertEqual(p.get(self.state+48), 1)
        p.put(self.mot+0x178, 13)
        self.call(p, 'update', stubs=self.stubs(calls))
        self.assertEqual(p.get(self.state+24), 2)

    def test_wing_rip_hits_once_and_kicks_only_miguel_away_on_both_facings(self):
        for face in (0, 1):
            p, calls = self.fixture(phase=4, facing=face), []
            p.put(self.enemy+0x18, 123); p.put(self.enemy+0x1c, 456)
            p.put(self.mot+0x16c, self.values['RIP_GAB'])
            for clock in (8, 9, 10, 14):
                p.put(self.mot+0x178, clock)
                self.call(p, 'update', stubs=self.stubs(calls))
            self.assertEqual(calls, [('hit', self.enemy, 4, 8192, self.hero)])
            self.assertEqual((p.get(self.enemy+0x18), p.get(self.enemy+0x1c)), (123, 456))
            self.assertEqual(p.get(self.state+24), 5)
            self.assertEqual(ct_signed(p.get(self.hero+0x18)), -0x2800 if face else 0x2800)
            self.assertEqual(p.get(self.hero+0x1c), 0x4000)

    def test_successful_rake_cannot_skip_the_next_tear_or_contaminate_reboarding(self):
        p, calls = self.fixture(phase=3), []
        p.put(self.mot+0x16c, self.values['RAKE_GAB']); p.put(self.mot+0x178, 6)
        self.call(p, 'update', stubs=self.stubs(calls))
        self.assertEqual(p.get(self.state+44), 4)
        p.put(self.mot+0x178, 13)
        self.call(p, 'update', stubs=self.stubs(calls))
        for ride in range(2):
            if ride:
                p.put(self.mot+0x16c, self.values['KICK_GAB']); p.put(self.mot+0x178, 14)
                self.call(p, 'update', stubs=self.stubs(calls))
                p.put(0x02145a4a, 0)
                self.call(p, stubs=self.stubs(calls))
                p.put(0x02145a4a, 0x10); p.put(self.state+44, 4)
                self.call(p, stubs=self.stubs(calls))
                p.put(self.ctl+0x14, 51)
                p.put(self.mot+0x16c, self.values['LATCH_GAB']); p.put(self.mot+0x178, 5)
                self.call(p, 'update', stubs=self.stubs(calls))
            self.call(p, stubs=self.stubs(calls, queued=(5,)))
            self.assertEqual((p.get(self.state+24), p.get(self.state+44)), (4, 0))
            p.put(self.mot+0x16c, self.values['RIP_GAB'])
            for clock in range(9):
                p.put(self.mot+0x178, clock)
                self.call(p, 'update', stubs=self.stubs(calls))
                self.assertEqual(p.get(self.state+24), 4, (ride, clock))
            p.put(self.mot+0x178, 9)
            self.call(p, 'update', stubs=self.stubs(calls))
            self.assertEqual(p.get(self.state+24), 5)
        self.assertEqual([c for c in calls if c[0] == 'hit'],
            [('hit', self.enemy, 4, 4096, self.hero)]+[('hit', self.enemy, 4, 8192, self.hero)]*2)

    def test_lethal_tear_kicks_without_dereferencing_a_destroyed_target(self):
        for changed_room in (False, True):
            p, calls = self.fixture(phase=4), []
            p.put(self.mot+0x16c, self.values['RIP_GAB']); p.put(self.mot+0x178, 9)
            stubs = self.stubs(calls)
            def destroy(probe, regs, flags):
                calls.append(('hit', *regs[:4]))
                probe.put(self.state+8, 0)
                for address, length in ((self.enemy, 0x100), (self.em, 0x400), (self.ec, 0xa0)):
                    for at in range(address, address+length):
                        probe.memory.pop(at, None)
                if changed_room:
                    probe.put(self.stats, 66)
                regs[0] = 4
                return flags
            stubs[self.values['WEB_HIT']] = destroy
            self.call(p, 'update', stubs=stubs)
            self.assertEqual(p.get(self.state+24), 0 if changed_room else 5)
            self.assertEqual(p.get(self.state+8), 0)
            if not changed_room:
                self.assertEqual((ct_signed(p.get(self.hero+0x18)), p.get(self.hero+0x1c)), (-0x2800, 0x4000))
                p.put(self.mot+0x16c, self.values['KICK_GAB']); p.put(self.mot+0x178, 4)
                self.call(p, 'update', stubs=self.stubs(calls))
                self.assertEqual(p.get(self.state+24), 5)

    def test_native_boss_attacks_release_before_another_rake_can_land(self):
        for mini, states in ((False, (15, 16)), (True, (37, 38, 42, 43, 45, 46, 91))):
            for state in states:
                p, calls = self.fixture(phase=3, mini=mini), []
                p.put(self.ec+0x14, state)
                p.put(self.mot+0x16c, self.values['RAKE_GAB']); p.put(self.mot+0x178, 8)
                self.call(p, 'update', stubs=self.stubs(calls))
                self.assertEqual((p.get(self.state+24), p.get(self.state+72), calls), (0, 1, []), (mini, state))

    def test_mini_hurt_and_turn_do_not_reverse_the_latched_shoulder_or_shake_it_off(self):
        for state in (63, 65, 67, 68, 74, 75, 77, 79):
            p, calls = self.fixture(phase=2, mini=True), []
            p.put(self.ec+0x14, state)
            p.put(self.em+0x180, 0)
            self.call(p, 'update', stubs=self.stubs(calls))
            self.assertEqual((p.get(self.state+24), p.get(self.state+88), p.get(self.mot+0x180), calls), (2, 1, 1, []))
            self.assertEqual(p.get(self.hero+0x18), 6144)

    def test_grip_height_matches_native_mini_scale_and_bounds_unknown_values(self):
        for scale, height in ((4915, 32768), (5734, 40956), (8192, 49152), (0, 40960), (9000, 40960)):
            p = self.fixture(mini=True)
            p.put(self.em+0x10, scale)
            out, _, _ = self.call(p, 'shoulder_height', actor=self.enemy)
            self.assertEqual(out[0], height)

    def test_separated_or_collision_blocked_ride_releases_without_remote_damage(self):
        for at, value in ((self.em+0x7c, 25*4096), (self.em+0x80, 20*4096)):
            p, calls = self.fixture(phase=3), []
            p.put(at, value)
            p.put(self.mot+0x16c, self.values['RAKE_GAB']); p.put(self.mot+0x178, 8)
            self.call(p, 'update', stubs=self.stubs(calls))
            self.assertEqual((p.get(self.state+24), calls), (0, []))

    def test_r_and_invalidation_release_without_paid_air_dodge_or_overwriting_hurt(self):
        p, calls = self.fixture(phase=2), []
        p.put(self.stats+12, 0)
        out, _, _ = self.call(p, stubs=self.stubs(calls, queued=(3,)))
        self.assertEqual((out[0], calls, p.get(self.state+24)), (19, [('consume', 3)], 0))
        for at, val in ((self.hero+0x34, 0), (self.stats+0x14, 0), (self.stats+0x84, 0),
                        (self.stats, 66), (self.ctl+0x14, 63), (self.em, self.hero),
                        (self.enemy+0x44, 0), (self.em+0x1f8, self.ctl), (self.state+112, 0)):
            p, calls = self.fixture(phase=2), []
            p.put(at, val)
            self.call(p, 'update', stubs=self.stubs(calls))
            self.assertEqual((p.get(self.state+24), p.get(self.state+8), p.get(self.state+112), calls), (0, 0, 0, []), (hex(at), val))
            if at == self.ctl+0x14:
                self.assertEqual(p.get(at), 63)


class LabScanner(unittest.TestCase):
    def test_mini_scan_rejects_stale_motion_controller_and_health(self):
        from tools.boarding_lab import minis
        ram = bytearray(4*1024*1024)
        actor, motion, controller = 0x1000, 0x2000, 0x3000
        for at, val in ((actor, 0x0212ce38), (actor+8, 0x0212ce54),
            (actor+0x30, kit.BASE+motion), (actor+0xfc, 327680), (actor+0x100, 327680),
            (motion, kit.BASE+actor), (motion+0x1f8, kit.BASE+controller),
            (controller, 0x02133c18), (controller+0x44, kit.BASE+actor)):
            struct.pack_into('<I', ram, at, val)
        self.assertEqual(len(minis(ram)), 1)
        for at, value in ((motion, 0), (controller+0x44, 0), (actor+0xfc, 0), (actor+0x100, 1)):
            old = w.u32(ram, at)
            struct.pack_into('<I', ram, at, value)
            self.assertEqual(minis(ram), [])
            struct.pack_into('<I', ram, at, old)


@unittest.skipUnless(b.PARENT_PATH.exists(), 'Published private parent missing')
class Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = b.PARENT_PATH.read_bytes()
        cls.after, cls.report = b.apply_rom(cls.before)

    def test_exact_parent_resource_and_arm_scope_and_unchanged_existing_shop_rows(self):
        self.assertRaises(ValueError, b.apply_rom, bytes(512))
        names, old = b.assets.resources(self.before)
        nn, new = b.assets.resources(self.after)
        self.assertEqual(names, nn[:len(names)])
        self.assertEqual({n for n, x, y in zip(names, old, new) if x != y}, {'American.strings', 'English.strings', 'GlobFiles.txt'})
        def arm(raw):
            hh = w.parse_header(raw)
            return raw[hh['arm9_offset']:hh['arm9_offset']+hh['arm9_size']]
        a, c = arm(self.before), arm(self.after)
        rt = self.report['runtime']
        self.assertEqual(a[kit.SOURCE:kit.SOURCE+kit.RESERVE], c[kit.SOURCE:kit.SOURCE+kit.RESERVE])
        allowed = set()
        for off, size in ((kit.TABLE_POINTERS, 8), (kit.ARENA_LOWER, 4), (h.BLACK_POINTER, 4),
            (h.BLACK_COUNT, 4), (b.oscorp_resources.COUNT_OFFSET, 4),
            *((row['site']-kit.BASE, 4) for row in rt['hooks'])):
            allowed.update(range(off, off+size))
        self.assertTrue(all(i in allowed for i, (x, y) in enumerate(zip(a[:rt['source_offset']], c)) if x != y))
        prior = kit.SOURCE+w.u32(a, h.BLACK_POINTER)-kit.TARGET
        shop = kit.SOURCE+rt['shop']-kit.TARGET
        self.assertEqual(a[prior:prior+352], c[shop:shop+352])
        self.assertEqual(struct.unpack_from('<3I', c, shop+352), (397, kit.NO_EVENT, kit.NO_EVENT))
        self.assertEqual(w.u32(c, shop+380), 275)
        self.assertEqual(self.report['ownership']['bit'], 88)

    def test_private_motion_counts_and_collision_have_no_native_attack_boxes(self):
        from tools.gmb import Gmb
        from tools.sca import Sca
        from tools.grip_compression import CompressedBlob
        names, blobs = b.assets.resources(self.after)
        idle = Gmb.parse(CompressedBlob.parse(blobs[names.index('spd_Idle.gmb')]).decoded)
        for part, clip in zip(b.art.PARTS, b.art.CLIPS):
            motion = Sca.parse(blobs[names.index('zz_B38_'+part+'.sca')])
            body = Gmb.parse(CompressedBlob.parse(blobs[names.index('zz_B38_'+part+'.gmb')]).decoded)
            self.assertEqual((motion.frame_count, motion.joint_count, body.record_count), (clip.samples, 37, clip.samples))
            self.assertEqual([c.kind for c in body.channels], [c.kind for c in idle.channels])
            for a, c in zip(idle.channels, body.channels):
                self.assertTrue(all(record in a.records for record in c.records))


if __name__ == '__main__':
    unittest.main()
