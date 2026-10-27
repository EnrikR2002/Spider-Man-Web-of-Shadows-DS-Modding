"""Air chord isolation, velocity/weak-owner safety and lossless Reel In composition."""
from pathlib import Path
import struct
import unittest
from tests.arm_runtime import ArmProbe
from tests import test_hunter_kit as foundation
from tools import reel_in as s, hunter_kit as h, tasm_kit as kit, wos_tool as w
from tools.chapter_renewal_combat import asm


class Runtime(unittest.TestCase):
    at, state = 0x021a1000, 0x021a0000
    hero, mot, ctl, stats = foundation.Runtime.hero, foundation.Runtime.mot, foundation.Runtime.ctl, foundation.Runtime.stats
    enemy, em, config, line = foundation.Runtime.enemy, foundation.Runtime.em, foundation.Runtime.config, foundation.Runtime.line
    ec, wrapper, stack, end = 0x02213000, 0x02214000, foundation.Runtime.stack, foundation.Runtime.end
    values = dict(STATE=state, NATIVE_THINK=0x021c0000, OLD_ANIMATION=0x021c0100,
        OLD_UPDATE=0x021c0200, OLD_EFFECT=0x021c0300, BOSS_CONFIG=0x02190000,
        REEL_SCA=6100, REEL_GMB=6101, REEL_GAB=6102, WEB_HIT=0x021c0600,
        WEB_HAND=0x021c0700, WEB_RELEASE=0x021c0800)

    @classmethod
    def setUpClass(cls):
        text = Path(h.__file__).with_suffix('.s').read_text()
        for key, value in foundation.Runtime.values.items():
            text = text.replace(key, f'0x{value:08x}')
        names = ('ram_ok', 'owned', 'xy', 'unlink_target')
        cls.helpers = asm(text+'\n.word '+','.join(names), 0x021b1000)
        cls.values.update(zip(('SHARED_'+n.upper() for n in names), struct.unpack('<4I', cls.helpers[-16:])))
        labels = ('owned', 'active', 'select_target', 'cleanup', 'clamp', 'body_anchor')
        code = asm(s.source(cls.values)+'\n.word '+','.join(labels), cls.at)
        cls.labels = dict(zip(labels, struct.unpack('<6I', code[-24:])))
        cls.code = s.runtime(cls.at, cls.values)
        if code[:-24] != cls.code:
            raise AssertionError('Runtime label export changed code')

    def fixture(self, *, phase=0, form=1, owned=True, parent=True, state=19, x=30, heavy=False):
        p = foundation.Runtime().fixture(form=form, owned=parent, x=x)
        p.code(0x021b1000, self.helpers)
        p.code(self.at, self.code)
        for at, value in ((self.hero+4, 0), (self.hero+0x1c, 0x1800),
            (self.stats+12, 0), (self.stats+0x14, (int(parent)<<19) | (int(owned)<<20)), (self.mot+0x80, 20*4096),
            (self.mot+0x2ac, 0),
            (self.ctl+0x14, state), (self.ctl+0x24, 2), (self.ctl+0x80, 0),
            (self.em+0x1f8, self.ec), (self.ec+0x14, 39), (self.enemy+0x18, 0),
            (self.em+0x58, self.wrapper), (self.wrapper+0x190, 0), (self.wrapper+0x194, 6*4096),
            (self.wrapper+0x198, 0), (self.em+0x44, x*4096), (self.em+0x48, 0), (self.em+0x4c, 0),
            (self.enemy+0x1c, 0x3000), (self.enemy+0x40, self.values['BOSS_CONFIG'] if heavy else self.config)):
            p.put(at, value)
        for i in range(3):
            p.put(self.em+12+4*i, 4096)
            for j in range(3):
                p.put(self.em+0x20+12*i+4*j, 4096 if i == j else 0)
        if phase:
            for off, value in ((0, self.hero), (4, self.ctl), (8, self.enemy+4),
                (16, self.em), (20, self.values['BOSS_CONFIG'] if heavy else self.config),
                (24, 1), (28, 2), (32, 65), (44, 4), (52, int(heavy)), (88, 1), (112, self.hero+4)):
                p.put(self.state+off, value)
            p.put(self.enemy+4, self.state+8)
            p.put(self.hero+4, self.state+112)
        return p

    def stubs(self, calls, *, queued=(5,), live=True, hit=4):
        def peek(p, r, flags):
            r[0] = int(p.get(r[1]) in queued)
            return flags
        def consume(p, r, flags):
            calls.append(('consume', p.get(r[1])))
            return flags
        def alive(p, r, flags):
            r[0] = int(live and r[0] == self.enemy)
            return flags
        def hand(p, r, flags):
            p.put(r[1], 0)
            p.put(r[1]+4, 20*4096)
            return flags
        def spawn(p, r, flags):
            p.put(r[0], self.line)
            return flags
        def receive(p, r, flags):
            calls.append(('hit', *r[:4]))
            r[0] = hit
            return flags
        def release(p, r, flags):
            calls.append(('release', r[0]))
            for off in range(0, 16, 4):
                p.put(r[0]+off, 0)
            return flags
        def nop(p, r, flags):
            return flags
        def face(p, r, flags):
            p.put(self.mot+0x180, p.get(r[1]))
            return flags
        return {0x020cff0c: peek, 0x020cfc34: consume, 0x02152c68: alive,
            self.values['WEB_HAND']: hand, self.values['WEB_HIT']: receive,
            self.values['WEB_RELEASE']: release, 0x0205f844: spawn,
            0x020672d0: nop, 0x0206632c: nop, 0x02072860: face}

    def run_entry(self, p, entry=0, *, regs=None, stops=None, **kw):
        r = list(range(100, 116)) if regs is None else list(regs)
        r[13:] = [self.stack, self.end, self.at+4*entry]
        return p.run(r, 0xa000001f, stops or {self.end, self.values['NATIVE_THINK'], self.values['OLD_UPDATE']}, kw.get('stubs'))

    def test_only_purchased_black_air_up_a_starts_and_links_both_actors(self):
        p = self.fixture()
        calls = []
        regs = list(range(100, 116)); regs[0] = self.ctl
        out, _, pc = self.run_entry(p, regs=regs, stubs=self.stubs(calls))
        self.assertEqual((pc, out[0], out[13], calls), (self.end, 51, self.stack, [('consume', 5)]))
        self.assertEqual(out[4:12], regs[4:12])
        self.assertEqual([p.get(self.state+i) for i in (0, 4, 8, 24, 112)],
                         [self.hero, self.ctl, self.enemy+4, 1, self.hero+4])
        self.assertEqual((p.get(self.hero+4), p.get(self.enemy+4)), (self.state+112, self.state+8))
        for kwargs in ({'form': 0}, {'owned': False}, {'parent': False}, {'state': 0}, {'state': 45}, {'state': 63}):
            p = self.fixture(**kwargs); calls = []
            out, _, pc = self.run_entry(p, regs=regs, stubs=self.stubs(calls))
            self.assertEqual((pc, out[0], calls, p.get(self.state+24)), (self.values['NATIVE_THINK'], self.ctl, [], 0))
        for direction, queued in ((0, (5,)), (4, (5,)), (6, (5,)), (2, (3, 5)), (2, (4, 5)), (2, (6,)), (2, ())):
            p = self.fixture(); p.put(self.ctl+0x24, direction); calls = []
            _, _, pc = self.run_entry(p, regs=regs, stubs=self.stubs(calls, queued=queued))
            self.assertEqual((pc, calls, p.get(self.state+24)), (self.values['NATIVE_THINK'], [], 0))

    def test_selector_does_not_steal_close_above_behind_or_out_of_range_native_a(self):
        regs = list(range(100, 116)); regs[0] = self.ctl
        for x, y in ((-20, 0), (37, 0), (20, -21), (20, 33), (6, 20)):
            p = self.fixture(x=x); p.put(self.em+0x80, y*4096); calls = []
            _, _, pc = self.run_entry(p, regs=regs, stubs=self.stubs(calls))
            self.assertEqual((pc, calls), (self.values['NATIVE_THINK'], []), (x, y))

    def test_below_is_symmetric_and_nearby_below_behind_turns_natively(self):
        for x, facing in ((0, 0), (0, 1), (-6, 1), (6, 0)):
            p = self.fixture(x=x); p.put(self.mot+0x180, facing)
            r = list(range(100, 116)); r[0] = self.ctl
            out, _, pc = self.run_entry(p, regs=r, stubs=self.stubs([]))
            self.assertEqual((pc, out[0], p.get(self.state+24)), (self.end, 51, 1))
            self.assertEqual(p.get(self.mot+0x180), facing if x == 0 else int(x > 0))

    def test_victim_velocity_is_bounded_and_requires_live_airborne_identity(self):
        regs = list(range(100, 116)); regs[4] = self.enemy
        p = self.fixture(phase=1, state=51); calls = []
        self.run_entry(p, 2, regs=regs, stubs=self.stubs(calls))
        self.assertEqual((p.get(self.enemy+0x18), p.get(self.enemy+0x1c)), (0xffffc000, 0x4000))
        for kwargs, edit in (({'heavy': True}, None), ({}, (self.ec+0x14, 37)),
            ({}, (self.state+112, 0)), ({}, (self.em, self.enemy+4)),
            ({}, (self.enemy+0x44, 0)), ({}, (self.enemy+0x40, self.config+4)),
            ({}, (self.ctl+0x14, 63)), ({}, (self.stats, 66)), ({'owned': False}, None)):
            p = self.fixture(phase=1, state=51, **kwargs)
            if edit: p.put(*edit)
            self.run_entry(p, 2, regs=regs, stubs=self.stubs([]))
            self.assertEqual((p.get(self.enemy+0x18), p.get(self.enemy+0x1c)), (0, 0x3000))

    def test_zero_hp_launch_and_heavy_zip_never_moves_the_heavy(self):
        regs = list(range(100, 116)); regs[4] = self.hero
        for known_heavy, ignored in ((False, False), (True, False), (False, True)):
            p = self.fixture(phase=1, state=51, heavy=known_heavy); p.put(self.state+80, 0)
            calls = []
            self.run_entry(p, 2, regs=regs, stubs=self.stubs(calls, hit=1 if ignored else 4))
            hits = [c for c in calls if c[0] == 'hit']
            self.assertEqual(hits, [] if known_heavy else [('hit', self.enemy, 0x25, 0, self.hero)])
            self.assertEqual(p.get(self.state+52), int(known_heavy or ignored))
            self.assertEqual((p.get(self.enemy+0x18), p.get(self.enemy+0x1c)), (0, 0x3000))
            if known_heavy or ignored:
                self.assertLessEqual(p.get(self.hero+0x18), 0x2800)
                self.assertEqual((p.get(self.line+0x80), p.get(self.line+0x84)), (0, 6*4096))

    def test_a_reused_action_clock_cannot_cast_before_the_new_clip_loads(self):
        p = self.fixture(phase=1, state=51); p.put(self.state+28, 0)
        calls = []
        regs = list(range(100, 116)); regs[4] = self.hero
        for clock in (9, 1):
            p.put(self.mot+0x178, clock)
            self.run_entry(p, 2, regs=regs, stubs=self.stubs(calls))
            self.assertFalse(any(c[0] == 'hit' for c in calls))
        p.put(self.mot+0x178, 2)
        self.run_entry(p, 2, regs=regs, stubs=self.stubs(calls))
        self.assertEqual(len([c for c in calls if c[0] == 'hit']), 1)

    def test_combo_recoil_is_one_impulse_only_for_a_descending_air_string(self):
        regs = list(range(100, 116)); regs[4] = self.hero
        for entry, vy in ((15, -100), (19, -100), (51, -100), (51, 0x2000)):
            p = self.fixture(phase=1, state=51)
            p.put(self.state+124, entry); p.put(self.hero+0x1c, vy)
            self.run_entry(p, 2, regs=regs, stubs=self.stubs([]))
            self.assertEqual(p.get(self.hero+0x1c), 0x1800 if entry == 51 and vy <= 0 else vy & 0xffffffff)
            p.put(self.hero+0x1c, -111)
            self.run_entry(p, 2, regs=regs, stubs=self.stubs([]))
            self.assertEqual(p.get(self.hero+0x1c), -111 & 0xffffffff)

    def test_heavy_anchor_uses_native_scaled_rotated_draw_pose_without_actor_writes(self):
        p = self.fixture(heavy=True)
        p.put(self.wrapper+0x190, 4096); p.put(self.wrapper+0x194, 6*4096)
        p.put(self.em+12, 8192); p.put(self.em+0x10, 6144)
        p.put(self.em+0x48, 12*4096)
        output = self.stack-0x100
        regs = list(range(100, 116)); regs[:2] = [self.enemy, output]
        regs[13:] = [self.stack, self.end, self.labels['body_anchor']]
        before = {at: p.get(at) for at in (self.enemy+0x18, self.enemy+0x1c, self.em+0x7c, self.em+0x80)}
        out, _, _ = p.run(regs, 0x1f, {self.end})
        self.assertEqual((out[0], p.get(output), p.get(output+4)), (1, 32*4096, 21*4096))
        self.assertEqual({at: p.get(at) for at in before}, before)
        self.assertEqual((out[4:12], out[13]), (regs[4:12], self.stack))
        for at, value in ((self.em+0x20, 0), (self.em+0x24, 4096),
                          (self.em+0x2c, -4096), (self.em+0x30, 0)):
            p.put(at, value)
        out, _, _ = p.run(regs, 0x1f, {self.end})
        self.assertEqual((out[0], p.get(output), p.get(output+4)), (1, 21*4096, 14*4096))
        for at, value in ((self.em+0x58, 0), (self.wrapper+0x194, 17*4096),
                          (self.em+0x10, 8193), (self.em+0x24, 4097)):
            p = self.fixture(heavy=True); p.put(at, value)
            out, _, _ = p.run(regs, 0x1f, {self.end})
            self.assertEqual(out[0], 0)

    def test_cleanup_keeps_line_clear_separate_and_does_not_touch_replaced_hero(self):
        for replaced in (False, True):
            p = self.fixture(phase=1, state=51)
            p.put(self.state+92, 1); p.put(self.state+56, 1)
            p.put(self.hero+0x18, 123); p.put(self.enemy+0x18, 456)
            if replaced:
                p.put(self.state+112, 0)
                p.put(self.hero+4, 0)
            r = list(range(100, 116)); r[13:] = [self.stack, self.end, self.labels['cleanup']]
            p.run(r, 0x1f, {self.end}, self.stubs([]))
            self.assertEqual(p.get(self.hero+0x18), 123 if replaced else 0)
            self.assertEqual(p.get(self.enemy+0x18), 0)
            self.assertEqual([p.get(self.state+i) for i in (0, 4, 8, 24, 96, 112)], [0]*6)
            self.assertEqual((p.get(self.hero+4), p.get(self.enemy+4)), (0, 0))

    def test_cleanup_preserves_a_later_native_reaction_velocity(self):
        p = self.fixture(phase=1, state=51)
        p.put(self.state+92, 1); p.put(self.ec+0x14, 42)
        p.put(self.enemy+0x18, 0x1234)
        r = list(range(100, 116)); r[13:] = [self.stack, self.end, self.labels['cleanup']]
        p.run(r, 0x1f, {self.end}, self.stubs([]))
        self.assertEqual((p.get(self.enemy+0x18), p.get(self.enemy+0x1c)), (0x1234, 0x3000))

    def test_a_real_floor_contact_lands_immediately_but_wall_ceiling_and_rising_contacts_do_not(self):
        for normal, vy, lands in ((4096, 0, True), (2000, -100, True), (0, -100, False),
                                  (-4096, 0, False), (4096, 100, False)):
            p = self.fixture(phase=1, state=51)
            p.put(self.mot+0x2ac, normal); p.put(self.hero+0x1c, vy)
            r = list(range(100, 116)); r[0] = self.ctl
            out, _, pc = self.run_entry(p, regs=r, stubs=self.stubs([], queued=()))
            self.assertEqual((pc, out[0], p.get(self.state+24)), (self.end, 24 if lands else 51, 0 if lands else 1))

    def test_private_animation_avoids_older_air_attack_routes_with_registers_preserved(self):
        p = self.fixture(phase=1, state=51)
        r = list(range(100, 116)); r[0], r[4] = 1, self.mot
        out, flags, pc = self.run_entry(p, 1, regs=r, stops={0x02070488})
        self.assertEqual((pc, out[:13], out[13]), (0x02070488, r[:13], self.stack))
        self.assertEqual([p.get(self.stack+i) for i in (0x2c, 0x38, 0x3c)], [6100, 6101, 6102])
        self.assertFalse(flags & 0x40000000)

    def test_chosen_y_starts_a_fresh_native_string_at_arrival_and_unpaid_r_releases(self):
        for queued in ((1,), (3,)):
            p = self.fixture(phase=1, state=51); p.put(self.state+48, 1)
            p.put(self.ctl+0x80, 1)
            calls = []
            r = list(range(100, 116)); r[0] = self.ctl
            out, _, pc = self.run_entry(p, regs=r, stubs=self.stubs(calls, queued=queued))
            self.assertEqual((pc, out[0]), (self.end, 51 if queued == (1,) else 19))
            self.assertIn(('consume', queued[0]), calls)
            self.assertEqual([p.get(self.state+i) for i in (0, 8, 24, 96, 112)], [0]*5)
            self.assertEqual(p.get(self.stats+12), 0)
            if queued == (1,):
                self.assertEqual(p.get(self.ctl+0x80), 0)

    def test_attack_effect_skip_is_only_the_synchronous_zero_damage_attacker_and_target(self):
        for guard, damage, same_attacker, same_target in ((1, 0, True, True), (0, 0, True, True),
            (1, 4096, True, True), (1, 0, False, True), (1, 0, True, False)):
            p = self.fixture(phase=1, state=51)
            p.put(self.state+36, guard)
            victim_ctl, attacker_cell, amount = 0x02230000, 0x02231000, 0x02232000
            p.put(self.stack+0x1d0, amount); p.put(amount, damage)
            p.put(victim_ctl+0x44, self.enemy if same_target else self.enemy+4)
            p.put(attacker_cell, self.hero if same_attacker else self.hero+4)
            r = list(range(100, 116)); r[5], r[6] = attacker_cell, victim_ctl
            out, flags, pc = self.run_entry(p, 3, regs=r, stops={0x02095670, self.values['OLD_EFFECT']})
            self.assertEqual(pc, 0x02095670 if guard and not damage and same_attacker and same_target else self.values['OLD_EFFECT'])
            self.assertEqual((out[:13], out[13], flags), (r[:13], self.stack, 0xa000001f))


@unittest.skipUnless(s.PARENT_PATH.exists(), 'private published parent missing')
class Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = s.PARENT_PATH.read_bytes()
        cls.after, cls.report = s.apply_rom(cls.before)

    def test_existing_resources_native_kit_and_unrelated_arm_words_stay_exact(self):
        an, ab = s.assets.resources(self.before); bn, bb = s.assets.resources(self.after)
        self.assertEqual([n for n, a, b in zip(an, ab, bb) if a != b],
                         ['American.strings', 'English.strings', 'GlobFiles.txt'])
        def arm(raw):
            hdr = w.parse_header(raw)
            return raw[hdr['arm9_offset']:hdr['arm9_offset']+hdr['arm9_size']]
        a, b = arm(self.before), arm(self.after)
        rt = self.report['runtime']
        self.assertEqual(a[kit.SOURCE:kit.SOURCE+kit.RESERVE], b[kit.SOURCE:kit.SOURCE+kit.RESERVE])
        allowed = set()
        for off, size in ((kit.TABLE_POINTERS, 8), (kit.ARENA_LOWER, 4), (h.BLACK_POINTER, 4),
                          (h.BLACK_COUNT, 4), (s.oscorp_resources.COUNT_OFFSET, 4),
                          *((r['site']-kit.BASE, 4) for r in rt['hooks'])):
            allowed.update(range(off, off+size))
        self.assertTrue(all(i in allowed for i, (x, y) in enumerate(zip(a[:rt['source_offset']], b)) if x != y))
        self.assertEqual(len(b)-len(a), rt['allocation_bytes'])
        for e in w.nitrofs_entries(self.before):
            if e['name'] != 'Glob.bin':
                n = next(x for x in w.nitrofs_entries(self.after) if x['name'] == e['name'])
                self.assertEqual(self.before[e['start']:e['end']], self.after[n['start']:n['end']])

    def test_new_row_owns_bit84_requires_web_yank_and_preserves_prices(self):
        header = w.parse_header(self.after)
        arm = self.after[header['arm9_offset']:header['arm9_offset']+header['arm9_size']]
        off = kit.SOURCE+self.report['runtime']['shop']-kit.TARGET
        self.assertEqual(struct.unpack_from('<3I', arm, off+9*32), (393, 392, kit.NO_EVENT))
        self.assertEqual(w.u32(arm, off+7*32+8), 393)
        self.assertEqual([w.u32(arm, off+i*32+28) for i in range(10)],
                         [75, 125, 150, 150, 200, 225, 125, 100, 150, 150])
        from tools.gmb import Gmb
        from tools.grip_compression import CompressedBlob
        names, blobs = s.assets.resources(self.after)
        idle = Gmb.parse(CompressedBlob.parse(blobs[names.index('spd_Idle.gmb')]).decoded)
        reel = Gmb.parse(CompressedBlob.parse(blobs[names.index('zz_R36_Reel.gmb')]).decoded)
        self.assertEqual(reel.record_count, 14)
        for a, b in zip(idle.channels, reel.channels):
            self.assertTrue(all(rec in a.records for rec in b.records))


if __name__ == '__main__':
    unittest.main()
