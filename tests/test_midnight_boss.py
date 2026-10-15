"""Signal Leech script lifecycle, delayed cancellation and scoped native data."""
import heapq
import struct
import unittest
import mod
from tools import midnight_boss as b, midnight_chapter as ch, midnight_rooms as mr, room_script as s, room_catalog
from tools.room_entities import Entities
from tools.room_events import Events
from tools.room_objects import RoomObjects


class Script:
    """Execute decoded native commands with their real delayed-action semantics."""
    def __init__(self, raw, flags=()):
        (self.entities, self.labels, self.batches) = s.names(raw, 1)
        rec = RoomObjects.parse(raw).records[1]
        self.groups = Events.parse(rec.sections[1], rec.raw[3]).groups
        self.vars = {f: 1 for f in flags}
        self.active, self.events, self.queue = set(), [], []
        self.now = self.serial = 0
        self.run(0)
    def action(self, action, frames=0):
        ag, entity, batch, eg = action
        if frames:
            self.serial += 1
            heapq.heappush(self.queue, (self.now + frames, self.serial, action))
            return
        if batch:
            self.active.update((batch - 1, i + 1) for i in range(len(self.entities[batch - 1])))
            self.events.append((self.now, self.batches[batch - 1]))
        if entity: self.active.add((ag, entity))
        if eg: self.run(eg - 1)
    def run(self, group):
        if isinstance(group, str): group = self.labels.index(group)
        for c in self.groups[group].commands:
            o = c.operand
            if c.opcode in (s.SET_VAR, s.INC_VAR):
                var, value = struct.unpack_from('<HB', o)
                self.vars[var] = value if c.opcode == s.SET_VAR else self.vars.get(var, 0) + value
            elif c.opcode == s.DELAY: self.action(o[2:6], struct.unpack_from('<H', o)[0])
            elif c.opcode == s.IF_VAR:
                var, frames, op, value = struct.unpack_from('<HHBB', o)
                got = self.vars.get(var, 0)
                passed = (got == value, got != value, got < value, got <= value, got > value, got >= value)[op]
                self.action(o[6:10] if passed else o[10:14], frames)
            elif c.opcode == s.DEACTIVATE:
                ag, entity, batch, _ = o
                if batch: self.active = {(a, e) for a, e in self.active if a != batch - 1}
                if entity: self.active.discard((ag, entity))
    def advance(self, frames):
        until = self.now + frames
        while self.queue and self.queue[0][0] <= until:
            self.now, _, action = heapq.heappop(self.queue)
            self.action(action)
        self.now = until
    def live(self, text):
        return {self.batches[a] for a, _ in self.active if text in self.batches[a]}


class MidnightBossTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom, glob, manifest = mod.load_clean()
        cls.blobs = {e['name']: glob[e['offset']:e['offset'] + e['size']] for e in manifest['entries']}
        at, _, _, size = struct.unpack_from('<4I', rom, 0x20)
        cls.arm9 = rom[at:at + size]
        names = [e['name'] for e in manifest['entries']]
        native = room_catalog.parse(cls.arm9, names)
        source = next(r for r in native if r.name == mr.SOURCE)
        raw, _ = ch.build_room(cls.blobs[mr.SOURCE + '_app.obj'], cls.blobs[ch.STATE_TEMPLATE + '_app.obj'],
                               ch.BY_NAME[b.ROOM], source.index, [r.name for r in native], {})
        cls.raw = ch.stage_authored(raw, ch.BY_NAME[b.ROOM], cls.blobs.__getitem__)

    def test_callbacks_are_rebound_and_every_target_is_local(self):
        sim = Script(self.raw)
        rec = RoomObjects.parse(self.raw).records[1]
        batches = Entities.parse(rec.sections[0]).batches
        for i in range(3):
            ag = sim.batches.index(f'Core {i + 1}')
            e, = batches[ag].records
            self.assertEqual(e[22], b.CORE_KIND)
            self.assertEqual(sim.labels[e[23] - 1], f'Core_{i + 1}')
            self.assertEqual(struct.unpack_from('<2i', e), (b.CORE_X[i] * 4096, 8 * 4096))
        for group in sim.groups:
            for c in group.commands:
                for act in s.actions(c):
                    self.assertTrue(s.targets(act) <= set(range(len(batches))))
                    if act[1]: self.assertLessEqual(act[1], len(batches[act[0]].records))
                    if act[3]: self.assertLessEqual(act[3], len(sim.groups))
                if c.opcode == s.ANIMATE:
                    self.assertLess(c.operand[0], len(batches))
                    self.assertLessEqual(c.operand[1], len(batches[c.operand[0]].records))
        self.assertLessEqual(len(sim.groups), 255)
        self.assertEqual(ch.visited(94), 163)

    def test_three_distinct_cores_are_required_and_duplicate_callbacks_are_safe(self):
        sim = Script(self.raw)
        sim.run('Start'); sim.run('Start'); sim.advance(100)
        sim.run('Core_2'); sim.run('Core_2'); sim.advance(100)
        self.assertEqual(sim.vars[b.COUNT], 1)
        sim.run('Core_1'); sim.run('Core_1'); sim.advance(100)
        self.assertEqual(sim.vars[b.COUNT], 2)
        self.assertFalse(sim.vars.get(151))
        sim.run('Core_3'); sim.run('Core_3'); sim.advance(1000)
        self.assertEqual(sim.vars[b.COUNT], 3)
        self.assertEqual(sim.vars[151], 1)
        self.assertEqual(sim.vars[b.RUN], 0)
        self.assertFalse(sim.live('Arc') | sim.live('Warning') | sim.live('Seal'))
        self.assertEqual([x[1] for x in sim.events if 'Leech Crew' in x[1]], ['Leech Crew 1', 'Leech Crew 2', 'Leech Crew 3'])

    def test_victory_cancels_warning_live_rest_and_queued_adds(self):
        for frame in (65, 160, 215):
            sim = Script(self.raw)
            sim.run('Start'); sim.advance(frame)
            for i in range(3): sim.run(f'Core_{i + 1}')
            sim.advance(2000)
            self.assertFalse(sim.live('Arc') | sim.live('Warning') | sim.live('Seal'))
            self.assertEqual(len([x for x in sim.events if 'Leech Crew' in x[1]]), 1)
            self.assertFalse(sim.queue)

    def test_breaker_is_optional_once_only_and_return_has_a_full_warning(self):
        sim = Script(self.raw)
        sim.run('Start'); sim.advance(200)       # active first lane
        self.assertTrue(sim.live('Arc'))
        sim.run('Breaker'); sim.run('Breaker')
        self.assertEqual(sim.vars[b.USED], 1)
        self.assertFalse(sim.live('Arc') | sim.live('Warning'))
        sim.advance(b.POWER_CUT - 1)
        self.assertFalse(sim.live('Arc'))
        sim.advance(1)
        end = sim.now
        sim.advance(220)
        next_arc = next(t for t, name in sim.events if t > end and 'Arc' in name)
        warning = max(t for t, name in sim.events if end <= t < next_arc and 'Warning' in name)
        self.assertGreaterEqual(next_arc - warning, b.WARNING[0] - 56)
        sim.run('Breaker')
        self.assertEqual(sim.vars[b.CUT], 0)

    def test_saved_victory_and_fresh_attempt_initialization(self):
        cleared = Script(self.raw, (151,))
        cleared.run('Start'); cleared.advance(3000)
        self.assertFalse(cleared.live('Core') | cleared.live('Arc') | cleared.live('Crew') | cleared.live('Entry'))
        fresh = Script(self.raw)
        self.assertEqual([fresh.vars[v] for v in range(b.RUN, b.ADDS[-1] + 1)], [0] * 10)
        fresh.run('Start'); fresh.advance(40)
        self.assertEqual(len(fresh.live('Core')), 6)     # three native cores and their three beacons

    def test_adapter_preserves_all_unknown_data_and_scopes_the_accessor(self):
        at = ch.ML_BASE + ch.ML_SPACE - 256
        code, patch = b.core_adapter(self.arm9, at)
        native = self.arm9[b.DATA_BASE - ch.BASE + b.CORE_KIND * 64:b.DATA_BASE - ch.BASE + (b.CORE_KIND + 1) * 64]
        new = code[b.LEGACY_CODE_SIZE:b.LEGACY_CODE_SIZE + 64]
        self.assertEqual(new[:20], native[:20])
        self.assertEqual(new[24:], native[24:])
        self.assertEqual(struct.unpack_from('<I', new, 20)[0], b.CORE_HEALTH)
        self.assertEqual(struct.unpack_from('<I', code, 4)[0], 0xE3510021)  # kind guard
        self.assertEqual(struct.unpack_from('<I', code, 40)[0], 0xE352005E)  # room guard
        warning = code[b.LEGACY_CODE_SIZE + 64:]
        native_warning = self.arm9[b.DATA_BASE - ch.BASE + b.WARNING_KIND * 64:b.DATA_BASE - ch.BASE + (b.WARNING_KIND + 1) * 64]
        self.assertEqual(warning[4:], native_warning[4:])
        self.assertEqual(struct.unpack_from('<I', warning)[0], 0)
        self.assertEqual(len(code), 216)
        self.assertEqual(patch[:2], (b.ACCESSOR, 0xE92D000F))
        self.assertEqual(ch.BASE + 0x139818, b.DATA_BASE + b.CORE_KIND * 64)

    def test_original_warning_mesh_roundtrips_and_has_no_texture_dependency(self):
        from tools import nitro_build as nb
        raw = b.warning_model()
        parts = nb.model_parts(raw)
        self.assertEqual(nb.room_model(parts), raw)
        self.assertEqual(len(parts.materials), 1)
        self.assertIsNone(parts.materials[0].texture)
        self.assertIsNone(parts.materials[0].palette)
        code, _ = b.core_adapter(self.arm9, ch.ML_BASE + ch.ML_SPACE - 256, 4000)
        self.assertEqual(struct.unpack_from('<3I', code, b.LEGACY_CODE_SIZE + 64), (0, 0xB6, 4000))

    def test_beacons_preserve_native_core_collision_and_disappear_per_core(self):
        from tools import nitro_build as nb
        raw = b.core_model()
        self.assertEqual(nb.room_model(nb.model_parts(raw)), raw)
        code, _ = b.core_adapter(self.arm9, ch.ML_BASE + ch.ML_SPACE - b.ADAPTER_SPACE, 4000, 4001)
        self.assertLessEqual(len(code), b.ADAPTER_SPACE)
        native = self.arm9[b.DATA_BASE - ch.BASE + b.CORE_KIND * 64:b.DATA_BASE - ch.BASE + (b.CORE_KIND + 1) * 64]
        core = code[b.ADAPTER_CODE_SIZE:b.ADAPTER_CODE_SIZE + 64]
        self.assertEqual(core[:20], native[:20])
        self.assertEqual(core[24:], native[24:])
        self.assertEqual(struct.unpack_from('<3I', code, b.ADAPTER_CODE_SIZE + 128), (0, 0xB6, 4001))
        sim = Script(self.raw); sim.run('Start')
        self.assertEqual(len(sim.live('Beacon')), 3)
        sim.run('Core_2'); sim.run('Core_2')
        self.assertEqual(sim.live('Beacon'), {'Core 1 Beacon', 'Core 3 Beacon'})
        sim.run('Core_1'); sim.run('Core_3'); sim.advance(2000)
        self.assertFalse(sim.live('Beacon'))

    def test_new_adapter_routes_three_kinds_only_inside_the_boss_room(self):
        at=ch.ML_BASE+ch.ML_SPACE-b.ADAPTER_SPACE
        code,_=b.core_adapter(self.arm9,at,4000,4001)
        def route(kind,room,room_pointer=0x02210000):
            memory={at+i:struct.unpack_from('<I',code,i)[0] for i in range(0,len(code),4)}
            memory.update({0x02145C5C:room_pointer,room_pointer:room})
            regs=[0x02310000,kind,0x12345678,0x98765432]+[0]*8+[0xABCDEF00,0,0x02010000,at]
            initial=regs[:];saved=None;z=False
            for _ in range(40):
                pc=regs[15];word=memory[pc];regs[15]=pc+4
                if not {0:z,1:not z,14:True}[word>>28]:continue
                if word==0xE92D500F:saved=regs[:]
                elif word==0xE8BD900F:
                    for r in (0,1,2,3,12,14):regs[r]=saved[r]
                    self.assertEqual(regs[:15],initial[:15])
                    return memory[initial[0]]
                elif word>>25&7==5:
                    off=word&0xFFFFFF
                    if off&0x800000:off-=1<<24
                    regs[15]=pc+8+off*4
                elif word&0x0FF00000==0x05900000:
                    base=(word>>16)&15;dest=(word>>12)&15
                    regs[dest]=memory[(pc+8 if base==15 else regs[base])+(word&0xFFF)]
                elif word&0x0DF00000==0x01500000:
                    z=regs[(word>>16)&15]==(word&255)
                elif word&0x0FF00000==0x02800000:
                    regs[(word>>12)&15]=pc+8+(word&255)
                elif word==0xE0822301:regs[2]=(regs[2]+(regs[1]<<6))&0xFFFFFFFF
                elif word==0xE5802000:memory[regs[0]]=regs[2]
                else:self.fail(f'Unsupported accessor instruction {word:08x}')
            self.fail('Accessor did not return')
        for kind,offset in ((b.CORE_KIND,0),(b.WARNING_KIND,64),(b.MARKER_KIND,128)):
            self.assertEqual(route(kind,94),at+b.ADAPTER_CODE_SIZE+offset)
            for room in (0,93,95):self.assertEqual(route(kind,room),b.DATA_BASE+kind*64)
            self.assertEqual(route(kind,94,0),b.DATA_BASE+kind*64)
        for kind in (0,0x11,0x14,0x22):self.assertEqual(route(kind,94),b.DATA_BASE+kind*64)


if __name__ == '__main__': unittest.main()
