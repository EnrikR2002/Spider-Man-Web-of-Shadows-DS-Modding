"""ARM input/floor/ownership contracts and lossless composition for Meteor Catch."""
import struct
import unittest
from pathlib import Path
from tests import test_hunter_kit as foundation
from tools import meteor_catch as s, hunter_kit as h, tasm_kit as kit, wos_tool as w
from tools.chapter_renewal_combat import asm


class Runtime(unittest.TestCase):
    at, state = 0x021a1000, 0x021a0000
    hero, mot, ctl, stats = foundation.Runtime.hero, foundation.Runtime.mot, foundation.Runtime.ctl, foundation.Runtime.stats
    enemy, em, config = foundation.Runtime.enemy, foundation.Runtime.em, foundation.Runtime.config
    ec, stack, end = 0x02213000, foundation.Runtime.stack, foundation.Runtime.end
    values = dict(STATE=state, GRIP=state+0x300, REEL_STATE=state+0x200, OLD_THINK=0x021c0000, OLD_ANIMATION=0x021c0100,
        OLD_UPDATE=0x021c0200, OLD_EFFECT=0x021c0300, WEB_HIT=0x021c0600, BOSS_CONFIG=0x02190000,
        CATCH_SCA=6200, CATCH_GMB=6201, CATCH_GAB=6202, IMPACT_SCA=6203, IMPACT_GMB=6204, IMPACT_GAB=6205,
        DIVE_SCA=6206, DIVE_GMB=6207, DIVE_GAB=6208)

    @classmethod
    def setUpClass(cls):
        text = Path(h.__file__).with_suffix('.s').read_text()
        for key, value in foundation.Runtime.values.items():
            text = text.replace(key, f'0x{value:08x}')
        cls.helpers = asm(text+'\n.word ram_ok,xy,unlink_target', 0x021b1000)
        cls.values.update(zip(('SHARED_RAM_OK', 'SHARED_XY', 'SHARED_UNLINK_TARGET'), struct.unpack('<3I', cls.helpers[-12:])))
        labels = ('owned', 'active', 'select_target', 'cleanup', 'update')
        code = asm(s.source(cls.values)+'\n.word '+','.join(labels), cls.at)
        cls.labels = dict(zip(labels, struct.unpack('<5I', code[-20:])))
        cls.code = s.runtime(cls.at, cls.values)
        assert code[:-20] == cls.code

    def fixture(self, *, phase=0, form=1, owned=True, parent=True, state=19, x=6, facing=1, enemy_state=39):
        p = foundation.Runtime().fixture(form=form, x=x, facing=facing)
        p.code(0x021b1000, self.helpers)
        p.code(self.at, self.code)
        p.code(0x02145a48, struct.pack('<4H', 0, 1, 0, 0))
        p.code(0x02203300, bytes(0x100))
        for at, value in ((self.hero+4, 0), (self.hero+0x1c, 0x1800), (self.mot+0x2ac, 0),
            (self.stats+12, 0), (self.stats+0x14, (int(parent)<<21) | (int(owned)<<22)),
            (self.ctl+0x14, state), (self.ctl+0x24, 0), (self.ctl+0x80, 0), (self.mot+0x258, 1),
            (self.mot+0x16c, self.values['CATCH_GAB']),
            (self.em+0x1f8, self.ec), (self.ec+0x14, enemy_state), (self.em+0x2ac, 0), (self.em+0x178, 0),
            (self.enemy+0x18, 0), (self.enemy+0x1c, 0x1000), (self.values['REEL_STATE']+24, 0)):
            p.put(at, value)
        p.code(self.values['GRIP'], struct.pack('<3i', 0, 6*4096, 4*4096)*18)
        p.put(self.em+0x58, 0x02214000)
        p.code(0x02214190, struct.pack('<3i', 0, 6*4096, 0))
        for mot, px in ((self.mot, 0), (self.em, x*4096)):
            for i in range(3):
                p.put(mot+12+i*4, 4096)
            matrix = (0, 0, -4096 if facing else 4096, 0, 4096, 0, 4096 if facing else -4096, 0, 0)
            for i, value in enumerate(matrix): p.put(mot+0x20+i*4, value)
            for i, value in enumerate((px, 0, 0)): p.put(mot+0x44+i*4, value)
        if phase:
            for off, value in ((0, self.hero), (4, self.ctl), (8, self.enemy+4), (16, self.em),
                (20, self.config), (24, phase), (28, 20), (32, 65), (88, facing), (112, self.hero+4)):
                p.put(self.state+off, value)
            p.put(self.enemy+4, self.state+8)
            p.put(self.hero+4, self.state+112)
        return p

    def stubs(self, calls, *, queued=(5,), hit=4, live=True):
        def peek(p, r, flags):
            r[0] = int(p.get(r[1]) in queued)
            return flags
        def consume(p, r, flags):
            calls.append(('consume', p.get(r[1])))
            return flags
        def alive(p, r, flags):
            r[0] = int(live and r[0] == self.enemy)
            return flags
        def receive(p, r, flags):
            calls.append(('hit', *r[:4]))
            r[0] = hit
            return flags
        def detach(p, r, flags):
            calls.append(('detach', r[0]))
            p.put(self.em+0x2ac, 0)
            return flags
        def transition(p, r, flags):
            p.put(r[0]+0x14, r[1])
            return flags
        return {0x020cff0c: peek, 0x020cfc34: consume, 0x02152c68: alive,
                self.values['WEB_HIT']: receive, 0x020739b4: detach, 0x02077844: transition}

    def run_entry(self, p, entry=0, *, actor=None, stubs=None):
        r = list(range(100, 116))
        r[0], r[4] = self.ctl, actor or self.hero
        r[13:] = [self.stack, self.end, self.at+4*entry]
        return p.run(r, 0xa000001f, {self.end, self.values['OLD_THINK'], self.values['OLD_UPDATE']}, stubs)

    def test_owned_air_a_links_and_probes_zero_damage_before_consuming_input(self):
        p, calls = self.fixture(), []
        out, _, pc = self.run_entry(p, stubs=self.stubs(calls))
        self.assertEqual((pc, out[0], out[13]), (self.end, 51, self.stack))
        self.assertEqual(calls, [('hit', self.enemy, 0x25, 0, self.hero), ('consume', 5)])
        self.assertEqual([p.get(self.state+i) for i in (0, 4, 8, 24, 112)],
                         [self.hero, self.ctl, self.enemy+4, 1, self.hero+4])

    def test_native_fallback_for_red_unowned_ground_chords_and_priority(self):
        for kw in ({'form': 0}, {'owned': False}, {'parent': False}, {'state': 0}, {'state': 45}, {'state': 63}):
            p, calls = self.fixture(**kw), []
            _, _, pc = self.run_entry(p, stubs=self.stubs(calls))
            self.assertEqual((pc, calls, p.get(self.state+24)), (self.values['OLD_THINK'], [], 0), kw)
        for direction, queued in ((1, (5,)), (2, (5,)), (3, (5,)), (5, (5,)), (6, (5,)), (7, (5,)),
                                   (0, (3, 5)), (0, (4, 5)), (0, ()), (0, (6,))):
            p, calls = self.fixture(), []
            p.put(self.ctl+0x24, direction)
            _, _, pc = self.run_entry(p, stubs=self.stubs(calls, queued=queued))
            self.assertEqual((pc, calls), (self.values['OLD_THINK'], []), (direction, queued))
        p = self.fixture(); p.put(self.values['REEL_STATE']+24, 1); calls = []
        _, _, pc = self.run_entry(p, stubs=self.stubs(calls))
        self.assertEqual((pc, calls), (self.values['OLD_THINK'], []))
        for held in (0, 0x41, 0x81, 0xc1, 0x51, 0x91):
            p, calls = self.fixture(), []
            p.code(0x02145a4a, struct.pack('<H', held))
            _, _, pc = self.run_entry(p, stubs=self.stubs(calls))
            self.assertEqual((pc, calls), (self.values['OLD_THINK'], []), held)

    def test_selector_requires_airborne_forward_near_light_live_target(self):
        for x, y, state, floor in ((-6, 0, 39, 0), (11, 0, 39, 0), (6, 13, 39, 0),
                                  (6, 0, 0, 0), (6, 0, 39, 4096), (6, 0, 49, 0)):
            p, calls = self.fixture(x=x, enemy_state=state), []
            p.put(self.em+0x80, y*4096); p.put(self.em+0x2ac, floor)
            _, _, pc = self.run_entry(p, stubs=self.stubs(calls))
            self.assertEqual((pc, calls), (self.values['OLD_THINK'], []), (x, y, state, floor))
        for facing in (0, 1):
            p, calls = self.fixture(x=6 if facing else -6, facing=facing), []
            out, _, pc = self.run_entry(p, stubs=self.stubs(calls))
            self.assertEqual((pc, out[0]), (self.end, 51))
        p, calls = self.fixture(), []; p.put(self.enemy+0x40, self.values['BOSS_CONFIG'])
        _, _, pc = self.run_entry(p, stubs=self.stubs(calls))
        self.assertEqual((pc, calls), (self.values['OLD_THINK'], []))

    def test_ignored_catch_is_heavy_and_never_consumes_a_or_moves_target(self):
        p, calls = self.fixture(), []
        before = p.get(self.enemy+0x18), p.get(self.enemy+0x1c)
        _, _, pc = self.run_entry(p, stubs=self.stubs(calls, hit=1))
        self.assertEqual((pc, calls), (self.values['OLD_THINK'], [('hit', self.enemy, 0x25, 0, self.hero)]))
        self.assertEqual((p.get(self.enemy+0x18), p.get(self.enemy+0x1c)), before)
        self.assertTrue(all(p.get(self.state+i) == 0 for i in (0, 4, 8, 24, 112)))

    def test_both_facing_steering_is_bounded_and_writes_no_coordinates(self):
        for face in (0, 1):
            p, calls = self.fixture(phase=2, state=51, x=7 if face else -7, facing=face), []
            before = dict(p.memory)
            self.run_entry(p, 2, actor=self.enemy, stubs=self.stubs(calls))
            for at in (self.enemy+0x18, self.enemy+0x1c):
                self.assertLessEqual(abs(struct.unpack('<i', struct.pack('<I', p.get(at)))[0]), 0x4000)
            for mot in (self.mot, self.em):
                for off in (0x7c, 0x80, 0x160, 0x164, 0x178):
                    self.assertEqual([p.memory[mot+off+i] for i in range(4)], [before[mot+off+i] for i in range(4)])
            self.assertEqual(calls, [])

    def test_actual_floor_causes_one_damage_and_one_bounce(self):
        p, calls = self.fixture(phase=2, state=51), []
        p.put(self.em+0x2ac, 4096); p.put(self.mot+0x2ac, 4096); p.put(self.enemy+0x1c, 0)
        self.run_entry(p, 2, actor=self.enemy, stubs=self.stubs(calls))
        self.assertEqual((p.get(self.state+24), p.get(self.state+48)), (3, 1))
        self.assertEqual(calls, [('hit', self.enemy, 0x1f, 0x2000, self.hero), ('detach', self.enemy)])
        p.put(self.ec+0x14, 41)
        self.run_entry(p, 2, actor=self.enemy, stubs=self.stubs(calls))
        self.assertEqual((p.get(self.enemy+0x18), p.get(self.enemy+0x1c), p.get(self.state+52)), (0, 0x1800, 0))
        p.put(self.enemy+0x1c, 1234)
        self.run_entry(p, 2, actor=self.enemy, stubs=self.stubs(calls))
        self.assertEqual(p.get(self.enemy+0x1c), 1234)
        self.assertEqual(len(calls), 2)
        out, _, _ = self.run_entry(p, stubs=self.stubs([]))
        self.assertEqual(out[0], 24)

    def test_grip_uses_the_next_live_sample_before_hero_animation_update(self):
        p, calls = self.fixture(phase=1, state=51, x=0), []
        p.put(self.mot+0x178, 3); p.put(self.state+40, 1)
        p.code(self.values['GRIP'], b''.join(struct.pack('<3i', 0, 6*4096, i*1024) for i in range(18)))
        self.run_entry(p, 2, actor=self.enemy, stubs=self.stubs(calls))
        self.assertEqual(p.get(self.enemy+0x18), 4096)
        self.assertEqual(calls, [])

    def test_floor_impact_waits_for_both_actors_and_lethal_hit_skips_bounce(self):
        p, calls = self.fixture(phase=2, state=51), []
        p.put(self.em+0x2ac, 4096); p.put(self.enemy+0x1c, 0)
        self.run_entry(p, 2, actor=self.enemy, stubs=self.stubs(calls))
        self.assertEqual((calls, p.get(self.state+48)), ([], 0))
        self.assertEqual(p.get(self.enemy+0x18), 0)
        p.put(self.mot+0x2ac, 4096)
        stubs = self.stubs(calls)
        receive = stubs[self.values['WEB_HIT']]
        def lethal(p, r, flags):
            flags = receive(p, r, flags)
            p.put(self.enemy+0x44, 0)
            return flags
        stubs[self.values['WEB_HIT']] = lethal
        self.run_entry(p, 2, actor=self.enemy, stubs=stubs)
        self.assertEqual((p.get(self.state+48), calls), (1, [('hit', self.enemy, 0x1f, 0x2000, self.hero)]))

    def test_no_air_impact_and_reaction_takeover_releases_without_velocity_damage(self):
        for floor in (0, -4096):
            p, calls = self.fixture(phase=2, state=51), []
            p.put(self.em+0x2ac, floor)
            self.run_entry(p, 2, actor=self.enemy, stubs=self.stubs(calls))
            self.assertEqual((calls, p.get(self.state+48)), ([], 0))
        p, calls = self.fixture(phase=2, state=51, enemy_state=42), []
        self.run_entry(p, 2, actor=self.enemy, stubs=self.stubs(calls))
        self.assertEqual((p.get(self.state+24), p.get(self.enemy+0x1c), calls), (0, 0x1000, []))

    def test_hurt_death_form_room_owner_and_target_loss_release_weak_links(self):
        for at, value in ((self.ctl+0x14, 63), (self.stats+0x84, 0), (self.hero+0x34, 0),
                          (self.stats, 66), (self.mot+0x1f8, 0x02203300), (self.enemy+0x44, 0),
                          (self.enemy+0x30, 0x02215000), (self.enemy+0x40, 0x02216000)):
            p, calls = self.fixture(phase=1, state=51), []
            p.put(at, value)
            self.run_entry(p, 2, stubs=self.stubs(calls))
            self.assertTrue(all(p.get(self.state+i) == 0 for i in (0, 4, 8, 24, 112)), (hex(at), value))
            if at == self.enemy+0x44:
                self.assertEqual(p.get(self.ctl+0x14), 19)
        for dodge in (0, 0x400):
            p, calls = self.fixture(phase=1, state=51), []
            p.put(self.stats+12, dodge)
            out, _, pc = self.run_entry(p, stubs=self.stubs(calls, queued=(3,)))
            self.assertEqual(p.get(self.state+24), 0)
            self.assertEqual((pc, out[0]), (self.values['OLD_THINK'], self.ctl) if dodge else (self.end, 19))
        p, calls = self.fixture(phase=3, state=24), []
        p.put(self.mot+0x2ac, 4096); p.put(self.stats+12, 0)
        out, _, pc = self.run_entry(p, stubs=self.stubs(calls, queued=(3,)))
        self.assertEqual((pc, out[0], p.get(self.state+24), calls), (self.values['OLD_THINK'], self.ctl, 0, []))

    def test_private_animation_selects_each_phase_and_preserves_native_registers(self):
        for phase, part in ((1, 'CATCH'), (2, 'DIVE'), (3, 'IMPACT')):
            p = self.fixture(phase=phase, state=51)
            regs = list(range(100, 116)); regs[0], regs[4] = 1, self.mot
            regs[13:] = [self.stack, self.end, self.at+4]
            out, flags, pc = p.run(regs, 0xa000001f, {0x02070488})
            self.assertEqual((pc, out[:14]), (0x02070488, regs[:14]))
            self.assertEqual([p.get(self.stack+i) for i in (0x2c, 0x38, 0x3c)],
                             [self.values[part+'_'+ext] for ext in ('SCA', 'GMB', 'GAB')])
            self.assertFalse(flags & 0x40000000)

    def test_impact_waits_for_its_own_resource_and_keeps_a_native_followup_queued(self):
        p = self.fixture(phase=3, state=24)
        p.put(self.mot+0x16c, self.values['DIVE_GAB'])
        out, _, pc = self.run_entry(p, stubs=self.stubs([], queued=()))
        self.assertEqual((pc, out[0], p.get(self.state+24)), (self.end, 24, 3))
        p.put(self.mot+0x16c, self.values['IMPACT_GAB']); p.put(self.state+84, 4)
        p.put(self.mot+0x178, 3)
        calls = []
        out, _, pc = self.run_entry(p, stubs=self.stubs(calls, queued=(5,)))
        self.assertEqual((pc, out[0], p.get(self.state+24), calls), (self.values['OLD_THINK'], self.ctl, 0, []))

    def test_utility_effect_skip_requires_exact_attacker_target_and_zero_hp(self):
        for guard, damage, attacker, target in ((1, 0, True, True), (0, 0, True, True),
            (1, 4096, True, True), (1, 0, False, True), (1, 0, True, False)):
            p = self.fixture(phase=1, state=51)
            p.put(self.state+36, guard)
            victim_ctl, cell, amount = 0x02230000, 0x02231000, 0x02232000
            p.put(self.stack+0x1d0, amount); p.put(amount, damage)
            p.put(victim_ctl+0x44, self.enemy if target else self.enemy+0x100)
            p.put(cell, self.hero if attacker else self.hero+0x100)
            regs = list(range(100, 116)); regs[5], regs[6] = cell, victim_ctl
            regs[13:] = [self.stack, self.end, self.at+12]
            out, _, pc = p.run(regs, 0xa000001f, {0x02095670, self.values['OLD_EFFECT']})
            self.assertEqual((pc, out[:14]), (0x02095670 if guard and not damage and attacker and target else
                                             self.values['OLD_EFFECT'], regs[:14]))

    def test_floor_flash_changes_only_its_local_point_for_the_exact_owned_impact(self):
        for damage, attacker, target in ((0x2000, True, True), (0, True, True), (0x1000, True, True),
                                         (0x2000, False, True), (0x2000, True, False)):
            p = self.fixture(phase=2, state=51)
            p.put(self.state+36, 2)
            victim_ctl, cell, amount = 0x02230000, 0x02231000, 0x02232000
            p.put(self.stack+0x1d0, amount); p.put(amount, damage)
            p.put(victim_ctl+0x44, self.enemy if target else self.enemy+0x100)
            p.put(cell, self.hero if attacker else self.hero+0x100)
            for off in (0x160, 0x164, 0x168): p.put(self.stack+off, 123)
            before = dict(p.memory)
            regs = list(range(100, 116)); regs[5], regs[6] = cell, victim_ctl
            regs[13:] = [self.stack, self.end, self.at+12]
            out, flags, pc = p.run(regs, 0xa000001f, {0x020955e0, self.values['OLD_EFFECT']})
            applies = damage == 0x2000 and attacker and target
            self.assertEqual((pc, out[:14], flags),
                (0x020955e0 if applies else self.values['OLD_EFFECT'], regs[:14], 0xa000001f))
            self.assertEqual([p.get(self.stack+off) for off in (0x160, 0x164, 0x168)],
                             [6*4096, 0, 0] if applies else [123]*3)
            self.assertTrue(all(value == p.memory[at] for at, value in before.items() if at < self.stack-0x100))


@unittest.skipUnless((Path(__file__).resolve().parents[1]/'original/Spider-Man - Web of Shadows (USA) (En,Fr).nds').exists(), 'private input missing: clean ROM')
class Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = s.PARENT_PATH.read_bytes()
        cls.after, cls.report = s.apply_rom(cls.before)

    def test_exact_parent_reproducible_output_and_only_allowed_resources(self):
        with self.assertRaises(ValueError): s.apply_rom(self.before[:-1]+b'x')
        a, b = s.assets.resources(self.before), s.assets.resources(self.after)
        self.assertEqual(b[0][:len(a[0])], a[0])
        self.assertEqual([n for n, x, y in zip(a[0], a[1], b[1]) if x != y],
                         ['American.strings', 'English.strings', 'GlobFiles.txt'])
        self.assertEqual(s.apply_rom(self.before)[1]['rom_sha256'], self.report['rom_sha256'])
        for e in w.nitrofs_entries(self.before):
            if e['name'] != 'Glob.bin':
                n = next(x for x in w.nitrofs_entries(self.after) if x['name'] == e['name'])
                self.assertEqual(self.before[e['start']:e['end']], self.after[n['start']:n['end']])

    def test_arm_scope_native_kit_and_existing_shop_records_stay_exact(self):
        def arm(raw):
            header = w.parse_header(raw)
            return raw[header['arm9_offset']:header['arm9_offset']+header['arm9_size']]
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
        old = kit.SOURCE+w.u32(a, h.BLACK_POINTER)-kit.TARGET
        new = kit.SOURCE+rt['shop']-kit.TARGET
        expected = bytearray(a[old:old+320]); struct.pack_into('<I', expected, 8*32+8, 395)
        self.assertEqual(b[new:new+320], expected)
        self.assertEqual(struct.unpack_from('<3I', b, new+320), (395, 394, kit.NO_EVENT))
        self.assertEqual(w.u32(b, new+348), 200)
        self.assertEqual(w.u32(b, h.BLACK_COUNT), 11)

    def test_impact_feet_are_planted_at_authored_height_and_clips_have_no_attack_boxes(self):
        from tools import spider2099_visual, spider2099_sculpt
        from tools.sca import Sca
        from tools.sca_author import sample
        from tools.gmb import Gmb
        from tools.grip_compression import CompressedBlob
        names, blobs = s.assets.resources(self.after)
        model = spider2099_visual.selected_model(blobs[names.index('spd.nsbmd')], 1)
        clip = Sca.parse(blobs[names.index('zz_M37_Impact.sca')])
        for frame in range(clip.frame_count):
            # The turntable normalizes pelvis Y to 5.724; restore authored height for floor QA.
            height = sample(clip, 1, frame, 'translation')[1]/4096-5.724
            mesh = spider2099_sculpt.posed_mesh(model, clip, frame)
            foot = min(vertex.position[1] for face in mesh for vertex in face)+height
            self.assertGreater(foot, -.1, frame)
            self.assertLess(foot, .25, frame)
        idle = Gmb.parse(CompressedBlob.parse(blobs[names.index('spd_Idle.gmb')]).decoded)
        for part, clip in zip(('Catch', 'Dive', 'Impact'), s.art.CLIPS):
            body = Gmb.parse(CompressedBlob.parse(blobs[names.index('zz_M37_'+part+'.gmb')]).decoded)
            self.assertEqual(body.record_count, clip.samples)
            self.assertEqual([c.kind for c in body.channels], [c.kind for c in idle.channels])
            for a, b in zip(idle.channels, body.channels):
                self.assertTrue(all(record in a.records for record in b.records))


if __name__ == '__main__':
    unittest.main()
