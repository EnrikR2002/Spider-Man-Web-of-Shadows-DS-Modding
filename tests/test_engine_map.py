"""RTTI recovery, hook census and the engine lookup agree with synthetic images and the catalogs."""
import hashlib
import struct
import unittest

from tools import arm9_hooks, arm9_rtti, engine_map

BASE = 0x02000000


def branch(at, target, link=False):
    return (0xEB000000 if link else 0xEA000000) | ((target - at - 8) >> 2) & 0xFFFFFF


class Memory:
    """A little-endian image written by address."""

    def __init__(self, size):
        self.data = bytearray(size)

    def words(self, address, *values):
        struct.pack_into(f'<{len(values)}I', self.data, address - BASE, *(v & 0xFFFFFFFF for v in values))
        return address

    def text(self, address, value):
        self.data[address - BASE:address - BASE + len(value) + 1] = value.encode() + b'\0'
        return address


class RttiTests(unittest.TestCase):
    def test_demangle(self):
        for mangled, readable in (
                ('18SpideyStateMachine', 'SpideyStateMachine'),
                ('N3xbd4BaseINS_8ModelSetEEE', 'xbd::Base<xbd::ModelSet>'),
                ('St9exception', 'std::exception'),
                ('12LRUCacheBaseILi15E7WaveKey11SNDWaveDataE', 'LRUCacheBase<15, WaveKey, SNDWaveData>'),
                ('N18SpideyStateMachine21SpideyCommandBaseArgsE', 'SpideyStateMachine::SpideyCommandBaseArgs'),
                ('N12CallerDetail10CallerImplIF7AutoPtrI5ActorEvEN13ActorInternal22AdaptResultToBaseActorIN5boost3_bi6bind_tINS8_'
                 '11unspecifiedE3NewI10DoorObjectENS8_5list1INS8_5valueI15EDoorObjectTypeEEEEEEEELm0EEE',
                 'CallerDetail::CallerImpl<AutoPtr<Actor> (), ActorInternal::AdaptResultToBaseActor<boost::_bi::bind_t<'
                 'boost::_bi::unspecified, New<DoorObject>, boost::_bi::list1<boost::_bi::value<EDoorObjectType>>>>, 0>'),
                ('PFvS2_ii6EngineE', 'PFvS2_ii6EngineE')):                    # unknown substitution: returned unchanged
            self.assertEqual(arm9_rtti.demangle(mangled), readable)

    def image(self):
        """Base (one pure virtual) and Derived : Base, each with a vtable; a member-pointer table follows Derived."""
        m, code_end = Memory(0x400), BASE + 0x100
        kinds = {}
        for i, kind in enumerate(arm9_rtti.KINDS):
            name = m.text(BASE + 0x100 + 0x30 * i, f'N10__cxxabiv1{len(kind)}{kind}E')
            info = m.words(BASE + 0x200 + 0x20 * i, 0, name)
            kinds[kind] = m.words(BASE + 0x208 + 0x20 * i, 0, info, BASE + 0x10, BASE + 0x14) + 8
        base = m.words(BASE + 0x280, kinds[arm9_rtti.KINDS[0]], m.text(BASE + 0x190, '4Base'))
        derived = m.words(BASE + 0x290, kinds[arm9_rtti.KINDS[1]], m.text(BASE + 0x198, '7Derived'), base)
        m.words(BASE + 0x2A0, 0, base, BASE + 0x20, 0, BASE + 0x28)                        # Base: f, pure, f
        m.words(BASE + 0x2B4, 0, derived, BASE + 0x20, BASE + 0x24, BASE + 0x28, BASE + 0x2C)
        table = m.words(BASE + 0x2CC, BASE + 0x30, 0, BASE + 0x34, 0)                      # {function, adjust} pairs
        m.words(BASE + 0x40, table)                                                        # code loads the table address
        return bytes(m.data), code_end

    def test_scan_bounds_tables_by_references_and_subclasses(self):
        image, code_end = self.image()
        found = {c['name']: c for c in arm9_rtti.scan(image, BASE, code_end)}
        self.assertEqual(found['Derived']['bases'], [{'name': 'Base', 'offset': 0}])
        self.assertEqual(found['Derived']['vtables'], [dict(address=BASE + 0x2BC, offset=0, slots=[BASE + 0x20, BASE + 0x24, BASE + 0x28, BASE + 0x2C])])
        self.assertEqual(found['Base']['vtables'][0]['slots'], [BASE + 0x20, 0, BASE + 0x28])
        self.assertEqual(set(found), {'Base', 'Derived'})

    def test_image_without_rtti_is_rejected(self):
        with self.assertRaises(ValueError): arm9_rtti.scan(bytes(0x200), BASE, BASE + 0x100)

    def test_catalog_matches_clean_rom(self):
        text = arm9_rtti.dumps(arm9_rtti.catalog(arm9_hooks.clean_arm9()))
        self.assertEqual(text, arm9_rtti.CATALOG.read_text(encoding='utf-8'), 'run python tools/arm9_rtti.py')


class HookTests(unittest.TestCase):
    def images(self):
        """A clean image with one autoload section, and a release that hooks one word into an appended block."""
        clean = Memory(0xC14)
        clean.words(BASE + arm9_hooks.MODULE_PARAMS, BASE + 0xC08, BASE + 0xC14, BASE + 0xC00)
        clean.words(BASE + 0x100, 0xE92D4010)
        clean.words(BASE + 0xC08, 0x01FF8000, 8, 0)
        target = 0x02100000
        modded = Memory(0xC30)
        modded.data[:0xC08] = clean.data[:0xC08]
        modded.words(BASE + 0x100, branch(BASE + 0x100, target + 4))
        modded.words(BASE + 0xC08, 0xE12FFF1E, 0xE12FFF1E, 0, 0)
        modded.words(BASE + arm9_hooks.MODULE_PARAMS, BASE + 0xC18, BASE + 0xC30, BASE + 0xC00)
        modded.words(BASE + 0xC18, 0x01FF8000, 8, 0, target, 16, 0)
        return bytes(clean.data), bytes(modded.data), target

    def test_layout_and_offsets(self):
        clean, modded, target = self.images()
        self.assertEqual(arm9_hooks.layout(modded), [(BASE, 0, 0xC00), (0x01FF8000, 0xC00, 8), (target, 0xC08, 16)])
        self.assertEqual(arm9_hooks.offset_of(modded, target + 4), 0xC0C)
        self.assertEqual(arm9_hooks.offset_of(clean, 0x01FF8004), 0xC04)
        with self.assertRaises(ValueError): arm9_hooks.offset_of(clean, target)
        self.assertEqual(arm9_hooks.branch_target(BASE + 0x100, branch(BASE + 0x100, target)), target)
        self.assertIsNone(arm9_hooks.branch_target(BASE, 0xE92D4010))

    def test_census_records_preimage_history_and_owner(self):
        clean, modded, target = self.images()
        later = bytearray(modded)
        struct.pack_into('<I', later, 0x100, branch(BASE + 0x100, target + 8))
        data = arm9_hooks.census(clean, [('1.0', 'First', modded), ('1.1', 'Second', bytes(later))])
        site = next(s for s in data['sites'] if s['address'] == '0x02000100')
        self.assertEqual((site['clean'], site['region'], site['target'], site['owner']), ('e92d4010', 'code', f'0x{target + 8:08x}', '1.0'))
        self.assertEqual(site['history'], [['1.0', f'{branch(BASE + 0x100, target + 4):08x}'], ['1.1', site['current']]])
        self.assertEqual(data['extension']['blocks'], [[f'0x{target:08x}', f'0x{target + 16:08x}', '1.0']])
        self.assertEqual(data['release'], '1.1')
        params = next(s for s in data['sites'] if s['address'] == f'0x{BASE + arm9_hooks.MODULE_PARAMS:08x}')
        self.assertNotIn('target', params)                       # autoload bookkeeping, not a hook
        restored = arm9_hooks.census(clean, [('1.0', 'First', modded), ('1.1', 'Undo', clean)])
        self.assertEqual(restored['sites'], [])

    def test_catalog_describes_stable_rom(self):
        stable = hashlib.sha256(arm9_hooks.arm9_of(arm9_hooks.STABLE)).hexdigest()
        self.assertEqual(engine_map.load('hooks')['arm9_sha256'], stable, 'run python tools/arm9_hooks.py')


class EngineMapTests(unittest.TestCase):
    def test_curated_file_is_consistent(self):
        self.assertEqual(engine_map.check(), [])

    def test_vtable_offsets_follow_native_indexing(self):
        self.assertEqual(engine_map.classes()['SpideyStateMachine']['vtables'][0]['address'], '0x021352a4')
        self.assertEqual(engine_map.locate('Spidey', 0x184), (20, 25))
        self.assertEqual(engine_map.primary('Spidey', 20, 25), 0x184)
        self.assertEqual(engine_map.origin('MiniBoss', 20, 25), ('Spidey', 20))
        self.assertEqual(engine_map.origin('Spidey', 8, 16), ('GameActor', 0))
        self.assertIsNone(engine_map.locate('Spidey', 0x400))
        self.assertEqual(engine_map.name_of(0x02060240), 'Spidey::HasAbility')
        self.assertEqual(engine_map.name_of(0x020B4888), 'SpideyStateMachine::Think')
        self.assertEqual(engine_map.name_of(0x021301D0), 'vtable NormalEnemy')

    def test_tables_name_their_handlers(self):
        self.assertEqual(engine_map.enum_name('PlayerState', 46), '46 GroundAttack1')
        self.assertEqual(engine_map.enum_name('PlayerState', 999), '999')
        enter = next(t for t in engine_map.load('symbols')['tables'] if t['name'] == 'SpideyStateMachine::EnterHandlers')
        self.assertEqual((len(enter['entries']), enter['entries'][24]), (92, 'vtable+0xC4'))
        self.assertEqual(engine_map.name_of(int(enter['entries'][57], 16)), 'SpideyStateMachine::Enter_57_58')
        self.assertEqual(engine_map.name_of(int(enter['entries'][63], 16)), 'SpideyStateMachine::Enter_63_HurtHitA')
        ground = engine_map.show_native_table('GroundTransitions')
        self.assertIn('[4] 0x020b5774 SpideyStateMachine::EvadeTransition', ground)
        self.assertIn('no table', engine_map.show_native_table('nonsense'))

    def test_lookups_work_from_catalogs(self):
        text = engine_map.describe(0x020B4888)
        self.assertIn('SpideyStateMachine vtable+0xA8', text)
        self.assertIn('CHANGED by the mod', text)
        self.assertIn('docs/TECHNICAL.md', text)
        self.assertIn('nothing recorded', engine_map.describe(0x02140000))
        self.assertIn('EvadeTransition', engine_map.find('evade'))
        self.assertIn('value    AbilityBit 7 = DrillKick', engine_map.find('drill'))
        self.assertIn('+0x184', engine_map.show_class('Spidey'))
        self.assertIn('subclasses: MiniBossStateMachine', engine_map.show_class('SpideyStateMachine'))
        self.assertIn('+0x14   s32   state', engine_map.show_table('structs', 'CharacterStateMachine'))
        self.assertEqual(engine_map.label(0x02152C74), '0x02152c74 kit::h_vortex_evade+0x4 (mod v0.2.0)')
        self.assertIn('Contact::Dispatch.call_ReceiveHit', engine_map.show_hooks('0x02078628'))
        hooks = engine_map.load('hooks')
        for site in hooks['sites']:
            self.assertEqual(site['history'][-1][1], site['current'])
        self.assertEqual(engine_map.block_of(int(hooks['extension']['target'], 16))[2], hooks['releases'][0][0])

    def synthetic(self):
        m = Memory(engine_map.CODE_END - BASE + 0x40)
        f = BASE + 0x10000
        m.words(f, 0xE92D4010,                                   # push {r4, lr}
                0xE3A02003, 0xE58D2000, 0xE28D1000, branch(f + 16, 0x020CFF0C, True),   # peek command 3
                0xE3A01007, 0xE5922184,                          # mov r1,#7; ldr r2,[r2,#0x184]
                0xE3A01005, 0xE59D2184,                          # mov r1,#5; ldr r2,[sp,#0x184]: a local, not HasAbility
                0x03A00039, 0x08BD8010,                          # moveq r0,#57; popeq {r4, pc}
                0xE3A0002E, 0xE8BD8010)                          # mov r0,#46; pop {r4, pc}
        m.words(f + 0x40, 0xE59FC004, 0xE081100C, branch(f + 0x48, f), 0xFFFFFFF8)     # this-adjusting thunk
        m.words(f + 0x60, 0xE59F0000, 0xE12FFF1E, 0x02145C5C)                           # ldr r0,=g_Stats; bx lr
        m.words(f + 0x80, 0xE52DE004, branch(f + 0x84, f, True))                       # push {lr}; bl f
        m.words(BASE + 0x200, f + 0x80)                          # a stored pointer to a push prologue
        return engine_map.Static(bytes(m.data)), f

    def test_static_index(self):
        index, f = self.synthetic()
        self.assertEqual(index.digest(f), dict(returns={46, 57}, peeks={3}, consumes=set(), abilities={7}))
        self.assertEqual(index.thunk(f + 0x40), f)
        self.assertIsNone(index.thunk(f))
        self.assertEqual(index.loads[0x02145C5C], [f + 0x60])
        self.assertEqual(index.calls[f], [f + 0x84])
        self.assertEqual((index.function(f + 0x20), index.function(f + 0x88)), (f, f + 0x80))
        self.assertEqual(index.callees(f + 0x80), [f])

    def test_player_actions_match_clean_rom(self):
        import mod
        from tools import actor_actions
        _, glob, manifest = mod.load_clean()
        names = [entry['name'] for entry in manifest['entries']]
        entry = next(e for e in manifest['entries'] if e['name'] == 'spd.xbd')
        rows = actor_actions.ActorActions.parse(glob[entry['offset']:entry['offset'] + entry['size']], names).actions
        values = engine_map.load('symbols')['enums']['Action']['values']
        for row in rows:
            clip = next(b for b in row.bindings if b['tag'] == 0)['name'][len('spd_'):-len('.sca')]
            self.assertIn(clip, values[str(row.action)])


if __name__ == '__main__':
    unittest.main()
