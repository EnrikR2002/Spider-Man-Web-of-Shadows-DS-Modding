"""Down+A queue direction, pure pull/idle return, scoped FX, and exact byte scope."""
import json
import struct
import unittest
from tests import test_hunter_kit as old
from tools import web_yank_combo as f, hunter_kit as h, tasm_kit as kit, wos_tool as w


class Runtime(unittest.TestCase):
    at, state = old.Runtime.at, old.Runtime.state
    hero, mot, ctl, stats = old.Runtime.hero, old.Runtime.mot, old.Runtime.ctl, old.Runtime.stats
    enemy, em, config, line = old.Runtime.enemy, old.Runtime.em, old.Runtime.config, old.Runtime.line
    stack, end = old.Runtime.stack, old.Runtime.end
    values = dict(old.Runtime.values, OLD_A=0x021b0900, RECORDS=0x021b1000, **f.shared_symbols(0x021d0000,old.Runtime.values))
    run_entry, transition, update = old.Runtime.run_entry, old.Runtime.transition, old.Runtime.update
    result = staticmethod(old.Runtime.result)

    def fixture(self, **kw):
        p = old.Runtime.fixture(self, **kw)
        p.code(0x021d0000,f.parent.runtime(0x021d0000,old.Runtime.values))
        p.code(self.at, f.runtime(self.at, self.values))
        self.actors={self.enemy}
        for at in range(self.values['RECORDS'],self.values['RECORDS']+512,4): p.put(at,0)
        p.put(self.state+120,1 if kw.get('phase') else 0)
        p.put(self.hero+4, self.state+112 if kw.get('phase') else 0)
        p.put(self.state+112, self.hero+4 if kw.get('phase') else 0)
        p.put(self.state+124, kw.get('facing', 1))
        p.put(self.em+0x1f8, 0x02213000)
        p.put(0x02213014, 37)
        p.put(self.enemy+0x18, 0)
        p.put(self.ctl+0x80, 9)
        p.put(self.ctl+0x24, 6)
        p.put(self.ctl+0x90, 0)
        return p

    def stubs(self, calls, *, r_queued=False, l_queued=False, **kw):
        stubs = old.Runtime.stubs(self, calls, **kw)
        stubs[self.values['OLD_A']] = self.result(0x7fffffff)
        def fresh(p,r,c):
            r[0]=int(kw.get('live',True) and r[0] in self.actors)
            return c
        stubs[0x02152c68]=fresh
        original_spawn=stubs[0x0205f844]
        def spawn(p,r,c):
            line=self.line+sum(row[0]=='line' for row in calls)*0x1000
            original_spawn(p,r,c)
            p.put(r[0],line)
            p.put(line+4,0)
            return c
        stubs[0x0205f844]=spawn
        def peek(p,r,c):
            command=p.get(r[1])
            calls.append(('peek',command))
            r[0]=int((command==5 and kw.get('queued',True)) or (command==3 and r_queued) or (command==4 and l_queued))
            return c
        def idle(p, r, c):
            calls.append(('state', r[0], r[1]))
            p.put(r[0]+0x14, r[1])
            return c
        stubs[0x020cff0c], stubs[0x02077844] = peek, idle
        return stubs

    def test_only_queued_down_a_arms_ground_or_ground_string_and_consumes_a(self):
        for current in (0, 1, 4, 5, 6, 46):
            p = self.fixture()
            p.put(self.ctl+0x14, current)
            self.assertEqual(self.transition(p), (46, [('consume', 5)]))
            self.assertEqual(p.memory[self.ctl+4], 1)
            self.assertEqual(p.get(self.state+88), 9 if current == 46 else 0)
        for direction in (0, 2, 4):
            p = self.fixture()
            p.put(self.ctl+0x24,direction)
            self.assertEqual(self.transition(p), (0x7fffffff, []))
        for direction in (5,7):
            p=self.fixture()
            p.put(self.ctl+0x24,direction)
            self.assertEqual(self.transition(p),(46,[('consume',5)]))
        self.assertEqual(self.transition(self.fixture(),r_queued=True),(0x7fffffff,[]))
        for state in (2, 3, 15, 19, 44, 45, 63):
            p = self.fixture()
            p.put(self.ctl+0x14, state)
            self.assertEqual(self.transition(p), (0x7fffffff, []))

    def test_red_unowned_r_and_native_object_handling_do_not_consume_a(self):
        for args in ({'form': 0}, {'owned': False}):
            self.assertEqual(self.transition(self.fixture(**args)), (0x7fffffff, []))
        p = self.fixture()
        self.assertEqual(self.transition(p, keys=0x100), (0x7fffffff, []))
        p.put(self.hero+0xc0, self.enemy+4)
        self.assertEqual(self.transition(p), (0x7fffffff, []))

    def test_point_blank_and_whiff_consume_only_the_chord_without_attack(self):
        for x in (0, 6, 12, 46):
            p = self.fixture(x=x)
            self.assertEqual(self.transition(p), (0, [('consume', 5)]))
            self.assertEqual(p.get(self.state+24), 0)

    def test_close_front_target_is_skipped_in_favor_of_a_real_distant_pull(self):
        p = self.fixture(x=7)
        # The standard freshness stub intentionally only accepts one target.
        self.assertEqual(self.transition(p), (0, [('consume', 5)]))
        p.put(self.em+0x7c, 30*4096)
        self.assertEqual(self.transition(p), (46, [('consume', 5)]))

    def test_web_catch_is_zero_hp_and_cosmetic_scope_flag_is_cleared(self):
        p = self.fixture(phase=2, clock=2)
        calls = self.update(p)
        self.assertIn(('hit', self.enemy, 0x16, 0, self.hero), calls)
        self.assertEqual(p.get(self.state+36), 0)
        self.assertFalse(any(c[0] == 'hit' for c in self.update(p)))

    def test_arrival_uses_native_idle_and_restores_combo_without_an_attack_or_clock_write(self):
        p = self.fixture(phase=2, clock=8, x=6)
        p.put(self.state+80, 1)
        p.put(self.state+44, 4)
        p.put(self.state+88, 9)
        calls = self.update(p)
        self.assertIn(('state', self.ctl, 0), calls)
        self.assertFalse(any(c[0] == 'hit' for c in calls))
        self.assertEqual(p.get(self.mot+0x178), 8)
        self.assertEqual(p.get(self.ctl+0x80), 9)
        self.assertEqual(p.memory[self.ctl+0x90], 10)
        self.assertEqual(p.get(self.hero+4), 0)
        self.assertEqual(p.get(self.state+24), 0)

    def test_native_hurt_form_room_replacement_and_dead_target_cleanup(self):
        for at, value in ((self.ctl+0x14, 63), (self.hero+0x34, 0), (self.stats, 76),
                          (self.state, self.hero+4), (self.enemy+0x44, 0), (self.state+20, 0)):
            p = self.fixture(phase=2)
            p.put(at, value)
            calls = self.update(p)
            self.assertFalse(any(c[0] == 'hit' for c in calls))
            self.assertEqual(p.get(self.state+24), 0)
            self.assertEqual(p.get(self.hero+4), 0)

    def test_fx_skip_requires_the_exact_synchronous_owned_catch_and_preserves_abi(self):
        for changes, skipped in (({}, True), ({self.state+36: 0}, False),
                                 ({self.state+24: 0}, False), ({self.state+8: 0}, False),
                                 ({0x02226000:4096},False)):
            p = self.fixture(phase=2)
            p.put(self.state+36, 1)
            p.put(self.state+48,self.state)
            p.put(self.stack+0x1d0,0x02226000)
            p.put(0x02226000,0)
            p.put(self.ctl+0x44, self.enemy)
            p.put(0x02224000, self.hero)
            p.put(0x02225020, 0x12345678)
            for at, value in changes.items(): p.put(at, value)
            r = list(range(16))
            r[2], r[5], r[6] = 0x02225000, 0x02224000, self.ctl
            before, out, flags, pc, _ = self.run_entry(p, 7, regs=r, stops={0x02095670, 0x02095440})
            self.assertEqual(pc, 0x02095670 if skipped else 0x02095440)
            self.assertEqual(out[1:15], before[1:15])
            self.assertEqual(flags, 0xa000001f)
            self.assertEqual(out[0], before[0] if skipped else 0x1234)

    def add_foe(self,p,index,x):
        actor=self.enemy if index==0 else 0x02240000+index*0x10000
        motion,controller=actor+0x1000,actor+0x3000
        for off,value in ((0,0x021301d0),(4,0),(0x18,0),(0x1c,777),(0x30,motion),
                          (0x40,self.config),(0x44,32768),(0x48,32768)):
            p.put(actor+off,value)
        for off,value in ((0,actor),(0x7c,x*4096),(0x80,0),(0x160,0),(0x164,0),(0x1f8,controller)):
            p.put(motion+off,value)
        p.put(controller+0x14,37)
        p.put(controller+0x44,actor)
        p.put(kit.KIT_STATE+0x20+16*index,actor)
        self.actors.add(actor)
        return actor

    def arm_crowd(self,p,count=6):
        actors=[self.add_foe(p,i,14+4*i) for i in range(count)]
        self.assertEqual(self.transition(p),(46,[('consume',5)]))
        p.put(self.state+24,2)
        p.put(self.ctl+0x14,46)
        p.put(self.mot+0x254,49)
        p.put(self.mot+0x258,49)
        return actors,[self.state]+[self.values['RECORDS']+128*i for i in range(4)]

    def test_six_candidates_bind_only_the_five_nearest_with_independent_lines(self):
        p=self.fixture()
        actors,records=self.arm_crowd(p)
        self.assertEqual(p.get(self.state+120),5)
        self.assertEqual([p.get(r+8)-4 for r in records],actors[:5])
        self.assertEqual(p.get(actors[5]+4),0)
        calls=self.update(p)
        self.assertEqual(sum(c[0]=='line' for c in calls),5)
        self.assertEqual(sum(c[0]=='hit' and c[2:4]==(0x16,0) for c in calls),5)
        self.assertEqual(len({p.get(r+96) for r in records}),5)

    def test_dead_primary_does_not_stop_other_targets_and_cleanup_unlinks_every_actor(self):
        p=self.fixture()
        actors,records=self.arm_crowd(p,5)
        self.update(p)
        p.put(actors[0]+0x44,0)
        p.put(self.mot+0x178,6)
        self.update(p)
        self.assertEqual(p.get(self.state+24),2)
        r=list(range(16));r[0]=actors[1]
        self.run_entry(p,6,regs=r)
        self.assertNotEqual(p.get(actors[1]+0x18),0)
        self.assertEqual(p.get(actors[1]+0x1c),777)
        p.put(self.ctl+0x14,63)
        self.update(p)
        self.assertEqual(p.get(self.hero+4),0)
        self.assertTrue(all(p.get(a+4)==0 for a in actors))
        self.assertTrue(all(p.get(r+8)==p.get(r+96)==p.get(r+112)==0 for r in records))

    def test_heavy_arrival_stops_hero_while_other_targets_keep_reeling(self):
        p=self.fixture()
        actors,records=self.arm_crowd(p,2)
        p.put(actors[0]+0x40,self.values['BOSS_CONFIG'])
        p.put(self.state+20,self.values['BOSS_CONFIG'])
        p.put(self.state+52,1)
        self.update(p)
        self.assertEqual(p.get(self.hero+0x18),5*4096)
        p.put(self.mot+0x7c,8*4096)
        p.put(self.mot+0x178,6)
        self.update(p)
        self.assertEqual(p.get(self.state+24),2)
        self.assertEqual(p.get(self.hero+0x18),0)

    def test_light_target_behind_a_heavy_zip_keeps_reeling_until_it_is_in_front(self):
        p=self.fixture()
        actors,records=self.arm_crowd(p,2)
        boss=actors[1]
        p.put(boss+0x40,self.values['BOSS_CONFIG'])
        p.put(records[1]+20,self.values['BOSS_CONFIG'])
        p.put(records[1]+52,1)
        p.put(boss+0x1000+0x7c,30*4096)
        self.update(p)
        p.put(self.mot+0x7c,20*4096)
        p.put(self.mot+0x178,6)
        self.update(p)
        self.assertEqual(p.get(self.state+84),0)
        r=list(range(16));r[0]=actors[0]
        self.run_entry(p,6,regs=r)
        self.assertEqual(p.get(actors[0]+0x18),6*4096)

    def test_reused_hero_addresses_with_a_cleared_weak_token_cannot_resume_the_old_cast(self):
        p=self.fixture(phase=2)
        p.put(self.state+112,0)
        p.put(self.hero+4,0)
        calls=self.update(p)
        self.assertFalse(any(c[0] in ('state','hit','line') for c in calls))
        self.assertEqual(p.get(self.ctl+0x14),46)
        self.assertEqual(p.get(self.state+24),0)

    def test_held_down_cannot_cancel_cast_but_native_r_and_l_can(self):
        for index,old in ((4,'OLD_STRING'),(5,'OLD_GENERIC')):
            for phase,queued,expected in ((2,{},46),(2,{'r_queued':True},0x7fffffff),
                                          (2,{'l_queued':True},0x7fffffff),(0,{},None)):
                p=self.fixture(phase=phase)
                for i,value in enumerate((44,45,46,47,48,self.end)):
                    p.put(self.stack+0x58+4*i,value)
                r=list(range(16));r[8]=self.ctl
                _,out,_,pc,calls=self.run_entry(p,index,regs=r,stops={self.end,self.values[old]},**queued)
                self.assertEqual(pc,self.values[old] if expected is None else self.end)
                if expected is not None:
                    self.assertEqual(out[0],expected)
                    self.assertEqual(out[13],self.stack+0x70)
                self.assertFalse(any(c[0]=='consume' for c in calls))


@unittest.skipUnless(f.PARENT_PATH.exists(), 'Private v0.34.1 parent unavailable')
class Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = f.PARENT_PATH.read_bytes()
        cls.result, cls.report = f.apply_rom(cls.parent)

    def test_only_version_and_instruction_text_resources_change(self):
        an, ab = h.assets.resources(self.parent)
        bn, bb = h.assets.resources(self.result)
        self.assertEqual(an, bn)
        self.assertEqual([n for n,a,b in zip(an,ab,bb) if a != b], ['American.strings', 'English.strings'])
        from tools.qol_suits_menu import decode_grown, slot_count
        meta = json.loads(f.PARENT_PATH.with_suffix('.build.json').read_text())
        changed = {50, 74, meta['hunter_kit']['text_id']+2}
        for name in ('American.strings', 'English.strings'):
            a,b = ab[an.index(name)],bb[bn.index(name)]
            self.assertEqual(slot_count(a),slot_count(b))
            self.assertEqual({i for i in range(slot_count(a)) if decode_grown(a,i)!=decode_grown(b,i)},changed)

    def test_extension_preserves_all_old_code_except_hooks_and_loader_metadata(self):
        ah,bh = w.parse_header(self.parent),w.parse_header(self.result)
        a = self.parent[ah['arm9_offset']:ah['arm9_offset']+ah['arm9_size']]
        b = bytearray(self.result[bh['arm9_offset']:bh['arm9_offset']+bh['arm9_size']])
        self.assertEqual(w.u32(b,0xb721c),0xe92d40f0)
        allowed = [h['site']-kit.BASE for h in self.report['runtime']['hooks']]
        allowed += [kit.TABLE_POINTERS,kit.TABLE_POINTERS+4,kit.ARENA_LOWER]
        for pos in allowed: b[pos:pos+4]=a[pos:pos+4]
        self.assertEqual(a[:-36],b[:len(a)-36])
        self.assertEqual(self.report['allocation_bytes'],8192)
        self.assertEqual(a[kit.SOURCE:kit.SOURCE+kit.RESERVE],b[kit.SOURCE:kit.SOURCE+kit.RESERVE])

    def test_sorted_saved_metadata_reassembles_the_exact_published_runtime(self):
        rt=self.report['runtime']
        values=json.loads(json.dumps(rt['values'],sort_keys=True))
        code=f.runtime(rt['entry'],values)
        h=w.parse_header(self.result)
        start=h['arm9_offset']+rt['source_offset']
        self.assertEqual(self.result[start:start+len(code)],code)


if __name__ == '__main__': unittest.main()
