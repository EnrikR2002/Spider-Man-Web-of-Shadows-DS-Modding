"""Skyjack code scope, complete Skitter motion/audio and native Crane route lifecycle."""
import json
import math
import struct
import unittest
from pathlib import Path
from tests.arm_runtime import ArmProbe
from tools import chapter_finish_kit as sky, chapter_finish_crane as crane
from tools import chapter_finish_motion as motion, chapter_finish_audio as audio
from tools import tasm_kit, wos_tool as w

ROOT = Path(__file__).resolve().parents[1]


class FrozenKit(unittest.TestCase):
    def test_frozen_code_reproduces_current_source_without_direct_juggle_store(self):
        self.assertEqual(sky.assemble(), sky.code_bytes())
        self.assertNotIn(struct.pack('<3I', 0xe595107c, 0xe0811002, 0xe585107c), sky.code_bytes())
        self.assertIn('str r2,[r4,#0x18]', sky.source())

    def test_patch_preserves_all_other_kit_data_and_rejects_changed_parent(self):
        rom = (ROOT/'build/version-0.28.0-final/Versioned.nds').read_bytes()
        result, _ = sky.apply(rom)
        header = w.parse_header(rom)
        start = header['arm9_offset']
        a = rom[start:start+header['arm9_size']]
        b = result[start:start+header['arm9_size']]
        low = tasm_kit.SOURCE+tasm_kit.OLD_STATE_END
        high = low+tasm_kit.ROUTE_OFFSET
        self.assertEqual(a[:low], b[:low])
        self.assertEqual(a[high:], b[high:])
        changed = bytearray(rom)
        changed[start+low+8] ^= 1
        with self.assertRaisesRegex(ValueError, 'exact published kit'):
            sky.apply(bytes(changed))


class NativeCraneRoute(unittest.TestCase):
    at = 0x02180000
    states, slots, roofs, hero = at+0x2000, at+0x3000, at+0x4000, at+0x5000
    ctl, actor, motion = 0x02200000, 0x02201000, 0x02202000
    stats, player, pm, record = 0x02203000, 0x02204000, 0x02205000, 0x02206000
    end = 0x03000000

    def fixture(self, phase=0, x=72, y=-6.7, py=25, vy=0, grounded=True, kind=1, room=97, state=0):
        p = ArmProbe()
        p.code(self.at, crane.navigation(self.at, self.states, self.slots, self.roofs, self.hero))
        for i, roof in enumerate((*crane.ROOFS, (0,)*6)):
            for j, value in enumerate(roof):
                p.put(self.roofs+i*24+j*4, round(value*4096))
        for i in range(8):
            p.put(self.states+i*4, 0)
            p.put(self.slots+i*4, 0)
        p.put(0x02145c5c, self.stats)
        p.put(self.stats, room)
        p.put(self.record+12, kind)
        p.put(self.ctl+0x14, state)
        p.put(self.actor+0x44, 50000)
        p.put(self.actor+0x10, 0x80 if grounded else 0)
        p.put(self.actor+0x1c, vy)
        p.put(self.hero, self.player)
        p.put(self.player+0x30, self.pm)
        for base, xx, yy in ((self.motion, x, y), (self.pm, 80, py)):
            p.put(base+0x7c, round(xx*4096))
            p.put(base+0x80, round(yy*4096))
            p.put(base+0x160, 0)
            p.put(base+0x164, 0)
        if phase:
            for i, value in enumerate((self.ctl, self.actor, phase, 100*4096, 3, round(x*4096), round(25.5*4096), 0)):
                p.put(self.states+i*4, value)
        return p

    def call(self, probe, proposed=0, stubs=None):
        regs = list(range(13))+[0x023ff000, self.end, self.at]
        regs[4], regs[5], regs[6] = self.ctl, proposed, self.actor
        regs[7], regs[8], regs[11] = self.record, self.slots, self.motion
        result, _, _ = probe.run(regs, 0, {self.end}, stubs)
        self.assertEqual(result[1:14], regs[1:14])
        self.assertEqual(probe.get(self.actor+0x44), 50000)
        return result[0]

    def test_below_roof_routes_to_a_clear_edge_without_placing_any_actor(self):
        p = self.fixture()
        before = [p.get(self.motion+x) for x in (0x7c, 0x80)]
        self.assertEqual(self.call(p), 1)
        self.assertEqual(p.get(self.states+8), 1)
        self.assertEqual(p.get(self.states+12), 100*4096)
        self.assertEqual(p.get(self.slots+28), 3277)
        self.assertEqual(before, [p.get(self.motion+x) for x in (0x7c, 0x80)])

    def test_jump_apex_keeps_return_route_until_actual_landing(self):
        p = self.fixture(phase=3, x=97, y=34, py=25, vy=5000, grounded=False)
        self.assertEqual(self.call(p), 5)
        self.assertEqual(p.get(self.states+8), 3)
        self.assertEqual(p.get(self.slots+28), (-3277)&0xffffffff)
        p = self.fixture(phase=3, x=80, y=25.3, py=25)
        self.assertEqual(self.call(p), 0)
        self.assertEqual(p.get(self.states+8), 0)

    def test_clear_edge_uses_native_jump_and_single_velocity_impulse(self):
        p = self.fixture(phase=2, x=100, y=5.3)
        jumps = []
        def jump(probe, regs, flags):
            self.assertEqual(regs[0], self.actor)
            self.assertEqual(regs[13] % 8, 0)
            jumps.append(True)
            return flags
        self.assertEqual(self.call(p, stubs={0x020739b4: jump}), 5)
        self.assertEqual(jumps, [True])
        self.assertEqual(p.get(self.actor+0x1c), 18842)
        self.assertEqual(p.get(self.motion+0x7c), 100*4096)

    def test_other_species_rooms_hurt_and_active_programs_keep_native_decisions(self):
        for options in ({'kind': 0}, {'kind': 4}, {'room': 78}, {'state': 37}, {'state': 53}):
            with self.subTest(options=options):
                p = self.fixture(**options)
                self.assertEqual(self.call(p), 0)
                self.assertEqual(p.get(self.slots+28), 0)
        p = self.fixture()
        p.put(self.slots+20, self.at+0x6000)
        self.assertEqual(self.call(p), 0)
        p = self.fixture()
        self.assertEqual(self.call(p, proposed=37), 0)


class SkitterResources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import mod
        from tools.sca import Sca
        from tools.animation_rig import AnimationRig
        _, glob, _ = mod.load_clean()
        offsets, names, _ = w.parse_glob(glob)
        cls.assets = dict(zip(names, (glob[a:b] for a, b in zip(offsets, offsets[1:]))))
        cls.idle = Sca.parse(cls.assets['hLpr_Idle.sca'])
        cls.parents = AnimationRig.parse(cls.assets['hLpr.nsbmd']).parents

    def test_attack_endpoints_share_rest_and_cross_contacts_with_motion(self):
        rest = motion.pose(self.idle, self.parents).fk()[1]
        for move in motion.MOVES:
            for frame in (0, move.samples-1):
                pose = motion.pose(self.idle, self.parents, 'hm_GroundAttack1.sca', frame, move.samples, move)
                points = pose.fk()[1]
                self.assertLess(max(math.dist(points[j], rest[j]) for j in (1, 9, 16, 22, 26)), .02)
            for i, (a, _) in enumerate(move.contacts):
                j = (9, 16)[i % 2]
                before = motion.pose(self.idle, self.parents, 'hm_GroundAttack1.sca', a-1, move.samples, move).fk()[1][j]
                after = motion.pose(self.idle, self.parents, 'hm_GroundAttack1.sca', a+1, move.samples, move).fk()[1][j]
                self.assertGreater(math.dist(before, after), .15)

    def test_prone_death_and_rise_keep_complete_low_to_upright_lifecycle(self):
        for source in ('hm_HurtLandFace.sca', 'hm_Die.sca'):
            p = motion.pose(self.idle, self.parents, source, 27, 28)
            self.assertLess(p.t[1][1], 1)
        p = motion.pose(self.idle, self.parents, 'hm_HurtLandGetUp.sca', 21, 22)
        self.assertAlmostEqual(p.t[1][1], motion.REST[0])
        for q in (-.00001, .00001, .64-.00001, .64+.00001, 1-.00001):
            self.assertTrue(all(math.isfinite(v) for v in motion.gait(q)))
        self.assertLess(math.dist(motion.gait(-.00001), motion.gait(.00001)), .002)

    def test_sound_only_replaces_eight_owned_waveforms(self):
        from tools import sdat
        rom = (ROOT/'build/version-0.28.0-final/Versioned.nds').read_bytes()
        e = next(e for e in w.nitrofs_entries(rom) if e['name'] == 'sound_data.sdat')
        raw = rom[e['start']:e['end']]
        result, _ = audio.sound_data(raw)
        a, b = sdat.Sdat.parse(raw), sdat.Sdat.parse(result)
        wid = a.file_id(3, 0)
        old, new = audio.waves(a.blob(wid)), audio.waves(b.blob(wid))
        self.assertEqual({i for i, (x, y) in enumerate(zip(old, new)) if x != y}, set(audio.ROWS.values()))
        self.assertEqual(len(new), 833)
        for i in range(len(a.entries)):
            if i != wid:
                self.assertEqual(a.blob(i), b.blob(i))
        manifest = json.loads((audio.DIR/'manifest.json').read_text())
        self.assertEqual(len({x['sha256'] for x in manifest['samples']}), 8)
        for entry in manifest['samples']:
            self.assertLessEqual(entry['peak'], 24000)
            self.assertGreater(entry['rms'], 500)


if __name__ == '__main__':
    unittest.main()
